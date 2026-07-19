# SR2FPGA Cleanup Deviation Waiver

## Approved Scope

- Task: Phase A Task 5 workspace cleanup
- User decision date: `2026-07-19`
- User decision: approved as a corrected specification waiver and authorized Phase A to continue
- Original cleanup preview entries: `184`
- Original cleanup preview SHA-256: `3048308e7bc5f545193e3892ce4853046b3369d2e5a6e0330820bd688a491c8d`

## Deviation

The tracked `.gitignore` was restored before `git clean -fd`. That restore removed an uncommitted `configs/local/*.local.yaml` ignore rule, so the cleanup emitted one additional `Removing configs/local/` line covering four local configuration files that were absent from the approved preview.

## Corrective Recovery

The four affected files were restored byte-for-byte from the frozen, verified backup. Their contents were not read or exposed during recovery.

| Restored path | Bytes | SHA-256 |
|---|---:|---|
| `configs/local/sr2fpga_his_v12_pro_repair_smoke.local.yaml` | 740 | `0ecc9fd4a5d5d38c86b2ce77c21eacb51f70c42dd4f2b17ca50fa1484917d1e1` |
| `configs/local/sr2fpga_his_v12_pro_repair_t1_t4.local.yaml` | 830 | `ad60cec8c929b1c658b7dd7b9a40f89b7f1893375d50adca88b4a92d2e392628` |
| `configs/local/sr2fpga_his_v12_pro_smoke.local.yaml` | 730 | `3abbdafa36e0686ce3d5172a802b9df718919f19e0f2b906e1626fb8fb92526c` |
| `configs/local/sr2fpga_multi_teacher_smoke.local.yaml` | 1971 | `0dba78b4759fae25622a991a25df206116e624beff0847269254bdfb2aa2d0da` |

## Final State

- All four restored files match the frozen backup hashes.
- All four restored files are ignored by current `origin/develop`.
- The main checkout is clean on `develop` at `54e2560ced4536b727bc23f340b1be90aee56a38`.
- The main checkout equals `origin/develop`.
- The external backup remains verified and unchanged.
- This waiver supplements, but does not alter, the 14-field workspace recovery audit.
