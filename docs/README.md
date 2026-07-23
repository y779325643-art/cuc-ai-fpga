# SR2FPGA Documentation Index

This index separates current guidance from dated research and implementation
history.

## Current Guidance

1. [Repository overview](../README.md)
2. [Current engineering status](current-status.md)
3. [Coding-agent guidance](../CLAUDE.md)
4. [Agent project](../agent/README.md)
5. [Training project](../training/README.md)
6. [Contracts](../contracts/README.md)
7. [Dataset releases](../datasets/README.md)
8. [Runtime artifacts](../artifacts/README.md)
9. [LLM-to-Agent/Training migration](migration/llm-to-agent-training.md)

Canonical ownership is:

- `agent/`: generation, verification, repair, and trajectories.
- `training/`: conversion, training, merge, and serving. Training does not
  import Agent.
- `contracts/`: versioned cross-project schemas and task catalog.
- `datasets/`: immutable releases.
- `artifacts/`: ignored runtime output.

`not_run` is not a failure. Current reports preserve it as a separate outcome
with a skip reason.

## Research Definition

- [Research objective](research-objective-sr2fpga-tcad.md)
- [Task target catalog](sr2fpga-task-catalog-v0.2.json)
- [Executable task evidence](sr2fpga-task-evidence-v0.1.json)
- [Task evidence status](sr2fpga-task-evidence-status.md)
- [Compressed T0-T4 smoke catalog](sr2fpga-t0-t4-task-catalog.json)

The target catalog describes the intended target contract and target policy.
The evidence ledger records the current executable and verification facts. Do
not infer implementation status from the target catalog alone. The task
evidence status document is the human-readable derived view. The compressed
T0-T4 file is the 24-alias deterministic smoke curriculum, not the task
difficulty authority.

## Active Implementation

- [Repository reorganization design](superpowers/specs/2026-07-17-sr2fpga-repository-reorganization-design.md)
- [Repository reorganization roadmap](superpowers/plans/2026-07-17-sr2fpga-repository-reorganization-roadmap.md)
- [B4 compatibility and cleanup plan](superpowers/plans/2026-07-17-sr2fpga-reorganization-phase-b4-compatibility-cutover-cleanup.md)

## Evidence

- [Phase D pilot report](results/2026-07-17-sr2fpga-phase-d-pilot-report.md)
- [Phase D H2 analysis](results/2026-07-17-sr2fpga-phase-d-failure-analysis-and-h2-hardening.md)
- [Phase C independent oracle evidence](sr2fpga-phase-c-independent-oracle-evidence-2026-07-14.md)
- `reports/reorganization/`: repository-reorganization verification reports.

## Historical Records

- `superpowers/specs/`: dated research and feature specifications.
- `superpowers/plans/`: dated implementation plans and execution history.
- `superpowers/decisions/`: decision records.
- `sr2fpga-agent-handoff-2026-06-22.md`: historical handoff.
- `research-issues-*.md`: research issue logs.

Historical documents retain the commands and paths that were valid when they
were written. Use the migration guide and current project READMEs for executable
commands.
