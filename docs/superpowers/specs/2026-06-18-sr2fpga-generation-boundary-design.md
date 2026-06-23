# SR2FPGA Generation Boundary Design

## Decision

This document records the agreed end-to-end generation boundary for the HNAI-FPGA / SR2FPGA research project as of 2026-06-18.

The project should be framed as a platform-conditioned FPGA RTL project generation system, not as a board-specific Zynq-7020 generator and not as a general "LLM writes Verilog snippet" demo.

Core objective:

> Generate a complete, buildable Verilog RTL project package from system requirements and a target platform profile, then use independent external FPGA tools to evaluate whether the generated package passes simulation, synthesis, implementation, timing, and optional board-level checks.

## End-To-End Generation Boundary

The generation stage does not call external EDA tools. It produces source artifacts and predictions only.

Input:

- Natural-language system requirement or structured requirement.
- Platform profile describing the target FPGA family, part, board, clocks, reset, available IO pins, IO standards, resource limits, and target toolchain.
- Optional project-level constraints such as target frequency, latency, resource budget, interface style, and verification cases.

Generated output:

- `manifest.json`
- `system_his.json`
- Verilog RTL source files
- Top-level Verilog module
- Timing constraint file
- Physical constraint file
- Verilog testbench
- Predicted synthesis and implementation report, recorded as predicted QoR

External evaluation output:

- Lint logs
- Simulation logs and optional waveforms
- Measured synthesis report
- Measured implementation report
- Measured timing report
- Measured power report
- Bitstream or binary configuration file
- Optional board run logs

The external evaluation outputs are not model-generated artifacts. They are produced by tools such as Vivado, Quartus, Yosys, Verilator, Icarus Verilog, ModelSim, or board-level test scripts.

## Generated Project Package

The generated package should follow this structure:

```text
generated_project/
  manifest.json
  system_his.json
  rtl/
    top.v
    modules/*.v
  constraints/
    timing.xdc | timing.sdc
    physical.xdc | pins.qsf
  sim/
    tb_top.v
  reports/
    predicted_qor.json
```

Tool-generated artifacts should be placed outside the generation boundary, for example:

```text
eval/
  lint.log
  sim.log
  waveform.*
  synth_report.*
  impl_report.*
  timing_report.*
  power_report.*
  bitstream.*
  board_run.log
```

## Engineering Source Boundary

The platform generates synthesizable Verilog RTL only.

Included:

- Pure Verilog RTL modules.
- Top-level Verilog module.
- Task-specific datapath, control logic, finite-state machines, memories, arithmetic logic, and interface logic.
- Explicit clock, reset, bit width, valid/ready, start/done, or other selected control protocol definitions.

Excluded:

- Vendor IP cores.
- Third-party IP cores.
- HLS C/C++.
- Vivado block design.
- Xilinx, Intel, or Lattice primitive-heavy designs unless explicitly allowed by the platform profile.
- Generated bitstream or binary configuration files.

Rationale:

- Excluding IP cores improves portability and keeps the research closer to general RTL and IC design.
- Excluding HLS avoids mixing RTL generation with HLS compiler behavior.
- Pure Verilog RTL creates a clearer benchmark for model capability, synthesis quality, and cross-platform evaluation.

## Constraint Boundary

The platform generates timing and physical constraints according to the platform profile.

Generated timing constraints may include:

- Primary clock definition.
- Generated clock definition when justified by the design.
- Input delay and output delay constraints.
- False path or multicycle path constraints only when supported by explicit design semantics.

Generated physical constraints may include:

- Pin location assignments.
- IO standard assignments.
- Clock and reset pin assignments.
- Board-specific usable IO mapping.

Constraint generation depends on a trusted platform profile. The model must not invent board pins, voltage standards, or device resources.

## Simulation And Verification Boundary

The platform generates a Verilog testbench.

The testbench should include:

- DUT instantiation.
- Clock and reset generation.
- Deterministic test vectors.
- Boundary cases.
- Self-checking assertions or expected-output comparisons.
- Clear pass/fail logging.

Python golden models may be added later as an optional artifact for algorithmic benchmarks, but the agreed minimum boundary is Verilog RTL plus Verilog testbench.

## Predicted QoR Boundary

The platform generates a predicted synthesis and implementation report. This should be named and treated as predicted QoR, not as a real tool report.

`predicted_qor.json` may include:

- Predicted LUT usage.
- Predicted FF usage.
- Predicted BRAM usage.
- Predicted DSP usage.
- Predicted maximum frequency or Fmax range.
- Timing risk level.
- Resource bottleneck explanation.
- Memory bandwidth risk.
- Routing congestion risk.
- Confidence score.
- Assumptions used by the prediction.

Measured synthesis, implementation, timing, and power reports must come from external EDA tools. The paper should clearly distinguish:

- Predicted QoR: generated by the model.
- Measured QoR: produced by the external toolchain.

The predicted QoR task can become a research contribution by comparing prediction accuracy against measured reports.

## Manifest Contract

`manifest.json` is part of the generated package. It is the project index, metadata record, and evaluation contract.

It should identify:

- Project name.
- Top module.
- HDL language.
- Target vendor, device family, part, board, and toolchain.
- Source file list.
- Constraint file list.
- Testbench entry point.
- Predicted QoR report location.
- Interface summary.
- Clock and reset summary.
- Expected evaluation flow.

Minimal example:

```json
{
  "project_name": "counter_8bit",
  "top_module": "counter_top",
  "language": "verilog",
  "target": {
    "vendor": "xilinx",
    "family": "artix7",
    "part": "xc7a35tcpg236-1",
    "board": "arty_a7",
    "toolchain": "vivado"
  },
  "sources": [
    "rtl/top.v",
    "rtl/modules/counter_core.v"
  ],
  "constraints": {
    "timing": "constraints/timing.xdc",
    "physical": "constraints/physical.xdc"
  },
  "simulation": {
    "testbench": "sim/tb_top.v",
    "type": "self_checking"
  },
  "reports": {
    "predicted_qor": "reports/predicted_qor.json"
  }
}
```

## Platform Profile

The project is not limited to Zynq-7020. It should support platform-conditioned generation.

A platform profile should include:

- Vendor, such as Xilinx, Intel, Lattice, or generic.
- Device family.
- Exact part number when available.
- Board name when targeting a board.
- Toolchain target, such as Vivado, Quartus, or open-source flow.
- Clock sources and frequencies.
- Reset pins and polarity.
- Available IO pins.
- IO voltage standards.
- Memory resources.
- DSP resources.
- BRAM, URAM, or embedded memory availability.
- Resource budget and unsupported device features.

The platform profile is trusted context. The generator uses it to produce constraints and platform-aware RTL decisions.

## Evaluation Levels

The revised L0-L5 levels should evaluate the generated package externally:

- L0: `manifest.json`, `system_his.json`, RTL files, constraints, testbench, and predicted QoR are complete and internally consistent.
- L1: Static checks and lint pass.
- L2: Testbench simulation passes.
- L3: Synthesis passes, and measured resource usage is compared with predicted QoR.
- L4: Implementation and timing pass, and measured timing is compared with predicted QoR.
- L5: Optional board-level execution passes for supported boards.

L5 is an evaluation result, not a generated artifact.

## Academic Framing

The recommended paper framing is:

> Platform-conditioned system-requirement-to-Verilog RTL project generation for FPGA design, with offline tool-verified evaluation and predicted QoR learning.

The key distinction from ordinary LLM-to-RTL work is that the system generates a multi-file RTL project package, including constraints, testbench, manifest, and predicted QoR. The generated package is then evaluated by independent FPGA tools.

The key distinction from tool-calling agent work is that generation itself does not rely on online EDA tool calls. Tool outputs are used offline for evaluation, dataset construction, QoR prediction accuracy measurement, and later model training.
