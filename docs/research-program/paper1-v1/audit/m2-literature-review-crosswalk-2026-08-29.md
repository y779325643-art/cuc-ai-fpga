# M2 文献综述交叉对照：2026-08-27 日志与 v1.7 当前稿

日期：2026-08-29

状态：M2 已通过并继续补强；不进入 M3

对照来源：

- 历史日志：
  `D:\Obsidian Vault\博士开题\硬件代码生成\日志\26.08.27 文献综述.md`；
- 当前阅读总结：
  [`../writing/literature-summary-v1.7.md`](../writing/literature-summary-v1.7.md)；
- 当前定位稿：
  [`../writing/m2-literature-positioning-v1.7.md`](../writing/m2-literature-positioning-v1.7.md)；
- 当前引用注册表：
  [`../foundation/canonical-citation-registry.md`](../foundation/canonical-citation-registry.md)。

历史日志保持不变。本文件决定哪些内容可以进入当前 Paper-1，哪些必须
改写或停止使用。

## 1. 总体判断

`26.08.27 文献综述.md` 是现有材料中结构最完整的综述草案。它提供了：

- 研究主题与边界；
- 关键词本体和多数据库查询式；
- 纳入/排除标准和质量评分；
- 角色识别与研究矩阵；
- 从模块生成到 structured intent、repository evolution、cross-stage
  closure 和 FPGA evidence 的递进式正文；
- Related Work 章节建议和定位句。

其主要问题不是结构薄弱，而是 authority、引用和执行状态没有稳定化：

- 文件仍声明 `paper1-freeze-v1.5`；
- 48 个 `cite` 和 9 个 `filecite` 是会话内引用；
- 检索截止写为 2026-08-27，但完整数据库执行记录主要截止到
  2026-07-17；
- v1.7 的 RQ1 primary/secondary hierarchy 尚未传播；
- 若干最新工作只有 identity-ready 状态，却在正文中承担数值性事实。

因此，该日志应作为**结构与候选主张来源**，不能直接作为当前可引用
综述正文。

## 2. 内容级 crosswalk

| 日志内容 | 当前判断 | v1.7 去向 | 理由 |
|---|---|---|---|
| 主题：“契约化 RTL 工程包生成、确定性工程物化与评测器隔离验证” | 保留 | 当前标题/定位主线 | 与 v1.7 RQ1/RQ2 一致 |
| 关键词本体：任务、方法、数据、评价、评测权限、FPGA 特性 | 保留 | 检索计划和 Related Work taxonomy | 覆盖 Paper-1 所需概念块 |
| Scopus/WoS/IEEE/ACM/arXiv/Scholar/CNKI 查询式 | 保留为计划 | search-plan 表，状态 `待执行` | 查询式存在不等于平台已执行 |
| 纳排标准、质量评分、重复版本规则 | 保留并收紧 | future execution contract | 必须绑定实际筛选记录和 canonical ID |
| “模块代码不等于工程交付” | 保留 | current summary §2.1 | 有 VerilogEval/RTLLM/RTLCoder 等支持 |
| “公开反馈收益需要独立终态评价” | 保留为研究动机 | current summary §2.2 | AutoChip/RTLFixer/VerilogCoder/HORIZON 支持问题动机；SR2FPGA 效果未建立 |
| structured plan/IR/intent 可降低直接 RTL 耦合 | 改写 | current summary §2.3 | 只能说其将决策显式化；不能预设提高 SR2FPGA 成功率 |
| repository repair/evolution 与 new-project construction 不同 | 保留 | current summary §2.4 | 与 RTL-Repo/Phoenix/CktEvo/HORIZON 对照一致 |
| CVDP/RealBench/ChipBench/ChipVerilog 扩大真实任务 | 分层使用 | CVDP 为 source-verified；其余按 registry 状态 | 不同工作证据链完整度不同 |
| CLOSER-Bench 支持跨阶段 closure | 身份级保留 | identity-level 背景 | 当前无本地 primary PDF/page anchors |
| ResBench 支持 resource-aware FPGA evaluation | 保留 | current summary §2.6 | claim-ready，但不能外推 P&R/board |
| HINT 是 closest executable-intent neighbor | 保留并加强 | current positioning §2.6 | 本地 v2 PDF 已 source-verified；必须说明 ASIC synthesis 与 route-level bundle |
| “现有文献尚未……”的全称 gap | 改写 | “在已执行检索范围与截止日期内未发现……” | saturation 未关闭，不能使用领域全称 |
| M3/M4 共享 HIS、比较 free vs skeleton | 保留 | v1.7 RQ1 | `M4-M3` 是 primary bundle，不是 skeleton-only effect |
| `M3-M2` 与两个 primary 并列 | 弃用 | mandatory secondary | v1.7 已更改 confirmatory hierarchy |
| OpenXC7 L4 作为论文结果支柱 | 收窄 | RQ4 bounded characterization | target-profile extension 可选；无一般 L4/L5 结论 |
| 文献数量或组件清单证明创新 | 弃用 | 结果条件化 claim rules | 创新强度必须由 official comparisons 和 gates 决定 |

## 3. 段落级映射

| 历史日志段落 | 当前稿位置 | 处理方式 |
|---|---|---|
| 858–862：从代码生成到模块 benchmark | `literature-summary-v1.7.md` §2.1 | 压缩；只保留 registry-backed 事实 |
| 864：tool feedback | §2.2 | 保留 public repair 动机；移除未稳定 cite tokens |
| 866：structured representation | §2.3 | 加入 HINT source-verified 边界，强调 bundle |
| 868：真实任务 benchmark | §2.5 | CVDP 可用；RealBench/ChipBench/ChipVerilog 降级 |
| 870–872：repository work 与 HORIZON | §2.4 | 保留任务边界、成本和 evaluator-risk 论证 |
| 874–876：cross-stage 与 FPGA | §2.6 | 保留 bounded endpoint；不把 ASIC/FPGA 混写 |
| 878–886：四个断裂与 SR2FPGA 定位 | §1、§3、§4 | 保留为候选 synthesis；gap 语言加检索范围限定 |
| 890–1011：Related Work 结构 | `m2-literature-positioning-v1.7.md` §2 | 基本保留；用 canonical keys 和证据层级替换工作清单 |

## 4. 四个交叉对比结论

### 4.1 任务单位

日志正确区分 module、existing repository 和 new project，但部分历史笔记
仍把 “repository/project-level” 作为统一类别。当前稿改为同时记录
starting state 与 artifact obligations，避免把代码补全、bug repair、PPA
evolution 和 requirement-to-project construction 合并比较。

### 4.2 表示层

日志已区分 structured plan、compiler IR、executable intent 和 project
contract，但早期总结仍倾向用“System-HIS 更高层”作为优势。当前稿不把
抽象层高低当作效果证据，只用 `M3-M2` 和 `M4-M3` 的冻结比较回答
representation bundle 与 materialization bundle 的价值。

### 4.3 Evaluator privilege

日志对 public-feedback adaptation 的风险判断是 Paper-1 最有价值的文献
synthesis。当前稿保留该问题，但将“评价创新成立”改为 prospective：只有
G3/G4b authority、official terminal artifacts 和 RQ2 outcome 完整后，才能
写 verifier-separation value。

### 4.4 FPGA endpoint

日志把 synthesis、P&R、timing、resource 和 target profile 纳入一条
物理证据线是正确的；但 HINT 的 SKY130 synthesis、ResBench 的 resource
evaluation、Chip-Chat 的人工物理案例和 SR2FPGA OpenXC7 L4 是不同证据。
当前稿将其分开，不使用“物理闭环”作为无条件总称。

## 5. 可直接复用的当前结构

当前 Related Work 建议维持五节：

1. Module-level RTL Generation and Benchmarks；
2. Tool Feedback, Repair, and Evaluator Privilege；
3. Structured Specifications, Hardware Intent, and Compiler-Mediated
   Generation；
4. Repository-Level Hardware Engineering and Cross-Stage Closure；
5. FPGA Resource Awareness and Bounded Physical Evidence。

最后单列 Positioning of SR2FPGA，使用以下比较轴：

`task unit | starting state | public facts | representation | deterministic
construction | artifacts | repair-visible evaluator | hidden final | physical
endpoint | denominator | cost/missingness | artifact availability`

## 6. 最终定位句

在当前本地、已执行检索和证据注册表范围内，SR2FPGA 的候选区别不是首次
生成 RTL、首次使用 typed intent、首次调用 EDA 或首次做 repository loop，
而是：在同一 requirement-to-project contract 和匹配权限/预算下，检验
deterministic materialization/edit-surface bundle 的增量，并将公开修复与
一次性隐藏终评、固定工程分母及有界 FPGA 物理端点组合进预声明实验。

该句定义研究位置，不预告实验结果，也不构成 “the first” 主张。

