# SR2FPGA Research Specifications

Use the task-based routes in the [documentation map](../README.md). Read
[current status](../current-status.md) first only when interpreting current
implementation, verification, debt, gate status, or results.

## Current Paper-1 Authority

- [English canonical specification](2026-08-14-sr2fpga-paper1-research-program-freeze-design.md)
- [Chinese reading companion](2026-08-14-sr2fpga-paper1-research-program-freeze-design.zh.md)

The English file governs the ACM TRETS target, research questions, M0-M5 method
conditions, information boundaries, the disjoint requirement-ambiguity audit,
metrics, statistics, the optional target-profile extension, experiment gates,
and claim rules. Paper-1 does not train models. Its active version is
`paper1-freeze-v1.7`, amended before G5 natural-model and official outcomes on
2026-08-27.

## Current Code-Development Specification

- [Paper-1 code architecture and development specification v1.11](2026-08-18-sr2fpga-paper1-code-architecture-development-spec.md)

This subordinate specification maps the frozen research protocol to code
modules, interfaces, state machines, artifacts, development work packages, and
acceptance tests. Its active version is `sr2fpga-paper1-code-dev-v1.11`. It does
not modify the estimand, method privileges, gate order, or outcome rules, and it
is not evidence that a target architecture is already implemented.

## Retained Narrow Semantic Authority

- [System-HIS v1.2 freeze](2026-06-24-sr2fpga-system-his-v1.2-freeze-design.md)

This file defines the retained System-HIS semantic boundary but is not evidence
of runtime conformance. Completed plans, decisions, and superseded specs were
removed from the working tree on 2026-08-14 and remain available in Git history.
This directory contains normative research, semantic, and code-design
specifications only; transient task plans and experiment results belong
elsewhere.
