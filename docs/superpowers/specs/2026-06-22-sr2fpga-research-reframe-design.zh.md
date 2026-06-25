# SR2FPGA 研究重定向设计（中文版）

> **说明：** 本文是英文权威版 `2026-06-22-sr2fpga-research-reframe-design.md` 的中文翻译，
> 供中文阅读与讨论使用。**两者不一致时，以英文版为准**；请勿把本文当作独立的真相源。
> 技术术语（System-HIS、L0–L5、REQ→HIS、data_flow、CDC、Fmax 等）按中文 EDA/ML 论文
> 惯例保留英文；schema / 代码块原样保留。

## 状态

提出于 2026-06-22。细化并界定 `docs/research-objective-sr2fpga-tcad.md` 的方向。本文是在对当前
data-agent 工作做了一次批判性审查之后达成一致的研究路线，把愿景拆解为一个可发表的论文计划，并
详细规定 Paper ①。

## 目标期刊

**主投：IEEE TCAD**，**ACM TRETS 作为退路**——目标定高，投稿时按实际做出来的成果再定。两者都看重
"物理实现 + 可复现"这条线；TCAD 还额外要求 TRETS 放松的方法新颖性（见最后一条）。一个对两者都有利的
点：**AC820-ZYNQ（XC7Z020）是主流商用 Xilinx 器件**，所以 TCAD"这是真实硅片吗"的本能质疑已经被回答
——比小 Lattice 片子更合适。重点：

- **物理实现是主菜，不是点缀**：L4 时序收敛 + L5 上板 + 资源/Fmax/功耗报告是核心证据。
- **一个全开放、可复现的闭环**（req→bitstream→board）是 TRETS 看重的主卖点。作者的 **AC820-ZYNQ
  板（芯片 XC7Z020CLG484-2）在 OpenXC7 支持清单内**，所以在*真实 Xilinx 器件*上跑全开放的
  Yosys→nextpnr-xilinx（OpenXC7）→bitstream→board 流程是可行的——待 spike 验证。**Vivado 保留为
  退路/基线**，而 **OpenXC7-vs-Vivado 对比本身是个加分项**（开放工具在 LLM 生成 RTL 上的可用性/QoR）。
  所有 code/data/scripts/器件公开，工具版本锁定。
- **方法新颖性是 TCAD 要补的缺口**（不放松）：TCAD 不会把"QLoRA 微调 + 一个工具回路"当作方法贡献——
  它需要一个真正的方法学想法（见 Method → "Method-novelty candidates"），外加超过 TRETS 下限的规模。
  若新颖性/规模没达到，就降投 TRETS（它对新颖性的门槛低得多）；论文其余部分不变。

## 动机

### 为什么问这个问题（外因论证）

驱动问题——*EDA 工具链的判断，能不能被内化进一个模型，使它能从需求出发，生成、诊断、修复并预测"项目级、
多文件、可物理实现"的 FPGA RTL 工程，而在推理时不再调用工具？*——值得问，有三个叠加的理由：

- **工具是 ground truth，但在推理尺度上用不起。** EDA 工具（Verilator/Yosys/nextpnr/板子）给的是*客观*的
  通过/不通过裁决，不是另一个模型的意见——但它昂贵、缓慢、外部、不可微。于是今天的 LLM-RTL 卡在两条路之间：
  (a) 不用工具（生成 + pass@k 看仿真——但"能仿真 ≠ 能上板"：Representation Bottleneck 报无条件端到端仅 48%，
  一线工程师也说"写得快不算本事，能上板才算"）；(b) 推理时每次调工具（成熟但慢/贵，且 **L4 P&R 分钟级/样本、
  无法扩展**——正是 Paper ② 的死穴）。把工具裁决内化，就能拿到*工具级正确性、LLM 级速度/成本*，解锁大规模
  QoR 代理搜索、无工具链生成、以及对领域专家的可及性。
- **它检验一个真正、可测量的科学命题。** "硬件的正确性/可实现性，是设计本身的*可学习函数*，还是本质上必须
  跑工具才知道？"——这是个有真假、且能对客观 ground truth（工具）测量的问题，不是自报质量。
- **领域的简单区已饱和，难区恰好就是这里。** 单模块仿真 benchmark（VerilogEval）已逼近天花板；没解的区是
  **跨文件一致性 + 物理可实现性**——TODAES'25 综述、ChipSeek-R1/MasterRTL/POET 的 future work、以及
  Representation Bottleneck 显式呼唤的"分离意图与实现的 LLM 原生 IR"，全部指向这里。项目级 + 物理是模型真正
  失败、也是科学所在的地方。

**问题的诚实形式（带威胁意识的重述）：** 正确的问法是工具裁决能被内化*多少*、在*哪里失效*——而非工具能否被
完全取代。有些量受物理本质约束、够不着（CDC 亚稳态、板级信号完整性；见 threats to validity）。所以成功**不是**
"取代工具"，而是测出的差值 **(b−a)** 与 **(c−a)**——工具在环反馈与工具验证微调各加了多少——外加画出 L0–L5 上
"哪些可内化 vs 哪些必须留给工具"的边界。**部分答案也是结果。**

### 为什么重定向（内因触发）

对当前状态做的一次"刻薄审稿人"审查发现了真实风险：项目有一条高质量数据流水线，但**还没有科学结果**，
而且初始任务（`counter`、`fifo`、`simple_fsm`、`ram_read_write`）太简单——强基线模型一次就在 L3 通过，
于是修复回路从不触发，`failure_to_patch` 一直为空。**修正任务难度是缓解大多数下游症状的根。**

本次重定向保留作者真正的目标——**一个能从自然语言需求生成完整 RTL 工程、并能根据工具反馈自修复的
模型**——但在真实资源预算下让它站得住、做得动。

## 现实意义（real-world impact）

区别于上面学术层面的"为什么问"——具体谁受益：

- **把 FPGA 门槛降给领域专家。** 全球硬件设计师不到 10 万，但最懂工作负载的人（机器人、信号处理、嵌入式、
  边缘 AI）大多不会写 HDL。可靠的"需求→可上板工程"路径让他们**不精通 HDL** 也能拿到定制硬件——具体场景：
  边缘 IoT、医疗可穿戴、机器人控制、小型 AI kernel，这些是 ASIC 太贵、通用处理器又不够的地方。
- **对已在做 FPGA 的团队：省时间、省授权钱。** EDA 流程慢（仿真分钟级、P&R 分钟到小时）、Vivado 按席位收费。
  内化工具裁决 = *更少工具迭代*、推理时不占授权/算力、设计周期更短——若 (c) 逼近 (b)，就是"不跑昂贵回路也拿
  到接近的质量"。
- **小团队也能做的 PPA 优化（Paper ②）。** 搜架构参数（流水深度、并行度、memory bank）求最佳功耗/面积/Fmax，
  今天要几千次慢工具跑。蒸馏出的快速 QoR 代理让这种搜索在一块 GPU 上可行——更省电、更优的边缘设计，没大算力也
  够得着。
- **即使模型没做成也留得下的公共品。** 工具验证的项目轨迹数据集 + L0–L5 benchmark + **全开放、免授权的
  req→bitstream→board 流程**（OpenXC7 跑在便宜的真器件 AC820-ZYNQ 上），为买不起商用 EDA 的研究者和小公司
  把 FPGA EDA 民主化。
- **一个具体应用锚点。** AC820-ZYNQ 上的边缘 RL 加速器旗舰案例，把整条链落在真实控制/机器人工作负载上。

**诚实的天花板（别过度声称）：** 它**不取代** FPGA 工程师——现实角色是助手 + 自动验证 + 初稿，不是自主流片。
物理本质的工作（大设计时序收敛、CDC 亚稳态、板级信号完整性）仍归工具/人（见 threats to validity）。PhD 尺度的
现实落地范围 = **中小设计 + 辅助式工作流 + 数据集/benchmark/开放流程作为公共品**，不是一个部署的产品。

## 硬约束（决定下面的每一个决策）

- **算力：** 本地微调仅一块 RTX 4090 24GB。**不可行：** 预训练、或训练一个正面打赢 GPT-5 / DeepSeek 的
  生成模型——这个野心放弃。**模型规模刻意暂不固定：** 数据集和 benchmark 设计必须保持 model-agnostic；
  模型与规模到建模阶段再按当时可用算力选。**当前优先级是建数据集。**
- **数据：** 没有现成数据；所有轨迹都是本地跑工具从零生成。**标签完全来自工具**（L0–L3 用开源
  Yosys/Verilator/Icarus，L4–L5 用 OpenXC7/Vivado），所以"tool-verified learning"是字面属实——监督来自
  工具，不是另一个 LLM。
- **硬件：** 上板验证用作者的 **AC820-ZYNQ 板**——芯片 **XC7Z020CLG484-2**（约 53k LUT、220 DSP、双核
  ARM；大到能放大设计和一个 RL 旗舰案例）。该器件**在 OpenXC7 支持清单内**，使全开放
  req→bitstream→board 流程成为可能（待 spike 验证）；**Vivado 为退路/基线**。

## 核心重定向：蒸馏的是工具，不是 LLM

早先的顾虑是"你用 DeepSeek 生成和修复，再拿来训练 → 你在蒸馏 DeepSeek"。作者的真实意图恰恰相反、也
更强：**把 EDA 工具预言机蒸馏进模型。** EDA 工具（Verilator / Yosys / Vivado / 板子）是一个昂贵、缓慢、
外部、不可微的预言机。研究问题是：能否把它们的判断内化，使模型在推理时**不调用工具**也能生成、预测、
诊断、修复 RTL。

同一个工具预言机扮演**双重角色**：

- 它是 benchmark 的**裁判**（评测/数据贡献），并且
- 它是模型的**老师**（方法贡献）。

评测与方法共用一个工具裁判，使整个故事自洽。

为了保持是*工具*蒸馏（而非 LLM 蒸馏）：

- **输入必须多源**——组合式构件库拼装、刻意变异/破坏的设计、真实 IP——而不只是某一个 LLM 的输出；
- **所有标签都来自工具。**

这种输入分布天然产生大量失败，从而**靠设计而非靠运气**让失败/修复轨迹复活。

## 前沿模型是链条的前半段（即基线）

一个前沿模型直接生成完整工程，**不是竞争对手——它是链条内部的一个测量点**：恰恰就是"前半段、无工具
反馈、首次尝试生成"这个基线。于是"和 GPT 竞争"从威胁变成本工作的**基线 + 消融**。更强的前沿模型只是
抬高起点；科学贡献是**工具反馈在它之上还能加多少**。

前沿模型现状（定性，**待测量、不从数字断言**——见"立即下一步"）：今天的前沿模型能可靠处理单文件/小
RTL（这就是 DeepSeek 一次通过 smoke counter L3 的原因），也能产出*形式上*的多文件工程，但**不能可靠**
产出大型、强跨文件一致、能收时序、可上板的工程——跨文件/跨模块契约错误和 L4 时序是它们的失败区。那个
失败区就是本工作瞄准的开放空间，也是为什么 benchmark 难度必须校准到前沿通过率开始下降的位置。

## 论文计划拆解（这是 2–3 篇的计划，不是一篇）

```
Paper ①  基础：工具预言机的双重角色
         ├─ System-HIS + 项目级 L0–L5 benchmark + 可复现
         │  req→bitstream→board 闭环          （评测/数据贡献）
         └─ 工具验证微调模型：生成 + 自修复    （方法贡献）
                    │  产出：可复现评测 + 轨迹数据 + QoR 预测器
                    ▼
Paper ②  优化：工具在环的 QoR 搜索（LUT / 性能 / 功耗）
         └─ 在架构参数上做 GA / 用工具奖励做 RL，
            用 Paper ① 的 QoR 预测器当快速代理适应度
```

依赖是有机的：Paper ② 的痛点是工具太慢、撑不起 GA/RL 需要的成千上万次评估；Paper ① 的 QoR 预测器
（一个工具蒸馏）正是解锁 Paper ② 的快速代理适应度。所以先做 ① 不是拖延——它是 ② 的前提和加速器。

GA/RL 和"重训一个大生成模型"**不在 Paper ① 范围内**（只作引子 + future work 一段）。

## Paper ① 设计

### 一句话论点

SR2FPGA 从系统需求出发，**经由 System-HIS 中间表示**，生成多模块、跨文件一致的 RTL **工程**，通过一条
**可复现流程**推进到 **L4 时序收敛**（外加 AC820-ZYNQ 上的 L5 上板案例），并用**项目级 L0–L5 评测**量化
每一层；在该评测上，一个工具验证微调模型**内化工具接受度**，在固定迭代预算下提升生成 + 自修复。

中文定位：**面向系统需求的项目级 RTL 工程生成——以 System-HIS 中间表示 + 项目级 L0–L5 评测 + 可复现
req→bitstream→上板闭环（AC820-ZYNQ）为贡献，并以工具验证轨迹微调一个模型，使其内化工具接受度、在固定
迭代预算下提升生成与自修复。**

### 研究问题（Research Questions）

论点拆成五个具体、可回答的问题。每个标注：怎么答、填的领域 gap、当前状态。

- **RQ1 — 表示。** 在需求与多文件工程之间插入需求级 IR（System-HIS），相比 req→project 直接生成，是否提升跨
  文件一致性与物理可实现性？
  *怎么答：* System-HIS 消融（req→HIS→project vs req→project），看 cross-file 一致性错误率 + L1–L4 通过率。
  *gap：* Representation Bottleneck（2026）证明 IR 选择 > 模型，并显式把"分离意图/实现的 LLM 原生 IR"列为
  future work；TODAES'25 把 NL↔RTL 中间表示列为未解；CPPL 是电路级、非需求级。*警示：* accessibility-competence
  悖论意味着这必须*测*、不能假设。*状态：* 需 v1.2 generator/checker + 模型；未跑。
- **RQ2 — 工具反馈的价值（b−a）。** EDA 工具在环修复回路，相比无工具首次尝试，把项目级工具接受度提升多少、在
  哪一层/哪个难度档提升最多？
  *怎么答：* 固定迭代预算下 (b)−(a)，按难度档。*gap：* 修复回路已成熟（AutoChip/MAGE/VerilogCoder/PEFA-AI）
  但都在单模块/仿真层，无项目级物理 + 可复用轨迹。*状态：* baseline (a)/(b) pilot 已跑（T1/T2→L3，膝点 T3）；
  需规模 + prompt 冻结。
- **RQ3 — 内化（c−a, c vs b）。** 工具验证微调能否把工具接受度内化进权重，使"无工具首次"(c) 逼近"工具在环"
  (b)？以及——微调的*小*模型的 (c) 能否追上*大*前沿模型的 (a)/(b)？
  *怎么答：* 同一可替换生成器上 (c) vs (a)/(b)。*gap：* ChipSeek-R1 用 per-attempt RL 内化，ASIC/单模块、无可复用
  数据集；Representation Bottleneck 主张"IR-aware training > 模型 scaling"。*状态：* **还没训练过任何模型——最大
  开口，也是 headline 结果。**
- **RQ4 — 失败结构 / 难度校准。** 在项目级尺度，前沿模型在 (i) 难度轴 和 (ii) L0–L5 验证深度 / 硬件语义鸿沟
  （seq-comb、背压、memory、CDC、时序）的哪里开始失败？
  *怎么答：* baseline (a) 跨 T1–T4 + 分层失败分类法（cross-file 一致性错误率 + 硬件语义失败分布）。*gap：*
  Representation Bottleneck 只测了极小单模块 + Lattice（综合"透明"）；项目级/Zynq 正是它排除、L4 才成约束的区；
  它的 seq(2.3×)/memory(43%) 梯度背书我们的轴。*状态：* pilot + 分类法在；需全层诊断模式 + 规模。
- **RQ5 — QoR 预测 / shift-left。** 模型能否在工具执行前预测 QoR（LUT/FF/BRAM/DSP/Fmax），predicted 与
  tool-measured 相关性如何？
  *怎么答：* predicted_qor vs measured_qor 校准。*gap：* MasterRTL 做 pre-synth PPA 但是独立 ASIC 预测器；
  shift-left 综述把"预测↔物理相关"列为核心难题。*状态：* 被卡——需真 measured QoR（OpenXC7 L4；Yosys L3 的 LUT
  是假的，Finding G）；该预测器同时是 Paper ② 的代理适应度。

**核心 vs 被卡：** RQ1、RQ2、RQ4 是必答的最小可发表核心；RQ3 是 headline 但需训练好的模型；RQ5 是 nice-to-have
且卡在 OpenXC7 L4 spike。五个都由使能性基础设施贡献（工具验证项目轨迹数据集 + L0–L5 benchmark + 可复现
req→bitstream→board 闭环）操作化——正是它让这些问题变得可测量。

### 别人针对每个 RQ 怎么解决（以及留下什么）

按 RQ 组织的视角（与下文按"工作类型"的 field map 互补）。每个 RQ：领域怎么解、我们占的空位。

- **RQ1（表示）。** *领域：* 无 IR 的 req→code 直生成（VerilogEval、RTLLM、RTLCoder、OpenLLM-RTL）；电路级 IR
  （CPPL：Python-DSL→电路 JSON，靠编译期位宽推断保一致）；软件级中间（Spec2RTL-Agent 走 HLS C）；非 NL 目标的
  编译器硬件 IR（FIRRTL/CIRCT/LLHD/HIR/Calyx）；把输出 HDL 当 IR 研究（Representation Bottleneck）。*留白：* 没人把
  **需求意图级 IR** 做成带消融的可学习/可评测对象；Representation Bottleneck 显式把它列为 future work → System-HIS。
  **状态：开放。**
- **RQ2（工具反馈，b−a）。** *领域（成熟）：* 编译/仿真反馈回路——AutoChip（+24.2%）、RTLFixer（语法）、MAGE
  （多 agent）、VerilogCoder（图规划 + AST 波形工具）、PEFA-AI（渐进式错误反馈）。*留白：* 全在单模块/功能/仿真层；
  没人在**项目级/物理**层、同一生成器、跨难度档隔离出干净的 (b−a) 差值。**状态：拥挤——靠层级 + 干净测量区分。**
- **RQ3（内化，c−a / c vs b）。** *领域（最拥挤）：* RL + 工具奖励——ChipSeek-R1（分层 syntax→sim→synth-PPA reward，
  ASIC）、VeriRL（trace-back rescore）、VeriReason（RL+testbench+reasoning）、RTLSeek；SFT（RTLCoder、Veribench-53K）；
  推理时 steering（MeltRTL、CASS-RTL）。*留白：* per-attempt reward、**无可复用轨迹数据集**、单模块、ASIC/仿真；没人把
  "(c) 不调工具能否匹配 (b)"或"小模型追大模型"框成问题。Representation Bottleneck 的"IR-aware training > 模型 scaling"
  支持我们。**状态：最拥挤——护城河 = 项目级 + 物理 + 可复用工具验证轨迹 + (a)/(b)/(c) + 可替换生成器。（最高风险；
  模型还没训。）**
- **RQ4（失败结构 / 难度）。** *领域：* 按复杂度报通过率的 benchmark（ArchXBench 6 级、RTL-Repo、ResBench、CVDP）；
  失败模式分析（Representation Bottleneck：组合 1.3–1.4× / 时序 2.3× / memory 43%；RTLFixer 语法）。*留白：* 没有
  **L0–L5 验证深度 × 硬件语义**的项目级交叉索引；它的 seq/memory 梯度背书我们的轴。**状态：半开放。**
- **RQ5（QoR 预测 / shift-left）。** *领域：* 专用 pre-synthesis PPA 预测器，多为独立 GNN、多为 ASIC——MasterRTL、
  DeepCircuitX、自监督电路 encoder；HLS DSE 预测器（IronMan、Chimera、AutoHLS、Intelligent4DSE）；POET。*留白：* 我们的
  预测器是**同一个工具蒸馏模型的一部分**（非独立 GNN），在 **FPGA 物理（L4）**，且喂 Paper ② 当代理适应度，带严格
  predicted/measured 分离。**状态：半开放。**

**拥挤度总结：** RQ1 开放；RQ2 拥挤（回路已成熟）；**RQ3 最拥挤（RL 簇）——差异化必须在这里最锋利**；RQ4/RQ5 半开放。

### 差异化（相关工作地图；完整文献综述在作者 vault 中）

三个支撑点，对照*当前*领域（不是 VerilogEval 时代的领域）诚实陈述：

1. **System-HIS 作为需求级前端 IR**——req→System-HIS→project 而非 req→code；一个显式、可学习、可评测的
   中间表示，位于硬件 IR 谱系（FIRRTL / CIRCT / LLHD / HIR / Calyx）**之上**，并可*下降到*它——它不替代
   也不重新实现 CIRCT。（决策：**浅 CIRCT 耦合**——定位 + 一个可选的 lowering 桥，而非深度依赖。）增益**由
   消融证明**。
2. **工具验证轨迹数据集 + L0–L5 项目评测**——护城河**不是**"项目级"：多文件/项目 benchmark **已经存在
   （RTL-Repo、CktEvo、ArchXBench）**，单凭这一点不再新颖。护城河是*数据单元* = 一条**项目轨迹**
   （generate→tool→fail→diagnose→patch，带 L0–L5 标签），那些 benchmark 不产出这个。
3. **可复现 req→bitstream→board 闭环**到 L4/L5（code/data/scripts/器件公开、版本锁定）——几乎没有先前
   RTL-LLM 工作到达 P&R/时序、上板、或完整可复现。

领域地图（每一条是什么、为什么不是我们）：

- **LLM-to-RTL benchmark / 模型：** VerilogEval、RTLLM、**RTLCoder（TCAD'25）**、OpenLLM-RTL——单模块 / RTL
  代码、pass@k。（RTLCoder 是最近的 TCAD 基线：代码生成模型 vs 我们的工具验证工程生成。）
- **项目级 RTL benchmark：** **RTL-Repo**（仓库上下文 Verilog *补全*；无综合/物理、无轨迹）和 **ArchXBench**
  （MLCAD'25；**按*设计复杂度*分 6 级**，前沿模型从其 Level 4 起就失败——作为 motivation 引用；注意它的级
  ≠ 我们的 L0–L5，后者是到 P&R+board 的*验证/物理深度*）。两者都不做物理收敛或工具验证轨迹。
- **工具反馈 / agentic：** AutoChip、RTLFixer、MAGE、**Spec2RTL-Agent**（spec→C++→HLS→RTL）、**VerilogCoder**
  （AAAI'25, arXiv 2408.08927；自主 agent + 图规划 + 基于 AST 的波形追踪*工具*）——修复/agent 回路已成熟 →
  不是卖点。
- **表示选择研究（关键 motivation，非竞争对手）：** **《From Natural Language to Silicon: The Representation
  Bottleneck in LLM Hardware Design》**（2026, arXiv 2604.17097）——3 个前沿 LLM × 6 种 IR
  （Verilog/VHDL/Chisel/Bluespec/PyMTL3/HLS-C），202 个任务；发现 **"IR choice, not model choice, is the
  dominant factor"**（仿真通过率随 IR 从 3%→88%；同一 IR 内换模型只差 <1.25×）。**实证支撑了我们的前提：杠杆
  在表示、不在模型**（因此前沿模型 = 基线）。*关键区分：* 他们的 "IR" = **输出 HDL**（单模块、极小的 Lattice
  iCE40UP5K、无轨迹）；System-HIS = HDL **之上的需求级中间 IR**（项目级、多文件、XC7Z020）——是正交、互补的
  轴，不是一回事。**最强定位（来自它自己的 Discussion）：** 它显式呼唤"一个**分离意图与实现的 LLM 原生 IR**"
  作为进一步缓解瓶颈的方向，并把其框架作为评估此类未来 IR 的基础设施——**即 System-HIS 正是它写成 future work
  的那个 IR。** 它另有两个发现实证背书我们的设计：瓶颈在**时序设计（2.3×）和 memory 设计（43% 总体）远大于组合
  逻辑（1.3–1.4×）**——背书我们 seq/comb + memory 难度轴；且结论是改进应来自 **IR-aware training 而非模型
  scaling**——背书"前沿模型=基线、在工具验证数据上微调"。它的 **"accessibility–competence 悖论"**（越友好的
  IR → LLM 越差）对 System-HIS 是设计警示，记入 threats to validity。**要正面回应、不回避的威胁：** 它发现 FPGA
  **综合"几乎透明"**——过了仿真就有 83–100% 映射到硅，瓶颈在*前端*——这表面上质疑我们对 L4 物理的强调。回答在
  regime：它的设计是**教学级、单模块、中位数<50 行、5280-LUT 的 Lattice iCE40**，且它自己承认"工业级复杂层级/
  IP 集成可能改排名""商用 Xilinx/Intel 数值可能不同"。综合透明是*设计太小*的结果，非普适真理。**我们的项目级
  多模块 regime（XC7Z020 53K LUT、真时序收敛）正是它排除的那一档——在那里 L4 才成为约束滤网。**（它 86.5% 的
  iCE40 通过率是**条件**于仿真通过；无条件端到端仅 48.1%。）
- **硬件 IR：** FIRRTL / CIRCT / LLHD / HIR / Calyx，以及 **CPPL**（LLM→电路 IR JSON→CIRCT→Verilog；输入
  是**带固定端口 + docstring 的 Python DSL，不是自然语言**；一致性靠编译期位宽推断；无物理/PnR）。CPPL 在
  电路结构层，System-HIS 在需求意图层（输入 = NL 需求，*下降到* CIRCT/CPPL）。
- **仓库级 PPA 优化（最接近 Paper ②）：** **CktEvo**——闭环 LLM+工具链编辑，在已有仓库上保功能、改 PPA；
  无 L4/L5 物理标签。我们的区别：搜 System-HIS 架构参数空间（而非编辑仓库），用蒸馏 QoR 代理。
- **HLS DSE：** NSGA-II、Chimera、IronMan、AutoHLS——优化给定设计点（与 Paper ② 直接相关，如预测器当代理
  适应度）。
- **FPGA 专用 benchmark：** **ResBench**（2025, arXiv 2503.08823）——56 题 / 12 类，FPGA 上的功能正确性 +
  LUT 资源估计；但**单模块、止于资源估计**（无 PnR、无时序收敛、无上板、无多文件工程结构）。最接近的现有
  FPGA benchmark；它的证据上限正好是我们 L3–L5 的起点。
- **RTL 生成的 RL（单模块簇）：** **ChipSeek-R1**（层次奖励 RL、ASIC 综合）、**VeriRL**（trace-back rescore
  处理稀疏奖励 + Veribench-53K, arXiv 2508.18462）、**VeriReason**（RL + testbench 反馈 + 思维链）——全是单
  模块 / 功能层；都不产出持久的工具验证轨迹数据集，也不到 FPGA 物理。它们共同的 future work：FPGA、多文件、
  物理——正是我们的设计空间。
- **合成 RTL 数据生成：** **SynCircuit**（HKUST 2025, arXiv 2509.00071）——扩散式图生成 + MCTS 造合成 RTL
  电路，目的是 ML4EDA 数据增强。电路图级：无 NL 需求输入、无 testbench、无工程结构。和我们的组合式 benchmark
  生产概念相邻但目的正交（电路级 ML 数据 vs 需求级可验证工程 + 轨迹）。

模型/数据是骑在这些之上的方法贡献，**不是** SOTA 模型声明。

### 我们填补的 gap（领域已承认）

这不是"为整合而整合"：LLM-for-EDA 综述（TODAES'25, arXiv 2501.09655）把这些列为开放问题，而最强的 RL/PPA
工作也把它们当 future work 承认。

| 已承认的 gap（综述 / 竞品自己的话） | 我们的贡献 |
|---|---|
| "完整多文件 / 端到端系统规格生成……仍未被探索" | req→System-HIS→多文件工程 |
| "桥接 NL 与 RTL……future work，未解决" | System-HIS 需求级前端 IR |
| "无系统性验证 / 可复现标准" | 可复现 req→bitstream→board 闭环 |
| "FPGA LLM 应用仍有限" | FPGA 物理实现（L4/L5） |
| ChipSeek-R1 / MasterRTL / POET 是 ASIC、单模块、止于综合（它们自己的 future work） | FPGA、多文件、到 P&R + 上板 |
| ChipSeek-R1 **无可复用轨迹数据集**（逐次 RL 奖励） | 一个持久的**工具验证轨迹数据集** |
| ResBench（2025）：最接近的 FPGA LLM benchmark，但单模块 + 止于 LUT 资源估计（无 PnR / 时序 / 上板） | L3 实测 QoR（Yosys）+ L4 时序（OpenXC7/Vivado）+ L5 上板 |
| SynCircuit（2025, HKUST）：电路图级合成 RTL 生成；无 NL 需求、无 testbench、无可验证工程结构 | 需求级组合式生成 + 机器自检 testbench + 工具轨迹 |
| 所有 LLM-to-RTL 工作都用黑盒 pass/fail；没有谁按**硬件语义类型**（软→硬鸿沟）给错误分类，也不做语义感知监督（MeltRTL 的"硬件特有不准确"最接近，但仍用仿真通过率） | SR2FPGA **按 L0–L5 交叉索引的硬件语义失败分类法**（seq/comb@L1、背压@L2、内存推断@L3、CDC 结构@L0、时序@L4）——见下文"硬件语义鸿沟" |

**警示（诚实的催）：** 这些是*已承认*的 gap，所以贡献只有在执行真的到达 L4/上板、真的建成轨迹数据集时
才成立——否则就塌成"把已知方法移植到 FPGA"。

### 核心论证

"项目级"的要点**不是**"代码更大"，而是**正确性结构（多模块 + 跨文件/跨模块一致性）+ 物理可实现性（综合 /
时序收敛）**。System-HIS 是从需求到该结构的桥（功能、端口、位宽、时钟/复位、FSM、数据通路、存储、接口）。
入场门票：生成对象必须是**可变拓扑的多模块设计**（一个 top 实例化若干子模块，端口/参数跨文件一致），而非
固定 6 文件模板——否则"项目级"就塌了。

### System-HIS schema（v1.1——结构契约层；字段按任务扩展）

**抽象层级（已定）：** 结构契约 + 粗粒度行为标签，**不是**完整行为规格。System-HIS 描述
modules / interfaces / connections / params 加一行行为意图；**功能正确性由 L2 testbench 验证，不在 HIS 中
描述**。这让 HIS 保持*意图*抽象（不是又一份 RTL）、让 REQ→HIS 可学习、让组合式生成器能可靠产出。L0 对照
HIS 检查结构；L2 检查功能。

```
project:   {name, description, top}                 # top = 顶层模块名
clocks:    [{name, target_fmax_mhz}]                # 时钟域 + 目标频率（L4/SDC 的权威来源）
resets:    [{name, polarity: active_low|active_high, kind: sync|async}]
modules:   [{
   name, role,                  # role = fifo|arbiter|pipeline|alu|regfile|cdc_sync|decoder|…
   clock, reset,                # 本模块属于哪个时钟/复位域
   ports:  [{name, dir: in|out|inout, width}],  # width = 解析后的整数（或 "PARAM" 引用）以便 L0 比较
   params: [{name, value}],
   intent: "<一行行为意图，标签级，不可执行>"
}]
# 注意：seq/comb 区分不是独立字段。在 v1.2 top-down schema 中它由结构表达——组合组件不拥有 `state`、
# 无 `clock` 域、`control_flow` 中无 `reset_rule`。见"硬件语义鸿沟"小节与 v1.2 spec
# (2026-06-24-sr2fpga-system-his-v1.2-topdown-design.md)。
connections: [{                 # 跨模块契约 = 跨文件一致性的核心
   from: "mod.port" | "TOP.port", to: "mod.port" | "TOP.port",
   protocol: register|valid_ready|axi_lite|axi_stream,
   width, cdc: true|false       # cdc=true 标记一次跨时钟域（难度轴 4）
}]
top_ports: [{name, dir, width}]                     # 顶层外部 IO
verification: {checks: [...], test_pass_means: "..."}   # 指导自动 testbench 的验收语义
qor_intent:  {resources: {lut?, ff?, bram?, dsp?}}      # 模型侧预测 → predicted_qor.json（频率在 clocks 里）
```

**双重用途**（为什么 System-HIS 是贡献而非副产物）：它既是生成的**中间监督目标**（REQ→HIS），又是 L0
检查器据以验证所生成 RTL 的**ground-truth 契约**。

字段随新设计族加入而按任务扩展——例如 Paper ② 的可搜索架构参数（并行度 / 流水深度 / memory banks）以后
会放在这里。

### Benchmark 设计

- **单题形式（基于验证，非参考匹配）：** RTL 没有唯一正确答案，所以 ground truth 是"通过验收标准"，绝不
  是"匹配某个参考文件"。输入 = NL 需求 + 机器可读接口契约。判定 = L0–L5 工具裁决 + 功能 testbench。
- **生产机制——组合式程序生成为主力：**
  - 一个参数化原语的**构件库**（FIFO、arbiter、CDC 同步器、流水级、ALU 片、寄存器堆、协议适配器、decoder…）；
  - 一个**拓扑生成器**，把构件接成多模块系统（chain / tree / bus-attached / producer-consumer）并自动保证
    接口契约一致；
  - 多样性 = 构件类型 × 参数空间 × 拓扑 × 协议变体 × 名字随机化（组合爆炸，不是固定模板数）；
  - 生成器同时产出 `(requirement, System-HIS, contract, testbench, constraints, reference impl)`。参考实现
    通过 testbench 给了 testbench 一个**机器自检的自洽性**——这是优先选程序生成而非 LLM 写测试的承重理由
    （没人能认证一份 LLM 写的 testbench）。
  - **算法族任务的 golden model：** 自洽只证明 RTL 参考与 testbench *彼此一致*，不证明它们算的*数学对*。对算法
    模块（FIR、FFT、矩阵乘、CORDIC、累加器、MAC），生成器还必须产出一个**软件 golden model**（Python/NumPy）
    来生成 testbench 的期望值，使 L2 能抓到"能跑但数不对"的 bug（如位宽截断 `8b×8b` 仍留 8b、符号数错误）。
    没有 golden 源，数值校验类任务就退化成只剩自洽，恰好漏掉分类法里 `internal_width_truncation` /
    `signedness_error` 针对的静默数值失败。
  - **（与 SynCircuit 的区别，HKUST 2025）：** SynCircuit 在电路图级造合成 RTL（扩散 + MCTS）做 ML4EDA 数据
    增强——无 NL 输入、无 testbench、无工程结构。我们的生成在需求意图级，产出可验证多文件工程 + 验收
    testbench + 工具轨迹。目的不同、抽象层不同；SynCircuit 证明了纯合成 RTL 生成可行、且数据稀缺是共同问题。
- **Testbench 纪律：** 只测**黑盒接口契约**（端口行为、协议时序、功能正确性）；绝不依赖内部信号名/实现细节
  ——这才让 benchmark 对任何实现都公平。
- **防泄漏：** held-out 参数组合 + 随机化，使具体实例在任何训练语料里实际不可见。（真实开源 IP 才是泄漏风险，
  合成实例不是。）
- **来源（混合）：** 组合式合成任务为主体（难度可控、可扩展、防泄漏），加一小批真实开源 IP（OpenCores /
  LiteX…）作外部效度锚点。LLM 可对程序生成的需求文本做**表面改写**成更自然的语言——只动措辞、绝不碰语义或
  验收——以缓解"合成 NL"的质疑。
- **难度轴（共四条，前两条为主）：**
  1. 跨模块 / 跨文件一致性（接口/参数契约数量）——主
  2. 时序压力（目标 Fmax / 关键路径深度）——主
  3. 协议/控制复杂度（register → valid/ready → 带背压流水 → AXI4-Lite/Stream）——把轴 1 推高的载体
  4. 结构规模（子模块数 / 层级深度）与 CDC——高难度档
- **难度分级（用于报告前沿通过率膝点）：** 把上述轴映射到 **T1 Easy / T2 Medium / T3 Hard / T4 Stress**，依据
  子模块数、跨模块契约数、协议类、目标 Fmax（具体阈值在 baseline (a) 测量时确定）。通过率**按档**报告，让前沿
  模型开始失败的膝点可见。
- **规模：** 千到约 1 万样本，不是百万级（数据量现实）。benchmark 题目以中小多模块设计为主（RL 规模加速器是
  *旗舰案例*，不是主体——见 scope）。现有确定性 `ProjectGenerator` 是构件库的种子。

### 评测层级与工具链

- **L0** 项目契约 + 跨文件一致性；**L1** lint（Verilator）；**L2** 功能仿真（Icarus Verilog）；**L3** 综合 +
  实测 QoR（Yosys）；**L4** 布局布线时序收敛（**OpenXC7 跑在 AC820-ZYNQ / XC7Z020CLG484-2，Vivado 作退路/基线**，
  报 Fmax/slack）；**L5** 稀疏代表性上板（AC820-ZYNQ）。
- **L0 一致性检查器（一个命名组件，不是脚注）：** 对照 System-HIS 契约验证所生成 RTL——top 实例化已声明的
  模块；每个端口名/方向/位宽、参数、跨模块连接都与 System-HIS 匹配；testbench 实例化真 top；约束引用真端口。
  这把跨文件一致性裁决自动化，并产出 **"cross-file consistency error rate"** 指标——单文件 benchmark 在结构上
  做不到的检查。
- **工具链（全开放为主，Vivado 退路）：** 综合和大规模数据到 **L3 用 Yosys**（开源、快、免费——适合千级样本）；
  **L4 时序收敛 + L5 上板用 OpenXC7（nextpnr-xilinx）跑在 AC820-ZYNQ**（XC7Z020CLG484-2，在 OpenXC7 支持清单内；
  220 DSP / ARM 承载更大设计含 RL 旗舰案例），给出全开放 req→bitstream→board 闭环——**待早期 spike 验证**。
  **Vivado 为退路/基线**，使 L4/L5 结果不会因开放工具不成熟而丢失，而 **OpenXC7-vs-Vivado（可用性/QoR）是 TRETS
  读者看重的加分对比**。所有 code/data/scripts/器件公开，工具版本锁定。

### 数据引擎（两条生产线）

- **Line A —— benchmark 评测集：** 质量优先，规模适中（几十到约几百题），每题含 requirement + System-HIS +
  contract + 功能 testbench + 约束 + 难度标签。
- **Line B —— 训练/轨迹数据：** 规模优先，全自动；大批量跑 generate → tools → fail → repair，收集 L0–L5 标签、
  诊断、补丁轨迹。难任务拉低首过率，所以失败/修复轨迹**靠设计**出现。**机时纪律：** 大规模回路只跑到 **L3
  （Yosys，秒级/样本）**；把慢的 **L4（Vivado，分钟级/样本）**留给评测集和代表性子集，不是每个样本。
- **输入候选来源：** 优先组合式构件库（免费、可控、量大、防泄漏）+ 少量 DeepSeek/本地候选。**所有标签来自工具**
  （工具蒸馏纯度）。
- **硬件语义鸿沟——按 L0–L5 交叉索引的失败分类法（一个命名贡献，不只是"更多错误类型"）：** LLM 在软件
  （顺序执行）语义上预训练，系统性地在硬件的并发/物理语义上失败。关键在于：**该鸿沟的每一类在不同验证深度
  显现**，所以 L0–L5 层级不只是"验证深度"，更是"所需硬件语义理解的深度"。这把失败分类法贡献从"我们有个分类
  法"升级成"我们把软→硬语义鸿沟映射到验证深度层级"——并说明先前工作（止于 L2/L3）只覆盖了鸿沟的前半段。

  | 语义鸿沟类 | 显现于 | 我们工具能否观测 | 如何 |
  |---|---|---|---|
  | seq/comb 混淆 | **L1** lint | 能（现在） | Verilator 具名警告：`MULTIDRIVEN`、`LATCH`、`COMBDLY`、`BLKSEQ` |
  | valid-ready 背压 | **L2** sim | 能，**当我们的 testbench 施加背压时** | testbench 由我们产出 → 可控 |
  | memory/BRAM 推断失败 | **L3** synth | 能（现在） | Yosys `stat`：`$mem` 映射成 BRAM vs 摊平成 FF/LUT |
  | CDC 缺同步器 | **L0**（结构）+ L5（亚稳态） | 仅结构 | L0 查 `cdc:true` 路径上是否有 `cdc_sync` 实例 |
  | 组合环 | **L1** lint | 能（现在） | Verilator `UNOPTFLAT` / Yosys（如 ready/valid 组合环） |
  | 复位极性/类型不符 | **L0** | 能（现在） | System-HIS `resets[].polarity/kind` vs RTL 复位用法 |
  | FSM 不可达 / 无安全态 | **L0**（结构）+ L1 | 部分 | `state.fsms` 可达性 + lint default/full-case |
  | 内部位宽截断 | **L2** sim | 能，**当 testbench 校验数值时** | golden-value testbench 抓 `8b×8b` 被静默留 8b |
  | 符号数错误 | **L2** sim | 能，**当 testbench 校验数值时** | golden-value testbench 抓 signed/unsigned 处理错误 |
  | 时序 / SDC 收敛 / 多周期 | **L4** P&R | 受 OpenXC7 spike 阻塞 | nextpnr/Vivado 时序报告（Fmax/slack） |

  （后六行是在用一份 practitioner 失败清单审计我们分类法后，对原三行的扩展——FPGA手记《AI写RTL》，2026-06，
  一篇非同行评审的行业博客，仅作完整性检查/motivation 佐证。只加了工具可检出的类，每类标注检出层。）

  **诚实边界（threats to validity——论文中要陈述，不要过度声称）：**
  - CDC：仅结构（同步器在不在），**非**行为——亚稳态在仿真中不可验证（时钟对齐），上板只能稀疏/不确定地出现。
  - 背压 / BRAM / 内部位宽 / 符号数 在 **testbench（或 QoR 机制）没真正施压时是空的**——覆盖度是生成器质量
    属性，不是自动的。
  - L4 时序/多周期受 OpenXC7 spike 落地阻塞。
  - 板级信号完整性 / 上板"玄学"调试**不在范围内**——那是人类 L5 工作，不是流水线能检出的。
  - 检测 ≠ 预防：流水线把这些*标注*成工具验证的失败、喂修复轨迹；训练后的模型是否不再犯，是 (a)/(b)/(c)
    的经验问题，不是保证。
  - **accessibility–competence 悖论（System-HIS 设计风险）：** Representation-Bottleneck 研究
    （2026, arXiv 2604.17097）发现*越友好*的表示反而可能*降低* LLM 表现。所以高层 System-HIS 不会自动更易
    生成——REQ→HIS 与 HIS→project 的难度取决于表示设计，System-HIS 消融必须诚实报告这点（不假设"加个更高层
    IR ⇒ 更好"，而是去*测量*它）。

- **硬件语义分类法的优先级分档：**
  - **Tier A（Paper ① 核心——现在 L0–L3 即可观测、边际成本低）：** seq/comb（L1）、memory/BRAM 推断（L3）、
    valid-ready 背压（L2）。各自喂*不同的*训练视图——seq/comb → `LOG2DIAG`/`FAILURE2PATCH`，BRAM-miss →
    `QOR_PRED`（一个*软*失败：过 L3 但爆资源预算，一个活的 shift-left 预测 vs 实测样本），背压 → 功能
    `FAILURE2PATCH`，是仿真通过类 benchmark 漏掉的（它们的 testbench 从不施加背压）。
  - **Tier B（现在结构、物理靠后）：** CDC——现在做 L0 结构检查 + 一个合成注入器（"删同步器"）；亚稳态/L5 留
    nice-to-have。
  - **Tier C（受 L4 阻塞）：** SDC/时序收敛——延后到 OpenXC7 spike 之后；端口名对约束的检查已在 L0 检查器里。

  `classify_failure()` 从 Verilator/Icarus/Yosys 日志检出 Tier-A 类，无需人工标注；标签作为 `failure_to_diagnosis`
  的命名子类记录。

- **这些在 System-HIS v1.2 中的落点（无需 schema 重设计）：**
  - seq/comb：由结构表达——组合组件不拥有 `state`、无 `clock`、无 `reset_rule`；未来 L0 扩展可标"声明组合但
    RTL 含 `always @(posedge clk)`"。
  - memory/BRAM：给 `state.memories[]` 扩 `memory_style: block|distributed` 与 `read_type: sync|async`；L3 对照
    意图与 Yosys 实测 BRAM。
  - CDC：`instances[].semantic_kind: cdc_sync` + 跨越 `data_flow` 上的 `cdc` 标记；L0 验证跨越路径上有同步器实例。
  - 背压：`verification.scenarios[]` 含一个背压激励；`control_flow` 已枚举 `handshake_rule` 和 `stall_rule`。

### 方法（模型）

- **它蒸馏什么：** 把工具能力内化——Paper ① 聚焦**生成 + 自修复**（读工具错误并修），最贴近作者意图。判别
  （QoR/通过预测 = Paper ② 的 QoR 预测器）是自然的伴随任务。**（Shift-left 框架）：** Shift-Left EDA 综述
  （2025, arXiv 2509.14551）把"关联早期 RTL 阶段预测与下游物理结果"定为 EDA 的核心开放挑战；SR2FPGA 的
  `predicted_qor.json`（模型侧、工具执行前）vs `measured_qor.json`（Yosys/Vivado 实测）分离 + QoR 校准正是
  shift-left 的一个实例——而那个相关性差距是要诚实报告的局限。
- **基座模型（推迟到建模阶段）：** family 和规模到时按可用算力选——数据集 model-agnostic。可能候选：code/RTL
  基座（Qwen2.5-Coder、DeepSeek-Coder、CodeLlama、StarCoder2…）按能放下的规模（一块 4090 上 QLoRA 是地板，不是
  天花板）。基座选择本身可以是一个小对比实验。
- **框架：** 工具在环（generate → 工具检查 → 对错误/资源的反馈 → 重生成/修复 → 记录），对应作者的步骤 1–4。
- **方法新颖性候选（为过 TCAD 门槛——以后选/深化）：** (i) **System-HIS 约束 / 验证引导解码**——生成受
  System-HIS 契约约束，使跨文件一致性按构造成立（区别于 CPPL，它在电路级 IR 上靠编译期检查保一致；我们在
  *解码时*、从*需求级*契约作用）；(ii) **结构化工具反馈学习**——把工具诊断当结构化训练信号（diagnosis→patch），
  不是在轨迹上做普通 SFT；(iii) **带一致性约束的两阶段 REQ→HIS→Project**。为 TCAD 选/深化一个；若都没落地，
  (a)/(b)/(c) 框架仍足以撑一篇 TRETS。

### 测量结构（公平的较量）

模型**不**以"生成得更好"来卖。一切都按**固定迭代预算下的工具接受度**测量，在同一个生成器上取三个点（这是
"前沿模型 = 链条前半段 = 基线"的可操作形式）：

- **(a) 首次尝试、无工具**——链条前半段基线（一个前沿/基座模型单独做的）；
- **(b) 带工具在环反馈/修复回路**——完整链条，推理时调用工具；
- **(c) 工具验证微调模型、首次尝试、无工具**——工具能力内化进权重。

贡献是这些差值：

- **b − a：** 工具在环框架有没有用？
- **c − a：** 工具验证微调有没有用？
- **c vs b：** 内化能否在推理时*不调工具*却匹配回路——若成立则是最强结果。

生成器**可替换**，由此得到一个有力的 headline 结果：用大模型（GPT/DeepSeek）当链条前半段拿高基线，但你真正能
微调的是一个更小的本地模型。于是问：**一个工具验证微调的小模型的 (c)，能否达到大模型的 (a) 甚至 (b)？** 小模型
用更少工具调用追上大模型，是个硬的、可发表的结果。

外加一个化解 critique #3 的纯度消融：**工具验证轨迹 vs 同源未过滤蒸馏轨迹**——工具过滤本身加不加分？负结果也
可报告，无论如何没人能说这是"只是蒸馏一个 LLM"。

### 计划的消融

- **System-HIS：** req→HIS→project vs req→project（证明 System-HIS 是贡献而非装饰——这支撑差异化第 1 点）。
- **QoR 预测校准：** 预测 vs Yosys 实测的相关性 / 校准曲线（预测 QoR 必须保持仅模型、绝不泄漏实测——保持现有
  `predicted_qor.json` / `measured_qor.json` 分离）。

### 范围（必备核心 vs 可选）

**必备核心**（最小可发表论文）：

- 组合式多模块构件库 + 拓扑生成器，带基于验证的 testbench 和 System-HIS；
- benchmark 评测集（几十到几百题，分难度）；
- 大规模 Yosys L0–L3 + 跨难度档的 baseline (a)；
- 工具验证 QLoRA 微调 + (a)/(b)/(c) 测量；
- System-HIS 消融。

**可选**（仅当时间/算力允许）：

- 大规模 L4 时序 和 几个之外的 L5 上板；
- AC820-ZYNQ 上的 RL 规模旗舰案例；
- OpenXC7-vs-Vivado 对比深度；QoR 校准深度。

**不在范围（YAGNI）：** 重训大生成模型（算力不足）；GA/RL / 重 QoR 优化（Paper ②，需 QoR 预测器当代理适应度）；
商业规模大器件结果。

## Paper ②（简述）

工具在环 QoR 优化（LUT / 性能 / 功耗）：在架构/System-HIS 参数上做 GA 和/或用工具导出奖励做 RL，用 Paper ①
的 QoR 预测器当快速代理适应度，使大规模搜索在一块 GPU 上可行。GA 优化架构参数，不是裸 Verilog token（与
research-objective 文档一致）。RL 旗舰案例自然落在这里，在 AC820-ZYNQ（220 DSP + ARM）上。最接近的先前工作：
**CktEvo**（仓库级闭环 LLM+工具链 PPA 优化）——区别在于搜 System-HIS 架构参数空间（而非编辑已有仓库），用蒸馏
QoR 预测器当代理适应度，带 CktEvo 没有的物理（L4）标签。

## 与现有文档的关系

本文界定并落地 `docs/research-objective-sr2fpga-tcad.md`。两者不一致时，本重定向（算力校准、拆成 ①/②、工具
预言机作为显式蒸馏目标、Zynq 可复现流程）主导近期工作。若采纳本方向，请更新 research-objective 文档。

## 立即下一步

首先，**与 codex 在途工作对账**：commit `6c7f273`（"Add control-oriented multi-module RTL tasks"）已经在往多
模块任务走，所以构件库切片必须建立在它之上——写代码前先检查它以免冲突。

然后第一个具体实验是**测量 baseline (a)**：让现有前沿/本地 LLM 在多个难度档上过现有工具流水线，记录跨文件一致性
错误率和 L3/L4 通过率。这是最便宜的切片（API/推理 + 大体已有的工具流），并同时 (1) 验证框架前提（前沿模型在难区
失败）、(2) 校准 benchmark 难度该落在哪（通过率膝点）、(3) 成为论文的基线 + motivation 实验。产出一小批分级多模块
任务集（构件库 MVP）是喂这次测量的前提。

并行地，在 AC820-ZYNQ 上跑一个 **OpenXC7 spike**——把一个代表性多模块设计一路推到 bitstream + 上板——尽早为全
开放 L4/L5 声明去风险，因为开放流卖点就压在它上面（若 spike 暴露缺口，Vivado 仍为退路）。

本 spec 获批后，用 writing-plans skill 为所选第一个切片写实现计划。
