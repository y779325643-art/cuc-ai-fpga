# SR2FPGA Phase A Workspace Recovery Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Preserve all local main-worktree changes in a verified external backup, then return the parameterized main checkout (`$repo`) to a clean `origin/develop` baseline.

**Architecture:** Capture Git state and binary patches, mirror every non-`.git` workspace file to the external `$backup` root, verify path/length/SHA256 equality and sample restoration, rerun the clean test baseline, then restore tracked files, clean reviewed untracked paths, and fast-forward `develop`. Cleanup is blocked until the user approves the `git clean -nd` preview.

**Tech Stack:** PowerShell 7, Git, `robocopy`, SHA256, JSON, pytest.

## Global Constraints

- Main checkout: `$repo`, resolved from the explicit `$repoRoot` input below.
- Isolated worktree: `$worktree`, resolved from the explicit `$worktreeRoot` input below.
- Backup root: `$backup`, created under the explicit external `$backupParent` input below.
- Never copy `.git`.
- Never commit `.env` contents or the external backup path inventory.
- Do not use `git reset --hard`.
- Validate resolved absolute paths before recursive operations.
- Stop on any file-count, byte-count, hash, JSON/JSONL parse, or restore mismatch.
- Do not clean until a fresh `git clean -nd` preview is approved.
- Preserve the isolated worktree throughout Phase A.

---

### Task 1: Capture Repository State and Git Patches

**Files:**
- Create externally: `repository-state.json`
- Create externally: `tracked-working-tree.patch`
- Create externally: `staged-index.patch`
- Create externally: `status.porcelain-v2.z`
- Create externally: `worktrees.txt`

**Interfaces:**
- Consumes: main checkout and remote refs.
- Produces: immutable pre-cleanup state and restorable Git patches.

- [ ] **Step 1: Resolve paths and refresh remote refs**

```powershell
$ErrorActionPreference = "Stop"
$repoRoot = Read-Host "Approved main checkout path"
$worktreeRoot = Read-Host "Approved isolated worktree path"
$backupParent = Read-Host "Approved external backup parent path"
$repo = (Resolve-Path -LiteralPath $repoRoot).Path
$worktree = (Resolve-Path -LiteralPath $worktreeRoot).Path
$backupParent = (Resolve-Path -LiteralPath $backupParent).Path
$backup = Join-Path -Path $backupParent -ChildPath "sr2fpga-reorganization-backup-20260717"

if ($repo -eq $worktree) { throw "Main checkout and isolated worktree must differ" }
if ($backup.StartsWith($repo, [System.StringComparison]::OrdinalIgnoreCase) -or $backup.StartsWith($worktree, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Backup root must be external to both worktrees: $backup"
}
if (Test-Path -LiteralPath $backup) { throw "Backup root exists: $backup" }

git -C $repo fetch origin
if ($LASTEXITCODE -ne 0) { throw "git fetch failed" }
```

Expected: exit 0. Record the fetched `origin/develop` commit; if it differs from the design snapshot, note the drift.

- [ ] **Step 2: Create and validate the backup root**

```powershell
New-Item -ItemType Directory -Path $backup | Out-Null
$backup = (Resolve-Path -LiteralPath $backup).Path
$expectedBackupPrefix = Join-Path -Path $backupParent -ChildPath "sr2fpga-reorganization-backup-"
if (-not $backup.StartsWith($expectedBackupPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Unsafe backup root: $backup"
}
```

Expected: the resolved path remains under the approved external `$backupParent`.

- [ ] **Step 3: Write state and patches**

```powershell
$status = @(git -C $repo status --porcelain=v2 --untracked-files=all)
$state = [ordered]@{
    schema_version = "sr2fpga-workspace-backup-v1"
    created_utc = [DateTime]::UtcNow.ToString("o")
    repository = $repo
    branch = (git -C $repo branch --show-current).Trim()
    head = (git -C $repo rev-parse HEAD).Trim()
    origin_develop = (git -C $repo rev-parse origin/develop).Trim()
    tracked_changed = @($status | Where-Object { $_ -match "^[12u] " }).Count
    untracked = @($status | Where-Object { $_ -match "^\? " }).Count
    design_worktree = $worktree
}
[System.IO.File]::WriteAllText(
    (Join-Path $backup "repository-state.json"),
    ($state | ConvertTo-Json -Depth 4) + [Environment]::NewLine,
    [System.Text.UTF8Encoding]::new($false)
)
git -C $repo diff --binary --full-index > (Join-Path $backup "tracked-working-tree.patch")
git -C $repo diff --cached --binary --full-index > (Join-Path $backup "staged-index.patch")
git -C $repo status --porcelain=v2 -z --untracked-files=all > (Join-Path $backup "status.porcelain-v2.z")
git -C $repo worktree list --porcelain > (Join-Path $backup "worktrees.txt")
```

Expected: the JSON parses; tracked and untracked counts are nonzero for the audited dirty workspace.

---

### Task 2: Mirror and Hash the Workspace

**Files:**
- Create externally: `workspace\`
- Create externally: `manifest.json`
- Create externally: `checksums.sha256`

**Interfaces:**
- Consumes: every file under the main checkout except `.git`.
- Produces: byte-for-byte snapshot and SHA256 manifest.

- [ ] **Step 1: Mirror the workspace**

```powershell
$workspaceBackup = Join-Path $backup "workspace"
New-Item -ItemType Directory -Path $workspaceBackup | Out-Null
& robocopy $repo $workspaceBackup /E /XJ /COPY:DAT /DCOPY:DAT /R:1 /W:1 /XD (Join-Path $repo ".git")
if ($LASTEXITCODE -gt 7) { throw "robocopy failed: $LASTEXITCODE" }
```

Expected: `robocopy` exits 0-7.

- [ ] **Step 2: Generate source records**

```powershell
$gitPrefix = [System.IO.Path]::GetFullPath((Join-Path $repo ".git") + "\")
$sourceFiles = @(
    Get-ChildItem -LiteralPath $repo -Recurse -File -Force |
        Where-Object {
            -not [System.IO.Path]::GetFullPath($_.FullName).StartsWith(
                $gitPrefix,
                [System.StringComparison]::OrdinalIgnoreCase
            )
        }
)
$records = @(
    foreach ($file in $sourceFiles) {
        [ordered]@{
            path = [System.IO.Path]::GetRelativePath($repo, $file.FullName).Replace("\", "/")
            length = $file.Length
            sha256 = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        }
    }
) | Sort-Object path
$manifest = [ordered]@{
    schema_version = "sr2fpga-workspace-backup-v1"
    repository = $repo
    source_head = (git -C $repo rev-parse HEAD).Trim()
    origin_develop = (git -C $repo rev-parse origin/develop).Trim()
    file_count = $records.Count
    byte_count = [long](($sourceFiles | Measure-Object Length -Sum).Sum)
    files = $records
}
[System.IO.File]::WriteAllText(
    (Join-Path $backup "manifest.json"),
    ($manifest | ConvertTo-Json -Depth 6) + [Environment]::NewLine,
    [System.Text.UTF8Encoding]::new($false)
)
[System.IO.File]::WriteAllLines(
    (Join-Path $backup "checksums.sha256"),
    @($records | ForEach-Object { "$($_.sha256)  $($_.path)" }),
    [System.Text.UTF8Encoding]::new($false)
)
```

Expected: checksum line count equals `manifest.file_count`.

---

### Task 3: Verify Integrity and Restoration

**Files:**
- Create externally: `verification.json`
- Create externally: `restore-test\`
- Create externally: `restore-instructions.md`

**Interfaces:**
- Consumes: Task 2 snapshot.
- Produces: hard pass/fail evidence required before cleanup.

- [ ] **Step 1: Verify every path, length, and hash**

```powershell
$manifest = Get-Content -LiteralPath (Join-Path $backup "manifest.json") -Raw | ConvertFrom-Json
$errors = [System.Collections.Generic.List[string]]::new()
foreach ($record in $manifest.files) {
    $target = Join-Path $workspaceBackup ($record.path.Replace("/", "\"))
    if (-not (Test-Path -LiteralPath $target -PathType Leaf)) {
        $errors.Add("missing: $($record.path)")
        continue
    }
    $item = Get-Item -LiteralPath $target
    if ($item.Length -ne [long]$record.length) {
        $errors.Add("length: $($record.path)")
        continue
    }
    $hash = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($hash -ne $record.sha256) { $errors.Add("sha256: $($record.path)") }
}
if ($errors.Count -gt 0) {
    $errors | Select-Object -First 20
    throw "Backup verification failed for $($errors.Count) files"
}
$backupFiles = @(Get-ChildItem -LiteralPath $workspaceBackup -Recurse -File -Force)
if ($backupFiles.Count -ne [int]$manifest.file_count) { throw "File-count mismatch" }
if ([long](($backupFiles | Measure-Object Length -Sum).Sum) -ne [long]$manifest.byte_count) {
    throw "Byte-count mismatch"
}
```

Expected: zero errors.

- [ ] **Step 2: Parse all backed-up JSON and JSONL**

```powershell
foreach ($record in $manifest.files) {
    $path = Join-Path $workspaceBackup ($record.path.Replace("/", "\"))
    if ($record.path -match "\.json$") {
        Get-Content -LiteralPath $path -Raw | ConvertFrom-Json | Out-Null
    }
    if ($record.path -match "\.jsonl$") {
        foreach ($line in Get-Content -LiteralPath $path) {
            if ($line.Trim()) { $line | ConvertFrom-Json | Out-Null }
        }
    }
}
```

Expected: no parse exception. Stop and record any pre-existing malformed file instead of silently excluding it.

- [ ] **Step 3: Restore representative file types**

```powershell
$restoreRoot = Join-Path $backup "restore-test"
New-Item -ItemType Directory -Path $restoreRoot | Out-Null
$extensions = @(".py", ".json", ".jsonl", ".v", ".md", ".yaml")
$selected = @(
    foreach ($extension in $extensions) {
        $manifest.files |
            Where-Object { $_.path.EndsWith($extension, [System.StringComparison]::OrdinalIgnoreCase) } |
            Select-Object -First 1
    }
)
foreach ($record in $selected) {
    $source = Join-Path $workspaceBackup ($record.path.Replace("/", "\"))
    $target = Join-Path $restoreRoot ($record.path.Replace("/", "\"))
    New-Item -ItemType Directory -Path (Split-Path -Parent $target) -Force | Out-Null
    Copy-Item -LiteralPath $source -Destination $target
    $hash = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($hash -ne $record.sha256) { throw "Restore mismatch: $($record.path)" }
}
```

Expected: restored samples hash-match.

- [ ] **Step 4: Write verification and restore instructions**

```powershell
$verification = [ordered]@{
    schema_version = "sr2fpga-workspace-backup-verification-v1"
    verified_utc = [DateTime]::UtcNow.ToString("o")
    file_count = [int]$manifest.file_count
    byte_count = [long]$manifest.byte_count
    hash_failures = 0
    structured_parse_failures = 0
    restore_samples = @($selected | ForEach-Object { $_.path })
    status = "pass"
}
[System.IO.File]::WriteAllText(
    (Join-Path $backup "verification.json"),
    ($verification | ConvertTo-Json -Depth 5) + [Environment]::NewLine,
    [System.Text.UTF8Encoding]::new($false)
)
$restoreText = @"
# Restore Procedure

1. Confirm verification.json reports pass.
2. Copy required relative paths from workspace back into $repo.
3. Apply tracked-working-tree.patch with git apply --binary.
4. Apply a nonempty staged-index.patch with git apply --index --binary.
5. Recompute SHA256 for restored files.
6. Keep .env content outside Git.
"@
[System.IO.File]::WriteAllText(
    (Join-Path $backup "restore-instructions.md"),
    $restoreText,
    [System.Text.UTF8Encoding]::new($false)
)
```

Expected: `verification.status` equals `pass`.

---

### Task 4: Reproduce the Baseline

**Files:**
- Read: `LLM/tests/`

**Interfaces:**
- Consumes: isolated worktree.
- Produces: fresh pre-migration test evidence.

- [ ] **Step 1: Verify isolated worktree state**

```powershell
git -C $worktree status --short
git -C $worktree log -1 --oneline
```

Expected: no status entries.

- [ ] **Step 2: Run the complete baseline suite**

```powershell
Push-Location $worktree
try {
    python -m pytest LLM/tests
    if ($LASTEXITCODE -ne 0) { throw "Baseline failed" }
} finally {
    Pop-Location
}
```

Expected: `905 passed, 349 subtests passed` for the recorded baseline.

---

### Task 5: Clean and Fast-Forward the Main Checkout

**Files:**
- Modify operationally: `$repo`
- Create in implementation branch: `docs/reorganization/2026-07-17-workspace-recovery-audit.md`

**Interfaces:**
- Consumes: verified backup and green baseline.
- Produces: clean main checkout and non-sensitive audit.

- [ ] **Step 1: Preview cleanup**

```powershell
$verification = Get-Content -LiteralPath (Join-Path $backup "verification.json") -Raw | ConvertFrom-Json
if ($verification.status -ne "pass") { throw "Backup is not verified" }
git -C $repo status --short
git -C $repo clean -nd
```

Expected: previewed untracked paths all exist in `backup\workspace`.

- [ ] **Step 2: Obtain explicit approval**

Report backup file count, byte count, backup root, and the complete `git clean -nd` preview. Do not continue until the user approves the destructive cleanup.

- [ ] **Step 3: Restore tracked files and remove reviewed untracked paths**

```powershell
if ((Resolve-Path -LiteralPath $repo).Path -ne $repo -or $repo -eq $worktree) {
    throw "Unsafe repository path"
}
git -C $repo restore --source=HEAD --staged --worktree -- .
if ($LASTEXITCODE -ne 0) { throw "git restore failed" }
git -C $repo clean -fd
if ($LASTEXITCODE -ne 0) { throw "git clean failed" }
```

Expected: ignored local secrets remain; ordinary untracked paths are removed.

- [ ] **Step 4: Fast-forward without hard reset**

```powershell
if ((git -C $repo branch --show-current).Trim() -ne "develop") {
    throw "Main checkout is not on develop"
}
git -C $repo merge --ff-only origin/develop
if ($LASTEXITCODE -ne 0) { throw "Fast-forward failed" }
$head = (git -C $repo rev-parse HEAD).Trim()
$remote = (git -C $repo rev-parse origin/develop).Trim()
if ($head -ne $remote) { throw "HEAD mismatch" }
if (@(git -C $repo status --short).Count -ne 0) { throw "Main checkout is not clean" }
```

Expected: clean main checkout equal to `origin/develop`.

- [ ] **Step 5: Write and commit the recovery audit**

Create `docs/reorganization/2026-07-17-workspace-recovery-audit.md` in the implementation worktree with the commit IDs and counts from `repository-state.json` and `verification.json`. Include only these fields:

```markdown
# SR2FPGA Workspace Recovery Audit

- Backup schema
- Source branch
- Source HEAD
- Published develop HEAD at capture
- Tracked changes captured
- Untracked files captured
- Snapshot files verified
- Snapshot bytes verified
- SHA256 failures
- Structured parse failures
- Restore samples verified
- Verification status
- Main checkout clean after recovery
- Main checkout equal to origin/develop after recovery
```

Run:

```powershell
git diff --check
git grep -n -E "sk-[A-Za-z0-9]|apiKey|ANTHROPIC_API_KEY=|OPENAI_API_KEY=" -- docs/reorganization
git add docs/reorganization/2026-07-17-workspace-recovery-audit.md
git commit -m "chore: record workspace recovery audit"
```

Expected: secret scan has no matches, commit succeeds, and implementation worktree is clean.


## Phase A Exit Criteria

Phase A is complete only when:

1. The external backup manifest, patches, workspace snapshot, and SHA-256 verification all pass.
2. A sample restore from the backup succeeds.
3. The clean baseline reproduces 905 tests and 349 subtests, or a documented higher count.
4. The user explicitly approves the reviewed cleanup preview before any cleanup runs.
5. The main checkout is clean and equal to current origin/develop after an ff-only update.
6. The non-sensitive recovery audit is committed in the implementation worktree.
7. The external backup remains unchanged for the rest of the migration.
8. Both the main checkout and implementation worktree are in the states recorded by the audit.
