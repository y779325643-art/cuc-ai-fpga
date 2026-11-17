# P02：结构生成论文的相关工作证据矩阵

日期：2026-10-21。用途：投稿路线准备与主张边界核对；不是 Related Work 正文、系统综述、原创性证明或实验结果。当前研究权威仍见 [paper1-v2.2](../../../../docs/specs/2026-09-15-sr2fpga-paper1-research-plan-v2.2.zh.md)，本记录不修改其定义或授权。

本轮关注的窄问题：**给定同一个已生成的 System-HIS，比较 M3 的完整工程生成与 M4 的确定性 top／实例／连线构建加受限行为填充，测量 initial 结果，不使用修复。** 这是待形成具体实验的比较对象，不是现有数据已经证明的结论，也不等于当前 PC 2.1 新 AI 任务闭环。

## 1. 检索与选择记录

- 检索日期：2026-10-21；本轮只做有界、问题驱动的定位，不声称覆盖全部相关工作。
- 起始集合：指定的 VerilogEval、RTLLM、AutoChip、HORIZON、STG、CLOSER-Bench、ChipVerilog。
- 补充原则：优先纳入明确涉及层次分解、可检查表示、结构装配或编译器 lowering 的机制近邻；不能只与早期单模块 benchmark 比较。
- 使用的查询包括：`site.arxiv.org VerilogEval evaluating large language models Verilog code generation 2309.07544`；`site.arxiv.org RTLLM open source benchmark RTL generation 2308.05345`；`site.arxiv.org AutoChip Automating HDL Generation Using LLM Feedback 2311.04887`；`site.arxiv.org 2606.12983 STG`；`site.arxiv.org RTL generation hierarchical decomposition deterministic structural skeleton module interface top-level LLM`；`site.arxiv.org "RTL" "intermediate representation" "deterministic" "generation" LLM`；`site.arxiv.org "RTL" "top-level" "hierarchical" "LLM" generation 2025`。
- 以 arXiv 官方摘要页确认标识／版本，打开其 HTML 方法或评估章节支持矩阵特征。检索中出现的二次摘要网站只作线索，不作特征证据。HINT 的参考文献提供了 CPPL 标识，随后核对 CPPL 官方页面。
- 补入 VeriGraphi、Hierarchical IRs、HINT、CPPL。用户选择“先核对创新性，再开发”后，于同日补读 CPPL §III–IV，并针对其他三项近邻复核具体对照边界；没有扩展为系统综述。
- 仓库 [历史 citation registry](../../../../docs/research-program/paper1-v1/foundation/canonical-citation-registry.md) 只作路由线索。其“已核实”不能替代本轮阅读记录；不继承其历史 claim-ready 权限。
- 未做：Web of Science／Scopus 全库检索、系统性筛选、原始实验复现、作者代码全量审计、完整 PDF 图表审读或文献的发表／收录状态认证。CPPL 作者当前代码仅抽查下述固定 commit 的 frontend／worker／README；不将其当成论文 v1 的实验快照。未把本记录内容上传给外部模型。

**阅读标签：** `方法段已核对` 表示下列具体 HTML 章节实际阅读过；`摘要级` 只能支持摘要明确描述的内容。`未核对` 表示当前证据不足，不能改写成“该工作没有”。文中方法与结果描述仍是作者报告，不是本项目独立复现结论。

## 2. 指定工作的证据矩阵

| 工作与固定原文版本 | 本轮阅读范围与生成对象 | 结构责任的已观察事实 | 验证与对照的已观察事实 | 对窄比较的关系与边界 |
| --- | --- | --- | --- | --- |
| **VerilogEval**；[2309.07544v2](https://arxiv.org/html/2309.07544v2)，2023-12-10 | 方法段已核对：§II-A、II-B、II-C；从文字描述及 module header 生成 Verilog completion。 | §II-A 明确把 self-contained 定义为不需要实例化其他模块，并说明该版不评估模块实例化能力。 | §II-C 使用 generated completion 与 golden solution 的仿真输出比较。 | 可说明该固定版本与多文件结构任务的范围区别；不能据此声称全部 VerilogEval 后续版本或其他基准都不涉及结构。后续版本未在本矩阵全面核对。 |
| **RTLLM**；[2308.05345v3](https://arxiv.org/html/2308.05345v3)，2023-11-11 | 方法段已核对：§II、III-A–C、IV；自然语言到设计 RTL，含不同结构要求的设计。 | §IV self-planning 先生成自然语言推理／实现计划，再交给模型生成 RTL；§III-C 的示例已有层次／流水等实现要求。 | §III-A 区分语法、功能与设计质量；§I／IV 描述模型及 self-planning 比较。 | “先计划后生成”不是本项目新颖性。论文版与当前 RTLLM 仓库的数据版本不可混用；同一生成计划下只改变确定性结构装配的配对实验，本轮未核对到。 |
| **AutoChip**；[2311.04887v2](https://arxiv.org/html/2311.04887v2)，2024-06-04 | 方法段已核对：§3、§4 的入口与任务表；给定描述、模块定义和测试条件生成 Verilog module。 | §3 的具体 system prompt 限制输出目标 module；任务表又包含 module-hierarchy 类题目。因此不宜把整项工作笼统描述为“完全不涉及层次”。 | §3 使用编译／仿真反馈迭代，终止于通过或次数上限；§5 的研究问题包括反馈与模型条件。 | 是工具反馈／修复路线的背景。本文拟测 initial 无修复，不能将对方最终迭代通过率直接当成同条件基线，也不能声称首创生成—工具—修复闭环。 |
| **HORIZON**，*Agentic Hardware Design as Repository-Level Code Evolution*；[2606.28279v1](https://arxiv.org/html/2606.28279v1)，2026-06-26 | 方法段已核对：§3 system overview、任务构建及 trace；§4 setup。生成／演化对象包括 RTL、验证工件和任务仓库。 | bootstrap agent 从 Markdown harness 构造 project pack，固定 evaluator、acceptance predicate 与运行／版本控制政策；后续 agent 修改 worktree。 | evaluator 封装各 suite 的原生 harness；轨迹保留 diff、版本和运行证据，过程含多轮搜索。 | 工程包、执行证据、版本轨迹和 agentic hardware 已有直接先例。本轮未核对其每项 edit allowlist 或全部实验配置，不能断言其“没有隔离／没有预算／没有结构处理”。 |
| **STG**，*Structured Testbench Generation for LLM-Driven HDL Design and Verification-Oriented Data Curation*；[2606.12983v1](https://arxiv.org/html/2606.12983v1)，2026-06-11 | 方法段已核对：§2.1–2.2、§3、§3.1。主要生成对象是 testbench。 | 输入 DUT 与 golden reference，解析模块／层次和设计种类，以参数化 Jinja 模板确定性构造 testbench；分析步骤允许轻量 LLM 查询。 | 编译执行并产生 pass/fail 与 coverage；§2 明确区分 trusted golden 与 LLM silver reference。 | 确定性模板和独立参考验证不是新贡献。它的生成对象与 DUT top 构建不同；不能从“对象不同”推断本项目机制原创或把 STG 当 DUT 生成强弱比较。 |
| **CLOSER-Bench**，*Evaluating Budgeted Cross-Stage Design Closure for Hardware Agents*；[2607.16632v1](https://arxiv.org/html/2607.16632v1)，2026-07-18 | 方法段已核对：§3 Design Principles、Stage-Paired Tasks、Budget and Trajectory Protocol。对象覆盖 spec→RTL、RTL→GDS、spec→GDS。 | 由评估协议控制起始边界、可编辑层和隐藏条件；同一设计意图形成跨阶段配对。 | 原文明确控制 aggregate budget、记录工具调用与轨迹，并区分公开反馈和隐藏 signoff。 | “配对、预算、轨迹、公开／隐藏分离”不能作为空白定位。其已读配对是跨阶段 closure；本项目拟比较同一生成 HIS 下的结构责任，仍需解释增量而非泛称首次受控评估。 |
| **ChipVerilog**，*A Large-Scale OpenCores-Derived Benchmark for LLM-Based Verilog RTL Generation*；[2607.13079v3](https://arxiv.org/html/2607.13079v3)，2026-08-17 | 方法段已核对：§3.3–3.4、Table 2。输入来自规格与参考 RTL 整理的描述，目标含单模块、跨模块及 IP/core。 | §3.4 的 multi-module 验证只替换 target module，其他 submodules 保持 reference 实现；与从零生成全部子模块的责任范围不同。 | 初始语法／编译／elaboration；局部及 multi-module 目标做等价，full-system 用仿真；Table 3 按多个生成样本报告。 | “多模块／跨模块已无人研究”明显不可写。可比较的是结构支持来自何处、谁负责生成；不能把其 reference 周边模块当作模型全工程生成，也不能直接拼接通过率。 |

## 3. 机制近邻：必须正面处理的重叠

| 工作与固定原文版本 | 本轮已读的机制证据 | 验证／对照范围 | 对本项目定位的具体影响 |
| --- | --- | --- | --- |
| **VeriGraphi**，*A Multi-Agent Framework of Hierarchical RTL Generation for Large Hardware Designs*；[2604.14550v2](https://arxiv.org/html/2604.14550v2)，2026-04-19 | 方法段已核对：§III-B–D、Algorithm 1。先形成包含端口、层次及连线关系的 HDA；§III-D5 的 Code Assembler 根据 INSTANCE_OF／CONNECTS 生成 top wrapper，子模块自底向上生成。 | §III-D3–5／Algorithm 1 含 syntax checking 与有限反馈重试；§III-E 描述从规格构建验证，而非仅凭代码可编译。未审计其 assembler 实现是否完全确定性。 | **直接强重叠。** 结构图、受检查 scaffold、top 装配和模型子模块生成均已有先例。可继续追问同一生成 HDA／HIS 下结构责任转移的 initial 配对，但不能先写“首次确定性 top 装配”。 |
| **LLM-based Hardware Development with Hierarchical IRs and End-to-End Multi-Agent Workflow**；[2608.30659v1](https://arxiv.org/html/2608.30659v1)，2026-08-31 | 方法段已核对：§2、§3.1–3.3。Architectural Sketch 描述拓扑／连接，Operational Specification 描述各块接口与行为；先生成子模块，再据这些信息构建 top。§3.2 还描述确定性 testbench 构造。 | §4.3.1 做 direct-generation／direct-repair 与去除各 IR 的消融；§4.3.2 比较两种 debug。已读实验含多次调用或 debug，不能当作本项目 initial 同条件结果。 | **直接强重叠。** 不能主张首个“结构＋行为 IR”或首个 IR 消融。已读消融并不是本项目拟定的同一已生成 HIS、仅改变结构构建责任的实验；是否已有等价设置仍需核查完整实现。 |
| **HINT**，*Toward an Executable Hardware-Intent Representation Layer for LLM-Driven RTL Generation*；[2608.07625v2](https://arxiv.org/html/2608.07625v2)，2026-08-19 | 方法段已核对：§3、§4.1。可执行硬件意图表示显式规定接口、状态、schedule 和资源；先接受 HINT，再以 lowering obligations 约束 RTL 实现。原文区分其 agentic lowering 与传统确定性 compiler pass。 | §4.1 固定测试资产、事务级检查，并允许局部 realization repair；§5 controlled study 与跨规模 workflow 的条件不同。 | **概念强重叠。** “可执行意图／pre-RTL 检查／结构行为分离”不能首创。可检验差异是具体的确定性发射与模型编辑边界及同 HIS initial 测量；这仍是假设定位。 |
| **CPPL: A Circuit Prompt Programming Language**；[2605.17892v1](https://arxiv.org/html/2605.17892v1)，2026-05-18 | **方法／评估段已核对：§III-A–D、Figs. 5–12；§IV-A–D、Tables I–IV。** 前端 DSL 显式给端口、层次和连接，确定性展开；预置实例与模型生成的 circuit operations 分开，再 lower 至 CIRCT／Verilog。 | §III-C 在 lowering 前有编译器错误反馈；§IV-A 设置三次 refinement、每题十个 sample，报告 pass@1／2／5。三路径共享 design description，不能据此称共享同一实际生成 IR；§IV-D 是 compiler optimization 开关消融。 | **直接强重叠。** 不能将“可信结构＋模型剩余逻辑＋确定性编译”整体写成新方法。论文没有在所读段落充分交代全部实验 DSL 的人／模型来源，也未报告目标同一生成契约下的 initial 责任转移对照；这些是阅读范围内的未决项。 |

以上机制特征均按各行指定原文段落记录，不依据二次概述补齐。VeriGraphi 的 assembler 是否纯程序、Hierarchical IRs 的 top 编辑政策，以及 CPPL 论文实验中 DSL 的实际来源与每个 sample 内部调用计数，仍有实现／原始记录级未决项。

## 4. 当前能形成的可检验差异

以下是待检验问题及需要保存的证据，不是已成立的贡献结论：

| 拟检验差异 | 应固定／记录什么 | 结论上限 |
| --- | --- | --- |
| 条件于同一个**生成**的 System-HIS，转移 top／实例／连线的生成责任是否改变 initial 结构错误与整体通过情况 | 两条件引用同一实际 HIS 字节及哈希；说明其生成、检查和失败分母；分别记录模型输出、确定性产物、结构检查与独立功能结果 | 只能归因于该已实现干预及其任务范围；不是自然语言到硬件的无条件系统增益，也不是“模型更会推理” |
| 受限行为填充是否减少结构错误，同时保留可测的行为失败 | 允许编辑的文件／区域；生成前后结构一致性；禁止改动的事实；模型可见上下文；实际不同的 prompt 和输出负担 | 不能把整个 treatment 的变化压缩成纯“表示效果”；需承认代码量、责任边界和提示内容同时变化 |
| 初始结果是否能与修复／搜索效果分离 | 初始候选不可变快照；在工具反馈前截断；全部模型调用、token、失败与 timeout；不选择多次尝试中的最佳结果 | 无修复只回答 initial 问题；不能据此声称修复效率、长期 agent 搜索或等总预算的最终优越性 |
| 确定性结构贡献占结果的多少 | 单列可信结构与模型行为的来源，检查预置模板／模块是否已经完成任务核心；外部 oracle 和控制例独立报告 | 工程成功可包含可信代码贡献；不能将可信模板的正确性全部归给模型，也不能将框架回归测试数当模型样本数 |

本地机制入口可供后续对齐：[method_contract.py](../../../../agent/src/sr2fpga_agent/method_contract.py)、[contract_skeleton.py](../../../../agent/src/sr2fpga_agent/contract_skeleton.py)。它们是当前实现的定位线索，不证明上述实验已经可按相同输入、独立功能 oracle 和完整分母运行。

## 5. 当前不能写的主张与待办

- 不能写“首次将结构化契约／IR 引入 LLM 硬件生成”“首次分层生成”“首次用确定性模板减少幻觉”“首次可检查 top 装配”或“首次工具反馈闭环”。上表已有明确重叠。
- 不能写“现有工作都只生成孤立模块”“没有多文件／层次 benchmark”“既有研究不考虑预算或轨迹”。ChipVerilog、层次方法与 CLOSER-Bench 已直接反驳这些泛化。
- 不能把别人的最终迭代／best-of-k 成功率与本项目 initial 成功率并列成公平性能比较；需要匹配目标、输入信息、生成责任、oracle、版本和预算。
- “同一生成 HIS 的 M3/M4 initial 责任转移比较”目前是**可能的窄增量**，不是本轮检索证明的空白。检索非穷尽；最近机制工作已有强重叠，原创性仍未解决。
- 后续若继续，优先解决 CPPL 论文的实验 DSL 来源／内部调用记录及 VeriGraphi assembler 的程序性，而非继续堆叠泛相关论文；再决定机制基线或有界实证分析的必要性。这里只列待办，不启动开发、框架复现或新实验。
- 本轮交付完成的是证据矩阵与未决项，不能据此标记“文献新颖性审查通过”或给录用概率；也没有完成稿件引用格式、全部 bibliographic 元数据或投稿合规检查。

## 6. 创新性复核结论：2026-10-21

范围：对四项机制近邻做章节级复核；CPPL 另抽查作者仓库 commit `d7ebbb5f4036ac57a768bc362996ab05e8c39b9f`。这次是有界定位核对，没有执行作者框架或本项目实验。

| 对照工作 | 已确认的强重叠及精确来源 | 与拟研究窄对照的关系 | 保留的阅读／实现限制 |
| --- | --- | --- | --- |
| **CPPL v1** | [§III-A/Fig. 5、§III-B/Fig. 8、§III-C–D/Figs. 9–12](https://arxiv.org/html/2605.17892v1)：DSL 展开接口和实例连接；模型生成操作；编译器检查后确定性发射，并在有效 IR 形成前反馈重生成。[作者当前 prompt L254–303](https://github.com/SawyDust1228/CPPL/blob/d7ebbb5f4036ac57a768bc362996ab05e8c39b9f/cppl/frontend/prompt.py#L254-L303) 区分预置／延后实例；[worker L106–119](https://github.com/SawyDust1228/CPPL/blob/d7ebbb5f4036ac57a768bc362996ab05e8c39b9f/cppl/agents/worker.py#L106-L119) 和 [L346–349](https://github.com/SawyDust1228/CPPL/blob/d7ebbb5f4036ac57a768bc362996ab05e8c39b9f/cppl/agents/worker.py#L346-L349) 表明部分实例由程序放置后与模型 body 拼接。 | [§IV-A、Tables I–III](https://arxiv.org/html/2605.17892v1) 是相同 description 的三种输出路径，并配置 refinement；**pass@1 不等于无反馈首轮输出**。[§IV-D/Table IV](https://arxiv.org/html/2605.17892v1) 消融 CIRCT optimization。所读实验未报告两条件复用同一实际生成架构字节、在 initial 切断反馈的责任转移比较。 | 前端接口支持用户提供结构；当前 [README 的 Agent Runtime](https://github.com/SawyDust1228/CPPL/blob/d7ebbb5f4036ac57a768bc362996ab05e8c39b9f/README.md) 明确 user-written module，但不证明论文每项 DSL 都人工编写。论文每 sample 内部请求／失败处理与 baseline 总资源是否匹配未充分说明；当前 LangGraph 与 static-repair 计数不可反推 v1。 |
| **VeriGraphi v2** | [§III-C–D、Algorithm 1](https://arxiv.org/html/2604.14550v2)：HDA 已包含层次／端口／连接；Code Assembler 使用 parent spec、child RTL 和连接图构造 top。先逐模块编译反馈，再对 top 反馈。 | [§V Tables I–II](https://arxiv.org/html/2604.14550v2) 分别比较编码迭代／人工干预和物理指标；已读正文未报告同一生成 HDA 下“全模型工程 vs 程序 top＋模型行为”的 initial 无反馈消融。 | 正文称 assembler 为 Agent；不能由 deterministic scaffold 字样推出纯程序 emitter。作者链接的 KG demo 是图展示，未提供本轮可核的生成器／assembler 源码；未执行或复现。 |
| **Hierarchical IRs v1** | [§2、§3.2](https://arxiv.org/html/2608.30659v1)：Design Generator 按 IR 生成子模块，再由 Sketch、OpSpec 和子 RTL 构造 top；该节明确确定性的是 testbench。 | [§4.3.1/Table 6](https://arxiv.org/html/2608.30659v1) 比较 direct generate-k／repair-k、去除 OpSpec、去除 Sketch（改单模块），均有 debug 条件；[§4.1](https://arxiv.org/html/2608.30659v1) 的无 debug 测量是单模块 OpSpec 增强。均不同于本项目拟定的同一实际 IR 初始结构责任干预。 | 不能声称作者没有受控消融，也不能把 top 已经确定性生成作为事实。未审计完整生成器源码或其实际 IR／candidate 共享记录。 |
| **HINT v2** | [§3、§4.1](https://arxiv.org/html/2608.07625v2)：可执行意图与预先检查约束 RTL realization；lowering 是 agentic，并允许 correctness repair。 | [§5.1–5.2/Table 2](https://arxiv.org/html/2608.07625v2) 控制模型、外部 contracts、oracle／verifier、编排与 revision 预算，比较 HINT 整条路线和 Direct；Direct 不以同一生成 HINT 为输入。首个成功综合即停止也不是首次输出。 | 已有受控 route-level 实证，不能把“受控比较表示”当空白；未核到同一生成 HINT 字节上的 initial 结构责任消融，不等于穷尽证明该设置不存在。 |

**判定：方法组合存在强重叠；在以上已核范围内，未发现严格等价的窄对照。** 目前最多支持“有误生成架构条件下，保留共享准入和完整失败分母的 initial 结构责任转移，是值得用小规模试验检验的实证问题”。这不是方法首创认定，不证明论文已满足 SCI/SCIE 的创新性或录用要求，也不授权立即开发或运行实验。若后续对照只是换表示／换工具链而没有隔离责任干预，其增量会与 CPPL、Hierarchical IRs、HINT 更难区分。

## 7. 局部责任划分的传统编译器近邻

本轮对方法卡补做有界查新，重点是方法机制本身而非其 initial 对照。原始来源如下；没有复现这些框架，也不把历史 RFC 当现成已实现能力。

| 原始来源及已读范围 | 已有内容 | 对当前方法卡的限制 |
| --- | --- | --- |
| [MLIR Dialect Conversion：Modes of Conversion、Conversion Target](https://mlir.llvm.org/docs/DialectConversion/) | 按合法性/动态合法性转换部分操作，允许某些原有操作不转换；另有只分析可转换性的模式 | 支持判定、部分转换和残余保留不是新编译思想；MLIR 不据此承担模型生成未知行为的正确性 |
| [TVM BYOC extended graph partitioning RFC：术语及 Steps 1–4](https://discuss.tvm.apache.org/t/rfc-byoc-an-extended-graph-partitioning-flow/6028)，2020-03-19历史提案 | 原子支持区域、编译归属互斥/覆盖、依赖合并、区域边界与导出；原文明确若干步骤当时未实现 | 给定 E_c 后分组并交给两个后端，与其骨架直接重叠；不把模型作为第二后端就称新算法 |
| [Jones/Gomard/Sestoft 作者目录](https://raspi.itu.dk/people/sestoft/pebook/toc.html)，目录/作者介绍级 | 部分求值、binding-time analysis、division、annotation consistency 是既有主题 | 本轮未全文审读，不引用具体正确性定理；模型补未实现行为也不能直接继承部分求值的语义保持结论 |

**当前判断：方法卡尚未通过新增机制门槛。** 与 CPPL 的实例预置/延后判据有区别，但 E_c 仍由预设原语给定，尚无自动推导及非平凡区分案例。下一项研究工作应是[方法卡 §10](local-responsibility-method-card.md#10-规则反例普通分区基线当前立项缺口)的规则—反例表与匹配普通分区比较，不以纯 planner/表达式实现替代新颖性验证。此判断不否认工程可实现性，也不把未发现等价论文当作原创新颖性证据。

## 8. 最后一轮有界设计：已执行停止条件

用户批准的最后一轮已完成，结论为 STOP；[完整推导与决定](local-responsibility-bounded-design-review.md)保留LINK、SELECT2、stall和同信息普通分区的比较。

本轮仅新增核对[CIRCT Handshake操作语义](https://circt.llvm.org/docs/Dialects/Handshake/)和[Dynamatic官方教程](https://epfl-lap.github.io/dynamatic/GettingStarted/Tutorials/Introduction/ModifyingDynamatic.html)：共享选择索引、token关联、同步/缓冲等均有直接表达与案例。没有复现或推断其已解决任意自然语言语义。

在本候选的显式协议输入范围内，关系约束不能推出共同owner，共同owner也不能保证关系正确；给普通分区同一语义前端可重现分组。因此按预定条件停止将该候选作为新增方法核心，不再为其追加planner实现，不继续以predicate/token换名扩展。此决定不等于论文总任务取消，也不自动恢复纯实证路线或选择其他方法。
