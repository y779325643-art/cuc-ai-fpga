"""Command-line entry point for the SR2FPGA data generation agent."""

from __future__ import annotations

import argparse
from pathlib import Path

from LLM.src.sr2fpga_agent.agent import DataGenerationAgent
from LLM.src.sr2fpga_agent.models import PlatformProfile, ProjectRequest


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate one SR2FPGA RTL dataset sample.")
    parser.add_argument("--dataset-root", required=True, type=Path)
    parser.add_argument("--sample-id", required=True)
    parser.add_argument("--task-type", default="counter")
    parser.add_argument("--width", default=8, type=int)
    parser.add_argument("--project-name", required=True)
    parser.add_argument("--requirement", default="")
    parser.add_argument("--platform", default="generic_verilog")
    args = parser.parse_args()

    requirement = args.requirement or f"Design a {args.width}-bit counter with enable and active-low reset."
    result = DataGenerationAgent(args.dataset_root).run_one(
        sample_id=args.sample_id,
        requirement=requirement,
        request=ProjectRequest(task_type=args.task_type, width=args.width, project_name=args.project_name),
        platform=PlatformProfile(name=args.platform, vendor="generic", toolchain="open_source"),
    )
    print(f"sample_dir={result['sample_dir']}")
    print(f"pass_level={result['pass_level']}")


if __name__ == "__main__":
    main()
