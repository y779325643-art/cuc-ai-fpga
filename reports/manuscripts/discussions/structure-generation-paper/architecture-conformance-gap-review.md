# 架构与模块角色符合性：有界近邻检索及可检验增量

日期：2026-10-21。范围：最多六项原始工作，深入最接近的 SV-Gap 与 RTL-Obliger 方法/公开实现，并抽核 GRADE-RTL 的 M/F 实现。仅写本文件；未运行模型、HDL、SAT、作者框架或付费研究服务，未改稿件、任务或进度表。未读取 SecRTL-Gen 标为 hidden 的测试内容，也未重算外部模型结果。

**判断：仍可研究领域适配与交接可靠性的增量，但宽泛的“功能通过仍不兑现声明意图”“附加意图合同＋专门检查＋证据记录”已有直接近邻。** 最值得裁决的窄对象是：从预先同意的模块输出职责，到实际 RTL 的端口边，再到标准验证后端，能否可靠交接且明确拒绝不支持的映射。标准工具可以承载这一研究；标准工具能表达或已复现该关系，不会自动否定工具/协议贡献，也不会自动替它证明增量。

本地新增[标准切点结果](../../../../artifacts/responsibility-standard-cutpoint-20261021-01/results.md)第9–43、72–103行须精确表述：ALU wrong_mode 有有效反例，一份 native ALU 的完整响应被证明；old delegate 的响应保留 `UNKNOWN_ADAPTATION`，FIR/TD未适配。不是三个profile均已实现通用标准适配。已有12份原生输出和12份固定父构造全通过，仍没有真实样本的增量检出收益。

收尾时根任务完成了独立[双输出alias资格](../../../../artifacts/responsibility-port-alias-qualification-20261021-01/results.json)：共享内部wire与分开等价表达式两个合法child，当前未改Icarus checker和保持层级replacement miter均通过；每实现16输入×4个z、128个响应scalar比较，全部失败计数为0。根任务报告实际10个HDL过程，本轮只读结果核表、不重跑。**因此“共享输出必然让当前force误判”的假设未复现，不得作为本项目已发现的缺陷或新机制收益。** 此新资格与原12模型/24评价分母分开。

## 1. 六项范围与总体覆盖

检索词围绕 RTL architecture conformance、module interactions、declared intent、structural oracle、LLM obligation inference；搜索结果只用于定位原文/作者仓库。reddit 只提供 SV-Gap 仓库线索，其计数和结论未作为论文证据。此为有界查新，不是系统综述，也不支持“未见即绝无”。

| 工作 / 版本 | 已读原始方法及实现 | 与问题的真实重合 / 边界 |
| --- | --- | --- |
| **SV-Gap**，作者软件与研究记录；固定SHA `856c5832b2b5f2dfbeac58a6e4961ecc0550e4df`，2026-09-28 | [methodology](https://github.com/shsridhar-beep/svgap/blob/856c5832b2b5f2dfbeac58a6e4961ecc0550e4df/docs/methodology.md)、[研究说明](https://github.com/shsridhar-beep/svgap/blob/856c5832b2b5f2dfbeac58a6e4961ecc0550e4df/docs/compact-research-note.md)、实际Yosys规则/manifest/report代码；详见第2节 | **直接近邻**：保留功能结果，加声明意图与实际结构/时序/等价oracle；有“同步器存在但原reset绕过”的原始记录。是作者公开软件/记录，不冒称本轮独立复现或已审稿论文 |
| **RTL-Obliger / SecRTL-Gen**，[arXiv:2608.26588v1](https://arxiv.org/html/2608.26588v1)，§II–IV、Alg.1、§V/VI边界；作者库SHA `4d5d944fb35e5c372b8e9620b5785a91d061f881` | 规范证据图、本体匹配、未覆盖元素、义务过滤、两阶段生成；公开库当前能核benchmark/Vanilla/评价代码，方法推理器未取得；详见第3节 | **直接近邻**：普通功能之外的信号义务与可追溯推导已是方法。其五类资源访问安全义务不等于任意模块值来源；其benchmark刻意省略安全要求，不能当本项目同信息显式责任对照 |
| **GRADE-RTL**，[arXiv:2609.25335v1](https://arxiv.org/html/2609.25335v1)，Evaluation Framework；作者库SHA `4feb91a7a8638671c18c3b1c1f62b156f39dc176` | [parsing.py L361–428](https://github.com/hsc-research/GRADE-RTL/blob/4feb91a7a8638671c18c3b1c1f62b156f39dc176/src/llm_rtl_eval/parsing.py#L361)、[stages.py L184–285](https://github.com/hsc-research/GRADE-RTL/blob/4feb91a7a8638671c18c3b1c1f62b156f39dc176/src/llm_rtl_eval/stages.py#L184) | M确实检查占位/blackbox/空过程/驱动/可选default，再做Yosys proc/opt/check；F flatten后做参考等价。**不是按“module completeness”名称就可推定已有条件角色语义**，也不能说它只编译。公开[artifact范围](https://github.com/hsc-research/GRADE-RTL/blob/4feb91a7a8638671c18c3b1c1f62b156f39dc176/ARTIFACT_STATUS.md)明确缺少全部论文原始运行材料 |
| **AutoSVA**，[arXiv:2104.04003v1](https://arxiv.org/html/2104.04003v1)，§III-A–C、§IV；作者库SHA `cfeb42d827fa80282db552aac2a9ee917ad04dcd` | 接口transaction注释、自动建模/假设/断言及工具脚本；[autosva.py L556–663](https://github.com/PrincetonUniversity/AutoSVA/blob/cfeb42d827fa80282db552aac2a9ee917ad04dcd/autosva.py#L556)、[README L7–9](https://github.com/PrincetonUniversity/AutoSVA/blob/cfeb42d827fa80282db552aac2a9ee917ad04dcd/README.md#L7) | 已有模块接口预期→标准formal工具的领域前端/交接方法；包括progress、data integrity、stability，不是新solver。它证明“复用成熟验证器也可以研究方法”，也使仅包装assertion的宽主张不足。本文不把当前组合算术实验扩成其时序范围 |
| **CPPL**，[arXiv:2605.17892v1](https://arxiv.org/html/2605.17892v1)，§III-A–D、Fig.5/7/10/11；同期838aab3与后续d7ebbb5 | 本轮复用[既有深审](neighbor-deep-review-cppl-hint.md)的固定源码定位，不再次执行 | 已构造接口/实例输入绑定，ALU父mux与原始a/b复用本就明确；后续还有执行patterns/internal probes。不能将其弱化为实例名存在，也没有本项目对其实际接受旁路的复现 |
| **HINT**，[arXiv:2608.07625v2](https://arxiv.org/html/2608.07625v2)，§3/Table1/Fig.1、§4.1、§5.1 | 复用既有完整方法深审；作者匿名库/完整SPEC仍未取得可审计内容 | 已有可执行架构合同、父state/helper/commit、前RTL验收和后共仿真；lowering是agentic。完整接受的父行为可消除相关自由度；“公开材料未证本项自由边界规则”不等于其必然允许旁路 |

## 2. 深读一：SV-Gap 已做到什么

### 2.1 声明、生成与验证的具体链条

作者[reset-counter生成指令 L8–11](https://github.com/shsridhar-beep/svgap/blob/856c5832b2b5f2dfbeac58a6e4961ecc0550e4df/integrations/harbor/svgap-reset-release/reset-counter/instruction.md#L8)不仅要求辅助flag同步，而是要求counter状态本身async assert / sync deassert。对应[manifest](https://github.com/shsridhar-beep/svgap/blob/856c5832b2b5f2dfbeac58a6e4961ecc0550e4df/integrations/harbor/svgap-reset-release/reset-counter/tests/manifest.toml)分别指定功能命令、结构backend、clock和reset的声明。这里的责任有公开任务依据，不是事后看到失败才添加的名称检查。

实际backend不是仅搜索 `sync` 字符串：[reference_yosys.py L37–53](https://github.com/shsridhar-beep/svgap/blob/856c5832b2b5f2dfbeac58a6e4961ecc0550e4df/src/svgap/backends/reference_yosys.py#L37)执行read/hierarchy/proc/opt_dff/opt_clean并读实际netlist；[L1203–1243](https://github.com/shsridhar-beep/svgap/blob/856c5832b2b5f2dfbeac58a6e4961ecc0550e4df/src/svgap/backends/reference_yosys.py#L1203)识别其窄定义的2FF reset链；[L744–763](https://github.com/shsridhar-beep/svgap/blob/856c5832b2b5f2dfbeac58a6e4961ecc0550e4df/src/svgap/backends/reference_yosys.py#L744)逐普通state的async-reset pin检查原始reset是否仍直达，并排除识别出的同步器本身。**所以“正确子结构存在，但没有承担声明的目标角色”已有实际检测代码。** 其识别是窄规则，不是一般CDC/RDC完备证明。

[verify_synchronizer_bypass.py L39–46、109–172](https://github.com/shsridhar-beep/svgap/blob/856c5832b2b5f2dfbeac58a6e4961ecc0550e4df/scripts/verify_synchronizer_bypass.py#L39)进一步盘点同步器输出的外部consumer角色；作者[reset记录 L97–120](https://github.com/shsridhar-beep/svgap/blob/856c5832b2b5f2dfbeac58a6e4961ecc0550e4df/docs/reset-replication-result.md#L97)报告同步器输出仅作用于同步datapath qualifier，而被标记state的异步pin仍接原网。本轮读了代码/记录，没有执行该盘点，也没有独立重算其模型计数。因此该结果按“作者公开报告”引用，不由reddit数量代替证据。

### 2.2 交接和证据合同也已实现

不是“对功能test再加一个lint”而已：[methodology的Evidence policy](https://github.com/shsridhar-beep/svgap/blob/856c5832b2b5f2dfbeac58a6e4961ecc0550e4df/docs/methodology.md#L72)区分fail、unknown、tool_error；schema v2把contributing与contextual oracle分开。[manifest.py L303–369](https://github.com/shsridhar-beep/svgap/blob/856c5832b2b5f2dfbeac58a6e4961ecc0550e4df/src/svgap/manifest.py#L303)解析这些配置；[validation.py L299–330](https://github.com/shsridhar-beep/svgap/blob/856c5832b2b5f2dfbeac58a6e4961ecc0550e4df/src/svgap/validation.py#L299)在required结果unknown或observed requirements未满足时返回incomplete，不把它们当closed。

作者[研究说明 L109–129](https://github.com/shsridhar-beep/svgap/blob/856c5832b2b5f2dfbeac58a6e4961ecc0550e4df/docs/compact-research-note.md#L109)将贡献定位于intent/evidence合同而非一个backend完备性。当前本项目若只说“明示意图、保留功能结果、接标准工具、存证”，将有很强重合。

### 2.3 尚不能据此判定的部分

固定版本的[21条规则表 L10–30](https://github.com/shsridhar-beep/svgap/blob/856c5832b2b5f2dfbeac58a6e4961ecc0550e4df/docs/finding-id-reference.md#L10)没有列出任意组合算术child-output自由响应的native规则；但其formal/equivalence后端和backend SDK本来允许扩展。**这只是本轮所核原生profile覆盖差别，不是框架不能表达本项目义务。** reset结构责任也不同于本项目明确选择的逻辑响应语义；两者都可称额外合同，不应混为同一种证明。

## 3. 深读二：RTL-Obliger 已把“缺少义务”做成方法

### 3.1 不是只给LLM一句安全提示

[§IV-B](https://arxiv.org/html/2608.26588v1#S4.SS2)把规范抽成封闭标签的FSG；标签分别描述element、生命周期、敏感性、操作、guard和exit。CWE本体含element/transfer pattern、scenario及信号级文本模板。[§IV-C、Alg.1](https://arxiv.org/html/2608.26588v1#S4.SS3)确定性检查reqE/reqT/context与未覆盖元素U，输出scenario及结构见证。§IV-C3再把U等填入义务。因此“规范证据→缺失缓解→具名信号义务→审计见证”已有明确方法，不能仅更名为架构责任推导。

[§IV-D](https://arxiv.org/html/2608.26588v1#S4.SS4)的LLM Judge只能保留/拒绝，不能发明义务；之后先功能草稿，再按义务修订。这个流程不等同本项目的一次完整RTL输出；它也不是依靠证明器发现错误后才存在义务。其§II-C明确区分功能规范没有蕴含的安全义务，与安全知识要求补上的规范范围。

### 3.2 官方实现核验的上限

论文脚注指向[NTDXYG/SecRTL-Gen](https://github.com/NTDXYG/SecRTL-Gen)。本轮读其默认main、唯一列出的公开branch及完整文件树，固定SHA `4d5d944fb35e5c372b8e9620b5785a91d061f881`（2026-08-04，早于论文v1）。[README L17、42–47、90–126](https://github.com/NTDXYG/SecRTL-Gen/blob/4d5d944fb35e5c372b8e9620b5785a91d061f881/README.md#L17)给出functional-only prompt、单模块、golden/hidden测试不进prompt、Vanilla与evaluation布局。

[example_Vanilla/evaluate.py L38–70](https://github.com/NTDXYG/SecRTL-Gen/blob/4d5d944fb35e5c372b8e9620b5785a91d061f881/example_Vanilla/evaluate.py#L38)实际把functional/security测试分开并分别计率；[run.py L69–121](https://github.com/NTDXYG/SecRTL-Gen/blob/4d5d944fb35e5c372b8e9620b5785a91d061f881/example_Vanilla/run.py#L69)可核普通生成和评价入口。**未在该公开树取得FSG抽取、CWE ontology matcher、Alg.1/Judge/两阶段方法的实现。** 不能把benchmark代码当作整个方法已复现，也不能推出作者没有其他实现或论文方法不存在。未读安全测试内容来寻找本项目题目或候选修复信息。

### 3.3 与本项目相同和不同的科学对象

它的benchmark刻意不向生成器给安全义务；评价用独立black-box安全测试。因此“功能测试通过但安全失败”可能来自遗漏的规范/测试，不是“生成器知道完整同信息承诺却没有兑现”的同一个因果问题。本项目则必须先公开并同意额外自由响应；“使用adder”本身不蕴含全部off-manifold合同。

安全责任经CWE语义进入测试，本项目的单边界逻辑响应需要自己的适用依据。不能把切点检查当新增能力，也不能把“把所有隐式要求提前写给模型”单独当新协议。可研究的是：可复核的职责范围/目标身份/变换语义在生成者与验收者之间是否丢失，以及自动交接是否降低错误和实际适配负担。

## 4. 当前剩余的可反驳gap

候选问题是：**当生成前已经明确接受一个child-output逻辑职责，如何把该承诺交给一个并非为该候选手写的标准验证后端，使它切的是同一个端口输出边，且不会将别名联动造成的伪反例误记为模型违约？** 这属于领域前端与语义交接的可靠性，不是新的SAT/cutpoint算法。

本地alias适配失败使这个问题有真实动机，但不证明其未被成熟wrapper解决。SV-Gap已强调实际结构和不确定性；AutoSVA已生成模块交互的formal scaffolding；CPPL/HINT可直接构造或固定父行为。当前方案须与它们代表的强替代比较，不能把输入/证据边界不同作为胜利。

现有all-output normal/active/inactive映射已经完整确定父上下文的外延函数。只选一个boundary、没规定每根内部wire，并不自动减少行为规格或超过最简完整IR的实现自由度。若新增机制仍需用户手写同样完整函数与wrapper，独立方法增量很弱；若可靠减少重复义务/实例映射/变换审阅工作，可以用实证支持工具或交接方法贡献。

## 5. 专审窄机制：端口边切割与保持证据

### 5.1 必须先明确切割的对象

“实际child-output端口边”应指**优化抹掉来源之前，选定实例的某输出port与父连接之间的驱动关系**。它不同于把所有同bit ID的net统一变成自由输入。后者可能同时切到top输入、其他child输出或别的instance，改变的关系超出公开承诺。

最小变换可以：解析真实实例/type/参数/port方向与宽度；在该实例外围生成保持层级的replacement wrapper；原child按原有输入连接继续计算，仅把选中输出向父提供的值换成新PI z，其他输出照原child连接；再交标准miter。记录真实绑定、单一z驱动及未修改的连接/参数。这是**普通wrapper/miter就能实现的强对照**；不能因为自动发射或多存一个证书就先称新颖。

“保持”应分两层：top外部输入身份不被z改写；未选输出保持其原有局部函数及连接语义。证书不能仅报告bit宽相同或编译exit0，也不能无条件规定未选输出在干预前后数值相等。

### 5.2 资格case与实际状态（本轮审查不执行）

| Case | 合法原设计及公开职责 | 整根alias切割的风险 | 强wrapper预期 / 裁决点 |
| --- | --- | --- | --- |
| A：透明输出 | child `o=a`；parent对child.o的显式输出连接供y，同时另有raw a用途；要求target边换z后y=z、raw路径仍用原a | flatten后o/a可能同位；切net会改变输入或raw路径 | 优化前只替换输出边可保留透明child内部实现；必须验证切边身份而非把所有同位信号都当目标 |
| B：同child双输出共用内部值 | child的sum和copy均来自内部v=a+b；父y=sum、echo=copy；只target sum，要求y=z而echo仍a+b | 把同bit整根net释放可能联动copy，但这不等于Icarus force输出port必然联动 | 根任务已做2-bit共享/分开表达式两个控制：当前force与原child＋sum=z wrapper均零错。该case目前是兼容性资格，不是现checker伪拒的证据 |
| C：同type两个instance | u0/u1合法相同module；仅u0.o为target | 全局改module定义或按名字模板替换会误改u1 | 只作用于所选实例，u1保持原连接/行为；不能以module名代替instance绑定 |
| D：非目标输出合法随z变化 | child `o=a,p=b`；父连a=x、b=o+1，外部y=p。o不依赖b，因此原图无组合环 | 要求p数值等于intact前会误拒合法上下文；其输入b本来随target边变化 | 输出边替换后p应为z+1。应保持“p=b的原函数和b=o+1的原连接”，不是p恒等原x+1；证书必须声明输入保持的作用域 |

另一个边界：如果**父本身**把target输出接回同一top输入net、或将两个输出port物理短接，而非只在child内部透明/共值，则不能一面保留那个物理同一性、一面要求其中一个值任意独立变化。必须定义基于哪条源级端口边解释职责，或返回该profile不支持；不得用别名拆分偷偷制造一种候选从未声明的上下文。

上述case只针对单边界、组合、电平二值，不新增并发/时序研究。A/B/C是正向兼容性资格，D反证过强“非目标值保持”条件。B的新结果表明，Yosys catalog/net别名与Icarus运行时port force不可混推；本轮没有在B上得到当前checker与标准wrapper的区分。

### 5.3 直接结论与强替代

- 对这些case，**保持层级的标准wrapper＋同信息miter在原则上就能同等处理**；本轮没有发现必须发明新求解或新组合语义才能解决的约束。
- B现在还有实际的零差异资格支持：标准wrapper足够，当前force也通过。不能把尚未实现的通用证书或“已有alias事故”升级为当前checker相对wrapper的优势。若继续，应先指出自动交接确实能省掉哪项同信息generic wrapper仍需的人工步骤，否则将此窄方向归入backend稳健性，而非已经成立的方法核心。
- 未解决的工程问题是自动定位/实例特化、别名抹平前的切割时点、未选port的函数/连接保持、证明物与候选版本绑定、unsupported/unknown处理。它们有可测试的真假，但“尚未在本地实现”不是领域空白。
- 若两种实现都用同一generic wrapper和相同人工字段，得到相同覆盖/unknown与工作量，则应放弃该窄机制的独立方法优势主张。可留下校准与可复用实现。
- 若自动交接在同样信息下，稳定避免人工适配错误，接受这些合法实现并正确定位越界，且减少实际人工映射/审阅步骤，则可支持有边界的软件/协议增量；需要数据，不能从一个历史伪反例推到一般收益。

## 6. 支撑论文贡献的最小真实证据

这是后续裁决清单，不是本轮运行授权，不要求先扩大模型调用量。

1. **明确领域必要性。** 至少在两个不同真实资产/要求来源上，由需求方在生成前接受具体模块角色及其抽象含义；例如组合MAC的中间结果与TD返回路径。要公开什么要求允许/禁止哪类优化，不能把toy ALU或仅自然语言“use”当充分依据。
2. **让两种强实现吃同一输入。** 同一instance/type/port/参数、相同普通/自由域与数学合同，比较实际输出边自动交接与generic hierarchy-preserving wrapper/标准miter；最简完整IR/固定父是另一构造控制。普通全net cut只能是故障消融，不能作为唯一弱baseline。
3. **先校准变换再评价候选。** 冻结A–D等资格预期，独立检验输出边、原输入、其他port/instance关系、alias及错误target；保留不支持和伪反例。工具错误不能进入模型违约分子。期望来自公开职责与独立检查，不让同一个变换器自行证明自己正确。
4. **测量实际增量。** 记录用户真正提供的语义条款/映射字段、重复表达、候选特化代码或脚本修订、人工检查步骤及unknown率；如测时间应定义相同起点/终点并保留实际记录。源码行数、一次修复的回忆、自动化标签不等于省工证据。
5. **模型效益另行裁决。** 现有12原生全pass只支持有界零差异；无需为工具正确性伪造真实错误率。若论文要主张首次生成收益或常见架构违约，才需要冻结信息/预算的真实候选研究，全部失败保留且不能倒改合同。

最少可成形的贡献路线是：**一个明确范围的模块角色交接格式与标准后端适配，外加独立变换资格、与标准wrapper的同信息比较和真实使用代价证据。** 这不要求新solver，但必须显示相对于SV-Gap式intent/evidence合同、AutoSVA式formal前端及完整IR的具体增量。当前尚未具备该比较证据，因此只能建议有界资格与成本对照，不能判定SCI充分性，也不应仅凭标准SAT成功就宣布整个研究没有贡献。
