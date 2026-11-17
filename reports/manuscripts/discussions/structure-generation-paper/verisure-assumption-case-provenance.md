# Veri-Sure三项无依据约束：公开案例溯源

日期：2026-10-21。仅核Veri-Sure arXiv `2601.19747v2`及作者仓库固定提交`aab5bed60f04157a4be8581b53f9e913287ba328`；不运行作者代码、模型、HDL、SAT，不读本项目hidden oracle，不改变评价、N15卡或稿件。

**结果：可公开配对并独立复核的具体条目为0。作者报告的三项无依据约束在所核范围内均为UNKNOWN：没有点名task ID、合同原句或对应审计明细。不能把汇总数当作三个已知环境收窄案例，也不能据此判定N15采纳或方法核心。**

## 1. 原文是否点名

已定向复核[官方v2 §6](https://arxiv.org/html/2601.19747v2#S6)、[Appendix C.2／Table7](https://arxiv.org/html/2601.19747v2#A3.SS2)及[PDF p.24](https://arxiv.org/pdf/2601.19747v2#page=24)。作者汇总为：209份合同中12份含13项错误，其中10项功能矛盾、3项规格未支持的约束。该表没有列出这三项的task ID、需求／合同文本、归类理由或逐项修复记录；§6也未补充这些身份。

“三项约束错误”不等于“三份彼此独立的合同”。此外，“12份错误合同中3个任务最终失败”是另一计数；原文没有证明这3个失败任务就是那3项约束所对应的任务。

复核[Appendix D.1–D.3](https://arxiv.org/html/2601.19747v2#A4)的点名案例：Prob157是乘法符号贡献，Prob118是历史寄存器边沿／复位诊断，Prob063是移位方向。这些是RTL修复案例，作者没有将它们标为Table7的三项约束错误，不能拿来补齐缺失身份。§6点名的Prob117／Prob145则属欠规定时序讨论，同样没有该映射。

## 2. 固定源码中的公开原始材料

通过作者[固定提交目录](https://github.com/xyjoey/Veri-Sure/tree/aab5bed60f04157a4be8581b53f9e913287ba328)的完整递归文件树核对，返回`truncated=false`，共661个文件。没有找到已保存的`contract.json`、逐项合同audit、运行结果JSON／CSV、失败到修复的原始run目录或归档包。这里是**该提交内未提供**，不是声称作者没有保存、没有其他公开版本或无法以后取得。

[公开基准目录](https://github.com/xyjoey/Veri-Sure/tree/aab5bed60f04157a4be8581b53f9e913287ba328/benchmarks/verilogeval-v2-ext/dataset_spec-to-rtl)含209份`*_prompt.txt`、209份`*_ref.sv`、209份`*_test.sv`，另有`problems.txt`和`Prob062_bugs_mux2.sv`。需求材料确实存在；但缺审计task映射与原合同，不能仅从209份需求猜出作者那三项新增条件。本轮没有逐读所有需求或参考RTL来制造替代案例。

固定版[README L199–207](https://github.com/xyjoey/Veri-Sure/blob/aab5bed60f04157a4be8581b53f9e913287ba328/README.md#L199)说明运行会保存合同、波形、提示和原始响应；[L225](https://github.com/xyjoey/Veri-Sure/blob/aab5bed60f04157a4be8581b53f9e913287ba328/README.md#L225)说明默认结果目录。它描述产物格式和路径，不是已经发布了作者本次209任务run的证据。重新运行随机生成也不能重建被审计的原合同，因此本轮未作此替代。

源码[Architect L99–138](https://github.com/xyjoey/Veri-Sure/blob/aab5bed60f04157a4be8581b53f9e913287ba328/eda_agent/architect_agent.py#L99)中的`EXAMPLE_OUTPUT`是提示格式示例；没有将它关联到Table7的审计条目，不能用作一份已识别的错误合同。

## 3. 逐项状态：不臆造案例身份

下表的1／2／3仅对应作者汇总中的匿名错误项，**不是已确认的三例task编号或三份独立合同**。

| 作者匿名条目 | 源需求／真实task | 加入条件 | 语义影响分类 | golden是否纠正 |
| --- | --- | --- | --- | --- |
| 第1项 | UNKNOWN；有公开需求全集，未提供该项映射 | UNKNOWN；无可配对原合同原句 | UNKNOWN：不能区分环境域收窄、额外输出要求、设计默认或其他规则 | UNKNOWN；无逐项执行／修复映射 |
| 第2项 | UNKNOWN；同上 | UNKNOWN；同上 | UNKNOWN；同上 | UNKNOWN；同上 |
| 第3项 | UNKNOWN；同上 | UNKNOWN；同上 | UNKNOWN；同上 | UNKNOWN；同上 |

Table7的类别只支持“作者认为存在原规格未支持的要求”这一归纳，不能直接推出输入环境被强化。即使以后拿到原句，仍须结合完整需求／接口／适用模式判断：输入合法域是否减少、输出承诺是否增加、还是某个原本允许的设计选择被固定；不能只凭assumption或constraint字段名称分类。

## 4. golden反馈的证据边界

[C.2正文](https://arxiv.org/html/2601.19747v2#A3.SS2)称12个错误合同中9个任务最终解决，原因是Debugger依据golden testbench的trace覆盖了错误合同影响。这是作者对**全部错误合同集合**的报告，未列出三项约束各属于成功还是失败集合，也未发布逐条修复链。因而不能说三项都被纠正、都未被纠正，或golden已恢复了各自全部原允许输入域。

“最终RTL在golden测试上通过”与“合同文本被修订并获准”“环境前提未被强化”“全部允许轨迹已恢复”也不同。所核[top_agent.py L155–193](https://github.com/xyjoey/Veri-Sure/blob/aab5bed60f04157a4be8581b53f9e913287ba328/eda_agent/top_agent.py#L155)是生成前lint修订；[L435–491](https://github.com/xyjoey/Veri-Sure/blob/aab5bed60f04157a4be8581b53f9e913287ba328/eda_agent/top_agent.py#L435)把同一合同交给后续RTL重生成／调试，不能当作这些未知条目已经正式修改合同的记录。

若要把任一条升级为可复核案例，最少需公开：task ID及需求版本、该次原合同与错误原句、作者audit分类定位、若声称已纠正则给对应前后RTL／合同及golden反馈。现阶段只有汇总层证据，缺少配对原件；本轮到此停止，不联系作者、不扩新文献、不对N15作新裁决。

关联：[方法／实现深审](neighbor-deep-review-verisure-assumptions.md)。本文件新增的是案例证据等级限制，不回写或改变既有报告。
