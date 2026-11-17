# KV-cache decode 的 FPGA 任务规格与三组对照

**状态为待评审的 Route A 开发设计。** 本文提出一个新 profile 和一项独立机制对照。三组结果属于该扩展，Paper‑1 v2.3 的 M0–M5、VPP‑L3 和既定主比较继续按现行协议定义。文中的器件、阈值和样本数是设计起点，须在看到模型结果前用手写参考完成资格检查并确定版本。当前工作只核对源码、约束和算术边界。 [v2.3 修订](../../../docs/specs/2026-10-28-sr2fpga-paper1-llm-case-amendment-v2.3.zh.md#1-当前总体和方法边界) · [v2.2 物理证据规则](../../../docs/specs/2026-09-15-sr2fpga-paper1-research-plan-v2.2.zh.md#14-fpga-物理证据与工作负载来源)

## 1. 现有开发路径

- 现行 `llm_gqa_decode_h4_kv2_d3_t4_v1` 是 `Hq=4, Hkv=2, D=3, Tmax=4` 的固定位精确任务。保留的语义包括三路 ready/valid、原子追加、`qh//2` 的 GQA 映射、稳定指数查表、最终 RNE 与饱和、满缓存反压和复位逻辑失效。旧任务的 256 周期义务属于该固定 profile。 [task.py](../../../agent/src/sr2fpga_agent/tasks/llm_attention/task.py#L42)
- 手写参考 PC 把 K/V 记为 `simple_dual_port`、读延迟 0。RTL 用组合读，每次追加同拍写每个数组的六个标量。checker 解析并求值 memory 描述，emitter 将行为体交给生成端。由此得到的是声明和结构的检查，物理 RAM 端口、读拍和映射仍要独立取证。 [参考 PC](../../../agent/src/sr2fpga_agent/tasks/llm_attention/task.py#L106) · [参考 RTL](../../../agent/src/sr2fpga_agent/tasks/llm_attention/reference.py#L50) · [checker](../../../agent/src/sr2fpga_agent/pc/checker.py#L262) · [emitter](../../../agent/src/sr2fpga_agent/pc/emitter.py#L180)
- 开发 target schema 只接受 `generic_yosys`。运行时以固定 facts、资产、ABI 和时钟／周期配置绑定 oracle，候选上下文目前整体包含 target。L3 实际执行 `yosys synth -top …; stat`。新任务需要新的可校验绑定和候选投影。 [target schema](../../../contracts/pc/2.1/development-target-v1.schema.json#L4) · [候选投影](../../../agent/src/sr2fpga_agent/execution/isolation.py#L56) · [oracle 绑定](../../../agent/src/sr2fpga_agent/execution/evaluation.py#L69) · [L3](../../../agent/src/sr2fpga_agent/execution/evaluation.py#L388)

## 2. 第一份 FPGA 任务卡

### 2.1 三组共享的功能和事务规格

建议新任务 `llm_gqa_decode_h4_kv2_d3_t512_v1`。保持原顶层端口方向、`clk`／`rst_n`、18-bit payload、两条 INT8 lane 及 head 尾拍语义。每次调用收 Q/K/V 各 8／4／4 拍，产生 8 拍 context。保留 Hq4、Hkv2、D3 及原公开 EXP LUT，容量扩大到 **512 个 token**。每个 K 或 V token 有 48 bit，K/V 持久净荷合计 `512 × 2 × 2 × 3 × 8 = 49,152 bit`。

- 每次事务的 Q/K/V 都收齐后才能提交本步 K/V。对本步求值时，`N` 等于提交后的有效长度，范围为 `1..512`。三路可并发或先后送达，各自保持固定拍序，受阻时保持完整 payload 和 valid。合法功能场景中，源在可以提供下一拍时至多暂停两拍，sink 至多连续阻塞两个 offered-valid 周期。上一调用最后一个 context 握手后的下一边沿起，源才能启动下一调用。首版只允许一个未完成调用。接收满第 512 步的输入后，各输入 ready 保持低，直到复位重新允许输入。TB 在满容量结果排空后用保持 valid 的第 513 步探针检查无握手。
- `rst_n` 同步低有效，取消部分输入或未完成输出，使 `valid_length=0`。复位后的第一个 token 从逻辑地址 0 开始。底层数据 RAM 可以保留旧位，所有读必须受有效地址范围约束。槽边界无 eviction、回绕或跨调用交织。
- QK、指数表索引、AV 和最终除法顺序沿用原 profile。扩大容量后 `den=sum(weight)` 范围为 `256..131072`，需至少 unsigned 18 bit。对一个 context 通道，`sum(weight*V)` 范围为 `[-16777216,16646144]`，需至少 signed 25 bit。最小负值取绝对值时用 unsigned 25 bit 或更宽。有效长度需要 10 bit，槽地址 9 bit。QK 单点积及其量化范围随 D3 保持。中间数学范围是规格，RTL 可以用其他安全位宽或等价算法。
- 共同的功能存活边界包括首输入 offer 到收齐 ≤128 周期，以及收齐到末 context 握手 ≤ `64N+1024` 周期。仅对合法服务场景的未取消事务判定，刻意不提供输入或阻塞到复位的探针另按取消语义判。整个 TB 的 watchdog 根据已声明的事务序列和每笔预算生成。旧 `4000` 周期 TB 常量无法覆盖长历史序列。
- 针对历史保留、两组 KV 区分、三路到达顺序、读到最新追加项、接近满容量和复位后地址重用构造定向输入。另用 512 个等分数 token 检查 `den=131072`，令不同 V 通道分别达到 `-128` 与 `127`，覆盖 AV 极值。性能用有差异的公开／私有工作负载，避免全相同数据掩盖漏读历史。

### 2.2 Target profile 与评测策略

建议保留现有通用 target 作为前端兼容配置，用新注册的 FPGA 目标扩展绑定物理阶段。表中字段是拟定语义，尚无可直接投喂的 schema 或配置。

| 所属 | 拟记录的字段与首版值 | 用途 |
| --- | --- | --- |
| FPGA target 公共部分 | `part=xc7z020clg484-2`，`flow=vivado`，`scope=logical_ooc`，`clock_port=clk`，`clock_period_ns=10.0` | 使用仓库已有同型号的工具配置作起点。工具版本、补丁、执行环境和 part 支持在资格阶段查实。 |
| FPGA target 公共部分 | 对除时钟外的顶层输入／输出均施加同一 `clk` 参考的逻辑 I/O 预算，`min=0 ns`，`max=2 ns`，覆盖 payload、ready/valid 和同步复位 | 由可信 XDC 在综合前绑定并贯穿实现。结果的范围是有明确接口预算的 OOC 核，布线后的 I/O 路径按这一逻辑范围报告。 |
| FPGA target 公共部分 | LUT ≤8,000，FF ≤10,000，DSP48 ≤8，全核 BRAM ≤4 个 RAMB36 等价单位。全容量持久 K/V 数据要有可追踪的 BRAM 映射 | 上限是拟资格值。全核的 BRAM 预算含暂存、复制、FIFO 和查表，K/V 归属另证。`RAMB36E1 + 0.5 × RAMB18E1` 按原语数计算，另留两种原语原始数与占用 tile 数。 |
| FPGA 性能要求，绑定到 target | Q/K/V 同时给出各自第一拍，随后各路有数据便持续 offer，sink 一直 ready。`N∈{1,16,128,512}` 时，输入收齐到首个 context 握手 ≤ `16N+384`，到末个 ≤ `16N+400` | 输入收齐后开始计数，四个 N 点都必须满足。公式给 RAM 读取、流水和精确归一化留余量。另报从首个输入 offer 开始的总周期。 |
| 可信评测运行策略 | 绑定 Vivado 实际版本、综合／布局布线 directives、同一受信 XDC、报告解析版本、源码和工具产物哈希、stage 超时和线程配置 | 决定怎样复现评测。隐藏向量、用于归属判定的内部观察记录和原始工具诊断由可信端持有。候选提供 RTL/FPP，XDC 和 Tcl 由评测端生成。 |

候选参考架构可将每个 K/V token 打成 48 bit，一份 K 存储、一份 V 存储，以同步读实现。7 系列 RAMB36E1 的 simple dual-port 形态支持 `512×72`，因此两份 `512×48` 在容量／端口上可分别容纳于一个 RAMB36E1。这是资源预算的设计依据。每个 head 的 QK、exp 和 AV 三趟扫描各约 `N` 拍，4 个 head 约 `12N`，3 路乘法器可在 QK 和 AV 间复用。12 个通道若各用最多约 25 拍迭代商运算，约需 300 拍，再计同步读及流水排空。参考设计可按 head 复用 score／weight 暂存。原 EXP 表的整数权重经过舍入，采用在线 softmax 或近似倒数的候选也须保持位精确输出。`16N+384` 仍须用真实参考和工具验证，包括 `N=1` 的固定开销。实际映射、除法周期、资源余量和 100 MHz 达标均待资格阶段确认。 [AMD UG953 RAMB36E1](https://docs.amd.com/r/2022.2-English/ug953-vivado-7series-libraries/RAMB36E1) · [仓库已有器件配置](../../../agent/configs/current/sr2fpga_line_a_l4_dual_tool_reference.example.yaml#L19)

### 2.3 PC 记录设计的实现承诺

| 写在哪里 | 内容与检查 |
| --- | --- |
| 公共 task facts | 功能真值、量化、形状、事务、有效容量、逻辑复位、通用功能上限。输入端 `signature.source=requirement_boundary`。三组都收到相同事实和 LUT。 |
| PC 2.1 现有字段 | 使用已注册的时钟域、模块／实例、接口、布线、`states` 和 `requirement_map`。候选自己声明所选 memory 的 `element_type`、`depth`、`organization`、`read_latency_cycles`、`read_during_write`、`initialization`、`reset_contents`。同步读参考可声明实际字宽、读延迟和 `reset_contents=preserve`。K/V 合并、拆分和 banking 都可选择。 |
| 拟扩展的可检查义务 | 在版本化的义务记录中关联 `target_profile`、缓存状态／实例、各 bank 的逻辑地址覆盖和角色（K、V 或合并），标记复位、原子提交、读请求到响应的延迟及调度如何消耗该延迟。静态检查角色引用、容量与分段覆盖、端口／时钟一致性和声明的时间关系。若只使用现有 PC 2.1，先以注册 sidecar 和可定位检查结果承载新增义务，避免向 closed schema 塞入临时字段。 |
| 独立评测 | TB 检查实际功能、复位、提交、背压和外部周期。内存同步读语义若成为得分义务，由统一的验证探针或网表证据核对响应边沿。目标综合、实际 BRAM 归属、资源上限、物理 slack 都从工具产物取值。PC 声明与实际实现的对应由评测证据建立。 |

接口延迟与存储读延迟是两种义务。`read_latency_cycles` 描述候选的局部实现，外部性能公式比较同一 ABI 上的事件。对缓存所有权、bank 数、每拍并行通道或具体 `RAMB*` 例化保持开放。第一轮可使用共同的可综合推断子集。若允许外部原语或平台包装，应为三组提供相同的公开组件和边界，保持现有隔离。 [PC memory schema](../../../contracts/pc/2.1/design-proposal-2.1.schema.json#L750) · [候选文件与 HDL 边界](../../../agent/src/sr2fpga_agent/execution/isolation.py#L107)

## 3. 三组对照与比较的含义

| 组别 | 第一次调用的输入与计划输出 | 第二次调用与准入 |
| --- | --- | --- |
| **A 功能规格** | 共同 task facts、ABI、LUT 和 FPP 交付要求，输出自然语言设计计划。目标型号、实际时钟、资源门槛和性能公式对模型隐藏。 | 按同一提示模板交完整自由 RTL/FPP。通用工程检查后封存。 |
| **B FPGA 约束文本** | 与 A 相同的功能信息，增加目标表中完整的器件、时钟、资源、BRAM 和性能义务，自然语言计划。 | 与 A 一样交完整自由 RTL/FPP，受同一工程检查。 |
| **C FPGA 约束＋可检查 PC** | 与 B 相同的目标事实，按相同义务 ID 渲染到可检查输入，模型提出 PC 和对应义务绑定。静态判据检查候选的声明，目标约束由可信端绑定。 | PC 合法时交与 B 同样的完整自由 RTL/FPP。PC 拒绝即记该槽前端失败，不追加修复机会。 |

- A→B 估计**公开目标信息的价值**。评测端仍在同一 FPGA 上测试 A，其目标不达标表示这次产物的物理结果。B→C 估计**结构化表示加静态准入**的联合增量。三组共同使用计划→整包生成，两次逻辑模型调用为上限。首轮统一无反馈修复并采用自由整包输出。C 的计划和最终 RTL 之间的可核对对应单列为机制证据。三组的联合通过使用同一个独立评测器。若需要分离表示与检查，可另行冻结同一 PC 的 checker 诊断开关对照。
- B/C 用一份目标事实清单逐条对照语义，包括公式、场景和预算。C 的类型、字段和检查规则是方法处理。B 可看到相同义务的可读定义与合规的设计选项，三组都不提供手写参考、黄金测试台或私有报告。为 A 构建独立可审计的候选可见投影，在计划和 RTL 两次调用上均检查；可信 oracle 的绑定仍使用完整评测权威。
- 三组在每个配对块使用同一公开功能输入、相同模型／版本、解码配置、总输入及输出 token 上限、单次输出限额和 EDA 机会。记录实际 token、工具阶段、停止原因和用时。C 的额外结构输入计入预算。三组在隔离会话中按预声明调度随机化并平衡顺序，最终 FPP 先封存，后跑共同私有验证与物理阶段。相同 replicate ID 表示配对位置。
- 最初建议 **1 个固定 profile × 8 个配对重复 × 3 组 = 24 个候选槽，最多 48 次逻辑模型调用和 24 个器件实现位置**。这是未来开发对照的规模草案，实际费用和工具耗时须以资格结果估计。单个设计簇的重复仅报告该 profile 上的差异。多个 context 长度是同一候选的重复测量。正式效应推断需要独立需求簇并按簇配对分析。

## 4. 统一评测、证据和分母

| 阶段 | 执行与判定 |
| --- | --- |
| 功能与协议 | 可信 TB 逐拍观察四路 ready/valid，由 Python oracle 按实际接受的 Q/K/V 更新缓存和计算结果。检查端口、尾拍、数值、背压稳定、原子追加、满缓存无接受、复位后历史失效及功能上限。公开和私有测试使用同一语义。每组最后只评分同一份封存 FPP。 |
| 周期延迟 | `t_in=max(t_Q_last_accept,t_K_last_accept,t_V_last_accept)`。`L_first=t_context_first_accept-t_in`，`L_last=t_context_last_accept-t_in`。按时钟上升沿编号相减，同边沿差为 0。性能场景 sink 始终 ready，首次有效等于首次握手。对四个 N 点逐项保存值，另报首 offer 至末输出和无插空连续请求之间的接收间隔。固定背压场景另报 offer／accept 和环境等待，避免把外部停顿混入无停顿门槛。只有功能正确且目标时钟达标时，才用 `cycles × 10 ns` 给出约束下的核级时间。 |
| 器件综合与 BRAM | 受信脚本使用 `synth_design -mode out_of_context -part`，按统一层次与工具策略输出 `report_ram_utilization`、层次资源、原语实例及可追踪网表／DCP。对 K/V 的写入数据与地址、读出到 QK／AV 的路径、有效深度、复制／合并和实际 primitive 归属做可复核绑定。计入 K/V 净荷，允许寄存器暂存和有效位。全核 BRAM 计数、`ram_style` 和 PC 声明只能作线索。BRAM 只用于 exp 表或少量 scratch 时，缓存映射义务失败。对融合设计保留盲审与证据不足状态。布线后复核原语清单，资源上限使用最终实现报告。 |
| 布线与时序 | 固定 `opt/place/route`、同一 XDC 和 OOC 核边界。留存 route status、完整 timing summary、`check_timing`、DRC 与最差路径。要求布线完成，setup `WNS ≥ 0` 且 `TNS = 0`，hold `WHS ≥ 0` 且 `THS = 0`，应覆盖的数据／控制端点均受约束，内核不存在未分析的内部时钟端点。约束例外只使用预声明且三组相同的策略。保存评测脚本和工具原始报告的哈希。 |

BRAM 归属先用三份受信控制件验证判定能力，包括真实 K/V BRAM、K/V 用 LUTRAM/FF 但旁路有一个可保留的真实 BRAM、以及 K/V 合并或分 bank 且全部映射到 BRAM。源码和网表归属审查隐藏实验组标签，候选自报映射不计得分。物理路线可复用现有 Vivado 的报告提取思路，需要从当前 FPP 的 `top.module` 和 source 记录解析输入。旧 helper 读取 `top_module` 和字符串列表，当前脚本只采集 max timing。 [旧 Vivado helper](../../../agent/src/sr2fpga_agent/vivado_report.py#L14) · [AMD RAM utilization](https://docs.amd.com/r/en-US/ug906-vivado-design-analysis/Running-the-RAM-Utilization-Report) · [AMD I/O 时序约束](https://docs.amd.com/r/2023.2-English/ug903-vivado-using-constraints/About-Constraining-I/O-Delay) · [AMD 约束覆盖检查](https://docs.amd.com/r/2024.1-English/ug906-vivado-design-analysis/Check-Timing-Section)

- **主要指标**是同一终止候选同时通过共同功能／协议、目标综合、K/V BRAM 归属、资源上限、全部延迟点及 OOC 布线时序的比例。分别报告 A、B、C 全部预排位置以及 `B−A`、`C−B` 的配对百分点差。把逐阶段通过率、失败原因、资源和按 N 的延迟曲线并列报告。配对差附通过／失败不一致对数。小样本只提供描述性结果和不确定性。
- 已确立的工程失败记 0，例如无有效候选、C 的静态准入拒绝、错误结果、映射失败、资源超限或时序失败。更晚阶段若未执行，阶段状态记 `not_observed`。工具环境故障、原始报告缺失或归属审查无法判定，联合结果记不可判并保留具体原因。公布计划分母、未知数和可判配对数。不可判按 `[0,1]` 取值，每个配对差的界限为 `[X下界−Y上界, X上界−Y下界]`，再对全部配对位置平均。候选引起的 timeout 与工具环境故障分别处理。完整性事件单列。
- 如后续预算只允许一部分候选跑布线，先于结果抽定配对块并三组同时保留。报告预选物理块的全分母和功能通过者条件分母。连续 QoR 指标报告其实际测量分母，并优先给出两臂均有可比较证据的配对差。正式实验的阈值、规模和确认性分析独立冻结。 [Paper‑1 计分与证据 §11](../../../docs/specs/2026-09-15-sr2fpga-paper1-research-plan-v2.2.zh.md)

## 5. 开发顺序与资格条件

1. 新增版本化任务绑定，参数化 oracle／harness，并用原 `Tmax=4` 用例做回归。在 `Tmax=512` 上加入满容量、分母与 AV 极值、部分输入复位和旧历史再访问测试。
2. 编写一份同步读参考，先做功能和周期验证，再资格确认目标工具、BRAM 证据判别、约束覆盖与资源阈值。任何阈值修订均在模型生成前记录版本与依据。
3. 接通注册 target、A/B/C 可见输入投影、C 的义务检查、封存、统一物理报告和配对分析。用手写正负控制验证漏检、超限、时序失败和工具不可判能够分开记录。
4. 在资格、工具预算、预声明槽位和权限明确后启动开发对照。可从统计上支持的论文结论仍取决于后续独立设计簇和正式协议。
