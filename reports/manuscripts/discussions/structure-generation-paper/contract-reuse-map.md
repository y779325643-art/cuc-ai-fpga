# M3/M4 结构生成研究：合同复用与版本缺口

当前适用性：新增局部责任划分候选已[停止作为核心贡献](local-responsibility-bounded-design-review.md)。本文保留旧机制和新profile缺口的静态盘点，不代表仍计划注册这些profile或执行相应模型对照；无schema/实现变更。

日期：2026-10-21。状态：P02 的静态代码／合同盘点，尚未实施、注册新格式或执行实验。进度只在上级[论文清单](../2026-10-21-structure-generation-paper-checklist.zh.md)维护。本文是技术准备材料，不是论文正文，也不是运行授权。

适用性：本文盘点原 M3/M4 两条件路径。用户已选择先细化新增的[局部责任划分机制](local-responsibility-method-card.md)，新条件身份、表达式承载、边界来源和匹配对照尚需评审后映射；本文不证明新机制已可沿两条件入口执行。

本篇使用旧 `System-HIS v1.2` 的独立缩减研究范围，比较共享同一生成契约的 M3/M4 `@initial`。它不取得 `paper1-v2.2`、PC 2.1、G3/G4b 或官方 VPP 资格。下列来源均为仓库相对路径加当前行号；缩写的 Python 路径均以 `agent/src/sr2fpga_agent/` 为前缀。代码状态基于 `develop`、HEAD `e20dfd2c` 及当前未提交工作树，不把 HEAD 单独当作完整源码身份。

## 1. 采用的最窄路径

复用现有 Runner、ArtifactStore、模型预算、方法适配器和单 episode 评价链，优先走已有 `PairedArtifactCoordinator`／`PairingKey` 的 lazy 共享路径，不进入完整 paired-block/full-pack 层，也不另建实验运行框架。每个配对只共享一次生成的 System-HIS 及共同准入结果；M3 的完整工程调用、M4 的结构构建与行为调用分别属于各自方法。只运行 M3/M4，不为满足旧格式执行另外四种方法。

成功配对的物理调用为共享规划 1 次＋M3 工程 1 次＋M4 行为 1 次；独立归因各为 2 次。失败时使用真实发生的调用，不补足、不重采样；规划、输入输出 token、构建／EDA 时间分别保存。没有 provider usage 的轴保留 unavailable，不能估成零。

建议运行链：既有 measurement freeze 固定两个 sample 的身份／顺序 → 原 episode-pack-v1 的两个公开投影相同的 pack（省略可选 `paired_block_ref`）→ coordinator 的同一规划 ArtifactRef 与共享／消费事件 → 两条原 attempt/cost/trajectory 链 → 原候选封存、统一公开评价和终端 → 从验证过的原始源重建两条件分析。独立最终私有语义评价仅在协议明确需要并获对应执行授权时接入；不使用时不得声称 development/official VPP。

这一选择**不要求先创建四种 schema 后继**。最小仍需补足规划执行到原始成本／失败的引用绑定，并为两组无候选位置提供可重算收据；现有匹配收据不足时，仅在既有 pre-candidate-stop 系列中提出 v4。P03 未完成前不能拿同一个 context、seed 或 PC hash 代替完整执行证据。

## 2. 已注册格式与真实实现

注册权威为 `contracts/manifest.json`。表中“复用”表示结构与现有 producer/reducer 有明确入口，不表示本篇端到端已经验证。

| 记录 | 注册格式／实际代码来源 | 本篇处理与边界 |
| --- | --- | --- |
| 运行配置、工具、样本与冻结 | `agent/src/sr2fpga_agent/measurement_freeze.py:20` 的 `build_measurement_freeze`，`:59` 的 `write_or_validate_freeze`；Runner `:1697` 的 `_measurement_freeze_manifest` | 复用现有 freeze 记录机制及 hash/resume 检查。其 `schema_version` 是 `sr2fpga-phase-d-freeze-v1`，不是 manifest 注册的 campaign 授权合同。还须绑定本篇协议、实际源码及未提交差异、准入／模型可见投影策略；不能将该文件当签署运行许可。 |
| 冻结公开需求与 episode | `contracts/episode-pack/episode-pack-v1.schema.json:29`、`:51`；`agent/src/sr2fpga_agent/frozen_context.py:106`、`:227`、`:288` | 复用 `episode-pack-v1`。公开 context 与 audit-only 分离；两组 `public_projection_sha256` 相同。首选省略可选 `paired_block_ref`，不指向未生产的块。禁止把审计／私有引用送进 prompt。现 builder 只允许 development/excluded。 |
| 旧契约与公共检查 | `contracts/system-his/system-his-v1.2.schema.json`；`agent/src/sr2fpga_agent/his_validation.py:121`；`generation/context_his.py:207` | System-HIS 序列化可复用；共同准入的语义修订必须显式版本绑定。当前 H2 执行 emitter，不能原样用作本篇无偏共同准入，见 implementation-scope。PC 2.1 schema 不适用本篇旧契约。 |
| 候选工程与构建来源 | `contracts/project-package/project-package-v1.schema.json`、`contracts/project-envelope/project-envelope-v1.schema.json`；`agent/src/sr2fpga_agent/project_contract.py:169`、`:310`、`:437` | 复用工程清单、实际文件字节验证及 whole-file/composite 来源记录。M3 的模型生成工程与 M4 的程序结构／模型行为必须据实区分；manifest 有效不等于功能正确。 |
| 评价前封存与最终封存 | `public-evaluation-candidate-v1/v2`、`terminal-candidate-v1`；`agent/src/sr2fpga_agent/artifact_store.py:206`、`:278`、`:373` | 复用既有 seal。v2 是 envelope-invalid 尝试的保留形态，不是可计完整工程；失败不能伪造 terminal。 |
| 方法独占成本与轨迹 | `attempt-event-v1`、`cost-summary-v1`、`trajectory-v2`；`agent/src/sr2fpga_agent/cost_accounting.py:72`、`:375`、`:492` | 复用逐方法原始事件、13 轴成本及 reducer。`trajectory-v2` 支持 terminal=null 与 missing-lineage reason；不能虚构 complete。共享规划成本不塞给首先执行的方法。 |
| 共享生成与消费事件 | `agent/src/sr2fpga_agent/method_adapters.py:84` 的 PairingKey、`:641` 的 coordinator、`:652` 的 `shared_his_generated`；`generation/context_his.py:266`、`method_adapters.py:345` | 复用原 append-event 机制和规划 ArtifactRef。现 generated 事件只有身份／PC hash，尚未绑定规划成本 refs；provider 异常发生在 materialize 完成前时还无 generated 事件。必须补开始／完成或失败及其真实 raw-cost/raw-output 引用；不是只读现事件即可验收。块准备 ledger 不作为本篇主路径前置。 |
| 统一公开评价 | `development-authoritative-attempt-public-outcome-v1`、`development-terminal-public-outcome-v1`；`agent/src/sr2fpga_agent/public_evaluator.py:207`、`:431`、`:632` | 复用受信工具 launcher、sanitized outcome 与 trusted public-L2 harness。候选 TB 不计可信 L2；缺失 harness 保留 not_run。attempt authority 的 `repair_visible=true` 是旧合同能力，本篇必须控制器禁止任何后续修复调用，不能改该 const 假装新格式。 |
| 单次终端选择 | `development-terminal-selection-v1`；`agent/src/sr2fpga_agent/terminal_selection.py:35`、`:110` | 可按 wire 值 `@1` 表示本篇唯一 initial 候选，须记录 `@initial` 到旧 `@1` 的映射；不篡改现枚举。无完整候选时不得调用此成功路径或强行构造 selection。 |
| 私有最终语义结果 | `development-hidden-execution-state-v1`、`development-hidden-conformance-outcome-v1`；`agent/src/sr2fpga_agent/evaluator_dispatch.py:44`、`:225`、`:346` | 按 P04/P07 的实际授权与独立评价方案复用；仅对同一封存终端执行，保留 execution/semantic 两轴与单次提交。它是开发／excluded 机制，不是已完成的 OS 隔离或官方 hidden 生产者；本轮不运行。 |
| 有完整终端的 episode outcome | `development-public-evaluation-v1`、`development-episode-outcome-v1`；`agent/src/sr2fpga_agent/episode_outcome.py:43`、`:158`、`:516` | 复用单 episode reducer，官方 VPP 固定 not_evaluated。development VPP 也需要 sanitized hidden conformance；不能把仅公开 L2/L3 通过重命名为 VPP。无终端时该 reducer 明确拒绝，不能删失败来满足它。 |
| 共享规划失败 | `development-checkpoint-stop-outcome-v1`；`agent/src/sr2fpga_agent/checkpoint_stop_outcome.py:18`、`:40`、`:69` | 现 reducer 真实依赖 paired-block 和 checkpoint manifest；首选缩减路径不伪造这两份 artifact，所以不直接套用该收据。复用其 retained／禁止替换和设计／基础设施区分原则，在原 pre-candidate-stop 后继绑定一次共享规划失败，给两组各留收据；不新建并行结果格式。 |
| 工具与 oracle 实执行证据 | `development-tool-environment-v1`、`development-public-l2-harness-v1`、`development-oracle-run-evidence-v1`；`agent/src/sr2fpga_agent/tool_environment.py:25`、`public_l2_harness.py:154`、`oracle_runner.py:226` | 保留原始日志、工具／配置 hash 与登记格式；工具清单或 mutation score 不单独赋予候选通过。所选任务的 harness/参考需 P04 独立资格核查。 |

## 3. 方案比较：避开整块层，不能绕过它的限制

| 选择 | 所需工作与能证明的范围 | 本篇决定 |
| --- | --- | --- |
| 直接写两元素 paired-block-v1 或缺节点 manifest-v1 | 不符合现 schema／reader；即使手写 JSON 可读也没有合法配对与成本证据 | 拒绝，不能伪装 v1 |
| 把完整块层全部扩成两条件版本 | 至少涉及 paired block、shared manifest、paired cost companion 及无候选失败收据的后继；还牵动顺序、全块 lineage 和 resume | 可作为未来确有整块功能需求时的方案，不是本篇 P03 必然前置；本次不选，避免扩成六方法框架 |
| 沿原 coordinator 与单 episode 链重建配对 | 从固定样本身份／顺序、相同公开 context、同一规划 ArtifactRef、generated/consumed 事件、两个独立 trajectory/cost/outcome 重建；补齐共享调用／失败原件绑定 | **首选**。不生产 paired-block、shared-manifest、full-pack 或 paired-cost companion；不新建运行权威。必要失败收据在原系列版本化 |

不能直接套用整块层的定位证据如下：

- `contracts/episode-pack/paired-block-v1.schema.json:44` 固定六个唯一方法；`agent/src/sr2fpga_agent/paired_block.py:17`、`:20`、`:148` 固定六方法 Williams 顺序；`runner.py:4338` 只规划完整六成员块。
- `contracts/episode-pack/development-shared-checkpoint-manifest-v1.schema.json:20` 固定三节点，`:78` 开始固定三个消费者集合；`agent/src/sr2fpga_agent/block_preparation.py:106` 真实执行 Direct、HIS、S_P 三份准备。不能填假 not_run 节点凑格式。
- `contracts/evaluation/development-paired-block-cost-reconciliation-v1.schema.json:37`、`:51`、`:489` 固定六方法、三 contrast 与六事件分区，且要求 full-pack lineage；`agent/src/sr2fpga_agent/paired_cost_views.py:74` 不是只接受一个任意方法列表的通用 reducer。
- 两个 `full-pack-*-reconciliation-v2` 也固定六组：runner schema `:26`、`:41`，outcome schema `:24`、`:43`。本篇不执行旧 full-pack reducer，不将未执行方法伪写缺失，也不另造两组 full-pack 成功证书。

### 3.1 首选路径仍必须补的证据

1. **配对身份与一次规划。** `PairingKey`（`method_adapters.py:84`）含 requirement revision、semantic instance、replicate、模型 provenance 与 seed；原 coordinator（`:641`）按 digest 存规划。以现 freeze 的恰好两个 sample 与预定 AB/BA 顺序为分析入口，重建并交叉验证这些字段及相同公开 context；不能只按文件名或相同 seed 配对。
2. **共享成本的原件绑定。** 当前 `shared_his_generated`（`:652`）只有 PC hash，既无规划 cost refs，也未在 provider 异常时形成失败事件。P03 须在原 append-event／attempt-event 机制内把一次规划执行、原始模型响应、规范化规划、共同准入结果及 raw cost refs 绑定，并让第二组消费成功或失败的同一来源，禁止失败后再规划。
3. **不改写 raw cost 所属。** lazy 共享时，规划调用可能记在首先消费的 episode ledger；这份实际记录按真实位置保留，不能事后复制或改标签。分析先 replay 两条闭合成本链，再按绑定的规划事件集合 S 与两组独占集合 U3/U4 分区：实际成本为 S＋U3＋U4；独立归因为 S＋U3、S＋U4；规划后增量为 U3/U4。所有原始事件只物理计一次，零值和 unavailable 逐轴保留，不能从一条 cost-summary 总数猜 S。派生 CSV／图表不是新的受信运行记录。
4. **无候选失败收据。** `development-episode-outcome-v1` 要求 terminal，`development-pre-candidate-stop-outcome-v3` 的 method 固定 M4（schema `:67`）、失败限 H0–H3（`:106`）；现共享 checkpoint-stop 又依赖本篇未生产的整块 manifest。优先提出同系列 `development-pre-candidate-stop-outcome-v4`，只补 M3/M4 共享规划／共同准入失败与各自工程／构建／行为失败，绑定原始事件、成本、terminal=null、新准入语义版本与保留分母；保留旧 v1–v3 replay，不另建结果系列。
5. **原始响应与规范化 PC 分开。** `generation/context_his.py:649` 的 `_normalize_his_project_identity` 会修 controller 项目命名。共享记录需保留原始响应与规范化 PC 两个 hash，事前只允许约定命名字段变化；不把设计字段修改伪装命名整理或免费修复。provider/解析失败也保留其原始输出或明确无响应状态。

`ArtifactStore.append_event`（`artifact_store.py:132`）现有 payload 可存引用；`attempt-event-v1` 已有 input/output artifact hashes（schema `:49`、`:54`），`AttemptCostLedger.record_cost` 接受它们（`cost_accounting.py:172`）。这些提供窄接线的候选，不等于已有 producer 已经写全。该 cost_delta 至少一个轴（schema `:149`），不能用空成本字典伪造引用事件；应使用现 append-event 绑定已闭合的真实 cost refs。P03 需用实际 writer/reader 正负例确定绑定能否无歧义承载；若必须新增封闭字段、枚举或改变已有语义，先列最小合同后继与影响，不能直接扩写 v1。因此不承诺“只新增 v4 必然足够”，也不把四个新 schema 当默认工程量。

## 4. 必须闭合的失败与分母

| 位置 | 原始证据与合法输出 | 分母／成本 |
| --- | --- | --- |
| 共享 PC 生成或共同语义准入失败 | raw PC／原始响应或明确无响应、绑定的成本／共同准入失败事件；同系列新版 pre-candidate stop 给两组各留引用一致的收据 | 两个预定条件均保留；设计失败与 provider/基础设施未知分开；实际调用按发生量，共享已用成本各自完整归因 |
| PC 通过，M3 自由输出失败 | M3 raw output、方法事件、cost-summary、terminal-null trajectory、新版 pre-candidate stop | M3 保留；不阻止 M4；禁止免费格式修复 |
| PC 通过，M4 emitter／静态结构失败 | 构建日志／失败引用、方法事件、真实零模型调用或已发生调用、同系列 stop | 只影响 M4；不能回流为共同 PC 拒绝或同时删除 M3 |
| M4 行为输出／合并失败 | 原始行为输出、构建 hash、完整失败链与 stop | M4 保留；禁止空 body／成功占位或补调用 |
| 有完整 FPP、公开或最终语义失败／not_run | 候选 seal、真实工具／语义记录、单 episode outcome | 按预定终点保留，不以文件夹有结果便计成功；缺失原因不变成零成本或通过 |

## 5. P03/P05 合同验收清单

- 同一生成 PC hash、共同准入策略和原始结果绑定到两组；不能仅以相同 seed 声称 PC 相同。
- schema/reader 对错版本、错 pair、额外／缺方法、跨样本引用、重复事件、伪造成本、隐藏引用进入模型输入均拒绝；旧六方法回放不受新 profile 隐式改变。新的两组分析不声称生成了旧 paired-block 合法实例。
- 共享事件只执行一次，方法事件不交叠；成功例 3 次物理／每组 2 次独立归因，失败例按真实发生量；13 轴含未知值，不只验证调用总数。
- 原子事件与终端字节发生漂移时 fail closed；中断／未知 provider 执行状态不得盲目重试。最小实现可先拒绝任何未完成的恢复，不能为了支持 resume 重复调用。
- 无 terminal 的两类 stop 与有 terminal 的 episode outcome 均可从原始源重算；完整分母不依赖成功 outcome 文件数量。
- 除已登记支持的开发／excluded 形态外，不设置 official/pass-credit/G3/G4b 标志。新版本只是记录能力，不能代替 P04 评价资格、P06/P08 执行授权或正文确认。

## 6. 当前仍需决策／授权

普通生成器修复、可信准入语义修订、合同后继版本与 reducer 修改的具体授权边界见 [implementation-scope.md](implementation-scope.md)。P01 的最终任务与参考资格、模型与预算、P03 可信表面授权均未解决；它们不阻塞本轮文档交付及其余只读材料整理。本轮没有新运行包、schema 实例、调用计数或通过结果。

## 7. 局部责任划分的新增映射（尚未实施）

原表盘点仍可复用的原件链，但“只换一个 M4 hash”不能把两个新条件变成合法实例。当前 [method_contract.py](../../../../agent/src/sr2fpga_agent/method_contract.py)的 M4 绑定原固定策略，`method_policy_sha256` 按该策略重算；[episode-pack-v1](../../../../contracts/episode-pack/episode-pack-v1.schema.json)的方法枚举为 M0–M5。新 profile 身份与绑定必须被实际 writer/reader 校验，不发明 `M4-local` 作为旧合同 wire 值，也不将新 profile hash 填成原策略 hash。

| 新增内容 | 需要绑定的输入与输出 | 现有缺口／最小处理建议 |
| --- | --- | --- |
| 公开补充声明 | 需求字节及来源定位、冻结公开投影、接口/参数/域/tuple、原语义务及来源 | 旧 public_context 是封闭对象，不能任意加字段；fact_records 引用也不等于 loader 已理解新语义。后续明确 sidecar 格式/版本与真实加载检查 |
| 生成架构与规范化 | 同一次原始响应、原始/规范化 PC、声明及 capability/controller 修订 | 保留已有命名白名单和双 hash；新增设计语义不得静默规范化。手工例和模型生成来源分开 |
| 条件策略与划分计划 | 原固定策略身份、新 controller profile、分组/能力原因、预分配读写集合及样本身份 | 可研究 M4 家族的显式 profile，但当前无已验证扩展路线；需最小受信绑定与 reader，封闭字段不够时提后继版本，不能仅凭目录名区分 |
| 单次模型响应 | 严格 `behavior_files` 加 `top_assignments`，实际 messages、原始响应及树内容 | 旧 `parse_behavior_files` 会忽略额外字段/转字符串，不能当新响应 validator；controller 只从校验后 ID/树发射顶层赋值 |
| 模型与程序来源 | 固定结构、划分、表达式/叶体、发射结果和 composite envelope 的字节关系 | 原 envelope 可描述来源，但不能证明 semantic ownership；须另有实际顶层/叶边界及依赖检查，不创建伪成功证书 |
| 失败与成本 | 共享规划事件、各条件唯一工程事件、无终端保留、新 profile 原件链 | 沿既有事件/trajectory/cost 复用并闭合身份；成功 reducer 要求 terminal 不构成排除失败的理由 |

本轮只确定映射要求，未注册上述 sidecar/响应/profile，未验证现 Runner 能执行两种新条件。纯划分/表达式开发可以先用内存输入，不产出貌似已注册的研究运行包；实验接线仍依赖实际合同与准入版本评审。
