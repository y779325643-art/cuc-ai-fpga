"""Command-line entry point for the SR2FPGA data generation agent."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from LLM.src.sr2fpga_agent.agent import DataGenerationAgent
from LLM.src.sr2fpga_agent.deepseek import (
    AnthropicCompatibleClient,
    AnthropicCompatibleConfig,
    DeepSeekOracleHisProjectGenerator,
    DeepSeekTwoStageProjectGenerator,
    DeepSeekProjectGenerator,
    DeepSeekRepairer,
    OpenAICompatibleClient,
    OpenAICompatibleConfig,
)
from LLM.src.sr2fpga_agent.models import PlatformProfile, ProjectRequest


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Generate one SR2FPGA RTL dataset sample.")
    parser.add_argument("--dataset-root", required=True, type=Path)
    parser.add_argument("--sample-id", required=True)
    parser.add_argument("--task-type", default="counter")
    parser.add_argument("--width", default=8, type=int)
    parser.add_argument("--project-name", required=True)
    parser.add_argument("--requirement", default="")
    parser.add_argument("--platform", default="generic_verilog")
    parser.add_argument("--provider", choices=["deterministic", "deepseek", "deepseek-his-v12"], default="deterministic")
    parser.add_argument("--model", default="deepseek-v4-pro")
    parser.add_argument("--base-url", default="https://api.deepseek.com")
    parser.add_argument("--api-key-env", default="DEEPSEEK_API_KEY")
    parser.add_argument("--repair-provider", choices=["none", "deepseek"], default="none")
    parser.add_argument("--max-attempts", default=1, type=int)
    args = parser.parse_args(argv)

    if args.max_attempts < 1:
        raise SystemExit("--max-attempts must be >= 1")

    requirement = args.requirement or f"Design a {args.width}-bit {args.task_type} RTL block with active-low reset."
    project_generator = build_project_generator(
        provider=args.provider,
        model=args.model,
        base_url=args.base_url,
        api_key_env=args.api_key_env,
    )
    repairer = build_repairer(
        provider=args.repair_provider,
        model=args.model,
        base_url=args.base_url,
        api_key_env=args.api_key_env,
    )
    result = DataGenerationAgent(
        args.dataset_root,
        project_generator=project_generator,
        repairer=repairer,
        max_attempts=args.max_attempts,
    ).run_one(
        sample_id=args.sample_id,
        requirement=requirement,
        request=ProjectRequest(
            task_type=args.task_type,
            width=args.width,
            project_name=args.project_name,
            description=requirement,
        ),
        platform=PlatformProfile(name=args.platform, vendor="generic", toolchain="open_source"),
    )
    print(f"sample_dir={result['sample_dir']}")
    print(f"pass_level={result['pass_level']}")


def build_project_generator(
    provider: str,
    model: str,
    base_url: str,
    api_key_env: str,
    event_sink=None,
):
    if provider == "deterministic":
        return None
    if provider == "deepseek":
        api_key = os.environ.get(api_key_env)
        if not api_key:
            raise SystemExit(f"{api_key_env} is not set")
        return DeepSeekProjectGenerator(
            OpenAICompatibleClient(
                OpenAICompatibleConfig(
                    api_key=api_key,
                    model=model,
                    base_url=base_url,
                )
            )
        )
    if provider == "deepseek-his-v12":
        api_key = os.environ.get(api_key_env)
        if not api_key:
            raise SystemExit(f"{api_key_env} is not set")
        return DeepSeekTwoStageProjectGenerator(
            OpenAICompatibleClient(
                OpenAICompatibleConfig(
                    api_key=api_key,
                    model=model,
                    base_url=base_url,
                )
            ),
            event_sink=event_sink,
        )
    raise SystemExit(f"Unsupported provider: {provider}")


def build_project_generator_for_connection(connection, event_sink=None):
    kind = connection.kind
    if kind == "deterministic":
        return None
    if kind not in {"openai_compat", "anthropic_compat", "deepseek", "deepseek-his-v12", "deepseek-oracle-his-v12"}:
        raise SystemExit(f"Unsupported source kind: {kind}")
    api_key = os.environ.get(connection.api_key_env)
    if not api_key:
        raise SystemExit(f"{connection.api_key_env} is not set")
    if kind == "anthropic_compat":
        client = AnthropicCompatibleClient(
            AnthropicCompatibleConfig(
                api_key=api_key,
                model=connection.model,
                base_url=connection.base_url,
                timeout_seconds=getattr(connection, "timeout_seconds", 120),
                max_tokens=getattr(connection, "max_tokens", 0) or 16384,
                transport_attempts=getattr(connection, "transport_attempts", 3),
            )
        )
        return DeepSeekTwoStageProjectGenerator(client, event_sink=event_sink)
    client = OpenAICompatibleClient(
        OpenAICompatibleConfig(
            api_key=api_key,
            model=connection.model,
            base_url=connection.base_url,
            timeout_seconds=getattr(connection, "timeout_seconds", 120),
            max_tokens=getattr(connection, "max_tokens", 0),
            transport_attempts=getattr(connection, "transport_attempts", 3),
        )
    )
    if kind == "deepseek":
        return DeepSeekProjectGenerator(client)
    if kind == "deepseek-oracle-his-v12":
        return DeepSeekOracleHisProjectGenerator(client, event_sink=event_sink)
    return DeepSeekTwoStageProjectGenerator(client, event_sink=event_sink)


def build_repairer(
    provider: str,
    model: str,
    base_url: str,
    api_key_env: str,
):
    if provider == "none":
        return None
    if provider == "deepseek":
        api_key = os.environ.get(api_key_env)
        if not api_key:
            raise SystemExit(f"{api_key_env} is not set")
        return DeepSeekRepairer(
            OpenAICompatibleClient(
                OpenAICompatibleConfig(
                    api_key=api_key,
                    model=model,
                    base_url=base_url,
                )
            )
        )
    raise SystemExit(f"Unsupported repair provider: {provider}")


def build_repairer_for_connection(connection):
    kind = connection.kind
    if kind == "deterministic":
        return None
    if kind not in {"openai_compat", "anthropic_compat", "deepseek", "deepseek-his-v12"}:
        raise SystemExit(f"Unsupported repair source kind: {kind}")
    api_key = os.environ.get(connection.api_key_env)
    if not api_key:
        raise SystemExit(f"{connection.api_key_env} is not set")
    if kind == "anthropic_compat":
        client = AnthropicCompatibleClient(
            AnthropicCompatibleConfig(
                api_key=api_key,
                model=connection.model,
                base_url=connection.base_url,
                timeout_seconds=getattr(connection, "timeout_seconds", 120),
                transport_attempts=getattr(connection, "transport_attempts", 3),
                max_tokens=getattr(connection, "max_tokens", 16384) or 16384,
            )
        )
        return DeepSeekRepairer(client)
    client = OpenAICompatibleClient(
        OpenAICompatibleConfig(
            api_key=api_key,
            model=connection.model,
            base_url=connection.base_url,
            timeout_seconds=getattr(connection, "timeout_seconds", 120),
            transport_attempts=getattr(connection, "transport_attempts", 3),
            max_tokens=getattr(connection, "max_tokens", 0),
        )
    )
    return DeepSeekRepairer(client)


if __name__ == "__main__":
    main()
