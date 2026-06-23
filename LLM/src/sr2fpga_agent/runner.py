"""Autonomous batch runner for SR2FPGA trajectory generation."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from LLM.src.sr2fpga_agent.agent import DataGenerationAgent
from LLM.src.sr2fpga_agent.cli import build_project_generator, build_repairer
from LLM.src.sr2fpga_agent.models import PlatformProfile, ProjectRequest
from LLM.src.sr2fpga_agent.recorder import DatasetRecorder


@dataclass(frozen=True)
class TaskConfig:
    source: str
    task_type: str
    widths: list[int]
    count: int


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
    model: str = "deepseek-v4-flash"
    base_url: str = "https://api.deepseek.com"
    api_key_env: str = "DEEPSEEK_API_KEY"
    platform: str = "generic_verilog"


@dataclass(frozen=True)
class PlannedSample:
    sample_id: str
    source: str
    task_type: str
    width: int
    project_name: str
    requirement: str


@dataclass(frozen=True)
class RunState:
    run_id: str
    next_index: int
    completed_samples: list[str]
    buckets: dict[str, list[str]]
    failure_types: dict[str, int]
    exports_refreshed: bool


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
        model=str(raw.get("model", "deepseek-v4-flash")),
        base_url=str(raw.get("base_url", "https://api.deepseek.com")),
        api_key_env=str(raw.get("api_key_env", "DEEPSEEK_API_KEY")),
        platform=str(raw.get("platform", "generic_verilog")),
    )


def run_batch(config: RunnerConfig, run_id: str | None = None, resume: bool = True) -> dict[str, Any]:
    if run_id is None:
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = config.run_root / run_id
    state_path = run_dir / "run_state.json"
    events_path = run_dir / "events.jsonl"
    summary_path = run_dir / "summary.json"
    run_dir.mkdir(parents=True, exist_ok=True)
    _write_json(run_dir / "config.json", _config_to_jsonable(config))

    if resume and state_path.exists():
        state = read_run_state(state_path)
    else:
        state = initial_run_state(run_id)
        write_run_state(state_path, state)

    samples = planned_samples(config)
    project_generator = build_project_generator(
        provider=config.provider,
        model=config.model,
        base_url=config.base_url,
        api_key_env=config.api_key_env,
    )
    repairer = build_repairer(
        provider=config.repair_provider,
        model=config.model,
        base_url=config.base_url,
        api_key_env=config.api_key_env,
    )

    for index, sample in enumerate(samples):
        if index < state.next_index or should_skip_sample(state, sample.sample_id):
            continue
        if (config.dataset_root / sample.sample_id).exists():
            state = _record_rejected(state, sample.sample_id, index + 1, "sample_exists")
            _append_event(events_path, {"event": "sample_exists", "sample_id": sample.sample_id})
            write_run_state(state_path, state)
            continue

        agent = DataGenerationAgent(
            config.dataset_root,
            project_generator=project_generator,
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
        )
        labels = _read_labels(config.dataset_root / sample.sample_id)
        bucket = classify_sample_bucket(labels)
        state = _record_completed(state, sample.sample_id, index + 1, bucket, config.dataset_root / sample.sample_id)
        _append_event(
            events_path,
            {
                "event": "sample_completed",
                "sample_id": sample.sample_id,
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
        )
        write_run_state(state_path, state)

    summary = _summary(config, state)
    _write_json(summary_path, summary)
    return summary


def initial_run_state(run_id: str) -> RunState:
    return RunState(
        run_id=run_id,
        next_index=0,
        completed_samples=[],
        buckets={"success_l3": [], "repair_trajectory": [], "rejected": []},
        failure_types={},
        exports_refreshed=False,
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
    )


def write_run_state(path: Path, state: RunState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(state), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def should_skip_sample(state: RunState, sample_id: str) -> bool:
    return sample_id in set(state.completed_samples)


def classify_sample_bucket(labels: dict[str, Any]) -> str:
    if labels.get("pass_level") == "L3":
        return "success_l3"
    if int(labels.get("failure_count", 0)) > 0:
        return "repair_trajectory"
    return "rejected"


def _config_to_jsonable(config: RunnerConfig) -> dict[str, Any]:
    payload = asdict(config)
    payload["dataset_root"] = str(config.dataset_root)
    payload["export_root"] = str(config.export_root)
    payload["run_root"] = str(config.run_root)
    return payload


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


def _summary(config: RunnerConfig, state: RunState) -> dict[str, Any]:
    return {
        "run_id": state.run_id,
        "total_planned": len(planned_samples(config)),
        "total_completed": len(state.completed_samples),
        "next_index": state.next_index,
        "buckets": state.buckets,
        "failure_types": state.failure_types,
        "exports_refreshed": state.exports_refreshed,
        "line_b_targets": config.line_b_targets,
    }


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
    return TaskConfig(
        source=str(item.get("source", raw.get("provider", "deterministic"))),
        task_type=str(item["task_type"]),
        widths=widths,
        count=count,
    )


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
            for width in task.widths:
                if produced >= task.count:
                    break
                sample_id = f"sample_runner_{task.task_type}_{width}_{sequence:06d}"
                project_name = f"runner_{task.task_type}_{width}_{sequence:06d}"
                samples.append(
                    PlannedSample(
                        sample_id=sample_id,
                        source=task.source,
                        task_type=task.task_type,
                        width=width,
                        project_name=project_name,
                        requirement=_default_requirement(task.task_type, width),
                    )
                )
                sequence += 1
                produced += 1
    max_samples = int(config.line_b_targets.get("max_samples", len(samples)))
    return samples[:max_samples]


def _default_requirement(task_type: str, width: int) -> str:
    return (
        f"Design a {width}-bit {task_type} as a complete SR2FPGA Verilog RTL project. "
        "Use multi-file RTL for FIFO, SPI, UART, PWM, and controller-style tasks; "
        "include system_his.json, manifest.json, "
        "timing constraints, a bounded self-checking testbench that prints TEST_PASS on success "
        "or TEST_FAIL on failure, and predicted QoR."
    )
