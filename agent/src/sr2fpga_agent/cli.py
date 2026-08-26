"""Command-line entry point for the SR2FPGA data generation agent."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from sr2fpga_agent.agent import DataGenerationAgent
from sr2fpga_agent.family_recipe import select_family_recipe
from sr2fpga_agent.frozen_context import (
    build_development_episode_pack,
    context_from_validated_episode_pack,
    freeze_ready_requirement_context,
)
from sr2fpga_agent.generation import (
    DirectProjectGenerator,
    FrozenContextDirectProjectGenerator,
    OracleHisProjectGenerator,
    TwoStageProjectGenerator,
)
from sr2fpga_agent.providers import (
    AnthropicCompatibleClient,
    AnthropicCompatibleConfig,
    OpenAICompatibleClient,
    OpenAICompatibleConfig,
)
from sr2fpga_agent.repair import ProjectRepairer
from sr2fpga_agent.requirement_boundary import evaluate_requirement_boundary
from sr2fpga_agent.models import PlatformProfile, ProjectRequest
from sr2fpga_agent.model_budget import ModelCallBudget


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Generate one SR2FPGA RTL dataset sample.")
    parser.add_argument("--dataset-root", required=True, type=Path)
    parser.add_argument("--sample-id", required=True)
    parser.add_argument("--task-type")
    parser.add_argument("--width", default=8, type=int)
    parser.add_argument("--project-name", required=True)
    parser.add_argument("--requirement", default="")
    parser.add_argument("--platform", default="generic_verilog")
    parser.add_argument(
        "--provider",
        choices=["deterministic", "deepseek", "deepseek-his-v12", "openai_compat"],
        default="deterministic",
    )
    parser.add_argument("--model", default="deepseek-v4-pro")
    parser.add_argument("--base-url", default="https://api.deepseek.com")
    parser.add_argument("--api-key-env", default="DEEPSEEK_API_KEY")
    parser.add_argument("--repair-provider", choices=["none", "deepseek"], default="none")
    parser.add_argument("--max-attempts", default=1, type=int)
    parser.add_argument("--decoding-seed", type=int)
    parser.add_argument(
        "--max-model-calls",
        default=0,
        type=int,
        help="Per-sample global model-call ceiling; 0 derives the method-matched ceiling",
    )
    args = parser.parse_args(argv)

    if args.max_attempts < 1:
        raise SystemExit("--max-attempts must be >= 1")
    if args.max_model_calls < 0:
        raise SystemExit("--max-model-calls must be >= 0")
    if args.decoding_seed is not None and args.decoding_seed < 0:
        raise SystemExit("--decoding-seed must be >= 0")
    if args.provider == "deterministic" and not args.task_type:
        raise SystemExit("--task-type is required when --provider deterministic is selected")

    task_type = args.task_type or "unclassified"
    requirement = args.requirement or f"Generate an {args.width}-bit {task_type} FPGA RTL project."
    request = ProjectRequest(
        task_type=task_type,
        width=args.width,
        project_name=args.project_name,
        description=requirement,
    )
    platform = PlatformProfile(name=args.platform, vendor="generic", toolchain="open_source")
    boundary = evaluate_requirement_boundary(request, platform)
    method_condition = _cli_method_condition(
        args.provider,
        repair_enabled=args.repair_provider != "none" and args.max_attempts > 1,
    )
    model_call_ceiling = args.max_model_calls or _default_model_call_ceiling(
        method_condition,
        args.max_attempts,
    )
    model_budget = ModelCallBudget(model_call_ceiling)
    metadata = {
        "analysis_population": "development",
        "method_condition": method_condition,
        "requirement_boundary": boundary.to_dict(),
        "model_call_budget": model_budget.summary(),
    }
    if boundary.disposition == "ready" and method_condition in {"M0", "M1", "M4", "M5"}:
        context = freeze_ready_requirement_context(boundary, platform)
        metadata["episode_pack"] = build_development_episode_pack(
            context,
            episode_id=args.sample_id,
            analysis_population="development",
            method_condition=method_condition,
            evaluator_metadata={"task_type": task_type},
        ).to_dict()
    if boundary.disposition == "ready" and args.provider in {"deepseek-his-v12", "openai_compat"}:
        metadata["family_recipe_decision"] = select_family_recipe(
            request,
            boundary.envelope,
        ).to_dict()
    project_generator = None
    repairer = None
    if boundary.disposition == "ready":
        project_generator = build_project_generator(
            provider=args.provider,
            model=args.model,
            base_url=args.base_url,
            api_key_env=args.api_key_env,
            model_budget=model_budget,
            decoding_seed=args.decoding_seed,
        )
        if method_condition in {"M0", "M1"} and isinstance(
            project_generator, DirectProjectGenerator
        ):
            project_generator = FrozenContextDirectProjectGenerator(
                project_generator.client,
                context_from_validated_episode_pack(metadata["episode_pack"]),
            )
        repairer = build_repairer(
            provider=args.repair_provider,
            model=args.model,
            base_url=args.base_url,
            api_key_env=args.api_key_env,
            model_budget=model_budget,
            decoding_seed=args.decoding_seed,
        )
    result = DataGenerationAgent(
        args.dataset_root,
        project_generator=project_generator,
        repairer=repairer,
        max_attempts=args.max_attempts,
    ).run_one(
        sample_id=args.sample_id,
        requirement=requirement,
        request=request,
        platform=platform,
        metadata=metadata,
    )
    _write_model_budget_summary(args.dataset_root, args.sample_id, model_budget.summary())
    print(f"sample_dir={result['sample_dir']}")
    print(f"pass_level={result['pass_level']}")
    if result.get("failure_type"):
        print(f"failure_type={result['failure_type']}")
    for index, question in enumerate(result.get("questions", []), start=1):
        print(f"clarification_{index}={question}")
    if result.get("capability_gaps"):
        print("capability_gaps=" + ",".join(result["capability_gaps"]))


def _cli_method_condition(provider: str, *, repair_enabled: bool) -> str:
    if provider == "deterministic":
        return "reference_deterministic"
    if provider == "deepseek":
        return "M1" if repair_enabled else "M0"
    return "M5" if repair_enabled else "M4"


def _default_model_call_ceiling(method_condition: str, max_attempts: int) -> int:
    if method_condition == "reference_deterministic":
        return 0
    if method_condition in {"M0", "M1"}:
        return max_attempts
    if method_condition in {"M4", "M5"}:
        return 2 + max(0, max_attempts - 1)
    raise SystemExit(f"No model-call allocation is implemented for {method_condition}")


def _write_model_budget_summary(dataset_root: Path, sample_id: str, summary: dict) -> None:
    metadata_path = dataset_root / sample_id / "metadata.json"
    if not metadata_path.exists():
        return
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    payload["model_call_budget"] = summary
    metadata_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def build_project_generator(
    provider: str,
    model: str,
    base_url: str,
    api_key_env: str,
    event_sink=None,
    model_budget: ModelCallBudget | None = None,
    decoding_seed: int | None = None,
):
    if provider == "deterministic":
        return None
    if provider == "deepseek":
        api_key = os.environ.get(api_key_env)
        if not api_key:
            raise SystemExit(f"{api_key_env} is not set")
        client = OpenAICompatibleClient(
                OpenAICompatibleConfig(
                    api_key=api_key,
                    model=model,
                    base_url=base_url,
                    seed=decoding_seed,
                )
            )
        if model_budget is not None:
            client = model_budget.client(client, "direct_project")
        return DirectProjectGenerator(client, max_attempts=1)
    if provider in {"deepseek-his-v12", "openai_compat"}:
        api_key = os.environ.get(api_key_env)
        if not api_key:
            raise SystemExit(f"{api_key_env} is not set")
        client = OpenAICompatibleClient(
                OpenAICompatibleConfig(
                    api_key=api_key,
                    model=model,
                    base_url=base_url,
                    seed=decoding_seed,
                )
            )
        if model_budget is not None:
            client = model_budget.client(client, "two_stage")
        return TwoStageProjectGenerator(
            client,
            max_attempts=1,
            event_sink=event_sink,
        )
    raise SystemExit(f"Unsupported provider: {provider}")


def build_project_generator_for_connection(
    connection,
    event_sink=None,
    model_budget=None,
    decoding_seed: int | None = None,
):
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
                requested_seed=decoding_seed,
            )
        )
        if model_budget is not None:
            client = model_budget.client(client, "two_stage")
        return TwoStageProjectGenerator(client, max_attempts=1, event_sink=event_sink)
    client = OpenAICompatibleClient(
        OpenAICompatibleConfig(
            api_key=api_key,
            model=connection.model,
            base_url=connection.base_url,
            timeout_seconds=getattr(connection, "timeout_seconds", 120),
            max_tokens=getattr(connection, "max_tokens", 0),
            transport_attempts=getattr(connection, "transport_attempts", 3),
            seed=decoding_seed,
        )
    )
    if model_budget is not None:
        client = model_budget.client(
            client,
            "direct_project" if kind == "deepseek" else "two_stage",
        )
    if kind == "deepseek":
        return DirectProjectGenerator(client, max_attempts=1)
    if kind == "deepseek-oracle-his-v12":
        return OracleHisProjectGenerator(client, event_sink=event_sink)
    return TwoStageProjectGenerator(client, max_attempts=1, event_sink=event_sink)


def build_repairer(
    provider: str,
    model: str,
    base_url: str,
    api_key_env: str,
    model_budget: ModelCallBudget | None = None,
    decoding_seed: int | None = None,
):
    if provider == "none":
        return None
    if provider == "deepseek":
        api_key = os.environ.get(api_key_env)
        if not api_key:
            raise SystemExit(f"{api_key_env} is not set")
        client = OpenAICompatibleClient(
                OpenAICompatibleConfig(
                    api_key=api_key,
                    model=model,
                    base_url=base_url,
                    seed=decoding_seed,
                )
            )
        if model_budget is not None:
            client = model_budget.client(client, "project_repair")
        return ProjectRepairer(client, max_attempts=1)
    raise SystemExit(f"Unsupported repair provider: {provider}")


def build_repairer_for_connection(
    connection,
    model_budget=None,
    decoding_seed: int | None = None,
):
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
                requested_seed=decoding_seed,
            )
        )
        if model_budget is not None:
            client = model_budget.client(client, "project_repair")
        return ProjectRepairer(client, max_attempts=1)
    client = OpenAICompatibleClient(
        OpenAICompatibleConfig(
            api_key=api_key,
            model=connection.model,
            base_url=connection.base_url,
            timeout_seconds=getattr(connection, "timeout_seconds", 120),
            transport_attempts=getattr(connection, "transport_attempts", 3),
            max_tokens=getattr(connection, "max_tokens", 0),
            seed=decoding_seed,
        )
    )
    if model_budget is not None:
        client = model_budget.client(client, "project_repair")
    return ProjectRepairer(client, max_attempts=1)


if __name__ == "__main__":
    main()
