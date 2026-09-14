# Supplemental Source-Verified Evidence

Status: active M2 evidence supplement

Updated: 2026-08-29

This file upgrades three works from identity-only to `source-verified` using
local primary PDFs. It does not replace a full section-aligned reader,
evidence card, or source map.

## Evidence level

`source-verified` means:

- title/authors/version or final publication metadata were read from the PDF;
- the PDF content hash is fixed;
- the claims below were checked on named pages;
- no stronger claim may be inferred beyond the listed anchors.

## HINT

- Canonical key: `hint`
- Source: `D:\Obsidian Vault\博士开题\硬件代码生成\文献\PDF 原文\2608.07625v2.pdf`
- SHA-256: `452473E873BC5A77D5DCEC64F0F7452F0E2017510D1C281CA13349642BEFEFDF`
- Identity: arXiv:2608.07625v2; 7 pages; PDF title and nine authors match the
  canonical BibTeX.

| Evidence ID | Verified claim | PDF anchor | Allowed M2 use | Forbidden extension |
|---|---|---|---|---|
| `E-HINT-S01` | HINT is an executable hardware-intent layer between behavioral specification/oracle and RTL that makes RTL-relevant microarchitecture and lowering obligations explicit. | p.1 abstract; pp.2–3 method/related-work framing | Closest structured-intent comparator | Do not call it equivalent to System-HIS or a complete project contract |
| `E-HINT-S02` | The controlled study compares the full HINT-mediated route with Direct C2RTL/C2HLSC; the route bundles representation, checking, acceptance and lowering. | pp.4–6, workflow and experimental design | Support route-level prior art and the need for mechanism isolation | Do not infer typedness-only or lowering-only effects |
| `E-HINT-S03` | The reported physical backend is Synopsys Design Compiler `compile_ultra` with SKY130 mapped area/timing comparisons. | pp.4–6 | Distinguish ASIC synthesis evidence from FPGA P&R | Do not claim FPGA packing, placement, routing, target-profile adaptation or board evidence |
| `E-HINT-S04` | The workflow uses frozen tests/transactions and raw compiler/testbench/synthesis diagnostics in iterative correction. | pp.4–5 | Support tool-feedback comparison | Do not claim repair-visible/final-hidden evaluator separation |
| `E-HINT-S05` | RealBench AES/SDC and a Vortex-derived VPU are cross-scale feasibility cases and are not pooled into the controlled RQ1 comparison. | pp.5–6 | Bound scale/case-study evidence | Do not convert these cases into a fixed-denominator general result |

## RTLCoder

- Canonical key: `rtlcoder`
- Source: `D:\Obsidian Vault\博士开题\硬件代码生成\文献\PDF 原文\RTLCoder - Fully Open-Source Efficient LLM-Assisted RTL Code Generation.pdf`
- SHA-256: `FD623A2FABC372C434030A8A1C45293990552BA4561EC18EA4D55EE`
- Identity: IEEE TCAD, vol. 44, no. 4, April 2025, pp. 1448–1461;
  DOI `10.1109/TCAD.2024.3483089` read from PDF metadata/header.

| Evidence ID | Verified claim | PDF anchor | Allowed M2 use | Forbidden extension |
|---|---|---|---|---|
| `E-RTLC-S01` | RTLCoder is a specialized open 7B model for natural-language-to-Verilog generation, built with an automated instruction/code dataset and customized training. | pp.1448–1450 (PDF pp.1–3) | Strong model-layer/module-generation comparator | Do not describe it as project generation or no-training work |
| `E-RTLC-S02` | The paper reports a dataset of more than 27,000 instruction-code samples and emphasizes open/local deployment. | pp.1448–1452 (PDF pp.1–5) | Describe model/data contribution with exact scope | Do not transfer dataset scale or privacy claims to SR2FPGA |
| `E-RTLC-S03` | Evaluation centers VerilogEval/RTLLM-style RTL benchmarks and pass@k/model quality, not a common multi-file FPGA project package endpoint. | evaluation sections/tables, PDF pp.9–13 | Support module-vs-project distinction | Do not infer manifest/constraints/P&R/hidden-project evidence |
| `E-RTLC-S04` | The work includes model fine-tuning and preference training; it is outside Paper-1's no-training M0–M5 treatment. | method sections, PDF pp.3–8 | Bound related work and future/training context | Do not treat it as an active Paper-1 method |

## CVDP

- Canonical key: `cvdp`
- Source: `D:\Obsidian Vault\博士开题\硬件代码生成\文献\PDF 原文\2506.14074v1.pdf`
- SHA-256: `D85E66E7FA3AE80E40C810C45877FF3E2DBED515D47F2C0326779E9EE973E58D`
- Identity: arXiv:2506.14074v1; 16 pages; CC BY 4.0 metadata in PDF.

| Evidence ID | Verified claim | PDF anchor | Allowed M2 use | Forbidden extension |
|---|---|---|---|---|
| `E-CVDP-S01` | CVDP contains 783 expert-authored problems across 13 hardware design and verification categories, in non-agentic and agentic formats. | p.1 abstract; p.9 conclusion; p.16 filtered-volume appendix | Describe broader benchmark task coverage | Do not equate all tasks with complete FPGA projects |
| `E-CVDP-S02` | The infrastructure uses containerized harnesses and open tools where possible; some verification categories require commercial tools. | pp.4–5 | Compare tool-backed benchmark infrastructure | Do not infer a uniform open-source or FPGA physical flow |
| `E-CVDP-S03` | The paper reports no more than 34% aggregate pass@1 for evaluated code-generation models, with `n=5` samples used to estimate pass@1. | pp.1,5 | Use as bounded benchmark difficulty evidence | Do not compare the number directly with VPP-L3@1 or a different denominator |
| `E-CVDP-S04` | CVDP includes RTL generation/modification, module reuse, testbench/assertion generation, debugging and comprehension, but explicitly does not cover the full project-inception-to-fabrication range. | pp.4,8–9,16 | Support task-granularity and missing-coverage analysis | Do not call CVDP a complete requirement-to-FPGA-project benchmark |
| `E-CVDP-S05` | Some comprehension evaluation uses BLEU and LLM-based judging, while code-generation tasks use executable harnesses. | pp.1,4–5 | Separate outcome types and oracle strength | Do not describe all CVDP outcomes as executable functional proof |

## External primary-page continuation

`realbench`, `hwebench`, `closerbench`, and `chipverilog` still have no matching
local primary PDF in the reviewed vault, but their current arXiv primary pages
were subsequently checked. Their bounded evidence is recorded in
[`external-primary-source-evidence.md`](external-primary-source-evidence.md).
