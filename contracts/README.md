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
The record pins the verified manifest SHA-256 so later curation rejects a
backup changed after the gate.

After that gate passes, preview the exact legacy evidence selection:

```powershell
python contracts/tools/curate_legacy_evidence.py `
  --root . `
  --backup-root $env:SR2FPGA_PHASE_A_BACKUP_ROOT
```

The preview is also ignored and blocks on API-key-shaped content, private
absolute paths, missing files, hash changes, or destination conflicts. Do not
use `--apply` until the preview and cleanup inventory have received explicit
approval. An approved application must name the tracked manifest explicitly:

```powershell
python contracts/tools/curate_legacy_evidence.py `
  --root . `
  --backup-root $env:SR2FPGA_PHASE_A_BACKUP_ROOT `
  --apply `
  --output reports/reorganization/legacy-evidence-curation.json
```
