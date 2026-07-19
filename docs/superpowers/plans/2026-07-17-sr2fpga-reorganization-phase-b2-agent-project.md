# SR2FPGA Repository Reorganization Phase B2: Agent Project Migration Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Move project generation, System-HIS validation, tool orchestration, repair, trajectory recording, and Agent tests into an independently installable `agent/` project without changing SR2FPGA behavior.

**Architecture:** `agent/src/sr2fpga_agent/` becomes the sole Agent implementation. It reads language-neutral files from root `contracts/`, writes runtime output under root `artifacts/`, and exposes console entry points. A temporary legacy namespace shim keeps `LLM.src.sr2fpga_agent` imports usable until Phase B4 completes the compatibility cycle.

**Tech Stack:** Python 3.11, setuptools, pytest, PyYAML, certifi, Verilator, Icarus Verilog, Yosys, OpenXC7/nextpnr.

**Depends on:** Phase B1 contract registry, canonical task catalog, and artifact policy.

**Must not do:** Change generation semantics, weaken validators, change task tiers, regenerate datasets, or make L4 default for Line B.

---

## Task 1: Create the Agent package contract and boundary tests

**Files:**
- Create: `agent/pyproject.toml`
- Create: `agent/tests/test_agent_package_boundary.py`
- Create: `agent/tests/test_repository_paths.py`
- Create later in this task: `agent/src/sr2fpga_agent/repository_paths.py`
- Modify: `pytest.ini`

### Step 1: Write failing package-boundary tests

`agent/tests/test_agent_package_boundary.py` must assert:

1. `agent/pyproject.toml` parses with `tomllib`.
2. Project name is `sr2fpga-agent`.
3. Python requirement is at least 3.11.
4. Runtime dependencies contain PyYAML and certifi.
5. Runtime dependencies do not contain torch, transformers, datasets, peft, trl, bitsandbytes, accelerate, or vllm.
6. Console scripts map to:
   - `sr2fpga-agent = sr2fpga_agent.cli:main`
   - `sr2fpga-runner = sr2fpga_agent.runner:main`
   - `sr2fpga-baseline-report = sr2fpga_agent.baseline_report:main`
   - `sr2fpga-req2file-eval = sr2fpga_agent.req2file_eval:main`
   - `sr2fpga-task-evidence = sr2fpga_agent.task_evidence:main`
7. The canonical package contains no import whose module starts with the heavy Training dependency names above.
8. The canonical package contains no import beginning with `LLM.`.

Implement the import scan with `ast.walk`, not regular expressions.

### Step 2: Write failing repository-path tests

Define the required API before implementation:

```python
from sr2fpga_agent.repository_paths import RepositoryPaths, discover_repository_root
```

Tests must cover:

- `SR2FPGA_REPO_ROOT` environment override.
- Upward discovery from a nested file beneath `agent/src/`.
- Rejection when `contracts/manifest.json` is absent.
- `RepositoryPaths.contracts_dir`.
- `RepositoryPaths.task_catalog`.
- `RepositoryPaths.agent_scripts_dir`.
- `RepositoryPaths.artifacts_dir`.
- No use of current working directory as implicit authority.

### Step 3: Run and confirm failure

```powershell
python -m pytest agent/tests/test_agent_package_boundary.py agent/tests/test_repository_paths.py -q
```

Expected result: package metadata and canonical module missing.

### Step 4: Add `agent/pyproject.toml`

Use setuptools with a `src` layout:

```toml
[build-system]
requires = ["setuptools>=75", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "sr2fpga-agent"
version = "0.1.0"
description = "SR2FPGA project generation and tool-verification agent"
requires-python = ">=3.11"
dependencies = [
  "certifi>=2024.8.30",
  "PyYAML>=6.0.2"
]

[project.optional-dependencies]
dev = ["pytest>=8.0"]

[project.scripts]
sr2fpga-agent = "sr2fpga_agent.cli:main"
sr2fpga-runner = "sr2fpga_agent.runner:main"
sr2fpga-baseline-report = "sr2fpga_agent.baseline_report:main"
sr2fpga-req2file-eval = "sr2fpga_agent.req2file_eval:main"
sr2fpga-task-evidence = "sr2fpga_agent.task_evidence:main"

[tool.setuptools.packages.find]
where = ["src"]
```

### Step 5: Implement repository-root discovery

`repository_paths.py` must:

1. Accept an optional start path.
2. Check `SR2FPGA_REPO_ROOT` first.
3. Resolve the candidate and require `contracts/manifest.json`.
4. Otherwise walk the resolved start path and its parents until the marker exists.
5. Raise a descriptive `FileNotFoundError` if no marker exists.
6. Return a frozen `RepositoryPaths` dataclass with properties for root, contracts, task catalog, agent scripts, artifacts, reports, and datasets.
7. Never silently fall back to `Path.cwd()` unless it was explicitly passed as `start`.

### Step 6: Update root pytest discovery

Set `pytest.ini` to:

```ini
[pytest]
pythonpath =
    .
    agent/src
    training/src
```

`training/src` may not exist until Phase B3; pytest accepts the path.

### Step 7: Run focused tests

```powershell
python -m pytest agent/tests/test_agent_package_boundary.py agent/tests/test_repository_paths.py -q
```

The boundary scan may still fail until Task 2 moves the package. The path tests must pass.

### Step 8: Commit

```powershell
git add agent/pyproject.toml agent/src/sr2fpga_agent/repository_paths.py agent/tests/test_agent_package_boundary.py agent/tests/test_repository_paths.py pytest.ini
git commit -m "build: define standalone Agent project"
```

---

## Task 2: Move the Agent source and REQ2FILE evaluator

**Files:**
- Move: `LLM/src/sr2fpga_agent/` to `agent/src/sr2fpga_agent/`
- Move: `LLM/src/req2file_eval.py` to `agent/src/sr2fpga_agent/req2file_eval.py`
- Preserve: `agent/src/sr2fpga_agent/repository_paths.py`
- Create: `LLM/src/sr2fpga_agent/__init__.py` as a temporary namespace shim
- Modify imports throughout: `agent/src/sr2fpga_agent/**/*.py`

### Step 1: Record the pre-move public surface

Run:

```powershell
python -c "import LLM.src.sr2fpga_agent as p; print(sorted(name for name in dir(p) if not name.startswith('_')))"
python -m LLM.src.sr2fpga_agent.runner --help
python -m LLM.src.req2file_eval --help
```

Save output in `artifacts/reorganization/phase-b2/public-surface-before.txt`. It is local evidence and must remain ignored.

### Step 2: Move with Git history

Use `git mv`, not copy-and-delete:

```powershell
New-Item -ItemType Directory -Force agent/src
Move-Item -LiteralPath agent/src/sr2fpga_agent/repository_paths.py -Destination agent/src/repository_paths.py
Remove-Item -LiteralPath agent/src/sr2fpga_agent
git mv LLM/src/sr2fpga_agent agent/src/sr2fpga_agent
Move-Item -LiteralPath agent/src/repository_paths.py -Destination agent/src/sr2fpga_agent/repository_paths.py
git mv LLM/src/req2file_eval.py agent/src/sr2fpga_agent/req2file_eval.py
git add -A agent/src LLM/src
```

Before running, check whether destination paths already exist and adapt the move order without overwriting files. The required final state is one canonical source tree only.

### Step 3: Rewrite canonical imports

Under `agent/src/sr2fpga_agent/`:

- Replace `from LLM.src.sr2fpga_agent...` with `from sr2fpga_agent...`.
- Replace `import LLM.src.sr2fpga_agent...` with canonical imports.
- Prefer existing relative imports if the file already uses them.
- Update `req2file_eval.py` to import Agent modules from `sr2fpga_agent`.
- Do not rename modules or public functions in this phase.

Use AST-based boundary tests to catch missed imports.

### Step 4: Add the temporary namespace shim

Create only `LLM/src/sr2fpga_agent/__init__.py` at the old package path. It must:

- Emit one `DeprecationWarning` stating the canonical import is `sr2fpga_agent`.
- Set package `__path__` to the canonical `agent/src/sr2fpga_agent` directory discovered relative to the repository root.
- Re-export the canonical package public names.
- Contain no Agent implementation.
- Be explicitly removed or reduced to documented wrappers after one compatibility release.

This shim allows old submodule imports such as `LLM.src.sr2fpga_agent.runner` to resolve canonical files without duplicating implementation.

### Step 5: Run import and CLI tests

```powershell
python -c "import sr2fpga_agent; import sr2fpga_agent.runner; import sr2fpga_agent.req2file_eval"
python -m sr2fpga_agent.runner --help
python -m sr2fpga_agent.req2file_eval --help
python -W default -c "import LLM.src.sr2fpga_agent.runner"
python -m pytest agent/tests/test_agent_package_boundary.py agent/tests/test_repository_paths.py -q
```

Expected result:

- Canonical imports pass.
- Both canonical CLIs show help without tool execution.
- Legacy import emits a deprecation warning and reaches canonical code.
- No `LLM.` import remains in canonical Agent source.

### Step 6: Commit

```powershell
git add agent/src LLM/src/sr2fpga_agent
git commit -m "refactor: move Agent implementation to standalone project"
```

---

## Task 3: Replace hard-coded parent indexing with repository paths

**Files:**
- Modify: `agent/src/sr2fpga_agent/agent.py`
- Modify: `agent/src/sr2fpga_agent/task_catalog.py`
- Modify: `agent/src/sr2fpga_agent/task_evidence.py`
- Modify any file found by the path audit
- Create: `agent/tests/test_agent_repository_resources.py`

### Step 1: Write failing resource-resolution tests

Tests must verify:

- Default task catalog resolves to `contracts/task-catalog/sr2fpga-task-catalog-v0.2.json`.
- OpenXC7 script resolves to `agent/scripts/openxc7_pnr.sh`.
- Task evidence source documents resolve from repository root.
- Default runtime output root resolves under `artifacts/`.
- Resolution works when the process current directory is a temporary directory outside the repository.

### Step 2: Audit hard-coded repository paths

Run:

```powershell
Get-ChildItem agent/src/sr2fpga_agent -Recurse -Filter *.py | Select-String -Pattern 'parents\[|Path\.cwd|/ "scripts"|/ "docs"|/ "configs"|/ "datasets"|/ "tmp"'
```

Classify every hit:

- Package-local resource.
- Repository-owned contract/config/script.
- Caller-provided runtime path.
- Test fixture.

Only repository-owned resources must use `RepositoryPaths`. Caller-provided paths remain explicit parameters.

### Step 3: Implement minimal replacements

Known required changes:

- `agent.py` must use `RepositoryPaths.agent_scripts_dir / "openxc7_pnr.sh"` instead of `parents[3]`.
- `task_catalog.py` must use `RepositoryPaths.task_catalog` instead of the docs copy.
- `task_evidence.py` must resolve repository evidence documents through `RepositoryPaths.root`.
- Defaults that currently write to root `tmp/` or mutable `datasets/` must resolve to `RepositoryPaths.artifacts_dir` unless explicitly overridden by the caller.

### Step 4: Run focused tests

```powershell
python -m pytest agent/tests/test_repository_paths.py agent/tests/test_agent_repository_resources.py -q
```

Expected result: pass from repository root and from a temporary current directory.

### Step 5: Commit

```powershell
git add agent/src/sr2fpga_agent agent/tests/test_agent_repository_resources.py
git commit -m "refactor: centralize Agent repository paths"
```

---

## Task 4: Move and canonicalize Agent tests

**Files:**
- Move most tests from `LLM/tests/` to `agent/tests/`
- Modify moved tests to import `sr2fpga_agent`
- Keep temporarily in `LLM/tests/` for Phase B3:
  - `test_prepare_dataset.py`
  - `test_training_dry_run.py`
  - `test_training_smoke_assets.py`
  - `test_serving_entrypoints.py`

### Step 1: Move tests with Git history

Move these Agent-owned groups:

- Every `test_sr2fpga_agent_*.py`.
- `test_req2file_eval.py`.
- `test_analyze_phase_d_h2_failures.py`.
- `test_sr2fpga_measurement_freeze.py`.
- `test_sr2fpga_paired_measurement.py`.
- `test_sr2fpga_phase_d_audit.py`.
- `test_sr2fpga_phase_d_integration.py`.
- `test_sr2fpga_task_catalog_v02.py`.
- `test_sr2fpga_task_evidence_v01.py`.

Use one PowerShell list and `git mv` each path. Do not move the four Training tests listed above.

### Step 2: Rewrite imports

In moved tests:

- Replace `LLM.src.sr2fpga_agent` with `sr2fpga_agent`.
- Replace `LLM.src.req2file_eval` with `sr2fpga_agent.req2file_eval`.
- Update monkeypatch strings and `patch()` targets as well as import statements.
- Update path fixtures from `LLM/src` to `agent/src`.
- Keep behavior assertions unchanged.

### Step 3: Add a source-of-truth test

Extend `test_agent_package_boundary.py` to assert:

- No Agent-owned test remains under `LLM/tests`.
- No canonical Agent test imports `LLM.`.
- `agent/src/sr2fpga_agent` is the only directory containing implementation files named `agent.py`, `runner.py`, and `recorder.py`.

### Step 4: Run Agent tests

```powershell
python -m pytest agent/tests -q
```

Expected result: all moved tests plus new boundary tests pass.

### Step 5: Run remaining legacy Training tests

```powershell
python -m pytest LLM/tests/test_prepare_dataset.py LLM/tests/test_training_dry_run.py LLM/tests/test_training_smoke_assets.py LLM/tests/test_serving_entrypoints.py -q
```

Expected result: same result as Phase A for these tests. Do not fix Training ownership in this task.

### Step 6: Commit

```powershell
git add agent/tests LLM/tests
git commit -m "test: move Agent coverage to Agent project"
```

---

## Task 5: Move Agent configs and scripts, then enforce artifact output roots

**Files:**
- Move: `configs/` to `agent/configs/`
- Move: `scripts/analyze_phase_d_h2_failures.py` to `agent/scripts/analyze_phase_d_h2_failures.py`
- Move: `scripts/audit_phase_d_pilot.py` to `agent/scripts/audit_phase_d_pilot.py`
- Move: `scripts/openxc7_pnr.sh` to `agent/scripts/openxc7_pnr.sh`
- Move or merge: `scripts/README.md` to `agent/scripts/README.md`
- Modify: `agent/configs/current/*.yaml`
- Create: `agent/tests/test_agent_config_policy.py`
- Modify script imports and documented invocations

### Step 1: Write failing config-policy tests

For every YAML file under `agent/configs/current/`, recursively inspect string values representing output paths. Assert default outputs do not begin with:

- `tmp/`
- `datasets/`
- `LLM/runs/`
- `LLM/checkpoints/`

Require active output roots to begin with `artifacts/agent/` or be null and supplied explicitly by the caller.

Also assert:

- Every active config resolves.
- Every script imports canonical `sr2fpga_agent`.
- `openxc7_pnr.sh` is executable in Git mode where supported.
- Archived and legacy configs are labeled non-default in their directory README.

### Step 2: Run and confirm failure

```powershell
python -m pytest agent/tests/test_agent_config_policy.py -q
```

### Step 3: Move configs and scripts

Use `git mv` and preserve `current`, `archive`, and `legacy` subdirectories. Update `agent/configs/README.md` to state:

- `current/` contains maintained examples.
- `archive/` is historical evidence and is not executed by default.
- `legacy/` is compatibility-only.
- Private overrides go in ignored `agent/configs/local/`.

### Step 4: Update active output paths only

For `agent/configs/current/*.yaml`:

- Replace runtime `tmp/...` roots with `artifacts/agent/runs/...`.
- Replace direct generation into `datasets/...` with `artifacts/agent/candidates/...`.
- Keep dataset release promotion as a separate explicit workflow.
- Preserve task sets, tiers, seeds, prompts, repair budgets, and tool settings.
- Do not rewrite archived experiment configs except to fix paths required for parsing.

### Step 5: Update script imports and paths

- Python scripts import `sr2fpga_agent`.
- Shell script path assumptions derive repository root from the script location or an explicit `SR2FPGA_REPO_ROOT`.
- OpenXC7 input/output paths remain caller-controlled.
- No script writes to tracked `tmp/` by default.

### Step 6: Run config and CLI tests

```powershell
python -m pytest agent/tests/test_agent_config_policy.py agent/tests/test_sr2fpga_agent_runner.py agent/tests/test_analyze_phase_d_h2_failures.py agent/tests/test_sr2fpga_phase_d_audit.py -q
python -m sr2fpga_agent.runner --config agent/configs/current/sr2fpga_deterministic_curriculum_smoke.example.yaml --run-id phase-b2-preflight --preflight
```

Expected result: tests and preflight pass; runtime output, if any, is under ignored `artifacts/agent/`.

### Step 7: Commit

```powershell
git add agent/configs agent/scripts configs scripts agent/tests/test_agent_config_policy.py agent/src/sr2fpga_agent
git commit -m "refactor: move Agent configs and scripts"
```

---

## Task 6: Verify independent Agent installation and behavior

**Files:**
- Create: `agent/tests/test_agent_cli_smoke.py`
- Create: `reports/reorganization/phase-b2-agent-project.md`
- Modify: `agent/README.md`

### Step 1: Add CLI smoke tests

Use `subprocess.run` with the current Python executable to verify:

- `python -m sr2fpga_agent.cli --help`.
- `python -m sr2fpga_agent.runner --help`.
- `python -m sr2fpga_agent.baseline_report --help`.
- `python -m sr2fpga_agent.req2file_eval --help`.
- `python -m sr2fpga_agent.task_evidence --help`.

Require exit code zero and a stable usage token. Do not invoke external EDA tools in CLI help tests.

### Step 2: Install Agent in editable mode

Use a dedicated local environment if Phase A defined one. Otherwise run:

```powershell
python -m pip install -e "agent[dev]"
```

Do not install Training dependencies.

### Step 3: Run the complete Agent suite

```powershell
python -m pytest agent/tests -q
```

Expected result: all pass.

### Step 4: Run deterministic preflight and smoke

```powershell
python -m sr2fpga_agent.runner --config agent/configs/current/sr2fpga_deterministic_curriculum_smoke.example.yaml --run-id phase-b2-agent-preflight --preflight
python -m sr2fpga_agent.runner --config agent/configs/current/sr2fpga_deterministic_curriculum_smoke.example.yaml --run-id phase-b2-agent-smoke
```

Verify:

- Summary and baseline report are created under `artifacts/agent/`.
- H0-H3 and L0-L3 fields remain present.
- Every episode contains `l4_open`, including `not_run` records.
- `not_run` is not counted as failure.
- No file changes under `datasets/` or tracked `tmp/`.

### Step 5: Verify legacy namespace behavior

```powershell
python -W default -m LLM.src.sr2fpga_agent.runner --help
```

Expected result: exit code zero plus one deprecation warning.

### Step 6: Run repository checks

```powershell
python -m pytest contracts/tests agent/tests -q
git diff --check
git status --short
git diff -- datasets
git status --short tmp
```

No dataset payload change is allowed. Existing tracked `tmp/` is still deferred to Phase B4; no new tracked tmp file is allowed.

### Step 7: Update Agent README and phase report

`agent/README.md` must document:

- Editable install.
- Canonical imports.
- Console commands.
- Config locations.
- Artifact output policy.
- External tool prerequisites.
- Legacy import warning.
- Explicit statement that Training is a separate project.

`reports/reorganization/phase-b2-agent-project.md` must record:

- Source and test moves.
- Canonical import and compatibility behavior.
- Agent test result.
- Deterministic smoke result.
- EDA tool versions used.
- Dataset and tmp cleanliness checks.
- Remaining dependency: Training and final cutover are not complete.

### Step 8: Commit

```powershell
git add agent/README.md agent/tests/test_agent_cli_smoke.py reports/reorganization/phase-b2-agent-project.md
git commit -m "test: verify standalone Agent project"
```

---

## Phase B2 Exit Criteria

Phase B2 is complete only when:

1. `agent/src/sr2fpga_agent/` is the only Agent implementation.
2. Canonical Agent source imports no `LLM.` module.
3. Agent runtime metadata contains no heavy Training dependencies.
4. All Agent tests pass from `agent/tests/`.
5. Canonical CLI help and deterministic smoke pass.
6. Root contracts and canonical task catalog resolve independently of current working directory.
7. Active Agent configs write only under ignored `artifacts/` by default.
8. Existing dataset releases are unchanged.
9. Legacy Agent imports work with a deprecation warning.
10. The phase report is committed and the worktree is clean.
