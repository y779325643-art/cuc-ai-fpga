# SR2FPGA Repository Reorganization Phase B4: Compatibility, Cutover, and Cleanup Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Finish the repository cutover by adding tested legacy forwarders, updating active documentation, retiring tracked `tmp/` content after backup verification, and proving the reorganized monorepo preserves behavior.

**Architecture:** `agent/` and `training/` are canonical executable projects; `contracts/` is the shared data boundary; `LLM/` contains forwarding compatibility only. Active documentation and examples use canonical commands. Historical dated plans remain historically accurate. Curated evidence may live under `reports/`, while runtime output lives under ignored `artifacts/`.

**Tech Stack:** Python 3.11, Bash, PowerShell, pytest, Git.

**Depends on:** Phases A and B1-B3 completed with clean commits.

**Safety rule:** No tracked or untracked `tmp/` content is removed until the Phase A backup manifest, checksums, and restore test have been reverified in the implementation session. No cleanup command may target a path outside the verified repository root.

---

## Task 1: Add explicit Python compatibility wrappers

**Files:**
- Create or modify: `LLM/README.md`
- Create: `LLM/src/_compat.py`
- Modify: `LLM/src/sr2fpga_agent/__init__.py`
- Create: `LLM/src/sr2fpga_agent/runner.py`
- Create: `LLM/src/sr2fpga_agent/cli.py`
- Create: `LLM/src/sr2fpga_agent/baseline_report.py`
- Create: `LLM/src/sr2fpga_agent/task_evidence.py`
- Create: `LLM/src/req2file_eval.py`
- Create: `LLM/src/prepare_dataset.py`
- Create: `LLM/src/training_dry_run.py`
- Create: `LLM/src/train_lora.py`
- Create: `LLM/src/merge_lora.py`
- Create: `compatibility_tests/test_python_entrypoints.py`
- Create: `compatibility_tests/test_no_duplicate_logic.py`

### Step 1: Write failing entrypoint tests

Use `subprocess.run` with the current Python executable. Test these documented old commands:

- `python -m LLM.src.sr2fpga_agent.runner --help`
- `python -m LLM.src.sr2fpga_agent.cli --help`
- `python -m LLM.src.req2file_eval --help`
- `python LLM/src/prepare_dataset.py --help`
- `python LLM/src/training_dry_run.py --help`
- `python LLM/src/train_lora.py --help`
- `python LLM/src/merge_lora.py --help`

For each command require:

1. Exit code zero.
2. Stderr contains `DEPRECATED`.
3. Stderr names the exact canonical replacement.
4. Stdout contains the same stable usage token as the canonical command.
5. The wrapper does not invoke external tools, models, or network for `--help`.

Also test legacy imports for representative non-entrypoint Agent modules:

```python
import LLM.src.sr2fpga_agent.recorder
import LLM.src.sr2fpga_agent.system_his_checker
```

They must resolve canonical implementation and emit at most one package-level warning per process.

### Step 2: Write the duplicate-logic test

Parse every Python file under `LLM/src`. Permit only:

- Imports.
- Constants for replacement command text.
- A `main` function that delegates.
- `if __name__ == "__main__"`.
- Namespace path forwarding in the legacy Agent package.
- Warning emission.

Reject classes and business functions named like canonical generation, validation, training, or repair functions. Require each wrapper to remain below 80 non-blank lines.

### Step 3: Run and confirm failure

```powershell
python -m pytest compatibility_tests/test_python_entrypoints.py compatibility_tests/test_no_duplicate_logic.py -q
```

### Step 4: Implement `LLM/src/_compat.py`

Provide two focused helpers:

```python
def warn_replacement(old_command: str, new_command: str) -> None:
    ...

def run_module(module_name: str, old_command: str, new_command: str) -> None:
    ...
```

Requirements:

- Print exactly one concise `DEPRECATED: <old> -> <new>` line to stderr per invocation.
- Add `agent/src` and `training/src` to `sys.path` only when executing a legacy file directly and the canonical package is not installed.
- Delegate with `runpy.run_module(module_name, run_name="__main__")`.
- Preserve `sys.argv`.
- Never catch or rewrite canonical exit codes.
- Contain no application logic.

### Step 5: Implement explicit wrappers

Each wrapper imports the helper and delegates to one canonical module. Exact replacements:

| Old command | Canonical replacement |
|---|---|
| `python -m LLM.src.sr2fpga_agent.runner` | `python -m sr2fpga_agent.runner` |
| `python -m LLM.src.sr2fpga_agent.cli` | `python -m sr2fpga_agent.cli` |
| `python -m LLM.src.req2file_eval` | `python -m sr2fpga_agent.req2file_eval` |
| `python LLM/src/prepare_dataset.py` | `python -m sr2fpga_training.prepare_dataset` |
| `python LLM/src/training_dry_run.py` | `python -m sr2fpga_training.training_dry_run` |
| `python LLM/src/train_lora.py` | `python -m sr2fpga_training.train_lora` |
| `python LLM/src/merge_lora.py` | `python -m sr2fpga_training.merge_lora` |

The legacy Agent package `__path__` forwarding from Phase B2 remains for non-entrypoint imports. Explicit CLI wrapper files take precedence for documented commands.

### Step 6: Run compatibility tests

```powershell
python -m pytest compatibility_tests/test_python_entrypoints.py compatibility_tests/test_no_duplicate_logic.py -q
```

Expected result: pass.

### Step 7: Commit

```powershell
git add LLM/README.md LLM/src compatibility_tests/test_python_entrypoints.py compatibility_tests/test_no_duplicate_logic.py
git commit -m "refactor: add Python compatibility entrypoints"
```

---

## Task 2: Add shell compatibility wrappers and legacy dependency guidance

**Files:**
- Create wrapper scripts under `LLM/scripts/` for every moved script from `training/scripts/`
- Modify: `LLM/requirements.txt`
- Create: `compatibility_tests/test_shell_entrypoints.py`
- Create: `compatibility_tests/test_legacy_dependency_file.py`

### Step 1: Write failing shell-wrapper tests

For every retained old shell path:

1. Require LF line endings.
2. Require a `DEPRECATED` message on stderr.
3. Require the message to name `training/scripts/<same-name>`.
4. Run with a fake downstream executable or a harmless `--help` path where supported.
5. Require argument forwarding without reordering.
6. Reject copied implementation blocks.

Cover at least:

- `LLM/scripts/setup_server.sh`
- `LLM/scripts/serve_qwen_vllm.sh`
- `LLM/scripts/serve_vllm.sh`
- `LLM/scripts/train_lora.sh`
- `LLM/scripts/merge_lora.sh`
- `LLM/scripts/test_api.sh`

### Step 2: Implement thin shell wrappers

Each wrapper must:

- Use `#!/usr/bin/env bash` and `set -euo pipefail`.
- Resolve repository root from the wrapper location.
- Print one deprecation line to stderr.
- Execute `training/scripts/<same-name>` with `"$@"`.
- Contain no environment defaults or vLLM/training logic.

### Step 3: Replace the mixed legacy requirements file

`LLM/requirements.txt` becomes a deprecated aggregate install file containing comments and editable references to the two projects:

```text
# Deprecated compatibility installer.
# Prefer: python -m pip install -e "agent[dev]"
# Training extras are optional and GPU/platform dependent.
-e ../agent
-e ../training
```

Do not force the heavy training or serving extras through the legacy aggregate. Document explicit `training[train]` and `training[serve]` commands in `LLM/README.md`.

### Step 4: Run focused tests

```powershell
python -m pytest compatibility_tests/test_shell_entrypoints.py compatibility_tests/test_legacy_dependency_file.py training/tests/test_serving_entrypoints.py -q
```

### Step 5: Commit

```powershell
git add LLM/scripts LLM/requirements.txt LLM/README.md compatibility_tests/test_shell_entrypoints.py compatibility_tests/test_legacy_dependency_file.py
git commit -m "refactor: add shell compatibility entrypoints"
```

---

## Task 3: Cut active documentation and automation over to canonical paths

**Files:**
- Modify: `README.md`
- Modify: `CLAUDE.md`
- Modify: `docs/README.md`
- Modify: `docs/current-status.md`
- Modify any non-dated active guide found by the audit
- Create: `docs/migration/llm-to-agent-training.md`
- Create: `compatibility_tests/test_active_documentation_paths.py`

### Step 1: Write a failing active-documentation test

Define active documents as:

- Root `README.md` and `CLAUDE.md`.
- `docs/README.md`.
- `docs/current-status.md`.
- Non-dated guides linked from `docs/README.md`.
- Current CI/workflow files if present.
- Current config READMEs.

Assert active documents:

- Use canonical `agent/` and `training/` paths.
- Do not present old `LLM/` commands as primary commands.
- May mention old commands only inside a deprecation or migration section.
- Link to existing paths.
- Document `contracts/`, `datasets/`, and `artifacts/` ownership.
- State that `not_run` is distinct from failure and Training does not import Agent.

Do not scan dated files under `docs/superpowers/plans/` or `docs/superpowers/specs/` as current command documentation.

### Step 2: Run and confirm failure

```powershell
python -m pytest compatibility_tests/test_active_documentation_paths.py -q
```

### Step 3: Update the root repository map

Root `README.md` must include:

- The monorepo map.
- Agent quick start.
- Training lightweight quick start and optional heavy extras.
- Contract and dataset policy.
- Artifact output policy.
- Legacy migration link.
- Current verification commands.

`CLAUDE.md` must use the same canonical commands and ownership boundaries used by Codex. Do not maintain conflicting agent instructions.

### Step 4: Add the migration guide

`docs/migration/llm-to-agent-training.md` must include:

- Old-to-new path table.
- Old-to-new command table.
- Install commands.
- Import migration examples.
- Config relocation table.
- One-cycle compatibility policy.
- Planned removal prerequisite: explicit later approval after active usage review.
- No date promise that has not been approved.

### Step 5: Preserve historical documents

Do not rewrite old commands inside dated plans/specs merely to make them look current. If a dated document is linked as evidence, add a short current navigation note outside it.

### Step 6: Run documentation tests and link audit

```powershell
python -m pytest compatibility_tests/test_active_documentation_paths.py -q
Get-ChildItem README.md,CLAUDE.md,docs -Recurse -File -Include *.md | Select-String -Pattern 'LLM/src|LLM/scripts|configs/current' | Select-Object Path,LineNumber,Line
```

Review every hit and classify it as active, migration documentation, or historical evidence.

### Step 7: Commit

```powershell
git add README.md CLAUDE.md docs/README.md docs/current-status.md docs/migration compatibility_tests/test_active_documentation_paths.py
git commit -m "docs: cut over to Agent and Training projects"
```

---

## Task 4: Inventory and retire tracked `tmp/` content

**Files:**
- Create: `contracts/tools/inventory_tracked_tmp.py`
- Create: `compatibility_tests/test_tmp_retirement.py`
- Create: `reports/reorganization/legacy-tmp-inventory.json`
- Create as needed: `reports/evidence/legacy-runs/<run-id>/`
- Modify active evidence references that point to moved run artifacts
- Remove tracked `tmp/` content only after the approval gate

### Step 1: Reverify the Phase A backup

The operator or Codex executor must explicitly supply the external backup root from the noncommitted Phase A handoff. Pass it through `-PhaseABackupRoot` or `SR2FPGA_PHASE_A_BACKUP_ROOT`; the script prompts only when both are absent. The root is not stored in `manifest.json` or any committed document. This block is a mandatory safety gate: do not execute `git mv`, `git rm`, or any other command that moves or deletes `tmp/` content unless it completes successfully.

```powershell
param(
    [string]$PhaseABackupRoot = $env:SR2FPGA_PHASE_A_BACKUP_ROOT
)

$ErrorActionPreference = "Stop"

$repoCandidate = (git rev-parse --show-toplevel).Trim()
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($repoCandidate)) {
    throw "Run the Phase B4 backup gate from the repository worktree"
}
$repo = (Resolve-Path -LiteralPath $repoCandidate).Path

if ([string]::IsNullOrWhiteSpace($PhaseABackupRoot)) {
    $PhaseABackupRoot = Read-Host "Phase A external backup root from the noncommitted handoff"
}
if ([string]::IsNullOrWhiteSpace($PhaseABackupRoot)) { throw "Backup root input is required" }
$backup = (Resolve-Path -LiteralPath $PhaseABackupRoot).Path

$comparison = [System.StringComparison]::OrdinalIgnoreCase
$repoPrefix = $repo.TrimEnd([char[]]@('\', '/')) + [IO.Path]::DirectorySeparatorChar
if ($backup.Equals($repo, $comparison) -or $backup.StartsWith($repoPrefix, $comparison)) {
    throw "External backup root resolves inside the repository"
}

$requiredFiles = @(
    "repository-state.json",
    "tracked-working-tree.patch",
    "staged-index.patch",
    "status.porcelain-v2.z",
    "worktrees.txt",
    "manifest.json",
    "checksums.sha256",
    "verification.json",
    "restore-instructions.md"
)
$requiredDirectories = @("workspace", "restore-test")
foreach ($relativePath in $requiredFiles) {
    if (-not (Test-Path -LiteralPath (Join-Path $backup $relativePath) -PathType Leaf)) {
        throw "Missing Phase A backup file: $relativePath"
    }
}
foreach ($relativePath in $requiredDirectories) {
    if (-not (Test-Path -LiteralPath (Join-Path $backup $relativePath) -PathType Container)) {
        throw "Missing Phase A backup directory: $relativePath"
    }
}

$strictUtf8 = [System.Text.UTF8Encoding]::new($false, $true)
$manifestPath = Join-Path $backup "manifest.json"
$verificationPath = Join-Path $backup "verification.json"
$checksumPath = Join-Path $backup "checksums.sha256"
$manifest = [IO.File]::ReadAllText($manifestPath, $strictUtf8) | ConvertFrom-Json
$verification = [IO.File]::ReadAllText($verificationPath, $strictUtf8) | ConvertFrom-Json
if ($manifest.schema_version -ne "sr2fpga-workspace-backup-v1") { throw "Unexpected backup manifest schema" }
if ($verification.schema_version -ne "sr2fpga-workspace-backup-verification-v1") { throw "Unexpected backup verification schema" }
if ($verification.status -ne "pass") { throw "Phase A verification status is not pass" }
if ([int]$verification.hash_failures -ne 0 -or [int]$verification.structured_parse_failures -ne 0) {
    throw "Phase A verification reports failures"
}
if ([int]$verification.file_count -ne [int]$manifest.file_count -or [long]$verification.byte_count -ne [long]$manifest.byte_count) {
    throw "Manifest and verification totals disagree"
}

function Resolve-ContainedBackupPath {
    param([string]$Root, [string]$RelativePath)
    $rootPrefix = $Root.TrimEnd([char[]]@('\', '/')) + [IO.Path]::DirectorySeparatorChar
    $platformPath = $RelativePath.Replace([char]'/', [IO.Path]::DirectorySeparatorChar)
    $candidate = [IO.Path]::GetFullPath((Join-Path $Root $platformPath))
    if (-not $candidate.StartsWith($rootPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Backup manifest path escapes its root: $RelativePath"
    }
    return $candidate
}

function Assert-ChecksumLedger {
    param([object[]]$Records, [string[]]$Lines)
    if ($Lines.Count -ne $Records.Count) {
        throw "Checksum ledger line count mismatch: expected $($Records.Count), got $($Lines.Count)"
    }
    for ($index = 0; $index -lt $Records.Count; $index++) {
        if ([string]::IsNullOrEmpty($Lines[$index])) {
            throw "Blank checksum ledger line at $($index + 1)"
        }
        $expectedLine = ([string]$Records[$index].sha256) + "  " + ([string]$Records[$index].path)
        if (-not [string]::Equals($Lines[$index], $expectedLine, [System.StringComparison]::Ordinal)) {
            throw "Checksum ledger mismatch at line $($index + 1)"
        }
    }
}

$workspaceRoot = (Resolve-Path -LiteralPath (Join-Path $backup "workspace")).Path
$records = @($manifest.files)
if ($records.Count -ne [int]$manifest.file_count) { throw "Manifest record count mismatch" }
$checksumLines = [IO.File]::ReadAllLines($checksumPath, $strictUtf8)
Assert-ChecksumLedger -Records $records -Lines $checksumLines

$integrityFailures = [System.Collections.Generic.List[string]]::new()
foreach ($record in $records) {
    $source = Resolve-ContainedBackupPath -Root $workspaceRoot -RelativePath ([string]$record.path)
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
        $integrityFailures.Add("missing: $($record.path)")
        continue
    }
    $item = Get-Item -LiteralPath $source
    $hash = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($item.Length -ne [long]$record.length -or $hash -ne [string]$record.sha256) {
        $integrityFailures.Add("content: $($record.path)")
    }
}
$workspaceFiles = @(Get-ChildItem -LiteralPath $workspaceRoot -Recurse -File -Force)
if ($workspaceFiles.Count -ne [int]$manifest.file_count) { $integrityFailures.Add("workspace file count") }
if ([long](($workspaceFiles | Measure-Object Length -Sum).Sum) -ne [long]$manifest.byte_count) {
    $integrityFailures.Add("workspace byte count")
}
if ($integrityFailures.Count -ne 0) { throw "Backup integrity recheck failed: $($integrityFailures -join ', ')" }

$restoreRoot = (Resolve-Path -LiteralPath (Join-Path $backup "restore-test")).Path
$restoreSamples = @($verification.restore_samples)
if ($restoreSamples.Count -eq 0) { throw "Verification contains no restore samples" }
foreach ($sample in $restoreSamples) {
    $record = @($records | Where-Object { $_.path -eq $sample })
    if ($record.Count -ne 1) { throw "Restore sample is not unique in manifest: $sample" }
    $restored = Resolve-ContainedBackupPath -Root $restoreRoot -RelativePath ([string]$sample)
    if (-not (Test-Path -LiteralPath $restored -PathType Leaf)) { throw "Missing restore sample: $sample" }
    $restoredHash = (Get-FileHash -LiteralPath $restored -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($restoredHash -ne [string]$record[0].sha256) { throw "Restore sample mismatch: $sample" }
}

$recheck = [ordered]@{
    schema_version = "sr2fpga-phase-b4-backup-recheck-v1"
    checked_utc = [DateTime]::UtcNow.ToString("o")
    repository = $repo
    backup_root = $backup
    file_count = [int]$manifest.file_count
    byte_count = [long]$manifest.byte_count
    checksum_line_count = $checksumLines.Count
    restore_sample_count = $restoreSamples.Count
    integrity_failure_count = 0
    status = "pass"
}
$recheckPath = Join-Path $repo "artifacts/reorganization/phase-b4/backup-recheck.json"
New-Item -ItemType Directory -Path (Split-Path -Parent $recheckPath) -Force | Out-Null
[System.IO.File]::WriteAllText(
    $recheckPath,
    ($recheck | ConvertTo-Json -Depth 4) + [Environment]::NewLine,
    [System.Text.UTF8Encoding]::new($false)
)
```

Expected: the gate writes ignored `artifacts/reorganization/phase-b4/backup-recheck.json` with `status=pass`. Stop if any check fails, and do not accept a backup root inferred from `manifest.json`.

### Step 2: Write the failing retirement test

The test must assert after cleanup:

- `git ls-files tmp` returns no path.
- Root `.gitignore` contains `/tmp/`.
- Canonical configs contain no default output under `tmp/`.
- Active documentation contains no live evidence reference under `tmp/`.
- `reports/reorganization/legacy-tmp-inventory.json` exists and lists every path tracked before cleanup.
- Every inventory record has one disposition:
  - `moved_to_curated_reports`
  - `external_backup_only`
- Every moved record names an existing destination.
- Every external-only record names the verified backup manifest, not an invented repository path.

### Step 3: Implement the inventory tool

`inventory_tracked_tmp.py` must:

1. Resolve the repository root and require `.git`.
2. Read `git ls-files -s -- tmp`.
3. Record path, Git mode, blob object ID, and blob size from `git cat-file -s`.
4. Accept a JSON classification map of source run roots to `moved_to_curated_reports`; default all other paths to `external_backup_only`.
5. Reject a classification destination outside `reports/evidence/legacy-runs/`.
6. Write deterministic sorted JSON.
7. Never delete or move files itself.

### Step 4: Classify evidence conservatively

Use active, non-dated evidence ledgers and reports to identify tracked `tmp/sr2fpga_runs/<run-id>` roots that remain necessary for current claims.

For each referenced tracked run, add a proposed source-to-destination entry to the classification map, but do not move it yet. The proposed destination is `reports/evidence/legacy-runs/<run-id>/` and must include only the minimum complete auditable set: labels, trajectory, measured QoR, tool versions, required logs, and summaries. Identify active references that will need updating. Do not propose caches, duplicated generated files, zip handoffs, PDFs, raw prompt dumps, or scratch outputs for promotion merely because they are tracked.

All unreferenced tracked tmp files receive `external_backup_only` disposition. Historical dated documents may retain original `tmp/` paths as historical text; the inventory maps those paths to the external backup.

### Step 5: Generate and review the pre-move inventory

Run the tool before any `git mv` or `git rm`, then manually inspect:

- Total record count equals pre-cleanup `git ls-files tmp | Measure-Object` count.
- Every moved run has a destination.
- No source path is omitted.
- No secret-bearing raw file is promoted into `reports/`.

### Step 6: Obtain explicit cleanup approval

Present the inventory totals:

- Number moved to curated reports.
- Number retained only in external backup.
- Total tracked bytes to remove.
- Backup path and recheck status.

Do not continue until the user explicitly approves removal against this inventory.

### Step 7: Move curated evidence and retire the remaining tracked tmp

After approval, use `git mv` for each approved classification-map entry, update the identified active references, and verify every destination contains the required audit files. Then verify the remaining tmp target one final time:

```powershell
$repo = (Resolve-Path -LiteralPath ((git rev-parse --show-toplevel).Trim())).Path
$recheckPath = Join-Path $repo "artifacts/reorganization/phase-b4/backup-recheck.json"
$strictUtf8 = [System.Text.UTF8Encoding]::new($false, $true)
$recheck = [IO.File]::ReadAllText($recheckPath, $strictUtf8) | ConvertFrom-Json
if ($recheck.status -ne "pass" -or $recheck.repository -ne $repo) {
    throw "The mandatory Phase B4 backup gate has not passed for this repository"
}
$tmpPath = (Resolve-Path -LiteralPath tmp).Path
if (-not $tmpPath.StartsWith($repo + [IO.Path]::DirectorySeparatorChar)) { throw "tmp is outside repository" }
git rm -r -- tmp
```

The `git rm` removes only tracked content from the migration branch. Untracked local content in the main dirty workspace was already backed up and is handled by the separate Phase A recovery operation; do not cross-delete between worktrees.

### Step 8: Run retirement tests

```powershell
python -m pytest compatibility_tests/test_tmp_retirement.py -q
git ls-files tmp
git status --short
```

Expected result: no tracked tmp path.

### Step 9: Commit cleanup separately

```powershell
git add reports/reorganization/legacy-tmp-inventory.json reports/evidence compatibility_tests/test_tmp_retirement.py contracts/tools/inventory_tracked_tmp.py
git add -u tmp
git commit -m "chore: retire tracked temporary artifacts"
```

---

## Task 5: Run full acceptance verification

**Files:**
- Create: `reports/reorganization/final-verification.md`
- Modify only when verification exposes a real defect in migrated code or tests

### Step 1: Verify Git and package boundaries

```powershell
git status --short
git diff --check
git ls-files tmp
$trackedArtifacts = @(git ls-files artifacts | Where-Object { $_ -ne "artifacts/README.md" })
if ($trackedArtifacts.Count -ne 0) { throw "Tracked runtime artifacts found: $($trackedArtifacts -join ', ')" }
python -m pytest contracts/tests agent/tests training/tests compatibility_tests -q
```

Expected result:

- Clean before generated smoke output.
- No whitespace errors.
- No tracked `tmp/` path and no tracked runtime file under `artifacts/`; the policy README is allowed.
- All focused suites pass.

### Step 2: Run the compatibility suite independently

```powershell
python -m pytest compatibility_tests -q
```

Every documented old command must delegate and print its replacement.

### Step 3: Run the clean baseline-equivalent suite

After test migration, the old single path no longer contains all tests. Use:

```powershell
python -m pytest contracts/tests agent/tests training/tests compatibility_tests -q
```

Compare total tests and subtests with the Phase A baseline of 905 tests and 349 subtests. The reorganized suite must preserve all original assertions and add migration coverage. A lower count requires a named, reviewed explanation; silently losing tests is a blocker.

### Step 4: Run deterministic Agent preflight and smoke

```powershell
python -m sr2fpga_agent.runner --config agent/configs/current/sr2fpga_deterministic_curriculum_smoke.example.yaml --run-id reorganization-final-preflight --preflight
python -m sr2fpga_agent.runner --config agent/configs/current/sr2fpga_deterministic_curriculum_smoke.example.yaml --run-id reorganization-final-smoke
```

Verify the run under `artifacts/agent/runs/reorganization-final-smoke/`:

- H0-H3 present.
- L0-L3 verdicts preserve semantics.
- L4-open record present.
- `not_run` remains separate from fail.
- Toolchain environment failures remain separate from model failures.
- Summary and baseline report render.

Do not require real L4 if the configured policy selects `not_run`. If OpenXC7 is available and the representative policy selects it, archive the local report under artifacts and report the result without changing the default Line B policy.

### Step 5: Run lightweight Training smoke

```powershell
python -m sr2fpga_training.prepare_dataset --input training/tests/fixtures/smoke_verilog_raw.jsonl --output artifacts/training/prepared-data/reorganization-smoke/chat.jsonl
python -m sr2fpga_training.training_dry_run --train-file artifacts/training/prepared-data/reorganization-smoke/chat.jsonl --max-seq-length 2048
```

Use actual preserved CLI flag names. Do not train or download a model.

### Step 6: Revalidate contracts and datasets

```powershell
python -m pytest contracts/tests/test_dataset_release_policy.py contracts/tests/test_contract_fixtures.py contracts/tests/test_project_dependency_boundaries.py -q
python contracts/tools/build_dataset_inventory.py --root . --release sr2fpga_rtl_v1 --release sr2fpga_phase_d_control_v1 --release sr2fpga_phase_d_v1
git diff --exit-code -- datasets/manifests
git diff --exit-code -- datasets/sr2fpga_rtl_v1 datasets/sr2fpga_rtl_v1_exports datasets/sr2fpga_phase_d_control_v1 datasets/sr2fpga_phase_d_control_v1_exports datasets/sr2fpga_phase_d_v1 datasets/sr2fpga_phase_d_v1_exports
```

Expected result: inventories reproduce and payload bytes remain unchanged.

### Step 7: Scan for secrets, private paths, and stale active imports

```powershell
Get-ChildItem agent,training,contracts,compatibility_tests -Recurse -File | Select-String -Pattern 'sk-[A-Za-z0-9]|(?i:(?<![A-Za-z0-9_])(?:[A-Za-z]:[\\/]+(?![\[<])[^\\/\s`"<>|]+(?:[\\/]+[^\\/\s`"<>|]+)*|\\{2,}(?![\[<])[A-Za-z0-9._-]+\\+(?![\[<])[A-Za-z0-9.$_-]+(?:\\+[^\\\s`"<>|]+)*|/mnt/[A-Za-z]/(?:Users/)?[^/\s`"<>|]+(?:/[^/\s`"<>|]+)*|/home/[^/\s`"<>|]+(?:/[^/\s`"<>|]+)*))|from LLM\.|import LLM\.'
```

Allowed hits:

- None in canonical source or configs.
- `LLM.` only inside compatibility tests or migration documentation.
- No API key values anywhere.

### Step 8: Write final verification report

`reports/reorganization/final-verification.md` must include:

- Baseline commit and migration head.
- Commit list by phase.
- Focused and full test counts.
- Agent deterministic smoke result and artifact path.
- Training conversion/dry-run result.
- Compatibility command matrix.
- Contract and dataset checksum result.
- Tracked tmp count: zero.
- Secret/private-path scan result.
- Known residuals, including one-cycle `LLM/` compatibility.
- Explicit `APPROVED` or `NOT APPROVED` verdict.

Only write `APPROVED` if every required acceptance check passed.

### Step 9: Commit the verification report

```powershell
git add reports/reorganization/final-verification.md
git commit -m "test: verify repository reorganization"
```

---

## Task 6: Finish and publish the migration branch

**Files:**
- No new implementation files expected

### Step 1: Run final fresh verification

```powershell
python -m pytest contracts/tests agent/tests training/tests compatibility_tests -q
git status --short
git log --oneline --decorate -15
```

Expected result: tests pass and worktree is clean.

### Step 2: Request code review

Use `superpowers:requesting-code-review`. Review must focus on:

- No lost tests.
- No duplicated implementation under `LLM/`.
- Correct dependency direction.
- Dataset immutability.
- Tracked tmp retirement audit.
- Compatibility behavior.
- Path handling on Windows and WSL.

Address findings with `superpowers:receiving-code-review` and rerun full verification.

### Step 3: Finish the branch

Use `superpowers:finishing-a-development-branch`. Do not merge into the dirty local `develop` worktree directly.

Preferred integration:

1. Push the verified feature branch.
2. Open a reviewable PR against current remote `develop`.
3. Let CI run focused and full suites.
4. Merge only after review and CI approval.
5. Keep the external Phase A backup unchanged until the merged remote commit is independently verified.

Pushing and PR creation require explicit user approval in the execution session.

---

## Phase B4 Exit Criteria

The reorganization is complete only when:

1. Agent, Training, Contracts, and Compatibility suites pass.
2. Test coverage is not silently reduced from the Phase A baseline.
3. Canonical Agent and Training commands work.
4. Documented legacy commands forward and print exact replacements.
5. `LLM/` contains compatibility and migration documentation only.
6. Active documentation uses canonical paths.
7. Existing datasets remain byte-identical and auditable.
8. No tracked `tmp/` or runtime `artifacts/` content remains.
9. No secret or private absolute path exists in canonical source/configs.
10. Deterministic Agent smoke and lightweight Training smoke pass.
11. Final verification report says `APPROVED`.
12. The branch is clean, committed, reviewed, and ready for explicitly approved publication.
