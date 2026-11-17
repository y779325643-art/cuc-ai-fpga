# 下一机制有界设计：读相位适配与采样锚点交接

日期：2026-10-21。范围：两个静态候选；不调用被测模型、不运行 HDL/SAT、不写实现或修改任务规则/正文。只新增本文件。检查时为 `develop`，HEAD `e20dfd2ce46c5690767e30cb629fb5c58aff073a`；未操作 staging、commit 或 remote。与 engineering_status 仅交换了公开路径和需求定位，没有转移运行授权。

**结论：定位到两类真实的结构交接问题，但当前没有一项具备可直接进入新核心开发的完整资格。** 第一项“按逻辑退休点保持容量的读相位适配”最值得进一步核对需求；第二项“变潜伏期模块的显式采样锚点传播”有清楚的语义，但当前更接近普通 sideband/closure 编译。它们都不能仅靠新字段、预先冻结或首次无反馈声称新颖；系统级省工和交接可靠性仍有可检验空间。

## 1. 公开资产确实给了什么

| 资产 | 本轮已读事实 | 尚未建立的要求 |
| --- | --- | --- |
| UART FIFO loopback | [目录](../../../../contracts/task-catalog/sr2fpga-task-catalog-v0.2.json#L846)有 frame correct、FIFO order、no drop/no duplicate 义务；[公开 intent](../../../../agent/src/sr2fpga_agent/project_generator.py#L2945)要求接收字节按序缓存并发送。实际 [top](../../../../agent/src/sr2fpga_agent/task_families/protocol.py#L850)在可发送时同时安排 read/start 并捕获 FIFO dout；[FIFO](../../../../agent/src/sr2fpga_agent/task_families/protocol.py#L887)是 `dout=mem[rd_ptr]` 的 show-ahead 读口 | 未定位到明确允许更改首字节发送周期、增加总缓存容量或改变满时写入行为的公开条款。仅有事务 scoreboard 标签不授权改外部时序 |
| vector MAC pipeline | [架构提示](../../../../agent/src/sr2fpga_agent/prompts.py#L458)规定两路输入 buffer、MAC、score stage 和配对路径；[实际 core](../../../../agent/src/sr2fpga_agent/task_families/datapath.py#L1627)共同接受 feature/weight；[L1643–1648](../../../../agent/src/sr2fpga_agent/task_families/datapath.py#L1643)在第四对被接受时将当前 bias 加入结果 | 公开 [intent](../../../../agent/src/sr2fpga_agent/project_generator.py#L3006)说固定向量长度、加 bias，但未定义 bias 在输入期间变化时应在哪个事件采样，也未明确许可改变 score 的外部周期 |
| 通用元数据 | [memory 要求](../../../../agent/src/sr2fpga_agent/prompts.py#L1230)已有 read_latency/read_type；[data-flow timing](../../../../agent/src/sr2fpga_agent/prompts.py#L168)可记 latency/II | 元数据存在，不等于已经有自动兼容性推导、全局容量保持或采样点保持 |

这些是代码与现有公开条目的事实，不能把参考实现的选择升级成用户的唯一规范。也不能将“未写固定延迟”解释为任意延迟变化已经被允许。下文都是有条件的设计，没有将它们写回任务或替换旧分母。

本轮不继续给 FIR 线性重组、sat-node 分区、局部连接枚举换名字；也不将固定正常函数的 checker 升格为已实现的义务推导器。

## 2. 候选 A：保持逻辑退休点和总容量的原生读相位适配

### 2.1 真实问题与明确规则

相同的 FIFO 抽象队列行为可以有两个原生读口；它们不保证在 UART 的全部外部输入轨迹下行为相同：

- **show-ahead：** 非空时当前 head 已在 dout，consume/pop 才推进指针。
- **registered response：** 一次合法 read request 推进队列，数据在下一拍响应；请求时刻的 dout 不代表被取走的 head。

它们可以实现相同的队列操作序列，但不自动具有相同的周期行为。UART 现 top 依赖前者：若仅替换同名、同宽 FIFO，父层可能在响应前启动 TX，并发出旧值。这个风险来自实际读相位与消费者取数关系，不是算术分区。

更强的限制是 **UART RX 没有 ready，不能由 adapter 反压**。即使总逻辑容量始终为 4，registered read 造成的额外启动或字节间隙仍可能推迟出队，使某个 RX 字节到达时从“不满”变成“满”，改变被丢弃的字节集合。因此“发送顺序不变”或“只有一拍差”不足以推出顶层事务等价。目录的 no-drop 标签没有给出量化的溢出/输入速率条件；不能暗加“永不溢出”环境假设，也不能将原有限 FIFO 宣称为能接受任意输入流。

**候选新增交接规则：原生 dequeue 与系统逻辑退休分开记账；未被下游实际接收的 pending/held 字节继续占用原系统容量。** 适配不是只给 valid 延后一拍。否则把一个 FIFO head 提前读到新 adapter 寄存器，会把 4 字节队列变成事实上的 5 字节队列，改变满时输入行为。

程序应仅从预先接受的原生协议 profile、容量与外部行为约束推导 wrapper/拒绝结果；不能从生成后的错误补写协议。输入不需要 FIFO 内部 RTL，但 profile 必须说明 read 的接受事件、响应时间、是否可停顿、何时推进存储，以及满/空的同时读写语义。

### 2.2 公开输入 → 程序处理 → LLM 职责 → 输出

| 阶段 | 具体内容 |
| --- | --- |
| 公开输入 | 逻辑 FIFO 容量 4；UART 的读字节使用关系；选择 show-ahead 或定长 1 拍 registered native profile；显式的外部时序容许范围；满时并发读写规则。后两项当前还未从公开需求闭合 |
| 程序推导 | 从 native request/response 事件生成 pending 与 holding 状态；在发出不可撤销 read 前预约响应槽；只有槽有容量才允许 issue；将 `native_stored+pending+held` 作为尚未退休队列 token 数；下游 TX 真正接受字节时才减少该数 |
| 组合门控 | 验证没有超订 response slot；总逻辑容量仍为 4；上游接收与满判定仍服从原规则；一个 dequeue 不会重复 issue；无 read response 被 stalled TX 覆盖。若原外部周期要求在 response 前发字节，直接报告该 native profile 不可适配，而不偷偷改变时序 |
| LLM 职责 | 一次生成所选原生 profile 的 FIFO/算术或存储行为；不能自行改 adapter/control scaffold 或选择另一读相位。生成前只得到自己的端口和协议承诺；生成后的局部验证检查它是否兑现 |
| 输出 | 多模块 RTL 的明确 wrapper、native component 接口、端口/事件映射、局部实现义务、组合适用/不支持原因。生成前保证的是“若组件兑现 profile，则 glue 的组合关系成立”，不可能在 RTL 尚不存在时证明候选已兑现行为 |

队列计数是这里的逻辑模型，不是建议修改现有评分。当前没有实现或证明上述转换。

### 2.3 具体正负设计及可区分问题

设计 A0 可以保留当前 show-ahead FIFO 及消费路径。A1 可用 registered FIFO 加 pending/hold adapter，但必须保留 4-token 总容量与原并发满判定，并进一步证明同一外部 RX/tx_enable 轨迹下的接收/丢弃集合和允许的 TX 行为不变；或者由既有明确需求许可其差异。仅许可“输出可晚一点”仍不够。若顶层要求原发送周期，A1 更可能不可用；预先拒绝就是正确结果。**当前没有这些公开许可或全轨迹保持证据，因此 A1 不是已经合格的保持顶层功能变体。**

两个明确负设计：

1. **相位错误：** 请求发出后立即以旧 dout 启动 TX。接口名/宽度和普通层次图均合法；例如刚入队字节 B，而输出寄存器仍为旧 A，父层发送 A。
2. **容量错误：** adapter 预取一个字节后只用 native FIFO 的空位数接收上游。此时 held=1、native_stored=3 已占满 4 个逻辑 token，再接收一个会使逻辑队列变为 5。无须等候模型偶然制造这个控制才能定义它。

第一项能区分只做端口/延迟标签检查的流程；第二项还能区分忽略逻辑退休点的预取 wrapper。它们**不能**区分候选和正确的标准 FIFO adapter/credit 编译；这必须作为强对照。

### 2.4 成熟强替代和最小新增机制

本轮核对 [CIRCT ESI 官方文档](https://circt.llvm.org/docs/Dialects/ESI/)的 channel signaling、dataDelay、FIFO/valid-ready wrap/unwrap。它已经显式表达协议种类及控制后数据到达时间，不只是连同宽 wire。文档自报多处陈旧，本轮未固定源码 SHA、未运行 ESI；不能声称当前具体 lowering 已自动保持本例 4-token 语义。

公平基线应获得**同一个 native profile、容量 4、退休点、同时读写规则与外部时序要求**：

- 用 ESI 式 channel 与标准 registered-FIFO→canonical-stream adapter，外加同一全局容量记账；不剥夺其 credit 信息。
- 用完整可执行 IR 明写 request/response/holding 状态和事件；任务数学不需要重写，但显式控制工作量应实际记录。
- 用一个小型、可复用、两原生模式的标准 queue adapter 模板；模板接受同样元数据，不按候选手写每份父 RTL。

在原生 mode 只有这两种、容量固定且同一 wrapper 可复用时，标准模板很可能同工同能。**可研究的最小系统增量**只剩：一份原生行为承诺同时生成模型接口、容量/相位 glue 与局部/组合义务，可靠处理不可适配情况，减少实际手工重复及误接。不能把 credit 或 FIFO 时序本身叫新算法。

最小设计边界是两种无取消、单 outstanding 读 profile；不碰 AXI、多时钟、乱序、可变响应延迟或自动缓存优化。不需要 LLM 选择 controller。LLM 可被标准 FIFO 实现替换，这不否定系统论文，但限定应归功于哪一层。

### 2.5 继续与停止条件

当前只记录为**未合格的条件性系统设计**，不进入实现，也不把 UART 当成已获许可的正例：先查清外部时序、容量和溢出语义。若不能改变原周期，候选需要证明在原 slack 内可适配；如果 RX 不可反压，任何增加间隙的方案还必须处理到达/满判定的差异。不能宣告队列操作序列相同就足够，更不能用新设无溢出假设缩小输入域。

已有 ready/valid stream 的公开 intent 是[跨 stall 保持顺序](../../../../agent/src/sr2fpga_agent/project_generator.py#L2982)，外部输入存在显式接受握手，较适合进一步核对潜伏期自由度。但这仍未证明其任务允许任意新增 pipeline/FIFO；实际单级、逐周期或输入保持承诺必须先核对。不因此自动新增 stream 变体或改变原顶层 ready/valid 轨迹的评价含义。

若标准两模式 adapter 吃同样字段即可产生同样 glue/义务、同样拒绝所有不适配组合，且人工适配/审阅工作量相同，则停止新交接机制主张，留为普通支持功能。若出现真实异构 IP/profile 需求，并可靠减少重复定义、误分类或人工作业，才可能支持有界协议/工具贡献；当前尚无这种成本或使用证据。

## 3. 候选 B：跨潜伏期边界传播显式采样锚点

### 3.1 实际交接问题

vector MAC 的 feature/weight 经两个独立 buffer 配对，第四个 `accept_pair` 时读取 bias。若把乘法器或累加/提交拆成有不同潜伏期的 helper，结果到达时再读取 live bias，可能把晚到的 bias 用于已接受的向量。整个模块图、端口和算术公式仍可以相同，错误来自“读取哪个事件上的值”。

**候选规则：可变调度不能移动用户已经声明的采样事件；跨该事件后的字段使用必须取该事件捕获的副本，并随同一逻辑 token 传递。** 这不是从 `sum(products)+bias` 自动推断出的规则；需要显式承诺，例如“bias 在本向量第四对输入被接受时采样”。实际代码体现这个选择，但当前公开需求没有将其确认为唯一要求。

### 3.2 输入与具体新增处理

公开输入为模块数据依赖、逻辑 accept/commit 事件、每个外部字段的采样锚点、允许的原生 helper 潜伏期/握手 profile，以及顶层周期或事务等价边界。程序应：

1. 标识第四对配对接受事件为向量 token 的采样 fence，不随某个物理乘法器 done 改名。
2. 对跨 fence 的依赖做 closure：例如 bias 必须在 fence 捕获；后段仅使用捕获副本；必要的 last/index 等元信息与数据属于同一 token。
3. 按选定 helper profile 生成寄存、holding 与触发/提交连接；一个 token 的数据和 bias 不能被分到不相关的 ready/valid 时序。
4. 若 helper 的完成/接受次序不支持该映射，或需要用户没有许可的外部延迟/吞吐变化，则返回不支持，不以增加缓冲自动扩大范围。

LLM 只实现既定 helper 行为；program 固定采样和 glue。输出是采样映射、capture 必要性、真实接口和局部/组合义务。原算术及 4 对向量长度不变，不新增精度要求。

### 3.3 实例、反例与强基线

假设该采样锚点已被接受，合法 B0 为当前即时乘加；合法 B1 为较晚得到乘积的 helper 加 token 化 bias 存储。B1 只有在外部行为约束容许时才合法。负 B-X 保留新 helper，却在 done 时读 live bias：某向量 fence 时 bias=1、done 时 bias=9，则输出比该显式承诺多 8；这是分析 witness，不是已发生的模型错误。

本轮核对 [Calyx 官方语言参考](https://docs.calyxir.org/lang/ref.html)的 extern primitive、group、invoke 和控制结构。它已有可以运行若干周期直到 done 的组及 go/done 调用；完整 control 可以明确先 capture、后 invoke、再 commit。不能把它弱化成只标 latency 的格式。CIRCT/ESI 式 typed message bundle 同样可以把 bias/last 与数据同传；普通前端的 capture/closure 与 sideband 传播也是强基线。

公平的最小基线不是手写所有新 FSM：给相同采样锚点和依赖图，普通 free-variable/liveness 分析生成 capture register，再用同一 native helper wrapper 和标准 bundle 保持 token 对齐。若候选的处理也仅是这一步，新增机制没有区别。完整 IR 的显式 control 可以作为第二成本对照，但不能故意拒绝更简单的模板/closure 基线。

### 3.4 当前判定与停止条件

**不建议作为当前新增核心保留。** 原因有两层：采样锚点尚缺公开要求来源；在锚点给定后，目前步骤与普通副本捕获、sideband bundle 和调用调度同工。这里没有提出新的 token 匹配、效果分析或 proof-composition 规则，也没有省工证据。

若未来真实任务已有多个明确采样锚点，普通前端必须重复手写而候选能可靠导出跨模块义务，可以研究交接成本；仍要同时给 closure/template、完整 Calyx 式 control 与标准 elastic bundle 相同信息。不能把未规定 bias 时刻的任务偷偷改成 snapshot 语义，也不能只因两份生成 RTL 具有不同潜伏期就宣称发现新错误。

## 4. 总裁决与交付边界

| 候选 | 相对旧算术/连接候选的新问题 | 当前资格 | 不可绕过的强对照 |
| --- | --- | --- | --- |
| A：退休点/容量保持的读相位适配 | 原生 read request/response 与系统 consume 不同相位，适配会改变 token 存放位置、容量及满时接收集合 | 一个真实交接点；RX 不可反压、时序/溢出许可和保持证据未闭合，UART 不是合格正例 | 同 profile 的标准 FIFO adapter、credit 记账、ESI 式 channel 和完整控制 IR |
| B：显式采样 fence 的 context 传播 | 不同潜伏期下 live sideband 的读取事件迁移 | 需求锚点缺失，且目前落入普通 capture/bundle 编译；不保留核心 | 普通 closure/capture、Calyx 式调用、typed token bundle |

本轮没有声称新的 adapter、credit、go/done、liveness 或 closure 算法。成熟原语不自动否定系统/协议贡献；决定因素是一个真实输入下新增了什么交接保证、减少了什么重复工作，能否与具体同信息强替代区分。当前没有这些实证，因此不推荐为满足“新机制”标签直接开发新 DSL 或调用更多模型。

没有把上述候选采纳成任务规则，没有修改 oracle/checker/评分或正文；没有实际实现 wrapper、capture、协议证明或候选生成，也没有新增性能分母。本文只核对公开源代码、目录标签与两项官方文档；Calyx/ESI 本地运行和完整实现资格均未执行。
