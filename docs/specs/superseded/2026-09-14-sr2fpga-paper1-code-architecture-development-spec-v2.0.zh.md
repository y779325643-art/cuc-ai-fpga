# SR2FPGA Paper-1 代码架构与开发规范
## PC 2.0、确定性工程构建与 B4 受限修复

**规范版本：** `sr2fpga-paper1-code-dev-v2.0-draft`  
**日期：** 2026-09-14  
**规范类型：** 研究计划的下位实现设计规范；全新目标架构，不是当前仓库实现说明  
**研究依据：** `paper1-v2.1-draft` [R]，以及随后确定的 PC 2.0 clean-slate 设计 [P]  
**PC 格式：** `sr2fpga-pc-2.0`；模型输出为 design 对象，完整 PC 由受信控制器组装  
**输出对象：** FPGA Project Package（FPP），以及独立保存的执行与验证证据  
**核心方法：** M0–M5；主要比较为 M5−M1@B4 与 M4−M3@initial  
**兼容政策：** 新核心不兼容 System-HIS v1.2，不保留旧别名、旧 reader 或兼容 façade  
**实施状态：** 本次仅重写规范；未修改仓库、PC schema 或参考检查器，未执行模型、EDA 工具或正式实验

> 本稿完整替代旧代码架构 SPEC 的目标设计，而不是在旧 G0–G9/CD1–CD10 流程上继续追加补丁。沿用研究计划的科学问题、信息权限、预算和统计边界，采用后续 PC 2.0 的表示设计；包划分、运行接口、批量行为生成、事件恢复及构建细节是本次提出的实现方案。历史实现快照、原型测试结果和新系统验收分别记录，不能互相自动继承。

## 阅读导航

| 需要解决的问题 | 主要章节 |
|---|---|
| 总体责任与包依赖 | [§2 总体架构](#architecture)、§3–§5 |
| PC2 如何进入真实工程 | [§6 PC 检查](#pc2)、[§7 构建](#build)、[§8 批量行为与 FPP](#behavior) |
| 方法、共享和预算是否公平 | [§9 方法](#methods)、[§10 配对 DAG](#paired)、[§11 修复](#repair)、[§12 预算](#budget) |
| 如何防止自证、泄漏和重复评分 | §13–§14、[§15 评测](#evaluation)、§16 |
| 应用任务怎样落地 | [§17 任务与负载](#tasks) |
| 从哪里开始改代码 | [§20 工作包](#workpackages)、[§21 验收](#tests)、[§22 替换清单](#replacement)、附录 A–C |

---

<a id="a0"></a>
## 0. 依据、权威与版本边界

### 0.1 本稿使用的材料

| 编号 | 材料 | 本稿中的作用 |
|---|---|---|
| [A] | `2026-08-18-sr2fpga-paper1-code-architecture-development-spec.md`，`sr2fpga-paper1-code-dev-v1.12` | 原架构与历史实现线索；保留有价值的责任边界，不继承过时 gate、预算、统计与兼容要求 |
| [R] | `2026-09-14-sr2fpga-paper1-research-plan-v2.1.zh.md` | 科学问题、M0–M5、B4、独立评测、任务、统计与 WP0–WP6 的研究依据 |
| [P] | `PC-2.0-clean-slate-design.zh.md` | PC 职责、层次模块、类型化接口、参数、状态、绑定及构建边界 |
| [S] | `project-contract-2.0.schema.json` 与 `design-proposal-2.0.schema.json` | 当前交付的 PC 2.0 候选机器格式；本稿不暗中修改其中的字段 |
| [T] | PC 2.0 包中的参考检查器、示例及 `reports/conformance.json` | 局部原型与既有测试记录；不是生产环境、仓库集成或硬件正确性证据 |

材料的实际字节 SHA-256 见附录 D。本次没有读取当前 Git 仓库、`contracts/manifest.json` 或 `docs/current-status.md`，因此不声明这些文件已注册、某个模块当前缺失或某个家族今天已经通过 L4。

[A] 的页首写明上位计划 v2.1 已采纳，但 [R] 文件自身仍标记 draft。这里保留这一状态差异：本次按用户要求以 v2.1 和后续 PC 2.0 作为目标设计依据，不据此推导正式 campaign 已获批准或冻结。

### 0.2 两条权威链

**规范链：** 被采纳的研究计划及显式修订 → 本实现 SPEC → 与该版本一致的 contract、能力配置、实验 manifest 和分析实现。

**事实链：** 实际代码与受测版本 → 原始事件和工具产物 → 可重建的状态与结果报告。

实现与规范不一致时记录 `implementation_protocol_drift`。代码已经这样运行，不意味着研究规则可被改写；文档提出一个能力，也不意味着该能力已经实现。`contracts/manifest.json` 只证明实际注册的格式身份，不自行改变研究的比较、权限或分母。

### 0.3 三个版本分别管理

| 版本对象 | 本次依据／建议 | 不应混淆的内容 |
|---|---|---|
| 研究计划 | `paper1-v2.1-draft` + 后续 PC 2.0 设计决定 | 不因实现 SPEC 升版自动获得实验许可 |
| 代码架构 SPEC | `sr2fpga-paper1-code-dev-v2.0-draft` | 不等于运行时所有 artifact 都使用版本 2.0 |
| PC 格式 | `sr2fpga-pc-2.0` | 不等于研究计划版本，不与旧 `system-his-v1.2` 混写 |

[R] §3.1 仍保留 System-HIS v1.2 与兼容映射的表述；后续用户明确选择了无兼容的 PC 2.0。该变化在本稿中显式采用，并列为上位文档同步项：将逻辑 `requirement_binding / design_decisions / obligation_trace` 对应为 `bindings / design / design.requirement_map`，更新能力与 H-stage 映射说明。实际采纳时一并记录方法版本变更，不能只改 runtime 而沿用旧研究身份。

### 0.4 无兼容，不等于抹去历史

新入口拒绝旧 PC、未知版本和不符合新 contract 的数据；不建立自动转换、双写、fallback 或静默别名。可以复用经过重新审查的路径安全、工具封装和事件存储代码，但复用的是实现，不是旧协议通过信用。

旧规范、旧数据与旧测试报告归档或保留在版本历史中，不原地重标为 PC 2.0。旧 `training/` 等非本研究资产不因本稿而删除，也不再作为新核心依赖或测试前提。

### 0.5 规范词与状态词

“必须”表示本设计的必要条件；“应”表示默认取舍，偏离须在实施前记录理由及影响；“可”不改变研究边界。所有新增接口名、目录和 contract key 均为目标设计，除明确引用 [S]/[T] 的内容外，不声称仓库已存在。

实施跟踪采用 `planned / prototyped / integrated / verified_in_scope`，每个状态附版本与证据范围；研究结果另行记录。静态测试通过不能写成 RTL 已通过，工具集成测试通过不能写成正式研究假设成立。

---

## 1. 目标、范围和不可破坏的不变量

### 1.1 最小闭环

```text
冻结、可评分的公开需求与目标配置
  → 按 MethodPolicy 执行 Direct／Structured／PC 路径
  → 完整 FPP，或有原因的无候选终止
  → 预算内公开检查与修复
  → 唯一终止候选封存，或封存 terminal-null 结果
  → 独立隐藏语义提交及指定 L3 确认
  → 预声明位置的 L4 物理确认
  → 从原始事件重建结果、失败、缺失与成本
```

公开需求已经独立裁定 ready 的正式任务，不能在方法运行时重新消歧、换 family 或补充新假设。产品侧的原始需求入口可以停止并返回澄清／能力不足，但其完整 A_req 审计不属于核心前置链。[R, §§1, 6, 12]

### 1.2 研究范围固定

| 内容 | 本架构地位 |
|---|---|
| M0–M5、PC 2.0、受信结构构建、受限修复 | 核心 |
| M5−M1@B4、M4−M3@initial | 一个主要 Holm 比较族 |
| 修复增量、自然失败 probe、跨模型复核 | 按研究计划预声明的次级分析，不增加主要假设 |
| 代表性 L4 | 必须形成有限范围的结果或明确失败证据；不要求全部成功 |
| 视觉／Q-table 案例 | 预结果决定是否纳入，独立描述性分组；不增加核心四家族分母 |
| A_req、EA、目标适配、公共 IP 深度集成 | 默认关闭，独立协议启用 |
| 生成模型训练、SFT、蒸馏、学习型 QoR、完整 SoC、L5 | 不属于最小 Paper-1；不创建对应核心执行路径 |

### 1.3 十项不变量

1. **同一公开事实。** 所有方法获得相同需求、接口 ABI、配置、公开资产及适用规则；不向 PC 方法额外提供参考架构或 oracle PC。
2. **一个设计权威。** PC2 的 `design` 是该 PC 方法的架构权威；展开图、ABI 和构建计划是派生对象，不可独立编辑。
3. **职责隔离。** 模型提出设计和行为；控制器绑定需求并授权动作；工具和评测器给出证据。
4. **首发真实。** 一个声明模型阶段最多一次逻辑调用；多个行为模块不能偷偷变成多次首发调用。
5. **共享包含失败。** 共享 PC／工程失败也属于共同起点，保留诊断、原始响应及已消耗预算。
6. **预算不重置。** 改 PC、重新构建、补代码、解析纠正与修复均消耗该方法同一总预算。
7. **标准不由候选决定。** Candidate TB、`TEST_PASS`、模型自报 pass 或 QoR 预测不能签发 VPP。
8. **隐藏不可回流。** 终止后隐藏结果不进入当前、其他方法、其他任务、案例或人工调参路径。
9. **失败和未知不同。** 设计失败留在分母；基础设施未知保留 NA；实际完整性破坏单独处理。
10. **历史不晋升。** 原型、参考、开发、pilot、核心、案例和扩展都有独立身份，不把前者重标为后者。

---

<a id="architecture"></a>
## 2. 总体架构：模块化单体控制，独立评测进程

### 2.1 组织方式

默认实现为一个本地可运行的模块化控制程序，加上受权限隔离的工具／评测 worker。先支持单协调器、有限并发或串行队列和文件存储；不引入分布式消息总线、微服务集群、复杂 ORM 或多 Agent 自由协商。

```text
                    研究负责人 / 受控批准记录
                               │
公开需求 / profiles ──→ CampaignPreflight ──→ FrozenRunContext
                               │
                      PairedBlockCoordinator
                               │
                  MethodPolicy + EpisodeExecutor
                   ┌───────────┼───────────────┐
                   │           │               │
               Direct       Structured      PC Planner
                   │           │               │
                   │        Free FPP       PC Validator
                   │                           │
                   │                 ┌─────────┴─────────┐
                   │                 │                   │
                   │              Free FPP       Structure Builder
                   │                 │                   │
                   │                 │          Batched Behavior Fill
                   └─────────────────┴───────────────────┘
                                      │
                             Candidate Committer
                                      │
                          独立 Public Evaluation Worker
                                      │ 公开诊断
                        有限 Repair Controller ──→ 新候选
                                      │
                              Terminal Selector
                                      │
                    Batch Seal Barrier / 无候选槽闭合
                                      │
                           独立 Hidden Evaluation Worker
                                      │ analysis-only outcome
                           L3 / 固定子集 L4 Worker
                                      │
                            离线 Outcome / Cost Reducers
```

图中回路只有 public diagnosis → repair；不存在 hidden/L4 → generation。工具可以在公开检查周期执行 L3；最终确认可复用同一候选与配置的有效证据，不强制免费或重复跑一次。

### 2.2 进程权限不是 Python 包名

| 执行域 | 可读内容 | 可写内容 | 禁止能力 |
|---|---|---|---|
| 生成／修复域 | 等价公开投影、自己的 PC/FPP、已批准公开诊断 | 模型响应与候选提议区 | 隐藏数据、oracle、任意仓库、评测目录、密钥文件 |
| 受信控制域 | 公开配置、方法与预算、事件、候选封存信息 | 绑定、构建产物、状态与事件 | 根据隐藏语义结果继续生成 |
| public worker | 候选快照、固定公开 harness 和工具 | 原始公开工具证据、受控诊断 | 修改需求、候选或隐藏 suite |
| hidden worker | 封存候选、私有 suite 与独立 oracle | 私有原始证据、analysis-only 结果 | 调用模型、修复、替换候选 |
| physical worker | 固定合格候选、目标配置与工具 | L4 报告及成本 | 反馈给核心修复或修改源工程 |
| offline analysis | 完整冻结分母、事件、合法结果投影 | 派生表格、统计与声明记录 | 模型调用、候选变更、重新选择终止工程 |

同一用户账户下“放在不同目录”不自动构成隔离。需要使用实际受控挂载、子进程权限或适合环境的沙箱方案，并验证不可访问路径。开发环境若只验证了部分边界，应按真实范围记录，不称生产安全。

---

## 3. Repository 与包职责

### 3.1 目标目录

以下是建议的目标布局。按工作包创建有实际实现的模块，不一次性建立空目录。保留 `agent/src/sr2fpga_agent/` 作为仓库组织位置，不保留旧运行语义或兼容入口。

```text
contracts/
  manifest.json                       # 活动 contract 身份与内容哈希
  pc/2.0/
    project-contract-2.0.schema.json
    design-proposal-2.0.schema.json
  runtime/                            # 新运行边界真正需要的 contracts
  task-catalog/                       # 任务目录单一入口，非模型 recipe 库

agent/src/sr2fpga_agent/
  core/                               # 纯类型、JSON/哈希、contract reader、诊断
  requirements/                       # 公开对象验证与只读投影
  pc/                                 # PC2 解析、绑定、类型、展开与报告
  build/                              # ABI、结构 emitter、行为装配、FPP
  methods/                            # M0–M5 策略与提示输入投影
  execution/                          # DAG、状态机、修复、终止与恢复
  gateway/                            # provider-neutral 请求、响应、计量
  accounting/                         # 预算预留、事件、三种成本视图
  storage/                            # 不可变 blobs、快照、journal
  workers/                            # public / hidden / physical 独立入口
  analysis/                           # 无生成权限的离线 reducer
  cli.py                              # 只解析命令并调用用例，不拥有方法语义

agent/tests/
  unit/
  contract/
  integration/
  tools/
  isolation/
  recovery/

artifacts/                            # 实际位置由配置确定，默认不提交大产物
reports/                              # 经选择发布的文档／结果，不作为可编辑运行事实
```

### 3.2 依赖方向

`core` 不导入模型 SDK、EDA runtime、训练库或应用 oracle。`pc` 与 `build` 只依赖纯核心和受信公开对象，不导入 task family generator。`methods` 不获得 worker 私有存储句柄。`execution` 调用受控 worker client，不通过 import 读取隐藏语义对象。

worker 可以共享纯 contract／FPP reader，但不能复用候选实现生成期望答案。`analysis` 不回调 `execution`。不要求创建独立 Python distribution 才有这些边界；先用包依赖测试和进程权限落实。

现有 `training/`、旧 release exporter、旧开发工具保留为独立资产；新 Paper-1 启动、安装和核心 CI 不导入或要求它们。删除或改造这些非核心资产不属于本次默认变更。

### 3.3 接入现有代码的原则

允许提取可用纯函数，但新 `cli → execution → methods/build/workers` 只能有一条活动路径。不能让新 API 最后委托一个仍可路由旧 HIS、执行隐藏修复或隐含重试的旧总控。旧代码可以归档；复用时用新合同测试其行为，而非只更名为 PC2。

---

## 4. 最小逻辑对象与所有权

### 4.1 对象清单

| 对象 | 权威生产者 | 主要内容 | 不得承担的责任 |
|---|---|---|---|
| PublicTaskContext | 任务裁定／受信 loader | 需求字节、公开边界、fact、假设、资产、适用阶段 | 模型动态改任务、私有 split 或答案 |
| RunPolicy / CampaignManifest | 研究配置与独立核验 | 方法、分母、预算、模型、工具、suite 承诺和分析 | 写入 PC 或向模型泄漏私有评测 |
| DesignProposal | LLM | 直接为 `entry/modules/requirement_map/notes?` | 自填完整 bindings 或通过状态 |
| ProjectContract | 受信 binder | `schema_version + bindings + design` | 文件实存证明、评测结果、授权 |
| PcCheckReport | 检查器 | 适用规则、范围、诊断、deferred_checks | 功能正确性证明 |
| BuildPlan / AbiMap | 受信构建器 | 派生实例、特化、物理端口、布局及行为单元 | 独立修改设计或注入算法 |
| BehaviorBundle / ProjectProposal | LLM | 批量行为内容或 Direct 完整文件提议 | 自定义 edit 权限或执行脚本 |
| FPP / CandidateEnvelope | committer | 实际文件、声明依赖、来源、哈希与受保护边界 | 以候选 TB 自证 |
| SharedCheckpoint | coordinator | 共享成功／失败对象及事件依赖 | 删除失败或免费计算 |
| TerminalRecord | selector / sealer | 唯一候选引用或明确无候选结局 | 依据隐藏结果选择版本 |
| Event / EvaluationOutcome | 相应控制器或 worker | 真实动作、状态、成本、已验证范围 | 模型自报或手工修改结果 |

这是逻辑清单，不要求一对象一 schema、一对象一文件。事件可用一个带判别字段的 contract；阶段报告可以复用一类范围明确的结果结构。详见 §18。

### 4.2 身份与哈希

至少保留 `campaign_id`、`population_id`、`semantic_instance_id`、`replicate_id`、`condition_id`、`paired_block_id`、`action_id`、`candidate_id`。`condition_id` 在核心映射到 M0–M5；probe／第二模型／案例使用冻结的独立条件与人口身份，不能与核心槽碰撞。

模型版本、目标与预算是冻结条件的属性，不由模型返回值决定样本身份。`replicate_id` 不等于 provider seed；调度 seed 与请求 seed 分开。

内容引用使用 `id + sha256`，hash 以存储的实际字节为准。结构化对象首次序列化采用固定编码；原始模型响应保留原字节，不把语义等价 JSON 宣称为字节相同。候选摘要由排序后的文件记录及其角色等受控字段生成，不包含摘要自身。

Hash 提供一致性检查，不等于签名、授权或防止所有参与方同时篡改。实际权限、受控批准记录与审计域分别负责这些问题。

### 4.3 单一状态权威

配置和原始事件是事实；`run_status`、trajectory、cost summary、VPP 表和 current-status 是派生视图。不能要求多个手工维护的 JSON 同时自称权威。模型输出中的 `authorized`、`owner`、`verified`、`pass` 等字段没有对应权限，未知字段应拒绝或作为非规范文本隔离。

---

## 5. 公开需求、目标与能力配置

### 5.1 正式入口只装载 ready 投影

正式核心从已冻结的 PublicTaskContext 运行，不执行自动 family 匹配、动态澄清或重新裁定。loader 先验证来源、版本、必需事实、资产身份和目标一致性，再分派方法。

开发入口可以接受原始需求并形成 ready／needs_clarification／capability_gap；非 ready 时不创建模型调用、候选或 EDA 任务。需要完整需求理解研究时启用独立 A_req，不把它混入核心分母。

### 5.2 适配 PC2 原型，而不创造并行需求权威

[P]/[T] 的示例 public 对象含 `boundary`、`facts`、`required_trace_facts`、`public_assets`；示例 target 与 capability 是参考输入，不是已注册生产格式。

实施时从仓库已裁定的公开对象生成只读检查视图，记录 adapter 版本和源字节引用。若现有对象无法表达必要信息，应显式升级该公共对象；不能为 PC2 另复制一套可独立编辑的需求数据库。

`bindings` 绑定正式公开源对象的实际内容身份，检查器同时验证“源对象 → 受信视图”的确定关系。视图缓存若持久化，必须可删除重建，不能自行替换源 hash。不得从模型提供的 expected bindings 验证模型自己。

### 5.3 外部 ABI 对各方法等价公开

冻结需求给出实际 RTL top 名称、可观测端口、位宽／符号／时钟复位和参数配置；逻辑接口展开规范或已冻结的外部 ABI 表也向 Direct／Structured 方法提供。只提供同样文本长度不等于信息等价。

PC2 入口模块使用 `signature.source=requirement_boundary`，内部模块使用 `declared`。公共 ABI 的给出不是为所有方法自动生成 RTL top；M0–M3 仍自由生成自己的工程，M4/M5 才使用受信结构构建。

### 5.4 fact 和资产

每条 fact 区分来源、guarantee／assumption／preference 等角色、适用条件和验证阶段。PC 的 numeric／timing 承诺只能引用已存在的事实与假设，不能产生更弱环境。

公共系数、权重、初始化数据是所有方法等价可用的输入，绑定原始字节、格式、布局和许可信息。隐藏回放图像、特定测试输入及期望输出不属于 public_assets，不能挂入候选目录。仅声明 asset ID 还不证明实际文件正确使用；构建与工具阶段必须验证可用字节和解析规则。

### 5.5 需求能力不足与模型决策越界

正式 task 的能力域资格在结果前检查。某个已 ready 任务中，模型选用当前能力配置不支持的协议、reset 或结构，是该候选的 PC/H 阶段设计失败，不能回写任务为 capability_gap 并移出分母。

若发现裁定本身有错误或整个固定目标确实无法运行，作为协议／基础设施问题记录并按预声明规则处理；不能用模型输出选择性重新裁定任务。

---

<a id="pc2"></a>
## 6. PC 2.0 检查与 H-stage 对齐

### 6.1 两份 schema，一个设计定义

完整 PC 固定为：

```text
schema_version: sr2fpga-pc-2.0
bindings:
  requirements: {id, sha256}
  target_profile: {id, sha256}
  capability_profile: {id, sha256}
design:
  entry
  modules
  requirement_map
  notes?                         # 非规范性
```

`design-proposal-2.0.schema.json` 的根直接引用 design 定义；模型响应不要再包一层 `design`，也不输出 bindings。binder 接收通过解析的 DesignProposal 与受信上下文，组装完整 PC，再用完整 schema 校验。

两份 schema 的设计定义必须来自同一生成源或在 CI 中核对语义一致；不允许分别手改后漂移。本次不改 [S] 已交付字节，生产注册须明确 id、版本、哈希与引用解析规则。

### 6.2 解析与有限表达式

重复 JSON key、PC 中浮点／非有限字面值、超出限制的大小或深度必须拒绝。该规则作用于 PC／DesignProposal；不能错误地扩展到成本报告、时间测量或允许小数的其他 contract。

参数只使用 [P]/[S] 的非负整数与有限 AST，所有形状参数显式赋值。检查未绑定参数、除零、负中间结果、超界与零位宽。禁止 eval、任意 HDL 表达式和模型自报 `resolved`。实际展开配置通过，不代表所有参数组合均被证明。

### 6.3 新的版本化映射，不沿用旧 W-rule 信用

本表为本次实现映射提案，建议注册为独立 `pc2-validation-policy` 版本；旧 H0–H3 名称只作报告层次，不继承旧 W1–W10 覆盖或 dry-lower 副作用。[A, §12; P, §12]

| 检查步骤 | 责任 | 允许输出 | 明确不做 |
|---|---|---|---|
| 输入解析／绑定核验 | 严格 JSON、受信来源及 binder 完整性 | 原始错误与来源结果 | 将控制器错误算作模型错误 |
| H0 | DesignProposal 与完整 PC 的 schema | 形状、枚举、字段错误 | RTL 或参数域完备证明 |
| H1 | 引用、可达性、参数与类型展开、域、方向和驱动关系 | JSON Pointer／实例路径、机械诊断 | 理解任意自然语言算法 |
| H2 | 冻结 capability 对所选实现的支持、资源化展开边界 | 支持／不支持及具体限制 | 发射 RTL skeleton、运行 M4 filler 或成功试综合后筛 PC |
| H3 | requirement binding、允许 fact role、关联覆盖及已定义可比较值 | fact／目标引用与局部一致性 | 将 trace coverage 称为完整语义 fidelity |

纯实例展开可由 H1/H2 共用一次确定性结果；适用的后续层在前层失败后标为 `not_run`。H3 某些可执行规则尚不存在时应在范围中列明 deferred checks，不能虚报“全部需求通过”。

M3/M4/M5 消费同一共同 PC 检查起点。H2 不得通过“先成功生成 M4 skeleton”获得准入资格；M3 必须能完全不调用 structure emitter。实际构建器自身异常与 PC 合法性分开记录。

### 6.4 类型、层次与连接的核心规则

| 面 | 必须落实的规则 |
|---|---|
| 层次 | 模块定义按 ID 索引；实例只属于 structural 模块；所有定义从入口可达；定义递归拒绝 |
| 端点 | `self` 或当前模块的直接子实例，不允许任意跨层字符串路径 |
| 类型 | bits/uint/sint/fixed/record 严格匹配；record 字段顺序、符号、小数位均有意义 |
| record 布局 | 第一字段最低有效位，偏移按前序字段宽度累加；不可依赖 object key 顺序 |
| value 连接 | 一个源可多个 sinks；每个接收端恰好一个合法源，显式 unused_values |
| stream 连接 | `ready_valid_v1` 点对点，不隐式广播、丢弃、加缓存或改变流控 |
| 域 | 子域显式绑定，组合模块可无实际时钟／reset；禁止按名字猜测或暗加 CDC |
| 状态 | behavioral 模块中的架构状态局部归属；register/memory/fifo 语义按 PC2 核心 |

不能从 `clocked` 推断无组合环，也不能由 PC 合法推出无握手死锁。这些需要生成后结构、仿真或适用形式检查。示例 capability 的 none/sync、单域范围不是所有 FPGA 平台的通用能力，扩展 async／多时钟前须新增实现与资格证据。

### 6.5 报告与错误来源

PcCheckReport 至少绑定 PC、公开上下文、schema、checker、能力配置的哈希，以及逐层 `pass/fail/not_run/not_applicable`、规则 ID、诊断位置和 deferred_checks。

错误来源分为 `candidate_design`、`trusted_implementation`、`infrastructure`、`integrity`。引用不存在的模块是候选错误；受信需求加载失败或构建器崩溃不能统称“模型生成失败”。绑定被实际篡改是完整性事件，不能由候选自填字段宣布恢复。

---

<a id="build"></a>
## 7. 确定性工程构建

### 7.1 构建链与派生对象

```text
CheckedPC + Public ABI + Target/Capability
  → ResolvedDesign（参数、类型、域的具体化）
  → BuildPlan（实例、特化、文件角色、行为单元）
  → AbiMap（逻辑端口到实际 HDL 信号）
  → 结构源码与受保护行为签名
  → 行为装配 → FPP
```

上述对象只由绑定的源输入派生。它们可缓存和检查，但不成为模型可修改的第二份 PC。build 不导入 family catalog 的答案生成器，不根据任务名称选择 FIFO、Sobel、Q-learning 等行为模板。

### 7.2 参数特化与命名

首版对本次任务实际参数配置展开，可为每个不同的模块定义／参数／ABI 组合产生稳定 `unit_id`。相同组合复用同一行为实现，但实例状态仍独立；不因为实例名字不同就重复请求模型。

物理名字和路径由受信规则产生，处理保留字、长度、大小写与碰撞，不把 PC identifier 直接当文件路径。unit 身份须包含定义和相关类型／域特征，不能仅用模块名缓存。时钟管脚名字差异由实例绑定承担，不应混淆域身份。

入口 top 名称与外部 ABI 来自任务。参数化通用库输出不是首版要求；只生成本配置特化工程时，结果声明限于该配置。编译器版本、排序、命名、打包规则必须固定，不依赖文件系统枚举或进程随机 hash。

### 7.3 构建器的允许范围

允许生成模块头、端口与参数声明、结构实例、连线、显式常量、record 打包／解包、stream 信号展开、源文件清单及声明式构建元数据。

stream 的 payload/valid 随逻辑 source→sink，ready 反向；对 self/child 按层次重新计算 HDL input/output。record 拼接必须符合 LSB-first 规则，带宽、字段顺序及 signedness 有独立测试。

不允许自动插入 FIFO、仲裁、fork/join、流水级、截断、舍入、同步器、算法核或 reset 控制。state 描述是行为义务，不授权构建器直接生成该家族的答案。确需行为适配，应由 PC 显式模块表达并由模型实现；公共行为 IP 要另有方法等价协议。

### 7.4 ABI 和目标约束

内部端口可以使用确定性的展开命名；外部 ABI 必须与任务一致。协议仅为 ready_valid_v1 时不能导出“完整 AXI 兼容”标签。公开任务必须使用 AXI Video 子集时，接口映射与协议语义在结果前明确并核验，不能靠改字符串绕过能力检查。

SDC/XDC 等实际工具约束由受控 target profile 和固定 launcher 生成／选用。候选只能引用适用配置，不能修改时钟、false path 或资源硬界限。不同工具的约束生成器必须分别资格验证，不从同名文件推导等价时序语义。

### 7.5 结构保证与限制

构建与检查应支持以下有限不变量：合法 PC 的受保护接口、实例、参数和网络按规定生成；有效行为装配不会修改这些结构；相同源输入与构建配置产生确定的结构产物。

这不保证算法、时序承诺、状态更新或数值正确；PC 本身可能做出错误实现决策。单个 root behavioral 也是合法 PC：若任务没有公开要求内部模块化，不能仅因缺少多模块而判失败；若大量模型选择此路径，应如实报告构建干预的实际覆盖，而不是偷偷强迫拓扑。

---

<a id="behavior"></a>
## 8. 批量行为生成、装配与 FPP 边界

### 8.1 一次调用生成全部行为单元

M4 的第二模型阶段定义为 **BatchedBehaviorFill**：一次逻辑模型调用返回该工程所有待实现行为单元。不得为每个叶模块新建一个生成 Agent、单独模型请求或隐藏重试。

输入包含公开需求、完整 PC、该候选的 ABI／行为单元清单、受保护签名和允许语法。输出建议采用一个严格 BehaviorBundle，按 `unit_id` 索引，每项是 **module body 文本**；模块头、模块名、端口与结尾由 composer 提供。此输出 contract 属于本次新增实施要求，不是 [S] 中已经定义的 PC 字段。

```text
BehaviorBundle
  schema_version
  build_plan_sha256
  units: { unit_id: { body: string } }
```

所有 required unit 必须恰好出现一次，未知单元拒绝；同一特化被多个实例复用时只填一次。缺少单元、响应截断或 bundle 格式错误保留原始提议，不能自动补空模块或给缺失单元免费再调用一次。M5 可在剩余预算内补全；M4 记录初始失败。

如果合法 PC 完全没有行为单元，例如仅包含允许的纯接线，跳过该模型调用并记录 `not_applicable(no_behavior_units)`；不为了凑两次调用而请求空输出。主策略规定的是每个声明阶段最多一次，不是每条路径必须消耗相同调用数。

### 8.2 批量输出太大时怎么办

在开发阶段测量上下文和单次输出容量，调整公开能力范围、模型和案例预算；所有比较方法的等价上限在 pilot 前冻结。正式任务不能因 M4 的模块多而临时分成多调用，也不能静默删行为单元或从其他候选取现成实现。

确需逐模块生成时，应当作为新的方法／预算协议单独设计，不能仍按本版 M4 两阶段首发和 B4 计分。Prompt 展开所用全部签名、源码和日志都计入真实输入 token，不将多段上下文视为免费工具消息。

### 8.3 源码与受保护结构检查

首版采用一个能力明确的可综合 SystemVerilog 子集；确切 parser、elaborator 和工具版本在实施资格中固定，而不是本稿虚构已安装工具。

composer 将 body 放入受信模块上下文后，使用真实解析／展开检查：恰好生成目标模块；受保护端口、域、参数及模块关系未变；没有跨单元预处理逃逸、额外模块、未声明依赖或访问评测器层次的引用。

不能用注释哨兵、字符串替换或正则对比代替解析。默认禁止由模型加入改变其他文件语义的宏、任意 include、DPI/FFI、外部系统调用和任意子模块实例；局部函数、局部常量、实现寄存器与允许的生成语法可以由能力配置明确开放。确需新的子模块，应先修改 PC，而不是藏在行为 body 中。

模型可以采用不同内部算法和状态编码，但仍承担公开数值／时序／协议义务。PC 中的架构状态不要求逐一对应物理寄存器名称，实际状态符合性不能只靠名字检查。

### 8.4 完整、可解析、正确是不同状态

完整的文件集合不等于语法正确；语法正确不等于公共测试通过。Direct 工程可具有完整 manifest 但在 L1 失败。M4 的 body 语法错误若导致无法证明装配边界，应保留可修复的提议与诊断，不能假装已产生可封存的边界有效 FPP。

分类必须依据具体阶段：格式／缺文件是 project proposal failure；被检查器拒绝的结构越界是无效候选尝试；实际受信文件已被修改才是完整性事件。方法特有边界检查结果独立记录，不把 Direct 因“不含 PC 或 build_plan”直接判 common L0 失败。

### 8.5 方法中立的 FPP

共同交付至少包括声明式 manifest、全部实际 RTL 源、top 与外部接口、文件依赖、语言／参数构建信息、适用约束引用及必需公开初始化资产。允许模型选择安全的源路径，不强制 Direct 的 top 文件固定为 `rtl/top.sv`。

PC、H 报告、候选 testbench、预测 QoR 和内部构建计划不是 M0/M1/M2 的共同必需文件。候选脚本仅可作为隔离的说明性附件，不能成为 worker 执行入口。TB 即使交付，也不自动进入 evaluator 的可信源列表。

CandidateManifest 只表达候选构建意图。外部 CandidateEnvelope 由 committer 产生，至少包含文件角色、实际 byte hash、来源、受保护区域／单元、适用方法政策、关联 PC/build plan 和 creation event。模型自填 ownership 不可信。

### 8.6 来源映射

`construction_origin_map` 至少区分公开边界、受信结构、模型行为、已声明公共资产和独立平台。M4/M5 组合源码可以标为 composite，并关联可信头部与模型 body 的原始 artifact，而不是给整文件单一虚假来源。

Direct 的共同安全封装不能自动帮它接线或补算法；M4 的受保护结构也不能自动获得功能分数。发布时可说明生成负担和结构责任，但代码行数不等于设计问题的难度或已解决义务数量。

---

<a id="methods"></a>
## 9. M0–M5 执行策略与模型网关

### 9.1 唯一方法表

| 方法 | 初始模型阶段 | 共同 PC 检查 | 结构构建器 | 后续模型动作 | 主报告终点 |
|---|---|---|---|---|---|
| M0 Direct | 1 次完整 ProjectProposal | 不适用 | 禁止 | 无 | @initial |
| M1 Direct-Repair | 共享 Direct 初始尝试 | 不适用 | 禁止 | 完整工程纠正／修复，受总 B4 限制 | @B4 |
| M2 Structured-Direct | 1 次无类型计划 + 1 次自由工程生成 | 不适用 | 禁止 | 无 | @initial |
| M3 PC-Free | 共享 1 次 PC 规划 + 1 次自由工程生成 | 适用，共同起点 | 禁止 | 无 | @initial |
| M4 PC-Skeleton | 共享 PC + 1 次批量行为填充 | 适用，共同起点 | 必须使用 | 无外层修复 | @initial |
| M5 PC-Online | 共享 M4 初始 checkpoint | 适用 | 适用 | design 修正／行为修复，受总 B4 限制 | @B4 |

M2 的计划只定义 generic container，例如 summary、file_plan 和 implementation_notes；不能引入 PC 类型规则、能力语义检查或 skeleton。M3 可接收完整 PC 与所有等价公开事实，但不消费 M4 的结构源码、行为空洞、成功构建报告或参考实现。

M3/M4 第二阶段各一次调用，不按模块数增加。M1/M5 的 @initial 由共享 M0/M4 初态描述；不额外运行一次名为“首发”的采样，也不为了补曲线对每个中间候选评分。

### 9.2 ModelGateway 只做传输，不拥有研究策略

模型、provider、wire API、量化与解码配置属于 provenance；不能由 source 类名决定方法、修复权限或 EDA 路径。冻结请求中的全部有效配置，记录请求、返回模型身份／fingerprint（若可用）、usage、停止原因和错误。

网关不得自动修 JSON、补文件、改需求、切换模型、提升 token 上限或 best-of-N。一个可消费的新模型完成结果是一次逻辑调用；parser/schema corrective prompt 也是新调用。默认关闭 SDK 内部隐式重试，或接入可完整观测且已冻结的 transport policy。

若使用结构化输出或受限解码，只能在方法政策中明确注册；不是因为某 provider 支持就对 PC 方法临时启用。未冻结该处理时，schema 仅作输出验证，不隐含 logit masking 或格式修复。

### 9.3 模型上下文与选择

同一对照块共享冻结模型／推理配置，方法会话相互隔离，不传递其他分支的修复成果。共享 artifact 的必要规划上下文可以受控复制，其内容进入信息记录。缓存不允许跨任务复用生成答案；provider 的计费缓存与方法答案缓存分开记录。

`documented_seed_control` 与 `stochastic_blocked` 按研究计划择一冻结。前者需要实际提供方机制与资格依据；后者不因缺 seed 而自动不合格，但不允许同随机流、确定重放或 bitwise-reproducibility 声明。单次或数次输出相同不证明 seed 机制。

未知 API 行为不能靠默认推断。实际集成时核验所选接口文档及请求响应测试，参数不支持时明确报错或选择已冻结的另一协议版本，不静默忽略。

---

<a id="paired"></a>
## 10. 共享起点、依赖调度与三种成本视图

### 10.1 共享 DAG

以下节点身份属于块而不是某个方法的私有执行顺序：

```text
S_D：一次 Direct 生成 ──────────────────→ M0、M1

S_C：一次 PC 规划 + 共同 PC 检查 ────────→ M3 的自由生成
                  │
                  └→ S_B：结构构建 + 批量行为填充 ─→ M4、M5

U_P：M2 无类型计划 ─→ U_F：M2 自由生成
```

S_C 即共享完整 PC 或其失败尝试；S_B 是完整的 behavior-filled 初始工程或相应失败，不是仅有空 skeleton。M4/M5 共享同一内容引用，不能分别请求模型填充。每个方法仍有独立结果行、终止槽和后续事件。

### 10.2 成功与失败共同记录

SharedCheckpoint 使用研究计划的三类状态：

| kind | 必需事实 | 消费者处理 |
|---|---|---|
| `pc_failure_checkpoint` | 原始 proposal、可解析 PC（若有）、检查诊断与前置事件 | M3/M4 初态失败；M5 可在余量内改 design |
| `project_failure_checkpoint` | 输入、有效 PC（适用时）、输出提议、缺失／错误与前置事件 | M0/M4 初态失败；M1/M5 仍按余量处理 |
| `project_checkpoint` | 不可变完整 FPP、envelope、PC/build 身份（适用时） | 消费公共检查并按方法权限继续 |

有效 S_C 尚未生成工程时是规划节点产物，不伪装为 `project_checkpoint`。后续 skipped S_B 记录 dependency_blocked 及原因，不产生虚假模型事件或免费空工程。共享前置基础设施失败不冒充普通 PC design failure。

### 10.3 调度

先由纯函数生成共享依赖、消费者与预算归因，再从可执行节点中按冻结调度策略选择。建议以本地 seed 为同层 ready nodes 生成稳定随机优先级，并在块间平衡可平衡的位置；执行器记录计划顺序和真实时间窗。

不再使用旧版“任意 M0–M5 六方法 Williams 行就等于所有调用均平衡”的假设。共享前置步骤与方法阶段必须服从 DAG；不可能完全平衡的位置明确说明。精确优先级／分块规则须在 pilot 前固定，不能看方法成功后调顺序。

默认先实现串行执行。若以后并行，预算预留和事件写入必须保持原子性；同时记录排队、服务与端到端耗时，不能把并行服务时间之和称为真实独立部署 wall-clock。

### 10.4 调用上限与实际归因

在全部初始阶段都可执行时：

| 视图 | 初始阶段 | M1/M5 追加阶段 | 每完整块上限 |
|---|---:|---:|---:|
| 实际去重逻辑调用 | 6 | 最多 3 + 2 | 11 |
| 六方法独立运行归因 | 1+1+2+2+2+2=10 | 最多 3 + 2 | 15 |

PC 提前失败会改变后续阶段分配，M5 的纠正也可能最多剩三次，但相应未运行的初始行为调用必须扣除；完整 DAG 的总上限仍按方法总预算推导，不能在失败路径给各阶段分别追加额度。

正式规划 360 块对应最多 3,960 个实际去重逻辑调用、5,400 个独立归因调用；这是 [R] 的规划上限，不是请求数、已运行结果或付费额度。probe、第二模型、案例与 transport attempts 另列。

### 10.5 三种成本计算

每个原始事件只发生一次；实际视图对事件 ID 去重。独立运行视图对每个方法取其完整依赖闭包，计入全部必要前置事件，不把共享成本摊薄或只记给最先运行的方法。增量视图从预声明共同 checkpoint 起计算，明确截止点。

共享 raw public 检查可以在候选、公开 suite、工具与环境完全相同且政策允许时复用，但每个消费者仍扣除等价检查机会并归因相应独立成本。方法专属 envelope／保护检查分别执行。hidden 不跨条件缓存分数；每个冻结终止槽保留自己的语义结果与计费记录。

共享结果不得依赖消费者可用预算差异选择性产生更好版本。若一组声明共享的方法连共同前置预算都不匹配，应在运行前判 protocol mismatch，而不是中途重新调用给某个方法单独修正。

---

<a id="repair"></a>
## 11. Episode 状态机与受限修复

### 11.1 生命周期

```text
PLANNED → CONTEXT_VERIFIED → INITIAL_NODE_CONSUMED
  → PC_CHECKED / PROJECT_PROPOSED（按方法）
  → CANDIDATE_COMMITTED → PUBLIC_EVALUATED
  → REPAIR_PROPOSED → REVALIDATED → 新 CANDIDATE_COMMITTED
  → TERMINAL_SEALED | TERMINAL_NULL
  → BATCH_SEAL_BARRIER
  → HIDDEN_SLOT_CLOSED
  → L3_CONFIRMED_OR_UNRESOLVED
  → PHYSICAL_SLOT_CLOSED（适用时）
  → OUTCOME_RECONCILED
```

上游失败不要求先创建虚假 candidate；每个计划方法位置都必须闭合。状态机由执行器驱动，模型只返回有限种类提议，不能调用“进入 official”“hidden pass”或“预算重置”。

### 11.2 修复动作的判别与计费

本版核心建议使用以下动作，具体输出 schema 在实施时注册：

| 方法／输入状态 | 可接受动作 | 执行后果 |
|---|---|---|
| M1，无完整工程或公开失败 | `replace_project` | 一次调用返回新的完整项目提议；common FPP 和公开检查重新执行 |
| M5，PC 非法 | `replace_design` | 一次调用只修 design；binder 用原 bindings 重新组装，全部 PC 检查重跑 |
| M5，已有 PC/FPP | `replace_behavior_units` | 一次调用返回一个或多个允许单元的新 body，未修改单元保留 |
| M5，需要架构变化 | `replace_design` | 建立新 PC、重建结构；需要行为时用余下的另一次调用重新生成 |

选择动作不增加一个隐藏 router 模型调用。可以由确定性规则限制可用动作，让同一次已计费的修复响应选择其允许的判别类型。模型解释性诊断若另外调用，也须消耗总预算，不增加额外“内部 Agent”额度。

首版优先使用整单元替换，不要求复杂的行级 diff 工具。修改 PC 的一次响应不能偷偷同时输出新设计和未经独立阶段约束的完整行为，伪装成一次原协议中的 PC correction。

### 11.3 PC 变化与旧候选

PC 修正产生新 hash，并全量重新检查／构建。首版全量使旧行为 bundle 失效，随后按余量生成新 bundle；不为省调用把不匹配的旧单元硬接到新结构。以后采用经过测试的精确失效闭包时，必须冻结其规则和成本身份。

原候选及其原 PC/envelope 永久不变。修改中的新 PC 是暂态分支；若无法形成新完整候选，终止选择可以按既定规则保留之前最后一个完整、边界有效的候选及其配套 PC，不能将旧 RTL 与新 PC 混合封存。

### 11.4 终止规则

M1/M5 在最早满足共同公开接受谓词时终止；否则消耗到冻结预算边界，选择最后一个完整且边界有效的 FPP。没有完整候选则封存 terminal-null，并保留上游设计失败／基础设施原因。

无效、空或重复提议消耗其真实调用与成本，不产生有效 repair transition。不得沿用旧版未经对齐的 `NoProgress` 自动提前终止或“每次 PC 只能改一次”限制来改变 B4。若未来选择这种停止规则，必须事先修订并冻结方法协议；不能在实现中任意增加。

越界尝试被拦截，不等于受信文件已经遭破坏；它作为无效尝试，按剩余预算处理。实际写入了受信／评测文件、泄漏隐藏信息或篡改谱系才触发完整性停止与受影响结果失效。

### 11.5 公共接受与最后检查

共同接受谓词绑定 L0、指定 L1、public L2、指定公开 L3 和适用边界检查。没有完成的检查不能视为通过。终止前不必免费再次运行完全相同的 suite；可复用同候选／同配置／同工具的已有有效报告。

最后一次输出仍可封存为未公开接受候选，但不得自动获得 VPP。最终只读验证补齐必需检查时使用固定 policy，并计入最终验证成本；不能向模型反馈或额外挑选候选。M0/M2/M3/M4 不因最终发现错误而获得新修复机会。

---

<a id="budget"></a>
## 12. 预算、计量与事件

### 12.1 B4 的含义

M1/M5 各最多 4 次逻辑模型调用；M0 最多 1 次，M2/M3/M4 每个初始声明阶段最多 1 次。M1 通常 1+3，M5 通常 2+2；PC 失败路径按实际消费重新计算剩余总额度，不给每个阶段各自一份 B4。

M1/M5 最多 4 个公开完整检查周期，且同等冻结 token、上下文、单次输出、工具子调用、活动时间、CPU/内存与 EDA 上限。具体值来自开发测量，不在本规范虚构统一秒数。M3/M4 使用匹配的两阶段预算配置。

完整周期必须列出固定工具及其执行／跳过规则；一次周期中的额外工具重跑也计量。PC 纯检查的运行时间单列，不能无限免费消耗资源；语法装配若启动外部工具，也记录真实子调用及预先定义的预算归属。

### 12.2 预算交易

每次有资源副作用的动作：`reserve → dispatch → observe → commit/reconcile`。logical call 在确定分派时消耗；已确定未分派的本地取消释放预留并留事件。远端是否执行不明确时不能假装零消费。

输入长度以所选模型可核验的 tokenizer／接口计量为依据，输出上限由请求及实际返回双向检查。provider usage 缺失时记录 unknown 与原因；可安全使用已预留上界限制后续调用，但不可把上界记为实测 token。

budget status 至少区分 `compliant / exceeded / unverifiable`。实际数值合规与功能可判定分别记录；计量不可核验会限制等预算声明，不把已经观测到的功能结果改写为没有测试。

### 12.3 计量轴

| 分组 | 必需记录 |
|---|---|
| 模型 | 逻辑调用、transport attempts、输入／输出／缓存 token、可用时的 reasoning usage、模型完成状态 |
| 修复 | corrective calls、提出／接受／拒绝的改动、真实 transition、重检次数 |
| 工具 | 各实际子命令、阶段、工具环境身份、CPU／内存适用限制、运行与退出状态 |
| 时间 | 排队、服务、端到端 elapsed、EDA、隐藏与物理时间分别记录 |
| 离线 | benchmark、oracle、任务和负载预处理的独立开销，不塞入某个模型的方法成本 |

计数为整数，时长可为数值；不复用 PC“禁止浮点”的解析限制。不同 provider 对 cached／reasoning token 的包含关系要映射并记录，不重复求和；不把不同 tokenizer 的 token 直接当同等 FLOPs。

### 12.4 Event 的最小内容

```text
identity: event_id, stream_id, sequence, parent_event_id, action_id
context: campaign/population/block/episode, method 或 shared_node
operation: stage, event_type, outcome_class, reason_code
artifacts: input_refs, output_refs, parent_candidate, resulting_candidate
accounting: reservation_ref, observed_usage, unavailable_reasons, timestamps
visibility: generation_public | control_only | evaluator_private | analysis_only
provenance: source_class, provider/tool/config refs
```

`source_class` 区分 natural_model、synthetic_fixture、reference 等来源；`outcome_class` 表示设计／基础设施／完整性等原因。二者不同，不能继续用一个 `failure_origin` 同时承载两种语义。

同一原始事件不可覆盖。汇总、trajectory 和成本表由 verified events 生成；模型自报 calls、success 或资源值不能作为权威。

### 12.5 transport retry 不能成为免费采样

冻结 policy 可重取已知同一远端请求的结果；若能够确认原请求未执行，按记录重新分派。请求超时且执行状态未知时，保留 uncertain，不默认再采样并把更好的响应作为同一次逻辑调用。

网络传输 attempt 与逻辑生成不同，但每次实际远端执行产生的 token／费用都不能丢失。没有可证明幂等语义的重新生成必须消耗相应新调用预算，或依协议停止为基础设施未知；不得以 SDK retry 掩盖 best-of-N。

---

## 13. 存储、候选封存与故障恢复

### 13.1 存储层

首版采用本地 content-addressed blob store、不可覆盖的对象索引和 append-only journal。单协调器写入可简化锁；要并行时显式增加原子写入／文件锁，不依赖“通常不会同时写”。无需仅为保存 artifact 引入数据库。

```text
run_root/
  public-inputs/                 # 已核验公开源；候选只见 allowlist 投影
  blobs/                         # 内容地址，访问由实际执行域限制
  control/                       # manifest、事件、预算、共享关系
  candidates/                    # 每个不可变快照；scratch 与封存分开
  public-diagnostics/            # 明确允许修复看到的投影

evaluator_root/                  # 不在候选可访问挂载内
  suites/
  raw-results/
  semantic-slots/
  analysis-outcomes/
```

根目录名不是安全保证。不得把整个 blobs 或 repository 挂载到候选域；否则“引用不透明”也会因实际文件可读而失效。

### 13.2 安全路径与实际文件

FPP 路径统一规范为受控相对路径，拒绝父目录段、盘符／UNC、跨平台分隔符混用、控制字符和声明外文件。写入目标不得沿符号链接、越出隔离根或覆盖受信文件；检查解析后的实际目标，不只做字符串前缀比较。

`$readmemh` 等合法初始化仅可读取 manifest 已声明、已核验的公开资产；数据回放由 harness 经接口注入。候选 `$system`、任意 include、层次访问评测对象等按冻结语言政策拒绝。对 parser／simulator 的未知漏洞不作绝对安全承诺。

### 13.3 候选提交和终止

committer 先在 scratch 校验提议、文件依赖及适用编辑边界，再写不可变 blobs 和外部 envelope，最后以原子索引记录 candidate。envelope 摘要不自引用；所有 reader 在使用前重验字节和对象关系。

TerminalRecord 绑定候选、配套 PC/build/envelope、公开接受状态、选择规则、方法预算与配置。无完整候选时用明确 `terminal_candidate_ref=null`、上游原因和费用闭合，而不是删掉该方法行。

M0/M1 或 M4/M5 可共享工程内容 hash，但方法结果与终止槽身份不同。共享工程不是共享未来修复权限。

### 13.4 action 级恢复

恢复从原始 journal 重建，不能只相信一个 `completed=true` 的 summary。建议每个外部 action 有稳定身份、预留记录、请求字节、原始结果落盘和已提交事件。

| 中断位置 | 恢复动作 |
|---|---|
| 预留后、确定尚未分派 | 撤销／继续同一 action；记录原因，不重复计量 |
| 模型响应已落盘、完成事件未写 | 重验响应和身份，完成事件提交；不再次请求模型 |
| 请求已分派、结果不可确定 | 仅按已验证幂等／状态查询策略处理，否则保留 unknown；不盲目采样 |
| 新候选已提交、summary 未生成 | 重建 summary，不重复装配或公开检查 |
| 补丁提议被拒 | 保留原完整候选和被拒提议，恢复相同剩余预算 |
| 共享节点完成，部分消费者尚未运行 | 只读复用已提交节点，不重做共同规划／生成 |
| 隐藏语义已提交，回执丢失 | 返回原提交，不再执行 suite |

本地事件幂等不证明远端 API “exactly once”。不能保证的外部执行必须诚实记为不确定；恢复规则在开发故障注入和正式前核验中测试。

---

## 14. 公开诊断与修复机制分析

### 14.1 诊断对象

公共诊断最少含 `stage`、`reason_code`、候选／PC hash、公开 evidence refs、相关源位置／JSON Pointer、可验证的 fact 关联、允许编辑目标与需要重检的依赖。

诊断来源为 `rule | tool | model_hypothesis`。没有机器证据时不能写“工具已证明该事实违反”；模型解释可以保留，但仍为假设。诊断字段来自 allowlist 投影，不把完整私有工具对象先序列化再删关键字。

候选源码与工具日志中的文本只是数据，不可改变系统指令。需要裁剪日志时，规则、长度和保留顺序冻结并一致，不能只给某个方法更多关键报错。

### 14.2 修复数量

分别统计：真实发生的模型纠正调用、提出改动、被接受的非空改动、实际重新检查，以及达到预定公开终止条件的结果。

“repair transition”必须有旧状态公开诊断、非空合法变更和实际重跑。出现新 attempt ID、repair 文件夹、H failure 或相同代码重复提交均不足以认定 transition。公开修复成功不自动代表终止隐藏正确。

### 14.3 R_generic / R_PC

probe 按研究计划从自然 M4 公开失败候选中预声明选择，不因隐藏失败补选，不注入故障补齐样本。两分支均得到同一 PC、FPP、公开需求、日志、模型、编辑范围和预算；R_PC 只额外得到冻结的义务关联／重检依赖字段。

每分支最多 2 次纠正调用与 2 个公开检查周期是研究计划默认；实际配置在结果前冻结。每家族最多 3 个独立语义实例、每实例一个 checkpoint 的建议不构成最低失败数门槛。没有自然失败就报告实际规模，不阻塞核心论文，也不将 probe 成功替换为 M5 成功。

---

<a id="evaluation"></a>
## 15. Public、hidden 与物理评测

### 15.1 Public worker

public worker 只从不可变候选和固定 policy 重建评测工作区。其共同检查为 FPP L0、指定 lint／编译 L1、独立公共 L2，以及指定 L3。配置绑定 top、源清单、合法初始化数据、语言、工具参数、超时、失败条件与预期完成条件。

候选 TB 和 stdout 中的 `TEST_PASS` 不能决定通过；可信 harness 必须验证预期事务和完整终止条件。候选自行 `$finish`、提前退出或伪造日志，不得等价于完成测试。进程 exit code 只是一项执行证据，不替代语义判定。

M0/M1/M2 的 H 阶段为 not_applicable，不因缺 PC 报 common L0 失败。PC 方法的内部一致性诊断与共同 FPP 检查分开记录；M3 不得通过调用 M4 emitter 才取得可评分资格。任何方法特有编辑边界都应由预声明 MethodPolicy 解释，不能临时改变共同 oracle。

### 15.2 先封存整个批次

正式默认执行次序为：完成核心、已纳入案例及已选 probe 的生成／修复 → 每个计划槽有 sealed candidate 或 terminal-null → 验证 batch barrier → 才执行并开放隐藏结果给离线分析域。

barrier 不能等待所有设计成功，只等待所有计划位置诚实闭合。基础设施导致的未执行位置有原因及缺失记录；不可为使 barrier 通过而删除失败实例。

生成侧与开发人员在生成阶段不查看隐藏语义结果；worker 调度返回 opaque job ref，而不是 pass/fail。跨任务或跨案例的间接反馈同样禁止。没有生成权限的后处理协调器可在合法结果后调度 L4，不复用能调用模型的 repair controller。

### 15.3 隐藏槽与幂等键分开

冻结的**唯一评分槽**建议为：

```text
HiddenSlotKey = (
  campaign_id,
  population_id,
  semantic_instance_id,
  replicate_id,
  condition_id
)
```

同一槽在开始前固定 candidate hash、评测配置 hash、suite commitment、任务和目标。`candidate_hash` 不作为可以自由新增槽的主键：同槽换候选、换 suite、换工具配置均拒绝。

worker 的内部 request/idempotency key 可以包含这些已固定 hash，但不能因此允许同一研究位置多次提交。第二模型、probe 或独立案例使用预声明不同 population/condition；不是在看到失败后换一个 ID 获得第二次评分。

### 15.4 两轴状态

```text
hidden_execution_status = completed | not_run | infrastructure_error | integrity_error
hidden_semantic_status  = pass | fail | null
```

`completed` 恰好对应一次已提交的 pass/fail。没有候选或未满足固定前提时，槽以 not_run 和原因闭合，semantic=null、语义提交数为零；上游已有设计失败仍可使 VPP=0。

提交前基础设施错误可按冻结政策重放同一候选和同一 suite；不改 seed、不换候选。重试耗尽记 infrastructure_error/NA。语义已经提交后，任何重试只能读取原回执，不能重新执行。ledger 损坏、候选／配置不匹配或重复提交尝试涉及完整性规则。

不把“同一进程只能调用一次函数”当作此保证；并发 worker、崩溃和回执丢失都必须由原子槽索引及恢复测试覆盖。

### 15.5 原始证据与允许可见的结果

原始隐藏输入、用例 ID、seed、路径、期望输出、stdout/stderr、诊断和分数留在 evaluator_private。analysis-only outcome 可给 reducer 提供两个状态轴、范围、原因、候选和 suite 绑定、成本与提交数，不回流生成／修复日志或候选附件。

一次 suite 可包含定向、固定随机、压力与真实负载回放。提前停止或完整执行政策固定；未执行用例不记为通过或零错误。新增后验负载必须是独立追加研究，不能改写原有分数。

### 15.6 物理确认

核心／案例 L4 仅对同一封存候选完整 VPP-L3 通过且属于预选物理位置时运行。固定源、目标器件／封装／速度等级、时钟、适用 I/O、例外和资源要求；不根据结果放宽约束或换源重跑。

记录具体工具可提供的阶段状态、映射、时序路径覆盖、slack／原生频率报告、资源、源与约束 hash、实际工具环境和费用。generic synthesis cell 数不是 FPGA LUT 数；尚未分析的 hold／I/O 路径不能称通过。OOC 内部时序不等于板级闭合。

预选位置的 VPP-L3 失败仍留在 L4 原分母，标明未进入原因；同时报告 L3 存活者的条件通过率。L4 失败不改写先前 L3 已验证的功能事实，也不允许核心 repair。无相应证据不报告 bitstream、L5、真实功耗、Vivado 或一般可部署性。

EA 只有独立启用时才能按其协议在搜索过程中使用 public L4 fitness；不能由公共工具菜单误开该权限给 M0–M5。

---

## 16. 结果归约、统计与证据范围

### 16.1 结果类型不折叠

| 观测 | 底层状态 | 主结果处理 |
|---|---|---|
| 无合法 PC／完整工程、已观测功能错误、不可综合、候选耗尽约定执行界限 | design failure | VPP-L3=0，保留计划位置 |
| 已有必需阶段明确失败，其余阶段未执行 | fail + not_run | 保留已确立的失败，不将全行删为 NA |
| 关键检查因提供方／工具／评测环境问题不可判定，且无充分设计失败证据 | infrastructure missingness | VPP 未知，报告 NA 与界限 |
| 受信文件实际被改、隐藏泄漏、事件／预算／评分槽破坏 | integrity error | 停止受影响范围与声明，按预注册规则判有效性 |
| 功能可判定但费用轴缺失 | semantic result + cost unavailable | 保留可判定结果，单独报告费用完整性与等预算声明的可核验性 |
| 某阶段因方法不适用而未运行 | not_applicable | 不能按失败计分 |

VPP=1 仍须满足 [R] 的共同工程、L1、public L2、hidden L2、指定 L3 及没有未解决实际边界／来源／预算违反。成本未知不是实际超限证明，也不能默认为合规；报告语义分数、预算可核验性与正式声明资格的不同维度，不能为了表格整齐伪造状态。仅有计量缺失不得单独把已可判定的设计改记 VPP=0 或 infrastructure NA；并列保存 `budget_status` 与声明资格，由 [R] 的有效性与保守确认规则决定是否支持正式优势结论。实际超预算仍按预声明违反规则处理，不能借“功能正确”忽略。

### 16.2 归约器输入

OutcomeReducer 只接受完整冻结人口、候选／terminal 记录、已验证阶段结果、事件与成本引用。所有正式位置先由 manifest 生成，再左连接结果；不能先筛成功 artifact 再形成分母。

同一个候选在多个表复用不增加 n。缺少 expected outcome、重复 condition、跨 block hash、错误共享关系或无法重建关键事件，应报告完整性／数据闭合问题，不把缺行自动视为成功或忽略。

### 16.3 主要比较与分析协议

本实现继承 [R] 的两个比较，不恢复 [A] 的旧 RQ1/RQ2 两个 Holm 家族：

| 对比 | 结果 | 规划最小效应 δ | 规划备择 Δ* |
|---|---|---:|---:|
| M5−M1 | @B4 的 VPP-L3 | 0.05 | 0.15 |
| M4−M3 | @initial 的 VPP-L3 | 0.03 | 0.10 |

这些是研究计划待明确采纳的默认参数，不是本稿新估计。按实例内重复配对差→家族均值→四家族等权宏均值，保留全部同簇方法与重复。一个 Holm 族、单侧 familywise α=0.05，同时报告两侧区间与负方向结果；不额外加回旧版重复的两侧下界强制门槛。

studentized cluster bootstrap、19,999 次重采样、固定分析 seed、退化规则及功效模拟按 [R] 实现并验证。无方差／极少分歧不得伪造 p 值。模型调用、像素、随机用例或 replicate 不作为独立语义样本。

NA 的比较方向下界赋值与上下界只在分析副本中实施，底层 NA 不改成真实 0/1。缺失率≤5%、方法间差异≤3 个百分点及联合功效≥0.80 都是计划默认，须在相应协议中采纳并冻结；不是代码编写者可根据结果调整的开关。

### 16.4 次级结果

报告 M3−M2、M1−M0、M5−M4、逐家族及错误机制、自然 probe、HFPA 和隐藏完成率、三种成本、代表性 L4、第二模型和纳入案例。不同条件人群的 HFPA 不直接相减解释成因果修复效应。

只能绘制公开检查进展；未评分的中间候选没有隐藏正确性标签，不得回填隐藏收敛曲线。更低平均费用若只是更多早失败，也不能自动称效率优势；需要额外成本优越性结论时按研究协议另冻正确性非劣和成本轴。

### 16.5 应用义务逐阶段报告

每个事实关联其适用验证阶段和证据状态：passed、failed、unverified、not_applicable。PC 的关联只是实现责任；state/numeric/timing 承诺不是自动满足。

无停顿周期吞吐可由适用仿真检查，指定器件时钟须有相应物理证据，真实相机／机器人闭环须有部署证据。VPP-L3=1 不把 L4、工作负载、板级或业务准确率义务一并关闭。

---

<a id="tasks"></a>
## 17. Benchmark、任务卡与应用负载

### 17.1 任务组织

保留 [R] 的四个主要候选：`uart_fifo_loopback`、`stream_fork_join`、`matched_filter`、`sobel_threshold`。开发家族、参考路径与 `qtable_update_core` 的独立案例身份按研究计划保留；本稿不核实今天每个家族是否 oracle-ready。

catalog 只提供任务与证据索引，不是主生成侧 family recipe。公开需求可以说明算法，但 evaluator 增加的 family／split／留出标签不自动进入模型上下文。不同合法内部架构应被同一外部 oracle 接受，不能以参考文件数量或拓扑当隐藏标准。

### 17.2 任务卡的两面

| 公开任务面 | 私有评测／研究面 |
|---|---|
| 计算目标、输入输出、位宽、协议、数值顺序、状态与复位 | 独立位精确参考、协议／时间监测器及资格证据 |
| 事实来源、环境假设、适用域、允许实现自由度 | 具体测试样本、固定随机编排、私有期望输出 |
| 目标时钟／资源与适用验证阶段、公共资产、FPP 交付 | 语义依赖／split、暴露审计、suite 承诺、物理选择 |
| 公共格式、组件使用机会和可见 smoke 规则 | 预处理记录、样本选择、成本与分析身份 |

隐藏的是向量和期望结果，不是接口行为、坐标规则或“什么时候算正确”。ready 裁定前补齐缺失事实；正式后不把参考实现的隐含规则新增为评分义务。

### 17.3 独立 oracle

oracle 由公开冻结需求建立，独立于候选 PC、candidate TB 和生成 RTL。资格至少包含正参考、公开定义缺陷类别的非等价变异、已知盲区、范围与工具身份；mutation score 不证明完备，也不是模型指标。

候选与 oracle 不能通过读取同一候选 intent／代码自动互相确认。可复用固定接口适配器，但需要独立 ABI 测试和黄金向量，避免构建器与 oracle 共享同一错误打包规则却互相通过。

### 17.4 视觉案例优先

先完成“带配置接口的流式图像处理与异常标记子系统”任务卡：算子、像素格式、窗口／坐标／边界、输出模式、无命中、帧级配置生效、背压、复位、时间与存储范围。参考职责分解不强制模型使用相同内部模块。

使用 record+stream 表达同一像素 token 的数据与元信息；对齐、缓冲和状态更新仍由行为实现负责。不得因为有行缓存就称 CNN，也不因回放通过而称工业缺陷检测有效。

640×480、60 fps、100 MHz 和两行缓存是 [R] 的推导示例，不作为 schema 或执行器默认值。首版可暂停源与真实实时源的到达／服务条件分开；不接受无限背压、有限缓存、持续输入且无条件零丢失的矛盾规格。

### 17.5 Q-table 随后

明确总位宽、小数位、符号、运算顺序、各级截断／舍入／溢出、表初始化、同址依赖、host 读写关系、接受／提交顺序、复位和结果背压。`argmax` 平局只有在动作索引可观测时才成为必要义务。

建议用公开任务中的确定事务序列约束状态更新；实现可选择停顿、转发或其他合法机制。模拟轨迹标为 simulated_trace，不写成真实机器人数据。该硬件执行更新运算，不代表训练生成模型或证明 RL 控制效果。

### 17.6 负载与预处理

区分定向、固定随机、真实数据派生、原始实测和模拟轨迹。MVTec AD 等仅为研究计划候选，正式使用前核验来源、许可、选择和预处理，不在本稿声称已经下载或采用。

冻结灰度转换、裁剪／缩放、量化、顺序、标记生成、源与派生文件 hash、预处理代码版本。私有样本经 trusted harness 接口注入；公共权重属于设计输入，不能把权重和隐藏图像混为同一资产权限。

真实回放不代替角落用例。同一工程内的多张图、多条轨迹和多个周期是覆盖，不增加独立工程 n。完整 suite 计分与超时在结果前固定，不只报告通过图片。

### 17.7 案例数量与暴露

视觉规划为 1 个项目规格×2 次重复×M1/M3/M4/M5，共 8 个方法结果；Q-table 纳入时另计 8 个。M1 仍承担 Direct 初始调用，即使没有单独 M0 展示行。案例与核心、第二模型、probe 分组，不挽救主要统计假设。

案例的较大 token／工具上限可以单独冻结，但比较方法信息与总预算等价；不能与核心配置直接混算。需要 L4 时预先列出所有对应位置，上游失败不替换。

正式案例优先在主方法冻结后运行。开发视觉／Q-table 若已暴露 `sobel_threshold` 等机制，要如实重审 family-held-out 或组合留出；换文件名、改位宽或换图片不能恢复未见身份。

---

## 18. 最小 machine contracts 与注册策略

### 18.1 不再“一次补丁一个授权 contract”

首版只注册真正跨进程、持久化或需独立核验的边界，内部纯 dataclass 不必各有文件 schema。建议按以下类别组织，具体路径和新版本须经 WP0 盘点后确定：

| 类别 | 建议容纳的逻辑对象 | 生产／消费边界 |
|---|---|---|
| 公共任务与 profiles | 需求、ABI、facts、资产、target、capability | 准备端 → 所有方法／checker／worker |
| PC2 schema | 完整 PC、design projection | model/binder → PC checker |
| 生成提议 | 无类型计划、ProjectProposal、BehaviorBundle、修复提议 | model → executor/committer |
| 构建与候选 | 派生 plan／ABI、FPP manifest、可信 envelope、TerminalRecord | builder → repair/worker |
| 运行清单 | RunPolicy、population、配对 DAG、模型／工具／suite 与分析引用 | preflight → coordinator/reducers |
| 事件与成本 | 判别式 Event、预算预留／实测及归约视图 | 所有动作 → accounting |
| 共享起点 | 三类 checkpoint 与输入依赖 | coordinator → method executor |
| 结果 | 分阶段 outcome、隐藏双轴、slot 绑定、范围与原因 | worker → analysis |

一个类别可在同一版本化 schema 内用判别联合表达，不强制拆出几十个几乎相同的 positive acceptance receipts。批准记录与核验报告也应直接绑定同一 campaign，不构建 G3/G4b 层层授权布尔链。

### 18.2 读写核验

writer 在原子发布前验证形状和必要语义；reader 在使用前核验版本、字节和跨对象关系。未知版本、非法引用、泄漏字段、控制权伪造和 budget mismatch fail closed。活动代码不得悄悄接受旧 PC 并补默认值。

schema 注册仅是格式检查；worker 的真实性、权限、候选来源和 oracle 独立性需要相应运行核验。`conformance.json` 是测试输出，不注册为项目设计输入或正式评测许可。

### 18.3 可删除重建的视图

trajectory、status、cost_summary、paired_outcomes、案例表、义务覆盖与论文表均从事件和不可变对象派生。导出时保留来源身份与版本；错误修正产生新视图和影响记录，不改原始事件。

历史资产不进入新运行 reader。确需解释旧结果，用只读离线工具和独立命名空间；它不是新核心的兼容入口，也不对旧结果授予 PC2 通过信用。

---

## 19. 运行模式、批准与操作入口

### 19.1 三种运行模式

| 模式 | 允许内容 | 启动条件与禁止项 |
|---|---|---|
| development | 小规模真实或 fake 模型、开发任务、公开工具、故障注入 | 明确资源限额和 opt-in；不得读取正式隐藏任务；结果不能升级为正式 |
| excluded_pilot | 冻结排除式人口、M0–M5 配对、费用／失败／方差测量 | WP3 的方法／阈值／预算／分析准备已完成；不能根据 pilot 效果改科学阈值 |
| official | 最终 manifest 中的固定主实验及已纳入分组 | 批准与独立核验通过、全量无结果配置一致；不动态改样本或方法 |

A_req、EA、board 等不是模式的隐式分支，只有独立协议启用后才装配对应组件。disabled 时不要求空 manifests、空目录或未经使用的测试／授权链。

### 19.2 CampaignPreflight

正式启动前核验研究／PC／方法版本、公开和私有输入承诺、样本与共享关系、模型与工具配置、预算、停止规则、oracle 资格、分析规则、案例选择以及负责人批准的同一内容摘要。

负责人批准记录来自受控外部渠道，独立程序重算输入身份和必需条件。若部署采用数字签名，明确签名算法、信任根与验证范围；未实现签名时不得把普通 checksum 写成“已验签”。不要求为了本地研究建立完整 PKI，但不得接受模型或 manifest 自填 `authorized=true` 作为许可。

核验失败前不得执行官方模型／EDA／评测或创建官方候选；可在专用审计区产生不含研究结果的失败报告。开发模式无需取得一份官方批准才能做每个无副作用检查；正式权限也不能通过 CLI 的 `--force` 绕过。

### 19.3 建议命令面

以下是目标 CLI 用例，不表示当前仓库已有这些命令，也不是本次执行记录：

```text
sr2fpga inspect-context <public-task>
sr2fpga validate-pc <pc> --context <public-task>
sr2fpga plan-build <pc> --context <public-task>
sr2fpga run-development --config <bounded-dev-config>
sr2fpga prepare-pilot --manifest <excluded-protocol>
sr2fpga verify-campaign --manifest <frozen-manifest>
sr2fpga run-campaign --manifest <verified-manifest>
sr2fpga resume --run <run-id>
sr2fpga analyze --manifest <manifest> --events <verified-store>
```

隐藏和物理 worker 的命令只在相应权限域可用，不能交给模型通用 shell。所有启动统一走同一 policy/resolver，不保留另一个绕过预算的“便捷旧入口”。

---

<a id="workpackages"></a>
## 20. WP0–WP6 实施顺序与交付

### 20.1 工作包

| 工作包 | 实施重点 | 最小验收产物 |
|---|---|---|
| WP0 范围与盘点 | 确认活动版本；盘点旧代码可复用函数、registry、任务、oracle、暴露 | 规范差异表、真实代码证据表、无兼容目标、研究 PC2 同步清单 |
| WP1 PC 与构建 | 受信公共视图、PC2 schema/checker、H 映射、ABI、结构 emitter、行为装配边界 | 正反例 PC、ABI 黄金数据、实际小工程结构输出、来源和边界验证；视觉任务卡 |
| WP2 真实开发闭环 | 单一 executor、M0–M5、批量行为调用、public 评测、B4、共享失败、恢复 | 开发任务上的真实模型／工具闭环及事件；至少可审计修复链，不伪装自然失败 |
| WP3 候选协议与 oracle | 任务资格、隐藏隔离、方法信息与预算、分析代码、case/probe 决策 | 未含正式结果的协议与分母、独立 oracle 资格、完整场景测试 |
| WP4 排除式 pilot 与最终冻结 | 全矩阵运行、成本／方差／缺失测量、功效／精度、最终独立核验 | 不删失败的 pilot、冻结最终 n 和配置、可重建官方 manifest |
| WP5 正式执行与物理 | 全部生成先封存、一次 hidden、指定 L3、预选 L4、纳入案例 | 每个位置明确 outcome、成本与证据范围；无反馈污染 |
| WP6 分析与发布 | 主次统计、机制解释、案例／物理分母、来源许可和限制 | 可重建论文表、声明清单、复现包与未完成事项 |

不增加新的 G0–G9/CD1–CD10 必须完成链。工作包验收是实现与测量条件，不要求方法有正向显著效果。关闭的扩展没有阻塞权。

### 20.2 优先实现的六个垂直切片

**切片 1：可信输入到 CheckedPC。** 先验证真实公开对象与 PC2 绑定，schema 与 H 映射，错误位置、未支持能力及引用错误；不要先跑全量家族生成。

**切片 2：CheckedPC 到结构工程。** 用组合模块、参数化复用、record／stream 和时钟 reset 生成真实可解析结构；先用标明为人工／参考的行为 body 验证装配器，不将其计作模型成果。

**切片 3：一次模型调用填完一个工程。** 验证输出 bundle、上下文、缺单元、截断、越界和无免费补齐；用真实工具确认已消费的是实际生成内容。

**切片 4：同一失败候选到预算化修复。** 先覆盖 M1，随后 M5 的 behavior 和 design 两类动作；全部成本和历史候选可重建。

**切片 5：完整共享配对块。** 验证 S_D/S_C/S_B、M2 路径、6/10 初始调用、11/15 上限、失败起点与顺序；M3 emitter/filler 调用必须为零。

**切片 6：隔离评测与一次提交。** 先用开发独立 suite 测试双轴结果、无候选、基础设施失败、回执丢失及同槽换候选拒绝，再进入 WP3/WP4 正式准备。

这些切片是工作包内部的实现顺序，不是新研究门槛。运行真实开发模型只需相应边界与明确限额，不等待完整 A_req、EA 或训练系统。

### 20.3 计划规模作为参数，不作为已执行结果

沿用 [R]：开发约 3 家族×2 任务；排除式 pilot 6 类机制×2 新实例×2 重复×6 方法=144 方法结果；主规划 4×30×3×6=2,160；第二模型候选 320；视觉和纳入的 Q-table 各 8。

独立 n 来自真实语义实例与依赖审计，不从位宽变体或图像数量推导。最终规模由预声明模拟和排除式 pilot 的干扰参数确定；不把 30／家族写死为统计充分，也不根据测试效果决定删掉哪个家族。

---

<a id="tests"></a>
## 21. 测试与验收矩阵

### 21.1 测试分层

测试依次覆盖纯函数／contract、PC 与构建、方法和配对集成、真实工具、隔离安全、故障恢复和端到端开发闭环。默认测试使用 fake model，不调用外部 API；真实模型与重量级 EDA 用显式 opt-in 的开发配置。

fake model 的输出只能检验编排与接口，不能作为模型能力结果。人工注入 RTL 故障可以测修复管线，不能进入自然失败率。工具未安装记 skip/not_run 并报告范围，不能把未执行测试标为 passed。

PC2 附带的 [T] 报告记录 70 项本地静态测试、0 failures、0 errors。本次没有重跑该测试，也不能据此认定新 emitter、AST 边界、OS 隔离、M0–M5 或正式评测已经验证。生产接入后对相同输入运行新路径，并新增真实构建／集成覆盖。

### 21.2 有限必需场景

以下 ID 是本 SPEC 的验收定位符，不是新 gate 或已经生成的运行证据：

| ID | 测试面 | 必须观察到的行为 |
|---|---|---|
| C01 | JSON/schema | 重复 key、旧版本、拼写错误、未知字段、PC 非法浮点、截断被拒；合法 PC 与 proposal 通过对应入口 |
| C02 | 模型输出投影 | design 为根对象；自填 bindings、评分或权限无效；受信组装后的完整 PC 核验一致 |
| C03 | 外部事实 | 修改需求／target/capability 被拒；fact role 和关联检查明确范围；Direct 获得等价公开 ABI |
| C04 | 表达式与参数 | 未绑定参数、除零、负中间量、零宽、超深／超界失败；实际绑定配置可展开 |
| C05 | 层次与类型 | 未定义模块／端口、定义递归、不可达定义、类型／域不匹配失败；参数化复用和组合实例可表达 |
| C06 | 协议信号 | payload/valid 正向、ready 反向；record LSB-first；stream 广播拒绝，value 合法扇出允许 |
| C07 | 结构 determinism | 同源及配置的结构文件／ABI 相同；没有随机路径、任务模板或未声明 FIFO／转换器 |
| C08 | 结构保证边界 | 正确 PC+错误算法 body 能进入独立功能检查并被 oracle 检出，不能静态自证 |
| C09 | 行为 bundle | 多单元首发仍恰好一次模型调用；缺单元／未知单元／部分输出没有免费补全；同特化复用 |
| C10 | AST／装配 | 提前 endmodule、额外模块、越界宏、未声明实例、signature 改动和隐藏路径访问被阻止 |
| C11 | FPP 中立性 | Direct 无 PC／候选 TB／QoR 仍可满足共同交付；非固定 top 源路径可用；脚本不能自定评测 |
| C12 | M2/M3 因素隔离 | M2 无 PC semantic checker；M3 不调用 emitter／filler／参考生成器，也不读 M4 产物 |
| C13 | 共享成功 | M0/M1 初始 FPP 相同、M3/M4 初始 PC 相同、M4/M5 行为填充后 FPP 相同；方法槽仍独立 |
| C14 | 共享失败 | PC fail／project fail 都复用同一失败与成本；下游未执行不伪造工程或清空分母 |
| C15 | B4 全路径 | 正常 1+3 与 2+2、PC 初始失败后余量、PC 修改再填行为均不超过总额；无隐式 router 调用 |
| C16 | 修复与选择 | 合法非空改动后重跑才是 transition；被拒改动保留旧候选；最早公开接受／最后完整规则无后验选择 |
| C17 | 成本闭合 | 6/10 初始与 11/15 最大调用视图可重建；共享事件不重复收费、不摊薄独立视图；未知不填零 |
| C18 | 调度 | 依赖顺序始终成立；本地 seed 与 provider seed 分离；恢复不重新做共享前置调用 |
| C19 | Public authority | 伪造 TEST_PASS、候选 TB、提前结束不产生 trusted L2 pass；实际 harness 结果与同候选绑定 |
| C20 | 隐藏隔离 | raw case／seed／status／summary canary 不进入任何模型、候选、公开诊断或可见事件 |
| C21 | 评分槽唯一 | 同槽同结果可读回；换候选／suite/工具拒绝；并发提交、回执丢失不能产生第二语义结果 |
| C22 | 隐藏失败与缺失 | hidden fail 不修复；无候选是 not_run+上游结局；pre-commit infra 与 committed failure 分开 |
| C23 | 批次屏障 | 主实验、纳入案例、probe 所有位置闭合前不开放 hidden；失败位置也能合法闭合 |
| C24 | 物理 | 只运行预选同候选 L3 存活者；约束不可变；未进入／失败保留分母，无 L4→repair |
| C25 | 统计与人口 | 完整、全失败、稀疏分歧、退化方差、NA、重复 ID、簇依赖、两项 Holm 均有合成测试 |
| C26 | 应用负载 | 预处理与输入 hash、协议边界／复位／数值核对；图像与轨迹数量不扩大 n；公开权重不泄漏私有样本 |
| C27 | 运行恢复 | reserve 后中断、响应落盘未入事件、candidate 已提交未汇总、未知远端执行均可按规定闭合 |
| C28 | 权限与范围 | 未核验官方配置不能启动正式副作用；disabled 扩展不被装配；新核心不导入旧兼容或训练路径 |

### 21.3 验收记录

每个场景记录实际输入、代码／contract／配置 hash、预期行为、真实结果、产物引用及未覆盖范围。通过条数不是研究结论；某项工具集成尚未执行就保留未验证，不用 unit test 的同名布尔值代替。

先运行最窄受影响测试，再运行相应 PC/build/method/worker 范围，最后运行新核心端到端回归。新核心不以旧 training/compatibility_tests 全部通过为完成前提；对确实复用的共享代码，应运行相关非破坏回归，避免影响无关资产。

---

<a id="replacement"></a>
## 22. 旧 SPEC 的退出与文档同步

### 22.1 显式替换表

| [A] 的旧内容 | 新设计处理 | 不应发生的行为 |
|---|---|---|
| System-HIS v1.2 + additive/read-compatible | PC2 单一严格入口；旧证据只读归档 | 写兼容 adapter 或静默转换后授予新分数 |
| 根部 intent/top/components/instances/data_flow/state 多处权威 | PC2 bindings + 层次 modules + requirement_map | 仅重命名字段却继续消费旧语义 |
| 兼容 `agent.py` / runner façade | 单一新 executor；可复用已审查纯函数 | 新旧编排互相回调、同时拥有方法控制 |
| G0–G9 与 CD1–CD10 层层依赖 | WP0–WP6 + 模式核验 + 有限验收场景 | 为旧 positive G3/G4b contract 等待无关基础设施 |
| 旧 RQ1 M4−M0、独立 RQ2 Holm 族 | M5−M1@B4、M4−M3@initial 的一个主要族 | 用旧统计脚本解释新实验 |
| 相同 repair 次数／旧 @A | 相同总 B4、token、工具和资源机会 | M5 获得免费规划或每叶多次首发 |
| H2 dry lower 与旧 W1–W10 | 新 PC2 policy 显式映射；M3 不调用 emitter | 成功 M4 构建成为共同 PC 过滤器 |
| 必然存在的共享工程 | 三类共享成功／失败 checkpoint | 初始失败被删或成本重置 |
| 同哈希或不同哈希都可新建 hidden key | 固定实验槽 + 候选／suite 不可变绑定 | 换 candidate hash 获得第二次隐藏评分 |
| NoProgress 或一次 correction 硬编码 | 研究计划冻结的终止与总预算规则 | 实现者偷偷缩短某方法机会 |
| attempted trusted edit 一律永久失败 | 被拦截的无效尝试与实际完整性破坏分开 | 把成功防护当作已经泄漏／被改 |
| 每终止强制重新 public 跑一遍 | 精确证据复用或计费的最终补齐 | 免费重复 EDA 或未测阶段默认为 pass |
| 训练／release/M6 占据主体架构 | 从新核心移出，保留历史资产独立边界 | 新 Paper-1 启动训练或等待训练授权 |
| 应用只有目录名和 architecture_obligations | 显式任务卡、来源、阶段、负载和案例分组 | synthetic shell 被命名成真实应用结果 |
| 大量“已实现／G3 未验收”历史段 | 保存 [A] 原文或 Git 历史；新状态由实证更新 | 搬来历史数字当新实现完成度 |

### 22.2 采纳时需要同步的位置

研究计划更新 PC2 序列化、逻辑字段映射和无兼容取舍；不改变已有主比较、B4、任务人口或统计方案。新方法版本与旧结果的关系显式记录。

根 AGENTS／项目 README 只链接当前规范与职责，不复制完整实验协议；`agent/README` 放真实已实现命令和最短开发路径。`docs/current-status.md` 只报告已验证范围和待实现项，不再保存另一份研究 gate 规则。

`contracts/manifest.json` 注册实际交付的 schema 和 runtime contracts，确保 writer/reader/fixtures 绑定同一内容。旧 README 的命令、旧冻结签署 hash、provider-specific method 名和旧层次引用按真实使用面清理。

这些是实施时的同步任务，不表示本次已经修改上述仓库文件。本次交付不改变原研究文档、PC schema 或历史证据的字节。

---

## 23. 完成标准、取舍和明确不做的事

### 23.1 一个实现切片的 Definition of Done

必须能够说明它实现的责任、有效输入、失败／未知／完整性状态和权限边界；相关 writer/reader 使用同一 contract；其模型／工具／重试费用可从事件重建；正反例与故障恢复在声明范围内通过；文档状态与实际实现一致。

切片没有触及的层不被宣称通过。PC schema 新增一条字段不等于该性质已有 checker，checker 通过也不等于 RTL 或目标器件正确。重大语义、提示、预算、suite、样本或终止规则变化必须新版本，正式结果打开后不得就地补写规则。

### 23.2 核心可进入正式研究的条件

完整 M0–M5 配对路径、真实公开工具、独立 oracle、隔离边界、固定分母、预算与恢复、一次评分槽以及主要分析能够执行和重建；pilot 给出可行性与规模依据；最终 manifest 获负责人批准并经独立核验。

不要求 pilot 效果显著，不要求自然失败 probe 满足虚构最小数，不要求 EA、A_req、训练、Vivado 或板级全部完成。具体正向论文结论仍取决于正式结果，而不是工程验收通过。

### 23.3 主要风险与默认应对

| 风险 | 默认处理 |
|---|---|
| 新 PC2 太长，模型只出现格式失败 | 在开发域改表示投影、支持范围或模型，版本化后重新 pilot；不在正式阶段偷偷多调用 |
| 行为叶数量导致预算失真 | 批量一次响应，记录全部上下文；逐叶 agent 另立方法 |
| 构建器逐渐变成答案模板库 | 结构与行为来源审计；禁止 family generator 依赖，公共行为库另列干预 |
| PC/H3 名称被误读为语义证明 | 显示规则范围、关联性质和 deferred checks；不以 trace 数量当完整 fidelity |
| parser／ABI 与 oracle 共用错误规则 | ABI 黄金数据、跨方向样例和独立期望核对；不只做自洽往返测试 |
| 预算或隐藏重试不完整 | 有界预留、原始响应落盘、固定评分槽；未知保留，不免费再采样 |
| 测试和授权基础设施再次膨胀 | 每个对象有实际消费者；一个 journal/contract family 服务相关场景，不为 disabled 扩展预建系统 |
| 应用范围失控 | 视觉优先、Q-table 随后，推理储备；平台／业务质量独立协议 |
| 对新架构宣称已落地 | 只从真实代码与产物更新状态；参考70项测试不晋升为新系统验证 |

### 23.4 不预建的能力

不设计通用 RTL 指令语言、全参数域证明、任意多时钟／CDC、任意第三方 IP、自动 SoC／驱动生成、多 Agent 协商平台、分布式训练、学习型 QoR 或大规模分布式运行服务。必要时按实际研究目标独立扩展，不把“不兼容”理解为“必须重写一切”或“必须支持一切”。

---

## 附录 A：核心服务接口责任

以下为设计签名，不是本次已经实现的 Python API。返回类型须用 closed union 区分成功、候选失败、基础设施与完整性错误；不能用裸 `bool` 或任意 dict 混合这些状态。

| 服务 | 输入 → 输出 | 关键限制 |
|---|---|---|
| `PublicContextLoader.load_verified` | 受信任务／profile refs → PublicTaskContext | 不推断未提供事实，不读取私有 family 答案 |
| `PcBinder.assemble` | DesignProposal + PublicTaskContext → PC | 只使用受信 bindings，不接受模型的 expected hash |
| `PcValidator.validate` | PC + context + policy → PcCheckReport + ResolvedDesign（成功时） | 纯检查／展开；不调用 LLM、emitter、oracle |
| `BuildPlanner.plan` | CheckedPC + ABI policy → BuildPlan | 派生对象只读，标明全部 behavior units |
| `StructureEmitter.emit` | BuildPlan → 结构 artifact set | 无家族行为、无动态脚本、固定输出 |
| `BehaviorComposer.compose` | plan + BehaviorBundle → FPP proposal / diagnostics | 必须校验受保护结构，失败不自动生成占位行为 |
| `CandidateCommitter.commit` | proposal + MethodPolicy + provenance → immutable CandidateRef | 候选自报权限无效，实际依赖与路径核验 |
| `PairedCoordinator.prepare` | FrozenRunContext + paired block → DAG/checkpoints | 同源节点一次生成，包含失败与消费者成本关系 |
| `EpisodeExecutor.advance` | state + allowed services → next action/result | 中央控制预算、状态与动作，无隐藏自循环 |
| `BudgetLedger.reserve/commit` | action、各轴需求／实测 → reservation/event | 原子、不可免费重置，unknown 不能变 zero |
| `PublicWorker.evaluate` | candidate + public policy → public outcome/diagnosis | 固定独立 harness，候选脚本／TB 不作权威 |
| `TerminalSelector.select` | ordered candidates + public results + budget → TerminalRecord | 最早公开接受／最后完整，无 hidden 输入 |
| `HiddenWorker.close_slot` | stable slot + fixed seal/suite → opaque ref | 语义提交唯一，analysis-only 内容不返回模型 |
| `PhysicalWorker.confirm` | verified eligible seal + fixed profile → L4 outcome | 不修改源与目标，不产生核心 repair |
| `RunRecovery.reconcile` | manifest + journal + verified blobs → resumable state | 优先使用已落盘结果，不重做不确定外部调用 |
| `OutcomeReducer.reduce` | frozen denominator + outcomes/events → results | 全分母、双轴、完整性与成本范围分开 |

公开工具诊断可作为模型输入；上述服务自身的私有 storage root、worker 实例、控制权限和 credentials 不能作为通用 services 对象传给模型适配器。

---

## 附录 B：研究要求到实现与测试的追踪

| 研究／PC 要求 | 本 SPEC | 主要实现面 | 关键验收 |
|---|---|---|---|
| [R] 同一公开事实与不可改需求 | §§4–6 | context loader、binder、信息投影 | C02–C03 |
| [P] 统一层次、类型、域和 stream | §§6–7 | pc checker、ABI、emitter | C04–C08 |
| [P] 行为叶＋受保护签名 | §8 | bundle、composer、AST boundary | C09–C10 |
| [R] M3/M4 同 PC 且不以 skeleton 筛选 | §§6、9–10 | H policy、method dispatch、共享 DAG | C12–C14 |
| [R] B4 与相同资源机会 | §§8–12 | batched fill、action policy、budget ledger | C09、C15、C17 |
| [R] 真实修复与固定终止 | §§11、14 | repair controller、selector | C16、C19 |
| [R] 独立 hidden、无跨任务反馈 | §§2、13、15 | OS isolation、barrier、slot worker | C20–C23、C27 |
| [R] 全分母、缺失、三成本 | §§10、12、16 | events、reducers、analysis | C14、C17、C22、C25 |
| [R] 单一主要 Holm 族 | §16 | frozen analysis implementation | C25 |
| [R] 代表性 L4、不是部署保证 | §§15–17 | physical worker、义务报告 | C24、C26 |
| [R] 视觉／Q-table 与真实回放 | §17 | task card、oracle、workload adapter | C26 |
| [R] WP0–WP6 与扩展关闭 | §§19–23 | mode guard、实施切片、文档同步 | C28 |

---

## 附录 C：实施时必须填实的参数与决定

本规范已确定目标结构，但下列值不能从旧快照或示例自动继承。开发可有明确的临时配置；官方 manifest 不能含影响运行的未定值。

| 项目 | 冻结／确认依据 |
|---|---|
| 公共任务和 profile 的实际 contract | WP0 盘点，源对象字段与 PC2 检查视图的一致性 |
| PC2 注册 id、schema bytes、checker/H policy | 两份 [S] 的一致版本及真实规则测试 |
| HDL 子集、parser、ABI emitter、语言标准 | 真正支持的语法、保护检查和黄金样例 |
| 主模型与第二模型、provider API、解码与上下文 | 开发域选择与实际接口能力，不凭历史版本名推断 |
| B4 各 token／工具／时间／内存轴 | 开发测量与 pilot 前匹配；不按成功结果追加额度 |
| transport 幂等与未知执行政策 | 实际 provider 行为／测试；不支持则停止或计新调用 |
| stage 调度、缓存、事件恢复策略 | DAG 规则、共享计费及故障注入测试 |
| 任务人口、语义依赖、暴露和 oracle 资格 | evaluator-owned 记录；不是 catalog 的单个 ready 布尔值 |
| 定向／随机／真实回放 suite | 完整公开规则、私有样本、预处理、期望输出与超时 |
| 精确 L3/L4 flow、器件与约束 | 合格参考路径与实际工具环境；不从开发截图继承 |
| 实验批准来源与独立核验方式 | 明确控制方、内容 hash 与实际权限；不假装 hash 是签名 |
| 主要统计和最终规模 | [R] 的预结果参数、模拟审计与 pilot nuisance estimates |
| 案例／probe／第二模型是否纳入 | WP3/WP4 的预结果决定；纳入后保留所有位置 |

这些待填项不允许由 LLM 在正式生成时自己选择。发现 schema 或 PC 设计确有表达缺口，应显式更新方法／contract 版本，不添加无约束 metadata 临时绕过。

---

## 附录 D：源文件身份与本次交付范围

下表 SHA-256 在本次写作时按实际挂载文件字节计算，用于确认所依赖的版本；不是签名、许可或当前仓库版本证明。

| 代号 | 文件 | SHA-256 |
|---|---|---|
| [A] | `2026-08-18-sr2fpga-paper1-code-architecture-development-spec.md` | `fd5123c3fe0c545f0229f40b65dd818780524466e1a6db0f95e810a7e3b3bf07` |
| [R] | `2026-09-14-sr2fpga-paper1-research-plan-v2.1.zh.md` | `2da34c3bf557bb65c36663f2b79ca34871f05dc2760b0a8830e80a61e42ecd14` |
| [P] | `PC-2.0-clean-slate-design.zh.md` | `23816bf3405d0ec8959d077e0418aa8ac5fc15399d1013c29f02aa64e21af0e3` |
| [S1] | `project-contract-2.0.schema.json` | `00c938a2436a3beba96cd6fa3625238b8a37b279485ccce1d71227037d02b416` |
| [S2] | `design-proposal-2.0.schema.json` | `cf615140e27482dd1222e8f5f13a3d0b3e521f85f5c7d67b3b4f9ed8aa3f34eb` |
| [T1] | `conformance.json` | `25b042c2707662d2b431fd4955d5325306a1c789a3d968d6715ce8c31ef6e3fa` |
| [T2] | `SR2FPGA-PC-2.0-clean-slate.zip` | `7024fbc1f1732505f331a45a1c7026d8a2157bc64a9ccfd7a4303fe99024e813` |

本次读取了 [A]、[R]、[P] 和 PC2 schema，并检查了 [T] 压缩包中的示例输入与参考 API 结构，以避免将示例 contract 当作生产需求格式。未重跑其70项测试，未调用付费模型、仿真、综合、布局布线或上板；新包布局、运行 contracts、构建器与执行器均为待实施设计。

本稿没有进行额外外部文献研究。文中的 PC 协议、类型规则、实验参数和任务语义分别来自 [P]/[S] 与 [R]；新控制、批量装配、评分槽和恢复方案是为落实这些材料而提出的工程决定。实际选择 provider／工具／数据源时另行核验采用版本，不将源文档的资料引用当成已安装能力。

---

**架构结论：** 新系统围绕一个受信、可计费、可恢复的执行器展开。PC2 只表达绑定既定需求的类型化架构；构建器只维护可机械保证的结构；模型在一次声明阶段中批量完成行为；公开反馈只在 B4 内修复；隐藏与物理证据通过独立域产生。用最少必要的 contract 和可重建事件支撑两个主要研究比较，而不是让历史兼容、授权层级或应用包装主导工程。
