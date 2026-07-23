# SR2FPGA Contracts

This directory owns language-neutral schemas and the canonical task catalog. It
must not contain runtime state.

## Audit Tools

- `tools/build_dataset_inventory.py` rebuilds deterministic release checksums.
- `tools/inventory_tracked_tmp.py` inventories tracked legacy temporary files
  without moving or deleting them.
- `tools/plan_legacy_evidence_migration.py` maps active legacy evidence
  references to stable report paths without copying them.
- `tools/verify_phase_a_backup.py` rechecks an explicitly supplied external
  Phase A backup before any cleanup:

```powershell
python contracts/tools/verify_phase_a_backup.py `
  --root . `
  --backup-root $env:SR2FPGA_PHASE_A_BACKUP_ROOT
```

The backup verifier writes only the ignored
`artifacts/reorganization/phase-b4/backup-recheck.json` record after every
manifest, byte-count, checksum, workspace, and restore-sample check passes.
