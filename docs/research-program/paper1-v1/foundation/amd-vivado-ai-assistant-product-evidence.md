# AMD Vivado AI Assistant / VivadoMCP Product Evidence

Status: active M2 implementation-reference evidence

Updated: 2026-09-04

This file records product and software evidence. It is not a peer-reviewed paper
record and does not establish comparative effectiveness.

## Evidence classes

### A. Vivado AI Assistant Extension

Primary source:
<https://docs.amd.com/v/u/en-US/vivado-ai-asst>

Document identity:

- AMD document/course ID: `VIVADO-AI-ASST`;
- revision: 1.0 English;
- release date: 2026-07-01;
- course spec identifies `2026.1 EA`;
- specified tools: Vivado Design Suite 2025.2, Vivado AI Assistant Extension,
  VS Code and GitHub Copilot;
- specified boards: Versal VCK190 and Kria KV260.

Bounded official claims:

| Evidence ID | Officially described capability | Evidence boundary |
|---|---|---|
| `E-AMD-VAA-01` | MCP-based knowledge grounding and guided prompts | Exact MCP endpoints, tool schemas and trust enforcement are not published in the spec sheet |
| `E-AMD-VAA-02` | AI-assisted project creation, block design and IP integration | Course capability, not measured autonomous success |
| `E-AMD-VAA-03` | Spec-driven KV260 prototype that builds, implements and validates a complete Vivado design with custom RTL and DMA-based hardware verification | Lab description; no released task pack, trace or denominator reviewed |
| `E-AMD-VAA-04` | RTL linting, log analysis, multi-run comparison and implementation-strategy analysis | No accuracy, cost or failure accounting published in the spec sheet |
| `E-AMD-VAA-05` | Iterative AI-guided timing closure | No reproducible method/version/result matrix available here |
| `E-AMD-VAA-06` | Simulation and AXI protocol debugging | No hidden-final or evaluator-separation evidence stated |
| `E-AMD-VAA-07` | ILA/VIO insertion and JTAG-driven hardware observation on VCK190 | Demonstrated course workflow, not a general board-debug benchmark |

Not established by the reviewed official material:

- the exact assistant extension build/hash;
- LLM/provider/model version beyond the GitHub Copilot dependency;
- complete MCP tool list or agent skill list;
- whether RTL or XDC are generated, edited or selected under a stable contract;
- requirement clarification or capability-gap semantics;
- candidate/evaluator separation or hidden terminal evaluation;
- immutable terminal-selection rules;
- assigned denominator, missingness, cost or token/tool accounting;
- independent performance data;
- cross-vendor operation.

### B. AMD/Xilinx FPL 2026 VivadoMCP

Primary source:
<https://github.com/Xilinx/fpl26_optimization_contest>

The AMD/Xilinx repository contains a public `VivadoMCP` used by a DCP timing
optimizer. The README states that it starts Vivado Tcl on demand and exposes
checkpoint I/O, timing reports, critical high-fanout analysis, pblocks, route
status, physical optimization, placement, routing, raw Tcl and restart actions.
The repository targets Vivado 2025.1 and combines VivadoMCP with RapidWrightMCP.

Evidence boundary:

- this is an AMD/Xilinx-authored public software artifact;
- it demonstrates that tool-mediated Vivado analysis and physical optimization
  are no longer an SR2FPGA-exclusive capability;
- it is not identified by AMD as the complete Vivado AI Assistant Extension
  tool implementation;
- its task starts from a DCP and optimizes timing, rather than from an open
  natural-language requirement to a new multi-file project;
- the repository README includes test/demo output, but this review did not run
  it locally or treat those numbers as independent evidence.

### C. Adjacent Vitis 2026.1 AI architecture

Primary source:
<https://docs.amd.com/r/en-US/ug1702-vitis-accelerated-reference/Using-AI-Features-of-the-Vitis-Unified-IDE>

UG1702 documents Theia AI agents named Architect, Coder, Command,
Orchestrator, Universal and User_Guide; a preconfigured AMD
`vivado-doc-server` at `https://vivado.amd.com/mcp/doc-search`; and configurable
LLM skill directories.

Evidence boundary:

- this establishes AMD's public agent/MCP/skills architecture in Vitis 2026.1;
- it does not prove that Vivado AI Assistant exposes the same agents, skills or
  MCP tools;
- it must not be used as the missing Vivado AI Assistant tool/skill inventory.

## Implementation lessons for SR2FPGA

The reviewed materials are most useful as an implementation and productization
reference:

1. separate documentation grounding from action tools;
2. expose Vivado operations through a bounded MCP tool surface rather than raw
   shell automation alone;
3. package recurring tasks as guided skills/workflows for design capture,
   analysis, timing closure and hardware debug;
4. bind every run to the Vivado version, device/board and project state;
5. preserve tool logs and multi-run comparisons as user-visible evidence;
6. make environment setup and capability checks part of onboarding;
7. keep dangerous Tcl or programming actions behind explicit permissions.

These lessons affect practical implementation choices. They do not establish a
new academic baseline or comparative result.
