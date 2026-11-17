# N33：比较起点、语义准备与停止条件审计

日期：2026-10-21。状态：**N19/N20当前输入公平；修正一处过强的恢复门，维持停止扩大投入。** N32取得另外三家族的实际原件，属于进展。本轮核当前方法卡、真实编译入口和结果，再定向回读CPPL相关方法与固定源码；不恢复旧候选，不改变贡献定位或运行新实验。

## 1. 实际比较没有一方从裸NL开始

[N19方法卡](contract-option-protocol-method-card.md:13)要求调用方提供并冻结可信完整normal函数，规划模型另提局部合同备选；不是已实现的NL→可信目标前端。[公平审计](local-option-protocol-fairness-review.md:93)讨论NL起点是条件分支，不能读成已执行路线。

主审核两份[选择器输入](../../../../artifacts/responsibility-local-semantic-selector-prototype-20261021-01/trusted-specs.json)与[编译器输入](../../../../artifacts/responsibility-direct-math-compiler-baseline-20261021-01/trusted-specs.json)当前字节相同，SHA均为a317f8aba45396101ec0db85ea2a2ffedaab7ee028ad7cdea081e737465dfe30。[compiler.py L109–137](../../../../artifacts/responsibility-direct-math-compiler-baseline-20261021-01/compiler.py:109)消费normal AST、核范围并逐输出发helper，没有NL解释或候选池入口。

重新读取[results.json](../../../../artifacts/responsibility-direct-math-compiler-baseline-20261021-01/results.json)仍为1个Python、4个HDL过程，全部completed/exit0，零重试、零模型/solver/API。编译器及结果文件SHA与[N20记录](direct-math-compiler-baseline-review.md)一致；本轮没有重跑。原FIR全域与TD有限位置的覆盖边界不变，不据记录状态单独认证全部功能或原角色合同。

## 2. 三个不同的比较问题

| 问题／共同起点 | 公平终点与强替代 | 当前可支持范围 |
| --- | --- | --- |
| 已有可信完整F，允许自由分解/合法重算 | 同normal-only功能终点；直接编译与局部备选→协调→一次body | N19/N20实际属于此层。零模型已取得限定资格，不能再称模型池是取得这些资格的必要条件；尚无配对协议结果或完整成本收益。 |
| 同一公开需求，尚未有可信行为表示 | 双方承担各自的建模、确认、失败及RTL生成；所有语义事实须同等可见 | 是另一项完整流程比较，目前未实现/执行。不能给编译器免费补F，也不能给候选免费补F而让对手自行猜；计成本也不能掩盖额外语义援助。 |
| 已有原字节RTL，需独立审核明确角色承诺 | 同合同/同允许实现集合的标准miter/cutpoint及前端交付 | 是N24待选的不同问题。重新构造任意正常实现不自动完成已有RTL审计；本轮不采纳该定位。 |

若双方共享同一份可信F，未知的共同准备成本不能被记为候选独有收益。仅对相同单位、可相加的成本分量可写“总成本=准备+后续执行”；共同项在增量比较中相消，完整交付仍需记账。人工主动分钟、wall-clock、token、费用及一次性工具适配分别记录，未测部分保留UNKNOWN，不混加单位或把字段数当工时。

## 3. CPPL的真实起点介于两者之间

定向回读[CPPL v1，2026-05-18，§III-A–D、Fig.5](https://arxiv.org/html/2605.17892v1#S3)：调用方明确给接口、宽度及格式化实例，行为意图仍在自然语言docstring中；模型补剩余运算IR，编译器检查并lower。它既不是裸NL自动得到全部层次，也不是已经收到完整可信行为AST。不能用N20消除其语义获取阶段，也不能因没有任意NL蕴含证明而否定论文报告的经验效果。

固定同期源码838aab3d81237baefdd4807ce0d09a8146192efc（2026-05-17），未认证为论文运行快照。协作者只回读三源码，主审独立核论文输入及实际生成入口：

| 源码 | 已核职责 |
| --- | --- |
| [frontend/prompt.py L227–275](https://github.com/SawyDust1228/CPPL/blob/838aab3d81237baefdd4807ce0d09a8146192efc/cppl/frontend/prompt.py#L227) | 将端口、docstring和child输出交给模型，要求剩余运算／output。 |
| [frontend/compiler.py L174–229](https://github.com/SawyDust1228/CPPL/blob/838aab3d81237baefdd4807ce0d09a8146192efc/cppl/frontend/compiler.py#L174) | 实际gen、抽JSON、预置实例/deferred核对、parse/validate/infer，以及失败反馈重发；完整body尚未在调用前给定。 |
| [codegen/circt.py L273–349、516–560](https://github.com/SawyDust1228/CPPL/blob/838aab3d81237baefdd4807ce0d09a8146192efc/cppl/codegen/circt.py#L516) | 运算映射、CIRCT passes与Verilog导出；确定合法行为表示之后是编译工作。 |

本轮未重审DSL捕获、完整validator、实验外层驱动或原始轨迹；不认证接口/层次由人手写还是另一模型准备，也不把其允许重发的结果当无反馈首次响应。没有适配/运行CPPL或证明其直接支持本地全部floor/sat/wrap；本地正常算术资格不能称胜过它。更广范围及后续版本仍见[既有深审](neighbor-deep-review-cppl-hint.md)。

## 4. 需要修正的门与维持的决定

N20末段曾要求恢复研究必须先有“编译器不能直接消除”的结构取舍。对要求新增结构决策的当前偏好，它指出一个可能方向；若读成所有系统贡献的必要条件，就比同报告及公平审计允许的真实成本／可靠性标准更强。**标准方法能给出相同答案，不自动否定一个不同交接流程的可测价值。**

恢复应先有真实需求下尚未满足的具体工作或成本／可靠性瓶颈、明确的新处理及公平可否定的主指标；结构取舍只是可能来源之一。不是把未知成本改称瓶颈，也不要求先证明通用编译理论上不能完成。本轮据此只修正文档门，不改变用户新增方法机制的偏好。

**N18/N19仍停止扩大实现／模型pilot。** 当前卡和编译器实际共享完整F，近邻已有局部备选组合等主步骤；没有新的完整链、真实池覆盖或配对总成本证据。未实施NL前端不能反过来替既有卡制造优势。要走另一条从需求起步的路径，须先说明新增处理、各方同等语义事实和独立终评；这不是本轮采纳或执行。

本轮修正比较方法的过强措辞，而非确认新核心。三版正文、任务、评分、原始分母及执行工件不改；不自动转向N24、添加人类澄清或新任务。SCI/SCIE目标继续。

## 5. 复核与文件验证

独立工程审查核两份可信输入、实际编译入口、结果SHA与恢复门，未见Blocker/Major；一项Minor行号已改为文件实际结尾L137。CPPL由另一位协作者定向回读主源及三源码，主审独立核其输入和gen入口；没有复现作者结果。

主审检查本轮五文档的240个本地文件链接均可达，4个行号后缀均在目标文件内，无尾随空白；唯一清单N1–N33连续且均六列。三版正文SHA一致；分支仍develop、HEAD e20dfd2ce46c5690767e30cb629fb5c58aff073a，状态计数仍D108、M56、RM5、R1、未跟踪39。没有暂存、提交、远端操作或实现测试；本轮只是只读方法／原件审查和讨论文档修正。
