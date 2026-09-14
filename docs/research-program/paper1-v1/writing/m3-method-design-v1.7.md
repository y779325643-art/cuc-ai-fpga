# SR2FPGA Paper 1 M3 方法设计包

日期：2026-09-01

阶段：M3 — 新方法、模型或方案设计

权威：`paper1-freeze-v1.7`

模式：现有方案审查、封装与解释；不修改实验协议、官方评价逻辑或
trusted evaluator

## 1. 方法定位与边界

SR2FPGA Paper 1 研究的不是“模型能否生成 Verilog”，而是两个受控问题：

1. 在同一 frozen generated System-HIS 下，deterministic project
   materialization 及其 editable-surface policy 相对 free project
   generation 是否增加方法中立的 `VPP-L3@1`；
2. public evaluator 可见的修复收益是否能经受 immutable terminal 上的
   one-shot hidden final。

System-HIS 是 requirement/project contract 和实验载体，不是首个 typed
hardware IR，也不是 episode control plane。`M4-M3` 估计
materialization/edit-surface bundle，不是 skeleton text、typedness 或更少
可编辑字符的纯效应。

当前状态：

- `已核实`：M0-M5 development adapters、frozen context、artifact store、
  deterministic skeleton、development public/terminal/hidden path、paired
  block 和 G3a/G3b development conformance 面存在并有测试；
- `待核实/未完成`：positive `g3-acceptance-v1`、G3c/G3d 剩余场景、
  official hidden/VPP producer、G4b authorization 和 official campaign；
- `未产生`：任何 M0-M5 方法效果、正式 repair 效果、一般 L4 或模型训练
  结果。

## 2. 方法框架图文字版

```text
独立 RQ0 audit population
  requirement facts
    -> requirement envelope
    -> ready / needs_clarification / capability_gap
    -> non-ready 在生成前停止

正式 VPP population（只接收 evaluator-adjudicated ready requirement）
  frozen public facts + project/interface contract + platform profile
    -> frozen requirement context / public projection
    -> paired-block preparation
         S_D: shared immutable Direct initial project (M0/M1)
         S_H: shared immutable generated System-HIS (M3/M4/M5)
         S_P: shared immutable skeleton-derived initial project (M4/M5)
    -> M0-M5 matched method condition
    -> candidate project package
    -> evaluator-owned public checks and sanitized diagnosis
         M0/M2/M3/M4: no outer public repair
         M1/M5: bounded public repair under matched global budget
    -> declared terminal selection (@1 or @A)
    -> immutable terminal seal
    -> exact terminal public rerun
    -> evaluator-owned one-shot hidden final
    -> sanitized hidden status only; no feedback to generation/repair
    -> L3 synthesis / bounded RQ4 L4 characterization when authorized
    -> immutable episode, cost, provenance, failure and missingness reducers
```

图中必须把 RQ0 与 VPP population 画成两条不同入口。H-stage 只出现在
HIS-producing methods 内，作为 mechanism outcome；不得画成所有方法共享的
功能正确性 gate。

## 3. 模块说明

| 模块 | 输入 | 输出 | 职责 | 权限/不可见信息 | 代码与合同依据 | 当前证据边界 |
|---|---|---|---|---|---|---|
| A. Requirement disposition | 原始需求、显式事实、允许默认、backend capability profile | `ready` / `needs_clarification` / `capability_gap`，requirement envelope | 先消解关键歧义，再判 capability；non-ready fail-closed | 不得读取 hidden cases；不得把未知事实补成默认 | `requirement_envelope.py`, `requirement_boundary.py`, ambiguity audit contracts | Development path 已实现；signed official RQ0 population 未执行 |
| B. Frozen context and public projection | adjudicated-ready facts、platform/profile、信息权限、预算与 provenance | hash-bound frozen context、public fact projection、episode identity | 保证各方法看见内容等价的公开事实 | 不含 canonical answer、trusted TB、hidden oracle、Recipe 私有内容 | `frozen_context.py`, episode-pack/contracts | Development/excluded conformance；G4b 未签署 |
| C. Planning representation | frozen context | untyped plan（M2）或 generated System-HIS（M3–M5） | 分离一般结构化控制与 typed contract | M2 不得获得 System-HIS schema/checker；Direct 不要求发出 HIS | `method_adapters.py`, `generation/context_his.py` | Adapter 已实现；方法效果未测 |
| D. H-stage validation | generated System-HIS、requirement envelope、platform profile | H0–H3 mechanism report 或 pre-candidate stop | 结构、需求忠实度、跨字段/能力适用性检查 | 只适用于 HIS methods；不能代替功能 oracle | `FrozenContextSystemHisValidationFacade`, H-stage contracts | G1 closed；完整方法价值仍是假设 |
| E. Deterministic materialization | validated frozen System-HIS | manifest、module shells、top wiring、constraints、TB scaffold、behavior holes | 机械物化声明的工程结构并限定 editable surface | 不作新的架构选择；不得写入 task-specific hidden answer | `contract_skeleton.py`, `context_his.py` | 代码路径存在；只能称 bundle treatment，不称效果 |
| F. Behavior generation | free-project context 或 skeleton/behavior-hole context | complete candidate project package | M0/M2/M3 自由生成完整项目；M4/M5 只填声明行为区域 | M4/M5 不能修改 trusted structure、TB、constraints 或 evaluator | direct/untyped/HIS facades, parsers, skeleton merge checks | Development adapters 已实现；complete official ladder 未运行 |
| G. Public evaluation and bounded repair | sealed attempt candidate、公开 tool outputs | authoritative public outcome、sanitized diagnosis、可选 patch | 用公开 lint/sim/public-L2/L3 信息指导 M1/M5 repair | 不能读取 hidden outcome；hidden failure 绝不触发 repair | `DataGenerationAgent`, public evaluator contracts, repair facades | Development/excluded path；G3 remaining repair scenarios open |
| H. Terminal selection and seal | 按序完整 public-evaluated attempts | declared terminal selection、immutable terminal candidate | `@1` 取唯一候选；`@A` 取 earliest accepted，否则 last complete | selection rule 预声明；不得看到 hidden 后再选 | `terminal_selection.py`, `artifact_store.py` | Development authority；`official_authority=false` |
| I. Hidden final authority | exact terminal seal、private commitment、public hashes、tool policy | opaque hidden ref、reducer-only sanitized `pass/fail/not_run` | 物理隔离 candidate/evaluator stores；consume once；不返回诊断 | private cases、raw outcome、private identifiers不跨回 candidate side | `evaluator_dispatch.py`, hidden/episode contracts | Development conformance only；official producer 缺失 |
| J. Evidence and cost reducers | attempts、events、artifact refs、tool/model costs、public/hidden/L3 states | episode outcome、VPP development projection、三种 cost view、failure/missingness | 让分母、权限、失败前沿和成本可重建 | reducer 不生成新 outcome，不把 `not_run` 改成 fail | `artifact_store.py`, `episode_outcome.py`, `cost_accounting.py`, `block_cost_accounting.py` | G3a/G3b 已实现；positive G3/G4b authority 缺失 |

## 4. 操作流程

### 4.1 Requirement boundary

1. 从请求构建 provenance-bearing `RequirementEnvelope`。
2. 提取 explicit/default/assumption/unknown facts。
3. 关键事实有两个以上实质解释时输出 `needs_clarification`。
4. 只有意图已解析但 backend 不支持时输出 `capability_gap`。
5. `ready` 才能进入 VPP method population；RQ0 audit 与 VPP population
   保持分离。

### 4.2 Frozen episode preparation

1. 冻结 public requirement facts、project/interface contract、platform、
   provider/model/inference provenance、budget、tool/evaluator commitments。
2. 为 `(semantic_instance_id, replicate_id)` 建立 stable `paired_block_id`。
3. 使用独立 `execution_schedule_seed` 平衡方法执行顺序；它不等于 provider
   decoding seed。
4. 物化 shared checkpoints：M0/M1 共用 `S_D`，M3/M4/M5 共用 `S_H`，
   M4/M5 共用 `S_P`。
5. 记录 actual campaign、standalone end-to-end、post-checkpoint incremental
   三种成本视图。

### 4.3 Planning and generation

1. M0/M1：Direct path 直接产生 full project；M1 从相同 initial Direct
   project 开始 repair。
2. M2：先产生 untyped structured plan，再自由产生 full project。
3. M3：产生并验证 System-HIS，再由 no-skeleton generator 自由产生 full
   project。
4. M4：复用 M3 的 frozen HIS，trusted lowerer 建 skeleton，模型只填写
   behavior regions；无 outer EDA repair。
5. M5：复用 M4 的 initial skeleton project，在与 M1 相同的 global repair/
   tool budget 下进行 public repair；HIS/HIS2PROJECT correction 也必须显式
   计入预算和 lineage。

### 4.4 Public evaluation and repair

1. 每个 attempt 先被 sealed 为 public-evaluation candidate。
2. evaluator-owned public authority 运行公开检查并产生 authoritative outcome。
3. 仅公开、sanitized diagnosis 可进入 M1/M5 repair。
4. patch 后重新 seal、重新运行公开 checks；保留失败、patch、call、cost 和
   no-progress。
5. infrastructure failure、candidate failure、capability gap、`not_run` 分开。

### 4.5 Terminal and hidden final

1. 按 `@1`/`@A` 规则选择 terminal；不允许 outcome-dependent cherry-pick。
2. 终态 candidate seal 后，exact project 重新接受 terminal public evaluation。
3. hidden authority 在物理分离 store 上 consume once。
4. candidate side 只得到 opaque ref；reducer 最多发布 sanitized
   `pass/fail/not_run`。
5. hidden outcome 永不回流到 generation、repair 或 terminal selection。

### 4.6 Outcome and bounded physical depth

1. VPP 由 method-neutral project contract、L0/L1/public-L2/one-shot
   hidden-L2/L3、权限与 provenance 完整性共同决定。
2. H0–H3 只对相应方法报告 mechanism outcome。
3. RQ4 在预声明 OpenXC7 子集上描述 L3→L4 attrition、timing/resource；
   不授权 L5、Vivado、cross-vendor 或一般部署外推。

## 5. M0–M5 条件与唯一变化因素

| 条件 | Planning | Project construction | Public outer repair | Shared artifact | 主要比较角色 | 禁止解释 |
|---|---|---|---|---|---|---|
| M0 Direct | 无 HIS/plan | requirement → free full project | 否 | 与 M1 共用 `S_D` | Direct baseline；M4-M0 primary 的对照 | 不要求 H-stage；不能因无 HIS 被额外惩罚 |
| M1 Direct-Repair | 同 M0 | 同一 initial Direct project | 是 | `S_D` | generic public-repair control；M1-M0 secondary | 当前不能称 exact HORIZON reproduction |
| M2 Structured-Direct | untyped structured plan | plan → free full project | 否 | 无 System-HIS | M3-M2 secondary representation-bundle 对照 | 不得使用 HIS schema/checker/skeleton |
| M3 HIS-Free | generated and H-validated System-HIS | HIS → free full project，true no-skeleton | 否 | 与 M4/M5 共用 `S_H` | M4-M3 primary 的直接对照 | M3-M2 不是 typing-only effect |
| M4 HIS-Skeleton | 与 M3 相同 frozen HIS | deterministic skeleton + behavior fill | 否 | `S_H`；与 M5 共用 `S_P` | materialization/edit-surface treatment；M4-M3、M4-M0 primary | 不得称 skeleton-only、template-only 或已有效 |
| M5 HIS-Online | 同 M4 | 从同一 `S_P` 开始 | 是 | `S_H` + `S_P` | evaluator-separated repair；M5-M4 RQ2 primary | repair/correction call 必须计费；hidden 不得反馈 |

Repair probe `R_generic` 与 `R_HIS` 从相同 frozen failing M4 checkpoint 开始，
属于 RQ2 mechanism analysis，不是第七、第八个 headline generator。

## 6. 资源与条件清单

| 类别 | 必需资源/条件 | 当前状态 | 对 M3 的含义 |
|---|---|---|---|
| Research authority | v1.7 freeze、argument map、section contracts、claim registry | 已核实 | 方法写作必须保持同步 |
| Contracts | project package/envelope、System-HIS v1.2、episode/terminal/public/hidden/cost contracts | G1/G2 locally closed；其余逐步实现 | schema conformance不等于功能结果 |
| Method runtime | M0-M5 adapters、frozen context、shared checkpoints、repair controller | development implementation exists | 可描述实现，不可描述效果 |
| Artifact integrity | write-once store、content hash、events、candidate seal、one-shot ledger | implemented/tested in development | 支撑可审计性主张的实现面 |
| Model/provider | 同一冻结 model/tokenizer/quantization/context/decoding family；seed mode由G4b选择 | official configuration 未冻结 | 不得声称 common randomness/deterministic replay |
| Public tools | lint、simulation/public-L2、synthesis及其版本和费用 | development tools存在；official manifest未签 | 必须按方法计费并区分 infrastructure failure |
| Hidden evaluator | private cases/commitment、物理分离 store、official CLI/process | development boundary exists；official producer missing | 阻止 official execution-ready 主张 |
| Statistical preparation | paired block、Holm、CI、minimum effects、power/missingness rules | v1.7 protocol存在；G4a/G4b未闭合 | 方法图可显示比较，不显示结果 |
| L4 | OpenXC7 named subset、tool/version/part/constraints | 历史代表性证据；official RQ4未运行 | 仅作有界 characterization 计划 |
| Governance | positive G3 acceptance、G4b receipt、official command gate | 未完成 | official campaign保持 NO-GO |

## 7. 相对近邻工作的具体改进点

以下是研究设计的候选区别，不是已证明效果：

| 近邻 | 已占据的位置 | SR2FPGA 不能主张 | 当前可检验区别 |
|---|---|---|---|
| RealBench | 60 module + 4 system-level from-scratch tasks，详细规格、formal verification | 首次 system-level RTL generation；此前无强 oracle | 将完整公共工程合同、matched M0-M5、public/hidden authority、固定分母和 FPGA endpoints 放入同一协议 |
| HINT | executable hardware-intent route、checking/lowering、ASIC synthesis | 首个 executable/typed intent；structured route 本身新 | 同一 frozen HIS 下 free vs materialized project 的 matched bundle comparison；FPGA project artifacts 与 evaluator separation |
| HORIZON | structured harness→project pack、Git-native repository evolution、visible evaluator convergence、trajectory/cost | 首个 repository agent、EDA loop、trajectory retention | requirement/project semantic contract；new-project construction；immutable terminal + one-shot hidden final；method-neutral VPP |
| HWE-Bench | 417 real existing-repository bug repairs、native regression、cross-artifact coordination | 首次 repository-scale hardware repair | starting-state 区分；from-requirement construction 与 matched Direct/HIS treatments |
| CLOSER-Bench | budgeted spec-to-RTL/RTL-to-GDS/spec-to-GDS、tool cost、cross-stage recovery | 首次 cross-stage closure 或 cost accounting | FPGA rather than Sky130 GDS endpoint；paired method interventions；public/hidden authority 与 fixed denominator |
| ChipVerilog | 64 OpenCores-derived cross-module/full-system RTL targets、equivalence/simulation | 首次 cross-module/full-system benchmark | generated artifact set extends beyond target RTL to method-neutral project package and named FPGA evidence |

## 8. 方法图建议

### 图位

- 临时编号：`Figure 2`
- 建议位置：Method 章节开头，在问题定义、M0–M5 总览段之后
- 优先级：核心解释图
- 类型：`EXPLANATORY`
- Readiness：`PLAN_READY`
- 暂定图名：**SR2FPGA matched project-generation and evaluator-separation framework**

### 为什么需要图

读者需要同时理解两条 population、三种 shared checkpoint、六个方法条件、
public repair、terminal seal、hidden authority 和 evidence reducers。压缩成单
流程会隐藏比较变量与权限边界。

### 准备表达什么

- 表达：facts/privileges、M0–M5 唯一变化因素、shared artifacts、public-
  repair/hidden-final 分离、terminal/cost/evidence lineage；
- 不表达：任何方法优于另一方法、任何 pass rate、official G3/G4b closure；
- 阅读顺序：boundary → matched treatments → public/terminal/hidden → evidence。

### 方案一：多面板全览

- **A Requirement boundary**：RQ0 独立入口与 ready-only VPP 入口；
- **B Matched method ladder**：M0–M5、`S_D/S_H/S_P` 和比较括号；
- **C Evaluator separation**：attempt→public→repair→terminal→one-shot hidden；
- **D Evidence plane**：artifact store、cost views、failure/missingness、VPP/RQ4。

优点：一张图可独立解释全文。风险：信息密度高，TRETS 单栏下可能拥挤。

### 方案二：全览图＋独立模块图（推荐）

- **Figure 2 全览**：boundary、M0–M5 和 public/hidden 主流程，只保留关键
  权限边界；
- **Figure 3 Matched-treatment design**：六方法、shared checkpoints、RQ1/RQ2
  comparisons 和 cost attribution；
- **Figure 4 Evaluator and evidence authority**：candidate/public/terminal/
  hidden stores、one-shot ledger、sanitized outcome 和 reducer lineage。

优点：每张图只承担一个解释任务，可在双栏版式下保持可读性；更符合复杂
方法不能强压一图的要求。代价：主文占用三张图，需结合最终页数决策。

### 制作条件与底线

- 不需要实验结果或 Python/R 数据；
- 使用代码化矢量路线（SVG/PDF）而非结果图或生成式位图；
- 所有模块名称来自 v1.7/当前代码，不虚构未实现 authority；
- 使用实线表示已实现 development surface、虚线表示冻结协议/未完成
  official gate；
- 用户确认图位和拆图方案前不渲染。

## 9. Evidence ledger

| 表述 | 状态 | 允许写法 |
|---|---|---|
| M0-M5 adapters存在 | 已核实 | “implemented/tested on development surfaces” |
| G3a/G3b exists | 已核实、范围受限 | “development conformance infrastructure” |
| G3 accepted | 未完成 | 不得写 |
| Official hidden/VPP exists | 未完成 | 不得写 |
| Materialization improves VPP | 假设 | 仅写 RQ/estimand |
| Public repair survives hidden final | 假设 | 仅写 RQ2 |
| OpenXC7 L4 generalizes | 不支持 | 仅报告命名子集和分母 |

