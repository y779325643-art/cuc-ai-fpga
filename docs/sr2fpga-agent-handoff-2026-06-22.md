# SR2FPGA Agent Handoff - 2026-06-22

## Current Goal

Build a tool-calling dataset factory for SR2FPGA:

requirement -> System-HIS -> multi-file Verilog RTL project -> open-source EDA tool labels -> diagnosis/patch trajectories -> trainable JSONL views.

The important research asset is not only passing RTL, but also failed attempts with tool logs, diagnosis, and locally computed `patch.diff`.

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

1. Add a formal batch data-generation runner instead of ad hoc Python snippets.
   - Suggested command: `python3 -m LLM.src.sr2fpga_agent.batch_generate --mode forced-repair --count ...`
   - It should write a JSON run summary under `tmp/data_generation_runs/` or another ignored run-log directory.

2. Add a first-class failure injector.
   - Current forced samples use only one injected error: rename RTL port `rst_n` to `reset_n`.
   - Next useful injectors: width mismatch, testbench expected-value mismatch, missing manifest source, wrong top module, constraint references missing clock.

3. Improve DeepSeek repair for real LLM failures.
   - `sample_llm_batch_000002` stopped at L1 after repair.
   - Inspect its attempt logs and patch before changing prompts.

4. Keep generated datasets out of Git for now.
   - Commit code, tests, docs, configs.
   - Do not commit `datasets/`, model weights, LoRA outputs, or API keys.

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

Export counts after refresh:

- `failure_to_diagnosis.jsonl`: 16
- `failure_to_patch.jsonl`: 14
- `his_to_project.jsonl`: 45
- `project_to_measured_qor.jsonl`: 45
- `project_to_predicted_qor.jsonl`: 45
- `requirement_to_his.jsonl`: 45
- `requirement_to_project.jsonl`: 45

Notes:

- Dataset snapshot is committed in `0ec152a Add SR2FPGA generated dataset snapshot`.
- API keys were not used for deterministic generation.
- DeepSeek generation now has a multi-module RTL contract for `uart_tx`,
  `spi_master`, `pwm_controller`, `fir_filter`, `streaming_valid_ready`, and
  `matrix_vector_mac`: prompts require `rtl/top.v` as an integration wrapper
  plus at least two submodule `.v` files, and the parser rejects single-file
  LLM responses for those task families.
- `DEEPSEEK_API_KEY` was not present in the current shell during this update,
  so no real DeepSeek multi-module sample was generated in this pass.
- Next useful work: add failure injectors for multi-module-specific errors.
- Known non-blocking hardening: `matrix_vector_mac` width values below 3 should be guarded or generated without negative repeat counts.
- Simulation label hardening was added after final review: `sim_run` now fails if the log contains `TEST_FAIL` or omits `TEST_PASS`, even when `vvp` exits 0.
- Rechecked after hardening: all 12 multi-module sample configurations still reach `L3`.
- Known pre-existing issue exposed by hardening: future `simple_fsm` generation currently reaches `L1` because its generated testbench prints `TEST_FAIL`; fix that separately before generating more FSM data.
