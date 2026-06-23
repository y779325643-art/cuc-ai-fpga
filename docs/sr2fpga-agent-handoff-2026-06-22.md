# SR2FPGA Agent Handoff - 2026-06-22

## Current Goal

Build a tool-calling dataset factory for SR2FPGA:

requirement -> System-HIS -> multi-file Verilog RTL project -> open-source EDA tool labels -> diagnosis/patch trajectories -> trainable JSONL views.

The important research asset is not only passing RTL, but also failed attempts with tool logs, diagnosis, and locally computed `patch.diff`.

## Current Handoff Update - 2026-06-23

Branch:

`codex/sr2fpga-data-agent`

Latest relevant commits:

- `5042bed Update project README for SR2FPGA` - root README is now the project
  entry point and reflects SR2FPGA, System-HIS, tool-verified trajectories,
  autonomous runner usage, dataset/export layout, deployment pointers, and
  secret-handling rules.
- `bb5d055 Document SR2FPGA autonomous runner` - `LLM/README.md` and this
  handoff file document the runner.
- `48a11b4 Add SR2FPGA runner CLI` - runner has a direct command-line entry:
  `python3 -m LLM.src.sr2fpga_agent.runner --config configs/sr2fpga_agent.example.yaml --run-id <run-id>`.
- `4da2e69 Fix SR2FPGA runner rejected sample cursor` - fixed resume/progress
  behavior for pre-existing sample directories.
- `1629619 Add autonomous SR2FPGA batch runner` - batch runner can plan samples,
  call `DataGenerationAgent.run_one()`, write `run_state.json`, `events.jsonl`,
  `summary.json`, and refresh exports.
- `9007910 Add SR2FPGA runner state buckets` - runner state tracks
  `success_l3`, `repair_trajectory`, and `rejected` buckets.
- `2157d1c update 2026.06.23 agent` - later workspace update adding Claude
  context files, report PDFs, temporary PDF renders, and smoke data.

Current verification:

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_failure_injector -q
# Ran 3 tests - OK

python3 -m unittest discover -s LLM/tests -q
# Ran 78 tests - OK
```

Current uncommitted work observed after the latest commits:

- New untracked files:
  - `LLM/src/sr2fpga_agent/failure_injector.py`
  - `LLM/tests/test_sr2fpga_agent_failure_injector.py`
- The failure injector currently supports:
  - `rename_reset_port`
  - `missing_manifest_source`
  - `wrong_top_module`
  - `FailureInjectingProjectGenerator` wrapper around a base project generator
- There are also tracked dataset deletions in the working tree, affecting:
  - parts of `sample_llm_repair_forced_minpatch_000011`
  - parts of `sample_llm_repair_forced_minpatch_000012`
  - `sample_llm_uart_tx_000001/attempt_001/rtl/uart_tx_core.v`
  - selected generated files under `sample_multimodule_000005` and
    `sample_multimodule_000010`
- Do not revert those deletions automatically. They may be intentional cleanup
  from Claude/user work. Confirm before staging or restoring dataset files.

Recommended immediate next step:

1. Decide whether the uncommitted dataset deletions should be kept, restored, or
   replaced by a cleaner dataset-snapshot commit.
2. Integrate `failure_injector.py` into the autonomous runner as an optional
   configured project-generator wrapper.
3. Add runner config fields for synthetic failure injection only after the
   dataset deletion question is resolved.

## Current Branch And Code State

- Branch: `codex/sr2fpga-data-agent`
- Latest committed repair optimization before this note: `d272dd2 Minimize DeepSeek repair patch noise`
- Current source changes in progress:
  - `LLM/src/sr2fpga_agent/recorder.py`
  - `LLM/tests/test_sr2fpga_agent_recorder.py`
- Reason: `export_training_views()` failed when a macOS `.DS_Store` file appeared under a generated project directory. The fix skips hidden files while exporting project files.
- Verification after the fix:
  - `python3 -m unittest LLM.tests.test_sr2fpga_agent_recorder.DatasetRecorderTest.test_export_training_views_ignores_hidden_project_files -q`
  - `python3 -m unittest discover -s LLM/tests -q`

## Data Generated In This Run

Dataset root:

`datasets/sr2fpga_rtl_v1`

Export root:

`datasets/sr2fpga_rtl_v1_exports`

New forced repair samples:

- `sample_llm_repair_forced_minpatch_000005` - L3, one failure, one repair patch
- `sample_llm_repair_forced_minpatch_000006` - L3, one failure, one repair patch
- `sample_llm_repair_forced_minpatch_000007` - L3, one failure, one repair patch
- `sample_llm_repair_forced_minpatch_000008` - L3, one failure, one repair patch
- `sample_llm_repair_forced_minpatch_000009` - L3, one failure, one repair patch
- `sample_llm_repair_forced_minpatch_000010` - L3, one failure, one repair patch
- `sample_llm_repair_forced_minpatch_000011` - L3, one failure, one repair patch
- `sample_llm_repair_forced_minpatch_000012` - L3, one failure, one repair patch

All eight forced repair patches are RTL-only and do not rewrite `manifest.json`.

New direct DeepSeek generation samples:

- `sample_llm_batch_000001` - L3, no repair needed
- `sample_llm_batch_000002` - L1, two failed attempts, one repair patch
- `sample_llm_batch_000003` - L3, no repair needed
- `sample_llm_batch_000004` - L3, no repair needed

Keep `sample_llm_batch_000002`: it is a useful real LLM boundary case where the current repair loop did not reach simulation/synthesis.

Current export counts after refresh:

- `failure_to_diagnosis.jsonl`: 16
- `failure_to_patch.jsonl`: 14
- `requirement_to_his.jsonl`: 33
- `his_to_project.jsonl`: 33
- `requirement_to_project.jsonl`: 33
- `project_to_predicted_qor.jsonl`: 33
- `project_to_measured_qor.jsonl`: 33

## Commands Used

Run tests:

```bash
python3 -m unittest discover -s LLM/tests -q
```

Refresh training views:

```bash
python3 - <<'PY'
from pathlib import Path
from LLM.src.sr2fpga_agent.recorder import DatasetRecorder
DatasetRecorder(Path("datasets/sr2fpga_rtl_v1")).export_training_views(
    Path("datasets/sr2fpga_rtl_v1_exports")
)
PY
```

Count export rows:

```bash
python3 - <<'PY'
from pathlib import Path
root = Path("datasets/sr2fpga_rtl_v1_exports")
for path in sorted(root.glob("*.jsonl")):
    print(path.name, sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip()))
PY
```

## Known Issues And Next Work

1. Continue hardening the autonomous runner.
   - Current command: `python3 -m LLM.src.sr2fpga_agent.runner --config configs/sr2fpga_agent.example.yaml --run-id <run-id>`.
   - Run state and logs live under `tmp/sr2fpga_runs/<run-id>/`.
   - Next useful runner feature is optional synthetic failure injection.

2. Finish first-class failure injector integration.
   - Current untracked injector code already covers reset-port rename, missing
     manifest source, and wrong top module.
   - Next useful injectors: width mismatch, testbench expected-value mismatch,
     constraint references missing clock, and multi-module connection mismatch.

3. Improve DeepSeek repair for real LLM failures.
   - `sample_llm_batch_000002` stopped at L1 after repair.
   - Inspect its attempt logs and patch before changing prompts.

4. Treat dataset commits deliberately.
   - The repo already contains a milestone dataset snapshot.
   - Do not stage generated dataset deletions or additions casually.
   - Never commit model weights, LoRA outputs, or API keys.

## Multi-Module Task Family Implementation

Spec path: `docs/superpowers/specs/2026-06-22-sr2fpga-multimodule-task-families-design.md`

Plan path: `docs/superpowers/plans/2026-06-22-sr2fpga-multimodule-task-families.md`

New deterministic task families:

- `uart_tx`
- `spi_master`
- `pwm_controller`
- `fir_filter`
- `streaming_valid_ready`
- `matrix_vector_mac`

Generated local samples:

- `sample_multimodule_000001`
- `sample_multimodule_000002`
- `sample_multimodule_000003`
- `sample_multimodule_000004`
- `sample_multimodule_000005`
- `sample_multimodule_000006`
- `sample_multimodule_000007`
- `sample_multimodule_000008`
- `sample_multimodule_000009`
- `sample_multimodule_000010`
- `sample_multimodule_000011`
- `sample_multimodule_000012`

Observed local labels:

| Sample | Task type | Pass level | Source count |
| --- | --- | --- | --- |
| `sample_multimodule_000001` | `uart_tx` | `L3` | 3 |
| `sample_multimodule_000002` | `uart_tx` | `L3` | 3 |
| `sample_multimodule_000003` | `spi_master` | `L3` | 3 |
| `sample_multimodule_000004` | `spi_master` | `L3` | 3 |
| `sample_multimodule_000005` | `pwm_controller` | `L3` | 3 |
| `sample_multimodule_000006` | `pwm_controller` | `L3` | 3 |
| `sample_multimodule_000007` | `fir_filter` | `L3` | 3 |
| `sample_multimodule_000008` | `fir_filter` | `L3` | 3 |
| `sample_multimodule_000009` | `streaming_valid_ready` | `L3` | 3 |
| `sample_multimodule_000010` | `streaming_valid_ready` | `L3` | 3 |
| `sample_multimodule_000011` | `matrix_vector_mac` | `L3` | 4 |
| `sample_multimodule_000012` | `matrix_vector_mac` | `L3` | 4 |

Real DeepSeek multi-file samples:

| Sample | Task type | Pass level | Source count | Outcome |
| --- | --- | --- | --- | --- |
| `sample_llm_spi_master_000001` | `spi_master` | `L1` | 3 | LLM generated `top.v`, `clock_divider.v`, and `spi_master_core.v`; first attempt failed lint with multi-driven registers, DeepSeek repaired lint, final attempt timed out in `vvp`. |
| `sample_llm_uart_tx_000001` | `uart_tx` | `L1` | 3 | LLM generated `top.v`, `baud_tick_gen.v`, and `uart_tx_core.v`; DeepSeek repaired lint, final attempts reached simulation but printed `TEST_FAIL`. |

Export counts after refresh:

- `failure_to_diagnosis.jsonl`: 21
- `failure_to_patch.jsonl`: 17
- `his_to_project.jsonl`: 47
- `project_to_measured_qor.jsonl`: 47
- `project_to_predicted_qor.jsonl`: 47
- `requirement_to_his.jsonl`: 47
- `requirement_to_project.jsonl`: 47

Notes:

- Dataset snapshot is committed in `0ec152a Add SR2FPGA generated dataset snapshot`.
- API keys were not used for deterministic generation.
- DeepSeek generation now has a multi-module RTL contract for `uart_tx`,
  `spi_master`, `pwm_controller`, `fir_filter`, `streaming_valid_ready`, and
  `matrix_vector_mac`: prompts require `rtl/top.v` as an integration wrapper
  plus at least two submodule `.v` files, and the parser rejects single-file
  LLM responses for those task families.
- A local ignored `.env` file now provides `DEEPSEEK_API_KEY` for real DeepSeek
  runs; do not commit the secret. `.env.example` documents the variable name.
- Real DeepSeek multi-file generation has been exercised. The first two samples
  are valuable failure/repair trajectories rather than L3 examples; next useful
  work is improving prompt constraints or repair policy for bounded testbenches
  and simulation semantic failures.
- Next useful work: add failure injectors for multi-module-specific errors.
- Known non-blocking hardening: `matrix_vector_mac` width values below 3 should be guarded or generated without negative repeat counts.
- Simulation label hardening was added after final review: `sim_run` now fails if the log contains `TEST_FAIL` or omits `TEST_PASS`, even when `vvp` exits 0.
- Rechecked after hardening: all 12 multi-module sample configurations still reach `L3`.
- Known pre-existing issue exposed by hardening: future `simple_fsm` generation currently reaches `L1` because its generated testbench prints `TEST_FAIL`; fix that separately before generating more FSM data.

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
