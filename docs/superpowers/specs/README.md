# Specs Index

Specs record approved designs and research decisions. They are not all active.
Use `../../current-status.md` for the current engineering state.

## Core SR2FPGA Specs

- `2026-06-18-sr2fpga-generation-boundary-design.md`
  - Defines the generation/evaluation boundary.

- `2026-06-18-sr2fpga-data-generation-agent-design.md`
  - V1 data-generation agent architecture.

- `2026-06-22-sr2fpga-llm-generation-entry-design.md`
  - DeepSeek project-generation entry.

- `2026-06-22-sr2fpga-deepseek-repair-loop-design.md`
  - DeepSeek repair loop and patch recording.

- `2026-06-22-sr2fpga-multimodule-task-families-design.md`
  - Multi-module deterministic task families.

- `2026-06-23-sr2fpga-autonomous-trajectory-runner-design.md`
  - Autonomous batch runner design.

- `2026-06-24-sr2fpga-system-his-v1.2-topdown-design.md`
  - Historical prototype top-down System-HIS v1.2 schema trial. **Superseded by
    the freeze spec below; `system-his-v1.2-topdown` is not a current clean-data
    target.**

- `2026-06-24-sr2fpga-system-his-v1.2-freeze-design.md`
  - **Current schema-governing spec.** Freezes `system-his-v1.2` as the single
    canonical schema (migrate deterministic generator off v1.1, v1.2 checker
    gains HIS↔RTL cross-checks, data_flow.timing, structured control_flow/FSM,
    quarantine legacy/v1.1). Tier-1 structural freeze is ratified; Tier-2 timing/
    FSM fields remain provisional until real pipelined/FSM tasks exercise them.
    Updated from the reframe hardening pass with REQ→HIS fidelity, measurement
    freeze, oracle hardening, contract-preserving skeleton generation, trajectory
    episode metadata, and data-release tier discipline.
    Implementation plan:
    `../plans/2026-06-24-sr2fpga-system-his-v1.2-freeze.md`.

- `2026-06-24-openxc7-l4-tool-stage-spike-design.md`
  - De-risk OpenXC7 (Yosys synth_xilinx → nextpnr-xilinx → bitstream) as the L4
    stage of the tool pipeline: batch, license-free post-P&R labels (real
    LUT/FF/BRAM/DSP + Fmax), runs on Windows+WSL2. Plan:
    `../plans/2026-06-24-openxc7-l4-tool-stage-spike.md`.

- `2026-06-25-system-his-constrained-decoding-design.md`
  - The TCAD method-novelty core: a decode-time mechanism making cross-file
    structural consistency hold **by construction** (Tier A deterministic shell
    from the contract + Tier B System-HIS-derived constrained decoding). Tier A
    is the next implementable contract-preserving step; Tier B is local-model-only
    because it needs logit access.

## Research Framing

- `2026-06-22-sr2fpga-research-reframe-design.md`
  - TCAD/TRETS research reframe and paper-program strategy.

## Historical Presentation Work

- `2026-06-04-hnai-fpga-project-overview-redesign-design.md`
  - Presentation redesign spec. Retained as project-deliverable history.
