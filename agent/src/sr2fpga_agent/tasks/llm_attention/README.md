# 固定量化 GQA 解码注意力开发 case

本 case 实现增量 decode 的 **KV cache 追加、分组 QK 打分、稳定减最大值、公开整数 exp LUT、归一化 AV**。它使用 Hq=4、Hkv=2、D=3、最多四个 cache token、两个 INT8 lane。`kv_head=query_head//2`，不同 KV 组使用不同数据；因此它覆盖真正的 grouped-query 映射，而不是单 KV head 的退化情形。

这是固定合成数据的工程开发任务，未加载真实 LLM 权重，也不声称语言模型精度、完整 Transformer、任意 softmax 或端到端 token 吞吐。候选应根据公开 facts/assets 实现相同冻结整数函数；通用 PC emitter 不插入 attention 算法。

## 公开接口与持久状态

`build_development_task()` 返回公开边界、facts、LUT 原始 bytes，以及完整注册开发 target/capability。它不返回 evaluator 的输入序列、oracle、驱动或期望答案。

四条 `ready_valid_v1` 流均使用单上升沿时钟和低有效同步复位：

| 流 | 方向 | 逻辑形状 | 每次调用拍数 | 量化 scale |
| --- | --- | --- | --- | --- |
| q | 输入 | Hq=4 × D=3 | 8 | 1/8 |
| k | 输入 | Hkv=2 × D=3 | 4 | 1/8 |
| v | 输入 | Hkv=2 × D=3 | 4 | 1/4 |
| context | 输出 | Hq=4 × D=3 | 8 | 1/4 |

所有元素均为 signed INT8、zero-point=0。lane0 在低 8bit，lane1 在随后 8bit，mask 位于 [17:16]。每个 head 独立占两拍，mask 为 `11,01`，尾拍无效高 lane 必须 raw0。不能把一个 head 的尾 lane 与下一个 head 首元素拼在同拍。

一次 invocation 收到完整 Q、K、V 后原子追加一条 K/V，再对有效 cache（包括本次新 token）求 context。三条输入流可以按任意顺序到达，内部等待全部收齐；下一 invocation 必须等待本次最后 context 拍被接受。cache 从 reset 后 length=0 开始，长度依次增至 1、2、3、4；历史 K/V 在多次 invocation 之间保留。第四次完成后所有输入 ready 均为 0，必须 reset 才能继续。

复位取消部分输入与待输出，并将 valid length 设为 0。物理缓存内容无需清零，旧值因为不再有效而不得参与结果。任务不提供完整 prefill 接口、滑动窗口、分页缓存、乱序标签或多请求交织。

## 精确冻结的近似数值规则

对 query head h 和已缓存 token t，令 g=h//2：

```text
dot[h,t] = Σd Q[h,d] × Kcache[t,g,d]
score[h,t] = clamp[-8,8](RNE(dot[h,t] × 37 / 1024))
max_score[h] = max_t score[h,t]
weight[h,t] = EXP_LUT[max_score[h] - score[h,t]]
context_raw[h,d] = sat_int8(RNE(Σt weight[h,t] × Vcache[t,g,d] / Σt weight[h,t]))
```

RNE 为有符号精确有理数向最近偶数舍入。Q/K scale 均为 1/8，`1/sqrt(3)` 使用公开工程近似 `37/64`，score 网格为 1/4，因此上述 index 系数为 37/1024。score clipping 和 exp LUT 都属于本 profile 明确可见的数值定义，不声称与任意生产模型的实数 softmax 相同。

LUT 的 delta 为 0..16，精确值为：

```text
(256,199,155,121,94,73,57,44,35,27,21,16,13,10,8,6,5)
```

这些整数近似 `256×exp(-delta/4)`；候选使用公开表本身，不自行计算浮点 exp。所有权重为正，最大项权重为 256，故分母不会为零。概率不先单独量化；最终 AV ratio 只舍入一次。

首个 token 时，任意 query 的 context 等于该组当前 V。两个零 query token 时，权重相同，输出是同组两条 V 的 ties-even 平均。这两个可手算性质以及组间差异被专门测试。参考累加器和中间 integer 的范围在该固定 INT8、T≤4 配置下小于 signed int32；不声明更大配置自动安全。

## 设计与验证职责

`reference_design()` 是手写开发 PC：一个结构 top 和一个 `CachedDecodeAttention` 行为 core。PC 声明 K/V memory 与 validLength register，tensor rule 使用显式 compute。`reference.py` 为时钟状态机和 signed 商/余数舍入，独立 `oracle.py` 使用 Python 整数/Fraction；二者只共享公开 LUT 常量。

参考微架构逐 head、逐有效 cache token 和通道串行计算，所有 head 复用 QK 与 AV 的有界乘加路径，比值计算位于唯一状态分支。QK 累加使用 signed17，乘公开常数 37 后使用 signed22；score 的除 1024 通过移位和余数位完成 nearest-even。LUT 权重使用 unsigned9，权重和使用 unsigned11（最多 1024），AV 累加使用 signed18。AV 的公开极值为 -131072 和 130048，取绝对值时使用 unsigned18，避免 signed18 的最小负数求负溢出；最终 ratio 使用有界 18/11 商余数和符号恢复。

计算阶段在有效 cache 长度 L 时为 `4×(7L+3)` 周期，L≤4 时最多 124 周期，再加输入、追加和输出服务；公开 256 周期完成义务保持不变。上述位宽依赖当前固定 INT8、D=3、T≤4 profile 的范围，不表示任意尺寸或量化配置均可直接复用，也不构成 FPGA 资源或时序达标结论。专门 HDL 回归以四个零 query token 将分母推到 1024，并覆盖 V 全 -128 和全 127 的两侧极值。

`reference_behavior_bodies()` 可通过 PC 真实 Yosys parser 装配；`render_reference_project()` 提供独立手写 wrapper。它们是工程控制，不是候选模型结果。

`harness.py` 属于 evaluator。固定 schedule 检查部分输入 reset、阻塞输出 reset、四次连续 append 至满、满缓存反压、reset 后两次新 decode、不同输入流到达顺序、source pauses、sink 两周期阻塞、尾 mask 和末尾 drain。监测器从真正 accepted Q/K/V 重建持久 cache，每个 offered 输出都与期望首拍比较，accepted 后才推进。它在清除最后输出状态之前检查 256-cycle completion，因此最后拍不会绕过时限判定。

标准完整 schedule 应有六次 completed invocation、48 个 accepted context beats、四个 reset 块、两次取消、最大 cache length=4、最终 cache length=2。`TEST_PASS`、进程退出 0、缺失 TRACE_END 或不完整输出都不能代替这些检查。

## 本地开发验证

从仓库根执行，并选择新的 artifacts basetemp：

```powershell
$env:PYTHONPATH = (Resolve-Path agent/src).Path
python -B -m pytest agent/tests/test_sr2fpga_llm_attention.py -q -p no:cacheprovider --basetemp=artifacts/paper1-ai/<fresh-attention-tests>
```

数学和 schema 检查无需模型或重型依赖。两项 HDL 检查需要真实 Icarus/vvp，PC-emitted 检查还需要真实 Yosys。工具崩溃保持失败，不能转成静默 skip；历史 Windows sandbox 的 Icarus 访问冲突应与主机批准环境结果分别保存。普通开发验证不授予 family qualification、正式 hidden、B4、公平比较或 L4 信用。
