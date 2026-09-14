# SR2FPGA Paper 1 M2 文献与论文定位复验

日期：2026-08-29

阶段：M2 — 现有方法与竞品方案分析

模式：`REVIEW`
结论：**部分通过；不得进入 M3**

## 1. 审查范围与权威

本报告只审查文献、定位、引用与写作材料，不修改代码、实验协议、
官方评价逻辑、已有 Obsidian 笔记或历史证据。

当前研究语义按以下顺序裁决：

1. `docs/specs/2026-08-14-sr2fpga-paper1-research-program-design.md`
   中的 `paper1-freeze-v1.7`；
2. `docs/current-status.md`、当前代码、注册合同和可复现实验；
3. `docs/research-program/paper1-v1/README.md`、`state.json`、
   `foundation/`、`writing/` 与当前审计记录；
4. `D:\Obsidian Vault\博士开题\硬件代码生成` 中的文献、TCAD/TRETS
   工作区与日志材料。

Obsidian 材料是研究与写作输入，不覆盖当前仓库权威。历史 TCAD、
v1.3、v1.5 和 v1.6 表述仅用于追溯。

## 2. 复验摘要

### 2.1 已核实

- 项目已形成任务单位、表示层、起始状态、oracle 权限、学习位置、
  物理深度、成本与 artifact 可用性的多轴文献框架。
- 已有 27 套 reader、27 张实质 evidence card、27 个
  `source_map.json` 和 28 个 TCAD 文献键。
- 27 个 source map 均可解析；全部图表资产存在。
- 27 份 reader 对应的源 PDF 均能按记录的 SHA-256 在资料库中定位；
  其中 23 个 work ID 对应唯一文件，`horizon`、`phoenix-bench`、
  `rtllm`、`verilogeval` 各有两份字节相同副本。
- `26.08.27 文献综述.md` 已形成完整检索词本体、数据库查询方案、
  纳排标准、证据强度框架、研究矩阵和递进式 Related Work 草稿。
- 论文定位已经放弃“首个 Agent”“首个 typed IR”“首个工具修复”
  等不可守主张，转向 deterministic materialization/edit-surface bundle、
  evaluator separation 和固定分母工程证据。

### 2.2 待修复

1. 重点日志仍混用 `paper1-freeze-v1.5`、`v1.6` 和 v1.7 前的 RQ1
   顺序，未全部传播 v1.7 的两成员 RQ1 Holm family。
2. 日志共有 48 个会话型 `cite`、19 个会话型 `filecite`，但没有标准
   BibTeX 引用键；离开原对话后不可复核。
3. TCAD 与 TRETS 两份 BibTeX 使用不一致键名和不同覆盖集合，尚不能
   作为一个稳定的主稿文献注册表。
4. 15 个旧 reader 的 `source_map.json.source_pdf` 仍指向搬迁前的
   `文献/papers/` 路径；哈希能找到现文件，但路径级复现失败。
5. 2026-08-27 文献综述中的多数据库查询主要是检索方案；当前可重建的
   已执行检索记录主要截止到 2026-07-17，二者不能合并称为“截至
   2026-08-27 已完成的系统检索”。

## 3. 现有方法对比表

| 方法群 | 代表工作 | 已占据的位置 | SR2FPGA 不得主张 | SR2FPGA 可检验的剩余位置 | 证据状态 |
|---|---|---|---|---|---|
| 模块级 RTL 生成与 benchmark | VerilogEval、RTLLM、RTLCoder、OpenLLM-RTL | 自然语言到单模块 RTL、pass@k、公开 testbench | 首次 LLM-to-RTL；模块通过等于工程交付 | 完整项目工件义务与方法中立 VPP | 部分已核实；RTLCoder/OpenLLM-RTL 尚缺完整本地证据链 |
| 工具反馈与 RTL 修复 | RTLFixer、AutoChip、VerilogCoder | compiler/simulation/waveform 反馈与迭代修复 | 首次 EDA-in-the-loop；公开通过等于隐藏正确 | public repair 收益能否经 one-shot hidden final | 核心三项已有 reader/card/BibTeX |
| 结构化规格、IR 与硬件意图 | CPPL、FIRRTL/CIRCT、FormalRTL、HINT、ChatCPU | typed/checkable IR、DSL、可执行参考、结构化计划或意图层 | 首个 typed hardware IR；System-HIS 存在即证明有效 | 同一 frozen HIS 下 M4-M3 的 materialization/edit-surface bundle；M3-M2 仅作次要 representation estimate | CPPL/FIRRTL/FormalRTL/ChatCPU 已核实；HINT 仅有 BibTeX，CIRCT 尚缺统一键/卡 |
| 真实 IP、层次与复杂任务 | ArchXBench、CVDP、RealBench、ChipBench、ChipVerilog | 多模块、真实 IP、复杂验证与 repository context | 首次多模块或系统级 RTL 生成 | 从无项目状态构造完整 project package 的统一工件义务 | ArchXBench 已核实；其余多为 TRETS BibTeX 或日志材料，需补 reader/card |
| 仓库修复与演化 | RTL-Repo、HWE-Bench、Phoenix-bench、CktEvo、HORIZON | 既有仓库/issue/harness 上的修复、演化、接受门和轨迹 | 首次 repository-level hardware agent、Git 闭环或 trajectory retention | 区分已有仓库修改与 requirement-to-new-project construction；隔离 repair-visible 与 final-only authority | RTL-Repo/Phoenix/CktEvo/HORIZON 已核实；HWE-Bench 需补证据包 |
| 跨阶段闭合 | CLOSER-Bench | 预算约束下 simulation/synthesis/STA/P&R 跨阶段轨迹 | 首次跨阶段 hardware closure evaluation | FPGA 项目在固定分母下的 L3→L4 有界描述性深度 | TRETS BibTeX 有记录；缺本地 reader/card |
| FPGA 资源与物理证据 | ResBench、Chip-Chat 及 FPGA tool-flow 工作 | LUT/resource、FPGA/GDSII 个案、物理端点 | 两个 L4 pilot 证明一般部署、跨器件或跨厂商能力 | 命名 OpenXC7 子集上的 attrition、timing/resource；target-profile adaptation 仅限单独冻结扩展 | ResBench、Chip-Chat 已核实；广义物理主张仍受限 |
| 参数学习、外部记忆与测试时适配 | VeriReason、ChipSeek、ChipMATE、Dr. RTL、Alpha-RTL | SFT/RL、外部技能记忆、per-design update | Paper 1 包含 learned treatment；HORIZON trajectory 等于训练 | 仅用于划清 Paper-1 no-training 边界和未来工作 | 多项已有 reader/card；全部在 Paper-1 treatment 之外 |

## 4. 不足分析

### 4.1 研究缺口表述仍需加检索范围限定

日志中的强表述是“现有文献尚未在相同模型、需求事实、target profile、
信息权限和总预算下……匹配比较”。该句可作为候选 gap，但当前最多写成：

> 在本报告所审查的本地语料、已执行检索记录及其截止日期内，未发现
> 同时满足上述全部条件的公开工作。

在补齐截至投稿日的增量检索、筛选流图和排除理由前，不得改写成领域
全称判断或 “the first”。

### 4.2 结构化表示不是单一处理变量

现有文献表明，结构化方法经常同时引入 schema、static checking、
deterministic construction、模板、较小编辑面和不同调用预算。因此：

- `M3-M2` 只能估计 frozen v1.7 定义的 representation bundle；
- `M4-M3` 估计 deterministic materialization 与 editable-surface policy
  的联合增量；
- 不得把任一比较解释为 typedness-only 或 skeleton-text-only 效应。

### 4.3 Public repair 的外部有效性仍受 oracle 权限影响

RTLFixer、AutoChip、VerilogCoder、HORIZON 等证明可见工具反馈有用，
但反馈权限、迭代预算和 acceptance predicate 不相同。它们不能形成一个
跨论文 pass-rate 排名。SR2FPGA 的可辩护位置是匹配条件下的 verifier
separation 实验，而不是新的修复算法。

### 4.4 FPGA 属性尚不能由 L3 或少量 L4 个案建立

资源数量、综合通过、P&R、bitstream 和 board functional evidence 是不同
端点。当前 Paper-1 只能把 RQ4 写成受限物理深度描述；target-profile
adaptation 是可选、单独冻结的扩展，不能反向成为 minimum Paper-1 的
既成贡献。

### 4.5 文献证据链的工程一致性不足

- 两份 BibTeX 只有 11 个完全相同键。
- 同一工作存在 `rtl-repo`/`rtlrepo`、`spec2rtl-agent`/`spec2rtl`、
  `phoenix-bench`/`phoenix` 三组别名。
- TCAD BibTeX 有 28 项，其中 27 项有 reader/card；`hint` 只有 BibTeX。
- TRETS BibTeX 有 20 项，其中若干新近工作没有 reader/card。
- 会话型引用没有稳定 work ID、BibTeX key 或原文锚点。

这会导致正文键漂移、重复计数和无法从主张回溯原文。

## 5. 改进方向

### 5.1 先统一当前主张层级

所有当前写作材料应采用 v1.7：

- RQ1 primary Holm family：`M4-M3`、`M4-M0`；
- mandatory secondary：`M3-M2`；
- 每个 primary 只能激活对应局部主张；
- 完整 RQ1 需要两个 primary claim-activation rule 均通过；
- RQ2 使用独立 Holm family：`M5-M4`、`R_HIS-R_generic`；
- RQ0 独立于 VPP population；RQ4 为有界、描述性物理深度；
- Paper-1 不训练、微调或合并模型。

### 5.2 建立一个 canonical citation registry

建议以 27 个现有 canonical work ID 为种子，统一：

`canonical_id -> BibTeX key -> reader -> evidence card -> source_map -> PDF hash`

优先消除三组别名，随后为 HINT、RTLCoder、CVDP、RealBench、HWE-Bench、
CLOSER-Bench、ChipVerilog 及正式 Related Work 中仍保留的工作补齐或明确
降级。没有 reader/card 的工作可以暂时引用书目信息，但方法、数字和
artifact 细节应标为 `待核实`。

### 5.3 把“检索设计”和“检索执行”拆成两张表

- 检索设计表保存数据库、完整查询式、过滤器和计划时间窗；
- 检索执行表保存实际日期、平台、返回数、筛选数、去重数、纳入数和
  排除理由。

只有第二张表有真实记录的数据库才能写成“已检索”。

### 5.4 把论文定位收束为组合而非首创

建议稳定使用：

> SR2FPGA 检验显式 requirement-to-project contract 经 deterministic
> materialization 与受控编辑面物化后，是否在匹配条件和独立终态评价下
> 提高 FPGA 定向 RTL 工程包的可验证成功率。

该句是待实验的研究问题，不是当前效果结论。

## 6. 相关文献清单

### 6.1 本地 claim-ready 集合（已核实证据链）

下列 27 个 canonical work ID 同时具有 reader、evidence card 和
`source_map.json`，且源 PDF 哈希已在本轮重新定位：

`agon`, `alpha-rtl`, `archxbench`, `autochip`, `chatcpu`, `chip-chat`,
`chipcraftbrain`, `chipmate`, `chipseek-r1`, `cktevo`, `cppl`, `dr-rtl`,
`firrtl`, `formalrtl`, `gpt4aigchip`, `hivegen`, `horizon`,
`phoenix-bench`, `representation-bottleneck`, `resbench`, `rtl-repo`,
`rtlfixer`, `rtllm`, `spec2rtl-agent`, `verilogcoder`, `verilogeval`,
`verireason`。

“claim-ready”只表示本地证据链足以支持其 evidence card 中被限定的主张，
不表示该工作可作为同协议可执行基线。

### 6.2 BibTeX/日志存在但证据包未闭合（待核实）

| 工作 | 当前本地状态 | 允许用途 | 暂不允许用途 |
|---|---|---|---|
| HINT | TCAD/TRETS BibTeX；无 reader/card | 身份与检索队列 | 细节、数字、完整 novelty boundary |
| RTLCoder | TRETS BibTeX；文献目录有材料，无统一 reader/card | 模块生成背景 | claim-level 数字与 artifact 判断 |
| CVDP | TRETS BibTeX | benchmark 身份 | 数据规模、类别与运行细节，除非回到原文 |
| RealBench | TRETS BibTeX | 真实 IP benchmark 身份 | testbench/formal 差异的精确数字 |
| HWE-Bench | TRETS BibTeX | repository repair 身份 | 417 等数字，除非原文锚定 |
| CLOSER-Bench | TRETS BibTeX | cross-stage closure 身份 | 任务数、工具深度和效果数字 |
| ChipVerilog | TRETS BibTeX | 层次/跨模块 benchmark 身份 | 规模与效果数字 |
| OpenLLM-RTL、ChipBench、CIRCT、Spec-Driven Hardware Evolution | 日志中出现；未在两份 BibTeX 中形成完整统一映射 | 发现线索或待补背景 | 直接进入最终正文事实 |

### 6.3 历史/边界工作

训练、外部记忆、测试时参数更新、HLS/DSE 和已有 RTL PPA 优化工作可用于
界定相关领域，但不进入 Paper-1 M0-M5 的 learned treatment 或同任务主表。

## 7. v1.7 文献与论文大纲同步审计表

| 文件 | 旧表述/问题 | v1.7 当前权威 | 建议修订 | 状态 |
|---|---|---|---|---|
| `日志/26.08.27 创新性判断.md:9` | 活动协议写为 v1.5 | 当前为 v1.7 | 更新版本；保留“正式结果未运行”边界 | 待修复 |
| `日志/26.08.27 创新性判断.md:693-694` | 用 M4-M3、M4-M0 描述贡献成立条件，但缺完整统计激活规则 | 两者为 RQ1 primary Holm family；还需 CI lower bound、`G_RQ1` 与局部/完整 claim 规则 | 补齐 claim-activation 条件 | 部分一致 |
| `日志/26.08.27 文献综述.md:25` | 活动协议写为 v1.5 | 当前为 v1.7 | 更新 authority banner；保留 pre-outcome 边界 | 待修复 |
| `日志/26.08.27 文献综述.md:880` | 方法关系基本正确，但引用为会话型 `filecite` | M3/M4 共享 frozen HIS；M4/M5 共享 initial skeleton project；以 freeze §5.2 为准 | 换成稳定仓库锚点和正式引用 | 部分一致 |
| `日志/26.08.27 文献综述.md:884` | 使用领域全称“现有文献尚未” | 只能在已执行检索范围和截止日期内陈述 | 改成范围限定的 “未发现” | 待修复 |
| `日志/26.08.27 研究整体方案优化版.md:5` | 权威写为 v1.6 | 当前为 v1.7 | 更新 banner | 待修复 |
| `日志/26.08.27 研究整体方案优化版.md:54-60` | 把两成员 RQ1 Holm family 写成建议、v1.6 fixed sequence 写成当前方案 | 该建议已由 v1.7 接受 | 改为“已生效 v1.7 决策”，删除待 amendment 语气 | 待修复 |
| `日志/26.08.28 确定性骨架生成.md:123,152` | 一处说输出处理/修复前重建并比 SHA；另一处说重试时骨架完全不重建 | 当前 `context_his.py` 会重建并比 SHA；兼容 `his2project.py` 在一次 generate 调用内复用对象 | 区分两个执行路径，避免互相否定 | 待修复 |
| `日志/26.08.28 确定性骨架生成.md:139` | “结构错误设计上根本不可能出错” | skeleton conformance 不是功能或架构正确性；价值待 M4-M3 验证 | 改成“在有效 HIS 与正确 lowerer 前提下，按构造消除一类声明/装配漂移” | 待修复 |
| `日志/26.08.29 中文大纲.md:1` | 权威写为 v1.5 | 当前为 v1.7 | 更新版本和 amendment 历史 | 待修复 |
| `日志/26.08.29 中文大纲.md:1016-1022` | 三个 RQ1 对比并列，未标 primary/secondary | M4-M3、M4-M0 为 primary；M3-M2 为 mandatory secondary | 重排并标注统计地位 | 待修复 |
| `日志/26.08.29 中文大纲.md:1065-1076` | 使用 v1.5 fixed sequence，并把 v1.7 结构写成未来 amendment | v1.7 已替换 fixed sequence | 改为两成员 Holm family 与局部/完整 claim 规则 | 阻断性问题 |
| `日志/26.08.29 中文大纲.md:1494-1500` | 任一 primary 为正即可进入 Track A，未明确局部主张 | 单个 primary 只能激活其对应 claim；完整 RQ1 需要二者均通过 | 把 Track A 拆成局部与完整支持语言 | 待修复 |
| `docs/research-program/paper1-v1/writing/argument_map.md` | 已采用 v1.7 primary/secondary 层级 | 与 freeze 一致 | 作为日志修订的当前写作锚点 | 已核实 |
| `docs/research-program/paper1-v1/writing/section_contracts.md` | 已绑定 RQ1/RQ2 Holm、证据义务和禁止主张 | 与 freeze 一致 | 保持不变 | 已核实 |

## 8. 引用可追溯性审计表

### 8.1 计数

| 对象 | 结果 | 判断 |
|---|---:|---|
| 日志 `filecite` | 19 | 不可脱离原会话复核 |
| 日志 `cite` | 48 | 不可作为最终论文引用 |
| 日志标准 `[@bibkey]` | 0 | 尚未接入 BibTeX |
| TCAD BibTeX keys | 28/28 唯一 | 结构可用，但与 TRETS 不统一 |
| TRETS BibTeX keys | 20/20 唯一 | 覆盖当前近邻，但部分缺 reader/card |
| reader/card/source-map | 27/27/27 | 结构完整 |
| 可按 SHA-256 定位的 reader 源 PDF | 27/27 | 内容来源可恢复 |
| source map 中路径可直接解析 | 12/27 | 15 条路径迁移未同步 |

### 8.2 映射等级

| 等级 | 必需链路 | 可用范围 |
|---|---|---|
| A — claim-ready | canonical ID + BibTeX + reader + card + source map + PDF hash + 原文锚点 | 可用于 card 明确允许的正文主张 |
| B — identity-ready | BibTeX + DOI/arXiv/稳定元数据；reader/card 不完整 | 只能确认工作身份、题名、年份和检索优先级 |
| C — discovery-only | 日志、搜索摘要或会话型 cite | 只能用于发现，不得进入正式事实 |

### 8.3 示例：HORIZON

当前可追溯链为：

`horizon` → `references.bib` → `readers/horizon/paper.md` →
`evidence-cards/horizon.md` → `source_map.json` →
`2606.28279v1.pdf` SHA-256 → `E-HZN-01` 至 `E-HZN-11`。

但其 evidence card 仍含历史句子“若保留 M6”，与 v1.7 no-training scope
冲突；这不破坏 HORIZON 原文证据，却会污染 SR2FPGA 当前解释，必须修订
或加历史状态标记。

## 9. 检索执行与检索方案审计

### 9.1 已执行并有记录

`SR2FPGA-TCAD/01_literature/gap-search-log.md` 记录：

- 时间窗：2026-07-16 至 2026-07-17；
- 覆盖截止：不晚于 2026-07-17；
- 实际来源：OpenAlex fallback，随后使用 arXiv、Crossref、IEEE、ACM、
  AAAI 和作者 artifact 做精确核对；
- 六个 broad query family，每组记录前 20 条筛选；
- 四轮 refinement；
- 去重顺序：DOI、arXiv ID、规范化题名、作者/年份；
- 明确的 full-reader 与 evidence-card-only 规则。

该记录支持“一轮可复核的补充检索”，但文件自身明确写着 saturation
尚未关闭。

### 9.2 已设计但不能视为全部执行

`日志/26.08.27 文献综述.md` 给出 Scopus、Web of Science、IEEE Xplore、
ACM DL、arXiv、Google Scholar 和 CNKI 的完整检索方案及筛选标准。
当前没有为每个平台同时找到实际执行日期、命中数、筛选数、去重数和
排除记录。因此这些内容应标成“检索方案/待执行”，不得写成已完成的
多数据库系统检索。

### 9.3 当前检索结论

文献材料对 M2 主题分析是 `SUFFICIENT`，无需重新建立语料库；但若要在
正式论文中使用截至投稿日的 novelty-gap 语言，仍需一次有完整日志的
增量检索和 metadata/version refresh。

## 10. M2 正式复验

### 一、总体结论

**部分通过。**

### 二、逐条验收

1. **能够明确本文相对谁改进**

   判断：**满足**。

   已明确相对模块生成、公开修复、结构化表示、仓库演化、跨阶段闭合和
   FPGA 资源评价等路线的差异，并能指出 M0-M5 内部匹配比较与外部能力
   矩阵的不同作用。

2. **不足具体而非泛泛**

   判断：**部分满足**。

   方法不足已经具体到任务单位、输入权限、oracle、预算、分母、artifact
   和物理端点；但 48 个会话型引用、19 个 filecite、15 条失效 source
   path 以及若干 bibliography-only 工作，使部分不足尚不能从最终正文
   稳定回溯到原始证据。

3. **改进方向与后续方案一致**

   判断：**部分满足**。

   核心方向与 v1.7 一致，但重点日志仍保留 v1.5/v1.6 的 RQ1 顺序、
   amendment 语气和局部/完整 claim 混淆。中文大纲的统计章节尚未达到
   v1.7 一致性。

### 三、关键缺口

1. 统一 v1.7 协议与 claim hierarchy。
2. 建立 canonical citation registry，替换会话型引用并修复 source paths。
3. 把检索方案与真实执行记录分开，补齐投稿前增量检索日志。

### 四、修改任务

1. 先修订 v1.7 同步矩阵中的阻断项，不改实验协议本体。
2. 统一 BibTeX 键并逐项建立 claim-to-anchor 映射。
3. 仅在真实执行后填写增量检索的返回数和筛选结果。

### 五、风险提醒

- 文献数量、reader 数量和代码实现均不构成方法效果。
- development、deterministic smoke、历史 L4 与协议设计不得进入 Results
  作为 official outcome。
- `M3-M2` 不得提升为 RQ1 primary，也不得救援失败的 primary claim。
- 单个 RQ1 primary 通过时，只能写对应局部主张。

### 六、是否允许进入下一阶段

**暂不允许。**

原因：三个 critical acceptance criteria 中，第二和第三项仍是部分满足。
本报告不修改阶段状态，也不授权 M3、G5 或任何 official campaign。

## 11. 当前路线卡

```text
当前站：M2——现有方法与竞品方案分析
已经完成：文献地图、近邻分类、基线角色、创新边界、Related Work 草稿
还需要：v1.7 同步、稳定引用链、检索执行记录与 source-map 路径修复
下一步：完成 M2 修复后重新验收，不进入 M3
需要你提供：若执行受限数据库增量检索，再提供机构访问；本地修复无需新增材料
```
