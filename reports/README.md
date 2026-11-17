# SR2FPGA Reports

This directory contains curated evidence, human-readable reports, and retained
historical manuscript materials. The [manuscript index](manuscripts/README.md)
separates drafts, discussions, reading notes and technical notes; these materials
are not execution evidence.

The current machine-readable task evidence ledger is
[`evidence/task-ledger/sr2fpga-task-evidence-v0.1.json`](evidence/task-ledger/sr2fpga-task-evidence-v0.1.json).
Its derived human-readable view is
[`evidence/task-ledger/sr2fpga-task-evidence-status.md`](evidence/task-ledger/sr2fpga-task-evidence-status.md).
Its evidence references resolve to stable artifacts under `reports/evidence/`
or to immutable dataset metadata.

Catalog labels such as `paper1_core` describe catalog intent. They do not define
a frozen benchmark population and create no Paper-1 outcome authority. Section
16.4 of the [historical v2.1 plan](../docs/specs/superseded/2026-09-14-sr2fpga-paper1-research-plan-v2.1.zh.md)
records a catalog/ledger audit snapshot, including the fact that
`oracle_readiness` and `core_modules` were unreliable in **both** directions:
at that audit, 64 of 71 families were labelled `ready` while
the ledger shows independent-oracle evidence for 9, and an empty `core_modules`
does not mean a family is single-module. Resolve family questions against this
ledger and the referenced artifacts, not against catalog fields.

Use the [research plan v2.2](../docs/specs/2026-09-15-sr2fpga-paper1-research-plan-v2.2.zh.md)
for research semantics and [current status](../docs/current-status.md) for the
present implementation boundary.

## Static Conformance Reports

[`conformance.json`](conformance.json) records the local static checks of the
[superseded PC 2.0 design candidate](../docs/specs/superseded/PC-2.0-clean-slate-design.zh.md): 70
cases, 0 failures, 0 errors. It is scoped, in its own words, to "local static
schema/checker conformance; NOT HDL or benchmark results" — it says nothing
about generated RTL, tool stages, or model effectiveness. The candidate's `[T0]`
evidence also cites `stream_static_report.json` and `comb_static_report.json`;
**neither is present in this checkout.**

Completed named-run reports are grouped under `evidence/phase-reports/`:

- [Phase C independent-oracle qualification](evidence/phase-reports/sr2fpga-phase-c-independent-oracle-evidence-2026-07-14.md)
- [Phase D frozen pilot](evidence/phase-reports/2026-07-17-sr2fpga-phase-d-pilot-report.md)
- [Phase D failure and H2 analysis](evidence/phase-reports/2026-07-17-sr2fpga-phase-d-failure-analysis-and-h2-hardening.md)

These reports are authoritative only for their named runs. Historical commands
inside them are provenance, not current operating guidance.
