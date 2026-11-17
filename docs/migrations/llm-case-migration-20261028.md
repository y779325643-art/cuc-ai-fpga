# LLM 推理案例迁移记录

本记录对应用户在 2026-10-28 明确提出的 LLM 推理 case 替换，以及随后选择的“同步修改 case 设计、任务代码和文档”。研究定义见 [paper1-v2.3 案例修订](../specs/2026-10-28-sr2fpga-paper1-llm-case-amendment-v2.3.zh.md)；本文件只记录实现和验证，不定义新的结果资格。

## 已完成的代码范围

| 范围 | 当前实现 |
| --- | --- |
| `tasks/llm_qkv/` | T2/Din5/Hq4/Hkv2/D3；三路独立输出、非零 zero point、精确 RNE、公开合成权重 |
| `tasks/llm_attention/` | Hq4/Hkv2/D3/容量4；真实持久 KV cache、组映射、原子追加、公开 exp LUT、AV、满缓存反压和 reset 失效 |
| `tasks/llm_ffn/` | T2/Din5/Dff7；gate/up、公开 SiLU LUT、乘积、down 和同输入残差 |
| `tasks/llm.py` | 公共准备、源快照、PC 检查和确定性构造、真实 parser 装配、参考控制执行与分层记录 |
| catalog/runtime | 当前版本绑定改为 v2.3，data revision 0.4.0；三家族 partial/not_ready，无旧 Runner aliases |
| 回归 | 三个 case 的数学、公开契约、静态结构、事务边界、真实解析和 RTL 测试；公共准备及历史总体隔离测试 |

每个新 case 将 `task.py`、`oracle.py`、`reference.py` 和 `harness.py` 分开。没有修改通用 PC schema、checker/emitter 的算法职责，也没有修改旧 DW→PW oracle、harness 或已有候选文件。

新总体中的 `partial` 表示存在固定开发实现，不表示 benchmark 家族已就绪。旧证据账本新增三条无结果占位；原有 74 条 family 记录及 alias/L4 记录逐值保留，不将这次工具回归晋升为官方结果。旧 CNN/residual/GEMM 选择保存在 `legacy_quantized_ai_core_v2_2`，历史 run 和审查报告不重命名。

## 执行边界

本次没有候选模型调用、训练、正式 hidden、统计 campaign、物理实现或外部发布。`check-reference` 执行的是公开任务的手写控制；实际 FPP 经 PC2.1 build/compose 生成，而非跳过构造直接测手写 wrapper。参考 wrapper 另有测试，不能替代 PC-emitted 工程验证。

工具运行和原始失败记录写在 `artifacts/paper1-ai/llm-case-migration-20261028/`。Icarus 在沙箱内再次出现 Windows `0xC0000005` 访问冲突；失败 XML/compile 记录保留，主机环境复核另建目录。新旧结果不覆盖。

## 验证记录

公共准备入口已实际执行三 case、零模型调用；初版源快照 key 不满足已有 ArtifactStore 对 `__init__.py` 段的限制，现已改为路径摘要生成安全 key，保持原 store 规则。首次失败目录保留；集成修正后 `integration-static-02.xml` 记录 **39 passed，5 subtests passed**。

最终组合与工具验证如下，产物都位于上述 runtime 目录：

| 检查 | 结果 | 产物 |
| --- | --- | --- |
| contracts、compatibility、catalog/evidence、PC 与公共准备相关回归 | 708 passed，5 subtests passed；5 个真实 parser 用例在该命令中另行排除 | `regression-02.xml`、`regression-02.log` |
| 三个新 case 数学、静态、真实 parser/HDL、逐 token 参考 | 44 passed | `llm-host-02.xml` |
| 注意力有界串行参考及新增极值回归 | 16 passed，包含与上行重叠的 14 项和新增 2 项 | `attention-optimized-host-01.xml` |
| 公共准备、源码/契约快照与失败状态最终复核 | 10 passed，与 708 项中的 suite 重叠 | `suite-final-01.xml` |
| QKV 实际 PC-emitted FPP | 检查、装配、编译、仿真、语义、完整 generic synth 均通过；3 次调用、Q48/K24/V24 输出拍、2 次取消 | `reference-01/qkv/result.json` |
| FFN 实际 PC-emitted FPP | 同上；3 次调用、18 输出拍、2 次取消 | `reference-01/ffn/result.json` |
| 注意力优化版实际 PC-emitted FPP | 同上；6 次 decode、48 输出拍、2 次取消、cache 最大4/最终2 | `attention-reference-02/result.json` |

按 classname/name 去重，共 754 个不同回归用例有通过记录，另有 5 个 subtests；重复复核不另增样本数。Ruff 通过。三个参考的完整综合分别为 QKV 52.57 秒、FFN 38.27 秒、注意力 6.28 秒，均未提高单次 60 秒上限。这些是工具运行时间，不是推理延迟或 FPGA 时钟指标。

首轮注意力参考虽然仿真通过，但大量展开的 32bit 可变除法使完整综合超时。只调整手写参考微架构为逐 head/token/channel 共享乘加和 18/11bit ratio 电路，保留公开 profile、oracle、harness、ABI 和 256 周期义务。补充真实 RTL 的 V=-128/127、den=1024 极值测试；原 `reference-01/attention` 超时记录不覆盖。

交叉审查还修正两个新 harness 的架构偏置：FFN 期望队列按 token 增量建立，允许调用内输入/输出重叠；QKV/FFN 的待输出 reset probe 并发送输入并等待首个输出，不强制完整帧缓冲。真实逐 token QKV 参考与独立 FFN trace 反例均通过。旧 evaluator 未因这些修改获得新的通过信用。

最终每 case 的结果属于其实际源快照。QKV/FFN 的通过记录保留在首轮各自目录，注意力采用优化后的单独记录；不能将原注意力超时改成同一运行已通过。新公开准备应选择新目录，源码变化会使旧 preparation 的全仓源快照复核拒绝继续使用。

## 保留的限制

三个 profile 使用不同量化和事务边界，尚未串成一层 decoder。FFN 小例的 residual 复用输入，不含 RMSNorm；QKV 不含 RoPE；attention 是明确的整数 softmax 近似 profile。合成小尺寸不能支持真实模型精度/吞吐、所有输入证明或家族总体优势。统一正式 M0–M5、cluster sampling、mutation qualification、冻结 split、全轴 B4 和新总体 L4 仍需独立实现与授权。
