# Code Review Bugfix Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix all 10 confirmed bugs surfaced in the 2026-06-30 code review, covering training-data integrity, runtime crash paths, and silent-wrong-behavior issues.

**Architecture:** Five independent fix tasks, each touching one or two files, ordered from lowest-risk (no test infrastructure changes needed) to highest-risk (training-view logic). All fixes are surgical — no refactoring, no new abstractions beyond what's necessary to fix the defect.

**Tech Stack:** Python 3.11+, stdlib `http.client`, `urllib`, `unittest`

## Global Constraints

- All Python run from repo root: `python3 -m unittest discover -s LLM/tests -q`
- Absolute imports: `from LLM.src.sr2fpga_agent...`
- No new files — all fixes are edits to existing source + existing test files
- Do not introduce CRLF line endings

---

## Bug Map (10 total)

| # | File | Line | One-liner |
|---|------|------|-----------|
| A1 | `contract_skeleton.py` | 24 | duplicate source key silently overwrites component |
| A2 | `contract_skeleton.py` | 367 | port `dir`/`direction` absent → `str(None)` → `wire` for input |
| B1 | `system_his_v12_checker.py` | 301 | missing `continue` after duplicate component error |
| B2 | `system_his_v12_checker.py` | 121 | FSM owner `"top"` not in `valid_fsm_owners` when `top.name` absent |
| C1 | `deepseek.py` | 1488/1164 | retry appends `user` turn after `user` turn → Anthropic HTTP 400 |
| C2 | `deepseek.py` | 208 | `http.client.IncompleteRead` uncaught → bypasses retry |
| D1 | `recorder.py` | 341 | measured QoR in `episode['verification']['l3']` leaks into `predicted_qor` training rows |
| D2 | `recorder.py` | 312 | `"BEHAVIOR_HOLE"` is substring of `"__BEHAVIOR_HOLE__"` → counted twice |
| E1 | `runner.py` | 1240 | unvetted `openai_compat`/`anthropic_compat` sources routed to `training_split='clean'` |
| E2 | `runner.py` | 487 | unknown `source.kind` silently passes preflight → late `SystemExit` |

---

## Task 1: contract_skeleton.py — port direction and duplicate source

**Files:**
- Modify: `LLM/src/sr2fpga_agent/contract_skeleton.py` (lines 24, 367)
- Test: `LLM/tests/test_sr2fpga_agent_contract_skeleton.py`

**Interfaces:**
- Produces: no signature change; `_testbench()` and `build_contract_skeleton_project()` behave correctly

- [ ] **Step 1.1: Write failing tests**

Open `LLM/tests/test_sr2fpga_agent_contract_skeleton.py` and add to the existing test class:

```python
def test_testbench_port_without_dir_key_is_reg(self) -> None:
    """Port dict missing both 'dir' and 'direction' must still emit reg for inputs."""
    from LLM.src.sr2fpga_agent.contract_skeleton import build_contract_skeleton_project
    from LLM.src.sr2fpga_agent.models import GeneratedProject, PlatformProfile, ProjectRequest

    minimal_his = {
        "schema_version": "system-his-v1.2",
        "intent": "test",
        "top": {
            "name": "dut",
            "ports": [
                {"name": "clk"},          # no 'dir' or 'direction' key
                {"name": "out", "dir": "output"},
            ],
            "clocks": [{"name": "clk", "target_fmax_mhz": 100}],
            "resets": [],
        },
        "state": {"registers": [], "counters": [], "fsms": [], "buffers": [], "memories": []},
        "components": [],
        "instances": [],
        "data_flow": [],
        "control_flow": [],
        "timing": {"target_fmax_mhz": 100},
        "resources": {"optimization_goal": "area", "expected": {}},
        "verification": {"testbench": "tb_dut", "scenarios": [], "pass_condition": "all_pass"},
        "artifacts": {"top_module": "dut", "rtl_sources": ["rtl/top.v"]},
    }
    req = ProjectRequest(task_type="counter", width=8, project_name="p")
    platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
    project = build_contract_skeleton_project(req, platform, minimal_his)
    tb = project.files["sim/tb_top.v"]
    # port 'clk' has no direction — must default to reg (input-side)
    self.assertIn("reg  clk", tb, "port without dir should default to reg")
    self.assertIn("wire  out", tb, "output port should remain wire")


def test_duplicate_source_raises(self) -> None:
    """Two components sharing the same source path must raise ValueError."""
    from LLM.src.sr2fpga_agent.contract_skeleton import build_contract_skeleton_project
    from LLM.src.sr2fpga_agent.models import PlatformProfile, ProjectRequest

    his = {
        "schema_version": "system-his-v1.2",
        "intent": "test",
        "top": {
            "name": "top",
            "ports": [],
            "clocks": [{"name": "clk", "target_fmax_mhz": 100}],
            "resets": [],
        },
        "state": {"registers": [], "counters": [], "fsms": [], "buffers": [], "memories": []},
        "components": [
            {"name": "a", "semantic_kind": "logic", "source": "rtl/shared.v",
             "ports": [], "intent": "a"},
            {"name": "b", "semantic_kind": "logic", "source": "rtl/shared.v",
             "ports": [], "intent": "b"},
        ],
        "instances": [],
        "data_flow": [],
        "control_flow": [],
        "timing": {"target_fmax_mhz": 100},
        "resources": {"optimization_goal": "area", "expected": {}},
        "verification": {"testbench": "tb", "scenarios": [], "pass_condition": "all_pass"},
        "artifacts": {"top_module": "top", "rtl_sources": ["rtl/top.v", "rtl/shared.v"]},
    }
    req = ProjectRequest(task_type="counter", width=8, project_name="p")
    platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
    with self.assertRaises(ValueError, msg="duplicate source must raise"):
        build_contract_skeleton_project(req, platform, his)
```

- [ ] **Step 1.2: Run failing tests**

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_contract_skeleton -q 2>&1 | tail -5
```

Expected: 2 new test failures.

- [ ] **Step 1.3: Fix `_testbench` port direction fallback (line 367)**

In `LLM/src/sr2fpga_agent/contract_skeleton.py`, find:

```python
        kind = "reg" if str(port_map.get("dir", port_map.get("direction"))) == "input" else "wire"
```

Replace with:

```python
        kind = "reg" if str(port_map.get("dir", port_map.get("direction", "input"))) == "input" else "wire"
```

This defaults missing direction to `"input"` so unknown-direction ports are conservatively treated as `reg`, which is safe for testbench stimulus drivers.

- [ ] **Step 1.4: Fix `components_by_source` duplicate detection (line 24)**

In `build_contract_skeleton_project`, find:

```python
    components_by_source = {str(component.get("source")): component for component in components}
```

Replace with:

```python
    components_by_source: dict[str, Any] = {}
    for _c in components:
        _src = str(_c.get("source"))
        if _src in components_by_source:
            raise ValueError(
                f"System-HIS has two components with the same source path '{_src}': "
                f"'{components_by_source[_src].get('name')}' and '{_c.get('name')}'. "
                "Each source file must belong to exactly one component."
            )
        components_by_source[_src] = _c
```

- [ ] **Step 1.5: Run tests and confirm pass**

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_contract_skeleton -q 2>&1 | tail -5
```

Expected: all tests pass, 0 failures.

- [ ] **Step 1.6: Run full suite to check for regressions**

```bash
python3 -m unittest discover -s LLM/tests -q 2>&1 | tail -5
```

- [ ] **Step 1.7: Commit**

```bash
git add LLM/src/sr2fpga_agent/contract_skeleton.py LLM/tests/test_sr2fpga_agent_contract_skeleton.py
git commit -m "fix: contract_skeleton port-direction default and duplicate-source guard"
```

---

## Task 2: system_his_v12_checker.py — duplicate component continue + FSM owner 'top'

**Files:**
- Modify: `LLM/src/sr2fpga_agent/system_his_v12_checker.py` (lines 121, 301–323)
- Test: `LLM/tests/test_sr2fpga_agent_system_his_v12_checker.py`

**Interfaces:**
- Produces: no signature change; `check_system_his_v12` returns correct errors without false positives

- [ ] **Step 2.1: Write failing tests**

Add to `LLM/tests/test_sr2fpga_agent_system_his_v12_checker.py`:

```python
def test_duplicate_component_does_not_generate_false_port_errors(self) -> None:
    """A duplicate component name must not cause spurious port-mismatch errors for valid components."""
    from LLM.src.sr2fpga_agent.system_his_v12_checker import check_system_his_v12

    his = _minimal_his()  # use the existing helper in the test file
    his["components"] = [
        {"name": "reg_a", "semantic_kind": "register", "source": "rtl/reg_a.v",
         "ports": [{"name": "d", "dir": "input"}, {"name": "q", "dir": "output"}], "intent": "first"},
        {"name": "reg_a", "semantic_kind": "register", "source": "rtl/reg_b.v",
         "ports": [{"name": "d", "dir": "input"}], "intent": "duplicate with fewer ports"},
    ]
    his["instances"] = [
        {"name": "u_reg", "component": "reg_a", "parameter_values": {},
         "clock": "clk", "reset": "rst_n", "owns_state": []}
    ]
    his["artifacts"]["rtl_sources"] = ["rtl/top.v", "rtl/reg_a.v", "rtl/reg_b.v"]
    result = check_system_his_v12(his)
    # Must report the duplicate error
    self.assertTrue(any("duplicate" in e for e in result.errors), result.errors)
    # Must NOT report 'q' as missing (it's in the first definition; second definition must not clobber)
    self.assertFalse(
        any("missing" in e and "q" in e for e in result.errors),
        f"Spurious port-mismatch errors found: {result.errors}",
    )


def test_fsm_owner_top_valid_when_top_name_absent(self) -> None:
    """FSM with owner='top' must pass even when the top dict has no explicit 'name' field."""
    from LLM.src.sr2fpga_agent.system_his_v12_checker import check_system_his_v12

    his = _minimal_his()
    his["top"].pop("name", None)   # remove name entirely
    his["state"]["fsms"] = [
        {
            "owner": "top",
            "name": "ctrl_fsm",
            "states": ["IDLE", "RUN"],
            "initial": "IDLE",
            "reset_state": "IDLE",
            "transitions": [],
        }
    ]
    result = check_system_his_v12(his)
    fsm_errors = [e for e in result.errors if "fsm" in e.lower() or "owner" in e.lower()]
    self.assertEqual(fsm_errors, [], f"Unexpected FSM owner errors: {fsm_errors}")
```

Note: if `_minimal_his()` doesn't exist in the test file, add it:

```python
def _minimal_his() -> dict:
    return {
        "schema_version": "system-his-v1.2",
        "intent": "test design",
        "top": {
            "name": "dut",
            "ports": [
                {"name": "clk", "dir": "input"},
                {"name": "rst_n", "dir": "input"},
                {"name": "out", "dir": "output"},
            ],
            "clocks": [{"name": "clk", "target_fmax_mhz": 100}],
            "resets": [{"name": "rst_n", "active": "low"}],
        },
        "state": {"registers": [], "counters": [], "fsms": [], "buffers": [], "memories": []},
        "components": [],
        "instances": [],
        "data_flow": [],
        "control_flow": [],
        "timing": {"target_fmax_mhz": 100},
        "resources": {"optimization_goal": "area", "expected": {}},
        "verification": {"testbench": "tb_dut", "scenarios": [], "pass_condition": "all_pass"},
        "artifacts": {"top_module": "dut", "rtl_sources": ["rtl/top.v"]},
    }
```

- [ ] **Step 2.2: Run failing tests**

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_system_his_v12_checker -q 2>&1 | tail -5
```

Expected: 2 new test failures.

- [ ] **Step 2.3: Fix missing `continue` in `_component_ports` (line 301)**

In `LLM/src/sr2fpga_agent/system_his_v12_checker.py`, find in `_component_ports`:

```python
        if name in component_ports:
            errors.append(f"components duplicate component '{name}'")
        if not str(component.get("semantic_kind", "")).strip():
```

Replace with:

```python
        if name in component_ports:
            errors.append(f"components duplicate component '{name}'")
            continue
        if not str(component.get("semantic_kind", "")).strip():
```

- [ ] **Step 2.4: Fix `valid_fsm_owners` to always include `"top"` (line 121)**

Find:

```python
    valid_fsm_owners = {str(top.get("name", "")).strip()} | set(instance_components)
    valid_fsm_owners.discard("")
```

Replace with:

```python
    valid_fsm_owners = {"top", str(top.get("name", "")).strip()} | set(instance_components)
    valid_fsm_owners.discard("")
```

- [ ] **Step 2.5: Run tests and confirm pass**

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_system_his_v12_checker -q 2>&1 | tail -5
```

Expected: all pass.

- [ ] **Step 2.6: Full suite regression check**

```bash
python3 -m unittest discover -s LLM/tests -q 2>&1 | tail -5
```

- [ ] **Step 2.7: Commit**

```bash
git add LLM/src/sr2fpga_agent/system_his_v12_checker.py LLM/tests/test_sr2fpga_agent_system_his_v12_checker.py
git commit -m "fix: v12_checker duplicate component continue + unconditional 'top' in valid_fsm_owners"
```

---

## Task 3: deepseek.py — Anthropic consecutive user turns + IncompleteRead retry

**Files:**
- Modify: `LLM/src/sr2fpga_agent/deepseek.py` (lines ~1164, ~1488, ~210)
- Test: `LLM/tests/test_sr2fpga_agent_deepseek.py`

**Interfaces:**
- `_with_system_his_retry_feedback(messages, error, content, task_type) -> list[dict]` — unchanged signature; now inserts stub assistant turn before retry user turn
- `_with_his_project_retry_feedback(messages, error, content) -> list[dict]` — same
- `OpenAICompatibleClient._request_once` — now also catches `http.client.IncompleteRead`

- [ ] **Step 3.1: Write failing tests**

Add to `LLM/tests/test_sr2fpga_agent_deepseek.py`:

```python
def test_system_his_retry_feedback_interleaves_assistant_turn(self) -> None:
    """_with_system_his_retry_feedback must insert an assistant stub before the retry user turn."""
    from LLM.src.sr2fpga_agent.deepseek import _with_system_his_retry_feedback

    initial = [
        {"role": "system", "content": "You are ..."},
        {"role": "user", "content": "Generate HIS"},
    ]
    result = _with_system_his_retry_feedback(initial, "bad json", "{bad}", task_type="counter")
    roles = [m["role"] for m in result]
    # Roles must alternate: system, user, assistant, user
    self.assertNotEqual(roles[-1], roles[-2], f"Consecutive same roles at end: {roles}")
    self.assertEqual(roles[-2], "assistant", f"Expected assistant before retry user: {roles}")
    self.assertEqual(roles[-1], "user", f"Expected retry user at end: {roles}")


def test_his_project_retry_feedback_interleaves_assistant_turn(self) -> None:
    """_with_his_project_retry_feedback must insert an assistant stub before the retry user turn."""
    from LLM.src.sr2fpga_agent.deepseek import _with_his_project_retry_feedback

    initial = [
        {"role": "system", "content": "You are ..."},
        {"role": "user", "content": "Generate behavior files"},
    ]
    result = _with_his_project_retry_feedback(initial, "bad json", "{bad}")
    roles = [m["role"] for m in result]
    self.assertNotEqual(roles[-1], roles[-2], f"Consecutive same roles at end: {roles}")
    self.assertEqual(roles[-2], "assistant", f"Expected assistant before retry user: {roles}")
    self.assertEqual(roles[-1], "user", f"Expected retry user at end: {roles}")


def test_openai_client_retries_on_incomplete_read(self) -> None:
    """IncompleteRead during streaming must be treated as a transient error and retried."""
    import http.client
    from unittest.mock import MagicMock, patch
    from LLM.src.sr2fpga_agent.deepseek import OpenAICompatibleClient, OpenAICompatibleConfig

    cfg = OpenAICompatibleConfig(
        api_key="test", base_url="https://example.com", transport_attempts=2, retry_backoff_seconds=0
    )
    client = OpenAICompatibleClient(cfg)

    call_count = 0

    def fake_urlopen(req, timeout, context):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise http.client.IncompleteRead(b"partial")
        resp = MagicMock()
        resp.__enter__ = lambda s: s
        resp.__exit__ = MagicMock(return_value=False)
        resp.read.side_effect = [b'{"choices":[{"message":{"content":"ok"}}]}', b""]
        return resp

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        result = client.chat([{"role": "user", "content": "hello"}])
    self.assertEqual(result, "ok")
    self.assertEqual(call_count, 2, "Should have retried once after IncompleteRead")
```

- [ ] **Step 3.2: Run failing tests**

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_deepseek -q 2>&1 | tail -5
```

Expected: 3 new test failures.

- [ ] **Step 3.3: Fix consecutive user turns in `_with_system_his_retry_feedback` (line ~1164)**

Find the function `_with_system_his_retry_feedback` in `deepseek.py`. The last line of the current implementation is a list spreading `[*messages, {"role": "user", ...}]`.

Change from:

```python
    return [
        *messages,
        {
            "role": "user",
            "content": (
                "Your previous System-HIS output failed validation. "
                ...
            ),
        },
    ]
```

To (insert a stub assistant turn before the retry user turn):

```python
    return [
        *messages,
        {"role": "assistant", "content": previous_content or "{}"},
        {
            "role": "user",
            "content": (
                "Your previous System-HIS output failed validation. "
                ...
            ),
        },
    ]
```

- [ ] **Step 3.4: Fix consecutive user turns in `_with_his_project_retry_feedback` (line ~1678)**

Same pattern. Find `_with_his_project_retry_feedback`. Change from:

```python
    return [
        *messages,
        {
            "role": "user",
            "content": (
                "Your previous behavior_files output failed validation. "
                ...
            ),
        },
    ]
```

To:

```python
    return [
        *messages,
        {"role": "assistant", "content": previous_content or "{}"},
        {
            "role": "user",
            "content": (
                "Your previous behavior_files output failed validation. "
                ...
            ),
        },
    ]
```

- [ ] **Step 3.5: Fix `IncompleteRead` not caught in `_request_once` (line ~210)**

At the top of `deepseek.py`, `http.client` is not yet imported. Add it to the imports:

Find the existing import block (lines 1-16) and add `import http.client` after the stdlib imports. The imports block should look like:

```python
import http.client
import json
import signal
import ssl
import threading
import time
import urllib.error
import urllib.request
```

Then in `OpenAICompatibleClient._request_once`, find the inner try/except block:

```python
        try:
            with urllib.request.urlopen(
                request,
                timeout=self.config.timeout_seconds,
                context=_default_ssl_context(),
            ) as response:
                try:
                    with _response_read_deadline(self.config.timeout_seconds):
                        return reader(response)
                except TimeoutError as exc:
                    raise _TransientOpenAICompatibleError(
                        "OpenAI-compatible API response read timed out"
                    ) from exc
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            message = f"OpenAI-compatible API request failed with HTTP {exc.code}: {body}"
            if exc.code in TRANSIENT_HTTP_STATUS_CODES:
                raise _TransientOpenAICompatibleError(message) from exc
            raise RuntimeError(message) from exc
        except TimeoutError as exc:
            raise _TransientOpenAICompatibleError("OpenAI-compatible API request timed out") from exc
        except urllib.error.URLError as exc:
            raise _TransientOpenAICompatibleError(f"OpenAI-compatible API request failed: {exc.reason}") from exc
```

Add one more except clause after `urllib.error.URLError`:

```python
        except http.client.IncompleteRead as exc:
            raise _TransientOpenAICompatibleError(
                f"OpenAI-compatible API response truncated (IncompleteRead): {exc}"
            ) from exc
```

- [ ] **Step 3.6: Run tests and confirm pass**

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_deepseek -q 2>&1 | tail -5
```

Expected: all pass.

- [ ] **Step 3.7: Full suite regression check**

```bash
python3 -m unittest discover -s LLM/tests -q 2>&1 | tail -5
```

- [ ] **Step 3.8: Commit**

```bash
git add LLM/src/sr2fpga_agent/deepseek.py LLM/tests/test_sr2fpga_agent_deepseek.py
git commit -m "fix: deepseek Anthropic retry interleave + IncompleteRead transient retry"
```

---

## Task 4: recorder.py — QoR label leakage + BEHAVIOR_HOLE double-count

**Files:**
- Modify: `LLM/src/sr2fpga_agent/recorder.py` (lines 138–145, 312–314)
- Test: `LLM/tests/test_sr2fpga_agent_recorder.py`

**Interfaces:**
- `export_training_views` — `predicted_qor` rows no longer include `verification` in the embedded episode
- `_behavior_hole_count` — counts each marker exactly once

- [ ] **Step 4.1: Write failing tests**

Add to `LLM/tests/test_sr2fpga_agent_recorder.py`:

```python
def test_predicted_qor_rows_exclude_verification(self) -> None:
    """project_to_predicted_qor.jsonl rows must not contain episode.verification (measured QoR)."""
    import tempfile, json
    from pathlib import Path
    from LLM.src.sr2fpga_agent.recorder import DatasetRecorder

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        recorder = DatasetRecorder(root)
        # Write a minimal sample with a predicted_qor file
        sample_id = "test_qor_leak"
        from LLM.src.sr2fpga_agent import GeneratedProject, PlatformProfile, ProjectGenerator, ProjectRequest
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="counter", width=4, project_name="c4"), platform
        )
        # Inject a fake predicted_qor into the project files
        project = GeneratedProject(
            project_name=project.project_name,
            files={**project.files, "reports/predicted_qor.json": '{"resources":{"lut":5}}'},
        )
        labels = {"pass_level": "L3", "checks": {"l3_synth_pass": True}}
        measured_qor = {"lut": 99, "ff": 12}
        recorder.write_final(
            sample_id, project, labels, measured_qor, {}, {"attempts": []}
        )
        output_dir = root / "exports"
        recorder.export_training_views(output_dir)
        qor_path = output_dir / "project_to_predicted_qor.jsonl"
        self.assertTrue(qor_path.exists())
        row = json.loads(qor_path.read_text().strip())
        episode = row.get("episode", {})
        # verification must be absent or stripped — measured lut=99 must NOT appear
        verification = episode.get("verification")
        if verification is not None:
            l3 = verification.get("l3", {})
            self.assertNotIn("lut", l3, "Measured lut must not appear in predicted_qor training row")


def test_behavior_hole_count_no_double_count(self) -> None:
    """__BEHAVIOR_HOLE__ must count as exactly 1, not 2 (substring overlap guard)."""
    from LLM.src.sr2fpga_agent.recorder import _behavior_hole_count

    content_single = "  // BEHAVIOR_HOLE: model-generated RTL behavior goes here."
    content_double = "  // __BEHAVIOR_HOLE__\n  // __BEHAVIOR_HOLE__"
    self.assertEqual(_behavior_hole_count(content_single), 1)
    self.assertEqual(_behavior_hole_count(content_double), 2)
    # Critical: the delimited form must not be counted twice
    content_delimited = "  // __BEHAVIOR_HOLE__"
    self.assertEqual(_behavior_hole_count(content_delimited), 1,
                     "__BEHAVIOR_HOLE__ must count as 1, not 2 due to substring overlap")
```

- [ ] **Step 4.2: Run failing tests**

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_recorder -q 2>&1 | tail -5
```

Expected: 2 new failures.

- [ ] **Step 4.3: Fix `_behavior_hole_count` double-counting (line 312)**

In `recorder.py`, find:

```python
def _behavior_hole_count(content: str) -> int:
    markers = ("BEHAVIOR_HOLE", "TODO_BEHAVIOR", "__BEHAVIOR_HOLE__")
    return sum(content.count(marker) for marker in markers)
```

Replace with:

```python
def _behavior_hole_count(content: str) -> int:
    # Count delimited form first, then plain form only for occurrences not part of __BEHAVIOR_HOLE__
    delimited = content.count("__BEHAVIOR_HOLE__")
    plain = content.replace("__BEHAVIOR_HOLE__", "").count("BEHAVIOR_HOLE")
    todo = content.count("TODO_BEHAVIOR")
    return delimited + plain + todo
```

- [ ] **Step 4.4: Fix QoR label leakage in `export_training_views` (lines 137–145)**

In `recorder.py`, find the `predicted_qor_rows.append(...)` block:

```python
            if final_files and predicted_qor_path.exists():
                predicted_qor_rows.append(
                    {
                        "sample_id": sample_id,
                        "metadata": metadata,
                        "episode": episode,
                        "files": final_files,
                        "predicted_qor": json.loads(predicted_qor_path.read_text(encoding="utf-8")),
                    }
                )
```

Replace with:

```python
            if final_files and predicted_qor_path.exists():
                predicted_qor_rows.append(
                    {
                        "sample_id": sample_id,
                        "metadata": metadata,
                        "episode": _episode_without_verification(episode),
                        "files": final_files,
                        "predicted_qor": json.loads(predicted_qor_path.read_text(encoding="utf-8")),
                    }
                )
```

Then add the helper function near the top of the file's private helpers (after `_check_status`):

```python
def _episode_without_verification(episode: dict[str, Any]) -> dict[str, Any]:
    """Return episode stripped of verification data for predicted-QoR training rows.

    At inference time no EDA tool has run, so verification.l3 measured resource
    counts must not appear as input context — they would create a label-leakage
    shortcut that breaks at deploy time.
    """
    if not isinstance(episode, dict):
        return episode
    result = dict(episode)
    result.pop("verification", None)
    return result
```

- [ ] **Step 4.5: Run tests and confirm pass**

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_recorder -q 2>&1 | tail -5
```

Expected: all pass.

- [ ] **Step 4.6: Full suite regression check**

```bash
python3 -m unittest discover -s LLM/tests -q 2>&1 | tail -5
```

- [ ] **Step 4.7: Commit**

```bash
git add LLM/src/sr2fpga_agent/recorder.py LLM/tests/test_sr2fpga_agent_recorder.py
git commit -m "fix: recorder QoR label-leakage in predicted_qor view + BEHAVIOR_HOLE double-count"
```

---

## Task 5: runner.py — unvetted sources to clean + unknown kind silent preflight

**Files:**
- Modify: `LLM/src/sr2fpga_agent/runner.py` (lines ~487, ~1238–1241)
- Test: `LLM/tests/test_sr2fpga_agent_runner.py`

**Interfaces:**
- `_sample_system_his_schema_version` — only `deepseek-his-v12` and `deterministic` sources get `"system-his-v1.2"` by default; `openai_compat`/`anthropic_compat` are quarantined until explicitly allowlisted
- `_check_source_auth` — adds error for unknown kinds instead of silently returning

**Design decision for E1:** Introduce a `VETTED_TWO_STAGE_KINDS` set containing only `{"deepseek-his-v12"}`. New source kinds (`openai_compat`, `anthropic_compat`) start quarantined. When operators have validated a new provider they add its kind to `VETTED_TWO_STAGE_KINDS`. This is minimal and reversible.

- [ ] **Step 5.1: Write failing tests**

Add to `LLM/tests/test_sr2fpga_agent_runner.py`:

```python
def test_unvetted_openai_compat_source_is_quarantined(self) -> None:
    """openai_compat sources must produce training_split='quarantine', not 'clean'."""
    from LLM.src.sr2fpga_agent.runner import PlannedSample, RunnerConfig, _sample_system_his_schema_version, SourceConnection
    from pathlib import Path

    config = RunnerConfig(
        dataset_root=Path("/tmp/test"),
        tasks=[],
        sources={
            "my_openai": SourceConnection(
                name="my_openai", kind="openai_compat", generation_mode="two_stage"
            )
        },
        model="gpt-4",
        base_url="https://api.openai.com/v1",
        api_key_env="OPENAI_API_KEY",
        repair_provider="none",
        max_attempts=1,
    )
    sample = PlannedSample(sample_id="s1", source="my_openai", task_type="counter",
                           width=8, project_name="c8")
    schema = _sample_system_his_schema_version(sample, config)
    self.assertEqual(schema, "system-his-v1.1",
                     "openai_compat must be quarantined until explicitly vetted")


def test_unknown_source_kind_fails_preflight(self) -> None:
    """A source with an unknown kind must produce a preflight error, not pass silently."""
    from LLM.src.sr2fpga_agent.runner import (
        PlannedSample, RunnerConfig, SourceConnection, _source_auth_diagnostics
    )
    from pathlib import Path

    config = RunnerConfig(
        dataset_root=Path("/tmp/test"),
        tasks=[],
        sources={
            "bad_source": SourceConnection(
                name="bad_source", kind="openai-compat",  # hyphen typo
                api_key_env="SOME_KEY", generation_mode="two_stage"
            )
        },
        model="",
        base_url="",
        api_key_env="SOME_KEY",
        repair_provider="none",
        max_attempts=1,
    )
    sample = PlannedSample(sample_id="s1", source="bad_source", task_type="counter",
                           width=8, project_name="c8")
    _, errors = _source_auth_diagnostics(config, [sample], validate_provider=False)
    self.assertTrue(
        any("unknown" in e.lower() or "unsupported" in e.lower() or "kind" in e.lower() for e in errors),
        f"Expected an error for unknown source kind, got: {errors}",
    )
```

- [ ] **Step 5.2: Run failing tests**

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_runner -q 2>&1 | tail -5
```

Expected: 2 new failures.

- [ ] **Step 5.3: Add `VETTED_TWO_STAGE_KINDS` constant and fix `_sample_system_his_schema_version` (line ~1238)**

In `runner.py`, find `LLM_SOURCE_KINDS` (around line 870) and add right after it:

```python
# Only these source kinds have been validated for the 'clean' training split.
# When a new provider is vetted, add its kind here — do not broaden the condition
# in _sample_system_his_schema_version directly.
VETTED_TWO_STAGE_KINDS = {"deepseek-his-v12", "deepseek-oracle-his-v12"}
```

Then find `_sample_system_his_schema_version`:

```python
def _sample_system_his_schema_version(sample: PlannedSample, config: RunnerConfig) -> str:
    connection = resolve_source_connection(config, sample.source)
    if connection.kind == "deterministic" or connection.generation_mode in {"two_stage", "oracle_his2project"}:
        return "system-his-v1.2"
    return "system-his-v1.1"
```

Replace with:

```python
def _sample_system_his_schema_version(sample: PlannedSample, config: RunnerConfig) -> str:
    connection = resolve_source_connection(config, sample.source)
    if connection.kind == "deterministic":
        return "system-his-v1.2"
    if connection.kind in VETTED_TWO_STAGE_KINDS and connection.generation_mode in {"two_stage", "oracle_his2project"}:
        return "system-his-v1.2"
    return "system-his-v1.1"
```

- [ ] **Step 5.4: Fix silent return in `_check_source_auth` for unknown kinds (line ~487)**

Find:

```python
    connection = resolve_source_connection(config, source)
    if connection.kind not in LLM_SOURCE_KINDS:
        return
```

Replace with:

```python
    connection = resolve_source_connection(config, source)
    if connection.kind == "deterministic":
        return
    if connection.kind not in LLM_SOURCE_KINDS:
        errors.append(
            f"Source '{source}' has unsupported kind '{connection.kind}'. "
            f"Supported kinds: {sorted(LLM_SOURCE_KINDS)}."
        )
        return
```

- [ ] **Step 5.5: Run tests and confirm pass**

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_runner -q 2>&1 | tail -5
```

Expected: all pass.

- [ ] **Step 5.6: Full suite regression check**

```bash
python3 -m unittest discover -s LLM/tests -q 2>&1 | tail -5
```

Expected: 0 failures.

- [ ] **Step 5.7: Commit**

```bash
git add LLM/src/sr2fpga_agent/runner.py LLM/tests/test_sr2fpga_agent_runner.py
git commit -m "fix: runner quarantine unvetted two-stage sources + error on unknown source kind"
```

---

## Self-Review

### Spec coverage (10 bugs → 5 tasks)

| Bug | Task | Step |
|-----|------|------|
| A1 duplicate source | Task 1 | Step 1.4 |
| A2 port direction | Task 1 | Step 1.3 |
| B1 missing continue | Task 2 | Step 2.3 |
| B2 FSM owner 'top' | Task 2 | Step 2.4 |
| C1 consecutive user turns | Task 3 | Steps 3.3–3.4 |
| C2 IncompleteRead | Task 3 | Step 3.5 |
| D1 QoR label leakage | Task 4 | Step 4.4 |
| D2 BEHAVIOR_HOLE count | Task 4 | Step 4.3 |
| E1 unvetted clean split | Task 5 | Step 5.3 |
| E2 silent unknown kind | Task 5 | Step 5.4 |

All 10 bugs covered. ✓

### Placeholder scan

No TBD, TODO, or "similar to" references. All steps contain actual code. ✓

### Type consistency

- `_episode_without_verification(episode: dict[str, Any]) -> dict[str, Any]` defined in Task 4 Step 4.4 and called in same step. ✓
- `VETTED_TWO_STAGE_KINDS` defined in Task 5 Step 5.3 and used in same step. ✓
- `_with_system_his_retry_feedback` / `_with_his_project_retry_feedback` signatures unchanged. ✓
