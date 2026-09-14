# Paper-1 v1.7 当前文献阅读总结

Status: active M2-derived summary

Updated: 2026-08-29

Evidence registry:
[`../foundation/canonical-citation-registry.md`](../foundation/canonical-citation-registry.md)

Reading coverage:
[`../foundation/reading-coverage-audit-v1.7.md`](../foundation/reading-coverage-audit-v1.7.md)

Crosswalk with the 2026-08-27 Obsidian review:
[`../audit/m2-literature-review-crosswalk-2026-08-29.md`](../audit/m2-literature-review-crosswalk-2026-08-29.md)

## 1. Current conclusion

已有工作已经覆盖模块级 RTL 生成、工具反馈修复、structured/typed hardware
representations、repository-level repair/evolution、复杂 benchmark 和部分
FPGA/physical evidence。SR2FPGA 因此不能把 Agent、typed IR、多文件、
repository loop、EDA feedback、trajectory retention 或 synthesis 本身作为
独占创新。

Paper-1 的可检验位置是：在相同 frozen requirement facts、System-HIS、
model、information privilege 和 budget 下，deterministic project
materialization/edit-surface bundle 是否相对 free project generation 提高
method-neutral `VPP-L3@1`；完整 untrained System-HIS pipeline 是否相对
Direct 有端到端价值；公开修复收益是否能通过 one-shot hidden final。

这些都是待正式实验回答的问题，不是当前结果。

## 2. Literature progression

### 2.1 Module generation established the basic task

VerilogEval and RTLLM establish natural-language-to-module RTL evaluation and
functional/design-quality metrics. RTLCoder shows that a specialized trained
7B model and RTL dataset can improve the module-generation route. These works
do not by themselves establish a complete multi-file FPGA project contract,
hidden project endpoint or named FPGA physical flow.

### 2.2 Tool feedback established public repair

RTLFixer, AutoChip and VerilogCoder show that compiler, simulation and waveform
diagnostics can guide correction. This prior art means SR2FPGA's question is not
whether feedback is useful, but whether gains under matched public feedback
survive a final evaluator-owned hidden assessment and what they cost.

### 2.3 Structured representations moved decisions upstream

FIRRTL, CPPL, FormalRTL, ChatCPU, AGON and HINT occupy different points from
compiler IR to executable intent. They show that interfaces, architecture,
reference behavior, checking and lowering can be made explicit before or during
RTL generation. They also show why a structured route is usually a bundle, not
a single typing treatment. Accordingly, v1.7 treats `M3-M2` as a secondary
representation-bundle estimate and `M4-M3` as the primary
materialization/edit-surface bundle.

### 2.4 Repository-level work displaced generic agent novelty

RTL-Repo, Phoenix-bench, CktEvo and HORIZON cover repository context, real bug
repair, existing-RTL evolution and acceptance-gated code evolution. HWE-Bench
adds 417 real historical bug-fix tasks across six large repositories,
reinforcing that repository-scale localization, semantic reasoning and
cross-artifact repair are established prior art. HORIZON makes
visible-evaluator convergence and its cost explicit, while also motivating
stronger final hidden evaluation. SR2FPGA must distinguish requirement-to-new-
project construction from existing-repository modification.

### 2.5 Broader benchmarks do not yet unify the Paper-1 endpoint

ArchXBench and CVDP broaden complexity, task categories and agent/tool
infrastructure. RealBench goes further with 60 module tasks and 4 system-level
from-scratch generation tasks, detailed multimodal specifications,
100%-line-coverage reference testbenches and formal equivalence. ChipVerilog
contains 64 OpenCores-derived targets including cross-module/full-system cases,
but excludes testbench, macro and auxiliary files from the generated target.
These works mean SR2FPGA cannot claim first system-level or hierarchical RTL
generation. Its remaining boundary is the method-neutral project contract,
matched information and budgets, public/hidden authority, fixed denominator
and FPGA endpoints.

CVDP explicitly notes that its tasks do not cover the full range from project
inception through fabrication. Pass@1/formal@1 values from these benchmarks
cannot be directly compared with `VPP-L3@1` because task units, contexts, tools
and denominators differ.

### 2.6 FPGA evidence must remain bounded

ResBench introduces resource-aware FPGA evaluation, while Chip-Chat provides a
human-intensive physical-completion case. HINT reports ASIC synthesis on SKY130,
not FPGA P&R. CLOSER-Bench evaluates budgeted spec-to-RTL/RTL-to-GDS/spec-to-GDS
closure with an open Sky130/OpenROAD flow, but current evidence is a ten-task
pilot and ASIC GDS path rather than FPGA P&R. Current SR2FPGA evidence contains
only bounded historical OpenXC7 examples. Paper-1 therefore keeps RQ4 as
named-tool, named-device,
assigned-denominator physical-depth characterization; it does not claim L5,
cross-vendor portability or general deployability.

## 3. Stable differentiation axes

Use the following axes in Related Work and the matched-work table:

1. task unit and starting state;
2. input facts and representation level;
3. generated artifact set;
4. deterministic construction and editable surface;
5. public repair-visible evaluator;
6. final hidden authority;
7. functional and physical endpoint;
8. fixed denominator, failure and missingness;
9. model/tool/cost budget;
10. public artifact and reproducibility.

No single prior paper must be declared absent on all axes. SR2FPGA's candidate
differentiation is the controlled combination and its matched experiment.

## 4. Current claim boundaries

- Do not claim first RTL Agent, first hardware IR, first repository evolution,
  first tool repair or first multi-file generation.
- Do not describe System-HIS existence as evidence of value.
- Do not interpret `M3-M2` as typing alone.
- Do not interpret `M4-M3` as skeleton text alone.
- Do not treat development smoke, deterministic references or historical L4 as
  official method outcomes.
- Do not import training, GA/NSGA-II, QoR prediction or L5 board claims from the
  broader doctoral plan into Paper-1.
- Use only registry-backed, evidence-bounded literature statements.

## 5. Reading status

This summary does not claim that every PDF in the vault has been re-read.
Current coverage is 27 claim-ready works, 3 local-PDF source-verified works and
4 official-primary-page verified works. Historical notes remain useful but are
not independent claim evidence.
