"""Prepare public LLM cases or validate their hand-authored development controls.

This controller dispatches no models and grants no official evaluation credit.
The generic PC emitter remains independent of all case algorithms.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, is_dataclass
import hashlib
from importlib import import_module
import json
from pathlib import Path
from typing import Any

from sr2fpga_agent.artifact_store import ArtifactStore
from sr2fpga_agent.models import canonical_json_bytes
from sr2fpga_agent.pc.context import check_task_design, load_public_task
from sr2fpga_agent.pc.development_tools import run_recorded
from sr2fpga_agent.pc.emitter import build_structure, compose_behavior, write_project
from sr2fpga_agent.pc.inputs import (
    ParseLimits, TrustedContext, TrustedSource, assemble_project_contract,
)
from sr2fpga_agent.repository_paths import RepositoryPaths


RESEARCH_PLAN_VERSION = "paper1-v2.3"
POPULATION_ID = "llm_inference_subsystems_v1"
CASE_MODULES = {
    "qkv": "sr2fpga_agent.tasks.llm_qkv",
    "attention": "sr2fpga_agent.tasks.llm_attention",
    "ffn": "sr2fpga_agent.tasks.llm_ffn",
}
CASE_FAMILIES = {
    "qkv": "llm_quantized_qkv_projection",
    "attention": "llm_kv_cache_decode_attention",
    "ffn": "llm_gated_ffn",
}


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(canonical_json_bytes(value))


def _case_module(case: str):
    if case not in CASE_MODULES:
        raise ValueError(f"unknown LLM case: {case}")
    return import_module(CASE_MODULES[case])


def _source_files(case: str) -> list[Path]:
    _case_module(case)
    repository = RepositoryPaths.discover().root
    package = Path(__file__).parents[1]
    return sorted({*package.rglob("*.py"), *(repository / "contracts").rglob("*.json")})


def prepare_case(case: str, output: str | Path) -> Path:
    """Write only frozen public inputs under public/; no reference or tools there."""
    module = _case_module(case)
    task = module.build_development_task()
    if task["family"] != CASE_FAMILIES[case] or task["development_only"] is not True:
        raise ValueError("LLM case identity or development scope mismatch")
    root = Path(output).resolve()
    artifacts = (RepositoryPaths.discover().root / "artifacts").resolve()
    if root == artifacts or not root.is_relative_to(artifacts):
        raise ValueError("LLM development output must be below artifacts/")
    if root.exists():
        raise FileExistsError("LLM development output must be a fresh directory")
    assets = []
    for index, (asset_id, data) in enumerate(sorted(task["public_assets"].items())):
        if not isinstance(data, bytes):
            raise ValueError("public assets must be original bytes")
        assets.append({"id": asset_id, "path": f"assets/asset-{index:03d}.json",
                       "size_bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    requirements = {
        "contract_version": "development-public-context-v2", "analysis_population": "development",
        "requirement_id": task["task_id"], "revision_id": "llm-development-v1",
        "public_text": task["public_text"], "boundary": task["boundary"]["boundary"],
        "fact_records": [{"fact_id": name, **fact, "provenance": "system_assumption",
                          "source_ids": [RESEARCH_PLAN_VERSION, task["task_id"]]}
                         for name, fact in sorted(task["facts"].items())],
        "public_assets": assets,
    }
    root.mkdir(parents=True)
    for name, value in (("requirements", requirements), ("target-profile", task["target_profile"]),
                        ("capability-profile", task["capability_profile"])):
        _write_json(root / "public" / (name + ".json"), value)
    for asset in assets:
        path = root / "public" / asset["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(task["public_assets"][asset["id"]])
    store = ArtifactStore(root / "store")
    for name in ("requirements", "target-profile", "capability-profile"):
        store.put_blob("public/" + name, (root / "public" / (name + ".json")).read_bytes(),
                       media_type="application/json")
    repository = RepositoryPaths.discover().root
    source_refs = {}
    for source in _source_files(case):
        relative = source.relative_to(repository).as_posix()
        source_key = "sources/file-" + hashlib.sha256(relative.encode("utf-8")).hexdigest()
        media_type = "application/json" if source.suffix == ".json" else "text/x-python"
        ref = store.put_blob(source_key, source.read_bytes(), media_type=media_type)
        source_refs[relative] = ref.to_dict()
    store.put_blob("configuration", canonical_json_bytes({
        "case": case, "family": task["family"], "task_id": task["task_id"],
        "research_plan_version": RESEARCH_PLAN_VERSION, "population_id": POPULATION_ID,
        "official": False, "analysis_population": "development", "model_calls": 0,
        "candidate_generated": False, "hidden_evaluation": "not_run", "sources": source_refs,
    }), media_type="application/json")
    public = _load_prepared(root, case)
    store.append_event("llm-case", "development_prepared", {
        "case": case, "family": task["family"], "bindings": public.sources.bindings(),
        "model_calls": 0, "official": False,
    })
    return root


def _load_prepared(root: Path, case: str):
    store = ArtifactStore(root / "store")
    configuration = json.loads(store.read_verified(store.reference("configuration")))
    if configuration["case"] != case or configuration["family"] != CASE_FAMILIES[case]:
        raise ValueError("prepared LLM case identity mismatch")
    repository = RepositoryPaths.discover().root
    for relative, reference in configuration["sources"].items():
        stored = store.reference(reference["key"])
        if stored is None or stored.sha256 != reference["sha256"]:
            raise ValueError("source snapshot reference mismatch")
        if (repository / relative).read_bytes() != store.read_verified(stored):
            raise ValueError("LLM case or construction sources changed after preparation")
    sources = {}
    for field, name in (("requirements", "requirements"), ("target_profile", "target-profile"),
                        ("capability_profile", "capability-profile")):
        content = (root / "public" / (name + ".json")).read_bytes()
        reference = store.reference("public/" + name)
        if reference is None or content != store.read_verified(reference):
            raise ValueError("frozen LLM public source changed")
        sources[field] = TrustedSource(name, content)
    return load_public_task(TrustedContext(**sources), asset_root=root / "public",
                            limits=ParseLimits(8_000_000, 128))


def check_reference(case: str, output: str | Path, *, synthesize: bool = False) -> dict[str, Any]:
    """Build and execute a manual control, with retained parser and tool failures."""
    root = prepare_case(case, output)
    receipt: dict[str, Any] = {
        "case": case, "family": CASE_FAMILIES[case], "official": False,
        "candidate_generated": False, "model_calls": 0, "hidden_evaluation": "not_run",
        "static": "not_run", "composition": "not_run", "compile": "not_run",
        "simulation": "not_run", "semantic": "not_run", "synthesis": "not_run",
        "status": "failed",
    }
    phase = "static"
    try:
        module = _case_module(case)
        public = _load_prepared(root, case)
        design = module.reference_design()
        pc = assemble_project_contract(canonical_json_bytes(design), public.sources,
                                       limits=ParseLimits(8_000_000, 128))
        checked = check_task_design(design, public)
        build = build_structure(checked, bindings=pc["bindings"], toolchain_id=public.target["target_id"])
        _write_json(root / "reference-design.json", design)
        _write_json(root / "pc.json", pc)
        _write_json(root / "build-plan.json", asdict(build))
        receipt.update(static="pass", build_plan_sha256=build.build_plan_sha256,
                       verification_obligations=list(checked.verification_obligations))
        reference = import_module(CASE_MODULES[case] + ".reference")
        bodies = reference.reference_behavior_bodies()
        bundle = {"contract_version": "pc21-behavior-bundle-v1", "build_plan_sha256": build.build_plan_sha256,
                  "units": {unit_id: {"body": bodies[unit["module_id"]]}
                            for unit_id, unit in build.units.items()}}
        _write_json(root / "reference-bundle.json", bundle)
        phase = "composition"
        project = compose_behavior(build, bundle, scratch_root=root / "parser",
                                   timeout_seconds=public.target["tool_timeout_seconds"],
                                   behavior_origin="hand_authored_development_control")
        project_root = write_project(project, root / "project")
        _write_json(root / "parser-evidence.json", project.parser_evidence)
        _write_json(root / "construction-origin-map.json", project.construction_origin_map)
        receipt["composition"] = "pass"
        harness = import_module(CASE_MODULES[case] + ".harness")
        (project_root / "trusted_llm_tb.sv").write_text(harness.render_testbench(), encoding="utf-8")
        manifest = json.loads(project.files["manifest.json"])
        timeout = public.target["tool_timeout_seconds"]
        commands = [("compile", ["iverilog", "-v", "-g2012", "-s", harness.TESTBENCH_TOP,
                                 "-o", "simulation.vvp", *[s["path"] for s in manifest["sources"]],
                                 "trusted_llm_tb.sv"]),
                    ("simulation", ["vvp", "simulation.vvp"])]
        for stage, command in commands:
            phase = stage
            result = run_recorded(command, project_root, stage, timeout_seconds=timeout)
            _write_json(root / (stage + ".json"), asdict(result))
            receipt[stage] = result.status
            if result.status != "passed":
                raise ValueError(f"{stage}: {result.status}, exit_code={result.exit_code}")
        phase = "semantic"
        trace = harness.check_trace(result.stdout)
        receipt["semantic"] = "pass"
        receipt["trace"] = asdict(trace) if is_dataclass(trace) else trace
        if synthesize:
            phase = "synthesis"
            script = "read_verilog -sv " + " ".join(s["path"] for s in manifest["sources"])
            script += "; synth -top " + manifest["top"]["module"] + "; stat"
            synthesis = run_recorded(["yosys", "-Q", "-T", "-p", script], project_root,
                                     "synthesis", timeout_seconds=timeout)
            _write_json(root / "synthesis.json", asdict(synthesis))
            receipt["synthesis"] = synthesis.status
            if synthesis.status != "passed":
                raise ValueError("generic synthesis: " + synthesis.status)
        receipt["status"] = "passed"
    except (ValueError, OSError, KeyError) as error:
        if receipt[phase] == "not_run":
            receipt[phase] = "failed"
        receipt["diagnostic"] = str(error)
    _write_json(root / "result.json", receipt)
    ArtifactStore(root / "store").append_event("llm-case", "reference_validation_completed", receipt)
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("prepare", "check-reference"))
    parser.add_argument("--case", choices=(*CASE_MODULES, "all"), required=True)
    parser.add_argument("--output", type=Path, required=True, help="Fresh directory below artifacts/")
    parser.add_argument("--synthesize", action="store_true", help="Also execute bounded generic Yosys synthesis")
    args = parser.parse_args(argv)
    if args.synthesize and args.operation != "check-reference":
        parser.error("--synthesize applies only to check-reference")
    cases = tuple(CASE_MODULES) if args.case == "all" else (args.case,)
    if args.output.exists():
        parser.error("output must be fresh; existing runs are never overwritten")
    receipts = []
    try:
        for case in cases:
            output = args.output / case if args.case == "all" else args.output
            if args.operation == "prepare":
                root = prepare_case(case, output)
                receipts.append({"case": case, "status": "prepared", "output": str(root), "model_calls": 0})
            else:
                receipts.append(check_reference(case, output, synthesize=args.synthesize))
    except (ValueError, OSError) as error:
        parser.exit(2, str(error) + "\n")
    print(json.dumps(receipts, ensure_ascii=True))
    return int(any(item["status"] == "failed" for item in receipts))


if __name__ == "__main__":
    raise SystemExit(main())
