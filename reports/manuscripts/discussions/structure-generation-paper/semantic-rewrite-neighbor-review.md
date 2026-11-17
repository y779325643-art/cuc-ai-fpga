# 非字面语义重写候选：RTLRewriter 与 ASPEN 有界深审

日期：2026-10-21。仅新增本文件；未生成候选、运行模型／HDL／作者框架、安装软件或读取 hidden 内容。采用 `paper-code-joint-analysis` 的有界问题流程；只深入以下两项，不扩第三篇。所有“未见”仅限已读原文与取得的公开材料，不证明领域绝无。

**判断：不建议将“LLM 发现非 AST 字面中间量、程序证明等价后生成 RTL”单独作为新核心继续开发。ASPEN 已有直接的方法重合，RTLRewriter 的公开资产也已有跨输出代数共享。FIR 的 `e/t` 变换可以是后续资格样例；只有自动推导并认证模块接口／局部合同的实际交接价值尚未被本轮两篇建立，也尚未被本项目证明，不能靠生成顺序差异直接认定创新。**

## 1. 固定来源、版本与已读范围

| 工作 | 原始来源与覆盖 | 实现材料及限制 |
| --- | --- | --- |
| RTLRewriter: Methodologies for Large Models aided RTL Code Optimization，ICCAD 2024 | [作者 PDF](https://www.cse.cuhk.edu.hk/~byu/papers/C239-ICCAD2024-RTL-rewrite.pdf)，9页；[arXiv v1](https://arxiv.org/abs/2409.11414v1)；[DOI](https://doi.org/10.1145/3676536.3676775)。细读 §§3.1–3.3、4.1–4.3，图2–6、表3/10；作者网页 PDF 无单独修订号，不把它声称为逐字节固定的最终会刊版 | 作者明确链接 [RTLRewriter-Bench](https://github.com/yaoxufeng/RTLRewriter-Bench)，固定提交 `96639fe67bc8f020c05978ef5028d75fcf6980f2`（2024-05-18）。递归树完整，抽核 README、提示与下列 RTL 配对；该树未提供 partition／C-MCTS／solver 调度框架源码，不能称框架实现审计完成 |
| ASPEN: LLM-Guided E-Graph Rewriting for RTL Datapath Optimization，MLCAD 2025 | [Cornell 作者 PDF](https://www.csl.cornell.edu/~zhiruz/pdfs/aspen-mlcad2025.pdf)，9页；[NVIDIA 官方记录](https://research.nvidia.com/labs/electronic-design-automation/publication/deng2025aspen/)标注 September 2025。细读 §III、Algorithm 1、图2–4、§IV、Appendix A/B 表IV/V | 本次未取得可归属作者、可固定 SHA 的框架源码。作者页未给代码链接；活动索引提示的 `zzzDavid/aspen-complete-workflow` 经 GitHub repo／commits 查询均404，不能以该线索证明实现，也不能断言从未开放 |

以下严格分开：论文报告的方法和结果、作者仓库可见的资产、已追溯生成调用的结果。本轮只有前两类；没有外部模型调用记录可供独立归因。正文不复述论文优化比例，不把作者报告当作本地复现。

## 2. 实际机制与顺序：短表核对

| 工作／定位（PDF页码） | 提议、选择、成本及反馈顺序 | 对候选的直接意义 |
| --- | --- | --- |
| RTLRewriter §3.1，pp.2–3，图2 | 既有 RTL 实例树分区，预测综合时间并考虑 edgecut | 不是数学函数中重新发明坐标／ABI |
| RTLRewriter §3.2，pp.3–5，图3/5、表3；§3.3，p.6，图6 | 分析／检索→LLM重写→仿真过滤、等价与综合→C-MCTS反馈／反思；保留最佳 | 直接改RTL，含多轮反馈；不是生成前冻结的证明合同 |
| ASPEN §III.A–C，pp.2–3，Algorithm 1、图2/3 | 一次提新规则及Z3脚本，证明后入池；按历史PPA选规则并做egglog saturation | “提议后认证再程序应用”已有 |
| ASPEN §III.D–E，p.4，图4；§IV.C/F，p.6；附录表IV/V，pp.8–9 | 抽取→程序转Verilog→综合→更新e-node成本／回退；最终Pareto点另做等价检查；含FIR、DCT、MCM新规则 | 非字面代数共享已有；不保证每个中间PPA点先验等价检查 |

来源：[RTLRewriter 方法](https://www.cse.cuhk.edu.hk/~byu/papers/C239-ICCAD2024-RTL-rewrite.pdf#page=3)、[ASPEN 方法](https://www.csl.cornell.edu/~zhiruz/pdfs/aspen-mlcad2025.pdf#page=2)、[ASPEN 附录](https://www.csl.cornell.edu/~zhiruz/pdfs/aspen-mlcad2025.pdf#page=8)。ASPEN 规则利用3倍项构造7倍、再由7倍项构造21倍，并有嵌套因式分解；不能描述为仅搬原AST子树。其规则的Z3脚本也由LLM提出，不等同于独立可信程序自动推导全部证明义务；没有源码，无法继续审计脚本／规则语义绑定。

两篇均有传统工具强对照：RTLRewriter §4.1/4.3 比较 Yosys／自建 Yosys+Egg 及搜索变体；ASPEN §IV.A/B 的 ROVER 是作者复现，采用初始规则和固定成本，并有商业综合对照。它们支持各自设置中的工具／代理增量研究，不证明 LLM 对本 FIR 小域不可替代。ASPEN 的最小面积与最小时延从前沿分别选择，不能合并成同一实现点；本轮不据其数字推断本项目收益。

## 3. 作者资产中与“必需输出可共享”直接相近的例子

固定 SHA 同第1节；路径拼写保持仓库原样。

| 资产及精确行 | 静态可见事实 | 不能推出什么 |
| --- | --- | --- |
| [subexpression_elimination_raw.v](https://github.com/yaoxufeng/RTLRewriter-Bench/blob/96639fe67bc8f020c05978ef5028d75fcf6980f2/short_benchmark/datapath/subexpression_elimination/subexpression_elimination_raw.v#L16)，16–21；[对应版本](https://github.com/yaoxufeng/RTLRewriter-Bench/blob/96639fe67bc8f020c05978ef5028d75fcf6980f2/short_benchmark/datapath/subexpression_elimination/subexpression_elimination.v#L16)，16–21 | 原 `s4=c+d+b*a`、`s5=a-b`；原 `s6=(b+1)*a+d+c-b` 改为复用输出 `s4+s5`，不是原s6的字面子树 | README第7行说明工程师整理optimized材料；这不是有生成日志的LLM发现，也不是本轮执行等价结果 |
| [commutativity_subexpression/basic.v](https://github.com/yaoxufeng/RTLRewriter-Bench/blob/96639fe67bc8f020c05978ef5028d75fcf6980f2/short_benchmark/basic/commutativity_subexpression/basic.v#L7)，7–12；[basic_ours.v](https://github.com/yaoxufeng/RTLRewriter-Bench/blob/96639fe67bc8f020c05978ef5028d75fcf6980f2/short_benchmark/basic/commutativity_subexpression/basic_ours.v#L6)，6–18 | 六输出重写显式保留共享加／乘／差项及重结合项 | 文件名 `_ours` 不是调用出处；未证明每份输出来源、验证轨迹或物理资源单份共享 |
| [prompt-example.txt](https://github.com/yaoxufeng/RTLRewriter-Bench/blob/96639fe67bc8f020c05978ef5028d75fcf6980f2/examples/prompt-example.txt#L38)，38–41 | 公开提示要求等价、PPA优化并输出Verilog | 自我检查要求不是形式保证，也未显示独立的模块合同推导 |

因此不能再用“先例没有跨既有输出共享”区分新候选；同样不能反过来把这些文件当成已独立验证的模型能力统计。ASPEN 附录明确报告 agent-generated 且通过规则验证，属于作者论文证据，仍不同于可核对请求／响应／求解日志的原始执行记录。

## 4. 对 `e=x0−x2; t=2x0−x1; f=2t−e` 的机制映射

以下是本轮独立手工分析，不是模型输出、工具验证或正式任务资格。公开数学来源：[冻结 FIR4 profile](../../../../artifacts/codex-responsibility-cross-task-20261021-01/public-tasks.md)第21–35行；该旧profile固定三MAC链。新分解改变内部接口及责任，必须另版本准备，不能沿用旧资格或24项评价分母。

| 拟新增步骤 | 本轮判断 | 必须回答的剩余问题 |
| --- | --- | --- |
| 提出原式没有的 `t`，利用本就输出的 `e` | 与已读代数重写／多输出共享实质重叠 | LLM相对同信息线性重写搜索或e-graph的具体增量是什么？ |
| 证明 `2t−e=f` | 标准等价认证，不是新求解算法 | 精确整数、截断与Verilog宽度语义是否一一绑定？ |
| 自动导出坐标范围、类型、模块接口及完整局部合同 | 两篇取得材料未建立这套交接机制 | 是否比从同一已认证DAG直接编译／抽子函数有实际收益？ |
| 固定接口后一次生成局部行为 | 与两篇主流程的顺序／反馈限制不同 | 编译器已有局部表达式时，模型填写还增加什么可测价值？ |

对 signed4 输入，手工界限为 `e∈[-15,15]`（signed5）、`t∈[-23,22]`（signed6），最终精确 `f∈[-46,44]`（signed7）。这些界限不是自动推导已实现的证据，也不能把“范围可证”当作架构优越性。

局部全域必须另讲清：若最终模块仅拿5位e、6位t的**完整编码域**作为输入，`2t−e` 的精确中间范围是 `[-79,78]`；若承诺精确整数中间值，需signed8容纳。若局部合同仅规定`wrap7(2t−e)`，正确扩展后的7位模运算也可直接满足，无须一概先计算8位精确值。若只承诺上述可达范围，须显式导出并证明范围假设，不能悄悄缩小自由局部合同。原profile的单边界干预响应也不会自动成为新e/t结构的责任规范。

代数式仅能证明功能等价，不能证明PPA变好。e的额外扇出、t路径、符号扩展与共享后的时序都可能有代价；保持命名／实例也不证明只用一份物理算术资源。两篇的工具反馈恰是对这种不确定性的处理，新候选去掉反馈后须另有可测目标。

## 5. 有界裁决与同信息强替代

**停止将这条FIR恒等式单独包装为新方法核心；保留资格／交接研究的可能，不作领域不存在的结论。** “非AST”“共享必需输出”“先证明再应用”均已有直接先例；“生成前而非生成后”只是顺序差异，必须产生额外可审计价值才构成贡献。

成熟原语或非LLM可替代性本身不会否定一项SCI系统方法；本轮停止建议针对已经重合的坐标提议／等价认证／程序抽取主张。ABI与首次无反馈流程仍是未证实的系统假设；NL→项目与既有RTL优化的输入差异也不自动构成gap。

若以后研究交接，最低强替代应共享公开全函数、位宽／范围及允许操作：①标准代数／e-graph或小系数有限搜索产生坐标；②同一认证DAG／完整IR直接编译并提取局部接口；③把同一认证局部函数交给模型生成。另须与同信息、可比生成预算的完整实现生成及有限候选协议比较，统一可信语义和全局复核。不能只比无约束整体RTL生成，也不能把ASPEN削弱成“LLM直接重写、不先证明”。

这能裁决的窄问题是：自动、可信的接口／局部义务交接是否减少建模／资格成本或提高明确约定的首次生成遵约率，而非恒等式是否成立。当前没有该增量证据；未取得作者框架时只能称按论文机制独立适配，不能称复现作者实现。若确定性编译给出相同接口／义务、且模型步骤不带来其他价值，应停止这项核心，而不是为保留LLM另加任务条件。

关联：[FormalRTL／Stepwise 深审](neighbor-deep-review-formalrtl-refinement.md)。本文不修改当前稿件、旧实验、trusted evaluator 或正式研究规范。
