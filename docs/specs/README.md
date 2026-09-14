# SR2FPGA Research Specifications

> [Terminology, 2026-09-08](2026-09-08-sr2fpga-terminology.md): Project Contract (PC),
> currently serialized as System-HIS v1.2; FPGA Project Package (FPP).
> DSC names the design-space contract; DP names one design point. Internal
> identifiers and historical evidence names remain unchanged.

Use the task-based routes in the [documentation map](../README.md). Read
[current status](../current-status.md) first only when interpreting current
implementation, verification, debt, gate status, or results.

## Approved Study Design (Execution Not Authorized)

- [PC field responsibility and assembly draft v1](2026-09-11-pc-field-responsibility-v1.md):
  field authority, deterministic derivation and rejection rules; not a registered runtime contract.

- [Approved PC layered-study design v1](2026-09-11-pc-layered-study-design-v1.md):
  PC generation, frozen-PC 2×2 comparison and end-to-end evaluation. Design
  structure approved; implementation, operational freeze and execution remain separate.

## Current Paper-1 Authority

- [English canonical specification](2026-08-14-sr2fpga-paper1-research-program-design.md)
- [Chinese reading companion](2026-08-14-sr2fpga-paper1-research-program-design.zh.md)

The English file governs the ACM TRETS target, research questions, M0-M5 method
conditions, information boundaries, the disjoint requirement-ambiguity audit,
metrics, statistics, the optional target-profile extension, experiment gates,
and claim rules. Paper-1 does not train models. Its active version is
`paper1-freeze-v1.7`, amended before G5 natural-model and official outcomes on
2026-08-27.

## Current Code-Development Specification

- [Paper-1 code architecture and development specification v1.12](2026-08-18-sr2fpga-paper1-code-architecture-development-spec.md)

This subordinate specification maps the frozen research protocol to code
modules, interfaces, state machines, artifacts, development work packages, and
acceptance tests. Its active version is `sr2fpga-paper1-code-dev-v1.12`. It does
not modify the estimand, method privileges, gate order, or outcome rules, and it
is not evidence that a target architecture is already implemented.

## Retained Narrow Semantic Authority

- [DSC / DP / PC / FPP terminology ledger](2026-09-08-sr2fpga-terminology.md)

- [System-HIS v1.2 freeze](2026-06-24-sr2fpga-system-his-v1.2-freeze-design.md)

This file defines the retained Project Contract semantic boundary but is not evidence
of runtime conformance. Completed plans, decisions, and superseded specs were
removed from the working tree on 2026-08-14 and remain available in Git history.
This directory contains normative research, semantic, and code-design
specifications only; transient task plans and experiment results belong
elsewhere.
