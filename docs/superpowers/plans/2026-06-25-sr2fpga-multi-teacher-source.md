# SR2FPGA Multi-Teacher Source Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let one runner batch draw candidate projects from several independent teacher models (Claude, GPT-5.5, DeepSeek, Qwen, deterministic), each with its own connection settings, so the trajectory dataset is multi-teacher.

**Architecture:** Add an optional per-source connection table (`sources:`) to the runner config and a resolver that maps each task's `source` to a `SourceConnection`. Reuse the existing OpenAI-API-shaped `DeepSeekClient` for every LLM teacher (it only sends `Authorization: Bearer <key>` to `<base_url>/chat/completions`). New teachers run the validated two-stage REQ2HIS -> HIS2PROJECT path. Per-teacher metrics already exist via `calibration_matrix["source"]`.

**Tech Stack:** Python 3.13 stdlib, `unittest`. Spec: `docs/superpowers/specs/2026-06-25-sr2fpga-multi-teacher-source-design.md`.

## Global Constraints

- Run all Python **from the repo root**; modules use absolute imports `from LLM.src.sr2fpga_agent...`.
- Tests are `unittest`; run with `python3 -m unittest LLM.tests.<module> -q`. No live API calls in tests — mock `DeepSeekClient.chat` or inject a fake client.
- **Backward compatibility is mandatory:** a config with no `sources:` block must behave exactly as today (`deterministic`, `deepseek`, `deepseek-his-v12` sources unchanged).
- New teachers use **`generation_mode: two_stage` only**; `direct` mode is not implemented for new sources.
- Connection table stores only the env var **name** (`api_key_env`), never a key value. Never commit keys.
- LF line endings for `*.py`/`*.yaml` (enforced by `.gitattributes`).
- LLM source kinds (treated as `natural_llm`): `openai_compat`, `deepseek`, `deepseek-his-v12`.

---

### Task 1: `SourceConnection` dataclass + `sources:` config parsing

**Files:**
- Modify: `LLM/src/sr2fpga_agent/runner.py` (add dataclass near `TaskConfig`; add `sources` field to `RunnerConfig`; parse in `load_runner_config`)
- Test: `LLM/tests/test_sr2fpga_agent_multi_teacher.py` (new)

**Interfaces:**
- Produces:
  - `SourceConnection(name: str, kind: str, model: str = "", base_url: str = "", api_key_env: str = "", generation_mode: str = "")` — frozen dataclass.
  - `RunnerConfig.sources: dict[str, SourceConnection]` (new field, default empty).
  - `load_runner_config` parses a top-level `sources:` mapping.

- [ ] **Step 1: Write the failing test**

Create `LLM/tests/test_sr2fpga_agent_multi_teacher.py`:

```python
import json
import tempfile
import unittest
from pathlib import Path

from LLM.src.sr2fpga_agent.runner import (
    RunnerConfig,
    SourceConnection,
    load_runner_config,
)


def _write_config(tmp: str, sources: dict) -> Path:
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
                "line_b_targets": {},
                "sources": sources,
                "tasks": [
                    {"source": "claude", "task_type": "counter", "widths": [8], "count": 1}
                ],
            }
        ),
        encoding="utf-8",
    )
    return config_path


class SourcesParsingTest(unittest.TestCase):
    def test_sources_block_parsed_into_connections(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_config(
                tmp,
                {
                    "claude": {
                        "kind": "openai_compat",
                        "model": "claude-opus-4-8",
                        "base_url": "https://api.anthropic.com/v1",
                        "api_key_env": "ANTHROPIC_API_KEY",
                        "generation_mode": "two_stage",
                    }
                },
            )
            config = load_runner_config(path)
            self.assertIn("claude", config.sources)
            conn = config.sources["claude"]
            self.assertEqual(conn.kind, "openai_compat")
            self.assertEqual(conn.model, "claude-opus-4-8")
            self.assertEqual(conn.base_url, "https://api.anthropic.com/v1")
            self.assertEqual(conn.api_key_env, "ANTHROPIC_API_KEY")
            self.assertEqual(conn.generation_mode, "two_stage")

    def test_missing_sources_block_defaults_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "runner.json"
            config_path.write_text(
                json.dumps(
                    {
                        "dataset_root": "d",
                        "export_root": "e",
                        "run_root": "r",
                        "tasks": [],
                    }
                ),
                encoding="utf-8",
            )
            config = load_runner_config(config_path)
            self.assertEqual(config.sources, {})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest LLM.tests.test_sr2fpga_agent_multi_teacher -q`
Expected: FAIL with `ImportError: cannot import name 'SourceConnection'`.

- [ ] **Step 3: Add the dataclass and config field**

In `runner.py`, after the `TaskConfig` dataclass (around line 47), add:

```python
@dataclass(frozen=True)
class SourceConnection:
    name: str
    kind: str
    model: str = ""
    base_url: str = ""
    api_key_env: str = ""
    generation_mode: str = ""
```

In `RunnerConfig` (frozen dataclass), add a field after `sample_id_prefix`:

```python
    sources: dict[str, "SourceConnection"] = field(default_factory=dict)
```

In `load_runner_config`, add a `sources=` argument to the `RunnerConfig(...)` construction:

```python
        sources=_load_sources(raw.get("sources", {})),
```

Add the helper near `_load_task_config`:

```python
def _load_sources(raw: dict[str, Any]) -> dict[str, SourceConnection]:
    sources: dict[str, SourceConnection] = {}
    for name, item in raw.items():
        sources[str(name)] = SourceConnection(
            name=str(name),
            kind=str(item.get("kind", "openai_compat")),
            model=str(item.get("model", "")),
            base_url=str(item.get("base_url", "")),
            api_key_env=str(item.get("api_key_env", "")),
            generation_mode=str(item.get("generation_mode", "")),
        )
    return sources
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest LLM.tests.test_sr2fpga_agent_multi_teacher -q`
Expected: PASS (2 tests).

- [ ] **Step 5: Run the full suite to confirm no regression**

Run: `python3 -m unittest discover -s LLM/tests -q`
Expected: OK (existing count + 2).

- [ ] **Step 6: Commit**

```bash
git add LLM/src/sr2fpga_agent/runner.py LLM/tests/test_sr2fpga_agent_multi_teacher.py
git commit -m "feat(runner): parse per-source teacher connection table"
```

---

### Task 2: `resolve_source_connection` resolver with legacy fallback

**Files:**
- Modify: `LLM/src/sr2fpga_agent/runner.py` (add resolver)
- Test: `LLM/tests/test_sr2fpga_agent_multi_teacher.py`

**Interfaces:**
- Consumes: `RunnerConfig.sources`, `SourceConnection` (Task 1).
- Produces: `resolve_source_connection(config: RunnerConfig, source: str) -> SourceConnection`. For a source present in `config.sources`, returns it. For `"deterministic"`, returns a deterministic connection. For legacy `"deepseek"`/`"deepseek-his-v12"`/other, synthesizes a connection from the global `config.model`/`base_url`/`api_key_env`.

- [ ] **Step 1: Write the failing test**

Append to `LLM/tests/test_sr2fpga_agent_multi_teacher.py`:

```python
from LLM.src.sr2fpga_agent.runner import resolve_source_connection


def _base_config(**overrides) -> RunnerConfig:
    base = dict(
        dataset_root=Path("d"),
        export_root=Path("e"),
        run_root=Path("r"),
        provider="deterministic",
        repair_provider="none",
        max_attempts=1,
        refresh_exports=True,
        line_b_targets={},
        tasks=[],
    )
    base.update(overrides)
    return RunnerConfig(**base)


class ResolveSourceTest(unittest.TestCase):
    def test_resolves_named_source_from_table(self) -> None:
        conn = SourceConnection(
            name="claude", kind="openai_compat", model="claude-opus-4-8",
            base_url="https://api.anthropic.com/v1", api_key_env="ANTHROPIC_API_KEY",
            generation_mode="two_stage",
        )
        config = _base_config(sources={"claude": conn})
        self.assertIs(resolve_source_connection(config, "claude"), conn)

    def test_deterministic_source_needs_no_entry(self) -> None:
        config = _base_config()
        conn = resolve_source_connection(config, "deterministic")
        self.assertEqual(conn.kind, "deterministic")

    def test_legacy_deepseek_his_v12_falls_back_to_global(self) -> None:
        config = _base_config(
            model="deepseek-v4-flash",
            base_url="https://api.deepseek.com",
            api_key_env="DEEPSEEK_API_KEY",
        )
        conn = resolve_source_connection(config, "deepseek-his-v12")
        self.assertEqual(conn.kind, "deepseek-his-v12")
        self.assertEqual(conn.generation_mode, "two_stage")
        self.assertEqual(conn.model, "deepseek-v4-flash")
        self.assertEqual(conn.api_key_env, "DEEPSEEK_API_KEY")

    def test_legacy_deepseek_direct_falls_back_to_global(self) -> None:
        config = _base_config(api_key_env="DEEPSEEK_API_KEY")
        conn = resolve_source_connection(config, "deepseek")
        self.assertEqual(conn.kind, "deepseek")
        self.assertEqual(conn.generation_mode, "direct")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest LLM.tests.test_sr2fpga_agent_multi_teacher.ResolveSourceTest -q`
Expected: FAIL with `ImportError: cannot import name 'resolve_source_connection'`.

- [ ] **Step 3: Implement the resolver**

In `runner.py`, add near the other `_sample_*` helpers:

```python
LLM_SOURCE_KINDS = {"openai_compat", "deepseek", "deepseek-his-v12"}


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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest LLM.tests.test_sr2fpga_agent_multi_teacher.ResolveSourceTest -q`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add LLM/src/sr2fpga_agent/runner.py LLM/tests/test_sr2fpga_agent_multi_teacher.py
git commit -m "feat(runner): resolve task source to a connection with legacy fallback"
```

---

### Task 3: Connection-based generator builder in `cli.py`

**Files:**
- Modify: `LLM/src/sr2fpga_agent/cli.py` (add `build_project_generator_for_connection`)
- Test: `LLM/tests/test_sr2fpga_agent_multi_teacher.py`

**Interfaces:**
- Consumes: `SourceConnection` (Task 1); existing `DeepSeekClient`, `DeepSeekConfig`, `DeepSeekProjectGenerator`, `DeepSeekTwoStageProjectGenerator`.
- Produces: `build_project_generator_for_connection(connection: SourceConnection, event_sink=None)`. Returns `None` for `deterministic`; a `DeepSeekProjectGenerator` for `kind == "deepseek"` (legacy direct); a `DeepSeekTwoStageProjectGenerator` for `openai_compat`/`deepseek-his-v12`. Raises `SystemExit` if the connection's `api_key_env` is unset.

- [ ] **Step 1: Write the failing test**

Append to `LLM/tests/test_sr2fpga_agent_multi_teacher.py`:

```python
import os
from unittest.mock import patch

from LLM.src.sr2fpga_agent.cli import build_project_generator_for_connection
from LLM.src.sr2fpga_agent.deepseek import (
    DeepSeekProjectGenerator,
    DeepSeekTwoStageProjectGenerator,
)


class ConnectionBuilderTest(unittest.TestCase):
    def test_deterministic_connection_returns_none(self) -> None:
        conn = SourceConnection(name="deterministic", kind="deterministic")
        self.assertIsNone(build_project_generator_for_connection(conn))

    def test_openai_compat_builds_two_stage_with_resolved_endpoint(self) -> None:
        conn = SourceConnection(
            name="claude", kind="openai_compat", model="claude-opus-4-8",
            base_url="https://api.anthropic.com/v1", api_key_env="ANTHROPIC_API_KEY",
            generation_mode="two_stage",
        )
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test"}, clear=False):
            generator = build_project_generator_for_connection(conn)
        self.assertIsInstance(generator, DeepSeekTwoStageProjectGenerator)
        client_config = generator.his_project_generator.client.config
        self.assertEqual(client_config.model, "claude-opus-4-8")
        self.assertEqual(client_config.base_url, "https://api.anthropic.com/v1")
        self.assertEqual(client_config.api_key, "sk-test")

    def test_legacy_deepseek_kind_builds_single_stage(self) -> None:
        conn = SourceConnection(
            name="deepseek", kind="deepseek", model="deepseek-v4-flash",
            base_url="https://api.deepseek.com", api_key_env="DEEPSEEK_API_KEY",
            generation_mode="direct",
        )
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "sk-ds"}, clear=False):
            generator = build_project_generator_for_connection(conn)
        self.assertIsInstance(generator, DeepSeekProjectGenerator)

    def test_missing_key_raises(self) -> None:
        conn = SourceConnection(
            name="gpt55", kind="openai_compat", model="gpt-5.5",
            base_url="https://api.openai.com/v1", api_key_env="OPENAI_API_KEY_ABSENT_FOR_TEST",
            generation_mode="two_stage",
        )
        with self.assertRaises(SystemExit):
            build_project_generator_for_connection(conn)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest LLM.tests.test_sr2fpga_agent_multi_teacher.ConnectionBuilderTest -q`
Expected: FAIL with `ImportError: cannot import name 'build_project_generator_for_connection'`.

- [ ] **Step 3: Implement the builder**

In `cli.py`, add (the `SourceConnection` import is only needed for typing; use a string annotation to avoid a circular import with `runner.py`):

```python
def build_project_generator_for_connection(connection, event_sink=None):
    kind = connection.kind
    if kind == "deterministic":
        return None
    if kind not in {"openai_compat", "deepseek", "deepseek-his-v12"}:
        raise SystemExit(f"Unsupported source kind: {kind}")
    api_key = os.environ.get(connection.api_key_env)
    if not api_key:
        raise SystemExit(f"{connection.api_key_env} is not set")
    client = DeepSeekClient(
        DeepSeekConfig(
            api_key=api_key,
            model=connection.model,
            base_url=connection.base_url,
        )
    )
    if kind == "deepseek":
        return DeepSeekProjectGenerator(client)
    return DeepSeekTwoStageProjectGenerator(client, event_sink=event_sink)
```

Confirm `cli.py` already imports `DeepSeekProjectGenerator`, `DeepSeekTwoStageProjectGenerator`, `DeepSeekClient`, `DeepSeekConfig` (it does — they are used by `build_project_generator`).

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest LLM.tests.test_sr2fpga_agent_multi_teacher.ConnectionBuilderTest -q`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add LLM/src/sr2fpga_agent/cli.py LLM/tests/test_sr2fpga_agent_multi_teacher.py
git commit -m "feat(cli): build project generator from a resolved source connection"
```

---

### Task 4: Wire runner per-sample dispatch through the resolver

**Files:**
- Modify: `LLM/src/sr2fpga_agent/runner.py` (`_project_generator_for_sample`)
- Test: `LLM/tests/test_sr2fpga_agent_multi_teacher.py`

**Interfaces:**
- Consumes: `resolve_source_connection` (Task 2), `build_project_generator_for_connection` (Task 3).
- Produces: `_project_generator_for_sample(project_generators, config, sample, events_path)` now resolves the sample's connection, builds via the connection builder, attaches a per-sample `event_sink` when `generation_mode == "two_stage"`, and caches per source (per-sample cache key for two-stage sources so each gets its own event sink).

- [ ] **Step 1: Write the failing test**

Append to `LLM/tests/test_sr2fpga_agent_multi_teacher.py`:

```python
from LLM.src.sr2fpga_agent.runner import PlannedSample, _project_generator_for_sample


class PerSampleDispatchTest(unittest.TestCase):
    def test_two_different_teachers_resolve_to_different_endpoints(self) -> None:
        claude = SourceConnection(
            name="claude", kind="openai_compat", model="claude-opus-4-8",
            base_url="https://api.anthropic.com/v1", api_key_env="ANTHROPIC_API_KEY",
            generation_mode="two_stage",
        )
        gpt = SourceConnection(
            name="gpt55", kind="openai_compat", model="gpt-5.5",
            base_url="https://api.openai.com/v1", api_key_env="OPENAI_API_KEY",
            generation_mode="two_stage",
        )
        config = _base_config(sources={"claude": claude, "gpt55": gpt})

        def make_sample(source: str) -> PlannedSample:
            return PlannedSample(
                sample_id=f"sample_{source}", source=source, task_type="counter",
                width=8, project_name=source, requirement="r",
                requirement_style="simple_prompt",
            )

        cache: dict = {}
        events = Path("ignored")
        with patch.dict(
            os.environ,
            {"ANTHROPIC_API_KEY": "sk-a", "OPENAI_API_KEY": "sk-o"},
            clear=False,
        ):
            gen_claude = _project_generator_for_sample(cache, config, make_sample("claude"), events)
            gen_gpt = _project_generator_for_sample(cache, config, make_sample("gpt55"), events)

        self.assertEqual(
            gen_claude.his_project_generator.client.config.base_url,
            "https://api.anthropic.com/v1",
        )
        self.assertEqual(gen_gpt.his_project_generator.client.config.model, "gpt-5.5")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest LLM.tests.test_sr2fpga_agent_multi_teacher.PerSampleDispatchTest -q`
Expected: FAIL (current `_project_generator_for_sample` calls `build_project_generator(provider=sample.source, ...)`, which raises `SystemExit: Unsupported provider: claude`).

- [ ] **Step 3: Rewrite `_project_generator_for_sample`**

Replace the body of `_project_generator_for_sample` in `runner.py` with:

```python
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
            _generation_event_sink(events_path, sample)
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
```

Update the import at the top of `runner.py`:

```python
from LLM.src.sr2fpga_agent.cli import (
    build_project_generator,
    build_project_generator_for_connection,
    build_repairer,
)
```

(`build_project_generator` may still be imported; leave it if other code uses it, otherwise drop it.)

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest LLM.tests.test_sr2fpga_agent_multi_teacher.PerSampleDispatchTest -q`
Expected: PASS (1 test).

- [ ] **Step 5: Run the full suite (the existing `deepseek-his-v12` path must still work)**

Run: `python3 -m unittest discover -s LLM/tests -q`
Expected: OK. If a `deepseek-his-v12` runner test fails, confirm the resolver returns `generation_mode == "two_stage"` for it (Task 2) so the event sink and cache key match prior behavior.

- [ ] **Step 6: Commit**

```bash
git add LLM/src/sr2fpga_agent/runner.py LLM/tests/test_sr2fpga_agent_multi_teacher.py
git commit -m "feat(runner): dispatch each sample through its resolved teacher connection"
```

---

### Task 5: Metadata driven by connection kind / generation_mode

**Files:**
- Modify: `LLM/src/sr2fpga_agent/runner.py` (`_sample_failure_origin`, `_sample_system_his_schema_version`, `PlannedSample.metadata`, call sites at the `sample_completed` event and `_generation_event_sink`)
- Test: `LLM/tests/test_sr2fpga_agent_multi_teacher.py`

**Interfaces:**
- Consumes: `resolve_source_connection`, `LLM_SOURCE_KINDS` (Task 2).
- Produces:
  - `_sample_failure_origin(sample: PlannedSample, config: RunnerConfig) -> str`
  - `_sample_system_his_schema_version(sample: PlannedSample, config: RunnerConfig) -> str`
  - `PlannedSample.metadata(config)` additionally records `"model"` (the resolved teacher model).

- [ ] **Step 1: Write the failing test**

Append to `LLM/tests/test_sr2fpga_agent_multi_teacher.py`:

```python
class MetadataTest(unittest.TestCase):
    def _sample(self, source: str) -> PlannedSample:
        return PlannedSample(
            sample_id=f"s_{source}", source=source, task_type="counter", width=8,
            project_name="p", requirement="r", requirement_style="simple_prompt",
            difficulty_tier="T1",
        )

    def test_openai_compat_two_stage_is_clean_v12_natural_llm(self) -> None:
        claude = SourceConnection(
            name="claude", kind="openai_compat", model="claude-opus-4-8",
            base_url="https://api.anthropic.com/v1", api_key_env="ANTHROPIC_API_KEY",
            generation_mode="two_stage",
        )
        config = _base_config(sources={"claude": claude})
        metadata = self._sample("claude").metadata(config)
        self.assertEqual(metadata["failure_origin"], "natural_llm")
        self.assertEqual(metadata["system_his_schema_version"], "system-his-v1.2")
        self.assertEqual(metadata["training_split"], "clean")
        self.assertEqual(metadata["model"], "claude-opus-4-8")

    def test_deterministic_metadata_unchanged(self) -> None:
        config = _base_config()
        metadata = self._sample("deterministic").metadata(config)
        self.assertEqual(metadata["failure_origin"], "deterministic_template")
        self.assertEqual(metadata["system_his_schema_version"], "system-his-v1.2")

    def test_legacy_deepseek_direct_is_v11_quarantine(self) -> None:
        config = _base_config(api_key_env="DEEPSEEK_API_KEY")
        metadata = self._sample("deepseek").metadata(config)
        self.assertEqual(metadata["failure_origin"], "natural_llm")
        self.assertEqual(metadata["system_his_schema_version"], "system-his-v1.1")
        self.assertEqual(metadata["training_split"], "quarantine")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest LLM.tests.test_sr2fpga_agent_multi_teacher.MetadataTest -q`
Expected: FAIL (current `metadata` has no `"model"` key and `failure_origin` for `claude` returns the raw source string `"claude"`).

- [ ] **Step 3: Update the helpers and `metadata`**

Replace `_sample_failure_origin` in `runner.py`:

```python
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
```

Replace `_sample_system_his_schema_version`:

```python
def _sample_system_his_schema_version(sample: PlannedSample, config: RunnerConfig) -> str:
    connection = resolve_source_connection(config, sample.source)
    if connection.kind == "deterministic" or connection.generation_mode == "two_stage":
        return "system-his-v1.2"
    return "system-his-v1.1"
```

In `PlannedSample.metadata`, change the two helper calls to pass `config`, and add the resolved model:

```python
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
            "topology_id": self.topology_id,
            "requirement_style": self.requirement_style,
        }
```

Fix the other two `_sample_failure_origin(sample)` call sites to pass `config`:
- In `run_batch`, the `sample_completed` event dict: `"failure_origin": _sample_failure_origin(sample, config),`
- `_generation_event_sink` must accept `config`. Change its signature to `_generation_event_sink(events_path, sample, config)`, use `_sample_failure_origin(sample, config)` inside, and update its one caller in `_project_generator_for_sample` (Task 4) to `_generation_event_sink(events_path, sample, config)`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest LLM.tests.test_sr2fpga_agent_multi_teacher.MetadataTest -q`
Expected: PASS (3 tests).

- [ ] **Step 5: Run the full suite**

Run: `python3 -m unittest discover -s LLM/tests -q`
Expected: OK. Watch for existing tests calling `_sample_failure_origin` with one arg — update them to pass a config if any fail.

- [ ] **Step 6: Commit**

```bash
git add LLM/src/sr2fpga_agent/runner.py LLM/tests/test_sr2fpga_agent_multi_teacher.py
git commit -m "feat(runner): derive failure-origin/schema/model from teacher connection"
```

---

### Task 6: Per-source preflight auth diagnostics

**Files:**
- Modify: `LLM/src/sr2fpga_agent/runner.py` (`runner_preflight`, add `_source_auth_diagnostics`, generalize the missing-key check)
- Test: `LLM/tests/test_sr2fpga_agent_multi_teacher.py`

**Interfaces:**
- Consumes: `resolve_source_connection`, `LLM_SOURCE_KINDS`, `planned_samples`.
- Produces: `runner_preflight` returns `provider_auth` keyed by **source name**; a source whose `api_key_env` is unset produces an error naming that source only; other sources are unaffected.

- [ ] **Step 1: Write the failing test**

Append to `LLM/tests/test_sr2fpga_agent_multi_teacher.py`:

```python
class PreflightAuthTest(unittest.TestCase):
    def test_missing_key_for_one_source_only(self) -> None:
        claude = SourceConnection(
            name="claude", kind="openai_compat", model="claude-opus-4-8",
            base_url="https://api.anthropic.com/v1", api_key_env="ANTHROPIC_KEY_PRESENT",
            generation_mode="two_stage",
        )
        gpt = SourceConnection(
            name="gpt55", kind="openai_compat", model="gpt-5.5",
            base_url="https://api.openai.com/v1", api_key_env="OPENAI_KEY_ABSENT",
            generation_mode="two_stage",
        )
        config = _base_config(
            sources={"claude": claude, "gpt55": gpt},
            tasks=[
                TaskConfig(source="claude", task_type="counter", widths=[8], count=1),
                TaskConfig(source="gpt55", task_type="counter", widths=[8], count=1),
            ],
        )
        env = {"ANTHROPIC_KEY_PRESENT": "sk-a"}
        with patch.dict(os.environ, env, clear=False):
            os.environ.pop("OPENAI_KEY_ABSENT", None)
            report = runner_preflight(config, run_id=None, validate_provider=False)
        self.assertFalse(report["ok"])
        self.assertTrue(any("OPENAI_KEY_ABSENT" in e for e in report["errors"]))
        self.assertFalse(any("ANTHROPIC_KEY_PRESENT" in e for e in report["errors"]))
        self.assertIn("gpt55", report["provider_auth"])
        self.assertEqual(report["provider_auth"]["claude"]["status"], "not_checked")
```

Add the `TaskConfig` import to the test file's imports:

```python
from LLM.src.sr2fpga_agent.runner import TaskConfig
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest LLM.tests.test_sr2fpga_agent_multi_teacher.PreflightAuthTest -q`
Expected: FAIL (current preflight checks only the single global `config.api_key_env` and keys `provider_auth` by `"deepseek"`, not by source name).

- [ ] **Step 3: Add `_source_auth_diagnostics` and rewire preflight**

Add to `runner.py`:

```python
def _source_auth_diagnostics(
    config: RunnerConfig,
    samples: list[PlannedSample],
    validate_provider: bool,
) -> tuple[dict[str, dict[str, str]], list[str]]:
    diagnostics: dict[str, dict[str, str]] = {}
    errors: list[str] = []
    seen: set[str] = set()
    for sample in samples:
        if sample.source in seen:
            continue
        seen.add(sample.source)
        connection = resolve_source_connection(config, sample.source)
        if connection.kind not in LLM_SOURCE_KINDS:
            continue
        api_key = os.environ.get(connection.api_key_env, "")
        if not api_key:
            diagnostics[sample.source] = {
                "status": "skipped",
                "detail": f"{connection.api_key_env} is not set",
            }
            errors.append(f"{connection.api_key_env} is not set for source {sample.source}")
            continue
        if not validate_provider:
            diagnostics[sample.source] = {"status": "not_checked", "detail": ""}
            continue
        client = DeepSeekClient(
            DeepSeekConfig(
                api_key=api_key,
                model=connection.model,
                base_url=connection.base_url,
                timeout_seconds=20,
            )
        )
        try:
            client.chat(
                [
                    {"role": "system", "content": "Return a tiny JSON object for authentication preflight."},
                    {"role": "user", "content": "Return {\"ok\": true}."},
                ]
            )
        except RuntimeError as exc:
            diagnostics[sample.source] = {
                "status": "failed",
                "detail": _sanitize_secret(str(exc), api_key),
            }
            errors.append(f"{sample.source} provider auth failed")
            continue
        diagnostics[sample.source] = {"status": "ok", "detail": ""}
    return diagnostics, errors
```

In `runner_preflight`, replace the DeepSeek-only key/auth block. Remove the old lines:

```python
    providers = {config.provider, config.repair_provider}
    providers.update(sample.source for sample in samples)
    if _uses_deepseek_provider(providers) and not os.environ.get(config.api_key_env):
        errors.append(f"{config.api_key_env} is not set")
```

and the later `provider_auth = _provider_auth_diagnostics(...)` + its `validate_provider` error loop, and instead use:

```python
    provider_auth, auth_errors = _source_auth_diagnostics(config, samples, validate_provider)
    errors.extend(auth_errors)
```

Keep the `providers` set used by the returned `"providers"` field — build it from the samples:

```python
    providers = {sample.source for sample in samples}
    providers.add(config.repair_provider)
```

Leave the returned `provider_auth` key as-is (now keyed by source name).

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest LLM.tests.test_sr2fpga_agent_multi_teacher.PreflightAuthTest -q`
Expected: PASS (1 test).

- [ ] **Step 5: Run the full suite (existing preflight tests must still pass)**

Run: `python3 -m unittest discover -s LLM/tests -q`
Expected: OK. If an existing test asserts `provider_auth["deepseek"]`, update it to assert on the source name (e.g. `"deepseek-his-v12"`) or adjust the assertion to the new per-source shape — note the change in the commit message.

- [ ] **Step 6: Commit**

```bash
git add LLM/src/sr2fpga_agent/runner.py LLM/tests/test_sr2fpga_agent_multi_teacher.py
git commit -m "feat(runner): per-source preflight auth diagnostics"
```

---

### Task 7: Example multi-teacher config + per-teacher reporting confirmation + docs

**Files:**
- Create: `configs/sr2fpga_multi_teacher.example.yaml`
- Modify: `docs/current-status.md` (add a pointer to the new config and spec/plan)
- Test: `LLM/tests/test_sr2fpga_agent_multi_teacher.py`

**Interfaces:**
- Consumes: everything above; `_calibration_breakdown` (existing) groups by `source`.
- Produces: a runnable example config and a test proving a mixed-teacher dataset yields one `calibration_matrix["source"]` row per teacher.

- [ ] **Step 1: Write the failing reporting test**

Append to `LLM/tests/test_sr2fpga_agent_multi_teacher.py`:

```python
from LLM.src.sr2fpga_agent.runner import _calibration_breakdown


class PerTeacherReportingTest(unittest.TestCase):
    def test_calibration_matrix_has_one_row_per_teacher(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dataset_root = Path(tmp)
            for source, pass_level in (("claude", "L3"), ("gpt55", "L0")):
                sample_id = f"sample_{source}"
                sample_dir = dataset_root / sample_id
                (sample_dir / "eval").mkdir(parents=True)
                (sample_dir / "eval" / "labels.json").write_text(
                    json.dumps({"pass_level": pass_level, "checks": {}, "failure_count": 0}),
                    encoding="utf-8",
                )
                (sample_dir / "metadata.json").write_text(
                    json.dumps({"source": source, "difficulty_tier": "T1"}),
                    encoding="utf-8",
                )
            breakdown = _calibration_breakdown(dataset_root, ["sample_claude", "sample_gpt55"])
            source_matrix = breakdown["calibration_matrix"]["source"]
            self.assertIn("claude", source_matrix)
            self.assertIn("gpt55", source_matrix)
            self.assertEqual(source_matrix["claude"]["l3_pass_rate"], 1.0)
            self.assertEqual(source_matrix["gpt55"]["l3_pass_rate"], 0.0)
```

- [ ] **Step 2: Run test to verify it passes immediately (reporting already exists)**

Run: `python3 -m unittest LLM.tests.test_sr2fpga_agent_multi_teacher.PerTeacherReportingTest -q`
Expected: PASS. This is a **characterization test** confirming the existing per-source grouping works for arbitrary teacher names. If it fails, the reporting code regressed in an earlier task — fix that task, do not weaken this test.

- [ ] **Step 3: Create the example config**

Create `configs/sr2fpga_multi_teacher.example.yaml`:

```yaml
# Multi-teacher trajectory batch: Claude + GPT-5.5 + DeepSeek + Qwen + deterministic control.
# Keys come only from *_API_KEY env (optionally a local ignored .env). Never commit keys.
dataset_root: datasets/sr2fpga_rtl_v1
export_root: datasets/sr2fpga_rtl_v1_exports
run_root: tmp/sr2fpga_runs
provider: deterministic        # global fallback / control
repair_provider: none
max_attempts: 1
refresh_exports: true
sample_id_prefix: multi_teacher
env_file: .env
line_b_targets: {}

sources:
  claude:
    kind: openai_compat
    model: claude-opus-4-8
    base_url: https://api.anthropic.com/v1
    api_key_env: ANTHROPIC_API_KEY
    generation_mode: two_stage
  gpt55:
    kind: openai_compat
    model: gpt-5.5
    base_url: https://api.openai.com/v1
    api_key_env: OPENAI_API_KEY
    generation_mode: two_stage
  qwen:
    kind: openai_compat
    model: qwen2.5-coder-7b-instruct
    base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
    api_key_env: DASHSCOPE_API_KEY
    generation_mode: two_stage
  deepseek-his-v12:
    kind: deepseek-his-v12
    model: deepseek-v4-flash
    base_url: https://api.deepseek.com
    api_key_env: DEEPSEEK_API_KEY
    generation_mode: two_stage

tasks:
  - source: claude
    task_type: component_topology
    topology_ids: [T1]
    widths: [8]
    count: 1
    requirement_style: simple_prompt
    measurement_point: a_first_attempt_no_tools
  - source: gpt55
    task_type: component_topology
    topology_ids: [T1]
    widths: [8]
    count: 1
    requirement_style: simple_prompt
    measurement_point: a_first_attempt_no_tools
  - source: deepseek-his-v12
    task_type: component_topology
    topology_ids: [T1]
    widths: [8]
    count: 1
    requirement_style: simple_prompt
    measurement_point: a_first_attempt_no_tools
  - source: deterministic
    task_type: component_topology
    topology_ids: [T1]
    widths: [8]
    count: 1
    requirement_style: simple_prompt
```

- [ ] **Step 4: Validate the example config parses and preflights**

Run: `python3 -m LLM.src.sr2fpga_agent.runner --config configs/sr2fpga_multi_teacher.example.yaml --run-id multi-teacher-smoke --preflight`
Expected: JSON report prints; `planned_samples: 4`; `provider_auth` lists `claude`, `gpt55`, `deepseek-his-v12` (each `not_checked` or `skipped` depending on which keys are set); `deterministic` does not appear in `provider_auth`. Exit code 0 only if all referenced keys are present; otherwise it reports the missing ones — that is expected without keys.

- [ ] **Step 5: Add docs pointer**

In `docs/current-status.md`, under "Important Pointers", add:

```markdown
- Multi-teacher source spec: `docs/superpowers/specs/2026-06-25-sr2fpga-multi-teacher-source-design.md`
- Multi-teacher source plan: `docs/superpowers/plans/2026-06-25-sr2fpga-multi-teacher-source.md`
- Multi-teacher runner config: `configs/sr2fpga_multi_teacher.example.yaml`
```

- [ ] **Step 6: Run the full suite**

Run: `python3 -m unittest discover -s LLM/tests -q`
Expected: OK.

- [ ] **Step 7: Commit**

```bash
git add configs/sr2fpga_multi_teacher.example.yaml docs/current-status.md LLM/tests/test_sr2fpga_agent_multi_teacher.py
git commit -m "feat(runner): multi-teacher example config + per-teacher reporting test + docs"
```

---

## Self-Review

**Spec coverage:**
- Per-source connection table (`sources:`) → Task 1.
- Resolution rules with legacy fallback → Task 2.
- Generalized OpenAI-compatible generator (reusing `DeepSeekClient`) → Task 3.
- Per-sample connection resolution → Task 4.
- Metadata: failure_origin / schema_version / training_split / resolved model driven by kind & generation_mode → Task 5.
- Preflight per-source auth → Task 6.
- Reporting (no new work) confirmation + example config + docs → Task 7.
- Resolved decisions (native endpoints, two_stage only, task-count balancing) → reflected in the example config (native base_urls, all `two_stage`, counts on tasks). Gemini left as a pure config add — documented in the spec, no code seam needed beyond `sources:`.
- Backward compatibility (no `sources:` block behaves as today) → Task 1 `test_missing_sources_block_defaults_empty`, Task 2 legacy fallback tests, and full-suite runs in Tasks 4/5/6.

**Placeholder scan:** No TBD/TODO; every code step shows full code; commands include expected output.

**Type consistency:** `SourceConnection` fields and `resolve_source_connection`/`build_project_generator_for_connection` signatures are used identically across Tasks 1–7. `_sample_failure_origin`/`_sample_system_his_schema_version` are updated to the two-arg `(sample, config)` form in Task 5 and all call sites are listed.

**Note for the implementer:** Tasks 4–6 modify functions that existing tests touch (`_project_generator_for_sample`, preflight `provider_auth` shape, `_sample_failure_origin` arity). Each of those tasks ends with a full-suite run and explicit guidance on the expected existing-test adjustments. Do not weaken the new tests to make old assertions pass — update the old assertions to the new per-source shape.
