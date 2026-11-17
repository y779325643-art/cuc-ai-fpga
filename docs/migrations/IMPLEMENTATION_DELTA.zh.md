# PC 2.0 → PC 2.1：实施同步清单

日期：2026-09-15。此文件是目标变更清单，不表示已经修改用户仓库、研究计划或实现 SPEC。PC 2.1 不提供旧格式 reader 或自动转换；历史证据保留原身份。

> **范围更正（2026-09-15 采纳后）：** 下文 §3 写的“不自动改……四家族总体”描述的是本清单交付时的范围，**已被 `paper1-v2.2` 取代**：主总体已改为 `ai_dw_pw_block`、`ai_quantized_residual_block`、`ai_tiled_gemm_pipeline` 三个家族，旧四家族退出主统计。M0–M5、B4、主要比较与 hidden 规则不变的部分继续有效。本段只更正活动约束，不改写本文件其余历史表述。

## 1. 格式与接口

| 对象 | 改动 | 禁止做法 |
|---|---|---|
| 注册完整 PC／模型输出 schema | 注册本包两份 2.1 schema、哈希和版本；design 定义保持同源 | 两份分别手改漂移；仍以 2.0 标记新语义 |
| Requirement Boundary | 需要张量的任务在既有公开边界中显式给出 tensor_contracts；不改变事实来源 | 只给 PC 分支额外语义、从 family ID 暗取参考架构 |
| Capability Profile | 显式启用 dense_quantized_v1 及六个资源化边界 | 看见 schema 能表达就声称 emitter 和 evaluator 已支持 |
| PC parser/checker | 调用本包静态规则或经重新测试的等价实现；错误位置/范围清楚 | 把 unknown/unsupported 改为默认通过 |
| FPP / actual evidence | 保持为 PC 之外的对象 | 把 `verification_obligations` 当实际通过结果 |

## 2. 对代码架构 SPEC 的对应修改位置

- §6：将活动 PC 版本改为 2.1；H0 检查新字段，H1 处理解析后的张量类型与连接，H2 核验有限 profile，H3 仍只检查绑定与可验证关联，不能自称完整需求蕴含证明。
- §7：BuildPlan / AbiMap 包含 lane、mask、遍历和元素类型身份；接口只物化声明结构，不自动做 Repack/Requantize/Fork/ReduceSum 的行为。
- §8：BatchedBehaviorFill 输入加入已解析 tensor contract 与关系；依然一次声明阶段最多一次调用。输出超长不能免费拆为逐模块生成。
- §11：改 shape、layout、quantization、groups、规则或其引用时，重算签名／ABI／构建身份；使旧 body/cache 失效或按明确依赖证明复用。不能用同位宽作为可复用条件。
- §15：公共诊断可以给出声明不匹配；独立 oracle 的规则不从候选 PC 生成。实际布局、配对、量化、reduce 生命周期和活性需要行为测试。
- §17：三个 AI JSON 示例是开发用表示样例；不能直接晋升 formal task、额外 family 或 oracle-ready。先补齐完整任务语义和独立参考。
- §21：加入本包的正反例；同时保留“低容量 FIFO 静态通过但活性未验证”的范围测试，防止过度声明。

## 3. 对研究计划的有限同步

~~本次只是方法版本增量，不自动改 M0–M5、B4、主要比较、四家族总体、统计参数或 hidden 规则。AI 案例是否进入后续研究须在结果前单独确定。~~

**已由 `paper1-v2.2` 取代（见文首更正）：** 方法（M0–M5）、B4、主要比较与 hidden 规则确实不变；但**总体已改为三个 AI 家族**，AI 任务不再是"待定案例"而是主总体。统计单位改为 `design_cluster_id`。

将 PC 术语、活动 schema 及支持域同步到 2.1；把“跨模块一致性”按接口结构、数值/布局声明、实际事务行为分开报告。静态拒绝率和关联覆盖不能替代隐藏正确率或直接证明胜过 Codex。

## 4. 建议的最小实际闭环

1. 选一个小型、固定形状的 Depthwise→Pointwise 开发任务；冻结权重、运算次序、量化、边界和协议环境，并写独立位精确参考。
2. 对相同公开任务定义一个可执行的 tensor ABI；先用人工参考验证 emitter 与实际调用路径，记录它不是模型效果。
3. 接入一次模型规划和一次批量行为生成，分别记录 PC 错误、行为错误与基础设施异常。
4. 加入公开反馈修复，保留 B4 与封存规则，再观察布局、数值和事务错误是否真的下降。
5. 才推进残差错拍／缓冲场景和分块 GEMM；不先搭建通用 CNN 编译器或完整 SoC。

本包的 Python 坐标／量化辅助函数只能服务其明确的精确有理数语义。接入外部量化 runtime 时，应验证 kernel 算术差异，不能只按名称认定 bit-exact。
