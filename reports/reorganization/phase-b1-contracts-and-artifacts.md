# Phase B1 Contracts And Artifacts Report

Date: 2026-07-23

## Scope

Phase B1 established repository ownership boundaries, canonical cross-project
contracts, and immutable inventories for the three existing dataset releases.
It did not move the Agent or Training implementation.

## Task Commits

| Task | Commit | Result |
|---|---|---|
| Repository project boundaries | `14b25013` | Added ownership READMEs and runtime ignore policy |
| Canonical System-HIS contract | `a5e93d69` | Added the v1.2 schema and registry |
| Trajectory and training-view contracts | `db7e64f5` | Added canonical status and derived-view semantics |
| Canonical task catalog | `1f4e94da` | Copied the v0.2 catalog byte-for-byte into `contracts/` |
| Immutable dataset inventories | `c7d99b7d` | Added release metadata, inventory tool, and SHA-256 manifests |

## Verification

- Contract suite: `29 passed in 1.01s`.
- Legacy suite: `905 passed, 349 subtests passed in 148.11s`.
- The legacy result matches the Phase A clean baseline.
- The canonical task catalog and `docs/` compatibility copy are byte-identical.
- Rebuilding all three dataset inventories produced the same inventory SHA-256
  values:
  - `sr2fpga_rtl_v1.sha256`:
    `7247ed8d9692d4c2346fbf1155335d66cd2fee643181dcddb2316ee87b05554f`
  - `sr2fpga_phase_d_control_v1.sha256`:
    `5fa48cfa05649ef8433d553b91d6716ca05526068b26045160215339bf3d5d33`
  - `sr2fpga_phase_d_v1.sha256`:
    `d852272397aeecea0b2dfaf3fc11a16ecc6265ba72373e471585ef8d910594e3`

## Dataset Inventory

Counts include each release payload and its paired export directory.

| Release | Files | Aggregate bytes |
|---|---:|---:|
| `sr2fpga_rtl_v1` | 8,536 | 139,216,929 |
| `sr2fpga_phase_d_control_v1` | 861 | 19,067,221 |
| `sr2fpga_phase_d_v1` | 462 | 8,373,479 |
| **Total** | **9,859** | **166,657,629** |

The existing payload and export bytes were not modified. Git reported no diff
under the six historical payload/export directories. Their tree object IDs
remain:

```text
57dcc43660c4cb883b3853f6d679db72e85f8eab  datasets/sr2fpga_rtl_v1
28f5ca65847cd445763599276729893fe5a779d3  datasets/sr2fpga_rtl_v1_exports
0d207a7b30ab73717aed5e18efb44160b81e87d4  datasets/sr2fpga_phase_d_control_v1
a8657fb3b87d7cbf6d2762afa86070817b2dc059  datasets/sr2fpga_phase_d_control_v1_exports
24ef2b27a07ffdfc9325282273ed76460d3b12d0  datasets/sr2fpga_phase_d_v1
cd855aa53bf41555aa7dff07af403811713ca454  datasets/sr2fpga_phase_d_v1_exports
```

## Policy State

- New runtime output is directed to ignored `artifacts/`.
- `artifacts/README.md` is the only tracked file under `artifacts/`.
- Existing tracked `tmp/` evidence remains in place for the Phase B4
  backup-and-cleanup gate.
- Legacy dataset releases remain `internal_only` and `review_required`; no
  historical configuration fingerprint was invented.

## Remaining Dependency

The Agent and Training projects have not yet been moved. Phase B2 must migrate
the data-generation Agent to `agent/` while consuming contracts from
`contracts/`; Phase B3 must independently migrate training code to `training/`.
