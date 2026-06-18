"""Command-line entry point for the SR2FPGA data generation agent."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from LLM.src.sr2fpga_agent.agent import DataGenerationAgent
from LLM.src.sr2fpga_agent.deepseek import DeepSeekClient, DeepSeekConfig, DeepSeekProjectGenerator
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
    parser.add_argument("--provider", choices=["deterministic", "deepseek"], default="deterministic")
    parser.add_argument("--model", default="deepseek-v4-flash")
    parser.add_argument("--base-url", default="https://api.deepseek.com")
    parser.add_argument("--api-key-env", default="DEEPSEEK_API_KEY")
    args = parser.parse_args()

    requirement = args.requirement or f"Design a {args.width}-bit counter with enable and active-low reset."
    project_generator = build_project_generator(
        provider=args.provider,
        model=args.model,
        base_url=args.base_url,
        api_key_env=args.api_key_env,
    )
    result = DataGenerationAgent(args.dataset_root, project_generator=project_generator).run_one(
        sample_id=args.sample_id,
        requirement=requirement,
        request=ProjectRequest(task_type=args.task_type, width=args.width, project_name=args.project_name),
        platform=PlatformProfile(name=args.platform, vendor="generic", toolchain="open_source"),
    )
    print(f"sample_dir={result['sample_dir']}")
    print(f"pass_level={result['pass_level']}")


def build_project_generator(
    provider: str,
    model: str,
    base_url: str,
    api_key_env: str,
):
    if provider == "deterministic":
        return None
    if provider == "deepseek":
        api_key = os.environ.get(api_key_env)
        if not api_key:
            raise SystemExit(f"{api_key_env} is not set")
        return DeepSeekProjectGenerator(
            DeepSeekClient(
                DeepSeekConfig(
                    api_key=api_key,
                    model=model,
                    base_url=base_url,
                )
            )
        )
    raise SystemExit(f"Unsupported provider: {provider}")


if __name__ == "__main__":
    main()
