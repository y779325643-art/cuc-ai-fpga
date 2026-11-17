# SR2FPGA Paper 1 LLM 推理案例修订

研究版本为 `paper1-v2.3`，日期为 2026 年 10 月 28 日。用户明确要求将设计 case 替换为 LLM 大模型推理相关场景，并选择同步修改设计、任务代码和文档。本修订是当前任务总体与案例的权威；它与 [v2.2 研究计划全文](2026-09-15-sr2fpga-paper1-research-plan-v2.2.zh.md) 共同组成当前计划。发生冲突时，本修订覆盖原计划的案例、总体和版本绑定条款，其余研究定义沿用。

状态为已采用、未冻结。授权包含仓库迁移、三个固定开发 case 的代码、独立 oracle、参考 RTL 和本地开发验证；不包含模型调用 campaign、正式 hidden、训练、物理评测或证据晋级。

## 1 当前总体和方法边界

研究问题保持为：Project Contract、确定性结构构造与受限公共反馈修复，能否改善多文件 FPGA 子系统生成。当前总体改为三个 LLM 推理子系统：

| 家族 | 实现目录 | 主要工程义务 |
| --- | --- | --- |
| `llm_quantized_qkv_projection` | `agent/src/sr2fpga_agent/tasks/llm_qkv/` | 同一输入的三路量化投影、不同 Query/KV head 数、head 轴布局、独立背压 |
| `llm_kv_cache_decode_attention` | `agent/src/sr2fpga_agent/tasks/llm_attention/` | KV cache 跨步生命周期、GQA head 映射、QK 分数、稳定 softmax 近似、AV、取消与完成 |
| `llm_gated_ffn` | `agent/src/sr2fpga_agent/tasks/llm_ffn/` | gate/up 双路投影、SiLU 查表、门控乘积、down projection、残差配对和量化次序 |

配置身份为 `research_plan_version=paper1-v2.3`、`population_id=llm_inference_subsystems_v1`、`pc_format=sr2fpga-pc-2.1`。M0–M5、M5−M1@B4 与 M4−M3@initial、两个主要假设的 Holm 族、design_cluster_id 独立单位、三家族等权分析、缺失与全分母规则、方法信息边界均沿用 v2.2。B4 未决 token/工具/时间轴仍需正式前冻结，不能因为换 case 获得额外免费调用。

这三个家族取代 DW→PW、量化残差块和分块 GEMM 的主总体位置。旧家族、固定 DW→PW 实现和所有原始记录保持原身份，继续用于历史解释或开发回归；不把它们的结果换标签归入 LLM。

## 2 与 LLM 推理的关系

本组案例对应 decoder 中的投影、注意力和门控前馈三个主要计算位置。GQA 将 Query heads 分组并共享组内 K/V heads；本开发配置使用 4 个 Query heads、2 个 KV heads，能够实际区分组映射错误。[GQA 原论文](https://aclanthology.org/2023.emnlp-main.298/)

门控 FFN 使用两个线性投影、一个分支的非线性和逐元素乘积，再进行输出投影，机制依据 GLU/SwiGLU 工作；当前硬件 profile 的整数查表规则由本仓库公开任务精确定义。[GLU Variants Improve Transformer](https://arxiv.org/abs/2002.05202)

首版使用手工设计的非退化合成常量和小尺寸，建立可检查的 RTL 闭环。它们不是从某个商业或开源 checkpoint 抽取的真实层，不提供端到端 token 生成、perplexity、模型质量、真实 LLM 吞吐或生产量化精度结论。RMSNorm、RoPE、输出词表头和多层调度位于当前 case 边界之外。

三个固定 profile 独立定义量化编码与调用边界；例如 QKV 的输出 zero point 和 scale 并不直接等于 attention 输入配置。它们不是已经可直接相连的 decoder 层。若要串接，必须公开并实现精确转换及新整体任务规格，不能增加一条 net 后假定端到端数值兼容。

## 3 公开共同约定

公开源使用已注册的 development public context v2、PC2.1 development target v1 和 capability v1；不创建第二套 tensor 或 FPP 格式。任务输出包含 task_id、family、development_only、boundary、facts、required_trace_facts、public_text、public_assets 和完整注册 profiles。

原始公开资产经 size_bytes 和 SHA256 绑定。候选只收到公开任务、精确数值规则、权重或 LUT；oracle、刺激、期望输出、手写参考行为不放入 public 目录。入口签名来自 requirement_boundary，内部模块分解由设计决定；手写控制的模块数量不成为候选硬要求。

数值使用显式整数与有理 scale，signed round to nearest ties to even，INT8 饱和顺序由各 case 固定。bias、zero point、舍入、激活与累加器范围不得由候选自选。LUT 的已公开原始整数表是该工程 profile 的语义，不能用不同 exp/sigmoid 实现悄悄替换。

流使用 ready_valid_v1，在上升沿 valid&&ready 时转移；阻塞时 valid 与完整 payload 保持。lane0 在低位，两个 INT8 lanes 加两个 mask 位组成 18bit。每个 head 或 feature 行重新分尾拍，invalid lane 为 raw0/mask0。同步低有效 reset 取消未完成事务；cache 的逻辑失效由有效长度和控制状态复位实现，不要求物理存储逐字清零。

## 4 QKV 投影固定开发 case

首版 T=2、Din=5、Hq=4、Hkv=2、Dhead=3、lanes=2。输入为 `[T,Din]`，Q 为 `[T,Hq,Dhead]`，K/V 分别为 `[T,Hkv,Dhead]`。输入 6 拍；Q 16 拍，K/V 各 8 拍。分支可以独立停顿，不允许为保持一路顺畅而丢失另一分支的数据。

三个权重矩阵和 bias 独立公开，使用 centered MAC、明确的输出重定标和饱和。GQA 的投影维度差异在本 case 体现；Query 到 KV 组的 attention 选择由下一个 case 验证，不把尺寸检查冒充组映射验证。

必须覆盖非零/负输入、正负 ties、饱和、head/coordinate 顺序、三路不同时接受、tail mask、连续调用、输入未收完或输出被阻塞时 reset，以及超时最后一拍边界。

## 5 带 KV cache 的 decode attention

首版 Hq=4、Hkv=2、D=3、Tmax=4、lanes=2。每次 decode 原子收齐 Q、当前新 K 和新 V；K/V 追加到真实持久 cache，再使用全部有效历史求本步 context。每组两个 Query heads 使用 `kv_head=qh//2`。不是把完整历史重新作为每步输入后称为 cache。

Q/K 的 affine scale 为 1/8、zero point 为 0。D=3 的工程缩放常量为 37/64，近似 1/sqrt(3)；logit 格点为 1/4：

```text
score_index = clip[-8,8](RNE(dot(Q,K) × 37 / 1024))
delta = max(score_index) - score_index
weight = EXP_LUT[delta]
context[d] = sat8(RNE(sum(weight × V[d]) / sum(weight)))
EXP_LUT = (256,199,155,121,94,73,57,44,35,27,21,16,13,10,8,6,5)
```

稳定 max subtraction 保证 delta 在 0..16，最大分数的权重为 256，分母非零。这里冻结的是整数 softmax 近似 profile，不声称与实数 softmax 或某个 LLM checkpoint 等价。两组 KV 使用不同数据，必须能检出错误 group 索引。

cache 从 reset 后空状态开始，连续 decode 验证历史保留和追加；满四步后 ready 保持低，合法环境在下一次输入前必须 reset。输入 Q/K/V 可分别停顿，但不得跨调用交织。reset 取消部分输入/输出并把 cache 有效长度归零；之后首步结果不得受到旧内容影响。

## 6 门控 FFN 固定开发 case

首版 T=2、Din=5、Dff=7、lanes=2。gate/up 为独立公开权重的投影，公开 256 项 SiLU LUT 将 gate code 映射到近似激活；逐元素乘 up，再经 down projection 和残差融合输出。

该固定工程 profile 使用输入/中间 scale=1/4、zero point=0，stage 的具体除数和饱和位置以公开 numeric fact 为准。LUT 采用每个 INT8 gate code 的固定表项，不在候选或 oracle 运行时依赖浮点 exp。

当前小例使用同一公开输入作残差旁路，明确其计算为 `FFN(x)+x`。归一化位于边界外；不能把它描述为完整 `FFN(RMSNorm(x))+x` 的 pre norm Transformer block，也不把同输入残差简化推广到真实 checkpoint。

必须验证 gate/up 分支次序、SiLU 负半轴、ties 与饱和、逐元素坐标配对、down 权重索引、bias 加入位置、残差只加一次、tail、背压和复位取消。参考微架构不构成候选必须使用的模板。

## 7 工程和评测职责

每个 case 独立提供 task.py、oracle.py、reference.py、harness.py。public task 定义必须实现什么；reference 是手写控制；oracle 用不同数学实现从接受输入重建答案；harness 检查事务。通用 checker/emitter 不根据家族或 intent 注入任何上述算法。

新的 `python -m sr2fpga_agent.tasks.llm` 提供 prepare 和 check-reference。prepare 只准备冻结公开输入和受信来源快照，不执行模型或工具；check-reference 将手写 design 经实际 PC assemble/check/build/compose 后执行编译、仿真和独立 trace 检查。显式 --synthesize 才增加有上限的通用综合。

开发通过不关闭正式资格。catalog 记为 partial、qualification_status=not_ready，无旧 Runner alias、正式 split 或虚构 mutation threshold。旧证据账本只追加无结果的占位行；原有结果字段、run ID、artifact refs 和哈希不改写。

## 8 正式前仍需完成的工作

三个固定小例不是三个有统计能力的家族总体。正式前仍要建立公开任务卡与配置覆盖、独立 design clusters、固定权重和 workload 来源、资格 mutation、public/hidden 划分、工具与目标资格、全轴预算和封存调度，以及继承的统计分析实现。

v2.2 的样本规模、功效和物理位置仅作为原研究设计基线；不能在换总体后宣称旧 pilot 已验证新规模。新的预算测量、设计簇抽样框、功效依据及 L4 子集需要在正式运行前按继承规则统一冻结。当前代码迁移没有产生这些正式结论。
