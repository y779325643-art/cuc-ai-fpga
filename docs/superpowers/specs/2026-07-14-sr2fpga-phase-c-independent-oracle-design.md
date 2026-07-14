# SR2FPGA Phase C Independent Oracle Design

**Date:** 2026-07-14

**Status:** approved architecture; implementation not started
**Scope:** independent Python golden models, scenario isolation, oracle bundles,
structured mismatch evidence, and evidence promotion for the four Paper-1
domains

## 1. Purpose

Phase B established executable L3 evidence for all 14 Paper-1 core families and
mutation-qualified the current embedded SystemVerilog testbenches. Phase C
removes the remaining same-implementation-language oracle risk.

The selected design is:

```text
trusted Python reference
-> deterministic scenario manifest
-> runtime oracle bundle
-> black-box SystemVerilog driver/checker
-> structured mismatch result
-> artifact-backed evidence promotion
```

The Python model and scenario generator are trusted infrastructure. They are not
generated, repaired, or edited by the model under evaluation.

## 2. Goals

Phase C must provide:

1. independent Python references for numeric, signal, image, and RL domains;
2. explicit `public_smoke`, `hidden_deterministic`,
   `randomized_fixed_seed`, and `stress` scenario classes;
3. deterministic input and expected-output artifacts with recorded seeds and
   hashes;
4. black-box simulation that consumes runtime oracle artifacts without exposing
   hidden concrete vectors to model prompts or training exports;
5. structured expected/actual/index/scenario mismatch evidence;
6. mutation qualification against the independent oracle;
7. evidence promotion from `embedded_sv` to `python_reference` only after a
   successful artifact-backed Line-A run.

## 3. Non-Goals

Phase C does not:

- add new task families;
- implement OpenXC7, Vivado, or L5 board work;
- replace Icarus/Verilator with Cocotb;
- make UVM the default oracle;
- expose hidden vectors to repair prompts;
- treat Python-reference availability as proof of L4/L5 correctness;
- rewrite the existing runner or testbench framework wholesale.

## 4. Selected Architecture

### 4.1 Canonical trusted references

Canonical reference code lives in:

```text
LLM/src/sr2fpga_agent/oracles/
  __init__.py
  types.py
  bundle.py
  numeric.py
  signal.py
  image.py
  rl.py
```

Responsibilities are separated as follows:

- `types.py`: immutable scenario, transaction, expected-output, and mismatch
  records;
- `bundle.py`: deterministic materialization, hashing, manifest validation, and
  safe path handling;
- domain modules: pure reference functions and domain scenario generation.

Domain functions accept explicit parameters and plain Python values. They do not
import generated RTL, parse DUT implementation text, or call the RTL generator.

### 4.2 Runtime oracle bundle

Before L2, the runner materializes a trusted bundle under the attempt evaluation
directory:

```text
attempts/attempt_xxxx/eval/oracle/
  manifest.json
  public/
    <scenario_id>/input.memh
    <scenario_id>/expected.memh
  hidden/
    <scenario_id>/input.memh
    <scenario_id>/expected.memh
  randomized/
    <scenario_id>/input.memh
    <scenario_id>/expected.memh
  stress/
    <scenario_id>/input.memh
    <scenario_id>/expected.memh
```

This directory is evaluation infrastructure, not a model-generated project
artifact. The bundle is excluded from REQ2FILE, HIS2PROJECT, repair context, and
training-view exports.

### 4.3 Manifest contract

`manifest.json` has this minimum shape:

```json
{
  "schema_version": "sr2fpga-oracle-bundle-v1",
  "family_id": "fir_filter",
  "reference_model": "numeric.fir_filter",
  "reference_version": "1",
  "task_parameters": {},
  "scenarios": [
    {
      "scenario_id": "hidden_boundary_001",
      "scenario_class": "hidden_deterministic",
      "seed": 101,
      "input_path": "hidden/hidden_boundary_001/input.memh",
      "expected_path": "hidden/hidden_boundary_001/expected.memh",
      "transaction_count": 32,
      "input_record_width_bits": 16,
      "expected_record_width_bits": 32,
      "input_fields": [
        {"name": "sample", "msb": 15, "lsb": 0, "signed": true}
      ],
      "expected_fields": [
        {"name": "result", "msb": 31, "lsb": 0, "signed": true}
      ],
      "input_sha256": "...",
      "expected_sha256": "..."
    }
  ],
  "bundle_sha256": "..."
}
```

All paths are relative, normalized, and constrained to the bundle root. Scenario
IDs are stable and contain no concrete vector values. Memory files use one
fixed-width hexadecimal record per line. Field layouts in the manifest define
packing, signed interpretation, and widths; testbenches may not infer layouts
from DUT source text.

### 4.4 Simulation integration

The existing trusted SystemVerilog testbench remains the driver and protocol
checker. The runner validates `manifest.json`, then starts one isolated
simulation per scenario and passes only that scenario's files and metadata as
explicit plusargs. The testbench does not parse JSON:

```text
vvp sim.out \
  +ORACLE_INPUT=<scenario/input.memh> \
  +ORACLE_EXPECTED=<scenario/expected.memh> \
  +ORACLE_SCENARIO_ID=<stable_id> \
  +ORACLE_SCENARIO_CLASS=<class> \
  +ORACLE_TRANSACTION_COUNT=<count>
```

The testbench uses `$readmemh` for vectors. The runner, not the model, supplies
the arguments. Starting a fresh simulation per scenario also gives every case a
defined reset boundary. Missing bundle files, hash mismatches, malformed
manifests, and unsupported reference models are infrastructure/oracle failures,
not DUT failures.

The testbench must print a machine-readable mismatch line before `TEST_FAIL`:

```text
SR2FPGA_MISMATCH {"scenario_id":"...","class":"hidden_deterministic",
"item_index":17,"expected":"0x...","actual":"0x..."}
```

`semantic_trace.py` or the structured-signal parser converts this into the
trajectory diagnosis. Hidden input values are not copied into prompts or
training rows.

The per-scenario results are aggregated into one L2 verdict. Every required
scenario must pass for L2 to pass. A DUT mismatch or timeout fails L2; an oracle
or tool-environment failure produces a separate non-model verdict and cannot be
silently treated as a skipped scenario.

### 4.5 Public and hidden visibility

Visibility rules are:

| Artifact | Generation/repair model | Simulator | Published dataset |
|---|---:|---:|---:|
| public scenario metadata | yes | yes | yes |
| public concrete vectors | optional | yes | yes |
| hidden scenario ID/class/seed hash | no concrete values | yes | yes |
| hidden concrete inputs/expected outputs | no | yes | no by default |
| randomized/stress scenario metadata and aggregate counts | no concrete values | yes | yes |
| structured mismatch metadata | sanitized | yes | yes |

Hidden vectors may be released only in a versioned benchmark release after the
official evaluation protocol is frozen. They are never included in model prompts
for the run that they judge. The evaluator-local manifest may store the actual
seed required to reproduce a scenario. Training and published trajectory exports
store only a one-way seed hash for hidden or otherwise withheld scenarios; they
must not expose a seed plus parameters that can regenerate withheld vectors.

## 5. Domain References

### 5.1 C1 Numeric

Initial families:

```text
fir_filter
matrix_vector_mac
```

The reference defines signed input interpretation, coefficient order, bit
growth, accumulator width, truncation, output latency, and accepted-token
ordering. Scenarios cover zero, impulse, positive/negative boundaries,
alternating signs, overflow-adjacent values, stalls, and reset.

### 5.2 C2 Signal

Initial families:

```text
matched_filter
peak_detector
p_pulse_radar_signal
```

The reference defines template order, signed correlation, threshold comparison,
first-index tie breaking, no-peak output `(found=0, value=0, index=0)`, frame
boundaries, and final-sample behavior.

### 5.3 C3 Image

Initial families:

```text
sobel_threshold
p_vision_defect_core
```

The reference defines row-major images, zero-valued one-pixel borders, Sobel
`Gx`/`Gy`, `abs(Gx)+abs(Gy)`, threshold comparison, axis tie rule, frame output
order, defect presence, and first thresholded coordinate. It does not implement
or claim connected-component analysis or bounding boxes.

### 5.4 C4 RL

Initial families:

```text
qtable_update_core
p_rl_qlearning_accel
```

The reference defines fixed-point encoding, TD target/update arithmetic,
rounding/truncation, saturation policy, argmax tie breaking, Q-table addressing,
start/done/status behavior, and reset. Full DQN training remains out of scope.

## 6. Scenario Policy

Each family declares at least one scenario in every class:

```text
public_smoke
hidden_deterministic
randomized_fixed_seed
stress
```

Requirements:

- all randomized scenarios use explicit recorded seeds;
- regeneration with the same reference version, parameters, and seed produces
  identical bundle hashes;
- public and hidden scenarios do not reuse identical concrete vectors;
- stress scenarios target protocol and numeric corner cases, not only larger
  random samples;
- hidden scenarios are omitted from generation and repair prompts;
- every scenario has a bounded timeout and expected transaction count.

## 7. Ownership and Edit Safety

The following paths are trusted and non-editable:

```text
LLM/src/sr2fpga_agent/oracles/**
attempts/*/eval/oracle/**
models/golden.py                  # when copied as a release artifact
hidden/**
oracle/**
```

`path_safety.py` must reject model patches touching these paths. A run loses
automatic pass credit if the DUT and the independent oracle are modified by the
same evaluated model.

## 8. Recorder and Evidence Schema

### 8.1 Trajectory

Each episode records:

```json
{
  "oracle_profile": {
    "kind": "python_reference",
    "reference_model": "numeric.fir_filter",
    "reference_version": "1",
    "bundle_sha256": "...",
    "scenario_counts": {
      "public_smoke": 1,
      "hidden_deterministic": 2,
      "randomized_fixed_seed": 3,
      "stress": 2
    },
    "hidden_vectors_exported": false
  }
}
```

Mismatch records include scenario ID/class, item or cycle index, expected,
actual, and failure category. Export sanitization removes hidden vector payloads
and absolute oracle paths.

### 8.2 Evidence ledger

`golden_model_status` may be promoted to `python_reference` only when audit can
verify:

- the referenced run/sample reached the declared L-level;
- the oracle manifest and bundle hash exist;
- all four scenario classes ran;
- hidden vectors were not exported;
- the family met its mutation threshold;
- no critical mutation survived or was non-scoreable;
- the run used the expected reference model and version.

Embedded-SV and Python-reference evidence are reported separately. A Python
reference does not erase earlier embedded-SV provenance.

## 9. Failure Classification

Failures are separated into:

```text
oracle_bundle_generation_failure
oracle_manifest_invalid
oracle_hash_mismatch
oracle_reference_exception
oracle_input_missing
oracle_expected_missing
dut_protocol_failure
dut_functional_mismatch
dut_timeout
toolchain_environment_failure
```

Oracle and environment failures are excluded from the model pass/fail
denominator. DUT mismatches and timeouts remain model/design failures.

## 10. Qualification Gates

### 10.1 Reference-model unit gate

- known hand-calculated examples pass;
- boundary and signed cases pass;
- deterministic regeneration produces identical hashes;
- malformed manifests and unsafe paths are rejected;
- reference code has no dependency on generated RTL.

### 10.2 Per-family Line-A gate

- H0-H2 pass, H3 is either pass or policy-valid `not_applicable`, and L0-L3
  pass. H3 may be `not_applicable` only when the task catalog explicitly marks
  `h3_applicability: not_applicable` because no natural-language requirement or
  oracle-HIS comparison exists; missing fidelity evidence or a failed comparison
  may not be converted to `not_applicable`;
- all four scenario classes complete;
- structured mismatch parsing is exercised by at least one controlled bad DUT;
- mutation score meets the catalog threshold;
- every critical mutation is scoreable and killed;
- hidden concrete vectors are absent from prompts and exports;
- artifact audit validates run, sample, family, L-level, manifest, bundle, and
  mutation provenance.

### 10.3 Phase C completion gate

```text
Independent golden domains: numeric, signal, image, RL
Target families with python_reference evidence: 9/9
Paper-1 core mutation-qualified: 14/14 retained
Hidden scenario classes present: 9/9 target families
Critical mutation survivors/non-scoreable: 0
Evidence audit issues: 0
```

Phase C does not require L4 or L5. Those remain Phase D and Phase E gates.

## 11. Implementation Order

```text
C0 oracle bundle/types/path-safety/recorder infrastructure
C1 numeric references and qualification
C2 signal references and qualification
C3 image references and qualification
C4 RL references and qualification
C5 combined Line-A run, evidence promotion, report, and audit
```

Each domain receives a separate implementation checkpoint and independent code
review. Later domains reuse C0 but may not weaken its isolation or evidence
requirements.

## 12. Verification Commands

The implementation plan must include at least:

```powershell
python -m pytest LLM/tests/test_sr2fpga_oracle_*.py -q
python -m pytest LLM/tests -q
python -m compileall -q LLM/src/sr2fpga_agent
python -m LLM.src.sr2fpga_agent.task_evidence `
  --output tmp/phase-c-evidence-verify.md `
  --audit-run-root tmp
git diff --check -- <phase-c-scoped-paths>
```

The combined qualification run uses a new versioned run ID, isolated dataset,
export, and run roots. Existing Phase-B artifacts are immutable inputs and are
not overwritten.

## 13. Risks and Controls

| Risk | Control |
|---|---|
| Python and RTL repeat the same bug | hand-calculated vectors, independent code structure, domain review |
| hidden-vector leakage | evaluator-only paths, prompt/export sanitization, regression tests |
| oracle becomes another generated artifact | canonical trusted package, patch denial, provenance hashes |
| `$readmemh` portability differences | fixed ASCII hex format and Icarus/Verilator tests |
| stale bundles after source changes | reference version plus bundle hash and isolated run roots |
| non-scoreable mutations mistaken for kills | artifact audit requires scoreable and killed cases |
| scope expands into new tasks | fixed nine-family Phase C target set |

## 14. Design Decision Summary

SR2FPGA Phase C uses trusted Python references to materialize deterministic
runtime oracle bundles. Existing black-box SystemVerilog testbenches consume
those bundles under the runner's control. Hidden vectors remain outside the
model-visible project and training exports. Evidence is promoted only through a
versioned, artifact-audited Line-A run that proves all scenario classes,
mutation strength, and reference provenance.
