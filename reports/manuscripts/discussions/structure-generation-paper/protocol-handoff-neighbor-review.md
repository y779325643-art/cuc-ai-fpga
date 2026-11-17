# 生成前协议备选协调：有界近邻与传统能力核查

日期：2026-10-21。只新增本文件；未运行模型、HDL、CIRCT／作者框架、安装或实验，未读候选／hidden 内容，不改变研究范围。问题限定为：模型提出模块接口／延迟／编码备选，程序先协调并冻结组合，再生成模块行为。本轮深入两篇LLM工作；传统文献和CIRCT是同信息能力对照，不扩成综述。

**结论：生成前明确接口／事务／时序、接受架构后lowering已有直接先例；弹性握手和缓冲的程序构造更有成熟理论与实现。已读两篇没有建立“有限合法备选→程序协调选择→行为前冻结”的完整具体流程，但这只是未证实的系统假设，尚不能认定创新gap。最需要解决的是备选合同的可信来源、全局可组合性及后续行为遵约之间的交接；名称、字段或先后顺序的变化不够。**

## 1. 主源选择、版本与实现可读性

| 主审对象 | 本轮相关完整方法 | 作者实现边界 |
| --- | --- | --- |
| HINT，`2608.07625v2` | 复用[既有深审](neighbor-deep-review-cppl-hint.md)，重新核对[§3、§4.1–4.2](https://arxiv.org/html/2608.07625v2#S3)、Table1/Fig1–2；[7页PDF](https://arxiv.org/pdf/2608.07625v2)，无单独方法附录 | 再访论文链接的[匿名仓库](https://anonymous.4open.science/r/anonymous-project-612D/)仍未取得可审计树／SPEC／SHA；不能由此断言没有实现 |
| LLM-based Hardware Development with Hierarchical IRs and End-to-End Multi-Agent Workflow，`2608.30659v1` | [官方全文](https://arxiv.org/html/2608.30659v1)，完整§§2.1–2.2、3.1–3.3、Fig2–4；[10页PDF](https://arxiv.org/pdf/2608.30659v1)，无单独方法附录 | 全文未定位作者框架仓库；标识及标题的有界检索未取得作者源码／SHA。方法事实来自论文，不称源码复核 |

先查`PartiRTL`／`Parti-RTL`未定位到足以识别作者、论文版本的主源，故没有据同名结果立项或当作缺失能力证据。本轮选HINT与含明确流控pattern的层次IR；CPPL的既有核查继续有效，不另展开第三项。未读到源码的结论均保留可得性限制。

## 2. 两篇实际把什么放在行为生成之前

| 工作／精确定位 | 约束来源和实际顺序 | 不能据此认定已做／没做的部分 |
| --- | --- | --- |
| HINT §3 Table1；§4.1 Stage0–2，PDF pp.3–4 | task接口／事务／时序先冻结；agent形成可执行架构，经检查接受再lowering，随后比对数据／事务时序；架构变化返回前阶段 | checker不提议架构；lowering是agentic。未见有限备选协调算法，不能据此称其不能选择或实现协议 |
| 层次IR §2.1–2.2、§3.1–3.2，PDF pp.2–5，Fig2–4 | LLM先定Sketch和操作规范：统一in_valid/out_valid、触发条件、单拍／多拍输入及输出pattern；模块验证后再由模型整合顶层控制 | 不能把valid-only接口自动读成完整ready/valid；程序构造的是测试，未建立协议适配器的确定性lowering／联合选择 |

HINT允许所需的latency／staging／schedule承诺，外部目标时序来自预声明规格或参考；它不是只查名字的草图。层次IR也已有协议和层次传播，不能弱化为纯端口列表。两者均有行为后的检查／修复路径，不是本候选的首次无反馈流程。该限制差异本身仍不证明贡献。来源：[HINT方法](https://arxiv.org/html/2608.07625v2#S4.SS1)、[层次IR接口与流程](https://arxiv.org/html/2608.30659v1#S2.SS1)。

## 3. 传统latency-insensitive能力：前提不能漏

Carloni／McMillan／Sangiovanni-Vincentelli 的[作者存档全文](https://ptolemy.berkeley.edu/projects/embedded/asves/dsm/lid/papers/lipTransactions.pdf)是2001年TCAD稿本；本轮读§I与§V，未全审18页证明。§V.B Definition V.5、Theorem V.1（PDF p.12）给stallable计算核的wrapper构造；§V.C（p.13）明确自动shell、relay插入及组合验证。它已覆盖计算／通信分离和延迟可变的组合方式。[出版标识](https://doi.org/10.1109/43.945302)

这里的前提包括核可停顿、协议遵约及按事务序列解释功能。它不授权把有精确外部周期要求的任务任意加延迟，也不从模型一句“支持stall”证明实现真的可停。自动wrapper不是新机制；证明模型生成的核满足该前提，是另一项需实证的交接工作。

## 4. CIRCT源码抽核：已有实际lowering，不只是可表达

固定`llvm/circt`提交[`26b9edcbdada0038f3918d0e198031fdc6c856e7`](https://github.com/llvm/circt/commit/26b9edcbdada0038f3918d0e198031fdc6c856e7)（2026-10-21）。只读下列定义、转换及相关rationale，未编译运行。官网ESI文档自警告部分陈旧，因此具体能力以下列固定源码为准。

| 实际能力 | 固定源码定位 | 输入已经承诺什么／不能外推什么 |
| --- | --- | --- |
| 类型化通道有ValidReady、FIFO、ValidOnly及dataDelay | [ESIChannels.td L33–85](https://github.com/llvm/circt/blob/26b9edcbdada0038f3918d0e198031fdc6c856e7/include/circt/Dialect/ESI/ESIChannels.td#L33) | ValidOnly要求接收方接受，不能随意当可背压；dataDelay是事务控制到数据的延迟，不是任意模块算法latency |
| 按已选signaling策略lower模块端口及实例 | [ESILowerPorts.cpp L45–72](https://github.com/llvm/circt/blob/26b9edcbdada0038f3918d0e198031fdc6c856e7/lib/Dialect/ESI/Passes/ESILowerPorts.cpp#L45)、[L213–227](https://github.com/llvm/circt/blob/26b9edcbdada0038f3918d0e198031fdc6c856e7/lib/Dialect/ESI/Passes/ESILowerPorts.cpp#L213) | 不是自动从未知module body推断它真正支持哪种协议；不是任意异构协议转换已全覆盖 |
| 通道buffer／elastic stage可在SV前插入；Handshake降低生成fork/join及ready/valid逻辑 | [ESIChannels.td L566–624](https://github.com/llvm/circt/blob/26b9edcbdada0038f3918d0e198031fdc6c856e7/include/circt/Dialect/ESI/ESIChannels.td#L566)、[HandshakeToHW.cpp L778–817](https://github.com/llvm/circt/blob/26b9edcbdada0038f3918d0e198031fdc6c856e7/lib/Conversion/HandshakeToHW/HandshakeToHW.cpp#L778)、[L974–994](https://github.com/llvm/circt/blob/26b9edcbdada0038f3918d0e198031fdc6c856e7/lib/Conversion/HandshakeToHW/HandshakeToHW.cpp#L974) | 算子／token图和类型由输入IR提供；不能只比较data线，把valid和ready拆成可独立错配的选项制造难度 |
| unit-rate actor等待输入token及输出接收条件；buffer有实际生成路径 | [HandshakeToHW.cpp L1107–1128](https://github.com/llvm/circt/blob/26b9edcbdada0038f3918d0e198031fdc6c856e7/lib/Conversion/HandshakeToHW/HandshakeToHW.cpp#L1107)、[L1660–1683](https://github.com/llvm/circt/blob/26b9edcbdada0038f3918d0e198031fdc6c856e7/lib/Conversion/HandshakeToHW/HandshakeToHW.cpp#L1660) | 本轮该buffer路径明确总建seq buffer；不将TD类型列出的每种buffer都声称已由该后端实现 |

[DC rationale L49–70](https://github.com/llvm/circt/blob/26b9edcbdada0038f3918d0e198031fdc6c856e7/docs/Dialects/DC/RationaleDC.md#L49)另给FIFO顺序和latency-insensitive语义。上述是实际抽核路径，不能扩为“整个CIRCT绝无协议选择器”；也不能把库中合法算子的lowering，直接等同不可信RTL实现已经遵守声明。

## 5. 真正还需裁决的交接细节（未建立为gap）

| 细节 | 必需可审计内容 | 最直接强对照／常见退化 |
| --- | --- | --- |
| 备选从哪里来 | 公开需求允许的自由度、已认证原语能力、模型额外假设分别记录；模型说明不能直接成为真硬约束 | 工程师／模板给同一域，或一次模型给完整IR；若域已完全规定唯一方案，就是编译／事实抄写 |
| latency和吞吐能否组合 | 区分固定周期与token顺序；给II、可停性、容量、初始token、reset／flush和外部接收义务 | 标准elastic图／定长延迟对齐；普通传播可解时照样应保留，不能人为拆关联线来制造联合性 |
| “编码”究竟是什么 | 线路signaling与payload／opcode／量化编码分开；后者需明确解码语义及可证明映射 | typed IR、既有encoder/decoder；位宽相同不能证明含义相同 |
| 选中声明后行为是否兑现 | 先冻结合同和适配器，再核每个实际module对stall／保持／事务对应／数值编码遵约；所有失败留分母 | 同一协议IR的确定性shell＋行为填充、完整IR直接lowering、同池简单选择／有限枚举 |

一个公开可反驳边界是：不可停的valid-only源若持续发送，而消费者可无限期stall，有限FIFO不能保证永不丢失。只有增加公开的速率／最大stall约束、选择可背压源，或改变获准架构，才可能修复。此为传统协议条件，不是新反例算法；不能靠候选声明“合法”跳过，也不能悄悄缩小环境替某选项过关。

首次生成前的协调能提前排除**声明之间**的矛盾，不能证明尚未生成的行为已可实现／将会遵约。尤其同一LLM可在同组内写错，程序生成适配器也不能补救任意错误编码或事务数目。需独立验证前后交接，不能用后验修复成功冒充首次结构决策收益。

## 6. 当前建议

保留一个窄的、可证伪系统问题：**面对同一公开规格与同一组确有自由度的局部协议备选，行为前协调是否比完整协议IR直接lowering、同池简单传播／枚举和同预算完整结构生成，减少真实组合违约或人工建模／资格成本？** 这尚无运行证据，当前组合profile的结果也不覆盖它。

成熟原语、非LLM替代或传统理论本身不会否定系统贡献；贡献需落在可信输入、受限协调、已生成行为与工具lowering之间的具体交接收益。若原语库和完整IR已经以同工同信息得到相同结果，这轮不能只凭“LLM备选＋程序固定”宣称新核心。若继续，先明确真实任务的可选域与环境，不为创新强加时延／资源要求；本文件不授权开发、执行或论文投稿。
