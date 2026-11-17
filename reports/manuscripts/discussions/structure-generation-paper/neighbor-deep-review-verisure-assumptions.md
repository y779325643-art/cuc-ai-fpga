# Veri-Sure：共享合同、假设确认与语义交接深审

日期：2026-10-21。范围仅本篇主源和作者实现；不运行模型、HDL、求解器或框架，不修改旧稿／N15卡／评价。本文的“未见”限定于下列已读方法、附录及源码，不代表领域中不存在相应技术。

**结论：Veri-Sure已经实现生成前的共享设计合同、显式假设及跨代理传播，不能把这些当N15的新点。所核实现没有将“模型提出但未采纳的环境条件”与“有权使用的公开环境”作可信的跨阶段域保全检查。这个差别可保留为待检验系统假设，尚不足以确认新方法贡献，也不需要发明新求解算法。**

## 1. 主源身份与版本

先复用Vault《Veri-Sure - Contract-Aware RTL Agents》，Zotero `J2VJA2Q4`、PDF key `QB53HI46`；其笔记早于本次更新，不能代替新版本原文。

[官方版本记录](https://arxiv.org/abs/2601.19747)列v1为2026-01-27，v2为2026-10-15。现题为 *Veri-Sure: Multi-Agent RTL Code Generation with Temporal Tracing, Slicing and Formal Verification*，作者Jiale Liu、Taiyu Zhou、Tianqi Jiang。本文以[官方v2全文](https://arxiv.org/html/2601.19747v2)及[29页PDF](https://arxiv.org/pdf/2601.19747v2)为准，定向读完整§3.1–3.4、§5.1、§6、Appendix B.1–B.5、C.2–C.3及相关案例；不沿用v1标题推断更强保证。

论文直接链接[作者仓库](https://github.com/xyjoey/Veri-Sure)。固定源码提交[`aab5bed60f04157a4be8581b53f9e913287ba328`](https://github.com/xyjoey/Veri-Sure/commit/aab5bed60f04157a4be8581b53f9e913287ba328)，提交时间2026-10-15 19:01:28 UTC。通过只读接口取得源码，未安装或运行；下文行号均指此SHA，不指浮动main。

## 2. 逐项方法与实际实现

| 问题 | 主源／实现定位及已证事实 | 解释边界 |
| --- | --- | --- |
| 合同何时形成 | v2 §3.1–3.2，PDF pp.4–5；Architect先于RTL写JSON合同，填接口、时序、行为及角落条件。[architect_agent.py L18–65](https://github.com/xyjoey/Veri-Sure/blob/aab5bed60f04157a4be8581b53f9e913287ba328/eda_agent/architect_agent.py#L18) | 生成前共享合同、显式补齐歧义都已存在；不是只给RTL后加assertion |
| 谁决定假设 | 同文件L24–30、47–65：歧义由Architect选择并记录；若提供golden TB，其接口／时序有优先级。合同类型L141–150包含`source_of_truth`及自由文本规则 | 所核生成调用没有逐条人工批准步骤。`source_of_truth`标签不证明每条新增环境限制来自该source；也不应把作者方法说成完全不管来源 |
| 程序检查什么 | v2 B.2，PDF p.20；[contract_linter.py L22–123](https://github.com/xyjoey/Veri-Sure/blob/aab5bed60f04157a4be8581b53f9e913287ba328/eda_agent/contract_linter.py#L22)完整函数检查JSON、端口名／方向／宽度、clock、latency及guidance | 没有在此函数实现行为可实现性、假设逻辑一致性、原输入域包含关系或批准状态核查。不能把该轻量lint解释成这些证明 |
| 是否严格阻止坏合同流入 | [top_agent.py L155–193](https://github.com/xyjoey/Veri-Sure/blob/aab5bed60f04157a4be8581b53f9e913287ba328/eda_agent/top_agent.py#L155)：错误触发最多两轮Architect修订，耗尽后仍写出并返回合同；warnings不触发修订 | 是best-effort修订，而不是所有语义／格式问题均关闭后才允许继续的门；本轮未运行，未测实际残留率 |
| 跨代理是否同一合同 | v2 B.1；[top_agent.py L249–277](https://github.com/xyjoey/Veri-Sure/blob/aab5bed60f04157a4be8581b53f9e913287ba328/eda_agent/top_agent.py#L249)、L334–342、L485–492把同一`contract_json`传给TB、RTL及Debugger；[rtl_editor.py L554–587](https://github.com/xyjoey/Veri-Sure/blob/aab5bed60f04157a4be8581b53f9e913287ba328/eda_agent/rtl_editor.py#L554)再交两formal helper | 统一文本和prompt优先级是实际机制；不等于逐条语义保真证书。不能以“多agent”推断它每次自由重写合同，也不能以同字符串推断行为已遵约 |
| formal reference是否独立可信 | v2 §3.4／B.5；[boolean_proofer_agent.py L13–46](https://github.com/xyjoey/Veri-Sure/blob/aab5bed60f04157a4be8581b53f9e913287ba328/eda_agent/boolean_proofer_agent.py#L13)由LLM将summary转参考SV；不清楚时可补假设写入reasoning。运行层[boolean_proofer.py L479–531](https://github.com/xyjoey/Veri-Sure/blob/aab5bed60f04157a4be8581b53f9e913287ba328/eda_agent/boolean_proofer.py#L479)生成spec与SBY工件 | 不是从可信完整数学规格无歧义编译出的独立oracle；作者自己限定其为诊断提示，不能将prove结果升级为原自然语言意图已获证明 |
| 实际证明对象 | [boolean_proofer.py L121–155](https://github.com/xyjoey/Veri-Sure/blob/aab5bed60f04157a4be8581b53f9e913287ba328/eda_agent/boolean_proofer.py#L121)选组合输出；L200–242让DUT与参考共享主输入并断言输出相等；L511–529为SBY组合证明脚本 | 渲染miter没有计划容量／服务的环境游戏，也没有对采用前提与原允许轨迹域作包含检查。这不表示标准formal工具不能承载这些问题 |
| vacuity与未触发条件 | v2 C.3，PDF p.24，明确监视器可能漏条件而无trigger；[asserter.py L562–571](https://github.com/xyjoey/Veri-Sure/blob/aab5bed60f04157a4be8581b53f9e913287ba328/eda_agent/asserter.py#L562)的局部pass表示未解析到触发错误行 | 所核路径未见独立的前件可达／cover门或环境强化检测；不能把“无触发”说成“非空性通过”。组合miter本身也不能被笼统指责为依靠环境assume取巧 |
| 最终谁裁决 | v2 §5.1、C.3；[README L44](https://github.com/xyjoey/Veri-Sure/blob/aab5bed60f04157a4be8581b53f9e913287ba328/README.md#L44)把论文功能成功定义为golden TB通过；[rtl_editor.py L554–595](https://github.com/xyjoey/Veri-Sure/blob/aab5bed60f04157a4be8581b53f9e913287ba328/eda_agent/rtl_editor.py#L554)把两helper结果仅交Debugger作提示 | 论文评测的golden gate不是穷尽正确性证明；一般运行也支持无golden的生成TB模式，不能把论文gate外推给所有CLI使用 |

补充实际优先级：golden模式的[Verifier提示L122–137](https://github.com/xyjoey/Veri-Sure/blob/aab5bed60f04157a4be8581b53f9e913287ba328/eda_agent/tb_generator.py#L122)要求保持golden行为、冲突时服从golden；而[Coder L20–27](https://github.com/xyjoey/Veri-Sure/blob/aab5bed60f04157a4be8581b53f9e913287ba328/eda_agent/rtl_generator.py#L20)和[Debugger L105–131](https://github.com/xyjoey/Veri-Sure/blob/aab5bed60f04157a4be8581b53f9e913287ba328/eda_agent/rtl_editor.py#L105)强调合同并同时要求通过仿真。它是prompt与独立测试反馈共同稳住语义，不是已证明所有来源永不冲突的单一形式合同。

作者在v2 C.2／Table7人工审计209份合同，报告12份有错，含3项无规格依据的约束；另有错误合同被golden trace驱动的调试绕过。这里是作者报告，未独立重算；该审计是重要反例，说明其确实研究合同幻觉，但不是每次生成前自动确认假设来源的机制。C.3／Table8还主动限定formal提示的不完整性，不能引用旧abstract把系统写成原规格的完整形式保证。

## 3. 对N15的强重合与剩余问题

与[当前方法卡](feasibility-assumption-method-card.md)逐项比较；当前只有卡及数学控制，不声称已实现生成机制或真实任务结果。

| N15拟议步骤 | Veri-Sure已覆盖／不能再称新 | 仍需证据的窄问题 |
| --- | --- | --- |
| 先合同后RTL，多个角色取同事实 | 已覆盖，并有实际源文件传递 | 仅改JSON字段或冻结同字符串，没有足够增量 |
| 显式写未确定前提 | Architect已经补假设并记说明；研究也审计无依据约束 | 能否使程序推导的`required_environment`始终保持未采纳，直到有依据才进入`adopted_environment`；这是执行语义而非字段命名 |
| 用程序阻止不可行计划 | 现有lint及组合RTL等价不是这一判定 | 受限容量／服务模型能否从真实公开条件可靠建立，给出可映射见证；不完整或过强组件摘要应保留UNKNOWN，不能误判全局不可能 |
| 保持跨阶段语义 | 已有同合同传播、prompt约束、golden最终检查与错误合同审计 | 同信息下，能否自动发现生成prompt、验证assume及汇总分母中的环境收窄，而不靠golden碰巧覆盖反例 |

可保留的具体检验式仍是标准合同规则：已采纳环境`A0`须蕴含组件所需前提`Areq`；不能用`A0∧Areq`替换原问题。该规则、assume-guarantee与非空性检查本身不是新算法。Veri-Sure公开实现没有在上述路径落实这项N15规则，但这只是相对该近邻的覆盖差别，不是原创性证明。

## 4. 最小决定性证据与反驳条件

下一步若用户选择N15，先用同一公开输入、有限能力库和标准后端比较：①Veri-Sure式Architect合同＋现有lint；②人工／确定性模板建立相同假设模型并作标准合同检查；③拟议可信交接。不能把前两者限制为只写自然语言，也不能将本方法独享已知容量／服务事实。

证据至少区分三种：原前提确足够的合法计划；已明确容量及零服务窗口下的可重放不可行见证；元数据或授权不足的UNKNOWN。再故意把“程序推导的建议条件”穿过计划、生成提示、验证及汇总，核是否被错误升级；反向核合法公开条件是否被误拒。容量模型必须算全部存储，公平性不得代替任意长停顿之前的安全保证，模型通过不替代实际RTL兑现能力。

如果已有标准合同模板以同等信息、相近建模工作量即可完成同样交接，应报告同等覆盖；仅增加状态标签不足以立新核心。若拟议流程能减少可核查的前提误采纳／重复录入，且不增加抽象误判，可研究系统增量；手写数学正反例不能证明这种收益，仍需真实公开资产和交接记录。现有N15资格不支持功能率改善、人工工时优势或SCI创新已成立的结论。

本轮仅完成主源／固定源码核对与本文件。未运行作者系统，未检查其209份原始合同，未读本项目候选输出或私有oracle；没有测试工具行为、真实UART波形或新的模型效应。前一轮[VClare／AutoSVA近邻](feasibility-assumption-neighbor-review.md)继续适用，本文不扩成更多文献综述。
