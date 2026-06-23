"""Autonomous batch runner for SR2FPGA trajectory generation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


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
