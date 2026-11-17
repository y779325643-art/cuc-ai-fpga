# 三个 LLM 开发 case 的覆盖与下一增量

本页依据 2026-11-05 路线 A 工作区的实际 task、oracle、reference、harness 与测试源码编写。分支为 `codex/paper1-ai`，起始 HEAD 为 `e20dfd2ce46c5690767e30cb629fb5c58aff073a`；未提交实现属于审阅对象。本次只新增本说明，没有运行测试、模型或 EDA，也没有修改任务语义、受信评测、评分或研究假设。

研究定义由 [v2.3 案例修订](../specs/2026-10-28-sr2fpga-paper1-llm-case-amendment-v2.3.zh.md)和 v2.2 基础方案决定。本文是开发覆盖导航，不是资格报告。已有实际运行见 [10 验证记录](10-validation.md)，其环境、源码版本和历史结果保持原范围；不能从“这里有测试函数”推断当前工作区已经重新通过。

## 如何读覆盖状态

- **已实装**：有公开义务、数学实现或检测代码，能定位具体路径。
- **有回归源码**：存在主动构造输入、反例或真实工具测试；本页没有执行这些测试。
- **仍待补强**：现有固定调度或测试没有单独建立该项检出／误拒绝证据，不等于已发现实现错误。
- **范围外**：当前 profile 明确排除的能力，不能通过增加一个测试悄悄变成任务要求。

通用 PC checker 检查的是**声明之间**的 shape、量化、布局、序列与连接关系。`compute` 声明不证明数学实现；实际算术、背压、复位和 cache 生命周期仍依赖执行及独立 oracle。三套 oracle 只共享公开常量，不导入参考 RTL 状态机，但仍需用手算、不同实现与变异检查共同避免同源错误。

## 固定配置与结构压力

| 家族 | 当前固定 profile | 手写 PC 控制的结构 | 有辨识力的义务 |
| --- | --- | --- | --- |
| QKV | T2、Din5、Hq4、Hkv2、D3、lane2；输入6拍，Q16/K8/V8拍 | `InputBroadcast`＋三投影，共4个行为 unit | 三分支恰好一次、不同 head 形状、非零 zero point、head-local tail、各路独立背压 |
| Attention | Hq4、Hkv2、D3、capacity4、lane2；Q8/K4/V4/context8拍 | 一个结构 wrapper＋单个 `CachedDecodeAttention` 行为 unit | 持久历史、GQA组索引、原子收齐／追加、整数 softmax profile、满额与 reset 失效 |
| FFN | T2、Din5、Dff7、lane2；输入／输出各6拍 | `FfnInputFork`、`FfnGateUp`、`FfnFuseDownResidual`，共3个行为 unit | gate/up/residual坐标与token配对、LUT、分阶段重定标／饱和、流控制 |

结构来源：[QKV reference_design](../../agent/src/sr2fpga_agent/tasks/llm_qkv/task.py#L128)、[Attention reference_design](../../agent/src/sr2fpga_agent/tasks/llm_attention/task.py#L106)、[FFN reference_design](../../agent/src/sr2fpga_agent/tasks/llm_ffn/task.py#L133)。这些模块数量属于手写控制，不是候选必须照抄的隐藏拓扑。

Attention 的单行为体能施加状态和数值压力，却很少产生多个计算模块之间的集成关系。它不能单独强力支撑“确定性构建改善跨模块组合”的机制解释。应分别记录候选的实际分解与错误类型；不能为了制造组合收益而要求所有候选复制参考模块数。

## QKV：已有覆盖与缺口

| 义务 | 已实装与回归源码 | 仍待补强 |
| --- | --- | --- |
| Q/K/V形状与公开边界 | [task.signatures](../../agent/src/sr2fpga_agent/tasks/llm_qkv/task.py#L57)；`test_qkv_public_contract_and_head_shapes`（[测试33行](../../agent/tests/test_sr2fpga_llm_qkv.py#L33)）查Q=[2,4,3]、K/V=[2,2,3]及公开面 | 将同位宽异轴序、异scale等已有通用checker反例，与该case的声明／真实行为变异对应起来；不能把schema通过算数值正确 |
| centered MAC、bias、zero point、RNE、饱和 | [evaluate_token](../../agent/src/sr2fpga_agent/tasks/llm_qkv/oracle.py#L11)用Fraction；`test_zero_point_and_asymmetric_impulse_hand_goldens`（[49行](../../agent/tests/test_sr2fpga_llm_qkv.py#L49)）与`test_independent_signed_divmod_projection_and_saturation`（[63行](../../agent/tests/test_sr2fpga_llm_qkv.py#L63)）有手算、不同舍入实现、随机和极值 | 当前未用计数断言证明Q/K/V各自覆盖正负半ties、奇偶商、两侧饱和及“先加zero point再饱和”的差别；应构造能区分错误次序的定向向量 |
| T,H,D遍历、lane／head尾拍 | `test_head_tails_and_physical_byte_goldens`（[95行](../../agent/tests/test_sr2fpga_llm_qkv.py#L95)）；pack/unpack查18bit、mask及无效lane raw0 | 补真实RTL的head交换、token交换、lane交换、跨head紧打包等分离变异；现有错误trace主要翻转一个数值bit，不能代表所有布局错误均已资格 |
| 分支背压、恰好一次广播、保持valid/payload | [check_trace](../../agent/src/sr2fpga_agent/tasks/llm_qkv/harness.py#L29)分别维护三路队列与stalled值；`render_testbench`三路采用不同周期的最多两拍stall；真实RTL测试在[204行](../../agent/tests/test_sr2fpga_llm_qkv.py#L204) | 固定周期不是全部合法调度。优先补各分支单独慢两拍、不同相位、先后完成、输出重发／漏拍的检测反例；遵守公开环境的最多两拍stall，避免用无限阻塞误判正常完成 |
| partial-input／pending-output reset、合法token级输出 | `test_qkv_token_streaming_reference_hdl_does_not_deadlock_reset_probe`（[209行](../../agent/tests/test_sr2fpga_llm_qkv.py#L209)）使用真实按token输出控制；pending probe并发送输入，任一路输出出现后取消 | 已有全frame与token级控制是正面覆盖；仍缺每条分支分别处于独特进度时的reset位置扫描，以及reset后重发／残留的逐义务变异 |
| 结束与最后一拍时限 | `test_complete_trace_checks_output_and_final_deadline_boundary`（[132行](../../agent/tests/test_sr2fpga_llm_qkv.py#L132)）查513/514绝对cycle边界、损坏输出及伪PASS；其首次offer在cycle1，对应差值512/513 | 补缺TRACE_END、重复结束、输出数量错误、stall期间valid撤回等单独反例，确保每条检测分支有可定位证据 |

## Attention：已有覆盖与缺口

| 义务 | 已实装与回归源码 | 仍待补强 |
| --- | --- | --- |
| GQA组映射、真实持久cache | [DecodeOracle](../../agent/src/sr2fpga_agent/tasks/llm_attention/oracle.py#L37)保存K/V历史；`test_hand_golden_two_groups_persistent_cache_reset_and_capacity`（[58行](../../agent/tests/test_sr2fpga_llm_attention.py#L58)）核首token、均分权重、reset和capacity；`test_independent_random_math_includes_score_clipping_and_old_token_dependence`（[92行](../../agent/tests/test_sr2fpga_llm_attention.py#L92)）不同数学实现核对并区分旧历史／两组 | 补`qh%2`等错误组映射、只用最新token、重复append、提前丢历史的RTL变异检出；数学oracle互比不能替代硬件变异资格 |
| score clipping、LUT、ratio RNE及宽度极值 | [numeric facts](../../agent/src/sr2fpga_agent/tasks/llm_attention/task.py#L53)固定整数profile；`test_signed_rounding_examples`（[54行](../../agent/tests/test_sr2fpga_llm_attention.py#L54)）；`test_reference_hdl_ratio_extremes_with_denominator_1024`（[189行](../../agent/tests/test_sr2fpga_llm_attention.py#L189)）分别覆盖V=-128/127 | 极值测试覆盖分母1024和AV两端，未独立证明所有LUT索引、score clip两侧、AV ratio正负半ties都在真实RTL出现；应记录触发值及能区分的错误规则 |
| 三输入原子收齐、到达次序 | [check_trace](../../agent/src/sr2fpga_agent/tasks/llm_attention/harness.py#L47)只在收齐8/4/4拍后更新oracle并允许输出；[render_testbench](../../agent/src/sr2fpga_agent/tasks/llm_attention/harness.py#L161)交替Q→K→V与V→K→Q | 公开规则允许三个完整输入流任意次序，当前只用两种顺序；优先覆盖其余四种整流顺序。部分输入取消目前仅送一拍Q，补K-only、V-only及两流收齐第三流未齐时reset；是否允许更细beat交织，先按公开规则解释，不擅自增加义务 |
| 满cache反压、reset失效、连续decode | 固定schedule四次append至满，检查全部input ready为0，再reset后两次；真实RTL入口`test_manual_reference_hdl_checks_persistence_gqa_stalls_and_resets`（[184行](../../agent/tests/test_sr2fpga_llm_attention.py#L184)）及PC-emitted入口（[197行](../../agent/tests/test_sr2fpga_llm_attention.py#L197)） | 补满额后的合法无输入观察、不同reset时机及reset后首值不受旧存储影响的变异；当前没有滑窗／分页／prefill或请求交织要求，不能以这些缺失扣分 |
| offered输出、tail、保持与256-cycle完成 | scoreboard逐个offered beat比对，accepted才推进；`test_pack_goldens_and_invalid_tail_fail_closed`（[112行](../../agent/tests/test_sr2fpga_llm_attention.py#L112)）；期限/伪PASS/损坏输出（[142行](../../agent/tests/test_sr2fpga_llm_attention.py#L142)） | 同样需要每个协议检测分支的负控制，尤其未收齐提前输出、阻塞时payload改变、输出后又接受下一调用、reset遗留；避免把数学正确当握手资格 |

逻辑cache失效只要求valid length归零，不要求物理memory逐字清零。当前attention把cache、QK、softmax近似与AV都放在同一个行为体，PC的`states`/`compute`只描述承诺，不能静态证明实际存储和状态转移。

## FFN：已有覆盖与缺口

| 义务 | 已实装与回归源码 | 仍待补强 |
| --- | --- | --- |
| SiLU表及分阶段整数语义 | [evaluate_token](../../agent/src/sr2fpga_agent/tasks/llm_ffn/oracle.py#L21)明确gate/up先RNE并饱和、LUT、product RNE并饱和、down RNE后加residual再饱和；`test_frozen_lut_matches_its_public_generation_rule`（[56行](../../agent/tests/test_sr2fpga_llm_ffn.py#L56)）用Decimal核256项表 | 表项全部核对不表示RTL实际查到全部表项。补gate/up交换、删stage saturation、提前饱和down、residual加两次等差分向量与硬件变异 |
| 正负half ties、bias、残差顺序与范围 | `test_signed_rounding_half_ties`（[67行](../../agent/tests/test_sr2fpga_llm_ffn.py#L67)）、手算（[71行](../../agent/tests/test_sr2fpga_llm_ffn.py#L71)）、不同列式实现与INT32范围界（[83行](../../agent/tests/test_sr2fpga_llm_ffn.py#L83)） | 当前math检查覆盖明确，仍需逐stage触发记录，证明测试能区分“down先sat后加x”等相近错误实现；不要只增加随机seed而不检验区分力 |
| token／channel配对 | 列式crosscheck含交换两个token的等变性；reference fuse按各自counter接收gate/up/residual后按相同坐标计算（[reference35行起](../../agent/src/sr2fpga_agent/tasks/llm_ffn/reference.py#L35)） | 交换token性质只验证oracle。补真实行为中residual错一token、gate/up错一channel或跨调用遗留的变异；黑盒最终输出能检出错误，不要求暴露内部调试信号给候选 |
| 内部独立流与外部背压 | `FfnInputFork`独立pending；`FfnGateUp`独立gate/up counter；外部harness有output周期stall及两个取消probe | 集成reference的fuse常同时接受gate/up，现有driver主要阻塞最终output。缺直接强制features/residual、gate/up非对称ready的unit级资格；不能用实现里“有两个counter”代替已证明独立背压 |
| 合法token输出、同调用输入输出重叠、禁止跨调用交织 | `test_monitor_accepts_token_streaming_with_optional_input_output_overlap`（[141行](../../agent/tests/test_sr2fpga_llm_ffn.py#L141)）为合成合法trace；提前下一调用拒绝（[165行](../../agent/tests/test_sr2fpga_llm_ffn.py#L165)）；pending-output reset probe并发送输入 | 合法流式FFN目前主要是monitor trace正控制，参考RTL仍全frame缓冲；可补一份不同调度的合法RTL控制，验证driver不会因架构选择误拒绝 |
| trace完整性与512-cycle期限 | 末拍时限及伪PASS反例（[129行](../../agent/tests/test_sr2fpga_llm_ffn.py#L129)）；真实RTL测试（[189行](../../agent/tests/test_sr2fpga_llm_ffn.py#L189)）检查三完整调用、18输出、3reset/2cancel，并损坏真实输出trace | 补漏拍／重拍、hold撤回、取消后旧结果等分别归因的负控制；执行环境故障应保留为工具状态，不能作为数学失败率 |

## 共同覆盖不能被解释成什么

公开准备回归 [test_prepare_writes_public_inputs_without_reference_or_tool_execution](../../agent/tests/test_sr2fpga_llm_suite.py#L29)检查资产／需求／target／capability和模型零调用；源码快照测试在[80行](../../agent/tests/test_sr2fpga_llm_suite.py#L80)。这能支持数据职责和来源约束，不等于所有OS访问隔离已资格。prepared public不得加入oracle、harness、刺激、期望输出或手写reference作为模型答案。

同位宽异layout的通用静态反例见 [test_equal_width_tensor_layout_conflict_rejected_but_local_rename_allowed](../../agent/tests/test_sr2fpga_pc21_semantic_checker.py#L174)，关系支持见[314行](../../agent/tests/test_sr2fpga_pc21_semantic_checker.py#L314)。这些回归不证明真实RTL遵循其声明；两端共同声明错误或body内部错算仍可能静态放行。下一覆盖表必须把“声明变异”“行为变异”“合法不同实现”分别记录，不能用一个总通过数混合。

三个固定profile不是三个具有统计能力的任务总体。换weights、尺寸、措辞或随机seed不能自动建立独立design cluster；新增案例应先说明来源与独立性，再考虑样本规划。当前尚未完成family mutation qualification、正式split、完整资源／隔离资格和物理证据。本页不把已有开发测试晋级为这些资格。

QKV输出的scale／zero point与attention输入不一致，QKV一次两个token与attention单步append的调用边界也不同；FFN仅为同输入残差`FFN(x)+x`。目前没有可直接拼接的decoder，RoPE、RMSNorm和真实checkpoint等价性均在范围外。串接需要另立公开数值转换、调用与整体任务规则，而不是直接连接相同18bit端口。

## 下一增量的可执行顺序

1. **先让已有检查可逐条反证。** 从上述测试入口补最小合法／错误trace对，覆盖hold、tail、结束、最后拍期限、取消与重发。每项写清对应公开fact、期望检出阶段和允许的合法替代实现；先做不调用工具的monitor／整数回归。本页没有执行这一步。
2. **补定向数值区分力。** 在当前固定profile内寻找能区分正确与错误规则的向量，记录正负ties、饱和两侧、LUT索引和stage；先独立手算／不同整数实现核对，再作为受信开发suite候选。找不到区分向量应记录不可辨识，不编造命中率。
3. **补调度自由度。** Attention补六种完整流次序与各类partial reset；QKV补分支不对称的合法有限stall相位；FFN先补unit级非对称接受与合法流式控制。保持现有完成时限和环境假设，不因测试不通过放宽它们。
4. **建立真实RTL变异的资格清单。** 从组映射、持久历史、量化次序、坐标配对和握手中选可执行非等价变异，同时保留合法融合／分解正控制；区分编译失败与语义检出。修改harness/oracle前说明文件范围、研究影响和新版本绑定；旧记录不覆盖。EDA验证属于后续明确开发执行范围，本页未执行。
5. **再补任务来源和组合压力。** 先选一个有公开来源且确有跨模块义务的开发子系统，写清它与当前profile的数值／状态差异。Attention可研究自然分解的替代控制，但不强制候选拓扑、不把模块数当复杂度。通过资格与来源审计后，再提出独立簇／配置和预算方案；不据本页启动campaign。

以上只推进案例说明、覆盖资格与对照可解释性，不引入Veri-Sure的修复策略，也不改变M0–M5及两个主比较。若需查看数学机制和参考数据流，继续阅读 [05 LLM案例](05-llm-cases.md)；操作命令以各case README和 [任务入口](../../agent/src/sr2fpga_agent/tasks/README.md)为准，执行前核对真实工具和副作用。
