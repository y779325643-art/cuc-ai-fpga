# SR2FPGA Paper-1 代码架构与开发规范

> 当前案例修订：2026-10-28 的 [paper1-v2.3 LLM case amendment](2026-10-28-sr2fpga-paper1-llm-case-amendment-v2.3.zh.md) 覆盖本文的家族与任务总体绑定，替换为 QKV、KV-cache decode attention、gated FFN。其余模块职责和安全、预算、独立评测边界沿用；本文仍是目标架构，实际实现见代码与当前状态。
## 面向三个量化 AI 加速子系统的 PC 2.1 构建、修复与独立评测

**规范版本：** `sr2fpga-paper1-code-dev-v2.1`  
**日期：** 2026-09-15  
**状态：** **当前下位实现规范**（2026-09-15 由用户随 `paper1-v2.2` 一并采纳）。已授权按本规范迁移仓库；**未授权正式实验**。见研究计划 §21  
**规范类型：** 研究计划的下位实现设计规范；完整目标架构，不是当前仓库状态说明  
**研究依据：** `paper1-v2.2` [R]  
**PC 格式：** `sr2fpga-pc-2.1` [P, S1, S2]  
**主任务总体：** `ai_dw_pw_block`、`ai_quantized_residual_block`、`ai_tiled_gemm_pipeline`  
**主要比较：** M5−M1 的总预算系统比较；M4−M3 的共享 PC 构建／编辑边界比较  
**输出：** 完整 FPGA Project Package（FPP）及分离保存的执行、验证和成本证据  
**兼容政策：** 新核心没有 System-HIS v1.2／PC 2.0 reader、别名、自动转换或回退路径  
**本稿撰写时的实施状态：** 只重新编写 SPEC；没有修改代码仓库、研究计划、PC schema 或 checker，没有运行生成模型、RTL、EDA 或正式实验。采纳后的迁移进度见 [`docs/migrations/research-plan-alignment.md`](../migrations/research-plan-alignment.md)，不在本规范内维护第二份状态。

> 本稿以代码架构 SPEC v2.0 [A] 为直接架构基线，将研究计划 v2.2 [R] 与 PC 2.1 [P]、实施差异清单 [D] 落实为包职责、数据对象、构建过程、方法调度、修复、预算、评测与测试要求。它完整替换旧架构的目标设计，不是在原四家族／PC 2.0 主流程后追加一个 AI 分支。文中明确标注的接口、目录和装配规则是本次实施提案，不代表仓库已存在；研究参数与 PC 数学语义不在本稿中自行改写。

## 阅读导航

| 要解决的问题 | 位置 |
|---|---|
| 当前依据、三类版本与不可破坏的约束 | [§0](#authority)、[§1](#scope) |
| 总体执行域、包职责与关键对象 | [§2](#architecture)–[§4](#objects) |
| AI 公开需求与 PC2.1 检查 | [§5](#requirements)、[§6](#pc) |
| 张量／lane／mask 如何变成真实源码 | [§7](#build)、[§8](#fpp) |
| M0–M5、共享、修复与全成本 | [§9](#methods)–[§13](#storage) |
| 实际一致性、独立 oracle、hidden 与物理 | [§14](#diagnostics)–[§17](#tasks) |
| 原生 Agent／消融、运行权限与可选边界 | [§19](#modes) |
| 开发先后、验收与旧规范退出 | [§20](#workpackages)–[§23](#done) |
| 服务接口、追踪、待定项、来源 | 附录 A–D |

---

<a id="authority"></a>
## 0. 依据、权威与版本边界

### 0.1 材料和用途

| 代号 | 材料 | 权威与使用范围 |
|---|---|---|
| [R] | 2026-09-15 研究计划 v2.2 | 研究对象、三个 AI 家族、设计簇、M0–M5、预算、统计和允许声明 |
| [P] | PC 2.1 AI-stream 设计说明 | 张量、数值、序列、有限关系及静态能力边界 |
| [S1]/[S2] | PC 2.1 完整与模型输出 schema | 已交付候选机器字段；两份 schema 的 design 定义一致 |
| [D] | PC2.0→2.1 IMPLEMENTATION_DELTA | checker、ABI、缓存失效、评测和任务同步线索 |
| [A] | 2026-09-14 代码架构 SPEC v2.0 | 可保留的执行、预算、评分槽、存储和恢复责任；旧总体和版本由本稿替换 |
| [T] | PC2.1 `reports/conformance.json` | 既有局部测试报告；不替代新系统集成、RTL 或模型证据 |

附录 D 记录本次实际读取文件的字节身份。本次没有读取当前 Git 仓库、活动 `contracts/manifest.json` 或 `docs/current-status.md`，因此不确认当前实现进度、现有 API、工具安装版本或家族 ready 状态。

### 0.2 两条权威链

**规范链：** 经明确采纳的 [R] 及显式研究修订 → 冻结的实验／分析协议 → 本 SPEC 与一致的运行 contracts、方法政策及能力配置。

**事实链：** 实际代码和受测版本 → 不可变事件、文件和工具产物 → 可重建状态与结果。

代码与研究义务冲突时记录 `implementation_protocol_drift`，修实现或明确修协议；不能因为旧代码已这样运行而改变分母、方法或判题标准。机器格式注册只确认格式身份，不自行授予实验许可或结果信用。

### 0.3 本版的替换关系

| 项目 | 本版活动设计 | 不再作为活动约束 |
|---|---|---|
| 研究版本 | `paper1-v2.2`（2026-09-15 采纳） | v1.8／v2.1 的旧主总体 |
| 架构版本 | `sr2fpga-paper1-code-dev-v2.1`（2026-09-15 采纳） | [A] 的 PC2.0、四家族、旧案例与样本公式 |
| PC 格式 | `sr2fpga-pc-2.1` | System-HIS v1.2、PC2.0 |
| 统计单位 | `design_cluster_id`，必要时更高依赖组 | 将每个尺寸变体／semantic_instance 一律算独立 n |
| Direct 修复 | 完整替换或通用文件级替换 | 强制 M1 每轮重传全部工程 |
| 物理集合 | 三 AI 家族预选位置 | 用旧 FIR／Sobel L4 代替新总体 |

[P]/[D] 中“本次 PC 优化不改变四家族”的条款描述其交付时的范围，已被后续 [R] 的总体修订取代。本版显式采用该后续决定；不修改 [P]/[D] 的历史字节，不通过全局替换抹除上下文。

### 0.4 来源规则与本次实施决定

[R] 决定研究语义，[P]/[S1]/[S2] 决定当前 PC 字段与数学约定。本稿细化的 `TensorAbiMap`、文件替换交易、缓存键、诊断关联和服务接口属于实施设计。若原材料未确定实际工具、数值、格式或 API，列入附录 C，由实施与资格验证完成，不伪称已有标准或能力。

没有旧格式兼容要求不等于禁止复用代码。纯函数、工具封装和存储组件可重新审查后复用；历史结果不可重标为新结果。训练、旧任务和其他非核心资产不因本稿而删除。

### 0.5 状态与规范用语

“必须”为必要规则，“应”为默认实现取舍，“可”为不改变研究语义的选项。实现状态使用 `planned / prototyped / integrated / verified_in_scope` 并绑定证据范围；研究结果另行记录。

[R] 中的模型、预算、阈值和数量仍是候选／规划时，不因复制进本 SPEC 而自动冻结。验收不要求方法正向显著；文档完成不等于实验许可。

---

<a id="scope"></a>
## 1. 目标、范围和关键不变量

### 1.1 目标闭环

```text
冻结且可评分的 AI 子系统需求／公共资产／目标配置
  → MethodPolicy 选择 Direct、Structured 或 PC 路径
  → 完整 FPP，或保留原因的无候选终止
  → 总预算内公开检查与修复
  → 唯一候选或 terminal-null 封存
  → 批次屏障 → 独立隐藏验证与指定 L3 确认
  → 预选 AI 物理位置的 L4
  → 全分母结果、错误、成本及统计归约
```

输出对象是具有完整计算与接口义务的子系统，不是单个 JSON、MAC、空壳工程或展示 UI。合法的模块融合与拆分由公开任务决定；不强制与参考源码布局相同。

### 1.2 研究配置范围

核心为三个 AI 家族、M0–M5、PC2.1、结构构建、受限修复、独立 oracle 和三家族 L4 深度研究。B4 是首选候选预算；新 AI 开发测量后、paired pilot 前统一锁定。

第二模型、原生 Agent C0/C1、自然失败 probe 与张量消融属于独立次级人口，按 [R] 的预结果决定启用或省略。EA、A_req、训练生成模型、Q-table、完整网络 importer、DDR／PCIe／相机／SoC 和 L5 不进入最小核心依赖。

旧 FIFO、RAM、MAC、UART、fork/join、matched-filter 和 Sobel 保留开发／回归价值，不计入新的三家族主均值。

### 1.3 十二项不变量

1. **事实相同。** 各方法获得相同公开数学、张量、量化、ABI、资产和环境事实，不给 PC 分支额外参考架构。
2. **需求不变。** 模型不能改 bindings、需求、精度、时钟、有效输入域或公开环境假设。
3. **一份设计权威。** PC 的 design 为该分支架构源；ResolvedDesign、ABI、BuildPlan 是可删除重建的派生对象。
4. **构建不代写算法。** 不暗插 Conv、GEMM、FIFO、repack、requantize、fork、累加控制或 CDC。
5. **声明和实现分开。** 声明一致不等于 RTL 行为一致；not_evaluated 的义务不能变成 pass。
6. **首发真实。** M4 一次行为阶段覆盖全部单元，不按模块隐含增加请求。
7. **Direct 有有效修复机会。** M1 可按冻结协议局部替换模型文件；不能给它人为的全工程重传负担。
8. **共享包括失败。** 共同 PC/FPP 失败及前置费用一样共享，不清空后重新开始。
9. **预算不重置。** 改 PC、改源码、修格式、重建、重检和网络执行的实际消费均记录。
10. **隐藏不回流。** hidden／核心 L4 不影响当前或其他任务、条件、人工调参和候选选择。
11. **完整分母。** 设计失败、基础设施未知、实际完整性破坏及未观察状态分开；配置和用例不虚增独立 n。
12. **证据不晋升。** 原型、参考、开发、pilot、主实验、扩展和后验诊断具有独立身份。

---

<a id="architecture"></a>
## 2. 总体架构与执行域

### 2.1 模块化本地控制程序

沿用 [A] 的单协调器、有限并发或串行优先方案。不预建微服务集群、消息总线、复杂 ORM 或自由协商的多 Agent 系统。

```text
研究计划／样本与分析配置           公开任务／权重／profiles
            └──────────→ CampaignPreflight ←─────────┘
                                   ↓
                       FrozenRunContext + PopulationPlan
                                   ↓
                        PairedBlockCoordinator
                    ┌──────────────┼─────────────────┐
                 Direct         Structured        PC Planner
                    │              │                  ↓
                    │           Free FPP          PC Checker
                    │              │            ┌─────┴─────┐
                    │              │         Free FPP    Structure Builder
                    │              │                         ↓
                    │              │                  Batched Behavior Fill
                    └──────────────┴─────────────────────────┘
                                   ↓
                         Candidate Committer
                                   ↓
                      Public Worker → 公共诊断
                                   ↑       ↓
                        预算内 Repair Controller
                                   ↓
                  TerminalSelector → BatchSealBarrier
                                   ↓
                Hidden Worker → analysis-only Outcome
                                   ↓
                   固定位置的 L3／L4 后处理确认
                                   ↓
                 Outcome／Cost／ClusterAnalysis Reducers
```

公开周期可包含 L3；最终只读确认可复用同候选、同配置的有效报告。图中的 hidden 后处理协调器没有模型调用能力。原生 Agent 是 §19 独立入口，不伪装成 ModelGateway 的一次文本调用。

### 2.2 访问矩阵

| 域 | 可读 | 可写 | 禁止 |
|---|---|---|---|
| 生成／修复 | 公共投影、自己的 PC/FPP、允许的公共诊断 | 提议和原始响应区 | hidden、参考答案、完整仓库、任务生成器、凭据 |
| 受信控制 | 公共配置、方法、预算、候选引用、事件 | bindings、结构、封存、预算与事件 | 根据隐藏结果修复或调参 |
| public worker | 不可变候选、冻结公共 harness／工具 | 原始公共证据与允许诊断 | 改候选、需求、目标或访问 hidden |
| hidden worker | 封存候选、私有 suite 和独立参考 | 私有证据及 analysis-only 结果 | 调模型、换候选、修改原评分 |
| physical worker | 合格封存候选、固定目标与工具 | 资源／时序证据 | 修改源码、给核心提供修复反馈 |
| 离线分析 | 固定人口、合法结果、事件与测量 | 派生表、误差分析和声明清单 | 重新生成、选候选、获得额外原始评分 |

不同 Python 包或目录不是安全保证。实际 mount、权限、工作区和工具启动策略必须验证。隐藏参考程序可在评测进程中运行，但候选运行沙箱只接收允许的 HDL harness 和接口激励，不获得参考答案库文件访问权。

### 2.3 简单性边界

共用纯 reader／contract 是允许的，共用候选算法作为 oracle 不允许。状态机与文件事件先本地实现，确有瓶颈再扩并发；数据对象数量由真实生产者／消费者决定，不为关闭扩展创建空系统。

---

<a id="packages"></a>
## 3. 仓库组织与依赖

### 3.1 目标布局

以下目录是本版目标，不是已发现的仓库树。延续 `agent/src/sr2fpga_agent/` 组织位置；只在有真实工作时创建文件。

```text
contracts/
  manifest.json
  pc/2.1/
    project-contract-2.1.schema.json
    design-proposal-2.1.schema.json
  runtime/                       # 实际跨进程／持久化边界
  task-catalog/                  # 任务、身份、资格索引唯一入口

agent/src/sr2fpga_agent/
  core/                          # 类型、严格解析、hash、诊断、contract reader
  requirements/                  # 公共任务／资产／profile 的受信只读视图
  pc/
    binding.py
    validation.py
    elaboration.py
    tensors.py                   # descriptor、直接边界与有限关系
  build/
    planning.py
    abi.py                       # value/record/stream/tensor_beat 展开
    structure.py
    behavior.py
    fpp.py
  methods/                       # M0–M5 和输出／信息政策
  execution/                     # 共享 DAG、状态、修复、终止与恢复
  gateway/                       # 传输、原始响应、能力与计量；不做方法策略
  accounting/                    # 预留、计费、三视图
  storage/                       # blobs、不可变索引、append-only journal
  workers/                       # public/hidden/physical 独立进程入口
  analysis/                      # 设计簇归约、错误、成本、统计；无生成能力
  cli.py
  native_agent/                  # 只有 C0/C1 纳入后创建

agent/tests/
  unit/ contract/ integration/ tools/ isolation/ recovery/

评测方受限资源根（路径由环境配置，不挂载到候选域）/
  oracle/                        # 三 AI 家族独立位精确参考
  suites/                        # hidden inputs、expectations、编排
  qualification/                 # 正参考、变异和工具资格证据
```

公开任务及资产通过 catalog 引用；不再为新 AI 家族另建可与 catalog 冲突的任务数据库。参考源码与私有 suite 的开发存储可以有适当版本管理，但运行时候选看不到其所在完整目录。

### 3.2 依赖约束

`core` 不导入模型 SDK、EDA runtime 或 oracle。`pc` 和 `build` 只依赖纯核心与受信公开视图，不导入家族答案生成器或 `build_ai_examples`。`methods` 不接收私有 worker/store 实例。`execution` 仅持有受控 worker client；`analysis` 不回调生成执行。

`tensor_reference.py` 的现有辅助函数不能成为生产构建、checker 和最终 oracle 共同且唯一的算法权威。[R, §8.1] 可复用已交叉验证的公共格式 reader，但必须有独立黄金数据和实现核对，不能只依赖自己 pack 再自己 unpack 的往返测试。

### 3.3 单一活动路径

新 CLI 必须进入新 policy、executor 和 worker，不委托仍有旧 HIS 兼容、免费重试或隐藏修复的总控。允许重新验证后提取旧纯函数；不保留两个同时拥有方法语义的 runner。

非核心训练、历史 exporters、Q-table 和旧家族回归独立保留。它们不成为新核心安装／运行的必要依赖，也不应因本次文档更新被删除。

---

<a id="objects"></a>
## 4. 逻辑对象、身份与所有权

### 4.1 最小对象表

| 对象 | 生产者 | 主要内容与用途 |
|---|---|---|
| PublicTaskContext | 受信 loader | 冻结需求、公共边界、facts、资产、目标与能力 |
| PopulationPlan / RunPolicy | 实验准备与核验 | 三家族、设计簇／配置／重复、条件、预算、suite 与分析 |
| DesignProposal | 模型 | 直接的 design 对象，不含 bindings |
| ProjectContract | binder | schema_version、受信 bindings、design |
| PcCheckReport / CheckedPC | checker | 检查范围、逐层结果、解析类型、诊断和待验证责任 |
| ResolvedDesign / BuildPlan / AbiMap | 受信构建服务 | 当前配置实例、特化单元、信号布局、依赖与行为单元 |
| ProjectProposal / BehaviorBundle / RepairProposal | 模型 | 完整工程、批量 body 或已允许的修改 |
| FPP / CandidateEnvelope | committer | 实际源码与资产引用、依赖、来源、字节和受保护边界 |
| SharedCheckpoint | coordinator | 成功／失败起点、消费者、前置事件和消费成本 |
| TerminalRecord | selector/sealer | 配套候选／PC／build 或 terminal-null 及原因 |
| Event / StageOutcome / HiddenOutcome | 控制器与对应 worker | 实际操作、两轴状态、证据范围和计量 |
| AnalysisBundle | 无生成能力的分析器 | 全分母、设计簇估计、错误与成本三视图 |

内部可使用不可变类型和判别联合；不是每个类型都需要一个 JSON 文件或数据库表。

### 4.2 家族、设计簇、配置与重复

[R, §7.1] 的身份必须在计划、运行、终止、事件和归约中贯通：

```text
family_id
  → design_cluster_id
      → semantic_instance_id       # 一个冻结配置
          → replicate_id
              → condition_id       # 核心映射为 M0–M5
```

此外保存 `campaign_id`、`population_id`、`paired_block_id`、`action_id`、`candidate_id`；存在共同来源依赖时保存 `dependency_group_id`，否则显式不适用。配置身份仍用 semantic_instance，不新增一套可分歧的 config_id。

同簇内维度、lane、权重替换和措辞变体不是新独立 n。跨家族共享来源由 dependency group 或正式前的无交叉来源划分处理。私有分簇／split 标签不自动进入模型；公开任务已有的算法名称不必刻意删除。

### 4.3 唯一性和映射核验

建议每个 campaign/population 内 semantic_instance 唯一映射到一份任务版本、family、design_cluster 和依赖身份；同一内容出现在第二模型等人口时记录相同任务来源，不能计为新的独立需求。

PairedBlockKey 由 campaign、population、semantic_instance、replicate 确定；方法是该块的消费者，不决定共同 PC 身份。父子关系、重复位置和配置权重均由 manifest 给出，不能从实际成功文件倒推。

### 4.4 字节身份和派生缓存

受信源与原始模型响应按实际存储字节计算 SHA-256。固定序列化可用于新派生对象，但不得把两个语义相同却字节不同的原始输入冒称同一 hash。候选摘要包含排序文件记录和相关受控字段，不包含摘要自身。

哈希不是授权或签名。缓存只有内容一致性语义，访问权由执行域实施。summary、trajectory、状态和表格都是派生视图；不得独立手改 `success=true` 形成权威。

---

<a id="requirements"></a>
## 5. AI 公开需求、资产与能力准备

### 5.1 不重新发明 Requirement Envelope

从仓库已有且完成裁定的公开对象构造只读 PC checker 视图；复用 [P] 所需的 boundary、facts、required_trace_facts、public_assets 等职责。若现有对象无法表达必要事实，应显式升级公共 contract，而非在模型侧补字段或复制第二份可编辑需求。

bindings 绑定原始受信对象；adapter 的版本、投影结果与源字节关系可审计。现有 PC 原型示例输入是适配样例，不自动成为生产任务格式。

### 5.2 所有方法获得同一可执行含义

公开面必须给出实际 RTL top、ABI、完整算子图、kernel/padding/stride、权重/Bias、类型与量化算法、中间精度、调用与复位、源／下游停顿和完成规则。内部结构未被明确约束时允许自由实现。

入口 PC 的 `signature.source=requirement_boundary` 引用这些事实；Direct 和 Structured 同样获得边界表和规则，但共同封装不自动替它们生成顶层 RTL 或接线。

任务描述不能依靠“标准 CNN”“正确 INT8”“适当缓存”留下判题所需的关键空白。隐藏 suite 只隐藏输入、编排和期望值，不隐藏算法规则。

### 5.3 三种零和量化 profile

必须区分：数学 padding 的实数零；有 mask 的无效 lane raw 0；有效 raw 0 在其 affine 编码下的数值。对非零 zero-point，不能让它们互相替代。[R, §6.1]

PC `exact_affine_v1`／`exact_affine_sum_v1` 是声明的精确数值关系，不是自动的 LiteRT/FINN kernel 兼容。实际 Conv/GEMM 的中间运算、Bias 与激活顺序仍由公开任务和独立参考定义。若采用受限尺度集合，应公开其范围并经工具资格验证；本 SPEC 不擅自固定二的幂、乘数／移位或新舍入规则。

### 5.4 公开资产与私有激励

权重、Bias、初始化和必要规范文件属于所有方法等价可用的公开资产，记录身份、字节、类型、排列、尺寸、量化及许可来源。asset ID 存在不代表字节、元素数或顺序正确；loader/worker 在使用前核验。

隐藏激活、矩阵输入、压力顺序和期望输出由 harness 注入，不挂载为候选可读文件。对固定权重的特化实现可以合法；对运行时可变矩阵，不得擅自常量化。是否可装载／更新由任务卡决定。

### 5.5 task-ready 与 candidate-unsupported 不混同

正式运行只验证并加载 frozen ready context，不重新问答、近邻匹配家族或选择较容易任务。候选选择了 unsupported 协议、超限张量、过长输出或非法架构，按候选设计失败计入分母。

若任务本身不自洽、参考或目标不能执行，是任务资格／协议问题；记录受影响位置和依据，不能利用模型失败选择性回写 capability_gap。具体处置遵循 [R] 的结果前修订和正式后完整性规则。

---

<a id="pc"></a>
## 6. PC 2.1 解析、语义检查与 H-stage

### 6.1 两份 schema，一个 design 定义

完整 PC 的结构不变：

```text
schema_version: sr2fpga-pc-2.1
bindings:
  requirements: {id, sha256}
  target_profile: {id, sha256}
  capability_profile: {id, sha256}
design:
  entry
  modules
  requirement_map
  notes?                         # 非规范说明
```

模型输出根直接为 design 内容，不另套一层 `design`，不提交 bindings。binder 只用受信上下文组装完整 PC，随后运行完整 schema 与绑定核验。两份 schema 必须同源生成或在 CI 核对 `$defs` 和根引用，不分别手改。

本稿不更改 [S1]/[S2] 的字段。注册版本、schema hash、checker 版本和验证 policy 分别保存；研究升级不意味着 schema 随之升版。

### 6.2 解析、层次、参数与类型

严格解析拒绝重复 JSON key、非法浮点／非有限字面值、超限大小和深度。PC 的整数规则不能被误用于包含测量小数的成本、时长或统计对象。

参数使用 PC2.1 继承的有限非负 AST；禁止 eval、任意 HDL 表达式、模型 `resolved` 和隐含参数默认。检查引用、范围、除零、负中间值和零宽。当前绑定配置通过，不代表整个参数域成立。

模块、端口、实例和状态按作用域处理；拒绝定义递归与不可达模块。value 可显式扇出，stream 点对点；每个接收端必须有合法驱动，端点仅为 self 或直接子实例。组合模块可不消费时钟／reset，clocked 不等于不存在 ready 组合环。类型匹配包括 record 顺序、signedness 和定点小数位。

### 6.3 新 H-stage 的责任映射

下表沿用 [A] 的分层并按 [D] 加入张量机制；它是本版待注册验证 policy，不继承旧 W-rule 或 dry-lower 通过记录。

| 步骤 | 内容 | 输出与限制 |
|---|---|---|
| 解析／绑定 | 原始 JSON、受信源身份、PC 绑定关系 | 控制器或源加载故障不得算模型语义错误 |
| H0 | DesignProposal 与完整 PC schema | 字段、判别分支、有限表达式形状；不解释算子数学 |
| H1 | 引用、参数／类型展开、层次、方向、驱动、域；tensor descriptor 和有限关系自洽 | 解析类型、诊断位置、匹配结果；不运行 emitter 或独立 oracle |
| H2 | 当前 capability profile、资源化展开限制、已实现 tensor 支持域 | 不支持的候选设计明确拒绝；不先成功试综合来筛共同 PC |
| H3 | requirement binding、fact role、关联覆盖及已定义可比较值 | 不把关系条数、trace 覆盖或自然语言 intent 当完整 fidelity |

前层失败时后续层标 not_run。可共用一次纯展开，但结构源码不能成为准入依据。M3 必须能够完全不调用 M4 的 emitter/filler 得到同一 PC 准入结果。

### 6.4 张量 descriptor

`signature.tensor_contracts` 为签名内命名契约；`stream.payload` 的 `tensor_beat` 引用该局部定义。比较展开内容，不要求不同模块使用同一个局部名字。[P, §§3–5]

| 面 | 必须实现的检查 |
|---|---|
| shape | 轴名唯一、extent 在实际参数环境中为正，轴集合一致 |
| element | 按 profile 允许的 uint/sint 和位宽；当前 tensor element 上限沿用 [P]，不扩大成任意类型 |
| quantization | integer 或已定义 affine；正最简有理数、范围可表示、zero-point 合法 |
| per-axis | 轴存在；scale／zero-point 表长度等于逻辑轴 extent；按逻辑坐标解释，不按 lane |
| layout | order 为全部轴的排列，从慢到快；lane_axis 为最快轴；lanes 合法 |
| tail | exact 要求整除；zero_pad_mask 明确 mask 和无效 lane；不自动修正 |
| sequence | dense 或 partial_sum；frame/reset 引用公开保证；groups、group_order 和归约轴合法 |
| 名字与使用 | 引用存在，未用契约不保留为隐藏语义；对象键顺序不是遍历顺序 |

直接 net 必须保持 shape、element、quantization、layout 和 sequence。总位宽相同不意味着兼容；不可用 raw bits 擦除冲突后仍宣称做了 tensor 检查。

### 6.5 有限关系与缓冲

`behavioral.tensor_rules` 检查 identity、fork、repack、requantize、zip_add、reduce_sum 和 compute 的声明关系。每个行为模块 tensor 端口恰好属于一个主关系；不重复伪造输入或遗漏输出。

| 关系 | 必需检查 | 不能据此获得的结论 |
|---|---|---|
| identity/fork | 输入输出完整契约匹配 | 实际无丢失、复制次数正确或无死锁 |
| repack | 保持逻辑形状、数值和序列，允许声明的布局改变 | 重排硬件已经存在或无需缓存 |
| requantize | 形状／布局／序列关系及显式数值模式 | 实际逐位舍入和溢出正确 |
| zip_add | 同调用／同坐标的形状、布局和序列相容，数值模式合法 | 两条真实 RTL 支路不会错配 |
| reduce_sum | partial_sum→dense，组、编码、宽度、清零／提交声明符合 [P] | 所有组实际到齐、Bias 一次或正确累加 |
| compute | 端口、方向、域和 fact 引用 | Conv／GEMM 数学、内部布局或所有状态符合 |

`buffer_rules` 将本地同域 FIFO 绑定到相同 tensor 契约的输入输出，容量单位为完整 `beats`。深度合法不等于充分；不按 latency、II 或数据量猜测通用安全 FIFO 深度。

### 6.6 数值语义不暗中替换

精确 affine 关系、same-scale centered sum、舍入枚举、输出范围与 reduce 溢出按 [P] 执行。per-axis 参数按逻辑坐标而不是物理 lane 索引。归约规定先完成全部组求和再处理最终溢出；不能把逐组饱和或提前重量化视为同一操作。

本稿不补写未定义的 Conv kernel、整数乘数／移位近似或 bias 规则；这些由已冻结 task/kernel profile 和独立参考裁定。发现无法综合的允许算法时，先修能力／任务资格并版本化，不能在模型结果后换数值标准。

### 6.7 报告与错误来源

PcCheckReport 至少保存源 PC/context/schema/checker/profile 的 hash、适用规则、逐层状态、JSON Pointer／实例路径、展开类型和 `deferred_checks`。新增 `verification_obligations` 初始为 `not_evaluated`，它是待验证责任，不是最终 oracle。

来源原因分别为候选设计、受信实现、基础设施和完整性；实际分类与 [R] 对应。候选错 layout 是候选问题；binder 拼错 hash 或 emitter 崩溃不能伪装为模型不会设计。

当前原型报告使用的静态范围应保留。正式接入后的新报告必须证明生产路径实际调用了这些规则，不能只复制 [T] 的通过数字。

---

<a id="build"></a>
## 7. 确定性构建、Tensor ABI 与派生身份

### 7.1 构建链

```text
CheckedPC + 受信 PublicTaskContext + 固定构建配置
  → ResolvedDesign：本配置的参数、类型、域与 tensor descriptor
  → BuildPlan：层次实例、特化单元、文件角色、行为责任
  → AbiMap：逻辑接口到真实信号；包括 TensorAbiMap 视图
  → StructureArtifactSet：受保护结构和行为签名
  → BehaviorComposer：批量 body 装配
  → FPP + 外部 CandidateEnvelope + construction_origin_map
```

TensorAbiMap 是 AbiMap 的派生部分，不是新的模型权威或必须独立保存的 schema。展开与源码的消费者只能读源 PC 及固定配置，不根据 family ID 调用参考生成器。

### 7.2 允许与禁止生成的内容

允许：模块头、显式参数特化、实例、纯连线、常量、record／lane／mask 的位布局、ready 反向线、源码清单及受控构建元数据。

禁止：隐式 FIFO、fork/join、仲裁、repack 的存储调度、requantize 算术、Conv/GEMM、累加状态机、自动流水化、截断／舍入／饱和、同步器或放松目标约束。

“显式声明了关系”不授权构建器把关系变成算法模板。受信结构输出与模型负责的算法体始终分开，来源图可重建。

### 7.3 Tensor beat 的精确物理布局

沿用 [P]：设元素存储位宽 b、lane 数 L。lane 0 在低位，lane j 的元素占 `[j*b +: b]`；有 mask 时其位 j 对应 lane j，并放在全部 payload lane 的高位。由此：

```text
lane_bits = L × b
mask_bits = 0                       当 tail=exact
mask_bits = L                       当 tail=zero_pad_mask
beat_bits = lane_bits + mask_bits
```

beat_bits 不包含独立的 valid/ready 信号。把 packed bus 当无差别有符号整数会丢失元素含义；需要逐 lane 解释 signedness、scale 和 zero-point，不自动在连线上施加转换。

例如两个 INT8 lane、zero_pad_mask，载荷为18位。无效 lane 必须 mask=0 且 raw bits=0；其值不参与计算，不等同数学 padding。上述规则须以明确十六进制黄金拍、坐标与符号边界例测试，不能只做自实现往返。

### 7.4 顺序、拍数和逻辑身份

shape 的列举顺序不决定遍历；layout.order 从慢到快，最快轴沿 lane 展开。若最快轴大小为 D，其余轴大小乘积为 P：

```text
dense_beats_per_invocation = P × ceil(D/L)
partial_sum_beats_per_invocation = dense_beats_per_invocation × groups
```

exact 分支事先验证 D 整除 L。拍数按 valid&&ready 的被接受事务计数，不按时钟计数。outermost／innermost 的 group 顺序严格按 [P] 定义，不用文件枚举或循环实现默认代替。

固定形状的有序调用通过拍数和公开边界隐式定位；不为了验证方便自动给硬件增加坐标、invocation_id 或 group_id 管脚。scoreboard 可以在评测器内部重建这些逻辑身份。

仅变更 AbiMap 中的 order 不能完成跨周期重排。若 PC 前后布局不同，应有明确行为边界；实际数据变换仍需独立功能验证。

### 7.5 参数特化、命名与单元复用

本版优先对任务实际绑定配置生成特化源码。相同模块定义、参数和相关语义可复用一个行为单元；不同实例的状态仍各自独立。符号 ID 不直接作为路径；固定命名处理保留字、大小写、长度和碰撞，top 实名与外部 ABI 来自任务。

构建顺序、序列化和路径规则固定，不依赖 Python 随机 hash、临时绝对目录或文件系统顺序。相同输入和固定构建配置应产生相同的受信结构字节；模型生成 body 本身不因此成为确定性结果。

### 7.6 语义完整的依赖键

本次实施细化要求：BuildPlan 与 unit 的身份覆盖任务绑定、module definition、参数环境、域／复位、完整 tensor descriptor、关系规则、资产依赖、ABI／emitter／checker 和能力版本。比较可先保守使用整体依赖摘要，不要求提前做最细失效分析。

shape、轴序、尺度、零点、per-axis 表、lane／mask、frame/reset、groups、group_order、numeric/timing/buffer rule 任何相关变化，即使 beat_bits 相同，也使旧行为不能自动复用。

默认只允许同一候选装配内的相同特化复用，以及研究明确允许的共享起点；不因缓存键恰好相同而跨任务、跨条件共享模型答案。结构性派生缓存、provider 计费缓存和模型答案缓存必须分别处理。

### 7.7 目标约束与构建资格

工具脚本、SDC/XDC 和目标资源政策来自受控 target profile。模型不能改时钟、添加 false path、弱化资源上限或改变 launcher。不同工具约束生成器分别验证；未覆盖 I/O 的 OOC 结果不称完整时序闭合。

结构生成完成只证明对应构建义务；实际 RAM/DSP 映射、权重加载、数学结果和工具支持需要后续证据。能力失败、候选错误和构建器自身异常保留不同原因。

---

<a id="fpp"></a>
## 8. 批量行为、装配边界与完整 FPP

### 8.1 BatchedBehaviorFill

M4 初始第二阶段以一次逻辑模型调用生成全部必需行为单元。输入为完整公共事实、PC、解析后的 tensor 契约、关系与待实现单元、受保护签名及可用语法。不得在工具内部逐模块请求或多次修 JSON。

建议沿用 [A] 的运行提议对象；这是实现 contract，不是新增 PC 字段：

```text
BehaviorBundle
  schema_version
  build_plan_sha256
  units: { unit_id: { body: string } }
```

模块头、端口、模块名和结尾由 composer 提供，body 为模块内部代码。每个 required unit 恰好出现一次，未知 unit 拒绝；一份特化多实例只填一次。缺单元、截断和格式错误保留原响应，不补空行为、不免费再请求。

无行为单元时按已定义条件跳过并记录不适用，不为凑调用数生成空响应。反过来，源配置容量不足时不能在正式任务中偷偷拆分调用；开发期统一调整方法预算或能力范围并重新冻结。

### 8.2 装配和真实解析

在受控 scratch 内组装，再进行真实 parser／elaboration 检查。首版采用有资格证据的可综合 HDL 子集；本稿不指定未经核查的现有安装版本。

必须验证生成后的模块签名、参数、域、实例与受保护结构一致；没有额外模块、跨文件宏影响、任意 include、外部调用、层次窥探或隐藏子模块。局部变量、函数、常量与实现状态可以按能力政策开放；新的架构子模块应通过 PC 表达。

不能用注释哨兵或正则搜索替代语法边界。PC 的架构状态不要求与每个 RTL 寄存器同名；实际写者、更新和 RAM 语义由适用工具／行为检查判断。

### 8.3 完整、合法和正确分开

完整文件集合不等于语法正确，语法正确不等于协议或计算正确。Direct 的完整工程可进入 L1 后失败；M4 body 若使保护边界无法确认，则保留可修提议与诊断，而不是伪造可封存 FPP。

成功拦截越界是无效尝试，不是实际受信文件已被破坏；后者才是完整性事件。common L0 不要求 Direct 提供 PC、tensor_rules、build_plan 或 H 报告。

### 8.4 方法中立的 FPP

必需交付为完整实际 RTL、声明式 manifest、top 与外部 ABI、依赖和语言／配置、适用约束引用，以及必需合法权重／初始化资产或受控不可变挂载引用。

权重挂载方案可以避免重复复制，但重建环境必须按同一引用装载相同字节，并使依赖闭包可核验；不得把尚未提供的文件链接当作完整资产。固定权重与运行时输入分开。

源路径可由 Direct 合法选择，不强制 `rtl/top.sv`。候选 TB、QoR、PC 和内部结构计划均非 universal required。候选脚本不成为 worker 的执行入口，候选 self-test 不授予公共或隐藏通过。

### 8.5 外部 envelope 与来源

committer 从实际文件构造 CandidateEnvelope，包含路径、角色、byte hash、方法、creation event、parent、PC/build 身份（适用时）和受保护边界。候选自填 ownership、editable、verified 不可信。

`construction_origin_map` 区分公开边界／资产、受信结构、模型行为和已声明平台。组合文件记录可信签名和模型 body 的来源，不将整文件误标为单一作者。模型少写了多少行仅是实现负担指标，不能代替工程难度或正确性。

---

<a id="methods"></a>
## 9. 方法策略、模型网关与公平输入

### 9.1 唯一方法表

| 条件 | 首发 | PC checker／结构构建 | 后续动作与终点 |
|---|---|---|---|
| M0 Direct | 一次完整 ProjectProposal | 不适用／禁止 | 无修复，@initial |
| M1 Direct-Repair | 共享 M0 初始尝试 | 不要求 PC／禁止结构构建器 | 通用工程修复，总预算终点 |
| M2 Structured-Direct | 一次无类型计划＋一次自由工程 | 不使用 PC 语义／不构建 | 无外层修复，@initial |
| M3 PC-Free | 共享 PC 规划＋一次自由工程 | 同一准入检查／禁止 emitter、filler | 无外层修复，@initial |
| M4 PC-Skeleton | 共享 PC＋一次批量行为 | 同一准入检查／受信结构 | 无外层修复，@initial |
| M5 PC-Online | 共享 M4 完整初态或失败 | 同一初态，后续可重检／构建 | design 或行为修正，总预算终点 |

B4 采用时总预算终点标 @B4；若研究在新 pilot 前批准其他命名预算，输出必须使用对应身份，不能继续标 B4。M0/M1/M2 的 H-stage 是 not_applicable；M3/M4 共同 PC 失败仍进入端到端分母。

M2 的 generic plan 可有 summary、file_plan、implementation_notes 等一般字段，不引入 PC 语义规则。M3 能看同一 PC 与公共事实，但不得看 M4 的结构源码、行为空洞或成功构建报告。

### 9.2 输出格式与资源机会

模型看到的数学、量化、资产、ABI 与公共工具事实等价。格式、checker 和编辑面的差异只来自预声明 treatment；不能一侧得到完整数值规范，另一侧只有短提示。

M1 的文件级修改按 §11 实施，不强迫全工程重传。M3/M4 各阶段最多一次，批量单元不另获调用。真正额外的 router、诊断或格式修正请求仍消耗总调用。

M4−M3 比较构建／编辑联合机制，不能单独归因 tensor checker；M5−M1 是整个流程比较。native C0/C1 与独立消融见 §19，不混为 M1 或新增核心方法。

### 9.3 ModelGateway

只负责传输、实际响应、使用量、停止原因和提供方／模型配置，不决定方法、family、修复或评分。禁止自动切模型、补 JSON、补缺文件、提高输出长度或 best-of-N。

SDK 重试关闭或接入已冻结可观察 policy。请求字段是否生效由实际接口核验；不能静默忽略不支持字段。Schema 默认只用于验证，受限解码是必须明确记录的额外方法配置。

保持分支会话隔离，受控共享必要的规划上下文也进入信息与 token 记录；不能共享其他分支的后继修复或跨任务答案。复用实际 provider 缓存计费不等于允许答案缓存。

### 9.4 模型、随机性与漂移

主模型／第二模型、精确版本、量化、tokenizer、上下文和解码由开发域选择并冻结，不限定必须小模型或某块 GPU。replicate 不等于模型 seed；调度 seed 与 provider seed 分开。

缺乏可核验 seed 时可采用 [R] 的 stochastic_blocked，报告冻结提供方配置下的测量，不声称同随机流或逐字重放。模型／工具身份变化按冻结规则暂停或另建条件，不混成同一研究结果。

---

<a id="paired"></a>
## 10. 共享起点、调度与预算图

### 10.1 共同起点 DAG

```text
S_D：一次 Direct 首发 ───────────────────→ M0、M1
S_C：一次 PC 规划＋共同 PC 检查 ──────────→ M3 自由生成
                          └→ S_B：构建＋批量行为 → M4、M5
U_P：M2 无类型计划 ───────────────────────→ U_F：自由工程
```

S_C 保存完整初始 PC 或其失败尝试，S_B 保存完成行为填充的完整工程或对应失败，不是仅有空 skeleton。M4/M5 必须消费同一不可变 S_B，而不是分别再请求模型。每个方法保留独立结果行、后继候选和终止槽。

### 10.2 失败共享

| checkpoint | 内容 | 结果处理 |
|---|---|---|
| pc_failure_checkpoint | 原始 proposal、可解析部分、H 诊断、来源和前置消费 | M3/M4 初态失败，M5 按余量纠正 |
| project_failure_checkpoint | 输入、适用 PC、工程或 body 提议、缺失／错误与成本 | 无完整 FPP；修复条件可按 policy 继续 |
| project_checkpoint | 完整不可变 FPP、适用 PC／build／envelope | 按方法进行公共检查与后继修复 |

有效 PC 尚未生成工程时是规划节点，不伪造 project_checkpoint。依赖阻塞阶段记 dependency_blocked，不生成假模型调用、空工程或零成本成功。共享前置基础设施异常按原因闭合，不能一律标成 PC 设计失败。

M1 后继不回流 M0；M5 后继 PC/RTL 不回流 M3/M4。不同消费者不得修改共同前置对象。

### 10.3 可核验调度

先由纯函数生成节点、前置边、消费者和各方法归因闭包，再按冻结的本地 seed 为可执行节点安排顺序，在块间平衡可平衡位置。记录实际开始、完成、排队和服务时间。

共享前置约束下不能宣称任意六方法排列都成立；不直接沿用旧 Williams 行替代真实 DAG。默认先串行；并发前补齐预算预留、消费者关系和事件原子性测试。

### 10.4 调用数量由图派生

在 [R] 的 B4 核心配置下：

| 视图 | 共享初始 | 正常追加上限 | 完整配对块上限 |
|---|---:|---:|---:|
| 实际去重逻辑调用 | 6 | 3＋2 | 11 |
| 六方法独立运行归因 | 10 | 3＋2 | 15 |

若 PC 提前失败，M5 的阶段分配变化，但跳过的初始行为调用也被扣除；由各方法总上限重新计算，不能逐阶段各发一份预算。逻辑调用不是外层 CLI 次数，也不是所有 transport attempts 的简单数量。

一般正式容量为 `blocks=3*n*c*r`、`method_results=6*blocks`；不等簇数／配置数时从完整 PopulationPlan 求和，不将等规模公式写死在 runner。原生 Agent 的计量不使用此表。

### 10.5 证据复用与三成本视图

实际成本对 event_id 去重；独立运行视图对每个方法取完整依赖闭包、计入必要全部前置成本；增量视图固定共享 checkpoint 起点。

同候选、同 suite、同工具／环境的原始 public 检查可按 policy 复用，但每个消费者仍消耗等价检查机会并计独立成本。方法特有保护检查分别执行。hidden 不借内容相同而跨条件复制分数；每个冻结评分槽仍独立闭合。

共享成本不按消费者人数摊薄为单方法费用，也不只记给第一个运行的方法。并行服务时间之和不能冒充独立部署 wall-clock。

---

<a id="repair"></a>
## 11. 生命周期、M1 文件级修复与 M5 两层修复

### 11.1 状态机

```text
PLANNED → CONTEXT_VERIFIED → INITIAL_NODE_CONSUMED
  → PC_CHECKED / PROJECT_PROPOSED
  → CANDIDATE_COMMITTED → PUBLIC_EVALUATED
  → REPAIR_PROPOSED → REVALIDATED → CANDIDATE_COMMITTED
  → TERMINAL_SEALED | TERMINAL_NULL
  → BATCH_SEAL_BARRIER
  → HIDDEN_SLOT_CLOSED
  → L3_CONFIRMED_OR_UNRESOLVED
  → PHYSICAL_SLOT_CLOSED（预选位置）
  → OUTCOME_RECONCILED
```

每个计划位置必须闭合。控制器允许动作，模型不能调用评分、强行通过、提升 budget 或恢复旧状态。禁止从 hidden/L4 回到 repair；正式封存后不替换原候选。

### 11.2 动作表

| 条件 | 动作 | 约束 |
|---|---|---|
| M1，无完整候选 | replace_project | 一次生成新的完整工程提议；保留已有失败与费用 |
| M1，有完整候选 | replace_project 或 replace_project_files | 后者为通用文件级替换；只做字节装配，不接线或补算法 |
| M5，PC 非法 | replace_design | 一次只输出 design，原 bindings 保持，重新全部检查 |
| M5，PC 合法但缺 body | replace_behavior_units／完整行为 bundle | 对同一 build plan 补齐；花费一次剩余调用 |
| M5，已有 FPP 行为错误 | replace_behavior_units | 只替换允许单元，保持配套 PC 和结构 |
| M5，需改变架构 | replace_design | 新 PC／BuildPlan；需要新行为时再用余量调用 |

动作判别可由确定性规则和同一次响应完成；单独 router 模型请求也计费。M1 文件级修复由 [R, §5.4] 明确允许，下面是本版的实施细化，不是放宽候选修改评测标准的权限。

### 11.3 M1 文件替换交易

建议一个修改提议绑定父候选摘要，并包含完整文件内容，不做脆弱的行号 diff：

```text
ProjectFilePatch（运行 contract 提案）
  schema_version
  action: replace_project_files
  base_candidate_sha256
  files: { safe_relative_path: replacement_text }
  remove_paths: [safe_relative_path, ...]
```

`files` 可替换已有模型源码或新增合法模型源码；同一路径不能既替换又删除。无需 rename 操作，改名用新增／删除明确表示。新删源或 top 变化时，必要的声明式 manifest 在同一交易中一致更新。

禁止修改受信需求、资产原始内容、targets、工具 policy、公共／隐藏 harness、真实 envelope、事件与预算。M1 可重构模型拥有的内部 RTL 和 top 源码，但最终必须继续满足原公共 ABI；它不受 M5 的内部模块拓扑保护约束。

实施顺序：核验父 hash → scratch 中应用全部字节修改 → 核验路径／依赖／manifest／适用安全约束 → 原子提交新候选 → 运行预算内公共检查。应用器不能修模块接口、自动添加源码或猜测缺失内容。

修改失败只保留被拒提议与原候选，不半提交；不能自动换用对照未获声明的“智能 merge”。空内容集合或字节完全不变仍计本次调用，但不记有效修复 transition。未形成过完整候选时优先 replace_project，避免以残片随意指定基准快照。

### 11.4 M5 design 更新与语义失效

替换 design 后重新 binder、H 检查、类型／tensor 展开与结构构建。首版对改变的 design 保守全量失效旧行为 bundle；若后续优化依赖闭包，须有语义完整的缓存键和回归测试并预先冻结政策。

不能只检查端口位宽未变就复用：量化表、遍历、lane、mask、groups、关系和资产变化都可能要求新行为。原候选与其原 PC/build/envelope 不变；新分支没有完整结果时，按原终止政策保留先前最后一个有效完整候选及其原配套对象。

一次 replace_design 响应不能偷带新完整 RTL 并被按一次原协议规划调用解释。需要分阶段的生成成本必须真实计入。

### 11.5 修复事实与终止

合法非空变更、之前的公共诊断和实际重跑共同形成 repair transition。H 错误、attempt_id 变化或出现 repair 文件夹均不是充分证据。PC纠正、行为修复、一般工程修复分别计数。

M1/M5 最早满足冻结公共接受谓词时停止，否则到总预算边界选择最后一个完整且边界有效的 FPP；无则 terminal-null。无效／重复提议不触发未注册的 NoProgress 提前停止。

对最后一次未完成公共检查的候选，可封存但不授予通过；固定最终只读检查补齐必要证据时另计最终验证费用，不反馈模型、不选择另一个候选。已有精确匹配的报告可按 policy 复用。

### 11.6 安全失败与方法失败

被保护层拦截的越界修改是无效候选动作，可按剩余预算继续。实际受信对象被写坏、hidden 泄漏、评分槽／事件谱系被篡改属于完整性事件，应停止受影响范围。不得把成功防御等同已经发生数据泄漏，也不得让实际破坏靠再写一个合法补丁自动恢复信用。

---

<a id="budget"></a>
## 12. 预算、计量与事件

### 12.1 候选 B4 的实际含义

M1/M5 各最多四次逻辑模型调用、最多四个公共完整检查周期；正常 M1 为1＋3，M5为2＋2。M0最多一次，M2/M3/M4每个声明阶段最多一次。[R, §10]

共同冻结累计输入／输出 token、单次输出、上下文、工具子调用、CPU／内存、活动时间和 EDA 上限。每个 public cycle 列出实际工具及执行／跳过规则。PC纯检查时间同样计量；装配若调用外部 parser/elaborator，保存实际子调用和预定预算归属，不把它藏成零成本。

B4 不是永久架构常量。开发测量后可在新 pilot 前批准其他命名预算；后续改变须新协议，不允许某分支临时放宽或保留失实终点标签。

### 12.2 预算交易与未知消费

所有资源副作用按 `reserve → dispatch → observe → commit/reconcile` 处理。确定尚未分派可释放预留并留事件；远端是否执行未知时不当作零消费。

使用实际 tokenizer／接口计量核验可计量轴。usage 缺失保留 unknown 和原因，预留上界只能用于限制后续动作，不能填成实测。cached/reasoning token 的包含关系按所选接口映射，避免重复求和；不同 tokenizer 的原始 token 不叫等 FLOPs。

budget_status 为 compliant、exceeded 或 unverifiable。成本不可核验不等于超限，也不等于合规；功能事实继续保存，等预算声明资格单独受限。

### 12.3 最小事件内容

```text
identity:
  event_id, stream_id, sequence, parent_event_id, action_id
context:
  campaign_id, population_id, paired_block_id, semantic_instance_id,
  condition_id 或 shared_node_id, sample_mapping_ref
operation:
  stage, event_type, outcome_class, reason_code
artifacts:
  input_refs, output_refs, parent_candidate_ref, resulting_candidate_ref
accounting:
  reservation_ref, observed_usage, unavailable_reasons,
  dispatch/start/end/service/queue 时间
provenance:
  source_class, model/provider/tool/config refs
visibility:
  generation_public | control_only | evaluator_private | analysis_only
```

sample_mapping_ref 指向不可变的 family/design_cluster/dependency/config 映射，事件可冗余关键身份但必须与该映射核对，不能各维护一份可冲突的簇信息。来源 natural_model/synthetic_fixture/reference 与错误原因是不同轴。

### 12.4 成本输出

分别报告模型与重试、PC规划／检查／构建、行为、修复、public、最终 hidden、L3和L4，以及离线任务／oracle／负载处理和工具适配成本。失败者不能从均值删除。

实际去重、独立运行、增量三视图按 §10 生成；若真实独立部署时延未测量，只报告归因服务时间，不把并行运行的服务和当作用户等待时间。

### 12.5 网络重试不成为免费采样

已证明幂等可重取原结果；确认原请求未执行时可按记录再分派；原请求状态未知时保持不确定，只按冻结政策停止或消耗新的合法调用。不能把得到第二份可选响应的重试记成同一次生成。

原始响应、计量和异常尽早落盘；默认禁止 SDK 隐式 best-of-N、隐藏 retry、模型 fallback 或自动提示纠错。

---

<a id="storage"></a>
## 13. 存储、封存与恢复

### 13.1 最小持久化

采用本地内容地址 blobs、不可覆盖对象索引和追加 journal。单协调器先简化写入；并发需要明确锁、事务／原子发布与恢复测试，不因“通常不会同时写”省略保证。

```text
run_root/
  public-inputs/             # 已核验的公开输入与资产
  proposals/                 # 原始模型响应与拒绝提议
  blobs/                     # 访问按域限制，非全部挂载
  control/                   # population、policy、预算、DAG、journal
  candidates/                # 不可变快照与候选 envelope
  public-diagnostics/        # allowlist 的修复可见投影

evaluator_root/             # 不在候选读写域
  references/ suites/ raw-results/ semantic-slots/ analysis-outcomes/
```

临时 scratch、不可变候选与报告分开。完整 blobs 或仓库不得挂载给模型；摘要不透明不能替代真实访问控制。

### 13.2 路径与依赖

候选路径为受控相对路径，拒绝父目录、盘符／UNC、分隔符混用、符号链接越界、控制字符和声明外依赖。实际目标路径在使用时核验，不只做字符串前缀比较。

HDL 的 include、系统调用、DPI/FFI、层次窥探、宏和加载资产按预先定义语言政策检查；合法 `$readmemh` 只读取 manifest 中已经核验的公开资产。评测器的驱动设施不因此向 DUT 放开任意文件访问。沙箱不宣称防住所有未知工具漏洞。

### 13.3 Commit 与 TerminalRecord

提议在 scratch 完成必要的安全／边界检查后写 blobs，最后原子写 candidate 索引。候选摘要不包含自身；reader 使用前重验关系与字节。

TerminalRecord 绑定 candidate、配套 PC/build/envelope（适用时）、公共接受状态、选择策略、预算、模型和工具上下文。无候选为 `terminal_candidate_ref=null`，保留上游失败／基础设施原因与成本，不删除结果槽。

M0/M1或M4/M5可共享内容但仍是不同条件终点。seal 不等于全部功能已验证，后续 worker 仍按固定步骤检查。

### 13.4 恢复表

| 中断情形 | 恢复要求 |
|---|---|
| reserve 后且确定尚未分派 | 继续同 action 或释放预留，保留事件 |
| 响应字节已落盘、完成事件缺失 | 重验原响应后提交事件，不再请求模型 |
| 远端执行状态不明 | 按已验证查询／幂等规则，否则 unknown；不盲目采样 |
| 文件替换 scratch 完成但未 commit | 以原 parent/hash 和完整提议恢复；禁止半候选成为正式状态 |
| 新 candidate 已 commit、summary 未写 | 由事件重建，不重复生成或免费工具检查 |
| PC 修改未产生新 FPP | 保留原完整候选及其旧 PC，不混用新旧配套 |
| 共享节点完成、某消费者未执行 | 只读复用已提交共享结果，不再计一次生成 |
| hidden 已提交、回执丢失 | 返回原结果，不重新执行 suite |

本地 action 幂等不证明远端 API exactly-once。原始状态不可核验时，不用手工 success 标记跳过问题。恢复不能重新发预算或改变模型配置。

---

<a id="diagnostics"></a>
## 14. 公共诊断、行为错误与机制观察

### 14.1 诊断对象

每条诊断包含 stage、reason_code、候选/PC hash、公开 evidence refs、源位置／JSON Pointer、相关 fact 与设计元素、允许编辑目标和重检依赖。来源为 `rule | tool | model_hypothesis`；模型推断不写成已被工具证明。

张量诊断可报告同位宽不同 order、编码不匹配、per-axis 索引／表问题、mask、group 顺序和违反的有限关系。规则代码与源位置应来自实际 checker，不凭文档手造原型并未产生的码。

公共投影采用 allowlist；不先把私有完整结果序列化后再删除若干关键词。候选代码和日志文本是数据，不可修改 Agent 指令、工具权限、budget 或 oracle。裁剪规则与长度预先冻结，避免给某方法额外关键信息。

### 14.2 三层一致性与局部算法分开

| 分类轴 | 说明 |
|---|---|
| 结构／工程 | 模块、接口、参数、驱动、层次和文件依赖 |
| 张量声明 | shape、轴序、lane/mask、sequence 的不匹配 |
| 数值声明或实现 | scale、zero-point、per-axis、舍入、溢出和 Bias 边界 |
| 实际事务对应 | 丢失／重复、同调用／同坐标错配、复位污染 |
| 部分和／状态 | K组、清零、归并、提交和适用存储生命周期 |
| 有界完成 | 规定环境下未完成；没有额外证据时不宣称死锁 |
| 局部算法 | 乘加、核索引或激活等内部行为错误 |
| 非模型原因 | 工具、oracle、runner、受信实现或完整性事件 |

根因记录 `confirmed / suspected / unclassified`、依据与观察范围。一个事件可有多个标签，但不能多次计为独立缺陷；无法运行后续阶段标 not_observed，不能记零缺陷。

### 14.3 不让诊断可见性变成不公平分数

M4 提供更多结构和关系信息可能更易定位错误；不能直接比较“命名错误数量”就推断某方法真实错误更多／更少。主要终点仍是共同外部行为和完整工程结果；同时报告可观察性与未分类比例。[R, §11.3]

单一 root behavioral 或粗 compute 合法时照常接受，不强迫参考拓扑；相应静态机制覆盖有限，单独记录。不能以强制更多 PC 关系条数制造方法信用。

### 14.4 Probe 与后验定位

自然失败 probe 只从 M4 的公共失败中按预定规则选取，每设计簇至多一个 checkpoint；具体上限与双分支预算见 §19。人工变异属于 conformance／oracle 资格，不进入自然缺陷率。

需要内部探针时按预声明方法中立的观测策略处理，或在生成全部封存后的只读调试副本中进行后验根因分析。新探针、副本和结果保留独立身份，不改变原 candidate hash、正式分数或给生成器新的机会。

---

<a id="evaluation"></a>
## 15. 独立 oracle、public／hidden 与物理确认

### 15.1 三条独立验证线

| 验证线 | 权威输入 | 最低观察 |
|---|---|---|
| 数学／位精确 | 冻结任务算法、量化步骤、合法权重／输入 | 完整输入到输出值、范围、舍入和顺序 |
| 协议／事务 | 公共 ABI、valid/ready、mask、调用、reset 与完成规则 | 接受／提供／提交、有效元素、丢失／重复／错配 |
| 时间／资源 | 公共环境与周期要求、指定工具和目标配置 | 完成时间、II、超时、映射与物理范围 |

可共享公开规格的事实，不共享候选计算实现来生成期望值。PC compute/numeric_rules/timing 只帮助定位，不改写判题；浮点参考不替代冻结的整数算法。

### 15.2 Oracle 实现边界与资格

评测方独立实现 DW/PW、残差和分块矩阵的位精确参考；固定输入打包器、输出解包器、协议 monitor 和 scoreboard 都需黄金数据／独立交叉核对。PC包的 tensor_reference 可用于开发对照，不能成为双方共同且唯一答案库。

正确参考工程须在所有计划配置和相应 suite 中通过。变异至少区分格式／声明／真实 RTL 三层，覆盖布局、lane、scale、per-axis、padding/mask、配对、部分和、reset 和提前结束。等价、不可执行、未检出变异分开，不用大量拼写错抬高语义覆盖。

当前静态示例不自动获得 oracle-ready。全部阶段资格记录真实代码、工具、范围和已知盲区；不宣称有限测试完备。

### 15.3 Public worker

只消费不可变候选与固定公开 policy，重建工作区后执行 L0、指定 lint/compile L1、trusted public L2 和规定 L3。记录实际命令、语言、top、源码、资产、超时、结束条件和原始产物。

候选 TB、stdout 的 TEST_PASS、exit=0 或提前 `$finish` 不是语义通过。harness 必须验证应有事务及完整结束。Direct 不因没有 PC 而失败，M3 不通过调用 M4 emitter 才获得评分资格。

公共诊断返回 §14 的受控投影，不修改候选。工具重跑依预算，最终验证不会变成免费修复期。

### 15.4 事务与 tensor scoreboard 的实施要求

下列是从 [R]/[P] 落实的评测职责，不要求 DUT 暴露这些内部 ID：

| 场景 | 评测器应核对 |
|---|---|
| dense 流 | 每调用期望拍数、有效 lane 和坐标枚举，停顿时 payload/valid 保持 |
| DW→PW | 输出坐标／通道、权重和 per-axis 对应、padding 与无效 lane 区别 |
| 残差 | 同调用／同坐标配对、不同进度／恢复、数值模式、旧帧不可混入 |
| GEMM | 多K组的最终数学、Bias一次、初始累加和完成后提交、连续矩阵状态 |
| reset | 在公开规定的中止／恢复规则下取消旧事务，重新开始不串用状态 |
| 有界完成 | 在固定源／下游模式及周期上限下完成，超时保留实际观察 |

期望行为从 task 和独立 oracle 定义，不要求生成模块与参考内部命名一致。对于融合实现，不强求内部 partial_sum 总线；最终数值与公开完成义务照常验证。判断内部死锁需要另有等待链或形式证据，超时本身只能支持有界完成失败。

### 15.5 批次屏障

正式默认先完成核心和已纳入第二模型、Agent、消融、probe 的相应生成分组，所有计划槽都有候选或有原因的无候选结局，再执行并披露相关 hidden 结果。[R, §8.3]

屏障等待位置闭合而非全部成功。需要分组屏障时，分组及无跨组反馈条件必须在结果前冻结；不能看过某组 hidden 后继续调整其他组。生成控制域仅获得 opaque job refs，后处理读取结果的协调器没有模型权限。

### 15.6 评分槽与幂等请求分开

```text
HiddenSlotKey = (
  campaign_id, population_id, semantic_instance_id,
  replicate_id, condition_id
)
```

design_cluster 与 dependency_group 通过冻结 sample mapping 绑定，不用更换簇标签创建第二个同任务分数。槽在评测前固定 candidate、task、suite 和工具上下文。candidate_hash 可以进入请求幂等键，但不能成为可换候选新增槽的主键。

同槽更换候选、suite 或工具配置拒绝；不同模型、probe、C0/C1 或消融只使用事前注册的独立身份。相同候选被多张表引用复用原结果，不重评扩大样本。

### 15.7 双轴状态与一次语义提交

```text
hidden_execution_status = completed | not_run | infrastructure_error | integrity_error
hidden_semantic_status  = pass | fail | null
```

completed 恰有一次语义 pass/fail 提交；无候选或固定前提不满足以 not_run/null 和原因闭合，提交数为0。上游已有设计失败仍为结果0，不因 hidden没跑而删除。

提交前固定基础设施重试只重放相同候选和配置；耗尽后仍不可评分则保留NA。提交后只能读取旧回执，禁止重跑 suite。并发 worker、崩溃与回执丢失必须由原子槽索引和恢复测试覆盖，不能仅靠进程内布尔值。

### 15.8 私有结果与实际完整性

原始 hidden 输入、case ID、seed、期望、路径、日志与分数保留评测私有域。分析投影含状态、范围、原因、绑定和计量，不进入任何模型上下文、候选附件、修复日志或人工调参渠道。

固定 suite 可包含多个定向、随机、压力或真实负载组；未执行组保持未观察。事后新增负载只能另列后验研究，不改原评分，不能给原方法恢复成功机会。

### 15.9 三家族物理位置

按 [R, §14.2] 的规划，三家族各预选3个正式设计簇，每簇1配置，固定replicate 1，覆盖M0–M5，共54个位置。数量是待冻结描述性配置，不能写死为始终54条 route。

选择先于模型结果，参考路径须事前可测；同一封存候选完整VPP-L3通过后才进入L4。上游失败和缺失留在预选分母，不拿其他成功候选补位。旧FIR／Sobel报告只能保持历史身份。

固定器件、封装、速度等级、时钟、I/O、资源、源码、权重与工具；禁止候选修改约束。记录实际资源／时序范围、slack、工具支持的原生频率、网表和约束hash、费用及失败。未分析hold或I/O不能标已通过，OOC不叫板级闭合。

报告预选全分母VPP-L4及L3存活者条件结果。L4失败不改写已验证L3，也不回到核心修复；无证据不报告bitstream、上板、功耗或普适PPA。开放工具与可选Vivado各自明确证据，任何厂商工具不由本规范变成期刊强制门槛。

---

<a id="analysis"></a>
## 16. 结果归约、设计簇统计与声明资格

### 16.1 状态和分母

OutcomeReducer 从完整 PopulationPlan 左连接实际结果，而不是从成功artifact遍历产生分母。重复ID、缺少槽闭合、交叉任务hash、共享关系矛盾或篡改事件都需显式报错。

| 情形 | 保存事实 | 研究处理 |
|---|---|---|
| 输出不全、非法候选、已观测功能错、不可综合、预算内候选超时 | 设计失败及阶段证据 | 0，保留全分母 |
| 已有必需阶段明确失败，后续未运行 | fail＋not_run | 失败已成立，不将整行改NA |
| 无充分失败证据但必要阶段因基础设施不可判 | infrastructure missingness | NA和上下界，不删行 |
| 受信对象实际破坏、hidden泄漏或槽／谱系损坏 | integrity_error | 按冻结规则停止受影响范围／声明，不能普通NA化 |
| 功能可判但计费缺失 | 语义结果＋cost unavailable | 不因token缺失改0；预算可核验性单列 |
| 方法不适用某检查 | not_applicable | 不按失败 |

VPP-L3按[R]的共同FPP/L0、L1、publicL2、hiddenL2、指定L3和实际边界／来源／预算规则建立。完整分阶段事实与budget_status同时保存，计量未知不是违规证明也不是合规证明，等预算确认性资格不得默认放行。

### 16.2 配对与设计簇估计

对同一f（家族）、i（设计簇）、j（具体配置）、r（重复）的X/Y保留配对：

```text
D_fi(X,Y) = sum_j w_fij × mean_r(Y_fijrX - Y_fijrY)
Delta_f   = mean_i D_fi
Delta     = (Delta_DW_PW + Delta_Residual + Delta_GEMM) / 3
```

默认簇内配置等权、家族内设计簇等权、三家族等权。配置权重先于结果冻结；簇中配置多不意味着更大总体权重。family、cluster、dependency和任务映射由manifest验证，不接受结果方重新分簇。

主要比较只有M5−M1总预算终点与M4−M3初态。给旧四家族均值除数改3不足以对齐新分析；必须改变独立单元和保留全部配置／重复。

### 16.3 统计policy由研究决定

[R, §12] 候选值如下，须在新pilot前明确采纳；本SPEC不赋予它们已冻结身份：

| 比较 | δ | Δ* |
|---|---:|---:|
| M5−M1 | 0.05 | 0.15 |
| M4−M3 | 0.03 | 0.10 |

检验Delta≤δ，两项共用单侧familywise α=0.05的Holm族；同时报告两侧95%区间和负方向结果。默认两侧区间不是多重比较同时区间，不增加旧版本的重复阈值门槛。

按完整设计簇在家族内重采样，保留配置、方法、重复及两个对比协方差；建议studentized cluster bootstrap、边界零假设居中、固定seed和19,999次重采样，具体实现须先经模拟核验。跨家族dependency_group要求整体协调重采样并保持目标权重；未支持该依赖方案时必须拒绝确认性分析，不静默退回独立抽样。

簇过少、零方差、稀疏分歧和不可辨识来源时只报告可支持的描述，不伪造p值。只有三个固定工程重复很多次，仍然是案例研究。

### 16.4 缺失与功效

完整分母上下界始终报告。确认性默认未知X取0、未知Y取1的比较方向下界仅作用于分析副本，不改底层NA；另报相反界限和完整配对敏感性。该推断在预声明场景下模拟验证，不能只因名为bootstrap就认定有效。

[R] 候选缺失上限为单方法5%、主要对比差异3个百分点，联合统计功效目标至少0.80；均在新pilot前确认。预算关键轴不可核验时，停止等预算优势声明，即使可观察成功率继续报告。

n/c/r来自新AI独立设计簇的功效／精度和成本规划；pilot仅提供干扰参数，不用观测处理效应重定δ或Δ*。实际完整性故障不是可任意假设概率的普通设计失败。

### 16.5 次级与机制结果

报告阶段转移、结构／声明／实际行为错误、修复、三成本、HFPA及其隐藏完成率、三家族L4、启用的第二模型／native／probe／消融。

```text
HFPA = public_accepted且hidden_completed且hidden_failed的数量
       / public_accepted且hidden_completed的数量
```

分母0记未定义；不同选择人群的HFPA不能直接相减当因果效应。只画公开检查进展与首次公开接受成本，不补画未评中间候选的hidden曲线。

义务状态由Evidence填写，候选关联和static pass不能关闭实际布局、配对、算法、活性或L4要求。新的低成本若来自更多提前失败不自动成为效率优势。所有正向声明遵循[R, §19]，未跑native对照不能说胜过Codex。

---

<a id="tasks"></a>
## 17. 三个AI家族、任务资格与负载

### 17.1 主总体与旧资产

| 角色 | 活动任务 |
|---|---|
| 主家族A | ai_dw_pw_block |
| 主家族B | ai_quantized_residual_block |
| 主家族C | ai_tiled_gemm_pipeline |
| 开发／回归 | 旧基础模块和UART／stream_fork_join等组合／matched-filter／Sobel；实际ID以旧catalog为准 |
| 非近期主线 | Q-table、完整SoC／DMA、训练与EA |

三个主标识为[R]拟注册身份，不宣称当前catalog已具备。任务角色调整不删除历史代码、记录或旧分数，也不为其授予新主统计权重。

### 17.2 每张任务卡的两面

公开面给精确计算、tensor／ABI、量化和所有关键中间步骤、边界与尾部、状态和调用、环境、目标、合法资产及实现自由度。私有面保存独立参考、具体suite、资格、来源依赖、开发暴露、抽样和分析身份。

参考内部文件名和拓扑不成为秘密判题标准。权重和Bias是公开设计输入，隐藏的图像／激活／矩阵是测试输入，两类资产不要混为同一权限。

### 17.3 家族A：DW→PW

真实计算包含Depthwise、明确中间量化／激活、Pointwise和最终输出处理。任务需裁定kernel索引、padding、stride、depth multiplier、Cin/Cout、Bias、各阶段累加范围、per-axis索引、外部遍历和完成规则。

内部统一布局合法，不为了触发repack检查强制错配。验证非对称坐标／通道、不同权重／尺度、非零zero-point、边界和掩码、停顿、连续调用及reset。不能用完全相同权重和零输入遮蔽通道交换。

[R] 的N=1、8×8、Cin=4、Cout=8和3×3DW＋1×1PW仅是首个开发配置建议，不写入schema默认，也不据此宣布工具可行。

### 17.4 家族B：量化残差

任务明确F(X)、S(X)、量化／激活位置及对应相加。初始可采用identity skip和相同形状，不以“标准ResNet”省略运算定义。

同编码加法处理零点，异尺度按指定数学；数据按同调用同坐标配对。硬件可用顺序计数和缓冲，不强迫每拍携带标签。容量由合法实现选择，完成责任在固定环境下验证，不指定参考FIFO深度。

压力覆盖独立分支推进、长停顿后恢复、启动等待、连续调用、正负与饱和边界和旧状态清理。超时只标bounded-completion failure，没有额外证据不写成死锁证明。

### 17.5 家族C：分块GEMM

任务含A/B接收与片上存储、完整矩阵运算、适用分块执行、归并、Bias／重量化及结果提交。公开矩阵维度、转置／遍历、装载方式、存储限额、数值和时间顺序。

显式partial_sum接口按PC序列核对K组、输出坐标和提交；融合累加实现只要符合公开任务同样接受，不强制额外reduce_sum模块。Bias一次，全部归并后在规定边界量化。

第一版不强制双缓冲／DMA／乱序。整齐K组可列能力域；非整除K尾块需独立冻结语义，不能把普通lane mask误当ragged K已支持。N维／K维规模、权重固定或运行时可变由任务决定，不能由候选偷偷简化。

### 17.6 资格、来源和留出

设计簇整组进入开发／pilot／正式分区。已有三个PC示例已参与方法开发，不叫unseen-family；默认声明已知AI机制上的设计簇、组合和配置留出。

资格包括完整公开任务、所有计划配置的独立参考与正确参考工程、协议／时间监测、分层变异、工具可执行性和盲区。正式前不足则按[R]修订任务或范围；正式后模型选不支持结构仍是该方法失败，不能重路由或删实例。

### 17.7 真实负载与工具边界

区分研究配置、公开模型子图、真实采集／派生激活。来源、选择、转换、量化、打包、字节和许可均固定。真实输入可用于RTL回放，不要求先接相机，但不因此宣称端到端精度或现场效果。

不把MVTec/Sobel旧案例继续当新核心前提；权重子图导入不是本版通用ONNX importer。任务卡和资产reader只支持已冻结格式，缺关键值先裁定，不交给模型猜测。

---

<a id="contracts"></a>
## 18. Machine contracts与运行一致性

### 18.1 仅注册实际边界

| 类别 | 内容 | 核验职责 |
|---|---|---|
| 公共任务与profiles | facts、tensor边界、数值profile、资产与适用域 | 来源、完整语义、版本和能力 |
| PC2.1 | 完整PC与模型design投影 | 同源schema、绑定和H检查 |
| 生成／修复提议 | ProjectProposal、BehaviorBundle、ProjectFilePatch、design更新 | 权限、父对象、内容和预算 |
| 派生构建与候选 | BuildPlan、AbiMap、FPP、envelope、TerminalRecord | 单一源、语义依赖、实际字节和保护 |
| 人口与方法 | family/cluster/config/replicate/dependency、DAG、policy、扩展 | 唯一映射、全分母、信息和预算 |
| 事件与成本 | action、原始usage、预留和三视图 | 追加事实、unknown与恢复 |
| 结果 | stage、双轴hidden、义务范围、物理与错误诊断 | 独立权威、slot与证据 |

类别可在一个schema文件中用有限判别分支表达；内部纯类型不要求独立注册。不要新增几十个只差authorized布尔值的回执来构成新gate链。

### 18.2 读写与版本

writer在原子发布前校验，reader在使用前核验格式、hash和跨对象关系。旧版本、未知字段、非法可见性、父候选不匹配或计量关系矛盾不能静默归一化。

注册schema不证明生产checker已调用它；测试必须走真实writer/reader路径。`conformance.json`是测试报告，不是PC、正式实验准入或当前完整性认证。

### 18.3 来源与派生视图

所有视图可从固定对象和事件重建。改summary不影响事实；修订分析实现时保留版本、影响和原结果。跨规范更名不全局替换历史hash或已执行样本身份。

---

<a id="modes"></a>
## 19. 运行模式、原生Agent与可选实验

### 19.1 三种模式

| 模式 | 允许 | 前提／禁止 |
|---|---|---|
| development | 开发实例、fake或明确限额真实模型、公共工具与故障测试 | 不读正式hidden，不晋升模型结果；保留暴露 |
| excluded_pilot | 冻结的新设计簇、配对方法和干扰参数测量 | WP3就绪；不据处理效果改δ／Δ*，不补容易样本 |
| official | 最终manifest的固定核心和已纳入人口 | 批准与独立核验，任务/模型/预算/分析不临时变化 |

正式前核验可在审计区写无研究结果的失败报告；核验未过不调用正式模型／工具或创建正式候选。开发无需完成所有扩展或官方授权链才做有限真实闭环，但仍须明确资源许可和最低隔离。

### 19.2 CampaignPreflight

核验[R]身份、PC2.1、方法、三AI家族与设计簇／依赖、实例映射、模型／工具、预算、suite、终止、物理子集、分析与扩展启用状态。最终配置不能含影响执行的待定值。

批准来自受控负责人渠道，程序重算同一内容和前提。普通hash不是签名；部署采用签名时明示信任根与范围。不接受manifest或模型自填authorized作为授权，不提供绕过正式核验的force入口。

### 19.3 Native C0/C1是独立系统实验

只有在WP3/WP4结果前纳入时装配NativeAgentAdapter。C0获得完整公共任务、合理FPGA指导、公共工具与受保护评测配置，自主组织工程；C1使用同一基础引擎／模型和事实，额外通过PC2.1、受信构建与行为装配执行。

以下为接口责任，不承诺某个实际Agent当前已暴露对应API：

```text
NativeRunRequest:
  sealed_public_context, engine/config refs, condition,
  workspace/tool permissions, measurable_budget, terminal_policy
NativeRunResult:
  terminal proposal or null, raw event/usage refs,
  tool activity, visibility/measurement limitations, termination reason
```

适配器不能把整次native run当作一个核心逻辑模型调用。记录可观察的token、工具、活动时间和内部turn范围；未暴露的内部计算保持unknown，不以外层运行四次匹配B4。

C1的强制结构边界由外部服务和访问控制落实，不只在提示中写“遵守PC”。C0同样有公共测试与需求保护，但不被迫模仿C1内部拓扑。实际引擎权限、接口和计量能力在纳入前验证；不能满足的范围明确缩小或省略，不在本稿假装已接入Codex。

C0/C1有独立population/condition、终止槽与同一外部oracle，分开报告，不进入主要Holm平均。引擎／模型无法完全匹配时只做明确限制的系统比较。核心只用M1时不得宣传优于Codex产品。

### 19.4 张量消融与修复probe

可选A_tensor_on/off共享未经该因素筛选的初始proposal，其余公共事实、基础安全／构建类型规则、模型、工具与预算相同。禁用规则若又承担必要ABI解释，就不是纯语义诊断消融；应改为仅控制诊断暴露并明确估计对象。具体开关、初态和方法范围须由独立协议冻结，不在主checker留任意生产bypass。

自然失败R_generic/R_PC建议每家族最多3个独立设计簇、每簇一个公共失败checkpoint；两侧同PC/FPP/事实/日志/模型/编辑范围，只改变允许的义务关联／重检诊断。每分支建议最多2次纠正和2个public cycle，其他轴等价。缺样如实报告，不用人工变异或hidden失败补足。

第二模型、native、消融、probe各有独立预算和结果身份；未纳入不创建空路径，纳入后不因结果差删除。它们不要求全部同时启动。

### 19.5 目标CLI用例

以下仅为待实现操作面，不代表当前命令存在，也不是本次执行记录：

```text
sr2fpga inspect-task <public-task>
sr2fpga validate-pc <pc> --context <public-task>
sr2fpga plan-build <pc> --context <public-task>
sr2fpga run-development --config <bounded-dev-config>
sr2fpga prepare-pilot --manifest <candidate-protocol>
sr2fpga verify-campaign --manifest <frozen-manifest>
sr2fpga run-campaign --manifest <verified-manifest>
sr2fpga resume --run <run-id>
sr2fpga analyze --manifest <manifest> --events <verified-store>
```

hidden／physical worker和oracle资格工具仅在相应评测域运行，不暴露给模型通用shell。原生Agent若纳入也走同一个权限、预算和终止边界，不产生第二条可绕过控制的便捷路径。

---

<a id="workpackages"></a>
## 20. WP0–WP6与实施顺序

### 20.1 工作包映射

| 工作包 | 要完成的实现 | 验收对象 |
|---|---|---|
| WP0 范围与资产审计 | 活动研究／PC／架构、三家族与旧任务角色、真实代码与registry、依赖和暴露 | 版本差异与复用清单、单一活动入口；不复制历史通过状态 |
| WP1 PC2.1与真实构建 | 公共输入适配、descriptor／关系、tensor ABI／mask、emitter、body装配和来源 | 纯结构、类型黄金例、保护边界与语义依赖测试 |
| WP2 完整任务与开发闭环 | 先DW→PW任务／独立参考／真实模型与工具，再残差与GEMM | 可评分任务、完整候选、自然失败或实际未出现失败的记录、真实修复与费用 |
| WP3 基准和候选协议 | 设计簇／依赖／配置、整簇留出、全部oracle资格、模型／方法／预算与统计、扩展决策 | 无正式结果的完整人口和配置；确认所有对照信息与资源机会 |
| WP4 排除式pilot和正式冻结 | 完整paired pilot、干扰参数／成本／精度、最终n/c/r、物理子集与核验 | 不删失败的结果、分析模拟和正式无结果manifest |
| WP5 正式执行与L4 | 计划位置全部闭合、批次屏障、唯一hidden提交、指定L3、预选物理及启用扩展 | 可重建完整结果、失败／未知、证据范围与成本 |
| WP6 分析和发布 | 两个主比较、错误／修复、三家族物理、已纳入native等、来源和限制 | 图表重建、允许声明、可复现产物与明确未验证项 |

这些工作包来自[R, §16]，不是新增G0–G9/CD1–CD10链。实现验收不要求PC赢过Direct，关闭扩展没有阻塞权。

### 20.2 最短可用开发路径

**切片1：可信输入到CheckedPC。** 适配真实公共任务，绑定PC2.1与profile，核验tensor和引用规则；产出位置明确的错误和真实deferred范围。

**切片2：CheckedPC到真实结构。** 先以标为人工参考的简单body验证tensor beat、record、ready反向、参数复用、纯组合／时钟模块和源码装配。不得把参考body进入模型成功统计。

**切片3：一个完整DW→PW开发任务。** 先冻结该开发任务的权重、kernel、量化、padding、ABI、停顿、reset和完成规则，建立独立整数参考及完整工具参考路径；再运行一次规划和一次批量行为。

**切片4：公共失败到预算化修复。** 先实现M1全工程／文件替换，再实现M5行为／design修正；保留parent、旧候选、合法改动与实际重检。没有自然失败就说明实际观察，不人为破坏任务伪造自然transition。

**切片5：完整共享六方法块。** 核验S_D/S_C/S_B、M2、6/10初始和11/15 B4上限、失败共享、顺序及恢复；M3的emitter/filler调用为0。

**切片6：独立终止验证与三家族扩展。** 验证hidden槽、基础设施恢复和无回流；然后把同一系统用于残差和GEMM的完整任务，不复制三个独立runner。

最低真实开发前提是公开域、明确预算、受信文件保护和基本事件，不要求先完成全量正式oracle发布、native、EA或训练。

### 20.3 规模由PopulationPlan计算

以下严格继承[R, §12.5]的规划，均非已运行数量或充分样本结论：

| 用途 | 规划身份与数量 | 运行解释 |
|---|---|---|
| 开发诊断 | 3家族×2开发配置×3重复＝18次Direct-Repair过程 | 非正式观察，不是18个独立设计 |
| paired pilot | 3家族×4新设计簇×1配置×2重复×6方法＝144方法结果 | 12簇、24块；不能按效果负而补样 |
| 正式核心 | 3家族×n簇×c配置×r重复×6方法 | n/c/r由新AI功效／精度与成本冻结 |
| 第二模型候选 | 每家族6簇×1配置×2重复×4关键方法＝144结果 | 18簇，独立人口，不扩大主要检验族 |
| Native C0/C1候选 | 每家族3簇×1配置×2重复×2条件＝36Agent episode | 9簇，不计为36个独立任务；预算不用B4外层调用替代 |
| 主物理子集候选 | 每家族3簇×1配置×1重复×6方法＝54位置 | 进入取决于同候选VPP-L3，失败不补位 |

仅作容量核对：n=20、c=2、r=3给出60簇、120配置、360块、2160方法结果；B4核心调用上限为3960实际去重／5400独立归因。相同总结果数不继承旧四家族功效。代码对任意冻结矩阵从节点／消费者自动求和，不硬编码这些算例。

### 20.4 完整三家族就绪

三家族均需真实可执行参考、独立suite、自然模型数据闭环与可辨识错误原因，才能进入宣称三家族基准的正式流程。有限配置／来源不足时在正式前按[R]降低为案例或估计性研究，不在结果后移除失败家族。

模型质量差、PC前置失败多或效果负是可报告结果，不是删除数据或让构建器代写算法的理由。工具或资格错误应按真实原因修复并版本化。

---

<a id="tests"></a>
## 21. 测试与验收矩阵

### 21.1 测试层次和范围

按纯函数／contract、PC语义、真实结构与装配、方法配对、工具、隔离、恢复、完整开发闭环逐层测试。fake provider是编排测试；真实模型和重型EDA采用明确限额的opt-in，不混入默认单元测试。

工具缺失应skip/not_run并报告，不能算passed。人工PC/RTL故障用于资格和边界测试，不进入自然模型缺陷率。原[T]的149项局部测试属于其原代码版本，本次没有重新运行；生产集成必须在新入口核验，不能继承数字代替验收。

下列V编号是本SPEC的验收定位，不是已经运行的测试或新增研究gate。一个测试可覆盖多项；每项对应实际风险，不强制一个编号一个新contract。

### 21.2 核心验收场景

| ID | 面 | 必须观察的行为 |
|---|---|---|
| V01 | 严格解析／schema | 重复key、旧版本、未知字段、非法PC浮点／截断拒绝；合法输入通过正确入口 |
| V02 | 设计投影 | 根为design；模型不能写bindings／评分；两份schema同源一致 |
| V03 | 需求绑定 | 替换需求／target/capability被发现；投影视图可追溯原字节；不接受候选自定expected hash |
| V04 | 参数和层次 | 未绑定、除零、零宽、越界、递归、悬空引用和不可达定义拒绝；合法复用可展开 |
| V05 | 类型与域 | 符号、record顺序和域冲突拒绝；组合模块无虚假时钟；state域正确 |
| V06 | Tensor形状／布局 | 同位宽HWC/CHW、缺轴／重轴、lane-axis错误可检出；合法局部契约改名不改语义 |
| V07 | 量化声明 | 错scale/zero-point、非最简尺度、per-axis长度／轴错误和范围越界可检出 |
| V08 | 尾部与三种零 | exact不整除拒绝；zero_pad_mask宽度/位序正确；padding、无效lane和有效raw0按独立黄金例区分 |
| V09 | 接线方向 | self/child的data/valid和反向ready正确；value合法扇出、stream隐式广播拒绝 |
| V10 | Tensor直接边界 | shape/element/quantization/layout/sequence均比较；raw擦除不冒充tensor兼容 |
| V11 | 有限关系 | 合法fork/repack/requantize/zip_add/reduce_sum通过相应声明检查；矛盾关系被拒绝 |
| V12 | 部分和顺序 | outermost/innermost和拍数黄金例正确；提前量化／缩窄／组声明冲突可检出 |
| V13 | FIFO范围 | 条目为完整beat、单位和域一致；低容量可静态合法但活性保持not_evaluated |
| V14 | 关联非证明 | 粗compute／全部fact指向顶层不得生成自动功能通过；deferred义务完整保留 |
| V15 | 构建确定性 | 同输入/配置的结构字节和ABI相同，不依赖随机hash或临时路径 |
| V16 | 无行为模板 | 构建器不导入example／family generator，不自动生成Conv/FIFO/重排/量化算法 |
| V17 | 批量行为 | 多unit仍一次声明调用，缺失／重复／未知unit不能免费补齐；无unit合法跳过 |
| V18 | 真实语法保护 | endmodule逃逸、额外模块、越界宏/include/实例、签名修改和私有路径访问被阻止 |
| V19 | FPP中立 | Direct无PC/TB/QoR、非固定top源路径可满足共同FPP；合法融合实现不因拓扑不同失败 |
| V20 | 资产核验 | 实际权重字节、布局和元素数核验；隐藏输入不挂入public assets；未提供文件不算完整 |
| V21 | 语义缓存失效 | 同位宽但scale、layout、lane/group/资产变化使旧body不可自动复用；跨任务答案缓存禁止 |
| V22 | M2/M3因素隔离 | M2不运行PC语义；M3 emitter/filler/参考模板调用为0，不看M4成功构建 |
| V23 | 共享成功 | M0/M1初态相同，M3/M4初始PC相同，M4/M5完整行为后工程相同；槽独立 |
| V24 | 共享失败 | 非法PC／不完整工程及原始费用共享，依赖阻塞不生成假工程或假调用 |
| V25 | M1文件修复 | 父hash、原子多文件替换、新删源和manifest一致；失败不半提交，不自动接线／补算法 |
| V26 | M1权限公平 | 可局部重构模型RTL；不得改需求／资产／target／harness；不强制全工程重传 |
| V27 | M5双层修复 | design修改和新行为各计费，重新检查；保留旧候选时连同其旧PC/build，不混版本 |
| V28 | B4全路径 | 正常1+3与2+2、前置失败余量和额外router均不超总额；不为每阶段重新发预算 |
| V29 | 终止与修复事实 | 最早公共接受／最后完整；空或重复修改计费但非transition；无hidden选择 |
| V30 | 成本三视图 | 6/10初始、11/15上限及失败路径可重建；共享不摊薄、不漏费；unknown不是0 |
| V31 | 调度／恢复 | DAG因果顺序、本地seed独立、已完成共享节点不重生成；并发预留无超售 |
| V32 | Public判题权威 | 伪TEST_PASS、候选TB和提前退出不能通过；完整事务／结束条件由harness检查 |
| V33 | Oracle独立性 | 冻结任务产生期望，不从候选PC/RTL生成答案；checker与oracle不是同一唯一算法实现 |
| V34 | 声明与行为反例 | 双方声明正确但RTL错layout/scale/配对时静态可通过，真实独立测试检出 |
| V35 | 三家族数值/事务 | DW/PW通道与padding；残差异尺度／错配；GEMM多K组／Bias／提交；局部算法错单独分类 |
| V36 | Hidden不可回流 | 私有case/seed/path/status/summary不进入任一模型／候选／公共日志或其他任务 |
| V37 | 批次屏障 | 核心及纳入分组的全部位置闭合；失败也可闭合；无越屏障反馈 |
| V38 | 唯一评分槽 | 同槽换candidate/suite/tool拒绝；并发与回执丢失不产生第二次语义提交 |
| V39 | 失败／未知 | hidden fail不修复；无候选not_run按上游计分；infra NA、integrity和cost unknown区分 |
| V40 | L4范围 | 只运行预选同候选L3存活者，54为配置非硬编码；未进入保留原分母，无L4→核心修复 |
| V41 | 设计簇身份 | 配置/重复/图像不增n；重复映射、跨簇版本或非法population混合被发现 |
| V42 | 统计与依赖 | 完整簇保留配对；跨家族依赖协调；零方差/NA/稀疏结果不伪造p；权重冻结 |
| V43 | 原始事件恢复 | reserve、响应已落盘、patch未提交、candidate已提交、未知远端等路径可正确闭合 |
| V44 | 权限与模式 | 未核验正式配置无正式副作用；disabled扩展不装配；新核心不读旧PC或训练路径 |

### 21.3 条件性扩展测试

只有相应扩展启用时才形成义务：

| ID | 面 | 要求 |
|---|---|---|
| X01 | Native C0/C1 | 公共事实／工具一致、C1结构权限有效、外层run不折算B4、事件与计量限制如实记录 |
| X02 | 张量消融 | 初始proposal未被被消融规则筛选；必要安全／ABI规则仍相同；估计对象与开关一致 |
| X03 | 自然失败probe | 整簇selector只读公共失败，不能用hidden补选；两分支上下文/预算一致 |
| X04 | 第二模型 | 子集先选、与核心结果分组、不同tokenizer不混为同等计算量 |

### 21.4 验收记录和测试顺序

每项记录输入、预期、真实结果、代码／schema／profile hash、artifact引用和未覆盖范围。通过数量不是论文结果，静态报告也不是emitter、OS隔离或RTL通过。

先最窄测试，再受影响的PC/build/method/worker范围，再新核心端到端回归；共享组件变更应运行相关旧回归以避免破坏非核心资产，但不以整套旧training/compatibility系统作为新研究必须通过的前提。

---

<a id="replacement"></a>
## 22. 旧架构退出与仓库同步

### 22.1 从架构v2.0到v2.1的实质变更

| 旧条款／资产 | 本版处理 | 不允许的捷径 |
|---|---|---|
| 研究v2.1＋PC2.0 | 研究v2.2＋PC2.1 | 只更改标题但仍读旧schema |
| 四主家族＋视觉/Q-table案例 | 三AI主家族；旧任务回归、Q-table移出近期主线 | 三份示例直接标ready或旧L4转新信用 |
| semantic_instance默认独立 | design_cluster为重采样单位，配置/重复嵌套，依赖组可跨家族 | 通过换权重/尺寸/ID制造独立n |
| 只维护位宽与record结构 | 解析tensor含义、量化、layout、lane/mask、sequence和关系 | 同位宽即接线/缓存安全 |
| BuildPlan/AbiMap只含基础类型 | 加入完整语义身份与tensor物理展开 | 改order文本就宣称完成重排 |
| M1强制replace_project | 增加通用原子文件级替换 | 给M1更少实际修复机会或自动补算法 |
| M5只按代码路径失效缓存 | 参数/编码/布局/组/关系/资产均进入依赖 | 新PC配旧body且不重验 |
| 旧物理子集 | 三AI预选位置，规划54 | 成功后挑样、失败换位 |
| 四家族均值与旧独立n | 三家族/整设计簇/配置权重/跨家族依赖 | 只把除数4换3 |
| M1被当作通用Agent表现 | C0/C1独立次级系统对照 | 外层run次数等同B4或混入主均值 |
| 日志错误皆称一致性 | 结构、声明、真实行为、局部算法与未知根因分开 | 所有hidden错都归因跨模块 |
| A_tensor仅口头说明 | 启用时独立初态/开关/预算/结果身份 | 与必要ABI解释一起关闭却叫纯诊断消融 |
| 旧规模2160 | 由3ncr与完整人口计划计算 | 因结果数相同继承旧功效 |

### 22.2 最早旧规范的历史边界

最早v1.12规范已记载其方法、G0–G9与预算尚未对齐后续研究，属于历史实现线索，不重新恢复其兼容reader、训练授权链和旧H2 dry-lower。[H, §0]

历史G关闭、测试数和当前实际代码是否存在，都不由本稿更新。无兼容仅约束新运行入口；旧源码、数据和报告保留原版本身份。

### 22.3 实施时的同步对象

根AGENTS、项目README、docs/specs索引链接活动研究与本架构；agent/README只列真实可用命令和最短开发路径，current-status从实际证据写能力，不复制另一套研究规则。

contracts注册PC2.1和真实runtime对象；task-catalog登记三家族、设计簇、具体配置、资格与旧任务角色；prompt、gateway、method、budget和slot reader统一使用新版本身份。

[P]/[D]更新其活动研究关系，删除仍作为约束的“四家族不变”；保留其原型和历史表述的来源。研究[R]对旧架构版本的引用在采纳本版时同步，不原地重标历史来源哈希。

实验配置、分析脚本和L4位置表按[R]重建；测试覆盖§21。不能全局替换所有v2.1、四家族或旧ID，因为它们也出现在合法历史记录和源文件身份中。

本次只交付新SPEC，不已执行上述同步；实际编码前必须读取当前仓库和注册表以决定可复用面。

---

<a id="done"></a>
## 23. 完成标准、优先取舍与未确定事项

### 23.1 一个实现切片完成的含义

能说明输入、输出、有效域、权限、错误和未验证范围；实际writer/reader及消费者一致；调用、工具、失败与恢复可由事件重建；相关正反例在真实执行路径通过；状态文档绑定实际证据。

没有触及的层不宣称通过。schema注册、149项旧局部测试、工具安装或某份reference成功，都不自动成为新模型／三家族实验完成。

### 23.2 核心可正式运行的条件

三家族完整资格，M0–M5真实共享与失败路径，独立oracle、受信边界、全预算与计量、一次评分槽及恢复、设计簇分析可执行；pilot形成新规模依据；最终manifest经负责人批准和独立核验。

不要求pilot正效应，不要求一定有足够自然失败来做probe，不要求native／张量消融／训练／EA／Vivado／L5全部同时完成。未启用不产生依赖；已启用则保留其所有计划位置和失败。

### 23.3 优化优先级

优先真实DW→PW任务与独立参考、Tensor ABI、结构emitter、一次批量行为及公平修复；随后将同一系统用于残差和GEMM。保持全量重建优先于复杂增量缓存，普通文件交易优先于复杂多Agent协作。

不把PC扩成完整算子编译IR，不让build变成参考答案库，不为新增模型或工具搭分布式平台。实质新功能需单独明确支持域、测试和研究影响，不通过自由metadata绕过严格契约。

### 23.4 来源尚未支持的事项

实际公共task contract、parser/elaborator、目标器件／工具版本、精确模型和预算轴、完整算子权重／kernel语义、参考实现、正式独立簇数量和native可观测计量，目前不能从已交付设计文档认证为已实现。

这些属于附录C的实施选择与资格核验；本SPEC不以模型知识或未运行示例填成当前事实，也不改写[R]的研究标准以适配未知实现。

---

## 附录 A：核心服务接口责任

下表为目标API职责，不是已经实现的Python签名。边界返回应使用可区分成功、候选失败、基础设施和完整性的类型；纯函数不持有隐藏句柄或模型凭据。

| 服务 | 输入 → 输出 | 必须保持的边界 |
|---|---|---|
| PublicContextLoader.load_verified | 受信task/profile/asset refs → PublicTaskContext | 不猜语义、不读私有答案；原字节与投影视图一致 |
| PopulationPlanner.expand | 冻结簇/配置/重复/条件 → 所有计划槽与映射 | 不从已成功artifact形成分母 |
| PcBinder.assemble | design＋可信context → PC2.1 | 只用受信bindings |
| PcValidator.validate | PC/context/policy → CheckedPC或范围明确诊断 | 不调用LLM、emitter、oracle；tensor规则可追溯 |
| TensorDescriptorResolver.resolve | 局部契约＋参数 → 具体shape/type/编码/layout/sequence | 不读取模型自报resolved，不选择算法 |
| BuildPlanner.plan | CheckedPC＋固定ABI配置 → BuildPlan | 所有behavior units明确，完整语义依赖可重建 |
| AbiLowerer.expand | 已解析端口 → value/record/tensor信号映射 | lane0低位、mask高位、ready反向；不做时序重排 |
| StructureEmitter.emit | BuildPlan → 结构源码集 | 纯结构，无家族行为 |
| BehaviorComposer.compose | BuildPlan＋bundle → 提议／诊断 | 真正解析保护边界，缺unit不补答案 |
| ProjectFilePatchApplier.apply | parent＋file patch＋policy → 新scratch提议 | 原子字节交易，不智能merge、不改受信对象 |
| CandidateCommitter.commit | 提议＋method/provenance → CandidateRef | 实际字节、依赖、资产、来源与保护核验 |
| PairedCoordinator.prepare | population/config → DAG/shared checkpoints | 共享包含失败与费用，不重新采样共同起点 |
| EpisodeExecutor.advance | 状态＋允许服务 → action/next state | 策略、预算、权限由控制器掌握 |
| BudgetLedger.reserve/reconcile | action＋上界/实测 → 预留与事件 | unknown不当zero，成本不重置 |
| PublicWorker.evaluate | candidate＋公共policy → 公共outcome/diagnosis | 独立harness，模型TB不自证 |
| TerminalSelector.select | 有序候选/公共结果/预算 → terminal | 最早公共接受或最后完整，无hidden输入 |
| HiddenWorker.close_slot | 固定slot/seal/suite → opaque receipt | 唯一语义提交，私有结果只向分析域 |
| PhysicalWorker.confirm | 合格seal＋固定target → L4 outcome | 预选位置、不改源码和目标、无核心反馈 |
| RunRecovery.reconcile | manifest/journal/blobs → 可继续状态 | 使用已落盘结果，不盲目远端重试 |
| OutcomeReducer.reduce | 全人口＋阶段/事件 → 全分母结果 | false/NA/integrity/不适用/计量分开 |
| ClusterAnalyzer.estimate | 冻结配置权重/依赖＋配对结果 → 估计和资格 | 整簇/依赖组、不膨胀n、不调科学阈值 |
| NativeAgentAdapter.run（条件启用） | C0/C1配置和公共上下文 → 原生事件与终止 | 不伪装核心单次模型调用，不返回hidden给Agent |

独立oracle不从PcValidator派生算法。verification_obligations用于解释仍需测什么，不决定最终期望答案。

---

## 附录 B：研究／PC要求到实现与验收追踪

| 上位要求 | 本SPEC | 主要实施面 | 验收定位 |
|---|---|---|---|
| [R] §§0–2 三AI总体／无训练 | §§0–1、17、22 | catalog、PopulationPlan、mode guard | V41、V44 |
| [R] §3 公开事实与三种零 | §5、§15 | loader、asset reader、oracle/ABI | V03、V08、V20、V33 |
| [P] §§3–7 tensor/数值/sequence | §§6–7 | tensors、H1/H2、ABI | V06–V12 |
| [P] §§8–9 buffer/待验证 | §§6、14–15 | relation checker、outcome scope | V13–V14、V34 |
| [R] §5 纯结构/批量行为 | §§7–8 | emitter、composer | V15–V18、V21 |
| [R] §5.4 M1文件修复 | §11 | FilePatchApplier、committer | V25–V26 |
| [R] §§7、12 设计簇/依赖 | §§4、16、20 | population planner、cluster analyzer | V41–V42 |
| [R] §§9–10 M0–M5/共享/B4 | §§9–12 | methods、DAG、gateway、ledger | V22–V31 |
| [R] §8 独立oracle | §§14–15、17 | evaluator实现／suite资格 | V32–V35 |
| [R] §15 唯一槽/隔离/恢复 | §§2、13、15 | worker权限、slot、barrier、journal | V36–V39、V43 |
| [R] §12 两主比较与缺失 | §16 | reducer、冻结analysis policy | V39、V41–V42 |
| [R] §13 扩展与归因边界 | §19 | NativeAdapter、诊断开关、probe selector | X01–X04 |
| [R] §14 三家族L4 | §15、§20 | physical planner／worker | V40 |
| [R] §16 最短闭环 | §20、§23 | DW→PW垂直切片和工作包 | 对应V项的实际集成记录 |
| [R] §20 下位规范同步 | §22 | README/AGENTS/spec/catalog/registry | V44及文档引用核验 |

---

## 附录 C：必须填实的实施参数

以下是源材料尚未最终冻结或尚无实现证据的事项。开发可以使用明确临时值，正式manifest不能用占位、旧快照或模型猜测补齐。

| 参数／决定 | 所需依据 | 冻结位置 |
|---|---|---|
| 公共需求/profile/task-card实际contract | 现有仓库盘点、原对象到PC视图的核验 | WP0–WP3 |
| 三家族完整数学、权重、量化、padding、K分组 | 任务卡、独立位精确参考及工具资格 | 进入各自实验前 |
| PC2.1 schema/checker/H-policy/source hashes | 实际注册与生产路径回归 | WP3前 |
| HDL语言子集、parser、elaborator、宏/include政策 | 真实工具支持和保护正反例 | WP1–WP3 |
| 外部ABI与内部tensor命名/展开 | 公共边界、golden beats、类型和位布局测试 | WP1–WP3 |
| 全量或有依据的增量失效／缓存 | 同位宽异语义测试、无跨任务答案复用 | WP3前 |
| 主/第二模型、网关、tokenizer、解码与容量 | 开发可执行性、计量和接口能力 | pilot前 |
| B4或替代预算全部资源轴 | AI开发输出与工具测量，方法机会匹配 | paired pilot前 |
| M1文件替换和M5修复输出contracts | 父hash、原子性、权限与费用测试 | paired pilot前 |
| design_cluster/dependency/split/config权重 | 来源、近重复、开发暴露与抽样框 | 正式结果前 |
| n/c/r、δ/Δ*、统计/缺失policy | [R]要求的预结果科学决定与模拟 | 科学参数pilot前，最终规模WP4 |
| public/hidden suites与固定超时/终止 | 三家族参考、缺陷资格、协议和私有域 | WP3–WP4 |
| L3/L4实际工具/器件/资源/时序覆盖 | 参考工具路径和实际环境身份 | 模型结果前 |
| native/probe/第二模型/消融是否纳入 | [R]的范围决策、精确预算与计量限制 | WP3–WP4 |
| 批次屏障分组和批准／独立核验渠道 | 无反馈设计、访问控制与故障测试 | 正式前 |
| 第三方资产和可公开产物 | 实际来源、采用版本与使用／发布许可 | 使用及发布前 |

缺少支持时报告unsupported／未验证；实际影响研究方法或数值语义的变化须新版本和新pilot，不允许以自由metadata或隐藏adapter补救。

---

## 附录 D：材料身份、文档核对与本次范围

### D.1 实际字节来源

下面的SHA-256由本次挂载文件计算，仅确认内容身份，不是签名、授权或远端仓库版本。

| 代号 | 文件与用途 | SHA-256 |
|---|---|---|
| [R] | `2026-09-15-sr2fpga-paper1-research-plan-v2.2.zh.md`；研究上位依据 | `4f13f037889785435d9f839c70f0e034adf01fd73bb4951a3df7d66fc19ebc33` |
| [P] | `PC-2.1-AI-stream-contract-design.zh.md`；PC2.1设计与有限语义 | `d64180961809c4ff7975963d12c97d3ae48b52f100126f09c47fd8fe7d1365ec` |
| [S1] | `project-contract-2.1.schema.json`；完整PC格式 | `0ccb03b097c4393fc8497c7ed4efc409bc3dfde1e4da1a263c61baae9f8b7dd5` |
| [S2] | `design-proposal-2.1.schema.json`；模型design格式 | `c3f0463d075ed4270ebbbd168b27635e9d94d260f5496fac27335a918ac12e19` |
| [D] | `IMPLEMENTATION_DELTA.zh.md`；PC实施变更线索，研究总体以R为准 | `be915dbba5f03093b425fc5d9b281a837b58c8c0594ceb4ca8cfebc776792ba1` |
| [A] | `2026-09-14-sr2fpga-paper1-code-architecture-development-spec-v2.0.zh.md`；上一版架构设计 | `9fa43aad906f9e1ac6bfc4c2b8dc263eb14399999da48ae9af18fe3419e7ce50` |
| [T] | `conformance.json`；既有局部测试报告，未重跑 | `4f9e26192ee5c26a6cd1fa22e916c9b8af4f07167814b47a6bfbcef9b5b06b9e` |
| [H] | `2026-08-18-sr2fpga-paper1-code-architecture-development-spec.md`；最早旧SPEC历史依据 | `fd5123c3fe0c545f0229f40b65dd818780524466e1a6db0f95e810a7e3b3bf07` |

[H] 只用于说明最早旧SPEC的历史边界；当前活动方法、总体和预算以[R]为准。[D]中关于“核心四家族不变”的旧范围限制被[R]明确取代，不继续作为执行约束。

### D.2 本次实际完成与未执行

本次读取[R]完整研究计划、[A]架构基线和[P]/[D]相关完整设计内容，程序化核对两份PC2.1 schema的design定义关系与源字节，编写本完整SPEC，并做文档级章节、链接、追踪ID、样本／预算算式和新旧范围检查。

没有重跑[T]的149项局部测试，没有新建或运行emitter／parser保护／oracle，没有读取当前Git代码、调用生成模型、处理新权重／输入、执行RTL／EDA／L4/L5或正式hidden。新增接口与测试矩阵是待落实的实现要求，不是已完成测试证据。

没有对本轮材料做额外外部文献研究。实际选用工具、模型网关和native引擎时须核验当时的接口和支持能力；文中不以来源中的网页记录冒充当前安装版本。

### D.3 采纳与后续变更

**采纳状态（2026-09-15）：** 本文件已与[R]和PC2.1一并采纳为当前下位实现规范，仓库迁移已获授权，正式实验未获授权；见[R]§21。runtime版本在实际注册时绑定。后续内部重构不改变研究语义时可按受测版本记录；若影响模型可见事实、checker行为、ABI、修复、预算、suite、抽样或终止，按[R]进行结果前版本修订。研究后发现的错误保留原证据与影响，不就地改写成成功。

---

**架构结论：** 新系统以三类量化AI子系统为主总体，沿一条可核验的执行路径运行。PC2.1检查结构与声明语义，确定性构建只维护接口／布局／连接，模型负责真实计算和流控，公共反馈在预算内修复，独立oracle与物理工具提供行为和实现证据。设计簇、配置、重复、模型调用和验证用例各守身份；没有通过增加字段、模板或治理层级来代替真实方法收益。
