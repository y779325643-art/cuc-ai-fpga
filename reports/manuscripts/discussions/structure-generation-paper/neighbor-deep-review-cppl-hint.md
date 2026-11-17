# CPPL / HINT 方法与实现深审：条件性模块责任的证据边界

日期：2026-10-21。用途：为当前候选重新定位；不是两套系统的复现、性能比较或创新性验收。只修改本文件；未运行作者框架、模型、HDL 或本地 checker。原生候选输出不进入本轮分析。

**结论：两篇近邻均已约束真实的父层组织，不能降格为“保留实例”或“提示计划”。当前可研究的窄问题，是在父层仍可读取原始操作数时，审计生成前明确声明的条件性自由边界响应。公开资料尚未证实近邻已实现该检查，但这既不证明其一定接受违规实现，也不证明当前检查或表示具有新颖性。** 固定父逻辑或足够严格的 typed IR 可以直接排除这些违规；当前工作不能声称全面超过它们。

## 1. 阅读范围与版本

| 对象 | 本轮已读 | 尚不能证明 |
| --- | --- | --- |
| CPPL | [v1 官方全文](https://arxiv.org/html/2605.17892v1)、[9 页 PDF](https://arxiv.org/pdf/2605.17892v1)，重点完整 §III-A–D、Fig.4–12、Theorem 1，及 §IV-A–D 的对照、修复与消融；该版本无方法附录 | 未取得论文实验的生成输入/原始轨迹；不能把网页示例或当前仓库当作所有实验的输出 |
| CPPL 同期公开代码 | 作者仓库首次提交 [838aab3，2026-05-17](https://github.com/SawyDust1228/CPPL/commit/838aab3d81237baefdd4807ce0d09a8146192efc) 的 frontend module/prompt/compiler、validator、CIRCT emitter 和 ALU 示例 | 此提交早于 v1 一天，但未核实它就是论文实验快照 |
| CPPL 后续公开代码 | 固定提交 [d7ebbb5，2026-08-19](https://github.com/SawyDust1228/CPPL/commit/d7ebbb5f4036ac57a768bc362996ab05e8c39b9f) 的相应入口及 worker、patterns、interpreter、工具 API、相关层次测试 | 后续代码不是 v1 已测能力的替代证据；未全面审计缓存、所有算子和所有代理路径 |
| HINT | [v2 官方全文](https://arxiv.org/html/2608.07625v2)、[7 页 PDF](https://arxiv.org/pdf/2608.07625v2)，完整 §3–4 方法、Fig.1–2、Table 1，及 §5–6；该版本无方法附录或 Algorithm 编号 | §4.2 指向的[作者匿名仓库](https://anonymous.4open.science/r/anonymous-project-612D/)未能取得可审计内容，因此没有代码 SHA、实现行号或完整 HINT SPEC 核验；不可据此声称仓库没有实现 |

下面分别标明论文事实、代码事实和推论。“未证”只限定此次材料和阅读范围，不表示领域内绝无该机制。源码均固定到以上 SHA，避免 main 漂移。

## 2. CPPL：哪些结构是构造保证，哪些父行为仍由模型决定

| 核查项 | 已证事实与定位 | 对当前问题的含义 |
| --- | --- | --- |
| 接口与实例绑定 | §III-A、Fig.5–6：函数签名给出端口/宽度，格式化模块调用给出实例和输入绑定，frontend 确定性展开。§III-B 明确先插 instance，再由模型生成其余操作。[论文方法](https://arxiv.org/html/2605.17892v1#S3) | 不只是实例名称提示；端口和部分 wiring 是程序构造 |
| 定理范围 | Theorem 1 证明 `Struct(H)=(V,E_h)` 与语法实例树同构；该投影不含 wiring。S-Conn 不改变投影。[§III-A](https://arxiv.org/html/2605.17892v1#S3.SS1) | 定理本身没有证明父输出如何按模式依赖 child；但不能据此忽略实际 frontend 的 wiring 绑定 |
| 同期具体实现 | `_split_instances` 根据输入引用是否已知区分 preplaced/deferred；前者由 `_instance_ops` 插入；后者精确比对 module/id/args，未满足则要求重发。[compiler.py L75–115](https://github.com/SawyDust1228/CPPL/blob/838aab3d81237baefdd4807ce0d09a8146192efc/cppl/frontend/compiler.py#L75)、[L174–221](https://github.com/SawyDust1228/CPPL/blob/838aab3d81237baefdd4807ce0d09a8146192efc/cppl/frontend/compiler.py#L174) | 在已读路径，程序固定 child 的存在和输入来源；并未预置全部父 mux 或运算 |
| 生成可见信息 | 同期 prompt 同时列全部父端口、logic docstring 和可引用的 child 输出，要求模型生成剩余逻辑和 output。[prompt.py L227–275](https://github.com/SawyDust1228/CPPL/blob/838aab3d81237baefdd4807ce0d09a8146192efc/cppl/frontend/prompt.py#L227) | 父层原始 a/b 并未被接口隔离移除；它们确实可用于其他操作 |
| 静态检查 | §III-C 的语法、宽度、覆盖、连接和组合环；同期 validator 的入口依次检查端口、SSA/终止、输出覆盖、实例和环。[validator.py L21–39](https://github.com/SawyDust1228/CPPL/blob/838aab3d81237baefdd4807ce0d09a8146192efc/cppl/ir/validator.py#L21)、[实例规则 L186–224](https://github.com/SawyDust1228/CPPL/blob/838aab3d81237baefdd4807ce0d09a8146192efc/cppl/ir/validator.py#L186) | 这些是具体、实质的合法性约束；所读入口没有定义独立 child-response 的 guard/response 检查 |
| refinement 与 lowering | §III-C 出错反馈，§III-D 将已生成的 operation graph 确定性降到 CIRCT；Fig.12 有 canonicalize/cse/hw-cleanup。论文也列出未用运算/实例 DCE。[§III-C–D](https://arxiv.org/html/2605.17892v1#S3.SS3) | deterministic lowering 保持所选操作的意义，不等于证明模型选对了所有父操作。不能把展开阶段的层次定理自动扩展到每次优化后的命名实例存在性 |

### 2.1 ALU 示例直接覆盖了模式选择与共享原始操作数

Fig.5 的 ALU 本来就要求：00 使用 Adder8 的结果，01 用 a/b 相减，10/11 用 a/b 做位运算。Fig.7 给出的实际 JSON IR 再用三个 mux 将 child sum 放到 00 分支；Fig.10、Fig.11 的 CIRCT/Verilog 展示相同组织。[Fig.5、7、10、11](https://arxiv.org/html/2605.17892v1#S3)

同期[官方示例 L12–22](https://github.com/SawyDust1228/CPPL/blob/838aab3d81237baefdd4807ce0d09a8146192efc/examples/cppl_demo.py#L12)也包含这组要求。**因此不能声称 CPPL 没考虑父层共享 a/b、没有表示条件性委托，或该公开示例发生旁路。** 模型产生的正确 mux 一经进入 IR，后端可直接按它发射 RTL；把整组 mux 固定下来更可以从构造上排除错误。

仍需区分：示例成功呈现的组织，与所有可通过前端合法性检查的 IR 都必然满足该组织，是不同命题。本轮没有向 CPPL 提交反例，也没有运行其 pipeline，因此不报告“CPPL 接受旁路”的结果。

同期实现的 `_make_stub_dicts` 为静态检查构造同签名、常零输出的 child stub，再与父 IR 一起 parse/validate/infer。[compiler.py L119–158](https://github.com/SawyDust1228/CPPL/blob/838aab3d81237baefdd4807ce0d09a8146192efc/cppl/frontend/compiler.py#L119)可直接核实这一点；此处的 stub 不是自由变量，也没有运行父输出的响应 scoreboard，不能仅凭“用了 stub”就把它等同当前额外响应检查。后续 patterns 的真实 dependency 执行则是另一条已实现的检查路径。

### 2.2 当前作者实现已增加功能执行与内部观测

不能将 v1 的实验描述推广成“CPPL 当前只能静态检查”。后续仓库有明确的 [Add interpreted module patterns 提交](https://github.com/SawyDust1228/CPPL/commit/892d264e71a03a30bc43a814a4a75b85ce1613ae)，与当前主版本相符：

| 后续代码事实 | 固定源码锚点 | 不能推到的保证 |
| --- | --- | --- |
| Case/Sequence 有 inputs、outputs、probes；内部 probe 可验证命名值 | [frontend/patterns.py L66–119](https://github.com/SawyDust1228/CPPL/blob/d7ebbb5f4036ac57a768bc362996ab05e8c39b9f/cppl/frontend/patterns.py#L66) | 不能把 probes 误读成任意覆盖 child 输出的 force |
| 候选先 parse/validate/infer，再执行 module patterns；真实 dependency IR 可用于层次仿真 | [worker.py L285–309](https://github.com/SawyDust1228/CPPL/blob/d7ebbb5f4036ac57a768bc362996ab05e8c39b9f/cppl/agents/worker.py#L285)、[层次测试 L534–561](https://github.com/SawyDust1228/CPPL/blob/d7ebbb5f4036ac57a768bc362996ab05e8c39b9f/tests/test_patterns.py#L534) | 不只是 external RTL test；也不因使用解释器就成为全域证明 |
| run_patterns 对 top inputs 执行 evaluate，再比较 outputs 并读取 peek_probe | [ir/patterns.py L71–142](https://github.com/SawyDust1228/CPPL/blob/d7ebbb5f4036ac57a768bc362996ab05e8c39b9f/cppl/ir/patterns.py#L71) | 已读执行路径检查正常层次行为和内部值，不是自由边界下的父响应 |
| evaluate 更新输入/时钟并计算真实子层，peek/peek_probe 是读操作 | [interpreter.py L132–192](https://github.com/SawyDust1228/CPPL/blob/d7ebbb5f4036ac57a768bc362996ab05e8c39b9f/cppl/ir/interpreter.py#L132)、[L428–463](https://github.com/SawyDust1228/CPPL/blob/d7ebbb5f4036ac57a768bc362996ab05e8c39b9f/cppl/ir/interpreter.py#L428) | 未核到在该 API 中将某 child response 解耦为独立输入的机制；不排除另加 harness/改写 IR 后可扩展实现 |
| preplaced/deferred 仍构造/核验实例，父剩余操作继续由模型写 | [worker.py L311–359](https://github.com/SawyDust1228/CPPL/blob/d7ebbb5f4036ac57a768bc362996ab05e8c39b9f/cppl/agents/worker.py#L311)、[prompt.py L254–303](https://github.com/SawyDust1228/CPPL/blob/d7ebbb5f4036ac57a768bc362996ab05e8c39b9f/cppl/frontend/prompt.py#L254) | 固定 binding 与正确模式下的语义委托不可互相替代 |
| 当前 runtime 提供工具、模式反馈和 repair；README 说明 retry 计数范围 | [README L54–145](https://github.com/SawyDust1228/CPPL/blob/d7ebbb5f4036ac57a768bc362996ab05e8c39b9f/README.md#L54) | 不能把此流程的最终成功当作无反馈首次输出 |

其 emitter 对 mux 和 instance 均有直接映射：[circt.py L345–349](https://github.com/SawyDust1228/CPPL/blob/d7ebbb5f4036ac57a768bc362996ab05e8c39b9f/cppl/codegen/circt.py#L345)、[L517–548](https://github.com/SawyDust1228/CPPL/blob/d7ebbb5f4036ac57a768bc362996ab05e8c39b9f/cppl/codegen/circt.py#L517)。可表达并确定性 lowering 正确父逻辑，是已实现能力；自动识别/审计任意 guard 下的自由边界响应，不由这两个函数单独建立。

### 2.3 CPPL 实验不能替代当前问题的直接证据

§IV-A：29 个 RTLLM 问题，每题 10 个 completion、报告 pass@1/2/5，允许最多 3 次 refinement；通过 Icarus/原 benchmark 单元测试评功能。§IV-D、Table IV 的消融是 CIRCT 优化对 AIG 节点数的影响。[实验全文](https://arxiv.org/html/2605.17892v1#S4)

这些不是条件性委托审计、父层重算比例或同信息责任卡实验。不能把其 pass@1 直接当“第一条无反馈模型响应通过率”，也不能把本项目的 C0/C1 称作 CPPL 重现或战胜 CPPL。

## 3. HINT：可执行父行为与约束后的 agentic lowering

| 核查项 | 论文已证事实与定位 | 未证部分及对照含义 |
| --- | --- | --- |
| 不只是结构草图 | §3、Table 1（PDF p.3）：persistent units/helpers、typed boundaries、ownership、state/control、sharing/reuse scope、schedule/resource/lowering obligations | 不能把 HINT 弱化成命名/类型提示；完整已验收 HINT 可固定大量真实父行为 |
| 父层确实有行为 | Fig.1（p.3）的 aes_step 显式含 st_cur 分支、RUN 下 round helper、next-state 与 commit；正文说完整 artifact 包含省略的 AES 数据逻辑 | 该图的 st_cur 是推进状态，不是任意业务 mode 的完整案例；图中还省略 request construction/write intents，不能据此推定共享原始操作数的所有路径规则 |
| 静态检查范围 | §3 末、§4.1 Stage 1：checker-enabled 流程检查许可形式/标签、类型引用、状态所有权与 commit、有界推进、实例/资源基数 | 未取得完整 SPEC/代码，不能判断其对重复算子、模式下 helper 使用或语义抵消的实际检测完备性 |
| 生成前冻结与前 RTL 验收 | §4.1 Stage 0–1、Fig.2（p.3–4）：验证材料先冻结；生成 HINT 后运行 reference/native 事务检查；适用门槛通过后才 lowering | 不是“结构合法就直接发 RTL”；已有明确可执行语义验收 |
| lowering 实现方式 | §3 说明是 agentic construction/lowering，而非普通确定性 passes；§4.1 Stage 2 由接受后的 HINT 及 lowering obligations 引导 RTL，并做 HINT–RTL 数据/事务时序共仿真 | 不能称 HINT 的整个 lowering 为确定性编译器；也不能仅因它使用 agent 就断言它会更改组织 |
| 内部结构保证边界 | §3 结尾（p.3）明确 HINT–RTL 比较检查 observable behavior/transaction timing，不声称 internal structural equivalence 的形式证明；架构变更回 Stage 1 | 普通功能共仿真不能升级成任意自由 child-response 关系证明；这也不否认其明确架构义务和实际组织审计 |
| 特定形式检查 | §4.1 Formal-checking scope（p.4）：Hif8_mul 有 Formality netlist 等价，其余依赖事务 regression/cosimulation | 普通 netlist 功能等价仍不自动检查额外自由边界合同；不能写 HINT 完全没有形式检查 |
| RQ1 与完整流程区别 | §5.1（p.5）：RQ1 不启用 HINT Lint/多代理；共享 20-revision 正确性预算；另有冻结后非修正 source audit 确认组织；RQ2 才用 checker-enabled 完整流程 | 既不能将完整 Lint 全归入 RQ1，也不能把 post-freeze audit 当修复或当形式定理 |

上述均可定位于 [HINT v2 §3–5](https://arxiv.org/html/2608.07625v2#S3)及 [PDF p.3–5](https://arxiv.org/pdf/2608.07625v2)。§5.2 另明确 Hif8_mul 是工程师写 HINT、Codex lowering 的 pilot，其余 controlled route 不应被统称手写模板实验。

**与当前问题真正相关的未证项：** 已读论文没有定义将单个 child response 解耦为自由 z 后，在 guard 内外分别比较父层全部受约束输出的具体规则，也未给出“父层保有原始操作数但不能重算指定职责”的专门检查算法。完整 HINT 可能已经通过固定父计算/绑定消除相关自由度；官方实现又未能核实。因此结论只能是“公开证据未建立此项检查”，不能写“HINT 必然允许旁路”“HINT 只查层次”或“当前方法验证了 HINT 从未处理的架构语义”。

## 4. 用一个区分构造澄清问题，而不冒充近邻失败

令 8-bit child 正常输出为 `s=wrap8(a+b)`。父层可构造：00 直接重算 a+b；01 用 `wrap8(s-2*b)`；10/11 仍 AND/OR；zero 从最终 res 计算。正常 child 下它与 CPPL Fig.5 的全部普通输出函数相同，child 又在 01 分支真实影响输出。该等式只需模 256 算术，不依赖隐藏输入。

若**另行明确承诺**自由边界规则“00 的 res=z、其余 mode 不受 z 影响”，上述构造同时违反 guard 内和 guard 外责任。这说明正常功能等价、实例/绑定存在、全局 live 或未优化依赖路径，并不在逻辑上蕴含该额外规则。内部正常值 probes 也不能单独分辨两个正常时内部值完全相同的实现。

这是手工分析，不是 CPPL/HINT 的实际接受结果。其限制包括：

- CPPL 已公开的正确 Fig.7 父 mux 本来满足这种响应；固定该 operation graph 就不产生反例。
- HINT 若接受后的父行为/绑定规则禁止此变换，合规实现不能自由选择此构造；需完整 SPEC/实现才能判定其验收路径。
- 将自由 z 当普通功能测试会产生不可能的内部值组合。它只能裁决事先公布的抽象响应合同，不得将合法普通优化一概判为功能错误。
- 它不证明某物理 adder 被唯一使用，不排除冗余算术，不证明面积、资源共享或综合后拓扑。

这一自由变量技术本身已有长期先例。Feng/Hu 2005 [§1、Fig.1–2，PDF p.1–2](https://www.cs.ubc.ca/~ajh/mypapers/2005FH.pdf)既说明把等价内部逻辑换成新 primary input，也明确自由 cutpoint 可能导致 false inequivalence。当前项目不能把 force、blackbox 或自由边界本身列为新算法。

## 5. 当前 checker 的真实重叠与剩余差别

当前公开对象是[三个新开发组合 profile](../../../../artifacts/codex-responsibility-cross-task-20261021-01/public-tasks.md)，不是旧完整 FPGA 任务的直接复用。[预先方案](../../../../artifacts/codex-responsibility-cross-task-20261021-01/plan.md)已限定 C0/C1 公开事实等价、首次生成无反馈；这与 CPPL/HINT 的已有修复流程是实验范围差别，不能自动成为新方法。

| 比较面 | 已有重叠 | 当前可区分的窄对象 / 限制 |
| --- | --- | --- |
| 结构及绑定 | CPPL 确定性 frontend；HINT typed hierarchy/ownership/resource commitments | 当前仅单目标的实际 module/output/type binding；不能宣传其结构覆盖比近邻更完整 |
| 功能检查 | CPPL 后续 executable patterns；HINT 前 RTL 和后 RTL 事务验收 | 当前也查普通函数，功能执行不是独有机制 |
| 模式/父行为 | CPPL ALU 的 mux；HINT AES 的 switch/helper/commit | 当前要求生成前把自由响应在 guard 内、guard 外和无关输出上完全写明；不是从“用某模块”自动推导 |
| 实现自由度 | CPPL 剩余 IR 操作由模型决定；HINT 接受完整架构后约束 lowering | 当前允许自由父 RTL，所以 checker 可审计实现是否保留所声明响应；若父 RTL 已固定，该差别可能消失 |
| 数学对象 | 近邻已约束程序/硬件语义，并做有限或特定形式检查 | 当前比较的是 `(普通输入,z) -> 全部指定输出` 的额外关系；范围小、单边界、comb，不能称通用架构正确性 |
| 证据 | 近邻论文有真实生成与多任务结果 | 当前[全宽六个手写控制资格](../../../../artifacts/responsibility-full-profile-qualification-20261021-01/results.md)证明该 revision 在这些控制上的有限辨识力，绝非模型收益或近邻反例；本轮未重跑 |

资格记录还明确：normal target 值、force/release、输入保持等已检查；所有声明中的每条连接、全部 leaf 局部域并未独立证明（results.md 第26行）。ALU/FIR 有所列有限域穷举，TD 只是采样。不得用“六控制通过”替代全域职责、每叶功能、全部 binding 或通用沙箱的证明。手工同 profile miter 等价即使成立，也不增加新颖性。

## 6. 应如何改进研究与主张

1. **放弃过宽定位。** 不再使用“首次在生成前固定结构”“首次验证架构语义”“实例保留即可保证职责”或“自由边界是新算法”。CPPL 已构造真实结构/绑定，HINT 已执行架构合同；它们不是只存在于提示里的弱基线。
2. **把对象写成附加合同。** 保留条件性响应这一可复核对象，同时公开 guard 外、全部输出、数值宽度/溢出及自由域。普通功能、额外 profile、结构检查、未验证项分开报告。合法优化不保持该 profile 时记 profile 不兼容。
3. **同信息对照要覆盖构造强基线。** 不能只比自然语言 C0。至少区别 CPPL 风格的固定接口/实例/绑定加自由父体、相同事实的责任卡、固定父响应/完整 typed IR。第三者本可从构造排除反例，应承认，不应故意不给它相同 guard/response 信息。HINT 同类完整可执行父行为对照若未实现，只能称启发式对照，不能挂 HINT 名字。
4. **先裁决检查的边际，而非重造 IR。** 在相同保留自由度下，比较普通功能、实例/绑定、优化后存在/全局 live、正常内部 probes 与额外响应检查各自排除了什么；同时保留合法输入交换和对合同相容的重写。不以理论可表达替代作者实现核验，也不把本地手写控制标为近邻输出。
5. **当前 C0/C1 只回答表示问题。** 即使责任卡改变首次通过情况，也只支持此 profile、模型和有限任务上的表示效应。若没有差异，应如实报告；若固定父控制同样成功，不能转称超过 typed IR。工程价值、审计增益和新生成算法是三个不同主张。
6. **保留明确的停止条件。** 若完全相同的公开合同和自由度下，普通既有构造/检查已覆盖所有责任区分，或需要把完整参考父实现写进卡才能得到增益，则当前材料不足支撑独立生成方法核心。可以留下可复用审计工具/任务资格结果，不用措辞制造创新。

建议当前描述：**“对首次生成的层次 RTL，研究事先显式声明的条件性模块响应合同的表示和有限 conformance 审计，并测量其相对于结构/功能检查及固定父构造的边际。”** 这是待裁决的研究问题，不是已确认的创新贡献；近邻完整实现未读部分、实际模型效果和适用任务广度仍保留为未决。
