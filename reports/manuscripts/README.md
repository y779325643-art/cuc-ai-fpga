# 稿件、讨论与论文准备

## 路线 A：机制验证新版初稿

[中文研究初稿 v0.5：SR2FPGA——契约驱动的 RTL 工程构建与反馈修复](D:/Project/cuc-ai-fpga/reports/manuscripts/drafts/contract-skeleton-repair-v0.5.zh.md)（2026-10-28）以规格解释、工程组合、行为诊断与修复回归的失败链组织论证，补核六篇原始文献，更新七个失败维度、机制对照与验收指标；已有 DW→PW 开发结果保留。[v0.4](D:/Project/cuc-ai-fpga/reports/manuscripts/drafts/contract-skeleton-repair-v0.4.zh.md) 及更早版本保留；下方按原时间记录此前研究及路线 B 进展。

## 历史研究与路线 B 记录

**N55修订版仍未通过真实资格：** [第二次结果与最小编译诊断](discussions/2026-10-26-tb-trace-audit-second-run-and-compiler-diagnosis.zh.md)记录两项编译异常退出且诊断为空、8项未运行；本轮2编译＋2版本、0仿真/模型，两轮累计4＋4。遗留sim.out未运行，不能覆盖失败退出。已准备6项仅编译的环境/入口/观测器对照，最多6编译、0版本/仿真/模型；尚未执行，不再凭静态推测补一版重跑资格。正文与旧证据保持。

**N54真实资格在编译处停止：** [实际结果与最小兼容修订](discussions/2026-10-26-tb-trace-audit-qualification-and-compatibility-fix.zh.md)记录两个观察器均因final调用task而编译失败，其余8位置按规则未运行；实际2编译＋2版本、0仿真/模型。旧结果保持，新版已将结束记录内联，10TB/合同/判定不变，Python检查及独立差异审查通过，123文件/2工具冻结但未重跑。下一步仅修订版10位置真实资格，最多20HDL＋2版本，两版累计最多22HDL＋4版本；正文保持，研究贡献未验收。下方N53为准备时点记录。

**N53实际轨迹审计准备完成：** 用户已确认收窄范围，按两个工作小时、0模型/HDL完成[只读观测、动态重放与资格准备](discussions/2026-10-22-tb-trace-audit-preparation.zh.md)。33项重放测试、11项执行器测试、29项独立合成检查通过；冻结123文件/2工具，旧证据与正文保持。10个手工资格位置尚未真实运行；下一阶段最多20HDL＋2版本、0模型/重试。FAIL与违例共存仍原因未归属，不由准备通过认定创新或投稿资格。下方N52“范围待选”保留为当时记录，已由本次用户决定推进到准备阶段。

**N52三条件设计评审已完成：** [源码误导增量与执行资格](discussions/2026-10-22-rtl-tb-misguidance-design-review.zh.md)补核软件直接近邻的正式出版登记，以及硬件checker/观测近邻；已列18拟议生成槽和54评价位置。原三条件最终判词表暂不执行：N50固定轨迹读取器不能解释自由TB实际刺激，错误ready还可能造成轨迹分叉。建议讨论收窄为“实际合法轨迹中已暴露违例未报告”的审计，先仅准备可信观测/诊断；108HDL只是候选开销，完整预算未定。0新HDL/被测模型、无实现或正文修改，新增评价范围待用户选择。

**N51实际资格检查已完成：** [三个任务执行结果与下一步](discussions/2026-10-22-three-task-qualification-results.zh.md)记录3参考通过、6人工控制均由实际语义违例检出，9位置全部完成；实际18HDL＋2版本、0模型/重试。独立原始trace复核和151文件/2工具哈希检查通过。三题具备有限开发评价资格，尚不建立模型收益或投稿贡献；下一步先评审“错误RTL是否误导TB”的具体问题与强对照，18次TB/108HDL仅为待评审建议，未启动。正文未改。

**N49筛选、N50准备已完成：** [现成资产资格筛选](discussions/2026-10-22-task-asset-screening-and-next-scope.zh.md)收敛到FIR8、DOT4-8、PEAK8，用户已确认新前瞻规范。[三个任务资格包](discussions/2026-10-22-three-task-qualification-preparation.zh.md)已包含公开合同、3参考/6控制、独立Python事务模型与93/109/324事件TB，准备检查及独立审查完成，151文件/2工具哈希冻结。实际HDL和被测模型调用均为0；下一阶段已固定9位置、最多18HDL＋2版本，不因准备完成称硬件资格通过或论文可投。正文未改。

**N48前瞻小试验已收口：** [源码可见性结果与裁决](discussions/2026-10-22-testbench-source-visibility-pilot-and-decision.zh.md)实际完成12次原生子agent生成（4RTL＋8TB）。4RTL均在有限参考检查中未见违例；7TB接受参考并检出2控制，3完整配对无差异，另1对因协调者提示换行偏差保留不可判。自然错误误验分母0/N/A；累计78HDL＋2版本包含两次已修复并保留的编译入口失败。测量流程可保留，当前源码可见性核心未通过；停止这两题扩采，不改正文。运输隔离／提示认证和复位文字限制均记录。

**N47有界审计已执行：** [完整结果与PI裁决](discussions/2026-10-22-acceptance-audit-results-and-publication-gate.zh.md)记录4对控制全部资格通过、13原TB全打印PASS、11项独立必要性质中3份历史工件确认违例、8份未见违例，另2份规格不足不可判。两份fork重复交付归同一机制，另确认一份skid重复累计。64HDL＋2版本调用，无新模型、无重试、225冻结输入保持；当前13份材料不足以直接支持SCI/SCIE投稿稿件，工程证据可保留，停止同源扩样并先具体化前瞻问题/真值，未改正文。

**N46队列与协议已准备：** [固定工件、公开义务和后续执行顺序](discussions/2026-10-22-acceptance-cohort-and-protocol.zh.md)绑定13份历史L3工程，明确6需求簇、8首轮/5修复路径及不可当独立模型试验的限制。11份拟查有限必要性质，join/TD缺规格保留不可判；强基线采用普通独立scoreboard。下一步先实现适配与正负控制，再在4小时上限内审计并作投稿资格裁决。本轮只有快照/静态核验，0新HDL/模型、未改正文。

**N45首日可行性检查已完成：** [执行结果与下一阶段](discussions/2026-10-22-acceptance-reliability-feasibility-gate.zh.md)记录两个历史家族的精确输入恢复、2参考＋9变异资格，以及单独复现的两份stream_fork交付错误（输入2、一路输出10次）。工程资格通过，已有实际问题支持继续工件审计；论文贡献与完整成稿资格仍待核。80次本地工具调用、0模型调用；未改正文、旧RTL或评分。

**2026-10-22全项目PI复盘：** 用户要求一周内投稿、本人投入70小时、Codex辅助、版面费不限。[全面进展与一周路线建议](discussions/2026-10-22-pi-project-progress-and-one-week-route-review.zh.md)将原备选B“现有多文件工程验收可靠性实证”列为首日8小时资格检查的首选。9家族对应45个独立参考变异，其他42个不同验证路径单列，旧向量缺失仍需解决。最新N43需新增时序语义适配，不默认是最快路线。用户已接受首篇系统／实证定位、优先一周投稿并先核可行性；该时点尚未执行；后续本地资格与诊断见上方N45，正文保持。下文保留既有路线及其历史授权。

当前论文任务的进度入口是[结构生成论文进度清单](discussions/2026-10-21-structure-generation-paper-checklist.zh.md)，[资产与路线备忘录](discussions/2026-10-21-minimum-scie-paper-route.zh.md)提供背景。**最新用户目标已授权持续研究、实验与SCI初稿，并明确让Codex子agent作被测生成模型。** 旧正文等待点已解除；创新性和正式运行资格仍需证据，发布、投稿及官方证据晋级没有自动授权。

当前候选聚焦“事前明确的条件性边界响应合同→实际RTL绑定→独立遵约审计”。[方法与实现深审：CPPL/HINT](discussions/structure-generation-paper/neighbor-deep-review-cppl-hint.md)与[VeriRefine/EQY](discussions/structure-generation-paper/neighbor-deep-review-verirefine-eqy.md)已核对完整方法和可取得的官方代码；自由切点不是新算法，近邻也不只是结构提示。实际方法增量仍需公平的成本/适用范围证据。

[跨任务实测结论](discussions/structure-generation-paper/cross-task-pilot-review.md)：三任务6份手写正负控制按预期资格；12份原生Codex首次输出全部通过；相同子文件的12个固定父构造也全部通过。本批没有观察到责任违约、提示方式提升或超越严格父构造的优势。全部位置、原始响应、运行审计、工具日志与源码哈希保留；属于开发研究，不能当总体效果或正式盲测。

[英文研究初稿v0.3](drafts/structure-responsibility-v0.3.en.md)整合当前方法、实际标准后端、16个完整局部域证明与新增强近邻；[独立核稿](discussions/structure-generation-paper/manuscript-v0.3-independent-review.md)已完成指定证据审查。[v0.2](drafts/structure-responsibility-v0.2.en.md)及[早期中文v0.1](drafts/structure-responsibility-v0.1.zh.md)本轮未改，保留为历史版本。[首轮带握手TD哨兵](discussions/structure-generation-paper/native-codex-development-pilot.md)的两份输出另列分母。当前初稿不是投稿资格或方法创新已验收，论文总目标继续。

新增[架构符合性近邻复核](discussions/structure-generation-paper/architecture-conformance-gap-review.md)核到SV-Gap的实际意图检查及RTL-Obliger的符号义务推导，进一步限制宽泛创新主张。[完整局部域验证](../../artifacts/responsibility-local-domain-proof-20261021-01/results.md)的16/16普通函数证明不等于TD父响应全域证明；[双输出别名资格](../../artifacts/responsibility-port-alias-qualification-20261021-01/results.md)也未复现当前force误判。用户已允许保持顶层功能的少量结构任务变体，[FIR/TD两个静态设计](discussions/structure-generation-paper/independent-method-core-review.md#7-最新范围两个保持完整顶层函数的结构变体)已完成，普通AST outlining仍是强替代，未启动新模型实验。[标准TD分区适配](../../artifacts/responsibility-td-compositional-baseline-20261021-02/results.md)按停止条件封存，累计4次资格均UNKNOWN、0原候选运行；不能据此宣称新方法收益。

[跨输出FIR语义接口复核](discussions/structure-generation-paper/semantic-interface-candidate-review.md)已通过4096正常输入与2048自由接口的纯数学核对，但不预置目标接口的小型非LLM搜索也找到了同一结果。[RTLRewriter/ASPEN深审](discussions/structure-generation-paper/semantic-rewrite-neighbor-review.md)确认新代数规则提议、证明与程序抽取已有直接先例。该恒等式不单独保留为新核心；可信接口交接的省工/可靠性仍是未验证的系统假设。本轮没有追加模型或HDL实验，v0.3未改。

[实际交接字段审查](discussions/structure-generation-paper/handoff-cost-decision-review.md)已区分已有自动化与人工语义：程序生成检查工件并核指定边界，完整角色/响应仍由作者给出；静态重复存在，人工工时优势未测。12固定父构造复用三份既有文件，未实现通用AST→RTL编译器。这些边界不改变既有候选评价结果。

最新[携带前提候选的标准强对照](discussions/structure-generation-paper/feasibility-standard-baseline-review.md)已实际完成7个Z3控制与2个metadata控制，普通SMT加同字段manifest覆盖本轮有限诊断；[独立审计](discussions/structure-generation-paper/feasibility-handoff-independent-audit.md)未见已实现的端到端处理差异或省工证据，因此停止将N15登记为独立新核心。[Veri-Sure v2](discussions/structure-generation-paper/neighbor-deep-review-verisure-assumptions.md)和[SynthTL](discussions/structure-generation-paper/neighbor-deep-review-synthtl.md)已按相关完整方法及固定作者源码复核，不能弱化其已有合同/人工确认/组合机制。原[真实协议核查](discussions/structure-generation-paper/real-handoff-bottleneck-review.md)、[协议近邻](discussions/structure-generation-paper/protocol-handoff-neighbor-review.md)、[方法卡](discussions/structure-generation-paper/feasibility-assumption-method-card.md)与[VClare/AutoSVA审查](discussions/structure-generation-paper/feasibility-assumption-neighbor-review.md)保留；真实UART尚未判错。范围问题仍待选择，未采纳新环境条件、未实施N15或追加模型运行，初稿仍为v0.3。

此前局部责任划分的决定：[有界评审结论为STOP](discussions/structure-generation-paper/local-responsibility-bounded-design-review.md)，该候选不追加实现。论文总任务继续，新的研究与原生Codex开发实验按最新授权推进；这不恢复已停止的程序/模型局部分区机制。

最新[两个局部计算合同变体](discussions/structure-generation-paper/local-option-variant-feasibility.md)补出了同型接口下的语义协调；[前置选择器](../../artifacts/responsibility-local-semantic-selector-prototype-20261021-01/results.md)通过2入口、39项限定检查，[独立审计](discussions/structure-generation-paper/local-option-selector-qualification-review.md)通过限定源码范围。[Parsel固定源码深审](discussions/structure-generation-paper/neighbor-deep-review-parsel-local-options.md)与[RTLScout/Spire深审](discussions/structure-generation-paper/neighbor-deep-review-rtlscout-options.md)保留强重合。决定性的[同信息零模型编译基线](discussions/structure-generation-paper/direct-math-compiler-baseline-review.md)已实际完成1发射+4HDL，FIR4096全域及TD327720预定位置均通过；不再扩本候选的完整LLM链或模型pilot。[方法卡](discussions/structure-generation-paper/contract-option-protocol-method-card.md)和[公平审计](discussions/structure-generation-paper/local-option-protocol-fairness-review.md)保留，协议收益与SCI创新仍未成立。现有时序任务的下一步范围问题待答，无新流量/PPA/时序约束，v0.3未改。

补充[真实案例溯源](discussions/structure-generation-paper/verisure-assumption-case-provenance.md)：Veri-Sure所报3项无依据约束没有公开逐项合同/审计映射，可配对复核0项，语义类型均UNKNOWN；不能把它们说成3个已知环境前提收窄案例或本方法已解决的失败。

最新[时序任务准备核查](discussions/structure-generation-paper/stateful-task-readiness-review.md)完成独立只读地图：旧TD实际公开prompt有明确单槽周期规则，但拓扑/状态分配固定；CRC/累加器guidance尚不足以冻结等价变体。HINT/Stepwise相关方法再审没有建立新gap，Stepwise的liveness范围与作者源码可得性均保留准确限制。正式时序范围待答，没有定义/开发/执行新任务；不能靠任务更难或更多模型样本补创新。

新增[N22/N23有界独立构思、强对照与裁决](discussions/structure-generation-paper/bounded-method-core-ideation-review.md)：条件NI已有直接先例；SAT重代入作者论文/ABC及CUDD固定实现进一步覆盖函数依赖、Q构造与关系投影。原三profile补明确角色后只有ALU的数学条件允许整体同保证省G，FIR/TD的实际上游不覆盖整个边界域。未发现新处理或实测作者成本收益，停止R1b独立结构生成核心，不追加同类原型；不声称已有端到端R1b前端或全领域无创新。无新被测RTL样本、工具实验、合同/评分或正文修改；不同贡献定位须先形成具体可评审方案。

[N24系统定位讨论卡](discussions/structure-generation-paper/bounded-method-core-ideation-review.md#12-n24不同贡献定位的讨论卡未采纳)已列明“明确架构合同的编写与RTL验证前端”的目标、输入输出、S0–S5依赖与验收。用户2026-10-22选择先评审这一工具定位，S0完成；正式立项尚未采纳。它研究合格合同交付错误/成本，不将省G或少字段当新增机制，未启动新开发/实验或修改初稿。

[N25期刊文章类型与交付门槛](discussions/structure-generation-paper/publication-route-evidence-review.md)区分政策、实际证据与未知：IEEE Access官方明示SCIE并接受应用/方法/负结果类型，仍需知识贡献与充分证据；SCP只核实出版商OSP轨道，现行细则/SCIE未确认；SoftwareX主源访问失败，均未升级为已确认达标目标。不以无新算法直接否决系统研究，也不以12全过或原型可运行认定可投稿。研究定位仍待用户选择，正文和实验保持原状。

[N26归档caller需求核查](discussions/structure-generation-paper/stateful-task-readiness-review.md#7-n26归档caller需求与实际模型输入分开核查)继续了原范围内的独立证据工作：193份有身份metadata中，CRC/累加器/Join共80目录但只有7份原字节需求版本，不能当80任务；两份Join长版还有接线文字差异。当前消息构造会叠加需求、平台与guidance，落盘requirement不认证完整历史输入；不能将其缺项说成模型实收缺项。未从eval/RTL/TB补语义，未采纳新时序变体、开发、运行新模型或改正文；N24待选不被扩大为整个项目阻塞。

[N27历史输入追溯](discussions/structure-generation-paper/stateful-task-readiness-review.md#8-n27完整历史输入的有界追溯收口)已有界收口，七版完整messages与生成代码绑定仍UNKNOWN，不再用旧日志扩查或当前模板补齐。[N28消费者前接口可实现性](discussions/structure-generation-paper/interface-realizability-candidate-review.md)只用原TD完整公开prompt，手工证明固定单消息至少9bit且可达到；不是模型失败或RTL验证。CorrectHDL已有HDL前分解/接口流程，标准SAT覆盖给定编码的判定，ABC已有编码与composition实际构造（局部≤11布尔输入，非宽RTL前端）。未找到新处理、现实压缩必要性或完整成本收益，暂不开发R2，不改旧R17合同、资源要求、初稿或评分。

[N29公开交接案例审查](discussions/structure-generation-paper/generation-gap-case-review.md)将原件与推论分开：ChipVerilog固定FPU前两缓存可核重复端口/候选语法错误及参考支持混合诊断，未认证历史messages或建立联合选择需求；ROME已有真实relay、逐模块工具检查与反馈，所报MIPS失败未找到配对工件。本地两个独立审查均未保留新案。N20只自动完成可信AST→RTL，原NL到可信F的准备成本仍未知；不因此认定新机制。无新被测生成/HDL/solver、任务采纳或正文修改。

[N30可信规格获取复核](discussions/structure-generation-paper/specification-acquisition-review.md)明确N19人工AST绑定后来的三输出组合TD8，N20不验证原单槽TD或N28完整变体；相关报告已澄清而不改旧运行。新增SynthTL保存交互案例与BenchMT原/修订文本，区分NL确认、给定DUT检查、需求补约束和实际源码保证；VeriRefine不是只核字符串，也未取得任意NL蕴含证明或作者代码。未以准备成本未知成立新核心，不为当前明确数学追加NL原型/实验，初稿仍v0.3。

[N31反例澄清近邻复核](discussions/structure-generation-paper/counterexample-clarification-neighbor-review.md)取得LTLTalk真实XOR、回答过滤及有界停止路径，另核nl2spec编辑重查和Spot无限语言差异能力。有限co-safe任务与无限P/Q明确分开；有界无见证不证明等价，单次回答不认证完整意图。通用反例澄清尚无额外规则，不开发或追加模型，人类交互未采纳；新增证据为进展，SCI新核心仍未验收，正文不变。

[N32独立构思与另三家族需求核查](discussions/structure-generation-paper/remaining-public-task-source-review.md)完成两份fresh-context弃权意见，另核193+9份一层metadata中MAC/匹配滤波/雷达的4需求/3原字节SHA。三种正文均只有单句，不能直接定义完整顶层或等价结构变体，也不认证历史模型只收一句。停止将这些功能名直接换入pilot；不以弃权票数认定领域无创新，无新被测调用/solver/HDL、任务采纳或正文修改。

[N33比较起点审计](discussions/structure-generation-paper/comparison-endpoint-audit.md)确认N19/N20实际共享同字节可信完整F，编译强对照在现范围内公平；CPPL还须由模型把docstring行为转IR，不能用N20声称胜过其完整流程。修正N20末段过强恢复门：同能力也可有真实总成本/可靠性价值，但当前未测证据不成为收益。维持旧候选停止和v0.3正文，不改定位/评分或追加实验。

[N34公开串行题面与适配候选](discussions/structure-generation-paper/external-serial-adapter-candidate-review.md)取得官方WaveDrom并定位停止位后的TFF观察错配，保留“从递推和窗口推导屏蔽/旧值捕获”的待核步骤C34。题目不强制parity或多文件，手算非模型失败；Filament已有实质控制生成，Greaves协议适配仍须完整深核，不能据有限未覆盖认创新。外部任务/新实现/被测实验未采纳，初稿仍v0.3。

[N35强近邻与同信息静态对照](discussions/structure-generation-paper/state-adapter-standard-baseline-review.md)已核Greaves/Nam的实际协议乘积适配，区分7/8页作者版本及源码UNKNOWN。相同递推、窗口和相位信息下，普通控制覆盖当前屏蔽/捕获；显式反相解码也合法。尚无额外处理或完整成本收益证据，停止当前C34单独核心的开发投入，保留相位案例。无新模型/HDL/solver或正文修改，SCI目标未完成。

[N36作者工件与请求绑定](discussions/structure-generation-paper/generated-artifact-binding-review.md)新取得VeriGraphi固定输出样本，定位图内方向问题、图/顶层来源差异及JALR局部状态缺口；未闭合同次生成或论文结果绑定，不把静态快照当运行失败。另深核2026-10-19配置生成研究及固定计分代码，区分config exact构造性保证、组合SAT、拒绝口径与真实样本分母。仍无新方法核心，不采纳外部CPU/ECC任务或新增模型；原稿和旧结果保持。

[N37工具系统定位与任务准备](discussions/structure-generation-paper/contract-frontend-task-readiness.md)按用户选择完成只读评审：已有完整合同→有限检查，尚无自动语义取得或通用标准义务编译；原字节RTL审核与重新构造不同，别名适配故障是真实线索但不是收益。用户已选择先可靠性、暂不主张人工省工。[N38独立需求复核](discussions/structure-generation-paper/external-architecture-audit-task-review.md)已找到OpenTitan明确的错误到告警承诺及既有验证框架；其时序／单侧合同尚不适配当前完整组合范围，S1同类任务和S2区别处理仍未验收。未进入开发、模型或正文修订。

[N38发表状态审计](discussions/structure-generation-paper/publication-status-novelty-audit.md)按用户“只有明确发表才判创新占用”的新要求分离身份：本轮七项中AutoSVA正式发表确认，其余六项正式发表未确认。HINT会议日程、SV-Gap软件DOI都不升级成论文出版；技术深审与强对照继续保留。AutoSVA限制宽泛义务前端主张，但不自动否决全部系统贡献；未确认发表也不反证原创或撤销实测/任务资格的停止理由，SCI核心仍未验收。

[N39交付可靠性复核](discussions/structure-generation-paper/verification-delivery-reliability-review.md)取得OpenTitan历史响应检查未读实际FSM的直接修复，未冒称实际误通过；另核STTT空泛性方法。独立手推证明正常回代/恢复/自由PI仍可漏掉消费范围错误，但标准优化前wrapper同样可补齐，尚无新增处理。当前不把这组检查登记为新核心或追加开发；保留后端资格意义，无新实验、任务采纳或正文修改。

[N40配置与义务完整性](discussions/structure-generation-paper/configuration-obligation-completeness-review.md)新核OpenTitan声明/注释/测试计划对账，以及OCRA正式合同细化与义务生成；参数手册能力与2015发表内容分开。独立候选把实际触发域当免费输入，纠错后撤回：assert enable不等于义务覆盖，给定语义的蕴含检查也属标准能力。停止简单对账/蕴含核心投入；实际编译语义关联仍待定义，仅准备工件审计边界，未采纳新审核对象或改正文/实验。

[N41实际监测工件方法卡](discussions/structure-generation-paper/compiled-monitor-audit-method-review.md)已核Yosys现存结构接口及lowering条件，明确来源不能由最终JSON补回；用共同开放观察接口核实际绑定和错误报告行为，避免正确DUT掩盖漏检。IJCAR2020已正式验证参考监测器并差分实际工具，标准比较算法不当新。当前只保留待验证的系统交接假设；用户在N42期间已选择先评审验证工件，后续可核两个真实案例及强对照，尚无案例验收/效益或新运行；SoftwareX[官方评审材料补核](discussions/structure-generation-paper/publication-route-evidence-review.md#6-n41softwarex官方评审材料补核索引仍未确认)不消除SCIE未知。正文保持原状。

[N42初稿证据审计](discussions/structure-generation-paper/manuscript-v0.3-current-evidence-audit.md)在范围待答期间完成独立工作：重算原24条评价和24条局部证明记录，确认既有有限结论可保留；未来须补N20实际normal-only编译强对照、可信数学起点及发表身份分层。N20不证明G/周期，旧12原生＋12固定父和16局部义务不能改称新工具可靠性分母。列出可复用材料与修订差距，没有改正文或重跑实验；用户后续答复允许的案例只读准备另记，不追认为既有实验。

[N43两例工件评审](discussions/structure-generation-paper/verification-artifact-two-case-readiness-review.md)按已选范围取得OpenTitan真实CheckerFsmAlert_A及PULP cc_fifo内联协议断言，闭合实际端点和宏语义，另核两项目公开构建清单。已有build入口，尚无选定配置的完整解析/编译资格；30周期等参考细节需独立信任，异步复位/四态支持未冻结。标准监测器强基线允许同样自动化；目前没有新增处理或配对可靠性证据，不将两项来源当已通过任务，也不继承旧组合checker资格。只读评审已完成，未开发、实验或改正文。

用户已将协议候选收窄为仅连接来源选择。[§11实际有界验证](discussions/structure-generation-paper/new-core-screening.md#11-连接来源限定版实际有界验证)补充fork/join参考握手枚举、完整通道分组与普通匹配对照，以及FIR符号累加图。fork/FIR有条件性样例，但公共事实、FIR内层冻结及真实运行资格尚未闭合；P02创新性未验收，不直接开发或运行模型。此前M06配置并发草案保留为历史备选，不是当前执行对象。

此前连接候选的[创新性与可行性裁决](discussions/structure-generation-paper/connection-choice-decision-review.md)已列出逐步输入、任务、输出、验收和依赖，并补充原文查新与全部80个候选子池的强对照。普通匹配/线性链直接构造与枚举全部等价，当前不建议直接作为最低补工SCIE主核心，不进入完整开发或主实验；保留协议假设，不认定完全无创新。未运行模型、HDL或正文。

[方法卡 v0.2](discussions/structure-generation-paper/local-responsibility-method-card.md)、[案例资格准备](discussions/structure-generation-paper/hybrid-case-qualification-plan.md)、[原对照建议](discussions/structure-generation-paper/study-protocol.md#10-局部责任划分当前主对照建议)和[机制比较](discussions/structure-generation-paper/mechanism-options.md)保留为历史工程参考，不能作当前执行计划或创新成立的证据。

| 当前准备材料 | 文件 |
| --- | --- |
| 资产、任务与来源 | [资产审计](discussions/structure-generation-paper/asset-audit.md)、[候选任务](discussions/structure-generation-paper/task-readiness.md)、[公开范围](discussions/structure-generation-paper/release-scope.md) |
| 定位与协议 | [相关工作证据矩阵](discussions/structure-generation-paper/related-work-matrix.md)、[研究协议准备稿](discussions/structure-generation-paper/study-protocol.md) |
| 最小补工 | [合同复用表](discussions/structure-generation-paper/contract-reuse-map.md)、[拟实施范围](discussions/structure-generation-paper/implementation-scope.md) |

本目录还保留历史论文草稿、内部讨论、阅读笔记与技术方案，不能作为当前实现或实验结果的证据。
按用途分组，保留原文件名和原字节；未根据文中的数值或结论更新任何研究声明。
Word 分类核对了文档开头；PDF 本轮按标题归类，未全文审读。

| 分类 | 文件 | 说明 |
| --- | --- | --- |
| 论文草稿 | [英文稿](drafts/HNAI_FPGA_IEEE_Access_Manuscript_1_副本.docx)、[中文翻译](drafts/HNAI_FPGA_IEEE_Access_Manuscript_1_中文翻译.docx) | 历史 IEEE Access 稿件及译文，不代表当前 TRETS 计划或投稿状态 |
| 讨论记录 | [IR 层讨论](discussions/关于IR层的讨论报告_副本.docx)、[记录](discussions/记录.docx) | 预研方向与工程问题讨论 |
| 阅读笔记 | [Spec2RTL](reading-notes/Spec2RTL.docx) | 对 Spec2RTL-Agent 的介绍与理解，非论文原件 |
| 技术笔记 | [研究路线报告](technical-notes/从系统需求到完整%20FPGA%20工程生成的%20AI%20研究路线报告.pdf) | 系统需求到 FPGA 工程的方向材料 |
| 技术笔记 | [天授 RL 方案](technical-notes/天授RL算法FPGA实现方案.pdf) | RL 算法实现方案 |
| 技术笔记 | [HDL 实现分析](technical-notes/五种主流强化学习算法FPGA_HDL实现分析.pdf)、[轻量化实现代码](technical-notes/五种主流强化学习算法_FPGA-Verilog_轻量化实现代码.pdf) | 强化学习算法的 FPGA 实现材料 |

当前研究入口见[文档导航](../../docs/README.md)，有执行证据的报告见[报告索引](../README.md)。
