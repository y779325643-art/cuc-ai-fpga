# Phase B4 Pre-Cleanup Verification

Date: 2026-07-23

Branch: `codex/reorganization-phase-b1`

Verified head: `cd23606c`

Verdict: **NOT APPROVED**

This is a pre-cleanup checkpoint, not the final repository-reorganization
verdict. All checks that do not depend on the Phase A external backup have
passed. The mandatory backup, evidence-migration, and tracked-`tmp/` retirement
gates remain open.

## Completed Reorganization Boundaries

- `agent/` is the canonical generation, verification, repair, and trajectory
  project.
- `training/` is the canonical conversion, training, merge, and serving
  project.
- Training imports neither Agent nor the legacy `LLM` namespace.
- `contracts/` owns versioned cross-project schemas and the canonical task
  catalog.
- `datasets/` contains immutable releases with deterministic SHA-256
  inventories.
- `artifacts/` is ignored runtime output; the only tracked path is
  `artifacts/README.md`.
- `LLM/` contains one-cycle compatibility entrypoints and migration
  documentation, not business logic.

## Test Evidence

The full executable suite was run with the intentionally failing retirement
gate excluded:

```powershell
python -m pytest contracts/tests agent/tests training/tests `
  compatibility_tests `
  --ignore=compatibility_tests/test_tmp_retirement.py -q
```

Result:

```text
1025 passed, 349 subtests passed
```

The compatibility surface was also run independently:

```text
27 passed
```

The retirement gate currently reports:

```text
2 passed, 2 failed
```

The two failures are expected and identify the remaining work:

1. 590 paths are still tracked under `tmp/`.
2. The active task-evidence ledger still contains legacy `tmp/sr2fpga...`
   references.

## Canonical Agent Verification

The canonical Agent preflight expanded 24 deterministic samples and found
Verilator, Icarus Verilog, VVP, and Yosys.

A fresh run used an isolated ignored dataset root under
`artifacts/reorganization/phase-b4/` to avoid reusing 24 pre-existing sample
IDs from an earlier smoke run.

Run ID: `reorganization-final-smoke-fresh`

| Measure | Result |
| --- | ---: |
| Planned / completed | 24 / 24 |
| Rejected | 0 |
| H0 / H1 / H2 pass | 24 / 24 / 24 |
| H3 pass / not applicable | 14 / 10 |
| L0 / L1 / L2 / L3 pass | 24 / 24 / 24 / 24 |
| L4-open not run | 24 (`disabled_by_config`) |
| Mutation score | 0.93 |

`not_run` was kept separate from failure as required.

## Canonical Training Verification

The lightweight Training path converted the repository fixture:

```text
Converted 6 rows
```

Dry-run result:

| Measure | Result |
| --- | ---: |
| Rows / valid rows | 6 / 6 |
| Minimum tokens | 45 |
| Maximum tokens | 164 |
| Mean tokens | 87.0 |
| Rows over 2048 | 0 |

A fresh `sr2fpga_training` import loaded none of:

- `sr2fpga_agent`
- `torch`
- `transformers`

## Contracts And Dataset Immutability

Focused contract and dataset-policy checks:

```text
16 passed
```

The following inventories were rebuilt:

- `datasets/manifests/sr2fpga_rtl_v1.sha256`
- `datasets/manifests/sr2fpga_phase_d_control_v1.sha256`
- `datasets/manifests/sr2fpga_phase_d_v1.sha256`

`git diff --exit-code` reported no change in any manifest, payload, or export
directory.

## Repository Boundary Scan

The scan covered 101 canonical source, configuration, and script files.

| Scan | Hits |
| --- | ---: |
| API-key-shaped secrets | 0 |
| Legacy `LLM` imports | 0 |
| Private absolute machine paths | 0 |

The OpenXC7 wrapper no longer contains a machine-specific default flake path.
It uses `OPENXC7_FLAKE_PATH`, `OPENXC7_CHIPDB_DIR`, or
`NEXTPNR_XILINX_CHIPDB_DIR`. Its focused tests and `bash -n` check passed.

## Legacy Evidence Inventory

Tracked temporary inventory:

| Measure | Result |
| --- | ---: |
| Tracked `tmp/` paths | 590 |
| Total Git blob bytes | 3,050,197 |
| Proposed curated moves | 0 |
| External-backup-only records | 590 |

Active evidence migration plan:

| Measure | Result |
| --- | ---: |
| Legacy evidence occurrences | 87 |
| Unique legacy references | 69 |
| Source roots / run groups | 5 / 5 |
| Planned references | 69 |
| Current status | `requires_phase_a_backup` |

The migration plan maps every unique reference exactly once into
`reports/evidence/legacy-runs/<run-id>/`. It does not copy, move, or delete
files.

## Open Mandatory Gates

The final verdict must remain **NOT APPROVED** until all of the following are
proven:

1. The operator explicitly supplies the Phase A external backup root.
2. The manifest, checksums, byte counts, and restore samples pass the B4 backup
   recheck.
3. The 69 active evidence references are restored from that verified backup
   and curated under stable `reports/evidence/legacy-runs/` paths.
4. The evidence ledger and its audit tests pass against the curated files.
5. The user reviews the final inventory totals and explicitly approves
   removal.
6. All 590 tracked `tmp/` paths are retired without touching untracked content
   in another worktree.
7. The complete suite, canonical smokes, dataset inventories, boundary scan,
   and retirement audit are rerun from the post-cleanup commit.
8. `reports/reorganization/final-verification.md` records an independently
   supported `APPROVED` verdict.
