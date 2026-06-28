# Plans Index

Plans are step-by-step implementation records. Most files here are historical
after their corresponding code has landed. Use `../../current-status.md` to find
the active slice.

## SR2FPGA Data-Agent Plans

- `2026-06-18-sr2fpga-data-generation-agent.md`
  - V1 data-generation agent. **Delivered. Still accurate.**

- `2026-06-22-sr2fpga-llm-generation-entry.md`
  - First LLM (DeepSeek) generation entry. **Delivered.** Proof-of-concept phase;
    generalized by multi-teacher source — status note added to the file.

- `2026-06-22-sr2fpga-deepseek-repair-loop.md`
  - DeepSeek repair loop. **Delivered. Still accurate.**

- `2026-06-22-sr2fpga-multimodule-task-families.md`
  - Multi-module task families. **Delivered. Still accurate.**

- `2026-06-23-sr2fpga-autonomous-trajectory-runner.md`
  - Autonomous runner shell. **Delivered.** Extended by multi-teacher source;
    status note added to the file.

- `2026-06-24-sr2fpga-system-his-v1.2-checker.md`
  - Earlier standalone checker plan for `system-his-v1.2-topdown`. Superseded by
    the freeze plan below; retained for traceability.

- `2026-06-24-sr2fpga-system-his-v1.2-freeze.md`
  - **System-HIS v1.2 freeze implementation plan.** Implements the canonical
    schema, RTL cross-checks, `data_flow.timing`, structured `control_flow`/FSM,
    and quarantine of legacy/v1.1 data. Tier-1 structural tasks delivered;
    Tier-2 timing/FSM tasks implemented but need exercise on real pipelined/FSM
    samples. Spec: `../specs/2026-06-24-sr2fpga-system-his-v1.2-freeze-design.md`.

- `2026-06-24-openxc7-l4-tool-stage-spike.md`
  - OpenXC7 L4 tool-stage spike. Adds OpenXC7 (Yosys synth_xilinx →
    nextpnr-xilinx → bitstream) as L4. Tasks 1/2/4/5 are runbook steps on
    Windows+WSL2; Task 3 is TDD code integration testable on any machine.
    Spec: `../specs/2026-06-24-openxc7-l4-tool-stage-spike-design.md`.

- `2026-06-25-sr2fpga-multi-teacher-source.md`
  - Multi-teacher source implementation plan. **Delivered and merged to `main`
    2026-06-26.** Spec:
    `../specs/2026-06-25-sr2fpga-multi-teacher-source-design.md`.

## Deployment / Training

- `2026-06-08-llm-cloud-finetune-deploy.md`
  - Cloud deployment and fine-tuning setup. **Delivered.** Pre-dates the Actor/Critic
    model-stack definition — status note added to the file connecting it to the
    reframe spec's training task list.

## Historical Presentation Work

- `2026-06-04-hnai-fpga-project-overview-redesign.md`
  - Presentation redesign implementation plan.
