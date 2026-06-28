# SR2FPGA 研究重构设计

> **说明：** 本文是英文权威版
> `2026-06-22-sr2fpga-research-reframe-design.md` 的中文 companion，
> 供中文阅读与讨论使用。**两者不一致时，以英文版为准**。

## 状态

方向已批准；最后更新于 2026-06-26。 本文档是 Paper ① 的已确定研究路线，由 docs/research-objective-sr2fpga-tcad.md 收束而来，并被拆解为一个可发表的研究计划与完整 spec。中文 companion 文档 2026-06-22-sr2fpga-research-reframe-design.zh.md 将与本文保持同步。若本文档与 objective doc 存在不一致，则近期工作以本文档为准。

当前状态（截至 2026-06-26）：

* System-HIS v1.2 已冻结并实现，Tier-1 ratification gate 已满足。
* L0–L3 数据生成 agent 已能基于客观工具 oracle 运行；multi-teacher source 已合并。
* 已记录 discovery-level pilot findings，当前为 N≈1/tier、探索性协议、尚非规模化证据。
* 尚未完成： 规模化 trajectory data、训练后的模型 (c) / RQ3、L4 物理实现 OpenXC7 spike、数据质量修复 F/E/G。
* 通向 TCAD 的三个 gate：
    1. 在冻结协议下进行规模化模型训练；
    2. 构建 constrained decoding；
    3. 完成带 Vivado 商业参考的 L4/L5 验证结果。

日期更新历史见文末 Changelog。

---

## 目录

* §1 项目总览
* §2 动机
* §3 核心研究原则
* §4 研究问题
* §5 相关工作与差异化
* §6 System-HIS 中间表示
* §7 评价框架 L0–L5
* §8 Benchmark 设计
* §9 数据引擎
* §10 方法：工具内化模型栈
* §11 实验设计
* §12 有效性、声明与审稿防御
* §13 Paper ② 概览
* §14 Artifact 与可复现性
* §15 近期下一步
* §16 文档关系与 companion specs
* Changelog

---

## §1 项目总览

### 1.1 一句话 thesis

SR2FPGA 通过 System-HIS 中间表示，从系统需求生成多模块、跨文件一致的 RTL 工程项目，并通过一个可复现流程推进到 L4 timing closure，同时在 AC820-ZYNQ 上提供 L5 上板案例；该流程用 L0–L5 项目级评价体系量化每个层级。在该评价体系上，工具验证微调后的模型内化工具接受度，并在固定迭代预算下提升生成与自修复能力。

中文定位：面向系统需求的项目级 RTL 工程生成——以 System-HIS 中间表示 + 项目级 L0–L5 评测 + 可复现 req→bitstream→上板闭环（AC820-ZYNQ）为贡献，并以工具验证轨迹微调一个模型，使其内化工具接受度、在固定迭代预算下提升生成与自修复。

### 1.2 项目分解

这是一个 2–3 篇论文的项目，而不是一篇论文能装完的工作：

```
Paper ①  Foundation: 工具 oracle 的双重角色
         ├─ System-HIS + 项目级 L0–L5 benchmark + 可复现
         │  req→bitstream→board 闭环      （评价 / 数据贡献）
         └─ 工具验证微调模型：生成 + 自修复  （方法贡献）
                    │  产出：可复现评价 + trajectory data + QoR predictor
                    ▼
Paper ②  Optimization: 工具在环 QoR 搜索（LUT / performance / power）
         └─ 在 architecture params 上做 GA / RL with tool reward，
            使用 Paper ① 的 QoR predictor 作为快速 proxy fitness
```

依赖关系是自然的：Paper ② 的核心瓶颈是 GA/RL 需要成千上万次工具评估，而真实工具太慢；Paper ① 的 QoR predictor 本质上是一个工具蒸馏出来的快速 proxy fitness，正好解除 Paper ② 的瓶颈。因此先做 ① 不是拖延，而是 ② 的前提和加速器。

GA/RL 以及“重新训练一个大规模生成模型”不属于 Paper ① 范围，只作为 teaser 和 future work 提及。

### 1.3 目标期刊/会议

首选目标：IEEE TCAD，ACM TRETS 作为 fallback。目标应先定高，最终根据实际完成度决定投稿。二者都重视 physical-realization + reproducibility；TCAD 额外要求 TRETS 相对放松的方法新颖性，见 §12.1。对二者都有利的一点是：AC820-ZYNQ（XC7Z020）是主流商用 Xilinx 器件，所以 TCAD 审稿人关于“这是否是真实 silicon”的本能质疑已经有较好回应。

* 物理实现是主菜，不是装饰： L4 timing closure + L5 on-board runs + resource/Fmax/power reporting 是核心证据。
* 完全开放、可复现的闭环，即 req→bitstream→board，是 TRETS 很看重的卖点。作者已有的 AC820-ZYNQ 板卡，芯片 XC7Z020CLG484-2，在 OpenXC7 支持列表中，因此可以在一个真实 Xilinx 器件上构建全开源的 Yosys→nextpnr-xilinx（OpenXC7）→bitstream→board 流程，但仍需 spike 验证。所有代码、数据、脚本、设备信息公开，工具版本固定。
* 开源主流程 + 商业参考流程： OpenXC7 仍然是主要的可复现开源流程。但对于 TCAD-strong 版本，必须在代表性 L4 子集上使用 Vivado 作为 Xilinx 商业参考流程进行验证。Vivado 不用于每一个 Line-B 训练轨迹，也不替代开源流程；它的作用是作为工业 sanity check，验证 timing、QoR、DRC/methodology warnings 和约束有效性。对于 TRETS-safe 工作，Vivado 仍是可选 fallback/baseline。
* 面向 TCAD，SR2FPGA 不应仅凭开源流程声称 FPGA 物理可实现性。 更可防守的表述是：OpenXC7 提供可复现开源路径；Vivado 在代表性 L4 子集上提供商业参考验证；L5 提供少量端到端上板可行性证据。
* 方法新颖性是冲 TCAD 的差距： TCAD 不会接受“QLoRA 微调 + 工具循环”作为方法贡献，它需要真正的方法学 idea，见 §10.6，并且需要超过 TRETS 最低要求的规模。如果方法新颖性或规模没有落地，则降级到 TRETS；论文其余部分不变。

### 1.4 硬约束

* 计算资源： 本地微调使用单张 RTX 4090 24 GB。不可行： 预训练或训练一个能够正面对抗 GPT-5 / DeepSeek 的生成模型，该野心放弃。模型大小当前刻意不固定： 数据集和 benchmark 设计必须保持 model-agnostic；模型和规模将在建模阶段根据当时可用算力决定。当前优先级是构建数据集。
* 数据： 现成数据不存在；所有 trajectories 都通过本地运行工具从零生成。公开训练标签主要来自开源工具，即 L0–L3 的 Verilator/Icarus/Yosys，以及 L4-open 的 OpenXC7，因此 “tool-verified learning” 是字面意义上的——监督信号来自工具，而不是另一个 LLM。Vivado 标签是商业参考标签，只用于代表性 L4 子集，并与 open_public 训练层级分离，除非机构 license review 允许发布。标签绝不来自另一个 LLM。工具内化指的是在声明工具流下学习工具验证标签，不意味着 reverse-engineering 或复刻专有 EDA 软件。
* 硬件： 上板验证使用作者的 AC820-ZYNQ 板卡，芯片为 XC7Z020CLG484-2，约 53k LUT、220 DSP、双核 ARM，足以容纳较大设计和一个 RL flagship case。该器件在 OpenXC7 支持列表中，因此可构建全开源 req→bitstream→board 流程，但需 spike 验证；Vivado 是 fallback/baseline。

---

## §2 动机

### 2.1 为什么这个问题重要

驱动性问题是：能否把 EDA 工具链的判断内化到模型中，使模型无需在推理阶段调用工具，就能从需求生成、诊断、修复并预测项目级、多文件、物理可实现 FPGA RTL 的质量？ 这个问题值得研究，原因有三点。

* 工具是 ground truth，但推理规模上不可用。 EDA 工具，例如 Verilator/Yosys/nextpnr/board，给出的是客观 pass/fail verdict，不是另一个模型的意见；但它们昂贵、慢、外部依赖、不可微。当前 LLM-RTL 流程只能在两者之间摇摆：
    a. 忽略工具，只做 generate + simulation pass@k，但 “sim-pass ≠ silicon”，Representation Bottleneck 报告 unconditional end-to-end 只有 48%，业内实践者也指出 “fast isn’t the skill, board-ready is”；
    b. 每次推理都循环调用工具，这成熟但慢且昂贵，并且 L4 P&R 每个样本需分钟级，不适合规模化，正是 Paper ② 的 blocker。
    如果能内化工具 verdict，就能以 LLM 的速度/成本输出接近工具质量的结果，从而解锁大规模 QoR proxy search、免工具链生成以及面向领域专家的可访问性。
* 它检验一个真实、可测量的科学命题。 “硬件正确性/可实现性是否是设计的一个可学习函数，还是本质上必须运行工具？” 这是一个可以通过客观 ground truth——工具——回答的真假问题，而不是自评质量。
* 领域里的容易区域已经饱和；困难区域正是这里。 单模块仿真 benchmark，例如 VerilogEval，已接近天花板；未解决区域是 跨文件一致性 + 物理可实现性。TODAES’25 survey、ChipSeek-R1/MasterRTL/POET 的 future-work statements，以及 Representation Bottleneck 对 “an LLM-native IR separating intent from implementation” 的明确呼吁，都指向这一点。Project-level + physical 是模型真正失败的地方，也是科学问题所在。

对问题的诚实表述： 正确问题不是工具能否被完全替代，而是工具 verdict 有多少能被内化、边界在哪里。有些量受物理约束，难以内化，例如 CDC metastability、板级 signal integrity，见 §12.1。因此成功不等于“替代工具”，而是测量 (b−a) 和 (c−a)：工具在环反馈与工具验证微调分别带来多少增益；同时映射 L0–L5 中哪些边界能内化，哪些必须留给工具。即便只是部分答案，也仍然是结果。

### 2.2 为什么需要这次 reframe

对当前状态进行 harsh-reviewer pass 后发现一个真实风险：项目有高质量数据 pipeline，但尚无科学结果；初始任务如 counter、fifo、simple_fsm、ram_read_write 太简单，强 base model 一次就能 L3 pass，repair loop 不触发，failure_to_patch 为空。修正任务难度是解除多数下游问题的根。

本次 reframe 保留作者真实目标：从自然语言需求生成完整 RTL 工程，并根据工具反馈修复它的模型，但在真实资源预算下使其更可防守、更可执行。

### 2.3 实际意义

区别于上面的学术动机，这里回答谁具体受益。

* 降低领域专家使用 FPGA 的门槛。 硬件设计师少于 10 万，但最懂 workload 的人，例如 robotics、signal processing、embedded、edge-AI 领域人员，大多不会写 HDL。一个可靠的 requirement→board-ready-project 路径，可以让他们在不熟悉 HDL 的情况下获得定制硬件。具体目标包括 edge IoT、医疗可穿戴、机器人控制、小型 AI kernel 等场景；ASIC 成本太高，而通用处理器又太慢。
* 为已有 FPGA 团队节省时间与 license 成本。 EDA 流程很慢，仿真以分钟计，P&R 以分钟到小时计；同时工具有 license 成本，例如每席 Vivado。内化工具 verdict 意味着更少工具迭代、推理阶段无需 license/计算资源，以及更短设计周期。如果 (c) 接近 (b)，则意味着无需昂贵工具循环就能获得工具质量输出。
* 让小团队也能做 PPA 优化，作为 Paper ②。 如今搜索 pipeline depth、parallelism、memory banks 等 architecture params，以优化 power/area/Fmax，往往需要成千上万次慢工具运行。一个蒸馏出的快速 QoR proxy 使单 GPU 上的搜索成为可能，让小团队也能得到更优化、低功耗的边缘设计。
* 即便模型结果不理想，也能留下公共资源。 工具验证 project-trajectory dataset + L0–L5 benchmark + 在廉价真实器件上实现的 全开源、免 license req→bitstream→board 流程，可以为无法负担商业工具的研究者和小公司 democratize FPGA EDA。
* 具体应用锚点。 AC820-ZYNQ 上的 edge-RL accelerator flagship case 将完整链路落到一个真实控制/机器人 workload 上。

诚实上限，不要 overclaim： 这不会替代 FPGA 工程师。现实定位是 assistant + automated verification + first draft，而非 autonomous tape-out。物理约束工作，如大设计 timing closure、CDC metastability、板级 signal integrity，仍留给工具/人类，见 §12.1。博士阶段的现实影响范围是 小/中型设计 + 辅助式 workflow + dataset/benchmark/open-flow 作为公共资源，不是已部署产品。

---

## §3 核心研究原则

### 3.1 蒸馏工具，而不是蒸馏 LLM

此前担忧是：“你用 DeepSeek 生成和修复，然后再训练模型，这不就是在蒸馏 DeepSeek 吗？” 作者的实际意图相反，而且更强：蒸馏 EDA 工具 oracle 到模型中。 EDA 工具，如 Verilator / Yosys / Vivado / board，是昂贵、缓慢、外部、不可微的 oracle。研究问题是：模型能否内化它们的判断，从而在推理阶段不调用工具时，也能生成、预测、诊断和修复 RTL？

同一个工具 oracle 扮演双重角色：

* 它是 benchmark 的 judge，即评价 / 数据贡献；
* 它是模型的 teacher，即方法贡献。

评价与方法共享同一个工具 judge，使故事自洽。

为了保持是 tool distillation，而不是 LLM distillation：

* 输入必须是多源的，包括组合式 component-library assembly、故意 mutation/broken designs、real IP，而不能只来自一个 LLM 输出；
* 所有标签来自工具。

这种输入分布自然会产生许多失败样本，使 failure/repair trajectories 不是靠运气出现，而是由设计保证。

### 3.2 Frontier model 是 baseline，而不是竞争者

一个 frontier model 直接生成完整项目，不是竞争对手，而是链条内部的一个测量点：它正是“第一半链条、无工具反馈、首次生成”的 baseline。因此“和 GPT 竞争”从威胁变成了本工作的 baseline + ablation。更强的 frontier model 只会抬高起点；科学贡献是工具反馈在此基础上还能增加多少。

Frontier-model 状态是定性的，需要测量，不能直接声称数字，见 §11.1。当前 frontier model 能可靠处理单文件/小型 RTL，这也是 DeepSeek 能一次通过 smoke counter 到 L3 的原因；它们也能形式上输出多文件项目，但不能可靠生成大型、强跨文件一致、可 timing closure、可上板的项目。跨文件/跨模块 contract error 和 L4 timing 是其失败区域。这正是本工作要瞄准的空间，也解释了为什么 benchmark 难度必须校准到 frontier pass rate 开始下降的区域。

---

## §4 研究问题

本文 thesis 被分解为五个具体、可回答的问题。每个问题都说明如何回答、填补什么 field gap，以及当前状态。

* RQ1 — 表示。 在 requirement 和 multi-file project 之间插入一个需求级 IR，即 System-HIS，是否相比直接 req→project 能提升跨文件一致性和物理可实现性？
    回答方式： 在 cross-file-consistency error rate + L1–L4 pass 上做 System-HIS ablation，即 req→HIS→project vs req→project。
    Gap： Representation Bottleneck (2026) 显示 IR choice > model，并明确提出 “an LLM-native IR separating intent from implementation” 是 future work；TODAES’25 将 NL↔RTL IR 列为未解；CPPL 是电路级，不是需求级。
    注意： accessibility–competence paradox 意味着这必须被测量，而不能假设高层 IR 必然更好。
    状态： v1.2 generator + L0 HIS↔RTL cross-check 已实现，Tier-1 已 ratified；ablation 仍需训练模型和 req→project 分支，尚未运行。
    新增 REQ→HIS fidelity sub-metric： System-HIS 必须忠实于原始需求，而不只是与生成 RTL 内部一致。否则模型可能误读需求，生成一个错误但自洽的 HIS，然后 RTL 和 testbench 都跟随这个错误 HIS，导致 L0/L2 仍然 pass。对于 synthetic tasks，generator 产生的 oracle HIS 支持字段级比较；对于 real/external tasks，使用小规模人工审查集。
    REQ-HIS fidelity metrics：
    * interface extraction accuracy：端口名、方向、位宽、协议；
    * clock/reset fidelity：极性、同步/异步类型、释放规则；
    * parameter fidelity：width、depth、latency、parallelism、memory banking；
    * behavior-intent fidelity：FIFO / arbiter / MAC / pipeline / AXI-lite / stream 语义；
    * verification-intent fidelity：required scenarios 和 corner cases；
    * constraint fidelity：target Fmax、resource budget、board shell/profile。
* RQ2 — 工具反馈价值，即 b−a。 EDA tool-in-the-loop repair loop 相比无工具首次生成，能在项目级工具接受度上提升多少？在哪个 level / difficulty tier 提升最大？
    回答方式： 固定迭代预算下测量 (b)−(a)，按 tier 报告。
    Gap： repair loop 已成熟，如 AutoChip/MAGE/VerilogCoder/PEFA-AI，但都偏单模块/仿真，不是 project-level/physical，也没有可复用 trajectory。
    状态： baseline (a)/(b) pilot 已运行，T1/T2 repair→L3，knee 在 T3；prompt leakage 已被实验证实，见 failure-repair Issue 4，因此需要规模化和冻结 prompt。
* RQ3 — 内化，即 c−a、c vs b。 工具验证 fine-tuning 能否内化工具接受度，使首次生成、无工具 (c) 接近工具在环 (b)？一个微调后的小模型的 (c) 能否达到大 frontier model 的 (a)/(b)？
    回答方式： 在同一个 swappable generator 上比较 (c) 与 (a)/(b)。
    Gap： ChipSeek-R1 通过 per-attempt RL 内化工具反馈，但它是 ASIC/单模块，没有可复用数据集；Representation Bottleneck 认为 “IR-aware training > model scaling”。
    内化范围： generation + repair，只要 verdict 是模型生成内容的函数即可。包括 L0–L3，以及 L4 failure diagnosis/repair：nextpnr/Vivado 会输出结构化 P&R 错误，如 resource_overflow、routing_congestion、带 critical path 的 timing_violation、constraint_error，这些能映射到可执行 patch，例如减少资源、重构、增加 pipeline registers、修 XDC，形态与 L1–L3 的 diagnosis→patch 相同。不纳入 RQ3 的是 timing-pressured designs 的连续、seed-noisy 的精确 Fmax margin，这属于 RQ5 prediction。
    状态： 还没有训练模型，这是最大 open piece，也是 headline result。
* RQ4 — 失败结构 / 难度校准。 在项目级，frontier models 会沿着哪些难度轴以及 L0–L5 verification depth / hardware-semantic gap 开始失败，例如 seq-comb、backpressure、memory、CDC、timing？
    回答方式： baseline (a) 在 T1–T4 上运行，并统计 per-level failure taxonomy，即 cross-file-consistency error rate + hardware-semantic failure distribution。
    Gap： Representation Bottleneck 只测试了 tiny single-module Lattice，认为 synthesis “transparent”；project-level/Zynq 是其排除的 regime，那里 L4 会成为约束。其 seq 2.3× / memory 43% 的梯度支持我们的难度轴。
    状态： pilot + taxonomy 已有；T4 failure frontier 已记录为 discovery，即 L0→lexical→lint→sim→functional；仍需 full-level diagnostic mode + scale。
* RQ5 — QoR prediction / shift-left。 模型能否在工具执行前预测 QoR，即 LUT/FF/BRAM/DSP/Fmax？预测值与工具实测值相关性如何？
    回答方式： predicted_qor vs measured_qor calibration。
    训练信号： OpenXC7 batch L4 reports，因为 license-free + batchable 才能收集足够 L4 labels。
    可学习性拆分： post-P&R utilization，即 LUT/FF/BRAM/DSP，很大程度上是 RTL × synthesis 的函数，因此更可学习；Fmax 取决于 seed-noisy、backend-heuristic critical path，因此可以预测但存在 noise floor / calibration gap，需要诚实报告。
    Gap： MasterRTL 做 pre-synthesis PPA，是单独的 ASIC predictor；shift-left survey 指出 predicted↔physical correlation 是 open challenge。
    状态： gated，需要真实 measured QoR，即 OpenXC7 L4；Yosys L3 LUT 是 vacuous，见 Finding G；OpenXC7 spike 已有 spec + plan。该 predictor 同时也是 Paper ② 的 proxy fitness。
    新增 tool-flow split： RQ5 预测的是在声明工具流下测得的 QoR，因此 OpenXC7-QoR 和 Vivado-QoR 是分离标签。OpenXC7 标签支持可复现开源流程和潜在较大规模 L4 labeling；Vivado 标签是 L4-commercial 子集上的商业参考标签。跨工具迁移/校准在 L4-agreement 子集上报告。

Core vs gated： RQ1、RQ2、RQ4 是必须回答的最低可发表核心；RQ3 是 headline 但需要训练模型；RQ5 是 nice-to-have，并由 OpenXC7 L4 spike gate。五个问题都依赖 enabling infrastructure contribution，即 tool-verified project-trajectory dataset + L0–L5 benchmark + 可复现 req→bitstream→board 闭环，使它们可测量。

原则：保留结构化工具信号，不要二值化。 每个工具阶段都比 pass/fail + 粗标签产生更丰富的可学习信号，trajectory dataset 必须捕获结构，而不能 flatten。

* L2 sim： 不仅记录 TEST_FAIL，还要记录 mismatch detail，例如 signal、expected vs actual、cycle，理想情况下保存 VCD。这正是 diagnosis→patch 的信号，也就是 VerilogCoder 的 AST waveform tracing 所利用的东西。
* L1/L3/L4 pass 时的 warnings： “passed-but-warned” 是 soft signal，例如 latch risk、width-extension、unused/undriven nets、BRAM-miss、timing-met-but-tight，是质量/风险标签，不能通过二值化丢弃。
* L3 synth-time diagnostics，如 inferred latch、comb loop、multi-driven，以及 L4 critical-path detail，如哪些 nets/cells，告诉模型哪里该 pipeline。这些都比 cell counts / Fmax headline number 更有价值。
* predicted vs measured residual 本身就是 RQ5 calibration signal。

Raw logs 已经按 stage 持久化；差距在于 extraction：当前 diagnosis record 和 training views 将丰富日志压缩成一个 failure_type 字符串，见 training-data-quality issue log。丰富 extraction 才能使 LOG2DIAG/FAILURE2PATCH 更有针对性，并扩大可内化范围。

---

## §5 相关工作与差异化

### 5.1 现有工作如何处理每个 RQ，以及留下什么空白

按 RQ 组织。每个 RQ 说明 field 如何解决，以及本工作的切入点。

* RQ1 表示。
    Field： 直接 req→code、无 IR，例如 VerilogEval、RTLLM、RTLCoder、OpenLLM-RTL；电路级 IR，例如 CPPL：Python-DSL→circuit-JSON，并通过 compile-time width inference 保证一致性；软件级中间表示，例如 Spec2RTL-Agent via HLS C；不以 NL 为目标的编译器硬件 IR，例如 FIRRTL/CIRCT/LLHD/HIR/Calyx；输出-HDL-as-IR 研究，即 Representation Bottleneck。
    Open： 没有工作学习/评估一个 requirement-intent IR 并做 ablation；Representation Bottleneck 明确把它作为 future work → System-HIS。状态：open。
* RQ2 工具反馈，b−a。
    Field 已成熟： compile/sim feedback loops，例如 AutoChip +24.2%、RTLFixer syntax、MAGE multi-agent、VerilogCoder graph planning + AST waveform tool、PEFA-AI progressive error feedback。
    Open： 全部偏单模块 / functional / simulation；没有在 project/physical level 上，以同一 generator 跨 difficulty tiers 做清晰的 b−a delta。状态：crowded，需要通过 level + clean measurement 差异化。
* RQ3 内化，c−a / c vs b。
    Field 最 crowded： RL with tool reward，包括 ChipSeek-R1 hierarchical syntax→sim→synth-PPA reward ASIC、VeriRL trace-back rescore、VeriReason RL+testbench+reasoning、RTLSeek；SFT 如 RTLCoder、Veribench-53K；inference-time steering 如 MeltRTL、CASS-RTL。
    Open： per-attempt reward、没有可复用 trajectory dataset、单模块、ASIC/sim；没有用 “without tools 的 (c) 是否匹配 (b)” 或 “小模型是否达到大模型” 来 framing。Representation Bottleneck 的 “IR-aware training > model scaling” 支持本工作。状态：最 crowded，因此差异化必须最锋利：project-level + physical + reusable tool-verified trajectory + (a)/(b)/(c) + swappable generator。最高风险：还没有训练模型。
* RQ4 失败结构 / 难度。
    Field： 按复杂度报 pass-rate 的 benchmarks，如 ArchXBench 的 6 levels、RTL-Repo、ResBench、CVDP；failure-mode analysis 如 Representation Bottleneck 中 combinational 1.3–1.4× / sequential 2.3× / memory 43%，以及 RTLFixer 的 syntax。
    Open： 没有 project scale 上的 L0–L5 verification-depth × hardware-semantic cross-index；它们的 seq/memory gradient 支持本工作难度轴。状态：half-open。
* RQ5 QoR prediction / shift-left。
    Field： 专门的 pre-synthesis PPA predictors，通常是独立 GNN，多数面向 ASIC，例如 MasterRTL、DeepCircuitX、自监督 circuit encoder；HLS DSE predictors 如 IronMan、Chimera、AutoHLS、Intelligent4DSE；POET。
    Open： 我们的 predictor 是同一个 tool-distilled model 的一部分，不是独立 GNN；并且面向 FPGA physical L4，作为 Paper ② 的 proxy fitness，同时严格分离 predicted/measured。状态：half-open。

Crowding summary： RQ1 open；RQ2 crowded，loops 已成熟；RQ3 最 crowded，即 RL cluster，因此必须最强差异化；RQ4/RQ5 half-open。

### 5.2 Field map：每条线是什么，以及为什么不是我们

三条支撑点，需要诚实地对应当前 field，而不是停留在 VerilogEval 时代。

1. System-HIS 作为 requirement-level front-end IR
    不是 req→code，而是 req→System-HIS→project；它是显式、可学习、可评价的中间表示，位于 FIRRTL / CIRCT / LLHD / HIR / Calyx 等硬件 IR 之上，并且可以 lower 到它们。它不是替代或重写 CIRCT。决策是 shallow CIRCT coupling：定位 + 可选 lowering bridge，而不是深依赖。收益由 ablation 证明。
2. Tool-verified trajectory dataset + L0–L5 project evaluation
    护城河不是“project-level”本身：multi-file/project benchmarks 已经存在，例如 RTL-Repo、CktEvo、ArchXBench。因此真正护城河是数据单位：project trajectory，即 generate→tool→fail→diagnose→patch，并带 L0–L5 labels。这些 benchmark 没有这种数据单位。
3. 可复现 req→bitstream→board 闭环到 L4/L5
    代码、数据、脚本、设备公开，版本固定。几乎没有既有 RTL-LLM 工作达到 P&R/timing、上板或完整可复现。

Field map：

* LLM-to-RTL benchmarks / models： VerilogEval、RTLLM、RTLCoder (TCAD’25)、OpenLLM-RTL——单模块 / RTL code / pass@k。RTLCoder 是最接近 TCAD baseline 的工作：code-gen model vs 我们的 tool-verified project generation。
* Project-level RTL benchmarks： RTL-Repo，仓库上下文中的 Verilog completion，无 synthesis/physical、无 trajectory；ArchXBench，MLCAD’25，按设计复杂度划分 6 levels，frontier models 从 Level 4 开始崩，可作为 motivation。注意它的 levels ≠ 我们的 L0–L5；前者是设计复杂度，后者是 verification/physical depth 到 P&R+board。二者都没有 physical closure 或 tool-verified trajectories。
* Tool-feedback / agentic： AutoChip、RTLFixer、MAGE、Spec2RTL-Agent，spec→C++→HLS→RTL；VerilogCoder，AAAI’25 / arXiv 2408.08927，graph-based planning + AST-based waveform-tracing tool。repair/agent loops 已成熟，因此本身不是卖点。
* Representation-choice study，关键 motivation 而非 competitor：
    “From Natural Language to Silicon: The Representation Bottleneck in LLM Hardware Design”，2026 / arXiv 2604.17097。该工作用 3 个 frontier LLM × 6 种 IR，Verilog/VHDL/Chisel/Bluespec/PyMTL3/HLS-C，覆盖 202 个任务，发现 “IR choice, not model choice, is the dominant factor”，同一 IR 内换模型差 <1.25×，而不同 IR sim pass 可从 3% 到 88%。这实证支持我们的前提：杠杆在表示而不在模型，因此 frontier models = baselines。
    关键区别： 它们的 “IR” 是输出 HDL，且是 single-module、tiny Lattice iCE40UP5K、无 trajectory；System-HIS 是 HDL 之上的 requirement-level intermediate IR，面向 project-level、multi-file、XC7Z020。这是正交且互补的轴，而不是同一件事。
    最强 positioning： 该论文 discussion 明确呼吁 “an LLM-native IR that explicitly separates intent from implementation”，即进一步减少瓶颈的未来工作——换言之，System-HIS 是该论文提出的 future work 方向。
    另外两个发现也支持本设计：sequential 2.3× 和 memory 43% 的 bottleneck 比 combinational 1.3–1.4× 更严重，支持我们的 seq/comb + memory difficulty axes；它们还认为改进应来自 IR-aware training，而非 model scaling，支持 “frontier model = baseline，fine-tune on tool-verified data”。
    其 accessibility–competence paradox，即更友好的 IR 反而可能导致 LLM 性能更差，是 System-HIS 设计风险，记录在 §12.1。
    必须诚实面对的威胁： 它们发现 FPGA synthesis nearly transparent，即一旦 design pass simulation，映射到 silicon 的比例为 83–100%。这表面上质疑我们强调 L4 physical 的必要性。回答是 regime 不同：它们的设计是 educational-scale、single-module、median <50 lines、使用 5,280-LUT Lattice iCE40，并承认 industrial designs with complex hierarchies / IP integration 可能改变排序，commercial Xilinx/Intel flows 也可能不同。Synthesis transparency 是 tiny design size 的结果，不是普遍真理。我们的 project-level multi-module regime on XC7Z020，53k LUT、真实 timing closure，正是它们排除的 regime，在这里 L4 成为 binding filter。 它们 headline 的 86.5% iCE40 pass 是在 sim success 条件下的；unconditional end-to-end 为 48.1%。
* Hardware IRs： FIRRTL / CIRCT / LLHD / HIR / Calyx，以及 CPPL。CPPL 是 LLM→circuit-IR JSON→CIRCT→Verilog，输入是 Python DSL with fixed ports + docstrings，而不是 natural language；通过 compile-time width inference 保证一致性，无 physical/PnR。CPPL 在 circuit-structure level，System-HIS 在 requirement-intent level，输入是 NL requirement，并可 lower 到 CIRCT/CPPL。
    System-HIS 也不同于 IP-XACT / SysML / FuseSoC-style engineering metadata： 它们描述 IP packaging、system models 或 build integration；System-HIS 是面向 LLM 的 requirement-level generation contract。它的评价标准不是文档是否完整，而是生成和验证结果。它用作：
    a. REQ→HIS 的 supervised target；
    b. L0 HIS↔RTL cross-checking 的 ground-truth contract；
    c. tool-trajectory learning 的 data anchor。
    它的评价标准是生成项目能否通过 L0–L5，而不是 HIS 文档是否完整。
* Repo-level PPA optimization，最接近 Paper ②： CktEvo。它是 closed-loop LLM+toolchain edits，在已有 repos 上保持功能并优化 PPA；没有 L4/L5 physical labels。我们不同点是搜索 System-HIS architecture-parameter space，而不是编辑 repos，并使用 distilled QoR proxy。
* HLS DSE： NSGA-II、Chimera、IronMan、AutoHLS。它们优化给定 design point，直接与 Paper ② 相关，例如 predictor-as-proxy-fitness。
* FPGA-specific benchmark： ResBench，2025 / arXiv 2503.08823，56 题 / 12 类，功能正确性 + LUT resource estimation on FPGA；但单模块，止于 resource estimation，没有 PnR、timing closure、board、多文件项目结构。它是最近的 FPGA benchmark，但其 evidence ceiling 正是我们 L3–L5 的起点。
* RL for RTL generation，单模块 cluster： ChipSeek-R1，hierarchical reward RL、ASIC synthesis；VeriRL，trace-back rescore + Veribench-53K；VeriReason，RL + testbench feedback + chain-of-thought reasoning。它们都是单模块 / functional，没有 persistent tool-verified trajectory dataset，也没有 FPGA physical。它们共同的 future work 是 FPGA、多文件、physical——正是我们的设计空间。
* Synthetic RTL data generation： SynCircuit，HKUST 2025 / arXiv 2509.00071，diffusion-based graph generation + MCTS，用于 ML4EDA data augmentation 的 synthetic RTL circuits。它是 circuit-graph level：没有 NL requirements、没有 testbench、没有 project structure。它与我们的 compositional benchmark production 概念相邻，但目的正交。

本工作的 model/data 是在这些基础上的方法贡献，不是 SOTA-model claim。

### 5.3 我们填补的 gap

这不是为了集成而集成。LLM-for-EDA survey，TODAES’25 / arXiv 2501.09655，将这些列为 open；最强 RL/PPA 工作也把它们作为 future work。

领域承认的 gap	我们的贡献
完整多文件 / 端到端系统规格生成仍未探索	req→System-HIS→multi-file project
NL 和 RTL 之间的桥接仍是 future work	System-HIS requirement-level front-end IR
缺少系统化验证 / 可复现标准	可复现 req→bitstream→board 闭环
FPGA LLM 应用仍有限	FPGA physical implementation L4/L5
ChipSeek-R1 / MasterRTL / POET 是 ASIC、单模块、停在综合层	FPGA、多文件、到 P&R + 上板
ChipSeek-R1 没有可复用 trajectory dataset，只有 per-attempt RL reward	持久化 tool-verified trajectory dataset
ResBench 是最接近的 FPGA LLM benchmark，但单模块且止于 LUT resource estimation	L3 measured QoR + L4 timing + L5 on-board
SynCircuit 是 circuit-graph synthetic RTL，无 NL requirements、无 testbench、无可验证 project structure	requirement-level compositional generation + machine-checked testbenches + tool trajectories
LLM-to-RTL 工作大多使用黑盒 pass/fail，没有按 hardware-semantic type 分类错误	SR2FPGA hardware-semantic failure taxonomy cross-indexed against L0–L5，见 §8.4

诚实 caveat： 这些是被 field 承认的 gaps，但只有真正执行到 L4/on-board，并构建真实 trajectory dataset，贡献才成立。否则会退化成“把已知方法移植到 FPGA”。

### 5.4 核心论点

“Project-level”的重点不是代码更大，而是 correctness structure，即多模块 + 跨文件/跨模块一致性，以及 physical realizability，即综合 / timing closure。System-HIS 是从 requirement 到该结构的桥梁，表达功能、端口、位宽、clock/reset、FSM、datapath、storage、interfaces。入场门槛是：生成对象必须是 variable-topology multi-module design，即 top 实例化多个 submodules，并且各文件之间 ports/params 一致；不能只是固定 6-file template，否则 “project-level” 会坍缩。

---

## §6 System-HIS 中间表示

canonical schema 是 system-his-v1.2，已冻结并实现。完整字段定义见 docs/superpowers/specs/2026-06-24-sr2fpga-system-his-v1.2-freeze-design.md；prototype -topdown 和 inline v1.1 已被 superseded。本节保留论证、aspect skeleton、原则和 well-formedness rules；freeze spec 是字段权威来源。

### 6.1 Schema：v1.2 canonical

抽象层级已确定： structure contract + coarse behavior tags，不是完整 behavioral spec。System-HIS 捕获 components / instances / interfaces / connections / params，以及一行 behavior intent；功能正确性由 L2 testbench 验证，不在 HIS 中完整描述。这样可保持 HIS 是 intent abstraction，而不是另一个 RTL；也使 REQ→HIS 可学习，并让 compositional generator 能可靠输出。L0 检查 HIS 与结构的一致性；L2 检查功能。

v1.2 aspect skeleton，按 FPGA architect 的思考方式组织：

```
schema_version: "system-his-v1.2"
intent:       {user_prompt, design_goal, assumptions}      # 在 contract 之上保存原始请求
top:          {name, parameters, clocks, resets, ports, interfaces}   # 设计边界优先
components:   [{name, semantic_kind, source, parameters, ports, intent}]   # 可复用模块定义
instances:    [{name, component, parameter_values, clock, reset, owns_state}]  # 具体模块实例，可重复实例化
data_flow:    [{name, path:[top.x|inst.port], width, protocol, cdc, timing:{latency_cycles, initiation_interval, throughput}?}]
control_flow: [{kind, when:<guard depth≤2>, effect, related_state, related_flows}]  # fsm_transition / enable_rule / stall_rule …
state:        {registers, counters, fsms:[{states, initial, reset_state}], buffers, memories}
timing:       {primary_clock, target_fmax_mhz, constraints}
resources:    {optimization_goal, expected:{lut?, ff?, bram?, dsp?}}    # model-side → predicted_qor.json
verification: {testbench, scenarios, pass_condition}       # 引导自动 testbench 的验收条件
artifacts:    {top_module, rtl_sources, testbench, constraints, manifest, predicted_qor}   # 映射到 project package
```

默认 clock/reset 纪律，用于固定标签语义，即 Finding F：

* 默认 task family 为 single-clock；
* 默认 reset 为 synchronous, active-high；
* asynchronous reset 只出现在明确标注的 task families 中；
* reset deassertion 必须同步；
* multi-clock / CDC tasks 是单独难度族，不混入普通任务。

System-HIS 中的 canonical shape：

```
clocks:
  - name: clk
    frequency_mhz: 100
resets:
  - name: rst
    polarity: active_high
    kind: synchronous
    deassertion: synchronous
```

L0/L2 检查 reset polarity/kind 是否与 System-HIS 匹配，以及 valid/state outputs 是否达到声明的 reset state。

Memory intent fields，使 BRAM inference 成为可检查项，而不是感觉：

* memory_style: block | distributed | registers
* depth, width, read_latency, read_type: sync | async
* read_during_write behavior，byte_enable 可选

L3 检查：expected BRAM/DSP usage vs measured mapping；unexpected FF/LUT memory expansion；即使功能通过，BRAM miss 也作为 soft QoR failure。

双重用途，这说明 System-HIS 是贡献而非旁路 artifact：它既是生成中的中间监督目标，即 REQ→HIS，也是 L0 checker 验证 generated RTL 的 ground-truth contract。

Quarantine： legacy / system-his-v1.1 samples 会被标注并保留以便追溯，但排除在 clean REQ2HIS training split 之外。不提供 migration tool；在 v1.2 下重新生成是获得 clean data 的路径。

随着新增 design families，字段可逐任务扩展，例如 Paper ② 的可搜索 architecture params：parallelism / pipeline depth / memory banks，会后续放入这里。

### 6.2 六条原则：System-HIS 作为 typed IR

System-HIS v1.2 在核心 schema 层面冻结，包括字段名、必需 top-level aspects、JSON/YAML 形状和训练目标格式。非破坏性的 validation extensions 可以继续演进，不需要 schema version bump。

1. 类型化契约字段，而不是 prose。
    intent，即 user_prompt、design_goal、assumptions，只是 provenance 和解释性上下文；它不会作为隐式语义来源被 L0/L2 checkers 使用。所有机器可检查语义必须出现在 typed fields 中：top、interfaces、components、instances、data_flow、control_flow、state、timing、resources、verification、artifacts。
2. Well-formedness。
    每个 instance 必须解析到 component；每个 data-flow endpoint 必须解析到 port 或 interface；width、direction、clock、reset、protocol 必须兼容；CDC path 携带 synchronizer intent；memory 和 protocol intent 必须被 lowerer 支持。见 §6.3 的 W1–W10 well-formedness rules。
3. Interface-first FPGA semantics。
    Ports 是物理信号边界；interfaces 是语义 bundle。valid-ready、AXI-stream、AXI-lite、BRAM、GPIO 等协议携带 role、channels、ordering、backpressure、reset behavior 和 checker templates。L0 检查 ports；L2/L2-UVM/L5 依赖 interfaces。
4. Bounded control grammar。
    control_flow.when 和 control_flow.effect 使用受限、类型化的 guard/effect 语言，guard nesting ≤ depth 2。自由文本 intent 可以解释 rule，但只有 typed guards/effects 会被检查或 lowered。
5. Contract-preserving lowering。
    System-HIS lower 为：symbol table → project manifest → top shell → module declarations → interface bundles → testbench scaffold → assertion/checker templates → logical constraints → board-shell binding → model-fillable behavior holes。它通过构造保证跨文件结构一致性；完整行为正确性交给 L2。
6. Canonicalization。
    canonical JSON serialization、stable IDs，与人类可读名称无关、deterministic field ordering，以及 normalized parameter expressions，用于 hashing、diffing、REQ→HIS fidelity scoring、L0 checking 和 training targets。

Intent / Contract / Advisory 字段分类：

类别	字段	Checker 角色
Intent	intent.*、解释性字符串	仅用于 provenance，不被 L0/L2 使用
Contract	top、interfaces、components、instances、data_flow、control_flow、state、verification.pass_condition	L0/L2 必须满足
Advisory	resources.expected、timing.target_fmax_mhz、predicted_qor	QoR/optimization hints，失败是 soft budget miss，不是功能失败

### 6.3 Well-formedness rules W1–W10

* W1. 每个 instance.component 必须引用恰好一个已声明的 component。
* W2. 每个 data_flow.path endpoint 必须通过 symbol table 解析到已有 top port 或 instance port。
* W3. 每条连接上的 port widths 和 directions 必须 type-compatible。
* W4. 每个拥有 state 的 instance 必须绑定到已声明的 clock 和 reset。
* W5. 声明为 combinational 的 component 不能拥有 state、clock 或 reset。
* W6. 每个 cdc:true data-flow 必须跨越两个不同 clock domains，并通过 synchronizer component 或显式声明的 CDC primitive。
* W7. 每个 memory intent 必须声明 depth、width、read_latency、read_type，如果要评估 BRAM/distributed/register mapping，还必须声明 memory_style。
* W8. 每个 verification scenario 必须引用已有 interfaces/signals，并映射到 lowerer-supported stimulus/checker template。
* W9. 每个 logical constraint 必须引用已声明 clocks/ports，并且不能 override board constraints。
* W10. artifacts 中列出的每个 artifact path 必须能由 manifest.json + top_module 可复现地产生。

### 6.4 H0/H1/H2 validation levels

这些验证在 L0 RTL checker 运行之前执行：

* H0 — schema-valid：JSON/YAML 形状、必需字段、enum values。
* H1 — well-formed：symbols 可解析、endpoints 存在、widths/types 兼容、W1–W10 通过。
* H2 — lowerable：所有 components/protocols/scenarios 都被当前 lowerer 和 testbench generator 支持。

REQ2HIS 模型输出在进入 L0–L3 pipeline 前必须经过 H0/H1/H2 评价。H0/H1/H2 失败有自己的 req_his_* diagnosis class，并且可以由 FAILURE2PATCH actor 修复，而无需运行 EDA tools。

### 6.5 REQ→HIS fidelity failure modes

req_his_missing_requirement | req_his_wrong_width | req_his_wrong_protocol
req_his_wrong_reset_kind | req_his_wrong_latency | req_his_missing_corner_case
req_his_over_specified_behavior | req_his_under_specified_interface

### 6.6 System-HIS v1.2 的 non-goals

System-HIS 不旨在：替代 FIRRTL/CIRCT/LLHD/Calyx 作为电路或编译器 IR；完整描述 cycle-accurate behavior；编码板级物理实现细节；作为 IP-packaging standard，例如 IP-XACT；使工具执行不再必要；或在没有 testbenches/properties 的情况下证明功能正确性。

---

## §7 评价框架 L0–L5

### 7.1 Level overview

* L0 project contract + cross-file consistency，即 HIS↔RTL checker；
* L1 lint，使用 Verilator，并执行 synthesizable-subset 纪律；
* L2 functional simulation，使用 Icarus Verilog，并且 coverage-qualified；
* L3 synthesis + measured QoR，使用 Yosys synth_xilinx；
* L4 place-and-route timing closure，OpenXC7 primary + Vivado commercial reference；
* L5 sparse representative on-board runs，AC820-ZYNQ XC7Z020CLG484-2。

工具链：全开源 primary，Vivado fallback。 L0–L3 使用开源工具 Verilator / Icarus / Yosys，可支撑 thousands of samples；L4/L5 使用 OpenXC7 nextpnr-xilinx 在 AC820-ZYNQ 上运行，但需要 spike 验证。Vivado 是 fallback/baseline：对于 TRETS-safe 工作是可选；对于 TCAD-strong，需要最小 Vivado commercial-reference subset。所有代码、数据、脚本、设备公开，工具版本固定。

### 7.2 L0：project contract 与跨文件一致性

L0 consistency checker 是一个命名组件，而不是旁注。 它根据 System-HIS contract 验证生成 RTL：top 是否实例化声明的 modules；每个 port name/direction/width、parameter 和 cross-module connection 是否与 System-HIS 匹配；testbench 是否实例化真实 top；constraints 是否引用真实 ports。这自动化了 cross-file-consistency verdict，并产生 “cross-file consistency error rate” 指标。这是单文件 benchmark 在结构上无法做到的检查。

### 7.3 L1：lint

L1 检查 implicit nets、width truncation、unused/undriven signals、inferred latches、combinational loops、sequential logic 中的 blocking assignment、combinational logic 中的 nonblocking assignment，从而执行 §8.5 定义的 SR2FPGA synthesizable RTL subset。

### 7.4 L2：functional simulation

L2 pass 不是简单的 “simulation finished”。 对 benchmark/evaluation items，L2 被报告为 coverage-qualified functional acceptance：

* L2a directed smoke tests；
* L2b randomized/stress scenarios；
* L2c required protocol/value coverage。

设计只有在声明 test contract 下才被接受为 syntactically and functionally accepted；因此 L2 pass/fail 会同时报告 scenario/coverage profile。

各 family 的最小 coverage targets：

* valid-ready / stream： valid 在 ready 为低时保持，randomized stalls、bursts、idle cycles、reset during transaction；
* FIFO / skid buffer： full、empty、almost_full/empty、simultaneous push-pop、overflow/underflow attempts；
* pipeline： 不同 latency paths、stalls、flush/reset during in-flight data；
* arithmetic： signed/unsigned、boundary values、overflow/truncation cases；
* memory/BRAM： read-after-write、same-address conflict、sync vs async read behavior；
* AXI-lite/stream subset： ordering、WSTRB、response channel、back-to-back transactions。

Public/hidden/stress test split： 每个 evaluation item 可包含多个 scenario classes：

* public scenarios： generation/repair loop 可见；
* hidden scenarios： 仅用于最终验收；
* randomized scenarios： 固定 seeds，并记录在 trajectory 中；
* stress scenarios： reset during transaction、backpressure、boundary values、full/empty、resource/timing stress。

最终 L2 acceptance 基于 hidden + stress suite，而不是 public smoke tests。这样可以防止模型或 repair loop “只修到刚好通过可见 testbench”。所有 seeds 记录以保证可复现。

Protocol assertion library： 对 protocol-heavy designs，generator 从 System-HIS protocol intent 生成 assertions/checkers，即 protocol_agents，可以是 SVA 或 immediate assertions。这些 checks 补充 scoreboards。例子包括：

* valid high 且 ready low ⇒ payload 必须保持稳定；
* FIFO：empty 时不能 read，full 时不能 write；
* reset 清除 valid/state outputs；
* 不允许 data drop 或 duplication；
* 支持子集中的 AXI-lite/stream ordering 和 response checks；
* 在可结构检查时检测 combinational ready-valid loop。

Checker provenance： assertions/checkers 是由 templates 生成的可信验证 artifacts，不是模型生成的 oracle logic。Checker 的正确性由 generator 负责，而不是 LLM。

L2F — optional property checks： 对选定 protocol-heavy task families，SR2FPGA 可以运行从 System-HIS protocol intent 生成的 bounded formal / property sanity checks。这只是可选代表性层，不是将范围扩展为完整 formal verification：

* FIFO：任意 bounded sequence 下无 overflow / underflow；
* valid-ready：bounded transaction windows 内 stall 时 payload stability；
* reset convergence 在有限 cycle count 内完成；
* one-hot FSM invariant；
* bounded transaction windows 内无 data duplication / drop；
* 支持子集中的 AXI-lite response ordering。

L2F 不要求每个 Line-B trajectory 都运行，也不 gate L2 pass。它在 benchmark/eval items 上运行，并作为 supplementary property acceptance score 报告。

L2S — optional post-synthesis netlist simulation： 在 Yosys synth_xilinx / write_verilog 输出的 synthesized netlist 上运行同一个 black-box testbench，并比较 RTL-sim 与 netlist-sim 行为。这能捕获综合后行为与 RTL 仿真不一致的构造：incomplete case、latch inference、RAM read semantics、uninitialized state、X-optimism、blocking/nonblocking misuse、memory-mapping differences。L2S 不要求每个大规模 Line-B trajectory 都跑，但应在 benchmark/eval set 和代表性子集上运行。

L2-core vs optional L2-UVM：

* L2-core： deterministic black-box self-checking simulation，是 Line B 默认路径；
* L2-UVM： 对选定 protocol-heavy tasks 使用可选 transaction-level UVM verification，例如 valid-ready stream、FIFO/skid buffer、AXI-stream subset、AXI-lite register block、RL-accelerator host interface。

UVM environments 由 System-HIS + trusted templates 生成，不允许 LLM 自由编写。L2-core vs L2-UVM stress ablation： 报告 directed L2 通过但 randomized/coverage-driven L2-UVM 失败的案例，以及 coverage deltas。

### 7.5 L3：synthesis + QoR

Synthesis 使用 Yosys synth_xilinx。L3 检查：

* expected BRAM/DSP usage vs measured mapping；
* unexpected FF/LUT memory expansion；
* 即使功能通过，BRAM miss 也作为 soft QoR failure。

不要把 generic Yosys-L3 LUT 作为强 QoR claim； 有意义的 FPGA QoR 使用 synth_xilinx 和/或 OpenXC7/Vivado L4 reports，见 Finding G。

### 7.6 L4：place-and-route timing closure

L4 被报告为三个 sub-verdicts：

* L4-open： 使用 OpenXC7 / nextpnr-xilinx 在 AC820-ZYNQ，XC7Z020CLG484-2，上做 place-and-route timing closure。这是主要可复现开源物理流程，但依赖 board-specific OpenXC7 spike。
* L4-commercial： 使用 Vivado 对相同 RTL、相同 generated core、相同 fixed board shell、相同 part XC7Z020CLG484-2 和相同 logical timing constraints进行 synthesis + implementation。L4-commercial 对 TCAD-strong 版本的代表性子集是必需，但不要求每个 Line-B trajectory。
* L4-agreement： 报告 OpenXC7/Vivado 在 pass/fail、utilization、WNS/Fmax、DRC/methodology warnings 和 runtime 上的一致与不一致。

L4 pass 需要满足以下全部条件，而不只是生成 bitstream：

1. place-and-route 完成；
2. 在声明目标频率下 target clock met，即 WNS ≥ 0；
3. 无 unconstrained clocks；
4. 无 unconstrained endpoints，除非明确解释并记录；
5. 无 black boxes；
6. 无 invalidating implementation 的 critical warnings；
7. post-P&R utilization 满足声明 resource budget；
8. generated core 通过 board shell 连接，且没有被优化掉；
9. timing/utilization/DRC reports 已归档。

对于 Vivado runs，归档：report_timing_summary、report_utilization、report_clock_utilization、report_drc、report_methodology、report_io，以及可选 report_power。对于 OpenXC7/nextpnr runs，归档：placement/routing logs、timing summary、device utilization、constraint/IO errors、bitstream generation status。

L4 pass 分开报告为：

* L4-open-pass： OpenXC7/nextpnr 在声明约束下完成 P&R 和 timing。
* L4-commercial-pass： Vivado 在声明目标时钟下完成 synthesis、implementation、DRC/methodology checks 和 timing。
* L4-agreement： OpenXC7 和 Vivado 在 physical verdict 上一致，或不一致被明确分类和解释。

设计只有在 Vivado 完成以下内容时才算 commercially validated：synthesis；opt/place/route；timing summary；utilization report；DRC report；methodology report；no black boxes；no unconstrained clocks；no unjustified unconstrained endpoints；WNS ≥ 0 under declared target clock。

OpenXC7：可行但仍待 spike，不是已完成证据。 OpenXC7 为 Zynq-7 target 提供了可行的全开源 L4/L5 路径，但在 board-specific spike 完成前，不能把它当作证据。OpenXC7 spike 必须验证： exact part/package/speed grade XC7Z020CLG484-2；board clock/reset/pin profile；XDC/PCF constraint correctness；bitstream generation；bitstream loading；board-shell smoke test；与 Vivado 在相同 RTL 和 logical constraints 上对比。

面向 TCAD，SR2FPGA 不应仅凭开源流程声称 FPGA 物理可实现性。 更可防守的表述是：OpenXC7 提供可复现开源路径；Vivado 在代表性 L4 子集上提供商业参考验证；L5 提供少量端到端上板可行性证据。

Commercial-tool reference validation： SR2FPGA 将 Vivado 作为代表性 L4 子集的商业参考流程。OpenXC7 仍是主要可复现开源流程，并在可行时作为可规模化物理标签来源；Vivado 用来验证 SR2FPGA-generated projects 能被主流商用 Xilinx FPGA flow 接受，并确保 timing/QoR 结论不只是开源工具链 artifact。

该对比不是完整商业规模 benchmark。它使用相同 RTL、相同 generated core、相同 fixed board shell、相同 Xilinx part XC7Z020CLG484-2、相同 logical timing constraints。论文报告 OpenXC7/Vivado 在 pass/fail、utilization、WNS/Fmax、DRC/methodology warnings、runtime 上的一致性，并明确分析不一致案例。

OpenXC7/Vivado disagreement taxonomy：

不一致案例不会丢弃，因为它们是有用的工具链证据：

* D0 both_pass；
* D1 OpenXC7_pass / Vivado_fail；
* D2 OpenXC7_fail / Vivado_pass；
* D3 both_fail_same_reason；
* D4 both_fail_different_reason。

原因标签：synthesis_mapping_difference、BRAM/DSP_inference_difference、constraint_interpretation_difference、timing_model_difference、routing_heuristic_difference、unsupported_primitive、invalid_XDC_or_board_constraint、unconstrained_path_detected_by_one_tool、critical_warning_policy_difference。

### 7.7 L5：board validation

L5 使用固定、人工审查过的 board harness。模型不生成整个板级工程。通过拆分三层，可以避免 board-level 噪声进入 pass-rate metric：

* generated core： SR2FPGA 生成、修复和评价的 RTL；
* fixed board shell： clock/reset、pin constraints、AXI-lite/BRAM/UART/GPIO bridge、reset synchronizer、debug/status registers；版本锁定并人工审计；
* host harness： Python/C 脚本，写入 input vectors、启动 core、读取 outputs/status/signature，并与 golden checksum/model 比较。

L5 pass 要求： bitstream 成功加载；host script 无 timeout 完成；generated core 通过 fixed shell 接收输入并产生输出；output signature/checksum 与 golden model 匹配；board log 和 host log 已归档。

L5-min，即上板范围： 1–3 个代表性设计；fixed board shell；host script；golden checksum/signature；归档日志。

L5-scale 明确不属于 Paper ① 范围。 L5 作为端到端物理可行性证据报告，不是大规模 pass-rate metric。

### 7.8 Verdict mode vs full-level diagnostic mode

为了防止早期 L0 failure 遮蔽 L1–L4 hardware-semantic failure distribution，见 Issue 5，将运行两种评价模式：

* Official verdict mode： 第一个 failing level 决定官方 Lk acceptance level。
* Full-level diagnostic mode： 在早期失败后，尽可能安全地使用 wrappers/normalization 继续收集额外 L1–L4 信号。

Diagnostic signals 不会提升 official pass level；它们只用于 failure taxonomy、LOG2DIAG 和 deeper failure-distribution analysis。

---

## §8 Benchmark 设计

### 8.1 Item form

单个 item 的形式是 verification-based，而不是 reference-matching。 RTL 没有唯一正确答案，因此 ground truth 是 “passes the acceptance criteria”，而不是“匹配某个 reference file”。输入 = NL requirement + machine-readable interface contract。判断 = L0–L5 tool verdicts + functional testbench。

### 8.2 生产机制：compositional

* 一个参数化 primitive component library，包括 FIFO、arbiter、CDC synchronizer、pipeline stage、ALU slice、register file、protocol adapter、decoder 等；
* 一个topology generator，将 components 连接成 multi-module systems，例如 chain / tree / bus-attached / producer-consumer，并自动保证 interface-contract consistency；
* diversity = component types × parameter space × topology × protocol variant × name randomization，即组合爆炸，而不是固定 template 数量；
* generator 同时输出 (requirement, System-HIS, contract, testbench, constraints, reference impl)。reference impl 通过 testbench，给出了 testbench 的 machine-checked self-consistency，这是优先选择 program generation 而不是 LLM-authored tests 的关键原因。
* 算法类任务的 golden model： self-consistency 只证明 RTL reference 和 testbench 一致，不证明它们算的数学是对的。对于算法模块，如 FIR、FFT、matrix-multiply、CORDIC、accumulators、MAC，generator 还必须输出软件 golden model，如 Python/NumPy，用于产生 testbench expected values，使 L2 能捕获“能跑但数值错”的 bug。
* 与 SynCircuit 的区别： SynCircuit，HKUST 2025，在 circuit-graph level 使用 diffusion + MCTS 生成 synthetic RTL，用于 ML4EDA data augmentation；没有 NL input、没有 testbench、没有 project structure。我们的生成发生在 requirement-intent level，产生可验证 multi-file projects + acceptance testbenches + tool trajectories。

Testbench discipline： 只测试 black-box interface contract，即 port behavior、protocol timing、functional correctness；绝不依赖 internal signal names / implementation details。这样 benchmark 对任何 implementation 都是公平的。

Anti-leakage： held-out parameter combinations + randomization 使具体实例基本不可能出现在训练语料中。泄漏风险来自 real open-source IP，而不是 synthetic instances。

Sources 混合： compositional synthetic tasks 是主体，具有可控难度、可规模化、leakage-safe；少量 real open-source IP，例如 OpenCores / LiteX，作为 external-validity anchors。LLM 可以只在表面上重写 program-generated requirement text，使其更自然，但只能改 wording，不能碰 semantics 或 acceptance，以缓解 “synthetic NL” 批评。

Scale： thousands 到约 10k samples，而不是 millions，符合现实数据量。Benchmark items 主要是 small/medium multi-module designs，RL-sized accelerator 是 flagship case，不是主体。已有 deterministic ProjectGenerator 是 component library 的种子。

### 8.3 Difficulty tiers T1–T4

四个 difficulty axes，前两个为 primary：

1. cross-module / cross-file consistency，即 interface/param contracts 数量，是 primary；
2. timing pressure，即 target Fmax / critical-path depth，是 primary；
3. protocol/control complexity，从 register → valid/ready → backpressured pipeline → AXI4-Lite/Stream；
4. structural scale，即 submodule count / hierarchy depth，以及 CDC，为高难度 tier。

Difficulty tiers 将这些轴映射到 T1 Easy / T2 Medium / T3 Hard / T4 Stress，依据 submodule count、cross-module contracts 数量、protocol class、target Fmax 等。在 baseline (a) measurement 期间固定具体阈值。Pass rates 按 tier 报告，使 frontier models 开始失败的 knee 可见。

Freeze protocol： difficulty thresholds 在 pilot set 上基于 baseline (a) frontier-model pass rates 校准一次，并在 official evaluation 前冻结。不得在看到 fine-tuned model results 后再调参。calibration run 记录每个 tier 的 expected submodule count、cross-file contract count、protocol class、target Fmax range 和 observed frontier pass-rate range，以便审稿人验证 freeze 早于 (c) measurement。

### 8.4 Hardware-semantic gap taxonomy，命名贡献

它是什么： LLM 预训练主要来自软件语义，即顺序执行，而硬件的并发/物理语义不同，因此会系统性失败。关键是，每类 gap 会在不同 verification depth 暴露，所以 L0–L5 hierarchy 不只是“验证深度”，也是“所需 hardware-semantic understanding 的深度”。这将 failure-taxonomy contribution 从“我们有一个 taxonomy”重构为“我们将 software→hardware semantic gap 映射到 verification-depth hierarchy”，并说明为什么只停在 L2/L3 的 prior work 只覆盖了前半段 gap。

Semantic-gap class	暴露层级	我们的工具能观测吗？	如何观测
seq/comb confusion	L1 lint	yes now	Verilator named warnings: MULTIDRIVEN, LATCH, COMBDLY, BLKSEQ
valid-ready backpressure	L2 sim	yes，前提是 testbench 施加 backpressure	我们生成 testbench，因此可控
memory/BRAM inference miss	L3 synth	yes now	Yosys stat: $mem 映射为 BRAM 还是被展开为 FF/LUT
CDC missing synchronizer	L0 structural + L5 metastability	仅结构可见	L0 检查 cdc:true path 上是否存在 cdc_sync instance
combinational loop	L1 lint	yes now	Verilator UNOPTFLAT / Yosys，例如 ready/valid comb loop
reset polarity/kind mismatch	L0	yes now	System-HIS resets[].polarity/kind vs RTL reset usage
FSM unreachable / no-safe-state	L0 structural + L1	partial	state.fsms reachability + lint default/full-case
internal width truncation	L2 sim	yes，前提是 testbench 检查数值	golden-value testbench 捕获 8b×8b 静默保持 8b
signedness error	L2 sim	yes，前提是 testbench 检查数值	golden-value testbench 捕获 signed/unsigned mishandling
timing / SDC closure / multicycle	L4 P&R	受 OpenXC7 spike gate	nextpnr/Vivado timing report，即 Fmax/slack
resource_overflow placement fails	L4 P&R	yes when L4 runs	nextpnr “failed to place”: cells exceed device
routing_congestion	L4 P&R	yes when L4 runs	nextpnr routing failure / congestion
timing_violation negative slack	L4 P&R	yes when L4 runs	nextpnr/Vivado slack + critical path → 指示哪里 pipeline
constraint_error unconstrained/illegal IO	L4 P&R	yes when L4 runs	nextpnr IO/constraint error vs XDC

最后六行是在审计 practitioner failure checklist 后加入的，例如 FPGA 手记 “AI写RTL”，2026-06。这是非同行评审 industry blog，仅作为 completeness check / motivation corroboration。仅加入工具可检测类别，并且每类都带 detection venue。

诚实边界，论文中必须声明，不要 overclaim：

* CDC：只能结构检查 synchronizer 是否存在，不能行为验证。metastability 无法在 aligned-clock simulation 中验证，在板上也只能稀疏/非确定性地暴露。
* backpressure / BRAM / internal-width / signedness 如果 testbench 或 QoR machinery 没有真正施压，则都是 vacuous。coverage 是 generator-quality property，不是自动成立。
* L4 timing/multicycle 受 OpenXC7 spike gate。
* 板级 signal integrity / on-board “玄学” debugging 不在范围内，那是 human L5 work，不是 pipeline 检测对象。
* Detection ≠ prevention：pipeline 会将这些标成 tool-verified failures，并喂给 repair trajectories；训练后模型是否减少这些错误是 (a)/(b)/(c) 的实证问题，不是保证。
* Accessibility–competence paradox，即 System-HIS design risk： Representation-Bottleneck study 发现更友好的表示反而可能导致 LLM 更差。因此高层 System-HIS 并不自动更容易生成；REQ→HIS 和 HIS→project 难度取决于表示设计，System-HIS ablation 必须如实报告。

Hardware-semantic taxonomy 的优先级：

* Tier A，Paper ① core： 当前 L0–L3 已可观测，边际成本低。包括 seq/comb L1、memory/BRAM inference L3、valid-ready backpressure L2。每个都喂给不同 training view：seq/comb → LOG2DIAG/FAILURE2PATCH；BRAM-miss → QOR_PRED，作为 soft failure，即 L3 pass 但 resource budget 爆掉，是活的 shift-left predicted-vs-measured sample；backpressure → functional FAILURE2PATCH，这是 sim-pass benchmarks 常漏的，因为它们的 testbenches 不施加 backpressure。
* Tier B，structural now, physical later： CDC。现在做 L0 structural check + synthetic injector “remove synchronizer”；metastability/L5 延后为 nice-to-have。
* Tier C，gated on L4： SDC/timing closure。等 OpenXC7 spike 后再做；constraints 中的 port-name checks 已在 L0 checker 中可用。

classify_failure() 从 Verilator/Icarus/Yosys logs 中检测 Tier-A 类别，不需要人工 annotation；标签被记录为 failure_to_diagnosis 的命名子类别。

Failure-label validation，regex classifier 必须校准，不能盲信：

* 从 L1/L2/L3/L4 中抽样 200–300 条 tool logs；
* 人工标注 primary failure class、secondary class、tool stage 和 patch category；
* 将 classify_failure() 与人工标签比较；
* 报告 precision、recall、confusion matrix；
* 可选：两个 annotators 或对 ambiguous logs 做 adjudication。

这些如何落到 System-HIS v1.2，不需 redesign schema：

* seq/comb：结构上捕获。combinational component 不拥有 state、clock、reset_rule；未来 L0 extension 可标记 “declared combinational but RTL has always @(posedge clk)”。
* memory/BRAM：扩展 state.memories[]，加入 memory_style: block|distributed 和 read_type: sync|async；L3 将 intent 与 Yosys-measured BRAM 比较。
* CDC：instances[].semantic_kind: cdc_sync + crossing data_flow 上的 cdc flag；L0 验证 crossing path 上有 synchronizer instance。
* backpressure：verification.scenarios[] 包含 backpressure stimulus；control_flow 已枚举 handshake_rule 和 stall_rule。

### 8.5 SR2FPGA synthesizable RTL subset

所有 model-generated RTL 都应遵循受限的可综合子集，避免 benchmark 奖励仿真可跑但不能综合、或跨工具行为不同的 RTL。

Required： `default_nettype none；显式 widths；stateful modules 显式 reset behavior；single-driver registers/nets；memory/arithmetic tasks 使用支持的 RAM/DSP inference templates。

Allowed： parameter/localparam；generate blocks；always_ff / always_comb 或严格的 always @* / always @(posedge clk)；带约束的 packed arrays；支持模板中的 synchronous memories。

Forbidden： # delays；force/release；DPI；synthesizable RTL 中的 classes/dynamic arrays；不可综合 initial blocks，除非是明确支持的 ROM/init policy；implicit nets；非任务明确要求的 intentional latches；multiple drivers。

### 8.6 Constraint classes：logical vs board

Constraints 分为两类：

* logical constraints： create_clock、target period、generated clocks、max delay、false paths、multicycle paths、timing intent；
* board constraints： package pins、IOSTANDARD、physical clock source、reset pin、board IO profile。

模型 / System-HIS 可以选择 board profile 并输出 logical timing intent。Board constraints 从可信 board profiles 生成，不允许 LLM 自由编写。L0 检查 constraints 是否引用真实 ports，以及所选 board profile 是否与 top-level shell 兼容，但不会信任任意 LLM-written board XDC。

### 8.7 Real-IP external anchor policy

Real-IP set 是一个小规模、精心挑选的 5–10 个 open-source IP cases，仅用于external validation，不用于训练。每个 case 记录 license、repository URL、commit hash、modifications、wrapper changes、original testbench availability 和 tool-compatibility patches。

---

## §9 数据引擎

### 9.1 两条生产线：Line A / Line B

* Line A — benchmark eval set： 质量优先，规模适中，几十到几百个 items；每个包含 requirement + System-HIS + contract + functional testbench + constraints + difficulty label。
* Line B — training/trajectory data： 规模优先，全自动；大规模运行 generate → tools → fail → repair，收集 L0–L5 labels、diagnoses、patch trajectories。困难任务会降低 first-pass rates，因此 failure/repair trajectories 会由设计自然出现。机器时间纪律： 大规模 loop 只跑到 L3，Yosys，每样本秒级；慢速 L4，Vivado 分钟级，只用于 eval set 和代表性子集，而不是每个样本。
* Candidate sources for inputs： 优先使用 compositional component library，免费、可控、大规模、leakage-safe；少量 DeepSeek/local candidates。所有标签来自工具，保证 tool-distillation purity。

### 9.2 Trajectory episode schema

每条 trajectory 是一个 episode，不是单个 input-output pair。数据单位是：requirement → generate → tool verdict → fail → diagnose → patch → re-verify → record outcome。下面是 canonical episode skeleton；L4 cross-tool block 单独展开。

```json
{
  "sample_id": "string",
  "requirement": "string",
  "oracle_his": {},
  "generated_his": {},
  "req_his_fidelity": {
    "interface_extraction": null,
    "clock_reset_fidelity": null,
    "parameter_fidelity": null,
    "behavior_intent_fidelity": null,
    "verification_intent_fidelity": null,
    "constraint_fidelity": null
  },
  "project": {
    "files": {},
    "deterministic_artifacts": [],
    "model_generated_artifacts": [],
    "model_token_fraction": null,
    "behavior_hole_count": null
  },
  "verification": {
    "l0": {"status": "pass|fail", "errors": []},
    "l1": {"status": "pass|fail|missing_tool", "warnings": [], "errors": []},
    "l2_core": {
      "status": "pass|fail|missing_tool",
      "public": {"status": null, "mismatch_detail": []},
      "hidden": {"status": null},
      "stress": {"status": null},
      "coverage": {"scenario_profile": null, "seeds": []}
    },
    "l2s": {"status": "pass|fail|not_run", "divergences": []},
    "l3": {
      "status": "pass|fail|missing_tool",
      "lut": null, "ff": null, "bram": null, "dsp": null, "cells": null,
      "bram_miss": false
    },
    "l4_open": {
      "tool": "openxc7_nextpnr",
      "status": "pass|fail|not_run",
      "wns_ns": null, "fmax_mhz": null,
      "lut": null, "ff": null, "bram": null, "dsp": null,
      "drc_warnings": [], "critical_warnings": [],
      "runtime_sec": null, "report_paths": []
    },
    "l4_commercial": {
      "tool": "vivado",
      "status": "pass|fail|not_run",
      "wns_ns": null, "fmax_mhz": null,
      "lut": null, "ff": null, "bram": null, "dsp": null,
      "drc_warnings": [], "methodology_warnings": [], "critical_warnings": [],
      "runtime_sec": null, "report_paths": []
    },
    "l4_agreement": {
      "class": "D0|D1|D2|D3|D4|not_applicable",
      "reason": "synthesis_mapping_difference|BRAM_DSP_inference_difference|constraint_interpretation_difference|timing_model_difference|routing_heuristic_difference|unsupported_primitive|invalid_XDC_or_board_constraint|unconstrained_path_detected_by_one_tool|critical_warning_policy_difference|null"
    },
    "l5": {"status": "pass|fail|not_run", "log_path": null}
  },
  "diagnosis": {
    "failure_level": "L0|L1|L2|L3|L4",
    "failure_type": "string",
    "failure_origin": "natural_model_failure|injected_mutation|toolchain_environment_failure",
    "structured_diagnosis": {}
  },
  "patches": [
    {
      "patch": "string",
      "diagnosis": {},
      "result_after_patch": {"l0": {}, "l1": {}, "l2_core": {}, "l3": {}}
    }
  ],
  "qor": {
    "predicted": {},
    "measured_open": {},
    "measured_commercial": {}
  },
  "data_release": {
    "tier": "open_public|restricted_reference|internal_only",
    "license_notes": []
  }
}
```

failure_origin 区分：自然失败的 model-generated designs，即 natural_model_failure；为覆盖训练而 deliberate mutation 产生的 designs，即 injected_mutation；以及工具链环境本身导致的 failures，即 toolchain_environment_failure，包括 timeout、license unavailable、missing dependency、tool crash、OpenXC7 chipdb issue。只有 natural_model_failure 和 injected_mutation 计入 model pass/fail numerator/denominator；toolchain_environment_failure 单独报告并排除在模型准确率指标之外。

v1.2 关键属性，完整 rationale 见 freeze spec：components vs instances 解决 v1.1 repeated-instance ambiguity；seq/comb 区分是结构性的，combinational component 不拥有 state/clock/reset_rule；data_flow.timing 使 pipeline depth + throughput 一等化，向 Paper ② 前向兼容；control_flow 是 load-bearing，在 L2 中验证，并驱动 testbench generation；guard nesting capped at depth 2，即 intent/RTL line。Provisional fields，包括 data_flow.timing、structured control_flow/FSM、guard grammar，是 Tier-2 ratification gate，已实现和检查，但在真实任务覆盖前，不要求进入 REQ2HIS target。

### 9.3 Failure injection suite

为了确保训练覆盖 rare but important failure classes，SR2FPGA 会故意向 known-good projects 注入 controlled mutations。Injected failures 在所有分析中都与 natural model failures 分开，通过 episode schema 中的 failure_origin 字段区分。

代表性 injected mutation classes：

* port width mismatch，即某个文件中的 parameter value 改变但未传播；
* reset polarity mismatch，即 RTL 为 active-low 而 HIS 声明 active-high；
* missing ready stall，即 valid-ready protocol 中 datapath 忽略 ready；
* BRAM template 中使用 async memory read，导致 LUT/FF mapping；
* signedness cast removal，即去掉 $signed()，产生静默 arithmetic error；
* missing CDC synchronizer，即 crossing data_flow 有 cdc:true 但无 sync instance；
* combinational ready-valid loop，即 ready combinationally depends on valid；
* invalid logical constraint，即错误 clock period 或 unconstrained path；
* removed pipeline register，导致 L4 timing pressure；
* one-hot FSM corruption，即 RTL 中 encoding 被改成 binary。

协议： injected failures 在 reference project 通过 L0–L3，或适用时 L4，之后注入，确保 pre-mutation baseline 是 clean 的。episode 中记录 injection point、mutation type 和 expected failure level。Injected samples 用于 LOG2DIAG 和 FAILURE2PATCH 训练覆盖；在 failure heatmap 中与 natural failures 分开报告。

### 9.4 Split policy：泛化机制 S1–S5

结果在多个 generalization regimes 下报告，而不仅是 parameter-heldout：

* S1 parameter-heldout： 同 family/topology，但未见过的 width/depth/latency/parallelism；
* S2 topology-heldout： 未见过的 wiring/topology patterns；
* S3 component-combination-heldout： 已知 components 的未见组合；
* S4 family-heldout： 整个 design family 从训练中 held out；
* S5 real-IP external： 真实 open-source IP 仅用于 external validation，绝不用于训练。

主结果至少应分开报告 in-distribution、parameter-heldout、topology-heldout、family-heldout performance。

### 9.5 IP / licensing / data-release discipline

SR2FPGA 生成自己的 RTL projects，并使用 EDA 工具作为客观 oracles。数据发布策略区分哪些可以公开，哪些 restricted 或 internal-only。

Data-release tiers：

Tier	内容	默认处理方式
open_public	generated requirements、System-HIS、RTL、testbenches；开源工具 Verilator/Icarus/Yosys/OpenXC7 logs 和 structured labels；L0–L4-open metadata；failure taxonomy	随 dataset 公开
restricted_reference	Vivado commercial-reference structured metadata，即从 reports 归一化的 timing/utilization summaries；L4-commercial labels	仅在机构 license review 和 Xilinx/AMD EULA 允许时发布
internal_only	raw Vivado timing/utilization/DRC/methodology reports；Vivado DCP / checkpoints；bitstreams；generated databases；LogiCORE artifacts；vendor IP；encrypted IP	用于内部审计和论文表格推导，不公开发布

原则：

* Archiving ≠ public release。 商业工具 raw reports 会为内部审计和 rebuttal 归档；它们会被总结为 normalized metadata 用于论文表格，并受 license review 约束。
* Vivado raw artifacts 不用于 public model training，除非适用 license 和机构 legal review 明确允许。
* 公开训练数据主要基于 generated designs 和 open-source tool labels。 Vivado 是商业参考验证流程，不是默认公开训练标签来源。
* Real open-source IP，即 S5 external-validation set，保留原仓库 license；wrapper 和 tool-compatibility patches 使用项目 license 开源。Real IP 不用于训练。
* Dataset card 见 §14.2，记录每个 trajectory version 的每个字段的 release tier。

---

## §10 方法：工具内化模型栈

### 10.1 蒸馏什么

SR2FPGA 训练的是项目级工具内化模型栈，而不只是若干 SFT tasks。Actor 生成和修复 FPGA projects；Critic 将 L0–L5 工具接受边界蒸馏成无需工具的 pass/risk/QoR predictions。这一 framing 将方法从“我们做 SFT”提升为“我们训练 actor + critic 来内化 EDA 工具链”。

* 蒸馏对象： 工具能力被内化。Paper ① 重点放在 generation + self-repair，即读取工具错误并修复，这是最接近作者意图的形式。Discrimination，即 QoR/pass prediction，也是自然伴随任务，作为 Paper ② 的 QoR predictor。Shift-left framing： Shift-Left EDA survey，2025 / arXiv 2509.14551，将 “correlating early RTL-stage predictions with downstream physical outcomes” 识别为 EDA 的核心 open challenge。SR2FPGA 的 predicted_qor.json，即 model-side、工具执行前，与 measured_qor.json，即 Yosys/Vivado measured，的分离与 QoR calibration，是 shift-left 的直接实例；correlation gap 必须诚实报告。
* Base model，推迟到 modeling stage： 模型 family 和 size 之后根据可用 compute 决定；dataset 是 model-agnostic。可能候选：code/RTL bases，如 Qwen2.5-Coder、DeepSeek-Coder、CodeLlama、StarCoder2 等，规模根据可用算力选择。单张 4090 上做 QLoRA 是下限，不是上限。Base choice 本身可以作为小型比较实验。

### 10.2 Actor

Actor 在 tool-verified trajectories 上训练，负责生成与修复：

* REQ2HIS — requirement → System-HIS，即结构化需求理解；
* HIS2PROJECT — System-HIS → multi-file RTL project，即 skeleton-filling；
* LOG2DIAG — tool log → structured diagnosis，即内化工具错误语义；
* FAILURE2PATCH — structured diagnosis → patch，即内化修复启发式；
* ARCH_MUTATE — HIS architecture-parameter mutation，用于 Paper ② search。

### 10.3 Critic

Critic 训练为内化工具 verdicts，负责预测与风险估计：

* PROJECT2RISK — project → L0–L3 risk score，即 tool-acceptance prediction；
* PROJECT2LEVEL — project → predicted highest passing level L0–L5；
* PATCH2VERIFY — proposed patch → pass/fail prediction without running tools；
* PROJECT2QOR — project → predicted LUT/FF/BRAM/DSP/Fmax，即 QOR_PRED。

Critic tasks 使 internalization 可测试：如果 PROJECT2LEVEL 准确，说明模型已内化工具接受边界；如果 PROJECT2QOR 与 measured QoR 相关，说明模型已内化资源利用。该 claim 只有在 model-generated behavioral holes 非平凡时才有效，其非平凡性通过 behavior_hole_count 和 model_token_fraction 记录；否则方法会退化为 deterministic generator + trivial critic。

### 10.4 QoR-search head，Paper ② 前提

当前先设计以保持连续性：

* HIS2QOR — HIS architecture params → predicted QoR，即快速 proxy fitness；
* ARCH2RANK — 按 QoR axes 上的 Pareto dominance 排列 HIS variants；
* Pareto/risk filtering，用于在搜索时减少昂贵 L4 工具调用。

### 10.5 Contract-preserving generation transparency

为了预先回应“你的 deterministic generator 构建了项目，LLM 只填 trivial holes”，每个 sample/trajectory 都记录哪些 artifacts 是 deterministic，哪些由 model-generated：

```json
{
  "deterministic_artifacts": [
    "manifest", "filelist", "top shell", "testbench scaffold",
    "constraints from board profile"
  ],
  "model_generated_artifacts": [
    "module internals", "control/datapath implementation", "patches"
  ],
  "model_token_fraction": 0.64,
  "behavior_hole_count": 5
}
```

核心表述：跨文件结构由 System-HIS 生成或约束；behavioral RTL 由模型生成；工具验证两者。 方法目标是 cross-file consistency by construction, functional/physical correctness by verification。

### 10.6 Method-novelty candidates

为通过 TCAD bar，需要选择并深化其中一个：

(i) System-HIS-constrained / verification-guided decoding
生成受 System-HIS contract 约束，使 cross-file consistency by construction。它不同于 CPPL；CPPL 在 circuit-level IR 上通过 compile-time checks 保证一致性，而我们是在 decode time 使用 requirement-level contract 约束。

(ii) Structured tool-feedback learning
将工具诊断作为结构化训练信号，即 diagnosis→patch，而不是普通 trajectory SFT。

(iii) Two-stage REQ→HIS→Project with consistency constraints

为 TCAD 选择并深化一个；若没有落地，(a)/(b)/(c) framework 仍可支撑 TRETS 论文。

### 10.7 TCAD-strong method claim

必须贯穿 Method / Contributions / abstract draft 的一句话是：System-HIS-constrained project synthesis——deterministic lowering 通过构造保证 cross-file consistency，而 model-generated behavioral holes 使用 structured EDA-tool trajectories 训练和修复。实验必须证明：

* L0 structural error rate 降到接近 0；
* L2 functionality 不退化；
* repair iterations 减少；
* structured diagnosis→patch 优于 raw-log repair。

### 10.8 Method statement：如何表述它，是否是新方法？

一句话回答 “你用了什么方法”： tool-verified learning。通过 System-HIS requirement-level IR，即 REQ→HIS→multi-file project，将 EDA 工具链的客观判断蒸馏到模型中；以 L0–L5 tool feedback 作为监督；将 structured diagnosis→patch 修复轨迹持久化为可复用数据集；并用 (a)/(b)/(c) 测量工具反馈与微调各自贡献多少。锚点是：distill the tool, not the LLM。

三种表述层级，答辩时要区分：

1. data-generation method — tool-verified trajectory factory，已完成；
2. evaluation method — project-level L0–L5 + L0 consistency checker + (a)/(b)/(c)，已完成；
3. model-training method — trajectory tasks 上的 SFT，即 REQ2HIS/HIS2PROJECT/LOG2DIAG/FAILURE2PATCH/QOR_PRED，已设计但未训练。

它是不是“新方法”？诚实回答，取决于粒度：

* 作为新技术/算法：不是。 优化器是标准 SFT/QLoRA；repair loop 已成熟，如 AutoChip；中间表示存在，如 HLS、CPPL、FIRRTL；蒸馏工具/test feedback 也存在，如 RL cluster、ChipSeek-R1。没有单块砖是新发明；尖锐审稿人会正确地说这是“已知技术应用到新 domain”。TCAD 不会接受 “QLoRA + tool loop” 作为方法贡献。
* 作为新 methodology / framework：可以防守。 具体组合——tool-oracle distillation + System-HIS requirement-level IR + project-level L0–L5 + (a)/(b)/(c) decomposition——尚未被做过。砖是旧的，构造是新的。这是新的做法，不是新工具。
* 若要成为 strong TCAD 意义上的“新方法”： 必须将一个 method-novelty candidate 做成真正技术贡献。最佳选择是 System-HIS-constrained / verification-guided decoding，即在 decode time 通过 requirement-level contract 实现 cross-file consistency by construction，区别于 CPPL 的 compile-time circuit-IR checks。如果实现了，这是新的；当前它还是 candidate，不是完成项。

诚实 claim discipline： 声称 “a new methodology for project-level tool-verified RTL generation”，以及 “the method novelty I am deepening is System-HIS-constrained generation”；不要声称 “a new training algorithm”。Venue calibration：TRETS 奖励 framework + reproducibility + dataset，novelty pressure 较低；TCAD 需要落地一个 method-novelty candidate。

---

## §11 实验设计

### 11.1 Measurement structure：公平对比

模型不以 “generates better” 销售。所有结果都在固定迭代预算下测工具接受度，并在同一个 generator 的三个点上比较。这就是 “frontier model = chain first half = baseline” 的 operational form：

* (a) first attempt, no tools — 第一半链条 baseline；
* (b) with the tool-in-the-loop feedback/repair loop — 完整链条，推理时调用工具；
* (c) tool-verified fine-tuned model, first attempt, no tools — 工具能力被内化进权重。

贡献是这些 deltas：

* b − a： 工具在环框架是否有帮助？
* c − a： 工具验证微调是否有帮助？
* c vs b： 内化能否在不调用工具的情况下匹配 tool loop？如果成立，这是最强结果。

Generator 是 swappable，可以产生一个有力 headline：用大模型如 GPT/DeepSeek 作为 chain first half，得到高 baseline；但实际可 fine-tune 的是较小 local model。然后问：工具验证微调后的小模型 (c) 能否达到大模型 (a)，甚至 (b)？ 若小模型以更少工具调用匹配大模型，这是硬结果。

还有一个 purity ablation，用于消除 critique #3：tool-verified trajectories vs same-source un-filtered distillation trajectories——工具过滤本身是否带来增益？即便结果为负，也可报告；无论如何都不能说这只是 distilling an LLM。

Optional learned-critic mode： 如果训练了 critic tasks，可以扩展出两个额外测量点：

* (c1) fine-tuned actor，first attempt，no real tools，即当前 (c)；
* (c2) fine-tuned actor + learned critic self-check / self-repair，no real tools，即 critic 在不调用工具时判断 actor 输出。

解释：

* c1 − a： tool-verified fine-tuning 对生成的提升；
* c2 − c1： learned critic 是否带来无工具自诊断价值；
* b − c2： 真实工具仍能弥补而 learned critic 不能弥补的 gap。

这个分解不是 TRETS-safe 版本必需项；如果 critic tasks 被训练，它是 TCAD-strong 增强项。

### 11.2 Statistical measurement protocol

所有 (a)/(b)/(c) 比较使用相同 task set、split、hidden tests、repair budget、timeout、tool versions、prompt family，并在 applicable 时使用相同 random seeds。报告：

* pass@1；可适用时报告 pass@k；
* repair success within N iterations；median repair iterations；
* L0/L1/L2/L3/L4 survival curve；
* per-tier T1–T4 results；per-family results；
* 对 b−a 和 c−a 做 paired comparison；
* sample size 允许时报告 bootstrap 95% confidence intervals。

不要把 L0–L5 压成一个 ordinal averaged score，而应报告 per-level pass rates / survival curves。

### 11.3 Baselines B0–B6

* B0 direct req→project；
* B1 req→HIS→project，无 deterministic skeleton；
* B2 req→HIS→skeleton→model fills behavior holes；
* B3 AutoChip-style raw-log repair；
* B4 SR2FPGA structured LOG2DIAG→PATCH repair；
* B5 fine-tuned small model，first attempt；
* B6 fine-tuned small model + repair。

Non-LLM sanity baselines，不作为 LLM baselines 比较，而用于验证 benchmark 和锚定 QoR 目标：

* B_ref： generator 输出的 deterministic reference implementation。用于验证 oracle HIS、testbench、constraints 内部一致，并确认 task 真的可实现。B_ref 通过 L0–L3，或适用时 L4，是 task 进入 evaluation set 的前提。
* B_template： deterministic skeleton + component-library composition，不包含 model-generated behavioral holes。用于校准 task feasibility 并建立 reference QoR，即 LUT/FF/BRAM/DSP/Fmax budgets。模型生成设计的 QoR 相对于 B_template QoR 报告。

### 11.4 Planned ablations

* System-HIS： req→HIS→project vs req→project，证明 System-HIS 是贡献而非装饰；这支撑 differentiation point 1。
* QoR prediction calibration： predicted vs tool-measured correlation / calibration curve。predicted QoR 必须保持 model-only，不能泄漏 measured results；保持 predicted_qor.json / measured_qor.json 分离。注意：generic Yosys-L3 LUT 是 vacuous，见 Finding G，因此真实 resource/timing calibration 需要 synth_xilinx 或 OpenXC7 L4 report。
* REQ→HIS fidelity： generated System-HIS vs oracle/manual System-HIS。
* Contract-preserving L0-by-construction： System-HIS-constrained skeleton generation vs free generation，证明它将 L0 structural error rate 推向 0，同时不损害 L2。
* OpenXC7 vs Vivado commercial-reference validation： 在同一 representative L4 subset 上比较 open-flow 和 commercial-flow 的 pass/fail、utilization、WNS/Fmax、DRC/methodology warnings、runtime。使用 §7.6 的 OpenXC7/Vivado disagreement taxonomy 明确报告不一致案例。

Full ablation list：

* with vs without System-HIS；
* with vs without contract-preserving skeleton generation；
* raw tool log vs structured diagnosis；
* public-only tests vs hidden/random/stress tests；
* tool-filtered trajectories vs unfiltered LLM trajectories；
* L2-core vs L2-UVM on protocol-heavy subset；
* generic Yosys QoR vs synth_xilinx/L4 QoR where applicable。

### 11.5 QoR results：budget / reference / ratio，而不是 raw counts

QoR 以 task budgets 和 reference implementations 为参照报告，而不仅是 raw counts。不要把 generic Yosys-L3 LUT 作为强 QoR claim；有意义 FPGA QoR 应使用 synth_xilinx 和/或 OpenXC7/Vivado L4 reports。 每个 task 可声明 resource_budget，即 max_lut/ff/bram/dsp；timing_budget，即 target_fmax_mhz；以及 reference_qor，即 deterministic reference implementation。报告：budget pass rate；generated/reference LUT、FF、BRAM/DSP、Fmax ratios；以及适用时 Pareto dominance / non-dominated count。

### 11.6 P&R noise and QoR calibration protocol

Post-P&R utilization 相对稳定，可单次运行报告。Timing metrics，如 WNS/Fmax，受 backend heuristic 和 seed 影响：对 representative L4 subset，若工具支持，使用多 seeds 并报告 mean、std、best、worst。QoR prediction 主要按 ranking/filtering/risk estimation 评价：Spearman rank correlation、calibration error、top-k design-selection accuracy、bad-design filtering accuracy；MAPE 只作为次要指标。

### 11.7 Scope variants

这里设置两个清晰出口，消除 “RQ1/RQ2/RQ4 是 minimum core” 与 “(a)/(b)/(c) fine-tuning 是 must-have” 之间的不一致。Dataset + benchmark + trajectory factory 无论如何都能支撑一篇论文；区别在于训练模型和物理结果是否落地。

TRETS-safe version：

* System-HIS；
* L0–L5 benchmark definition；
* tool-verified trajectory factory；
* L0–L3 scaled results；
* tool-in-loop repair b−a；
* failure taxonomy / semantic-gap heatmap；
* OpenXC7 primary open flow；Vivado fallback optional；
* 如果可用，提供 L4/L5-min representative physical evidence。

TCAD-strong version：

* 包含全部 TRETS-safe components；
* System-HIS-constrained / contract-preserving generation；
* 训练后的模型 (c)；
* System-HIS ablation；
* structured diagnosis→patch ablation；
* OpenXC7 primary open flow + Vivado commercial-reference validation on representative L4 subset；
* 至少一个 verified L4 / L5-min physical result；
* OpenXC7/Vivado agreement/disagreement analysis。

RQ5 QoR prediction： 不是 Paper ① must-have conclusion；如果 L4 labels 可用，可以作为 calibration preview / Paper ② bridge 报告。

L5-min，上板范围：

* 1–3 个代表性 designs；
* fixed board shell；
* host script；
* golden checksum/signature；
* archived logs。

L5-scale 明确不属于 Paper ① 范围。 L5 被报告为端到端物理可行性证据，不是大规模 pass-rate metric。

Out of scope / YAGNI： 重新训练大规模生成模型，算力不足；GA/RL / heavy QoR optimization，属于 Paper ②，需要 QoR predictor 作为 proxy fitness；商业规模大器件结果。

---

## §12 有效性、声明与审稿防御

### 12.1 Threats to validity 与 three gates，面向审稿人

一次 simulated referee-side review，即 docs/research-threats-to-validity-2026-06-25.md 和 .zh.md，认为该项目当前是一个强且诚实的 plan + infrastructure + discovery pilots，但尚非 evidence-bearing contribution。三个强调不同的 reviewers，即 evidence/rigor、originality、methodology/reproducibility，收敛到 three gates。要形成可防守 TCAD method paper，必须清除这些 gates；它们正是 spec 中已标记 gated 的事项。

1. 在冻结协议下、以规模化方式训练模型
    (c) / RQ3 headline 尚不存在，因为还没有训练模型；pilot 是 N≈1/tier、single model、exploratory。需要按 tier 报告 (a)/(b)/(c) 与 confidence intervals；冻结 prompt，因为 prompt-leakage 已观察到，见 failure-repair Issue 4。
2. 构建并验证 constrained decoding
    method-novelty core，即 2026-06-25-system-his-constrained-decoding-design.md，目前只是设计。没有它，贡献是 methodology，不是 method。需要证明它通过构造将 L0 降至约 0，同时不损害 L2。
3. 完成带商业参考的 verified physical L4/L5 evidence
    TCAD physical-realization claim 不能只依赖未经验证的 OpenXC7 spike。TCAD-strong 的最低 gate 是：一个 OpenXC7 L4/L5-min result，再加上代表性 L4 子集上的 Vivado commercial-reference validation，使用相同 RTL、相同 fixed board shell、相同 part 和相同 logical constraints。固定工具版本；归档 timing/utilization/DRC/methodology reports；明确分类 OpenXC7/Vivado disagreement cases。

还需要完成 referees 会要求的 enabling fixes：data-quality，即 noisy labels、vacuous LUT，F/E/G/DQ-H0；full-level diagnostic mode，避免 L0 short-circuit 遮蔽 L1–L4 distribution，见 Issue 5。必须保留的诚实优点： 项目没有 overclaim，会标明 discovery vs evidence，并把 physics-bound limits 划出范围；论文中应保持这种纪律。

### 12.2 Claim discipline

使用 “tool-accepted under the specified contract”、“functionally accepted by the generated golden-model testbench”、“physically implemented under the specified constraints” 或 “Lk-pass”。避免 overclaim，如 “correct design”、“fully verified”、“silicon-proven”、“tool replacement”。工具和 testbenches 是在声明 contract 下的客观 oracles，而不是完整正确性证明。

### 12.3 Reviewer-question checklist

Spec 应能直接回答以下问题：

1. System-HIS 是否不只是 prompt template？ → REQ→HIS fidelity + System-HIS ablation。
2. Contract-preserving generation 是否让任务变 trivial？ → deterministic vs model-generated artifact metadata + L2/L3/L4 results。
3. Testbench 是否太弱？ → hidden/random/stress tests + coverage + assertions + optional L2-UVM。
4. RTL simulation 是否能经受 synthesis？ → L2S post-synthesis netlist simulation。
5. L4 timing 是否真实？ → WNS ≥ 0、no unconstrained paths、no black boxes、archived DRC/timing reports。
6. OpenXC7 是否真的能在这块板上工作？ → board-specific spike + Vivado reference flow。
7. QoR 是否有意义？ → synth_xilinx/L4 QoR、budgets、reference ratios、P&R noise protocol。
8. 数据是否泄漏 generator templates？ → topology/family/component-heldout splits，即 S1–S5。
9. Failure taxonomy 是否真实？ → manual log-label validation。
10. SFT 是否只是蒸馏 LLM？ → multi-source inputs + tool-filtered vs unfiltered ablation + tool-only labels。

---

## §13 Paper ② 概览

Tool-in-the-loop QoR optimization，即 LUT / performance / power：在 architecture/System-HIS parameters 上做 GA，和/或使用 tool-derived reward 的 RL，并使用 Paper ① 的 QoR predictor 作为快速 proxy fitness，使大规模搜索可在单 GPU 上可行。GA 优化的是 architecture parameters，而不是 raw Verilog tokens，这与 research-objective document 一致。RL flagship case 自然放在 AC820-ZYNQ 上，利用 220 DSP + ARM。最接近的 prior work 是 CktEvo，即 repo-level closed-loop LLM+toolchain PPA optimization。差异化点是：我们搜索 System-HIS architecture-parameter space，而不是编辑已有 repos；使用 distilled QoR predictor 作为 proxy fitness；并拥有 CktEvo 缺少的 physical L4 labels。

---

## §14 Artifacts 与可复现性

### 14.1 Artifact and reproducibility checklist

面向 artifact review，例如 TCAD / TRETS / ACM artifact track，公开 artifact 应包含或引用以下内容。

Environment：

* 能复现 L0–L3 的 Docker / Nix environment，包含精确 Verilator、Icarus、Yosys 版本；
* L4-open 的 OpenXC7 / nextpnr-xilinx 版本；
* restricted commercial-reference subset 的 Vivado 版本记录；
* board profile version，AC820-ZYNQ XC7Z020CLG484-2；
* System-HIS schema version，即 system-his-v1.2；
* generator commit hash 和 random seeds。

Data：

* task split manifest，即 S1–S5、T1–T4 assignments；
* official evaluation 前冻结的 prompt versions；
* repair budget、timeout、tool-call accounting；
* per-trajectory data_release tier markers；
* dataset card，见 §14.2。

Reproducing results：

* eval set 上 L0–L3 evaluation 的 command lines；
* 各 stage 预期 runtime，即 L0/L1/L2/L3 typical；
* representative L4-open OpenXC7 和 L4-commercial Vivado script；
* L5 board-shell harness，fixed shell version-locked、host script、golden checksums。

### 14.2 Dataset / benchmark card

每个 released dataset version 都要报告和归档：

字段	是否必需
Version	yes
按 family 和 difficulty tier 统计的任务数量	yes
按 split S1–S5 统计的 trajectories 数量	yes
generated vs real-IP external S5 的比例	yes
工具版本 Verilator/Icarus/Yosys/OpenXC7/Vivado	yes
L0–L4-open label availability	yes
L4-commercial label availability	conditional，若 license-cleared
Hidden-test policy	yes
Coverage / scenario profile	yes
每个字段的数据发布层级	yes
Known limitations	yes
generated data 和 code 的 license	yes
Citation	yes

Dataset card 是命名 deliverable，不是事后补充。它使数据贡献能被审查和复现。

---

## §15 近期下一步

Framing premise 和 component-library MVP 已验证；v1.2 freeze 已实现，Tier-1。顺序设计为：先加固 oracle，再 scale；先 scale，再训练。Steps 1–6 gate official (a)/(b)/(c) measurement；step 7 即 OpenXC7/Vivado L4-min 可并行运行且相互独立。Schema freeze 和 OpenXC7 spike 已有 specs/plans；剩余 gate 是执行 + scale，而不是继续设计。

1. Measurement freeze
    冻结 prompts、seeds、timeout、repair budget、tool versions、hidden tests、split policy 和 pass/warn/fail semantics。还需通过真实 FSM/pipeline task 运行 provisional fields 来 ratify v1.2 Tier-2，即 data_flow.timing、structured control_flow/FSM、guard grammar；RL-agent FSM 是 reference。
2. Oracle hardening
    增加 REQ→HIS fidelity；增加 L2 hidden/random/stress tests + coverage targets；增加 assertion library；增加 optional L2S post-synthesis netlist simulation；最终确定 L2-core / optional L2-UVM split。
3. IP/data-release discipline
    为每个 trajectory 字段确定 open_public / restricted_reference / internal_only tier assignment；决定 Vivado structured metadata 是否能在 license 下发布；标注所有 episode schema fields 的 release tier；记录 institutional legal review status。
4. Data-quality fixes
    F：reset/clock label noise；E：taxonomy name drift；G：vacuous Yosys-L3 LUT → 使用 synth_xilinx 或将 QoR 推迟到 L4；DQ-H0：structured tool-signal extraction，包括 L2 mismatch detail、L4 failure families、pass-time warnings。
5. Contract-preserving generation
    System-HIS → deterministic project skeleton；model fills behavior holes；记录 deterministic vs model-generated artifact metadata；运行 L0-by-construction ablation。
6. Full-level diagnostic mode
    official verdict mode 仍采用 first-failing-level；diagnostic mode 收集更深 L1–L4 signals，见 Issue 5。
7. Scale Line B through L3
    为 RQ3 生成足够 trajectories；按 S1–S5 split policy 报告。当前数据是 N≈1/tier，是 discovery，不是 evidence。
8. OpenXC7 + Vivado L4 reference spike
    * 将一个 generated design 通过 OpenXC7 跑到 bitstream；
    * 用相同 RTL/core/board-shell/logical-constraints 通过 Vivado 跑一遍；
    * 验证 exact part XC7Z020CLG484-2；
    * 归档 timing/utilization/DRC/methodology reports；
    * 分类 OpenXC7/Vivado agreement 或 disagreement；
    * 用该结果定义第一批 L4-open/L4-commercial labels。
9. First SFT model
    产出第一个 (c) 点；先从 REQ2HIS、HIS2PROJECT、LOG2DIAG、FAILURE2PATCH 开始；在冻结 (a)/(b)/(c) 协议下评价，使用单张 4090 进行 SFT。
10. Artifact packaging
    创建 dataset card，见 §14.2；创建 tool-version manifest；创建带 Docker/Nix environment 的 reproduce-L0-L3 script；创建 representative L4-open / L4-commercial evaluation script；锁定 board shell 版本。

---

## §16 文档关系与 companion specs

本文档对 docs/research-objective-sr2fpga-tcad.md 进行收束和 operationalization。若两者存在差异，则近期工作以本文档为准；本文档是 compute-calibrated、拆解为 ①/②、明确 tool oracle 作为 distillation target、并采用 Zynq reproducible flow 的 reframe。如果采纳该方向，应更新 research-objective document。

Companion specs，待主章节稳定后拆出：
本文档当前同时承担 design spec 和 paper-protocol reference。各部分稳定后，应拆分以下 companion specs，以保持主文档可执行：

Companion spec	内容
sr2fpga-data-release-and-licensing.md	完整数据发布政策、license review checklist、field-level tier assignments
sr2fpga-trajectory-schema.md	版本化完整 episode schema、字段定义、migration notes
sr2fpga-model-stack.md	Actor/Critic/QoR-head architecture、training task definitions、loss formulations
sr2fpga-artifact-reproducibility.md	完整 artifact checklist、Docker/Nix environment spec、command-line reference
sr2fpga-l4-openxc7-vivado-protocol.md	L4 run protocol、board shell spec、agreement taxonomy、report archive format

在此之前，主 spec 保留这些主题的 summary versions，如上所示；companion specs 是 forward pointers，而不是 blockers。

---

## Changelog

日期	摘要
2026-06-22	原始 reframe spec。研究路线批准，Paper ①/② 分解，System-HIS framing，L0–L5 定义，(a)/(b)/(c) measurement structure，目标 venue TCAD/TRETS，hard constraints，motivation 与 differentiation。
2026-06-25	Reviewer-hardening update。收紧 verification oracle，如 L2 coverage-qualified、coverage targets、protocol assertion library；measurement protocol，如 frozen protocol、per-tier CI、survival curves；L4 physical-pass definition，如 WNS≥0、9 条 criteria、no unconstrained paths、archived reports；data split policy S1–S5；claim discipline。还增加 L2F optional property checks、L2S post-synthesis netlist simulation、L2-core vs L2-UVM distinction、TCAD-strong 的 OpenXC7/Vivado commercial-reference requirement，以及 REQ→HIS fidelity sub-metric。
2026-06-26	Artifact/data-release/model-stack update。新增：1. 显式 IP/licensing/data-release policy，即 open_public / restricted_reference / internal_only tiers；2. SR2FPGA tool-internalizing model stack 定义，即 Actor / Critic / QoR-search head，并解释为什么这是 model stack；3. 完整 trajectory episode schema；4. optional (c1)/(c2) measurement，将 generation internalization 与 learned no-tool diagnosis 分开；5. failure-injection suite 和 natural/injected/toolchain failure-origin 字段；6. L2F optional property-check layer；7. artifact reproducibility + dataset card checklists。
2026-06-27	文档重组。 内容不变；章节为可导航性重构。Paper ① Design 这个 1527 行 h2 被拆成 12 个顶层章节 §1–§12。Episode schema 从 System-HIS 移到 Data Engine §9.2。Hardware-semantic gap taxonomy 从 Data Engine 移到 Benchmark Design §8.4。所有 L4 定义合并到 §7.6，之前分散在 6 个小节。Immediate Next Steps 重新编号为 1–10。加入 Changelog。
