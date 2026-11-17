# 现有资产中的真实结构交接需求核查

日期：2026-10-21。本轮只读公开定义及指定 RTL 分段，不运行模型、HDL、SAT、生成器或作者框架，不修改实现、旧 artifacts 或正文。分支 `develop`，revision `e20dfd2ce46c5690767e30cb629fb5c58aff073a`；保留已有工作树和暂存改动。判断不使用 hidden testbench/oracle/vector/seed 实现，也不重启已停止的 M06 方向。

**结论：没有找到一个已成立、且现有直接构造尚不能满足的交接瓶颈。** 找到一例确有两种逐周期等价结构的公开 FIR 资产，但其依赖约束可直接构造；另有 UART FIFO 的真实读时机耦合，不过公开条款不足以认定不同潜伏期方案都是原需求允许的结构。不能把这两种情况合并成两个新方法正例。

## 1. 公开依据与判断权限

读取范围是 `agent/README.md`，`task_catalog.py`、`family_recipe.py` 的公开定义，catalog 对应公开条目，`task_families/{stream,protocol,datapath}.py` 的 RTL 函数；为追到 recipe 的实际文字，定向读取其调用的 `prompts.py` 公共 guidance。`family_recipe.py:411`–`:425` 将 initial/retry guidance 纳入 recipe hash；该文件开头明确这是 legacy development 选择器，不是 PC2.1 核心入口。

Catalog 的 `architecture_obligations` 是公开义务标签，不能当作已经给定了所有时钟级条件。例如 FIR 的 `coefficient_order/accumulator_width/latency_within_bound/initiation_interval` 在 `contracts/task-catalog/sr2fpga-task-catalog-v0.2.json:1693`–`:1712`；这里没有具体的可选内部延迟或延迟等价规则。公开 RTL 能支持本轮的结构和代数判断，不能自行替代尚未给出的正式需求裁决。

下文区分：①现有公开要求；②从当前 RTL 手工推导的等价选择；③需要新增公共语义后才能成立的选择。两例均未执行验证，不作为新候选表现或正式结果。

## 2. FIR：真实的累加连线自由度，尚不是未满足瓶颈

**已有要求与接口。** 公开 catalog 要求系数顺序、累加宽度及流水相关义务。当前公开实现的 top 是 sample/result ready-valid 接口，例化 `fir_filter_core`，输出宽度为 `WIDTH+3`（`agent/src/sr2fpga_agent/task_families/datapath.py:2159`–`:2187`）。core 固定系数 NEW=3、PREV=-2、OLD=1（`:2209`–`:2211`），历史样本是 `sample_d0/sample_d1`。同一 `sample_valid && sample_ready` 接收时刻捕获结果并移动历史；堵塞时保持（`:2219`、`:2251`–`:2263`）。

三个 helper 是纯组合 MAC，共用同一 `ACC_WIDTH=RESULT_WIDTH`。每个 helper 把自己的乘积加到 accum，结果按同一宽度编码（`:2272`–`:2285`）。从该公开 RTL 得到接收时的函数是

`result = encode_(WIDTH+3)(3*sample - 2*sample_d0 + sample_d1)`。

**两种合理结构。** 保留所有 sample/coefficient 绑定、三个 helper、历史寄存器、输出寄存器和握手，不添加任何并发、性能或时序承诺：

| 累加连接 | A：当前公开结构 | B：手工等价结构 |
|---|---|---|
| `u_mac_new_sample.accum` | 0 | `stage1`，即 previous helper 的 result |
| `u_mac_previous_sample.accum` | `stage0`，即 new helper 的 result | 0 |
| `u_mac_oldest_sample.accum` | `stage1` | `stage0` |
| 最终输出 | oldest helper 的 `filtered_result` | 同一输出 |

new/previous/oldest 的 sample 和 coefficient 端点逐项保持当前值：`sample/3`、`sample_d0/-2`、`sample_d1/1`（`:2221`–`:2248`）。A 是 `new→previous→oldest`；B 是 `previous→new→oldest`。同宽度模加法的交换/结合律给出相同结果；普通乘积、每个 helper 的截断和最后输出宽度均未改变。寄存器更新和 `sample_ready` 没有改变，所以从该 RTL 推导的是同一接收/输出周期行为，不是把原任务改成仅事务等价。该判断是静态推导，未编译或仿真。

Catalog 公开义务未指定这三个组合 helper 的物理累加先后；上述 B 保持每个时间样本与其原系数相配，因此没有用交换样本历史来规避 `coefficient_order`。若另有独立任务要求明确把物理链顺序固定为 A，则该要求必须一并审查；本轮未把缺少这类条款当成已完成新任务资格认证。

**真实跨决策约束。** 三个项须各贡献一次、累加依赖无环、首节点来自零、末节点连到最终输出，且全部项使用同一次接受事件对应的历史样本。只核端口位宽，不能保证这些关系：例如双向接 new↔previous 会成环，跳过一个 helper 会漏项。这里不需要假设新的模块延迟、编码或缓冲行为；MAC 本身无状态。

**标准编译/直接构造能做什么。** 已知三项和固定 MAC ABI 后，任选一个合法拓扑顺序，直接发射零起点及相邻 accum 连线即可。固定 A 已满足当前公开实现的全部算术/握手行为，构造 B 也只需改上述三处来源。把这些普通依赖约束写成约束系统可以检查错误组合，但本资产没有显示必须由 LLM 提供某个不可机械构造的选项，或现有合法 A 无法满足需求。

**判定。** 可作为“不同内部连线但顶层功能相同”的开发负对照；不是一个已发现的未满足交接需求。它不支持延迟选择收益、资源优化收益或新协议推导机制。公开 catalog 的延迟/II 标签也不足以把它扩成新的硬件优化题。

## 3. UART FIFO loopback：真实接口耦合，缺第二个获准时序方案

**已有要求与接口。** Catalog 的明确公开义务是 `uart_frame_correct`、`fifo_order_preserved`、`no_drop_no_duplicate`（`contracts/task-catalog/sr2fpga-task-catalog-v0.2.json:846`、`:867`–`:869`）。公开 top 接口是 `clk/rst_n/rx/tx/tx_enable`，并组合 RX、FIFO、TX（`agent/src/sr2fpga_agent/task_families/protocol.py:797`–`:845`）。这里没有公开列出 FIFO 读延迟的可选域，也没有声明允许 UART TX 起始沿相对原实现任意后移。

当前 FIFO 是四深度、8 位 show-ahead 接口：`dout=mem[rd_ptr]`，empty/full 由 count 组合产生，`rd_en && !empty` 时移动 rd_ptr（`:871`–`:907`）。父控制在 `tx_enable && !fifo_empty && !tx_busy && !tx_start` 时，同时安排 `fifo_rd_en`、`tx_start`，并把当时的 `fifo_dout` 捕获到 `tx_data`（`:851`–`:861`）。这是真实的跨文件时序依赖：父依赖的是**发出读请求之前就可见的队首值**，不是仅依赖一个 8 位端口名。

**选择与约束。**

- A：保留当前 show-ahead FIFO 及父捕获时机，是现有自洽实现。
- B 的常见设想是把 FIFO 改成请求后才提供数据的注册读，并让父“读请求→等待→锁存数据→启动 TX”。它需要匹配数据可用周期、pop 时点、TX start/data 捕获时点及重复启动抑制，不能只统一端口名或位宽。

B 没有在本轮被认定为满足原顶层功能：增加等待可能改变 tx 引脚的起始沿，公开义务标签没有裁定这种改变是否允许。若需要预取才能完全隐藏内部延迟，则预取、容量与边界周期的正确性又须实际设计并证明；本轮没有现成的第二份已公开方案可直接复用。因此不能把“两个子模块各自能工作”推成“两种组合都已获原需求允许”。

**标准编译/直接构造能做什么。** 对现有 show-ahead ABI，当前父控制已经直接实现交接。若可信侧确实提供一个不同读时延 ABI及相应顶层时序允许范围，确定性适配控制可以按数据可用关系安排动作；这是需要先给定的公共事实。当前代码没有显示一个已经存在的、要求在两类 FIFO 间自动选择且尚无法满足的用户需求。仅观察到潜在替换风险，不等于发现了新生成方法必须解决的缺口。

**判定。** 不计为第二个合格的双结构正例。不能为使该例成立而新增“只比较字节序列、忽略 tx 时序”、额外并发、吞吐目标或新的缓冲策略。

## 4. 收口

stream fork/join 的公开 recipe 已规定组件、实例、显式 payload/valid/ready 路径，并禁止融合（`agent/src/sr2fpga_agent/prompts.py:437`–`:454`、`:590`–`:599`）。公开 join 的组合方程是双 valid 配对、ready 交叉条件和相加；fork 则要求相应双向握手绑定（`agent/src/sr2fpga_agent/task_families/stream.py:916`–`:920`、`:1455`–`:1458`）。同型对称通道交换不能自动成为新的非平凡协议/潜伏期选择问题。vector MAC 的公开接口也明确共同接受条件及配对数据（`agent/src/sr2fpga_agent/task_families/datapath.py:1627`–`:1630`）；本轮没有据此加入未声明的替代配对语义。

本轮资产支持“一例普通等价结构选择”和“一处真实读时机耦合风险”，支持不了两个已具备公开合法替代方案的未满足交接瓶颈。没有新增问题定义、评分规则或实验预算；不把该局部无例结论推广为所有多模块硬件都不存在交接问题。

## 附录：UART 无丢失摘要与环境前提

补充只读核查未在已定位公开 guidance/requirement-envelope 代码中找到明确的 overflow 丢弃许可、UART 到达速率约束、`tx_enable` 最长关闭时间，或“只对已接纳 byte 保证”的条款。精确文本及层级如下：

- `agent/src/sr2fpga_agent/project_generator.py:2945` 的固定 `_expected_behavior` 摘要是 “received UART bytes are buffered in order and transmitted without drops or duplicates”。它写入 `intent.design_goal`（`:699`）；`verification.expected_behavior`（`:744`）则经 `_test_pass_means`（`:3044`–`:3045`）包装成 TEST_PASS 说明。这是 legacy 生成侧摘要，不是含环境假设、接纳事件和时间量词的完整协议；代码没有在该字符串中定义 `received` 等同于 FIFO 已写入。
- 同一 intent 的默认 assumptions 只有 “single synchronous clock” 和 “no vendor-specific IP”（`:701`）。Catalog 的 frame/order/no-drop 标签亦未给上述前提。`requirement_envelope.py:252`–`:263` 明确区分显式文本、可信 defaults/assumptions；`:411`–`:418` 优先使用实际 `request.description`，空缺才生成泛化任务句。该机制不是一条预置 UART 流量限制；本轮未获得一份已裁决的具体实例 envelope 来证明另有约束。
- 公开接口只有 RX 输入、TX 输出及 `tx_enable`，没有接收背压（`project_generator.py:2393`–`:2402`）。参考 RTL 的写使能在 FIFO full 时被屏蔽（`task_families/protocol.py:830`–`:838`），停发条件及四深容量见前节。屏蔽写入是实现行为，不能反向当作需求已经允许 overflow 丢弃。

若把摘要额外解释成“RX 可持续送入合法帧，`tx_enable` 可任意久关闭，所有接收字节仍无条件保留并最终发送”，有限缓冲且不可背压的系统无法保证它；即使输入遵守 UART 波特率，足够长的停发仍可耗尽容量。这是条件性的静态不可实现性判断，未运行失败用例。应保留结论为：**无条件解释不可实现；需求可能缺环境前提或接纳/溢出定义，正式语义尚未定。** 不能据此宣布原任务已坏，也不能自行增补丢弃许可、最长停发或 eventual-enable 条件再用于评分。
