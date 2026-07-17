# SR2FPGA Documentation Index

This directory contains the research objective, current engineering status,
handoff notes, design specs, implementation plans, and decision logs for
HNAI-FPGA / SR2FPGA.

## Start Here

Read these first:

1. `../README.md`
   - Repository entry point and current capability overview.

2. `research-objective-sr2fpga-tcad.md`
   - Concise project objective summary.

3. `superpowers/specs/2026-06-22-sr2fpga-research-reframe-design.md`
   - Primary research framing and paper-program spec.
   - Governs when it differs from the concise objective summary.

4. `current-status.md`
   - Short living status page for the current engineering state.
   - Use this before continuing code or dataset work.

5. `sr2fpga-task-catalog-v0.2.json`
   - Intended target contract and target policy for the 71-family task map.
   - It describes the desired curriculum and must not be read as current
     executable evidence.

6. `sr2fpga-task-evidence-v0.1.json`
   - Current executable and verification facts for each catalog family.

7. `sr2fpga-task-evidence-status.md`
   - Human-readable derived view generated from the v0.2 catalog and v0.1
     evidence ledger.

8. `sr2fpga-t0-t4-task-catalog.json`
   - Canonical machine-readable task catalog for the compressed T0-T4
     curriculum. It is the 24-alias deterministic smoke curriculum, not task
     difficulty authority; it records default widths, topology IDs, RTL
     categories, and testbench-oracle expectations.

9. `research-issues-failure-repair-2026-06-24.md` and
   `research-issues-training-data-quality-2026-06-24.md`
   - Research-significant issues found during natural LLM failure/repair runs and
     a review of the training-data contract; useful for paper motivation,
     benchmark design, ablations, and threats to validity.

10. `sr2fpga-agent-handoff-2026-06-22.md`
   - Detailed handoff and historical run notes for the SR2FPGA data agent.

11. `../CLAUDE.md`
   - Agent-facing coding guidance, invariants, commands, and git hygiene.

## Core Research Docs

- `superpowers/specs/2026-06-22-sr2fpga-research-reframe-design.md`
  - Primary research framing and paper-program reasoning.

- `research-objective-sr2fpga-tcad.md`
  - Concise objective summary aligned to the reframe spec.

- `sr2fpga-t0-t4-task-catalog.json`
  - Current T0-T4 task catalog used by
    `../configs/sr2fpga_t0_t4_deterministic_smoke.example.yaml`.

- `superpowers/decisions/2026-06-22-sr2fpga-reframe-decision-log.md`
  - Decision trail explaining how the current research framing was chosen.

- `research-issues-failure-repair-2026-06-24.md`
  - Living issue log for academically meaningful failure-repair observations.

- `superpowers/specs/2026-06-24-sr2fpga-system-his-v1.2-freeze-design.md`
  - Current schema-governing spec: freezes `system-his-v1.2` as canonical, staged
    behind a ratification gate. Plan: `superpowers/plans/2026-06-24-sr2fpga-system-his-v1.2-freeze.md`.

- `superpowers/specs/2026-06-24-sr2fpga-system-his-v1.2-topdown-design.md`
  - Prototype System-HIS v1.2 top-down architecture contract design.
    **Superseded by the freeze spec above.**

- `research-issues-training-data-quality-2026-06-24.md`
  - Living issue log for training-data-contract quality (failure-label noise,
    taxonomy drift, QoR signal validity) found while reviewing recorder/log_parser.

- `research-threats-to-validity-2026-06-25.md` (+ `.zh.md`)
  - Referee-side review of the research plan (3 reviewers + synthesis). The three
    gates to a defensible TCAD method paper: train a model (scaled, frozen
    protocol) + build constrained decoding + land one physical L4/L5 result.

- `superpowers/specs/2026-06-25-system-his-constrained-decoding-design.md`
  - TCAD method-novelty core: decode-time mechanism ensuring cross-file
    structural consistency by construction (Tier A deterministic shell + Tier B
    System-HIS-derived constrained decoding). Tier A is the next implementable
    step; Tier B requires logit access (local model only).

- `superpowers/specs/2026-06-25-sr2fpga-multi-teacher-source-design.md`
  - Multi-teacher source design. Runner draws from several independent teacher
    models in one batch so the dataset is not a single-model artifact. **Delivered
    and merged to `main` 2026-06-26.**

## Engineering Docs

- `current-status.md`
  - Current work state and next recommended actions.

- `sr2fpga-agent-handoff-2026-06-22.md`
  - Detailed SR2FPGA data-agent handoff.

- `superpowers/specs/`
  - Approved feature designs and research design records.

- `superpowers/plans/`
  - Historical implementation plans. Treat these as execution history unless
    `current-status.md` explicitly marks a plan as active.

## Deployment And Training

- `../LLM/README.md`
  - Cloud deployment, fine-tuning, model serving, and SR2FPGA agent operations.

- `../LLM/DEPLOY.md`
  - Detailed Windows/WSL deployment runbook.

- `../LLM/data/README.md`
  - Training-data format and conversion instructions.

## Documentation Organization Notes

- Keep root `README.md` broad and concise.
- Keep operational model and training details in `LLM/README.md`.
- Keep current task status in `current-status.md`.
- Keep dated handoff notes for detail and historical context.
- Do not rewrite completed plans to match current code. Add status notes in
  indexes or handoff files instead.
- Presentation/deck work under `superpowers/specs/` and `superpowers/plans/`
  is preserved as historical project-deliverable work, not active data-agent
  guidance.

## Review Draft

The cleanup rationale is recorded in:

- `guidance-docs-review-2026-06-23.md`
