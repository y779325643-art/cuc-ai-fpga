# 新方法核心的有界独立构思与反驳

日期：2026-10-21。N22应用`scientific-brainstorming`的独立构思、证据分离与反驳流程；N23接续核对标准语义商主源和现有profile。本文所有新机制均为idea，不是创新发现；不修改现行研究语义、旧G合同、可信评价或稿件正文。先前N20/N21的停止结论保留。

## 1. 问题、范围与预定门槛

焦点是：在现有组合任务、首次无反馈生成、最低补工的范围内，能否提出一个具体的新处理，形成相对强近邻及同信息基线的可检验增量。完整可信normal可直接编译；当前原生12份全通过。少量自由分解变体已经允许，新的时序范围尚待用户选择。本轮不新增PPA、流量、外部周期或禁止重算要求，不使用隐藏评价反馈，也不将人工反例说成真实模型失败。

两份独立任务的派发文字已共同要求以下门槛，先于接收其结论；没有事后评分、票数排名或数值权重：

1. 输入必须说明谁提供、是否已有、是否仍需作者新加语义；强基线得到同样信息。
2. 新处理须有准确输入/输出、可执行或可手算区分例及端点预测。不是只更改名称、阶段顺序或比较一个故意弱化的基线。
3. 复用成熟原语不自动否决；需要指出真实多处理的需求或减少的工作。相同输入/处理/结果但未测省工，不能直接立项。
4. 数值手算、机制idea、尚未查新的原创性与实际运行证据分别标明；新保证若更弱，不能冒充同保证省工。
5. 输出最多两个独立候选、主审最多一个讨论候选；最多两项相关近邻深审，再一次短修订。允许全部弃权，不自动选赢家；没有新被测生成或开发授权。

## 2. 独立来源与锚定限制

两名AI研究协作者以`fork_turns=none`分别启动，均未指定模型/推理覆盖、未看到对方或主审候选。收到相同事实和边界，分别分配作者规范负担、结构推导选择的视角。角色是研究设计者，不是被测RTL生成模型；研究agent条目不加入任何候选性能分母。

| ID / contributor | 独立允许材料与问题 | 实际首轮输出 |
| --- | --- | --- |
| A1，`/root/core_authoring_independent`，AI-assisted independent | N20审查、N18方法卡、N19可信spec/public数学；能否在保留强语义/自由度的同时减少作者输入 | 弃权；曾考虑有限语义解释池＋分歧问题＋作者一次确认，但同信息枚举能做相同工作，且确认信息不能凭空省去 |
| S1，`/root/core_selection_independent`，AI-assisted independent | 相同材料；能否提出非普通CSP选项的新结构推导 | 弃权；曾考虑从下游反推充分接口，但TD的E已是AST节点，FIR系数兼容是普通线性约束，没有真实端点收益 |

四份允许材料是[直接编译审查](direct-math-compiler-baseline-review.md)、[方法卡](contract-option-protocol-method-card.md)、[trusted-specs](../../../../artifacts/responsibility-local-semantic-selector-prototype-20261021-01/trusted-specs.json)及[public数学](../../../../artifacts/responsibility-local-semantic-selector-prototype-20261021-01/public-math-source.md)。首轮两者均只读指定材料，没有先查文献、工具实验或写文件。主审等两份终态后才向其他审查者提交下述R1。

独立上下文仍由同一AI服务提供，参与者不是领域人类专家，也不代表独立统计样本；共同给出的已验证事实本身会锚定方向。二者弃权是透明的研究判断，不能当作“所有可能方法均无创新”的证明。

## 3. A1为何不能省去缺失语义

**idea：** 先枚举少量解释、求分歧输入，请作者一次确认，再形成唯一规范。**assumption：** 真实意图已在有限池内；未覆盖的解释不会因问一个例子而被证明不存在。

协作者给出的手算见证可定位其信息成本：若原需求未确定取整，`reward=0,next=-1,gamma=1,value=0,alpha=16`，floor得到`R=E=U=-1`，向零取整得到全部0。没有作者补充信息时，程序不能判哪项才是原意。

另一手工分歧点为`reward=0,next=-97,gamma=33,value=0,alpha=8`：floor/向零取整，以及先饱和误差/先缩放宽误差，四解释的`(R,E,U)`分别是`(-201,-128,-64)`、`(-200,-128,-64)`、`(-201,-128,-101)`、`(-200,-128,-100)`。这是从公开公式改变两项规则得到的四种假设，不是当前TD真有歧义；当前公开规格已经明示floor及先sat。

**decision：不为A1开发。** 保留完整公式时，公平强基线是公式前端＋直接编译；删去规则时，确认只是补回作者语义。有限解释枚举同样可以找到分歧问题。未给出新增处理、真实作者时间/错误率数据，不能用少几个JSON字段替代省工证据。本轮没有执行这些手算例，也没有新增作者询问实验。

## 4. S1为何未产生当前需要的新选择

**idea：** 由可观察输出反推接口充分量，选择非字面分组。**challenge：** TD的`E=sat8(R-value)`已经是显式节点，普通sat outlining得到同样桥；FIR两块`x1`系数和为−2即可，普通线性规范化/约束枚举已有合法解。更一般语义商可能非AST子表达式，但当前任务不要求哪种分解、共享或接口宽度，尚无真实取舍。

**decision：不为S1开发。** 同一完整AST的零模型编译先行，随后才是AST分区、代数规范化及完整约束枚举。不同结构本身不是新增收益；不能追加接口位宽或PPA偏好来制造目标。该判断只限当前材料，不推及所有时序或模块任务。

## 5. R1讨论候选：条件非干扰的角色声明

这是主审在两份独立输出后提出的第三个idea，origin为AI-assisted discussion，尚未采纳。它尝试只给边界`z`、其私有上游`x`、允许上下文`c`、输出`y`、公开guard `g(c)`，而不写全部自由响应函数G。对实际parent在边界替换后得到的`P(x,z,c)`：

- active：`∀x1,x2,z,c. g(c) ⇒ P(x1,z,c)=P(x2,z,c)`，即固定边界和允许上下文后，输出不再依赖归child负责的原始上游。
- inactive：`∀x,z1,z2,c. ¬g(c) ⇒ P(x,z1,c)=P(x,z2,c)`，即该模式下边界不能影响输出。

普通功能与child合同仍独立验证；上式本身不证明数学正确，也不自动证明child具有非空影响。guard可满足性、变量/别名分组、上下文泄漏及非空责任是否需要额外条款，均是待反驳问题。它与经典信息流非干扰/双副本自组合强重合，不主张新证明算法。

**手工机制例，非现有任务/模型样本。** `x:signed3`，child算`h=x²:signed6`，顶层需求为`y=(x!=0)`，guard恒真。委托parent `P=(z!=0)`对x独立；绕过parent `P=(x!=0)`普通功能相同但active条件失败。

**不可隐藏的保证差别。** `P=(z>0)`在正常`z=x²`下同样正确，也满足上述非干扰；但若旧合同规定完整`G=(z!=0)`，自由signed6边界`z=-1`时两者不同。因此R1明确不是同保证的G压缩，不能据此替换旧checker或降低旧评分。它只能研究另一个较弱、需事先明确同意的角色声明，不能从减少公式字段直接宣布进步。

同信息强基线至少包括手工/参数化双副本非干扰miter、成熟RTL信息流工具、严格父构造与完整IR。本轮分别交由非提案者做语义反驳和最多两项原文/实现深审；没有因此授权实现或修改合同。

**独立challenge：** 这些标签只有来自“该模式下输出只能通过指定child结果取得该组输入信息”的明确承诺才有效；仅要求实例存在、模块名或“负责加法”不能自动推出此隔离。必须按输出分别声明，FIR的独立edge输出仍可合法读原始输入；允许上下文不得夹带私有输入的别名/派生信息。NI也不证明必须使用child、无冗余运算或物理资源保留。

## 6. 两项近邻的方法与实际代码

检索日期2026-10-21，查询为`RTL information flow noninterference conditional assumptions self composition Iodine SecVerilog UPEC official github`和`SecVerilog dynamic labels hardware noninterference declassification github author`。先独立构思后查新；最终只深审SV-Gap与SecVerilog，没有因同名或检索摘要判新颖。

**SV-Gap。** 作者固定提交`856c5832b2b5f2dfbeac58a6e4961ecc0550e4df`（2026-09-28）已有[声明意图与证据合同](https://github.com/shsridhar-beep/svgap/blob/856c5832b2b5f2dfbeac58a6e4961ecc0550e4df/docs/methodology.md)、[实际reset pin规则](https://github.com/shsridhar-beep/svgap/blob/856c5832b2b5f2dfbeac58a6e4961ecc0550e4df/src/svgap/backends/reference_yosys.py#L744)及[用途consumer追踪](https://github.com/shsridhar-beep/svgap/blob/856c5832b2b5f2dfbeac58a6e4961ecc0550e4df/scripts/verify_synchronizer_bypass.py#L109)，能检查存在同步器却绕过其声明角色。该核定规则路径不是通用双运行NI，不可由此推定其他backend不能表达。本轮复核既有固定源码，未执行作者工具；详细原件见[既有深审](architecture-conformance-gap-review.md)。

**SecVerilog。** [作者论文](https://www.cs.cornell.edu/andru/papers/asplos15/asplos15.pdf)为ASPLOS2015，相关§3–5实际通过依赖安全标签、分支谓词和约束控制信息流，§5.2定义双运行可观察确定性。作者实现固定`5373abf58ebe895125c1f9d9c92cf3461abc907a`（2015-03-13，早于会议，不称最新版）。[typecheck.cc L419](https://github.com/aferr/secverilog/blob/5373abf58ebe895125c1f9d9c92cf3461abc907a/verilog-0.9.6/typecheck.cc#L419)合并rhs和pc标签并生成约束，[L776](https://github.com/aferr/secverilog/blob/5373abf58ebe895125c1f9d9c92cf3461abc907a/verilog-0.9.6/typecheck.cc#L776)更新分支环境，[L1069](https://github.com/aferr/secverilog/blob/5373abf58ebe895125c1f9d9c92cf3461abc907a/verilog-0.9.6/typecheck.cc#L1069)接外部格/标签配置；[作者条件标签例](https://github.com/aferr/secverilog/blob/5373abf58ebe895125c1f9d9c92cf3461abc907a/test/diamond.v#L13)并非只支持固定标签。

对R1的**映射推论，未执行适配**：边界先独立化，取不可比D1/D2，令x为D1、z为D2、c为LOW，y标签由公开g在D2/D1间切换，则对应active排除x与inactive排除z。论文安全策略本就能表达这种条件允许依赖，不是本候选的新NI能力。

必须保留实现边界：[check_expr.cc L29–40](https://github.com/aferr/secverilog/blob/5373abf58ebe895125c1f9d9c92cf3461abc907a/verilog-0.9.6/check_expr.cc#L29)对二元运算直接join标签，不能保证识别所有语义抵消；该固定代码的函数调用被忽略并返回底标签，不可未经受支持子集检查签核任意RTL。动态寄存器标签擦除可能改变功能，不能默认为只读检查；组合wire无此擦除。论文完整证明另引技术报告，本轮未取得该完整证明或运行其测试。这些限制不产生我们的已验证优势；普通语义双副本miter仍是强对照。

研究审查者读相关完整方法及源码；主审独立打开作者论文§5.2/5.3和擦除边界，并用GitHub插件回核上列三个关键代码段，没有运行SecVerilog或把源码缺口用作创新证据。

**decision：R1不作为新核心开发。** 条件NI与双副本已有实质先例，较弱保证不能换成“同保证减少作者工作”的主张。

## 7. 唯一post-check修订R1b：先证明覆盖资格，再省G

这是一个讨论后修订，非新实验或采纳合同。它试图修正R1的保证放弱：仍给完整F/h和可信角色划分，但只有证明角色可实现、且实际上游覆盖完整边界后，才允许不输入G。否则保留原G或报告资料不足，不自行外推域外响应。

对每个合法且active的c，在**实际允许上游域**X(c)与非空声明边界域B上，要求：

1. `h(x,c)∈B`。
2. `h(x1,c)=h(x2,c) ⇒ F(x1,c)=F(x2,c)`，即同一接口值不能要求两个不同输出。
3. `h(X(c),c)=B`，满射不能仅取child独立端口的全域。
4. 普通功能、实际child合同及active/inactive NI都是相应域的全称保证，有限测试不能代入下述推论。空active不获得角色覆盖credit。

**数学推论，非原创定理声明。** 定义`Q(z,c)=F(x*,c)`，其中`h(x*,c)=z`。第3项保证x*存在，第2项保证选哪个x*都一样。active NI给`P(x,z,c)=P(x*,z,c)`，普通正确性再给`P(x*,h(x*,c),c)=F(x*,c)`，故P等于唯一Q。inactive NI与普通功能给`P(x,z,c)=F(x,c)`。

这不自动等价任意旧G。只有旧active G本身在此域对私有x无语义依赖、且与F/h一致时，才能由唯一性推出它就是Q。若旧G允许额外x依赖，改为NI仍是换保证，不能声称省掉重复输入。

**手工非字面例。** 模16算术下，固定允许上下文b、私有a，`h=(a+b)mod16`、`F=(a-b)mod16`。每个b下a→h是双射，故`Q=(z-2b)mod16`，不是F中某个字面加法节点的替换。本例证明可由语义商得到相同响应，未区分新算法；它是尚未采纳的角色/结构变体，不能改旧ALU的guard或重新计分。

**两个不可省的负例。** `h(x0,x1)=x0、F=x1`虽满射却不满足第2项，属于角色声明不可实现；child `h(u)=u`虽在其局部ABI满射，若实际上游只给u=0，第3项仍失败。最初平方例非满射，会被这项资格排除；原TD正常R也不覆盖完整signed17，不能继承资格。

独立反驳者确认上述条件下的推论，仍建议STOP当前独立核心：新增处理是标准函数分解/语义商资格、域证据及NI前端，作者还要给F/h、类型、合法域、guard和角色划分。最强基线是**同输入自动函数分解/商构造＋NI模板**，完整IR也可使用自动所得Q，不能强迫它手写G。已读SV-Gap/SecVerilog未见这套完整资格流程的实现，仅说明核定覆盖不同，不证明领域没有。

## 8. 本轮决定与后续门

本轮两项独立弃权、R1停止新能力主张、R1b修正保证问题但未获创新验收。主审决定：**不进入新实现或模型实验；R1b只保留为数学与输入资格的后续研究假设，不登记已成立核心。** 原因是相对“自动语义商＋同NI资格”仍无具体的新处理、绑定收益或作者工作证据；不是因成熟算法存在便否定系统研究。

若继续R1b，只能先核自动函数分解/语义商的原始方法及实际实现，给同信息最强对照，并找到至少一项现有公开角色确实满足该保证/资格的任务和可核实的输入工作差异。候选式子更短或旧G字段被省略都不是实际工时证据。没有实质差异就结束该候选，不再追加同类小原型。正式时序范围仍待答，本文未用该等待采纳新问题；v0.3及全部旧运行不变，SCI总目标仍未完成。

收尾独立只读审查核对本文、N22/N23及§20，确认A1手算、平方类型/负z示例、R1b四条件与旧G额外条件及源文/映射边界，未发现指定范围需修改的实质问题；未运行或修改文件。此审查不认证方法创新或SCI充分性。

## 9. N23：标准函数依赖与关系投影的实际能力

本阶段只深审两项主源：IWLS2007的SAT重代入方法/作者ABC实现，以及CUDD作者实现。检索日期2026-10-21，查询包括`Boolean functional dependency SAT interpolation fixed divisors resubstitution ABC Jiang paper`。研究与工程审查者各负责一项，另一审查者独立核profile数学；没有执行作者软件、solver、HDL或新候选生成。

### 9.1 固定divisor的SAT重代入

Mishchenko、Brayton、Jiang、Jang的[作者论文《SAT-Based Logic Optimization and Resynthesis》](https://people.eecs.berkeley.edu/~alanmi/publications/2007/iwls07_ifs.pdf)（IWLS2007，pp.358–364）§2.3给出固定divisor的充要条件：不存在在care内、全部divisor同值但目标不同的两输入。§3.4用双份逻辑检查，§3.5从UNSAT证明插值生成依赖函数；§2.5允许不可达divisor赋值作don't-care补全。故无需作者先写Q，也不要求补全唯一。不能把这类补全当作旧G的域外承诺。

对R1b，divisor取`(h(x,c),c)`，care取合法`X(x,c)∧g(c)`，逐输出位检查：

`care(x1,c1)∧care(x2,c2)∧c1=c2∧h(x1,c1)=h(x2,c2)∧(F_i(x1,c1)≠F_i(x2,c2))`。

全部位UNSAT就是所需的fiber一致性；满射仍是另一问题。这是方法的直接映射，不是已运行的RTL适配。

作者官方ABC固定提交`fba0adf4ccca0be59ddc6e77a85eb0cc64e04a8b`（2026-10-21），不是把当前源码当2007实验版本：

| 实际代码 | 核定处理／限制 |
| --- | --- |
| [resSat.c L52](https://github.com/berkeley-abc/abc/blob/fba0adf4ccca0be59ddc6e77a85eb0cc64e04a8b/src/opt/res/resSat.c#L52)、[satUtil.c L312](https://github.com/berkeley-abc/abc/blob/fba0adf4ccca0be59ddc6e77a85eb0cc64e04a8b/src/sat/bsat/satUtil.c#L312) | 旧res调用的复制函数开头是assert，旧复制体已注释；不能将此残留入口冒称可运行复现。 |
| [mfsInter.c L88](https://github.com/berkeley-abc/abc/blob/fba0adf4ccca0be59ddc6e77a85eb0cc64e04a8b/src/opt/mfs/mfsInter.c#L88)至L222 | 后续mfs显式加载两份CNF、反置目标位，再以XOR变量和候选约束匹配divisor；不用旧复制stub。 |
| [mfsResub.c L101](https://github.com/berkeley-abc/abc/blob/fba0adf4ccca0be59ddc6e77a85eb0cc64e04a8b/src/opt/mfs/mfsResub.c#L101) | SAT调用后UNSAT返回1；SAT返回0并保存divisor差分反例；未决返回−1、计timeout。此入口只判依赖，不物化Q，也不直接检查实际候选parent P。 |
| [mfsInter.c L329](https://github.com/berkeley-abc/abc/blob/fba0adf4ccca0be59ddc6e77a85eb0cc64e04a8b/src/opt/mfs/mfsInter.c#L329)、[satInter.c L948](https://github.com/berkeley-abc/abc/blob/fba0adf4ccca0be59ddc6e77a85eb0cc64e04a8b/src/sat/bsat/satInter.c#L948) | 另一入口再求UNSAT、指定共同divisor、插值truth table并转逻辑函数。所核truth路径共同变量≤8，不能直接承诺任意宽RTL查询。 |

高层mfs会自行选window/divisor，不能默认其局部care和R1b完整合法域一致。还需前端构造可信F/h、固定位级角色与域；本地未实现此适配。主审回读作者论文§2.3及§3.4–3.5，并独立核mfs两副本、三态返回、旧stub和插值限制。仅静态确认调用路径，不称已复现或可按某条现成CLI直接运行。

### 9.2 CUDD的image与两副本关系

固定CUDD3.0.0导入提交[`f54f533303640afd5dbe47a05ebeabb3066f2a25`](https://github.com/cuddorg/cudd/commit/f54f533303640afd5dbe47a05ebeabb3066f2a25)，提交作者Fabio Somenzi、作者日期2016-01-01，提交日期2016-01-20。相关源也标注作者；不称最新版。

| 已实现API | 核定语义 |
| --- | --- |
| [Cudd_bddExistAbstract](https://github.com/cuddorg/cudd/blob/f54f533303640afd5dbe47a05ebeabb3066f2a25/cudd/cuddBddAbs.c#L101) | 消去cube中的变量；正cube验证失败返回NULL并设非法参数。 |
| [Cudd_bddAndAbstract](https://github.com/cuddorg/cudd/blob/f54f533303640afd5dbe47a05ebeabb3066f2a25/cudd/cuddAndAbs.c#L104) | 已封装合取与存在投影，即`∃cube.(f∧g)`。 |
| [Cudd_bddPermute](https://github.com/cuddorg/cudd/blob/f54f533303640afd5dbe47a05ebeabb3066f2a25/cudd/cuddCompose.c#L290)、[SwapVariables](https://github.com/cuddorg/cudd/blob/f54f533303640afd5dbe47a05ebeabb3066f2a25/cudd/cuddCompose.c#L428) | 支持变量重命名；映射、变量组及共享上下文由调用者正确给定。 |
| [Cudd_bddComputeCube](https://github.com/cuddorg/cudd/blob/f54f533303640afd5dbe47a05ebeabb3066f2a25/cudd/cuddUtil.c#L2272) | phase=NULL时构造全正量化cube；逻辑关系另由AND/XOR/XNOR组合。 |

以下是前端组合推导，**不是现成CUDD角色profile**。设A(c)为合法active上下文，建立`R(x,z,c)=X(x,c)∧Eq(z,h(x,c))`与`I(z,c)=∃x.R(x,z,c)`，再检查：

- 域外值：`A(c)∧I(z,c)∧¬B(z)`。
- 覆盖洞：`A(c)∧B(z)∧¬I(z,c)`。
- fiber冲突：`A(c)∧R(x,z,c)∧R(x',z,c)∧OR_i XOR(F_i(x,c),F_i(x',c))`。

三者为空、且A/B非空等输入条件有效，便可判相关数学资格；不需要构造Q。只能量化私有x，必须保留c；否则会把逐context覆盖错当总体覆盖。两副本仅重命名x，共享z/c。

还需可信数学到BDD的位向量前端、实际域/变量分组、角色与输出策略、guard空域检查以及返回分类。NULL表示失败，不是BDD假值；内存/节点/超时等失败不能授通过。CUDD也不会自动证明实际RTL的普通功能、child合同或NI。主审回核存在投影、合取投影和置换三个实际函数；未安装或运行CUDD，未测运行规模、集成成本或端到端资格。

## 10. N23：原三个profile的逐输出适用性

依据[原公开数学/绑定](../../../../artifacts/codex-responsibility-cross-task-20261021-01/public-tasks.md)及三个公共JSON模板作静态分析，模板仍为enabled:false，不改变历史运行中其他启用副本。它们没有独立private/context声明字段；以下划分是依据完整旧合同作的分析，不能先读G再把删除G算作实测作者省工。

| 原profile与输出 | 拟议private / context | 同保证省G的静态条件 |
| --- | --- | --- |
| ALU4.out | private a/b；context mode；保持原guard mode==0 | h为模16和，任意z取a=z、b=0可达；active F=h，旧G=z，不依赖a/b。数学上满足资格。仍需全域普通/child/NI保证及明确角色划分，当前未执行新认证。 |
| FIR4.filtered | private x0/x1；context x2；guard恒真 | h=`wrap7(3*x0−2*x1)`，实际−38…37，无wrap；z=63/−64不可达。fiber一致但不满射，不能删原`wrap7(z+x2)`的域外承诺。 |
| FIR4.edge_value | private x1；context x0/x2；另有对z独立的输出策略 | 不能沿用filtered的私有集合；固定x0/x2时h也不满射。原edge对z独立，可直接NI＋普通功能确定该输出G；这是另一条frame要求，不是满射资格通过。 |
| TD8全部三个输出 | private reward/next/gamma；context value/alpha；guard恒真 | h=R的实际范围−2168…2151，远小于signed17。普通输出均由h/context决定，但每个context下仍有覆盖洞，不能整体省G或缩小B。 |

FIR的必要区别有具体手算见证：x2=0时，`(x0,x1)=(0,0)`与`(2,3)`同给h=0，edge却为0/2；若把x0也禁止给edge，就会拒绝原合法要求。filtered另可在仅z=63时把结果加1再wrap，普通功能与NI仍成立，却违反原G。

TD乘积范围为−32640…32385，floor除16后−2040…2024，再加reward得到上述R范围；端点可取得。只在z=65535时把return_value改为0不改变任何正常功能，也不引入私有依赖，却违反原G。下游完整局部域组合证明可能另行恢复响应，但不能把已有局部语义当作上游满射或新省工。

**限定计数：** 假设补齐角色声明后，ALU4一项数学资格成立；FIR4/TD8不能据R1b整体去G。这不是自动通过率或新模型结果，也没有证明当前工具已经生成或验证上述标签。NI＋同资格的强审计基线同样可保持Q隐式；不能强迫它为纯检查物化Q。

## 11. N23裁决

**停止把R1b作为当前结构生成论文的独立新核心，不追加相同小原型。** 标准SAT依赖判定已经覆盖fiber与Q构造，CUDD已有image/关系操作，NI模板也可不物化Q；数学资格适用还需作者额外明确角色/域。现有材料没有显示新的推导能力、绑定收益或实际建模节省。当前唯一整体适用的ALU原active G本来就是z，字段更少不代表实际作者时间更少。

这个裁决不声称全领域已有端到端R1b profile，也不以传统原语可实现就自动否决系统研究。若另行研究“合同编写与验证前端”，可以把覆盖资格、可信绑定、回退和成本作为不同的系统问题；那需要明确贡献定位及真正的同信息基线，不能沿用“更强结构生成”主张或把尚未测量的省工写成结论。原合同、全部历史结果和正文v0.3不变，整体SCI目标仍未完成。

收尾独立只读审查复核§9–11，未发现限定范围内的实质问题：代码能力没有扩大为端到端实现，逐输出分区及上游范围正确，停止理由没有把成熟原语等同于系统无价值。未运行软件、读取候选RTL/TB或修改文件。这个审查不建立创新性、实际省工或SCI充分性。

## 12. N24：不同贡献定位的讨论卡（未采纳）

**2026-10-22范围更新：用户已选择“先评审验证工具系统贡献”，随后明确“先可靠性，暂不主张人工省工”。** S0范围选择完成；[N37任务准备评审](contract-frontend-task-readiness.md)核现有工具、真实需求线索与强对照，S1/S2仍未闭合。此选择不等于正式采纳或进入S3–S5，也不启动新开发、模型实验或正文改写；下列阶段门继续适用。“未采纳”指未正式立项，不再表示尚未答复评审方向。

[N38后续复核](external-architecture-audit-task-review.md)已确认独立OpenTitan审核需求及已有框架；其时序单侧响应尚不适配当前纯组合全响应范围，S1合格任务与S2区别处理仍未验收。[发表身份新口径](publication-status-novelty-audit.md)将正式论文占用裁决与技术能力比较分开，不因发表未确认自动恢复旧开发投入。

**初版提出的取舍：** 是否将首篇的主要方法目标，从“新的结构生成决策机制”转为“明确架构合同的编写与RTL验证前端”。这是不同的研究问题，不是R1b修订或恢复；本节准备可评审范围，没有由此产生新工具、任务、实验或正文授权。原先允许少量结构变体的决定仍有效。

目标用户是审核已有多模块RTL的验证工程师或集成人员。输入为可信侧已明确的F/h/域/角色/guard及必要的完整G，外加已提交的RTL。输出是可追溯到这些声明与实际端口的标准验证义务、绑定检查和分项判词。审核对象保持原字节是这个工具问题的工作对象，不将此要求回填为旧生成任务的新限制。若工作只是从完整数学生成任意合法结构，N20直接编译仍是更直接的替代方案。

**可检验系统假设，尚无证据：** 在同语义、同允许实现集合下，一条显式关联数学角色、实际边界和标准验证义务的交接链，能减少合格合同交付中的配置错误或实际总成本。不得把schema、少写字段、包装命令行或工具运行秒数当作这项收益；也不主张新NI、函数分解或求解算法。

可复用旧原型的封闭AST、源快照、指定路径/端口核验、有限工件生成及来源记录。需要补的处理包括每输出角色与数学锚/实际边界的显式关联、域/guard/响应自洽检查、标准义务发射、绑定完整性核验和分项失败分类。非满射时保留完整G或明确资料不足；没有由正常F推定域外承诺的许可。哪些关联能机械推导、哪些仍由作者声明，要在实现前逐项登记，不能把手工输入隐藏进metadata。

| 顺序与依赖 | 输入材料 | 具体任务 | 输出文件（创建与验收状态见N37及唯一清单） | 验收与停止条件 |
| --- | --- | --- | --- | --- |
| S0，先讨论贡献定位 | 本卡、用户希望新增方法机制的原要求、N23停止理由 | 用户决定是否接受验证工具系统问题；未选定前不扩写为已成立创新 | 在本卡与唯一清单记录选择 | 接受此定位只决定范围，不自动成立创新、采纳新评分或启动实验 |
| S1，依赖S0 | 现有真实需求/作者工作记录、原完整合同、旧原字节RTL；N13字段审查 | 找到需要独立审核架构承诺的工作项；区分真实需求与人工资格反例，列作者实际交付步骤 | `contract-frontend-task-readiness.md` | 有可追踪的额外架构需求和待完成工作；若只有本研究手工反例或完整IR直接构造任务，停止，不以扩样本补需求 |
| S2，依赖S1 | 同一F/h/G/域/角色、N23强标准能力、固定工具版本 | 画出双方完全同信息/同接受集合的流程；基线允许模板、自动层次/别名处理和隐式Q；先写成本单位、失败口径及停止门 | `contract-frontend-comparison-plan.md` | 不用裸CLI对精心封装工具，不强迫基线手写可自动生成内容；明确区别处理，否则停止 |
| S3，依赖S2及明确开发范围 | 已限定纯组合/单边界/多输出的输入格式、旧checker、标准miter/cutpoint | 只补已登记的交接处理；明确每个语义字段的提供者、自动化步骤和错误状态 | `artifacts/contract-frontend-prototype-<run-id>/`中的原型、冻结计划和变更记录 | 不改旧oracle/评分；不支持或资源失败保留未决；实现不是研究效益证据 |
| S4，依赖S3及明确本地资格运行范围 | 预先固定的合法替代、条件委托/别名/输入交换、非满射/多输出策略及语义/角色/绑定负控制 | 独立核义务等价和实际端口关联，保留误接受、误拒绝、UNKNOWN、超时与未跑分母 | 同一artifact目录中的资格日志、结果与封存索引 | 已知语义/绑定负例若获通过，先停止效益评价；资格反例不冒充模型真实失败，旧12份全过仅作集成材料 |
| S5，依赖S4及预定成本研究范围 | 同准备度输入、可复用标准流程、事前冻结的作者/任务与操作记录办法 | 比较一次合格合同交付的编写、绑定、调试、复核主动时间与最终语义错误；学习/设置及复用成本分别记录并报告总成本 | 同一artifact目录中的交付记录和分析；审核后形成研究报告 | 工具秒数/字段数不替代人工时间；AI作者不能冒充人类工程师。没有实际成本/可靠性差异，则不主张系统效益，也不扩大模型调用寻找有利结果 |

以上文件名用于具体交付边界，不建立平行进度系统；阶段状态仍只维护论文唯一清单。运行样本数、工具过程上限、随机化/顺序、资源限制和实际成本判据应在相应计划中确定，当前没有这些数值，故不执行S3–S5。已有实验授权不扩展为任意新campaign。

同信息标准miter/cutpoint、可复用自动脚本，以及需要时的ABC/CUDD资格检查，均是正式强对照；不允许把已支持别名的工具故意配置成失败。实际功能、局部合同与自由响应的全部保证保持同一口径，不能以更弱合同更便宜作为胜出。仅是审计的基线无须输出Q或重新生成RTL；完整IR能直接完成的工作则保留确定性构造替代。

工程研究协作者只读审查已有三份报告后同样建议将端点限定为合格合同交付成本/错误，并指出当前三手工profile、12全过输出还不能证明真实需求或工时收益。故本卡**不是立项推荐或SCI创新验收**；用户若仍坚持新的生成决策机制，应保留此卡为讨论材料，在另外明确的真实开放设计问题上继续，而不把它冒充原目标完成。

初版独立收尾审查核本节、N24清单行及README，未发现当时范围的实质问题：待选定位、未执行状态、同信息强对照和S0–S5依赖一致，没有恢复R1b或暗示实测省工。该审查未新增检索、实验或文件修改。用户2026-10-22的答复及后续实际评审以本节开头更新和N37为准，旧停止结论不因选择评审而解除。
