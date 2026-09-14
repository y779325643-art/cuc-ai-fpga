# SR2FPGA Paper 1 M4 实施路径与原型审查包（v1.7）

日期：2026-09-04  
审查 checkout：`c32fce02db1e`（`develop`）  
阶段：M4“实施路径与原型构建”  
性质：只读实现审查与后续实施计划；不是实验执行或结果报告

## 1. 范围、权威与状态词

本文件承接 `paper1-freeze-v1.7`、`docs/current-status.md`、Paper-1
workspace 的 argument map / section contracts，以及 M3 方法设计包。M3 的十个
模块是唯一框架；不另建平行架构。

本次没有修改代码、合同、测试、artifact、M0–M5、实验协议或 evaluator；没有
调用真实模型、启动 G5、运行 official campaign 或产生官方评价结果。

状态定义：

- `implemented`：当前代码存在相应执行路径；不表示产生方法效果。
- `verified`：本 checkout 上有可复现测试或可核验 artifact 支撑限定的实现事实。
- `partial`：部分路径存在，但达到 Paper-1 验证目标所需的闭环仍缺关键环节。
- `missing`：当前没有所需实现或权威 artifact。
- `out-of-scope`：不属于 Paper-1 M4。

证据标记：`已核实`、`待核实`、`AI推断`。测试通过、development smoke 和历史
L4 均不得解释为方法效果。

## 2. 当前实现—方法模块—证据映射表

| M3 模块 | 当前实现文件与入口 | 注册合同 / 数据接口 | 测试与可复现实证 | 状态 | 与 Paper-1 核心验证目标的关系 | 最小剩余实施缺口 | 风险、依赖与备选方案 |
|---|---|---|---|---|---|---|---|
| A. Requirement disposition | `requirement_envelope.py::build_requirement_envelope/route_requirement`；`requirement_boundary.py::evaluate_requirement_boundary`；`requirement_audit.py` | requirement audit case/replay/outcome/witness/event；System-HIS backend capabilities | `test_sr2fpga_agent_requirement_envelope.py` 等；2026-09-04 聚焦测试通过【已核实】 | `partial` | 阻止未知工程事实被静默默认，分离 RQ0 与 VPP population | 签名的 official RQ0 fixture population、冻结统计阈值与正式执行器【待核实】 | 风险：规则误拦截/漏拦截。依赖：gold adjudication。备选：保持 `needs_clarification` / `capability_gap` fail-closed，不让 non-ready 进入方法路径 |
| B. Frozen context and public projection | `frozen_context.py::freeze_ready_requirement_context/build_development_episode_pack`；`paired_block.py`；`block_preparation.py` | `episode-pack-v1`、`paired-block-v1`、`development-shared-checkpoint-manifest-v1`、model gateway provenance | paired block、block preparation、full-pack tests；当前 G3c replay 目录只含生成输出【已核实】 | `partial` | 保证 M0–M5 的公开事实、配对身份和 shared checkpoint 可比 | signed official pack/evaluator commitment loader 与 G4b authority【待核实】 | 风险：调用方自报身份或旧兼容路径绕过。备选：无完整、可验证 pack 时拒绝授予 G3/G4b/official 权限 |
| C. Planning representation | `method_contract.py::method_contract`；`method_adapters.py::MethodAdapterRegistry`；`generation/context_his.py`；`runner.py::_bind_runner_method_generator` | `system-his-v1.2` 及 well-formedness/compatibility；planning artifacts 通过 write-once `ArtifactStore` 引用 | `test_sr2fpga_agent_method_adapters.py`、`test_sr2fpga_agent_runner_method_dispatch.py`【已核实】 | `partial` | 保持 M2 untyped plan、M3–M5 System-HIS 和 Direct 路径的权限差异 | 消除剩余隐式兼容分发；将每次调用的 capability/provenance 绑定到完整 G3 acceptance【待核实】 | 风险：条件间信息泄漏。备选：以 closed `MethodContract` 和 adapter registry fail-closed，非声明能力不分发 |
| D. H-stage validation | `his_validation.py::validate_*_h_stages`；`FrozenContextSystemHisValidationFacade`；System-HIS checker/fidelity/capabilities | System-HIS H-stage outcome、well-formedness、compatibility、fidelity、capability contracts | H-stage/System-HIS tests；G1 locally closed【已核实】 | `implemented`，限定验证为 `verified` | 为 HIS-producing methods 提供 H0–H3 mechanism outcomes 与 pre-candidate stop | 把 M5 的真实 H-stage correction 场景及其 episode outcome 纳入 artifact-derived G3 matrix【待核实】 | 风险：把 H-stage 当功能 oracle。备选：H0–H3 仅作机制状态，功能正确性仍由 public/hidden evaluator 决定 |
| E. Deterministic materialization | `contract_skeleton.py::build_contract_skeleton_project/merge_behavior_files`；`context_his.py::_build_skeleton/lower_skeleton_project_output` | `project-package-v1`、`project-envelope-v1`、System-HIS 与 shared checkpoint refs | `test_sr2fpga_agent_contract_skeleton.py`、adapter/block tests；G3c replay 中 M3/M4/M5 HIS SHA-256 相同，M4/M5 `top.sv` SHA-256 相同【已核实】 | `implemented`，限定验证为 `verified` | 实现 M4 相对 M3 的 deterministic-materialization/edit-surface treatment | 将现有哈希事实纳入注册 manifest、完整 event lineage 和正向 G3 acceptance【待核实】 | 风险：将 treatment 误称 pure skeleton effect。备选：始终按 v1.7 称 materialization/edit-surface bundle；哈希不闭合则整 block 不获资格 |
| F. Behavior generation | `episode_executor.py::emit_candidate/_lower`；Direct/untyped/HIS generation facades；`method_adapters.py` repair-capable adapters | project package/envelope；planning/model-output refs；method contract | adapter、runner dispatch、full-pack smoke tests【已核实】 | `partial` | 提供 M0/M2/M3 free-project 与 M4/M5 behavior-hole 两类候选生成面 | 统一 M5 project-repair facade ownership；闭合完整 M0–M5 G3 scenario matrix【待核实】 | 风险：M4/M5 越权修改结构/TB/constraints。备选：lowerer 与 merge validation 拒绝越界文件，输出失败状态而非修补 trusted surface |
| G. Public evaluation and bounded repair | `agent.py::_evaluate_development_attempt_publicly/_run_pipeline`；`public_evaluator.py`；`public_l2_harness.py`；`repair.py` | public-evaluation-candidate v1/v2、development public outcomes、public L2 harness、attempt event | public evaluator/L2、repair engineering smoke、episode/full-pack tests【已核实】 | `partial` | 为 M1/M5 提供 evaluator-owned、repair-visible 的 sanitized diagnosis，并与 hidden 隔离 | G3c/G3d 中真实的 public failure→diagnosis→patch→rerun，以及 no-progress、capability、failure/missingness 的 artifact-derived acceptance【待核实】 | 风险：development diagnosis 被误当 official，或 hidden 反馈进入 repair。备选：仅注册 public outcome 可见；hidden ref 不参与 repair；未闭环则 `not_evaluated` |
| H. Terminal selection and seal | `terminal_selection.py::select_development_terminal_candidate`；`artifact_store.py::seal_candidate/seal_public_evaluation_candidate`；`agent.py::_select_and_seal_development_terminal` | development terminal selection、terminal candidate/public outcome contracts | `test_sr2fpga_agent_terminal_selection.py`、artifact/episode tests【已核实】 | `implemented`，development authority `verified` | 固定 `@1`/`@A` 选择规则，防止观察 hidden 后 cherry-pick | official authority/command gate 对同一选择与 seal 的签名绑定【待核实】 | 风险：旧路径或人工选择绕过。备选：无完整 public-evaluated sequence 或哈希不匹配即 fail-closed |
| I. Hidden final authority | `evaluator_dispatch.py::DevelopmentHiddenEvaluationAuthority.evaluate_once`；`agent.py::_run_development_hidden_evaluation` | `official-hidden-outcome-v1` schema；`development-hidden-conformance-outcome-v1`；opaque hidden ref；episode outcome | evaluator-dispatch、episode/full-pack spy/fail-closed tests【已核实】 | `partial` | 验证 candidate/evaluator store、consume-once 与不向 repair 泄漏的边界设计 | official hidden/VPP producer、两轴 hidden missingness、private commitment loader、独立 process/CLI 与 G4b verifier【缺失】 | 风险：把 development reducer 当 official oracle。备选：继续固定 official/pass-credit/G3/G4b flags 为 false；缺生产者则 hidden=`not_evaluated` |
| J. Evidence and cost reducers | `episode_outcome.py`；`cost_accounting.py`；`block_cost_accounting.py`；`paired_cost_views.py`；`artifact_store.py` | attempt event、cost summary、development episode/full-pack outcome、paired cost reconciliation、`trajectory-v2` | cost、block cost、paired cost、episode outcome、full-pack tests；333/333 聚焦测试通过【已核实】 | `partial` | 重建固定分母、三成本视图、失败前沿、terminal/hidden lineage；不生成新 outcome | positive artifact-derived `g3-acceptance-v1`、完整两轴 missingness 与 official reducer/manifest binding【缺失】 | 风险：reducer 将缺失重编码成成功/失败或把 shared cost 归到单一方法。备选：不完整输入保留 incomplete/`not_evaluated`，不授予 paired-confirmatory 权限 |

### 2.1 Artifact 边界说明

当前发现两个未晋升的 G3c replay 目录：

- `artifacts/g3c-eval-replay-v1-1-pilot-002/`
- `artifacts/g3c-eval-replay-v1-1-pilot-002-l2/`

其中 M3/M4/M5 的 `system_his.json` SHA-256 均为
`1d495a9aae2838bc78e18bb6ff50891caa21a410a560713b3d0e205da1693dbc`；
M4/M5 的 `rtl/top.sv` SHA-256 均为
`8c93bba2c3f1f7ffb90c2205e39282745e2c39b2d40a5fb7c4dc9fd2b2bb459b`。
这支持“该 replay 输出呈现 shared HIS/initial project 一致性”的有限实现事实【已核实】。
目录没有正向 `g3-acceptance-v1`、完整场景清单、官方权限或晋升记录，因此不得据此
宣称 G3 已通过、M4/M5 有效或 official VPP 已运行【已核实】。

`reports/evidence/legacy-runs/` 下的 L4 和历史运行只作历史 provenance；不进入
本次 M4 原型效果判断【已核实】。

## 3. 原型功能清单

| 原型能力 | 当前结论 | 可允许的表述 |
|---|---|---|
| requirement facts 提取、路由与 non-ready fail-closed | `partial` | development implementation exists |
| 冻结 context、episode pack、paired block 与 shared checkpoint | `partial` | development/excluded conformance exists |
| M0–M5 closed method contracts 与 adapter dispatch | `partial` | adapters are implemented and tested |
| H0–H3 System-HIS validation | `implemented/verified` | mechanism conformance；不是功能正确性 |
| deterministic skeleton 与 behavior-hole merge | `implemented/verified` | treatment implementation；效果未测 |
| public evaluation、sanitized diagnosis 与 bounded repair | `partial` | development path exists；G3 repair scenarios 未闭合 |
| terminal selection、candidate seal 与 exact reconstruction | `implemented/verified`（development） | selection/integrity conformance |
| one-shot hidden boundary | `partial` | development isolation conformance；非 official hidden |
| event/cost/episode/full-pack reducers | `partial` | development accounting/reconstruction conformance |
| official G3 acceptance / G4b verifier / campaign unlock | `missing` | 不得声称 execution-ready |
| Training、LoRA、模型微调 | `out-of-scope` | Paper-1 不授权训练 |

## 4. 流程文档

当前原型的最短可信路径如下；任一 authority/hash/lineage 检查失败均保持
fail-closed：

1. 原始 requirement → `RequirementEnvelope` → clarification/capability/ready。
2. ready facts → frozen context/public projection → development episode pack。
3. `(semantic_instance_id, replicate_id)` → paired block 与 balanced order。
4. block preparation 先物化 `S_D`、`S_H`、`S_P`，记录 method-neutral cost。
5. method adapter 按 M0–M5 唯一条件读取允许的 frozen artifacts。
6. HIS methods 执行 H0–H3；失败在 pre-candidate 阶段终止。
7. Direct/free-project 或 skeleton/behavior-hole 路径生成 candidate package。
8. attempt seal → evaluator-owned public checks → authoritative sanitized public outcome。
9. 仅 M1/M5 可在共同上限内读取 public diagnosis，修复后重新 seal/evaluate。
10. `@1`/`@A` 选择 terminal → exact terminal rerun → immutable terminal seal。
11. development hidden authority 在分离 store 中 consume once，只返回 opaque ref。
12. reducers 重建 episode/full-pack、missingness 与三成本视图；不自行创造 pass。

从第 1–12 步得到的是 development/excluded conformance 原型。只有 positive G3
acceptance、G4a、excluded G5、signed G4b 依次闭合后，official command gate 才能
成为合法入口；本文件不越过该顺序。

## 5. 实施计划

以下是剩余最小路径，不授权在本次执行：

| 顺序 | 实施包 | 复用现有实现 | 最小新增/闭合项 | 完成判据 |
|---|---|---|---|---|
| M4.1 | G3c evaluation/repair closure | public evaluator、repair facade、terminal/hidden development authority | artifact-derived M1/M5 failure→diagnosis→patch→rerun；no-progress、public/hidden pass/fail 与两轴 missingness 场景 | 每个冻结场景都有注册输入、事件、seal、outcome、cost 和 fail-closed 断言；无真实模型要求 |
| M4.2 | G3d capability/provenance closure | gateway provenance、budget/cost reducers | per-call capability binding；M5 H-stage correction 与 project repair lineage；provider/public/hidden/L3 failure 分类 | reducer 从 artifact 而非调用方声明得出每个矩阵单元状态 |
| M4.3 | Positive G3 acceptance | full-pack/episode reducers、G3a/G3b artifacts | 最小 `g3-acceptance-v1` producer/verifier 及注册 schema；仍固定 official/pass-credit/G4b 为 false | 完整冻结 G3 matrix 全绿且 acceptance 可从 refs 重算；无 official side effect |
| M4.4 | G4a candidate preparation | contracts/catalog/current evaluator inventory | candidate VPP split、oracle qualification、统计实现、最小效应/功效方案与 disjoint audit population | 候选包完整但明确未签名、未执行 G5/official |
| M4.5 | G4b implementation preparation | write-once store、hash/commitment、reducers | campaign-freeze verifier、无副作用 prerequisite check、authorization receipt、official command gate | 仅在 G5 之后、全部前置 refs 验证通过时才能签署；本阶段只准备，不运行 |

最小优先级是 M4.1→M4.3。G4a/G4b 不应先于 positive G3 closure 编码成可绕过的
“空壳授权”。这是一项基于依赖图的 AI 推断，不是实验事实【AI推断】。

## 6. 测试准备材料

### 6.1 本次已执行的只读聚焦验证

命令使用 `python -m pytest -p no:cacheprovider`，覆盖 16 个现有 test modules：
requirement envelope、method adapters、H-stage、contract skeleton、public evaluator/L2、
terminal selection、evaluator dispatch、episode outcome、attempt/block/paired cost、paired
block、runner dispatch 与 full-pack smoke。

结果：`333 passed in 1666.45s (0:27:46)`【已核实】。环境为 Windows、Python
3.13.2、pytest 9.1.1。该结果只验证当前 checkout 的离线 fake/deterministic
实现与 fail-closed 合同；未运行真实模型、official held-out、正式 hidden producer、
训练、证据晋升或 Paper-1 效果分析。

### 6.2 后续最小测试矩阵

| 层 | 准备项 | 必须断言 | 禁止升级的解释 |
|---|---|---|---|
| Contract | 新 G3 acceptance schema/manifest tests | exact version、required refs、authority flags false、tamper fail | schema pass ≠ G3 pass |
| Unit | acceptance reducer/capability binding | 只从 verified refs 派生；缺失/冲突 fail-closed | unit pass ≠ end-to-end |
| Scenario | 冻结 G3c/G3d cells | M1/M5 patch transitions、M5 H correction、hidden non-feedback、missingness 两轴 | fake client pass ≠ model effectiveness |
| Integration | complete six-member paired block | S_D/S_H/S_P identity、balanced order、budget、terminal、one-shot hidden、cost views | development full-pack ≠ official VPP |
| Negative | tamper/duplicate/legacy/partial paths | 无 G3/G4b/pass-credit/official 权限 | 拒绝路径不证明任务正确性 |
| Reproduction | clean checkout command + artifact inventory | hashes、versions、exit code、machine-readable acceptance refs | local machine result ≠ remote CI |

### 6.3 测试前置资源

- 无需真实模型：G3 implementation conformance 可使用 fake/deterministic clients。
- 需要固定且注册的 scenario fixtures、公开 harness、private commitment 占位接口、
  provider capability manifests、tool availability/missingness fixtures。
- 需要 artifact 根目录与 evaluator 根目录物理分离，所有输出写入 `artifacts/`。
- G4a/G4b/official 测试必须在对应授权到位后另行执行；不得用本次结果补写。

## 7. 图件处理

M4 不新增图。M3 的 Figure 2（全览）、Figure 3（matched treatment）和 Figure 4
（evaluator/evidence authority）已经覆盖实施流程和权限边界；新增一张“实施流程图”
会重复信息。后续只有当代码入口与 Figure 2–4 出现结构性偏差时才更新现有图，而不
创建第四套平行表达【AI推断】。

## 8. M4 当前结论

当前原型已覆盖十个模块，且其主要 development/excluded 路径可在当前 checkout
复现；因此“已有可审查原型”成立【已核实】。但它尚不能完整支撑 Paper-1 的后续
验证目标：positive artifact-derived G3 acceptance、剩余 G3c/G3d、两轴 hidden
missingness、official hidden/VPP producer 与 G4b verifier/command gate 未闭合
【已核实】。

因此本次结论为：**M4 部分通过，保持 M4 transition hold；不得进入 M5。**

