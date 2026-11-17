"""PC2.1 input, typed semantic checking and deterministic RTL development CLI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .inputs import (
    ParseLimits, PcInputError, TrustedContext, TrustedSource,
    assemble_project_contract, parse_project_contract,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("assemble", "check", "validate", "build", "compose"))
    parser.add_argument("--input", type=Path, required=True,
                        help="Model design for assemble; complete PC for check")
    for name in ("requirements", "target-profile", "capability-profile"):
        parser.add_argument(f"--{name}", type=Path, required=True)
        parser.add_argument(f"--{name}-id", required=True,
                            help="Controller-selected public source identity")
    parser.add_argument("--max-bytes", type=int, required=True)
    parser.add_argument("--max-depth", type=int, required=True)
    parser.add_argument("--output", type=Path,
                        help="New PC file (assemble), or fresh artifacts directory (build/compose)")
    parser.add_argument("--asset-root", type=Path, help="Operator-selected public asset directory")
    parser.add_argument("--behavior-bundle", type=Path, help="Body-only proposal for compose")
    args = parser.parse_args(argv)
    writes = args.operation in {"assemble", "build", "compose"}
    if writes != (args.output is not None):
        parser.error("assemble/build/compose require --output; check/validate do not accept it")
    if (args.operation == "compose") != (args.behavior_bundle is not None):
        parser.error("compose requires --behavior-bundle; other operations do not accept it")
    try:
        limits = ParseLimits(args.max_bytes, args.max_depth)
        # Bound candidate loading before decoding. Trusted source bytes are
        # selected explicitly by the operator, not read from candidate bindings.
        with args.input.open("rb") as handle:
            raw = handle.read(limits.max_bytes + 1)
        context = TrustedContext(**{
            name: TrustedSource(getattr(args, f"{name}_id"),
                                getattr(args, name).read_bytes())
            for name in ("requirements", "target_profile", "capability_profile")
        })
        if args.operation == "assemble":
            pc = assemble_project_contract(raw, context, limits=limits)
            encoded = (json.dumps(pc, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
            # Use the same admission rules on the saved object; bindings and
            # formatting may make the assembled object larger than its design.
            parse_project_contract(encoded, context, limits=limits)
            with args.output.open("xb") as handle:
                handle.write(encoded)
        else:
            pc = parse_project_contract(raw, context, limits=limits)
        if args.operation in {"validate", "build", "compose"}:
            from dataclasses import asdict
            from sr2fpga_agent.contract_registry import ContractRegistry
            from sr2fpga_agent.repository_paths import RepositoryPaths
            from .context import check_task_design, load_public_task
            task = load_public_task(context, asset_root=args.asset_root, limits=limits)
            checked = check_task_design(pc["design"], task)
            receipt = {
                "pc_format": "sr2fpga-pc-2.1", "input_schema_and_bindings": "pass",
                "semantic_validation": "pass", "scope": checked.scope,
                "deferred_checks": checked.deferred_checks,
                "rtl_construction": "not_run", "functional_correctness": "not_evaluated",
            }
            if args.operation in {"build", "compose"}:
                from .emitter import build_structure, compose_behavior, write_project
                from .inputs import _parse, _validate
                output = args.output.resolve()
                artifact_root = (RepositoryPaths.discover().root / "artifacts").resolve()
                if not output.is_relative_to(artifact_root) or output == artifact_root:
                    raise ValueError("build output must be a fresh directory below artifacts/")
                if output.exists():
                    raise ValueError("output directory already exists")
                build = build_structure(checked, bindings=pc["bindings"],
                                        toolchain_id=task.target["target_id"])
                if args.operation == "compose":
                    with args.behavior_bundle.open("rb") as handle:
                        bundle = _parse(handle.read(limits.max_bytes + 1), limits)
                    _validate(bundle, "pc21_behavior_bundle", ContractRegistry())
                    project = compose_behavior(build, bundle,
                                               timeout_seconds=task.target["tool_timeout_seconds"],
                                               scratch_root=output.parent / (output.name + "-parser"))
                    write_project(project, output)
                    (output / "construction-origin-map.json").write_text(
                        json.dumps(project.construction_origin_map, indent=2) + "\n", encoding="utf-8")
                    (output / "parser-evidence.json").write_text(
                        json.dumps(project.parser_evidence, indent=2) + "\n", encoding="utf-8")
                    receipt["rtl_construction"] = "composed_and_parsed"
                else:
                    output.mkdir(parents=True)
                    for path, content in build.files.items():
                        target = output / path
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_text(content, encoding="utf-8")
                    (output / "build-plan.json").write_text(
                        json.dumps(asdict(build), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                    receipt["rtl_construction"] = "structure_only_behavior_required"
                receipt["build_plan_sha256"] = build.build_plan_sha256
            print(json.dumps(receipt))
            return 0
    except (PcInputError, OSError, ValueError) as error:
        parser.exit(2, f"PC2.1 input rejected: {error}\n")
    print(json.dumps({
        "pc_format": "sr2fpga-pc-2.1",
        "input_schema_and_bindings": "pass",
        "semantic_validation": "partial",
        "semantic_checks": {
            "entry_module_exists": "pass",
            "instance_modules_exist": "pass",
            "module_hierarchy_acyclic": "pass",
            "all_modules_reachable": "pass",
            "signature_sources_valid": "pass",
            "instance_parameter_names_valid": "pass",
            "instance_parameter_bindings_complete": "pass",
        },
        "rtl_construction": "not_run",
        "scope": "development_input_validation",
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
