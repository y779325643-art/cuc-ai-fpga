"""Prepare explicit manual-response fixtures for the development runtime CLI.

This script is a test utility, not a model generation service. It runs no model
or HDL tool. All response bytes are labelled synthetic_fixture.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from importlib import import_module
from pathlib import Path
import re

from sr2fpga_agent.execution.evaluation import expected_public_abi
from sr2fpga_agent.execution.integration import load_public_directory, validate_document
from sr2fpga_agent.execution.isolation import ToolLimits
from sr2fpga_agent.models import canonical_json_bytes
from sr2fpga_agent.pc.context import check_task_design
from sr2fpga_agent.pc.emitter import build_structure
from sr2fpga_agent.repository_paths import RepositoryPaths
from sr2fpga_agent.tasks.llm import CASE_MODULES, prepare_case


def prepare(case: str, output: Path, campaign_id: str) -> Path:
    root = RepositoryPaths.discover().root
    output = output.resolve()
    if not output.is_relative_to((root / "artifacts").resolve()):
        raise ValueError("fixture output must be below artifacts/")
    output.mkdir(parents=True, exist_ok=False)
    prepared = prepare_case(case, output / "inputs")
    public = load_public_directory(prepared / "public")
    module = import_module(CASE_MODULES[case])
    reference = import_module(CASE_MODULES[case] + ".reference")
    design = module.reference_design()
    build = build_structure(check_task_design(design, public), bindings=public.sources.bindings(),
                            toolchain_id=public.target["target_id"])
    bodies = reference.reference_behavior_bodies()
    bundle = {"contract_version": "pc21-behavior-bundle-v1", "build_plan_sha256": build.build_plan_sha256,
              "units": {name: {"body": bodies[unit["module_id"]]} for name, unit in build.units.items()}}
    top, ports = expected_public_abi(public)
    files = {"rtl/" + name: text for name, text in reference.render_reference_project().items()}
    tops = [name for name, text in files.items() if re.search(r"\bmodule\s+" + re.escape(top) + r"\b", text)]
    if len(tops) != 1:
        raise ValueError("manual fixture lacks a unique public top")
    manifest = {"contract_version": "project-package-v1", "project_name": top,
        "top": {"module": top, "source": tops[0], "interface": {"ports": [
            {"name": name, "direction": direction, "width": width} for name, (direction, width) in ports.items()]}},
        "sources": [{"path": name, "role": "rtl_source", "language": "systemverilog"} for name in sorted(files)],
        "artifacts": [], "build": {"toolchain_id": public.target["target_id"], "language_standard": "systemverilog-2012"}}
    files["manifest.json"] = canonical_json_bytes(manifest).decode()
    proposal = canonical_json_bytes({"contract_version": "pc21-project-proposal-v1", "files": files}).decode()
    tape = {"contract_version": "pc21-model-replay-v1", "source_class": "synthetic_fixture", "responses": {
        "direct_project": [proposal], "untyped_plan": ["Implement exactly the frozen public arithmetic and transaction requirements."],
        "project_from_plan": [proposal], "pc_plan": [canonical_json_bytes(design).decode()],
        "project_from_pc": [proposal], "behavior": [canonical_json_bytes(bundle).decode()]}}
    values = {"max_total_input_tokens": 2_000_000, "max_total_output_tokens": 2_000_000,
        "max_single_output_tokens": 100_000, "max_context_tokens": 500_000,
        "max_public_tool_calls": 128, "max_final_public_tool_calls": 0, "max_hidden_tool_calls": 0,
        "max_active_seconds": 1800, "max_eda_seconds": 1800, "max_cpu_seconds": 7200, "max_memory_bytes": 2_147_483_648}
    configuration = {"contract_version": "pc21-runtime-config-v1", "research_plan_version": "paper1-v2.3",
        "population_id": "llm_inference_subsystems_v1", "analysis_population": "development", "campaign_id": campaign_id,
        "case": case, "design_cluster_id": "synthetic-fixed-" + case, "dependency_group_id": None,
        "semantic_instance_id": "synthetic-" + case, "replicate_id": "r0", "schedule_seed": 17,
        "public_directory": (prepared / "public").relative_to(root).as_posix(), "limits": values,
        "final_limits": {**values, "max_public_tool_calls": 0, "max_final_public_tool_calls": 16, "max_hidden_tool_calls": 16},
        "tool_limits": asdict(ToolLimits()), "max_model_call_seconds": 30,
        "transport": {"kind": "replay", "path": (output / "tape.json").relative_to(root).as_posix()},
        "backend": {"kind": "local_development"}}
    for name, value, key in (("tape.json", tape, "pc21_model_replay"), ("config.json", configuration, "pc21_runtime_config")):
        validate_document(key, value)
        (output / name).write_bytes(canonical_json_bytes(value))
    return output / "config.json"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=(*CASE_MODULES, "all"), default="attention")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--campaign-id", default="synthetic-pc21-runtime-fixture")
    args = parser.parse_args()
    selected = CASE_MODULES if args.case == "all" else (args.case,)
    for case in selected:
        path = prepare(case, args.output / case if args.case == "all" else args.output, args.campaign_id)
        print(path)


if __name__ == "__main__":
    main()
