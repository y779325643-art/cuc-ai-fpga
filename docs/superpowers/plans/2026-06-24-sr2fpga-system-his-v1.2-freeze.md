# System-HIS v1.2 Freeze Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> **Authoring note:** This plan was written by the planning session; **code is to be implemented by codex.** Each task gives exact files, interface contracts, concrete TDD test cases (the behavioral contract), and reuse pointers into existing code. Implementation steps give specifications and code sketches for the non-obvious parts rather than full line-by-line code, because codex owns the codebase and its style. The tests are authoritative — implement to pass them.

**Goal:** Freeze `system-his-v1.2` as the single canonical System-HIS schema: migrate the deterministic generator to it, give the v1.2 checker HIS↔RTL cross-checks, add the `data_flow.timing` contract and structured `control_flow`, and quarantine legacy/v1.1 data.

**Architecture:** One canonical schema string `system-his-v1.2`. RTL-introspection helpers are extracted from the v1.1 checker into a shared module so the v1.2 checker can reuse the existing port/width-parsing machinery instead of re-implementing it. The v1.2 checker grows from IR-self-consistency to IR + HIS↔RTL cross-checks. The deterministic generator (trusted baseline) emits v1.2 and its output doubles as golden checker fixtures.

**Tech Stack:** Python 3 (stdlib only), `unittest`, run from repo root with absolute imports `from LLM.src.sr2fpga_agent...`.

**Source spec:** `docs/superpowers/specs/2026-06-24-sr2fpga-system-his-v1.2-freeze-design.md`

## Execution Status - 2026-06-25

The original freeze plan has been implemented and extended by the follow-up T4
pilot work. The canonical schema is now `system-his-v1.2`; deterministic
generation, DeepSeek prompts, runner metadata, recorder exports, and L0 project
checking all route through the v1.2 contract.

Completed beyond the original freeze checklist:

- shared RTL introspection is available in `rtl_introspect.py`;
- v1.2 L0 checking includes HIS↔RTL cross-file consistency, width candidate
  equivalence, structured control-flow validation, and FSM owner inference for
  instance-prefixed names;
- generated samples are split into clean/quarantine training views by schema
  version;
- generation and repair failures are recorded as dataset events instead of
  crashing the runner;
- runner summaries include attempt stage transitions, contract metrics, and
  latent generated-testbench issue summaries;
- generated-testbench static checks now cover observation races and valid-held
  reaccept risks;
- semantic trace parsing is available for valid-ready mismatch diagnosis;
- repair acceptance now rejects v1.2 repairs that introduce new L0 contract
  regressions when the upstream failure was not already an L0 consistency
  failure.

Latest local evidence:

- `pilot-his-v12-t4-fresh-l3h-20260625`: `L0_FAIL`, useful repair oscillation
  and contract-regression signal.
- `pilot-his-v12-t4-fresh-l3i-20260625`: official `L0_FAIL`, later shown to be
  an evaluator false positive around FSM owner inference.
- `pilot-his-v12-t4-fresh-l3j-20260625`: `L1`, semantic trace found a
  generated-testbench valid reaccept/oracle bug.
- `pilot-his-v12-t4-fresh-l3k-20260625`: `L1`, no latent testbench issues after
  the checker/prompt fix; remaining mismatches are cleaner RTL/protocol
  semantic repair targets.

Current next step is no longer schema freeze itself. It is to freeze the current
prompt/checker configuration for a small T3/T4 batch and decide whether the next
milestone optimizes for L3 repair success or for a cleaner failure-repair
dataset slice.

## Global Constraints

- Run everything from the repo root; modules use absolute imports `from LLM.src.sr2fpga_agent...` (no `__init__.py` under `LLM/`).
- Test command: `python3 -m unittest discover -s LLM/tests -q` (must stay green after every task).
- Canonical schema string is exactly `system-his-v1.2` (the `-topdown` suffix is retired; treat `-topdown` and `system-his-v1.1` as legacy).
- `predicted_qor.json` stays model-only; never leak measured/tool results into it.
- LF line endings for `*.py/.sh/.yaml/.env`; never introduce CRLF.
- Never commit API keys, `.env`, model weights, or large generated datasets; `tmp/sr2fpga_runs/` stays local.
- Cross-check strictness (from spec): port existence + direction strict; width semantic-equivalence; guard grammar nesting depth ≤ 2.

## Current-state reconciliation (verified 2026-06-24, tip `bbf70af`)

- `project_generator.py:160` emits `"schema_version": "system-his-v1.1"`.
- At plan start, `system_his_v12_checker.py:9` had `SCHEMA_VERSION = "system-his-v1.2-topdown"` and did **IR self-consistency only** — it never read RTL (`GeneratedProject`/`.files`/module parsing absent).
- `system_his_checker.py` (v1.1) **already implements** HIS↔RTL cross-checks and contains reusable helpers: `_parse_module_ports`, `_declared_module_ports`, `_module_port_body`, `_matching_paren`, `_port_width`, `_normalize_width`, `_declared_modules`. Reuse these; do not rewrite.
- No uncommitted codex work; only `tmp/sr2fpga_runs/` is untracked.

## File structure

- Create `LLM/src/sr2fpga_agent/rtl_introspect.py` — shared RTL port/width parsing (extracted from v1.1 checker).
- Modify `LLM/src/sr2fpga_agent/system_his_checker.py` — import from `rtl_introspect`; dispatch v1.2 to the new cross-check.
- Modify `LLM/src/sr2fpga_agent/system_his_v12_checker.py` — rename schema const; add `data_flow.timing`, structured `control_flow`/FSM, guard grammar, and an RTL cross-check entry point.
- Modify `LLM/src/sr2fpga_agent/project_generator.py` — emit `system-his-v1.2` for all task families.
- Modify `LLM/src/sr2fpga_agent/deepseek.py` — v1.2 prompts/parser (drop `-topdown`; add timing + control_flow contract).
- Modify `LLM/src/sr2fpga_agent/runner.py` — schema-version labels; quarantine metadata.
- Tests: extend `test_sr2fpga_agent_system_his_v12_checker.py`, `test_sr2fpga_agent_project_generator.py`; add `test_sr2fpga_agent_rtl_introspect.py`.
- Docs: `docs/current-status.md`, `docs/sr2fpga-agent-handoff-2026-06-22.md`, `docs/system_his_examples/t4_dual_stream_join.system-his-v1.2.json`.

---

### Task 1: Extract shared RTL-introspection helpers (DRY foundation)

**Files:**
- Create: `LLM/src/sr2fpga_agent/rtl_introspect.py`
- Modify: `LLM/src/sr2fpga_agent/system_his_checker.py` (replace local helpers with imports)
- Test: `LLM/tests/test_sr2fpga_agent_rtl_introspect.py`

**Interfaces:**
- Produces: `parse_module_ports(content: str, module_name: str) -> dict[str, dict]` (each value `{"direction": str, "width": int|str}`); `declared_modules(files: dict[str,str], sources: list[str]) -> set[str]`; `declared_module_ports(files, sources) -> dict[str, dict[str,dict]]`; `normalize_width(value) -> str`; `port_width(range_text: str|None) -> int|str`.
- Consumes: nothing new.

- [x] **Step 1: Write the failing test**

```python
# test_sr2fpga_agent_rtl_introspect.py
from LLM.src.sr2fpga_agent.rtl_introspect import parse_module_ports, normalize_width

def test_parse_module_ports_extracts_direction_and_width():
    rtl = "module top(input clk, input rst_n, input en, output reg [7:0] count);\nendmodule\n"
    ports = parse_module_ports(rtl, "top")
    assert ports["count"]["direction"] == "output"
    assert normalize_width(ports["count"]["width"]) == normalize_width(8)
    assert ports["clk"]["direction"] == "input"

def test_normalize_width_treats_range_and_int_equal():
    assert normalize_width("[7:0]") == normalize_width(8)
```

- [x] **Step 2: Run to verify it fails** — `python3 -m unittest LLM.tests.test_sr2fpga_agent_rtl_introspect -q` → FAIL (module not found).

- [x] **Step 3: Implement** — move `_parse_module_ports`, `_module_port_body`, `_matching_paren`, `_port_width`, `_normalize_width`, `_declared_modules`, `_declared_module_ports`, `_declared_module_parameters`, `_module_parameter_names`, `_split_port_declarations` from `system_his_checker.py` into `rtl_introspect.py` as public functions (drop leading underscore on the ones other modules need: `parse_module_ports`, `declared_modules`, `declared_module_ports`, `declared_module_parameters`, `normalize_width`, `port_width`). Keep `normalize_width` semantics: numeric `[N:0]` → `str(N+1)`, otherwise stripped string.

- [x] **Step 4: Update v1.1 checker to import them** — in `system_his_checker.py`, replace the moved local helpers with `from LLM.src.sr2fpga_agent.rtl_introspect import (...)`. Keep its public `check_project_l0` behavior identical.

- [x] **Step 5: Run full suite** — `python3 -m unittest discover -s LLM/tests -q` → all pass (v1.1 checker behavior unchanged).

- [x] **Step 6: Commit decision** — commit intentionally not created in this dirty workspace: `git add LLM/src/sr2fpga_agent/rtl_introspect.py LLM/src/sr2fpga_agent/system_his_checker.py LLM/tests/test_sr2fpga_agent_rtl_introspect.py && git commit -m "Extract shared RTL-introspection helpers"`

  Status note: implementation and verification are complete; commit was not
  created because the current workspace already contains broader uncommitted
  work and the user did not request a commit.

---

### Task 2: Rename canonical schema string to `system-his-v1.2`

**Files:**
- Modify: `LLM/src/sr2fpga_agent/system_his_v12_checker.py:9`
- Modify: `LLM/src/sr2fpga_agent/system_his_checker.py` (dispatch constant)
- Modify: `LLM/src/sr2fpga_agent/deepseek.py` (prompt + parser schema string)
- Modify: `LLM/src/sr2fpga_agent/runner.py` (`_sample_system_his_schema_version`)
- Modify: `docs/system_his_examples/t4_dual_stream_join.system-his-v1.2.json`
- Modify: configs referencing the schema string if any
- Test: `LLM/tests/test_sr2fpga_agent_system_his_v12_checker.py`

**Interfaces:**
- Produces: `SCHEMA_VERSION == "system-his-v1.2"` consumed by checker, deepseek parser, runner labels.

- [x] **Step 1: Write the failing test**

```python
from LLM.src.sr2fpga_agent.system_his_v12_checker import check_system_his_v12, SCHEMA_VERSION

def test_canonical_schema_version_is_v12():
    assert SCHEMA_VERSION == "system-his-v1.2"

def test_checker_rejects_topdown_suffix(valid_v12_payload):
    payload = dict(valid_v12_payload); payload["schema_version"] = "system-his-v1.2-topdown"
    result = check_system_his_v12(payload)
    assert not result.passed
```

- [x] **Step 2: Run to verify it fails** — FAIL on the old
  `SCHEMA_VERSION == "system-his-v1.2-topdown"` value and on acceptance of the
  retired suffix.

- [x] **Step 3: Implement** — set `SCHEMA_VERSION = "system-his-v1.2"`; update the v1.1 checker's dispatch constant (`SYSTEM_HIS_V12_SCHEMA`), the deepseek prompt text + `parse_system_his_v12` expectation, `runner._sample_system_his_schema_version` (return `"system-his-v1.2"` for the two-stage source), and the example JSON `schema_version`.

- [x] **Step 4: Run full suite** — `python3 -m unittest discover -s LLM/tests -q` → all pass (175 tests).

- [x] **Step 5: Commit decision** — commit intentionally not created in this dirty workspace: `git commit -am "Rename canonical System-HIS schema to system-his-v1.2"`

  Status note: implementation and verification are complete; commit was not
  created because the current workspace already contains broader uncommitted
  work and the user did not request a commit.

---

### Task 3: Validate `data_flow.timing` contract (IR self-consistency)

**Files:**
- Modify: `LLM/src/sr2fpga_agent/system_his_v12_checker.py`
- Test: `LLM/tests/test_sr2fpga_agent_system_his_v12_checker.py`

**Interfaces:**
- Consumes: existing `_data_flow_names` walk.
- Produces: per-flow `timing` validation folded into the data_flow check.

- [x] **Step 1: Write the failing test**

```python
def test_data_flow_timing_optional_but_validated():
    # missing timing is OK
    ok = dict(valid_v12_payload())  # flow with no "timing"
    assert check_system_his_v12(ok).passed
    # present timing must be well-formed
    bad = with_flow_timing({"latency_cycles": 3, "initiation_interval": 0})
    res = check_system_his_v12(bad)
    assert not res.passed
    assert any("initiation_interval" in e for e in res.errors)
```

- [x] **Step 2: Run to verify it fails** — malformed `timing` was accepted before implementation.

- [x] **Step 3: Implement** — when a `data_flow[i]` has a `timing` key: `latency_cycles` non-negative int; `initiation_interval` positive int; `throughput` (if present) non-empty string. Absent `timing` is valid (optional per spec).

- [x] **Step 4: Run suite** — `python3 -m unittest discover -s LLM/tests -q` → all pass (176 tests).

- [x] **Step 5: Commit decision** — commit intentionally not created in this dirty workspace: `git commit -am "Validate optional data_flow.timing contract in v1.2 checker"`

  Status note: implementation and verification are complete; commit was not
  created because the current workspace already contains broader uncommitted
  work and the user did not request a commit.

---

### Task 4: Validate structured `control_flow`, FSM, and guard grammar (IR self-consistency)

**Files:**
- Modify: `LLM/src/sr2fpga_agent/system_his_v12_checker.py`
- Test: `LLM/tests/test_sr2fpga_agent_system_his_v12_checker.py`

**Interfaces:**
- Consumes: `state.fsms`, `control_flow`, declared signal/state/flow name sets.
- Produces: `validate_guard(when, valid_signals, depth=0) -> list[str]` (errors); FSM + transition + enable_rule validation folded into the control_flow check.

Guard grammar (spec §control_flow): atom `{signal, op, value}` with `op ∈ {==,!=,<,>,&&,||}` and `signal` resolving to a declared port / state / flow / `fsm.state`; combinators `all_of`/`any_of` (lists); **max nesting depth 2**.

- [x] **Step 1: Write the failing tests**

```python
def test_fsm_structure_validated():
    # initial/reset_state must be in states
    bad = with_fsm({"name":"m","states":["A","B"],"initial":"Z","reset_state":"A"})
    assert not check_system_his_v12(bad).passed

def test_fsm_transition_endpoints_must_be_declared_states():
    bad = with_control([{"kind":"fsm_transition","fsm":"m","from":"A","to":"NOPE",
                         "when":{"signal":"go","op":"==","value":1}}])
    res = check_system_his_v12(bad)
    assert any("NOPE" in e for e in res.errors)

def test_guard_depth_over_two_rejected():
    deep = {"all_of":[{"any_of":[{"all_of":[{"signal":"a","op":"==","value":1}]}]}]}
    bad = with_control([{"kind":"enable_rule","when":deep,
                         "effect":{"action":"assert","target":"q.start"}}])
    res = check_system_his_v12(bad)
    assert any("depth" in e.lower() for e in res.errors)

def test_guard_unknown_operator_rejected():
    bad = with_control([{"kind":"enable_rule",
                         "when":{"signal":"a","op":"~=","value":1},
                         "effect":{"action":"assert","target":"q.start"}}])
    assert not check_system_his_v12(bad).passed
```

- [x] **Step 2: Run to verify they fail** — FSM structure, transition endpoint,
  guard depth, and guard operator tests failed before implementation.

- [x] **Step 3: Implement**
  - `state.fsms[]`: `states` non-empty list of strings; `initial` and `reset_state` ∈ `states`; `name` unique; record fsm names + `<fsm>.state` as referenceable signals.
  - `fsm_transition`: `fsm` ∈ declared fsm names; `from`/`to` ∈ that fsm's states; `when` passes `validate_guard`; optional `effect` target resolves to a declared instance/state/flow.
  - `enable_rule`: `when` passes `validate_guard`; `effect.target` resolves.
  - `validate_guard(when, valid_signals, depth)`: if `when` has `all_of`/`any_of` → must be a list, recurse with `depth+1`, and **error if depth+1 > 2**; else must be an atom `{signal, op, value}` with `op` in the allowed set and `signal` ∈ `valid_signals` (declared ports across instances/top, state names, flow names, `<fsm>.state`).

- [x] **Step 4: Run suite** — `python3 -m unittest discover -s LLM/tests -q` → all pass (180 tests).

- [x] **Step 5: Commit decision** — commit intentionally not created in this dirty workspace: `git commit -am "Validate structured control_flow, FSM, and guard grammar (depth<=2)"`

  Status note: implementation and verification are complete; commit was not
  created because the current workspace already contains broader uncommitted
  work and the user did not request a commit.

---

### Task 5: Add HIS↔RTL cross-check to the v1.2 checker

**Files:**
- Modify: `LLM/src/sr2fpga_agent/system_his_v12_checker.py`
- Test: `LLM/tests/test_sr2fpga_agent_system_his_v12_checker.py`

**Interfaces:**
- Consumes: `rtl_introspect.parse_module_ports`, `declared_modules`, `declared_module_ports`, `normalize_width` (Task 1).
- Produces: `check_system_his_v12_against_rtl(payload: dict, project: GeneratedProject) -> SystemHisV12CheckResult` — runs the IR self-check **plus** RTL cross-checks.

Cross-checks (spec §L0 cross-check):
- **Strict:** each `components[].name` is an RTL module in its `source`; each `instances[].component` resolves; each instance appears instantiated in `rtl/top.v`; for every component port, the RTL module has a port of the same name and **same direction**; `data_flow.path` endpoints (`top.<port>` / `<instance>.<port>`) exist in the resolved RTL ports; `artifacts` match `manifest.json`; testbench instantiates the top; SDC `get_ports` reference only real top ports; each `state.fsms[].states` name appears in the owner module RTL (name-level grep of state identifiers).
- **Semantic:** port width compared via `normalize_width` (so `[7:0]` ≡ `8` ≡ a param resolving to 8) — never raw-string compare.

- [x] **Step 1: Write the failing tests**

```python
def test_cross_check_passes_for_consistent_project(consistent_v12_project):
    res = check_system_his_v12_against_rtl(consistent_v12_project.his, consistent_v12_project)
    assert res.passed

def test_cross_check_flags_renamed_port():
    proj = consistent_v12_project()
    proj.files["rtl/counter_core.v"] = proj.files["rtl/counter_core.v"].replace("count", "cnt")
    res = check_system_his_v12_against_rtl(proj.his, proj)
    assert not res.passed

def test_cross_check_flags_direction_mismatch():
    # HIS says output, RTL says input
    ...
    assert not res.passed

def test_cross_check_width_semantic_equivalence_passes():
    # HIS width "8" vs RTL "[7:0]" must pass
    ...
    assert res.passed
```

- [x] **Step 2: Run to verify they fail** — failed because
  `check_system_his_v12_against_rtl` did not exist.

- [x] **Step 3: Implement** — `check_system_his_v12_against_rtl` first calls `check_system_his_v12(payload)` (IR self-check), then, using `rtl_introspect` helpers over `artifacts.rtl_sources`, applies the strict + semantic cross-checks above, appending errors. Mirror the v1.1 checker's existing cross-check logic but against the v1.2 `components`/`instances`/`data_flow` model.

- [x] **Step 4: Run suite** — `python3 -m unittest discover -s LLM/tests -q` → all pass (184 tests).

- [x] **Step 5: Commit decision** — commit intentionally not created in this dirty workspace: `git commit -am "Add HIS<->RTL cross-check to v1.2 checker (port/direction strict, width semantic)"`

  Status note: implementation and verification are complete; commit was not
  created because the current workspace already contains broader uncommitted
  work and the user did not request a commit.

---

### Task 6: Dispatch v1.2 through the project-level L0 checker

**Files:**
- Modify: `LLM/src/sr2fpga_agent/system_his_checker.py`
- Test: `LLM/tests/test_sr2fpga_agent_system_his_v12_checker.py` (or the L0 dispatch test location)

**Interfaces:**
- Consumes: `check_system_his_v12_against_rtl` (Task 5).
- Produces: `check_project_l0(project)` routes `schema_version == "system-his-v1.2"` to the cross-check and returns an `L0CheckResult` whose `errors` include cross-file consistency violations (feeding the metric).

- [x] **Step 1: Write the failing test**

```python
def test_l0_dispatch_runs_v12_cross_check_on_v12_project():
    proj = consistent_v12_project()
    proj.files["sim/tb_top.v"] = proj.files["sim/tb_top.v"].replace("top", "wrong_top")
    result = check_project_l0(proj)
    assert not result.passed
    assert any("instantiate" in e.lower() or "top" in e.lower() for e in result.errors)
```

- [x] **Step 2: Run to verify it fails** — v1.2 L0 accepted a project whose
  testbench no longer instantiated the top module.

- [x] **Step 3: Implement** — in `check_project_l0`, when the parsed `system_his.json` has `schema_version == "system-his-v1.2"`, call `check_system_his_v12_against_rtl(payload, project)` and map its result into `L0CheckResult` (plus the existing basic project-artifact contract). Keep v1.1/legacy dispatch unchanged.

- [x] **Step 4: Run suite** — `python3 -m unittest discover -s LLM/tests -q` → all pass (185 tests).

- [x] **Step 5: Commit decision** — commit intentionally not created in this dirty workspace: `git commit -am "Route system-his-v1.2 projects through cross-file L0 check"`

  Status note: implementation and verification are complete; commit was not
  created because the current workspace already contains broader uncommitted
  work and the user did not request a commit.

---

### Task 7a: Migrate deterministic generator to v1.2 — single-module families

**Files:**
- Modify: `LLM/src/sr2fpga_agent/project_generator.py`
- Test: `LLM/tests/test_sr2fpga_agent_project_generator.py`

**Interfaces:**
- Produces: `ProjectGenerator.generate(...)` emits `system_his.json` with `schema_version == "system-his-v1.2"` and the full aspect structure (spec §schema shape) for `counter`, `fifo`, `simple_fsm`, `ram_read_write`.

- [x] **Step 1: Write the failing test**

```python
from LLM.src.sr2fpga_agent.system_his_checker import check_project_l0

def test_counter_emits_valid_v12():
    proj = ProjectGenerator().generate(ProjectRequest("counter",8,"c"), platform())
    his = json.loads(proj.files["system_his.json"])
    assert his["schema_version"] == "system-his-v1.2"
    assert check_project_l0(proj).passed
```

- [x] **Step 2: Run to verify it fails** — deterministic single-module families
  still emitted `system-his-v1.1`.

- [x] **Step 3: Implement** — rewrite `_system_his()` to build the v1.2 aspects: `intent`, `top` (name/parameters/clocks/resets/ports/interfaces), `components`, `instances`, `data_flow` (with optional `timing` where a pipeline exists), `control_flow` (reset_rule + any FSM for `simple_fsm`), `state`, `timing`, `resources`, `verification`, `artifacts`. `simple_fsm` must declare its FSM in `state.fsms` + `fsm_transition` rules and pass the FSM cross-check. Reuse the deterministic RTL already produced so cross-check passes by construction.

- [x] **Step 4: Run suite** — single-module v1.2 L0 test passes; full suite passes (190 tests after Tasks 8/9).

- [x] **Step 5: Commit decision** — commit intentionally not created in this dirty workspace: `git commit -am "Emit system-his-v1.2 from deterministic generator (single-module families)"`

  Status note: implementation and verification are complete; commit was not
  created because the current workspace already contains broader uncommitted
  work and the user did not request a commit.

---

### Task 7b: Migrate deterministic generator to v1.2 — composed_* topologies

**Files:**
- Modify: `LLM/src/sr2fpga_agent/project_generator.py`
- Test: `LLM/tests/test_sr2fpga_agent_project_generator.py`

**Interfaces:**
- Produces: v1.2 output for `composed_event_counter` (T1), `composed_stream_accumulator` (T2), `composed_stream_fork` (T3), `composed_dual_stream_join` (T4), plus the other multi-module families (`uart_tx`, `spi_master`, `pwm_controller`, `fir_filter`, `streaming_valid_ready`, `matrix_vector_mac`).

- [x] **Step 1: Write the failing test**

```python
import pytest
@pytest.mark.parametrize("task", ["composed_event_counter","composed_stream_accumulator",
    "composed_stream_fork","composed_dual_stream_join","uart_tx","spi_master",
    "pwm_controller","fir_filter","streaming_valid_ready","matrix_vector_mac"])
def test_multimodule_emits_valid_v12(task):
    proj = ProjectGenerator().generate(ProjectRequest(task,8,task), platform())
    assert json.loads(proj.files["system_his.json"])["schema_version"] == "system-his-v1.2"
    assert check_project_l0(proj).passed
```

- [x] **Step 2: Run to verify it fails** — covered by the deterministic
  generator migration from v1.1 to v1.2 and then extended to all multi-module
  families.

- [x] **Step 3: Implement** — map each topology's `COMPONENT_TOPOLOGIES` nodes/edges to v1.2 `components`/`instances`/`data_flow`. Streaming families (`composed_stream_*`, `streaming_valid_ready`, `matrix_vector_mac`) get `data_flow.timing` (latency/II) and `control_flow` `handshake_rule`/`stall_rule` where backpressure exists. Repeated instances (the two `skid_buffer` in T4) use distinct `instances[].name` referencing one `components[].name` — the v1.2 split that fixes the old ambiguity.

- [x] **Step 4: Run suite** — `python3 -m unittest discover -s LLM/tests -q` → all pass (190 tests after Tasks 8/9).

- [x] **Step 5: Commit decision** — commit intentionally not created in this dirty workspace: `git commit -am "Emit system-his-v1.2 from deterministic generator (multi-module/composed families)"`

  Status note: implementation and verification are complete; commit was not
  created because the current workspace already contains broader uncommitted
  work and the user did not request a commit.

---

### Task 8: Update DeepSeek two-stage prompts/parser to v1.2 contract

**Files:**
- Modify: `LLM/src/sr2fpga_agent/deepseek.py`
- Test: `LLM/tests/test_sr2fpga_agent_deepseek.py`

**Interfaces:**
- Consumes: `check_system_his_v12` (extended in Tasks 3–4).
- Produces: `_system_his_v12_messages` requests `system-his-v1.2` with `data_flow.timing` (optional) and structured `control_flow`/guards; `parse_system_his_v12` validates against the extended checker.

- [x] **Step 1: Write the failing test**

```python
def test_parser_requires_canonical_v12_schema():
    payload = valid_v12_json_text()  # schema_version system-his-v1.2
    assert parse_system_his_v12(payload)["schema_version"] == "system-his-v1.2"

def test_parser_rejects_topdown_as_v12():
    with pytest.raises(ValueError):
        parse_system_his_v12(topdown_json_text())
```

- [x] **Step 2: Run to verify it fails** — prompt did not yet mention
  `data_flow.timing`, structured `when/effect`, guard grammar, or depth <= 2.

- [x] **Step 3: Implement** — update prompt strings and the example JSON inside `_system_his_v12_messages` to the canonical schema + new aspects (timing, structured control_flow with the guard grammar and depth-2 rule); keep the bounded checker-feedback retry. No live API call in tests — feed canned JSON to `parse_system_his_v12`.

- [x] **Step 4: Run suite** — DeepSeek tests pass; full suite passes (190 tests after Task 9).

- [x] **Step 5: Commit decision** — commit intentionally not created in this dirty workspace: `git commit -am "Update DeepSeek two-stage prompts/parser to canonical v1.2 contract"`

  Status note: implementation and verification are complete; commit was not
  created because the current workspace already contains broader uncommitted
  work and the user did not request a commit.

---

### Task 9: Quarantine labeling for legacy/v1.1 data

**Files:**
- Modify: `LLM/src/sr2fpga_agent/runner.py` (metadata) and/or `LLM/src/sr2fpga_agent/recorder.py` (export views)
- Test: `LLM/tests/test_sr2fpga_agent_runner.py` and/or `LLM/tests/test_sr2fpga_agent_recorder.py`

**Interfaces:**
- Produces: each sample's `metadata.json` carries `system_his_schema_version` ∈ {`legacy`, `system-his-v1.1`, `system-his-v1.2`} and a derived `training_split` ∈ {`clean`, `quarantine`} where non-v1.2 → `quarantine`. Export views carry both fields.

- [x] **Step 1: Write the failing test**

```python
def test_non_v12_sample_is_quarantined():
    md = sample_metadata(schema_version="system-his-v1.1")
    assert md["training_split"] == "quarantine"

def test_v12_sample_is_clean():
    md = sample_metadata(schema_version="system-his-v1.2")
    assert md["training_split"] == "clean"
```

- [x] **Step 2: Run to verify it fails** — metadata/export rows did not include
  `training_split`, and deterministic samples were still labeled v1.1.

- [x] **Step 3: Implement** — derive `training_split` from the schema version when building sample metadata; propagate into `export_training_views` rows so a clean-split filter is a one-field query. Do not delete or migrate existing quarantined samples.

- [x] **Step 4: Run suite** — `python3 -m unittest discover -s LLM/tests -q` → all pass (190 tests).

- [x] **Step 5: Commit decision** — commit intentionally not created in this dirty workspace: `git commit -am "Label legacy/v1.1 samples as quarantine, v1.2 as clean training split"`

  Status note: implementation and verification are complete; commit was not
  created because the current workspace already contains broader uncommitted
  work and the user did not request a commit.

---

### Task 10: Update living docs (status + handoff + example)

**Files:**
- Modify: `docs/current-status.md`, `docs/sr2fpga-agent-handoff-2026-06-22.md`, `docs/system_his_examples/t4_dual_stream_join.system-his-v1.2.json`

- [x] **Step 1:** Update the example JSON to canonical `system-his-v1.2` with a `data_flow.timing` example and a structured `control_flow` FSM/guard example (it is the reference fixture).
- [x] **Step 2:** In `current-status.md` and the handoff, record: v1.2 frozen as canonical, deterministic generator migrated, v1.2 checker now does cross-file checks, legacy/v1.1 quarantined. Remove the "two schemas in parallel" framing.
- [x] **Step 3: Commit decision** — commit intentionally not created in this dirty workspace: `git commit -am "Update status/handoff/example for System-HIS v1.2 freeze"`

  Status note: implementation and verification are complete; commit was not
  created because the current workspace already contains broader uncommitted
  work and the user did not request a commit.

---

## Self-review

**Spec coverage:** v1.2 canonical (Task 2,7) ✓; generator migration (7a/7b) ✓; HIS↔RTL cross-check strict ports/direction + semantic width (5) ✓; FSM state-name cross-check (5) ✓; data_flow.timing (3,7b) ✓; structured control_flow + guard depth≤2 (4) ✓; one-checker dispatch (6) ✓; quarantine labeling (9) ✓; DRY reuse of v1.1 helpers (1) ✓; docs (10) ✓. RL accelerator is forward-compat (expressible via Tasks 3–5 primitives), not a build task — consistent with spec scope.

**Placeholder scan:** Test fixtures referenced as helpers (`valid_v12_payload`, `consistent_v12_project`, `with_flow_timing`, `with_fsm`, `with_control`, `sample_metadata`) are to be authored by codex alongside the tests; each test asserts concrete behavior. No TBD/TODO in implementation specs.

**Type consistency:** `check_system_his_v12(payload)` (IR) and `check_system_his_v12_against_rtl(payload, project)` (IR+RTL) both return `SystemHisV12CheckResult`; `rtl_introspect` function names match across Tasks 1/5; `normalize_width` used consistently for the semantic width rule; schema string `system-his-v1.2` consistent across Tasks 2/7/8/9/10.

## Reconciliation guidance for codex

- Tasks are independent commits; **Task 1 (helper extraction) must land first** so Task 5 can reuse the parsing machinery instead of duplicating it.
- Tasks 7a/7b touch the largest surface (`project_generator.py`); land Tasks 1–6 (checker ready) before them so the generator can be validated against the finished checker.
- This plan only modifies the spec/plan docs in this session; **all code changes above are codex's to implement.** Coordinate so codex is not mid-edit in `project_generator.py` / `system_his_v12_checker.py` when starting — those are the two highest-collision files.
