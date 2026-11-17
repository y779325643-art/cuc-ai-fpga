# 路线 B：AI 生成 RTL 测试台的可靠性研究

> 本页保留路线 B 当时的研究记录。原 `cuc-ai-fpga-tb` 工作树和 `codex/tb-reliability` 本地分支已移除。当前开发入口见 [WORKTREE.md](../../WORKTREE.md)。

## 研究范围与入口

当前方向关注 AI 生成测试台在实际合法轨迹中，对已经暴露的 RTL 语义违例是否漏报。未暴露、非法刺激、编译失败、工具不可用与暴露后漏报必须分别保留；FAIL 与见证共存也不自动说明失败原因已经归属。

下表中的历史运行产物及讨论原稿保留在本地资料中。链接记录原相对路径，供持有对应资料的工作区查找。

| 材料 | 当前用途 |
| --- | --- |
| [稿件与讨论索引](../../reports/manuscripts/README.md) | 既有研究路线与报告入口；日期较旧的状态需结合原始运行记录理解 |
| [N54 报告](../../reports/manuscripts/discussions/2026-10-26-tb-trace-audit-qualification-and-compatibility-fix.zh.md) | 原版编译失败及最小修订的形成过程，保留当时“未重跑”描述 |
| [N55 报告](../../reports/manuscripts/discussions/2026-10-26-tb-trace-audit-second-run-and-compiler-diagnosis.zh.md) | 修订版失败结果与后续六项仅编译诊断的准备范围 |
| [修订准备包](../../artifacts/tb-trace-audit-prep-20261026-01/README.md) | 已冻结的观察器、重放、资格计划与输入绑定 |
| [早期三任务资格包](../../artifacts/three-task-qualification-prep-20261022-01/README.md) | 修订包仍引用的原始硬件与支持代码；必须保持相对位置和字节 |
| [run-01 结果](../../artifacts/tb-trace-audit-qualification-run-20261026-01/results.json) | 原版两个 nominal 编译失败、其余八项未运行的实际结果 |
| [run-02 结果](../../artifacts/tb-trace-audit-qualification-run-20261026-02/results.json)、[账本](../../artifacts/tb-trace-audit-qualification-run-20261026-02/run-ledger.json)、[运行后绑定](../../artifacts/tb-trace-audit-qualification-run-20261026-02/postexecution.json) | 晚于 N54 报告的修订版实际运行记录 |

## 整理时发现的最新实际记录

2026-10-26 的工作区整理发现 run-02 已执行。十个位置中，两项为 `unusable_compile_failed`，另八项为 `unrun_prior_task_qualification_failure`；当前资格仍未通过。该次记录包含两次 HDL 编译、两次版本查询，没有仿真或被测模型调用。连同 run-01，已有账本累计为四次 HDL 编译与四次版本查询。

run-02 的两次编译退出码均为 3221225477，保存的标准输出和错误输出为空；不能直接沿用 run-01 的 `final` 调用 task 诊断解释本次失败。输入清单、结果、账本及四份工具记录的保存哈希在整理时已只读核对。

整理期间另有会话更新了 N55 报告和进度索引；这些并发更新已保留并纳入新 worktree。N54 和旧包 README 保留撰写时点的状态，不为更新导航而改写历史内容。本次目录整理没有启动新运行，也没有把复制包当作新增样本。

## 下一步与执行边界

N55 已准备[六项仅编译诊断](../../artifacts/tb-trace-audit-compile-diagnosis-prep-20261026-01/README.md)，尚未执行。后续从 N55 和该准备包核对诊断范围及适用授权，再依据真实诊断明确编译失败的原因与所需修订。保留 run-01、run-02 和两个准备版本；不能覆盖已存在的 run-02，或直接重写冻结输入。

研究协议、预期分类、模型可见信息和资格规则继续按现有记录执行。本次“整理 worktree”的授权不增加 HDL、模型或自动重试额度。需要真实工具重现、再次资格运行或候选模型实验时，应先核对已有授权及预算；缺少适用范围时再补充明确执行指令。

三条件 18 模型方案未因目录拆分而启动，SCI/SCIE 贡献和投稿资格也没有由工具可用或历史开发检查自动成立。稿件仍保留既有版本，参见 [稿件目录](../../reports/manuscripts/drafts/)。

## 文件与产物

源码仍遵守 `agent/`、`contracts/` 的既有职责。已复制的历史包保留同名相对路径，不通过 junction、硬链接或共享可写目录与 A 相连。新的一般运行可写入本 worktree 的 `artifacts/tb-reliability/<run-id>/`；协议另有既定路径时使用新的唯一目录并保留来源绑定。

此 worktree 仍含共同基线的 Paper-1 源码和历史材料，文件存在不代表它属于本路线的任务总体、证据或执行计划。通用代码修复的同步方式见 [两路线索引](README.md)。
