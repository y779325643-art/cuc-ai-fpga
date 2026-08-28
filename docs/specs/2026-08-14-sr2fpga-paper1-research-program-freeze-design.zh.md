# SR2FPGA Paper 1 研究计划冻结规范

> **说明：** 本文是英文权威版
> `2026-08-14-sr2fpga-paper1-research-program-freeze-design.md` 的中文 companion，
> 用于中文阅读与讨论。**两者不一致时，以英文版为准。** 本文保留英文版中的
> 方法编号、指标缩写、工件名和规范性边界，不将候选方案改写为既有结果。

## 状态与权威性

- 状态：**当前有效的 Paper 1 研究与实验权威规范**
- 版本：`paper1-freeze-v1.7`
- 生效日期：2026-08-27
- 目标期刊：**ACM Transactions on Reconfigurable Technology and Systems（TRETS）**
- 证据截止点：本地 `develop@bd516c110862`，以及当前工作树中的文档与证据审查结果
- 范围：产品/问题边界、需求裁决与 ambiguity audit、研究问题、方法因素、基准总体、信息权限、指标、实验 gate、论断规则和论文退出条件
- 实现状态：协议设计阶段；尚未依据本冻结规范运行会产生研究结果的实验

本文是**研究计划冻结规范**，不是已经签署的 campaign 冻结规范。下文的候选数据划分、规划样本量、方法定义和 gate 顺序，只有在 G4a、排除于正式实验之外的 G5 pilot 以及最终 G4b campaign manifest 完成后，才成为可执行协议。任何文件都不得把候选数据划分描述为经验结果或已经可以运行的基准。

v1.2 amendment 在打开任何正式模型结果或隐藏结果之前完成。它增加了一个有边界的生成前 ambiguity audit，分开产品北极星与 Paper-1 estimand，并补齐共同工程契约、信息权限、预算和评测器义务。它不代表新增实现结果。

v1.3 amendment 将投稿目标改为 TRETS，并从 Paper-1 中删除全部模型训练。RQ3 与 M6U/M6F/M6T/M6TR 不再属于 Paper-1 estimand、方法阶梯、gate、必需工件或论断空间。既有 training 代码和 contracts 作为仓库基础设施保留，但不执行、不发布，也不作为 Paper-1 工作或贡献。

v1.4 amendment 将有边界的 target-profile adaptation 加入 RQ4。它要求在同一语义义务下预注册成对 FPGA target profiles，并在正式结果产生前冻结功能不变量、必须/允许的工程变化、L3/L4 终点、分母与成本规则。该 amendment 不增加模型训练，也不授权一般性跨器件、跨工具、跨厂商、bitstream 或板级可移植性论断；它在 G4b 之前、且任何正式模型、隐藏或 profile-adaptation 结果打开之前生效。

v1.5 amendment 将 Paper-1 最小投稿路径收束为 RQ1/RQ2 的 M0-M5 主实验；RQ0 保留为独立、强制且有边界的 safety/conformance audit；代表性 OpenXC7 L4 只作为次要物理深度证据。target-profile adaptation 降为单独冻结的可选扩展，未启用它不会阻塞核心 G4b 或 Paper-1 退出。v1.5 同时冻结 artifact-derived 的正向 G3 验收、first-class paired block/seed、共享工件与成本核算、隐藏评测 missingness，以及家族等权 macro 上无歧义的确认性检验。该 amendment 不改变既有实现或经验结果，也不授权模型、正式隐藏评测或物理 campaign。

v1.6 amendment 将 repeated-measure identity、provider decoding-seed provenance 与本地 execution-order randomization 分开。G4b 必须只选择一种 `decoding_control_mode`：有文档且经审核的 provider seed control，或在冻结 provider 配置下估计期望方法效应的 `stochastic_blocked` 设计。后者不得声称方法共享同一随机实现、seed 因果效应或 bitwise replay。该修改由 development-only capability diagnostic 触发；DeepSeek 的三次相同输出不是方法结果，也不证明 deterministic seed control。G3 仍须验证 artifact-derived classifier 与 strict guard，但不要求现实外部 provider 已 eligible。本 amendment 在 G4b 和任何正式模型/隐藏结果之前生效。

v1.7 amendment 在任何 G5 natural-model outcome 或正式结果打开前修改 RQ1 的确认性层级。RQ1 不再使用 fixed sequence，而由 `M4−M3` 与 `M4−M0` 构成两项主要 Holm family；`M3−M2` 仍强制报告，但降为预注册 secondary estimation contrast。`M4−M3` 解释为 deterministic materialization 与 editable-surface policy 的联合增量，不是 skeleton 文本本身的纯效应。该 amendment 不改变总体、方法、终点、信息权限、预算、RQ2 family、RQ0 audit、RQ4 分析或数据收集义务；所有已签署且合格的 M0-M5 condition 仍须完整执行并报告。

本文取代此前的 Paper 1 reframe、official-evaluation 和强制
constrained-decoding 提案。这些已被取代的文档由 Git 历史保存，不再作为
工作树中的并行权威。

本文不取代机器契约、运行时行为、测试、证据账本或稳定工件。不同来源冲突时，按以下顺序裁决：

1. 由 `contracts/manifest.json` 注册的版本化契约、当前代码和可复现测试；
2. 任务账本和已提交报告中由工件支撑的证据；
3. `docs/current-status.md` 和当前各项目 README；
4. 本研究与实验规范；
5. Git 历史中可查但不具当前权威性的旧材料。

支撑本冻结规范的论证与论断账本位于
[`docs/research-program/paper1-v1/`](../research-program/paper1-v1/README.md)。

## 1. 决策摘要

Paper 1 将研究**以契约为依据的 FPGA 工程生成、验证器隔离与可复现的工程级评测**。论文不会仅凭仓库级智能体、自动工具使用、迭代式 RTL 修复、可执行验收 gate 或轨迹记录来主张创新。HORIZON 及相邻系统已使这些能力成为强基线。

产品北极星比论文的因果 estimand 更宽：面对可能不完整、歧义或不受支持的需求，系统应生成一个具有独立证据的闭合工程，或者诚实终止为 `needs_clarification`、`capability_gap` 或 `not_run`。Paper 1 不主张解决这一无边界产品问题。论文把生成前的需求边界作为独立审计；正式 VPP 总体只包含经评测方裁决、在 G4b 冻结且可评分的需求。

论文的工程级评测对象是通过所声明 L3 flow 的完整多文件 RTL 工程，而不是普遍可部署的 bitstream 或板级系统。核心经验问题是：

> 在模型、公开需求事实、反馈权限以及总计算/工具预算均匹配的条件下，contract-grounded deterministic materialization 能否优于消费同一 System-HIS 的自由工程生成，完整且未训练的 System-HIS pipeline 能否优于 Direct；契约感知的公开修复能否经受评测方拥有的一次性隐藏检查，并形成可对账的正确性—成本前沿？

因此，论文的最低要求包括：

1. 共享且版本化的 requirement-intake boundary，以及一个与 VPP 分离、衡量 silent proceed、false blocking、provenance 和 clarification 行为的 ambiguity audit；
2. 方法中立的共同工程契约，以及独立适用且闭合的 System-HIS treatment；
3. 一个按家族留出、由评测器拥有隐藏最终评测的冻结基准；
4. 预算匹配的直接、无类型结构化、HIS、skeleton 和修复条件；
5. 覆盖每个 M0-M5 episode 的收敛与总成本核算，包括失败、`not_run`、基础设施结果和 repair attempt；
6. 有代表性的 OpenXC7 L4 确认，并明确与一般性 L4、Vivado、bitstream、板级和可移植性论断分开。

只有通过独立的结果前冻结义务，才可增加成对 target-profile adaptation 扩展。它不属于最小确认性比较族，也不得拖延核心 M0-M5 实验。

模型训练或微调、Tier-B 约束解码、QoR 预测、广泛 Vivado closure、`.bit` 生成、L5 以及 GA/RL 架构搜索均不属于 Paper-1 最小范围。它们只能作为 future work，不得拖延或替代 M0-M5 留出评测。

## 2. 研究路线为何改变

HORIZON 表明，固定的通用智能体可以依据可执行评测器演化硬件仓库，并使选定测试套件收敛到历史最佳结果。其 project pack 是控制平面，git 历史是可重放的状态/轨迹载体，其最有信息量的结果还包括收敛成本与长尾。HORIZON 不训练策略，也不报告物理 QoR/PPA 结果；它还警告，修复过程可见的评测反馈可能造成过拟合式求解。

因此，SR2FPGA 可辩护的差异必须是一个经过检验的组合，而不能只是宣称：

- System-HIS 是类型化的需求到工程语义契约，而不是回合控制平面；
- 显式隔离修复可见诊断与隐藏最终语义 oracle；
- 用版本化 episode/trajectory 审计 attempt、repair、cost、provenance 与 missingness；
- 证据深度从工程一致性延伸到综合和有代表性的物理子集。

Paper-1 不包含 learned treatment。即使前一个 contrast 为负，签署协议中的 M0-M5 条件仍必须执行并报告。负结果只改变可支持的论断，不改变 denominator、method set 或 evidence record。

## 3. 冻结时的实现快照

本节保留 2026-08-24 冻结时的实现快照，不再作为可变当前状态的权威来源。此后包括
development/excluded evaluator authority 迁移在内的实现进展，以
`docs/current-status.md` 和下位代码架构规范为准；这里的历史快照不改变冻结的
estimand、方法定义或 gate 顺序。

### 3.1 已实现能力

- `agent/` 支持确定性和模型驱动的多文件生成、两阶段 `REQ2HIS -> HIS2PROJECT`、H0-H3 结果记录、L0-L4 工具编排、修复 hook、独立 oracle、mutation qualification，以及轨迹/训练视图导出。
- 所有当前 generation method 之前都有共同 Requirement Envelope/boundary；开发级 OASA 已有 sealed loader、Phase A/B、exactly-one replay、witness 和 cluster reducer，但没有 signed fixture population、冻结 interval 或 official campaign。
- `training/` 支持数据集转换、dry-run、手工 LoRA/SFT、adapter 合并和不导入 Agent 的 serving；这些模型命令不是 G4b-gated 正式 M6 入口。
- 已存在版本化的 System-HIS、project/terminal/evaluation、OASA、trajectory、candidate training-release、training-view、task catalog、dataset 和 evidence artifacts。Schema 注册不等于 release 认证或 official evaluator producer。

### 3.2 已验证证据

- 任务账本覆盖 71 个目标家族；其中 31 个已实现，并具有 L3 或更高层级证据。
- 目录指定的 14 个 Paper 1 核心家族均已实现、达到 L3，并在确定性/参考路径上通过 mutation qualification。
- 21 个家族通过 mutation qualification，9 个具有独立 Python 参考证据。
- FIR filter 和 matrix-vector MAC 两个家族具有经整理的 OpenXC7 布线后 L4 通过证据。
- Phase C 记录为 9/9 L3、9/9 独立 Python oracle 通过，以及 45/45 个可评分 mutation 被检出。
- Phase D 是有效的负向 pilot：24/24 个 live episode 完成，其中 12 个生成失败、12 个 H2 失败、0/24 通过 L0-L3、零次修复尝试，且没有 live L4 结果。

### 3.3 研究目标，而非现有结果

- 已签名的 evaluator-owned requirement-intake fixtures、冻结统计阈值和正式 ambiguity-audit campaign；
- 由 Runner 统一拥有的 M0-M5 end-to-end episode path，消费方法中立工程契约、immutable terminal seal 及分离的 public/hidden evaluator；
- 留出家族上的表示或修复有效性增益；
- Tier-B logit-masked 约束解码；
- 经过校准的 QoR 预测；
- 一般性的 OpenXC7 L4、任何 Vivado 通过、`.bit` 证据或 L5；
- 具有应用真实性的 RL、图像、雷达、SoC 或主机集成加速。

### 3.4 2026-08-24 快照中的阻塞性不一致

以下 P0 义务必须在产生研究结果的正式 campaign 之前关闭。可变实现事实由 `docs/current-status.md` 维护。G1/G2 已在 2026-08-24 working tree 本地关闭，但都不是模型 outcome：

- development OASA 已有 sealed loader、witness、one-answer replay 和 reducer；仍无 signed fixture population、冻结 interval/threshold 和 official audit execution；
- provider-neutral M0-M5 core 已包含 M2 Structured-Direct 与 M3 HIS-Free，但 legacy Runner 还不能把同一 frozen pack 贯穿 public evaluation、terminal selection/reseal 与 official hidden dispatch；
- development hidden boundary 可从独立 store 一次性消费 sealed terminal candidate 并返回 opaque ref，但不生成 official outcome，也未替换 legacy Runner 的 adaptive candidate-TB/oracle path；
- logical model call 已计数，但 provider token、transport/parser retry、tool/wall/EDA budget 和 canonical runtime trajectory reconstruction 尚未闭合为一个 matched episode budget；
- 历史 trajectory 可能缺少显式 call/patch/rerun evidence；G4b 仍需冻结 migration/exclusion decision；
- 四个候选主要留出家族中，只有 `matched_filter` 和 `sobel_threshold` 具备合格的独立 oracle 证据；
- candidate eligibility、v2 view、matched pool 和 unpromoted release 作为非 Paper-1 仓库基础设施保留；其不完整不再阻塞 Paper-1，任何 Paper-1 run 都不得调用它们。

## 4. 研究问题与证伪规则

### RQ0 — 独立且有边界的需求边界 conformance audit

在一个与 VPP benchmark 和全部开发视图分离的密封 case set 上，共同的生成前 requirement boundary 能否区分 `ready`、`needs_clarification` 与 `capability_gap`；能否把用户事实、平台默认、系统假设和 unresolved fact 保留为不同 provenance class；并阻止每个 non-ready case 越过工程生成边界？

审计由评测器管理，并在 M0-M5 工程生成之前停止。gold disposition、material interpretation witness、critical-fact ID、allowed-default ID、clarification answer object 和 capability rationale 均为私有信息。被审计系统只能看到原始 requirement、公开平台 context/default 和冻结的公开 capability-profile identifier。正确 disposition 不是工程、L-stage、VPP 或 repair 成功。

RQ0 是强制审计，但在统计和运行上与主要 RQ1/RQ2 estimand 完全分离。它的结果不得删除、替换、改道或重加权 VPP instance，也不得修改方法、prompt、Family Recipe、预算、信息权限或 terminal-selection rule。

如果 critical false-proceed rate 超过 G4b 阈值、未声明语义假设被伪装成用户事实或允许默认、未知请求被强制映射到最近家族、关键澄清事实未被指出，或 non-ready case 产生工程模型调用或候选写入，则 RQ0 不受支持。正结果只支持命名审计集上的有边界 requirement-boundary 行为，不证明任意 open-world requirement 理解或工程正确性。

### RQ1 — 端到端契约价值

在外部需求事实和总预算相同的条件下，生成式 System-HIS 流程能否比 Direct 取得更高的、方法中立的已验证工程成功率？在 System-HIS 路径内部，deterministic materialization/edit-surface 联合干预带来多少增量，representation bundle 又提供何种次级证据？

比较与解释：

- M3 对 M2 估计的是**两阶段表示组合**。它同时改变 plan schema、prompt、checker 和表示长度，因此不得描述为“仅由类型化产生”的纯因果效应。两条分支必须匹配 planner/generator 调用次数、全局预算和实际输入事实。
- M4 对 M3：对每个 semantic-instance/replicate block 复用完全相同的冻结 generated-HIS 工件，并联合改变 deterministic project materialization 与配套 editable-surface policy。没有额外正交对照时，不得把它写成 skeleton 文本、可编辑字节数或某条 lowerer rule 的纯效应。
- M4 对 M0 是端到端系统比较，不隔离单一机制。

只有两个主要 contrast 都通过各自的预声明规则，才能支持完整 RQ1；若仅一项通过，只能支持该项对应的局部论断。如果表观收益只是把失败从 H/L0 转移到隐藏 L2，或在核对有效信息和总成本后消失，则 RQ1 同样不受支持。

RQ1 是两项 hypothesis 构成的主要确认性 family。`M4−M3` 与 `M4−M0` 按第 7.5 节使用 Holm 控制；`M3−M2` 是强制报告的预注册 secondary estimation contrast，不能开启、救援或替代任一主要论断。

### RQ2 — 验证器隔离与修复

从冻结且匹配的初始状态出发，有边界的公开修复能否改善 terminal `VPP-L3@A`，消耗多少总成本，并且该改善能否经受一次性隐藏评测，而不是只优化公开评测器？

- M5 对 M1 是**端到端系统比较**，不是孤立的修复策略效应；两者的初始生成器、工件、诊断和可编辑范围均不同。
- M5 对 M4 衡量 HIS 流程内公开反馈修复所带来的增量成功率与成本，并作为主要确认性 online-repair bundle contrast。
- 修复机制 probe 从同一个冻结的失败 M4 工程出发，配对比较通用修复策略与 HIS-aware 修复策略。初始状态、模型、公开工具输出、可编辑范围和全局预算完全相同；仅声明为 HIS-aware 的诊断字段不同。
- 对每个修复条件报告 `P(hidden failure | public acceptance)`。不得对隐藏评测资格不同的比率直接做减法。

配对的 R_HIS−R_generic probe 是 RQ2 的第二个确认性 contrast。M1−M0 是次要 generic-repair 诊断；M5−M1 是必须报告、但只作描述性的端到端正确性—成本比较。

如果没有发生真实的 failure→diagnosis→patch→rerun 转换，公开收益在一次性隐藏评测下消失，或可信工件被修改，则 RQ2 不受支持。

### RQ3 — 从 Paper-1 撤回

v1.3 TRETS amendment 撤回原工具验证训练视图问题。Paper-1 不微调模型、不创建 training treatment、不选择 checkpoint，也不报告 learned improvement。既有 M6 和 training-view contracts 仅作为非 Paper-1 仓库基础设施保留，不获得 Paper-1 方法、结果或可复现性贡献。

### RQ4 — 次要且有边界的物理深度刻画

在原始固定分母上，有多少候选到达预声明的代表性 OpenXC7 L4 子集？在 L3 survivor 中又出现哪些额外损耗、时序或资源行为？RQ4 在最小论文中只作次要描述，不能替代无条件 VPP-L4，也不能推出 bitstream、板级、Vivado、跨器件或跨厂商可移植性。包括失败 episode 和不可用 cost axis 在内的总 episode cost 是贯穿 RQ1/RQ2 的结果，不由 RQ4 独占。

**可选 target-profile adaptation 扩展：** 只有核心 G4b package 已就绪且另有结果前冻结时，才可增加成对 profile 子集。每个 pair 必须具有稳定 `profile_pair_id`、baseline/variant `target_profile_id`、功能不变量、必须/允许/禁止变化、profile-specific L3/L4 终点和 evaluator-owned compliance oracle。除非扩展自身预先冻结了有功效依据的 contrast 与 multiplicity rule，否则只作描述性分析；未启用扩展不会阻塞最小 Paper-1 campaign 或投稿。

## 5. 方法与基线阶梯

### 5.1 参考条件

- **B_ref — 确定性参考：** 用于可信工程和 oracle sanity check。它证明基准可执行，不证明模型能够求解。
- **B_template — 确定性 skeleton/behavior 参考：** 工程和 QoR 锚点，不计入学习模型贡献。
- **能力上界：** 在声明的直接/修复条件下运行大型闭源模型。单独报告，绝不用于估计微调增益。

### 5.2 匹配模型条件

M0-M5 使用相同的小型/开放基础模型版本、tokenizer、quantization、context limit、decoding family 和 episode population。当前代码尚未实现完整阶梯；G3 是强制运行时 gate。

- **M0 Direct：** 将需求与共同的公开工程/接口契约直接交给一个完整工程生成器。不生成 System-HIS，在评分前不接收公开评测反馈，也不要求通过 H-stage。
- **M1 Direct-Repair：** M0 加上全局修复预算内的公开评测器诊断/修复。它是**受 HORIZON 启发的 Direct-Repair 对照**。只有当 G3 实现 project pack、不可变且由评测器拥有的验收通道、accepted-checkpoint 历史、持久 session/state 策略和可审计仓库轨迹后，才可称为 HORIZON-like；没有原始发布协议时，绝不能称为 HORIZON 的精确复现。
- **M2 Structured-Direct：** 模型阶段 1 从同一需求事实生成无类型结构化 plan；阶段 2 自由生成完整工程。该 plan 不含 System-HIS 类型、跨字段 checker 或确定性 skeleton。
- **M3 HIS-Free：** 模型阶段 1 生成 System-HIS；阶段 2 通过真正的 no-skeleton generator 自由生成完整工程。进行 materialization comparison 时，M3 与 M4 使用同一个冻结 generated-HIS 工件。
- **M4 HIS-Skeleton：** 可信代码把 generated System-HIS 降低为契约 skeleton，模型只填充声明的 behavior region。它没有外层 EDA repair；任何 planner/parser/schema retry 都是显式计入预算的模型调用，不能隐藏在“第一次尝试”中。
- **M5 HIS-Online：** M4 加上与 M1 完全相同的全局 repair/tool 预算内公开评测器诊断和外层修复。
- **R_generic / R_HIS 修复 probe：** 将两种修复策略应用于同一个冻结失败 M4 工程，用于 RQ2 机制分析。它们是配对诊断条件，不是新的 headline generator。

正式匹配执行单位是由 `(semantic_instance_id, replicate_id)` 和稳定 `paired_block_id` 标识的版本化 **replicate block**。同一 block 中，M0/M1 共用不可变的初始 Direct 工程，M3/M4 共用完全相同的 generated-HIS，M4/M5 共用不可变的初始 skeleton-derived 工程；完整 M0-M5 block 还共用公开 fact projection、模型/推理配置、tool/evaluator commitment、hidden-case seed 和全局预算策略。repair probe 使用独立 `repair_probe_block_id`，两种策略消费同一个失败 M4 checkpoint。`replicate_id` 是预先规划的重复测量身份，不从 provider 返回值推导，也不意味着方法共享同一 realized randomness。任一所需 identity 或 content hash 不同，该比较即为 unpaired，不能进入确认性推断。

G4b 必须冻结且只能冻结一种 decoding-control mode：

- `documented_seed_control`：每个 replicate 映射到一个冻结 requested seed，并由 hash-bound、独立审核的 provider capability profile 证明该机制在文档边界内可用于 replay。这本身不证明不同方法 prompt 或 token trajectory 之间存在 common random numbers；更强的跨请求共同随机性论断还需要单独文档化的 coupling mechanism。
- `stochastic_blocked`：冻结 replicate ID、provider/model/gateway/inference 配置、请求次数和平衡执行计划；provider 接受 requested seed 时只把它作为 request provenance。方法效应解释为冻结 stochastic decoding distribution 上的期望效应；不得声称 same randomness、seed effect、deterministic replay 或 bitwise reproducibility。

method order 在 replicate block 间用独立于 provider decoding seed 的本地 `execution_schedule_seed` 随机化并保持平衡。共享工件是实验控制，不代表免费成本：ledger 把共享事件作为 block-level 实际 campaign 消耗只记录一次；在每个方法的 standalone end-to-end cost 中完整计入该方法所需的共享前置成本；并另报 shared checkpoint 之后的 incremental contrast cost。不得只向先执行的方法收费。G4b 必须在结果前冻结这三种成本视图及 reducer。

| 推断角色 | 冻结比较 |
| --- | --- |
| RQ1 primary Holm family | M4−M3；M4−M0 |
| RQ2 Holm 确认性 family | M5−M4；R_HIS−R_generic |
| 必须报告的次要/描述性 | M3−M2；M1−M0；M5−M1；per-family effect；stage transition；正确性—成本前沿 |
| 仅参考 | B_ref；B_template；frontier ceiling |

M6U、M6F、M6T、M6TR 与 `M6F[E_traj]` 在 v1.3 下均不是 Paper-1 method condition；相关代码和 contracts 位于本协议范围之外。

**A_req — requirement-boundary audit** 不是 M6，也不是工程生成 treatment。它对每个密封审计 case 只执行一次冻结的共同 intake boundary，并在任何 M0-M5 model stage、candidate workspace 写入、repair 或 project evaluator 之前拦截。它不获得 VPP 或工程方法 credit。

共同公开工程契约必须方法中立，要求 L0-L3 所需的完整 RTL source set、top/interface declaration、manifest、适用 constraint、build/tool metadata 和 trusted-edit boundary。System-HIS、H0-H3 record、generated requirement trace、candidate testbench 和 predicted QoR 都是条件适用或 advisory artifact，不得成为 M0/M1/M2 的普遍准入条件或隐藏评分权威。

方法分配前，每个正式 VPP instance 都必须由独立评测者裁决为 `ready`，并转换成一个冻结的公开 requirement-fact projection。M0-M5 获得内容等价的 fact ID、value 与 provenance；序列化格式可以不同，但外部需求事实不能不同。正式 VPP run 只验证并复用该冻结 ready projection，不进行自适应用户澄清或改写需求。自动 intake component 只在 A_req 中接受效果审计。

外部 skill、retrieval 或 persistent memory 是单独的二元因素。它们不属于最小方法阶梯，且不得只为某一个条件静默开启。

### 5.3 模型可以看到和不得看到什么

每次运行都由一个版本化**回合包（episode pack）**创建；其中包含模型可见的公开投影和仅评测器可见的私有投影：

```text
episode_id
适用时的 paired_block_id 与 repair_probe_block_id
analysis_population: official_vpp | ambiguity_audit
requirement_id、requirement_revision_id、semantic_instance_id、paraphrase_group_id 和 requirement text
requirement-envelope version/hash，以及公开 fact ID、value 和 provenance
platform-default profile ID/hash 与 backend-capability profile ID/hash
family_id、topology_id、generalization_class 和 semantic parameters
platform_profile_id
method_condition 和 model provenance
public artifact contract
allowed edit surface
repair-visible evaluator policy
private hidden evaluator identifier/hash 和 hidden-case seed
terminal-candidate selection 和 infrastructure-retry policy
model-call/token/retry/repair/tool/wall/EDA budgets
requested decoding seed、provider seed-control status/fingerprint 和平衡后的 method execution order
prompt hash 和 effective-information hash
contract/catalog/tool versions 和 hashes
适用时的 base_requirement_cluster_id 与 ambiguity_case_id
仅 A_req 使用的私有 gold disposition commitment、critical-fact ID、allowed-default ID、clarification-answer commitment 和 capability rationale
```

每个 episode-pack 字段都必须具有显式 visibility class。`family_id`、topology/generalization label、私有 disposition commitment、预期 clarification 内容、Recipe decision 与 hidden evaluator identifier 默认只对评测器可见；出现在 pack 清单中不代表模型可见。用户原始文本中明确出现的 family identifier 仍属于用户事实，评测器追加的 family metadata 则不是。

候选工作区不得暴露：

- `agent/src/` 中的确定性生成器或任务模板；
- 可信 testbench、独立参考模型、mutation source、hidden vector/property 或评分脚本；
- 留出参考工程、System-HIS 答案、轨迹、数据集或训练导出；
- API key、私有 endpoint、vendor artifact 和无关仓库状态。

所有方法均由评测器拥有的 harness 评分。候选方生成的 testbench 是不可信工件，绝不能作为隐藏评测权威。公开 smoke check 及其声明的诊断可以对修复器可见；隐藏的确定性、固定随机 seed 和 stress case 必须保持私有。

对于每个 `(semantic_instance_id, replicate_id, method_condition)`，公开停止规则只选择一个 terminal candidate。在 `@1` 下，每个声明的模型阶段恰好调用一次，内部 retry 禁用；所有调用/token 均纳入成本核算。在 `@A` 下，冻结最早满足公开验收的候选；如果没有，则在预算耗尽时冻结最后一个完整候选。若未生成完整工程，结果为设计失败。

terminal candidate 一经设为不可变，隐藏评测器只执行一次。配对方法使用相同的冻结 hidden-case seed。隐藏结果不得触发修复、候选替换、prompt/tool/budget 变更或第二次评测。预声明的 infrastructure retry 只能重放同一个不可变候选。任何隐藏 path、case ID、hash、stdout/stderr、status、score 或 summary 都不得进入模型/修复消息；必须由 spy test 证明这一边界。

隐藏闭合使用两个正交机器字段：

```text
hidden_execution_status = completed | not_run | infrastructure_error | integrity_error
hidden_semantic_status = pass | fail | null
```

`completed` 必须恰好提交一次 `pass` 或 `fail`；semantic fail 是 `VPP-L3=0` 的 design outcome，不能触发修复、替换或再次评分。`not_run(reason)` 表示没有 immutable terminal 等上游条件使隐藏评分不适用；VPP 由上游设计结果决定，不能把 `not_run` 自身称为隐藏失败。commit 前 infrastructure error 只能按冻结规则重放同一 terminal hash；耗尽后是 unscorable，不是模型失败。integrity error 触发冻结的 campaign abort/invalidation rule。semantic result 一旦 commit，任何 retry 都被禁止。

规范/oracle System-HIS 只能用于明确标注的上界，或内容等价表示诊断，绝不能用于 headline 端到端比较。M2/M3 有效信息审计必须列出所有可见事实；仅匹配 token 总量不能证明信息等价。

Family Recipe 是版本化 generation-information privilege，不是缺失 requirement fact 的替代品。只有共同 boundary 已返回 `ready` 后才允许选择 Recipe；完整 decision 与 policy hash 仍只对评测器可见。任何主要留出 headline condition 都不接收 family-specific Recipe 正文；catalog-assisted analysis 若存在，必须预声明为独立的次要 content-equivalent information treatment，并向所有被比较方法提供等价信息。Recipe text、route decision 或 family alias 不得解决 A_req gold ambiguity，也不得进入私有 label。

ambiguity-audit case 不暴露 gold status、遗漏 fact、accepted answer、私有 capability rationale 或 reference artifact。独立 visibility spy test 必须证明这些字段不会到达 model、Recipe、HIS、project、repair 或 training context。

`semantic_instance_id`、`replicate_id` 与 `paired_block_id` 必须是 planned sample 和 runtime 的一等字段；不得用 `family_id` 代替实例或 replicate ID。`requested_decoding_seed` 是独立 provenance 字段，不得静默硬编码，也不得用作 replicate identity。provider adapter 必须记录 requested seed、provider system fingerprint（如有）和 seed-control capability。`documented_seed_control` 模式要求冻结、可复现且经独立审核的 decoding 机制；`stochastic_blocked` 模式可以保留 unavailable/undocumented seed control，但不得把它伪装成名义 capability 或据此声称确定性。

### 5.4 全局预算与重试核算

campaign 分别冻结模型调用、输入/输出/缓存 token、planner/parser/schema retry、外层修复尝试、公开工具调用、wall time 和 EDA time 的上限。每次 retry 都是一等 attempt event，并消耗相应的全局预算。provider transport retry 属于基础设施事件，绝不能静默增加某种方法的模型预算。

`@1` 表示每个声明的流水线阶段调用一次，而不是“外层 attempt 0”。比较同时报告共同总预算和分阶段分配。方法执行顺序在 replicate block 内由冻结的本地 `execution_schedule_seed` 随机化并保持平衡，而 model gateway、cache policy、代码和工具版本均冻结。schedule seed 不进入模型请求，也不得复用为 `requested_decoding_seed`。

A_req 使用单独冻结的 preflight call/token/wall-time 预算，不消耗 M0-M5 工程生成预算。正式 ready projection 的构造成本作为共同 benchmark overhead 报告，不得在方法间差异化计费。M0-M5 必须分别报告 inference/episode、repair、公开工具、hidden evaluator、wall-time 与 EDA cost；Paper-1 不包含训练成本或 amortized training claim。

每个 repair-capable condition 只有一个冻结的模型侧 repair/correction 总调用上限。M5 的 System-HIS correction 与外层工程 repair 虽分属不同 stage，但共同消耗该上限，不能各自获得一个免费调用。provider transport retry 只有在满足冻结基础设施规则、且完全重放同一请求时才不消耗该上限。

## 6. 基准总体与数据划分冻结

### 6.1 任务权威

分母是规范 contracts catalog 中包含 14 个家族的 `recommended_sets.paper1_core` 列表。目录意图必须与证据账本 join；只有通过 benchmark-readiness gate 的家族才能进入运行。

以下是**候选 G4a 划分**，不是已执行或最终冻结的数据划分。只有在 G4b 阶段、机器可读 split manifest 已存在且每个主要留出家族都具有由评测器拥有的合格隐藏 oracle 证据后，它才成为最终划分。G4a 必须冻结客观排除标准和有序 reserve list。替换只能发生在 G4b 之前，且必须早于任何官方 requirement 的结果可见之时。

**开发家族（9 个）：**

- `sync_fifo`
- `single_dual_port_ram`
- `valid_ready_stream_accumulator`
- `mac_array`
- `matrix_vector_mac`
- `fir_filter`
- `peak_detector`
- `pattern_matcher`
- `p_stream_trigger_filter`

**主要按家族留出的测试家族（4 个）：**

- `uart_fifo_loopback` — 协议组合
- `stream_fork_join` — stream/control 组合
- `matched_filter` — 数值信号处理
- `sobel_threshold` — 图像流水线

**旗舰参数/拓扑留出家族（1 个）：**

- `qtable_update_core`；单独报告，因为当前目录不允许对该家族主张 S4 family-held-out。

规划目标是每个留出家族 30 个独立**语义实例**。G4b 在不使用任何正式结果的情况下冻结最终样本量：一个排除于正式实验之外的 pilot 提供 paired-discordance、cluster-dependence、attrition 和 runtime 范围，用于围绕最小关注效应进行预声明的功效/精度模拟。如果规划目标经该分析后保持不变，基准共包含 120 个 semantic-instance cluster。三个 replicate block 是每个 cluster 内的重复测量，不是 360 个独立样本。

保持相同行为的同义改写、位宽变体和重复隐藏随机 seed 共用一个 `semantic_instance_id` 或 `paraphrase_group_id`，绝不虚增 `n`。pilot requirement 和任何用于调试的 prompt 均排除在正式测试之外。由于只有四个有意选择的留出家族，推断只以这四个命名家族为条件；若要对“新的 FPGA 家族”总体作出论断，必须在 G4b 前增加更多留出家族。

### 6.2 数据划分与泄漏规则

- 测试家族 ID、alias、requirement、canonical HI、reference project、trajectory 以及 memory/skill entry 均从所有训练视图排除。
- 开发/模型选择仅使用训练家族内部按 requirement 留出的切片。正式测试结果保持密封，直到模型、停止规则和分析代码全部冻结。
- 在不同 fold 之间删除完全重复 hash，以及归一化 RTL/AST 或 requirement 近重复项。相似度方法和阈值须在 G4b 前写入 split manifest 并冻结。
- 跨 fold 审计 module-level hash、component-graph overlap、interface signature 和 semantic-mechanism cluster。manifest 将每个测试实例标为 seen-primitives/unseen-composition、unseen-family/seen-mechanism 或 unseen-mechanism；这些标签界定泛化论断的边界。
- 所有源 episode 保留 `family_id`、topology/alias、requirement hash、`semantic_instance_id`、`paraphrase_group_id`、model/provider provenance 和 source release。
- T5-T12 是历史拓扑 ID，不是难度等级。官方元数据分别保留 `topology_id`、`family_id`、`difficulty_tier` 和 `sample_id`。
- G4b 签署后，只要已经观察到任何正式模型结果或隐藏结果，就不得删除或替换任何家族、语义实例或方法。

### 6.3 Oracle 就绪 gate

每个留出家族必须具备：

- 由评测器拥有、独立于候选文件的黑盒行为 oracle；
- 修复期间不可见的 hidden/random/stress case；
- 针对声明缺陷类别的 mutation qualification；
- 不可变 edit-surface enforcement；
- 包含 hash 和工具版本的 benchmark-readiness 工件。

截至本证据截止点，四个候选主要留出家族中只有 `matched_filter` 和 `sobel_threshold` 满足合格独立 oracle 的证据要求。`uart_fifo_loopback` 和 `stream_fork_join` 必须在 G4b 前补齐缺口。无论目录是否标记 `ready`，仅有嵌入式或候选可见 testbench 都不足以获得最终隐藏评分。

### 6.4 独立的 requirement-ambiguity audit 总体

ambiguity audit 与 14-family VPP join、四个主要留出家族、旗舰总体、全部开发 view 和 G5 generation pilot 完全分离。独立统计单元是 `base_requirement_cluster_id`；variant、paraphrase、answer branch 与 intake decoding seed 均为重复观测，不增加 `n`。

候选规划目标是 100 个独立撰写的 base cluster。每个 cluster 含四个密封且具有 counterfactual 关系的公开 variant：

1. fully specified `ready` control；
2. 只省略一项经评测器批准的公开默认值的 `ready` control；
3. 一项需要 `needs_clarification` 的关键遗漏或冲突；
4. 一项在冻结 backend profile 下明确为 `capability_gap` 的连贯显式需求。

perturbation strata 至少覆盖 width/depth/storage、clock/reset/CDC、protocol/handshake/backpressure、同时事件 priority 与 error behavior、numeric representation，以及 latency/throughput/acceptance obligation。必须加入“family 名未知但语义完整且受支持”的 `ready` 反例，防止 family lookup coercion。自然撰写 case 是主要刺激；机械删词与 fault injection 只是辅助 conformance suite。

每个私有 case 由两名具备硬件能力的标注者独立冻结 fact graph、materially distinct interpretation witness、expected disposition/reason code、critical-fact ID、permitted-default ID、capability ID/profile hash、acceptable clarification fact ID 和 one-turn answer object；第三名 adjudicator 必须在打开任何被审计输出前解决分歧。`needs_clarification` 至少需要两个会改变可观察行为、接口、约束或支持状态的实质解释，或一个显式冲突。`capability_gap` 要求需求已经连贯解析，并对应命名 profile 中精确的不支持 capability。如果一种合理解释受支持而另一种不受支持，gold status 必须是 `needs_clarification`，不能猜测后报 gap。

审计分两个固定 phase。Phase A 输出结构化 disposition、reason、critical-fact、capability、default 和 assumption ID 后立即停止。Phase B 仅对合格 clarification case 回放一次预写 answer object，并要求得到预提交的 `ready` 或 `capability_gap`。不允许自适应人工回答、需求改写、第二轮追问、工程生成、repair 或 hidden project oracle。`not_run` 只保留给 evaluator/runner infrastructure，既不是语义 gold label，也不是系统可选择的拒答标签。

最终 audit case、label、witness、answer object、alias 和 perturbation template 均不得进入 training、prompt debugging、Family Recipe、retrieval、skill、memory 或正式 VPP input。pilot audit case 永不进入最终 audit；audit outcome 不得在 G4b 后删除、替换或筛选正式 VPP instance。

## 7. 结果定义

### 7.1 Headline 指标

**通过 L3 的已验证工程通过（Verified Project Pass through L3，`VPP-L3`）**是方法中立的二元工程结果。候选只有同时满足下列条件才计为通过：

1. 符合共同的公开工程/接口 manifest 与不可变 edit surface；
2. 在方法中立的工程契约下通过 L0 工程一致性；
3. 通过 L1 lint 与公开 L2 simulation；
4. 通过由评测器拥有的一次性隐藏语义 oracle；
5. 在已冻结且名称准确的 Yosys flow 下完成 L3 synthesis；
6. 未发生可信工件、edit surface、provenance 或预算违规。

此处“完整工程”是 L0-L3 契约所需的冻结多文件 RTL/build package，不代表 routed hardware、bitstream、board execution 或未声明平台约束已经满足；这些论断必须有单独命名的 L4/L5 证据。

H0/H1/H2/H3 仅是生成 System-HIS 的方法所具有的机制结果。对 M0/M1/M2，它们是 `not_applicable` 而非 failure；在跨方法 VPP 定义中，绝不能成为某条件独有的优势。若 HIS-stage 设计失败导致工程未生成，该方法仍通过普通生成路径得到 VPP=0。

为公开 L2、隐藏 L2、评测器身份、edit/provenance violation、infrastructure status 和 `vpp_l3` 记录显式机器字段。绝不能从遗留 `pass_level=L3` 标签推导 VPP-L3。在每阶段一次调用规则下报告 `VPP-L3@1`，在公开修复预算下报告 `VPP-L3@A`。REQ2FILE row 绝不获得工程级通过计分。

### 7.2 必须报告的次要指标

- 分别报告仅适用于相应条件的 H0/H1/H2/H3，以及共同的 L0/L1/公开 L2/隐藏 L2/L3 结果；
- 首个失败阶段和阶段转换矩阵；
- 公开验收和 `P(hidden failure | public acceptance)`；
- 实际修复尝试、成功修复、diagnosis/patch 是否存在，以及 oracle-edit violation；
- 对**每个**正式 episode（包括失败 episode）报告可获得的 total/input/output/cached token、模型调用、工具调用、attempt、wall-clock time 和 EDA runtime；
- 达到首次成功所需资源，在冻结预算处截尾；不成功 episode 明确视为 right-censored，且绝不从成本报告中删除；
- 将基础设施失败、设计失败、timeout 和 `not_run` 分别作为不同结果；
- 各家族结果，以及家族等权 macro average。

公开验收后的已观测隐藏失败诊断定义为：

```text
HFPA_observed =
  N(public_accept and hidden_execution_status=completed and hidden_semantic_status=fail)
  / N(public_accept and hidden_execution_status=completed)
```

必须同时报告 `hidden_completion_rate_given_public_accept`、hidden infrastructure-unscorable 数量以及 best/worst-case bounds。hidden eligibility 或 completion denominator 不同的方法不得直接相减。

对 L4 同时报告原始固定分母上的无条件 `VPP-L4`，以及作为 survivor attrition 的 `P(L4 pass | VPP-L3 pass)`。开发家族、留出家族和旗舰家族必须分开。禁止未注册的 PPA 显著性检验。

如果启用可选 target-profile 扩展，分别报告 baseline/variant outcome 与二元 `TPA-L4`。只有两个成员均保持相同功能不变量、满足各自工程/约束契约、实现全部必须变化且无禁止变化，并通过所需 L3/OpenXC7 L4 终点，才计 `TPA-L4=1`。correctness scorability 与 cost-axis 完整性相互独立：token、wall 或 EDA cost 缺失只影响成本/missingness 分析，不能迫使一个功能上可评分的 pair 变成 `not_run`。必须报告完整 pair 分母、失败阶段、compliance violation、时序/资源变化、cost availability 与 unavailable reason；baseline-only 或 survivor-only 分析无 adaptation credit。

mutation score 用于判定 oracle 质量，不是模型性能指标。通用 L3 cell statistics 不得称为 FPGA LUT QoR。只有在成功的、命名明确的 stage 和 tool flow 上，measured QoR 才可接受。

### 7.3 仅用于 ambiguity audit 的结果

对 A_req 定义 `proceed=1`：在 gold non-ready case 上，final intake decision 授权工程生成，或者实际发生 project planner、REQ2HIS、project generator、repair model、candidate-workspace 写入或 project-evaluator 调用。评测器会在执行下游调用前拦截不安全授权，但仍把它计为 false proceed；任何逃逸的下游 event 还要另记 generation-boundary violation。先生成再返回 `needs_clarification` 同时违反两条规则。

必须报告：完整 disposition confusion matrix（`not_run` infrastructure 单列）；`FP_amb = P(proceed | gold needs_clarification)`；`FP_gap = P(proceed | gold capability_gap)`；主要安全摘要 `max(FP_amb, FP_gap)` 与 generation-boundary violation count；两个 gold-ready variant 上的 false blocking；critical clarification fact、capability、permitted default 与 explicit assumption ID 的 precision/recall；重复询问已知事实的比例；unknown-family coercion count；一次 replay 到预提交状态的 closure；以及 intake call/token/wall time 和 infrastructure status。

候选规划验收目标为：两个各 100-case 的 non-ready stratum 中均观察到零次 false proceed，且各自 one-sided 95% upper bound 不高于 3%；零 generation-boundary violation；零 undeclared semantic assumption；critical-fact recall 100%；one-replay closure 至少 95%；每个 ready stratum 的 false blocking 不高于 5%。G4b 仅使用 excluded pilot 冻结最终样本量与资源预算；3% false-proceed、5% false-block、95% replay、100% critical-fact 和 exact interval rule 是 G5 前冻结的科学标准，pilot 不得放宽。通过只支持命名集合上的有限 conformance 论断，不支持零风险或工程正确性论断。

100 个独立 cluster、每 cluster 四个 variant 共 400 case，每个 non-ready stratum 有 100 个观测。使用 independent base-cluster outcome 上的 one-sided exact Clopper-Pearson bound；零 false proceed 时 upper bound 为 `1-0.05^(1/100)=2.951%`，出现一次错误即不通过 3% gate。`FP_amb` 与 `FP_gap` 必须同时通过，是 intersection-union safety rule。non-ready `not_run` 在 primary worst-case gate 中计为 unsafe；ready `not_run` 计为 false block；随机 intake 的任一 unsafe seed 使整个 cluster 失败。因此 G4b 只能根据 excluded pilot 冻结最终 cluster 数，不能改变 threshold 或预设 100 必然足够。若有 `N_A` cluster、`S_A` intake seed，Phase A 为 `4*N_A*S_A` 次调用，one-answer replay 至多再加 `N_A*S_A`，总 ceiling 为 `5*N_A*S_A`（100 cluster、1 seed 为 500；3 seed 为 1,500）。

### 7.4 失败、缺失和重试规则

- 模型生成/解析失败、候选无效输出、预算耗尽，以及在冻结资源限制内由候选/工具引起的 timeout，均属于设计结果：`VPP-L3=0`，且保留在完整分母中。下游隐藏阶段可以是 `not_run`；该标签本身不重新分类为 failure。
- provider transport outage，或候选不可变之后发生的 evaluator/runner/tool infrastructure failure，使用固定 retry 次数，并且只重放该候选。
- 如果固定 retry 后仍无法评分，不得静默删除配对中的任何一方。将 semantic-instance/replicate block 标记为 unscorable 并报告，同时提供 complete-pair、all-unscorable-as-failure 敏感性分析，以及 worst/best bound。
- 只有影响所有配对方法的共同 outage 才可推迟该 block。看到任何隐藏结果后都不得替换 requirement。
- G4b 冻结 unresolved-infrastructure rate 和方法间不平衡阈值。超过阈值会使 campaign 无效并触发有记录的 rerun；这绝不授权事后排除。

每个 episode 的 hidden slot 必须以两个状态轴生成恰好一个 evaluator-owned sanitized outcome artifact，并记录 failed stage、冻结 reason class、retry eligibility/exhaustion、sanitized exception class，以及适用时的 semantic-commit count。吞掉异常、只返回无法被 reducer 闭合的 opaque reference、遗漏预期 outcome 或重复 commit 都是 integrity failure，不是 candidate success 或 design failure。

对于 A_req，即使系统把 gold non-ready case 预测为 `ready`，评测器也要在 disposition 评分后拦截；记录 false proceed，但不实际执行 generation。若任何下游 event 逃逸，再另记 generation-boundary violation。audit infrastructure failure 记为 `not_run`，保留在 audit denominator 与 missingness table 中，不能改写为正确 disposition。超过冻结 audit-infrastructure 阈值会使该次 audit 无效，而不是允许补样。

### 7.5 统计契约

独立基准单位是 `semantic_instance_id`。同义改写、hidden case seed 和 planned `replicate_id` 是重复测量。对于配对比较 X−Y，先在每个 replicate block 内计算二元差值，再在 semantic instance 内平均 replicate difference，随后在家族内对实例求平均。headline estimate 是四个命名家族均值的等权平均。在 `stochastic_blocked` 下，这是冻结 provider/configuration distribution 上的 randomized-block estimate，不意味着 X 与 Y 消费同一 realized random stream。

区间采用嵌套分层 bootstrap：在每个家族内重采样 semantic instance，同时保留所选 block 的所有 method pair、同义改写、hidden case 与 replicate。区间以四个冻结家族和固定 M0-M5 协议为条件，不是覆盖全部 FPGA 任务家族的区间。

确认性 hypothesis 具有方向性，使用 one-sided familywise alpha 0.05。RQ1 与 RQ2 是两个独立 Holm family，不在二者之间回收 alpha，因此这两个 family 各自控制 0.05 并不等于整篇论文的全局 familywise error rate 为 0.05。所有表同时报告双侧 95% CI 和两个方向的 effect。正向论断要求：Holm 拒绝预声明 threshold null、双侧 95% CI 下端严格超过命名 minimum effect，并且命名的 integrity、missingness 与 budget gate 全部通过。multiplicity 只控制确认性推断，不控制 data collection；每个已签署且合格的 M0-M5 condition 都必须执行并报告。

对 RQ1，令 `Y1_ifqm` 为 family `f`、semantic instance `i`、planned replicate `q`、method `m` 的 terminal `VPP-L3@1`。对主要 contrast `c in {43,40}`，先定义 `D_ifc = mean_q(Y1_ifq,a_c-Y1_ifq,b_c)`，再定义 `Delta_fc = mean_i(D_ifc)` 与 `Delta_c=(1/4)sum_f Delta_fc`，其中 `(a_43,b_43)=(M4,M3)`、`(a_40,b_40)=(M4,M0)`。方向性 null 为 `H0_43: Delta_43 <= delta_min_materialization` 和 `H0_40: Delta_40 <= delta_min_system`。两个 cluster-respecting one-sided p-value 构成 RQ1 Holm family：报告 raw 与 adjusted p-value；若 `p_(1)<=p_(2)`，只有 `p_(1)<=0.025` 才拒绝第一项，随后只有 `p_(2)<=0.05` 才拒绝第二项。

`M4−M3` 估计 deterministic materialization/edit-surface bundle；`M4−M0` 估计未训练的端到端 system value，不隔离单一组件。对 `c in {43,40}`，令 `delta_43=delta_min_materialization`、`delta_40=delta_min_system`。当且仅当 Holm 拒绝 `H0_c` 且 `Delta_c` 的双侧 95% CI 下端严格超过 `delta_c` 时，令 `S_c=1`。当且仅当全部适用于 RQ1 的命名 integrity、leakage、information、budget、hidden-completion 与 infrastructure-missingness gate 均通过时，令 `G_RQ1=1`；当且仅当 `S_c=1` 且 `G_RQ1=1` 时，定义 `C_c=1`。每个 `C_c=1` 只能开启其对应的局部论断；完整 RQ1 要求 `C_43=C_40=1`。

`M3−M2` 是强制报告的预注册 secondary representation-bundle estimand：报告家族等权 macro、per-family estimate 和双侧 95% CI，默认不报告确认性 p-value；它不能救援失败的主要比较，也不能解释为 typing-alone effect。

确认性 threshold test 以完整 `semantic_instance_id` 为重采样单位，整体保留其 planned replicate 与全部方法 outcome，并固定 family membership 与 equal-family weight。G4a 冻结 studentized statistic、boundary-null centering、family 内 cluster-resampling rule、interval form、resample 次数、analysis seed、tie/extreme-case rule 与 code hash；G4b 原样签署。只有独立审查证明 whole-cluster label exchangeability 时，才可把 cluster-swap test 称为 finite-sample exact；该检验只对应其声明的 sharp null，不能代替非零 minimum-effect threshold test。禁止在 replicate、requested seed、paraphrase 或 hidden case 层独立 sign flip。

per-family effect 与 leave-one-family-out 是强制描述性诊断，不开启、关闭或救援 macro claim。G4a 在 G5 前冻结 `{delta_min_materialization, delta_min_system}`、各自科学依据，以及可选的 M3−M2 secondary interpretation threshold。只有正 point estimate 不充分；任何 family-level 或 confirmatory secondary claim 都需要新的结果前 hierarchical multiplicity 与 power contract。

对每个已签署 family `f`、semantic instance `i`、replicate `q`，令 `YA_ifqm` 为方法 `m` 的 terminal `VPP-L3@A`。定义 `D_if,54 = mean_q(YA_ifq,M5-YA_ifq,M4)`、`Delta_f,54 = mean_i(D_if,54)`、`Delta_54 = (1/4) sum_f Delta_f,54`。该 intention-to-treat estimand 包含所有 signed cluster，无论 M5 是否实际 repair。M5 的唯一 repair/correction allowance 可用于 System-HIS correction 或 outer project repair，因此 M5−M4 是 online-repair bundle effect，不是任一 stage 的纯效应。

repair-policy probe 的冻结 selector 在任何 repair branch 或 hidden outcome 打开前，每个 semantic instance 最多选一个 eligible failing M4 checkpoint。eligibility 要求 immutable candidate、命名 public failure stage、有效 repair-visible diagnosis、剩余预算，且无 infrastructure/integrity/trusted-edit violation。selector 冻结 family/failure-stage strata、tie-break seed、per-family cap `k_f` 和最小可分析数 `k_min,f`；超 cap 时按冻结 seed 采样，结果后不得 top-up/替换。令 `Z_ifr` 为 policy `r∈{R_HIS,R_generic}` 后的 terminal hidden VPP；no-patch、failed-patch、budget-exhausted branch 在选定分母中保留为零。`Delta_R` 是 selected independent cluster 上配对 `Z_HIS-Z_generic` 的家族等权 macro。任一 `k_min,f` 未满足时，该 probe 为 non-rejecting/descriptive，不能静默删除。

RQ2 null 为 `H0_54: Delta_54 <= delta_min_54` 与 `H0_R: Delta_R <= delta_min_repair_policy`。两个 cluster-respecting one-sided p-value 用 Holm 控制 familywise alpha 0.05；同时报告双侧 95% CI 和全部 per-family effect。M5−M1 是必须报告的描述性端到端系统比较/正确性—成本前沿，不属于该机制 family。

最小 RQ4 分析均为描述性。如果启用可选 adaptation 扩展，其独立单位才是 `profile_pair_id`。按预声明 strata 在完整 pair 内重采样，并整体保留两个成员和全部重复 seed。任何确认性 adaptation contrast 都需要独立的结果前 freeze、minimum effect、样本量依据和 multiplicity rule；结果打开后不得升级。

RQ0 是独立 safety/conformance audit，不进入 VPP multiplicity family。resampling unit 是 `base_requirement_cluster_id`；四个 variant、paraphrase、answer branch 与 intake seed 必须整体保留。报告 `FP_amb`/`FP_gap` 原始 stratum count 与 one-sided bound，并对次要 audit metric 给出 cluster-resampled 95% interval。若 intake 使用随机 decoding，任何 seed 在 non-ready case 上 proceed 都使该 base cluster 在主要安全指标中失败；seed average 只作诊断。

M5 对 M1 的端到端比较以正确性—成本前沿报告。效率论断还要求先通过冻结的正确性非劣 margin 和 primary cost axis，然后才能检验成本优势。总 episode cost 包含失败；达到成功的时间在预算处截尾，并显示不成功数量。

对每个确认性 contrast `c`，`delta_c` 是足以支持科学论断的最小效应，不是 power 所假设的效应。G4a 在 G5 前另行冻结 `Delta*_c > delta_c` 和至少 0.80 的 target power。excluded pilot 只能估计 paired discordance、cluster replicate dependence、repair eligibility、attrition、missingness 和 runtime，不能用已观测 treatment effect 设置 `delta_c` 或 `Delta*_c`。若四家族每家 `n` 相等、replicate-averaged paired difference 的 pilot cluster variance 为 `sigma^2_fc`，则 `SE(Delta_c) ~= sqrt(sum_f sigma^2_fc/(16n))`，planning approximation 为 `n_c >= (z_.975+z_(1-beta))^2 sum_f sigma^2_fc / [16(Delta*_c-delta_c)^2]`。最终 `n` 由预声明 joint simulation 确定；模拟必须覆盖 RQ1/RQ2 两个 Holm family、两项 RQ1 共享 M4 的 covariance、完整 Holm+CI 判定、attrition/missingness、repair eligibility，以及冻结的 gate-valid envelope 内所选 decoding-control mode。不得为导致论断失效的 gate failure 虚构发生概率，也不得在 statistical power 中把它当作普通负 outcome。RQ1 planning 以 `G_RQ1=1` 为条件；实际 `G_RQ1=0` 会使 RQ1 claim activation 无效。若保留完整 RQ1 论断，joint statistical power 目标是 `P(S_43=1 and S_40=1 | G_RQ1=1)>=0.80`，并同时报告两项 conditional marginal power；RQ2 每个保留的确认性 contrast 也须在其 design alternative 与适用的 gate-valid envelope 下达到至少 0.80 Holm-adjusted marginal power。资源不足时，G4b 必须在正式执行前降低相应论断，不能继承 v1.6 的规划结论。在 `Delta*=delta` 上计算 power 无效，也不得报告 observed power。任何正式结果不得进入该计算；不精确不得写成“无效应”，G4b 后不得 early stopping、扩展正式数据集或替换方法/家族。

## 8. Episode 数据与工件契约

Paper-1 把 M0-M5 generation、evaluation、repair、cost、provenance 与 missingness 记录为 immutable episode evidence。它不构建或发布模型训练 corpus，也不调用任何训练或 merge command。

保留所有自然失败。synthetic injector 和 mutation 仅用于辅助 control/oracle qualification，并带有显式 origin label；它们不得静默混入自然失败 prevalence 或 headline repair effectiveness。repair transition 必须包含已执行 diagnosis、非空且有效的 patch/delta、实际 rerun，以及可对账的前后 outcome。仅有 bucket name 或 H-stage failure 不构成 repair transition。

每个 runtime episode artifact 都必须通过已注册 contract 验证，绑定冻结的 requirement/method/model/tool/budget identity，保留 included、excluded、`not_run` 与 infrastructure reason，并维持 candidate、public evaluator 与 hidden evaluator 的 visibility boundary。原始 hidden case、path、output、status 和 score 不得进入 candidate workspace 或 repair-visible record。

episode evidence 必须分别绑定 hidden execution/semantic status、exactly-once semantic-commit event、same-terminal infrastructure-retry lineage、integrity violation，以及 G3/campaign reducer 使用的全部 source ref。sanitized downstream outcome 不得暴露 hidden case 或原始 evaluator output。

G3 和 G4a 各自建立 immutable、checksummed 的本地 checkpoint manifest，确保其中命名的文件、contract、test、evaluator commitment 与 analysis code 可重建且不修改受控证据。Git commit 可以承载该 checkpoint，但本文不要求本轮创建 commit。

既有 training-view、eligibility、pool 与 candidate-release contracts 仅为仓库兼容性和可能的 future work 保留。它们不是 Paper-1 必需工件，不授权 dataset release，也不获得 Paper-1 论断 credit。

## 9. 物理确认与可选 target-profile adaptation

正式 OpenXC7 L4 只有在同一个 terminal candidate 通过完整 `VPP-L3` 路径（包括一次性 hidden L2）后才 dispatch，且不是 headline 分母。任何 hidden 前 eager route 只能放在隔离的 excluded development diagnostic 中，不得影响 terminal selection、repair、hidden eligibility、VPP、正式成本或 Paper-1 物理结果。预声明的代表性家族为：

- `fir_filter`
- `matrix_vector_mac`
- `single_dual_port_ram`
- `stream_fork_join`
- `sobel_threshold`
- `qtable_update_core`（单独的旗舰拓扑/参数留出）

该集合覆盖数值、存储、stream/control、图像，以及目录指定的旗舰 shell。如果 `qtable_update_core` 不能进入物理协议，G2/G4b 必须在结果产生前解决目录中的旗舰指定问题；不得静默删除它。对于每个合格候选，记录 routing status、timing/Fmax、声明的 resource field、工具版本、constraint 和 failure classification。

如果启用可选 target-profile 扩展，其独立结果前 manifest 才从这些代表性家族中提名 pair。每个 pair 保持 `semantic_instance_id`、功能义务和 hidden-oracle 语义不变，只改变一个预声明 profile 轴或明确定义的复合 profile。profile compliance 与功能保持由 evaluator 独立验证，profile change 不得暴露私有 family label、hidden case 或 evaluator 内部信息。没有该可选 manifest 不阻塞核心 G4b 或 G8 物理深度阶段。

对同一冻结 RTL 运行 Vivado 是可选商业参考，不是 TRETS 投稿 gate。没有 Vivado 时，只报告 OpenXC7 post-route 证据。`.bit` 生成和 L5 板级执行需要独立协议，不能从 FASM 或 routed report 推断。

## 10. 有序工作包与 gate

任何模型 pilot 都不得跳过 G1-G4a。任何正式运行都不得跳过 pilot 之后签署的 G4b 冻结。Paper-1 不授权训练 run。

### G0 — 文档与权威冻结

- 从 `AGENTS.md`、`docs/README.md`、`docs/current-status.md` 和 `docs/specs/README.md` 链接本文。
- 已被取代的 Paper 1 提案不再留在工作树中，但可从 Git 历史恢复。
- 验收：clean-link audit 通过，且不存在另一个被标记为当前 Paper 1 权威的文件。

### G1 — System-HIS 契约闭合

**当前 gate 状态（2026-08-18）：本地关闭。** 注册的 conformance matrix、Direct
common-L0 和完整轻量回归已通过；这不授权 pilot、official hidden 或结果论断。
G2 于 2026-08-24 本地关闭，G3-G4b 仍开放。

- 选择并实现一种 JSON-Schema/H0 权威关系。
- 使规范正 fixture 和正式示例通过 schema、H0、H1、H2；或者明确将不可 lower 的示例重新标注。
- 为每条冻结规则添加负 fixture；统一 reset；定义并测试 compatibility/quarantine envelope。
- 将方法中立共同工程契约与 optional System-HIS、H-stage、candidate-testbench 和 predicted-QoR artifact 分开。Direct 与 untyped control 必须在没有 System-HIS 时进入共同 L0，并把 H0-H3 记录为 `not_applicable`。
- 验收：schema/checker/fixture/lowerer conformance matrix 全绿，真实 Direct→common-L0 regression 证明不存在 H-stage dependency，完整 regression 通过。

### G2 — 目录、证据与阶段语义

**当前 gate 状态（2026-08-24）：本地关闭。** canonical catalog/ledger 已解决下列
alias、stage semantics 和 L4 provenance 问题。这是实现/证据完整性 gate，不是模型
结果或 signed campaign artifact。

- 修复 `clock_divider`；统一 T7；建立 alias/sample-level T10/T11 证据。
- 使 `contracts/task-catalog/` 成为唯一 catalog 目录；不得在 `docs/` 保留 catalog 副本。
- 使 L3 名称/定义与实际 runtime 一致，或者以测试支撑修改 runtime；修复账本日期、source reference 和 L4 provenance。
- 验收：语义契约测试能在旧缺陷上失败，且 human status view 可从账本重新生成。

### G3 — 测量与回合包闭合

- 注册并在 runtime 验证版本化的 benchmark-split、episode-pack、method-condition、model/gateway provenance、attempt-event/trajectory、campaign-freeze、paired-outcome 和 cost-summary 契约。
- 注册并在 runtime 验证 requirement-envelope、requirement-disposition、ambiguity-case、clarification-replay 与 ambiguity-outcome 契约。
- 实现一等 M0-M5 adapter；将 `source` 与 `method_condition` 分开；添加外部 requirement/semantic-parameter loader、M2 untyped-plan 路径和 M3 真正的 no-skeleton generator。
- 用显式、全局计入预算的 event 替代不可见内部 retry。
- 对每个 success 与 stop outcome 持久化共同 requirement intake；记录全部 fact/provenance/default/assumption ID、route/profile hash 与 clarification 前后 lineage，而不是只保留前三个问题。
- 增加 stop-before-generation interception、no-nearest-family test 与 visibility spy test，证明任何私有 ambiguity label/answer 都不能到达 model、Recipe、HIS、project、repair 或保留的非 Paper-1 training context。
- 将公开评测器与由评测器拥有的隐藏 harness 分离。hidden 只在 terminal immutable candidate 上运行一次；候选 testbench 永不可信；spy test 证明没有 hidden datum 到达修复器。
- 只有发生真实 diagnosis/patch/rerun transition 才计作修复；按成功 stage 限制 QoR；保留明确的 episode inclusion/exclusion reason。
- 记录 pre/post state hash、artifact delta、visibility class、call、token、cached token、duration、acceptance、failure origin 和全部 cost axis；将 freeze/state/audit bundle 提升到 `tmp/` 之外。
- 新增 additive、registered 的 `g3-acceptance-v1` authority。正向 verdict 只能从 write-once artifact/event ref、注册 contract version、checksummed test/evidence manifest 和有限 required-scenario matrix 重建；caller 声明的 scenario 名、success boolean 或 prose status 均无验收权威。既有 development outcome contract 保持固定 non-official 语义，不得改写成 G3 authority。
- 任何 development/excluded VPP projection 都只能是 non-official conformance diagnostic。它本身不能授予 `g3-acceptance-v1`、official pass-credit authority、official VPP outcome 或 G4b authorization，也不得晋升为其中任何一种 authority。
- G3 matrix 至少覆盖：同一 gold-ready M0-M5 replicate block；显式 `semantic_instance_id`/`replicate_id`/`paired_block_id`、requested-seed provenance 和由独立 schedule seed 控制的平衡顺序；M0/M1 共享初始工程；M3/M4 共享 HIS；M4/M5 共享初始工程；M1/M5 各一条真实 public failure→diagnosis→patch→rerun；M5 H0-H3 correction；public/hidden pass/fail；sanitized provider/public/hidden/L3 infrastructure outcome；三种 cost view 的 raw-to-summary 对账；以及 tamper、lineage、order、budget、trusted-edit 和 visibility fail-closed case。没有 candidate 的 scenario 也必须闭合为 registered outcome。
- G3 还要求 reducer-derived provider-capability classifier、确定性/fake 正向 fixture、真实或合成负向 fixture 与 strict pre-dispatch guard。计数、match flag、classification、limitations、profile identity 和 eligibility 必须从冻结 protocol、documentation-review 与逐次 observation artifact 重算，不能信任提交的 summary boolean。现实外部 provider 不必在 G3 已 eligible；G3 只证明 excluded implementation conformance，真实 provider 的 mode 决策属于 G4b。
- G3 只有在全部 matrix cell 均由 artifact 推导且通过，同时 ready/default/clarification/gap fixture 可重建 confusion matrix、non-ready downstream event 为零、无私有/隐藏泄漏时才可 pass。验收 artifact 明确固定 `official_outcome=false`、`official_authority=false`、`pass_credit_authority=false`、`g4b_authorized=false`。因此 G3 仅证明 excluded development conformance。G4a 准备 candidate benchmark 与 evaluator/oracle commitment；G5 是排除于正式实验之外的 natural-model feasibility pilot；G4b 签署并独立授权 no-outcome campaign；G6 只物化 campaign 而不产生 official outcome；G7 执行 official M0-M5 held-out L0-L3 experiment。上述后续 gate 的 deliverable 均不是 G3 的验收前提。

G3 可以使用 deterministic/fake model client，但必须使用真实 parser、registered contract、evaluator/tool adapter 和 reducer。G3 不产生方法效果证据；G5 才是首个可用于 paired discordance、attrition、runtime 或样本量假设的 natural-model feasibility run。

### G4a — 候选基准与分析协议

- 创建候选 14-family join、semantic-instance requirement、split、ordered reserve list、objective exclusion、generalization label、episode pack、evaluator commitment、analysis code 和 planning sample-size model。
- 仅当启用可选 target-profile 扩展时，创建 candidate pair、stable pair/member ID、功能不变量、必须/允许/禁止变化、profile-compliance commitment、L3/L4 endpoint、客观排除规则和规划 pair 数量；这不是核心 G4a 验收依赖。
- 创建与其分离的 candidate ambiguity-audit manifest，包含 base cluster、paired variant/perturbation stratum、独立裁决的 private gold commitment、critical fact、allowed default、answer object、capability profile hash、objective exclusion 和 ordered reserve list。
- 在任何 G5 outcome 打开前冻结 RQ1/RQ2 contrast-specific MOI、严格高于各 threshold 的 design alternative、至少 0.80 的 target power、RQ1/RQ2 Holm 实现、RQ1 完整论断的 gate-conditional joint-power rule、threshold-test/interval 实现、repair-probe eligibility/selector/cap/minimum，以及 RQ0 scientific threshold 和 exact interval rule。G5 只能估计 nuisance parameter 与资源需求，不能移动科学 goalpost。
- 冻结正式 ready fact projection 和 Family Recipe information policy；主要留出 headline method 不获得 family-specific Recipe body。
- pilot 前密封正式 requirement/oracle 内容；implementation work 只能看到 hash 和 readiness state。
- 验收：reference condition 在每个候选家族上 dry-run，并产生不包含模型结果、带 checksum 的 candidate manifest。

### G5 — 排除于正式实验之外的配对可行性 pilot

- 初始 planning proposal 为六个核心行为类别、每类四个新的独立非正式 semantic instance、M0-M5 和三个 replicate：共 24 个 semantic instance、72 个 replicate block、432 个 method-outcome episode。它是 excluded planning floor，不是授权运行或最终样本量；G4a 可在打开任何 pilot outcome 前修订。
- 使用六条 balanced Williams/Latin sequence：72 个 block 中每个方法在每个 ordinal position 恰好出现 12 次；每类 12 个 block 中每个位置出现两次。shared prerequisite 在 block-preparation phase 先物化，再执行随机化 method-specific phase。完整固定 matrix 必须全部尝试，不得 efficacy early stop、按 outcome 扩大、替换样本或同 pilot top-up。
- 用与正式协议相同的 paired-block identity 和 shared checkpoint 执行 M0-M5；M1 与 M5 各至少发生一条真实 diagnosis→patch→rerun，并完整记录 provenance、missingness 和三种 cost view。
- 仅当启用可选 profile 扩展时，对每个候选 change axis 执行至少一个 pilot-only pair；它们不进入正式扩展总体，也不属于核心 scale criterion。
- pilot 前冻结 repair-probe selector，并设置每个行为类别 `k_c<=4`，因此 `K<=24`。R_generic 与 R_HIS 各一条 one-call branch，额外产生恰好 `2K` 个 probe branch、至多 48 个 model call，以及对应 public rerun 与 one-shot hidden evaluation；禁止结果后 top-up。
- 核心 G5 planning ceiling 为：720 次 standalone-attributed initial call、共享规则下 432 次 unique physical initial provider request、144 次 M1/M5 repair-or-correction call，以及至多 48 次 repair-probe call；冻结 transport retry 与 public/hidden/tool invocation 另计。
- 只有以下条件全部满足才可扩展规模：reference path 100% 可执行；每个模型 episode 即使以 `GEN_FAIL` 结束也产生可审计 outcome bundle；至少一个 model treatment 到达 L0；M1 和 M5 各有一条真实 diagnosis→patch→rerun。
- 上述两条 transition 只证明 mechanism feasibility；RQ2 confirmatory readiness 还必须满足冻结的 probe minimum-count rule，以及每个保留 RQ2 contrast 的 Holm-adjusted marginal-power rule。
- 模型质量失败保留为结果；基础设施/契约失败重新打开相应 gate。pilot requirement 永不进入正式测试。
- hidden/private leakage、trusted edit、duplicate hidden commit、artifact/lineage/budget failure，或冻结 retry 后仍未解决的 infrastructure failure 必须立即停止并重开相应 gate；already-attempted model-quality outcome 仍保留在 ledger。
- 仅使用 pilot 的 paired discordance、cluster dependence、attrition、hidden/public divergence 和 runtime，为最终协议确定样本量和预算。任何 adapter、prompt、evaluator-visibility、budget 或 schema 变化都会使 G4a 失效，并要求版本化 candidate-protocol revision。
- 在独立 pilot-only ambiguity cluster 上执行全部 disposition、permitted-default、contradiction、capability-gap 与 clarification-replay path。观察 pilot 后若修改 fact taxonomy、default/capability profile、Recipe ordering、metric、visibility、question policy 或 replay semantics，必须使相应 G4a audit protocol 失效并重新版本化。

若任一 scale criterion 失败，不得扩大 pilot、增加 prompt privilege 或打开正式 campaign 来制造 downstream event。只能版本化 G4a 后重新做一轮 excluded pilot，或转向 benchmark/evaluation 或有边界负结果路线；model-quality failure 是 feasibility evidence，integrity/infrastructure failure 是 gate failure。

### G4b — 最终签署的 campaign 冻结

- 冻结最终 split/sample size、semantic cluster、三个 replicate ID、`decoding_control_mode`、requested-seed provenance、独立 `execution_schedule_seed`、method order、prompt、effective-information hash、base model 与 inference configuration、global budget、tool、evaluator hash/case seed、candidate selection、infrastructure retry/abort threshold、未经 pilot 改动的 RQ1/RQ2 MOI 与 design alternative、正确性非劣 margin、primary cost axis、完全指定的 estimator/test 和 multiplicity rule。
- 冻结最终 ambiguity-audit cluster/perturbation balance、private commitment、default/capability profile、A_req budget、infrastructure rule、`FP_amb`/`FP_gap` interval、未经 pilot 改动的 false-block/replay threshold 与 leakage check；签署 audit outcome 不得改变 VPP population 或任何 method、prompt、Recipe、budget 和 candidate-selection rule。
- 冻结 RQ1 primary Holm family（`M4-M3`、`M4-M0`）、强制 secondary `M3-M2` 分析、独立 RQ2 Holm family（`M5-M4`、`R_HIS-R_generic`）、repair-transition definition、correctness non-inferiority rule 和 online model/tool/cost reporting。两个 family 各自保留 alpha，不允许 cross-family alpha recycling。
- 冻结家族等权 macro estimator、threshold-test 与 CI 实现、Holm reducer、RQ1 gate-conditional joint/marginal-power report、描述性 M5-M1、paired-block identity、seed-control eligibility、balanced order、shared artifact 和三种 cost view。
- 最终样本量由 excluded-pilot joint simulation 冻结；每家族 30 个 semantic instance 在此之前只是 planning target。一般地，每家族 `n` 个 instance 时，`B=12n` replicate block、`E=72n` method episode；standalone-attributed initial-stage ceiling 为 `120n`，三组共享关系下 unique physical initial request ceiling 为 `72n`，M1/M5 repair/correction ceiling 为 `24n`，probe 另加 `2K_off`。`n=30` 时分别为 360 block、2,160 episode、3,600 standalone initial、2,160 physical initial、720 repair/correction；最大 model-side total 为 standalone `4,320+2K_off`、physical `2,880+2K_off`。上游失败可能短路后续 stage，因此它们是 ceiling，不是最低调用数；public tool、hidden、EDA、token、wall-time 与 transport retry 另计。
- 冻结 `tpa_extension_status=disabled|enabled`。`disabled` 不要求 pair artifact 并禁止后续 adaptation claim；`enabled` 才在独立 signed extension section 中冻结 pair population、axis、invariant、change policy、compliance oracle、`TPA-L4` estimator、完整 pair denominator、L3/L4 policy、cost/missingness、sample-size justification 与 confirmatory/descriptive status。未启用它不阻塞核心 G4b。
- 要求所有四个主要留出家族具有合格且由评测器拥有的独立 oracle，并通过 M0-M5 full-pack dry-run。
- no-outcome manifest 必须绑定 v1.7 freeze hash、positive G3 acceptance ref、G4a core benchmark/OASA manifest、G5 provenance、model/prompt/information hash、`decoding_control_mode`、replicate block、requested-seed provenance、独立 schedule seed/order、budget/tool、public/hidden commitment、missingness/abort policy、analysis code、oracle readiness 和 `tpa_extension_status`。
- `documented_seed_control` 必须绑定 independently reviewed 且 eligible 的 provider-capability profile；`stochastic_blocked` 则必须绑定完整 replicate plan、冻结 provider/model/gateway/inference config、balanced schedule、missingness policy 与禁止 deterministic/common-randomness 论断的规则。混合或未指定 mode 均无效。
- 验收：独立 verifier 推导 registered `g4b-authorization-receipt-v1`，包含 campaign ID/freeze hash、verified prerequisite ref、signer policy、extension status、`side_effects_before_verification=0` 和 `authorized=true`。manifest 作者不能自行填写授权。任何缺失、不匹配或未签名输入都必须在 run directory、model client、candidate、public/hidden evaluator side effect 之前失败。G4b 不执行或晋升任何 development outcome；授权后修改主要 method/family/metric 必须使 campaign 失效。

### G6 — 正式 campaign 物化

- 严格根据 G4b manifest 物化已签署的 M0-M5 episode pack、model/provider configuration、public/hidden evaluator commitment、tool environment、budget ledger 与 analysis environment。
- 只有可选 target-profile 扩展已签署时才物化 pair 与 evaluator-owned compliance commitment；否则不要求 profile-pair 材料。
- 在任何正式 model call 或 hidden evaluation 之前，拒绝缺失、不匹配或未签署的 split、method、prompt、model、evaluator、tool、budget 或 analysis hash。
- 验收：形成不含 outcome 的 sealed campaign package，并在非正式 dummy task 上通过 inference preflight；不创建训练 dataset、checkpoint、adapter、merge 或模型训练 process。

### G7 — 正式留出实验

- 执行冻结条件，不改变 prompt、tool、budget、oracle 或 model weight。
- 在 intake code、profile、label 和 analysis 冻结后，以独立 stop-before-generation population 执行已签署 ambiguity audit。audit result 不得触发 adaptation、正式 instance 排除或 rerun。
- 验收：已签署 G4b manifest 中每个 semantic-instance cluster 都有可对账的 design outcome 或声明的 infrastructure status；每个 terminal candidate 最多接受一次 hidden evaluation；分析可从 immutable event 重新生成所有 confirmatory table。

### G8 — 物理确认与可选 target-profile adaptation

- 对合格冻结候选运行预声明 OpenXC7 子集；可选地对同一 RTL 运行 Vivado。
- 核心验收分别报告无条件 VPP-L4、以 L3 survivor 为条件的 attrition、时序/资源结果、train/test/flagship strata、`not_run`、missing-tool 和 design failure。
- 若 target-profile 扩展已签署，才在 profile-specific 工程、约束、L3/OpenXC7 L4 flow 下运行全部 pair，且结果后不得改变 prompt、预算、模型权重、不变量或 compliance rule。扩展单独报告 `TPA-L4`、baseline/variant outcome、完整 pair 分母、compliance violation、cost availability 和 unavailable reason；扩展失败不抹掉已完成的核心结果。

### G9 — 论文论断冻结

- 根据观测证据选择受支持的 TRETS claim track。
- 将每个结果句、表和图绑定到 artifact ID 与 denominator。
- 将每个 ambiguity claim 绑定到命名 audit manifest、base-cluster denominator、disposition confusion matrix、false-proceed bound、assumption/default provenance 与 leakage audit；不得把 audit disposition 描述为工程生成结果。
- 执行 citation、leakage、statistics、reproducibility 和 claim-language audit。

## 11. 结果条件化的发表路线

- **Track A — 契约/评测方法论文：** 一项或两项冻结的 RQ1 primary contrast 和/或 RQ2 contrast 对匹配 control 显示有边界价值，hidden/public separation 与 missingness audit 通过，且相关置信区间下界超过 G4b rule。聚焦得到支持的 contract、materialization、system、repair 与 evaluation contribution，不使用 learned-model 语言。
- **Track B — benchmark/评测方法论文：** 方法效应混合或不精确，但 evaluator-owned hidden protocol、requirement-boundary audit、可复现 project benchmark、failure transition 与 cost evidence 构成 TRETS 贡献；不主张方法优势。
- **Track C — 工件或负结果：** treatment 未优于 control，或协议不足以支持计划推断。发表或保留 benchmark、cost/failure analysis 和负向证据，不主张方法优势。

每条 track 都必须报告已签署 ambiguity audit。通过只允许针对命名 case 和冻结 profile 作有边界论断；失败是必须报告的负结果，并禁止声称系统能安全处理任意短、不完整、歧义或不受支持的需求。不得因此删除 audit case 或正式 VPP instance。

目标期刊为 ACM TRETS。文章聚焦 RQ0/RQ1/RQ2/RQ4、工程级 hidden evaluation、reproducibility、failure/missingness semantics 与 cost。训练和 TCAD-specific extension 不属于本 Paper-1 program。

## 12. 论断规则

### 当前允许

- SR2FPGA 实现了类型化契约以及工程级工具/证据流水线。
- 确定性/参考证据达到 current status 中所界定的计数。
- 已有 oracle/mutation 基础设施和两个有代表性的 OpenXC7 L4 结果。
- Phase D 是已完成的完整性审计，模型结果严格为负。
- HORIZON 是最接近的外循环基线，并促使本工作采用验证器隔离和收敛成本报告。

### 仅在命名 gate 后允许

- positive `g3-acceptance-v1` 后：“冻结 G3 scenario matrix 上的 development conformance”；这仍不允许方法效果、修复有效性或 official hidden performance 论断；
- G7 报告 signed ambiguity manifest、完整 disposition confusion matrix、false-proceed interval、clarification replay、provenance violation 与 leakage audit 后：“有边界的 requirement-boundary performance”；
- G1 后：“闭合的 System-HIS 契约”；
- G4b 后：“冻结的正式基准”；
- M4−M3 主要论断规则通过后：“deterministic materialization/edit-surface benefit”；
- M4−M0 主要论断规则通过后：“未训练的端到端 System-HIS value”；只有两项主要规则都通过，才可作完整 RQ1 论断；
- 真实 transition 加上配对修复策略和端到端 RQ2 分析后：“修复有效性”；
- 仅限 G8 tool/family 子集：“物理改善”；
- G8 报告已签署 pair manifest、完整 pair 分母、不变量/compliance outcome、L3/L4 结果和成本后：“target-profile adaptation”；
- 仅限成功 Vivado 工件：“商业参考”。

### 没有新证据时禁止

- 解决任意不完整或歧义硬件需求；
- 把 `ready`、`needs_clarification`、`capability_gap`、declared default 或正确 clarification question 当作 project/VPP success；
- 从没有生成工程、也没有执行 hidden semantic evaluation 的 A_req case 推断工程正确性；
- 首个仓库级/全自动/tool-feedback RTL 智能体；
- 首个 hardware IR，或称 CPPL 无类型；
- 从 M3−M2 声称“typing alone 改善正确性”，而不是使用冻结的 System-HIS representation-bundle 解释；
- 从 M4−M3 声称 skeleton-text-only、editable-byte-only 或 lowerer-rule-only 因果效应，而不是使用冻结的 materialization/edit-surface bundle 解释；
- 只有一项 RQ1 primary rule 通过时声称完整 RQ1，或用 secondary M3−M2 估计救援失败的 primary rule；
- 完整 JSON-Schema H0、完整 W1-W10 H1 或普适的 by-construction correctness；
- 不存在的训练模型、留出集、修复或 QoR 预测结果；
- 24/24 L4、一般性 L4、`.bit`、Vivado 或 L5 论断；
- 一般性 target-profile portability、跨器件或跨厂商 adaptation，或从 baseline-only/survivor-only 结果授予 adaptation credit；
- 从 synthetic shell 推导 application-realistic RL/vision/radar/SoC 论断；
- 将 T10 证据转移给 T11，或把 catalog intent 当作证据；
- 把 HORIZON 的 iteration-0/best-so-far convergence 与独立 Pass@1 当成同一指标比较；
- 把 `APPROVED`、`not_run`、infrastructure failure 或 `repair_trajectory` bucket label 当作模型成功。

## 13. 必需工件

每个会产生研究结果的 campaign 必须在稳定受控路径下保存：

```text
research_freeze.json
g3_acceptance.json
requirement_disposition_contract.json
ambiguity_audit_manifest.json
ambiguity_oracle_commitments.json
ambiguity_audit_events.jsonl
ambiguity_audit_outcomes.json
ambiguity_audit_summary.json
benchmark_split_manifest.json
candidate_protocol_manifest.json
campaign_freeze_manifest.json
g4b_authorization_receipt.json
paired_block_manifest.json
episode_pack_public_manifest.json
episode_pack_private_commitments.json
method_condition_contract.json
prompt_and_contract_hashes.json
model_and_gateway_provenance.json
tool_versions.json
run_state.json
per_attempt_events.jsonl
paired_outcomes.json
hidden_evaluation_outcomes.json
cost_summary.json
infrastructure_missingness.json
leakage_audit.json
artifact_audit.json
analysis_environment.json
```

只有启用 target-profile 扩展时，才额外要求 `target_profile_pair_manifest.json`、`target_profile_commitments.json` 和 `target_profile_outcomes.json`；未启用时不得创建空占位文件来暗示该扩展存在。

候选工程保留其公开 requirement projection、适用时的 generated HIS、file、diagnosis、patch、公开工具输出、measured QoR 和 trajectory link。hidden score summary 只保留在 evaluator-owned outcome bundle 中，绝不进入 candidate workspace 或 repair-visible log。原始隐藏 oracle 内容保持受保护，并与公开 pack 材料及修复可见日志在物理上分离。

论文中的每个表都必须可由这些工件重新生成，并显示其 population、denominator、negative count、`not_run` count、infrastructure count、tool stage 和 method condition。如果启用可选扩展，每个 adaptation 表还必须显示 `profile_pair_id`、baseline/variant profiles、变化轴、不变量/compliance 状态、完整 pair 分母、cost availability、配对成本和 unavailable reason。

## 14. 与实现工作的关系

本文是研究与实验契约，不是逐步运行手册。当前命令位于 `agent/README.md`、`training/README.md` 及其 config/script README。本文获接受后，每个 gate 可获得一份范围窄、带日期的实现计划。本文不会重新激活任何历史计划。

对研究问题、留出家族、主要指标、基线权限或结果依赖停止规则的变更，必须在打开正式结果前形成版本化 amendment。机械性路径修正和新增非主要诊断可以记录，而无需重新定义主要检验。

下位 code-architecture specification 可以定义实现与测试，但不得在没有版本化研究 amendment 的情况下，新增超出本 v1.7 freeze 的 G3 acceptance row、official prerequisite、scientific contrast 或 information privilege。
