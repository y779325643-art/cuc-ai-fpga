"""Operator-selected public inputs, development preflight and verified analysis views."""
from __future__ import annotations

from dataclasses import asdict
import importlib
import json
from pathlib import Path
from typing import Any

from sr2fpga_agent.analysis import canonical_sha256
from sr2fpga_agent.artifact_store import ArtifactStore
from sr2fpga_agent.contract_registry import ContractRegistry
from sr2fpga_agent.local_tools import resolve_executable
from sr2fpga_agent.models import canonical_json_bytes
from sr2fpga_agent.pc.context import load_public_task
from sr2fpga_agent.pc.inputs import ParseLimits, TrustedContext, TrustedSource
from sr2fpga_agent.repository_paths import RepositoryPaths
from sr2fpga_agent.tasks.llm import CASE_FAMILIES

from .budgets import BudgetLedger, BudgetLimits
from .evaluation import EvaluationResult, TerminalEvaluationAuthority, assert_supported_case, task_identity
from .gateway import ReplayTransport
from .isolation import DockerBackend, LocalDevelopmentBackend, ToolLimits, candidate_sha256
from .runtime import (METHODS, PairedBlockRuntime, RuntimeIdentity, RuntimeIntegrityError, finalize_batch,
                      runtime_source_snapshot, terminal_value, _sha as _runtime_hash)


def load_json(path: Path) -> Any:
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result
    def nonfinite(value):
        raise ValueError("nonfinite JSON number: " + value)
    with Path(path).open("rb") as stream:
        raw = stream.read(64_000_001)
    if len(raw) > 64_000_000:
        raise ValueError("runtime input exceeds its local read bound")
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite)


def validate_document(key: str, value: Any) -> None:
    errors = ContractRegistry().load_schema(key).validate(value)
    if errors:
        raise ValueError("; ".join(errors))


def load_public_directory(directory: Path):
    directory = Path(directory).resolve(strict=True)
    sources = {}
    for field, name in (("requirements", "requirements"), ("target_profile", "target-profile"),
                        ("capability_profile", "capability-profile")):
        sources[field] = TrustedSource(name, (directory / (name + ".json")).read_bytes())
    return load_public_task(TrustedContext(**sources), asset_root=directory, limits=ParseLimits(8_000_000, 128))


def configured_limits(values: dict[str, Any], *, final: bool = False) -> dict[str, BudgetLimits]:
    return {method: BudgetLimits.for_method(method, **values,
            **({"max_public_cycles": 0} if final else {})) for method in METHODS}


def load_callable(spec: str):
    module, separator, name = spec.partition(":")
    if not separator or not module or not name or not all(part.isidentifier() for part in module.split(".")) or not name.isidentifier():
        raise ValueError("trusted factory must have the form module:function")
    value = getattr(importlib.import_module(module), name)
    if not callable(value):
        raise ValueError("selected factory is not callable")
    return value


def backend_from_config(config: dict[str, Any]):
    if config["kind"] == "local_development":
        return LocalDevelopmentBackend()
    return DockerBackend(config["image"], user=config.get("user", "1000:1000"))


def preflight(config: dict[str, Any], *, formal: bool = False) -> dict[str, Any]:
    validate_document("pc21_runtime_config", config)
    def reject_literal_credentials(value):
        if isinstance(value, dict):
            if any(str(key).lower() in {"api_key", "access_token", "password", "secret"} for key in value):
                raise ValueError("runtime configuration must select credentials by environment reference")
            for item in value.values():
                reject_literal_credentials(item)
        elif isinstance(value, list):
            for item in value:
                reject_literal_credentials(item)
    reject_literal_credentials(config["transport"])
    public = load_public_directory(Path(config["public_directory"]))
    assert_supported_case(config["case"], public)
    configured_limits(config["limits"])
    configured_limits(config["final_limits"], final=True)
    limits = ToolLimits(**config["tool_limits"])
    if limits.timeout_seconds > public.target["tool_timeout_seconds"]:
        raise ValueError("configured tool limit exceeds the frozen public target")
    reasons = []
    backend = backend_from_config(config["backend"])
    if isinstance(backend, DockerBackend):
        if not backend.available():
            reasons.append("pinned_local_docker_toolchain_unavailable")
    elif any(resolve_executable(tool) is None for tool in ("yosys", "iverilog", "vvp")):
        reasons.append("local_development_tools_unavailable")
    if config["transport"]["kind"] == "replay":
        validate_document("pc21_model_replay", load_json(Path(config["transport"]["path"])))
    # Preflight never imports a live transport factory, reads credentials or dispatches models.
    if formal:
        reasons.extend(["formal_execution_not_supported_by_development_entry", "research_protocol_unfrozen",
                        "task_family_not_qualified"])
        if not backend.isolation_qualified:
            reasons.append("os_isolation_not_qualified")
    return {"requested_scope": "formal" if formal else "development", "ready": not reasons,
            "reasons": reasons, "official": False, "model_calls": 0,
            "case": config["case"], "bindings": public.sources.bindings(), "backend": backend.policy()}


def _write_new(path: Path, value: Any, *, contract_key: str | None = None) -> None:
    if contract_key:
        validate_document(contract_key, value)
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = canonical_json_bytes(value)
    if path.exists():
        if path.read_bytes() != encoded:
            raise ValueError("existing output binds different content; use a fresh directory")
        return
    with path.open("xb") as stream:
        stream.write(encoded)


def run_development(configs: list[dict[str, Any]], output: Path, *, allow_model_calls: bool = False,
                    terminal_suite_factory: str | None = None) -> dict[str, Any]:
    if not configs or len({item["campaign_id"] for item in configs}) != 1:
        raise ValueError("development batch must select one nonempty campaign")
    root = Path(output).resolve()
    artifacts = (RepositoryPaths.discover().root / "artifacts").resolve()
    if root == artifacts or not root.is_relative_to(artifacts):
        raise ValueError("runtime output must be below artifacts/")
    binding_records = []
    for config in configs:
        report = preflight(config)
        if not report["ready"]:
            raise ValueError("development preflight rejected: " + ",".join(report["reasons"]))
        binding_records.append(report["bindings"])
        if config["transport"]["kind"] != "replay" and not allow_model_calls:
            raise ValueError("live transport requires --allow-model-calls and explicit run scope")
    root.mkdir(parents=True, exist_ok=True)
    run_store = ArtifactStore(root / "control" / "run-store")
    run_store.put_blob("source-bindings", canonical_json_bytes(runtime_source_snapshot()), media_type="application/json")
    run_store.put_blob("input-bindings", canonical_json_bytes(binding_records), media_type="application/json")
    run_store.put_blob("replay-bindings", canonical_json_bytes([
        canonical_sha256(load_json(Path(config["transport"]["path"]))) if config["transport"]["kind"] == "replay" else None
        for config in configs]), media_type="application/json")
    run_store.put_blob("configuration", canonical_json_bytes({"configs": configs,
        "terminal_suite_factory": terminal_suite_factory}), media_type="application/json")
    existing = run_store.reference("report")
    if existing is not None:
        report = json.loads(run_store.read_verified(existing))
        _write_new(root / "run.json", report, contract_key="pc21_runtime_report")
        return report
    blocks = []
    for index, config in enumerate(configs):
        case = config["case"]
        public = load_public_directory(Path(config["public_directory"]))
        identity = RuntimeIdentity(config["campaign_id"], CASE_FAMILIES[case], config["design_cluster_id"],
            config["dependency_group_id"], config["semantic_instance_id"], config["replicate_id"])
        transport_config = config["transport"]
        if transport_config["kind"] == "replay":
            tape = load_json(Path(transport_config["path"]))
            transport = ReplayTransport(tape["responses"])
        else:
            transport = load_callable(transport_config["factory"])(dict(transport_config["settings"]))
            if not transport.is_live:
                raise ValueError("client factory did not provide a live provider transport")
        backend = backend_from_config(config["backend"])
        if isinstance(backend, DockerBackend):
            if not backend.qualify(root / "private" / f"qualification-{index}"):
                raise ValueError("Docker confinement qualification failed")
        block = PairedBlockRuntime(public, case=case, identity=identity,
            output_root=root / "control" / f"b{index}", evaluator_root=root / "private" / f"b{index}",
            transport=transport, limits=configured_limits(config["limits"]),
            final_limits=configured_limits(config["final_limits"], final=True), tool_limits=ToolLimits(**config["tool_limits"]),
            backend=backend, schedule_seed=config["schedule_seed"], allow_model_calls=allow_model_calls,
            max_model_call_seconds=config["max_model_call_seconds"])
        blocks.append(block)
    # All generation closes before the trusted private suite factory is imported.
    generations = [block.generate() for block in blocks]
    final = None
    if terminal_suite_factory:
        suites = load_callable(terminal_suite_factory)({case: block.task for case, block in zip([b.case for b in blocks], blocks)})
        final = finalize_batch(blocks, private_root=root / "private" / "authority", private_suites=suites)
        _write_new(root / "private" / "terminal-analysis.json", final)
        export_analysis_views(blocks, final, root / "analysis")
    report = {"contract_version": "pc21-runtime-report-v1", "analysis_population": "development", "official": False,
        "claim_authorized": False, "natural_model_dispatches": sum(
            item["budget"]["actual"]["observed"]["model_calls"] for block, item in zip(blocks, generations)
            if block.gateway.transport.is_live),
        "source_classes": sorted({block.gateway.transport.source_class for block in blocks}),
        "blocks": [{"identity": item["identity"], "budget": item["budget"],
                    "terminals": {method: {"candidate_sha256": terminal["candidate"]["candidate_sha256"] if terminal["candidate"] else None,
                                           "public_accepted": bool(terminal["public_evaluation"] and terminal["public_evaluation"].get("public", {}).get("accepted")),
                                           "repair_transitions": len(terminal["repairs"])}
                                  for method, terminal in item["terminals"].items()}}
                   for item in generations],
        "terminal_barrier": final["barrier"] if final else None,
        "terminal_evaluation": "completed" if final else "not_run"}
    validate_document("pc21_runtime_report", report)
    run_store.put_blob("report", canonical_json_bytes(report), media_type="application/json")
    _write_new(root / "run.json", report, contract_key="pc21_runtime_report")
    return report


def export_analysis_views(blocks: list[PairedBlockRuntime], final: dict[str, Any], output: Path) -> None:
    """Re-read the evaluator authority; caller-supplied scores are not trusted."""
    if not final.get("barrier"):
        raise ValueError("analysis export requires a closed terminal barrier")
    # The private authority validates candidate/task/suite/semantic-commit bindings.
    authority_root = blocks[0].private_root.parent / "authority"
    authority = TerminalEvaluationAuthority(authority_root,
        planned_slots=[block.identity.slot(method) for block in blocks for method in METHODS])
    slots, results = [], []
    barrier = authority.store.reference("barrier")
    if barrier is None or final["barrier"]["barrier_id"] != "barrier-" + barrier.sha256:
        raise RuntimeIntegrityError("analysis does not bind the stored terminal barrier")
    for block in blocks:
        generation = block.generate()
        terminal_budget = BudgetLedger(ArtifactStore(block.private_root / "terminal-accounting"),
            "terminal-" + _runtime_hash(asdict(block.identity)), block.final_limits).snapshot()
        for method in METHODS:
            natural_slot = block.identity.slot(method)
            raw = authority.analysis_result(natural_slot)
            seal = json.loads(authority.store.read_verified("seals/" + authority._key(natural_slot)))
            terminal = generation["terminals"][method]
            candidate = terminal["candidate"]
            public = terminal["public_evaluation"]
            public_ref = ArtifactStore(block.private_root / "final-public-store").reference("public/" + authority._key(natural_slot))
            if public_ref is not None:
                evidence = EvaluationResult(**json.loads(ArtifactStore(block.private_root / "final-public-store").read_verified(public_ref)))
                public = {"public": evidence.public_feedback(), "outcome": evidence.to_dict()}
            if candidate is not None:
                ref = candidate["artifact_ref"]
                source = json.loads(block.store.read_verified(ref["key"]))
                if candidate_sha256(source["files"]) != raw["candidate_sha256"]:
                    raise RuntimeIntegrityError("analysis source candidate bytes differ")
            if raw["hidden_execution_status"] == "integrity_error":
                raise RuntimeIntegrityError("integrity violation cannot become an ordinary missing row")
            value = terminal_value(terminal, public, raw)
            statuses = {generation["budget"]["methods"][method]["status"], terminal_budget["methods"][method]["status"]}
            budget_status = "exceeded" if "exceeded" in statuses else "unverifiable" if "unverifiable" in statuses else "compliant"
            slot = {"slot_id": canonical_sha256(natural_slot), "family_id": block.identity.family_id,
                "design_cluster_id": block.identity.design_cluster_id, "dependency_group_id": block.identity.dependency_group_id,
                "semantic_instance_id": block.identity.semantic_instance_id, "replicate_id": block.identity.replicate_id,
                "method_condition": method, "endpoint": "B4" if method in {"M1", "M5"} else "initial",
                "task_sha256": task_identity(block.task), "suite_sha256": seal["suite_sha256"]}
            slots.append(slot)
            # Fail/pass must agree with the sealed private outcome; public failures
            # can establish zero even when the hidden suite is correctly not run.
            results.append({"slot_id": slot["slot_id"], "task_sha256": slot["task_sha256"],
                "suite_sha256": slot["suite_sha256"], "value": value,
                "outcome_class": "design_outcome" if value is not None else "infrastructure_unscorable",
                "budget_status": budget_status, "integrity_status": "intact" if block.backend.isolation_qualified else "unverifiable",
                "candidate_sha256": raw["candidate_sha256"], "reason": raw.get("reason", "terminal_evaluated")})
    manifest = {"contract_version": "pc21-analysis-manifest-v1", "research_plan_version": "paper1-v2.3",
                "population_id": "llm_inference_subsystems_v1", "analysis_population": "development", "slots": slots}
    manifest_hash = canonical_sha256(manifest)
    _write_new(output / "manifest.json", manifest, contract_key="pc21_analysis_manifest")
    _write_new(output / "results.json", {"contract_version": "pc21-analysis-results-v1",
        "manifest_sha256": manifest_hash, "results": results}, contract_key="pc21_analysis_results")
