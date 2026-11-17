# M3/M4 结构生成研究：P03 最小实施范围

当前适用性：局部责任划分候选已按最后一轮停止条件退出核心贡献，[决定与依据](local-responsibility-bounded-design-review.md)已归档。下文原 I 项和新增 D 项仅为历史技术盘点；**本篇不为该候选追加 D2/D3 planner 或表达式开发**。后续新核心确定后再重定实施范围，不按本稿自动执行。

日期：2026-10-21。状态：P02 的拟实施范围；当前没有实施授权、代码修复或实验执行。本轮只写本文及 [contract-reuse-map.md](contract-reuse-map.md)，不改源码、测试、注册 schema 或实验配置，不写论文正文。唯一进度记录是[论文清单](../2026-10-21-structure-generation-paper-checklist.zh.md)。下文函数与 `路径:行号` 是本次只读核查的当前定位，不是已经完成的变更；表内省略的 Python 文件前缀均为仓库相对目录 `agent/src/sr2fpga_agent/`。

## 1. 范围、处理变量与实现选择

适用性：下列 I1–I8 是原 M3/M4 两条件方案的准备范围。用户已选择先细化[局部责任划分机制](local-responsibility-method-card.md)；划分器、表达式承载、跨区/叶模块边界与新增匹配条件均未包含在原实现完成量中，须方法评审后补齐实际改动面。本文不代表新机制已获实施授权。

只接通旧 System-HIS 下共享生成 PC 的 M3/M4 初始生成。M3 自由输出完整 RTL 工程；M4 由程序生成结构并一次批量填行为。两组共同公开需求、同一 PC 和共同语义准入；无契约修复、工程修复、工具反馈追加调用。估计的是“确定性结构构建＋受限输出责任”的联合机制，不是只改变提示文本或 tensor checker 的单独效应。

选择在原 Runner／facade／ArtifactStore 中接通显式 M3/M4 研究 profile，沿 `PairedArtifactCoordinator`＋`PairingKey`＋两条单 episode 链工作，不进入完整 paired-block/full-pack 层；从原始事件重建配对分析。旧六方法路径及历史验收保持原入口和版本。本篇不执行 M0/M1/M2/M5，不增设第二套 agent、事件系统、评分或进度记录。首选不生产 paired-block、shared-manifest、full-pack 或 paired-cost companion；不把四个 schema 后继当必然前置。

旧 System-HIS 方法、当前 `paper1-v2.2` 和 PC 2.1 是不同协议。当前计划 `docs/specs/2026-09-15-sr2fpga-paper1-research-plan-v2.2.zh.md:264` 禁止共同准入依赖 M4 emitter，`:508` 说明联合效应；旧代码不符合的地方记录为 `implementation_protocol_drift`，不能直接宣称迁移完成。现 `agent/src/sr2fpga_agent/runner.py:539` 仍拒绝当前研究版本绑定，本篇不能删除这一 guard 获取资格。

## 2. 已发现、尚未修复的两个关键混杂

### F1：M4 的额外任务族 TB 信息

实际路径：`contract_skeleton.py:381` 的 `_testbench` → `:393` 的 `_deterministic_functional_testbench` → `ProjectGenerator().generate(...).files["sim/tb_top.v"]`（`:403`）。`prompts.py:1252` 的 `_frozen_his_skeleton_messages` 在 `:1273` 把整个 skeleton 文件字典送入模型；M3 的 `_frozen_his_free_project_messages`（`:1285`）没有同样的任务族 TB。即使评分不运行 candidate TB，模型已收到额外行为示例，不能归因成只有结构差异。

**窄修法选择：** 两组模型均不接收任务专用 TB／oracle／参考实现。M4 prompt 改用 controller 构造的模型可见结构投影：按声明 RTL、manifest 和公开约束的 allowlist 读取；排除 `sim/`、candidate TB、预测 QoR 报告及一切 evaluator-private 内容，不能按字符串包含 “testbench” 粗糙过滤。PC 与公开 facts 仍完整、相同。M3 不补发任务族示例，避免扩大研究变量。

最终工程中若保留既有程序提供的 candidate TB，只能作为明示来源的调试／advisory 文件，既不发送模型，也不能计独立功能成功；共同可信 evaluator 忽略两组自带 TB。M3 的工程输出责任与 M4 的程序供给责任须在协议中明示。若 P01/P02 要求两组相同的候选 TB 交付责任，则需另行对称处理；不得在运行后按结果决定。默认不修改全局 `ProjectGenerator` 的任务算法或 oracle。

### F2：共享 H2 准入先运行 M4 emitter

`his_validation.py:121` 的 frozen validator 在 `:151` 执行 `_lowerability_errors`，随后 `:154` 调 `_dry_lowerability_errors`；后者在 `:287` 执行 `build_contract_skeleton_project`。这会把 emitter 支持情况变成两组共同选择条件。

**窄修法选择：** 新 profile 使用显式、带版本／策略 hash 的共同数据语义准入，保留 schema、既有合法性／身份／需求忠实度检查；把 emitter 的实际 dry build 和静态结构 crosscheck 移到 M4 独有构建阶段。不得只是删除 `_dry_lowerability_errors` 让更多 PC 算通过：必须逐条核对它实际阻止的 malformed 情况，为有共同语义依据的错误保留不执行 emitter 的检查及负例；其余 emitter 限制才记为 M4 构建失败。若无法完成这种分解，则 P03 未通过，付费 pilot 不得先行。

原 validator 默认旧语义保持；新准入通过原 `FrozenContextSystemHisValidationFacade` 的显式 profile 接入，不由候选 PC 或任意文件字段自行选择。policy、源码、capability profile 与运行配置均绑定到现有冻结／来源记录。新共同准入不得报告为“旧完整 H2 通过”：若后继记录保留 h2 阶段名，必须绑定新语义版本及实际检查集合，并由版本匹配 reader 验证；无法准确承载时先解决记录版本，不能复用旧 H2 pass 标签蒙混。修订不回写旧 PC、G3 receipt 或模型结果。

## 3. 具体改动表（全部为待授权候选）

“普通”表示受后续生成器开发任务覆盖即可实施；“可信”表示涉及受信准入、结果分类或 reducer 语义，必须有明确覆盖文件／表面的授权。本文不是这些动作的授权。

| 项 | 候选源码／合同及现有入口 | 原因、研究影响与风险 | 最小验收与相关测试 | 权限类别 |
| --- | --- | --- | --- | --- |
| I1 模型可见骨架投影 | `agent/src/sr2fpga_agent/prompts.py:1252` `_frozen_his_skeleton_messages`；`generation/context_his.py:124` `emit_skeleton_project_output`／`:187` `_build_skeleton` | 关闭 F1；可能误删填充所需接口或把 TB 藏进其他 artifact。投影由 controller allowlist 产生，不信任候选 role 标签作为唯一判据 | 捕获真实 messages，确认两组无任务族 TB/参考/私有材料；M4 仍得到完整声明结构。扩展 `agent/tests/test_sr2fpga_agent_context_his.py`、`test_sr2fpga_agent_prompts.py`；用 sentinel 验证不泄漏，不把字符串缺失测试当功能正确 | 普通生成输入改动；涉及信息边界，须定向验证 |
| I2 共同准入与 M4 构建分离 | `agent/src/sr2fpga_agent/his_validation.py:121`、`:232`、`:281`；`generation/context_his.py:207` validator facade、`:632` 静态骨架检查；`episode_executor.py:76` | 关闭 F2；改变哪些 PC 属共同失败，影响分母和方法效果。风险是无意删除检查、改变 H2 定义或抹除原历史语义 | 新 profile 的共同准入 monkeypatch emitter 后仍可执行；原本非法的共同语义负例仍失败；合法但 emitter 不支持的 PC 允许 M3 尝试、只使 M4 构建失败。旧默认语义回归保持。扩展 `test_sr2fpga_agent_his_validation.py`、`test_sr2fpga_agent_context_his.py`、`test_sr2fpga_agent_method_adapters.py` | **可信准入语义，需明确授权**；记录新 policy/hash 与受影响证据 |
| I3 两条件身份与预定顺序 | `agent/src/sr2fpga_agent/method_adapters.py:84` 的 PairingKey；`runner.py:1697` freeze sample 记录／`:4298` pairing；既有 `generation/context_his.py:266` 共享分支 | 同一 freeze 中每个配对恰好两个 sample，固定 AB/BA 顺序；从 PairingKey、公开投影、semantic instance/replicate 与共享规划引用交叉重建。旧六方法 planner 保持原状；不写 paired-block-v1 实例 | 重复／缺组／异模型／异 PC/context 拒绝；不会调用其余四组；旧 v1 六方法路径不受影响。扩展 `agent/tests/test_sr2fpga_agent_context_his.py`、`test_sr2fpga_agent_runner_method_dispatch.py`、`test_sr2fpga_measurement_freeze.py` | 普通窄编排；不能授予运行权 |
| I4 共享规划及其原始成本／失败绑定 | `agent/src/sr2fpga_agent/method_adapters.py:641` coordinator／`:652` generated event；`generation/context_his.py:76`／`:266`／`:649`；`cost_accounting.py:172` 的 artifact-hash 参数；`artifact_store.py:132` | 沿现事件机制绑定一次规划执行、原始响应与规范化 PC 双 hash、共同准入、raw cost refs；第二组消费相同成功或失败，不重规划。现 generated event 只有 PC hash，provider 失败还可能无 event，必须补证据接线。禁止静默改设计，仅允许预先声明的 controller 命名规范化 | 一个规划调用；两组消费相同原件；共同失败两组保留，M4 独有失败不阻 M3；原始/规范化差异越出命名白名单拒绝；无 Direct/S_P 假节点。扩展 `test_sr2fpga_agent_method_adapters.py`、`test_sr2fpga_agent_context_his.py`、`test_sr2fpga_agent_cost_accounting.py` | 普通来源接线；失败归类／分母部分属可信语义；封闭字段不足须先提最小后继 |
| I5 初始调用、重试和预算 | `agent/src/sr2fpga_agent/runner.py:3800`／`:3841`／`:3861`；`model_budget.py:18`／`:250`；`generation/context_his.py:76`／`:90`／`:124`；`method_contract.py:151` | 每个声明阶段一次，M3/M4 无修复。旧 `generation/his2project.py:33` 有循环，不能误走；provider 传输重试与逻辑调用需分开 | 成功对物理 3 调用、独立归因各 2；截断/非法格式不补调；PC 失败两组各保留真实共享已用成本。输入输出 token/超时/usage unknown 记录有效；无付费测试用 fake provider。扩展 `test_sr2fpga_agent_runner_budget_policy.py`、`test_sr2fpga_agent_context_his.py`、`test_sr2fpga_agent_cost_accounting.py` | 普通控制器改动；实际执行预算须另批 |
| I6 两条件派生成本分析 | 复用 `agent/src/sr2fpga_agent/cost_accounting.py:375`／`:492` 的逐 episode replay；不调用 `paired_cost_views.py:74` 的六方法 companion writer | 原始规划调用保留在实际发生的 ledger；以 I4 绑定的事件集合分出 S/U3/U4，去重得实际成本、完整依赖得独立归因、去除共享 S 得工程增量。输出派生表，不新造权威运行格式 | 13 轴；disjoint partition、完整原始引用、不可用传播、失败成本、顺序不变和 tamper 负例通过；原 cost-summary 保持实执行含义，不能冒充 standalone。在实际分析入口加入窄测试，原六方法 companion fixture 不改 | 新分析可由分析开发任务覆盖；若改既有受信成本 reducer 则需明确覆盖，不默认修改 |
| I7 无候选失败与完整分母 | `agent/src/sr2fpga_agent/pre_candidate_outcome.py:57`；`episode_outcome.py:158`；原 checkpoint-stop reducer `:18` 只作为限制核对；提案 `contracts/evaluation/development-pre-candidate-stop-outcome-v4.schema.json` | 无整块 manifest 时不套 checkpoint-stop-v1；在原 pre-candidate-stop 系列补共享规划失败以及 M3 输出／M4 构建/行为失败，绑定 I4 原件与各方法 terminal-null trajectory；不能因成功 reducer 需要 terminal 而删除 | 每个预定条件恰有可回放 outcome/stop；共享成本只执行一次；无伪 terminal/隐藏执行；设计与基础设施/完整性分开；retained=true、不得替换。补 `agent/tests/test_sr2fpga_agent_pre_candidate_stop_outcome.py` 和适用合同正负例；旧 v1–v3 仍 replay | **outcome／评分语义，需明确授权** |
| I8 封存、统一评价与最终结果接通 | 优先原样复用 `artifact_store.py:206`／`:278`、`public_evaluator.py:207`／`:431`、`terminal_selection.py:35`、`episode_outcome.py:158`；private 最终评价复用 `evaluator_dispatch.py:44`，不新写 oracle | 生成差异不能变成评分差异；不能把候选 TB 或模型自报当可信功能。新路线默认不修改 oracle、隐藏案例或成功阈值；若原 evaluator 确实不支持任务则先回 P04 明确范围 | 同一外部终点/配置/工具；candidate TB 忽略、私有内容不进 prompt；单次 initial 终端不按隐藏结果选择；缺 oracle/工具保留 not_run。复用 `test_sr2fpga_agent_public_evaluator.py`、`test_sr2fpga_agent_terminal_selection.py`、`test_sr2fpga_agent_episode_outcome.py`、`test_sr2fpga_agent_hidden_execution_state.py` | 只接线可属普通；**修改 evaluator/oracle/成功定义必须另有明确授权** |

首选仅对原 pre-candidate-stop 系列提出必要的后继，获准后才改 `contracts/manifest.json` 并补正负例；本轮未创建 schema。`episode-pack-v1`、`trajectory-v2`、单方法成本／候选／公开结果形态优先保持；块层格式全部不生产。I4 的引用接线需核查现 writer/reader 能否无歧义承载；若封闭字段／枚举或语义不足，则另列最小后继，不能先承诺“只改一个 schema 必足够”，也不能默扩 v1。四个版本的整块扩展是未选择的备选，详见 companion 的方案比较。

## 4. P03 必须解决的共同约束

1. **公开信息对称。** 两组共享的生成 PC 与公开事实字节身份可核对；同模型/解码不等于同输出，必须读实际 ArtifactRef。M4 独有的是结构及输出边界，不是任务族行为示例。
2. **没有检查逃逸。** H0/H1/H3 和共同数据语义仍执行；构建特有拒绝移到 M4，不以删除 oracle、吞异常、空行为或放宽阈值完成“公平性”。构建器缺陷也作为实际失败保留。
3. **没有免费追加机会。** M3/M4 一次规划共享＋一次各自工程；初始非法格式、截断、不完整与工具失败不会开启模型修复。最小版本可拒绝不确定状态的 resume，不盲目重采样。
4. **同一外部成功标准。** 内部 H/checker 诊断只是过程证据；独立功能／公开评价与所要求综合终点对两组相同。共同 PC 失败进两组分母，方法独有失败只进本组；基础设施缺失按预定规则另列。
5. **来源与历史隔离。** 程序结构、调试 TB、公开组件及模型行为如实记录；旧结果不重写。新 profile/合同/准入修订只能验证新版本；旧通过数量不作为本篇验收。

## 5. 验证顺序、输出与授权边界

P03 的输入是 P01 可追溯任务清单、P02 共同准入与职责协议，以及明确覆盖拟改表面的实施授权。建议先完成 I1/I2 的无模型输入／语义负例，再做 I3/I4 的两条件计划与共享失败，再做 I5–I7 的成本／失败 replay，最后用 I8 已有 evaluator 做 P05 集成。I1/I2 与 P04 的参考／oracle 材料资格可在不重叠文件下并行；P04 不以更改评分来适配生成器。

检查先用表中现有测试的受影响节点和新增窄负例；跨合同验证再覆盖既有 contracts/Agent 的相关 reader，不以全仓重跑代替必要行为检查。之后才在获授权的 P04/P05 范围运行真实参考候选的编译／仿真／综合。本文不运行这些命令，也不生成通过数量。

未来输出由实际 owning 源码／schema／测试文件与 `artifacts/structure-generation-paper/<dev-id>/implementation-verification.md`、`validation.xml`、适用注册记录及日志组成。新文件名仅表明窄位置，最终改动需与获准范围一致；没有任务需要就不创建新模块。任务运行失败原件在版本化 artifacts 保留，进度仅回写主清单。

目前需要明确授权的是 I2 的受信准入修订与 I7 的失败／分母分类及相应合同后继；I6 首选只新增派生分析、不改受信成本 reducer，若实施确需改它则补列实际范围；若 I8 需改 oracle/evaluator 则同样另列文件与影响。普通生成／编排工作在后续明确开发任务授权内进行，不逐条重复请求许可。本轮仅文档请求不足以启动任何实施。

模型、token/费用/时间上限及 provider 条件尚待决定，但不阻塞 P01/P02 的材料整理，也不应作为无付费代码准备的资源障碍。P06 pilot 与 P08 主对照各需有范围／资源上限的执行授权；P03 完成不自动开启任一运行。正文仍须用户另行明确确认，批准本实施范围或实验都不替代正文确认。

## 6. 当前机制的最小开发子步（代码尚未创建）

原 I1–I8 继续作为需要复用/修订的接线盘点。下列拆分说明工程上可以先做纯核心，再接入运行链；**不是当前研究优先级的立项建议**。本轮查新发现普通原子区域/部分转换的直接重叠，应先完成方法卡 §10 的规则与区分反例，再决定是否为论文投入这项实现。下列 owning 文件名是候选开发位置，不是已实现入口。

| 子步 | 输入／具体任务 | 拟输出与验收 | 前后依赖／表面 |
| --- | --- | --- | --- |
| D1 明确接口义务 | 公开 tuple/域/时延及原语类型；规定从声明到 E_c/E_r 的受限规则，缺失/冲突拒绝 | 方法卡内输入表与混合案例资格计划；可手工重建拥有者，不把模型任意 E_c 当真值 | P02 设计；进入运行资格的语义另经版本化评审 |
| D2 纯划分器 | 已校验内存义务/共同实现关系/能力规则；分组并分别计算局部与整体策略的读写集合、理由和退化情况 | 候选 `agent/src/sr2fpga_agent/generation/structure_partition.py`；相应窄测试覆盖确定性、完备/互斥、闭包、改名与非法输入；不调用模型/评估器 | 依赖 D1；普通生成开发，不改旧 H2/方法枚举 |
| D3 受限表达式校验及发射 | 信号 ID/宽度表、预分配读写集合、严格树；拒绝重复键/字段、错误宽度和越权；输出确定性 assign 文本 | 候选 `agent/src/sr2fpga_agent/generation/top_expressions.py`及测试；未知 ID、类型/大小、缺写/重复写、非法树均拒绝，完整输入才发射 | 与 D2 可分工开发；不假定叶 RTL 已安全，不引入通用 HDL parser |
| D4 最小无模型组合检查 | 手工公开正反例；D2 计划+D3 树输出，核对结构字节、边界和模型写集合 | 必要的窄 regression 与设计/实现差异说明；这些开发检查不计论文效果或 P04 oracle 资格 | 依赖 D2/D3；不运行私有评价/研究错误集，不写官方 evidence |
| D5 运行与可信边界接线 | sidecar/profile/严格响应格式、新失败语义、共同准入、叶边界及实际依赖检查 | 根据实际 writer/reader 提最小后继及 F1/F2 等具体文件变更，再完成原 I 项受影响验收 | 需实际表面明确；不能在 D2/D3 顺便放宽评分或赋予运行资格 |

普通核心开发与受信语义修改分开验收，不让 D5 阻塞 D2/D3 的纯函数可行性检查。反过来，D2/D3 通过也不代表可执行研究、全工程所有权或模型功能正确。当前未创建上述源码、测试、schema 或运行配置；新机制是否形成足够方法贡献仍受近邻比较和机制证据约束。
