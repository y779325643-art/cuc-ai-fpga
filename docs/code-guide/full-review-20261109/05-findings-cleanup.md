# 审查发现、冗余判断与整理顺序

本章汇总可定位的问题与维护建议。**本次没有修改实现或改变评分，也没有删除旧代码。** P2 表示应安排修复的可靠性问题；P3 表示较低优先级的健壮性/说明问题。优先级不是研究结果等级。

## 1. 问题总表

| 编号 | 级别 | 问题 | 本次证据 | 影响范围 |
| --- | --- | --- | --- | --- |
| F01 | P2 | Docker 开发运行中断后，同目录恢复撞上旧资格探测目录 | 当前源码 + 合成后端目录探针复现 | 当前 PC2.1 Docker 路径恢复 |
| F02 | P2 | 自由需求交接包遗漏用户补充工程约束 | Python 审查函数 + Node 内存执行前端函数复现 | app 自由需求模式 |
| F03 | P2 | 裸 pytest 收集可能加载模型 | AST 与 pytest 配置静态确认；未导入模型脚本 | 仓库根默认测试入口 |
| F04 | P2 | 行为拼装异常保留原始 parser 文本并回传修复 | 本次静态复核；此前已有合成复现 | 当前 PC2.1 M5 反馈路径 |
| F05 | P2 | 工具异常退出分类只覆盖少数退出码 | 本次静态复核；此前有真实异常分类记录 | 当前评估状态与结果解释 |
| F06 | P2 | 旧 messages 转换将 null 变成文本 `"None"` | 当前函数内存复现 | Training 旧消息兼容输入 |
| F07 | P3 | dry-run 的非对象行报错和空集结果不完整 | 当前函数内存复现；空集现象在旧手册也有记录 | Training 轻量预检 |

363 项选定回归通过不意味着上表的问题不存在：已有测试覆盖的是各自声明的场景，没有覆盖所有恢复路径、前端导出组合和异常输入。不能把“测试全绿”解释为全仓库无缺陷。

## 2. F01：中断恢复被自身目录阻断

**触发条件：** Docker 后端已完成资格探测，运行在最终 report 提交之前中断，用户用同样的输出目录恢复。

[`integration.py:179`](../../../agent/src/sr2fpga_agent/execution/integration.py#L179) 重新创建 backend，并使用固定的 `private/qualification-{index}` 路径调用 `qualify()`；[`isolation.py:253`](../../../agent/src/sr2fpga_agent/execution/isolation.py#L253) 使用 `mkdir(..., exist_ok=False)`。第二次执行在真正探测前即抛 `FileExistsError`。已有最终 report 时会提前返回，因此不属于这个触发范围。

本次以合成 `available` / process runner 替换实际 Docker 调用，第一次资格检查成功，第二个 backend 在同目录触发异常。实际 Docker 调用和模型调用均为 0。结果见首次探针输出（本地 `artifacts/documentation/full-review-20261109/docker-resume-64e703c0/probe-result.json`），另保存了独立复核脚本（本地 `artifacts/documentation/full-review-20261109-01/docker_resume_probe.py`）和复核结果（本地 `artifacts/documentation/full-review-20261109-01/docker-probe-8974cfc4/result.json`）。这验证了恢复路径的目录冲突，不是实际 Docker 隔离资格测试。

修复时应为每次资格探测创建独立目录，或安全验证并复用绑定正确的资格记录。不要只把 `exist_ok` 改成 true 后无条件信任旧 `probe.txt`。验收应覆盖首次运行、资格后中断、配置/镜像变化、探测失败和已有最终 report 的重开。

## 3. F02：自由需求交接丢失字段

**触发条件：** 用户只在工程上下文表单中填写接口、I/O、验证意图或交付物，审查返回 `ready`，前端生成交接文件。

[`app/app.js:234`](../../../app/app.js#L234) 的 `freeModeFiles()` 没有保存 `payload.engineering_context`；输出只有需求文字、部分项目信息与 boundary。后端 [`audit_requirement()`](../../../app/server.py#L509) 的审查响应也不等于完整请求快照。

本次使用四个不同的合成标记，真实审查函数返回 `ready` 后，Node `vm` 执行前端 helper，确认三个交接文件均未包含四类标记。因而下游仅收到交接文件时，可能不知道用户额外指定的接口或交付要求。探针没有启动浏览器或 HTTP 服务，所以不宣称完成了 UI 端到端测试。

建议交接包保存完整、经过验证的请求快照，并让生成提示引用这些字段。验收应逐字段检查可追溯性；不能仅检查文件数或是否出现 `HANDOFF`。复现脚本与结果见外围探针（本地 `artifacts/documentation/full-review-20261109-01/periphery-probes.py`）及输出（本地 `artifacts/documentation/full-review-20261109-01/periphery-probes.json`）。

## 4. F03：默认测试发现可能执行手动模型 smoke

[`training/scripts/test_gemma_transformers.py:11`](../../../training/scripts/test_gemma_transformers.py#L11) 与第 16 行在模块顶层调用 tokenizer/model 的 `from_pretrained()`，没有 `main` 守卫。根 [`pytest.ini`](../../../pytest.ini) 没有通过 `testpaths` 限定测试目录，该脚本又符合默认测试文件名。

未指定目录的 pytest 可能在收集时先导入它：缺依赖会收集失败，依赖可用时可能触发模型加载、下载或 GPU 初始化。是否实际联网取决于环境与缓存，本次没有执行这个危险收集路径。

建议将模型 smoke 重动作放入显式 `main()`，或使用非测试文件名，同时明确正常回归目录。当前应使用 owning README 中的指定路径命令；本次验证也使用明确文件列表。此发现的依据是源码与配置，不是一次模型加载实测。

## 5. F04：异常反馈绕过正常白名单投影

[`pc/emitter.py:386`](../../../agent/src/sr2fpga_agent/pc/emitter.py#L386) 把 parser stderr 尾部加入 `PcBuildError`；[`runtime.py:296`](../../../agent/src/sr2fpga_agent/execution/runtime.py#L296) 的 `_diagnostic()` 主要做路径替换和截断。初始 body 失败与修补失败中的 diagnostic 会进入后续反馈状态，而正常评估反馈使用 `public_feedback.py` 的受限投影。

旧手册 R1 已用合成任意标记复现该路径；本次确认相关实现仍存在，未再次调用模型/HDL。它证明反馈策略覆盖不一致，**没有证明真实 hidden 内容已泄漏**。详见[原审查 R1](../09-deep-review.md)及[本次调用追踪](02-agent-runtime.md)。

修复宜统一 composition 错误的类别、合法候选文件/行号和固定提示，原始日志留在评估侧。验收需覆盖初始 body、补 body 和已有候选修补，不能只测试 `EvaluationResult.public_feedback()`。

## 6. F05：工具异常与候选失败可能混在一起

[`evaluation.py:430`](../../../agent/src/sr2fpga_agent/execution/evaluation.py#L430) 的 `_require_tool()` 先将 `missing_tool` 归为基础设施错误，再将 `3221225477`、`-1073741819`、`-11` 识别为 crash；其余非成功结果进入候选边界失败。旧手册记录的 Yosys `std::bad_alloc` / exit 3 因而被归为 parser rejection。

本次确认分支未变，没有重新执行该 HDL 场景。未知工具异常应该结合进程、资源及环境证据判断；不能凭 `bad_alloc` 字样断言宿主 OOM，也不能把全部 timeout 改成基础设施失败。

建议在工具适配层保存可验证的异常/资源信息，再依据明确版本的规则归约。这个修复可能改变 0 与缺失值的解释，属于评估语义维护；需要单独确认受影响规则、版本化与回归范围，并保留旧记录不变。详见[原审查 R3](../09-deep-review.md)。

## 7. F06–F07：训练预检的数据类型与空集边界

[`prepare_dataset.py:292`](../../../training/src/sr2fpga_training/prepare_dataset.py#L292) 和 [`training_dry_run.py:78`](../../../training/src/sr2fpga_training/training_dry_run.py#L78) 先做 `str(content).strip()`；JSON null 对应的 `None` 因此变成非空文本。应先校验字符串类型再规范空白，避免把格式错误伪装成内容。这针对旧 messages 路径，不能推断严格 v2 schema 也接受 null。

[`dry_run_chat_jsonl():29`](../../../training/src/sr2fpga_training/training_dry_run.py#L29) 对 `[]` 行直接调用 `.get()` 而抛 `AttributeError`；空输入则返回零行且 `fits_max_seq_length=true`。后者只能表示“没有超长行”，不能表示训练数据已就绪。应明确非空检查和带行号的对象类型错误；长度判断与数据可训练性宜分别表达。

上述行为均通过 StringIO 合成输入调用当前函数复现，结果在外围探针输出（本地 `artifacts/documentation/full-review-20261109-01/periphery-probes.json`）。未加载 tokenizer、训练框架或真实数据集。

## 8. 冗余不能只按“长得像”判断

### 8.1 确认的相同代码

对 Agent/Training 生产源码及 app 后端的函数 AST 做精确比较，保留至少 10 行、跨文件出现的同构函数，得到 3 组。比较去除了源码行位置信息，但保留函数名、参数、语句和常量；它不是相似度检测，不能据此宣称“全仓库只有三处重复”。

| 精确相同的函数 | 源码位置 | 判断 |
| --- | --- | --- |
| `_run_stage`，22 行 | [`generation/skeleton_fill.py:50`](../../../agent/src/sr2fpga_agent/generation/skeleton_fill.py#L50) 与 [`two_stage.py:73`](../../../agent/src/sr2fpga_agent/generation/two_stage.py#L73) | 同一项目中的计时、开始/完成/失败事件包装，可考虑提取小型公共 helper |
| `_emit_stage_event`，13 行 | [`skeleton_fill.py:73`](../../../agent/src/sr2fpga_agent/generation/skeleton_fill.py#L73) 与 [`two_stage.py:96`](../../../agent/src/sr2fpga_agent/generation/two_stage.py#L96) | 相同事件字典构造；与上一项一起整理更清楚 |
| `_row_ref`，14 行 | [`training_pool.py:262`](../../../agent/src/sr2fpga_agent/training_pool.py#L262) 与 [`release_bundle.py:427`](../../../training/src/sr2fpga_training/release_bundle.py#L427) | 位于两个独立项目，是同一文件契约的生产/消费解释；不应直接跨项目 import 去重 |

第一类提取时应保留异常传播、事件名、字段与计时含义；第二类跨项目重复适合通过契约样例/兼容测试保持一致，不能为了减少十几行破坏项目边界。

### 8.2 近似重复与重叠职责

| 现象 | 为什么存在 | 合理处置 |
| --- | --- | --- |
| 两份 `_validate_messages` | 转换器和干跑分别校验旧消息 | 可在 Training 内部共用，并一起修复 null 问题 |
| 多个 schema loader | 有通用注册器，也有旧格式专用接口 | 先比较返回类型、版本检查、缓存与 `$ref` 规则，再统一底层；不要把所有 policy 当 schema |
| `contract_skeleton.py` 与 `pc/emitter.py` | 两代结构表示、文件布局和编辑边界不同 | 是迁移中的重叠职责，不能直接互换或合并 |
| `model_budget.py` / `budget_allocation.py` 与 `execution/budgets.py` | 旧调用分配、provider 限制与新多轴账本职责不同 | 文档写清用途；迁移应连同 writer/reader 和结果格式做 |
| Agent 与 Training 各自的 hash/reader | 独立项目按文件交换 | 用共同契约和测试保持一致，不引入跨项目运行依赖 |
| oracle 与 reference 的计算逻辑相似 | 数学检查必须独立于 RTL 构造 | 保留独立性；不能抽成同一答案函数后用它自证正确 |
| 多份自动生成 slide 文件 | 展示构建器生成薄封装或自包含页面 | 改生成器而非逐页修；保留可重建历史成品的源版本 |
| datasets/reports 中大量相似 RTL | 多版本数据、不同候选和 attempt 的留存 | 身份、哈希、引用不同；内容相似不足以授权删除 |

### 8.3 可以先做的文档整理

`pc/README.md` 的两段 runtime 介绍、`research-plan-alignment.md` 的两段相同说明存在重复；`pc/semantics.py` 的参数值规则注释没有准确区分“本基础检查函数不负责”与“完整 checker 已实现”。这些不会因本次说明文档新增而自动修复，具体位置见[契约章节](03-contracts-hardware.md)。

`configs/current/` 实际是维护中的 legacy 示例；`g3_*` 是旧契约身份；PC2.0 是历史草案；历史 PPT 中的 M6/CIRCT 等是当时设计材料。它们应该保留明确的导航和年代，不能只改名成“当前”来解决理解困难。

## 9. 建议的后续整理顺序

1. **先修用户可见错误和执行入口边界：** F02、F03、F06/F07；增加对应最小回归，不引入模型/训练依赖。
2. **再修恢复和反馈完整性：** F01、F04；覆盖中断后恢复、原始日志过滤、正常诊断可用性。
3. **单独设计评估分类改动：** F05 涉及研究结果解释，应明确新旧规则和受影响证据，不回写历史结论。
4. **提取小范围公共 helper：** generation 的两组复制和 Training 内部消息校验；不跨项目共享运行代码。
5. **最后规划旧流程退役：** 逐个确认入口、消费者、历史读取、数据导出和回放需求，形成版本迁移；在迁移验收前不删旧 schema、reducer 或样本证据。

这是可分批实施的建议，不是本轮已执行的修改。仍需正式开展的自然模型实验、真实 Docker 资格、族资格、器件综合/物理实现与上板验证，不会因文档整理或上述轻量测试通过而完成。
