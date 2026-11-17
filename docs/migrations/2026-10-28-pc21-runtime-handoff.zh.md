# SR2FPGA 路线 A 会话交接

交接日期：2026 年 10 月 28 日。本轮已完成 LLM case 切换，以及 PC2.1 六方法生成/修复、预算、评测边界和统计分析的开发实现。当前没有正在运行或等待恢复的实验；下一会话应先核对工作树与本交接，再根据用户的新指令继续。

**没有运行正式实验，没有真实候选模型请求，没有实际正式 held-out 评测，也没有提交、推送或证据晋级。** 现有结果来自软件回归、显式手写响应夹具和真实本地 HDL 工具。不要将这些结果写成模型方法成功率。

## 1 用户目标与最新澄清

用户先要求深度代码审查和方法/字段报告，随后明确要求将案例换成 LLM 推理，并选择同步修改设计、代码和文档。接着要求规划 SCI 论文实验，最后授权补齐实验前的四块代码：PC2.1 M0–M5 生成与修复、预算控制、评测隔离、统计分析，暂不跑正式实验。这些开发工作已交付；本交接本身不增加运行授权。

用户最后问“要 Docker 干嘛”，已澄清：

- Docker 是本轮选择的**评测工具进程隔离后端**，不是 SCI、PC2.1、模型调用或 RTL 生成的必需依赖。
- 当前开发验证使用本机 Yosys/Icarus/vvp，已经完成，无需先安装 Docker。
- 模型输入/反馈权限由公共投影、候选文件准入和评测接口控制；Docker 主要限制工具对主机其他文件和资源的访问，不能单独替代全部信息边界。
- 虚拟机、独立评测机或系统权限沙箱都是可能替代路径，目前没有适配这些后端。
- 用户没有要求安装 Docker，也没有要求删除 Docker 后端或放开正式 gate。不要擅自执行这几项操作。

当前 `execution.integration.preflight(formal=True)` 还会明确报告 development entry 不支持正式执行、协议未冻结、任务未资格；OS 隔离未资格只是其中一项。**安装 Docker 不等于可以立即开始正式实验。** 这是当前保守的实现选择，不能表述为期刊的规定。

## 2 工作区与权威入口

| 项目 | 当前值 |
| --- | --- |
| 工作区 | `cuc-ai-fpga` 仓库根目录 |
| 分支 | `codex/paper1-ai` |
| HEAD | `e20dfd2ce46c5690767e30cb629fb5c58aff073a` |
| 路线 | A，LLM 推理子系统的契约驱动 FPGA 工程生成 |
| 研究版本 | `paper1-v2.3` 案例修订，方法/预算/统计规则继承 v2.2 基础计划 |
| 当前 PC | `sr2fpga-pc-2.1` |
| 研究状态 | 已采纳、未冻结，正式实验未授权 |

开始先读 [AGENTS.md](../../AGENTS.md)、[WORKTREE.md](../../WORKTREE.md)、[两路线索引](../routes/README.md)，核对 cwd/branch/revision 和 staged/unstaged/untracked。路线 B 位于同级 `cuc-ai-fpga-tb`，不属于本任务。

当前研究权威是 [v2.3 LLM case amendment](../specs/2026-10-28-sr2fpga-paper1-llm-case-amendment-v2.3.zh.md) 与 [v2.2 基础计划](../specs/2026-09-15-sr2fpga-paper1-research-plan-v2.2.zh.md)。[架构规范 v2.1](../specs/2026-09-15-sr2fpga-paper1-code-architecture-development-spec-v2.1.zh.md) 描述目标，不等同当前实现。当前能力从代码和对应证据核实；长状态页中保留的旧迁移段落只覆盖其原日期与范围。

### 工作树保护

工作区原来就有大量修改、删除和未跟踪文件，HEAD 不代表当前实现。交接开始时仍有108项普通删除、57项普通修改、331项未跟踪，以及5项重命名后修改和1项重命名记录；现场以 `git status` 为准。这些删除大部分是更早的材料整理，不是本轮主动清理。

原暂存区有6项文档向 superseded 的重命名，已保留。没有执行 git reset/clean/restore/stash，也未提交或推送。许多本轮源码仍未跟踪，不能用“清理未跟踪文件”收尾。本轮源码已在 runtime ArtifactStore 中保存实际字节归档；原暂存区备份在 `artifacts/paper1-ai/pc21-runtime-implementation-20261028/git-staged-start.patch`。

## 3 已完成的案例与实现

### LLM 三案例

| 家族 | 源码 | 当前固定开发配置与边界 |
| --- | --- | --- |
| `llm_quantized_qkv_projection` | [llm_qkv](../../agent/src/sr2fpga_agent/tasks/llm_qkv/README.md) | T2/Din5/Hq4/Hkv2/D3、lane2；三路输出独立背压、非零zero-point、signed RNE；不含RoPE |
| `llm_kv_cache_decode_attention` | [llm_attention](../../agent/src/sr2fpga_agent/tasks/llm_attention/README.md) | Hq4/Hkv2/D3/容量4、lane2；持久KV追加、GQA h//2、公开exp LUT、精确整数归一化、reset逻辑失效 |
| `llm_gated_ffn` | [llm_ffn](../../agent/src/sr2fpga_agent/tasks/llm_ffn/README.md) | T2/Din5/Dff7、lane2；gate/up、SiLU LUT、乘积、down、同输入残差；不含RMSNorm |

三者各有公开 task、独立 oracle、显式手写 RTL reference 与 evaluator-owned harness。三个量化/事务 profile 独立，不是已经直接串接的 decoder，也没有加载真实 checkpoint。旧 DW→PW、残差/GEMM身份、参考及所有历史证据保留原范围。

案例迁移使 catalog data revision 为0.4.0；当前主集合为上述三个 LLM 家族，partial/not_ready，旧三AI集合保存在 `legacy_quantized_ai_core_v2_2`。本轮 runtime 工作没有再改案例、catalog或历史结果。

### 当前运行与分析模块

| 文件/目录 | 实际职责 |
| --- | --- |
| [execution/runtime.py](../../agent/src/sr2fpga_agent/execution/runtime.py) | `PairedBlockRuntime`、共享初始DAG、M1/M5修复、缓存恢复、最后完整候选、`finalize_batch` |
| [execution/gateway.py](../../agent/src/sr2fpga_agent/execution/gateway.py) | text-only `ModelGateway`、`ReplayTransport`、`ClientTransport`、显式tokenizer/provider factory |
| [execution/proposals.py](../../agent/src/sr2fpga_agent/execution/proposals.py) | 严格格式、模型拥有文件准入、父hash绑定和完整文件替换交易 |
| [execution/budgets.py](../../agent/src/sr2fpga_agent/execution/budgets.py) | 持久多轴 `BudgetLedger`、共享全额归因、未知保留和晚到补证 |
| [execution/isolation.py](../../agent/src/sr2fpga_agent/execution/isolation.py) | 公开投影、RTL子集、本地未资格后端、Docker受限后端 |
| [execution/evaluation.py](../../agent/src/sr2fpga_agent/execution/evaluation.py) | `Pc21Evaluator`、冻结suite/source承诺、公共反馈、终态屏障、一次语义提交及高层readback |
| [execution/integration.py](../../agent/src/sr2fpga_agent/execution/integration.py) | 配置/公开输入加载、只读preflight、开发批次与可信分析导出 |
| [execution/development.py](../../agent/src/sr2fpga_agent/execution/development.py) | 明确合成的不同终态输入，生成关闭后才加载；不是正式hidden suite |
| [analysis](../../agent/src/sr2fpga_agent/analysis/README.md) | manifest全分母、设计簇配对归约、studentized bootstrap、Holm、区间、缺失/资格及合成检查 |

SD共享M0/M1，SC共享M3/M4/M5，SB共享M4/M5；M3没有结构构建器，不能用M4 emitter决定共同PC准入。正常初始为6次实际/10次独立归因调用；完整B4最多11/15，失败/早停按实际节点减少。

M1允许工程整体替换和模型文件交易。M5设计变更清空旧行为，另一次body调用继续收费；无效/no-op提议收费但不记有效修改。新分支未完成保留原最后完整候选。生成封存后模型门禁持续生效，不能用私有结果恢复修复。

预算采用 reserve→dispatch→reconcile/cancel，按所有共享消费者原子检查。`used`含未核实预留，`observed`才是已测消费；失败不退款，未知派发不自动重发。终态只读public补检和private工具使用独立额度，不能混成免费公共迭代。

终态按完整批次封存后才开放私有评分；slot key不以candidate hash新增评分机会。同一槽/同一冻结上下文幂等读原回执；实际完整性错误停止流程。分析导出重读封存、候选和评测绑定，不能相信调用方填的成功数值。

源码/契约/配置/输入/tape有冻结绑定，实际Agent Python及contract JSON字节连同未提交源码归档到ArtifactStore，Git HEAD只作辅助身份。旧Runner/HIS adapters仍是legacy，不要将其改名冒充当前入口。

其他必要修改包括：PC emitter增加可注入预算/隔离frontend runner；ArtifactStore堵住Windows盘符/ADS/device/trailing-dot标识；`contracts/manifest.json`注册9个当前runtime/analysis实际边界，保留全部74个原注册条目。

## 4 真实验证与证据

### 最新基础设施核验

权威清单：[completion-check.json](../../artifacts/paper1-ai/pc21-runtime-implementation-20261028/completion-check.json)。本交接创建前再次运行其轻量核验脚本成功：当前246个归档源文件hash吻合，原暂存和27个案例/catalog文件保持，原74条contract登记保持。

| 验证 | 实际结果 | 相对本轮artifact目录的文件 |
| --- | --- | --- |
| 综合软件/契约/兼容与相关旧核心回归 | 821 passed，1 skipped，6个真实工具用例另行排除 | `combined-final-01.xml` |
| 六方法共享/修复/恢复/格式公平/隐私/环境失败分类 | 14 passed；真实PC/Yosys，synthetic transport和受控public verdict | `methods-final-03.xml` |
| 真实attention评测worker全链 | 1 passed | `evaluator-real-host-01.xml` |
| 原PC真实parser保护 | 5 passed | `pc-parser-host-final.xml` |
| 预检/门禁/可信导出/源码字节归档 | 7 passed，前6项与综合套件重叠 | `adapter-final-03.xml` |

去重为 **842个不同用例有通过记录，另1个OS不允许创建symlink的探针跳过**。Ruff、whitespace检查通过；后续19项文档兼容复核属于已有集合，不另加分母。754是前一轮案例开发的核验数，不能与842相加成独立实验样本。

`artifacts/paper1-ai/pc21-runtime-implementation-20261028/cli-replay-final-03/` 是最终真实工具集成：显式手写 `synthetic_fixture` 响应经过六方法调度、实际PC构造、真实parser/编译/仿真/oracle/综合、6槽封存、不同合成终态输入和分析视图导出。初始6实际/10归因，自然模型派发0。`run.json`与control/private stores留存；6个功能结果为1仍不授予正式VPP信用。

本地后端没有OS隔离资格，worker CPU与peak memory未实测；对应预算和完整性资格明确是 `unverifiable`，没有补成compliant/intact。CLI集成数据不是正式hidden，也不是方法准确率对照。

### 其他上下文记录

- [LLM案例迁移记录](llm-case-migration-20261028.md)：前轮754开发回归、三个手写控制真实工具证据和attention串行优化；不代表模型生成性能。
- [论文实验与数据方案](../../artifacts/paper1-ai/llm-publication-planning-20261028/论文实验与数据方案.zh.md)：任务簇、资格、pilot、M0–M5、成本/机制、L4与真实LLM来源回放的规划。
- [LLM案例设计与实现报告](../../artifacts/paper1-ai/llm-case-migration-20261028/LLM推理案例设计与实现报告.zh.md)。
- [早期深度代码审查](../../artifacts/code-review/20261028-route-a/SR2FPGA方法与实现深度审查报告.zh.md)和[字段参考](../../artifacts/code-review/20261028-route-a/field-reference.md)。审查是当时快照；部分问题后已修复，部分仅影响legacy/旧DW case，重新判断前先读当前代码。旧复现脚本可能断言“旧错误仍存在”，不是现行回归入口。

## 5 尚未验证与下一步候选

当前没有新的任务选择或运行额度；以下是接续工作候选，不是默认执行授权：

1. **实际provider/tokenizer小范围联调**：适配代码已存在，但没有真实模型请求验证。开始前只向用户补问缺失的模型、任务/次数、token与工具/时间上限；没有scope就继续做本地mock/只读准备。不要读出或打印凭据，配置使用env引用。
2. **按实际部署选择隔离路径**：本机Docker不存在，实际容器资格未测。不要把安装Docker当论文前置，也不要仅为消除blocked而删gate/伪填资格。如用户选择VM、独立评测机或系统权限沙箱，再适配并实测相应边界和资源限制。
3. **benchmark建设**：三个固定合成profile仍不是独立簇总体。扩展要有来源、公开数学、资产、reference/oracle、资格和整簇split。尺寸/lane/权重seed/随机输入不能自动充当独立设计。
4. **统计支持域与校准**：当前拒绝跨多个簇共享dependency group；尚无协调组bootstrap。exact-task-hash guard不等于完整近重复审计。合成simulate的 `calibration_validated=false`，不能声称真实总体功效或错误率已校准。
5. **正式前冻结**：科学预算数值、δ/Δ*、缺失规则、簇/配置/重复、物理子集仍需针对LLM总体确认。144 pilot和2160正式结果在方案中只是容量候选，不是已批准运行，也不是“够发表/功效已足够”。

如果用户只说“继续”，先说明上述哪条将继续，并在已有授权内完成可逆代码/准备；真实模型、正式/实际held-out、重训练、L4/上板、push/PR/发布和证据晋级仍按AGENTS的明确scope执行。本会话未承诺默认进行这些动作。

## 6 最快的接续命令

从仓库根执行，先确认当前worktree源码导入路径：

```powershell
git branch --show-current
git rev-parse HEAD
git status --short
$env:PYTHONPATH = (Resolve-Path agent/src).Path
python -B -c "import sr2fpga_agent; print(sr2fpga_agent.__file__)"
python -B -m sr2fpga_agent.execution --help
python -B -m sr2fpga_agent.analysis --help
```

代码未改变时，可轻量复核本轮原始清单；它不是对未来修改的通用验收脚本：

```powershell
python -B artifacts/paper1-ai/pc21-runtime-implementation-20261028/verify-final.py
```

源码、schema、配置、输入或tape变化后，旧run被source guard拒绝继续是预期行为。不能修改旧snapshot/manifest或842断言来强行通过；需要新的run目录、版本记录和对应新验证。重跑使用新basetemp，不覆盖历史产物。先看拥有者README选择最窄测试；无需无原因重跑几分钟的完整method回归。

显式零模型fixture的可重做命令在 [fixture README](../../agent/tests/fixtures/pc21_runtime/README.md)，runtime/API细节在 [execution README](../../agent/src/sr2fpga_agent/execution/README.md) 和 [analysis README](../../agent/src/sr2fpga_agent/analysis/README.md)。单家族导出只作开发视图；联合分析要求完整三家族计划与足够独立簇，少簇输出退化/不可推断状态。

Windows注意：Yosys曾打不开270字符的实际存在路径，现composition/worker用短物理目录、保留完整逻辑ID。Icarus曾在sandbox返回 `0xC0000005`，相同测试经宿主审批的主机环境通过；保持环境区分，不能把崩溃判成模型缺陷，不能执行失败编译残留vvp或弱化断言。

## 7 给下个会话的启动提示

> 先读当前仓库的 AGENTS.md、WORKTREE.md 和 docs/migrations/2026-10-28-pc21-runtime-handoff.zh.md，确认仍在路线A的 codex/paper1-ai。保留全部既有staged/unstaged/untracked与历史run。PC2.1六方法开发实现和842项核验已完成，真实模型请求及正式实验均为0。Docker只是所选隔离后端，不是论文必需；不要自行安装或解除正式gate。先核对交接中的当前证据与未验证项，再根据我接下来指定的目标继续工作。
