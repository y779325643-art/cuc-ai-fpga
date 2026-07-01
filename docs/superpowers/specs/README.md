# Specs Index

Specs record approved designs and research decisions. They are not all active.
Use `../../current-status.md` for the current engineering state.

## Core SR2FPGA Specs

- `2026-06-18-sr2fpga-generation-boundary-design.md`
  - Defines the generation/evaluation boundary.

- `2026-06-18-sr2fpga-data-generation-agent-design.md`
  - V1 data-generation agent architecture. **Delivered.** Task families and training
    task names have since expanded — status note added to the file.

- `2026-06-22-sr2fpga-llm-generation-entry-design.md`
  - First LLM (DeepSeek) generation entry. **Delivered.** DeepSeek was the initial
    provider example; the multi-teacher source spec generalized it — status note
    added to the file.

- `2026-06-22-sr2fpga-deepseek-repair-loop-design.md`
  - DeepSeek repair loop and patch recording. **Delivered. Still accurate.**

- `2026-06-22-sr2fpga-multimodule-task-families-design.md`
  - Multi-module deterministic task families. **Delivered. Still accurate.**

- `2026-06-23-sr2fpga-autonomous-trajectory-runner-design.md`
  - Autonomous batch runner design. **Delivered.** Two post-delivery corrections
    applied: `v1.1`→`v1.2` and `HIS2FILES`→`HIS2PROJECT` — status note added.

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
    LUT/FF/BRAM/DSP + Fmax), runs on Windows+WSL2. Legacy `agent._run_pipeline`
    references in the plan must be remapped to the current runner/local-tool
    pipeline before implementation. Plan:
    `../plans/2026-06-24-openxc7-l4-tool-stage-spike.md`.

- `2026-06-25-system-his-constrained-decoding-design.md`
  - The TCAD method-novelty core: a decode-time mechanism making cross-file
    structural consistency hold **by construction** (Tier A deterministic shell
    from the contract + Tier B System-HIS-derived constrained decoding). Tier A
    has an initial deterministic skeleton/body-merge implementation path; Tier B
    is local-model-only because it needs logit access.

- `2026-06-25-sr2fpga-multi-teacher-source-design.md`
  - Multi-teacher source design. Lets one runner batch draw from several
    independent teacher models (Claude, GPT-5.5, DeepSeek, Qwen, deterministic)
    so the trajectory dataset is not a single-model artifact. **Delivered and
    merged to `main` 2026-06-26.** Plan:
    `../plans/2026-06-25-sr2fpga-multi-teacher-source.md`.

## Research Framing

- `2026-06-22-sr2fpga-research-reframe-design.md`
  - **Current research authority.** TCAD/TRETS research reframe and paper-program
    strategy. The English file is authoritative over the Chinese companion.

## Official Eval And Complexity Ladder

- `2026-06-29-sr2fpga-official-eval-set-gap-closure-design.md`
  - **Current official-eval coverage spec.** Adds only `alu_control_unit` and
    `crc_stream_checker` to close processor-like control and checksum/data-integrity
    gaps. The public/reporting curriculum is compressed to T0-T4; integrated T4
    shell tasks remain supplemental complexity evidence, not the primary official
    aggregate until real workload references exist. Plan:
    `../plans/2026-06-29-sr2fpga-official-eval-set-gap-closure.md`.

- `2026-06-29-sr2fpga-t5-vector-mac-feature-pipeline-design.md` through
  `2026-06-29-sr2fpga-t12-replay-arbiter-shell-design.md`
  - Historical implementation specs for topology IDs t5-t12. These now map into
    compressed reporting tiers T3 (datapath and memory shells) and T4 (integrated
    host-facing system shells). Use them as supplemental complexity evidence and
    System-HIS stress cases. Do not add a new synthetic tier by default without a
    new approved design grounded in real workload/interface references.

### Compressed T-Series Reporting Tiers

| Tier | Scope | Representative tasks |
| --- | --- | --- |
| T0 | Basic RTL and benchmark coverage | `counter`, `simple_fsm`, `fifo`, `ram_read_write`, `uart_tx`, `spi_master`, `pwm_controller`, `fir_filter`, `streaming_valid_ready`, `matrix_vector_mac`, `alu_control_unit`, `crc_stream_checker` |
| T1 | Multi-module composition | `t1_event_counter`, `t2_stream_accumulator` |
| T2 | Stream/control systems | `t3_stream_fork`, `t4_dual_stream_join` |
| T3 | Datapath and memory shells | `t5_vector_mac_pipeline`, `t6_td_update_core`, `t7_policy_value_shell`, `t8_replay_sample_shell` |
| T4 | Integrated host-facing system shells | `t9_host_protocol_shell`, `t10_rl_accelerator_shell`, `t11_batch_rl_accelerator_shell`, `t12_replay_arbiter_shell` |

### Testbench Contract For T0-T4

Every generated `sim/tb_top.v` must be a black-box behavioral oracle for the
generated RTL project, not a smoke test that unconditionally prints `TEST_PASS`.

- Drive legal top-level inputs and transactions derived from the task contract /
  System-HIS behavior.
- Compute or encode expected observable outputs in the testbench.
- Compare only top-level I/O and externally visible status signals; do not use
  hierarchical DUT internals such as `dut.u_*`.
- Print `TEST_FAIL` with a reason on reset, handshake, output-data, ordering, or
  status mismatches.
- Print `TEST_PASS` only after all required input/output comparisons have
  succeeded.
- Include a timeout watchdog that prints `TEST_FAIL timeout...` if the expected
  behavior does not complete.
- Static checking must reject vacuous pass testbenches as
  `testbench_missing_functional_oracle` when `TEST_PASS` can occur without a
  prior conditional `TEST_FAIL` oracle.
- LLM project, HIS2PROJECT, and repair prompts must state the same rule so bad
  testbenches are discouraged before static checking: never print `TEST_PASS`
  unconditionally; print it only after conditional `TEST_FAIL` checks compare
  top-level observable behavior against the expected behavior.

Tier-specific minimum coverage:

| Tier | Minimum testbench behavior |
| --- | --- |
| T0 | Reset plus direct functional I/O checks for basic RTL, memory, stream, ALU, CRC, UART/SPI-style protocol outputs |
| T1 | Composition checks across module boundaries, including event gates, accumulation, ready/valid acceptance, and final observable state/output |
| T2 | Stream/control checks for fork/join behavior, backpressure, multi-input synchronization, output ordering, and readiness recovery |
| T3 | Datapath/memory-shell checks for expected arithmetic, TD/value results, replay sample content, latency-bounded valid outputs, and occupancy/status |
| T4 | Integrated shell checks for host/register transactions, IRQ/status, arbitration, batch outputs, replay packet content, and conflict/ordering cases |

## Historical Presentation Work

- `2026-06-04-hnai-fpga-project-overview-redesign-design.md`
  - Presentation redesign spec. Retained as project-deliverable history.
