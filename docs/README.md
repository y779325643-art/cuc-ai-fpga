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

5. `research-issues-failure-repair-2026-06-24.md`
   - Research-significant issues found during natural LLM failure and repair
     runs; useful for paper motivation, benchmark design, ablations, and
     threats to validity.

6. `sr2fpga-agent-handoff-2026-06-22.md`
   - Detailed handoff and historical run notes for the SR2FPGA data agent.

7. `../CLAUDE.md`
   - Agent-facing coding guidance, invariants, commands, and git hygiene.

## Core Research Docs

- `superpowers/specs/2026-06-22-sr2fpga-research-reframe-design.md`
  - Primary research framing and paper-program reasoning.

- `research-objective-sr2fpga-tcad.md`
  - Concise objective summary aligned to the reframe spec.

- `superpowers/decisions/2026-06-22-sr2fpga-reframe-decision-log.md`
  - Decision trail explaining how the current research framing was chosen.

- `research-issues-failure-repair-2026-06-24.md`
  - Living issue log for academically meaningful failure-repair observations.

- `superpowers/specs/2026-06-24-sr2fpga-system-his-v1.2-topdown-design.md`
  - Prototype System-HIS v1.2 top-down architecture contract design.

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
