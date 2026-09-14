"""Opt-in PC decision interface; never an implicit migration or repair pass."""
from __future__ import annotations

import argparse
import copy
from dataclasses import asdict, dataclass, field
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import sys
from typing import Any

from jsonschema import Draft202012Validator

from sr2fpga_agent.artifact_store import ArtifactRef, ArtifactStore
from sr2fpga_agent.contract_registry import ContractRegistry
from sr2fpga_agent.contract_skeleton import CANONICAL_PREDICTED_QOR_PATH, CANONICAL_TIMING_CONSTRAINT_PATH
from sr2fpga_agent.frozen_context import (
    FrozenRequirementContext, RequirementFactRecord, _freeze,
    capability_profile_id, context_from_validated_episode_pack,
    frozen_project_name, frozen_requirement_trace_template,
    platform_profile_id, platform_profile_sha256,
)
from sr2fpga_agent.his_validation import first_failed_h_stage, validate_frozen_system_his_payload_h_stages
from sr2fpga_agent.models import PlatformProfile
from sr2fpga_agent.path_safety import validate_project_relative_path, validate_sample_id
from sr2fpga_agent.repository_paths import discover_repository_root
from sr2fpga_agent.providers import ModelOutputEmpty, ModelOutputTruncated
from sr2fpga_agent.requirement_boundary import capability_profile_sha256
from sr2fpga_agent.system_his_capabilities import load_system_his_backend_capabilities


ASSEMBLY_VERSION = "pc-assembler-v1"
HOST_BINDINGS = {
    "target_platform": ("intent", "target_platform"),
    "acceptance_criteria": ("verification", "acceptance_obligation"),
    "declared_task_type": ("intent", "declared_task_type"),
}


class PCAssemblyError(ValueError):
    def __init__(self, stage: str, path: str, message: str):
        self.stage = stage
        super().__init__(f"{path}: {message}")


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=True, allow_nan=False, sort_keys=True,
                       separators=(",", ":")) + "\n").encode("utf-8")


def _hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _runtime_stamp() -> str:
    root = discover_repository_root()
    files = sorted((root / "agent/src").rglob("*.py")) + sorted((root / "contracts").rglob("*.json"))
    return _hash(_json_bytes({
        "files": [(path.relative_to(root).as_posix(), _hash(path.read_bytes())) for path in files],
        "python": sys.version, "jsonschema": version("jsonschema"),
    }))


def _validate_context(context: FrozenRequirementContext, platform: PlatformProfile) -> None:
    registry = ContractRegistry()
    for key, expected in {
        "pc_decisions": "pc-decisions-v1", "pc_assembly_execution": "pc-assembly-execution-v1",
        "pc_assembly_record": "pc-assembly-record-v1", "system_his": "system-his-v1.2",
    }.items():
        if registry.load_schema(key).version != expected:
            raise ValueError(f"PC interface requires {key}={expected}")
    schema = registry.load_schema("episode_pack").document
    public = context.to_dict()
    Draft202012Validator({"$defs": schema["$defs"], **schema["properties"]["public_context"]}).validate(public)
    encoded = json.dumps({k: v for k, v in public.items() if k != "public_projection_sha256"},
                         ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    if _hash(encoded) != context.public_projection_sha256 or context.disposition != "ready":
        raise ValueError("invalid frozen public context digest or disposition")
    ids = [item.fact_id for item in context.fact_records]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate frozen facts")
    # Ready contexts retain optional unknown facts. The existing frozen trace
    # excludes them; never turn those unknowns into fabricated required values.
    if (context.platform_profile_id, context.platform_profile_sha256) != (
        platform_profile_id(platform), platform_profile_sha256(platform),
    ):
        raise ValueError("frozen platform mismatch")
    capabilities = load_system_his_backend_capabilities()
    if (context.capability_profile_id, context.capability_profile_sha256) != (
        capability_profile_id(capabilities.registry_version), capability_profile_sha256(capabilities),
    ):
        raise ValueError("frozen capability registry mismatch")


def _context_from_public(public: dict[str, Any]) -> FrozenRequirementContext:
    return FrozenRequirementContext(**{
        **public, "fact_records": tuple(RequirementFactRecord(
            item["fact_id"], _freeze(item["value"]), item["provenance"], tuple(item["source_ids"])
        ) for item in public["fact_records"]),
    })


def _unique(items: list[dict], label: str) -> dict[str, dict]:
    result = {}
    for item in items:
        name = item["name"]
        if name in result:
            raise PCAssemblyError("uniqueness", label, f"duplicate name: {name}")
        result[name] = item
    return result


def _resolve_binding(pc: dict, binding: dict, label: str) -> str:
    tokens = binding["collection"].split(".")
    value: Any = pc
    pointer: list[str] = []
    for key in tokens:
        if not isinstance(value, dict) or key not in value:
            raise PCAssemblyError("binding_reference", label, f"collection does not exist: {binding['collection']}")
        value = value[key]
        pointer.append(key)
    steps = ([binding["name"]] if "name" in binding else []) + binding["path"]
    for key in steps:
        if isinstance(value, list):
            matches = [i for i, item in enumerate(value) if isinstance(item, dict) and item.get("name") == key]
            if len(matches) != 1:
                raise PCAssemblyError("binding_reference", label, f"name must resolve uniquely: {key}")
            index = matches[0]
            pointer.append(str(index))
            value = value[index]
        elif isinstance(value, dict) and key in value:
            pointer.append(key)
            value = value[key]
        else:
            raise PCAssemblyError("binding_reference", label, f"field does not exist: {key}")
    return "/" + "/".join(token.replace("~", "~0").replace("/", "~1") for token in pointer)


def _model_field_sources(value: Any, prefix: str = "") -> dict[str, str]:
    if isinstance(value, (dict, list)) and value:
        children = value.items() if isinstance(value, dict) else enumerate(value)
        result = {}
        for key, child in children:
            result.update(_model_field_sources(child, prefix + "/" + str(key).replace("~", "~0").replace("/", "~1")))
        return result
    return {prefix: "model"}


def _assemble(context: FrozenRequirementContext, body: dict) -> tuple[dict, dict, dict]:
    pc = copy.deepcopy(body["decisions"])
    field_sources = _model_field_sources(pc)
    instances = _unique(pc["instances"], "$.decisions.instances")
    _unique(pc["components"], "$.decisions.components")
    for key in ("ports", "parameters", "clocks", "resets", "interfaces"):
        _unique(pc["top"].get(key, []), f"$.decisions.top.{key}")
    for key in ("data_flow", "control_flow"):
        _unique(pc[key], f"$.decisions.{key}")
    for index, component in enumerate(pc["components"]):
        for key in ("ports", "parameters"):
            _unique(component[key], f"$.decisions.components[{index}].{key}")
    for index, instance in enumerate(instances.values()):
        instance["owns_state"] = []
        field_sources[f"/instances/{index}/owns_state"] = "derived"
    names: set[str] = set()
    for group in ("registers", "counters", "fsms", "buffers", "memories"):
        for index, state in enumerate(pc["state"][group]):
            name, owner = state["name"], state["owner"]
            if name in names:
                raise PCAssemblyError("uniqueness", f"$.decisions.state.{group}[{index}].name", f"duplicate state: {name}")
            names.add(name)
            if owner == "top":
                continue
            if owner not in instances:
                raise PCAssemblyError("ownership", f"$.decisions.state.{group}[{index}].owner", f"unknown owner: {owner}")
            instances[owner]["owns_state"].append(f"{owner}.{name}")
    sources = []
    for index, component in enumerate(pc["components"]):
        path = component["source"]
        try:
            if validate_project_relative_path(path) != path:
                raise ValueError("noncanonical path")
            if path in {"manifest.json", "system_his.json", "sim/tb_top.v", CANONICAL_TIMING_CONSTRAINT_PATH, CANONICAL_PREDICTED_QOR_PATH}:
                raise ValueError("source collides with a fixed non-RTL artifact")
        except ValueError as exc:
            raise PCAssemblyError("path", f"$.decisions.components[{index}].source", str(exc)) from exc
        if path not in sources:
            sources.append(path)
    pc["schema_version"] = "system-his-v1.2"
    pc["project_name"] = frozen_project_name(context)
    pc["intent"]["user_prompt"] = context.public_text
    pc["timing"]["constraints"] = [CANONICAL_TIMING_CONSTRAINT_PATH]
    pc["verification"]["testbench"] = "sim/tb_top.v"
    pc["artifacts"] = {
        "top_module": pc["top"]["name"], "rtl_sources": sources,
        "testbench": pc["verification"]["testbench"],
        "constraints": list(pc["timing"]["constraints"]), "manifest": "manifest.json",
        "predicted_qor": CANONICAL_PREDICTED_QOR_PATH,
    }
    trace = frozen_requirement_trace_template(context)
    facts = trace["required_facts"]
    field_sources.update({
        "/schema_version": "derived", "/project_name": "derived", "/intent/user_prompt": "frozen",
        "/intent/requirement_trace/requirement_id": "frozen", "/intent/requirement_trace/required_facts": "frozen",
        "/intent/requirement_trace/fact_to_his": "derived", "/intent/requirement_trace/unresolved_facts": "derived",
        "/timing/constraints": "derived", "/verification/testbench": "derived", "/artifacts": "derived",
    })
    host_keys = set(facts) & set(HOST_BINDINGS)
    model_keys = set(facts) - host_keys
    if set(body["fact_bindings"]) != model_keys:
        missing = sorted(model_keys - set(body["fact_bindings"]))
        extra = sorted(set(body["fact_bindings"]) - model_keys)
        raise PCAssemblyError("binding_keys", "$.fact_bindings", f"missing={missing}, extra/host-controlled={extra}")
    binding_sources = {}
    for key in facts:
        if key in host_keys:
            root, field = HOST_BINDINGS[key]
            pc[root][field] = copy.deepcopy(facts[key]["value"])
            field_sources[f"/{root}/{field}"] = "frozen"
            trace["fact_to_his"][key] = [f"/{root}/{field}"]
            binding_sources[key] = "host_copy"
        else:
            trace["fact_to_his"][key] = [_resolve_binding(pc, item, f"$.fact_bindings.{key}[{index}]")
                                         for index, item in enumerate(body["fact_bindings"][key])]
            binding_sources[key] = "model"
    pc["intent"]["requirement_trace"] = trace
    return pc, binding_sources, field_sources


def _no_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


@dataclass(frozen=True)
class PCAssemblyResult:
    status: str
    failure_stage: str | None
    diagnostics: tuple[str, ...]
    pc: dict | None
    validation_report: dict | None
    binding_sources: dict[str, str]
    field_sources: dict[str, str] = field(default_factory=dict)


def assemble_pc(context: FrozenRequirementContext, platform: PlatformProfile, raw_response: bytes | str) -> PCAssemblyResult:
    """Pure, non-mutating assembly. Invalid trusted context is an integrity error."""
    _validate_context(context, platform)
    try:
        text = raw_response.decode("utf-8") if isinstance(raw_response, bytes) else raw_response
        body = json.loads(text, object_pairs_hook=_no_duplicate_keys,
                          parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"nonfinite JSON: {value}")))
        json.dumps(body, ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (ValueError, UnicodeError, RecursionError) as exc:
        return PCAssemblyResult("input_parse_failed", "input_parse", (str(exc),), None, None, {})
    errors = ContractRegistry().load_schema("pc_decisions").validate(body)
    if errors:
        return PCAssemblyResult("decision_schema_failed", "decision_schema", errors, None, None, {})
    try:
        pc, origins, sources = _assemble(context, body)
    except PCAssemblyError as exc:
        return PCAssemblyResult("assembly_failed", exc.stage, (str(exc),), None, None, {})
    report = validate_frozen_system_his_payload_h_stages(context, pc, platform=platform)
    stage = first_failed_h_stage(report)
    passed = report.get("passed") is True
    unverified = not passed and stage is None
    if unverified:
        stage = next((key for key in ("h0", "h1", "h2", "h3") if report[key]["status"] != "pass"), "h3")
    diagnostics = tuple(str(item) for item in report[stage].get("diagnostics", [])) if stage else ()
    if unverified and not diagnostics:
        diagnostics = (f"{stage} was {report[stage]['status']}",)
    return PCAssemblyResult("pc_valid" if passed else "pc_unverified" if unverified else "pc_validation_failed", stage,
                            diagnostics, pc, report, origins, sources)


def decision_messages(context: FrozenRequirementContext, platform: PlatformProfile) -> list[dict[str, str]]:
    _validate_context(context, platform)
    facts = frozen_requirement_trace_template(context)["required_facts"]
    model_keys = sorted(set(facts) - set(HOST_BINDINGS))
    schema = ContractRegistry().load_schema("pc_decisions").document
    return [
        {"role": "system", "content": "Return only a pc-decisions-v1 JSON decision body, not a complete PC or FPP. Use only the supplied public context."},
        {"role": "user", "content": (
            "Choose the architecture, state owners and semantic fact bindings. The host copies fixed "
            "facts and derives owns_state/artifact inventories. Do not emit controlled fields, pass "
            "claims, RTL or evaluator metadata. Unknown owners and missing bindings will be rejected, "
            "not repaired. Names are case-sensitive and globally unique within each collection; "
            "state names are globally unique and owners must be top or a declared instance. "
            "Bindings select named objects/fields, never numeric array indices. Empty path selects "
            "the whole named object. Do not invent new assumptions to bypass required facts.\n"
            + "Public context:\n" + json.dumps(context.to_dict(), ensure_ascii=False, indent=2)
            + "\nRequired model fact binding keys:\n" + json.dumps(model_keys)
            + "\nThe host owns acceptance_criteria, target_platform and declared_task_type bindings when present."
            + "\nDecision schema:\n" + json.dumps(schema, ensure_ascii=False, indent=2)
        )},
    ]


def _persist(store: ArtifactStore, prefix: str, context: FrozenRequirementContext,
             platform: PlatformProfile, raw: bytes, calls: int = 0,
             provider_failure: str | None = None, execution_ref: ArtifactRef | None = None):
    raw_ref = store.put_blob(prefix + "/raw", raw, media_type="application/octet-stream")
    context_ref = store.put_blob(prefix + "/context", _json_bytes(context.to_dict()), media_type="application/json")
    platform_ref = store.put_blob(prefix + "/platform", _json_bytes(asdict(platform)), media_type="application/json")
    registry = ContractRegistry()
    stamp = _runtime_stamp()
    if execution_ref is None:
        execution = {"contract_version": "pc-assembly-execution-v1", "raw_response_ref": raw_ref.to_dict(),
                     "context_ref": context_ref.to_dict(), "platform_ref": platform_ref.to_dict(),
                     "logical_model_calls": calls, "provider_failure_type": provider_failure}
        execution_ref = store.put_validated_json(prefix + "/execution", execution, contract_key="pc_assembly_execution")
    else:
        execution = json.loads(store.read_verified(execution_ref))
        if registry.load_schema("pc_assembly_execution").validate(execution):
            raise ValueError("invalid PC assembly execution source")
        if (execution["raw_response_ref"], execution["context_ref"], execution["platform_ref"]) != (
            raw_ref.to_dict(), context_ref.to_dict(), platform_ref.to_dict(),
        ):
            raise ValueError("PC assembly execution source does not bind these inputs")
        calls, provider_failure = execution["logical_model_calls"], execution["provider_failure_type"]
    result = (PCAssemblyResult("provider_failed", "provider", (provider_failure,), None, None, {})
              if provider_failure else assemble_pc(context, platform, raw))
    if _runtime_stamp() != stamp:
        raise ValueError("PC interface changed during assembly; source inputs retained")
    pc_ref = store.put_blob(prefix + "/pc", _json_bytes(result.pc), media_type="application/json") if result.pc is not None else None
    report_ref = store.put_blob(prefix + "/h-validation", _json_bytes(result.validation_report), media_type="application/json") if result.validation_report is not None else None
    payload = {
        "contract_version": "pc-assembly-record-v1", "assembly_version": ASSEMBLY_VERSION,
        "decision_version": "pc-decisions-v1", "scope": "development_pc_interface_not_experiment",
        "raw_response_ref": raw_ref.to_dict(), "context_ref": context_ref.to_dict(), "platform_ref": platform_ref.to_dict(),
        "decision_schema_sha256": _hash(registry.load_schema("pc_decisions").path.read_bytes()),
        "pc_schema_sha256": _hash(registry.load_schema("system_his").path.read_bytes()),
        "implementation_sha256": stamp,
        "status": result.status, "failure_stage": result.failure_stage, "diagnostics": list(result.diagnostics),
        "pc_ref": pc_ref.to_dict() if pc_ref else None, "validation_report_ref": report_ref.to_dict() if report_ref else None,
        "binding_sources": result.binding_sources, "logical_model_calls": calls, "provider_failure_type": provider_failure,
        "field_sources": result.field_sources,
        "execution_ref": execution_ref.to_dict(),
        "official_outcome": False, "pass_credit_authority": False, "experiment_execution_authorized": False,
    }
    payload["record_id"] = "pc-assembly-" + _hash(_json_bytes(payload))
    ref = store.put_validated_json(prefix + "/record", payload, contract_key="pc_assembly_record")
    return payload, ref


def _claim(store: ArtifactStore, attempt_id: str) -> str:
    validate_sample_id(attempt_id)
    claims = store.root / "pc-attempt-claims"
    claims.mkdir(exist_ok=True)
    (claims / attempt_id).mkdir(exist_ok=False)  # Atomic and retained even on interruption.
    return "pc-interface/" + attempt_id


def record_pc_assembly(store: ArtifactStore, attempt_id: str, context: FrozenRequirementContext,
                       platform: PlatformProfile, raw_response: bytes | str):
    _validate_context(context, platform)
    prefix = _claim(store, attempt_id)
    raw = raw_response.encode("utf-8", errors="surrogatepass") if isinstance(raw_response, str) else raw_response
    return _persist(store, prefix, context, platform, raw, 0, None)


class PCDecisionGenerator:
    """Opt-in single logical model call; no retries or implicit M0–M5 relabeling."""
    def __init__(self, client, platform: PlatformProfile, store: ArtifactStore):
        self.client, self.platform, self.store = client, platform, store

    def generate(self, context: FrozenRequirementContext, attempt_id: str):
        stamp = _runtime_stamp()
        messages = decision_messages(context, self.platform)
        prefix = _claim(self.store, attempt_id)
        # Retain the trusted input even if the process is interrupted mid-call.
        self.store.put_blob(prefix + "/context", _json_bytes(context.to_dict()), media_type="application/json")
        self.store.put_blob(prefix + "/platform", _json_bytes(asdict(self.platform)), media_type="application/json")
        try:
            raw = self.client.stream_chat(messages).encode("utf-8", errors="surrogatepass")
        except Exception as exc:
            content = exc.content if isinstance(exc, (ModelOutputEmpty, ModelOutputTruncated)) else ""
            raw = content.encode("utf-8", errors="backslashreplace") if isinstance(content, str) else b""
            self.store.put_blob(prefix + "/raw", raw, media_type="application/octet-stream")
            if _runtime_stamp() != stamp:
                raise ValueError("PC interface changed during model invocation; raw response retained") from exc
            return _persist(self.store, prefix, context, self.platform, raw, 1, type(exc).__name__)
        self.store.put_blob(prefix + "/raw", raw, media_type="application/octet-stream")
        if _runtime_stamp() != stamp:
            raise ValueError("PC interface changed during model invocation; raw response retained")
        return _persist(self.store, prefix, context, self.platform, raw, 1, None)


def read_verified_pc_assembly(store: ArtifactStore, ref: ArtifactRef) -> dict:
    payload = json.loads(store.read_verified(ref))
    errors = ContractRegistry().load_schema("pc_assembly_record").validate(payload)
    if errors:
        raise ValueError("invalid PC assembly record: " + "; ".join(errors))
    unsigned = {key: value for key, value in payload.items() if key != "record_id"}
    if payload["record_id"] != "pc-assembly-" + _hash(_json_bytes(unsigned)):
        raise ValueError("PC assembly record ID mismatch")
    if payload["implementation_sha256"] != _runtime_stamp():
        raise ValueError("PC assembly implementation changed")
    context = _context_from_public(json.loads(store.read_verified(ArtifactRef(**payload["context_ref"]))))
    platform = PlatformProfile(**json.loads(store.read_verified(ArtifactRef(**payload["platform_ref"]))))
    _validate_context(context, platform)
    raw_ref = ArtifactRef(**payload["raw_response_ref"])
    prefix = raw_ref.key.removesuffix("/raw")
    if raw_ref.key != prefix + "/raw":
        raise ValueError("invalid PC raw-response key")
    rebuilt, rebuilt_ref = _persist(store, prefix, context, platform, store.read_verified(raw_ref),
                                    execution_ref=ArtifactRef(**payload["execution_ref"]))
    if rebuilt != payload or rebuilt_ref != ref:
        raise ValueError("PC assembly record does not replay from its source artifacts")
    return payload


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Offline PC decision assembly; no model or EDA calls.")
    parser.add_argument("--episode-pack", type=Path)
    parser.add_argument("--platform", type=Path)
    parser.add_argument("--response", type=Path)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--verify", metavar="RECORD_KEY")
    args = parser.parse_args(argv)
    root = args.output_root.resolve()
    artifacts = discover_repository_root() / "artifacts"
    if root == artifacts or not root.is_relative_to(artifacts):
        parser.error("output root must be a dedicated directory below repository artifacts/")
    if args.verify:
        if not root.is_dir():
            parser.error("assembly store does not exist")
        store = ArtifactStore(root)
        ref = store.reference(args.verify)
        if ref is None:
            parser.error("record not found")
        payload = read_verified_pc_assembly(store, ref)
    else:
        if not all((args.episode_pack, args.platform, args.response)):
            parser.error("episode-pack, platform and response are required")
        if root.exists():
            parser.error("output root already exists; use a fresh directory")
        pack = json.loads(args.episode_pack.read_text(encoding="utf-8"))
        context = context_from_validated_episode_pack(pack)
        if pack["audit_only"]["analysis_population"] not in {"development", "excluded"}:
            parser.error("the new PC interface is restricted to development/excluded input")
        platform = PlatformProfile(**json.loads(args.platform.read_text(encoding="utf-8")))
        _validate_context(context, platform)
        raw = args.response.read_bytes()
        payload, ref = record_pc_assembly(ArtifactStore(root), "attempt-000", context, platform, raw)
    print(json.dumps({"status": payload["status"], "record_ref": ref.to_dict(), "pc_ref": payload["pc_ref"]}, indent=2))
    return 0 if args.verify or payload["status"] == "pc_valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
