# 09 方法机制与代码实现深度审查

_2026-10-29 · 路线 A 工作区 · 审查与文档任务，不修改研究定义或可信评测实现。_

## 📋 范围与判断标准

本次沿“公开输入→PC→共享六方法→预算/修复→独立验证→终态→统计”读取核心实现，并检查 legacy、Training 与 UI 的入口和边界。依据是当前源码、注册 schema、v2.3/v2.2 规范、相关测试和实际轻量运行。

本报告不是逐行穷尽所有历史文件的审计，也没有实际调用自然模型、运行 GPU 训练、Docker 资格测试、正式 held-out 或物理实现。具体实测与环境差异全部列在 [10 验证记录](10-validation.md)。

优先级在本报告中表示：P1 会直接损害核心边界/结果解释，P2 为需修复的局部可靠性问题，P3 为低风险诊断或说明问题。缺口与真实缺陷分别记录，不以问题数量评价审查深度。

## 🔎 R1｜P2：行为拼装异常绕过结构化公共反馈

**触发条件：** M5 初始或后续 body 无法通过真实 parser，运行器仍有预算进入下一次生成/修复。

**代码证据：**

- [emitter.py:385](../../agent/src/sr2fpga_agent/pc/emitter.py#L385) 将 `stderr[-3000:]` 直接加入 `PcBuildError`。
- [runtime.py:295](../../agent/src/sr2fpga_agent/execution/runtime.py#L295) 的 `_diagnostic` 只替换 control/private 根路径并截断字符，不做类别白名单投影。
- [runtime.py:388](../../agent/src/sr2fpga_agent/execution/runtime.py#L388) 捕获初始 body 错误，保留 `diagnostic`，再由 [body request](../../agent/src/sr2fpga_agent/execution/runtime.py#L377) 放入下一次 `public_feedback`。
- 已有候选的 body repair 在 [runtime.py:473](../../agent/src/sr2fpga_agent/execution/runtime.py#L473) 至后续反馈保留处存在同类静态路径。
- 正常 evaluator 路径使用 [public_feedback.py](../../agent/src/sr2fpga_agent/execution/public_feedback.py) 与注册 `pc21-public-feedback-v2`，因此两类错误路径的过滤强度不同。

**复现：** 用现有 synthetic transport 和受控公共 verdict 注入一个失败 frontend，其 stderr 含唯一合成标记。第一次 behavior 请求无反馈，第二、第三次请求的 `public_feedback.diagnostic` 都保留了原标记。外部模型与 HDL 工具调用均为 0。

复现材料：[简明结果](../../artifacts/documentation/code-guide-20261029-01/runtime-review-feedback-probe/probe-summary.json)、[原始结果](../../artifacts/documentation/code-guide-20261029-01/runtime-review-feedback-probe/probe-result.json)、[脚本](../../artifacts/documentation/code-guide-20261029-01/runtime-review-feedback-probe.py)。这些是本地诊断，文件随本地 artifacts 保留，不是正式证据发布。

**影响与边界：** 已证明候选自身 parser stderr 可以绕过结构化反馈策略；异常文本可能进入后续模型上下文，策略与实现覆盖不一致。没有使用私有测试内容，也没有证明 hidden 或 trusted testbench 已泄漏。

**建议：** 为 composition 定义有界、白名单公共诊断，并统一初始 body、补 body 和 body repair 的调用路径；原始日志仅留在评估方产物。验收应检查合成任意文本不能回传，同时合法候选文件/行号和可用诊断仍保留。不能通过放宽 parser 或静默吞错误解决。本轮未改实现。

## 🔎 R2｜P3：轻量训练干跑把空文件报告为可容纳

**触发条件：** 输入 chat JSONL 为空，或经过上游过滤后零行。

[training_dry_run.py:29](../../training/src/sr2fpga_training/training_dry_run.py#L29) 遍历零行后返回 `rows=0`、`valid_rows=0`、`fits_max_seq_length=true`。`--fail-on-truncation` 只处理超长，不因空输入失败。实测结果见 [peripheral-dry-run-probes.json](../../artifacts/documentation/code-guide-20261029-01/peripheral-dry-run-probes.json)。

**影响：** 只看 exit code 或 fits 布尔值的调用者可能把空数据当作可用训练集。这不证明已有训练事故，也不代表正式 canonical release 被接受；[release_reader.py](../../training/src/sr2fpga_training/release_reader.py) 明确拒绝空 canonical 数据。

**建议：** 干跑单独判断非空，或显式提供 data_ready 状态，并保留“正则 token 估计”标记。验收应区分空文件、全空白、合法一行和超长输入。本轮仅记录诊断保护缺口，未改训练代码。

## 🔎 R3｜P2：工具异常退出分类过窄

**实测触发：** QKV 主机回放的共享 `initial-SD/public` 中，Yosys parser 退出码为 3，stderr 为未捕获的 `std::bad_alloc`。当前结果却记录为 `execution_status=completed`、`semantic_status=fail`、`diagnostic_codes=[parser_rejected]`，M0/M1 最终归为 `design_outcome=0`。

[evaluation.py:430](../../agent/src/sr2fpga_agent/execution/evaluation.py#L430) 的 `_require_tool` 只识别三个固定崩溃退出码；本次异常落入普通 `CandidateBoundaryError`。同一候选 hash 在 M3 的公共解析和完整公共流程随后通过，进一步说明该条 stderr 不能简单解释为固定语法错误。

证据：[分类复现摘要](../../artifacts/documentation/code-guide-20261029-01/runtime-review-bad-alloc-classification.json) 绑定了原始记录路径和候选 SHA。对该真实 `ToolResult` 再调用分类函数，以零模型、零工具方式复现了相同归类。

**影响与限制：** 工具未捕获异常与普通设计拒绝混在一起，可能影响失败分类与统计解释。缺少内存实测与硬限额证据，不能断言这是主机 OOM，也不能直接认定必须永久记为基础设施缺失；仍需区分主机/工具故障与候选资源耗尽。普通综合超时按当前规则单独记录，不与此异常混为一谈。

**建议：** 在工具适配层记录明确异常类型和资源证据，按冻结政策进行归约，避免只依赖三个数字。验收需覆盖正常编译错误、已知信号/异常、候选资源超限、主机不可用与未知退出。更改 reducer 会影响结果语义，应保留旧记录并对新版本单独验证。本轮未修改评分或重分类历史产物。

## 🧾 文档与元数据漂移

| 位置 | 当前问题 | 影响/处置 |
| --- | --- | --- |
| 根 README 的 Minimal Setup | 曾把整个 PC 入口笼统描述为不生成 RTL | 本次限定 `assemble/check`，说明 `build/compose` 能生成结构/工程 |
| Agent README 当前 runtime 段落 | 同段说明重复 | 本次去重并加入中文手册入口 |
| [task catalog notes](../../contracts/task-catalog/sr2fpga-task-catalog-v0.2.json#L10) | 总体说明仍提旧 v2.2，机器可读 current_research 已是 v2.3 | 低优先级人工导航问题；未改 catalog 数据 |
| current-status、PC/execution README 部分段落 | 存在重复内容；status 还保留多个明确标注的历史快照 | 读者应先看当前章节及实际代码；历史事实不能直接累加为当前能力 |

这些说明问题不构成算法错误，也不能仅通过改文档让资格门槛成立。

## 🧱 方法与实现的一致性矩阵

| 方法要求 | 当前机制 | 已核实范围 | 仍需注意 |
| --- | --- | --- | --- |
| 同一公开事实与外部 ABI | `PublicTask`、源字节与资产 hash、独立 ABI 推导 | 实际 loader/checker/evaluator 与相应测试 | 来源独立性与人工 adjudication 不能由hash证明 |
| PC 声明检查而非自动证明算法 | checker 输出未评估行为义务 | 参数/域/类型/tensor 与执行义务分离 | 仅检查当前绑定配置 |
| 确定性结构不含案例算法 | 通用 emitter + 外部 behavior unit | emitter 无按家族生成算法的分派 | reference 不能偷偷充当候选答案 |
| M0–M5 共享初始生成 | SD/UP/SC/SB DAG，失败也共享 | runtime 分支与持久 checkpoint | 自然模型执行有效性本次未测 |
| B4 公平预算 | reserve/dispatch/reconcile、多轴、actual/standalone | 代码、fixture 与针对性测试 | 本地 CPU/memory 不可验证；科学预算未冻结 |
| 公共反馈不含私有结果 | v2投影、终态后才加载suite | evaluator投影与终态机制 | R1 表明 composition 路径覆盖不全 |
| 唯一终止候选 | seal、批次屏障、one-shot slot | 代码与开发回放 | 本地目录分离不等于强访问隔离 |
| 簇为独立统计单位 | 层级权重、联合bootstrap、Holm、missingness界限 | 手算与合成统计回归 | 跨簇依赖组拒绝；近复制仍需审计 |

这些归纳是当前实现解释，不将目标架构目录名冒充已存在文件。功能偏离目标时应记为 `implementation_protocol_drift`，结合 [migration](../migrations/research-plan-alignment.md) 与 [runtime implementation record](../migrations/pc21-runtime-implementation-20261028.md) 处理。

## 🚧 已知限制与后续工作

| 限制 | 为什么重要 | 合适的下一步 |
| --- | --- | --- |
| 三家族各只有固定开发控制，catalog partial/not_ready | 不足以支持总体成功率或主假设 | 完成独立设计簇、任务/split与mutation资格 |
| 本地后端不具 OS/资源隔离资格 | 不能保证候选访问和硬资源限额 | 对实际 Docker engine/镜像执行合成资格检查 |
| 日志上限在子进程结束后检查 | `max_output_bytes` 不是实时磁盘配额 | 需要硬磁盘界限时设计限额/监控并实测，不能从配置推断 |
| L3 为 generic synthesis | 无 FPGA mapping、布局布线或L4证据 | 明确工具目标并按授权执行物理资格 |
| provider/精确tokenizer无本次真实请求 | 接口存在不证明真实服务兼容 | 用明确模型、预算、停止条件开展受控接入验证 |
| release inspector未接入手动train_lora | 不是完整自动训练授权链 | 作为独立训练工程改造；不扩大 Paper-1 任务 |
| 新旧入口共存 | 用户可能用旧runner/UI解释新方法 | 使用本手册入口表与显式旧协议拒绝守卫 |

优先处理会影响信息边界和结果解释的代码问题，再进行真实后端资格与任务资格工作。正式运行需要这些前置条件和明确运行授权；本次文档完成不代替任何一道研究门槛。
