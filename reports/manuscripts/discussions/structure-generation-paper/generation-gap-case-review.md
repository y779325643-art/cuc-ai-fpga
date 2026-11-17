# N29：从公开失败工件核查生成问题，而非从汇总低分推定gap

日期：2026-10-21。状态：**完成有界案例审查；获得一个外部任务的两份可定位候选错误，但没有建立新的生成核心。** 上一轮N27/N28取得新原件/数学及强对照证据并改变后续投入决定，属于进展；本轮不重复旧日志追溯或已停止候选。

范围：两名协作者分别核四份本地公开材料、四份既有研究材料；另一协作者筛四篇新主源，只深审ROME。主审另深审ChipVerilog，共两项新增方法/实现审查、三项只作线索。未执行模型、HDL、solver或作者代码；未读取本项目候选RTL、TB、reference、隐藏评价或凭据。外部候选/编译日志为公开开发案例，不能以后冒充未见样本。

## 1. 本地实例与输入成本：不能混淆两个结论

| 已核公开入口 | 当前可以支持什么 | 仍不满足什么 |
| --- | --- | --- |
| [原TD完整prompt](../../../../artifacts/codex-native-td-pilot-20261021-01/prompts/global.txt:6) | 有完整算术与单槽周期语义 | 已固定三模块、R17接口及连接，不能原样当开放分解实例 |
| [原FIR4完整prompt](../../../../artifacts/codex-responsibility-cross-task-20261021-01/prompts/FIR4-C0.txt:9) | 有完整输入类型、算式、系数、自由响应 | 模块数、实例及级联已明确；局部写法自由不等于分解自由 |
| [catalog FIR条目](../../../../contracts/task-catalog/sr2fpga-task-catalog-v0.2.json:1693) | 列出义务类别 | 没有该实例完整数值/周期，类别名称不能补成新约束 |
| [family_recipe](../../../../agent/src/sr2fpga_agent/family_recipe.py:188) | 路由与guidance身份 | 不能认证实例输入完整或拓扑可改 |

两位独立审查均未保留新案。结论只覆盖所核材料，不证明仓库或领域没有合格问题。少量结构变体的设计许可仍有效，但开放集合须另行明确，不能修改旧prompt后称原实验。

**N20已实际实现的是“可信normal AST→RTL”，并非“原始自然语言→可信AST→RTL”全部自动化。** 当前prompt的数学可人工转录，不代表程序已经有自动前端。可信F的获得成本尚未测量；本方法和强基线都必须承担同样准备成本。这个未知提示了需核的交接阶段，本身没有提供新推导规则或可区分机制，也不恢复N18/N19。

## 2. ChipVerilog：核到具体工件，但原因和方法收益要分开

审查[论文v3](https://arxiv.org/html/2607.13079v3#S3)，2026-08-17；原文§3.3–3.4和§4.1已经区分prompt整理、目标模块替换与参考子模块、完整系统仿真。不是仅有短独立模块的弱对照。版本由[arXiv记录](https://arxiv.org/abs/2607.13079)确认；v1附录结构不同，不用v1替代v3方法。

固定作者仓库SHA **`3eea482f20c048966d54ed04c418b85e5fd4d498`，2026-08-15**，不认证为论文实验冻结版本。范围固定为FPU这**一个任务、缓存的前两个DeepSeek候选**，不按错误类型筛样，不重跑、不推算总体率。论文汇总中的复杂层次低分不直接证明是哪类结构错误。

| 原件与配对检查 | 已证错误／结果 | 不能据此推断 |
| --- | --- | --- |
| [t1候选L192起](https://github.com/HKUSTGZ-MICS-LYU/ChipVerilog/blob/3eea482f20c048966d54ed04c418b85e5fd4d498/Result/deepseek/fpu/fpu_t1.v#L192)、[compile.log](https://github.com/HKUSTGZ-MICS-LYU/ChipVerilog/blob/3eea482f20c048966d54ed04c418b85e5fd4d498/Result/deepseek/fpu/fpu_t1/compile.log)、[result.json](https://github.com/HKUSTGZ-MICS-LYU/ChipVerilog/blob/3eea482f20c048966d54ed04c418b85e5fd4d498/Result/deepseek/fpu/fpu_t1/result.json) | 同一exception实例两次绑定inexact；源码与归档elaboration错误一致，缓存exit1/compile_fail，后续检查skip | 不是已观察的行为旁路、跨局部备选冲突或新方案胜出；未证明只改这一处即可通过 |
| [t2候选L247起](https://github.com/HKUSTGZ-MICS-LYU/ChipVerilog/blob/3eea482f20c048966d54ed04c418b85e5fd4d498/Result/deepseek/fpu/fpu_t2.v#L247)、[compile.log](https://github.com/HKUSTGZ-MICS-LYU/ChipVerilog/blob/3eea482f20c048966d54ed04c418b85e5fd4d498/Result/deepseek/fpu/fpu_t2/compile.log)、[result.json](https://github.com/HKUSTGZ-MICS-LYU/ChipVerilog/blob/3eea482f20c048966d54ed04c418b85e5fd4d498/Result/deepseek/fpu/fpu_t2/result.json) | module层条件分支内直接给wire赋值，日志有候选语法/非法实例错误；同时列参考支持文件重复声明，缓存exit9/compile_fail | 不能把全部诊断都归因模型；未隔离参考/工具语言模式影响，也未证明存在语义结构选择难题 |

这是固定提交内候选字节与缓存日志的静态配对，**不是本轮重新执行**。结果的model字段是作者标签，不另行认证实际provider版本、网络发送或运行环境；同树与同路径不是完整历史生成谱系。未读取参考RTL或TB来判断功能。

### 2.1 当前生成输入不能自动认证缓存候选的历史上下文

作者[FPU description](https://github.com/HKUSTGZ-MICS-LYU/ChipVerilog/blob/3eea482f20c048966d54ed04c418b85e5fd4d498/Src/double_fpu/des/verilog/fpu_double/description.txt)描述了顶层端口、操作/舍入及处理流程，但未列完整子模块ABI或各操作具体完成周期。当前[build_user_prompt L181](https://github.com/HKUSTGZ-MICS-LYU/ChipVerilog/blob/3eea482f20c048966d54ed04c418b85e5fd4d498/tools/generate_deepseek_results.py#L181)、[payload L259](https://github.com/HKUSTGZ-MICS-LYU/ChipVerilog/blob/3eea482f20c048966d54ed04c418b85e5fd4d498/tools/generate_deepseek_results.py#L259)及[调用L343](https://github.com/HKUSTGZ-MICS-LYU/ChipVerilog/blob/3eea482f20c048966d54ed04c418b85e5fd4d498/tools/generate_deepseek_results.py#L343)读description构造system/user消息，没有追加依赖RTL或ABI。

评价侧[resolve_support_files_for L811](https://github.com/HKUSTGZ-MICS-LYU/ChipVerilog/blob/3eea482f20c048966d54ed04c418b85e5fd4d498/tools/formal_equivalence.py#L811)按模块名寻找参考支持，[verify_candidate L1709](https://github.com/HKUSTGZ-MICS-LYU/ChipVerilog/blob/3eea482f20c048966d54ed04c418b85e5fd4d498/tools/formal_equivalence.py#L1709)分别装配两侧，缺依赖可发stub后再编译。不能将存在stub或当前工具接口读成已认证完整系统功能。

但本轮没有定位t1/t2的实际初始消息快照，因此**不能断言这两个旧候选当时没有收到ABI，或将错误因果归于输入不足**。固定仓库Result/logs本轮目录索引只见formal；README所指Zenodo DOI工具无法访问，保留UNKNOWN，不断言归档不存在。到此停止追溯。

### 2.2 对新机制的裁决

重复端口绑定、方向、宽度和非法表达首先面对普通parser、接口校验及typed emitter；既有[CPPL/HINT](neighbor-deep-review-cppl-hint.md)是真实强对照。FPU集成比原小算术复杂，不自动给出联合选择的新增处理。修正支持文件或补齐公共ABI是任务/基础设施准备，也不能算方法成功。

## 3. ROME：承认已有具体交接与反馈流程，失败案例只到作者报告级

[ROME v1完整方法§3.1–3.3](https://arxiv.org/html/2407.18276v1#S3)有人工或模型分层、逐模块生成和测试反馈、顶层集成及relay上下文。[§6](https://arxiv.org/html/2407.18276v1#S6)报告早期模型的MIPS漏control unit、信号命名不一致，需要人工干预；同节另报GPT-4经过自动反馈获得无人工干预实例，不能只摘失败段将全流程说成失效。

仓库[README](https://github.com/ajn313/ROME-LLM/blob/be3977e16b9b032d8800b73491479fb85b4dc1f1/README.md)对应该论文。代码固定 **`be3977e16b9b032d8800b73491479fb85b4dc1f1`，2026-10-17**，不能替代2024论文运行版。主审回读Notebook的[接口抽取L1016](https://github.com/ajn313/ROME-LLM/blob/be3977e16b9b032d8800b73491479fb85b4dc1f1/ROME_Demo.ipynb#L1016)、[hier_gen L1130及L1236附近](https://github.com/ajn313/ROME-LLM/blob/be3977e16b9b032d8800b73491479fb85b4dc1f1/ROME_Demo.ipynb#L1130)和[Icarus/vvp L848](https://github.com/ajn313/ROME-LLM/blob/be3977e16b9b032d8800b73491479fb85b4dc1f1/ROME_Demo.ipynb#L848)：当前代码确实传既有模块接口，并把先前完整RTL与当前RTL一起编译、检查和修复，不是只有提示口号。

固定完整tree112项，包含MIPS相关TB路径，但未定位所述失败生成件/运行日志。协作者检查15个Notebook cell，保存输出全空；主审复核完整树及关键代码，没有读取TB。故本轮没有形成该MIPS失败的完整原件链，不据作者叙述造错误端点或效果分母。更不把“缺某个模块”直接判错：需先核事前承诺，合法融合实现不能仅因不同于人工分解被拒。

另外仅筛查：[LocalV v1附录E](https://arxiv.org/html/2602.00704v1#A5)的方向混淆没有配对失败工件；[Spec2RTL-Agent v1 §V-E](https://arxiv.org/html/2506.13905v1#S5.SS5)维度错误发生在Python子函数，不冒称RTL实例；[RTL++ v1 §IV-E](https://arxiv.org/html/2505.13479v1#S4.SS5)图辅助描述不是所需交接失败。三项不登记为已深审方法或新核心依据。

## 4. 当前决定及后续证据门

不开发“端口去重”“转发header”或“先列模块再集成”的改名方案，不以更复杂任务或更多模型调用补创新；不恢复局部备选、R1b、R2，也未采纳N24系统定位。两份外部错误有具体原件，已比汇总失败率更明确，但它们没有给出现有标准流程之外的处理。

下一项生成机制必须同时给出：可追溯完整公开输入；事前确有必要的结构决定；标准同信息流程的实际能力；新步骤额外处理什么；可以否定该步骤价值的具体区分例与成本端点。自然语言到可信F、公共依赖ABI和架构要求都要纳入准备账，不能免费给方法、留给基线自行猜测。若改用外部IP、改变时序/资源或转研究定位，应先形成具体范围供用户讨论；此报告不采纳这些变更。

本轮只新增静态报告及索引状态，零新增被测模型生成、零HDL/solver执行、零新性能样本；外部缓存两份不加入原12模型样本分母。旧稿v0.3、三版初稿字节、旧合同/评分、数据及现行研究定义不改，SCI/SCIE创新门仍未验收。没有将未知历史输入或待选定位扩大为整个目标阻塞。

独立收尾复核本报告及三处索引，并回读两候选片段/两份编译日志，未发现限定范围的Blocker/Major；缓存身份、混合诊断、历史输入UNKNOWN及N20输入边界一致。该复核不重新认证ROME运行或全文方法。主审静态检查四份文件的205条本地文件链接可达、29个N阶段行均为6列；三版初稿SHA及Git状态计数与本轮开始一致。未提交、暂存或推送。
