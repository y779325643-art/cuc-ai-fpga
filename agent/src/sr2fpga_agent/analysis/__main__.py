"""Offline manifest validation, cluster analysis and synthetic code checks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from sr2fpga_agent.repository_paths import RepositoryPaths
from sr2fpga_agent.contract_registry import ContractRegistry

from .core import AnalysisInputError, AnalysisPolicy, analyze, validate_dataset
from .simulation import simulate


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise AnalysisInputError("duplicate JSON key")
        result[key] = value
    return result


def _nonfinite(value: str):
    raise AnalysisInputError("nonfinite JSON number: " + value)


def _load(path: Path) -> Any:
    with path.open("rb") as stream:
        raw = stream.read(64_000_001)
    if len(raw) > 64_000_000:
        raise AnalysisInputError("analysis input exceeds 64MB local read bound")
    return json.loads(
        raw.decode("utf-8"), object_pairs_hook=_pairs, parse_constant=_nonfinite
    )


def _write(output: Path | None, value: dict[str, Any]) -> None:
    if value.get("contract_version") == "pc21-cluster-analysis-v1":
        errors = ContractRegistry().load_schema("pc21_cluster_analysis").validate(value)
        if errors:
            raise AnalysisInputError("analysis report contract rejected: " + "; ".join(errors))
    encoded = json.dumps(value, ensure_ascii=True, allow_nan=False, indent=2) + "\n"
    if output is None:
        print(encoded, end="")
        return
    root = (RepositoryPaths.discover().root / "artifacts").resolve()
    destination = output.resolve()
    if destination == root or not destination.is_relative_to(root):
        raise AnalysisInputError(
            "analysis output must be a fresh file below artifacts/"
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("x", encoding="utf-8") as stream:
        stream.write(encoded)
    print(json.dumps({"output": str(destination), "official": False, "model_calls": 0}))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="operation", required=True)
    for name in ("validate", "analyze"):
        command = commands.add_parser(name)
        command.add_argument("--manifest", type=Path, required=True)
        command.add_argument(
            "--results", type=Path, required=True, help="JSON list of result rows"
        )
        if name == "analyze":
            command.add_argument("--policy", type=Path, required=True)
        command.add_argument("--output", type=Path)
    synthetic = commands.add_parser("simulate")
    synthetic.add_argument("--policy", type=Path, required=True)
    synthetic.add_argument("--trials", type=int, default=20)
    synthetic.add_argument("--clusters-per-family", type=int, default=8)
    synthetic.add_argument("--configurations", type=int, default=1)
    synthetic.add_argument("--replicates", type=int, default=2)
    synthetic.add_argument("--seed", type=int, default=0)
    synthetic.add_argument("--boundary-null", action="store_true")
    synthetic.add_argument("--baseline-probability", type=float, default=0.4)
    synthetic.add_argument("--cluster-heterogeneity", type=float, default=0.2)
    synthetic.add_argument("--missing-probability", type=float, default=0)
    synthetic.add_argument("--effect-heterogeneity", type=float, default=0)
    synthetic.add_argument("--shared-pair-fraction", type=float, default=0)
    synthetic.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        registry = ContractRegistry()
        if args.operation == "simulate":
            policy = _load(args.policy)
            errors = registry.load_schema("pc21_analysis_policy").validate(policy)
            if errors:
                raise AnalysisInputError("; ".join(errors))
            report = simulate(
                AnalysisPolicy.from_dict(policy),
                trials=args.trials,
                clusters_per_family=args.clusters_per_family,
                configurations=args.configurations,
                replicates=args.replicates,
                seed=args.seed,
                boundary_null=args.boundary_null,
                baseline_probability=args.baseline_probability,
                cluster_heterogeneity=args.cluster_heterogeneity,
                missing_probability=args.missing_probability,
                effect_heterogeneity=args.effect_heterogeneity,
                shared_pair_fraction=args.shared_pair_fraction,
            )
        else:
            manifest, result_document = _load(args.manifest), _load(args.results)
            for key, document in (
                ("pc21_analysis_manifest", manifest),
                ("pc21_analysis_results", result_document),
            ):
                errors = registry.load_schema(key).validate(document)
                if errors:
                    raise AnalysisInputError("; ".join(errors))
            results = result_document["results"]
            if "manifest_sha256" in result_document:
                observed = validate_dataset(manifest, results).manifest_sha256
                if result_document["manifest_sha256"] != observed:
                    raise AnalysisInputError(
                        "results document manifest binding mismatch"
                    )
            if args.operation == "validate":
                report = {
                    "status": "valid",
                    "official": False,
                    "model_calls": 0,
                    **validate_dataset(manifest, results).summary(),
                }
            else:
                policy = _load(args.policy)
                errors = registry.load_schema("pc21_analysis_policy").validate(policy)
                if errors:
                    raise AnalysisInputError("; ".join(errors))
                report = analyze(manifest, results, AnalysisPolicy.from_dict(policy))
        _write(args.output, report)
    except (AnalysisInputError, OSError, ValueError, TypeError, KeyError) as error:
        parser.exit(2, "analysis rejected: " + str(error) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
