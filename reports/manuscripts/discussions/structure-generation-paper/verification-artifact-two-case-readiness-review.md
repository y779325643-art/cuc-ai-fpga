# N43：验证工件审计的两个真实来源与强对照资格

日期：2026-10-22。范围：用户已选择“评审验证工件审计”，本轮只读核两个真实案例及强对照。不开发、不运行模型/HDL/证明器、不改正文、任务或评分。方法仍为[N41系统假设](compiled-monitor-audit-method-review.md)，不是已成立创新。

**结论：找到两个真实交付的断言来源；尚未取得两个经构建资格的审计任务，也未建立相对强对照的新增处理。** 可以具体讨论单时钟有限安全监测器的审核，但不能继承旧纯组合checker资格，或由正确来源存在推出可靠性收益。两例的公开语义、实际端点与配置风险如下。

## 1. 案例一：OpenTitan ROM控制器的错误到告警断言

固定提交为`8fe9809738dc738f50f7011a0c671ccfe5a61020`。它是实际IP中的调用，而不是仅有框架宏或N39的UVM历史任务。

| 项目 | 原件与本轮认定 |
| --- | --- |
| 公开义务 | [rom_ctrl.hjson L170–177](https://github.com/lowRISC/opentitan/blob/8fe9809738dc738f50f7011a0c671ccfe5a61020/hw/ip/rom_ctrl/data/rom_ctrl.hjson#L170)描述异常控制流进入Invalid并触发告警；L215–219说明稀疏FSM。前者给需求线索，后者不单独规定所有故障的响应。 |
| 实际调用 | [rom_ctrl.sv L545–553](https://github.com/lowRISC/opentitan/blob/8fe9809738dc738f50f7011a0c671ccfe5a61020/hw/ip/rom_ctrl/rtl/rom_ctrl.sv#L545)的CheckerFsmAlert_A指向`gen_fsm_scramble_enabled.u_checker_fsm.u_state_regs`，目标为`alert_tx_o[AlertFatalIdx]`。实例和断言均位于`!SecDisableScrambling`分支。 |
| 端点闭合 | [rom_ctrl_fsm.sv L168–174](https://github.com/lowRISC/opentitan/blob/8fe9809738dc738f50f7011a0c671ccfe5a61020/hw/ip/rom_ctrl/rtl/rom_ctrl_fsm.sv#L168)实际实例化u_state_regs；[prim_flop_macros.sv L45–73](https://github.com/lowRISC/opentitan/blob/8fe9809738dc738f50f7011a0c671ccfe5a61020/hw/ip/prim/rtl/prim_flop_macros.sv#L45)展开primitive，SIMULATION分支另用行为寄存器并检查等价，非该分支直接连接输出。不能忽略此区别重建路径。 |
| 实际错误语义 | [prim_sparse_fsm_flop.sv L28–56](https://github.com/lowRISC/opentitan/blob/8fe9809738dc738f50f7011a0c671ccfe5a61020/hw/ip/prim/rtl/prim_sparse_fsm_flop.sv#L28)只在INC_ASSERT时检测枚举未定义状态，否则`unused_err_o=0`。这不是所有综合配置中都存在的物理错误输出。 |
| 检查模板 | [prim_assert_sec_cm.svh L20–40、L67–68](https://github.com/lowRISC/opentitan/blob/8fe9809738dc738f50f7011a0c671ccfe5a61020/hw/ip/prim/rtl/prim_assert_sec_cm.svh#L20)检查上述unused_err_o上升沿后0至30周期内的`alert_p`，默认GATE为0；并在FPV模式另加入复位变化后10周期源错误为0的假设。它不检查持续高错误的每个周期，也不直接证明错误检测本身。 |
| 时钟、复位与工具分支 | [prim_assert.sv L16–17及L102–113](https://github.com/lowRISC/opentitan/blob/8fe9809738dc738f50f7011a0c671ccfe5a61020/hw/ip/prim/rtl/prim_assert.sv#L16)默认clk_i与!rst_ni，按VERILATOR/SYNTHESIS/YOSYS等选择宏实现；[standard宏 L77–82](https://github.com/lowRISC/opentitan/blob/8fe9809738dc738f50f7011a0c671ccfe5a61020/hw/ip/prim/rtl/prim_assert_standard_macros.svh#L77)在posedge采样、disable iff复位值不严格为0时中止。不能将standard分支语义冒充所有工具配置。 |
| 告警链 | [rom_ctrl.sv L507–523](https://github.com/lowRISC/opentitan/blob/8fe9809738dc738f50f7011a0c671ccfe5a61020/hw/ip/rom_ctrl/rtl/rom_ctrl.sv#L507)将checker_alert并入fatal请求，sender接clk_i/rst_ni。看到同一时钟不证明已经处理复位中止、历史初始化或告警握手环境。 |

可讨论的窄参考义务是“指定错误端点的上升沿在有限周期内到达指定告警端点”。**30周期、上升沿解释、复位/初始历史和额外假设，仍须可信需求方独立确认**：Hjson没有独立规定全部这些细节。以实际宏作为抽取对象M，再原样复制成唯一参考R，只能自我一致，不能认证需求履行。若复用宏作可信参考，必须明确其事前信任边界及待审绑定/配置，而不是同时审核宏语义又用它作唯一真值。

本例不证明整个countermeasure、全部故障模型、无效状态检测或物理保护。当前没有自然漏报率、真实缺陷复现或完整编译运行结论。

## 2. 案例二：PULP common_cells的FIFO调用协议断言

固定提交为`e73baaec2ca665cd80c3c384e9258e35242b829c`。[README L114](https://github.com/pulp-platform/common_cells/blob/e73baaec2ca665cd80c3c384e9258e35242b829c/README.md#L114)列cc_fifo为active，L139说明低有效异步复位。当前路径是cc_fifo，不把历史fifo_v3路径当现版本。

| 项目 | 原件与本轮认定 |
| --- | --- |
| 公开义务来源 | [cc_fifo.sv L24–39](https://github.com/pulp-platform/common_cells/blob/e73baaec2ca665cd80c3c384e9258e35242b829c/src/cc_fifo.sv#L24)接口注释限定非满push、非空pop。来源是作者源码注释，未取得另一份独立规范或完整SoC集成合同。 |
| 实际检查器 | [cc_fifo.sv L128–135](https://github.com/pulp-platform/common_cells/blob/e73baaec2ca665cd80c3c384e9258e35242b829c/src/cc_fifo.sv#L128)内联full_write和empty_read，分别为`full_o |-> ~push_i`、`empty_o |-> ~pop_i`。没有另一个bind文件；无外部bind也不意味着无实际观察关联。 |
| 采样和中止 | [assertions.svh L117–127](https://github.com/pulp-platform/common_cells/blob/e73baaec2ca665cd80c3c384e9258e35242b829c/include/common_cells/assertions.svh#L117)展开为posedge clk_i及`disable iff((!rst_ni) !== '0)`。未知复位时也禁用；不能只比较组合布尔式就声称完整SVA等价。 |
| 激活配置 | 模块外层COMMON_CELLS_ASSERTS_OFF，以及[宏L16–29](https://github.com/pulp-platform/common_cells/blob/e73baaec2ca665cd80c3c384e9258e35242b829c/include/common_cells/assertions.svh#L16)的ASSERTS_OFF、SYNTHESIS、XILINX_SIMULATOR、ASSERTS_OVERRIDE_ON影响是否交付实际检查器。只见源码调用不证明某部署启用了它。 |
| 参数与依赖 | 原件默认Depth=8、DataWidth=32、FallThrough=0，另有类型参数、cc_pkg和寄存器宏。本轮不自行选定这些值为正式任务；完整DUT elaboration与只提取检查锥的依赖不同。 |

这是**调用方接口使用**义务，不是FIFO内部数据顺序、满空标志计算或全部功能正确性的证明。在明确二值和相同采样/复位契约下，两条的同周期错误条件分别可表示为`full_o && push_i`和`empty_o && pop_i`；这是静态解释，不是本轮运行结果。需要可信侧先确认参考解释，并保留实际读取端点，不能用当前FIFO可达状态代替开放观察域。

本例目前仅审核通用单元自身的内联交付，未核某SoC的实例连接。正确交付也可作资格正例；“预期正确”仍未经过本系统验证，不能记已通过。

### 2.1 两项目都已交付构建入口

为避免把未读配置误写成项目缺失，两位协作者各再限读一次目录、两份构建清单，主审回核关键段；没有展开TB内容。

| 入口 | 已闭合与仍有边界 |
| --- | --- |
| [OpenTitan rom_ctrl.core L8–32、L58–86](https://github.com/lowRISC/opentitan/blob/8fe9809738dc738f50f7011a0c671ccfe5a61020/hw/ip/rom_ctrl/rom_ctrl.core#L8) | 有RTL依赖、完整IP顶层和工具target；lint默认Verilator并设置SYNTHESIS=true，不能当SVA启用证据。formal顶层是rom_ctrl_fsm，不能直接充当rom_ctrl顶层CheckerFsmAlert_A的完整FPV配置。 |
| [OpenTitan rom_ctrl_sim.core L5–28](https://github.com/lowRISC/opentitan/blob/8fe9809738dc738f50f7011a0c671ccfe5a61020/hw/ip/rom_ctrl/dv/rom_ctrl_sim.core#L5) | 实际sim入口顶层tb、默认VCS，依赖完整IP与rom_ctrl_sva。已找到源级recipe，不代表全部依赖、宏、环境或最终编译工件已审核。 |
| [PULP Bender.yml L13–38](https://github.com/pulp-platform/common_cells/blob/e73baaec2ca665cd80c3c384e9258e35242b829c/Bender.yml#L13) | 导出include，声明依赖和cc_pkg/cc_fifo源顺序；FIFO在not(all(xilinx,vivado_ipx))分支，不依赖formal才加入。未将依赖版本约束冒称解析后的SHA。 |
| [PULP common_cells.core L107–116](https://github.com/pulp-platform/common_cells/blob/e73baaec2ca665cd80c3c384e9258e35242b829c/common_cells.core#L107) | default target使用rtl并暴露COMMON_CELLS_ASSERTS_OFF布尔vlogdefine参数，没有显式default。列出参数不等于默认将其置真；实际定义仍须核命令行和展开。ASSERTS_OVERRIDE_ON也不能绕过cc_fifo外层的COMMON_CELLS_ASSERTS_OFF。 |

因此缺的是**选定交付配置的解析与实际工件资格**，不是没有构建入口。当前没有使用VCS或其他工具，也未声称本地已具备其许可、依赖或同等SVA支持；未来可用前端和完整成本需另核。

## 3. 同范围条件、可复用边界与主要风险

两例在抽象上均可落入单时钟、有限状态、安全监测器，但“单时钟”不自动解决异步disable iff。N41尚未冻结异步复位支持，本轮不暗中采纳它，也不把两例改写为同步复位夹具。若只支持二值，必须明确与四值SVA的结论边界；若需要精确处理未知值与采样区域，应先估算前端工作量。

| 处理 | 可复用基础 | 尚缺／不能免费给予的输入 |
| --- | --- | --- |
| 交付与配置封存 | 既有哈希、状态和来源记录方式；项目公开宏与fileset。 | 具体参数/defines/include顺序、工具版本、所审阶段与实际检查单元清单；源码recipe不是真实编译记录。 |
| 观察绑定 | N41所核Yosys结构/端口/属性接口及源层次。 | 配置后实际层次、位/切片、宏展开与观察身份；优化后缺失的源边不能按名称猜回。 |
| 时间语义 | 标准SVA/自动机/顺序等价后端。 | $rose初态、范围延迟、并发触发、reset中止、工具特有lowering及报告时机的合格适配；当前旧checker没有这些能力。 |
| 参考义务 | 工程文档、接口合同和可复用可信模板。 | 独立确认的细化语义及信任方；不能把实际M全部复制为R，又声称发现了规范符合性。 |
| 合法观察域 | 事前明确的环境约束。 | 实际assume与公开环境的对应、额外收窄检查；不得把所审义务本身加入环境而消除见证。 |

同一个正确DUT在开放观察接口上允许出现反事实错误轨迹，是审核监测器的必要设计选择，不是宣布硬件实际可产生那些轨迹。规范端点原本若共享同一信号，也不能为制造差异而拆开真实别名。

## 4. 强对照必须完成相同工作

主要对照是**可复用的标准监测器语义等价流程**：获得同一可信参考与域，允许自动宏/层次展开、实际观察映射、采样与复位核对、配置检查、监测锥提取，再用标准顺序等价、乘积或SMT比较错误轨迹和报告时刻。不能只给对照裸CLI或错绑定脚本，也不能要求它逐份手写本方法自动生成的共同信息。

另两项可作消融：一是静态端点/时钟/宏启用核对，二是在原DUT正常轨迹上执行已交付检查器。前者可能直接覆盖这些简单工件的多数错误，后者可能掩盖错绑定；都不能作为唯一主要对手。标准流程尚未在这两例执行，本轮不预报其成败或把“原则上可写”当实测完成。

[AutoSVA及既有义务/绑定链](contract-frontend-task-readiness.md#4-最接近的能力已存在贡献须落在具体交接)、[IJCAR2020参考监测器验证及实际工具差分](compiled-monitor-audit-method-review.md#2-正式发表近邻验证参考监测器再检查实际监测器)已约束宽贡献。不同工程项目、SVA语言或来源表本身不足以证明新增核心；成熟后端也不排除有证据的系统贡献。当前需要指出的是**从交付到合格比较的哪一步多完成了可验证处理**，并证明不是手工先填完整映射或强基线同样已完成的步骤。

## 5. 接下来怎样闭合，按依赖推进

这里是只读评审的缺口及进入条件，后续进度仍由[唯一清单](../2026-10-21-structure-generation-paper-checklist.zh.md)维护；不是获准实验配置或新评分定义。

| 顺序 | 输入材料 | 具体任务 | 输出文件 | 验收标准 | 前后依赖 |
| --- | --- | --- | --- | --- | --- |
| 1，本文已完成来源核查 | 两个固定提交、公开义务与实际宏调用 | 闭合实际端点、有限义务、时钟/复位和激活风险 | 本文件§1–3 | 两项可定位真实来源，不当作已验证构建或效果样本 | 用户已选择评审对象；为下一步提供原件 |
| 2，构建及参考仍待资格 | 公开build入口、参数/宏/工具记录；可信需求解释 | 固定所审交付阶段，确认激活检查器；明确R的独立信任、域与细化语义 | 继续补本文件及唯一清单，不创建运行结果 | 可分别指出公开依据、可信补充和unknown；禁用/缺失不得算语义通过 | 依赖1；不以源码清单代替实际编译 |
| 3，区别处理仍待具体化 | 2的同范围输入、现成前端能力与标准对照 | 列可复用链、确需新增的机械步骤及其可反驳条件 | N41方法卡及本文件的后续修订 | 同信息强基线完整；有具体差别或明确只有集成/资格价值，不凭未知成本立项 | 依赖2，先于开发 |
| 4，尚未启动 | 通过2/3的明确支持集与授权范围 | 才考虑最小适配与独立正负资格；再决定是否值得研究可靠性 | 届时按现有artifacts与运行合同留证，本轮无新结果目录 | 人工负控制不冒充自然错误或新增真实来源；全部失败/未知留账 | 依赖2/3及明确开发/执行授权，先于效果研究与正文 |

若30周期或复位/环境语义无法独立确认，就将相应项留unknown，不放宽后声称通过；若新增工作实际只是已有宏展开和miter拼接，且没有实际交付可靠性增量，就保留两例作资格来源，停止扩大该候选。若必须新增大量语言、异步/四态支持，先重新评估最低补工目标。当前不主张人工省工。

## 6. 审查与实际操作边界

两位协作者分别核OpenTitan实际IP调用、PULP实际单元及宏；主审回核实际调用和规范片段，补读primitive与宏分支，未接受命名即证明。另一位工程审查者认为两例是同抽象支持集候选，构建/参考、异步复位和强对照仍未闭合；没有因成熟后端而否决系统研究，也未将“默认正确”记成通过。

全部源码核查通过只读工具；未读测试刺激、golden或隐藏用例，未安装/编译/求解/生成新候选。论文正文、旧checker、旧原始结果和评价口径保持原字节。本轮完成的是来源与方法适用性评审，不是SCI创新或可行性最终验收。

独立工程收尾对方法、参考与强对照边界限定通过，未发现可定位问题；其未重读全部外部源码，不代替主审源核对。主审实际检查七份本轮文档的297个本地链接，均可达且无尾随空白；唯一清单N1–N43连续、各六列。三版正文和checker的四项SHA256与轮前一致；Git仍为develop、HEAD `e20dfd2ce46c5690767e30cb629fb5c58aff073a`，状态计数D108、M56、RM5、R1、未跟踪39不变。没有暂存、提交、远端写入或官方证据晋级；文件检查不冒称工具资格实验。

构建补充合入后，独立审查者另核§2.1与已给原件摘录一致，未发现问题；该次只核新增文字，未展开TB、重读外部来源或执行构建。
