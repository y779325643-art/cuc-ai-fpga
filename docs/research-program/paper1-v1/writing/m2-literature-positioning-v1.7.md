# Paper-1 v1.7 文献定位与论文结构派生稿

Status: active M2-derived writing aid

Authority: `paper1-freeze-v1.7`

Outcome status: pre-outcome; no official method result exists

Citation registry: [`../foundation/canonical-citation-registry.md`](../foundation/canonical-citation-registry.md)

本文件是历史日志和 TCAD/TRETS 材料的当前派生稿。它不修改历史材料，
也不改变研究协议、方法条件、统计规则或评价 authority。

## 1. 稳定定位

SR2FPGA 不研究“大模型能否写出一段 Verilog”这一已被广泛覆盖的问题，
也不把 System-HIS 的存在、repository loop、EDA feedback 或轨迹保存单独
作为创新。Paper-1 检验：显式 requirement-to-project contract 经
deterministic materialization 和受控 editable surface 物化后，是否在
匹配模型、需求事实、信息权限、预算和独立终态评价下，提高 FPGA 定向
RTL 工程包的可验证成功率。

这是待实验的研究问题，不是当前效果结论。

## 2. Related Work 结构

### 2.1 Module-level RTL generation and benchmarks

VerilogEval、RTLLM 等建立了自然语言到模块 RTL、自动 testbench 和
pass@k 范式。它们适合衡量模块功能符合性，不直接覆盖 manifest、
跨文件接口、constraints、build metadata 和工程 trust boundary。
当前可使用 `verilogeval`、`rtllm`；RTLCoder 的正式 TCAD 身份、7B
模型/训练路线和 module-benchmark 边界已由本地原文核实，但完整
reader/card/source-map 仍待补齐。

### 2.2 Tool feedback and RTL repair

RTLFixer、AutoChip 和 VerilogCoder 表明 compiler、simulation 和 waveform
反馈可驱动公开修复。这些工作占据 EDA-in-the-loop 和 iterative repair
空间。SR2FPGA 的剩余问题是公开反馈收益能否经受 frozen terminal 上的
one-shot hidden final，而不是提出首个修复循环。使用 `rtlfixer`、
`autochip`、`verilogcoder`。

### 2.3 Structured specifications, IR, and executable intent

FIRRTL、CPPL、FormalRTL、ChatCPU、AGON 等分别覆盖 compiler IR、circuit
IR、可执行参考、structured description 和处理器语义 IR。System-HIS
只能定位为 requirement/project obligations 的实验载体。`M3-M2` 是
mandatory secondary representation-bundle estimate，不能解释为
typedness-only effect。HINT 身份已进入统一 BibTeX，但在 claim-level
reader/card 补齐前只标 `待核实`。

### 2.4 Repository tasks and code evolution

RTL-Repo、Phoenix-bench、CktEvo 和 HORIZON 覆盖 repository context、真实
issue 修复、已有 RTL 演化和 acceptance-gated repository evolution。
它们意味着 repository agent、Git-native state、可执行 gate 和轨迹保留
均不是 SR2FPGA 独占贡献。SR2FPGA 必须区分 existing-repository modification
与 requirement-to-new-project construction。使用 `rtl-repo`,
`phoenix-bench`, `cktevo`, `horizon`；HWE-Bench 细节保持 `待核实`。

### 2.5 Cross-stage and FPGA physical evidence

ResBench 与 Chip-Chat 分别提供资源感知评价和人类主导的物理完成个案。
当前 Paper-1 的 RQ4 只允许在命名 OpenXC7 子集上描述 L3→L4 attrition、
timing 和 resource behavior。两个历史 L4 pass 不是一般部署证据。
Target-profile adaptation 只有在单独冻结的可选扩展完成后才能主张。
使用 `resbench`、`chip-chat`；CVDP 的任务覆盖、容器化 harness 和明确的
project-inception-to-fabrication 限制已由原文核实，可用于 task-granularity
边界。CLOSER-Bench 只作 identity-level 背景，直到
claim chain 补齐。

### 2.6 Closest executable-intent neighbor

HINT 已由本地 v2 原文核实：它在 behavioral specification/oracle 与 RTL
之间引入 executable hardware-intent layer，并把 representation、checking、
acceptance 与 lowering 作为完整 route 评价。其后端证据是 SKY130 上的
Design Compiler synthesis，而不是 FPGA P&R；其反馈流程也没有建立
SR2FPGA 所需的 repair-visible/final-hidden authority separation。因此 HINT
强化了 structured-intent prior art，同时使 `M4-M3` 的 bundle 解释和 FPGA
endpoint/evaluator 边界更加必要。

## 3. v1.7 研究问题和统计地位

### RQ0 — 独立需求边界审计

RQ0 在与 VPP benchmark 分离的 sealed population 上检验 requirement
disposition。它在 M0-M5 generation 前停止，不是 RQ1/RQ2 method outcome。

### RQ1 — Contract and deterministic materialization value

Primary Holm family：

1. `M4-M3`：同一 frozen generated HIS 下的 deterministic
   materialization/edit-surface bundle；
2. `M4-M0`：完整 untrained System-HIS pipeline 相对 Direct 的端到端价值。

Mandatory secondary：

- `M3-M2`：two-stage representation bundle，只报告预声明估计，不作为
  primary，也不能救援失败的 primary。

每个 primary 只有在本地 Holm、双侧 95% 区间下界、minimum effect 和
`G_RQ1` validity gate 全部满足时，才激活对应局部主张。完整 RQ1 主张
要求两个 primary claim-activation rule 均通过。

### RQ2 — Evaluator-separated public repair

独立 RQ2 Holm family：

1. `M5-M4`：M5 online-repair bundle 的增量成功和成本；
2. `R_HIS-R_generic`：同一 frozen failing M4 checkpoint 上的 repair-policy
   probe。

`M1-M0` 是 secondary generic-repair diagnostic；`M5-M1` 是 mandatory
descriptive end-to-end comparison。

### RQ4 — Bounded physical-depth characterization

RQ4 描述命名工具、器件、任务和分母上的 L4 物理深度。它不是主方法
效应，也不授权跨设备、跨厂商、bitstream 或 board 泛化。

## 4. 摘要和 Results 占位契约

正式结果产生前，摘要只允许写研究问题、方法条件、评价设计和已实现的
有界基础设施，不填方法效果数字。

结果占位必须分开：

- RQ1 primary：`M4-M3`、`M4-M0` 的 effect、raw/Holm-adjusted p value、
  双侧 95% interval、local claim activation；
- RQ1 secondary：`M3-M2` estimate，明确标记 secondary；
- RQ2：`M5-M4` 与 `R_HIS-R_generic` 的独立 Holm family；
- RQ0：需求边界 confusion matrix 与安全阈值；
- RQ4：预声明 OpenXC7 分母、L3→L4 attrition、timing/resource；
- cost/missingness：actual、standalone、incremental cost 和基础设施缺失。

Development smoke、deterministic references、历史 L4 和 G3 conformance 不得
填入上述占位作为 official outcome。

## 5. Result-contingent claim language

| 结果条件 | 最大允许表述 |
|---|---|
| 两个 RQ1 primary 均激活 | 完整 RQ1：materialization/edit-surface increment 与 untrained end-to-end system value |
| 仅 `M4-M3` 激活 | 只写 materialization/edit-surface increment |
| 仅 `M4-M0` 激活 | 只写 end-to-end system value，不作组件归因 |
| 两个 primary 均未激活 | 不写确认性 RQ1 method-value claim；转向评价、artifact 或负结果 |
| RQ1/RQ2 混合 | 只写各自通过的局部主张，并完整报告成本、失败和 missingness |

## 6. Contribution structure

当前可写的是 prospective contribution design：

1. 将完整 RTL project package 而非单文件作为评价单位；
2. 把 deterministic materialization/edit-surface bundle 设为匹配 treatment；
3. 将 repair-visible public evaluator 与 final-only hidden authority 分离；
4. 用固定分母记录工程阶段、失败、缺失、权限和成本；
5. 在命名 OpenXC7 子集上提供有界物理深度。

在对应 gate 和 official outcome 出现前，不使用“improves”“validated
benefit”“complete benchmark”“deployment-ready”或任何首创语言。

## 7. Current outline

1. Introduction
   - 从模块级 RTL 生成转向工程交付；
   - 结构化表示存在不等于机制价值；
   - public repair 与 hidden final 的冲突；
   - v1.7 RQ0/RQ1/RQ2/RQ4 与有界贡献。
2. Background and Related Work
   - module generation；
   - tool feedback and repair；
   - structured specification/IR/intent；
   - repository tasks and cross-stage closure；
   - FPGA resource and physical evidence；
   - multi-axis positioning table。
3. Problem Definition and Evaluation Object
4. SR2FPGA Method and M0-M5 Ladder
5. Experimental Protocol
6. Results（保持正式占位）
7. Discussion and Threats
8. Reproducibility and Artifacts
9. Conclusion（保持结果条件化语言）

## 8. Evidence use

- 正文只使用 canonical citation keys。
- `已核实` 工作仍受 evidence card 的 allowed/forbidden wording 约束。
- `待核实` 工作只用于身份级陈述。
- 任何 “未发现” 必须附检索平台、查询、日期、命中与筛选记录。
- 文献事实不能替代 SR2FPGA empirical outcome。
