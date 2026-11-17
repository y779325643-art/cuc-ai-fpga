# N15 独立审计：现有不变量与未实现的系统交接

日期：2026-10-21。范围：只读[方法卡](feasibility-assumption-method-card.md)、实际 `requirement_envelope.py`、既有近邻审查及 engineering_status 的独占标准基线 artifact；不运行其脚本或新增实验/模型/HDL，不修改实现、正文、旧卡或其他 agent 的文件。只新增本报告。检查时 `develop`、HEAD `e20dfd2ce46c5690767e30cb629fb5c58aff073a`；未操作 staging、commit 或 remote。

**裁决：在当前明确范围内，停止把 N15 作为已具实证增量的独立核心推进。** 容量可行性、充分前提认证、非空性检查和来源/采纳 manifest 可以构成正确的工程流程；N15 尚无已经实现并对照的语义落地、交接可靠性或省工作用。当前标准流程对有限分析与采纳投影提供了实际强基线；系统即使功能等价，仍可能以更低成本形成贡献，不要求独有能力。可信语义落地、实际生成/验证上下文一致性及 body 能力验证均未实现，不能把待补工作本身计作贡献。这不是因使用成熟原语或 LLM 可替代而否定系统论文，也不是对整篇研究创新性的裁决。

## 1. 实际代码：已有来源分组，不存在独立 adoption 机制

| 实际入口 | 已实现事实 | 不能据此宣称 |
| --- | --- | --- |
| [`RequirementFact`](../../../../agent/src/sr2fpga_agent/requirement_envelope.py#L155) | key/value/origin/evidence；origin 在 builder 内被赋为 explicit/default/assumption/unknown | 没有 proposed/accepted 生命周期、授权主体或原文蕴含证明 |
| [builder L269–288](../../../../agent/src/sr2fpga_agent/requirement_envelope.py#L269) | 拒绝 defaults/assumptions/clarifications 的部分同 key 冲突 | 不验证不同 key 的逻辑一致性、条件是否获准、环境是否非空 |
| [builder L334–365](../../../../agent/src/sr2fpga_agent/requirement_envelope.py#L334) | 明文提取优先；caller clarification 记 explicit；caller default/assumption 分别记录标记 | caller 传入 clarification 本身不是外部用户确认的证明；不应让 candidate 自报来源直接进入可信 caller 通道 |
| [`to_prompt_payload`](../../../../agent/src/sr2fpga_agent/requirement_envelope.py#L194) | 向 prompt 分别传 explicit/default/assumption/unknown、原需求文本、歧义项 | 无 adoption 过滤；这里的 assumption 是 caller 已提供的假设，不是 N15 的“建议但未采纳条件”容器 |
| [`requirement_trace_template`](../../../../agent/src/sr2fpga_agent/requirement_envelope.py#L208) | 生成包含 value/origin 的 required facts 和待填 fact-to-HIS 指针 | 模型填对 JSON pointer 不证明源句蕴含所填结构/条件 |
| [`to_dict`](../../../../agent/src/sr2fpga_agent/requirement_envelope.py#L226) | 在 prompt payload 外保留完整 fact/evidence；prompt payload 本身未携带逐 fact evidence | 没有证明后续消费者都使用同一证据与采纳状态 |
| [request builder L384–407](../../../../agent/src/sr2fpga_agent/requirement_envelope.py#L384) | 当前请求入口传 platform/request defaults 及 caller clarification；未传本次 N15 的 proposed assumptions | 不能说 N15 的未采纳条件已实际流经现有生成路径，也不能把通用 assumptions 参数等同已实现 N15 集成 |
| [路由 L451–462](../../../../agent/src/sr2fpga_agent/requirement_envelope.py#L451) | 由已列 critical ambiguities 决定 ready/needs_clarification | 不是容量、服务、可实现性判定；不是整个计划已可行 |
| [`_requirement_id`](../../../../agent/src/sr2fpga_agent/requirement_envelope.py#L665) | 对规范化文本及 explicit/default/assumption 值分组做 hash | 未绑定 N15 plan、adoption manifest、solver domain、证明脚本或实际 body；证据文本不在该 identity 字段中 |

源码的 evidence 来自[正则匹配或派生标记](../../../../agent/src/sr2fpga_agent/requirement_envelope.py#L472)，例如[时钟事实](../../../../agent/src/sr2fpga_agent/requirement_envelope.py#L482)；这有可追踪价值，但不等于通用自然语言形式化认证。现 API 没有承诺接收未采纳 proposal，因此这里不报告一个已复现的现有产品缺陷。N15 若接入它，必须先在信任边界外处理 adoption，不能直接将 pending proposal 放入 `supplied_assumptions` 后声称系统已保护它。

## 2. 端到端不变量逐项审计

| 所需不变量 | 标准 solver＋同 manifest 是否能覆盖 | 当前实际证据/缺口 |
| --- | --- | --- |
| 输入模型与已采纳 A0 可满足；避免 vacuous safety | 能；分别检查环境 SAT 与 bad-state 查询 | 标准基线覆盖这一控制；不是新的队列或契约规则 |
| 只使用 A0，未采纳 Areq 不进入 solver assume | 能；manifest 的确定性投影即可决定 assert 集合 | 新控制可以检验投影，尚无 N15 运行链可比较 |
| A0 足以认证使用 Areq 的局部保证 | 能；`A0∧¬Areq` 不可满足才建立蕴含 | 失败只是不认证该合同；不能跳成不可实现 |
| 精确抽象模型下有限窗口容量安全/违规见证 | 能；标准整数转移或有限状态检查 | 只能限定在模型/窗口；源需求、时序或 body 不随之被证明 |
| 原文真正蕴含某项容量、服务或环境限制 | 只给人工同 manifest 时，根本没有检验这个关系 | 未实现可信 semantic lowering。candidate 自报 origin/locator 无法补上 |
| candidate prompt、verification assume 和统计所用域均为同一获准 A0 | 普通同 manifest 的 renderer/checker 可以实现并核对；并非 solver 单独保证 | 目前没有 N15 端到端 serializer、实际生成上下文、verification harness 与统计链的相等性证据 |
| 计划能力与实际生成 body/实例/参数一致 | 需额外实现验证，不由 plan solver 或 manifest 标签完成 | 当前没有对应 body 验证；`capacity_verified` 类标签只能记录状态，不能自己产生证明 |
| unknown/条件外输入不被改为成功或移出旧分母 | 同 manifest 的报告规则可以实现 | 本轮只产生开发控制，不是候选效果；无可比较的 N15 总体效果或工作量数据 |

所以，“超出本轮控制已经检验的部分”和“可以建立研究增量的部分”不是同一集合。前一种目前只是尚未做的可信落地与集成工作；后一种既可能来自新增保证，也可能来自同保证下更低的真实交接成本。当前两类实证都没有，不能用实现清单代替贡献证据。

## 3. 三个必须保持的逻辑边界

### 3.1 候选自报 origin 不能提升为原文事实

`origin=public`、一个存在的 locator、或“已引用某库”只说明候选作出了声明。可信程序仍需要知道：该引用确实对应目标声明、其量化范围包含当前使用、库前提确实被满足。不得由生成该计划的模型自行给这些命题盖章。

如果来源由人手工形式化，标准基线也应获得相同事实；如果 N15 要声称自动减少这项工作，则必须给出实际已实现的抽取/检查规则、允许原文范围和独立错误控制。当前 N15 卡只有字段与约束，没有该算法或验证证据。不能把这项缺口改名为“语义来源保持”后作为已实现增量。

### 3.2 不蕴含充分 Areq，不代表计划不可能

设 A0 是已采纳环境，Areq 是某个已知足够的前提。`SAT(A0∧¬Areq)` 只说明 A0 中包含该合同未覆盖的环境。若 Areq 比必要条件更强，这些环境可能仍然安全。

当前固定零服务窗口中，C=4、q0=0、A0 为总到达≤4，而 Areq 为总到达≤3；4 次到达不满足 Areq，却没有超容量。因此不能把合同蕴含查询的 SAT 见证当成容量反例。认证失败、精确安全模型中的真实 bad witness、以及所有允许架构的不可实现性，是不同结论。

### 3.3 plan capacity 与实际 body 分开

在宣称 C=4、q′=q+a、d=0 的模型里找到第 5 次到达见证，只证明该精确抽象计划违反其安全承诺。它不证明真实 UART 的全部存储都被正确抽象、到达/退休定义符合需求、候选用了相同容量，或某模块 body 确实满足该能力。

后续若 body 自报“FIFO4/无额外 holding”，仍需实际验证；反过来，加 holding register 改变总能力也不能沿用旧模型证书。当前卡把层次分开是正确的设计要求，但尚无端到端实现来兑现它。

## 4. 标准基线的实际结果与本审计核对范围

engineering_status 的独占目录为 [standard-baseline artifact](../../../../artifacts/responsibility-capacity-standard-baseline-20261021-01/results.md)。本审计只读了 `results.json`/`results.md`、fixtures、origin/adoption manifest、runner 中采纳投影/metadata gate 的代码，以及 c3/c6 的实际 SMT 脚本、c6/c7 的原始 log 与 c6 的 replay；没有执行代码或重跑 solver。完整逐记录 provenance 由该 artifact 保留。

固定模型为 C=4、H=6、每事件到达 a∈{0,1}、无退休 d=0、q′=q+a；全部 origin/adoption 标注由开发者显式提供。实际 7/7 个 Z3 过程完成；无 retry、timeout 或 tool-unknown；另两项 metadata unknown 没有 solver 过程。artifact 记录工具为 Z3 4.15.5，过程总 wall time 为 0.490029900 秒；未测人工准备/审阅成本，不作 N15 速度比较。

| 控制 | 已采纳环境/起点 | 实际查询 | 有限范围内结论 |
| --- | --- | --- | --- |
| c1 | q0=0，无到达上界 | ENV SAT，OVERFLOW SAT | 有容量违规见证 |
| c2 | q0=0，总到达≤4 已采纳 | ENV SAT，OVERFLOW UNSAT | 六事件窗口内安全 |
| c3 | q0=0，≤4 仅是未采纳 proposal | ENV SAT，OVERFLOW SAT | proposal 未改变输入域；与 c1 一样可违规 |
| c4 | q0=2，总到达≤4 已采纳 | ENV SAT，OVERFLOW SAT | 未扣除已有占用会违规 |
| c5 | q0=2，总到达≤2 已采纳 | ENV SAT，OVERFLOW UNSAT | 六事件窗口内安全 |
| c6 | q0=0，A0=总到达≤4；保守 Areq=≤3 | ENV SAT，OVERFLOW UNSAT；A0∧¬Areq SAT | 不蕴含该充分条件，仍未出现容量违规 |
| c7 | 总到达≤0 且≥1 均已采纳 | ENV UNSAT，OVERFLOW UNSAT | 环境矛盾，不给安全 credit |
| m1/m2 | capacity 未知，或仅 model 自报 C=4 | 无 solver；均 unknown | 不将标签升级为可信能力 |

其中两处可直接核源码/原始输出：c3 的 [script](../../../../artifacts/responsibility-capacity-standard-baseline-20261021-01/runs/c3/script.smt2)没有 `arrivals_total≤4` 断言；c6 的 [script](../../../../artifacts/responsibility-capacity-standard-baseline-20261021-01/runs/c6/script.smt2)只在独立诊断 push/pop 中检查 `arrivals_total>3`。c6 的 [log](../../../../artifacts/responsibility-capacity-standard-baseline-20261021-01/runs/c6/z3.log)及 [replay](../../../../artifacts/responsibility-capacity-standard-baseline-20261021-01/runs/c6/witness-replay.json)给出 `a=111100`、`q=0123444`，明确不是 overflow。c7 的 [原 log](../../../../artifacts/responsibility-capacity-standard-baseline-20261021-01/runs/c7/z3.log)记录环境/overflow 均 UNSAT，结果未将其计为 safe。

[manifest](../../../../artifacts/responsibility-capacity-standard-baseline-20261021-01/origin-adoption-manifest.json)带有与卡对应的 predicate/origin/locator/adoption/derivation_dependencies；m2 还明确保存 model 自称 public/accepted 的嵌套标签，同时由可信 fixture 将其列为 unverified/unadopted。它测试“可信状态覆盖模型自报”，不是自动识别真实原文来源。runner 的普通 `adopted_bounds` 投影及 metadata gate 就能完成本批分类；没有 N15 额外路径参与。

实际计数为 3 overflow witness、3 safe-in-window、1 inconsistent、2 metadata unknown。它们是 7 个标准有限数学控制加 2 个 metadata 控制，不是 9 个候选模型，不是 UART 真实任务，不是 Pacti 复现；有限窗口 UNSAT 不得提升为无限输入或活性证明。证据验证了标准路径的本批能力，未测得系统工作量优势，也不证明任何系统集成都无价值。

## 5. 近邻与“协议增量”的正确尺度

沿用既有深审，不新增文献检索：方法卡已核 Pacti 的实际 compose/refines/quotient；[RTL-Obliger 深审](architecture-conformance-gap-review.md#3-深读二rtl-obliger-已把缺少义务做成方法)已记录规范证据→义务的正式方法；[VeriRefine 深审](neighbor-deep-review-verirefine-eqy.md#2-verirefine必须分开的三层保证)明确区分出处锚定、表示语义与实现忠实性。不得将它们降为只有字符串标签。

这些近邻没有自动证明 N15 零价值；但它们使“附来源、求前提、生成前冻结、保留 unknown”这样的宽叙述不足以成为独立贡献。当前基线有相同 A0、能力、事件规则及来源/采纳 manifest 时，N15 必须指出额外保证或实际人工工作减少发生在哪一步。

目前本批能表达的容量、环境非空性与 metadata 采纳投影不变量，已有标准分析加同 manifest 的实际支持；这没有验证真实 prompt/verification/统计链。N15 尚无实现链或工作量对照。功能等价的集成仍可能省工，但不能只因它们尚未写入仓库，就当作已获得的系统创新。

## 6. 剩余最小 hypothesis 与当前 STOP

唯一可以精确定义的剩余假设是：**以一份获准事实/能力记录为源，N15 在 candidate 输入、验证假设和结果域三处保持逻辑相同的 A0，并比同 manifest 的标准 renderer/checker 少做可记录的人工作业。** 这不要求新 solver，不要求 LLM 不可替代；要求真实集成与工作量证据。

但在当前 UART/ready-valid 范围，该假设尚无实现、没有实际三个消费者输出，也没有实际人工成本记录。现有控制仅验证 manifest 投影/有限模型计算；同功能 renderer 是应面对的强基线，不是省工贡献在逻辑上不可能的证明。由于当前缺少可比较的 N15 链与成本证据，该假设仍只是工程验收目标，不能单靠改名保留成已经成立的独立研究核心。

**当前 STOP：** 不因 N15 名称新增 DSL、模型调用或主实验；保留有限模型资格与需求歧义诊断。若以后普通实现确有使用需求，可以按工程任务补 adoption/proof-context 一致性，但不能在未出现可比较增量时宣传成新方法。这里不以假想未来协议或新任务挽救候选，也不据此裁定论文总体是否有创新。

没有采纳新 A0、没有把 legacy UART 改成正式无条件语义，也没有把排除条件外输入算成功。计划证据、body 证据与候选效果继续分列；本报告不改变任何既有状态或分母。
