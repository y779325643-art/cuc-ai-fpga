# N50：三个前瞻任务的资格包准备完成

2026-10-22。用户已确认采用FIR8、DOT4-8、PEAK8的新前瞻规范，并仅授权规范与参考资格准备，不调用被测模型或写正文。本轮据此完成开发材料、Python检查、独立审查和字节冻结；**没有执行HDL编译/仿真，三个任务的硬件资格仍为未运行。**

## 已完成的可检查交付

| 部分 | 实际交付 | 验证等级 |
| --- | --- | --- |
| 公开合同 | [共同握手/复位规则](../../../artifacts/three-task-qualification-prep-20261022-01/public/common.md)及[FIR8](../../../artifacts/three-task-qualification-prep-20261022-01/public/fir8.md)、[DOT4-8](../../../artifacts/three-task-qualification-prep-20261022-01/public/dot4_8.md)、[PEAK8](../../../artifacts/three-task-qualification-prep-20261022-01/public/peak8.md)三卡 | 独立静态审查通过；新规范不追认旧需求、不改当前Paper-1任务总体 |
| 参考与控制RTL | 3套复用的确定性参考，6套单处语义错误控制，共27源文件；每个控制有3–7拍公开手算反例 | 来源、函数提取、单文件差异和哈希已核；没有实际golden PASS或control FAIL结果 |
| 独立参考检查 | Python事务模型、合法刺激、逐边沿Verilog TB、实际trace重放器；FIR93、DOT109、PEAK324事件 | 17组Python断言检查通过；数字是激励事件，不是模型样本或HDL检查成功数 |
| 执行器 | 固定9组合、限时/限调用、全部分母、失败停止和来源绑定 | 主审20项合成/假执行器检查通过；独立审查另核27判词例及预算边界，存在覆盖重叠，不合并为实验数 |
| 准备冻结 | [prepared-manifest.json](../../../artifacts/three-task-qualification-prep-20261022-01/prepared-manifest.json) | 151个包内/已加载依赖文件及2工具二进制哈希核验通过；未查询工具版本、未执行HDL |

参考实现来自旧模板的精确函数输出；Python事务模型只依据新公开合同编写，没有读取golden或控制获取答案。双方对相同数学的一致性仍待真正仿真。6个控制是人工资格案例，不能作为自然模型错误、独立生成样本或创新收益。

本轮明确保留异步低有效复位、每次复位至少两个上升沿、PEAK非空帧长度1–256、仅rst_n=1的上升沿计事务。输出阻塞时持有，允许同沿退休旧输出并接受新输入；无效输出payload与复位期间ready不作额外值要求。

## 准备期间修正了什么

在执行任何HDL之前，主审和独立审查发现并关闭参考返回键`passed/pass`不一致、兄弟模块导入路径，以及无见证FAIL/关键X可能误作控制检出的集成问题。现在只有合法非空轨迹前缀中的明确二进制违例才能支持FAIL；空FAIL、timeout、正常trace改FAIL和关键X均不能算成功检错。正常无效payload中的X仍允许。

为让六个已声明控制的资格更易核查，补入两个明确公共序列，形成`generated-v2`；原generated、r01源码和原manifest保留。一次Python合成负例夹具错误也保留了失败与修正记录。它们是准备缺陷，不是DUT/模型错误；最终开发检查通过不意味着准备过程从未失败。

证据：[公开合同审查](../../../artifacts/three-task-qualification-prep-20261022-01/public-contract-review.md)、[硬件静态审查](../../../artifacts/three-task-qualification-prep-20261022-01/hardware-review.md)、[参考审查](../../../artifacts/three-task-qualification-prep-20261022-01/reference-review.md)、[执行器独立审查](../../../artifacts/three-task-qualification-prep-20261022-01/runner-review.md)、[准备验证记录](../../../artifacts/three-task-qualification-prep-20261022-01/preparation-validation.json)。

## 接下来可执行的最小阶段

下一步已经具体到[固定运行计划](../../../artifacts/three-task-qualification-prep-20261022-01/qualification-plan.json)：3任务×每题1参考＋2错误控制＝9个位置，最多18次HDL调用＋2次版本查询，单过程30秒、批次调用预算600秒，0模型、0自动重试。每题先验参考，再验两控制；该题出现非预期或不可用结果就保留后续未运行位置，其他题在共同预算内继续。输出写新运行目录，不能覆盖本准备包或历史结果。命令和目录见[包README](../../../artifacts/three-task-qualification-prep-20261022-01/README.md)。

本轮确认只覆盖准备，所以尚未启动该批次，也没有把CLI的`--execute`当作研究授权。通过标准是参考真实运行被接受、两个控制各有真实数值/事务违例且与独立重放一致；编译失败、超时、X和缺失不算检出。通过后才能决定下一轮被测生成的任务/对照/预算。

**研究状态：已获得可执行资格准备包；尚未证明三个任务可运行、验收流程更可靠或论文贡献充分。** 这一阶段解决可判定输入和真值准备，不将三题数量当SCI最低门槛。正文、旧候选/检查器、现行研究定义与旧N48冻结输入保持；没有Git提交、推送、发布或证据晋级。
