# 契约约束多文件 FPGA 结构生成论文：进度清单

更新日期：2026-10-26。本文是本篇缩减研究的唯一进度清单；[资产盘点与路线备忘录](2026-10-21-minimum-scie-paper-route.zh.md)保留背景、依据和历史候选方案，不重复维护后续阶段状态。

**N55再次编译失败，诊断方式收窄：** [修订版结果](2026-10-26-tb-trace-audit-second-run-and-compiler-diagnosis.zh.md)确认2项异常退出、诊断为空，8项未运行；本轮2编译＋2版本、0仿真/模型，累计4＋4。失败留下的sim.out未执行，尚无功能或漏报结论。六项最小编译对照已准备，下一轮最多6编译、0版本/仿真/模型，先区分当前入口、TB与观测器组成的影响；不再仅凭静态猜测修补并重跑资格。正文保持。

**N54真实运行未通过，兼容修订已准备：** [执行与修订记录](2026-10-26-tb-trace-audit-qualification-and-compatibility-fix.zh.md)确认两个nominal均因观察器final调用task而编译失败，8位置保留未运行；实际2HDL编译＋2版本、0仿真/模型。最小修订在新目录内联相同Z记录，10TB及语义/阈值不变；33/11/29项Python检查和独立差异审查通过，123文件/2工具冻结，按0自动重试规则未运行新版本。下一步仍为同10位置真实资格，最多20HDL＋2版本；旧成本保留，正文未改。下方N53为此前准备状态。

**N53准备已完成，真实资格未运行：** 用户选择“收窄审计，先做准备”，[实际轨迹审计包](2026-10-22-tb-trace-audit-preparation.zh.md)已实现只读端口观测、实际ready合法性与动态数学重放、五类手工正负材料和有界执行器。33项重放测试、11项执行器测试、29项独立检查通过，123文件/2工具冻结；实际0HDL/版本/模型，正文和旧证据保持。下一阶段为10个位置、最多20HDL＋2版本、0模型/重试的真实资格验证；尚无新候选效果或SCI贡献结论。下方N52待选状态是历史时点，本次授权仅推进准备。

**N52设计评审完成、范围待选：** [三条件增量与执行资格](2026-10-22-rtl-tb-misguidance-design-review.zh.md)新增正式软件出版证据、硬件近邻及独立设计审查，预列18生成/54评价位置。宽泛“错误代码误导测试”有直接重叠；仅PASS/FAIL也不能区别未暴露与漏报，错误ready会改变实际输入轨迹。原18次不执行，108HDL不含新增观测资格。建议仅准备实际轨迹审计的可信组件，2工作小时、0HDL/模型，须用户明确选择这一评价范围；本轮0新运行、未实施或改正文，旧资格不变。

**N51实际运行完成：** [三任务资格结果](2026-10-22-three-task-qualification-results.zh.md)中3参考通过93/109/324事件，6人工控制各有实际数值/事务反例，9位置全完成，无不可用/未运行。实际18HDL＋2版本、0模型/重试；独立原始trace审查与151冻结文件/2工具哈希核对通过。有限开发资格成立，模型效果与SCI贡献未成立；下一步先评审受控错误RTL对TB判断的影响问题及强对照，具体新生成预算仍未冻结或执行，正文未改。下文N49/N50保留准备阶段时点记录。

**N49筛选、N50准备已完成：** [现成任务筛选](2026-10-22-task-asset-screening-and-next-scope.zh.md)完成当前三家族、旧九家族/T5及已有外部案例核查；用户已确认FIR8、DOT4-8、PEAK8新前瞻规范。[资格准备包](2026-10-22-three-task-qualification-preparation.zh.md)已完成公开合同、3参考/6控制、独立事务模型与93/109/324事件、执行器和独立审查，151文件及2工具哈希冻结。Python开发检查通过；本轮0 HDL、0被测模型，硬件资格仍未运行。下一阶段固定9位置、最多18HDL＋2版本、0重试/模型；不能由准备成功直接认定论文贡献，正文保持。

**N48已完成的前瞻试验：** [测试台源码可见性小试验](2026-10-22-testbench-source-visibility-pilot-and-decision.zh.md)完成12次原生子agent被测生成（4RTL＋8TB）；4RTL有限参考检查未见违例，7TB均接受正确参考并拒绝两固定错误控制。3完整配对无观察差异，最后A因协调者提示换行偏差阻断4评价行，保留总分母且不补抽；不可由A3／4、B4／4说B更优。自然错误误验分母0/N/A。累计78HDL＋2版本含两次保留的入口编译失败；01的54、02的57冻结输入及16候选源保持。测量能力可保留，源码可见性作为当前论文核心暂不通过，停止在两资格题上扩样；下一步先核代表性现成任务的规格／独立参考与具体系统问题，不改正文或官方证据。

**N47已完成的审计：** [全队列审计与投稿资格裁决](2026-10-22-acceptance-audit-results-and-publication-gate.zh.md)完成4对正负控制、13原TB回放和11项有限性质检查，64HDL＋2版本调用、0模型调用。全部控制资格通过；原TB全打印PASS，但独立复核确认C05/C10两份fork重复交付、C12一份skid重复累计，共3工件/2机制；其余8份有限检查未见违例、2份欠规格不可判。225冻结输入保持。工程与问题存在性通过，仅据13份历史材料直接形成SCI/SCIE投稿稿件不通过；停止扩大同源旧队列，不改正文，新的前瞻研究问题/真值与对照仍须具体化。用户已允许必要的新模型使用子agent，本批无需新增样本。

**N46已完成的准备：** [队列与有限验证协议](2026-10-22-acceptance-cohort-and-protocol.zh.md)固定全部13份历史L3工件，6需求簇/5任务类，13终态包无字节重复但不代表独立采样；8首轮路径与5修复路径分开。163份输入复制与169个来源路径哈希核验通过。拟仅对11份counter/accumulator/fork做条件性必要性质检查，join/TD语义不足保留不可判；强对照为普通可信scoreboard。下一阶段4小时/最多64 HDL＋2版本查询的计划尚不可执行，先做适配与正负控制资格；本轮0 HDL、0模型、正文未改，论文贡献仍未验收。

**N45已执行结果：** 首日检查已执行，详见[资格报告](2026-10-22-acceptance-reliability-feasibility-gate.zh.md)。FIR/MAC的16向量文件及bundle承诺精确恢复，2参考通过、9人工变异均被强基线与原固定测试拒绝，无包装器增益。来源审计另复现两份历史fork的真实重复交付（2输入、一路10输出），第三份不同实现通过同轨迹。13份历史L3快照59/59文件绑定，原始模型交互仍未认证。条件进入工件队列与验证协议准备，贡献/完整研究未验收；本轮无新模型、无正文。

**N44用户决定：** 在一周70小时的限制下，用户已接受首篇以系统／实证贡献为主、优先一周投稿、先核可行性。下一阶段按原备选B“多文件工程验收可靠性实证＋工具交付”准备首日8小时资格检查；新增生成机制留到后续。完整路线比较与每阶段输入、任务、输出、验收和依赖见[PI复盘](2026-10-22-pi-project-progress-and-one-week-route-review.zh.md)。此决定确定首篇贡献定位；下文为既有路线记录，具体研究与运行协议尚待资格检查，本轮不启动新实验或正文。

**最新用户目标与授权：持续推进，允许实验，找到gap与创新点，完成SCI初稿；并明确要求Codex子agent直接充当被测生成模型。** 这一最新指令解除此前正文等待确认点，授权为该目标开展必要本地开发实验和初稿准备。SCI/SCIE、证据真实和首次生成无反馈的既有要求保留；不自动授权外部发布、官方证据晋级或无上限付费运行。旧候选评审的结论仍有效，不因允许写作而认定创新成立。

**创新性裁决更新：用户明确“只有明确发表了的工作才考虑我们的创新性被占用”。** 按可核正式期刊／会议出版记录执行；预印本、录用／日程、软件仍需技术比较和引用，但不单凭其身份判占用。当前七项[发表状态审计](structure-generation-paper/publication-status-novelty-audit.md)确认AutoSVA正式发表，其余六项未确认；不是全领域普查。历史技术判断保留，只有未核正式发表重叠这一占用理由不继续有效；现有实测强对照、任务资格和区别处理不足的停止理由仍有效。

当前范围：SCI/SCIE；首次生成、无反馈修复；仅对事前明确的架构承诺判违约。当前已实现的研究为**生成前明示条件性边界响应合同，生成后绑定实际RTL并独立审计**；新增方法核心尚未验收。它复用成熟切点技术，暂按“契约遵约实证审计＋自动检查工具”评估，不主张新求解算法、物理资源保持或已证明提示提升。本篇是独立开发研究，不替换现行`paper1-v2.2`，不继承其官方任务资格。

**当前实际完成：** [英文研究初稿v0.3](../drafts/structure-responsibility-v0.3.en.md)已整合标准后端、完整局部域证明及新增强近邻；[v0.2](../drafts/structure-responsibility-v0.2.en.md)和[早期中文v0.1](../drafts/structure-responsibility-v0.1.zh.md)本轮未改，作为历史版本保留。三任务12原生首次输出与12程序父构造全部通过既定有限检查；另16个原child义务全部获完整局部域SAT证明。全部分母独立记账，不把追加验证变成新模型样本。[三个公开组合子图与六份提示](../../../artifacts/codex-responsibility-cross-task-20261021-01/plan.md)及[独立整数预核](../../../artifacts/codex-responsibility-transport-20261021-01/preflight-result.json)保持原字节；数学预核仍不等于RTL证明。

**最新范围决定：** 用户明确允许在保持顶层功能的前提下，设计少量可选择模块分解/接口的结构任务变体；本次只确定研究范围，不启动新一轮模型实验。旧固定任务、原始输出及结果不回改。N10的FIR/TD两个静态设计及N12跨输出语义重组复核均已完成；未将新增选择空间本身当作创新。

当前执行顺序如下。所有输出路径相对仓库根目录；状态随原始运行记录更新，不将文档准备或手写控制当作模型效果。

| 阶段 | 输入材料 | 具体任务 | 输出文件 | 验收标准 | 依赖与状态 |
| --- | --- | --- | --- | --- | --- |
| N1 近邻与贡献边界 | CPPL/HINT/HierSVA、经典切点、VeriRefine及EQY原文 | 核对前置意图、实际边界绑定、独立响应检查的重叠；限定贡献 | 本清单；`structure-generation-paper/new-core-screening.md`与初稿相关工作 | 不声称首创切点；不能以未找到完整等价论文证明原创 | 已完成指定近邻复核；原创性仍有不确定性 |
| N2 公开任务与同信息提示 | 现有ALU/FIR/TD公开算术子图、用户接受的显式承诺范围 | 固定三组合profile、C0/C1相同事实、边界全域和有限评价域；记录改动与复用 | `artifacts/codex-responsibility-cross-task-20261021-01/{plan.md,public-tasks.md,prompts/,profiles/,input-manifest.json}` | 两条件均知完整附加合同；不含测试/参考代码；生成前哈希封存 | N1；已准备并做独立数学预核 |
| N3 可复用检查器资格 | 闭合JSON AST、Yosys实际层次/端口、手工mini正负控制 | 自动绑定、正常与替换检查、force/release/恢复、guard覆盖与失败分类 | `artifacts/responsibility-prototype-20261021-01/` | 合法alias/输入交换不误拒；旁路被拒；未知/disabled不冒充通过 | N2；修订mini及新版透明alias资格完成；原8次夹具编译失败保留，新版6全宽控制与24评价进一步资格 |
| N4 实际位宽任务资格 | N2冻结profile、独立忠实/旁路RTL、N3检查器 | 三任务逐个正确对照通过后再负对照；固定父构造资格 | `artifacts/responsibility-full-profile-qualification-20261021-01/` | 三个全宽正例通过；等价旁路正常功能通过而附加责任失败；每工具30秒 | N2/N3；6/6正负控制资格完成，保留实际工具证据 |
| N5 原生首次生成 | 六份冻结提示、合格profile、[执行范围](../../../artifacts/codex-responsibility-transport-20261021-01/execution-scope.md) | 固定3×2×2=12位置、fresh context、无工具/无修复指令；白名单保存、实际工具使用与token审计 | `artifacts/codex-responsibility-transport-20261021-01/{trials/,preflight-result.json}` | 所有预定位置留分母；保留原始响应与失败；只报告观察到的隔离/配置能力 | N4；12/12已首次生成、解析及运行审计；10个不同源码组合。无新增外部付费API |
| N6 强基线与解释 | N5所有响应、同合同手工miter、固定父模板 | 统一执行原候选及预先规定的“同子文件＋固定父”对照；分开普通功能与责任；记录耗时/覆盖 | N5目录评价与汇总；`artifacts/responsibility-manual-miter-20261021-01/`；`artifacts/responsibility-standard-cutpoint-20261021-01/` | 不把程序父当修复；不删失败；不将等价miter包装成更弱基线；全部通过也如实保留 | 跨任务24评价全过；两提示各6/6。标准Yosys在ALU上实际证明native、检出wrong_mode；旧delegate自由响应因别名适配缺陷保留UNKNOWN，共6调用，不外推FIR/TD |
| N7 SCI研究初稿与验收 | N1–N6/N8/N9实际证据、近邻和限制 | 形成完整英文研究初稿；逐主张追溯、独立评审 | `reports/manuscripts/drafts/`及`structure-generation-paper/manuscript-review.md` | 新增量与真实证据相符；不以稿件存在代替充分研究；SCI/SCIE录用不作保证 | 英文v0.3约5500正文词；[独立审阅](structure-generation-paper/manuscript-v0.3-independent-review.md)完成，所核事实/语义无剩余Blocker/Major；创新增量仍未验收 |
| N8 实质方法增量复核 | N6标准后端、完整响应建模负担、SV-Gap/RTL-Obliger等实际近邻 | 评估可省工机制及同信息强替代，核对实际方法与实现 | `structure-generation-paper/method-increment-followup.md`；`structure-generation-paper/architecture-conformance-gap-review.md`；`structure-generation-paper/neighbor-deep-review-formalrtl-refinement.md` | 不把普通AST替换、完整局部验证或工具名称当新机制；每项须有具体处理差别、真实案例及反驳条件 | 六项架构符合性复核及FormalRTL/Stepwise完整方法深审已完成；另核VPID原文。语义分解与组合义务已有实质先例，当前无新核心验收 |
| N9 已公开局部合同的完整域补核 | N2公开局部数学、N5原样child文件、独立正负控制 | 标准SAT验证16个预定模块义务；四类先正后负资格，全部不改候选 | `artifacts/responsibility-local-domain-proof-20261021-01/` | 最多24次Yosys、每次30秒；保留未知/未跑；不缩域、不增加模型调用、不回改旧24结果 | 已完成：4正证明＋4负有效反例＋16原child证明，恰24次调用，0超时/未知；主审核202文件哈希与原始判词一致。补覆盖，不作为新方法 |
| N10 少量结构任务变体 | 用户最新范围决定、现有FIR/TD顶层函数与数值边界、N8实际近邻 | 至多两个变体，开放模块分解/接口；列两种合法结构、一个错误组合、强直接构造/IR基线和LLM相对程序基线的实际贡献 | `structure-generation-paper/independent-method-core-review.md`及后续方法卡（仅有保留机制才创建） | 顶层功能不变、不加隐性时序/资源限制、不靠造失败；普通编译同工同能则只留资格题，不宣布新核心 | [两个静态变体及饱和接口候选评审](structure-generation-paper/independent-method-core-review.md)已完成；普通AST outlining仍为同机制强替代，暂只留资格题。未实现或运行新模型 |
| N11 证明分区的直接强对照 | 原4份TD update原字节、已合格局部reference、3手写资格控制 | 不改生成结构，在现有E输出内直接分区：先证明E相等，再切E证明条件U相等；核真实别名/原输入保持 | `artifacts/responsibility-td-compositional-baseline-20261021-01/`与`-02/` | 最多7次Yosys，30秒外限/两SAT各10秒；分区反例不冒称普通功能错；旧全域证明不重跑；不以单次耗时证明统计加速 | 已按停止条件封存：累计4/7资格过程均因释放PI与实际消费者脱离而UNKNOWN，0原候选执行；剩余3次不用。主审核69＋41封存文件及原始绑定一致。强对照未完成，不支持新接口或加速收益 |
| N12 非字面子式的语义接口复核 | N10的FIR顶层函数、已有edge输出、RTLRewriter及最接近代数重写工作 | 静态评审跨输出重组e=x0−x2、t=2x0−x1、f=2t−e；核精确位宽、非LLM线性共享强替代、作者实际方法与实现 | [静态设计与可重算基线](structure-generation-paper/semantic-interface-candidate-review.md)；[RTLRewriter/ASPEN深审](structure-generation-paper/semantic-rewrite-neighbor-review.md)；`artifacts/responsibility-semantic-interface-static-20261021-01/` | 不把恒等式或三对四个加减号当PPA收益；同信息强替代成功则不据本例主张新增代数能力，但不以成熟原语/LLM可替代性直接否定系统贡献 | 已完成：4096正常输入、2048自由接口数学一致；不预置t的151向量基线自动找到同一接口。主审重算完全一致，并独立核作者RTL配对及ASPEN原文。停止该恒等式单独作为新核心，交接省工假设未验。无新模型/HDL调用，初稿原字节保持 |
| N13 可信交接的实际输入与省工假设 | 已实现checker、三profile、标准ALU miter/cutpoint实际代码与父构造 | 逐字段核对谁提供数学/role/路径/位宽/映射，程序实际推导什么；比较同信息标准工具与直接构造，核normal函数是否唯一决定自由响应 | [实际字段与交接审查](structure-generation-paper/handoff-cost-decision-review.md) | 每项差别有实际字段/代码行，未计时不声称减少人工工时；不把工具适配失败计为方法收益；无模型/HDL调用、无实现改动 | 已完成：当前程序执行完整作者合同，不推导role/guard/响应；标准ALU需同样语义。三inactive与normal相同，存在静态重复，但无工时证据；12固定父复用三份文件，非通用AST emitter。主审核实际消费代码、miter与重复树一致，省工增量未成立 |
| N14 真实协议交接与同信息能力 | 公开family recipe/guidance、UART/FIR/stream接口；HINT/层次IR、CIRCT/Calyx | 寻找既有需求允许的两种结构、跨决策约束；核读相位/退休/采样锚点及传统lowering | [资产核查](structure-generation-paper/real-handoff-bottleneck-review.md)；[有界设计](structure-generation-paper/next-mechanism-bounded-design.md)；[近邻核查](structure-generation-paper/protocol-handoff-neighbor-review.md) | 不默许改变周期、溢出或sideband采样语义；实例与完整通道整体核验，不把标准wrapper改名新机制 | 已完成：FIR等价累加顺序仍可直接构造；UART真实读相位耦合但替代时序许可未定；采样fence缺需求锚。0个已成立未满足瓶颈，未启动模型/HDL或实现 |
| N15 携带前提的结构计划候选 | N14的UART摘要/环境缺口；明确声明的容量控制；VClare/AutoSVA/Pacti | 区分已采纳与推导前提，设计行为前的计划判定/见证/待定交接；核容量安全与公平性区别 | [方法卡](structure-generation-paper/feasibility-assumption-method-card.md)；[近邻深审](structure-generation-paper/feasibility-assumption-neighbor-review.md)；`artifacts/responsibility-capacity-assumptions-static-20261021-01/` | 新假设不自动进入prompt/验证/统计；充分前提不满足不自动等于不可能；不把FIFO深度当系统总容量；数学控制不冒充真实任务或模型效果 | 静态卡与有界数学资格完成：320窗口轨迹（129满足窗口界、191有超界前缀）、17信用单步；主审独立组合计数、见证守恒和冻结哈希一致。无模型/HDL。VClare及AutoSVA已有生成前澄清/义务，Pacti是强标准基线；系统增量未验。已向用户提出是否纳入事务/容量合同的范围讨论，未擅自采纳 |
| N16 同信息标准基线与独立核心审计 | N15同一有限事件模型、同字段来源/采纳manifest；Veri-Sure最新版与SynthTL主源/固定代码 | 先冻结7个Z3控制与2个metadata控制，核环境非空、proposal不提升、保守充分条件；独立审计实际链路与系统增量 | [标准对照](structure-generation-paper/feasibility-standard-baseline-review.md)；[独立审计](structure-generation-paper/feasibility-handoff-independent-audit.md)；[Veri-Sure深审](structure-generation-paper/neighbor-deep-review-verisure-assumptions.md)；[SynthTL深审](structure-generation-paper/neighbor-deep-review-synthtl.md)；`artifacts/responsibility-capacity-standard-baseline-20261021-01/` | 最多7过程、每次10秒；全部位置留账；空环境不算安全；无模型/HDL。普通流程能做同判定不自动否定系统论文，仍须实际差异/工作量证据 | 已完成7/7过程，3溢出见证、3窗口安全、1inconsistent；另2metadata UNKNOWN，0未跑/重试/超时。主审核12冻结及46封存文件、7原日志、10SAT见证与7组组合计数。标准流程覆盖本轮有限诊断；N15无已实现端到端链/省工证据，停止将其登记为独立新核心，不改变待选范围或旧结果 |
| N17 近邻真实约束案例的来源复核 | Veri-Sure v2作者人工审计与同一固定仓库 | 最多核3个新增约束错误项，配对公开需求与合同；区分环境收窄、输出限制、设计默认及golden纠正 | [案例溯源](structure-generation-paper/verisure-assumption-case-provenance.md) | 无配对原件就UNKNOWN；不由汇总数编造案例、因果关系或本方法收益；不运行框架/模型/形式工具 | N16；已完成限定范围：论文未点名，固定提交完整661文件中无原合同/audit/run。可配对0项，3匿名错误项类别与逐项纠正均UNKNOWN；主审独立复核文件树。不是3个已知环境收窄实例 |
| N18 同型接口下的局部合同兼容 | 用户允许的FIR/TD分解变体、原normal函数、Parsel/Stepwise/SynthTL与RTLScout原文及代码 | 找到两个跨局部语义选择例，保留合法重算；冻结一次数学资格；深审真实局部组合与公平对照，形成具体方法卡 | [两例可行性](structure-generation-paper/local-option-variant-feasibility.md)；[公平性审计](structure-generation-paper/local-option-protocol-fairness-review.md)；[Parsel深审](structure-generation-paper/neighbor-deep-review-parsel-local-options.md)；[RTLScout深审](structure-generation-paper/neighbor-deep-review-rtlscout-options.md)；[方法卡](structure-generation-paper/contract-option-protocol-method-card.md)；`artifacts/responsibility-local-semantic-options-static-20261021-01/` | 相同类型不能冒充语义；不增PPA/时序/流量要求；同池闭包、压缩完整方案和直接构造均保留；手工数学不冒充模型结果 | 静态例与一次数学资格完成：FIR4096输入×4组合；TD327680合法嵌入元组×4组合，后者非全域。合法匹配均零差异、交叉有公开反例；C_R两个合法重算组合静态保留。Parsel/RTLScout固定源码及相关完整方法已核，未确认新增核心或协议收益 |
| N19 隔离前置选择器原型 | N18可信完整normal与手工局部合同池；封闭精确数学AST | 分离可信目标/候选池；验证ABI/范围/绑定，展开≤64组合；支持规则内认证、真实公开见证反驳，其余UNKNOWN；输出选中合同/接线，保留同池闭包/直接构造控制 | `artifacts/responsibility-local-semantic-selector-prototype-20261021-01/`；[独立资格审计](structure-generation-paper/local-option-selector-qualification-review.md)；N18方法卡 | 至多2个资格Python入口、每个外30秒、无重试；0模型/HDL/SAT；全部组合留账，CR合法，摘要通过不当RTL通过；冻结代码/fixture后再执行并独立审代码 | 依赖N18；已实现并完成2/2入口、39/39检查，FIR2/4、TD4/6组合认证，另4组合有公开反例，合法CR均保留。主审核10冻结及22封存文件hash、运行账和4见证；独立源码审计未见限定认证错误。仅前置摘要选择，不含RTL发射/行为模型，未证明协议收益 |
| N20 完整数学输入的零模型编译基线 | N19冻结trusted-specs及原公开数学；用户允许自由分解/接口的变体，非旧固定责任合同 | 通用AST→位精确RTL，每个输出抽非空helper；独立公共原式生成有限TB；先静审冻结文件，再执行预定资格 | `artifacts/responsibility-direct-math-compiler-baseline-20261021-01/`；[原始结果与裁决](structure-generation-paper/direct-math-compiler-baseline-review.md) | 至多1个Python发射入口、2次iverilog和2次vvp，各30秒、零重试/模型/SAT；FIR4096全域、TD327680嵌入元组及40固定极值位置，TD不冒称全域或不重复；逐节点64位范围与signed/floor/sat/wrap正确；全部失败留账 | 依赖N19可信输入；已实现并实际完成1Python+4HDL，全exit0、零重试、零未跑。FIR4096/4096、TD327720/327720位置通过；2/3helper和全部输出实际生成，主审核9冻结、9生成、41封存hash及raw，独立封存后复核通过。零模型构造在限定域成立，旧责任合同/TD全域/LLM比较未验证；当前不再扩大N18/N19机制投入 |
| N21 后续任务准备与范围决定 | N18–N20裁决、旧TD实际公开prompt、CRC/累加器guidance/catalog、HINT/Stepwise完整相关方法；用户对新增机制与最低补工的要求 | 在范围待选时完成独立只读准备地图，区分既有周期规则与需新增语义，核同信息FSM/adapter及近邻；不采纳时序变体，未有差别不开发 | [时序任务准备核查](structure-generation-paper/stateful-task-readiness-review.md)；本清单和`structure-generation-paper/new-core-screening.md` | 不新加流量/PPA/时序条件、不启动被测模型；未知公共语义不从TB/参考补入；不能不给基线同信息；每项新机制须给真实取舍、额外推导或实际省工、停止条件 | 依赖N20；只读准备已完成：旧TD明示单槽周期规则但状态/拓扑固定，CRC/累加器已查公开材料不足，0项通过新核心开发门；HINT/Stepwise再审未得新gap，源码限制保留。正式时序范围仍待用户答复，未定义/开发/执行新任务 |
| N22 有界独立构思与条件NI反驳 | N20/N21停止证据、同一公共数学/方法卡；scientific-brainstorming独立构思程序 | 2名fresh研究agent先独立构思、最多各1案；主审1个讨论案；非提案者反驳、最多2近邻深审、1次post-check修订 | [独立构思与反驳记录](structure-generation-paper/bounded-method-core-ideation-review.md) | 同信息、同保证比较；不以放弱合同省字段，不把数学手算当运行；普通NI/自动函数分解均为强基线；不增新任务条件或被测样本 | 依赖N20；完成：2项独立弃权，R1条件NI已有SecVerilog直接覆盖，SV-Gap实际用途检查亦保留；R1b用fiber一致/实际上游满射修正保证差别，独立审查确认精确条件，但未有相对强基线的额外处理/省工证据。未开发/实验/改旧评分 |
| N23 自动语义商强基线复核 | N22 R1b数学条件、F/h与角色/域信息、SAT重代入作者论文/ABC及CUDD作者实现 | 只读核fiber、逐context覆盖、隐式Q及实际代码路径；逐输出审查原三profile，不从旧G反推标签后冒称省工 | [N23主源、适用性与裁决](structure-generation-paper/bounded-method-core-ideation-review.md#9-n23标准函数依赖与关系投影的实际能力) | 至多2项主源深审；论文/源码版本分开，静态路径不冒称执行；同保证、同信息，旧G/评分保持 | 依赖N22；已完成。SAT依赖/插值及CUDD关系投影覆盖核心数学处理；旧ABC stub与后续路径、8共享变量限制均记录。补角色后仅ALU4数学上整体适用，FIR/TD实际域不满射。无新增推导/绑定或实测省工，停止R1b独立结构生成核心，不写同类原型；无新实验 |
| N24 验证前端系统定位讨论 | N13实际字段负担、N20/N23停止证据、用户新增机制偏好 | 先准备具体目标用户/输入输出/复用与新增处理、同信息基线、真实成本端点和S0–S5依赖，讨论是否接受不同贡献定位 | [系统定位讨论卡及范围更新](structure-generation-paper/bounded-method-core-ideation-review.md#12-n24不同贡献定位的讨论卡未采纳) | 不把R1b改名为新核心；没有真实任务或实际成本/可靠性差异则停止，不以字段数充工时 | 讨论卡已准备；2026-10-22用户选择先评审工具定位，S0完成。N37完成S1现有材料盘点，任务资格/S2仍未闭合；不解除N23停止结论，不采纳新任务/评分或启动开发/实验/正文修改 |
| N25 SCIE文章类型与交付门槛 | N7现稿/核稿、N13成本边界、N23停止证据；期刊/出版商与Clarivate主源 | 独立核文章类型、具体索引证据及交付要求，区分政策、项目判断和未确认；不代选N24 | [主源与现稿缺口](structure-generation-paper/publication-route-evidence-review.md) | 不以IF/WoS代SCIE，不以允许软件/负结果认定录用；不杜撰模型/任务数、全域证明或上板的统一最低要求 | 已完成有界主源核查。IEEE Access官方明示SCIE及多种类型，仍需知识贡献与充分证据；SCP仅核出版商OSP轨道，现行细则/SCIE未确认；SoftwareX因访问失败未确认。不依赖N24选择，无新开发/实验/正文修改 |
| N26 真实caller需求原件与版本 | N21有限guidance、legacy归档requirement/身份metadata、当前公开消息构造代码 | 不把N24待选当全项目阻塞；只读定位CRC/累加器/Join原始需求，SHA去重，区分raw需求、当前模板与完整历史messages | [原件、分母与来源边界](structure-generation-paper/stateful-task-readiness-review.md#7-n26归档caller需求与实际模型输入分开核查) | 不读eval/RTL/TB补语义，不认source标签为网络认证；不以目录数当任务数，不采纳新时序任务 | N21；已完成。193份有身份metadata中三家族80目录/80req/7SHA版本；48无metadata另47req/42SHA不自动分类。Join长版有实际接线文字差异；当前源码确认raw需求不等于组合messages，完整历史输入仍UNKNOWN。无新模型/HDL/solver或正文修改，未建立新核心 |
| N27 完整历史输入有界追溯收口 | N26七份需求SHA、artifacts/reports文件名索引、历史来源索引与公开字段schema | 只查初始消息/请求及版本绑定；不打开eval/trajectory等其他角色、不用当前模板补旧消息 | [追溯范围及UNKNOWN](structure-generation-paper/stateful-task-readiness-review.md#8-n27完整历史输入的有界追溯收口) | 原需求→完整消息→模板/代码revision→run身份需可核关联；未找到不等于从未存在，不持续扩查旧日志 | N26；完成限定追溯，七版均仍UNKNOWN；artifacts/agent索引0文件，五组来源记录及公开投影schema不补足发送记录。停止扩查，无新任务、模型、工具实验或正文修改 |
| N28 消费者前接口可实现性候选R2 | 原TD完整公开prompt、F/h/合法域/可见划分；CorrectHDL、2024 ACD及N23 SAT强对照 | 手工给同外部功能下的可行/不可行接口及宽度下界；审真实encoder/decoder构造与输入成本，判是否有额外处理 | [静态推导、固定源码与执行门](structure-generation-paper/interface-realizability-candidate-review.md) | 不改旧R17合同，不凭空加资源预算；存在Q不冒充RTL通过，不把标准SAT或分类编码称新算法；强基线可自动构造两侧 | 完成手工推导与限定主源深审：9bit足够、任意固定8bit不够；不是模型失败。SAT直接覆盖给定h的判定，ABC实际构造两侧但仅局部≤11布尔输入；无新处理或现实压缩必要性证据，暂不开发。零新模型/solver/HDL，v0.3不变 |
| N29 公开结构交接失败原件与问题资格 | 本地完整prompt/catalog/recipe、N20可信AST成本边界；ChipVerilog v3/固定作者源码与前两份FPU缓存候选，ROME v1/固定作者Notebook，另三项仅筛 | 独立核现有开放问题；配对具体源码与缓存诊断；核生成上下文及评价装配，区分行为bug、信息缺项、标准检查与新处理 | [案例、方法细节与后续门](structure-generation-paper/generation-gap-case-review.md) | 不以汇总低分推原因，不把当前wrapper当历史发送记录；不将参考文件错误全归模型；不加外部缓存到本项目分母，不新定义任务/运行 | 已完成：本地两审均弃权；一项外部FPU任务的两缓存中核重复端口/候选语法错误及混合支持诊断，ROME失败叙述未配对原件。N20不是NL→AST自动前端，准备成本仍未知；普通接口/typed emitter仍为强对照，未建立新核心，不开发或追加被测样本，正文不变 |
| N30 自然语言到可信规格的来源与成本边界 | 原单槽TD、公开组合TD8、N19手工AST与N20入口；VeriRefine/SynthTL主源、保存教程及RTL-BenchMT修订文本 | 核源身份和字段转录；审NL一致性、oracle与给定DUT各自保证；取得实际保存案例，澄清N20/N28引用范围 | [规格获取审查](structure-generation-paper/specification-acquisition-review.md)；N20/N28范围说明 | 不把后来的三输出组合任务当原两输出单槽；不将人工F视作免费，不以引文/回译等同语义证明；保存案例非本轮运行，不改旧证据 | 完成：N19源SHA绑定公开组合TD8，N20不覆盖原单槽或N28全流程。SynthTL教程对不等价候选均答y但最终返回给定DUT条件式，非最终失败；BenchMT原/修订文本增加参数及周期，可核但不是同义改写。未找到新机制，不开发/新增被测实验；初稿和旧结果不变 |
| N31 区分反例与澄清流程的实际近邻 | N30的P/Q保存案例；nl2spec v1/固定作者代码、LTLTalk论文/固定作者代码及Spot官方文档 | 分工深审候选编辑、XOR见证、环境约束、回答过滤和停止分支；主审补读包装器，独立手算无限区分例 | [方法／源码与语义边界审查](structure-generation-paper/counterexample-clarification-neighbor-review.md) | 不混用有限co-safe与无限LTL；不将有界无见证当等价、单候选当完整意图；单次否定不能自动确认另一候选；未采用人类交互，不运行作者软件/模型 | 依赖N30；已完成。nl2spec有编辑重查，LTLTalk实际XOR及过滤已核，Spot有无限语言差异能力；通用反例澄清无已指出额外规则，不开发/pilot。新源码证据为进展，非SCI核心验收；旧分母、任务、评分和三版正文不变 |
| N32 独立构思与另三家族公开需求资格 | 两份完整公开算术/单槽TD输入；两个指定归档根的一层metadata及三精确task_type需求 | 两fresh-context协作者先独立构思并允许弃权；另审MAC/匹配滤波/雷达原件，主审重算身份、原字节/strip hash和分母 | [独立意见、实际原件与下一步限制](structure-generation-paper/remaining-public-task-source-review.md) | 不以两票弃权代替原创性判断，不把短提示当完整messages或把缺项当开放许可；不从reference补语义，不将不同vector家族猜作别名 | 完成：两构思均未保留机制；202 metadata中三身份4需求/3SHA、各一句，尚不能据此定义完整顶层与等价变体。停止将这些短提示直接换进模型pilot；新增原件为进展，无新被测调用/solver/HDL/任务/正文改动 |
| N33 比较起点与停止门审计 | N19实际卡/公平审计、N20输入/编译入口/结果；CPPL v1及固定同期三源码 | 独立核共同可信F与真实入口，主审核字节/SHA和五过程记录；回读CPPL意图→IR→编译链，收窄过强恢复条件 | [比较起点与语义准备审查](structure-generation-paper/comparison-endpoint-audit.md)；N20末段说明 | 不把未实现NL前端当N19既有能力，不用手工F后台胜过不同起点系统；同能力可有成本/可靠性价值，但未知成本不当收益 | 完成：N19/N20同字节可信F，现比较输入公平；CPPL调用方给结构但模型补行为IR，N20非其完整流程对比。仅修正文档门，维持N18/N19停止，无新被测/工具实验、定位/任务/正文/评分改动 |
| N34 外部完整题面与状态适配候选 | HDLBits三官方串行题面/公开WaveDrom及可选TFF；Filament v1/固定stable三源码、Greaves/Nam作者PDF | fresh-context核题面/独立构思，主审核官方脚本与首帧相位手算；提出从递推和窗口推适配的C34，深审Filament并筛直接协议适配近邻 | [题面、错配、C34与后续门](structure-generation-paper/external-serial-adapter-candidate-review.md) | parity可选/多文件非原题要求；手算不冒称模型失败；区间guard不等同中性输入；Greaves未深核不宣布缺失；外部任务不自动纳入 | 本轮完成：得到停止采样前后odd翻转的具体来源例，C34仅待核步骤，创新未确认。下步先深审Greaves再写同信息控制/归约对照，不开发/新增被测或评分/任务/正文改动 |
| N35 状态适配的强近邻与同信息裁决 | N34可信递推/窗口及公开题面；Greaves/Nam两份作者PDF和出版清单 | 深审协议乘积/数据匹配/选择，主审核关键算法；独立推导普通屏蔽/捕获及合法反相解码，核真实增量与停止门 | [强对照、输入责任与C34裁决](structure-generation-paper/state-adapter-standard-baseline-review.md) | 7/8页版本及源码UNKNOWN分开；同信息相位必需项明确；四格不冒称执行，未列XOR不代表不能有限展开；同能力不自动否决系统贡献 | 依赖N34；完成有限复核。普通控制覆盖当前具体步骤，尚无额外处理/完整成本收益，停止C34单独核心开发投入；保留案例，无新模型/HDL/solver、外部任务或正文改动 |
| N36 作者生成工件与原请求绑定 | VeriGraphi v2及新取得固定输出仓库；arXiv:2610.25881v1、固定计分源码和RESULTS.lock | 核三份KG/RTL静态差异及JALR来源，主审全读复核；深审表示/拒绝/组合SAT/config exact与实际样本分母 | [真实工件、实现路径与绑定限制](structure-generation-paper/generated-artifact-binding-review.md) | 同目录非同次输入输出证明；宽变换非必然非法；确定性后端构造保证与SAT分开；可达空间不当每格分母，未知不冒称作者失败或新gap | 依赖N35后继续研究；完成限定来源复核，新增工件/代码证据但新核心未成立；不恢复停止案，不采纳外部任务、修改正文或追加被测实验 |
| N37 验证工具系统定位评审 | 用户2026-10-22选择、N24阶段门、N13字段/现checker、旧标准结果与三项固定强近邻 | 核已实现/已验证/目标边界及真实adapter故障；区分原字节审核和重构，评S1需求/S2强对照及可靠性/成本端点 | [工具定位与任务准备](structure-generation-paper/contract-frontend-task-readiness.md)；N24范围更新 | 不把12输出当12真实需求，不追认人工工时，不用裸CLI或已知错adapter作主对照；选择评审不等于立项/运行授权 | S0完成且用户选择先可靠性、暂不主张人工省工；只读评审完成，S1独立审核工作资格/S2仍未闭合，建议先补；无新开发/被测模型/正文或评分变更 |
| N38 独立工程需求与正式发表审计 | OpenTitan固定要求/宏/父封装/通用注入框架，用户可靠性选择及正式发表判据，七项身份主源 | 核真实额外需求、实际交接和当前合同接受集合；分开正式论文与预印本/录用/软件，回核AutoSVA具体覆盖 | [独立审核需求](structure-generation-paper/external-architecture-audit-task-review.md)、[发表身份审计](structure-generation-paper/publication-status-novelty-audit.md)；N37/N24后续说明 | 不把时序单侧告警压成完整组合G，不凭局部未见推全框架缺失，不以软件DOI/排程作正式论文；需求成立不等于工具增量成立 | 依赖N37，限定只读复核完成；独立需求已支持，S1同类任务/S2区别处理仍未通过；七项中AutoSVA正式发表确认，其余未确认，不自动恢复旧投入；无新开发/实验/任务采纳/正文改动 |
| N39 真实交付错误与完整性条件 | OpenTitan PR15563元数据/直接修复/评论，STTT正式记录与作者稿，独立组合反例 | 核错误探测对象与作者既有处理，区分空泛性/绑定/切边资格；手推正常回代、恢复及自由PI三条件不充分 | [验证交付可靠性](structure-generation-paper/verification-delivery-reliability-review.md)；N37/N38身份后续说明 | 历史修复不冒称实际误通过；手推不当执行；不把单侧时序改成组合G，不将未覆盖某层直接认gap | 依赖N38；限定复核完成。新增真实历史错误与判据反例；wrapper/映射/miter仍无同信息区别处理，不作新核心开发。S1同类任务/S2机制未通过，无新实验/任务或正文修改 |
| N40 配置与验证义务完整性 | OpenTitan固定三份注释/计划/CI实现；OCRA正式出版/作者稿/2.1.0手册；fresh-context构思及现checker | 核已有声明对账与语义义务生成；深审合同细化/配置界；反证EN不等于触发覆盖域并撤回免费Cj候选 | [完整性复核与待评审边界卡](structure-generation-paper/configuration-obligation-completeness-review.md)；N37/N38身份后续说明 | 论文与当前手册能力分开；配置上限不当穷尽；不从三文件未见推全局缺失；同信息蕴含不当新机制，手推非执行 | 依赖N39；限定来源/机制评审完成。停止简单清单/触发蕴含核心开发；实际编译语义关联未定义，仅准备验证工件审计边界，未采纳新对象/任务/实验或正文改动 |
| N41 实际监测工件的具体方法评审 | Yosys固定接口/类型/lowering源码，IJCAR2020出版社定稿，独立开放接口推演，SoftwareX官方评审材料 | 核实际来源保留和时钟边界，定义R/M错误行为与绑定/环境分项比较，区分标准算法和系统交接；补期刊软件交付证据 | [实际工件方法卡](structure-generation-paper/compiled-monitor-audit-method-review.md)；[N25补核](structure-generation-paper/publication-route-evidence-review.md#6-n41softwarex官方评审材料补核索引仍未确认) | 不把M/来源/EN当免费语义，不以当前正确DUT域认证监测器，不将有限差分当全称证明；软件评审材料不当SCIE证明 | 依赖N40；来源与具体卡完成，S1/S2未验收、收益未测；用户在N42期间选择先评审验证工件，可核两个真实案例/强对照，不开发/实验/改正文；不因后端成熟否定所有系统价值，亦不据框架存在认创新 |
| N42 初稿与最新证据的修订准备审计 | v0.3当前字节、N20/N33、发表身份记录、原pilot/local/standard/compiler JSON及同F输入 | 独立核未来修稿的重要遗漏和引用口径；重算旧记录分母/状态，列原RTL及待选工件对象的资产复用边界 | [初稿证据与修订差距](structure-generation-paper/manuscript-v0.3-current-evidence-audit.md) | N20不冒称G/周期/旧角色证明；12＋12不当24独立样本，16局部不当系统证明；记录重读不当执行，未答不视为同意 | 在N41范围待答时完成独立工作；确认原有限结果可保留，需补后续强对照/起点/身份及相应新主指标。本审计正文与旧结果未改、无新实验；后续收到评审新对象的答复，案例源核查另记 |
| N43 两个真实验证工件来源与强对照资格 | 用户已选择工件审计评审；OpenTitan rom_ctrl与PULP cc_fifo固定源码、宏及构建清单；N41方法卡 | 核公开义务、实际调用/端点、采样复位、宏激活与源级构建入口；列独立参考、强基线和区别处理缺口 | [两例方法适用性评审](structure-generation-paper/verification-artifact-two-case-readiness-review.md) | 两项来源不当两项已通过任务；不复制M作唯一R、不将recipe当编译结果、不抹平异步/四态边界；基线同样自动化 | 来源核查完成；已有build入口，最终配置/参考与语义资格未闭合。尚无新增处理或收益证据，S1/S2未验收；不开发/实验/改正文 |
| N44 全项目PI复盘与一周路线排序 | 全项目状态/旧资产、N1–N43、原件抽查；用户一周/70小时/Codex/版面费不限 | 核各路线完成度和停止原因、现有证据、强对照及期刊政策；提出8小时资格检查和条件70小时计划 | [全项目进展与一周路线建议](2026-10-22-pi-project-progress-and-one-week-route-review.zh.md) | 不混合45＋42变异口径；文件存在不当复运行；新算法非统一发表门槛；保留同信息强对照和独立真值 | 全面评审完成；用户已接受原B系统／实证定位、优先一周投稿并先核可行性；8小时检查待执行，本轮未开发、运行或改正文 |
| N45 首日可行性与真实错误复现 | 用户已选系统／实证并要求下一步；前两归档家族、113来源库存及13份L3声称 | 恢复16向量、运行2参考＋9变异；来源与快照绑定；另对全部3个fork作同一公开事务守恒诊断 | [资格结果与下一阶段](2026-10-22-acceptance-reliability-feasibility-gate.zh.md)；两份独立artifact运行目录 | 不混合11对象与3诊断；不把手工变异或metadata当独立LLM样本；强基线同信息；原件哈希与注册证据验证 | 工程资格通过；2份历史工件重复交付已复现，允许条件继续队列/协议准备；论文贡献未验收，未写正文 |
| N46 工件队列与有限义务准备 | N45库存与全部13份L3保存工件、公开需求和实际top接口 | 固定版本/哈希/需求簇；区分首轮与修复；列必要性质、未知与同信息标准基线；准备有界后续顺序 | [N46准备结果](2026-10-22-acceptance-cohort-and-protocol.zh.md)；`artifacts/acceptance-cohort-protocol-20261022-01/` | 13例完整、59对RTL/TB绑定；不补造join/TD数值规则；fork检查不擅加输入ack先于分支交付；无效/未知不冒充通过 | 准备完成，独立静态复核；下一步实现控制和最多11例有限性质检查，4小时内作Go/No-go；本轮0新HDL/模型/正文 |
| N47 全队列有界审计及投稿裁决 | N46冻结队列/协议，用户继续执行授权；实际复位/接口源码 | 实现并资格4对控制；13原TB＋11有限性质；独立轨迹/源码裁决与近邻比较 | [N47执行结果](2026-10-22-acceptance-audit-results-and-publication-gate.zh.md)；`artifacts/acceptance-cohort-audit-20261022-01/` | 同信息标准scoreboard；全13分母；合法切通不误拒；上界含初值/全部呈现；原件不变；预算落实 | 实际64HDL＋2版本，0模型/重试；8控制全合格，3违例/8未见/2不可判，2机制；工程Go、仅当前队列直接投稿No-go，正文不改 |
| N48 前瞻源码可见性资格试验 | N47停止结论、用户继续执行与子agent被测授权；两份新公开时序规格、固定正负控制 | 冻结4RTL＋8TB位置；参考资格、独立真值、A/B成对生成和控制判别；记录全部失败与执行偏差 | [N48结果及停止裁决](2026-10-22-testbench-source-visibility-pilot-and-decision.zh.md)；`artifacts/tb-visibility-pilot-20261022-01/`及`-02/` | 先资格后候选；无反馈／修复／补抽；全位置留账；3完整开发配对；自然误验0分母不作0% | 已完成12被测调用、78HDL＋2版本；4RTL有限通过，7TB判别两控制，3配对差0；1协调者转录偏差、4评价行unrun。运输认证不完整及reset文字限制保留；停止这两题扩采，正文不改 |
| N49 现成任务资格筛选 | N48停止结论、当前三AI家族/PC2.1、旧九家族/T5、已有外部来源 | 核公开合同、独立参考、实际入口和最小补工；制作三项具体范围草案并讨论新增规则 | [N49筛选与范围](2026-10-22-task-asset-screening-and-next-scope.zh.md)；`artifacts/task-asset-screening-20261022-01/` | 代码/记录与实际运行分开；不补造历史要求；不按失败选题 | 完成；未找到无需补规范和资格即可扩样的代表性现成包；用户接受FIR8/DOT4-8/PEAK8新前瞻规范，只启动准备 |
| N50 三任务公开规范与参考资格准备 | N49已确认范围、旧确定性模板、独立公开数学 | 写4公开卡、独立事务参考/合法刺激、3参考6控制、限额执行器；Python检查及独立静态审查、冻结来源 | [N50准备结果](2026-10-22-three-task-qualification-preparation.zh.md)；`artifacts/three-task-qualification-prep-20261022-01/` | 不依候选生成oracle；FAIL须有明确数值见证；X/超时/缺失不可算kill；全部9位置、明确新旧版本 | 准备完成，151文件/2工具哈希核验；20主审集成检查、17参考断言组及独立检查通过；真实HDL/模型均0。下步有界运行18HDL＋2版本需另行执行授权，不改正文 |
| N51 三任务实际参考资格 | N50冻结包及固定9位置、用户下一步指令 | 唯一执行3参考/6控制；逐项数值重放、独立原始轨迹复核、预算与来源核验 | [N51执行结果](2026-10-22-three-task-qualification-results.zh.md)；`artifacts/three-task-qualification-run-20261022-01/` | 参考完整通过；控制须有合法前缀真实违例；失败/未运行留分母；冻结输入不变 | 完成18HDL＋2版本，0模型/重试；3参考通过、6控制检出，9/9位置完成。有限工程资格通过，研究贡献待核；下一轮仅列设计建议，未生成或改正文 |
| N52 三条件前瞻设计与近邻增量复核 | N48/N51、三题公开卡、近邻作者原文/固定代码/出版登记 | 核已有三条件重叠与动态刺激混淆；列18槽/54评价、全分母、实际轨迹分类与新增组件范围 | [N52设计评审](2026-10-22-rtl-tb-misguidance-design-review.zh.md)；`artifacts/rtl-tb-misguidance-design-20261022-01/` | 不由最终PASS推错误期望；不把固定轨迹资格迁移自由TB；不把108当完整预算；正式与预印本分开 | 评审完成，原18次暂不执行；建议收窄实际轨迹审计并仅作2小时准备，范围待用户选择；0新HDL/模型/实现/正文 |
| N53 实际轨迹审计组件与资格准备 | 用户收窄准备授权、N50公开数学/参考及状态控制、N52测量缺口 | 明确TA1合同；只读观测、实际ready合法性、动态重放与五类对照；独立评审和冻结 | [N53准备结果](2026-10-22-tb-trace-audit-preparation.zh.md)；`artifacts/tb-trace-audit-prep-20261022-01/` | 指定见证/环境错误原因；未知/缺失不算检出；FAIL仍未归属；旧输入与正文不变 | 准备完成；33重放/11执行器/29独立检查通过，123文件/2工具冻结；0HDL/版本/模型。下步10手工位置、20HDL＋2版本真实资格尚未运行，贡献未验收 |
| N54 真实观测资格与兼容修订 | N53冻结包、用户继续指令、固定十位置及停止规则 | 实际运行；保留编译失败与未运行；定位final任务调用；新版本最小内联修订和独立审查 | [N54结果与修订](2026-10-26-tb-trace-audit-qualification-and-compatibility-fix.zh.md)；`artifacts/tb-trace-audit-qualification-run-20261026-01/`及新准备包 | 不把编译失败当功能违例；无trace不作漏报结论；不覆盖旧包或自动重试；案例/合同/阈值保持 | 实际2编译＋2版本，2不可用/8未运行，0仿真/模型。修订已冻结123文件/2工具但未真实验证；下步仍10位置资格，正文不改 |
| N55 修订版资格与最小编译诊断准备 | N54新冻结包、用户下一步指令、旧成功入口与本轮原始日志 | 执行唯一资格；核空诊断失败及遗留产物；准备六项编译对照，不猜测根因 | [N55结果与诊断范围](2026-10-26-tb-trace-audit-second-run-and-compiler-diagnosis.zh.md)；`artifacts/tb-trace-audit-qualification-run-20261026-02/`及编译诊断准备包 | 全十位置保留；不运行失败编译产物；不由空诊断归因；删减探针不得进入功能评价 | 本轮2编译＋2版本，2不可用/8未运行，0仿真/模型；两轮累计4＋4。六项仅编译诊断已准备未执行，正文不改 |

**本轮结果：** [12原始输出与12固定父构造全部通过](structure-generation-paper/cross-task-pilot-review.md)，没有观察到责任违约或提示/构造提升。N18补语义协调资格与强近邻，N19前置原型通过39项限定检查；N20零模型编译已实际通过FIR全域与TD预定子域。当前不再扩N18/N19完整模型链；新增方法核心、完整生成收益与SCIE充分性均未验收。

**最新候选范围：** N15范围问题未由执行替代，仍不开发该生成链或采纳新环境。N18/N19已完成前置工具，N20证明当前完整数学输入可以直接生成通过预定功能资格的多helper RTL，故不再据此扩写LLM选择链或模型pilot。工具可执行不等于方法创新，标准工具存在也不自动否决系统贡献；当前停止扩大投入依据是缺少近邻之外的处理/完整成本收益与真实必要任务。N21范围问题仍待答，独立准备地图已完成但未采纳新时序任务；不能仅以更难的时序替代新处理。旧12份模型分母、正文v0.3和现行研究定义不变。

N22/N23已完成有界构思、反驳及标准强对照复核。条件非干扰、自动函数依赖及关系投影已有直接方法/实现；R1b只有在接口覆盖及函数一致等严格条件下才可同保证省G。原三profile仅ALU的数学条件整体适用，且旧active G本来就是z；未发现新处理或实际省工，停止R1b独立结构生成核心，不追加同类原型。若转向合同编写/验证前端，应先给出具体系统问题、同信息基线及真实成本端点，并与用户讨论贡献定位，不能将此停止案改名当创新。

N24已准备不同贡献定位的S0–S5讨论卡。2026-10-22用户选择先评审验证工具系统贡献，并明确先可靠性、暂不主张人工省工，S0完成；N37核工具能力与强对照，N38已找到独立工程审核需求，但时序单侧响应不等同当前完整组合合同，S1同类任务资格/S2区别处理仍未闭合。这不是正式立项或SCI创新验收，本轮不启动新开发、成本研究、模型实验或正文改写。

**当前评审进展：** 用户进一步选择先评审已提交验证工件，[N43](structure-generation-paper/verification-artifact-two-case-readiness-review.md)已配对OpenTitan实际错误到告警调用、PULP FIFO实际协议断言及两项目公开build入口。两者是来源资格，非编译通过或可靠性样本。先闭合选定配置与独立参考，明确复位/四态支持，再核强基线之外的实际处理；没有这项区别或系统可靠性证据，不扩大实现。旧12/12和16局部证明不迁移为新对象结果。

N25独立补核了期刊文章类型与现稿交付门槛。已核IEEE Access政策不把全新算法作为所有类型的统一必要条件，但仍须区别已有工作并提供可靠知识贡献；用户新增方法机制的偏好仍保留。现稿事实核对通过不等于科学贡献验收，主要缺口仍是具体增量与适当证据。未确认SCIE的软件期刊不补入达标名单，未据此改定位或新增实验。

N26复核后确认仍有原目标内已授权的独立证据工作，不将研究偏好待选误判为整个目标impasse。现已补齐三个家族归档caller需求的80/7去重及当前消息构造来源；原始requirement缺字段不代表全部模型输入缺字段。N26当时建议先追溯完整公共输入/版本，现已按N27有界收口；完整历史messages及新时序任务资格仍未确认，不能从隐藏评价补语义或直接扩模型样本。

N27已按界限收口历史输入追溯，七版均UNKNOWN，不再无限检索旧日志。N28独立使用已完整公开的原TD输入补出9bit最小消息的静态例，并核CorrectHDL实际分解流程、ABC实际encoder/composition与N23 SAT。数学可行不等于新方法；标准基线覆盖判定/构造原理，现实压缩约束及额外收益缺失，暂不为R2开发原型或新增模型样本。报告列明重新进入开发前的真实必要性、额外处理与同信息基线三项门。

N29已核外部公开失败工件并深审ChipVerilog/ROME的实际方法与代码，没有仅凭低分推gap。两份FPU缓存只支持端口/语法及混合支持文件诊断；当前description/wrapper不认证其历史输入。ROME已有relay和逐模块编译/反馈，所述MIPS失败未配对原件。N20取得可信AST前的准备成本不能隐去，也不能把这项未知当新增机制。本轮没有合格新核心或新运行；外部IP任务并未采纳。

N30进一步核清N19绑定的是后来的R/E/U组合TD8，不是原E/U单槽TD；N20与N28报告已澄清完整覆盖边界，原执行结果不回改。可信AST的人工转录未知成本仍不构成创新。SynthTL真实保存翻译案例、VeriRefine实际审计/歧义限制，以及BenchMT一项参数/周期修订均已定向核查，不将来源/人工确认/内部一致性当语义真值，也不抹去近邻的经验效果。当前没有足够的新处理立项理由。

依赖主线：N1/N2 → N3 → N4 → N5 → N6 → N7。当前不依赖训练、上板、布局布线或实现整个PC 2.1。正文已获用户授权，无须重复确认；发布、投稿、官方证据晋级仍须具体目标授权。原生spawn接口不能硬禁工具或设置provider token上限，实际零工具使用仅为观察，不能作硬隔离证明。

**历史路线的裁决保持：** 局部程序/模型分区已[停止](structure-generation-paper/local-responsibility-bounded-design-review.md)；有限连接备选的80个子池中，普通匹配/链直接构造与联合枚举等价，因此[保留假设、不追加完整开发](structure-generation-paper/connection-choice-decision-review.md)。它们与当前条件性边界审计不是同一机制，下面的旧P00–P12仅供回溯，不再是执行指令。旧正文等待点、旧模型调用数与“尚无任何真实模型结果”等语句描述当时状态，已被本页当前状态替代。

## 历史阶段记录（不作为当前执行计划）

## P00　范围与进度基线

- **输入材料：** 用户已确认的 A 路线、仅研究结构生成且不加修复的选择；背景备忘录；[AGENTS.md](../../../AGENTS.md)及当前仓库状态。
- **具体任务：**
  - [x] 记录 M3/M4、共享生成契约、首次生成、无修复的研究范围。
  - [x] 区分本篇旧版研究与现行 v2.2/PC 2.1 主线。
  - [x] 将正文写作设为单独的用户确认点；建立本清单。
- **输出文件：** 本清单；已有 `reports/manuscripts/discussions/2026-10-21-minimum-scie-paper-route.zh.md` 的进度入口链接。
- **验收标准：** 范围与用户既有选择一致；不重复索取已给出的选择；不把选择方向解释为实验、正文、公开或投稿授权；没有生成论文成稿段落。
- **前后依赖：** 无新增前置；为 P01/P02 提供基线。状态：已确认。

## P01　资产审计与候选任务

- **输入材料：** [任务证据账本](../../evidence/task-ledger/sr2fpga-task-evidence-v0.1.json)、Phase C/D 原件、`datasets/manifest.json`、旧生成器/骨架/oracle 代码、文献与旧稿索引、已有 241 样例及 113 条自然模型元数据盘点。
- **具体任务：**
  - [x] 按任务列出需求、RTL、模块层次、参数、参考模型、输入向量、工具日志和来源的存在性与缺口。
  - [x] 区分完整原件、仅摘要、来源不完整、尚未实现；旧 L3 标签不直接计功能成功。
  - [x] 形成调试任务与主研究候选表，按结构复杂度和参考可用性选取，不按旧模型好结果筛选。
  - [x] 核对任务别名与准确运行类型；标记共享算法/设计谱系，避免把不同随机种子当独立设计。
  - [x] 记录自有/第三方代码及数据许可状态、可公开范围、缺失的历史配置；不补造旧 provenance。
- **输出文件（已创建）：** [资产审计](structure-generation-paper/asset-audit.md)、[候选任务与静态就绪表](structure-generation-paper/task-readiness.md)、[来源及公开范围](structure-generation-paper/release-scope.md)。
- **验收标准：** 每个候选任务都有可追溯输入、真实模块责任、oracle 类型和明确缺口；“静态可匹配”与“当前可运行”分开；主研究候选不以空自测 PASS 作为资格；未公开数据保持原状态。
- **前后依赖：** 依赖 P00；结果进入 P02/P04。状态：静态审计完成，3 个调试与 6 个主候选均有来源和缺口；没有执行 P04，也未恢复旧向量或取得公开许可。

## P02　文献定位与实验协议

- **输入材料：** P00 范围、P01 就绪表、既有文献 registry、最接近工作的原文、M3/M4 适配器/预算/骨架代码与实际混杂检查。
- **具体任务：**
  - [x] 形成与近期生成、仓库级 agent、结构化生成及验证工作的差异表；不得将已有常识直接列为创新。
  - [x] 明确处理变量是“确定性结构构建＋行为输出约束”的组合；标出 top、内部模块、manifest、约束、初始化文件的程序/模型责任。
  - [x] 定义共同准入、契约失败、各组工程失败、基础设施缺失、截断、超时、重试和停止口径的准备方案。
  - [x] 预先提出主要终点及结构错误/成本等次要指标；保留完整分母，可另报共同合法契约条件下结果。
  - [x] 提出设计簇、配对、重复、顺序与解码控制原则及有限样本分析；具体设计簇、模型和资源数值待后续锁定。
  - [x] 核对现有 episode、trajectory、checkpoint、cost、outcome 合同的适用性，记录两条件实验的格式缺口和版本策略。
  - [x] 按用户“先核对创新性，再开发”的选择，复核 CPPL、VeriGraphi、层次 IR、HINT 的方法、对照与实现边界，记录阅读限制。
  - [x] 记录用户要求方法本身新增机制；补充局部责任划分与可执行控制生成两候选的代码可行性及近邻风险。
  - [x] 用户选择先细化局部责任划分；形成输入/规则/手工正反例/退化情况明确的方法卡，并列保证边界和匹配对照。
  - [x] 补充声明/分组来源、受限树类型及旧 parser 缺口；给出局部对整体的匹配两条件建议，补合同映射和纯核心开发子步。
  - [x] 形成十五条手工预期、独立参考分层及环境非法处理的混合案例资格计划；明确未取得资格、未运行。
  - [x] 执行用户批准的最后一轮协议自动推导/反例设计；LINK、SELECT2、stall均未形成同信息普通分区不能处理的区别，按条件停止该核心候选。
  - [x] 继续筛选独立决策闭包、数值边界、事务传播与局部备选联合选择；记录新协议的手工案例、同信息强对照、近邻、补工和未成立部分，不把筛选完成记为创新验收。
  - [x] 按用户选择保留协议候选，核对实际公开需求/prompt及参考结构；加入Parsel/DecompRL强近邻、M02可派生负对照、M06配置版本案例草案与评价修订缺口。没有把新并发语义施加到旧任务或其结果。
  - [x] 按连接来源限定版执行小规模Python参考等式/符号枚举，验证fork/join逐线与完整通道两种粒度、普通匹配强对照及FIR累加子图；记录公开事实与内层冻结缺口。没有运行模型/HDL或将人工候选池结果冒充效果证据。
  - [x] 按步骤自动研究：复核组件连接合成/PTM组合等直接近邻；形成两例共同公开事实与固定声明草案，独立检查全部80个非空有序子池及强对照，审计结构保护和完整runner补工，并作投入裁决。仅诊断脚本在artifacts内执行，不扩大为模型实验或正文。
  - [ ] 为新的核心机制明确输入、规则、同信息基线和区分案例，再评审相应任务、边界、版本及实施范围；不继续为已停止候选补自动规则。不把未找到等价对照当作方法原创或 SCIE 充分性的证明。
- **输出文件（已创建）：** [研究协议](structure-generation-paper/study-protocol.md)、[相关工作证据矩阵](structure-generation-paper/related-work-matrix.md)、[合同复用与版本缺口](structure-generation-paper/contract-reuse-map.md)、[最小实施范围](structure-generation-paper/implementation-scope.md)、[新增机制讨论](structure-generation-paper/mechanism-options.md)、[局部责任划分方法卡](structure-generation-paper/local-responsibility-method-card.md)、[混合案例资格准备](structure-generation-paper/hybrid-case-qualification-plan.md)、[有界设计结论](structure-generation-paper/local-responsibility-bounded-design-review.md)、[新核心筛选](structure-generation-paper/new-core-screening.md)、[连接候选投入裁决](structure-generation-paper/connection-choice-decision-review.md)。已停止机制的技术部分标为历史准备，不表示实现迁移或创新成立。
- **验收标准：** 同一契约与公开事实、无隐含修复；成功依赖可信功能评估，结构检查不能替代功能；没有事后选择分母；与最接近工作有可检验的区别。模型/预算未知项明确标待定，不杜撰。方案仅作用于本篇，不静默替换根研究权威。
- **前后依赖：** 文献部分可在 P00 后与 P01 并行，协议定稿依赖 P01。状态：整阶段未验收；局部责任划分已停止；连接候选有界研究完成，暂不进入完整开发/主实验，保留协议假设。新核心待定，不以工程准备量推定SCI/SCIE贡献。新profile/任务均未实施或取得资格。

## P03　纯生成核心、公平性与运行接线

适用性：以下包含已停止候选的历史实施待办，当前不执行其 D2/D3。论文新的核心确定后重定具体代码范围；共同公平性、失败保留和验证原则仍可复用。

- **输入材料：** P01/P02；`agent/src/sr2fpga_agent/prompts.py`、`contract_skeleton.py`、`his_validation.py`、`method_adapters.py`、`runner.py`、`generation/context_his.py`及相关现有测试。
- **具体任务：**
  - [ ] 在实施前列明拟改文件、原因、研究影响与验证办法；涉及受信准入、oracle、评分语义时，先取得明确覆盖该表面的授权，保留旧修订与结果。
  - [ ] 先按实施范围 D2/D3 完成纯分组规划与受限树校验/发射，再用 D4 手工公开正反例检查；不将纯核心测试视为真实评价接通。
  - [ ] 处理 M4 独享任务族测试平台的公开信息混杂，核对模型实际收到的内容；不得读入私有参考或 hidden 信息。
  - [ ] 处理共同 H2 准入依赖 M4 emitter 的选择问题，或按已确定协议显式限制旧 emitter 支持范围。
  - [ ] 按最终确定的 profile 身份接通局部/整体两条件共享契约；原 M3/M4 仅按确认的参照范围接入，不额外运行六方法，不引入重复运行框架。当前 M0–M5 闭合枚举和原 M4 policy hash 不能直接冒用。
  - [ ] 禁用初始生成中的免费格式修复、隐含多次尝试和工具反馈修复；为共享失败、独有构建失败保留输出和成本。
  - [ ] 首选现 coordinator＋两条单 episode 原件链，不生产六方法 paired-block/manifest/full-pack；补共享原始响应、规范化契约、成本及失败绑定，必要失败收据在原系列版本化，不给不兼容输出套旧格式标识。
- **输出文件（计划）：** P02 范围批准后修改的实际 `agent/src/...`、必要的注册合同及窄范围测试；`artifacts/structure-generation-paper/<dev-id>/implementation-verification.md`、`validation.xml`。新文件的最终名称在 `implementation-scope.md` 中确定，不在本轮创建占位代码。
- **验收标准：** 正常与负例测试覆盖实际模型输入、共同准入调用路径、共享契约哈希、一次初始调用、失败保留及成本归因；不以文档声明代替控制；不降低评分阈值，不把 mock 当真实模型效果。
- **前后依赖：** 依赖 P01/P02及覆盖实际修改面的实施授权；与 P04 可并行；完成后进入 P05。状态：未开始，现有混杂未修复。

## P04　任务、参考与评估资格

- **输入材料：** P01 就绪表、P02 指标与接口边界；选定需求、参考 RTL、独立 Python/可信 harness、历史向量承诺、变异原件、真实工具环境。
- **具体任务：**
  - [ ] 固定所选任务的数学行为、接口、参数、复位、握手和期望输出；检查骨架是否遗漏顶层或内部必要行为。
  - [ ] 恢复受信可用输入；无法按旧承诺恢复时，建立明确的新修订，保留旧记录，不复写历史。
  - [ ] 用独立推导或可执行反例确认正确参考及错误真值；不能让待评价 oracle 同时定义错误并证明自身有效。
  - [ ] 使用真实编译/仿真/综合检查正确参考，并检验选定的已知错误；等价、未编译、真值未定及基础设施失败单列。
  - [ ] 模型可见材料、公开开发评估与 evaluator-private 内容按协议分离；最终私有评估内容不得用于调提示、修候选或选任务。
- **输出文件（计划）：** `artifacts/structure-generation-paper/<qualification-id>/task-qualification.md`、`tool-versions.json`；每任务由实际注册合同承载的参考输入、oracle manifest/evidence、候选封存和工具日志。恢复输入和失败结果均留在该版本运行目录。
- **验收标准：** 所选任务真实可执行；正确参考通过统一终点，已确认错误的判定可解释；输入字节和工具/配置可追溯；原始自测 PASS 与可信功能结果分开。不能只用历史 JSON 完成本阶段。
- **前后依赖：** 依赖 P01/P02；与 P03 可并行；完成后进入 P05。状态：未开始。研究性错误集/私有评估执行须有对应明确范围，不能将其伪装为普通回归。

## P05　无付费模型的集成验证

- **输入材料：** P03 实现及单元回归、P04 合格任务/参考、P02 协议与格式映射。
- **具体任务：**
  - [ ] 用受控假模型/离线回放检查两组配对、顺序、输入哈希、token/调用事件和成本归因。
  - [ ] 覆盖契约失败、M3 输出失败、M4 构建/行为失败、截断、超时、基础设施缺失和未知执行状态；不得盲目重采样。
  - [ ] 用真实工具跑通固定参考候选的统一评估；检查候选不能改受信测试、评分或私有材料。
  - [ ] 验证结构化运行输出符合适用注册 schema，且能从原始事件重建终端与结果；修复仍暴露的问题后只重跑受影响检查。
- **输出文件（计划）：** `artifacts/structure-generation-paper/<integration-id>/validation.xml`、`integration-verification.md`、实际合同要求的事件/轨迹/结果和日志。
- **验收标准：** 两条件全链可核对，关键负例失败方式正确；参考候选的真实工具行为符合预期；无新增付费调用。只有满足所需行为才验收，不用通过测试数量代替验收。所有开发记录明确不构成模型效果证据。
- **前后依赖：** 依赖 P03/P04；通过后才能进入 P06。状态：未开始；现有 221 项回归不代替本阶段。

## P06　有界真实模型 pilot

- **输入材料：** P05 验收；具体模型/版本、接口能力；明确的 pilot 任务、样本与调用/token/费用/工具/时间上限、重试和停止规则。
- **具体任务：**
  - [ ] 先写完整 pilot 方案和成本上界；用户已有授权仅复用其明确覆盖范围，缺少预算项时只询问缺项。
  - [ ] 建议起点为 3 个调试任务各 1 对，即 6 个条件输出；无重试且每阶段一次调用时为 9 次实际调用，另记录两组各自独立归因成本。此数值仍是提案。
  - [ ] 获得有范围、有资源上限的执行授权后运行，保留全部输入、输出、失败、来源、截断、实际成本与日志；完成即停，不自动扩量。
  - [ ] 只检查流程、测量和开销是否可靠；发现问题则记录修订，不挑最好任务或用私有评估结果调方法。
- **输出文件（计划）：** `reports/manuscripts/discussions/structure-generation-paper/pilot-plan.md`；`artifacts/structure-generation-paper/<pilot-id>/pilot-review.md`及实际合同承载的不可变运行包。
- **验收标准：** 授权范围与实际执行相符；每个预定位置有可解释结果或缺失原因，费用可核算；流程验收不要求 M4 获胜。若 protocol/代码有影响比较的修改，不以旧 pilot 当新版本资格。
- **前后依赖：** 依赖 P05 和 pilot 范围/预算；结果进入 P07，必要时返回 P02–P05。状态：未开始，模型与费用上限待定。

## P07　主对照方案锁定

- **输入材料：** P06 pilot 及其修订；重新通过的受影响离线检查；P01–P05 的最终版本。
- **具体任务：**
  - [ ] 固定任务/设计簇、配对和重复数、生成契约与准入、模型与解码、顺序、token及工具/时间/费用限制。
  - [ ] 固定主要/次要指标、完整与条件分母、基础设施缺失处理、分析方法和结果表结构；不按 pilot 有利效果筛任务。
  - [ ] 区分 pilot 和主对照材料；示例“6 任务×3 对”只能在独立设计覆盖、预算和主张匹配后决定，不能当成通用充分样本量。
  - [ ] 绑定代码、未提交差异、任务、评估及工具版本；按既有记录合同保存，不新增相互竞争的冻结格式。
  - [ ] 单独明确主实验执行范围和上限；pilot 授权不自动继承为主实验扩量许可。
- **输出文件（计划）：** `reports/manuscripts/discussions/structure-generation-paper/main-study-plan.md`、`analysis-plan.md`；`artifacts/structure-generation-paper/<main-id>/` 内由现有记录机制保存的配置、代码状态和版本绑定。
- **验收标准：** 计划在主结果产生前确定；所有待定资源项已解决；独立单位没有被随机重复放大；许可范围和可发布内容明确。称“本篇主对照”而非自动取得 v2.2 官方 campaign 权限。
- **前后依赖：** 依赖 P06；若修改方法/评分，先完成相应版本记录和受影响 P03–P05；为 P08 提供唯一执行输入。状态：未开始。

## P08　主对照执行

- **输入材料：** P07 锁定计划、配置和代码版本；主实验明确执行授权。
- **具体任务：**
  - [ ] 严格执行预定两条件配对；记录同一契约、各自工程调用、终端候选、工具结果和全部成本。
  - [ ] 共享契约失败保留在两组完整分母；M3/M4 独有失败和基础设施缺失按预定规则处理。
  - [ ] 不看私有结果继续修复或挑选，不修改方法以追求优势，不自动补跑到显著。
  - [ ] 中断后仅按可核实执行状态恢复；任何改版或超范围需求单独记录，不覆盖原始输出。
- **输出文件（计划）：** `artifacts/structure-generation-paper/<main-id>/` 的实际注册事件、轨迹、成本、outcome、封存候选、工具日志；`execution-review.md`。
- **验收标准：** 每个预定位置都可核对；完整分母、源码/配置/工具版本和执行成本一致；无静默失败排除。完整执行但无优势可以通过执行完整性验收，不能伪写为效果成功。
- **前后依赖：** 依赖 P07；完成后进入 P09。状态：未开始，没有本篇主对照数据。

## P09　结果分析与图表

- **输入材料：** P08 原始运行包、P07 分析规则；只用于明确比较/背景的历史材料。
- **具体任务：**
  - [ ] 从原始产物重建每个条件的结构、可信功能、综合、成本、失败和缺失结果，核对全部分母。
  - [ ] 以任务/设计簇处理依赖；单列共同合法契约的条件分析；报告不确定性与有限范围，不把重复当独立任务。
  - [ ] 对结构故障归因抽核真实诊断；“结构符合”不等于“算法正确”，程序提供的结构不计作模型自行生成成果。
  - [ ] 生成主表、配对比较、阶段失败图和成本图；区分预定分析与探索性分析，保留负结果。
- **输出文件（计划）：** `artifacts/structure-generation-paper/<analysis-id>/analysis-review.md`、`tables/*.csv`、`figures/*.svg`、`figures/*.pdf`；必要分析代码放实际 owning 路径，名称在实施时确定。
- **验收标准：** 表格能追溯到样例与事件；独立重算关键计数一致；图与数据、失败分母一致；全部统计主张在有限任务与版本内成立。CSV/图表只是派生分析，不能替代注册运行记录。
- **前后依赖：** 依赖 P08；产出进入 P10。状态：未开始；本阶段只产出分析说明、表图，不写论文 Results 正文。

## P10　提纲与主张核对

- **输入材料：** P02 文献差异和协议；P09 表图及限制；用户的 SCIE 要求、作者/单位与公开限制。
- **具体任务：**
  - [ ] 完成标题候选、章节提纲、每节证据分配及拟表达主张清单；不写成稿段落。
  - [ ] 建立主张—证据—限制映射，删除或降低缺证据的性能、泛化、训练、修复、PC 2.1 或上板主张。
  - [ ] 核对候选期刊当时的官方 SCIE、范围、模板和单位认可要求；不把影响因子或历史收录替代当前覆盖。
  - [x] 最新目标“持续推进，允许实验，找到gap，和创新点，完成SCI初稿”已明确授权正文；后续不重复请求同一确认。
  - [ ] 核对提纲、证据表、语言/模板及未解决问题，按实际验证范围约束所有实证主张。
- **输出文件（计划）：** `reports/manuscripts/discussions/structure-generation-paper/manuscript-outline.md`、`claim-evidence-map.md`、`submission-target.md`；用户确认记录链接写回本阶段。
- **验收标准：** 每项实证主张有对应证据；未验证的机制与差异明确标假设，不能由写作授权推定创新成立。阶段性初稿允许保留清楚标识的研究缺口，不将其称为可投稿完成稿。
- **前后依赖：** 完整主张验收依赖P02/P09；已验证开发结果可先进入获授权初稿。状态：正文授权已取得，主张核对继续进行。

## P11　正文撰写与修订（已授权）

- **输入材料：** P10 用户明确确认的范围、提纲、主张表与目标模板；P02/P09 的真实材料。
- **具体任务：**
  - [ ] 仅在明确确认覆盖范围内撰写摘要及相应章节；方法写实际执行版本，结果只用核实数据。
  - [ ] 完成引用核对、图表引用、局限性、数据/代码可用性和实际 AI 使用披露。
  - [ ] 依据稿件审查问题定向修订，不增加未验证结论，不把旧稿缺证据数值带入新稿。
- **输出文件（已创建）：** [研究初稿v0.1](../drafts/structure-responsibility-v0.1.zh.md)，以中文Markdown供审阅；引用与原始证据链接随稿保留，后续是否转为英文/模板不影响当前起草。历史稿件保持原状。
- **验收标准：** 正文在已确认范围内；事实、数字、代码版本、图表和引用一致；缺失或负结果如实表达；“写完”不等于已达期刊接受或正式发布。
- **前后依赖：** 最新目标已提供正文授权；完整稿验收仍依赖P10主张核对及充分研究证据。v0.1已创建并补入第二轮实测；整体目标继续active，P12未开始。

## P12　投稿包与复现交付

- **输入材料：** P11 完整稿及审查；P07–P09 运行/分析材料；作者确认、版权/许可、目标期刊要求及发布边界。
- **具体任务：**
  - [ ] 生成目标模板稿、图表、补充说明、披露和复现操作说明；检查从源文件到最终 PDF 的一致性。
  - [ ] 整理最小可检查软件/数据包，排除凭证、私有端点、evaluator-private 内容及无发布许可材料。
  - [ ] 完成内部预提交核对；把未解决审稿风险和复现限制交给用户。
  - [ ] 外部代码/数据发布、提交期刊、支付 APC、推送或部署均按明确目标与已有授权处理；本清单不授权这些动作，也不同时多投。
- **输出文件（计划）：** `artifacts/structure-generation-paper/<submission-id>/manuscript.pdf`、`submission-check.md`、`reproduction-guide.md`及选定格式的补充包；需要正式晋级的材料按既有受控流程处理。
- **验收标准：** 投稿文件可打开、格式和图表正确、作者/声明完整、关键结果可追溯；敏感与未许可材料未外发。准备完成、已提交、录用、发表、实际 SCIE 检索分别记录，不互相替代。
- **前后依赖：** 依赖 P11；公开和提交属于独立外部动作。状态：未开始。

## 当前下一步与维护方式

最新执行以N18–N50为准：N19/N20已完成组合normal-only资格，尚无选择协议额外收益，停止扩大LLM链/pilot；N23也已停止R1b独立核心。[N27](structure-generation-paper/stateful-task-readiness-review.md)收口历史追溯，[N28](structure-generation-paper/interface-realizability-candidate-review.md)补数学区分但不开发。[N29](structure-generation-paper/generation-gap-case-review.md)取得外部错误，[N30](structure-generation-paper/specification-acquisition-review.md)核规格获取，[N31](structure-generation-paper/counterexample-clarification-neighbor-review.md)核XOR澄清，[N32](structure-generation-paper/remaining-public-task-source-review.md)另核三家族原始需求并完成两份独立构思，均未建立新核心。新增三家族4份原件仅3种单句，不能直接当完整messages或已准备好等价变体；不靠换功能名扩模型样本。[N33](structure-generation-paper/comparison-endpoint-audit.md)确认当前N19/N20起点相同并收窄过强恢复门，维持停止：同能力可有真实成本/可靠性价值，但尚无新链/配对收益。[N34](structure-generation-paper/external-serial-adapter-candidate-review.md)取得外部串行相位例；[N35](structure-generation-paper/state-adapter-standard-baseline-review.md)已深核协议适配并补同信息普通控制，当前屏蔽/捕获步骤尚无额外处理或成本收益，停止C34单独核心开发投入，保留案例，不采纳外部任务。[N36](structure-generation-paper/generated-artifact-binding-review.md)新增作者KG/RTL快照差异及配置计分入口证据，同次生成和原请求绑定未闭合，不冒称运行失败或新机制；若归因历史失败须先核实际需求/计划/首次输出配对；新设计仍可凭真实必要任务和静态区分立项，不将历史失败当通用必要前提。N20不验证原单槽或N28完整流程，可信F与依赖ABI也不是免费输入。下一项机制须先有真实问题、同信息标准能力、明确额外处理及谁提供语义真值；本轮不为明确数学另造NL/澄清原型。外部IP、参考驱动修订、人工交互或正式采纳新任务须先具体讨论，均未采纳。用户已选择先评审N24工具系统定位，以可靠性为先、暂不主张人工省工；[N37](structure-generation-paper/contract-frontend-task-readiness.md)完成只读能力评审；[N38](structure-generation-paper/external-architecture-audit-task-review.md)补独立工程需求，但现有时序单侧响应与当前合同不同，S1同类任务/S2区别处理仍未闭合，不进入开发。正式发表占用按[N38身份审计](structure-generation-paper/publication-status-novelty-audit.md)，与技术强对照分开。[N39](structure-generation-paper/verification-delivery-reliability-review.md)再核历史探测对象错误及空泛性方法，手推三条件不足；优化前wrapper等仍无区别处理，不作新核心开发，不扩模型样本。[N40](structure-generation-paper/configuration-obligation-completeness-review.md)确认声明清单对账及OCRA语义义务生成已有，触发域候选因标准蕴含与实际编译提取未定义撤回；仅准备工件审计边界，不采纳新对象/任务。[N41](structure-generation-paper/compiled-monitor-audit-method-review.md)已具体化中间接口、实际绑定、开放轨迹及报告时间的比较卡，系统交接收益仍未证；用户已选择评审对象扩展，后续可核两个真实案例/强对照，不由此启动开发或实验。[N42](structure-generation-paper/manuscript-v0.3-current-evidence-audit.md)在待答期间完成初稿/记录独立审计，列可复用材料与未来修订差距，正文未改，后续仅按新答复准备两个真实案例，不追认为既有实验。[N43](structure-generation-paper/verification-artifact-two-case-readiness-review.md)已核两项真实断言来源及build入口，但配置、独立参考、异步/四态资格与区别处理未闭合，未进入开发或效果研究。N25[期刊政策](structure-generation-paper/publication-route-evidence-review.md)不代替系统贡献证据或新campaign授权。下列既有停止结论和维护约束继续适用。

1. 已完成唯一追加的有界设计，按约定停止局部责任划分作为核心贡献，不再为它扩查、追加自动规则轮次或写planner。结论及反例见[评审记录](structure-generation-paper/local-responsibility-bounded-design-review.md)。
2. [连接候选裁决](structure-generation-paper/connection-choice-decision-review.md)保留原结论。当前原型、12次原生生成、24项有限评价、16个全域局部证明及强近邻复核已完成；具体限制见N6/N11。[两个结构变体](structure-generation-paper/independent-method-core-review.md#7-最新范围两个保持完整顶层函数的结构变体)、N12重组和N13交接审查仍未建立新核心。N13已列出实际语义输入与人工责任，当前未证实更少规范或工时。后续研究应围绕真实未满足的交接需求：先明确标准流程缺什么、新规则多做什么及同信息反例，再设计可复核的成本/可靠性对照；有实质差别后才开发和预定模型pilot。当前不追加筛选模型失败的调用，不把手写反例当模型失败率，不自动引入M06新并发或PPA目标。
3. 每阶段完成时，更新状态、勾选实际完成项，并附相应产物和执行证据；未满足验收的阶段保持部分完成或未开始。
4. 本清单只记录本篇准备进度，不修改 `docs/current-status.md`、现行研究计划、历史数据或官方 gate 状态，不另建平行 JSON 进度系统。
5. **最新用户目标已授权P11初稿与实验。** 新的原生Codex生成是有界开发哨兵，按plan.md单独记录，不覆盖历史诊断或正式研究状态。正文须区分已实测、实现目标与待验证假设；研究证据不足时保持目标active，不能以一个流程哨兵替代SCI论文任务。
