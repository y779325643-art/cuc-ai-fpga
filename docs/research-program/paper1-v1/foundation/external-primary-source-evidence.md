# External Primary-Source Evidence

Status: active M2 evidence supplement

Updated: 2026-08-29

These works were checked against current arXiv abstract/full-HTML primary
pages. They do not yet have a local PDF hash or full local reader/card/source
map chain.

## RealBench

- Canonical key: `realbench`
- Primary source: <https://arxiv.org/html/2507.16200v1>
- Version: arXiv:2507.16200v1, submitted 2025-07-22

| Evidence ID | Verified claim | Primary anchor | Paper-1 use boundary |
|---|---|---|---|
| `E-REAL-W01` | RealBench uses four real open-source IP/core designs, detailed multimodal specifications and rigorous verification. | Abstract; Introduction; Section II | Strong IP/system-level generation benchmark comparator |
| `E-REAL-W02` | It contains 60 module-level tasks and 4 system-level tasks; system-level tasks generate a complete design from hierarchy specifications. | Table I; Section II-D | Do not claim prior work lacks all system-level generation |
| `E-REAL-W03` | Reference testbenches target 100% line coverage and a formal workflow uses Yosys netlists plus JasperGold equivalence. | Section II-C | Stronger oracle than ordinary testbench; commercial formal dependency remains |
| `E-REAL-W04` | The reported o1-preview result is 13.3% formal@1 on module tasks and 0% on system tasks. | Abstract; Introduction; Results | Keep model/version/denominator attached; do not compare directly with VPP-L3@1 |
| `E-REAL-W05` | The system task focuses generated Verilog and its system-level testbench, not a method-neutral FPGA package with public/hidden authority and L3/L4 endpoints. | Section II-D; benchmark scope | Differentiate through contract/evaluator/FPGA axes, not “first system generation” |

## HWE-Bench

- Canonical key: `hwebench`
- Primary source: <https://arxiv.org/html/2604.14709v3>
- Version: arXiv:2604.14709v3, revised 2026-05-05

| Evidence ID | Verified claim | Primary anchor | Paper-1 use boundary |
|---|---|---|---|
| `E-HWE-W01` | HWE-Bench contains 417 real historical bug-fix tasks across six Verilog/SystemVerilog/Chisel repositories. | Abstract; Section 3.2 | Repository bug-repair prior art, not new-project generation |
| `E-HWE-W02` | Tasks run in containerized environments and use each project's native simulation/regression flow. | Abstract; benchmark construction | Execution-grounded repair evidence; not one uniform oracle |
| `E-HWE-W03` | Five repositories use Verilator; OpenTitan requires VCS; 172/417 tasks form the Verilator-accessible subset. | Section 3.2 | Artifact/tool availability must be reported per subset |
| `E-HWE-W04` | The current v3 table reports 70.7% overall resolved rate for the top listed agent and identifies localization, semantic reasoning and cross-artifact coordination failures. | Results and failure analysis | Preserve model/framework/version and repository distribution |
| `E-HWE-W05` | The starting state is an existing repository plus a historical bug report and ground-truth patch lineage. | Benchmark construction | It cannot replace requirement-to-new-project controls |

## CLOSER-Bench

- Canonical key: `closerbench`
- Primary source: <https://arxiv.org/html/2607.16632v1>
- Version: arXiv:2607.16632v1, submitted 2026-07-18

| Evidence ID | Verified claim | Primary anchor | Paper-1 use boundary |
|---|---|---|---|
| `E-CLOSER-W01` | CLOSER-Bench defines a budgeted cross-stage protocol pairing spec-to-RTL, RTL-to-GDS and spec-to-GDS tasks for one design/hidden objective. | Abstract; protocol overview | Closest cross-stage evaluation comparator |
| `E-CLOSER-W02` | It records simulator, synthesis, STA and P&R invocations and measures final quality, anytime progress, tool cost and cross-stage recovery. | Abstract; research questions | Supports stage/cost reporting; endpoints and task differ from FPGA VPP |
| `E-CLOSER-W03` | The implementation uses Verilator, Yosys, OpenROAD, KLayout, Sky130 and Harbor. | Abstract/method | ASIC RTL-to-GDS flow, not FPGA packing/routing or board evidence |
| `E-CLOSER-W04` | Current evidence is a ten-task pilot plus a physical-flow audit; the full three-way agent matrix is future evaluation. | Contributions/pilot | Do not describe it as a large completed benchmark campaign |

## ChipVerilog

- Canonical key: `chipverilog`
- Primary source: <https://arxiv.org/html/2607.13079v3>
- Version: arXiv:2607.13079v3, revised 2026-08-17

| Evidence ID | Verified claim | Primary anchor | Paper-1 use boundary |
|---|---|---|---|
| `E-CHIPV-W01` | ChipVerilog contains 64 generation targets from five OpenCores-derived families, including standalone, multi-module and full-system targets. | Abstract; Sections 3.1–3.2 | Large/hierarchical RTL benchmark comparator |
| `E-CHIPV-W02` | The corpus has about 20,400 Verilog lines; several targets exceed 1,000 lines. | Sections 2–3 | Supports scale/context claims only |
| `E-CHIPV-W03` | Each instance pairs a curated natural-language specification with target RTL; macro, testbench and auxiliary files are excluded from generated targets. | Sections 3.1–3.2 | It is not a complete project-package generation benchmark |
| `E-CHIPV-W04` | Outputs pass syntax/compilation/elaboration, then equivalence for module/multi-module targets or simulation for full-system targets. | Section 3.1 | No common FPGA P&R/target-profile endpoint follows |

## Registry rule

These four works are `official-primary-page verified`. Their claims may be used
only with the exact version and bounded evidence above. A local PDF hash and
section-aligned reader remain optional strengthening work.

