# SR2FPGA Reports

This directory contains curated, intentionally committed evidence and
human-readable reports only.

The current machine-readable task evidence ledger is
[`evidence/task-ledger/sr2fpga-task-evidence-v0.1.json`](evidence/task-ledger/sr2fpga-task-evidence-v0.1.json).
Its derived human-readable view is
[`evidence/task-ledger/sr2fpga-task-evidence-status.md`](evidence/task-ledger/sr2fpga-task-evidence-status.md).
Its evidence references resolve to stable artifacts under `reports/evidence/`
or to immutable dataset metadata.

Catalog labels such as `paper1_core` describe catalog intent; they do not define
a G4b-signed benchmark population under v1.7 or create Paper-1 outcome authority.
Use the [active freeze](../docs/specs/2026-08-14-sr2fpga-paper1-research-program-design.md)
for research semantics and [current status](../docs/current-status.md) for the
present implementation boundary.

Completed named-run reports are grouped under `evidence/phase-reports/`:

- [Phase C independent-oracle qualification](evidence/phase-reports/sr2fpga-phase-c-independent-oracle-evidence-2026-07-14.md)
- [Phase D frozen pilot](evidence/phase-reports/2026-07-17-sr2fpga-phase-d-pilot-report.md)
- [Phase D failure and H2 analysis](evidence/phase-reports/2026-07-17-sr2fpga-phase-d-failure-analysis-and-h2-hardening.md)

These reports are authoritative only for their named runs. Historical commands
inside them are provenance, not current operating guidance.
