# SR2FPGA Phase C Independent Oracle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add independent Python reference models, evaluator-only oracle bundles, hidden/random/stress scenarios, and auditable Line-A evidence for the nine Phase C task families.

**Architecture:** Trusted Python reference builders write versioned fixed-width `.memh` bundles under each attempt's `eval/oracle/` directory. The existing SystemVerilog testbenches remain protocol drivers, run once per scenario through explicit plusargs, and emit structured mismatch records; the agent aggregates the scenario verdicts without exposing hidden vectors to prompts or training exports.

**Tech Stack:** Python 3.11+, frozen dataclasses, JSON, SHA-256, `random.Random`, Icarus Verilog/SystemVerilog 2012, existing `CommandRunner`, pytest/unittest, existing SR2FPGA recorder and evidence ledger.

## Global Constraints

- Implement exactly four domains and nine families: numeric (`fir_filter`, `matrix_vector_mac`), signal (`matched_filter`, `peak_detector`, `p_pulse_radar_signal`), image (`sobel_threshold`, `p_vision_defect_core`), and RL (`qtable_update_core`, `p_rl_qlearning_accel`).
- Keep Python reference code independent of generated RTL; it may consume only the task family contract, width, fixed task parameters, and scenario seed.
- Store runtime bundles under `attempts/attempt_xxxx/eval/oracle/`; never add them to `GeneratedProject.files`.
- Run a fresh simulator process for every required scenario and require every scenario to pass for L2 to pass.
- Keep `public_smoke`, `hidden_deterministic`, `randomized_fixed_seed`, and `stress` as the only Phase C scenario classes.
- Export only hidden scenario IDs/classes, counts, hashes, and sanitized mismatch metadata. Never export hidden input/expected records, actual hidden seeds, or a seed/parameter combination that regenerates hidden vectors.
- Treat oracle and tool-environment failures as non-model verdicts. Treat DUT mismatches and DUT timeouts as model/design failures.
- Preserve existing embedded testbench behavior when independent-oracle mode is disabled.
- Do not weaken existing mutation suites or the Phase B `14/14` Paper-1-core mutation-qualified gate.
- Keep L4 and L5 behavior unchanged; Phase C completion requires L0-L3 only.
- The worktree contains unrelated user changes. Stage and commit only files named by each task.

---

## File Structure

### New files

- `LLM/src/sr2fpga_agent/oracles/__init__.py`: family-to-reference-builder registry and public bundle API.
- `LLM/src/sr2fpga_agent/oracles/types.py`: immutable bundle, scenario, field-layout, and run-evidence types.
- `LLM/src/sr2fpga_agent/oracles/bundle.py`: `.memh` writing, manifest/hash validation, loading, and export sanitization.
- `LLM/src/sr2fpga_agent/oracles/numeric.py`: FIR and matrix-vector reference builders.
- `LLM/src/sr2fpga_agent/oracles/signal.py`: matched-filter, peak-detector, and pulse-radar reference builders.
- `LLM/src/sr2fpga_agent/oracles/image.py`: Sobel and vision-defect reference builders.
- `LLM/src/sr2fpga_agent/oracles/rl.py`: TD-update and Q-learning-shell reference builders.
- `LLM/src/sr2fpga_agent/oracle_runner.py`: one-process-per-scenario execution and aggregate ToolResult creation.
- `LLM/tests/test_sr2fpga_agent_oracle_bundle.py`: bundle/path/hash/determinism/sanitization tests.
- `LLM/tests/test_sr2fpga_agent_oracle_runner.py`: scenario invocation and verdict aggregation tests.
- `LLM/tests/test_sr2fpga_agent_oracle_numeric.py`: hand-calculated numeric reference tests.
- `LLM/tests/test_sr2fpga_agent_oracle_signal.py`: hand-calculated signal reference tests.
- `LLM/tests/test_sr2fpga_agent_oracle_image.py`: hand-calculated image reference tests.
- `LLM/tests/test_sr2fpga_agent_oracle_rl.py`: hand-calculated RL reference tests.
- `configs/current/sr2fpga_phase_c_independent_oracle.example.yaml`: deterministic nine-family Line-A qualification run.
- `docs/sr2fpga-phase-c-independent-oracle-evidence-2026-07-14.md`: generated/curated Phase C evidence report after C5.

### Modified files

- `LLM/src/sr2fpga_agent/agent.py`: build attempt-local bundles, invoke scenario runner, aggregate labels, and reuse the same bundle for mutation runs.
- `LLM/src/sr2fpga_agent/runner.py`: load `run_independent_oracle`, pass it to the agent, and summarize independent-oracle evidence.
- `LLM/src/sr2fpga_agent/recorder.py`: persist sanitized `oracle_profile` and per-class L2 status without exporting bundle payloads.
- `LLM/src/sr2fpga_agent/log_parser.py`: parse `SR2FPGA_MISMATCH` JSON lines before legacy `TEST_FAIL` text.
- `LLM/src/sr2fpga_agent/path_safety.py`: classify oracle source/runtime paths as trusted artifacts.
- `LLM/src/sr2fpga_agent/task_families/datapath.py`: oracle-mode testbench branches for five numeric/signal families.
- `LLM/src/sr2fpga_agent/task_families/image.py`: oracle-mode testbench branches for two image families.
- `LLM/src/sr2fpga_agent/task_families/rl.py`: oracle-mode testbench branches for two RL families.
- `LLM/src/sr2fpga_agent/task_evidence.py`: validate and render independent-oracle evidence fields.
- `docs/sr2fpga-task-evidence-v0.1.json`: record Phase C evidence after the qualification run while retaining the existing schema path.
- `docs/sr2fpga-task-evidence-status.md`: regenerate the human-readable evidence matrix.
- `docs/current-status.md`: record Phase C completion only after C5 gates pass.
- Existing tests for agent, runner, recorder, path safety, structured signals, project generation, and evidence audit.

---

### Task 1: C0 Bundle Types, Serialization, and Validation

**Files:**
- Create: `LLM/src/sr2fpga_agent/oracles/__init__.py`
- Create: `LLM/src/sr2fpga_agent/oracles/types.py`
- Create: `LLM/src/sr2fpga_agent/oracles/bundle.py`
- Test: `LLM/tests/test_sr2fpga_agent_oracle_bundle.py`

**Interfaces:**
- Produces: `OracleField`, `OracleScenarioSpec`, `OracleScenarioManifest`, `OracleBundle`, an initially empty `REFERENCE_BUILDERS` registry, `build_oracle_bundle_for_request()`, `write_oracle_bundle()`, `load_oracle_bundle()`, and `sanitize_oracle_profile()`.
- Consumes: no generated RTL and no agent state.

- [ ] **Step 1: Write failing dataclass and serialization tests**

```python
def test_bundle_round_trip_uses_relative_paths_and_fixed_width_memh(tmp_path):
    scenario = OracleScenarioSpec(
        scenario_id="public_smoke_001",
        scenario_class="public_smoke",
        seed=7,
        input_record_width_bits=8,
        expected_record_width_bits=12,
        input_fields=(OracleField("sample", 7, 0, True),),
        expected_fields=(OracleField("result", 11, 0, True),),
        input_records=(0x05, 0xFC),
        expected_records=(0x00F, 0xFEA),
    )
    bundle = write_oracle_bundle(
        root=tmp_path / "oracle",
        family_id="fir_filter",
        reference_model="numeric.fir_filter",
        reference_version="1",
        task_parameters={"width": 8},
        scenarios=(scenario,),
    )
    loaded = load_oracle_bundle(bundle.root)
    assert loaded.manifest["family_id"] == "fir_filter"
    assert (bundle.root / "public/public_smoke_001/input.memh").read_text() == "05\nfc\n"
    assert loaded.scenarios[0].input_sha256
    assert loaded.bundle_sha256 == bundle.bundle_sha256
```

Add tests that reject `../escape.memh`, absolute paths, unsupported scenario classes, duplicate scenario IDs, overlapping field ranges, records wider than the declared width, missing files, modified files, malformed JSON, and zero transactions.

- [ ] **Step 2: Run the tests and verify the module is missing**

Run:

```powershell
python -m pytest LLM/tests/test_sr2fpga_agent_oracle_bundle.py -q
```

Expected: collection fails because `sr2fpga_agent.oracles` does not exist.

- [ ] **Step 3: Implement immutable oracle types**

```python
SCENARIO_CLASSES = frozenset(
    {"public_smoke", "hidden_deterministic", "randomized_fixed_seed", "stress"}
)

@dataclass(frozen=True)
class OracleField:
    name: str
    msb: int
    lsb: int
    signed: bool

@dataclass(frozen=True)
class OracleScenarioSpec:
    scenario_id: str
    scenario_class: str
    seed: int
    input_record_width_bits: int
    expected_record_width_bits: int
    input_fields: tuple[OracleField, ...]
    expected_fields: tuple[OracleField, ...]
    input_records: tuple[int, ...]
    expected_records: tuple[int, ...]

@dataclass(frozen=True)
class OracleScenarioManifest:
    scenario_id: str
    scenario_class: str
    seed: int
    input_path: str
    expected_path: str
    transaction_count: int
    input_record_width_bits: int
    expected_record_width_bits: int
    input_fields: tuple[OracleField, ...]
    expected_fields: tuple[OracleField, ...]
    input_sha256: str
    expected_sha256: str

@dataclass(frozen=True)
class OracleBundle:
    root: Path
    family_id: str
    reference_model: str
    reference_version: str
    task_parameters: dict[str, object]
    scenarios: tuple[OracleScenarioManifest, ...]
    bundle_sha256: str
    manifest: dict[str, object]
```

- [ ] **Step 4: Implement fixed-width writing and strict validation**

`write_oracle_bundle()` must use lowercase hexadecimal, one record per line, and exactly `ceil(width / 4)` digits. `load_oracle_bundle()` must recompute every file hash and a canonical JSON bundle hash before returning.

```python
def _memh_text(records: tuple[int, ...], width: int) -> str:
    digits = (width + 3) // 4
    limit = 1 << width
    if not records or any(record < 0 or record >= limit for record in records):
        raise ValueError("oracle records must fit the declared unsigned bit pattern")
    return "".join(f"{record:0{digits}x}\n" for record in records)

def _safe_bundle_path(root: Path, relative_path: str) -> Path:
    candidate = (root / relative_path).resolve()
    candidate.relative_to(root.resolve())
    return candidate
```

The manifest stores the actual seed only in the evaluator-local bundle. `sanitize_oracle_profile()` emits `seed_sha256` and never emits `seed`, `input_path`, `expected_path`, or record payloads for withheld scenarios.

`oracles/__init__.py` owns the registry used by the agent. Task 1 initializes it without domain builders so C0 can be tested independently:

```python
REFERENCE_BUILDERS: dict[str, Callable[[int, Path], OracleBundle]] = {}

def build_oracle_bundle_for_request(
    family_id: str,
    request: ProjectRequest,
    output_root: Path,
) -> OracleBundle | None:
    builder = REFERENCE_BUILDERS.get(family_id)
    return None if builder is None else builder(request.width, output_root)
```

- [ ] **Step 5: Run bundle tests**

Run:

```powershell
python -m pytest LLM/tests/test_sr2fpga_agent_oracle_bundle.py -q
```

Expected: all bundle tests pass.

- [ ] **Step 6: Commit Task 1 only**

```powershell
git add -- LLM/src/sr2fpga_agent/oracles LLM/tests/test_sr2fpga_agent_oracle_bundle.py
git commit -m "feat: add independent oracle bundle format"
```

---

### Task 2: C0 Scenario Runner, Structured Mismatch Parsing, and Trusted Paths

**Files:**
- Create: `LLM/src/sr2fpga_agent/oracle_runner.py`
- Modify: `LLM/src/sr2fpga_agent/oracles/types.py`
- Modify: `LLM/src/sr2fpga_agent/log_parser.py`
- Modify: `LLM/src/sr2fpga_agent/path_safety.py`
- Test: `LLM/tests/test_sr2fpga_agent_oracle_runner.py`
- Test: `LLM/tests/test_sr2fpga_agent_structured_signals.py`
- Test: `LLM/tests/test_sr2fpga_agent_patch_as_pr.py`

**Interfaces:**
- Consumes: `OracleBundle`, `CommandRunner.run()`.
- Produces: `OracleScenarioResult`, `OracleRunEvidence`, `run_oracle_scenarios()`, `write_oracle_run_evidence()`, and an aggregate `ToolResult(stage="sim_run")`.

- [ ] **Step 1: Write failing one-process-per-scenario tests**

```python
def test_runner_invokes_vvp_once_per_scenario_and_aggregates_all_pass(bundle, fake_runner):
    evidence, tool_result = run_oracle_scenarios(fake_runner, Path("project"), bundle)
    assert len(fake_runner.calls) == 4
    assert all(call.command[:2] == ["vvp", "sim.out"] for call in fake_runner.calls)
    assert tool_result.status == "passed"
    assert {item.scenario_class for item in evidence.scenario_results} == {
        "public_smoke", "hidden_deterministic", "randomized_fixed_seed", "stress"
    }
```

Add tests proving that one DUT mismatch fails the aggregate, one timeout fails the aggregate, an invalid bundle returns `oracle_hash_mismatch` as a non-model failure, and a missing simulator returns `toolchain_environment_failure`.

- [ ] **Step 2: Run targeted tests and verify failure**

```powershell
python -m pytest LLM/tests/test_sr2fpga_agent_oracle_runner.py LLM/tests/test_sr2fpga_agent_structured_signals.py -q
```

Expected: oracle-runner imports or structured JSON assertions fail.

- [ ] **Step 3: Implement scenario execution and aggregate status**

Add `OracleScenarioResult` and `OracleRunEvidence` to `oracles/types.py`. `OracleRunEvidence` exposes `scenario_counts()` and `class_status(scenario_class)`, where a class passes only if it is present and all its scenarios pass.

```python
def run_oracle_scenarios(
    command_runner: CommandRunner,
    project_dir: Path,
    bundle: OracleBundle,
) -> tuple[OracleRunEvidence, ToolResult]:
    scenario_results = []
    for scenario in bundle.scenarios:
        command = [
            "vvp", "sim.out",
            f"+ORACLE_INPUT={bundle.root / scenario.input_path}",
            f"+ORACLE_EXPECTED={bundle.root / scenario.expected_path}",
            f"+ORACLE_SCENARIO_ID={scenario.scenario_id}",
            f"+ORACLE_SCENARIO_CLASS={scenario.scenario_class}",
            f"+ORACLE_TRANSACTION_COUNT={scenario.transaction_count}",
        ]
        result = command_runner.run(command, cwd=project_dir, stage="sim_run")
        result = validate_oracle_simulation_output(result)
        scenario_results.append(OracleScenarioResult.from_tool_result(scenario, result))
    evidence = OracleRunEvidence.from_results(bundle, tuple(scenario_results))
    return evidence, aggregate_oracle_tool_result(evidence)
```

The aggregate is `passed` only when every required scenario reports `TEST_PASS`. A process failure containing `TEST_FAIL` remains a DUT failure; missing files, invalid hashes, and command-not-found conditions carry a separate `failure_origin` in evidence.

- [ ] **Step 4: Parse structured mismatch JSON before legacy text**

```python
if raw_line.startswith("SR2FPGA_MISMATCH "):
    payload = json.loads(raw_line.removeprefix("SR2FPGA_MISMATCH "))
    mismatches.append(
        {
            key: payload[key]
            for key in ("scenario_id", "class", "item_index", "expected", "actual")
            if key in payload
        }
    )
    continue
```

Malformed `SR2FPGA_MISMATCH` lines must not crash log parsing; they are ignored and the following `TEST_FAIL` still determines failure.

- [ ] **Step 5: Extend trusted artifact matching**

Add normalized path checks for `oracle/`, any `*/eval/oracle/` segment, and `LLM/src/sr2fpga_agent/oracles/`. Confirm that RTL-only patches remain allowed and oracle/runtime files set `touched_trusted_artifacts=True`.

- [ ] **Step 6: Run targeted tests**

```powershell
python -m pytest LLM/tests/test_sr2fpga_agent_oracle_runner.py LLM/tests/test_sr2fpga_agent_structured_signals.py LLM/tests/test_sr2fpga_agent_patch_as_pr.py -q
```

Expected: all targeted tests pass.

- [ ] **Step 7: Commit Task 2 only**

```powershell
git add -- LLM/src/sr2fpga_agent/oracle_runner.py LLM/src/sr2fpga_agent/oracles/types.py LLM/src/sr2fpga_agent/log_parser.py LLM/src/sr2fpga_agent/path_safety.py LLM/tests/test_sr2fpga_agent_oracle_runner.py LLM/tests/test_sr2fpga_agent_structured_signals.py LLM/tests/test_sr2fpga_agent_patch_as_pr.py
git commit -m "feat: run independent oracle scenarios"
```

---

### Task 3: C0 Agent, Runner, Recorder, and Export Integration

**Files:**
- Modify: `LLM/src/sr2fpga_agent/agent.py`
- Modify: `LLM/src/sr2fpga_agent/runner.py`
- Modify: `LLM/src/sr2fpga_agent/recorder.py`
- Test: `LLM/tests/test_sr2fpga_agent_tooling.py`
- Test: `LLM/tests/test_sr2fpga_agent_runner.py`
- Test: `LLM/tests/test_sr2fpga_agent_recorder.py`

**Interfaces:**
- Consumes: bundle registry, `run_oracle_scenarios()`, sanitized oracle profile.
- Produces: `run_independent_oracle` config, per-attempt bundle path, labels/checks, `trajectory.oracle_profile`, and summary counts.

- [ ] **Step 1: Write failing config and orchestration tests**

```python
def test_runner_config_defaults_independent_oracle_off(tmp_path):
    config = load_runner_config(write_config(tmp_path, {}))
    assert config.run_independent_oracle is False

def test_line_a_oracle_mode_writes_bundle_outside_generated_project(tmp_path):
    agent = agent_with_fake_tools(tmp_path, enable_independent_oracle=True)
    result = agent.run_one(
        sample_id="sample_fir",
        requirement="Implement the declared FIR stream contract.",
        request=ProjectRequest(task_type="fir_filter", width=8, project_name="fir"),
        platform=PlatformProfile(name="generic", vendor="generic", toolchain="open_source"),
        metadata={"family_id": "fir_filter", "evaluation_line": "line_a"},
    )
    sample = Path(result["sample_dir"])
    assert (sample / "attempts/attempt_000/eval/oracle/manifest.json").is_file()
    assert not (sample / "final/generated_project/oracle").exists()
```

Add tests for disabled legacy behavior, unsupported families returning `not_run`, oracle-build failure producing non-model no-credit, all-four-class pass, hidden/stress failure, mutation reuse of the final attempt bundle, and JSONL export absence of hidden `.memh` content and actual seeds.

- [ ] **Step 2: Run targeted tests and verify failure**

```powershell
python -m pytest LLM/tests/test_sr2fpga_agent_tooling.py LLM/tests/test_sr2fpga_agent_runner.py LLM/tests/test_sr2fpga_agent_recorder.py -q
```

Expected: assertions for `run_independent_oracle` and `oracle_profile` fail.

- [ ] **Step 3: Add explicit configuration and registry lookup**

Add `run_independent_oracle: bool = False` to `RunnerConfig` and `enable_independent_oracle: bool = False` to `DataGenerationAgent`. Load the YAML field with the existing strict boolean parser and pass it from `run_batch()` to the agent.

```python
def build_oracle_bundle_for_request(
    family_id: str,
    request: ProjectRequest,
    output_root: Path,
) -> OracleBundle | None:
    builder = REFERENCE_BUILDERS.get(family_id)
    return None if builder is None else builder(request.width, output_root)
```

- [ ] **Step 4: Build one bundle per attempt and reuse it for mutations**

In `run_one()`, derive `attempt_root = project_dir.parent`, write the bundle to `attempt_root / "eval/oracle"`, and pass the loaded bundle into `_run_pipeline()`. Keep `final_oracle_bundle` and `final_oracle_evidence` alongside `final_tool_results`. `_oracle_strength()` receives the final bundle and passes it to every mutated-project `_run_pipeline()` call; it must not regenerate hidden scenarios per mutant.

```python
tool_results = self._run_pipeline(
    project,
    project_dir,
    platform,
    oracle_bundle=attempt_oracle_bundle,
)
```

Compile once. When a bundle exists, replace the legacy single `vvp sim.out` call with `run_oracle_scenarios()`. When no bundle exists, retain the current single-run path unchanged.

- [ ] **Step 5: Add labels and no-credit rules**

Pass sanitized evidence into `_labels()` and populate:

```python
checks.update(
    {
        "l2_hidden_pass": evidence.class_status("hidden_deterministic") == "pass",
        "l2_stress_pass": evidence.class_status("stress") == "pass",
        "l2_randomized_pass": evidence.class_status("randomized_fixed_seed") == "pass",
        "l2_coverage_profile": "independent_python_reference",
        "l2_scenario_counts": evidence.scenario_counts(),
    }
)
```

If independent-oracle mode is enabled for a supported target family and bundle generation/validation fails, set `automatic_pass_credit=False`, use `pass_level="ORACLE_ERROR"`, and set a non-model `failure_origin`. Do not convert this to `L2` failure.

- [ ] **Step 6: Persist sanitized evidence and summary metrics**

The trajectory contains:

```json
{
  "oracle_profile": {
    "kind": "python_reference",
    "reference_model": "numeric.fir_filter",
    "reference_version": "1",
    "bundle_sha256": "...",
    "scenario_counts": {
      "public_smoke": 1,
      "hidden_deterministic": 1,
      "randomized_fixed_seed": 1,
      "stress": 1
    },
    "class_status": {
      "public_smoke": "pass",
      "hidden_deterministic": "pass",
      "randomized_fixed_seed": "pass",
      "stress": "pass"
    },
    "hidden_vectors_exported": false
  }
}
```

`DatasetRecorder.export_training_views()` must strip any raw evaluator path and seed even if a malformed caller inserts them. Runner summary adds `independent_oracle.pass/fail/not_run/infrastructure_error` and per-domain/per-family counts.

- [ ] **Step 7: Run integration tests**

```powershell
python -m pytest LLM/tests/test_sr2fpga_agent_tooling.py LLM/tests/test_sr2fpga_agent_runner.py LLM/tests/test_sr2fpga_agent_recorder.py -q
```

Expected: all targeted tests pass and legacy tests remain unchanged.

- [ ] **Step 8: Commit Task 3 only**

```powershell
git add -- LLM/src/sr2fpga_agent/agent.py LLM/src/sr2fpga_agent/runner.py LLM/src/sr2fpga_agent/recorder.py LLM/tests/test_sr2fpga_agent_tooling.py LLM/tests/test_sr2fpga_agent_runner.py LLM/tests/test_sr2fpga_agent_recorder.py
git commit -m "feat: integrate independent oracle evidence"
```

---

### Task 4: C1 Numeric References and Testbench Adapters

**Files:**
- Create: `LLM/src/sr2fpga_agent/oracles/numeric.py`
- Modify: `LLM/src/sr2fpga_agent/oracles/__init__.py`
- Modify: `LLM/src/sr2fpga_agent/task_families/datapath.py`
- Test: `LLM/tests/test_sr2fpga_agent_oracle_numeric.py`
- Test: `LLM/tests/test_sr2fpga_agent_project_generator.py`
- Test: `LLM/tests/test_sr2fpga_agent_failure_injector.py`

**Interfaces:**
- Produces: `build_fir_filter_bundle(width, root)` and `build_matrix_vector_mac_bundle(width, root)`.
- Semantics: FIR coefficients `(3, -2, 1)` with zero reset history; matrix coefficients `(2, -1, 3, 1)` with four accepted samples per result.

- [ ] **Step 1: Write hand-calculated reference tests**

```python
def test_fir_reference_matches_declared_coefficients():
    assert fir_outputs([5, -4, 7], width=8) == [15, -22, 34]
    assert fir_outputs([127], width=8) == [381]

def test_matrix_vector_reference_uses_fixed_rom_order():
    assert matrix_vector_outputs([1, 2, 3, 4], width=8) == [13]
    assert matrix_vector_outputs([127, -128, 127, 127], width=8) == [890]
```

Add signed minimum/maximum, reset-before-record, stalled output, deterministic regeneration, all-four-class presence, and exact field-layout tests.

- [ ] **Step 2: Run numeric tests and verify failure**

```powershell
python -m pytest LLM/tests/test_sr2fpga_agent_oracle_numeric.py -q
```

Expected: numeric reference functions are missing.

- [ ] **Step 3: Implement independent arithmetic**

Use explicit two's-complement normalization rather than importing generated RTL helpers:

```python
def signed(value: int, width: int) -> int:
    masked = value & ((1 << width) - 1)
    return masked - (1 << width) if masked & (1 << (width - 1)) else masked

def fir_outputs(samples: Sequence[int], width: int) -> list[int]:
    d0 = d1 = 0
    outputs = []
    for sample in samples:
        current = signed(sample, width)
        outputs.append(3 * current - 2 * d0 + d1)
        d1, d0 = d0, current
    return outputs

def matrix_vector_outputs(samples: Sequence[int], width: int) -> list[int]:
    if len(samples) % 4:
        raise ValueError("matrix-vector scenarios require groups of four samples")
    coefficients = (2, -1, 3, 1)
    return [
        sum(signed(value, width) * coefficient for value, coefficient in zip(samples[i:i+4], coefficients))
        for i in range(0, len(samples), 4)
    ]
```

Scenario builders use high-entropy 128-bit seeds for withheld classes and encode reset/stall controls in declared input fields. Expected records contain `expect_output` plus signed result bits.

- [ ] **Step 4: Add oracle-mode branches to both testbenches**

Each testbench first checks `ORACLE_INPUT`. If absent, run the existing embedded smoke block unchanged. If present, load both files, decode the family-specific fixed layout, reset the DUT, drive each record, apply declared stalls, compare only records with `expect_output=1`, and emit:

```systemverilog
$display("SR2FPGA_MISMATCH {\"scenario_id\":\"%0s\",\"class\":\"%0s\",\"item_index\":%0d,\"expected\":\"0x%0h\",\"actual\":\"0x%0h\"}",
         oracle_scenario_id, oracle_scenario_class, item_index, expected_result, result);
$display("TEST_FAIL functional mismatch");
$finish;
```

Keep valid-ready payload stability checks active in both legacy and oracle modes.

- [ ] **Step 5: Run numeric and existing generator/mutation tests**

```powershell
python -m pytest LLM/tests/test_sr2fpga_agent_oracle_numeric.py LLM/tests/test_sr2fpga_agent_project_generator.py LLM/tests/test_sr2fpga_agent_failure_injector.py -q
```

Expected: all pass.

- [ ] **Step 6: Run a deterministic C1 smoke through L3**

Use a temporary config containing only `fir_filter` and `matrix_vector_mac`, `evaluation_line: line_a`, `run_independent_oracle: true`, and L4 disabled. Verify both trajectories show four scenario classes, `kind=python_reference`, L3 pass, and mutation score `1.0`.

- [ ] **Step 7: Commit Task 4 only**

```powershell
git add -- LLM/src/sr2fpga_agent/oracles/numeric.py LLM/src/sr2fpga_agent/oracles/__init__.py LLM/src/sr2fpga_agent/task_families/datapath.py LLM/tests/test_sr2fpga_agent_oracle_numeric.py LLM/tests/test_sr2fpga_agent_project_generator.py LLM/tests/test_sr2fpga_agent_failure_injector.py
git commit -m "feat: add numeric independent references"
```

---

### Task 5: C2 Signal References and Testbench Adapters

**Files:**
- Create: `LLM/src/sr2fpga_agent/oracles/signal.py`
- Modify: `LLM/src/sr2fpga_agent/oracles/__init__.py`
- Modify: `LLM/src/sr2fpga_agent/task_families/datapath.py`
- Test: `LLM/tests/test_sr2fpga_agent_oracle_signal.py`
- Test: `LLM/tests/test_sr2fpga_agent_project_generator.py`
- Test: `LLM/tests/test_sr2fpga_agent_failure_injector.py`

**Interfaces:**
- Produces: `build_matched_filter_bundle()`, `build_peak_detector_bundle()`, and `build_pulse_radar_bundle()`.
- Semantics: matched template `(-1, 2, -3, 4)`, threshold `10`, first-index tie breaking, and empty result `(found=0, value=0, index=0)`.

- [ ] **Step 1: Write hand-calculated signal tests**

```python
def test_matched_filter_known_reversed_pulse():
    assert matched_filter_outputs([4, -3, 2, -1], width=8)[-1] == 30

def test_peak_detector_threshold_and_first_tie():
    assert detect_peak([11, 16, 16, 14], threshold=10) == (1, 16, 1)
    assert detect_peak([-3, 0, 9], threshold=10) == (0, 0, 0)

def test_pulse_radar_runs_correlation_then_frame_peak():
    assert pulse_radar([4, -3, 2, -1], width=8, threshold=10) == (1, 30, 3)
```

Add final-sample participation, reset-clears-history, negative-correlation, exact-threshold, repeated equal peak, backpressure, and deterministic hash tests.

- [ ] **Step 2: Run signal tests and verify failure**

```powershell
python -m pytest LLM/tests/test_sr2fpga_agent_oracle_signal.py -q
```

Expected: signal reference functions are missing.

- [ ] **Step 3: Implement signal references without RTL imports**

```python
MATCHED_TEMPLATE = (-1, 2, -3, 4)

def matched_filter_outputs(samples: Sequence[int], width: int) -> list[int]:
    history = [0, 0, 0, 0]
    outputs = []
    for sample in samples:
        history = [signed(sample, width), *history[:3]]
        outputs.append(sum(value * coefficient for value, coefficient in zip(history, MATCHED_TEMPLATE)))
    return outputs

def detect_peak(values: Sequence[int], threshold: int) -> tuple[int, int, int]:
    best_value = 0
    best_index = 0
    found = 0
    for index, value in enumerate(values):
        if value >= threshold and (not found or value > best_value):
            found, best_value, best_index = 1, value, index
    return found, best_value if found else 0, best_index if found else 0
```

The pulse-radar model applies the matched filter to every accepted sample and then runs `detect_peak()` over the frame correlations.

- [ ] **Step 4: Add oracle-mode branches to three signal testbenches**

Use fixed layouts:

- matched input: `sample`, `reset_before`, `stall_cycles`; expected: `correlation`.
- peak input: `sample`, `in_last`, `reset_before`, `stall_cycles`; expected: `expect_output`, `found`, `value`, `index`.
- radar input: same controls as peak; expected value/index use `acc_width=2*width+2`.

Retain the current embedded tests as the no-plusarg fallback and retain all output-stability assertions.

- [ ] **Step 5: Run C2 tests**

```powershell
python -m pytest LLM/tests/test_sr2fpga_agent_oracle_signal.py LLM/tests/test_sr2fpga_agent_project_generator.py LLM/tests/test_sr2fpga_agent_failure_injector.py -q
```

Expected: all pass.

- [ ] **Step 6: Run a three-family C2 Line-A smoke through L3**

Verify `matched_filter`, `peak_detector`, and `p_pulse_radar_signal` each pass all four scenario classes and kill all catalog mutations. Any surviving or non-scoreable critical mutation blocks C2 completion.

- [ ] **Step 7: Commit Task 5 only**

```powershell
git add -- LLM/src/sr2fpga_agent/oracles/signal.py LLM/src/sr2fpga_agent/oracles/__init__.py LLM/src/sr2fpga_agent/task_families/datapath.py LLM/tests/test_sr2fpga_agent_oracle_signal.py LLM/tests/test_sr2fpga_agent_project_generator.py LLM/tests/test_sr2fpga_agent_failure_injector.py
git commit -m "feat: add signal independent references"
```

---

### Task 6: C3 Image References and Testbench Adapters

**Files:**
- Create: `LLM/src/sr2fpga_agent/oracles/image.py`
- Modify: `LLM/src/sr2fpga_agent/oracles/__init__.py`
- Modify: `LLM/src/sr2fpga_agent/task_families/image.py`
- Test: `LLM/tests/test_sr2fpga_agent_oracle_image.py`
- Test: `LLM/tests/test_sr2fpga_agent_project_generator.py`
- Test: `LLM/tests/test_sr2fpga_agent_failure_injector.py`

**Interfaces:**
- Produces: `sobel_frame()`, `vision_defect_frame()`, and two bundle builders.
- Semantics: 5x5 row-major frames, one-pixel zero border, `abs(Gx)+abs(Gy)`, threshold `>=`, axis tie `abs(Gx) >= abs(Gy)`, and first row-major defect coordinate.

- [ ] **Step 1: Write image reference tests**

```python
def test_flat_frame_has_no_edges_and_axis_tie_is_one_inside():
    result = sobel_frame([[0] * 5 for _ in range(5)], threshold=255)
    assert sum(result.edges) == 0
    assert result.axes[6:9] == (1, 1, 1)

def test_vision_defect_uses_first_row_major_thresholded_coordinate():
    frame = vertical_step_frame(level=255)
    result = vision_defect_frame(frame, threshold=255)
    assert result.defect_present is True
    assert (result.first_x, result.first_y) == (1, 1)
```

Add horizontal edge, vertical edge, exact threshold, border output, output ordering, all-zero frame, maximum pixel values, and deterministic bundle tests.

- [ ] **Step 2: Run image tests and verify failure**

```powershell
python -m pytest LLM/tests/test_sr2fpga_agent_oracle_image.py -q
```

Expected: image reference functions are missing.

- [ ] **Step 3: Implement explicit 3x3 Sobel arithmetic**

```python
GX = ((-1, 0, 1), (-2, 0, 2), (-1, 0, 1))
GY = ((-1, -2, -1), (0, 0, 0), (1, 2, 1))

def sobel_frame(frame: Sequence[Sequence[int]], threshold: int) -> SobelResult:
    _validate_5x5_u8(frame)
    edges = [0] * 25
    axes = [0] * 25
    for y in range(1, 4):
        for x in range(1, 4):
            gx = sum(frame[y+dy-1][x+dx-1] * GX[dy][dx] for dy in range(3) for dx in range(3))
            gy = sum(frame[y+dy-1][x+dx-1] * GY[dy][dx] for dy in range(3) for dx in range(3))
            index = y * 5 + x
            edges[index] = int(abs(gx) + abs(gy) >= threshold)
            axes[index] = int(abs(gx) >= abs(gy))
    return SobelResult(tuple(edges), tuple(axes))
```

`vision_defect_frame()` uses the edge tuple, reports whether any edge exists, and returns the first row-major edge coordinate. It does not implement connected components or bounding boxes.

- [ ] **Step 4: Add oracle-mode branches to both image testbenches**

Input records contain `pixel`, `in_last`, `reset_before`, and output-stall control. Expected Sobel records contain `edge`, `axis`, and `out_last`; vision records additionally carry final-frame `defect_present`, `first_x`, and `first_y`. Keep the 25-output bound and output-stability assertions.

- [ ] **Step 5: Run C3 tests**

```powershell
python -m pytest LLM/tests/test_sr2fpga_agent_oracle_image.py LLM/tests/test_sr2fpga_agent_project_generator.py LLM/tests/test_sr2fpga_agent_failure_injector.py -q
```

Expected: all pass.

- [ ] **Step 6: Run a two-family C3 Line-A smoke through L3**

Verify both image families have four scenario classes, no hidden vector payload in trajectory/exports, all critical mutations killed, and L3 pass.

- [ ] **Step 7: Commit Task 6 only**

```powershell
git add -- LLM/src/sr2fpga_agent/oracles/image.py LLM/src/sr2fpga_agent/oracles/__init__.py LLM/src/sr2fpga_agent/task_families/image.py LLM/tests/test_sr2fpga_agent_oracle_image.py LLM/tests/test_sr2fpga_agent_project_generator.py LLM/tests/test_sr2fpga_agent_failure_injector.py
git commit -m "feat: add image independent references"
```

---

### Task 7: C4 RL References and Testbench Adapters

**Files:**
- Create: `LLM/src/sr2fpga_agent/oracles/rl.py`
- Modify: `LLM/src/sr2fpga_agent/oracles/__init__.py`
- Modify: `LLM/src/sr2fpga_agent/task_families/rl.py`
- Test: `LLM/tests/test_sr2fpga_agent_oracle_rl.py`
- Test: `LLM/tests/test_sr2fpga_agent_project_generator.py`
- Test: `LLM/tests/test_sr2fpga_agent_failure_injector.py`

**Interfaces:**
- Produces: `td_update()`, `rl_accelerator_step()`, and two bundle builders.
- Semantics: Q4-style scale `16`, signed TD arithmetic, truncation toward arithmetic right shift, width saturation, first-index argmax tie, declared config register map, done/IRQ behavior.

- [ ] **Step 1: Write RL reference tests**

```python
def test_td_update_matches_declared_fixed_point_examples():
    assert td_update(reward=4, value=10, next_value=20, gamma=8, alpha=4, width=8) == (4, 11)
    assert td_update(reward=2, value=6, next_value=16, gamma=8, alpha=8, width=8) == (4, 8)

def test_argmax_tie_chooses_first_action():
    assert argmax_first((9, 9)) == 0

def test_rl_shell_examples():
    config = RLConfig(weight0=2, bias0=1, weight1=3, bias1=0, alpha=4, enable=True)
    assert rl_accelerator_step(config, obs0=4, obs1=2, reward=1, next_value=8, done=False) == (0, 7, 7, False, False)
```

Add negative TD error, saturation, exact tie, reset, done/IRQ, register-address, output stall, and deterministic bundle tests.

- [ ] **Step 2: Run RL tests and verify failure**

```powershell
python -m pytest LLM/tests/test_sr2fpga_agent_oracle_rl.py -q
```

Expected: RL reference functions are missing.

- [ ] **Step 3: Implement fixed-point functions explicitly**

```python
FIXED_SHIFT = 4

def saturate_signed(value: int, width: int) -> int:
    low, high = -(1 << (width - 1)), (1 << (width - 1)) - 1
    return min(max(value, low), high)

def td_update(reward: int, value: int, next_value: int, gamma: int, alpha: int, width: int) -> tuple[int, int]:
    target = reward + ((next_value * gamma) >> FIXED_SHIFT)
    error = saturate_signed(target - value, width)
    updated = saturate_signed(value + ((error * alpha) >> FIXED_SHIFT), width)
    return error, updated
```

Implement the shell from its declared register and arithmetic contract, not by importing `task_families.rl`. Encode input operation kind (`reset`, `cfg_write`, `sample`), register address/data, sample payload, done flag, and stall controls in the input records. Expected records use `expect_output`, selected action, value estimate, updated value, episode done, and IRQ.

The independent shell contract is explicit:

```python
def rl_accelerator_step(config: RLConfig, obs0: int, obs1: int, reward: int, next_value: int, done: bool) -> tuple[int, int, int, bool, bool]:
    score0 = min(obs0 * config.weight0 + config.bias0, 0xFF)
    score1 = min(obs1 * config.weight1 + config.bias1, 0xFF)
    selected_action = int(score1 > score0)
    value_estimate = (score0 + score1) >> 1
    td_error = max(reward + next_value - value_estimate, 0)
    update_delta = min((config.alpha * td_error) >> FIXED_SHIFT, 0xFF)
    updated_value = (value_estimate + update_delta) & 0xFF
    episode_done = bool(done)
    irq = episode_done
    return selected_action, value_estimate, updated_value, episode_done, irq
```

For widths other than 8, replace `0xFF` with `(1 << width) - 1`. Register addresses are fixed: `0=weight0`, `1=bias0`, `2=weight1`, `3=bias1`, `4=alpha`, `5=enable`. Equal scores select action 0.

- [ ] **Step 4: Add oracle-mode branches to both RL testbenches**

The TD core adapter drives one update per input record. The accelerator adapter interprets operation records, performs configuration writes before samples, and compares only sample records marked `expect_output`. Preserve existing valid-ready and done/IRQ assertions.

- [ ] **Step 5: Run C4 tests**

```powershell
python -m pytest LLM/tests/test_sr2fpga_agent_oracle_rl.py LLM/tests/test_sr2fpga_agent_project_generator.py LLM/tests/test_sr2fpga_agent_failure_injector.py -q
```

Expected: all pass.

- [ ] **Step 6: Run a two-family C4 Line-A smoke through L3**

Verify both RL families pass all four scenario classes and meet the catalog `0.90` mutation threshold with no survivor/non-scoreable critical mutations.

- [ ] **Step 7: Commit Task 7 only**

```powershell
git add -- LLM/src/sr2fpga_agent/oracles/rl.py LLM/src/sr2fpga_agent/oracles/__init__.py LLM/src/sr2fpga_agent/task_families/rl.py LLM/tests/test_sr2fpga_agent_oracle_rl.py LLM/tests/test_sr2fpga_agent_project_generator.py LLM/tests/test_sr2fpga_agent_failure_injector.py
git commit -m "feat: add rl independent references"
```

---

### Task 8: C5 Qualification Config, Evidence Ledger, Renderer, and Audit

**Files:**
- Create: `configs/current/sr2fpga_phase_c_independent_oracle.example.yaml`
- Create: `docs/sr2fpga-phase-c-independent-oracle-evidence-2026-07-14.md`
- Modify: `LLM/src/sr2fpga_agent/task_evidence.py`
- Modify: `docs/sr2fpga-task-evidence-v0.1.json`
- Modify: `docs/sr2fpga-task-evidence-status.md`
- Modify: `docs/current-status.md`
- Test: `LLM/tests/test_sr2fpga_task_evidence_v01.py`
- Test: `LLM/tests/test_sr2fpga_agent_baseline_report.py`
- Test: `LLM/tests/test_sr2fpga_agent_runner.py`

**Interfaces:**
- Consumes: nine qualified trajectories and their attempt-local bundle manifests/results.
- Produces: artifact-backed `python_reference` evidence, independent-oracle summary/report sections, and zero-issue local audit.

- [ ] **Step 1: Write failing evidence-schema and audit tests**

Extend `TaskFamilyEvidence` with an optional immutable `IndependentOracleEvidence`:

```python
@dataclass(frozen=True)
class IndependentOracleEvidence:
    status: str
    run_id: str
    bundle_sha256: str
    scenario_classes: tuple[str, ...]
    hidden_vectors_exported: bool
```

Tests require `status in {"not_run", "qualified", "unqualified"}`; qualified entries require all four scenario classes, a non-empty run and bundle hash, `golden_model_status="python_reference"`, and `hidden_vectors_exported=False`. The audit must open the declared trajectory and bundle manifest/results, recompute hashes, verify family/sample/run identity, and reject leaked hidden vectors or missing scenario classes.

- [ ] **Step 2: Run evidence tests and verify failure**

```powershell
python -m pytest LLM/tests/test_sr2fpga_task_evidence_v01.py LLM/tests/test_sr2fpga_agent_runner.py LLM/tests/test_sr2fpga_agent_baseline_report.py -q
```

Expected: independent-oracle fields and report sections are missing.

- [ ] **Step 3: Implement backward-compatible ledger parsing**

Keep `schema_version="sr2fpga-task-evidence-v0.1"` and the existing file path to avoid a broad migration. Missing `independent_oracle_evidence` defaults to:

```json
{
  "status": "not_run",
  "run_id": "",
  "bundle_sha256": "",
  "scenario_classes": [],
  "hidden_vectors_exported": false
}
```

Add a renderer summary row `Independent Python oracle qualified` and a verification-matrix column `Independent oracle`.

- [ ] **Step 4: Create the nine-family qualification config**

The YAML uses deterministic source, `evaluation_line: line_a`, one width-8 sample per target family, `run_independent_oracle: true`, `run_l4_open: false`, `run_l4_commercial: false`, and `max_attempts: 1`. It must list the nine task aliases explicitly and let `planned_samples()` derive T3/T4 from the catalog.

- [ ] **Step 5: Run the complete Phase C batch**

```powershell
python -m LLM.src.sr2fpga_agent.runner --config configs/current/sr2fpga_phase_c_independent_oracle.example.yaml --run-id phase-c-independent-oracle-20260714-v1 --preflight
python -m LLM.src.sr2fpga_agent.runner --config configs/current/sr2fpga_phase_c_independent_oracle.example.yaml --run-id phase-c-independent-oracle-20260714-v1
```

Expected summary:

```text
samples=9
success_l3=9
rejected=0
independent_oracle_qualified=9
oracle_infrastructure_error=0
critical_mutation_survivors=0
critical_mutation_non_scoreable=0
```

- [ ] **Step 6: Inspect concrete artifacts before promoting evidence**

For at least one family per domain, inspect:

```text
metadata.json
attempts/attempt_000/eval/oracle/manifest.json
attempts/attempt_000/eval/oracle/results.json
eval/labels.json
eval/trajectory.json
oracle_mutations/*/eval/sim_run.json
```

Recompute bundle/file hashes and verify exported JSONL files contain neither hidden memh content nor actual hidden seeds.

- [ ] **Step 7: Promote all nine ledger entries and regenerate reports**

For each target family set `golden_model_status="python_reference"`, retain its proven highest L-level and mutation evidence, set qualified independent-oracle evidence, set `last_verified_run` to the Phase C run, and add concrete trajectory/bundle/mutation artifact references. Do not change non-target families.

Run:

```powershell
python -m LLM.src.sr2fpga_agent.task_evidence --output docs/sr2fpga-task-evidence-status.md --audit-run-root tmp
```

Expected: exit code 0 and no audit issues.

- [ ] **Step 8: Write the Phase C evidence report and current-status update**

The report must include the run ID, config, 9/9 family table, four-domain table, per-class scenario counts, bundle hashes, mutation scores, L0-L3 status, leakage audit result, artifact paths, commands, tool versions, and remaining limitations. Update `docs/current-status.md` only after every completion gate is proven.

- [ ] **Step 9: Run C5 tests**

```powershell
python -m pytest LLM/tests/test_sr2fpga_task_evidence_v01.py LLM/tests/test_sr2fpga_agent_runner.py LLM/tests/test_sr2fpga_agent_baseline_report.py -q
```

Expected: all pass.

- [ ] **Step 10: Commit Task 8 only**

```powershell
git add -- configs/current/sr2fpga_phase_c_independent_oracle.example.yaml LLM/src/sr2fpga_agent/task_evidence.py LLM/tests/test_sr2fpga_task_evidence_v01.py LLM/tests/test_sr2fpga_agent_runner.py LLM/tests/test_sr2fpga_agent_baseline_report.py docs/sr2fpga-task-evidence-v0.1.json docs/sr2fpga-task-evidence-status.md docs/sr2fpga-phase-c-independent-oracle-evidence-2026-07-14.md docs/current-status.md
git commit -m "docs: publish phase c independent oracle evidence"
```

---

### Task 9: Full Regression and Completion Audit

**Files:**
- Modify only files required by failures caused by Tasks 1-8.
- Verify: all `LLM/tests` and Phase C run artifacts.

**Interfaces:**
- Consumes: the complete Phase C implementation and evidence.
- Produces: requirement-by-requirement completion proof.

- [ ] **Step 1: Run formatting and whitespace checks**

```powershell
git diff --check
```

Expected: no whitespace errors in Phase C changes.

- [ ] **Step 2: Run all tests**

```powershell
python -m pytest LLM/tests
```

Expected: zero failed tests. Record the exact passed/subtest counts in the evidence report.

- [ ] **Step 3: Re-run the evidence audit**

```powershell
python -m LLM.src.sr2fpga_agent.task_evidence --output docs/sr2fpga-task-evidence-status.md --audit-run-root tmp
```

Expected: exit code 0 and no stderr issues.

- [ ] **Step 4: Audit all explicit Phase C gates**

Verify from current files and artifacts:

```text
Independent golden domains: 4/4
Target families with python_reference evidence: 9/9
Paper-1 core mutation-qualified: 14/14 or stronger
Hidden scenario classes present: 9/9
Critical mutation survivors/non-scoreable: 0
Evidence audit issues: 0
Hidden vector/seed leakage findings: 0
```

Do not mark Phase C complete if any value is inferred only from tests without corresponding trajectory/bundle evidence.

- [ ] **Step 5: Review the final diff for scope**

Confirm every changed line traces to bundle infrastructure, one of the nine domain adapters/models, qualification evidence, or a regression caused by those changes. Leave unrelated dirty-worktree files untouched.

- [ ] **Step 6: Commit any verified audit-only corrections**

```powershell
git add -- docs/sr2fpga-phase-c-independent-oracle-evidence-2026-07-14.md docs/sr2fpga-task-evidence-status.md docs/current-status.md
git commit -m "test: close phase c verification gaps"
```

Skip this commit when no audit correction was needed.

---

## Completion Evidence Map

| Spec requirement | Implementing task | Authoritative evidence |
| --- | --- | --- |
| Fixed-width bundle and manifest contract | Task 1 | bundle unit tests plus real `manifest.json` |
| Safe relative paths and hashes | Tasks 1-2 | rejection tests plus recomputed C5 hashes |
| One simulation per scenario | Task 2 | fake-runner call count plus `results.json` |
| All-scenarios L2 aggregation | Tasks 2-3 | aggregate tests plus nine labels/trajectories |
| Hidden vectors excluded from prompts/exports | Tasks 1, 3, 8 | sanitization tests plus export-content audit |
| Structured mismatch | Task 2 and domain adapters | parser tests plus controlled bad-DUT trajectories |
| Trusted oracle edit surface | Task 2 | patch-as-PR tests |
| Numeric domain | Task 4 | hand-calculated tests plus C1/C5 artifacts |
| Signal domain | Task 5 | hand-calculated tests plus C2/C5 artifacts |
| Image domain | Task 6 | hand-calculated tests plus C3/C5 artifacts |
| RL domain | Task 7 | hand-calculated tests plus C4/C5 artifacts |
| Nine-family evidence promotion | Task 8 | ledger, report, run summary, trajectory refs |
| Phase B mutation gate retained | Tasks 4-9 | full tests and evidence audit |
| No L4/L5 regression | Tasks 3 and 9 | existing L4 tests and full suite |
