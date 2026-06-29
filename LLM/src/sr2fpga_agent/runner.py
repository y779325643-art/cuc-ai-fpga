"""Autonomous batch runner for SR2FPGA trajectory generation."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from LLM.src.sr2fpga_agent.agent import DataGenerationAgent
from LLM.src.sr2fpga_agent.baseline_report import baseline_rows, render_markdown
from LLM.src.sr2fpga_agent.cli import (
    build_project_generator_for_connection,
    build_repairer,
    build_repairer_for_connection,
)
from LLM.src.sr2fpga_agent.deepseek import (
    AnthropicCompatibleClient,
    AnthropicCompatibleConfig,
    OpenAICompatibleClient,
    OpenAICompatibleConfig,
)
from LLM.src.sr2fpga_agent.failure_injector import FailureInjectingProjectGenerator
from LLM.src.sr2fpga_agent.local_tools import resolve_executable
from LLM.src.sr2fpga_agent.models import PlatformProfile, ProjectRequest
from LLM.src.sr2fpga_agent.project_generator import COMPONENT_TOPOLOGIES, ProjectGenerator
from LLM.src.sr2fpga_agent.recorder import DatasetRecorder
from LLM.src.sr2fpga_agent.testbench_checker import check_testbench_static_issues


VALID_MEASUREMENT_POINTS = {
    "a_first_attempt_no_tools",
    "b_tool_in_loop_repair",
    "c_finetuned_first_attempt_no_tools",
}

VALID_REQUIREMENT_STYLES = {"contract", "natural_component", "simple_prompt"}


@dataclass(frozen=True)
class TaskConfig:
    source: str
    task_type: str
    widths: list[int]
    count: int
    failure_injectors: list[str] = field(default_factory=list)
    difficulty_tier: str = "T1"
    failure_origin: str = ""
    topology_ids: list[str] = field(default_factory=list)
    measurement_point: str = ""
    requirement_style: str = "contract"


@dataclass(frozen=True)
class SourceConnection:
    name: str
    kind: str
    model: str = ""
    base_url: str = ""
    api_key_env: str = ""
    generation_mode: str = ""
    timeout_seconds: int = 120


@dataclass(frozen=True)
class RunnerConfig:
    dataset_root: Path
    export_root: Path
    run_root: Path
    provider: str
    repair_provider: str
    max_attempts: int
    refresh_exports: bool
    line_b_targets: dict[str, float | int]
    tasks: list[TaskConfig]
    model: str = "deepseek-v4-pro"
    base_url: str = "https://api.deepseek.com"
    api_key_env: str = "DEEPSEEK_API_KEY"
    platform: str = "generic_verilog"
    env_file: Path = Path("")
    sample_id_prefix: str = "runner"
    sources: dict[str, "SourceConnection"] = field(default_factory=dict)


@dataclass(frozen=True)
class PlannedSample:
    sample_id: str
    source: str
    task_type: str
    width: int
    project_name: str
    requirement: str
    failure_injectors: list[str] = field(default_factory=list)
    difficulty_tier: str = "T1"
    failure_origin: str = ""
    topology_id: str = ""
    measurement_point: str = ""
    requirement_style: str = "contract"

    def metadata(self, config: RunnerConfig) -> dict[str, Any]:
        connection = resolve_source_connection(config, self.source)
        schema_version = _sample_system_his_schema_version(self, config)
        return {
            "source": self.source,
            "generator_provider": self.source,
            "model": connection.model,
            "failure_origin": _sample_failure_origin(self, config),
            "difficulty_tier": self.difficulty_tier,
            "measurement_point": self.measurement_point or _measurement_point(config),
            "repair_provider": config.repair_provider,
            "failure_injectors": list(self.failure_injectors),
            "task_type": self.task_type,
            "width": self.width,
            "system_his_schema_version": schema_version,
            "training_split": _training_split(schema_version),
            "contract_skeleton_mode": _contract_skeleton_mode(self, config),
            "topology_id": self.topology_id,
            "requirement_style": self.requirement_style,
        }


@dataclass(frozen=True)
class RunState:
    run_id: str
    next_index: int
    completed_samples: list[str]
    buckets: dict[str, list[str]]
    failure_types: dict[str, int]
    exports_refreshed: bool
    config_fingerprint: str = ""


def load_runner_config(path: Path) -> RunnerConfig:
    raw = _load_mapping(path)
    return RunnerConfig(
        dataset_root=Path(str(raw["dataset_root"])),
        export_root=Path(str(raw["export_root"])),
        run_root=Path(str(raw["run_root"])),
        provider=str(raw.get("provider", "deterministic")),
        repair_provider=str(raw.get("repair_provider", "none")),
        max_attempts=int(raw.get("max_attempts", 1)),
        refresh_exports=_parse_bool(raw.get("refresh_exports", True), "refresh_exports"),
        line_b_targets=dict(raw.get("line_b_targets", {})),
        tasks=[_load_task_config(item, raw) for item in raw.get("tasks", [])],
        model=str(raw.get("model", "deepseek-v4-pro")),
        base_url=str(raw.get("base_url", "https://api.deepseek.com")),
        api_key_env=str(raw.get("api_key_env", "DEEPSEEK_API_KEY")),
        platform=str(raw.get("platform", "generic_verilog")),
        env_file=Path(str(raw.get("env_file", ""))),
        sample_id_prefix=str(raw.get("sample_id_prefix", "runner")),
        sources=_load_sources(raw.get("sources", {})),
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run an autonomous SR2FPGA trajectory batch.")
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--run-id", default="")
    parser.add_argument("--no-resume", action="store_true")
    parser.add_argument("--preflight", action="store_true", help="Check runner readiness without generating samples")
    parser.add_argument(
        "--validate-provider",
        action="store_true",
        help="During preflight, make a minimal provider auth request without generating samples",
    )
    args = parser.parse_args(argv)

    config = load_runner_config(args.config)
    if args.preflight:
        report = runner_preflight(config, run_id=args.run_id or None, validate_provider=args.validate_provider)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        if not report["ok"]:
            raise SystemExit(1)
        return
    summary = run_batch(config, run_id=args.run_id or None, resume=not args.no_resume)
    print(f"run_id={summary['run_id']}")
    print(f"total_completed={summary['total_completed']}")
    print(f"success_l3={len(summary['buckets'].get('success_l3', []))}")
    print(f"repair_trajectory={len(summary['buckets'].get('repair_trajectory', []))}")
    print(f"rejected={len(summary['buckets'].get('rejected', []))}")


def runner_preflight(
    config: RunnerConfig,
    run_id: str | None = None,
    validate_provider: bool = False,
) -> dict[str, Any]:
    """Check whether a runner config is ready to launch without creating samples."""
    loaded_env_keys = _load_env_file(config.env_file)
    samples = planned_samples(config)
    run_dir = config.run_root / run_id if run_id else None
    required_tools = ("verilator", "iverilog", "vvp", "yosys")
    tools = _discover_tool_statuses(required_tools)
    errors: list[str] = []
    warnings: list[str] = []

    missing_tools = [tool for tool, status in tools.items() if status == "missing"]
    if missing_tools:
        warnings.append("missing HDL tools: " + ", ".join(missing_tools))

    if run_dir is not None and run_dir.exists():
        warnings.append("run directory already exists: " + str(run_dir))

    if not samples:
        errors.append("no planned samples")
    provider_auth, auth_errors = _source_auth_diagnostics(config, samples, validate_provider)
    errors.extend(auth_errors)

    providers = {sample.source for sample in samples}
    providers.add(config.repair_provider)

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "planned_samples": len(samples),
        "samples": [_preflight_sample_preview(sample, config) for sample in samples],
        "run_dir": str(run_dir) if run_dir is not None else "",
        "tools": tools,
        "providers": sorted(provider for provider in providers if provider),
        "env_file": _env_file_label(config.env_file),
        "api_keys": _api_key_diagnostics(config, loaded_env_keys),
        "provider_auth": provider_auth,
    }


def _preflight_sample_preview(sample: PlannedSample, config: RunnerConfig) -> dict[str, Any]:
    metadata = sample.metadata(config)
    return {
        "sample_id": sample.sample_id,
        "source": sample.source,
        "task_type": sample.task_type,
        "width": sample.width,
        "requirement_style": str(metadata["requirement_style"]),
        "requirement": sample.requirement,
        "difficulty_tier": str(metadata["difficulty_tier"]),
        "topology_id": str(metadata["topology_id"]),
        "failure_origin": str(metadata["failure_origin"]),
        "measurement_point": str(metadata["measurement_point"]),
        "system_his_schema_version": str(metadata["system_his_schema_version"]),
        "training_split": str(metadata["training_split"]),
        "contract_skeleton_mode": str(metadata["contract_skeleton_mode"]),
    }


def _discover_tool_statuses(tools: tuple[str, ...]) -> dict[str, str]:
    statuses: dict[str, str] = {}
    for tool in tools:
        statuses[tool] = "found" if shutil.which(tool) or resolve_executable(tool) else "missing"
    return statuses


def run_batch(config: RunnerConfig, run_id: str | None = None, resume: bool = True) -> dict[str, Any]:
    _load_env_file(config.env_file)
    if run_id is None:
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = config.run_root / run_id
    state_path = run_dir / "run_state.json"
    events_path = run_dir / "events.jsonl"
    summary_path = run_dir / "summary.json"
    config_fingerprint = _config_fingerprint(config)
    run_dir.mkdir(parents=True, exist_ok=True)

    if resume and state_path.exists():
        state = read_run_state(state_path)
        if state.config_fingerprint and state.config_fingerprint != config_fingerprint:
            raise SystemExit(
                f"Run config fingerprint mismatch for {run_id}: "
                f"existing {state.config_fingerprint}, current {config_fingerprint}"
            )
    else:
        state = initial_run_state(run_id, config_fingerprint=config_fingerprint)
        write_run_state(state_path, state)

    _write_json(run_dir / "config.json", _config_to_jsonable(config))

    samples = planned_samples(config)
    project_generators: dict[str, object | None] = {}
    repairer = _repairer_for_config(config)

    for index, sample in enumerate(samples):
        if index < state.next_index or should_skip_sample(state, sample.sample_id):
            continue
        if (config.dataset_root / sample.sample_id).exists():
            state = _record_rejected(state, sample.sample_id, index + 1, "sample_exists")
            _append_event(events_path, {"event": "sample_exists", "sample_id": sample.sample_id})
            write_run_state(state_path, state)
            continue

        sample_project_generator = _project_generator_for_sample(project_generators, config, sample, events_path)
        agent = DataGenerationAgent(
            config.dataset_root,
            project_generator=sample_project_generator,
            repairer=repairer,
            max_attempts=config.max_attempts,
        )
        result = agent.run_one(
            sample_id=sample.sample_id,
            requirement=sample.requirement,
            request=ProjectRequest(
                task_type=sample.task_type,
                width=sample.width,
                project_name=sample.project_name,
                description=sample.requirement,
            ),
            platform=PlatformProfile(name=config.platform, vendor="generic", toolchain="open_source"),
            metadata=sample.metadata(config),
        )
        labels = _read_labels(config.dataset_root / sample.sample_id)
        bucket = classify_sample_bucket(labels)
        state = _record_completed(state, sample.sample_id, index + 1, bucket, config.dataset_root / sample.sample_id)
        _append_event(
            events_path,
            {
                "event": "sample_completed",
                "sample_id": sample.sample_id,
                "source": sample.source,
                "failure_origin": _sample_failure_origin(sample, config),
                "difficulty_tier": sample.difficulty_tier,
                "task_type": sample.task_type,
                "width": sample.width,
                "pass_level": result["pass_level"],
                "bucket": bucket,
            },
        )
        write_run_state(state_path, state)

    if config.refresh_exports:
        DatasetRecorder(config.dataset_root).export_training_views(config.export_root)
        state = RunState(
            run_id=state.run_id,
            next_index=state.next_index,
            completed_samples=state.completed_samples,
            buckets=state.buckets,
            failure_types=state.failure_types,
            exports_refreshed=True,
            config_fingerprint=state.config_fingerprint,
        )
        write_run_state(state_path, state)

    summary = _summary(config, state)
    _write_json(summary_path, summary)
    (run_dir / "baseline_report.md").write_text(
        render_markdown(str(summary["run_id"]), baseline_rows(summary), summary=summary),
        encoding="utf-8",
    )
    return summary


def initial_run_state(run_id: str, config_fingerprint: str = "") -> RunState:
    return RunState(
        run_id=run_id,
        next_index=0,
        completed_samples=[],
        buckets={"success_l3": [], "repair_trajectory": [], "rejected": []},
        failure_types={},
        exports_refreshed=False,
        config_fingerprint=config_fingerprint,
    )


def read_run_state(path: Path) -> RunState:
    data = json.loads(path.read_text(encoding="utf-8"))
    return RunState(
        run_id=str(data["run_id"]),
        next_index=int(data["next_index"]),
        completed_samples=[str(item) for item in data.get("completed_samples", [])],
        buckets={str(key): [str(item) for item in value] for key, value in data.get("buckets", {}).items()},
        failure_types={str(key): int(value) for key, value in data.get("failure_types", {}).items()},
        exports_refreshed=bool(data.get("exports_refreshed", False)),
        config_fingerprint=str(data.get("config_fingerprint", "")),
    )


def write_run_state(path: Path, state: RunState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(state), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def should_skip_sample(state: RunState, sample_id: str) -> bool:
    return sample_id in set(state.completed_samples)


def classify_sample_bucket(labels: dict[str, Any]) -> str:
    if labels.get("pass_level") == "L3":
        return "success_l3"
    if labels.get("pass_level") == "GEN_FAIL":
        return "rejected"
    if int(labels.get("failure_count", 0)) > 0:
        return "repair_trajectory"
    return "rejected"


def _config_to_jsonable(config: RunnerConfig) -> dict[str, Any]:
    payload = asdict(config)
    payload["dataset_root"] = str(config.dataset_root)
    payload["export_root"] = str(config.export_root)
    payload["run_root"] = str(config.run_root)
    payload["env_file"] = _env_file_label(config.env_file)
    return payload


def _config_fingerprint(config: RunnerConfig) -> str:
    payload = json.dumps(_config_to_jsonable(config), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _load_env_file(path: Path) -> set[str]:
    loaded: set[str] = set()
    if path == Path("") or not path.is_file():
        return loaded
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        if not key or key in os.environ:
            continue
        os.environ[key] = _strip_env_value(value.strip())
        loaded.add(key)
    return loaded


def _strip_env_value(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _env_file_label(path: Path) -> str:
    return "" if path == Path("") else str(path)


def _api_key_diagnostics(config: RunnerConfig, loaded_env_keys: set[str]) -> dict[str, dict[str, object]]:
    value = os.environ.get(config.api_key_env, "")
    source = ""
    if value:
        source = _env_file_label(config.env_file) if config.api_key_env in loaded_env_keys else "environment"
    return {
        config.api_key_env: {
            "present": bool(value),
            "source": source,
            "fingerprint": _secret_fingerprint(value) if value else "",
        }
    }


def _secret_fingerprint(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:8]


def _source_auth_diagnostics(
    config: RunnerConfig,
    samples: list[PlannedSample],
    validate_provider: bool,
) -> tuple[dict[str, dict[str, str]], list[str]]:
    diagnostics: dict[str, dict[str, str]] = {}
    errors: list[str] = []
    seen: set[str] = set()
    for sample in samples:
        _check_source_auth(config, sample.source, seen, diagnostics, errors, validate_provider)
    if config.repair_provider and config.repair_provider != "none":
        _check_source_auth(config, config.repair_provider, seen, diagnostics, errors, validate_provider)
    return diagnostics, errors


def _check_source_auth(
    config: RunnerConfig,
    source: str,
    seen: set[str],
    diagnostics: dict[str, dict[str, str]],
    errors: list[str],
    validate_provider: bool,
) -> None:
    if source in seen:
        return
    seen.add(source)
    connection = resolve_source_connection(config, source)
    if connection.kind not in LLM_SOURCE_KINDS:
        return
    api_key = os.environ.get(connection.api_key_env, "")
    if not api_key:
        diagnostics[source] = {
            "status": "skipped",
            "detail": f"{connection.api_key_env} is not set",
        }
        errors.append(f"{connection.api_key_env} is not set for source {source}")
        return
    if not validate_provider:
        diagnostics[source] = {"status": "not_checked", "detail": ""}
        return
    client = _preflight_client(connection, api_key)
    try:
        client.chat(
            [
                {"role": "system", "content": "Return a tiny JSON object for authentication preflight."},
                {"role": "user", "content": "Return {\"ok\": true}."},
            ]
        )
    except RuntimeError as exc:
        diagnostics[source] = {
            "status": "failed",
            "detail": _sanitize_secret(str(exc), api_key),
        }
        errors.append(f"{source} provider auth failed")
        return
    diagnostics[source] = {"status": "ok", "detail": ""}


def _provider_auth_timeout_seconds(connection: SourceConnection) -> int:
    return max(20, min(connection.timeout_seconds, 120))


def _preflight_client(connection: SourceConnection, api_key: str):
    timeout_seconds = _provider_auth_timeout_seconds(connection)
    if connection.kind == "anthropic_compat":
        return AnthropicCompatibleClient(
            AnthropicCompatibleConfig(
                api_key=api_key,
                model=connection.model,
                base_url=connection.base_url,
                timeout_seconds=timeout_seconds,
            )
        )
    return OpenAICompatibleClient(
        OpenAICompatibleConfig(
            api_key=api_key,
            model=connection.model,
            base_url=connection.base_url,
            timeout_seconds=timeout_seconds,
        )
    )


def _sanitize_secret(text: str, secret: str) -> str:
    if not secret:
        return text
    return text.replace(secret, "<redacted>")


def _record_completed(
    state: RunState,
    sample_id: str,
    next_index: int,
    bucket: str,
    sample_dir: Path,
) -> RunState:
    buckets = {key: list(value) for key, value in state.buckets.items()}
    buckets.setdefault(bucket, [])
    if sample_id not in buckets[bucket]:
        buckets[bucket].append(sample_id)

    completed_samples = list(state.completed_samples)
    if sample_id not in completed_samples:
        completed_samples.append(sample_id)

    failure_types = dict(state.failure_types)
    for failure_type, count in _sample_failure_types(sample_dir).items():
        failure_types[failure_type] = failure_types.get(failure_type, 0) + count

    return RunState(
        run_id=state.run_id,
        next_index=next_index,
        completed_samples=completed_samples,
        buckets=buckets,
        failure_types=failure_types,
        exports_refreshed=state.exports_refreshed,
        config_fingerprint=state.config_fingerprint,
    )


def _record_rejected(state: RunState, sample_id: str, next_index: int, failure_type: str) -> RunState:
    buckets = {key: list(value) for key, value in state.buckets.items()}
    buckets.setdefault("rejected", [])
    if sample_id not in buckets["rejected"]:
        buckets["rejected"].append(sample_id)

    completed_samples = list(state.completed_samples)
    if sample_id not in completed_samples:
        completed_samples.append(sample_id)

    failure_types = dict(state.failure_types)
    failure_types[failure_type] = failure_types.get(failure_type, 0) + 1

    return RunState(
        run_id=state.run_id,
        next_index=next_index,
        completed_samples=completed_samples,
        buckets=buckets,
        failure_types=failure_types,
        exports_refreshed=state.exports_refreshed,
        config_fingerprint=state.config_fingerprint,
    )


def _read_labels(sample_dir: Path) -> dict[str, Any]:
    return json.loads((sample_dir / "eval" / "labels.json").read_text(encoding="utf-8"))


def _sample_failure_types(sample_dir: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    attempts_dir = sample_dir / "attempts"
    if not attempts_dir.exists():
        return counts
    for diagnosis_path in sorted(attempts_dir.glob("attempt_*/diagnosis.json")):
        diagnosis = json.loads(diagnosis_path.read_text(encoding="utf-8"))
        failure_type = str(diagnosis.get("failure_type", "unknown"))
        counts[failure_type] = counts.get(failure_type, 0) + 1
    return counts


def _failure_family(failure_type: str, stage: str = "") -> str:
    if failure_type == "generation_failed" or stage == "generation":
        return "generation_failure"
    if failure_type == "repair_failed" or stage == "repair":
        return "repair_failure"
    if failure_type == "l0_contract_violation":
        return "artifact_contract_failure"
    if stage == "testbench_static_check" or failure_type in {
        "testbench_observation_race",
        "testbench_stimulus_reaccept_risk",
    }:
        return "testbench_failure"
    if stage in {"rtl_identifier_check", "lint", "sim_compile"}:
        return "rtl_compile_failure"
    if stage == "sim_run":
        return "rtl_sim_failure"
    if stage == "synth":
        return "synth_failure"
    if failure_type in {"syntax_error", "module_not_found", "parameter_mismatch", "port_mismatch", "width_mismatch"}:
        return "rtl_compile_failure"
    if failure_type == "sample_exists":
        return "sample_rejection"
    return "unknown_failure"


def _sample_failure_families(sample_dir: Path) -> set[str]:
    families: set[str] = set()
    attempts_dir = sample_dir / "attempts"
    if not attempts_dir.exists():
        return families
    for diagnosis_path in sorted(attempts_dir.glob("attempt_*/diagnosis.json")):
        diagnosis = json.loads(diagnosis_path.read_text(encoding="utf-8"))
        families.add(
            _failure_family(
                str(diagnosis.get("failure_type", "unknown")),
                str(diagnosis.get("stage", "")),
            )
        )
    return families


def _sample_attempt_stage_transitions(sample_dir: Path) -> dict[str, int]:
    stages: list[str] = []
    attempts_dir = sample_dir / "attempts"
    if not attempts_dir.exists():
        return {}
    for diagnosis_path in sorted(attempts_dir.glob("attempt_*/diagnosis.json")):
        diagnosis = json.loads(diagnosis_path.read_text(encoding="utf-8"))
        stage = str(diagnosis.get("stage", "")).strip()
        if stage:
            stages.append(stage)

    transitions: dict[str, int] = {}
    for from_stage, to_stage in zip(stages, stages[1:]):
        transition = f"{from_stage}->{to_stage}"
        transitions[transition] = transitions.get(transition, 0) + 1
    return transitions


def _sample_latent_testbench_issues(sample_dir: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    for testbench_path in sorted(sample_dir.glob("attempts/attempt_*/generated_project/sim/tb_top.v")):
        issues = check_testbench_static_issues(testbench_path.read_text(encoding="utf-8"))
        for issue in issues:
            counts[issue.failure_type] = counts.get(issue.failure_type, 0) + 1
    return counts


def _summary(config: RunnerConfig, state: RunState) -> dict[str, Any]:
    calibration = _calibration_breakdown(config.dataset_root, state.completed_samples)
    return {
        "run_id": state.run_id,
        "config_fingerprint": state.config_fingerprint,
        "total_planned": len(planned_samples(config)),
        "total_completed": len(state.completed_samples),
        "next_index": state.next_index,
        "buckets": state.buckets,
        "failure_types": state.failure_types,
        "failure_family_breakdown": calibration["failure_family_breakdown"],
        "attempt_stage_transition_breakdown": calibration["attempt_stage_transition_breakdown"],
        "latent_testbench_issue_breakdown": calibration["latent_testbench_issue_breakdown"],
        "metadata_breakdown": calibration["metadata_breakdown"],
        "pass_level_breakdown": calibration["pass_level_breakdown"],
        "calibration_matrix": calibration["calibration_matrix"],
        "contract_metrics": calibration["contract_metrics"],
        "exports_refreshed": state.exports_refreshed,
        "line_b_targets": config.line_b_targets,
    }


def _calibration_breakdown(dataset_root: Path, sample_ids: list[str]) -> dict[str, dict[str, dict[str, int]]]:
    metadata_fields = (
        "source",
        "failure_origin",
        "requirement_style",
        "contract_skeleton_mode",
        "difficulty_tier",
        "topology_id",
        "measurement_point",
    )
    metadata_breakdown: dict[str, dict[str, int]] = {field: {} for field in metadata_fields}
    failure_family_breakdown: dict[str, int] = {}
    attempt_stage_transition_breakdown: dict[str, int] = {}
    latent_testbench_issue_breakdown: dict[str, int] = {}
    pass_level_breakdown: dict[str, int] = {}
    calibration_counts: dict[str, dict[str, dict[str, Any]]] = {
        field: {} for field in (*metadata_fields, "failure_family")
    }
    total_labeled = 0
    l0_contract_failures = 0
    for sample_id in sample_ids:
        sample_dir = dataset_root / sample_id
        labels_path = sample_dir / "eval" / "labels.json"
        if not labels_path.exists():
            continue
        labels = json.loads(labels_path.read_text(encoding="utf-8"))
        total_labeled += 1
        l0_contract_failed = labels.get("checks", {}).get("l0_complete") is False
        if l0_contract_failed:
            l0_contract_failures += 1
        pass_level = str(labels.get("pass_level", "unknown"))
        pass_level_breakdown[pass_level] = pass_level_breakdown.get(pass_level, 0) + 1
        metadata = _read_sample_metadata(sample_dir)
        for field in metadata_fields:
            value = str(metadata.get(field, "")).strip()
            if not value:
                continue
            metadata_breakdown[field][value] = metadata_breakdown[field].get(value, 0) + 1
            _record_calibration_cell(calibration_counts[field], value, pass_level, l0_contract_failed)
        for failure_family in sorted(_sample_failure_families(sample_dir)):
            failure_family_breakdown[failure_family] = failure_family_breakdown.get(failure_family, 0) + 1
            _record_calibration_cell(
                calibration_counts["failure_family"],
                failure_family,
                pass_level,
                l0_contract_failed,
            )
        for transition, count in _sample_attempt_stage_transitions(sample_dir).items():
            attempt_stage_transition_breakdown[transition] = (
                attempt_stage_transition_breakdown.get(transition, 0) + count
            )
        for issue_type, count in _sample_latent_testbench_issues(sample_dir).items():
            latent_testbench_issue_breakdown[issue_type] = latent_testbench_issue_breakdown.get(issue_type, 0) + count
    return {
        "metadata_breakdown": metadata_breakdown,
        "failure_family_breakdown": failure_family_breakdown,
        "attempt_stage_transition_breakdown": attempt_stage_transition_breakdown,
        "latent_testbench_issue_breakdown": latent_testbench_issue_breakdown,
        "pass_level_breakdown": pass_level_breakdown,
        "calibration_matrix": _calibration_rates(calibration_counts),
        "contract_metrics": {
            "total_labeled": total_labeled,
            "l0_contract_failures": l0_contract_failures,
            "cross_file_consistency_error_rate": (
                0.0 if total_labeled == 0 else l0_contract_failures / total_labeled
            ),
        },
    }


def _record_calibration_cell(
    cells: dict[str, dict[str, Any]],
    value: str,
    pass_level: str,
    l0_contract_failed: bool,
) -> None:
    cell = cells.setdefault(value, {"total": 0, "pass_levels": {}, "l0_contract_failures": 0})
    cell["total"] += 1
    cell["pass_levels"][pass_level] = cell["pass_levels"].get(pass_level, 0) + 1
    if l0_contract_failed:
        cell["l0_contract_failures"] += 1


def _calibration_rates(counts: dict[str, dict[str, dict[str, Any]]]) -> dict[str, dict[str, dict[str, Any]]]:
    matrix: dict[str, dict[str, dict[str, Any]]] = {}
    for field, cells in counts.items():
        matrix[field] = {}
        for value, cell in cells.items():
            total = int(cell["total"])
            l3_count = int(cell["pass_levels"].get("L3", 0))
            l0_contract_failures = int(cell.get("l0_contract_failures", 0))
            matrix[field][value] = {
                "total": total,
                "pass_levels": cell["pass_levels"],
                "l3_pass_rate": 0.0 if total == 0 else l3_count / total,
                "l0_contract_failures": l0_contract_failures,
                "cross_file_consistency_error_rate": (
                    0.0 if total == 0 else l0_contract_failures / total
                ),
            }
    return matrix


def _read_sample_metadata(sample_dir: Path) -> dict[str, Any]:
    path = sample_dir / "metadata.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _append_event(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as output:
        output.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _parse_bool(value: Any, name: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized == "true":
            return True
        if normalized == "false":
            return False
    raise SystemExit(f"{name} must be a boolean")


def _load_task_config(item: dict[str, Any], raw: dict[str, Any]) -> TaskConfig:
    widths = [int(width) for width in item.get("widths", [8])]
    count = int(item.get("count", 1))
    if count > 0 and not widths:
        raise SystemExit("Task widths must not be empty when count is positive")
    measurement_point = str(item.get("measurement_point", ""))
    if measurement_point and measurement_point not in VALID_MEASUREMENT_POINTS:
        allowed = ", ".join(sorted(VALID_MEASUREMENT_POINTS))
        raise SystemExit(f"Unsupported measurement_point: {measurement_point}. Expected one of: {allowed}")
    requirement_style = str(item.get("requirement_style", "contract"))
    if requirement_style not in VALID_REQUIREMENT_STYLES:
        allowed = ", ".join(sorted(VALID_REQUIREMENT_STYLES))
        raise SystemExit(f"Unsupported requirement_style: {requirement_style}. Expected one of: {allowed}")
    return TaskConfig(
        source=str(item.get("source", raw.get("provider", "deterministic"))),
        task_type=str(item["task_type"]),
        widths=widths,
        count=count,
        failure_injectors=[str(injector) for injector in item.get("failure_injectors", [])],
        difficulty_tier=str(item.get("difficulty_tier", "T1")),
        failure_origin=str(item.get("failure_origin", "")),
        topology_ids=[str(topology_id) for topology_id in item.get("topology_ids", [])],
        measurement_point=measurement_point,
        requirement_style=requirement_style,
    )


LLM_SOURCE_KINDS = {"openai_compat", "anthropic_compat", "deepseek", "deepseek-his-v12"}


def resolve_source_connection(config: RunnerConfig, source: str) -> SourceConnection:
    if source in config.sources:
        return config.sources[source]
    if source == "deterministic":
        return SourceConnection(name="deterministic", kind="deterministic")
    if source == "deepseek-his-v12":
        kind, mode = "deepseek-his-v12", "two_stage"
    elif source == "deepseek" or source.startswith("deepseek-"):
        kind, mode = "deepseek", "direct"
    else:
        kind, mode = "openai_compat", "two_stage"
    return SourceConnection(
        name=source,
        kind=kind,
        model=config.model,
        base_url=config.base_url,
        api_key_env=config.api_key_env,
        generation_mode=mode,
    )


_GENERATION_MODE_BY_KIND = {
    "openai_compat": "two_stage",
    "anthropic_compat": "two_stage",
    "deepseek-his-v12": "two_stage",
    "deepseek": "direct",
    "deterministic": "",
}


def _load_sources(raw: dict[str, Any]) -> dict[str, SourceConnection]:
    sources: dict[str, SourceConnection] = {}
    for name, item in raw.items():
        kind = str(item.get("kind", "openai_compat"))
        generation_mode = str(item.get("generation_mode", ""))
        if kind == "openai_compat" and generation_mode == "direct":
            raise SystemExit(
                f"Source {name!r}: generation_mode 'direct' is not supported for kind 'openai_compat'"
            )
        if not generation_mode:
            generation_mode = _GENERATION_MODE_BY_KIND.get(kind, "")
        sources[str(name)] = SourceConnection(
            name=str(name),
            kind=kind,
            model=str(item.get("model", "")),
            base_url=str(item.get("base_url", "")),
            api_key_env=str(item.get("api_key_env", "")),
            generation_mode=generation_mode,
            timeout_seconds=int(item.get("timeout_seconds", 120)),
        )
    return sources


def _load_mapping(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        data = json.loads(text)
    else:
        try:
            import yaml
        except ModuleNotFoundError as exc:
            raise SystemExit("PyYAML is required for YAML runner configs; use .json or install pyyaml") from exc
        data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise SystemExit("Runner config must be a mapping")
    return data


def planned_samples(config: RunnerConfig) -> list[PlannedSample]:
    samples: list[PlannedSample] = []
    sequence = 1
    for task in config.tasks:
        if task.count > 0 and not task.widths:
            raise SystemExit("Task widths must not be empty when count is positive")
        produced = 0
        while produced < task.count:
            for topology_id, task_type, difficulty_tier, width in _task_expansion_items(task):
                if produced >= task.count:
                    break
                sample_key = topology_id or task_type
                sample_id = f"sample_{config.sample_id_prefix}_{sample_key}_{width}_{sequence:06d}"
                project_name = f"{config.sample_id_prefix}_{sample_key}_{width}_{sequence:06d}"
                samples.append(
                    PlannedSample(
                        sample_id=sample_id,
                        source=task.source,
                        task_type=task_type,
                        width=width,
                        project_name=project_name,
                        requirement=_default_requirement(
                            task_type,
                            width,
                            topology_id=topology_id,
                            requirement_style=task.requirement_style,
                        ),
                        failure_injectors=list(task.failure_injectors),
                        difficulty_tier=difficulty_tier,
                        failure_origin=task.failure_origin,
                        topology_id=topology_id,
                        measurement_point=task.measurement_point,
                        requirement_style=task.requirement_style,
                    )
                )
                sequence += 1
                produced += 1
    max_samples = int(config.line_b_targets.get("max_samples", len(samples)))
    return samples[:max_samples]


def _task_expansion_items(task: TaskConfig) -> list[tuple[str, str, str, int]]:
    if task.task_type != "component_topology":
        return [("", task.task_type, task.difficulty_tier, width) for width in task.widths]
    topology_ids = task.topology_ids or sorted(_topology_id_to_task_type())
    items: list[tuple[str, str, str, int]] = []
    topology_lookup = _topology_id_to_task_type()
    for topology_id in topology_ids:
        if topology_id not in topology_lookup:
            raise SystemExit(f"Unsupported topology_id: {topology_id}")
        task_type = topology_lookup[topology_id]
        difficulty_tier = str(COMPONENT_TOPOLOGIES[task_type]["difficulty_tier"])
        for width in task.widths:
            items.append((topology_id, task_type, difficulty_tier, width))
    return items


def _topology_id_to_task_type() -> dict[str, str]:
    return {str(spec["topology_id"]): task_type for task_type, spec in COMPONENT_TOPOLOGIES.items()}


def _default_requirement(
    task_type: str,
    width: int,
    topology_id: str = "",
    requirement_style: str = "contract",
) -> str:
    if requirement_style == "simple_prompt":
        return _simple_prompt_requirement(task_type, width)
    if requirement_style == "natural_component" and topology_id:
        return _natural_component_requirement(task_type, width, topology_id)
    return (
        f"Design a {width}-bit {task_type} as a complete SR2FPGA Verilog RTL project. "
        "Use multi-file RTL for FIFO, SPI, UART, PWM, and controller-style tasks; "
        "include system_his.json, manifest.json, "
        "timing constraints, a bounded self-checking testbench that prints TEST_PASS on success "
        f"or TEST_FAIL on failure, and predicted QoR.{_topology_requirement_clause(task_type, topology_id)}"
    )


def _simple_prompt_requirement(task_type: str, width: int) -> str:
    prompts = {
        "composed_event_counter": (
            f"Generate an {width}-bit FPGA RTL project that counts incoming event pulses."
        ),
        "composed_stream_accumulator": (
            f"Generate an {width}-bit FPGA RTL project that accepts a valid-ready input stream and accumulates samples."
        ),
        "composed_stream_fork": (
            f"Generate an {width}-bit FPGA RTL project that duplicates one valid-ready input stream to two output streams."
        ),
        "composed_dual_stream_join": (
            f"Generate an {width}-bit FPGA RTL project that joins two input streams, accumulates joined samples, "
            "and exposes one output stream."
        ),
        "composed_vector_mac_pipeline": (
            f"Generate an {width}-bit FPGA RTL project that accepts paired feature and weight streams, "
            "computes a fixed-length vector MAC score with bias, and exposes one score stream."
        ),
        "composed_td_update_core": (
            f"Generate an {width}-bit FPGA RTL project that accepts reward, value, next_value, gamma, "
            "and alpha inputs, computes TD error, and emits an updated value stream."
        ),
        "composed_policy_value_shell": (
            f"Generate an {width}-bit FPGA RTL project with config registers, two observation inputs, "
            "policy score comparison, selected action output, and value estimate output."
        ),
        "composed_replay_sample_shell": (
            f"Generate an {width}-bit FPGA RTL project with a host-side replay sample write interface, "
            "a small replay store, fabric-side sample readout, and occupancy status."
        ),
        "composed_host_protocol_shell": (
            f"Generate an {width}-bit FPGA RTL project with AXI-lite-style control/status writes and reads, "
            "AXI-stream-style sample output, and irq reporting."
        ),
        "composed_rl_accelerator_shell": (
            f"Generate an {width}-bit FPGA RTL project with host configuration, sample capture, "
            "policy/value scoring, TD update, result streaming, and irq reporting."
        ),
        "composed_batch_rl_accelerator_shell": (
            f"Generate an {width}-bit FPGA RTL project with shared host configuration, two-lane batch sample capture, "
            "dual-lane policy/value scoring, dual-lane TD update, result staging, and irq reporting."
        ),
    }
    return prompts.get(task_type, f"Generate an {width}-bit {task_type} FPGA RTL project.")


def _natural_component_requirement(task_type: str, width: int, topology_id: str) -> str:
    topology = COMPONENT_TOPOLOGIES[task_type]
    title = _natural_component_title(task_type)
    components = _natural_component_summary(task_type)
    behavior = _topology_expected_behavior(task_type)
    edges = "; ".join(f"{edge['from']} -> {edge['to']}" for edge in topology["edges"])
    return (
        f"Build an {width}-bit {title} as a complete SR2FPGA Verilog RTL project. "
        f"This is component topology {topology_id}, difficulty tier {topology['difficulty_tier']}. "
        f"Use {components}. The design must implement this black-box behavior: {behavior}. "
        "Keep rtl/top.v as the integration wrapper and keep each reusable component in a separate RTL file. "
        f"Preserve these interface contracts: {edges}. "
        "Include system_his.json, manifest.json, timing constraints, predicted QoR, and a bounded "
        "self-checking testbench that prints TEST_PASS only on success or TEST_FAIL on failure."
    )


def _natural_component_title(task_type: str) -> str:
    titles = {
        "composed_event_counter": "event-counting subsystem",
        "composed_stream_accumulator": "streaming accumulator datapath",
        "composed_stream_fork": "valid-ready stream fork datapath",
        "composed_dual_stream_join": "dual-stream join datapath",
        "composed_vector_mac_pipeline": "vector MAC feature pipeline",
        "composed_td_update_core": "TD-error value-update datapath",
        "composed_policy_value_shell": "policy/value accelerator shell",
        "composed_replay_sample_shell": "replay sample host/fabric shell",
        "composed_host_protocol_shell": "host protocol control and stream shell",
        "composed_rl_accelerator_shell": "synthetic RL accelerator shell",
        "composed_batch_rl_accelerator_shell": "two-lane batch RL accelerator shell",
    }
    return titles[task_type]


def _natural_component_summary(task_type: str) -> str:
    summaries = {
        "composed_event_counter": "an event_gate in front of a counter_core",
        "composed_stream_accumulator": "a skid_buffer feeding an accumulator_core",
        "composed_stream_fork": "a skid_buffer feeding a stream_fork and two stream_stage outputs",
        "composed_dual_stream_join": (
            "two skid_buffer instances feeding stream_join, then accumulator_core, then stream_stage"
        ),
        "composed_vector_mac_pipeline": (
            "feature and weight skid_buffer instances feeding vector_mac_core, then stream_stage"
        ),
        "composed_td_update_core": (
            "td_input_stage feeding discount_core, then td_update_core, then stream_stage"
        ),
        "composed_policy_value_shell": (
            "config_reg_bank and observation_stage feeding policy_score_core, then action_select_core, "
            "then stream_stage"
        ),
        "composed_replay_sample_shell": (
            "host_sample_stage feeding replay_store, then sample_pack_core and sample_read_stage, "
            "with occupancy_counter status"
        ),
        "composed_host_protocol_shell": (
            "axi_lite_write_ctrl and axi_lite_read_ctrl feeding control_reg_bank, then "
            "sample_stream_adapter and irq_status"
        ),
        "composed_rl_accelerator_shell": (
            "host_config_bank and sample_capture_stage feeding policy_value_core, then "
            "td_update_core and result_stream_stage"
        ),
        "composed_batch_rl_accelerator_shell": (
            "batch_config_bank and batch_sample_buffer feeding dual_policy_value_core, then "
            "dual_td_update_core and batch_result_stage"
        ),
    }
    return summaries[task_type]


def _topology_requirement_clause(task_type: str, topology_id: str) -> str:
    if not topology_id:
        return ""
    topology = COMPONENT_TOPOLOGIES[task_type]
    nodes = ", ".join(f"{node['id']}:{node['component']}" for node in topology["nodes"])
    edges = "; ".join(f"{edge['from']} -> {edge['to']}" for edge in topology["edges"])
    behavior = _topology_expected_behavior(task_type)
    return (
        f" Use component topology {topology_id} at difficulty tier {topology['difficulty_tier']}. "
        f"Instantiate nodes {nodes}. Wire required edges: {edges}. "
        f"Expected behavior: {behavior}. "
        "Keep rtl/top.v as the integration wrapper and keep submodules in separate RTL files."
    )


def _topology_expected_behavior(task_type: str) -> str:
    behaviors = {
        "composed_event_counter": "event_valid pulses pass through an event gate and increment the counter core",
        "composed_stream_accumulator": (
            "valid input samples pass through a skid buffer and accumulate into the running sum"
        ),
        "composed_stream_fork": (
            "valid input samples pass through a skid buffer and are duplicated to two output stages"
        ),
        "composed_dual_stream_join": (
            "two valid-ready input streams are buffered, synchronized, joined, accumulated, and staged"
        ),
        "composed_vector_mac_pipeline": (
            "paired feature and weight streams are buffered, multiplied and accumulated over a fixed vector length, "
            "biased, and staged as score output"
        ),
        "composed_td_update_core": (
            "a reward, value, next value, discount factor, and learning rate tuple is staged, "
            "converted into a temporal-difference error, and used to emit an updated value"
        ),
        "composed_policy_value_shell": (
            "configuration writes set weights, biases, and enable; observation pairs are staged, "
            "scored, compared, and emitted as selected action plus value estimate"
        ),
        "composed_replay_sample_shell": (
            "host-side transition samples are staged into a small replay store, then read back in FIFO order "
            "through a fabric-side valid-ready sample output with occupancy reporting"
        ),
        "composed_host_protocol_shell": (
            "AXI-lite-style writes configure sample registers and start streaming; one AXI-stream-style payload "
            "is emitted, status can be read back, and irq remains asserted until cleared"
        ),
        "composed_rl_accelerator_shell": (
            "configuration writes set weights, biases, alpha, and enable; sample tuples are captured, "
            "scored into a selected action and value estimate, updated through a TD datapath, "
            "and staged as a result stream with episode irq reporting"
        ),
        "composed_batch_rl_accelerator_shell": (
            "configuration writes set shared weights, biases, alpha, and enable; a two-lane batch is captured, "
            "each lane is scored and updated through duplicated policy/value and TD datapaths, "
            "and both lane results are staged with batch_done irq reporting"
        ),
    }
    return behaviors[task_type]


def _sample_failure_origin(sample: PlannedSample, config: RunnerConfig) -> str:
    if sample.failure_origin:
        return sample.failure_origin
    if sample.failure_injectors:
        return "synthetic_injected"
    connection = resolve_source_connection(config, sample.source)
    if connection.kind in LLM_SOURCE_KINDS:
        return "natural_llm"
    if connection.kind == "deterministic":
        return "deterministic_template"
    return sample.source


def _sample_system_his_schema_version(sample: PlannedSample, config: RunnerConfig) -> str:
    connection = resolve_source_connection(config, sample.source)
    if connection.kind == "deterministic" or connection.generation_mode == "two_stage":
        return "system-his-v1.2"
    return "system-his-v1.1"


def _contract_skeleton_mode(sample: PlannedSample, config: RunnerConfig) -> str:
    connection = resolve_source_connection(config, sample.source)
    if connection.generation_mode == "two_stage":
        return "behavior_files"
    if connection.kind == "deterministic":
        return "deterministic_template"
    if connection.kind in LLM_SOURCE_KINDS:
        return "legacy_full_project"
    return connection.kind or sample.source


def _training_split(schema_version: str) -> str:
    return "clean" if schema_version == "system-his-v1.2" else "quarantine"


def _measurement_point(config: RunnerConfig) -> str:
    if config.repair_provider != "none" and config.max_attempts > 1:
        return "b_tool_in_loop_repair"
    return "a_first_attempt_no_tools"


def _project_generator_for_sample(
    project_generators: dict[str, object | None],
    config: RunnerConfig,
    sample: PlannedSample,
    events_path: Path,
) -> object | None:
    connection = resolve_source_connection(config, sample.source)
    cache_key = sample.source
    if connection.generation_mode == "two_stage":
        cache_key = f"{sample.source}:{sample.sample_id}"
    if cache_key not in project_generators:
        event_sink = (
            _generation_event_sink(events_path, sample, config)
            if connection.generation_mode == "two_stage"
            else None
        )
        project_generators[cache_key] = build_project_generator_for_connection(
            connection,
            event_sink=event_sink,
        )
    project_generator = project_generators[cache_key]
    if not sample.failure_injectors:
        return project_generator
    base_generator = project_generator or ProjectGenerator()
    return FailureInjectingProjectGenerator(base_generator, sample.failure_injectors)


def _repairer_for_config(config: RunnerConfig):
    if config.repair_provider in config.sources:
        return build_repairer_for_connection(resolve_source_connection(config, config.repair_provider))
    return build_repairer(
        provider=config.repair_provider,
        model=config.model,
        base_url=config.base_url,
        api_key_env=config.api_key_env,
    )


def _generation_event_sink(events_path: Path, sample: PlannedSample, config: RunnerConfig):
    def emit(payload: dict[str, Any]) -> None:
        _append_event(
            events_path,
            {
                **payload,
                "sample_id": sample.sample_id,
                "source": sample.source,
                "failure_origin": _sample_failure_origin(sample, config),
                "difficulty_tier": sample.difficulty_tier,
                "topology_id": sample.topology_id,
                "requirement_style": sample.requirement_style,
                "measurement_point": sample.measurement_point,
            },
        )

    return emit


if __name__ == "__main__":
    main()
