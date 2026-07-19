# SR2FPGA Repository Reorganization Phase B1: Contracts and Artifacts Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Establish stable cross-project contracts, make task and dataset metadata auditable, and create an ignored runtime artifact boundary before moving Agent or Training code.

**Architecture:** The repository root owns language-neutral contracts and immutable dataset release metadata. `agent/` and `training/` consume those contracts but do not define competing copies. Generated runs, checkpoints, logs, and caches go under ignored `artifacts/`. Existing dataset payload bytes remain unchanged during this phase.

**Tech Stack:** JSON Schema draft 2020-12, Python 3.11 standard library, pytest, PowerShell, Git.

**Depends on:** `docs/superpowers/plans/2026-07-17-sr2fpga-reorganization-phase-a-workspace-recovery.md` completed and approved.

**Produces for later phases:**

- `contracts/manifest.json` as the contract registry.
- Canonical System-HIS, trajectory, training-view, and task-catalog files under `contracts/`.
- `datasets/manifest.json` and deterministic SHA-256 inventories.
- Root policy files that prevent new runtime output from entering tracked source trees.

---

## Task 1: Add repository boundary tests before creating the new directories

**Files:**
- Create: `contracts/tests/test_repository_boundaries.py`
- Modify: `.gitignore`
- Create: `agent/README.md`
- Create: `training/README.md`
- Create: `contracts/README.md`
- Create: `artifacts/README.md`
- Create: `reports/README.md`

### Step 1: Write the failing boundary test

Create `contracts/tests/test_repository_boundaries.py` with tests that resolve the repository root from `Path(__file__).resolve().parents[2]` and assert:

1. `agent/`, `training/`, `contracts/`, `artifacts/`, and `reports/` exist.
2. Each directory has a `README.md`.
3. The root `.gitignore` contains exact root-scoped entries:
   - `/artifacts/*`
   - `!/artifacts/README.md`
   - `/tmp/`
   - `/agent/configs/local/`
   - `/training/configs/local/`
4. `datasets/` is not globally ignored.
5. `reports/` is not globally ignored.

Use this exact helper so path resolution remains stable:

```python
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def read_root_file(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")
```

### Step 2: Run the test and confirm it fails

Run:

```powershell
python -m pytest contracts/tests/test_repository_boundaries.py -q
```

Expected result: failure because the new project shells and ignore entries do not exist.

### Step 3: Add the minimum repository shells

Create concise READMEs with these ownership statements:

- `agent/README.md`: project generation, validation, repair, L0-L4 orchestration, and trajectory recording.
- `training/README.md`: dataset preparation, SFT/LoRA training, adapter merge, and serving smoke assets.
- `contracts/README.md`: language-neutral schemas and canonical task catalog; no runtime state.
- `artifacts/README.md`: local generated runs, logs, caches, checkpoints, and reports; directory contents are ignored.
- `reports/README.md`: curated, intentionally committed evidence and human-readable reports only.

Append the five root-scoped ignore entries to `.gitignore`. Do not ignore `datasets/`, `contracts/`, or `reports/`.

### Step 4: Run the focused test

```powershell
python -m pytest contracts/tests/test_repository_boundaries.py -q
```

Expected result: pass.

### Step 5: Commit

```powershell
git add .gitignore agent/README.md training/README.md contracts/README.md contracts/tests/test_repository_boundaries.py artifacts/README.md reports/README.md
git commit -m "chore: establish repository project boundaries"
```

---

## Task 2: Add the contract registry and System-HIS schema

**Files:**
- Create: `contracts/manifest.json`
- Create: `contracts/system-his/system-his-v1.2.schema.json`
- Create: `contracts/tests/test_contract_manifest.py`
- Create: `contracts/tests/test_system_his_schema.py`

### Step 1: Write failing registry tests

`contracts/tests/test_contract_manifest.py` must:

1. Parse `contracts/manifest.json` with `json.loads`.
2. Require `contract_registry_version` to equal `"1.0"`.
3. Require entries named `system_his`, `trajectory`, `training_view_row`, and `task_catalog`.
4. Resolve every registered path relative to the repository root.
5. Reject absolute paths and paths containing `..`.
6. Require the System-HIS path created in this task to exist. The all-registered-path existence assertion is added in Task 4 after every registered file exists.

`contracts/tests/test_system_his_schema.py` must parse the schema and assert:

- `$schema` is `https://json-schema.org/draft/2020-12/schema`.
- `$id` is `https://sr2fpga.local/contracts/system-his/v1.2`.
- `type` is `object`.
- `additionalProperties` is false at the top level.
- `required` exactly contains:
  `schema_version`, `intent`, `top`, `state`, `components`, `instances`, `data_flow`, `control_flow`, `timing`, `resources`, `verification`, `artifacts`.
- `properties.schema_version.const` is `system-his-v1.2`.

Do not add `jsonschema` as a dependency in this phase. These tests validate the repository contract shape with the standard library.

### Step 2: Run and confirm failure

```powershell
python -m pytest contracts/tests/test_contract_manifest.py contracts/tests/test_system_his_schema.py -q
```

Expected result: missing files.

### Step 3: Create `contracts/manifest.json`

Use this registry shape:

```json
{
  "contract_registry_version": "1.0",
  "contracts": {
    "system_his": {
      "version": "system-his-v1.2",
      "path": "contracts/system-his/system-his-v1.2.schema.json"
    },
    "trajectory": {
      "version": "trajectory-v1",
      "path": "contracts/trajectory/trajectory-v1.schema.json"
    },
    "training_view_row": {
      "version": "training-view-row-v1",
      "path": "contracts/training-views/training-view-row-v1.schema.json"
    },
    "task_catalog": {
      "version": "v0.2",
      "path": "contracts/task-catalog/sr2fpga-task-catalog-v0.2.json"
    }
  }
}
```

### Step 4: Create the System-HIS schema

The schema must encode the current canonical v1.2 top-level contract without inventing lower-level semantics in this migration. Use:

- Exact top-level required keys listed above.
- `schema_version` as a constant.
- `intent` as a non-empty string or object matching current accepted examples.
- `top` as an object requiring the current top name/module field used by the checker.
- Arrays for `components`, `instances`, and `data_flow`.
- Objects or arrays matching current repository examples for `state`, `control_flow`, `timing`, `resources`, `verification`, and `artifacts`.
- `$defs` for reusable identifier and endpoint strings.
- No change to accepted semantics beyond what existing v1.2 checker tests prove.

Before finalizing the schema, inspect these sources and mirror their accepted shape:

```powershell
Get-Content agent/src/sr2fpga_agent/system_his_v12_checker.py
Get-ChildItem -Recurse -Filter system_his.json | Select-Object -First 10 -ExpandProperty FullName
```

At this phase the first path may still be `LLM/src/sr2fpga_agent/system_his_v12_checker.py`. Use whichever canonical path exists; do not keep two implementations.

### Step 5: Run focused tests

```powershell
python -m pytest contracts/tests/test_contract_manifest.py contracts/tests/test_system_his_schema.py -q
```

Expected result: all current assertions pass. The registry shape is complete, and this task checks existence only for the System-HIS file already created. No test is skipped.

### Step 6: Commit

```powershell
git add contracts/manifest.json contracts/system-his/system-his-v1.2.schema.json contracts/tests/test_contract_manifest.py contracts/tests/test_system_his_schema.py
git commit -m "feat: add canonical System-HIS contract"
```

---

## Task 3: Add trajectory and training-view schemas

**Files:**
- Create: `contracts/trajectory/trajectory-v1.schema.json`
- Create: `contracts/training-views/training-view-row-v1.schema.json`
- Create: `contracts/tests/test_trajectory_schema.py`
- Create: `contracts/tests/test_training_view_schema.py`

### Step 1: Write failing trajectory tests

The trajectory test must assert:

- `$id` is `https://sr2fpga.local/contracts/trajectory/v1`.
- Top-level required keys include `episode_id`, `requirement`, `his_validation`, `verification`, and `attempts`.
- The shared `stage_status` enum is exactly:
  `pass`, `fail`, `not_run`, `infrastructure_error`.
- `verification` contains fields for `l0`, `l1`, `l2`, `l3`, `l4_open`, `l4_commercial`, and `l5`.
- `l4_open` and `l4_commercial` allow `skip_reason` only when status is `not_run` or `infrastructure_error`.
- `not_run` is not represented as `fail`.

Use a small recursive helper to locate `$defs.stage_status.enum`; do not introduce a full schema-validation dependency.

### Step 2: Write failing training-view tests

The training-view schema must define these `view_type` values:

- `requirement_to_his`
- `his_to_project`
- `requirement_to_project`
- `requirement_to_file`
- `failure_to_diagnosis`
- `failure_to_patch`
- `project_to_predicted_qor`
- `project_to_measured_qor`

For `requirement_to_file` rows, the schema must require:

- `source_episode_id` as a non-empty string.
- `file_role`.
- `path` as a relative path.
- `official_eval_unit` with `const: false`.
- `standalone_pass_credit` with `const: false`.

The schema must not assign project-level pass credit to a file-level row.

### Step 3: Run and confirm failure

```powershell
python -m pytest contracts/tests/test_trajectory_schema.py contracts/tests/test_training_view_schema.py -q
```

Expected result: missing schemas.

### Step 4: Implement the two schemas

Keep these schemas descriptive and backward-compatible:

- Use optional fields for values absent in historical episodes.
- Require core identity and stage containers for new v1 records.
- Permit additional diagnostic payload fields inside stage records.
- Keep `toolchain_environment_failure` represented by `infrastructure_error` status or an explicit `failure_origin`; never map it to a model failure.
- Add `contract_version` constants to new records, but let migration readers supply defaults for old data.

### Step 5: Run focused tests

```powershell
python -m pytest contracts/tests/test_trajectory_schema.py contracts/tests/test_training_view_schema.py contracts/tests/test_contract_manifest.py -q
```

Expected result: pass for all three.

### Step 6: Commit

```powershell
git add contracts/trajectory contracts/training-views contracts/tests/test_trajectory_schema.py contracts/tests/test_training_view_schema.py contracts/manifest.json
git commit -m "feat: define trajectory and training-view contracts"
```

---

## Task 4: Move the task catalog authority into `contracts/`

**Files:**
- Create: `contracts/task-catalog/sr2fpga-task-catalog-v0.2.json`
- Create: `contracts/tests/test_task_catalog_contract.py`
- Preserve for one compatibility cycle: `docs/sr2fpga-task-catalog-v0.2.json`

### Step 1: Write the failing authority test

The test must assert:

1. The canonical contract path exists.
2. It parses as JSON.
3. Every task has a unique non-empty `family_id`.
4. Every task declares `sr2fpga_tier`, `system_his_profile`, `skeleton_level`, `oracle_kind`, `target_l_level`, `mutation_suite`, and `benchmark_role`.
5. `target_l_level.official` is one of `L0` through `L5`.
6. `l4_open_policy` is one of `none`, `optional`, `representative_subset`, or `required_for_flagship`.
7. The compatibility copy under `docs/` is byte-identical to the canonical file during this migration cycle.

Read the actual root key used by the existing catalog before writing the iteration helper. Do not assume it is named `tasks` if the file uses a different key.

### Step 2: Run and confirm failure

```powershell
python -m pytest contracts/tests/test_task_catalog_contract.py -q
```

Expected result: canonical file missing.

### Step 3: Copy without changing bytes

Copy the current catalog to the canonical location:

```powershell
New-Item -ItemType Directory -Force contracts/task-catalog
Copy-Item -LiteralPath docs/sr2fpga-task-catalog-v0.2.json -Destination contracts/task-catalog/sr2fpga-task-catalog-v0.2.json
```

Do not normalize, reorder, or edit task entries in this phase.

### Step 4: Complete the registry existence assertion

Extend `test_contract_manifest.py` to require every registered path to exist now that Tasks 2-4 have created all contract files.

### Step 5: Run focused tests

```powershell
python -m pytest contracts/tests/test_task_catalog_contract.py contracts/tests/test_contract_manifest.py -q
```

Expected result: pass.

### Step 6: Commit

```powershell
git add contracts/task-catalog contracts/tests/test_task_catalog_contract.py contracts/tests/test_contract_manifest.py
git commit -m "chore: establish canonical task catalog"
```

---

## Task 5: Add immutable dataset release manifests and checksums

**Files:**
- Create: `datasets/README.md`
- Create: `datasets/manifest.json`
- Create: `datasets/manifests/sr2fpga_rtl_v1.sha256`
- Create: `datasets/manifests/sr2fpga_phase_d_control_v1.sha256`
- Create: `datasets/manifests/sr2fpga_phase_d_v1.sha256`
- Create: `contracts/tools/build_dataset_inventory.py`
- Create: `contracts/tests/test_dataset_release_policy.py`

### Step 1: Write failing dataset policy tests

The test must:

1. Parse `datasets/manifest.json`.
2. Require exactly these release IDs:
   - `sr2fpga_rtl_v1`
   - `sr2fpga_phase_d_control_v1`
   - `sr2fpga_phase_d_v1`
3. Require each release to contain:
   - `payload_path`
   - `exports_path`
   - `checksum_manifest`
   - `release_tier` equal to `internal_only`
   - `license_status` equal to `review_required`
   - `config_fingerprint` equal to null
   - `config_fingerprint_status` equal to `legacy_unavailable`
4. Require payload, exports, and checksum files to exist.
5. Reject absolute or parent-traversing paths.
6. Recompute SHA-256 for a deterministic sample of the first, middle, and last file listed in each checksum manifest.

### Step 2: Run and confirm failure

```powershell
python -m pytest contracts/tests/test_dataset_release_policy.py -q
```

Expected result: metadata and inventories missing.

### Step 3: Implement the inventory tool

Create `contracts/tools/build_dataset_inventory.py`. It must:

- Accept `--root` and repeated `--release` arguments.
- Walk files in sorted POSIX-relative path order.
- Exclude the generated checksum manifest itself.
- Stream file bytes into `hashlib.sha256`.
- Write lines as `<digest>  <relative-posix-path>` with LF line endings.
- Write through a temporary sibling file and replace atomically.
- Refuse paths outside the supplied repository root.
- Return non-zero if a release directory is missing.

The command interface must be:

```powershell
python contracts/tools/build_dataset_inventory.py --root . --release sr2fpga_rtl_v1 --release sr2fpga_phase_d_control_v1 --release sr2fpga_phase_d_v1
```

### Step 4: Create the dataset manifest

Use `dataset_manifest_version: "1.0"` and one object per release. Keep historical data immutable. Do not claim a configuration fingerprint that was not recorded when these releases were generated.

Example release shape:

```json
{
  "release_id": "sr2fpga_rtl_v1",
  "payload_path": "datasets/sr2fpga_rtl_v1",
  "exports_path": "datasets/sr2fpga_rtl_v1_exports",
  "checksum_manifest": "datasets/manifests/sr2fpga_rtl_v1.sha256",
  "release_tier": "internal_only",
  "license_status": "review_required",
  "config_fingerprint": null,
  "config_fingerprint_status": "legacy_unavailable"
}
```

`datasets/README.md` must state:

- Existing releases are read-only evidence.
- New runner output must go to `artifacts/` first.
- Promotion into `datasets/` requires a versioned release ID, config fingerprint, tool versions, license review, checksum inventory, and explicit approval.
- This phase does not modify payload bytes.

### Step 5: Generate inventories

```powershell
python contracts/tools/build_dataset_inventory.py --root . --release sr2fpga_rtl_v1 --release sr2fpga_phase_d_control_v1 --release sr2fpga_phase_d_v1
```

### Step 6: Verify payload immutability

Before staging, use Git to prove no existing dataset payload changed:

```powershell
git status --short datasets
git diff -- datasets/sr2fpga_rtl_v1 datasets/sr2fpga_rtl_v1_exports datasets/sr2fpga_phase_d_control_v1 datasets/sr2fpga_phase_d_control_v1_exports datasets/sr2fpga_phase_d_v1 datasets/sr2fpga_phase_d_v1_exports
```

Expected result: only new README, manifest, and checksum inventory files appear; no diff under existing release payloads or exports.

### Step 7: Run focused tests

```powershell
python -m pytest contracts/tests/test_dataset_release_policy.py -q
```

Expected result: pass.

### Step 8: Commit

```powershell
git add datasets/README.md datasets/manifest.json datasets/manifests contracts/tools/build_dataset_inventory.py contracts/tests/test_dataset_release_policy.py
git commit -m "chore: inventory immutable dataset releases"
```

---

## Task 6: Add contract compatibility fixtures and complete Phase B1 verification

**Files:**
- Create: `contracts/tests/fixtures/system_his_minimal_v1_2.json`
- Create: `contracts/tests/fixtures/trajectory_minimal_v1.json`
- Create: `contracts/tests/fixtures/training_view_req2file_v1.json`
- Create: `contracts/tests/test_contract_fixtures.py`
- Modify: `docs/superpowers/specs/2026-07-17-sr2fpga-repository-reorganization-design.md` only if implementation discovered a contract fact that the approved design states incorrectly

### Step 1: Add representative fixtures

Create one minimal valid fixture per schema. Fixtures must contain concrete values and no dummy markers.

The REQ2FILE fixture must include:

```json
{
  "contract_version": "training-view-row-v1",
  "view_type": "requirement_to_file",
  "source_episode_id": "fixture-episode-001",
  "file_role": "rtl",
  "path": "rtl/top.sv",
  "official_eval_unit": false,
  "standalone_pass_credit": false,
  "input": {"requirement": "Implement a synchronous counter."},
  "output": {"content": "module top(input logic clk); endmodule"}
}
```

### Step 2: Write fixture tests

The test must:

- Parse every fixture.
- Check required values against the corresponding schema properties.
- Verify all fixture paths are relative.
- Verify REQ2FILE cannot claim standalone pass credit.
- Verify trajectory `not_run` stages carry a non-empty `skip_reason`.
- Verify `infrastructure_error` is distinguishable from model `fail`.

### Step 3: Run all contract tests

```powershell
python -m pytest contracts/tests -q
```

Expected result: all pass.

### Step 4: Run the unchanged legacy suite

```powershell
python -m pytest LLM/tests -q
```

Expected result: match the Phase A clean baseline. If the count changes only because tests were intentionally added outside `LLM/tests`, the original `LLM/tests` result must remain unchanged.

### Step 5: Verify policy and source cleanliness

```powershell
git diff --check
git status --short
git ls-files artifacts tmp
git diff -- datasets/sr2fpga_rtl_v1 datasets/sr2fpga_rtl_v1_exports datasets/sr2fpga_phase_d_control_v1 datasets/sr2fpga_phase_d_control_v1_exports datasets/sr2fpga_phase_d_v1 datasets/sr2fpga_phase_d_v1_exports
```

Expected result:

- No whitespace errors.
- No tracked runtime file under `artifacts/`; `artifacts/README.md` is the only allowed tracked file there.
- Existing tracked `tmp/` is still present at this intermediate phase and is handled only in Phase B4 after backup; do not delete it here.
- No legacy dataset payload modification.

### Step 6: Record the phase result

Create a short `reports/reorganization/phase-b1-contracts-and-artifacts.md` containing:

- Commit IDs from Tasks 1-5.
- Contract test count and result.
- Legacy suite count and result.
- Dataset inventory file counts and aggregate bytes.
- Explicit statement that payload bytes were not modified.
- Remaining dependency: Agent and Training have not yet been moved.

### Step 7: Commit the phase report

```powershell
git add contracts/tests/fixtures contracts/tests/test_contract_fixtures.py reports/reorganization/phase-b1-contracts-and-artifacts.md
git commit -m "test: verify repository contracts and dataset policy"
```

---

## Phase B1 Exit Criteria

Phase B1 is complete only when:

1. `python -m pytest contracts/tests -q` passes.
2. `python -m pytest LLM/tests -q` matches the Phase A clean baseline.
3. Every path in `contracts/manifest.json` exists.
4. The canonical task catalog and compatibility copy are byte-identical.
5. Dataset inventories can be reproduced deterministically.
6. Existing dataset payload and export bytes are unchanged.
7. New runtime output is directed toward ignored `artifacts/` by policy.
8. No tracked runtime artifact is added.
9. The worktree is clean after the phase report commit.
10. The next plan may consume `contracts/` without importing code from `LLM/`.
