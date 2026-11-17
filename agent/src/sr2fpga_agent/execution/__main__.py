"""Current PC 2.1 preflight and explicitly scoped development/replay execution."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .integration import load_json, preflight, run_development


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="operation", required=True)
    inspect = commands.add_parser("preflight")
    inspect.add_argument("--config", type=Path, action="append", required=True)
    inspect.add_argument("--formal", action="store_true", help="Inspect missing formal prerequisites; never execute")
    run = commands.add_parser("run-development")
    run.add_argument("--config", type=Path, action="append", required=True)
    run.add_argument("--output", type=Path, required=True)
    run.add_argument("--allow-model-calls", action="store_true")
    run.add_argument("--terminal-suite-factory", help="Trusted module:function, imported only after generation closes")
    args = parser.parse_args(argv)
    try:
        configs = [load_json(path) for path in args.config]
        if args.operation == "preflight":
            reports = [preflight(config, formal=args.formal) for config in configs]
            print(json.dumps(reports, ensure_ascii=True))
            return int(any(not item["ready"] for item in reports))
        result = run_development(configs, args.output, allow_model_calls=args.allow_model_calls,
                                 terminal_suite_factory=args.terminal_suite_factory)
        print(json.dumps({"output": str(args.output.resolve()), "official": False,
                          "natural_model_dispatches": result["natural_model_dispatches"],
                          "terminal_evaluation": result["terminal_evaluation"]}))
        return 0
    except (ValueError, OSError, RuntimeError, PermissionError) as error:
        parser.exit(2, "PC2.1 runtime rejected: " + str(error) + "\n")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
