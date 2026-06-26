# SR2FPGA 研究重定向设计（中文版）

> **说明：** 本文是英文权威版 `2026-06-22-sr2fpga-research-reframe-design.md` 的中文翻译，
> 供中文阅读与讨论使用。**两者不一致时，以英文版为准**；请勿把本文当作独立的真相源。
> 技术术语（System-HIS、L0–L5、REQ→HIS、data_flow、CDC、Fmax 等）按中文 EDA/ML 论文
> 惯例保留英文；schema / 代码块原样保留。

## 状态

已批准方向；**原始 2026-06-22，最后更新 2026-06-25。** 细化并界定
`docs/research-objective-sr2fpga-tcad.md` 的方向，把愿景拆解为一个可发表的论文计划，并详细规定 Paper ①。
英文权威版同步维护本中文版。两者与 objective 文档冲突时，以本重定向为准。

**基础设施与证据状态（2026-06-25）：** data-generation agent 已能用客观工具预言机跑 L0–L3；
**System-HIS v1.2 已冻结并实现**（确定性生成器对所有任务族发 v1.2；v1.2 L0 检查器做 HIS↔RTL 交叉检查且
经验证有牙——能抓注入的端口/testbench 失配；legacy/v1.1 已隔离）——**freeze 批准闸门的 Tier-1 已达成。**
已有丰富、**有记录的探索性实验过程**——baseline (a)/(b) pilot、约 30 个 run、一份 25 条 issue 的失败-修复
研究日志（带 paper hooks）——产出 **discovery 级发现**：跨文件一致性是修复膝点；T4 失败前沿被系统推下
L0→词法→lint→sim→功能；prompt 收紧会泄漏；L0 会掩盖更深的 RTL 失败。这些是 **discovery，还不是规模化证据**
（N≈1/档、单一模型、探索性协议）。**尚未有：** 规模化轨迹数据、训练好的 (c) 点（RQ3）、L4 物理（OpenXC7
spike）、以及数据质量修复（F/E/G）。

**Reviewer-hardening update（2026-06-26）：** 本次修订收紧验证 oracle、测量协议、物理通过定义、数据切分
策略和论文表述纪律。目标不是扩展愿景，而是加固 oracle、测量、物理通过定义、数据切分和表述纪律，使每一个
"pass" 都能经受 FPGA/DV/EDA 审稿人的追问：L2 必须 coverage/stress 限定，L3/L4 QoR 必须用有意义的 FPGA
映射，L4 pass 需要显式的时序/约束检查，L5 用固定 board shell，且 System-HIS 不仅对 RTL 评估、还要对原始需求
评估其忠实度。

**Artifact/data-release/model-stack update（2026-06-26）：** 本次修订新增：(1) 明确的 IP/许可/数据发布策略
（open_public / restricted_reference / internal_only 三档；Vivado 原始产物未经许可审核不用于公开训练）；(2)
SR2FPGA 工具内化模型栈定义（Actor / Critic / QoR-search head，并说明为什么这是模型*栈*而非 SFT 任务列表）；
(3) 完整轨迹 episode schema；(4) 可选 (c1)/(c2) 测量点，将生成内化与无工具自诊断分开量化；(5) 失败注入套件
与 natural/injected/toolchain failure_origin 字段；(6) L2F 可选形式化属性检查层；(7) artifact 可复现性 +
数据集 card 清单。本文档记录设计；后续待主要小节稳定时，会把数据发布、轨迹 schema、模型栈、artifact
可复现性各拆成独立 companion spec（见"与现有文档的关系"）。

## 目标期刊

**主投：IEEE TCAD**，**ACM TRETS 作为退路**——目标定高，投稿时按实际做出来的成果再定。两者都看重
"物理实现 + 可复现"这条线；TCAD 还额外要求 TRETS 放松的方法新颖性（见最后一条）。一个对两者都有利的
点：**AC820-ZYNQ（XC7Z020）是主流商用 Xilinx 器件**，所以 TCAD"这是真实硅片吗"的本能质疑已经被回答
——比小 Lattice 片子更合适。重点：

- **物理实现是主菜，不是点缀**：L4 时序收敛 + L5 上板 + 资源/Fmax/功耗报告是核心证据。
- **一个全开放、可复现的闭环**（req→bitstream→board）是 TRETS 看重的主卖点。作者的 **AC820-ZYNQ
  板（芯片 XC7Z020CLG484-2）在 OpenXC7 支持清单内**，所以在*真实 Xilinx 器件*上跑全开放的
  Yosys→nextpnr-xilinx（OpenXC7）→bitstream→board 流程是可行的——待 spike 验证。**Vivado 保留为
  退路/基线**。对于 **TRETS-safe** 工作，Vivado 是可选的；对于 **TCAD-strong** 版本，必须在代表性
  L4 子集上完成 Vivado 商业参考验证。所有 code/data/scripts/器件公开，工具版本锁定。
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
- **数据：** 没有现成数据；所有轨迹都是本地跑工具从零生成。**公开训练标签主要来自开源工具**
  （L0–L3 用 Verilator/Icarus/Yosys，L4-open 用 OpenXC7），所以"tool-verified learning"是字面属实——
  监督来自工具，不是另一个 LLM。**Vivado 标签是商业参考标签**，仅覆盖代表性 L4 子集，在机构许可审核
  允许发布前，与 `open_public` 训练档分开管理。标签绝不来源于另一个 LLM。*工具内化是指在声明的工具流
  程下、从工具验证标签中学习；不意味着逆向工程或复现专有 EDA 软件。*
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
  悖论意味着这必须*测*、不能假设。*状态：* v1.2 生成器 + L0 HIS↔RTL 交叉检查已实现（Tier-1 已批准）；消融还需
  训练好的模型 + req→project 对照臂；未跑。
  *新增 REQ→HIS fidelity 子指标：* System-HIS 必须忠实于**原始需求**，而非仅与所生成的 RTL 自洽——否则模型可
  误解需求、生成"错误但自洽"的 HIS，使 RTL 与 testbench 都跟着错误 HIS，而 L0/L2 仍可能通过。合成任务用生成器
  发出的 oracle HIS 做字段级比对；真实/外部任务用一小批人工审阅集。**REQ-HIS fidelity 指标：** 接口抽取准确度
  （端口名/方向/位宽/协议）；clock/reset 忠实度（极性、同步/异步类型、deassertion）；参数忠实度（width/depth/
  latency/parallelism/memory banking）；行为意图忠实度（FIFO/arbiter/MAC/pipeline/AXI-lite/stream 语义）；
  验证意图忠实度（所需场景与 corner case）；约束忠实度（目标 Fmax、资源预算、board shell/profile）。
- **RQ2 — 工具反馈的价值（b−a）。** EDA 工具在环修复回路，相比无工具首次尝试，把项目级工具接受度提升多少、在
  哪一层/哪个难度档提升最多？
  *怎么答：* 固定迭代预算下 (b)−(a)，按难度档。*gap：* 修复回路已成熟（AutoChip/MAGE/VerilogCoder/PEFA-AI）
  但都在单模块/仿真层，无项目级物理 + 可复用轨迹。*状态：* baseline (a)/(b) pilot 已跑（T1/T2 修复→L3，膝点 T3）；
  prompt 泄漏已被经验观察到（failure-repair Issue 4）→ 需规模 + 冻结的 prompt。
- **RQ3 — 内化（c−a, c vs b）。** 工具验证微调能否把工具接受度内化进权重，使"无工具首次"(c) 逼近"工具在环"
  (b)？以及——微调的*小*模型的 (c) 能否追上*大*前沿模型的 (a)/(b)？
  *怎么答：* 同一可替换生成器上 (c) vs (a)/(b)。*gap：* ChipSeek-R1 用 per-attempt RL 内化，ASIC/单模块、无可复用
  数据集；Representation Bottleneck 主张"IR-aware training > 模型 scaling"。*内化的 scope：* 生成 + 修复，限于"判决是
  模型产出的函数"的部分——**L0–L3，外加 L4 *失败* 诊断/修复**：nextpnr/Vivado 吐结构化 P&R 报错
  （`resource_overflow`、`routing_congestion`、`timing_violation` 带关键路径、`constraint_error`），映射到可操作 patch
  （降资源 / 重构 / 打拍 / 修 XDC）——和 L1–L3 同一 diagnosis→patch 形态。留在 RQ3 *之外*（由 RQ5 当预测处理）的，
  是有时序压力设计的连续、seed 噪声的*精确* Fmax 余量。*状态：* **还没训练过任何模型——最大开口，也是 headline 结果。**
- **RQ4 — 失败结构 / 难度校准。** 在项目级尺度，前沿模型在 (i) 难度轴 和 (ii) L0–L5 验证深度 / 硬件语义鸿沟
  （seq-comb、背压、memory、CDC、时序）的哪里开始失败？
  *怎么答：* baseline (a) 跨 T1–T4 + 分层失败分类法（cross-file 一致性错误率 + 硬件语义失败分布）。*gap：*
  Representation Bottleneck 只测了极小单模块 + Lattice（综合"透明"）；项目级/Zynq 正是它排除、L4 才成约束的区；
  它的 seq(2.3×)/memory(43%) 梯度背书我们的轴。*状态：* pilot + 分类法在；T4 失败前沿被推下
  L0→词法→lint→sim→功能已记录为 discovery；需全层诊断模式 + 规模。
- **RQ5 — QoR 预测 / shift-left。** 模型能否在工具执行前预测 QoR（LUT/FF/BRAM/DSP/Fmax），predicted 与
  tool-measured 相关性如何？
  *怎么答：* predicted_qor vs measured_qor 校准。*训练信号：* **OpenXC7 批量 L4 报告**（免授权 + 可批量正是让足够
  L4 标签可收集的前提）。*可学性拆分：* 布线后**利用率（LUT/FF/BRAM/DSP）主要是 RTL × 综合的函数 → 较好学**；
  **Fmax 取决于 seed 噪声、后端启发式的关键路径 → 能学成预测器但有噪声地板 / 校准 gap**（诚实报告）。*gap：*
  MasterRTL 做 pre-synth PPA 但是独立 ASIC 预测器；shift-left 综述把"预测↔物理相关"列为核心难题。*状态：* 被卡——
  需真 measured QoR（OpenXC7 L4；Yosys L3 的 LUT 是假的，Finding G）；OpenXC7 spike 现有 spec+plan；该预测器
  同时是 Paper ② 的代理适应度。
  *工具流切分（新增）：* RQ5 预测的是声明工具流下的工具测得 QoR——**OpenXC7-QoR** 和 **Vivado-QoR**
  是独立标签。OpenXC7 标签支撑可复现开源流程和更可规模化的 L4 标签采集；Vivado 标签是 L4-commercial
  子集上的商业参考标签。跨工具迁移/校准在 L4-agreement 子集上报告。

**核心 vs 被卡：** RQ1、RQ2、RQ4 是必答的最小可发表核心；RQ3 是 headline 但需训练好的模型；RQ5 是 nice-to-have
且卡在 OpenXC7 L4 spike。五个都由使能性基础设施贡献（工具验证项目轨迹数据集 + L0–L5 benchmark + 可复现
req→bitstream→board 闭环）操作化——正是它让这些问题变得可测量。

**原则——保留结构化工具信号（不要二值化）。** 每个工具阶段吐的可学信号远比"通过/失败 + 粗标签"丰富，轨迹数据集
必须保留*结构*、不要压扁：

- **L2 仿真：** 不只 `TEST_FAIL`，而是**失配明细**（信号、expected vs actual、第几拍；最好连 VCD）——正是 diagnosis→patch
  信号（VerilogCoder 的 AST 波形追踪就吃这个）。
- **L1/L3/L4 *通过时*的警告：** "过了但带警告"是*软*信号（latch 风险、位宽扩展、未用/未驱动 net、BRAM-miss、时序勉强
  达标）——是质量/风险标签，不能被二值化丢掉。
- **L3 综合期诊断**（推断 latch、组合环、多驱动）与 **L4 关键路径明细**（哪些 net/cell，告诉模型该在*哪里*打拍）——
  超出 headline 的 cell 数 / Fmax 数字。
- **predicted vs measured 残差**本身就是 RQ5 校准信号。

原始日志已按阶段保存；缺口在*抽取*——诊断记录与训练视图现在把丰富日志压成一个 `failure_type` 字符串（见
training-data-quality issue 日志）。把这步抽取做厚，正是让 LOG2DIAG/FAILURE2PATCH 精准、并拓宽可内化范围的关键。

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
  电路结构层，System-HIS 在需求意图层（输入 = NL 需求，*下降到* CIRCT/CPPL）。**System-HIS 也不同于
  IP-XACT / SysML / FuseSoC 式的工程元数据：** 它们描述 IP 封装、系统建模或构建集成，而
  System-HIS 是面向 LLM 的需求级生成契约——以生成和验证结果来评价，而非以文档完整性来评价。
  它同时扮演三个角色：(a) REQ→HIS 的监督目标，(b) L0 HIS↔RTL 交叉检查的 ground-truth
  契约，(c) 工具轨迹学习的数据锚点。其评价标准是生成的工程能否通过 L0–L5，而非 HIS 文档
  是否完整。
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

### System-HIS schema（canonical：v1.2——已冻结；见 freeze spec）

**canonical schema = `system-his-v1.2`，已冻结并实现**（完整字段定义见
`docs/superpowers/specs/2026-06-24-sr2fpga-system-his-v1.2-freeze-design.md`；原型 `-topdown` 与下面的内联 v1.1
已被取代）。本小节只保留*论证*和切面骨架；字段权威是 freeze spec。

**抽象层级（已定）：** 结构契约 + 粗粒度行为标签，**不是**完整行为规格。System-HIS 描述
components / instances / interfaces / connections / params 加一行行为意图；**功能正确性由 L2 testbench 验证，
不在 HIS 中描述**。这让 HIS 保持*意图*抽象（不是又一份 RTL）、让 REQ→HIS 可学习、让组合式生成器能可靠产出。
L0 对照 HIS 检查结构；L2 检查功能。

**v1.2 切面骨架**（按 FPGA 架构师推理的顺序组织）：

```
schema_version: "system-his-v1.2"
intent:       {user_prompt, design_goal, assumptions}      # 把请求保留在契约之上
top:          {name, parameters, clocks, resets, ports, interfaces}   # 先定设计边界
components:   [{name, semantic_kind, source, parameters, ports, intent}]   # 可复用模块定义
instances:    [{name, component, parameter_values, clock, reset, owns_state}]  # 具体块（允许重复实例）
data_flow:    [{name, path:[top.x|inst.port], width, protocol, cdc, timing:{latency_cycles, initiation_interval, throughput}?}]
control_flow: [{kind, when:<guard 深度≤2>, effect, related_state, related_flows}]  # fsm_transition / enable_rule / stall_rule …
state:        {registers, counters, fsms:[{states, initial, reset_state}], buffers, memories}
timing:       {primary_clock, target_fmax_mhz, constraints}
resources:    {optimization_goal, expected:{lut?, ff?, bram?, dsp?}}    # 模型侧 → predicted_qor.json
verification: {testbench, scenarios, pass_condition}       # 指导自动 testbench 的验收
artifacts:    {top_module, rtl_sources, testbench, constraints, manifest, predicted_qor}   # 映射到工程包
```

#### System-HIS 作为类型化 IR——纪律与边界

System-HIS v1.2 冻结的是**核心 schema 层**（字段名、必需顶层 aspect、JSON/YAML 结构和
训练目标格式）。非破坏性验证扩展——well-formedness checks、枚举细化、可选 advisory 字段、
lowering-time diagnostics——可以在不升版本号的情况下继续演进。

**让 System-HIS 成为类型化 IR 而非结构化 prompt 的六条原则：**

1. **类型化契约字段，而非 prose。** `intent`（user_prompt、design_goal、assumptions）
   仅用于需求溯源和解释，**不作为 L0/L2 checker 的隐式语义来源**。所有机器可检查语义必须
   出现在 typed fields 中：`top`、`interfaces`、`components`、`instances`、`data_flow`、
   `control_flow`、`state`、`timing`、`resources`、`verification`、`artifacts`。

2. **Well-formedness。** 每个 instance 必须解析到唯一的 component；每个 data-flow 端点
   必须通过 symbol table 解析到 top port 或 instance port；width、direction、clock、reset、
   protocol 必须兼容；CDC path 必须携带 synchronizer intent；memory/protocol intent 必须
   被当前 lowerer 支持。（见以下 W1–W10。）

3. **Interface-first FPGA 语义。** ports 是物理信号边界；interfaces 是语义 bundle。
   valid-ready、AXI-stream、AXI-lite、BRAM、GPIO 等协议携带 role、channel、ordering、
   backpressure、reset behavior 和 checker template。L0 检查端口；L2/L2-UVM/L5 依赖
   interfaces 生成 stimulus、checker 和 host harness。

4. **受限 control grammar。** `control_flow.when` 和 `control_flow.effect` 使用受限、
   类型化的 guard/effect 语言（guard 嵌套上限 2 层）。自然语言 `intent` 可以解释规则，
   但只有 typed guards/effects 会被 checker 或 lowerer 使用。

5. **Contract-preserving lowering。** System-HIS lower 成：symbol table → project manifest
   → top shell → module declarations → interface bundles → testbench scaffold →
   assertion/checker templates → logical constraints → board-shell binding → model-fillable
   behavior holes。它保证跨文件结构一致性 by construction；完整行为正确性是 L2 的职责。

6. **Canonicalization。** 使用 canonical JSON serialization、stable IDs（独立于
   human-readable 名称）、确定性字段顺序和标准化参数表达式，用于 hashing、diff、REQ→HIS
   fidelity 评分、L0 checking 和训练目标。

**Intent / Contract / Advisory 字段分类：**

| 类 | 字段 | Checker 角色 |
|---|---|---|
| **Intent** | `intent.*`，解释性字符串 | 仅用于溯源——不参与 L0/L2 判定 |
| **Contract** | `top`、`interfaces`、`components`、`instances`、`data_flow`、`control_flow`、`state`、`verification.pass_condition` | L0/L2 必须满足 |
| **Advisory** | `resources.expected`、`timing.target_fmax_mhz`、`predicted_qor` | QoR/优化提示——不满足是软 budget miss，不是功能失败 |

**Well-formedness 规则（W1–W10）：**

- W1. 每个 `instance.component` 必须引用且只引用一个声明的 `component`。
- W2. 每个 `data_flow.path` 端点必须通过 symbol table 解析到已存在的 top port 或 instance port。
- W3. 每条连接上的端口 width 和 direction 必须类型兼容。
- W4. 每个拥有 state 的 instance 必须绑定到声明的 clock 和 reset。
- W5. 声明为 combinational 的 component 不得拥有 state、clock 或 reset。
- W6. 每个 `cdc:true` data-flow 必须跨越两个不同的时钟域，并必须经过 synchronizer
  component 或显式声明的 CDC primitive。
- W7. 每个 memory intent 若评估 BRAM/distributed/register 映射，则必须声明 `depth`、
  `width`、`read_latency`、`read_type` 和 `memory_style`。
- W8. 每个 verification scenario 必须引用已存在的 interfaces/signals，并映射到
  lowerer 支持的 stimulus/checker template。
- W9. 每个 logical constraint 必须引用已声明的 clock/port，且不得覆盖 board constraint。
- W10. `artifacts` 中列出的每个产物路径必须能从 `manifest.json` + `top_module` 复现。

**H0/H1/H2 System-HIS 校验层级**（在 L0 RTL checker 运行之前执行）：

- **H0** — schema 合法：JSON/YAML 结构、必需字段、枚举值。
- **H1** — well-formed：symbol 解析通过，端点存在，width/type 兼容，W1–W10 通过。
- **H2** — lowerable：所有 component/protocol/scenario 被当前 lowerer 和 testbench 生成器支持。

REQ2HIS 模型输出在进入 L0–L3 流水线之前于 H0/H1/H2 层评估。H0/H1/H2 失败有
独立的 `req_his_*` 诊断类，可由 FAILURE2PATCH Actor 修复而无需运行 EDA 工具。

**REQ→HIS fidelity 失败模式：**

`req_his_missing_requirement` | `req_his_wrong_width` | `req_his_wrong_protocol` |
`req_his_wrong_reset_kind` | `req_his_wrong_latency` | `req_his_missing_corner_case` |
`req_his_over_specified_behavior` | `req_his_under_specified_interface`

**System-HIS v1.2 的非目标：**

System-HIS **不**旨在：替代 FIRRTL/CIRCT/LLHD/Calyx 成为电路或编译器 IR；完整指定
周期级行为；编码板级物理实现细节；作为 IP 封装标准（cf. IP-XACT）；使工具执行变得
不必要；或在无 testbench/property 的情况下证明功能正确性。

v1.2 关键性质（完整理由见 freeze spec）：`components` vs `instances` 解决 v1.1 的重复实例歧义；seq/comb 区分由
**结构**表达（组合组件不拥有 `state`/`clock`/`reset_rule`）；`data_flow.timing` 让流水深度 + 吞吐成为一等
（前向兼容 Paper ②）；`control_flow` 承重、在 L2 验证、并驱动 testbench 生成；guard 嵌套上限 2 层（意图/RTL 分界）。
**暂定字段**（`data_flow.timing`、结构化 `control_flow`/FSM、guard 语法）是批准闸门的 Tier-2——已实现并校验，但在
真实任务跑通各字段前不强制进 REQ2HIS 目标。

**默认 clock/reset 纪律（钉死标签语义——Finding F）：**
- 默认任务族是**单时钟**；
- 默认复位是**同步、active-high**；
- 异步复位只出现在显式标注的任务族；
- 复位 **deassertion 必须同步**；
- 多时钟 / CDC 任务是**独立的难度族**，不混入普通任务。

System-HIS 中的规范写法：

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

L0/L2 检查复位极性/类型与 System-HIS 一致，且 valid/state 输出达到声明的复位态。

**Memory 意图字段（让 BRAM 推断成为可检查项，而非凭感觉）：**
- `memory_style: block | distributed | registers`
- `depth`、`width`、`read_latency`
- `read_type: sync | async`
- `read_during_write` 行为
- `byte_enable`（可选）

L3 检查：意图 BRAM/DSP 用量 vs 实测映射；意外的 FF/LUT memory 膨胀；BRAM miss 即使功能通过也记为**软 QoR 失败**。

**双重用途**（为什么 System-HIS 是贡献而非副产物）：它既是生成的**中间监督目标**（REQ→HIS），又是 L0
检查器据以验证所生成 RTL 的**ground-truth 契约**。

**隔离：** legacy / `system-his-v1.1` 样本打标保留作追溯，**排除在干净 REQ2HIS 训练集之外**（无迁移器；
在 v1.2 下重新生成才是干净数据的路径）。

字段随新设计族加入而按任务扩展——例如 Paper ② 的可搜索架构参数（并行度 / 流水深度 / memory banks）以后
会放在这里。

#### 完整轨迹 episode schema

每条轨迹是一个 **episode**，不是单条输入输出对。数据单元是：requirement → generate → 工具裁决 → 失败
→ 诊断 → 补丁 → 重新验证 → 记录结果。以下是规范的 episode 骨架：

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
      "tool": "openxc7_nextpnr", "status": "pass|fail|not_run",
      "wns_ns": null, "fmax_mhz": null,
      "lut": null, "ff": null, "bram": null, "dsp": null,
      "drc_warnings": [], "critical_warnings": [],
      "runtime_sec": null, "report_paths": []
    },
    "l4_commercial": {
      "tool": "vivado", "status": "pass|fail|not_run",
      "wns_ns": null, "fmax_mhz": null,
      "lut": null, "ff": null, "bram": null, "dsp": null,
      "drc_warnings": [], "methodology_warnings": [], "critical_warnings": [],
      "runtime_sec": null, "report_paths": []
    },
    "l4_agreement": {
      "class": "D0|D1|D2|D3|D4|not_applicable",
      "reason": "..."
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
    {"patch": "string", "diagnosis": {}, "result_after_patch": {}}
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

`failure_origin` 区分：模型生成的自然失败（`natural_model_failure`）、为覆盖率刻意注入的失败
（`injected_mutation`）、工具链环境本身引起的失败（`toolchain_environment_failure`——超时、license 不可用、
缺依赖、工具崩溃、OpenXC7 chipdb 问题）。只有前两类计入模型 pass/fail 分子/分母；`toolchain_environment_failure`
单独报告，排除在模型准确度指标之外。

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
  模型开始失败的膝点可见。**冻结协议：** 难度阈值在 pilot 集上校准一次（用 baseline (a) 前沿模型通过率），
  **在官方评测开始前冻结**，不在看到微调模型结果后再调整。校准结果记录每档的预期子模块数、跨文件契约数、
  协议类、目标 Fmax 范围和观测到的前沿通过率范围——以便审稿人确认冻结发生在 (c) 测量之前。
- **规模：** 千到约 1 万样本，不是百万级（数据量现实）。benchmark 题目以中小多模块设计为主（RL 规模加速器是
  *旗舰案例*，不是主体——见 scope）。现有确定性 `ProjectGenerator` 是构件库的种子。

#### L2 oracle 加固：coverage-qualified 仿真

L2 pass **不是**"仿真跑完了"的裁决。对 benchmark/评测题，L2 按 **coverage-qualified 功能验收**报告：
- **L2a** directed smoke 测试；
- **L2b** randomized/stress 场景；
- **L2c** 所需协议/数值覆盖。

设计只在**声明的测试契约下**才被语法与功能接受；因此我们在 L2 pass/fail 旁同时报告场景/覆盖画像。

各族最低覆盖目标：
- **valid-ready / stream：** ready 拉低时保持 valid、随机 stall、burst、idle 周期、事务中复位；
- **FIFO / skid buffer：** full、empty、almost_full/empty、同时 push-pop、overflow/underflow 尝试；
- **pipeline：** 不同 latency 路径、stall、in-flight 数据中 flush/reset；
- **arithmetic：** 有/无符号、边界值、overflow/截断；
- **memory/BRAM：** read-after-write、同地址冲突、sync vs async 读行为；
- **AXI-lite/stream 子集：** ordering、WSTRB、response channel、back-to-back 事务。

#### Public/hidden/stress 测试切分

每个评测题可含多种场景类：
- **public：** 对生成/修复回路可见；
- **hidden：** 仅用于最终验收；
- **randomized：** 固定 seed，记录在轨迹中；
- **stress：** 事务中复位、背压、边界值、full/empty、资源/时序压力。

最终 **L2 验收基于 hidden + stress 套件**，而非仅 public smoke——防止模型或修复回路"修到刚好过可见
testbench"。所有 seed 记录以便复现。

#### 协议断言库（protocol assertion library）

对协议密集设计，生成器从 **System-HIS 协议意图**（`protocol_agents`；SVA 或 immediate assertions）发出
断言/checker，与 scoreboard 互补。例如：
- valid 高且 ready 低 ⇒ payload 必须保持稳定；
- FIFO：empty 时不读；full 时不写；
- 复位清零 valid/state 输出；
- 无数据丢失或重复；
- 支持子集的 AXI-lite/stream ordering 与 response 检查；
- 结构上可查时，无组合 ready-valid 环。

**checker 来源声明：** 断言/checker 是**从模板生成的可信验证产物**，不是模型写的 oracle 逻辑。生成器（不是 LLM）
负责 checker 的正确性。这与"testbench 裁决模型的 RTL，不是反过来"的原则一致。

#### L2F 可选形式化属性检查

对选定的协议密集任务族，SR2FPGA 可运行从 System-HIS 协议意图生成的**有界形式化/属性 sanity 检查**。这是可选的
代表性层——不扩大 Paper ① 的主线范围——为 DV/formal 审稿人提供一个可防守的 hook：

- FIFO：有界序列下无 overflow / underflow；
- valid-ready：有界事务窗口内 payload 在 stall 时保持稳定；
- 有界周期数内复位收敛；
- one-hot FSM 不变式；
- 有界事务窗口内无数据重复/丢失；
- 支持子集的 AXI-lite response ordering。

L2F **不要求覆盖每条 Line-B 轨迹**，不作为 L2 pass 的门。在 benchmark/eval 题上运行，作为补充属性验收分数。
"coverage-qualified"不要求所有样本都有商业 SV functional coverage；覆盖可用确定性场景计数器、协议事件计数器、
scoreboard 事件 bin、以及开源工具支持时的可选行/翻转覆盖来实现。

#### SR2FPGA 可综合 RTL 子集

所有模型生成的 RTL 应遵循受限可综合子集，使 benchmark 不奖励"能仿真但不能综合"（或跨工具行为不一致）的 RTL。

**必需：** `` `default_nettype none ``；显式位宽；有状态模块显式复位行为；单驱动 register/net；memory/算术任务用
支持的 RAM/DSP 推断模板。
**允许：** parameter/localparam；generate 块；`always_ff`/`always_comb` 或严格 `always @*`/`always @(posedge clk)`；
有文档限制的 packed array；支持模板内的同步 memory。
**禁止：** `#` 延时；force/release；DPI；可综合 RTL 中的 class/动态数组；不可综合 `initial`（除显式支持的
ROM/init 策略外）；隐式 net；非任务明确要求的故意 latch；多驱动。

#### 约束分类：logical vs board

约束分两类：
- **logical 约束：** `create_clock`、目标周期、生成时钟、max delay、false path、multicycle path、时序意图；
- **board 约束：** 封装 pin、IOSTANDARD、物理时钟源、复位 pin、板级 IO profile。

模型 / System-HIS 可**选择 board profile 并发出 logical 时序意图**。board 约束从**受信任的 board profile 生成，
不由 LLM 自由书写**。L0 检查约束引用真端口、且所选 board profile 与顶层 shell 兼容，但**不**把任意 LLM 写的
board XDC 当作可信。

#### 切分策略（泛化 regime S1–S5）

结果按多种泛化 regime 报告，而非只 parameter-heldout：
- **S1 parameter-heldout：** 同族/同拓扑，未见 width/depth/latency/parallelism；
- **S2 topology-heldout：** 未见 wiring/拓扑模式；
- **S3 component-combination-heldout：** 已知构件的未见组合；
- **S4 family-heldout：** 整个设计族从训练中扣除；
- **S5 real-IP external：** 真实开源 IP 仅作外部验证、**绝不训练**。

主结果至少分离 in-distribution、parameter-heldout、topology-heldout、family-heldout 四种表现。

#### Real-IP 外部锚点策略

real-IP 集是**小而精的 5–10 个开源 IP 案例**，**仅外部验证、不训练**。每个案例记录 license、仓库 URL、commit
hash、改动、wrapper 变更、原 testbench 可用性、工具兼容补丁。

#### IP、许可与数据发布策略

SR2FPGA 自行生成 RTL 工程，以 EDA 工具作为客观 oracle。数据发布策略区分可公开发布的、受限的和仅内部的内容。

**数据发布档位：**

| 档位 | 内容 | 默认处置 |
|---|---|---|
| `open_public` | 生成的 requirement、System-HIS、RTL、testbench；开源工具（Verilator/Icarus/Yosys/OpenXC7）日志和结构化标签；L0–L4-open 元数据；失败分类法 | 随数据集公开发布 |
| `restricted_reference` | Vivado 商业参考结构化元数据（从报告规范化的时序/利用率摘要）；L4-commercial 标签 | 仅在机构许可审核和 Xilinx/AMD EULA 允许时发布 |
| `internal_only` | Vivado 原始时序/利用率/DRC/methodology 报告；Vivado DCP/checkpoint；bitstream；生成数据库；LogiCORE 产物；vendor IP；加密 IP | 归档用于内部审计和论文答辩；**不公开发布** |

**原则：**
- **归档 ≠ 公开发布。** 商业工具原始报告归档用于内部审计和答辩；以规范化元数据形式写入论文表格，须经许可审核。
- **Vivado 原始产物未经许可不用于公开模型训练。**
- **公开训练数据主要基于生成设计和开源工具标签。** Vivado 是商业参考验证流程，不是默认的公开训练标签来源。
- 真实开源 IP（S5 外部验证集）保留原仓库 license；wrapper 和工具兼容补丁在项目 license 下开源。真实 IP 不用于训练。
- 数据集 card（见"数据集 / benchmark card"）记录每个轨迹版本每个字段的发布档位。

### 评测层级与工具链

- **L0** 项目契约 + 跨文件一致性；**L1** lint（Verilator）；**L2** 功能仿真（Icarus Verilog）；**L3** 综合 +
  实测 QoR（Yosys）；**L4** 布局布线时序收敛（分为 **L4-open / L4-commercial / L4-agreement**）；**L5** 稀疏代表性上板（AC820-ZYNQ）。
- **L4-open：** 使用 OpenXC7 / nextpnr-xilinx 在 AC820-ZYNQ (`XC7Z020CLG484-2`) 上进行布局布线和时序收敛。
  这是主要的可复现开源物理流程，但仍依赖 board-specific OpenXC7 spike 验证。
- **L4-commercial：** 使用 Vivado 对相同 RTL、相同 generated core、相同固定 board shell、相同器件
  `XC7Z020CLG484-2` 和相同逻辑时序约束进行 synthesis + implementation。对于 **TCAD-strong** 版本，
  L4-commercial 必须在代表性子集上完成，但不要求覆盖每个 Line-B 轨迹。
- **L4-agreement：** 报告 OpenXC7/Vivado 在 pass/fail、资源、WNS/Fmax、DRC/methodology warning
  和 runtime 上的一致与不一致。
- **L0 一致性检查器（一个命名组件，不是脚注）：** 对照 System-HIS 契约验证所生成 RTL——top 实例化已声明的
  模块；每个端口名/方向/位宽、参数、跨模块连接都与 System-HIS 匹配；testbench 实例化真 top；约束引用真端口。
  这把跨文件一致性裁决自动化，并产出 **"cross-file consistency error rate"** 指标——单文件 benchmark 在结构上
  做不到的检查。
- **工具链（全开放为主，Vivado 退路）：** 综合和大规模数据到 **L3 用 Yosys**（开源、快、免费——适合千级样本）；
  **L4 时序收敛 + L5 上板用 OpenXC7（nextpnr-xilinx）跑在 AC820-ZYNQ**（XC7Z020CLG484-2，在 OpenXC7 支持清单内；
  220 DSP / ARM 承载更大设计含 RL 旗舰案例），给出全开放 req→bitstream→board 闭环——**待早期 spike 验证**。
  **Vivado 为退路/基线**，使 L4/L5 结果不会因开放工具不成熟而丢失。对于 **TRETS-safe** 工作，Vivado 是可选的；
  对于 **TCAD-strong** 版本，必须在代表性 L4 子集上完成 Vivado 商业参考验证。OpenXC7-vs-Vivado 的更深入
  可用性/QoR对比是加分项。所有 code/data/scripts/器件公开，工具版本锁定。

#### L1 lint 检查（可综合子集强制）

L1 检查隐式 net、位宽截断、未用/未驱动信号、推断 latch、组合环、时序逻辑里的阻塞赋值、组合逻辑里的非阻塞
赋值——强制 Benchmark 设计中定义的 SR2FPGA 可综合 RTL 子集。

#### L2S（可选）——综合后网表仿真 / 综合 sanity

**L2S** 是可选的综合后网表仿真 / 综合等价 sanity 阶段：在 Yosys `synth_xilinx` / `write_verilog` 产出的网表上
跑**同一份黑盒 testbench**，对比 RTL-sim 与 netlist-sim 行为。它能抓住综合后仿真行为发散的 RTL 构造：不完整
`case`、latch 推断、RAM 读语义、未初始化状态、X-optimism、阻塞/非阻塞误用、memory 映射差异。**L2S 不要求每条
大规模 Line-B 轨迹都跑**，但应在 benchmark/eval 集和代表性子集上跑。

#### L4 pass 定义

**L4 pass 需满足全部以下，而非仅 bitstream 生成：**
1. P&R 完成；
2. 目标时钟达标：声明目标频率下 **WNS ≥ 0**；
3. 无未约束时钟；
4. 无未约束 endpoint（除非显式说明并记录）；
5. 无 black box；
6. 无使实现失效的 critical warning；
7. 布线后利用率落在声明的资源预算内；
8. 生成核通过 board shell 连接、**未被优化掉**；
9. 时序/利用率/DRC 报告已归档。

**Vivado** run 归档：`report_timing_summary`、`report_utilization`、`report_clock_utilization`、`report_drc`、
`report_methodology`、`report_io`、（可选）`report_power`。**OpenXC7/nextpnr** run 归档：placement/routing 日志、
时序摘要、器件利用率、constraint/IO 错误、bitstream 生成状态。

#### OpenXC7：可行、待 spike——不是已完成证据

OpenXC7 为 Zynq-7 目标提供一条**貌似可行的全开放 L4/L5 路径**，但**在 board 专属 spike 落地前不当作证据**。
Vivado 保留为参考/退路流程，使物理结果不被开放工具成熟度阻塞。本 spec 任何地方都不得暗示全开放 L4/L5 已完成。
**OpenXC7 spike 必须验证：**
- 精确 part/package/speed grade：**XC7Z020CLG484-2**；
- board clock/reset/pin profile；
- XDC/PCF 约束正确性；
- bitstream 生成；
- bitstream 加载；
- board-shell smoke 测试；
- 在同一 RTL 和 logical 约束下与 Vivado 对比。

#### 板级验证纪律（L5）

L5 用**固定、人工审阅的 board harness**。模型**不**生成整个板级工程——三层分离把板级噪声挡在 pass-rate 指标外：
- **生成核（generated core）：** SR2FPGA 生成/修复/评测的 RTL；
- **固定 board shell：** clock/reset、pin 约束、AXI-lite/BRAM/UART/GPIO bridge、复位同步器、debug/status 寄存器；
  **版本锁定、人工审计**；
- **host harness：** 写输入向量、启动核、读输出/状态/signature、并与 golden checksum/model 比对的 Python/C 脚本。

**L5 pass 需：** bitstream 成功加载；host 脚本无 timeout 完成；生成核**通过固定 shell**收到输入并产出输出；
输出 signature/checksum 与 golden model 匹配；board 日志和 host 日志归档。

#### Verdict 模式 vs 全层诊断模式

为防早期 L0 失败审查掉 L1–L4 硬件语义失败分布（Issue 5），跑两种评测模式：
- **官方 verdict 模式：** **首个失败层**决定官方 `Lk` 验收层级。
- **全层诊断模式：** 早期失败后在安全处用 wrapper/normalization best-effort 续跑，收集额外 L1–L4 信号。

诊断信号**不提升官方通过层级**；仅用于失败分类法、LOG2DIAG 和更深的失败分布分析。

### 数据引擎（两条生产线）

- **Line A —— benchmark 评测集：** 质量优先，规模适中（几十到约几百题），每题含 requirement + System-HIS +
  contract + 功能 testbench + 约束 + 难度标签。
- **Line B —— 训练/轨迹数据：** 规模优先，全自动；大批量跑 generate → tools → fail → repair，收集 L0–L5 标签、
  诊断、补丁轨迹。难任务拉低首过率，所以失败/修复轨迹**靠设计**出现。**机时纪律：** 大规模回路只跑到 **L3
  （Yosys，秒级/样本）**；把慢的 **L4（Vivado，分钟级/样本）**留给评测集和代表性子集，不是每个样本。
- **输入候选来源：** 优先组合式构件库（免费、可控、量大、防泄漏）+ 少量 DeepSeek/本地候选。**所有标签来自工具**
  （工具蒸馏纯度）。
#### 失败注入套件（failure-injection suite）

为确保训练能覆盖罕见但重要的失败类型，SR2FPGA 向已知好的工程**刻意注入受控变异**。注入失败通过 episode
schema 中的 `failure_origin` 字段与自然模型失败区分，所有分析中单独处理。

代表性注入变异类型：
- 端口位宽不符（一个文件改了 parameter，未传播）；
- 复位极性不符（RTL active-low，HIS 声明 active-high）；
- 缺 `ready` stall（valid-ready 协议：数据路径忽略 `ready`）；
- BRAM 模板中异步读（强制 LUT/FF 映射）；
- 符号数转换被删（`$signed()` 被去掉，产生静默算术错误）；
- 缺 CDC 同步器（`cdc:true` 路径上无同步器实例）；
- 组合 ready-valid 环（ready 组合依赖 valid）；
- 非法逻辑约束（时钟周期错误、路径未约束）；
- 删除流水寄存器（在 L4 产生时序压力）；
- one-hot FSM 编码被改成二进制。

**协议：** 注入在参考工程通过 L0–L3（或适用时 L4）**之后**进行，确保变异前基线是干净的。注入点、变异类型、
预期失败层级记录在 episode 中。注入样本用于 LOG2DIAG 和 FAILURE2PATCH 训练覆盖；在失败热图中与自然失败
单独报告。

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
  | resource_overflow（放不下） | **L4** P&R | 能（L4 跑起来时） | nextpnr "failed to place"：cell 超器件 |
  | routing_congestion（布线拥塞） | **L4** P&R | 能（L4 跑起来时） | nextpnr 布线失败/拥塞 |
  | timing_violation（slack 为负） | **L4** P&R | 能（L4 跑起来时） | nextpnr/Vivado slack + 关键路径 → 该在哪打拍 |
  | constraint_error（未约束/非法 IO） | **L4** P&R | 能（L4 跑起来时） | nextpnr IO/约束错 vs XDC |

  （后六行是在用一份 practitioner 失败清单审计我们分类法后，对原三行的扩展——FPGA手记《AI写RTL》，2026-06，
  一篇非同行评审的行业博客，仅作完整性检查/motivation 佐证。只加了工具可检出的类，每类标注检出层。）

  **工具链/环境失败类别（toolchain_environment_failure）：** 单独的失败类 `toolchain_environment_failure`
  覆盖：工具超时；工具崩溃；缺依赖项；license 不可用（Vivado seat/server）；文件系统或路径错误；工具版本不支持
  的语法；OpenXC7 chipdb 问题；Vivado license/server 问题。这些**排除在模型 pass/fail 分子/分母之外**，
  作为独立的基础设施健康指标报告。比例高说明是环境问题，不是模型质量问题。

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

  **Failure-label 校准（regex 分类器要校准，不能盲信）：**
  - 跨 L1/L2/L3/L4 抽样 200–300 条工具日志；
  - 人工标注主失败类、次类、工具阶段、patch 类别；
  - 把 `classify_failure()` 与人工标签对比；
  - 报告 precision、recall、混淆矩阵；
  - 可选：对歧义日志用两名标注者或裁决。

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

#### SR2FPGA 工具内化模型栈

SR2FPGA 训练的是一个**项目级工具内化模型栈**，而非只是一个 SFT 任务集合。Actor 生成和修复 FPGA 工程；Critic
把 L0–L5 工具接受边界蒸馏成无工具的通过/风险/QoR 预测。这个定位把方法从"我们做 SFT"升级为"我们训练
Actor + Critic 来内化 EDA 工具链"。

**Actor**（生成与修复，在工具验证轨迹上训练）：
- `REQ2HIS` — requirement → System-HIS（结构化需求理解）；
- `HIS2PROJECT` — System-HIS → 多文件 RTL 工程（skeleton 填充）；
- `LOG2DIAG` — 工具日志 → 结构化诊断（内化工具错误语义）；
- `FAILURE2PATCH` — 结构化诊断 → 补丁（内化修复启发式）；
- `ARCH_MUTATE` — HIS 架构参数变异（为 Paper ② 搜索提供输入）。

**Critic**（预测与风险估计，训练目标是内化工具裁决）：
- `PROJECT2RISK` — 工程 → L0–L3 风险分（工具接受度预测）；
- `PROJECT2LEVEL` — 工程 → 预测最高通过层级 L0–L5；
- `PATCH2VERIFY` — 候选补丁 → 不调工具的通过/不通过预测；
- `PROJECT2QOR` — 工程 → 预测 LUT/FF/BRAM/DSP/Fmax（即 `QOR_PRED`）。

**QoR-search head**（Paper ② 的前置，现在就设计好以保持连贯性）：
- `HIS2QOR` — HIS 架构参数 → 预测 QoR（快速代理适应度）；
- `ARCH2RANK` — 按 QoR 轴 Pareto 排名 HIS 变体；
- Pareto/风险过滤以减少搜索过程中昂贵的 L4 工具调用。

Critic 任务是让"内化"可被测量的关键：若 `PROJECT2LEVEL` 准确，说明模型内化了工具的接受边界；若
`PROJECT2QOR` 与实测 QoR 相关，说明模型内化了资源利用。**此 claim 仅在模型生成的行为 hole 非平凡时有效**
——由 `behavior_hole_count` 和 `model_token_fraction` 记录；否则该方法退化为带平凡 Critic 的确定性生成器。

#### Contract-preserving 生成透明度

为预防"你的确定性生成器搭好工程、LLM 只填 trivial hole"的质疑，**每个样本/轨迹都记录哪些产物是确定性的、
哪些是模型生成的**：

```
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

核心表述：**跨文件结构从 System-HIS 生成或受其约束；行为 RTL 由模型生成；工具对两者裁决。** 方法目标是
**跨文件一致性按构造成立，功能/物理正确性靠验证**。

#### TCAD-strong 方法 claim（一句硬技术点）

必须贯穿 Method / Contributions / abstract draft 的一句：**System-HIS 约束的工程综合**——确定性 lowering 让
跨文件一致性*按构造*成立，而模型生成的行为 hole 用**结构化 EDA 工具轨迹**训练与修复。实验要对应该 claim 给出：
- L0 结构错误率趋零；
- L2 功能不退化；
- 修复迭代数下降；
- 结构化 diagnosis→patch 优于 raw-log 修复。

### 方法陈述（怎么讲清楚；算不算"新方法"？）

**一句话回答"你用了什么方法？"：** *工具验证学习（tool-verified learning）*——把 EDA 工具链的客观判断**蒸馏进
模型**，经由 **System-HIS 需求级 IR**（REQ→HIS→多文件工程），用 **L0–L5 工具反馈作监督**，把**结构化
diagnosis→patch** 修复轨迹存成可复用数据集，并用 **(a)/(b)/(c)** 量化工具反馈和微调各自的增益。锚点：
*蒸馏的是工具，不是 LLM。*

**三个 register（被追问时分清）：** (1) **造数据方法**——工具验证轨迹工厂（已做）；(2) **评测方法**——项目级
L0–L5 + L0 一致性检查器 + (a)/(b)/(c)（已做）；(3) **训模型方法**——在轨迹任务上 SFT（REQ2HIS/HIS2PROJECT/
LOG2DIAG/FAILURE2PATCH/QOR_PRED）（设计了，还没训）。

**算不算"新方法"？——诚实，取决于粒度：**

- **当作新技术/新算法：不算。** 优化器是标准的（SFT/QLoRA），修复回路成熟（AutoChip…），中间表示已有
  （HLS、CPPL、FIRRTL），蒸馏工具/测试反馈已有（RL 簇、ChipSeek-R1）。没有一块砖是新发明的；刻薄审稿人会
  （正确地）说"已知技术搬到新领域"，TCAD 不会接受"QLoRA + 一个工具回路"当方法贡献。
- **当作新方法学/框架：算，可防守。** 这套特定组合——工具预言机蒸馏 + System-HIS *需求级* IR + *项目级*
  L0–L5 + (a)/(b)/(c) 分解——没人做过；砖是旧的，搭法是新的。这是新的*做事方式*，不是新*工具*。
- **要成为强意义（TCAD）的"新方法"：** 必须把上面某个 method-novelty 候选做成真技术贡献——最佳是
  **System-HIS 约束 / 验证引导解码**（解码时让跨文件一致性按*构造*成立，区别于 CPPL 的电路级 IR 编译期检查）。
  这个*如果做出来*是真新的；现在是候选、没做。

**诚实声称纪律（答辩用）：** 声称"一套面向项目级、工具验证的 RTL 工程生成的**新方法学**"和"我在做深的方法
新颖性是 System-HIS 约束生成"；**不要**声称"一个新训练算法"。venue 校准：TRETS 看重框架 + 可复现 + 数据集
（新颖性压力小）；TCAD 要求做实一个 method-novelty 候选。

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

**可选 Critic 模式**——若 Critic 任务已训练，测量可扩展两个额外点：

- **(c1)** 微调 **Actor**、首次尝试、不用真实工具（= 当前 (c) 点）；
- **(c2)** 微调 **Actor + 学习 Critic** 自检/自修复、不用真实工具（Critic 在不调工具的情况下判断 Actor 输出）。

解读：
- **c1 − a：** 工具验证微调对生成的提升；
- **c2 − c1：** 学习 Critic 是否有无工具自诊断价值；
- **b − c2：** 真实工具仍然能弥合的差距（Critic 弥合不了的部分）。

此分解不是 TRETS-safe 版的必需；若 Critic 任务已训练，则作为 TCAD-strong 加强项。主 (a)/(b)/(c) 框架不变；
(c1)/(c2) 作为 Critic 模式消融标注，不替换 (c)。

#### 统计测量协议

所有 (a)/(b)/(c) 对比用**相同**的任务集、split、hidden 测试、修复预算、timeout、工具版本、prompt family
（官方评测前冻结）、以及（适用时）随机 seed。报告：
- **pass@1**；适用时 **pass@k**；
- N 次迭代内修复成功率；修复迭代中位数；
- **L0/L1/L2/L3/L4 survival curve**；
- 分档 T1–T4 结果；分族结果；
- **b−a** 与 **c−a** 的配对比较；
- 样本量允许时 bootstrap **95% 置信区间**。

**不要把 L0–L5 压成单一平均序数分**——按层报通过率 / survival curve。

#### Baselines（B0–B6）

- **B0** 直接 req→project；
- **B1** req→HIS→project，无确定性 skeleton；
- **B2** req→HIS→skeleton→模型填行为 hole；
- **B3** AutoChip 式 raw-log 修复；
- **B4** SR2FPGA 结构化 LOG2DIAG→PATCH 修复；
- **B5** 微调小模型，首次尝试；
- **B6** 微调小模型 + 修复。

**非 LLM sanity baseline**（不作为 LLM baseline 对比；用于验证 benchmark、锚定 QoR 目标）：

- **B_ref：** 确定性参考实现（生成器产出）；用于验证 oracle HIS、testbench 和约束内部自洽，并证明任务可实现。
  B_ref 通过 L0–L3（或 L4）是任务进入评测集的前提。
- **B_template：** 确定性 skeleton + 构件库组合，无模型生成行为 hole；用于校准任务可行性、建立参考 QoR（LUT/
  FF/BRAM/DSP/Fmax budget）。模型生成设计的 QoR 相对于 B_template QoR 报告。

### 计划的消融

- **System-HIS：** req→HIS→project vs req→project（证明 System-HIS 是贡献而非装饰——这支撑差异化第 1 点）。
- **QoR 预测校准：** 预测 vs 工具实测的相关性 / 校准曲线（通用 Yosys-L3 的 LUT 是假的，Finding G，所以真正的
  资源/时序校准需 `synth_xilinx` 或 OpenXC7 L4 报告）（预测 QoR 必须保持仅模型、绝不泄漏实测——保持现有
  `predicted_qor.json` / `measured_qor.json` 分离）。
- **REQ→HIS fidelity：** 生成的 System-HIS vs oracle/人工 System-HIS，使表示作为**需求理解目标**评估，而非仅
  自洽契约。
- **Contract-preserving（L0-by-construction）：** System-HIS 约束的 skeleton 生成 vs 自由生成——证明它把 L0
  结构错误率推向零且不伤 L2。

**完整消融表：**
- 有/无 System-HIS；
- 有/无 contract-preserving skeleton 生成；
- raw 工具日志 vs 结构化诊断；
- 仅 public 测试 vs hidden/random/stress 测试；
- 工具过滤轨迹 vs 未过滤 LLM 轨迹；
- 协议密集子集上 L2-core vs L2-UVM；
- 适用处 generic Yosys QoR vs `synth_xilinx`/L4 QoR。

#### QoR 结果：budget / reference / ratio（非裸计数）

QoR **相对任务预算与参考实现**报告，而非只报裸计数。**不要把通用 Yosys-L3 LUT 当强 QoR 声明；有意义的 FPGA
QoR 用 `synth_xilinx` 和/或 OpenXC7/Vivado L4 报告。** 每个任务可声明 `resource_budget`（max_lut/ff/bram/dsp）、
`timing_budget`（target_fmax_mhz）、`reference_qor`（确定性参考实现）。报告：budget 通过率；generated/reference 的
LUT、FF、BRAM/DSP、Fmax 比；以及适用处 Pareto dominance / non-dominated 数。

#### P&R 噪声与 QoR 校准协议

布线后**利用率相对稳定**，可单次 run 报告。**时序指标（WNS/Fmax）是后端启发式、seed 敏感**：对代表性 L4 子集，
在支持处跑多 seed 并报 **mean、std、best、worst**。QoR 预测主要按 **ranking/filtering/risk estimation** 评估：
Spearman rank correlation、calibration error、top-k 设计选择准确度、坏设计过滤准确度——**MAPE 仅作次要指标**。

#### L2-core vs 可选 L2-UVM

UVM 是**可选的 L2-UVM 加强层，不是默认可扩展 oracle**：
- **L2-core：** 确定性黑盒自检仿真——Line B 的默认；
- **L2-UVM：** 对选定协议密集任务（valid-ready stream、FIFO/skid buffer、AXI-stream 子集、AXI-lite 寄存器块、
  RL 加速器 host 接口）的可选事务级 UVM 验证。

UVM 环境从 **System-HIS + 受信任模板**生成，不由 LLM 自由编写。**L2-core vs L2-UVM stress 消融：** 报告 directed
L2 通过但 randomized/coverage 驱动 L2-UVM 失败的案例，及覆盖差。

### 范围变体（scope variants）

两个干净出口，消除"RQ1/RQ2/RQ4 是最小核心"与"(a)/(b)/(c) 微调是必备"之间的内部不一致。数据集 + benchmark +
轨迹工厂无论如何都撑得起一篇论文；区别在于训练好的模型和一个物理结果是否落地。

**TRETS-safe 版：**
- System-HIS；
- L0–L5 benchmark 定义；
- 工具验证轨迹工厂；
- L0–L3 规模化结果；
- 工具在环修复 **b−a**；
- 失败分类法 / 语义鸿沟热图；
- OpenXC7 作为主要开源流程；
- Vivado 退路可选；
- 如果条件允许，提供 L4/L5-min 代表性物理证据。

**TCAD-strong 版：**
- 全部 TRETS-safe 组件；
- System-HIS 约束 / contract-preserving 生成；
- 训练好的模型 **(c)**；
- System-HIS 消融；
- 结构化 diagnosis→patch 消融；
- **在代表性 L4 子集上进行 Vivado 商业参考验证**；
- 至少一个验证过的 **L4 / L5-min** 物理结果；
- OpenXC7/Vivado 一致与不一致分析。

**RQ5 QoR 预测：** 非 Paper ① 必备结论；**若有 L4 标签**，可作 calibration preview / Paper ② 桥接报告。

**L5-min（上板范围）：**
- 1–3 个代表性设计；
- 固定 board shell；
- host 脚本；
- golden checksum/signature；
- 归档日志。

**L5-scale 明确不在 Paper ① 范围。** L5 作为端到端物理可行性证据报告，**不是**大规模 pass-rate 指标。

**不在范围（YAGNI）：** 重训大生成模型（算力不足）；GA/RL / 重 QoR 优化（Paper ②，需 QoR 预测器当代理适应度）；
商业规模大器件结果。

### Threats to validity 与三道闸门（referee-aware）

一次审稿人视角模拟评审（`docs/research-threats-to-validity-2026-06-25.md` + `.zh.md`）认定：本计划目前是强、诚实的
**计划 + 基础设施 + discovery pilot，还不是带证据的贡献**。三个侧重不同的审稿人（证据/严谨；新颖性；方法学/可复现）
**收敛到三道闸门**，是站得住的 TCAD 方法论文必须过的——每道正是 spec 已标为 gated 的事：

1. **冻结协议下、规模化训练一个模型**——(c)/RQ3 headline 还不存在（没训模型）；pilot 是 N≈1/档、单模型、探索性。
   按档报 (a)/(b)/(c) 带置信区间；冻结 prompt（prompt 泄漏已观察到，failure-repair Issue 4）。
2. **把约束解码做出来并验证**——方法新颖性核（`2026-06-25-system-his-constrained-decoding-design.md`）只有设计；
   没有它，贡献是*方法学*不是*方法*。证明它让 L0 按构造→~0 且不伤 L2。
3. **完成带商业参考的 L4/L5 物理证据。** TCAD 的物理实现 claim 不能只依赖尚未验证的
   OpenXC7 spike。TCAD-strong 的最低门槛是：至少一个 OpenXC7 L4/L5-min 结果，
   并在代表性 L4 子集上用 Vivado 作为商业参考流程验证相同 RTL、相同固定 board shell、
   相同器件和相同逻辑约束。需要固定工具版本，保存 timing/utilization/DRC/methodology
   reports，并明确分类 OpenXC7/Vivado 不一致案例。

外加审稿人会要的使能性修复：数据质量（噪声标签、假 LUT——F/E/G/H0）+ 全层诊断模式，使 L0 短路不审查掉 L1–L4 分布
（Issue 5）。**要保留的诚实优点：** 该计划不过度声称——区分 discovery vs evidence、把物理本质限制划在范围外；
manuscript 里保持这股纪律。

### Claim discipline（声称纪律）

用 **"tool-accepted under the specified contract"**、**"functionally accepted by the generated golden-model
testbench"**、**"physically implemented under the specified constraints"** 或 **"Lk-pass"**。避免过度声称：
"correct design"、"fully verified"、"silicon-proven"、"tool replacement"。工具和 testbench 是**声明契约下的客观
oracle，不是正确性的完整证明**。

### 审稿人问题清单（reviewer-question checklist）

spec 应能直接回答以下每一条：
1. **System-HIS 不只是 prompt 模板吗？** → REQ→HIS fidelity + System-HIS 消融。
2. **contract-preserving 生成会让任务变 trivial 吗？** → 确定性 vs 模型生成产物元数据 + L2/L3/L4 结果。
3. **testbench 是否太弱？** → hidden/random/stress 测试 + 覆盖 + 断言 + 可选 L2-UVM。
4. **RTL 仿真能挺过综合吗？** → L2S 综合后网表仿真。
5. **L4 时序是真的吗？** → WNS ≥ 0、无未约束路径、无 black box、归档 DRC/时序报告。
6. **OpenXC7 在这块板上真能跑吗？** → board 专属 spike + Vivado 参考流程。
7. **QoR 有意义吗？** → `synth_xilinx`/L4 QoR、budget、reference 比、P&R 噪声协议。
8. **数据是否泄漏生成器模板？** → topology/family/component-heldout 切分（S1–S5）。
9. **失败分类法是真的吗？** → 人工日志标注校准。
10. **SFT 是否只是蒸馏一个 LLM？** → 多源输入 + 工具过滤 vs 未过滤消融 + 仅工具标签。

## Paper ②（简述）

工具在环 QoR 优化（LUT / 性能 / 功耗）：在架构/System-HIS 参数上做 GA 和/或用工具导出奖励做 RL，用 Paper ①
的 QoR 预测器当快速代理适应度，使大规模搜索在一块 GPU 上可行。GA 优化架构参数，不是裸 Verilog token（与
research-objective 文档一致）。RL 旗舰案例自然落在这里，在 AC820-ZYNQ（220 DSP + ARM）上。最接近的先前工作：
**CktEvo**（仓库级闭环 LLM+工具链 PPA 优化）——区别在于搜 System-HIS 架构参数空间（而非编辑已有仓库），用蒸馏
QoR 预测器当代理适应度，带 CktEvo 没有的物理（L4）标签。

## Artifact 与可复现性清单

用于 artifact review（TCAD / TRETS / ACM artifact track），公开 artifact 应包含或引用：

**环境：**
- 复现 L0–L3 的 Docker / Nix 环境（精确的 Verilator、Icarus、Yosys 版本）；
- L4-open 用 OpenXC7 / nextpnr-xilinx 版本；
- restricted 商业参考子集记录的 Vivado 版本；
- board profile 版本（AC820-ZYNQ XC7Z020CLG484-2）；
- System-HIS schema 版本（`system-his-v1.2`）；
- 生成器 commit hash 与随机 seed。

**数据：**
- 任务切分清单（S1–S5、T1–T4 分配）；
- prompt 版本（官方评测前冻结）；
- 修复预算、timeout 和工具调用计账；
- 各轨迹 `data_release` 档位标记；
- 数据集 card（见下文）。

**复现结果：**
- 评测集 L0–L3 评测命令行；
- 各阶段（L0/L1/L2/L3 典型）预期运行时间；
- 代表性 L4-open（OpenXC7）和 L4-commercial（Vivado）评测脚本；
- L5 board-shell harness（固定 shell 版本锁定、host 脚本、golden checksum）。

## 数据集 / Benchmark Card

每个发布的数据集版本，报告并归档：

| 字段 | 是否必需 |
|---|---|
| 版本号 | 是 |
| 按族和难度档的任务数 | 是 |
| 按 split S1–S5 的轨迹数 | 是 |
| 生成 vs 真实 IP 外部（S5）的比例 | 是 |
| 工具版本（Verilator/Icarus/Yosys/OpenXC7/Vivado） | 是 |
| L0–L4-open 标签可用性 | 是 |
| L4-commercial 标签可用性 | 条件（若许可通过） |
| Hidden 测试策略 | 是 |
| 覆盖 / 场景画像 | 是 |
| 每字段数据发布档位 | 是 |
| 已知局限 | 是 |
| 生成数据和代码的 license | 是 |
| 引用格式 | 是 |

数据集 card 是一个具名可交付物，不是事后补丁——它是让数据贡献可被他人审查和复现的保证。

## 与现有文档的关系

本文界定并落地 `docs/research-objective-sr2fpga-tcad.md`。两者不一致时，本重定向（算力校准、拆成 ①/②、工具
预言机作为显式蒸馏目标、Zynq 可复现流程）主导近期工作。若采纳本方向，请更新 research-objective 文档。

**Companion specs（待主要小节稳定后拆出）：**
本文目前同时承担设计 spec 和 paper 协议参考文档。待各节稳定后，以下 companion spec 应从主文档拆出，以保持主文档可执行：

| Companion spec | 内容 |
|---|---|
| `sr2fpga-data-release-and-licensing.md` | 完整数据发布策略、许可审核清单、字段级档位分配 |
| `sr2fpga-trajectory-schema.md` | 版本化完整 episode schema、字段定义、迁移说明 |
| `sr2fpga-model-stack.md` | Actor/Critic/QoR-head 架构、训练任务定义、loss 形式 |
| `sr2fpga-artifact-reproducibility.md` | 完整 artifact 清单、Docker/Nix 环境规范、命令行参考 |
| `sr2fpga-l4-openxc7-vivado-protocol.md` | L4 运行协议、board shell 规范、一致性分类法、报告归档格式 |

在此之前，主 spec 携带所有这些主题的摘要版（如上），companion spec 是前向指针，不是阻塞项。

## 立即下一步

框架前提与构件库 MVP 已验证；v1.2 freeze 已实现（Tier-1）。已重排，使 oracle 加固先于规模、规模先于训练：

1. **测量冻结（measurement freeze）**——冻结 prompt、seed、timeout、修复预算、工具版本、hidden 测试、split 策略、
   pass/warn/fail 语义。（同时在真实 FSM/流水任务上跑通暂定字段——`data_flow.timing`、结构化 `control_flow`/FSM、
   guard 语法——以批准 v1.2 Tier-2；RL-agent FSM 为参照。）
2. **Oracle 加固**——加 REQ→HIS fidelity；加 L2 hidden/random/stress 测试 + 覆盖目标；加断言库；加可选 L2S
   综合后网表仿真；定稿 L2-core / 可选 L2-UVM 切分。
2.5. **IP/数据发布策略落地**——确定 open_public / restricted_reference / internal_only 对每个轨迹字段的档位分配；
   确认 Vivado 结构化元数据能否在许可下发布；给所有 episode schema 字段标注发布档位；记录机构法律审核状态。
3. **数据质量修复**——F（reset/clock 标签噪声）、E（分类法名漂移）、G（Yosys-L3 LUT 假 → 上 `synth_xilinx` 或把
   QoR 推到 L4）、H0（结构化工具信号抽取：L2 失配明细、L4 失败族、通过时警告）。
4. **Contract-preserving 生成**——System-HIS → 确定性工程 skeleton；模型填行为 hole；记录确定性 vs 模型生成
   产物元数据；跑 L0-by-construction 消融。
5. **全层诊断模式**——官方 verdict 模式保持首失败层；诊断模式收集更深 L1–L4 信号（Issue 5）。
6. **规模化 Line B 到 L3**——为 RQ3 生成足够轨迹；按 split 策略 S1–S5 报告。（现有数据 N≈1/档——discovery，非
   evidence。）
7. **OpenXC7 + Vivado L4 参考 spike**
   - 将一个 generated design 通过 OpenXC7 跑到 bitstream
   - 将相同 RTL/core/board-shell/logical constraints 通过 Vivado 跑一遍
   - 确认器件为 `XC7Z020CLG484-2`
   - 保存 timing/utilization/DRC/methodology reports
   - 分类 OpenXC7/Vivado 一致或不一致
   - 用该结果定义第一批 L4-open/L4-commercial 标签
8. **第一个 SFT 模型**——产出第一个 (c) 点；先做 REQ2HIS、HIS2PROJECT、LOG2DIAG、FAILURE2PATCH；在冻结的
   (a)/(b)/(c) 协议下评测（单卡 4090 SFT）。
8.5. **Artifact 打包**——创建数据集 card（见"数据集 / Benchmark Card"）；创建工具版本清单；创建带 Docker/Nix 环境
   的 L0–L3 复现脚本；创建代表性 L4-open / L4-commercial 评测脚本；版本锁定 board shell。

第 1–6 步是官方 (a)/(b)/(c) 测量的前置门；OpenXC7/Vivado L4-min（7）并行、独立。schema freeze 与 OpenXC7 spike
的 spec/plan 均已存在（writing-plans 已完成）；剩下的门是执行 + 规模，不是更多设计。
