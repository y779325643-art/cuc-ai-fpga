# N36：作者输出样本、生成表示与请求绑定

日期：2026-10-21。状态：**取得新的作者工件及实现路径，未建立新方法核心。** N35已完成C34停止裁决，本轮不恢复该案。研究者分工核VeriGraphi公开输出和一篇新近表示研究，主审独立读关键原文、工件与计分入口。新增证据改变后续案例准入：同目录文件不能自动视为完整生成轨迹，生成器正确也不能替代请求绑定。

先查ResearchVault Notes：配置所指`02vault/_index`不存在；对Notes按题名/标识搜索未命中这两项，未扫描全文库或修改Vault。随后直接核作者/官方来源。没有新增被测生成、训练、HDL、solver或作者框架运行；下述JSON盘点是静态文件分析，不是候选实验。

## 1. VeriGraphi：新增公开输出，不等于生成器实现已取得

[官方最新版本仍为v2，2026-04-19](https://arxiv.org/abs/2604.14550)。相关完整方法有HDA、逐模块生成、编译反馈和装配；Algorithm 1将parent、child RTL和CONNECTS交给CodeAssembler。§IV-A成本表将Hierarchy Analysis标为skipped，§V干预数是每模块最大修复计数，不是全项目总数；这些不能认证实际跳过HDA，也未列具体修复。[方法、成本与指标定义](https://arxiv.org/html/2604.14550v2)

新取得作者[输出样本仓库](https://github.com/SazzadSowmik/VeriGraphi-output-samples)，固定`4a3d7c6d05a23f7f7feb14efe264c6b522676c67`，提交日期2026-06-22，晚于论文v2。限定只读三件：KG、顶层、ControlUnit；未读TB、reference、CSV或评价日志。生成器、真实HDA检查器以及Assembler的LLM/程序实现仍UNKNOWN，不将样本仓库当生成器代码。

| 固定工件／定位 | 可直接核对的静态观察 |
| --- | --- |
| [KG L269](https://github.com/SazzadSowmik/VeriGraphi-output-samples/blob/4a3d7c6d05a23f7f7feb14efe264c6b522676c67/RV32I_generated/knowledge_graphs/kg_RiscV32I_20260319_081042.json#L269) | CONNECTS把decoder的7bit opcode送到ControlUnit的32bit instruction。宽度变化未给显式变换；不能仅凭此称Verilog必然编译失败，隐式扩展可能合法。 |
| [KG L290](https://github.com/SazzadSowmik/VeriGraphi-output-samples/blob/4a3d7c6d05a23f7f7feb14efe264c6b522676c67/RV32I_generated/knowledge_graphs/kg_RiscV32I_20260319_081042.json#L290) | 目标RegisterFile.pc在同件L23–26被声明为输出；L311–315另一连接将ControlUnit的输入jump_target作为源。属于图内方向与声明不协调，未执行工具诊断。 |
| [顶层 L74](https://github.com/SazzadSowmik/VeriGraphi-output-samples/blob/4a3d7c6d05a23f7f7feb14efe264c6b522676c67/RV32I_generated/rtl/RiscV32I/RiscV32I.v#L74) | ImmediateGenerator和L89–97的ControlUnit实际都收到顶层完整instruction，分别不同于KG给出的decoder.imm与decoder.opcode来源。 |
| [ControlUnit L11](https://github.com/SazzadSowmik/VeriGraphi-output-samples/blob/4a3d7c6d05a23f7f7feb14efe264c6b522676c67/RV32I_generated/rtl/RiscV32I/ControlUnit.v#L11) | 独立局部registers数组在完整文件没有赋值，却被L30的JALR读取；顶层实例未传入RegisterFile的rs1数值。 |

主审独立读三件原文，并在内存解析KG：9个module、9条connects；其中两条端点方向不符自身声明，一条存在上述7→32宽度变化。盘点全部九条，没有将这三项算成功能失败率或笼统称三处非法连接。

**绑定限制：** 两件静态文件来源于同一提交和目录，足以比较文本，却没有确认同一次生成中KG→该顶层的输入/输出绑定、人工改动顺序或论文评价版本。可能有修复后未同步图等其他解释。不能据此宣布CodeAssembler在运行时忽略其真实输入，也不认定论文所报通过结果被本轮推翻。

## 2. JALR是具体语义风险，尚不是可归因的论文失败样本

论文Ref.17所链[ISA v2.1 §2.5，纸页15](https://www2.eecs.berkeley.edu/Pubs/TechRpts/2016/Archive/EECS-2016-118.pdf#page=27)规定目标由rs1值加有符号立即数，再清最低位。主审回核原文：若指令为`32'h000080e7`、建筑状态x1=0x100，所需目标为0x100。当前ControlUnit读取的却是没有建立该状态关系的局部数组，不能从所读文件保证其跟随建筑寄存器值。

这是公开代码上的静态状态传递缺口；没有运行、假定四值仿真结果、强制局部数组值或构造该作者失败日志。完整原始需求到KG的版本也未闭合：论文称238页，而所链Ref.17是133页；页数差不能独立证明用错规格。不能将该单条件当完整CPU测试，更不能直接把RISC-V作为本论文已采纳任务。

普通未赋值检查、接口/端点检查、确定性实例发射以及既有层次IR都是先要面对的强处理。此案例尚未指出超出它们的新增规则；不借它恢复已停止的信息接口可实现性R2或责任切点机制。

## 3. 新近表示研究：核实际入口与结果分母

[arXiv:2610.25881v1，2026-10-19](https://arxiv.org/abs/2610.25881v1)研究ECC表示，包含平铺/参数化RTL、矩阵和配置。完整§III–VII已读：只有few-shot行覆盖四表示；NL为模型改写，真实用户提示留待后续。约千万是可达空间，3584是部署网格，均不是各格实测分母。非法输入检查已存在，不能直接当我们的新gap。[正文与Tables I–IV](https://arxiv.org/html/2610.25881v1)

作者实现固定`thesid16/learn-the-interface@45ce811db11d4204ad74f2b1d19ed94bd2c91162`，2026-09-01，早于论文。协作者核以下三源码；主审独立核run.py和RESULTS.lock，未执行或认证训练快照。

| 实现／记录 | 实际保证与未闭合项 |
| --- | --- |
| [rtlgen/run.py L57](https://github.com/thesid16/learn-the-interface/blob/45ce811db11d4204ad74f2b1d19ed94bd2c91162/src/ecc_train/rtlgen/run.py#L57) | 配置路径按预测宽度生成encoder/decoder。L170–181非配置路径才调用对原宽度参考的两个组合等价检查；配置明确转为另处exact-match计分。不是此入口逐份证明完整时序memory wrapper。 |
| [formal.py L34](https://github.com/thesid16/learn-the-interface/blob/45ce811db11d4204ad74f2b1d19ed94bd2c91162/src/ecc_bench/formal.py#L34) | 组合Yosys miter/SAT；后续cell count是面积代理，不能扩大成完整物理PPA。 |
| [refusal.py L26](https://github.com/thesid16/learn-the-interface/blob/45ce811db11d4204ad74f2b1d19ed94bd2c91162/src/ecc_bench/refusal.py#L26) | 在已知非法输入集，None或非法预测均计拒绝，合法预测计泄漏；不区分解析失败和显式拒绝，不证明逐字段NL忠实性。 |
| [RESULTS.lock](https://github.com/thesid16/learn-the-interface/blob/45ce811db11d4204ad74f2b1d19ed94bd2c91162/RESULTS.lock) | 明示配置metric=config_exact，再经确定性后端推得等价；few-shot四表示各n=12，RAG/copy/LoRA/scratch配置各n=80，部分其他行未直接列n。参数化行记录10/12截断，不把它冒称已证明参数化表示理论上无法压缩。 |

配置精确匹配加相同确定性后端，可以是有效的构造性保证，不要求每份再跑相同SAT；需要保留后端及请求规范化正确等前提。本轮尚未读elsewhere的exact-match调用链或完整wrapper资格，不据此判作者计分错误。它已有实质表示/拒绝研究，论文“开放”或“未覆盖真实用户”本身不能当我们已解决的处理。

## 4. 对本篇的决定与后续资格

当前应分开核：原请求到形式计划的忠实性、形式计划到RTL的实现符合、最终顶层功能。三者不能互相代替；这是证据/比较标准，不登记为新算法。本轮取得真实工件差异及明确代码路径，仍没有通过方法增量门的新核心，不新增变体、开发或模型pilot。

若下一项动机依赖历史生成失败，应优先核可追溯的公开需求、实际计划、首次输出及版本绑定，再判断标准流程具体缺哪步。只有同目录快照、汇总失败或模型自述时，相关因果归因保持UNKNOWN。新设计并非必须先取得历史失败：真实必要任务上的静态区分与明确额外处理仍可用于立项，但不能冒称实测收益。不继续靠更多类似管线论文、接口改名或小控制例扩大候选。用户的少量结构变体许可保留，外部CPU/ECC任务尚未采纳；N24不同系统定位也未由本轮替用户选择。

SCI初稿与新核心仍是未完成的整体目标。既有停止决定、12原生/12父构造、16局部证明、N20结果、三版正文及现行研究定义保持原状。

## 5. 本轮验证

独立只读审查核三份VeriGraphi工件、run.py及RESULTS.lock，未发现限定范围的Blocker/Major/Minor；没有复核论文全文、ISA、历史生成谱系、elsewhere计分链或完整wrapper。论文相关完整方法及ISA所引段由主审核读，不以此认证未取得的运行绑定。

主审实际文件检查通过：四文档228个本地链接可达、无尾随空白；清单N1–N36连续且均六列，三版正文SHA与轮前一致。Git仍为develop、HEAD e20dfd2ce46c5690767e30cb629fb5c58aff073a，状态计数D108、M56、RM5、R1、未跟踪39不变。本轮只维护该报告及唯一清单/导航，不暂存、提交或执行远端写入。
