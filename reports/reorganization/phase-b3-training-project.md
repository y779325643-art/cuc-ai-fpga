# Phase B3 Standalone Training Project Report

Date: 2026-07-23

Status: PASS

## Scope

Phase B3 separated dataset preparation, no-model validation, LoRA/QLoRA
training entry points, adapter merging, and serving smoke assets from the
legacy `LLM/` project.

The canonical Training package now lives at
`training/src/sr2fpga_training/`. It consumes versioned files under
`contracts/` and immutable releases under `datasets/`; it does not import the
Agent implementation.

## Task Commits

| Task | Commit | Result |
|---|---|---|
| Standalone package boundary | `23feb2c2` | Added lightweight metadata, optional heavy extras, entry points, and boundary tests |
| Training implementation move | `63159a6e` | Moved four modules and four existing test groups into `training/` |
| Config and serving assets | `6df037b8` | Moved configs, scripts, and fixture; removed private machine defaults |
| Training-view provenance | `c447f059` | Enforced source episode and no-pass-credit rules for canonical REQ2FILE rows |
| Independent installation | `19025243` | Verified editable lightweight install, CLI help, conversion, and dry-run |

## Ownership State

- Canonical Training source: 6 Python files under
  `training/src/sr2fpga_training/`.
- Training tests: 8 files under `training/tests/`.
- Committed config assets: 4 examples plus `training/configs/README.md`.
- Operational assets: 7 scripts plus `training/scripts/README.md`.
- Smoke input:
  `training/tests/fixtures/smoke_verilog_raw.jsonl`.
- Legacy `LLM/src` contains only
  `LLM/src/sr2fpga_agent/__init__.py`, the temporary Agent compatibility shim.

Training source imports neither `sr2fpga_agent` nor `LLM.`. Agent source
imports neither `sr2fpga_training` nor the heavy ML stack.

## Dependency And Configuration Boundary

The base Training installation requires only PyYAML. Optional extras are:

- `train`: Accelerate, bitsandbytes, Datasets, PEFT, PyTorch, Transformers,
  and TRL.
- `serve`: vLLM.
- `dev`: pytest.

Committed examples use public model identifiers and write to ignored
`artifacts/training/`. Machine-local paths and endpoints belong in ignored
`training/configs/local/` or environment variables.

Agent tool fallback paths were also removed from source during the final
boundary audit. Tool discovery now uses `PATH`,
`SR2FPGA_TOOL_FALLBACK_DIRS`, and
`SR2FPGA_OSS_CAD_SUITE_ROOT`.

## Training-View Provenance

Training reads the registered training-view schema through
`contracts/manifest.json`. Canonical `requirement_to_file` rows are rejected
unless:

- `source_episode_id` is non-empty;
- `official_eval_unit` is `false`;
- `standalone_pass_credit` is `false`.

Existing historical rows without `view_type` remain convertible. REQ2FILE is
therefore retained as a derived training view without standalone project pass
credit.

## Lightweight Verification

The project installed successfully with:

```powershell
python -m pip install -e "training[dev]"
```

No `train` or `serve` extra was installed. All four canonical module help
commands passed from a temporary working directory.

The real lightweight conversion command was:

```powershell
python -m sr2fpga_training.prepare_dataset `
  --input training/tests/fixtures/smoke_verilog_raw.jsonl `
  --output artifacts/training/prepared-data/smoke/chat.jsonl
```

It converted 6 rows. The no-model validation command was:

```powershell
python -m sr2fpga_training.training_dry_run `
  --input artifacts/training/prepared-data/smoke/chat.jsonl `
  --max-seq-length 2048
```

Dry-run result:

- Rows: 6.
- Valid rows: 6.
- Estimated token range: 45-164.
- Rows over 2048: 0.
- `fits_max_seq_length`: `true`.

No model was trained, downloaded, loaded, or merged. CUDA was not initialized.
No vLLM server was started.

## Test And Audit Results

- Training suite before the cross-project audit:
  `52 passed, 5 subtests passed in 13.33s`.
- Final contracts plus Agent plus Training suite:
  `989 passed, 349 subtests passed in 155.46s`.
- Cross-project boundary tests: 5 pass.
- Fresh-process imports confirmed:
  - importing Agent does not load Torch;
  - importing dataset preparation does not load Torch;
  - importing dry-run validation does not load Transformers.
- Corrected strict source scan found no `LLM.` dependency, private absolute
  path, or API-key-shaped literal in canonical source.
- `git diff -- datasets` was empty.
- No tracked change appeared beneath `tmp/` or `artifacts/`.

## Remaining Work

Phase B4 must:

- add or retire the planned legacy Training command wrappers;
- update active root and legacy documentation to canonical commands;
- remove obsolete `LLM/` residue and old dependency files after compatibility
  review;
- back up and clean tracked `tmp/` according to the cutover plan;
- run the final full-suite, data-integrity, and repository-status audit.
