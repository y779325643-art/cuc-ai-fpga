# N32：独立构思与另外三类任务的公开原件资格

日期：2026-10-21。状态：**完成两次独立构思及限定原件核查，没有保留新核心。** N31新增XOR实现／停止路径证据属于进展。本轮新增三类任务的实际需求来源，排除“只换较复杂功能名称即可建立结构研究问题”的推进方式；不宣称整个资产库没有可研究问题。

## 1. 范围、先验标准和角色

继续使用已应用的scientific-brainstorming流程：先独立构思，再分享和审查；允许弃权，不按票数确认创新。评价标准在委派时明确：精确新增步骤、可信语义提供者、公开任务中的必要决定、同信息最强替代、可区分预测及否定条件；未做数值评分。

两位fresh-context协作者收到相同中性任务，只读[公开组合任务](../../../../artifacts/codex-responsibility-cross-task-20261021-01/public-tasks.md)及[原单槽TD prompt](../../../../artifacts/codex-native-td-pilot-20261021-01/prompts/global.txt)。在提交独立意见前没有互看、搜索文献或读旧构思报告。主审已有近邻知识，不作为独立第三份构思。随后另一位协作者只读另外三类任务的metadata与需求，主审核原件、字段、哈希和计数。

本轮协作者都是开发研究角色，**没有充当被测生成模型**。未执行模型生成、solver、HDL或作者软件，也未读取候选RTL、TB、reference、eval或trajectory补语义。Python仅用于本地metadata索引、文件计数／哈希和文档检查。没有新任务、人工交互、环境/PPA/时序要求或官方实验采纳。

## 2. 两份独立意见：弃权不是领域原创性判断

| 构思来源／阶段 | 原始提案或弃权 | 判断与尚需证据 |
| --- | --- | --- |
| AI协作者A，independent | 考察后放弃“语义图→枚举切分→符号替换边界→选择接口→一次lowering” | 当前ALU/FIR/TD完整公式和边界已确定该过程；同信息typed IR、符号替换及普通求解可完成。没有指出不同处理，不能据新流程图成立核心。 |
| AI协作者B，independent | 明确弃权，不推荐新增步骤；另核算术／控制分开是否形成区别 | 单槽TD控制也已确定。人工完整转移关系须同样给编译基线；模型自行生成关系与RTL一致，不独立认证NL解释。 |

两者的意见只覆盖所给完整公开输入；不是全领域检索结果，也不证明任意语义图工具都已实现。本轮不另搜文献去重复审查一个未成立的新提案。此前[完整数学编译](direct-math-compiler-baseline-review.md)、[时序准备](stateful-task-readiness-review.md)和[接口可实现性](interface-realizability-candidate-review.md)的实际能力／限制仍适用：N20只执行组合normal-only，不认证原单槽控制或完整角色响应。

两者共同的prediction是：在当前固定语义例子上，继续增加分块／证明包装更可能扩充编译器覆盖，尚无首次生成增益证据。这不是实测结果。可以推翻本次弃权的证据，是一个获准真实变体及明确算法，在相同可信输入下自动完成基线需要额外人工决定的接口／控制处理，并给出完整成本或可靠性差异；成熟工具可复用，不要求从零发明solver。

## 3. 另外三家族：实际索引和去重分母

仅索引下列两个根目录的一层sample metadata，不扩查旧日志：

| 根目录 | metadata文件／可解析数 | 本轮纳入方式 |
| --- | --- | --- |
| [sr2fpga_rtl_v1](../../../../datasets/sr2fpga_rtl_v1) | 193／193 | 仅按顶层task_type精确匹配，不给无metadata目录猜身份 |
| [Phase-C independent v2 dataset](../../../../reports/evidence/legacy-runs/phase-c-independent-oracle-20260716-v2/dataset) | 9／9 | 同样规则；历史参考资格不迁移为本篇资格 |

| 精确task_type | 目录数／有requirement数／原字节SHA唯一数 | 去重正文第1行（全部内容） |
| --- | --- | --- |
| matrix_vector_mac | 2／2／1 | Generate an 8-bit FPGA RTL project that implements a small matrix-vector multiply-accumulate datapath. |
| matched_filter | 1／1／1 | Generate an 8-bit matched_filter FPGA RTL project. |
| pulse_radar_signal | 1／1／1 | Generate an 8-bit pulse_radar_signal FPGA RTL project. |
| 合计 | 4／4／3 | 三份不同的单句需求，不是四个独立任务或模型样本 |

同时见到9份composed_vector_mac_pipeline metadata，本轮明确排除，未把它猜作matrix_vector_mac别名；没有读其需求或产物。以上计数限两个指定根和三个精确身份，不外推其他归档、所有家族或完整历史输入。

### 3.1 可复核的原件及哈希

| 原件 | 当前原字节SHA256 |
| --- | --- |
| [MAC需求](../../../../datasets/sr2fpga_rtl_v1/sample_t0_t4_deterministic_smoke_matrix_vector_mac_8_000010/requirement.txt:1)；对应[metadata L10](../../../../datasets/sr2fpga_rtl_v1/sample_t0_t4_deterministic_smoke_matrix_vector_mac_8_000010/metadata.json:10) | f50f7381b18974157c2539148255bd321a8f2644e0bdf1c140e992c2504ec1a1 |
| [另一份同字节MAC需求](../../../../reports/evidence/legacy-runs/phase-c-independent-oracle-20260716-v2/dataset/sample_phase_c_independent_oracle_v2_matrix_vector_mac_8_000002/requirement.txt:1) | f50f7381b18974157c2539148255bd321a8f2644e0bdf1c140e992c2504ec1a1 |
| [Matched filter需求](../../../../reports/evidence/legacy-runs/phase-c-independent-oracle-20260716-v2/dataset/sample_phase_c_independent_oracle_v2_matched_filter_8_000003/requirement.txt:1)；[metadata L20](../../../../reports/evidence/legacy-runs/phase-c-independent-oracle-20260716-v2/dataset/sample_phase_c_independent_oracle_v2_matched_filter_8_000003/metadata.json:20) | 0e8c94ae54c242036726f12dddc0931d59b94bcb03281f9d7b3f616dab5bfe28 |
| [Pulse radar需求](../../../../reports/evidence/legacy-runs/phase-c-independent-oracle-20260716-v2/dataset/sample_phase_c_independent_oracle_v2_pulse_radar_signal_8_000005/requirement.txt:1)；[metadata L20](../../../../reports/evidence/legacy-runs/phase-c-independent-oracle-20260716-v2/dataset/sample_phase_c_independent_oracle_v2_pulse_radar_signal_8_000005/metadata.json:20) | 334aa4c37c59920ab197abc8500b2a7b36ac99e5ce329098a38fd9f897248e5f |

三份正文均只有一个非空行；当前原字节分别104、52、56 bytes。四份metadata的source都标deterministic，仅是本地标签，不认证实际调用。Phase-C三份metadata的requirement_sha256不同于表中原字节hash；将对应UTF-8文本去除两端空白后重算均与字段相符。这解释当前两种计算口径的对应，未认证历史hash算法或完整运行绑定，不将其直接登记为内容损坏。

### 3.2 哪些语义可以据此使用

三个短提示明确8bit、FPGA RTL工程及功能名；MAC另明确小型矩阵向量乘累加。单凭这些文本，没有完整确定数值运算、模块责任、端口或周期，更未给出需要联合选择的连接／接口备选。用户已经允许少量结构变体，但该许可不能补齐缺失的顶层语义；缺少字段也不能直接作为已明确的选择空间来验收两个实现等价。

例如要验证MAC变体保持同一函数，需有可信矩阵／向量形状、系数及数值编码等语义来源；仅有功能名称不能决定这些取值。匹配滤波／雷达同样不能从名称补出滤波系数、帧和阈值规则。这里没有将这些项目添加为原任务要求，也不据此判原工具错误；后续准备应区分已有公共上下文与真正新增的选择。

这些requirement原件不是完整历史messages。没有查发送记录、当前guidance或参考实现来补齐，不能推断旧模型实际只收到一句话，也不能把缺字段归因为模型错误。[N26/N27](stateful-task-readiness-review.md#7-n26归档caller需求与实际模型输入分开核查)确立的来源区别继续适用，但其七版追溯结论不自动迁移为本轮三家族的历史调查结果。

## 4. 对执行顺序的影响

本轮不推荐把这三个功能名直接替换进下一轮模型实验，不采用从参考实现反推的新规范，不恢复已停止机制或N24待选系统定位。少量保持顶层功能的结构变体许可仍有效；其前提是有可核对的完整顶层语义，而不是靠功能名认定等价。

后续候选仍须按顺序提供：完整公开需求及来源→确实需要的结构决定→同信息标准流程的实际处理→新增规则的区分例→包括语义准备的成本／可靠性端点。先前FIR/TD静态变体已完成，不因本轮弃权而重新开展同类planner或扩大生成样本。若正式采纳不同来源的新任务、新增时序/环境要求或改变贡献定位，应先形成具体可审阅范围供讨论；独立只读研究可继续，本轮没有采纳这些变化。

当前可交付结论是：两个独立构思均未保留机制，另三类归档需求也尚不能建立新的开放结构问题。新增原件资格证据改变下一步：停止把这些短提示直接当作“更复杂且已准备好的任务”；不是整个研究无授权可做，也不是SCI目标完成。旧12份原生输出与12父构造、16局部证明、N20执行、任务/评分及三版正文保持原样；本轮只更新讨论与唯一进度清单，不改官方研究定义或运行分母。

## 5. 独立复核与文件验证

独立只读审查复核报告、两个根的metadata索引及四份需求原件，重算计数、字节数和哈希一致，未见限定范围内的Blocker/Major/Minor。未把弃权当原创性证据，也未将短需求等同历史完整输入；这不认证旧运行或新机制效果。

主审静态检查本轮四文档的227个本地文件链接全部可达，无尾随空白；唯一清单N1–N32连续且均六列。三版正文SHA与轮前一致。分支仍为develop、HEAD e20dfd2ce46c5690767e30cb629fb5c58aff073a；工作树计数仍为D108、M56、RM5、R1、未跟踪39。没有暂存、提交、远端操作或实现测试；本轮结果仅为构思／来源资格证据。
