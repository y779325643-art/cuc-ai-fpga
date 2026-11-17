# 英文初稿 v0.2 独立审阅

日期：2026-10-21。模式：`review`，末轮仅对已提出的 METH-001 做 `targeted-re-review`。仅写本文件，不改稿件、协议、检查器或结果；未重跑模型、HDL、形式验证或作者框架。

审阅对象：[英文稿](../../drafts/structure-responsibility-v0.2.en.md)。初读 SHA256 为 `e93ea59177ad317417e597d1a999c6d185094760df46b209124b1e8cf7daeb80`；根任务据审阅意见修改 §3/§7.2 后已复核，随后新增 Feng/Hu 先例段与引用亦已读取。最终复核版本为 `71ec0c4e8afa499b307eea854514004489daf897eafc1652ee9356e8c12253da`。下文稿件行号对应最终复核版本。

**结论：在“开发原型与有界零差异结果”的定位下，未发现仍未解决的具体 Blocker/Major 事实或主张错误。** 数据分母、null 解释和近邻强度与所核材料一致。一项有关完整外延函数与内部实现自由度的措辞问题已核实修正。此结论不表示方法创新已成立、论文已可投稿或 SCI 总目标完成。

## 1. 实际问题及复核状态

| ID / 等级 / 状态 | 可定位问题 | 实际影响与复核 |
| --- | --- | --- |
| METH-001 / Minor / resolved | 初读 §7.2 把潜在价值表述为较小义务，并只说逐输出映射“可能接近”写父实现；§3 尚未显式区分外延完整性与内部组织未定 | 对这些 profile，完整 active/inactive 映射已经确定 `(x,z)` 到全部外部输出的函数。没列每个内部信号，不蕴含比最简完整 IR 更小的行为规格、更大实用自由度或更低建模成本。修订后[稿第60行](../../drafts/structure-responsibility-v0.2.en.md#L60)和[第167行](../../drafts/structure-responsibility-v0.2.en.md#L167)已明确以上边界，并把成本/自由度优势保留为未证；本轮复读确认解决 |

没有为满足数量而追加问题。其余研究缺口列于第4节，不冒充稿件已经宣称的结果错误。

## 2. 数据与分母：独立复核通过

主要来源：[evaluation-summary.json](../../../../artifacts/codex-responsibility-transport-20261021-01/evaluation-summary.json)第5–409行及24个 records；[runtime-audit.json](../../../../artifacts/codex-responsibility-transport-20261021-01/runtime-audit.json)；[root-result-verification.json](../../../../artifacts/codex-responsibility-transport-20261021-01/root-result-verification.json)第3–24行。

本轮直接从 summary 的24个 record 内 coverage/metrics 重算各 arm 总计，从 runtime 的12个 record 重加 token、配置、工具调用及后续反馈计数；没有重新执行 evaluator。summary 文件实算 SHA256 为 `7163d5cb0060978878e39903a3c4017bbe6a7b1f7d0b06d032eab881a2e2564c`，与根验证记录一致。

| 核查项 | 重算/读取结果 | 稿件定位与裁决 |
| --- | --- | --- |
| 真实生成与构造分母 | 12 first_output + 12 program_parent；全部 passed，其他状态均0；2条件各6份，3任务各4份原始输出 | 第144–155行正确；没有把24评估说成24模型生成，也没有移除失败/unknown |
| 线程拒绝 | 1次发生于初始化前；12个已初始化候选，无生成重试 | 第116行正确地区分13次 wrapper invocation 与12次生成；不是被隐藏的候选失败 |
| 普通输出比较 | 每 arm：ALU 4,096、FIR 32,768、TD 768，合计37,632 | 第146–151行相符 |
| 响应输出比较 | 每 arm：ALU 65,536、FIR 4,194,304、TD 14,592，合计4,274,432 | 第146–151行相符；标为 scalar comparisons，未当样本数 |
| 其他比较 | 每 arm：2,167,552 input/probe pairs、6,512,384 input-integrity scalar comparisons；根记录另核20,736普通 target-port comparisons；各类失败计数均0 | 第153行相符；这些仍不是独立任务或总体统计分母 |
| 工具执行 | 两 arm 合计24次 Yosys、24次 compile、24次 simulation；summary 的独立验证记录72 stages exit0 | 第155行相符；本轮未重新审阅全部72段原始日志，依赖已保存根验证记录，不声称再次执行 |
| 使用量 | input 363,002，cached-input 333,056；output 10,772，其中reasoning 4,336；total 373,774 | 第120行正确，reasoning未重复相加；global 186,980、located 186,794，不解释成相同成本或节约 |
| runtime边界 | 12份均记录gpt-6.1-sol/ultra，工具调用与后续反馈均0；hard denial=false、plaintext attestation=false | 第116–118行准确保留配置≠快照认证、零调用≠硬隔离、加密输入未端到端明文核证的限制 |
| 重复与独立性 | 10个source bundle，12个attempt仍保留 | 第116、122行未把不同文本/重复attempt当独立设计总体 |

[全宽六控制](../../../../artifacts/responsibility-full-profile-qualification-20261021-01/results.md)第9–26行与稿第128–136行一致：三份faithful响应零错，三份bypass分别3,840 / 520,192 / 2,845个scalar mismatch；均正常通过。它们没有混入12份原生输出的成功/失败计数。

[手工miter](../../../../artifacts/responsibility-manual-miter-20261021-01/results.md)第6–30行与稿第140行一致：delegate 16,384/16,384；wrong_mode 8,704通过、7,680失败，00/01各3,840，10/11为0；两个normal projection均1,024/1,024。稿第104、140行没有将normal projection冒充真实adder另跑，也没有把ALU两父实现的核对升级成任意绑定或全部profile资格。

## 3. 主张—证据与近邻裁决

| 主张 | 证据与范围 | 裁决 |
| --- | --- | --- |
| 本轮没有观察到提示组织或固定父构造的通过数收益 | 两提示各6/6，两实现arm各12/12；稿第153、177、181行明确不证明统计等价或一般无效 | PASS；“bounded null finding”按文中限定是描述性零差异，不是已检验的统计零假设 |
| CPPL不是只保留实例名 | [CPPL/HINT深审](neighbor-deep-review-cppl-hint.md)第18–59行：接口/真实binding、ALU父mux、共享原始a/b、确定性lowering；同期838aab3与后续d7ebbb5分开 | 稿第25–27、167行正确；没有声称CPPL必然接受本项目反例，也未宣称当前代码只能静态检查 |
| HINT有实质架构与语义保证 | 同深审第60–75行：前RTL执行、父switch/helper/commit、后共仿真，agentic lowering；RQ1与完整Lint流程区别；作者完整SPEC/代码不可核 | 稿第29行准确，不把“未证精确自由响应检查”写成“必然允许重算” |
| 成熟工具已能暴露正常等价、自由切点响应不同 | [VeriRefine/EQY深审](neighbor-deep-review-verirefine-eqy.md)第36–55行；本轮又只读核对官方固定SHA的[ex_bind.sv](https://github.com/YosysHQ/eqy/blob/fb8b21160297b3e66bf94f3c24f8a8bf1cd3fd51/examples/simple/ex_bind.sv)和[ex_bind.eqy](https://github.com/YosysHQ/eqy/blob/fb8b21160297b3e66bf94f3c24f8a8bf1cd3fd51/examples/simple/ex_bind.eqy)：两边X/Y相同，Z分别为X xor Y及A xor C；配置bind X/Y保留上游关系 | 稿第41–43行相符；这是源码/代数能力依据，不是EQY在本项目已运行或已适配成功的结果 |
| 固定父/完整IR是强替代 | 稿第60、112、167–169行承认可由构造排除违约，最简IR可能保留同样内部选择；当前成本及有用实现空间均未证 | PASS，METH-001已解决。不能据“不逐信号规定”继续推出优势 |
| 三任务是新开发profile，不是原创benchmark发现 | 稿第25行称CPPL ALU为直接先例；第82、173行明确新组合开发面、非无偏样本、非旧任务资格继承 | PASS；没有发现把ALU相似例子当benchmark新颖性的具体主张。其科学增量仍需别的证据 |
| 普通功能/资源/全部leaf与binding保证 | 稿第62、70、175行把额外profile违约、单target绑定、有限域和物理资源界限分开 | PASS；当前不能从这些结果推全局叶函数、每条连接、综合资源或一般RTL正确性 |

VeriRefine的guard/action/出处审查、Direct条件与实现未取得边界，在稿第33行与[深审第23–34行](neighbor-deep-review-verirefine-eqy.md#L23)一致。没有把普通IR只能表达、尚未实施的适配，写成作者已经做过的具体检查。

## 4. 真正决定方法贡献的未证研究问题

以下是 SCI 总目标仍未闭合的研究问题，**不是用一个较大模型实验就自动补齐的样本量问题**；本评审不授权任何新增运行，也不预判尚未存在的工具适配结果。

1. **相同数学义务下的增量是什么？** 现有AST已经完整描述父上下文外部函数。须实际比较最简完整IR/固定父构造与标准切点流程，在相同域、signed/wrap/sat、实际目标与额外合同下分别需要什么建模和映射步骤；不能先假定IR较繁琐或不支持该关系。当前标准适配没有结果，不能作能力判决。
2. **自动绑定与干预可靠性是否实质减少人工负担？** 手工miter和六控制已支持有限正确性核对；仍需区分现有工具已经提供的匹配/partition能力与本工具新增的可验证便利，明确支持/unknown边界。命令顺序、换一个标签、将force换成miter都不足以单独构成创新。
3. **所谓保留的自由度具体是什么？** 必须按合同相容的实现族定义，不以不同字符串、10个source hash或省略中间信号规则计数。若最简完整IR同样接受这些变体，不能再主张更大实现空间；可以如实比较审阅或适配代价。
4. **额外强合同为什么在真实任务中值得付出成本？** 用户事先接受足以使违约定义有效，却不证明广泛实用价值。需明确何种真实架构要求需要这种off-manifold关系，而不仅是为区分手写bypass而新增规则；ALU与CPPL例子相近，不能单独承担应用或任务新颖性。
5. **真实首次生成中的边际收益是否存在？** 本轮原生输出零违约，故没有真实新增检出、提示收益或构造收益。后续若仍为零，可保留诚实的复现实证/工具开发结果，不能把手写负例换算为模型效果。是否值得补任务，应由上述未决问题驱动，不能只为制造失败。

稿件第19、167–181行已大体承认这些限制。因此当前文字可以作为诚实开发初稿，但不能把“初稿已经存在”与“用户的创新点与SCI论文目标已经完成”混为一谈。作者/机构、目标刊物适配、最终图表与披露、对外可复现材料也仍需后续作者工作；本轮没有投稿适配或发布验收。

## 5. 审阅终止与限制

- **事实/数值与分母：PASS。** 本轮只做已有JSON/报告的只读重算，未重跑HDL。
- **null解释、近邻/版本、公平性边界：PASS。** 未解决Blocker=0、Major事实错误=0；METH-001已复核解决。
- **方法新颖性及实用增量：NEEDS_EXTERNAL_VERIFICATION / 未证。** 不由本轮审稿签发通过。
- **原始日志、全部候选RTL和完整叶功能：未作新的全面审计。** 使用保存的root验证及明确范围的控制报告；未对摘要之外的候选行为另行推断。
- **最终排版/渲染、完整文献综述、目标刊物准备：NOT_ASSESSABLE。** 当前是Markdown初稿，未做版面或投稿验收。

停止理由：授权范围内的关键核对完成，唯一具体措辞问题已解决；尚未执行的强适配与方法效益不能靠继续文字审查补出。本文件不要求根任务改动已封存的24条评估数据。
