# N31：区分反例与人类澄清的实际近邻核查

日期：2026-10-21。状态：**完成定向方法／源码复核，未成立新的生成机制；不开发通用反例澄清原型。** 本轮取得实际XOR构造、回答过滤及有界停止路径，属于证据进展，不是SCI创新已验收。生成前人类澄清尚未采纳。

## 1. 研究问题与执行边界

[N30](specification-acquisition-review.md)取得SynthTL保存教程：两个不等价候选均记录接受，但最终返回给定DUT的条件式，未发现最终系统失败。本轮只问：若程序先给出能区分候选的行为，再请需求所有者判断，是否构成尚未覆盖的方法步骤？这不是新增实验方案，也不把本段问题实际发给用户。

两位协作者分别审nl2spec与LTLTalk，另一位独立核静态区分例；主审回读关键论文、实现入口、过滤与XOR路径。未运行模型、solver、数学脚本、HDL或作者软件；未读取本项目候选RTL、隐藏TB或参考实现补语义。没有新模型样本、任务定义、评分改动或官方证据晋级。

## 2. nl2spec：人工子翻译编辑已有实际实现

论文固定[arXiv v1，2023-03-08，§3.1–3.2、Algorithm1及§4.2](https://arxiv.org/html/2303.04864v1#S3)。它展示子翻译候选及置信度，让用户编辑后重查模型，以用户批准停止；实例包含括号和时间含义修订。不能将这些步骤登记为空白，也不因需要人工而否认其报告的经验效果。CAV出版版本本轮未能取得，不声称核过版本差异。

作者源码固定[1765c9cd1069ee560ae67ea71e67c8fa134b3d14](https://github.com/realChrisHahn2/nl2spec/tree/1765c9cd1069ee560ae67ea71e67c8fa134b3d14)，2023-08-29，晚于论文并新增GPT-4；不是认证后的论文实验版本。

| 可定位路径 | 实际处理与限制 |
| --- | --- |
| [frontend.py L14–48、85–113](https://github.com/realChrisHahn2/nl2spec/blob/1765c9cd1069ee560ae67ea71e67c8fa134b3d14/src/frontend.py#L85)；[backend.py L4–33](https://github.com/realChrisHahn2/nl2spec/blob/1765c9cd1069ee560ae67ea71e67c8fa134b3d14/src/backend.py#L4) | NL、编辑项和lock进入后端模型分派；ground_truth未作为这次后端请求参数。没有展开models.py，不声称模型adapter内部调用链已核闭合。 |
| [prompting.py L55–102](https://github.com/realChrisHahn2/nl2spec/blob/1765c9cd1069ee560ae67ea71e67c8fa134b3d14/src/prompting.py#L55) | 将人工给定子翻译写入提示，重新生成整体公式；不是程序机械组合并证明全部局部承诺保真。 |
| [ambiguity.py L12–20、54–115](https://github.com/realChrisHahn2/nl2spec/blob/1765c9cd1069ee560ae67ea71e67c8fa134b3d14/src/ambiguity.py#L54) | 子翻译按字符串频次计分；最终对解析产物（失败时保留字符串）取众数；lock置前并标记。未核得语义等价类去重、正确概率校准或最终公式兑现lock的证明。 |

四文件及所读方法未显示自动合成区分轨迹的路径。这只界定本版本覆盖范围；不能从一篇未显示该步骤，就宣布领域存在创新空白。prompting.py还使用LTLfParser尝试解析，失败可留下字符串；本轮不据此认证整个系统的时序语义。

## 3. LTLTalk：区分轨迹、环境约束和回答过滤已有完整机制

主源为[OOPSLA 2020论文，DOI 10.1145/3428269，§3–4、§5及§8](https://malyzajko.github.io/papers/oopsla2020.pdf)。其对象是co-safe LTL、有限机器人演示：正演示产生受假设支持的负例，NL软偏置与大小目标得到有限候选；前两候选的XOR加世界约束生成简短区分行为，用户判断后过滤候选。论文已承认候选截断及轨迹长度界造成的不完备，并报告经验效果；不能把它降格成仅展示公式或纯重试。

作者代码固定[16e99b1506130c0eb59747203480524a2cdf4435](https://github.com/mpi-sws-rse/ltltalk-interactive-synthesis/tree/16e99b1506130c0eb59747203480524a2cdf4435)，2021-08-30；未认证为2020论文运行版本。复核README及下列四源码文件，主审补读实际差异条件包装器。

| 可定位路径 | 实际实现及保证边界 |
| --- | --- |
| [candidatesCreation.py L22、92、125、146–154](https://github.com/mpi-sws-rse/ltltalk-interactive-synthesis/blob/16e99b1506130c0eb59747203480524a2cdf4435/candidatesCreation.py#L92) | 构造演示样本、调用DAG编码、限制候选及尝试次数、规范化和阻塞已返回解；不是穷尽意图空间。 |
| [同文件 L164–204、213–251](https://github.com/mpi-sws-rse/ltltalk-interactive-synthesis/blob/16e99b1506130c0eb59747203480524a2cdf4435/candidatesCreation.py#L164) | 二值回答硬过滤全部旧候选；空集/unknown失败、单候选返回ok。找不到world/path时按候选对象的比较删除一个后递归；未读比较实现，不认证为长度最优规则。 |
| [encoding/run_solver_tests.py L45–97](https://github.com/mpi-sws-rse/ltltalk-interactive-synthesis/blob/16e99b1506130c0eb59747203480524a2cdf4435/encoding/run_solver_tests.py#L45) | L57–60确实构造两候选XOR；按有上下界及步长的range搜索，调用get_finite_witness，unsat继续、unknown返回；成功后再次求值检查区分条件，搜索耗尽返回三个None。未读constants或被导入的solverRuns.py，不给默认数值或全链证明声明。 |
| [SATOfLTLEncoding.py L104、279–298](https://github.com/mpi-sws-rse/ltltalk-interactive-synthesis/blob/16e99b1506130c0eb59747203480524a2cdf4435/encoding/smtEncoding/SATOfLTLEncoding.py#L279) | 实际使用Optimize、要求公式满足和世界约束，加入简单世界的优化；testing分支有timeout。结合包装器只能认证所读有界搜索，不能保证全域最短轨迹。 |
| [flask-routes.py L247](https://github.com/mpi-sws-rse/ltltalk-interactive-synthesis/blob/16e99b1506130c0eb59747203480524a2cdf4435/flask-routes.py#L247) | 用户回答路由实际调用候选更新并处理零/单/多候选，返回后续区分world/path，非仅论文示意。 |

dagSATEncoding.py未展开；不声称已复现候选优化器。有限候选剩一个，只表示该池的停止；长度界内无见证，不是全域等价证书。单次回答硬删除候选的路径也未显示噪声恢复；后续grammar重排名不能自动解释成这一步抗噪。这些限制不抹去已有机制，也不单独构成我们的新算法。

## 4. 无限轨迹的工具强对照与语义边界

[Spot官方语言包含／等价示例](https://spot.lre.epita.fr/ipynb/contains.html)已提供语言等价检查及exclusive_run／exclusive_word，用于返回只属于一个自动机语言的无限字。本轮仅核官方文档示例，访问于2026-10-21，没有固定源码、安装版本或运行复现。

LTLTalk的co-safe有限任务不等于任意RTL安全性质；上述Spot能力也不自动给出NL解析、用户接口或正确意图。不能将LTLf解析、有限world trace和无限LTL字混用，也不声称LTLTalk代码直接执行了下一节例子。但仅把标准语言差异见证接到已有用户候选过滤流程，目前仍未指出新增求解／交接规则；“换到RTL”不足以直接验收方法贡献。

## 5. 同一个真实保存案例的静态区分

沿用[N30的SynthTL保存教程](specification-acquisition-review.md#32-synthtl新增可配对的公开保存翻译案例)，令A表示GRANT高，B表示REQUEST高。明确按从t=0开始的无限二值轨迹解释：

- P = G(A → (B ∧ X¬B))。
- Q = G(A → B) ∧ X¬B。

取所有t≥0均有A=0、B=1。P的每个蕴含均真；Q在t=0要求B在t=1为0，故为假。恒定无限延续是完整区分见证，可以用单状态循环表示；两个观测点足以否定Q，却不足以证明全局P，只能给出P兼容前缀。这里是手算，不是solver或模型结果。

可展示的问题示例是：“如果始终没有GRANT，REQUEST是否允许一直保持为1？”它没有实际发起。只有在同一已确认环境允许该见证、且回答可靠时，回答允许才与Q的禁止冲突；回答禁止则表明P单独不足以表达完整许可集合。若正式问题已限定完整意图必须是P/Q二选一，后者才能据此排除P。否则还可能缺环境假设或其他要求，不能从一个否定回答推出应选择Q。两种回答都不认证余下公式表达全部NL意图。

程序可核形式候选之间的差异，最终语义判断仍需可信需求所有者或另有授权的规格来源。不能用隐藏TB、参考实现或生成模型自我确认替代这项责任；给定DUT的验证也不等于自行获得DUT。

## 6. 裁决、重新进入门与当前进度

**不将通用“合成反例→问用户→筛候选”保留为新增方法核心，也不为它启动原型或模型pilot。** 这项结论依据实际近邻处理与当前未指出额外规则，不是断言所有RTL交互研究无创新，亦非要求必须发明新求解器。

若今后提出不同机制，进入开发前必须依次有：

1. 来自完整公开需求、确实需要选择的真实案例；当前TD数学已明确，不能人为制造歧义证明必要性。
2. 相同时序语义、环境信息、候选及人工查询预算下的强对照，包含已核的候选编辑与语言差异能力。
3. 新增程序规则与可区分输入，说明标准方法不能以同设置完成什么；诚实UNKNOWN本身不算新核心。
4. 可反驳的完整可靠性／成本端点，计入规格准备、人工回答、无候选、unknown与后续生成失败；未测工时不声称省工。
5. 若采用人类澄清、外部任务或N24的合同前端定位，先完成具体范围讨论，再拟定有资源边界的运行；本轮没有采纳这些变化。

本轮只更新该审查与既有导航、唯一清单。原12份生成和12个父构造、16项局部证明、N20运行及其限定范围不变；三版正文保持原字节。新增结构变体的许可仍有效，但不自动采纳人工交互或新campaign。SCI/SCIE方法核心仍未验收，整体目标继续；本轮代码证据进展不被记为“无进展”或整个目标阻塞。

## 7. 独立复核与文件验证

独立只读复核未见Blocker/Major；一项Minor已修正：最终公式可能先解析再取众数，不能笼统称字符串投票。另一位审查者补清开放规格下否定回答的含义，已体现在§5。此审查不认证作者软件的执行效果。

本轮四份文档的210个本地文件链接全部存在，唯一清单N1–N31均为六列且连续，无尾随空白；三版正文SHA与轮前一致。Git仍为develop、e20dfd2ce46c5690767e30cb629fb5c58aff073a；工作树状态计数保持D108、M56、RM5、R1、未跟踪39。没有暂存、提交或远端操作；纯文档核查未运行实现测试。
