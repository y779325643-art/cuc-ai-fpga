# 时序方向的公开任务准备核查

日期：2026-10-21。接续N20零模型编译结果，只读核对下一步所需材料，不采纳新的任务范围、外部语义或评分。当前分支`develop`、HEAD `e20dfd2ce46c5690767e30cb629fb5c58aff073a`，已有工作树修改保留。范围问题仍待用户答复；本轮的准备地图不等于允许时序变体进入开发或模型实验。

更新：下文§1–6保留N21的有限准备范围；N26在§7补核了归档caller需求、去重分母及当前消息构造来源。已找到原始需求存档，但未确认完整历史模型消息；N24待选只约束其不同贡献路线，不阻断原目标内独立的只读证据核查。

**结论：核到一项逐周期控制明示的既有公开TD任务，以及两项仍缺关键公开语义的CRC/累加器资产；没有找到一项可直接进入新核心开发的“真实开放结构取舍＋明确新处理”正例。** 因此不能把增加时序复杂度当成N18/N19创新问题的解法，也不能声称仓库中所有任务都缺时序定义。

## 1. 本轮已完成什么

- 工程审查者读取公开catalog、generation guidance、requirement envelope及README，返回候选的已有事实和缺失事实；随后与主审分别复核旧TD公开prompt。
- 研究审查者复核HINT/Stepwise相关完整方法和附录，并重查作者实现可得性；主审回到原文核关键方法、验收边界及liveness表述。本轮未取得可新增审计的作者实现，不造commit SHA。
- 独立决策审查者检查N18/N20与v0.3贡献/限制，核“时序是否产生新机制”及同信息强基线，没有保留新的方法核心。
- 未运行被测模型、HDL、SAT/SMT或作者框架；未修改原型、可信评价、任务定义、旧运行、官方研究状态或正文。

这是有界准备核查，不是全仓库公开请求穷举。真实caller的`requirement_text`可能比家族guidance更具体；未拿到对应冻结请求时，不能由模板缺字段推出全部实际任务均不完整。

## 2. 三项实际材料的不同结论

| 材料 | 已明确的公开事实 | 尚未成立的结构选择／资格 | 当前判断 |
| --- | --- | --- | --- |
| 旧signed8/Q4 TD单槽任务 | [实际公开prompt L27](../../../../artifacts/codex-native-td-pilot-20261021-01/prompts/global.txt:27)固定三个模块、实例和R→update连接，top负责输出槽，算术核无状态；[L49](../../../../artifacts/codex-native-td-pilot-20261021-01/prompts/global.txt:49)至L57明确ready、接受沿、结果捕获、bubble、stall保持、同时消费替换、禁旁路和异步复位 | 原任务已固定时间分配与状态归属，不能把输入寄存或额外流水当现有自由度。若另开算术分解变体，仍须兑现同一外部周期规则；没有因此得到新的时序协调机制 | 是“时序语义明确”的正例，是“已有真实开放时序取舍”的非正例；普通单槽寄存器/FSM构造为强基线 |
| CRC stream checker家族 | [guidance L423](../../../../agent/src/sr2fpga_agent/prompts.py:423)至L435固定三模块、端口及CRC/完成/输出状态归属；[catalog L4971](../../../../contracts/task-catalog/sr2fpga-task-catalog-v0.2.json:4971)要求CRC更新和帧边界处理 | 已查材料未给具体多项式/初值、帧事件优先级、expected_crc采样点及输出周期。尚不能判断两种内部方案是否都满足同一完整要求。不能从reference/TB补成候选公共事实 | UNKNOWN；尚无对应完整冻结请求，不采纳变体 |
| 流式累加器家族 | [guidance L602](../../../../agent/src/sr2fpga_agent/prompts.py:602)至L613固定buffer→accumulator、端口方向与sample_valid路径；[catalog L1404](../../../../contracts/task-catalog/sr2fpga-task-catalog-v0.2.json:1404)要求堵塞稳定、无丢重及累加正确 | 已查材料未给完整数值编码、复位值、接受事件至sum/sample_valid的周期关系。不能自行允许搬移缓冲、改等待周期或状态ownership | UNKNOWN；需要对应实际公开请求，不以义务标签替代逐周期语义 |

上述TD只使用此前已经生成前冻结的公开prompt，未读其responses或harness来推导要求。[首轮TD报告](native-codex-development-pilot.md)中的2份模型输出仍是旧实验；本次阅读不新增样本、不重跑、不改变其结论，也不与后续12份组合任务合并分母。

CRC/累加器的catalog虽标`oracle_readiness: ready`，这不证明完整语义已经在本轮允许的候选可见输入中。反过来，本轮未见字段也不证明现有oracle错误。[envelope L194](../../../../agent/src/sr2fpga_agent/requirement_envelope.py:194)只是保留实际caller的explicit/default/assumption/unknown分类，不能自动补全这些数学或时序选择。

## 3. 近邻复核对时序路线的约束

[HINT v2](https://arxiv.org/html/2608.07625v2#S4.SS1)在架构生成前冻结接口、事务与时序，接受可执行架构后再lower为RTL并检查数据与边界时序；已有明确状态/调度承诺。不能将它描述为只检查端口标签，或认为转时序就超出其方法对象。其论文匿名入口本轮仍未取得可审计内容，完整profile/实现与SHA不可核；这是可得性限制，不是不存在相应能力。原详细记录见[HINT深审](neighbor-deep-review-cppl-hint.md)与[协议交接审查](protocol-handoff-neighbor-review.md)。

[Stepwise v2 §4](https://arxiv.org/pdf/2606.19387v2#page=5)已有并行、piping和双向组合规则，附录Euclid1有相互依赖过程。它对“先分过程再实现”的覆盖是实质性的；但[§3](https://arxiv.org/html/2606.19387v2#S3)明确把progress要求放在prompt，未纳入spec statements的liveness属性。不能将其形式保证扩大为任意ready-valid活性。这个范围差别本身也不构成我们的新核心：当前没有新的活性机制、合法任务或收益证据。未定位可归属作者的实现，不以第三方仓库替代。完整既有深审见[FormalRTL/Stepwise记录](neighbor-deep-review-formalrtl-refinement.md)。

两项均允许某种反馈/回退；本篇首次无修复只是评价边界，不能单靠禁用反馈主张新方法。标准elastic shell、接口adapter及完整FSM lowering也仍需保留；[已有CIRCT/Carloni核查](protocol-handoff-neighbor-review.md#3-传统latency-insensitive能力前提不能漏)不因本轮转向讨论而失效。

## 4. 哪些缺口不能靠加模型样本补上

1. 局部备选组合已有近邻；扩大样本不会产生新的选择规则。
2. 当完整可执行行为和允许的固定构造都已给定，模型规划不是取得一个合法结构的必要步骤。时序若也完全给成转移函数，普通FSM lowering仍是强基线；本轮没有实现该FSM编译器，不冒称已经跑通。
3. 当前尚未确定哪项真实需求迫使系统优选另一分解。把“能选”作为任务本身，会令固定返回一个合法解的基线已经完成目标。
4. 原文裁决、事件/时序合同、参考行为和角色响应仍由作者提供。省工必须核这些输入的实际编写/适配工作，不能用模型成功率替代。

完整数学不是只能供我们使用的秘密优势。若改成候选不可见但程序据之筛选，必须重新核协议中的评价信息使用；不能借隐藏normal、不给编译基线同信息来制造必要性。本轮没有改变信息边界。

## 5. 真正进入开发之前的验收门

这不是新的执行授权，也不要求把所有事项都手写成完整控制器。若用户保留时序方向，下一份方法设计必须先同时给出：

- 已有明确需求中的接受、采样、保持、复位与外部时序，以及可信原生接口能力；新增假设另列，不能默认为原需求。
- 两个由同一原需求允许、且有实际动机的内部结构，一个可定位的不兼容组合；仅把模块名或连线顺序改写不算。
- 新程序具体多推导或少要求作者填写什么；普通参数化构造、同字段wrapper/adapter及必要的完整IR lowering得到何结果。
- 全输入与全尝试的主指标、人工输入/新任务适配成本、未知与失败处理。完整方案采样可用共享字典/索引压缩，不能被故意弱化。

缺任一项先停在准备层，不开发、不通过模型失败寻找动机。这是对最低补工可行性的门控，而不是拒绝复用成熟工具。当前通过上述全部门槛的任务数为0；它只涵盖本轮已查材料，不是全领域无gap断言。

## 6. 阅读边界与源文件身份

工程审查者一次对混合`stream.py`作关键词检索时，意外返回32–100、124–223、251–407、515–656区间内的零散TB/参考RTL匹配行，随即停止该文件读取；未使用这些内容补需求。本轮没有新被测模型上下文，旧候选均在此次读取前封存。因此不改旧样本、不声称本轮完全未见测试代码；未来被测生成仍需全新且只含获准公开输入的上下文。主审本轮仅据上述guidance/catalog/envelope及公开TD prompt定位事实。

以下为本轮只读核对时的当前字节SHA，不是把历史运行重新冻结，也不是新的数据/交换合同：

| 公开源 | SHA256 |
| --- | --- |
| `agent/src/sr2fpga_agent/prompts.py` | `892d2a8341dee6e15274f8d1a7374dd63447e101bbbee11a3a6f3e998b5a926c` |
| `contracts/task-catalog/sr2fpga-task-catalog-v0.2.json` | `e42dd9aaf08ce20f17956dddf81acb83771cc476c2c0021ec7029ae7a6cef172` |
| `agent/src/sr2fpga_agent/requirement_envelope.py` | `5c0fc8b20f6c3a47e6fad86e50a6ff2a5a0fc909e797940c95da5cac600d92a4` |
| 旧TD `prompts/global.txt` | `05f8783799f165488bfa09f68978f0b1fafc7dca7cf72cf6f3f82fe2615ba0dd` |

报告完成后，独立审查者只读复核本文、N21清单、§19及上述公共来源：四份SHA一致，未发现指定语义/授权范围内需修改的实质问题；特别核了caller范围、旧TD周期反例、0项的有限分母、liveness与源码可得性及误读披露。其未运行实验、修改文件或读取`stream.py`。这项审查不增加候选或方法效果证据。

目前可交付的是范围与验收负担明确的准备结论，不能据此称新核心或SCI充分性成立。[N20结论](direct-math-compiler-baseline-review.md)、旧运行及v0.3正文保持原状；整体论文目标仍未完成。

## 7. N26：归档caller需求与实际模型输入分开核查

### 7.1 为什么继续查原件

N24讨论卡和N25期刊核查已经完成准备，但用户尚未选择不同贡献定位。主审与独立审查者复核后确认：N21明示尚未取得对应caller原件，只查了有限guidance；不能把这一未完成的证据工作或N24偏好待选，扩大为整个项目无授权可继续的阻塞。于是开展独立的需求原件清点，不采纳时序变体，也不进入N24的S1成本研究链。

工程协作者先读两份owning README、CRC/累加器各一份身份metadata和requirement，共6文件、正文少于600行；再限定三个精确task_type扩展去重。主审另核双流汇合三个代表、当前消息构造与记录调用路径，并独立重算全部计数/哈希。只读需求原文、身份白名单和当前公开构造代码；未读候选RTL、TB、reference、评分或eval/trajectory来补语义，未运行生成器、模型、HDL或solver。

### 7.2 分母与7份原字节版本

`datasets/sr2fpga_rtl_v1`当前有241个`sample_*`目录，其中193份一层metadata可解析并有可提取task_type。按这193份记录中的精确三家族名筛出80目录，80份requirement均存在：

| 精确task_type | 目录／requirement数 | 原字节SHA去重数 | 重复分组 |
| --- | --- | --- | --- |
| crc_stream_checker | 5／5 | 2 | 简短1、contract4 |
| composed_stream_accumulator | 23／23 | 2 | natural19、simple4 |
| composed_dual_stream_join | 52／52 | 3 | natural A18、simple22、natural B12 |
| 合计 | 80／80 | 7 | 是存档分组，不是80任务或新模型样本 |

剩余48目录没有metadata，未自动归入任何家族。主审只对其中公开需求另作字节/字面检索：47份requirement、42个SHA，另一`sample_output_repair`没有requirement；全文对`crc|accumulat\w*|join`字面模式均无匹配。它不证明这些目录在语义上一定不相关，也不认证其任务或来源。以下80/7只覆盖有身份记录的指定家族，不冒充241目录全体任务资格。

七份需求正文都只有一行，工程审查者读全部unique版本；主审回核代表文本与SHA如下。相同文本的多协议/多目录仍保留原身份，不合并为一个实验结果。

| 代表公开需求 | 份数 | SHA256 | 原文已给／未给 |
| --- | ---: | --- | --- |
| [CRC简短版](../../../../datasets/sr2fpga_rtl_v1/sample_t0_t4_deterministic_smoke_crc_stream_checker_8_000012/requirement.txt:1) | 1 | `010d0e91d42cbc32e3b203861e3b68384f1155a9f965af8ee924bf601f829c57` | 只给8位流式CRC；未给poly/init、帧优先级、采样或周期。对应metadata来源为deterministic，不当真实LLM提示 |
| [CRC contract版](../../../../datasets/sr2fpga_rtl_v1/sample_official_eval_gap_closure_crc_stream_checker_8_000014/requirement.txt:1) | 4 | `d17a5e0a96b7e9a62523a7cb6c011748a2e743090613ff49e69eb6667c70eacb` | 加通用多文件/manifest/TB/QoR交付要求，仍未给上述CRC行为细节 |
| [累加器natural](../../../../datasets/sr2fpga_rtl_v1/sample_baseline_b_smoke_t2_stream_accumulator_8_000002/requirement.txt:1) | 19 | `42b0f8a4d9918a7af41d15418abf6b1bc184cf73be6662a053b27e17211818f1` | 固定skid→accumulator及六条接口连接；未给符号/溢出、复位值、采样优先级或精确周期 |
| [累加器simple](../../../../datasets/sr2fpga_rtl_v1/sample_pilot_his_v12_repair_20260625_t2_stream_accumulator_8_000002/requirement.txt:1) | 4 | `b6b033484c5710020319380be72c4ab1dea799bd8e4ce789b9686ae9389b1d5c` | 给8位valid-ready流和累加；未补齐完整数值/事件语义 |
| [Join natural A](../../../../datasets/sr2fpga_rtl_v1/sample_baseline_b_t3_t4_smoke_t4_dual_stream_join_8_000002/requirement.txt:1) | 18 | `52514a39c01d76963f5f8ac78205a3e23b810db908c148bf7292755dd776d79f` | 固定双skid→join→accumulator→stage，含accumulator.sample_ready→join.out_ready；未明确join算式、溢出或精确延迟 |
| [Join simple](../../../../datasets/sr2fpga_rtl_v1/sample_his_v12_smoke_t4_dual_stream_join_8_000001/requirement.txt:1) | 22 | `75aa355473af402df13f284e2effce16fc98cba7c73a176350610179e1fe70bd` | 给双流汇合、累加和单输出流；未补齐完整时序/数值定义 |
| [Join natural B](../../../../datasets/sr2fpga_rtl_v1/sample_official_eval_gap_closure_detfix_t4_dual_stream_join_8_000004/requirement.txt:1) | 12 | `bb29b684eb4cb9c4117357ed62c64f8f03a96c5806eccfc9a5d70ce436e64a8e` | 改为stage.in_ready→join.out_ready，并增加top.out_ready→stage.out_ready；仍未补齐完整逐周期规则 |

natural A/B是具体接线文字差异，不只措辞改写；没有根据RTL决定哪个正确，也不预断它们在合法alias/传递路径解释下必定语义不等价。不能仅用家族ID互换两份需求，或把多个协议下同一需求的副本当成额外任务多样性。元数据width均8，schema标签包含v1.1/v1.2/v1.2-topdown；source标签不认证provider或实际网络请求。

### 7.3 为什么仍不能把requirement.txt当完整历史prompt

- [datasets README](../../../../datasets/README.md:1)将历史release标为内部、待审且配置fingerprint不可恢复，未授予统一benchmark或新campaign身份。
- 当前[recorder.py:41](../../../../agent/src/sr2fpga_agent/recorder.py:41)的start_sample只持久化传入requirement及平台/metadata；[agent.py:310](../../../../agent/src/sr2fpga_agent/agent.py:310)的run_one将requirement和ProjectRequest分别作为参数接收，[L389](../../../../agent/src/sr2fpga_agent/agent.py:389)先记录，[L416](../../../../agent/src/sr2fpga_agent/agent.py:416)再将request交给生成器。此路径不证明落盘文本逐字等于最终messages。
- 当前[prompts.py:64](../../../../agent/src/sr2fpga_agent/prompts.py:64)的REQ2HIS构造还组合平台、有效需求、route/envelope及task guidance；[L792](../../../../agent/src/sr2fpga_agent/prompts.py:792)的行为阶段含已检查HIS和骨架；[L909](../../../../agent/src/sr2fpga_agent/prompts.py:909)的direct构造亦有平台、公开投影及结构说明。已静态回核三个generation入口确实将这些messages交给client，未调用其生成方法或展开动态骨架。
- 当前构造函数不是历史版本证明，不能用今天代码重建“当年实际发送的字节”。主审只查80目录中eval/generated_project以外的文件名，没有找到名称含request/prompt/message/input的独立文件；没读eval/trajectory，不据此宣称所有位置均不可能藏有发送记录。

当前源码身份是只读审查时的字节，并非新运行冻结：

| 源 | SHA256 |
| --- | --- |
| recorder.py | `65d62b3fe6df75460eccc9557dcaf141d3de71dc6f505157abcc331444051da0` |
| agent.py | `af571d72de3b811dfdae612816e5c97f7cc64aeaf936d707986029f8229c7ac3` |
| prompts.py | `892d2a8341dee6e15274f8d1a7374dd63447e101bbbee11a3a6f3e998b5a926c` |
| datasets README | `aa9af3e331e7de09d2f86e23c9c302099e80710d6affc72be8006dc7f079a15d` |

### 7.4 对下一步的实际影响

原件存在已从未知改为可核事实；指定家族的原始requirement版本与重复数也已明确。但完整历史候选输入仍UNKNOWN，外部行为/合法结构集合尚未据此冻结。不能将raw文本缺项直接写成历史模型的输入缺陷、模型责任错误或我们已解决的新gap；也不能拿当前guidance回填旧合同，或从TB/reference猜期望。

后续若继续这些家族，应先追溯可核公共输入包/版本及明确语义来源；若只能新编公开需求，必须明确是新任务版本、先裁定时序范围和全体比较方信息，再准备有界计划。此处未实施这些变更。当前没有新核心或SCI充分性结论，也未恢复N18/N19、N15或R1b；N24偏好选择与整个研究的独立证据工作保持区分。

独立收尾审查重算241＝193＋48、三家族80/7及另47/42，核七份代表文本、所列SHA、四份当前源码身份与三个消息入口，未发现限定范围的实质问题。其未读eval/候选RTL/TB、未实验或改文件；不认证任务资格、创新或SCI充分性。主审文档检查通过，三版初稿哈希和原有Git状态计数保持本轮开始值。

## 8. N27：完整历史输入的有界追溯收口

2026-10-21，只读续查N26的七个raw需求版本。范围限于artifacts/reports文件名索引、历史来源索引、两份Phase-D报告的路径引用及公开字段schema；不打开其所指eval、trajectory、labels、候选RTL、TB或reference，不用当前模板重建旧消息。独立工程审查者读取四份文件的允许部分，主审回核以下三处及目录索引。

| 来源 | 实际能支持的事实 | 不能支持的结论 |
| --- | --- | --- |
| `artifacts/agent/`文件索引 | 目录存在，本次索引0文件；允许范围的文件名搜索未定位对应初始messages/request快照 | 其他位置或历史版本从未保存过消息 |
| [再生来源索引](../../../reorganization/regenerated-evidence-sources.json:5) | 五组早期run的旧路径、candidate根及run根 | 七个需求SHA与完整消息、模板/代码SHA的绑定 |
| [Phase-D报告路径引用](../../../evidence/phase-reports/2026-07-17-sr2fpga-phase-d-pilot-report.md:142) | 引用了audit及requirement等工件；本轮只据引用识别角色，没有打开评价记录 | 由需求哈希相同推出完整messages相同，或将报告汇总当原始发送记录 |
| [episode-pack公开字段](../../../../contracts/episode-pack/episode-pack-v1.schema.json:29) | 规定public_text、facts、profile及public_projection哈希 | 自动认证完整system/user消息、生成时代码和实际发送字节 |

**收口结论：CRC两版、累加器两版、Join三版的完整历史初始输入与生成时代码绑定均仍为UNKNOWN。** 缺少可核链条：`raw需求SHA → 完整初始消息字节/哈希 → 模板与代码revision → 运行身份`。不能拼接不同run材料、用source标签替代provider记录或从隐藏评价补语义。

停止扩查旧日志。未定位完整历史输入是本次可恢复性的限制，不证明原件不存在，也不是模型错误或方法gap的证据。未来若新编这些家族的公开任务，应单独定义版本、明确数值/周期语义与同信息边界，先解决N21范围问题；此处没有采纳、实现或运行新任务。三版初稿、现行研究定义和历史结果不变。另一项仅使用既有TD完整公开prompt的[接口可实现性静态审查](interface-realizability-candidate-review.md)独立记录，不拿N27未知材料作其输入。
