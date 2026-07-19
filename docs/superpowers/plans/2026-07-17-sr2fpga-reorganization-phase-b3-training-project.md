# SR2FPGA Repository Reorganization Phase B3: Training Project Migration Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Move dataset preparation, dry-run validation, LoRA/QLoRA training, adapter merge, and serving smoke assets into an independently installable `training/` project with no dependency on Agent implementation code.

**Architecture:** `training/src/sr2fpga_training/` owns model-training workflows. It consumes versioned JSON/JSONL contracts and released datasets, never imports `sr2fpga_agent`, and writes local outputs under ignored `artifacts/training/`. Heavy ML and serving dependencies are optional extras so data conversion and tests remain lightweight.

**Tech Stack:** Python 3.11, setuptools, pytest, PyYAML, datasets, PEFT, PyTorch, Transformers, TRL, bitsandbytes, accelerate, optional vLLM.

**Depends on:** Phase B1 training-view contract and dataset release metadata. Phase B2 may be complete, but Training must not import Agent.

**Must not do:** Train a model during migration verification, download models, expose private paths or API keys, mutate released dataset payloads, or treat REQ2FILE rows as standalone evaluation units.

---

## Task 1: Define the standalone Training package and dependency boundary

**Files:**
- Create: `training/pyproject.toml`
- Create: `training/src/sr2fpga_training/__init__.py`
- Create: `training/tests/test_training_package_boundary.py`

### Step 1: Write the failing boundary test

Parse `training/pyproject.toml` with `tomllib` and assert:

1. Project name is `sr2fpga-training`.
2. Python requirement is at least 3.11.
3. Base dependencies contain only lightweight requirements needed by imported top-level code, initially `PyYAML`.
4. Optional extra `train` contains:
   - `accelerate`
   - `bitsandbytes`
   - `datasets`
   - `peft`
   - `torch`
   - `transformers`
   - `trl`
5. Optional extra `serve` contains `vllm`.
6. Optional extra `dev` contains pytest.
7. Console scripts map to:
   - `sr2fpga-prepare-dataset = sr2fpga_training.prepare_dataset:main`
   - `sr2fpga-training-dry-run = sr2fpga_training.training_dry_run:main`
   - `sr2fpga-train-lora = sr2fpga_training.train_lora:main`
   - `sr2fpga-merge-lora = sr2fpga_training.merge_lora:main`
8. AST scans of `training/src` find no import beginning with `sr2fpga_agent` or `LLM.`.
9. Importing `sr2fpga_training.prepare_dataset` and `sr2fpga_training.training_dry_run` does not load torch, transformers, datasets, peft, trl, bitsandbytes, accelerate, or vllm into `sys.modules`.

### Step 2: Run and confirm failure

```powershell
python -m pytest training/tests/test_training_package_boundary.py -q
```

Expected result: package metadata and modules missing.

### Step 3: Add `training/pyproject.toml`

Use:

```toml
[build-system]
requires = ["setuptools>=75", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "sr2fpga-training"
version = "0.1.0"
description = "SR2FPGA dataset preparation and model training workflows"
requires-python = ">=3.11"
dependencies = [
  "PyYAML>=6.0.2"
]

[project.optional-dependencies]
train = [
  "accelerate>=0.34.0",
  "bitsandbytes>=0.43.3",
  "datasets>=2.21.0",
  "peft>=0.12.0",
  "torch>=2.4.0",
  "transformers>=4.53.0",
  "trl>=0.10.1"
]
serve = ["vllm>=0.6.0"]
dev = ["pytest>=8.0"]

[project.scripts]
sr2fpga-prepare-dataset = "sr2fpga_training.prepare_dataset:main"
sr2fpga-training-dry-run = "sr2fpga_training.training_dry_run:main"
sr2fpga-train-lora = "sr2fpga_training.train_lora:main"
sr2fpga-merge-lora = "sr2fpga_training.merge_lora:main"

[tool.setuptools.packages.find]
where = ["src"]
```

Create a minimal `__init__.py` that exports a version string only. Do not eagerly import training backends.

### Step 4: Run the metadata assertions

```powershell
python -m pytest training/tests/test_training_package_boundary.py -q
```

Expected result: metadata assertions pass; module existence assertions may remain failing until Task 2.

### Step 5: Commit

```powershell
git add training/pyproject.toml training/src/sr2fpga_training/__init__.py training/tests/test_training_package_boundary.py
git commit -m "build: define standalone Training project"
```

---

## Task 2: Move Training modules and tests

**Files:**
- Move: `LLM/src/prepare_dataset.py` to `training/src/sr2fpga_training/prepare_dataset.py`
- Move: `LLM/src/training_dry_run.py` to `training/src/sr2fpga_training/training_dry_run.py`
- Move: `LLM/src/train_lora.py` to `training/src/sr2fpga_training/train_lora.py`
- Move: `LLM/src/merge_lora.py` to `training/src/sr2fpga_training/merge_lora.py`
- Move tests:
  - `LLM/tests/test_prepare_dataset.py`
  - `LLM/tests/test_training_dry_run.py`
  - `LLM/tests/test_training_smoke_assets.py`
  - `LLM/tests/test_serving_entrypoints.py`
- Modify moved test imports and paths

### Step 1: Record pre-move command behavior

Run and store ignored evidence under `artifacts/reorganization/phase-b3/`:

```powershell
python -m LLM.src.prepare_dataset --help
python -m LLM.src.training_dry_run --help
python -m LLM.src.train_lora --help
python -m LLM.src.merge_lora --help
```

Do not invoke training.

### Step 2: Move source files with Git history

```powershell
git mv LLM/src/prepare_dataset.py training/src/sr2fpga_training/prepare_dataset.py
git mv LLM/src/training_dry_run.py training/src/sr2fpga_training/training_dry_run.py
git mv LLM/src/train_lora.py training/src/sr2fpga_training/train_lora.py
git mv LLM/src/merge_lora.py training/src/sr2fpga_training/merge_lora.py
```

Keep heavy imports inside `main()`. If any heavy import is top-level, move it into the command execution path without changing behavior.

Change the default config in `train_lora.py` from `LLM/configs/train_lora.yaml` to `training/configs/train_lora.example.yaml`.

### Step 3: Move the four Training tests

Use `git mv` into `training/tests/`. Rewrite imports:

- `LLM.src.prepare_dataset` to `sr2fpga_training.prepare_dataset`.
- `LLM.src.training_dry_run` to `sr2fpga_training.training_dry_run`.
- Any command path to the canonical Training module.
- Repository paths to `training/` locations established in Task 3.

### Step 4: Remove the Agent test dependency

`test_serving_entrypoints.py` currently imports `executable_env` and `resolve_executable` from Agent. Replace that dependency with test-local standard-library behavior:

- Use `shutil.which("bash")`.
- Copy and normalize `os.environ` directly.
- Keep the existing WSL path conversion helper in the Training test or move it to a small Training-owned `serving_paths.py` only if production scripts need the same function.
- Do not import `sr2fpga_agent`.

### Step 5: Run moved unit tests

```powershell
python -m pytest training/tests/test_prepare_dataset.py training/tests/test_training_dry_run.py -q
python -m pytest training/tests/test_training_package_boundary.py -q
```

Expected result: conversion, dry-run, package boundary, and no-eager-heavy-import tests pass.

### Step 6: Run canonical CLI help

```powershell
python -m sr2fpga_training.prepare_dataset --help
python -m sr2fpga_training.training_dry_run --help
python -m sr2fpga_training.train_lora --help
python -m sr2fpga_training.merge_lora --help
```

Expected result: exit code zero without loading or downloading a model.

### Step 7: Commit

```powershell
git add training/src training/tests LLM/src LLM/tests
git commit -m "refactor: move Training implementation to standalone project"
```

---

## Task 3: Move Training configs, scripts, and fixtures

**Files:**
- Move: `LLM/configs/*.yaml` to `training/configs/*.example.yaml`
- Move: `LLM/configs/serve_vllm.env.example` to `training/configs/serve_vllm.env.example`
- Move: `LLM/scripts/*` to `training/scripts/*`
- Move: `LLM/data/examples/smoke_verilog_raw.jsonl` to `training/tests/fixtures/smoke_verilog_raw.jsonl`
- Move or merge: `LLM/data/README.md` to `training/tests/fixtures/README.md`
- Move: `test_gemma_transformers.py` to `training/scripts/test_gemma_transformers.py`
- Create: `training/configs/README.md`
- Modify: `training/tests/test_training_smoke_assets.py`
- Modify: `training/tests/test_serving_entrypoints.py`
- Create: `training/tests/test_training_config_policy.py`

### Step 1: Write failing config-policy tests

Tests must assert:

1. No tracked Training config or script contains:
   - a private WSL mount path, such as `/mnt/<drive>/<user>`
   - a mounted Windows user home, such as `/mnt/<drive>/Users/<name>`
   - a private Windows root, such as `<private-windows-root>`
   - a literal API key prefix such as `sk-`
2. Default `train_file` and `output_dir` values are repository-relative paths under `artifacts/training/`.
3. Model defaults are public model identifiers or environment-variable-driven values, not personal local paths.
4. Local overrides belong under ignored `training/configs/local/`.
5. Shell scripts use `TRAINING_VENV_PATH`, `MODEL_PATH`, or `QWEN_MODEL_PATH` overrides and do not hard-code a user directory.
6. Fixture tests write to `tmp_path` or ignored `artifacts/`, never root tracked `tmp/`.

### Step 2: Run and confirm failure

```powershell
python -m pytest training/tests/test_training_config_policy.py training/tests/test_training_smoke_assets.py training/tests/test_serving_entrypoints.py -q
```

Expected result: old locations and private defaults fail.

### Step 3: Move files with Git history

Preserve script names for compatibility wrappers in Phase B4. Rename YAMLs to make example status explicit:

- `train_lora.yaml` to `train_lora.example.yaml`.
- `train_qwen_req2file_short.yaml` to `train_qwen_req2file_short.example.yaml`.
- `train_qwen_smoke.yaml` to `train_qwen_smoke.example.yaml`.

Move the smoke JSONL fixture into `training/tests/fixtures/`. It is test data, not a release dataset.

### Step 4: Replace machine-specific defaults

Use these committed defaults:

- Generic model identifiers such as `Qwen/Qwen2.5-Coder-7B-Instruct` or `google/gemma-4-12b-it`.
- `train_file` under `artifacts/training/prepared-data/<dataset-id>/`.
- `output_dir` under `artifacts/training/adapters/<run-id>/`.
- Serving scripts require an explicit model path or accept a public model identifier.
- Virtual environment defaults may be `.venv` under `training/` or must be supplied through `TRAINING_VENV_PATH`.

Do not claim an unverified model identifier in executable tests. Config tests should validate shape and absence of private paths; they must not access the network.

### Step 5: Update scripts

- Replace `LLM/src.*` module invocations with `sr2fpga_training.*` or installed console scripts.
- Resolve repository root from the script location.
- Preserve LF line endings.
- Keep vLLM argument tests by injecting a fake `vllm` executable.
- Preserve `--language-model-only` and other existing tested flags where still applicable.
- Make missing local model diagnostics actionable without naming a private download directory.

### Step 6: Update fixture tests

- Use `training/tests/fixtures/smoke_verilog_raw.jsonl`.
- Use pytest `tmp_path` or `TemporaryDirectory` for converted outputs.
- Read release exports through `datasets/manifest.json` rather than hard-coded dataset roots where practical.
- Preserve current row-count and context-length assertions unless the input release proves different.

### Step 7: Run focused tests

```powershell
python -m pytest training/tests/test_training_config_policy.py training/tests/test_training_smoke_assets.py training/tests/test_serving_entrypoints.py -q
```

Expected result: pass on Windows without requiring vLLM, CUDA, or a local model.

### Step 8: Commit

```powershell
git add training/configs training/scripts training/tests LLM/configs LLM/scripts LLM/data test_gemma_transformers.py
git commit -m "refactor: move Training configs and serving assets"
```

---

## Task 4: Enforce training-view provenance at dataset preparation time

**Files:**
- Modify: `training/src/sr2fpga_training/prepare_dataset.py`
- Create: `training/src/sr2fpga_training/contracts.py`
- Create: `training/tests/test_training_view_provenance.py`

### Step 1: Write failing provenance tests

Cover these cases:

1. A valid `requirement_to_file` row with `source_episode_id`, `official_eval_unit: false`, and `standalone_pass_credit: false` converts successfully.
2. Missing `source_episode_id` raises `DatasetFormatError`.
3. `official_eval_unit: true` raises `DatasetFormatError`.
4. `standalone_pass_credit: true` raises `DatasetFormatError`.
5. Project-level views continue converting.
6. Historical rows without `view_type` continue through existing legacy formats.
7. No Agent package import occurs.

### Step 2: Run and confirm failure

```powershell
python -m pytest training/tests/test_training_view_provenance.py -q
```

### Step 3: Implement a Training-owned contract reader

`contracts.py` must:

- Discover repository root from explicit `SR2FPGA_REPO_ROOT` or by walking upward for `contracts/manifest.json`.
- Read the training-view schema path from `contracts/manifest.json`.
- Cache parsed JSON per process.
- Expose a focused `validate_training_view_provenance(row)` function.
- Validate only provenance and pass-credit rules needed by Training; do not duplicate Agent validation logic.
- Raise a Training-owned exception translated to `DatasetFormatError` by `prepare_dataset.py`.

### Step 4: Integrate before message conversion

When `view_type == "requirement_to_file"`, call the provenance validator before constructing messages. The conversion output remains chat JSONL and includes no new hidden evaluation claim.

### Step 5: Run focused tests

```powershell
python -m pytest training/tests/test_training_view_provenance.py training/tests/test_prepare_dataset.py training/tests/test_training_smoke_assets.py -q
```

Expected result: pass.

### Step 6: Commit

```powershell
git add training/src/sr2fpga_training/contracts.py training/src/sr2fpga_training/prepare_dataset.py training/tests/test_training_view_provenance.py
git commit -m "feat: enforce training-view provenance"
```

---

## Task 5: Verify lightweight and optional-heavy installation paths

**Files:**
- Create: `training/tests/test_training_cli_smoke.py`
- Modify: `training/README.md`

### Step 1: Add lightweight CLI tests

Use `subprocess.run` and the current Python executable to verify help for all four modules. Also run a real lightweight conversion and dry-run using the smoke fixture and `tmp_path`.

Tests must prove:

- No model download.
- No CUDA initialization.
- No heavy dependency import for prepare/dry-run.
- Train and merge commands can show help without heavy dependencies.

### Step 2: Install lightweight Training project

```powershell
python -m pip install -e "training[dev]"
```

Do not install `training[train]` or `training[serve]` as part of migration verification.

### Step 3: Run complete Training tests

```powershell
python -m pytest training/tests -q
```

Expected result: all pass without GPU or model files.

### Step 4: Run conversion and dry-run commands

```powershell
python -m sr2fpga_training.prepare_dataset --input training/tests/fixtures/smoke_verilog_raw.jsonl --output artifacts/training/prepared-data/smoke/chat.jsonl
python -m sr2fpga_training.training_dry_run --train-file artifacts/training/prepared-data/smoke/chat.jsonl --max-seq-length 2048
```

Use the actual existing CLI option names discovered from `--help`. If they differ, preserve the existing public interface and document the exact canonical command in the README rather than silently renaming flags.

### Step 5: Document Training ownership

`training/README.md` must document:

- Lightweight editable install.
- Optional `train` and `serve` extras.
- Canonical module and console commands.
- Config and local override policy.
- Dataset release consumption.
- Training-view provenance rule.
- Artifact output policy.
- Explicit statement that Training does not import Agent.
- API keys and provider endpoints are local environment variables only.

### Step 6: Commit

```powershell
git add training/README.md training/tests/test_training_cli_smoke.py
git commit -m "test: verify standalone Training project"
```

---

## Task 6: Complete cross-project boundary verification

**Files:**
- Create: `contracts/tests/test_project_dependency_boundaries.py`
- Create: `reports/reorganization/phase-b3-training-project.md`

### Step 1: Add cross-project AST tests

The test must scan canonical source trees and assert:

- Agent source does not import Training or heavy ML libraries.
- Training source does not import Agent or `LLM.`.
- Both may read files registered under root `contracts/`.
- Neither source tree contains a private absolute path.
- Root `LLM/src` contains no canonical implementation file after moves; only compatibility code is allowed.

### Step 2: Run all lightweight project tests

```powershell
python -m pytest contracts/tests agent/tests training/tests -q
```

Expected result: all pass.

### Step 3: Run import isolation in fresh processes

```powershell
python -c "import sr2fpga_agent; import sys; assert 'torch' not in sys.modules"
python -c "import sr2fpga_training.prepare_dataset; import sys; assert 'torch' not in sys.modules"
python -c "import sr2fpga_training.training_dry_run; import sys; assert 'transformers' not in sys.modules"
```

### Step 4: Verify source and data cleanliness

```powershell
git diff --check
git diff -- datasets
git status --short tmp artifacts
Get-ChildItem agent/src,training/src -Recurse -Filter *.py | Select-String -Pattern 'LLM\.|(?i:(?<![A-Za-z0-9_])(?:[A-Za-z]:[\\/]+(?![\[<])[^\\/\s`"<>|]+(?:[\\/]+[^\\/\s`"<>|]+)*|\\{2,}(?![\[<])[A-Za-z0-9._-]+\\+(?![\[<])[A-Za-z0-9.$_-]+(?:\\+[^\\\s`"<>|]+)*|/mnt/[A-Za-z]/(?:Users/)?[^/\s`"<>|]+(?:/[^/\s`"<>|]+)*|/home/[^/\s`"<>|]+(?:/[^/\s`"<>|]+)*))|sk-'
```

Expected result: no dataset diff, no new tracked tmp/artifact output, and no forbidden source references.

### Step 5: Write the phase report

Record:

- Source, test, config, script, and fixture moves.
- Lightweight test result.
- Dependency-boundary result.
- Commands used for conversion and dry-run.
- Explicit statement that no model training or model download occurred.
- Remaining work: compatibility wrappers, tracked tmp cleanup, active documentation cutover, and full-suite verification.

### Step 6: Commit

```powershell
git add contracts/tests/test_project_dependency_boundaries.py reports/reorganization/phase-b3-training-project.md
git commit -m "test: verify Agent and Training separation"
```

---

## Phase B3 Exit Criteria

Phase B3 is complete only when:

1. `training/src/sr2fpga_training/` is the sole Training implementation.
2. Training imports neither Agent nor `LLM.`.
3. Agent runtime dependencies contain no heavy ML stack.
4. Training lightweight tests pass without GPU, model files, vLLM, or network.
5. Training configs and scripts contain no private absolute paths or secrets.
6. Training output defaults to ignored `artifacts/training/`.
7. REQ2FILE provenance and no-pass-credit rules are enforced.
8. Existing released datasets are unchanged.
9. Cross-project boundary tests pass.
10. The phase report is committed and the worktree is clean.
