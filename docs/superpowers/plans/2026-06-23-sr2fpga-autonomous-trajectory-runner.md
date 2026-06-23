# SR2FPGA Autonomous Trajectory Runner Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a first autonomous SR2FPGA batch runner that can run existing deterministic and DeepSeek sources from a config file, record resumable run state, classify samples into success/repair/rejected buckets, refresh exports, and write compact research summaries.

**Architecture:** Keep `DataGenerationAgent.run_one()` as the per-sample execution unit. Add a focused `runner.py` module for config loading, sample planning, resume state, bucket classification, batch orchestration, export refresh, and CLI entry. Do not implement the compositional component-library generator in this slice; keep it as a first-class future `source` value so the runner architecture does not become DeepSeek-specific.

**Tech Stack:** Python stdlib, optional PyYAML for `.yaml` config loading, `unittest`, existing `DataGenerationAgent`, `DatasetRecorder`, DeepSeek provider builders from `cli.py`.

---

## File Structure

- Create `LLM/src/sr2fpga_agent/runner.py`
  - Owns config dataclasses, config loading, sample-id generation, run-state persistence, bucket classification, batch execution, export refresh, summary writing, and `main(argv)`.
- Create `LLM/tests/test_sr2fpga_agent_runner.py`
  - Unit tests for config loading, sample planning, bucket classification, resume behavior, and export refresh.
- Create `configs/sr2fpga_agent.example.yaml`
  - Safe committed example config with no secrets.
- Modify `LLM/README.md`
  - Add autonomous runner usage and explain `.env` loading.
- Modify `docs/sr2fpga-agent-handoff-2026-06-22.md`
  - Record runner implementation status and command.

The first implementation must not edit `DataGenerationAgent.run_one()` unless the tests expose a necessary orchestration gap.

---

### Task 1: Runner Config And Planning

**Files:**
- Create: `LLM/src/sr2fpga_agent/runner.py`
- Create: `LLM/tests/test_sr2fpga_agent_runner.py`

- [ ] **Step 1: Write failing config and planning tests**

Add this test file:

```python
import json
import tempfile
import unittest
from pathlib import Path

from LLM.src.sr2fpga_agent.runner import (
    RunnerConfig,
    TaskConfig,
    load_runner_config,
    planned_samples,
)


class RunnerConfigTest(unittest.TestCase):
    def test_load_runner_config_from_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "runner.json"
            config_path.write_text(
                json.dumps(
                    {
                        "dataset_root": "datasets/sr2fpga_rtl_v1",
                        "export_root": "datasets/sr2fpga_rtl_v1_exports",
                        "run_root": "tmp/sr2fpga_runs",
                        "provider": "deterministic",
                        "repair_provider": "none",
                        "max_attempts": 1,
                        "refresh_exports": True,
                        "line_b_targets": {
                            "l3_success_ratio": 0.4,
                            "repair_trajectory_ratio": 0.6,
                            "max_samples": 3,
                        },
                        "tasks": [
                            {
                                "source": "deterministic",
                                "task_type": "counter",
                                "widths": [4, 8],
                                "count": 2,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            config = load_runner_config(config_path)

            self.assertEqual(config.dataset_root, Path("datasets/sr2fpga_rtl_v1"))
            self.assertEqual(config.export_root, Path("datasets/sr2fpga_rtl_v1_exports"))
            self.assertEqual(config.run_root, Path("tmp/sr2fpga_runs"))
            self.assertEqual(config.provider, "deterministic")
            self.assertEqual(config.repair_provider, "none")
            self.assertEqual(config.max_attempts, 1)
            self.assertTrue(config.refresh_exports)
            self.assertEqual(config.line_b_targets["max_samples"], 3)
            self.assertEqual(config.tasks[0].task_type, "counter")
            self.assertEqual(config.tasks[0].widths, [4, 8])

    def test_planned_samples_expand_widths_and_counts(self) -> None:
        config = RunnerConfig(
            dataset_root=Path("datasets/sr2fpga_rtl_v1"),
            export_root=Path("datasets/sr2fpga_rtl_v1_exports"),
            run_root=Path("tmp/sr2fpga_runs"),
            provider="deterministic",
            repair_provider="none",
            max_attempts=1,
            refresh_exports=True,
            line_b_targets={"l3_success_ratio": 0.4, "repair_trajectory_ratio": 0.6, "max_samples": 4},
            tasks=[
                TaskConfig(source="deterministic", task_type="counter", widths=[4, 8], count=2),
                TaskConfig(source="deterministic", task_type="fifo", widths=[8], count=1),
            ],
        )

        samples = planned_samples(config)

        self.assertEqual(
            [(item.sample_id, item.task_type, item.width, item.project_name) for item in samples],
            [
                ("sample_runner_counter_4_000001", "counter", 4, "runner_counter_4_000001"),
                ("sample_runner_counter_8_000002", "counter", 8, "runner_counter_8_000002"),
                ("sample_runner_fifo_8_000003", "fifo", 8, "runner_fifo_8_000003"),
            ],
        )
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_runner.RunnerConfigTest -q
```

Expected: fail with `ModuleNotFoundError` or `ImportError` for `LLM.src.sr2fpga_agent.runner`.

- [ ] **Step 3: Implement config dataclasses and sample planning**

Create `LLM/src/sr2fpga_agent/runner.py` with:

```python
"""Autonomous batch runner for SR2FPGA trajectory generation."""

from __future__ import annotations

import argparse
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


def load_runner_config(path: Path) -> RunnerConfig:
    raw = _load_mapping(path)
    return RunnerConfig(
        dataset_root=Path(str(raw["dataset_root"])),
        export_root=Path(str(raw["export_root"])),
        run_root=Path(str(raw["run_root"])),
        provider=str(raw.get("provider", "deterministic")),
        repair_provider=str(raw.get("repair_provider", "none")),
        max_attempts=int(raw.get("max_attempts", 1)),
        refresh_exports=bool(raw.get("refresh_exports", True)),
        line_b_targets=dict(raw.get("line_b_targets", {})),
        tasks=[
            TaskConfig(
                source=str(item.get("source", raw.get("provider", "deterministic"))),
                task_type=str(item["task_type"]),
                widths=[int(width) for width in item.get("widths", [8])],
                count=int(item.get("count", 1)),
            )
            for item in raw.get("tasks", [])
        ],
        model=str(raw.get("model", "deepseek-v4-flash")),
        base_url=str(raw.get("base_url", "https://api.deepseek.com")),
        api_key_env=str(raw.get("api_key_env", "DEEPSEEK_API_KEY")),
        platform=str(raw.get("platform", "generic_verilog")),
    )


def _load_mapping(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        return json.loads(text)
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_runner.RunnerConfigTest -q
```

Expected: `OK`.

- [ ] **Step 5: Commit**

```bash
git add LLM/src/sr2fpga_agent/runner.py LLM/tests/test_sr2fpga_agent_runner.py
git commit -m "Add SR2FPGA runner config planning"
```

---

### Task 2: Bucket Classification And Run State

**Files:**
- Modify: `LLM/src/sr2fpga_agent/runner.py`
- Modify: `LLM/tests/test_sr2fpga_agent_runner.py`

- [ ] **Step 1: Add failing tests for bucket classification and state persistence**

Append these tests to `RunnerConfigTest`:

```python
    def test_classify_sample_bucket(self) -> None:
        self.assertEqual(classify_sample_bucket({"pass_level": "L3", "failure_count": 0}), "success_l3")
        self.assertEqual(classify_sample_bucket({"pass_level": "L1", "failure_count": 2}), "repair_trajectory")
        self.assertEqual(classify_sample_bucket({"pass_level": "L0", "failure_count": 0}), "rejected")

    def test_run_state_round_trip_and_skip_completed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "run_state.json"
            state = RunState(
                run_id="run_test",
                next_index=1,
                completed_samples=["sample_runner_counter_4_000001"],
                buckets={"success_l3": ["sample_runner_counter_4_000001"], "repair_trajectory": [], "rejected": []},
                failure_types={},
                exports_refreshed=False,
            )

            write_run_state(state_path, state)
            loaded = read_run_state(state_path)

            self.assertEqual(loaded.run_id, "run_test")
            self.assertEqual(loaded.next_index, 1)
            self.assertEqual(loaded.completed_samples, ["sample_runner_counter_4_000001"])
            self.assertTrue(should_skip_sample(loaded, "sample_runner_counter_4_000001"))
            self.assertFalse(should_skip_sample(loaded, "sample_runner_counter_8_000002"))
```

Update imports at the top:

```python
from LLM.src.sr2fpga_agent.runner import (
    RunState,
    RunnerConfig,
    TaskConfig,
    classify_sample_bucket,
    load_runner_config,
    planned_samples,
    read_run_state,
    should_skip_sample,
    write_run_state,
)
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_runner.RunnerConfigTest.test_classify_sample_bucket LLM.tests.test_sr2fpga_agent_runner.RunnerConfigTest.test_run_state_round_trip_and_skip_completed -q
```

Expected: fail with missing `RunState` or missing classification functions.

- [ ] **Step 3: Implement bucket classification and state helpers**

Add to `runner.py`:

```python
@dataclass(frozen=True)
class RunState:
    run_id: str
    next_index: int
    completed_samples: list[str]
    buckets: dict[str, list[str]]
    failure_types: dict[str, int]
    exports_refreshed: bool


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
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_runner.RunnerConfigTest -q
```

Expected: `OK`.

- [ ] **Step 5: Commit**

```bash
git add LLM/src/sr2fpga_agent/runner.py LLM/tests/test_sr2fpga_agent_runner.py
git commit -m "Add SR2FPGA runner state buckets"
```

---

### Task 3: Batch Execution Loop

**Files:**
- Modify: `LLM/src/sr2fpga_agent/runner.py`
- Modify: `LLM/tests/test_sr2fpga_agent_runner.py`

- [ ] **Step 1: Add failing test for deterministic batch run and export refresh**

Append this test:

```python
    def test_run_batch_records_samples_summary_and_exports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = RunnerConfig(
                dataset_root=root / "datasets",
                export_root=root / "exports",
                run_root=root / "runs",
                provider="deterministic",
                repair_provider="none",
                max_attempts=1,
                refresh_exports=True,
                line_b_targets={"l3_success_ratio": 0.4, "repair_trajectory_ratio": 0.6, "max_samples": 1},
                tasks=[TaskConfig(source="deterministic", task_type="counter", widths=[4], count=1)],
            )

            summary = run_batch(config, run_id="run_unit")

            run_dir = root / "runs" / "run_unit"
            self.assertEqual(summary["run_id"], "run_unit")
            self.assertEqual(summary["total_completed"], 1)
            self.assertEqual(summary["buckets"]["success_l3"], ["sample_runner_counter_4_000001"])
            self.assertTrue((run_dir / "run_state.json").exists())
            self.assertTrue((run_dir / "summary.json").exists())
            self.assertTrue((run_dir / "events.jsonl").exists())
            self.assertTrue((root / "datasets/sample_runner_counter_4_000001/eval/labels.json").exists())
            self.assertTrue((root / "exports/requirement_to_project.jsonl").exists())
```

Update imports:

```python
from LLM.src.sr2fpga_agent.runner import (
    RunState,
    RunnerConfig,
    TaskConfig,
    classify_sample_bucket,
    load_runner_config,
    planned_samples,
    read_run_state,
    run_batch,
    should_skip_sample,
    write_run_state,
)
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_runner.RunnerConfigTest.test_run_batch_records_samples_summary_and_exports -q
```

Expected: fail with missing `run_batch`.

- [ ] **Step 3: Implement `run_batch` and summary writing**

Add to `runner.py`:

```python
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
            state = _record_rejected(state, sample.sample_id, "sample_exists")
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


def _config_to_jsonable(config: RunnerConfig) -> dict[str, Any]:
    data = asdict(config)
    data["dataset_root"] = str(config.dataset_root)
    data["export_root"] = str(config.export_root)
    data["run_root"] = str(config.run_root)
    return data


def _record_completed(
    state: RunState,
    sample_id: str,
    next_index: int,
    bucket: str,
    sample_dir: Path,
) -> RunState:
    buckets = {key: list(value) for key, value in state.buckets.items()}
    buckets.setdefault(bucket, []).append(sample_id)
    failure_types = dict(state.failure_types)
    for failure_type in _sample_failure_types(sample_dir):
        failure_types[failure_type] = failure_types.get(failure_type, 0) + 1
    return RunState(
        run_id=state.run_id,
        next_index=next_index,
        completed_samples=[*state.completed_samples, sample_id],
        buckets=buckets,
        failure_types=failure_types,
        exports_refreshed=False,
    )


def _record_rejected(state: RunState, sample_id: str, reason: str) -> RunState:
    buckets = {key: list(value) for key, value in state.buckets.items()}
    buckets.setdefault("rejected", []).append(sample_id)
    failure_types = dict(state.failure_types)
    failure_types[reason] = failure_types.get(reason, 0) + 1
    return RunState(
        run_id=state.run_id,
        next_index=state.next_index + 1,
        completed_samples=[*state.completed_samples, sample_id],
        buckets=buckets,
        failure_types=failure_types,
        exports_refreshed=False,
    )


def _read_labels(sample_dir: Path) -> dict[str, Any]:
    return json.loads((sample_dir / "eval" / "labels.json").read_text(encoding="utf-8"))


def _sample_failure_types(sample_dir: Path) -> list[str]:
    failure_types: list[str] = []
    attempts_dir = sample_dir / "attempts"
    if not attempts_dir.exists():
        return failure_types
    for diagnosis_path in sorted(attempts_dir.glob("attempt_*/diagnosis.json")):
        diagnosis = json.loads(diagnosis_path.read_text(encoding="utf-8"))
        failure_type = diagnosis.get("failure_type")
        if isinstance(failure_type, str):
            failure_types.append(failure_type)
    return failure_types


def _summary(config: RunnerConfig, state: RunState) -> dict[str, Any]:
    return {
        "run_id": state.run_id,
        "dataset_root": str(config.dataset_root),
        "export_root": str(config.export_root),
        "total_completed": len(state.completed_samples),
        "buckets": state.buckets,
        "failure_types": state.failure_types,
        "exports_refreshed": state.exports_refreshed,
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _append_event(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as output:
        output.write(json.dumps(payload, ensure_ascii=False) + "\n")
```

- [ ] **Step 4: Run runner tests**

Run:

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_runner -q
```

Expected: `OK`.

- [ ] **Step 5: Commit**

```bash
git add LLM/src/sr2fpga_agent/runner.py LLM/tests/test_sr2fpga_agent_runner.py
git commit -m "Add autonomous SR2FPGA batch runner"
```

---

### Task 4: Runner CLI And Example Config

**Files:**
- Modify: `LLM/src/sr2fpga_agent/runner.py`
- Create: `configs/sr2fpga_agent.example.yaml`
- Modify: `LLM/tests/test_sr2fpga_agent_runner.py`

- [ ] **Step 1: Add failing CLI test**

Append this test:

```python
    def test_runner_main_loads_config_and_prints_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / "runner.json"
            config_path.write_text(
                json.dumps(
                    {
                        "dataset_root": str(root / "datasets"),
                        "export_root": str(root / "exports"),
                        "run_root": str(root / "runs"),
                        "provider": "deterministic",
                        "repair_provider": "none",
                        "max_attempts": 1,
                        "refresh_exports": True,
                        "line_b_targets": {"max_samples": 1},
                        "tasks": [{"source": "deterministic", "task_type": "counter", "widths": [4], "count": 1}],
                    }
                ),
                encoding="utf-8",
            )

            output = run_main_for_test(["--config", str(config_path), "--run-id", "run_cli_unit"])

            self.assertIn("run_id=run_cli_unit", output)
            self.assertIn("total_completed=1", output)
```

Add this helper at the bottom of the test file:

```python
def run_main_for_test(argv: list[str]) -> str:
    import io
    from contextlib import redirect_stdout
    from LLM.src.sr2fpga_agent import runner

    output = io.StringIO()
    with redirect_stdout(output):
        runner.main(argv)
    return output.getvalue()
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_runner.RunnerConfigTest.test_runner_main_loads_config_and_prints_summary -q
```

Expected: fail with missing `main`.

- [ ] **Step 3: Implement CLI main**

Add to `runner.py`:

```python
def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run an autonomous SR2FPGA trajectory batch.")
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--run-id", default="")
    parser.add_argument("--no-resume", action="store_true")
    args = parser.parse_args(argv)

    config = load_runner_config(args.config)
    summary = run_batch(config, run_id=args.run_id or None, resume=not args.no_resume)
    print(f"run_id={summary['run_id']}")
    print(f"total_completed={summary['total_completed']}")
    print(f"success_l3={len(summary['buckets'].get('success_l3', []))}")
    print(f"repair_trajectory={len(summary['buckets'].get('repair_trajectory', []))}")
    print(f"rejected={len(summary['buckets'].get('rejected', []))}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Add example config**

Create `configs/sr2fpga_agent.example.yaml`:

```yaml
dataset_root: datasets/sr2fpga_rtl_v1
export_root: datasets/sr2fpga_rtl_v1_exports
run_root: tmp/sr2fpga_runs
provider: deepseek
repair_provider: deepseek
model: deepseek-v4-flash
base_url: https://api.deepseek.com
api_key_env: DEEPSEEK_API_KEY
platform: generic_verilog
max_attempts: 4
refresh_exports: true

line_b_targets:
  l3_success_ratio: 0.4
  repair_trajectory_ratio: 0.6
  max_samples: 4

tasks:
  - source: deepseek
    task_type: uart_tx
    widths: [8]
    count: 2
  - source: deepseek
    task_type: spi_master
    widths: [8]
    count: 2
```

- [ ] **Step 5: Run CLI test and full runner tests**

Run:

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_runner -q
```

Expected: `OK`.

- [ ] **Step 6: Commit**

```bash
git add LLM/src/sr2fpga_agent/runner.py LLM/tests/test_sr2fpga_agent_runner.py configs/sr2fpga_agent.example.yaml
git commit -m "Add SR2FPGA runner CLI"
```

---

### Task 5: Documentation And Verification

**Files:**
- Modify: `LLM/README.md`
- Modify: `docs/sr2fpga-agent-handoff-2026-06-22.md`

- [ ] **Step 1: Update README with runner usage**

Add this section after the DeepSeek repair CLI example in `LLM/README.md`:

````markdown
### Autonomous Batch Runner

Use the runner when generating more than one sample. The runner reads a config,
creates sample IDs, runs the existing `DataGenerationAgent`, records a resumable
run state, refreshes training exports, and prints a compact summary.

```bash
set -a
source .env
set +a

python3 -m LLM.src.sr2fpga_agent.runner \
  --config configs/sr2fpga_agent.example.yaml \
  --run-id deepseek-multimodule-smoke
```

Run state and full logs live under `tmp/sr2fpga_runs/<run-id>/`. Keep those logs
local by default. Commit only milestone dataset snapshots or compact summaries
when they are useful for research traceability.
````

- [ ] **Step 2: Update handoff note**

Add this note near the bottom of `docs/sr2fpga-agent-handoff-2026-06-22.md`:

```markdown
## Autonomous Runner Plan

Spec path:
`docs/superpowers/specs/2026-06-23-sr2fpga-autonomous-trajectory-runner-design.md`

Plan path:
`docs/superpowers/plans/2026-06-23-sr2fpga-autonomous-trajectory-runner.md`

Confirmed decisions:

- implement the runner shell first around existing deterministic and DeepSeek
  sources;
- keep large future datasets local by default, with only milestone snapshots
  committed;
- keep full run state/logs under ignored `tmp/sr2fpga_runs/`; commit compact
  summaries only when useful for research traceability.
```

- [ ] **Step 3: Run full tests**

Run:

```bash
python3 -m unittest discover -s LLM/tests -q
```

Expected: all tests pass.

- [ ] **Step 4: Run a deterministic runner smoke**

Use a temporary JSON config so the smoke does not touch committed datasets:

```bash
python3 - <<'PY'
import json
import tempfile
from pathlib import Path
from LLM.src.sr2fpga_agent.runner import main

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    config = root / "runner.json"
    config.write_text(json.dumps({
        "dataset_root": str(root / "datasets"),
        "export_root": str(root / "exports"),
        "run_root": str(root / "runs"),
        "provider": "deterministic",
        "repair_provider": "none",
        "max_attempts": 1,
        "refresh_exports": True,
        "line_b_targets": {"max_samples": 1},
        "tasks": [{"source": "deterministic", "task_type": "counter", "widths": [4], "count": 1}]
    }), encoding="utf-8")
    main(["--config", str(config), "--run-id", "smoke"])
PY
```

Expected output includes:

```text
run_id=smoke
total_completed=1
success_l3=1
```

- [ ] **Step 5: Inspect git status**

Run:

```bash
git status --short --branch
```

Expected: only planned source/test/doc/config files changed, plus pre-existing untracked `.claude/`, `CLAUDE.md`, report PDFs, and `tmp/`.

- [ ] **Step 6: Commit**

```bash
git add LLM/README.md docs/sr2fpga-agent-handoff-2026-06-22.md
git commit -m "Document SR2FPGA autonomous runner"
```

---

## Final Verification

Run:

```bash
python3 -m unittest discover -s LLM/tests -q
python3 -m unittest LLM.tests.test_sr2fpga_agent_runner -q
git log --oneline -8
git status --short --branch
```

Expected:

- all unit tests pass;
- runner tests pass;
- recent commits include runner config, state/buckets, batch runner, CLI, and docs;
- no `.env` or secret files are staged;
- generated temporary run logs remain under ignored `tmp/`.

## Deferred Work

- Compositional component-library generator.
- First-class L0 System-HIS consistency checker.
- `docs/runs/` compact summary publishing.
- OpenXC7/Vivado L4 runner backend.
- Local model provider.
- Real IP anchors.
