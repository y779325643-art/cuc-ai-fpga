# VeriRefine 与 EQY 方法深审：责任合同的真实近邻

日期：2026-10-21。状态：只读来源审查完成；没有复现、模型调用或 HDL 执行。只新增本报告，不改候选、检查器、稿件或已有六份全宽控制。

**判断：不能把现方案定位为新的切点检测能力。EQY 的官方源码和示例已经直接处理“正常等价、独立内部切点下响应不同”的情形。VeriRefine 也已经把逐信号行为、优先 guard/action 和规范出处变成生成前的显式承诺。仍可检验的区别，是用少量局部、预声明的响应合同约束实际生成 RTL，同时保留其余父行为的表达自由；这需要与足够强的 IR/构造/切点基线比较，当前不能据此确认方法原创性或 SCI 充分性。**

## 1. 阅读与来源边界

| 来源 | 本次实际核对范围 | 版本与限制 |
| --- | --- | --- |
| [VeriRefine 官方 HTML](https://arxiv.org/html/2607.18519v1) | §3.1–§3.5.2 完整方法，§4.1/§4.3/§4.4，Tables1–3，公式、JSON 样例与图注；结合引言/相关工作辨认自述范围 | arXiv:2607.18519v1，2026-07-20；正文没有编号算法。本文使用章节/表号，不虚构 Algorithm1。 |
| [同版本官方 PDF](https://arxiv.org/pdf/2607.18519v1) | 13页文档的文本、末尾结束位置与附录/代码可用性线索 | 末尾为参考文献，未见独立附录。截图服务未能稳定返回可审阅图像；图形内部细节未作完整视觉核对，不以图注替代隐藏的实现细节。未读取不存在于已取文档中的补充材料。 |
| VeriRefine 作者实现定位 | 官方论文/摘要页的链接；公开查询 `"VeriRefine" "github"`、`"A Progressive Approach to Synthesizable RTL" code`、`"Xiangfei Kong" "VeriRefine" code github`；GitHub repository search `VeriRefine` 和 code search `gca_expression spec_citation` | 未定位到可归属原作者的实现。命中的第三方阅读笔记/论文转存未作为实现证据。这个结果是本次检索限制，不能写“作者没有代码”或“实现肯定不检查语义”。 |
| [EQY 配置](https://yosyshq.readthedocs.io/projects/eqy/en/latest/config.html)、[产物](https://yosyshq.readthedocs.io/projects/eqy/en/latest/outdir.html)、[X语义](https://yosyshq.readthedocs.io/projects/eqy/en/latest/xprop.html) | gold/gate、匹配、collect/partition、bind/merge/amend、实际中间产物与证明状态；明确二值任务与 gold 的三值 safe-replacement 语义差别 | 官方 latest 文档，检索日读取；不是已安装本地 EQY 版本的运行资格。 |
| [EQY 官方源码](https://github.com/YosysHQ/eqy/tree/fb8b21160297b3e66bf94f3c24f8a8bf1cd3fd51) | `src/eqy_partition.cc` 中匹配位到 PI、信号/驱动复制、miter 生成；`src/eqy.py` 匹配和 SAT/SBY 脚本生成；`examples/simple/ex_bind.*` 全文 | 固定 commit `fb8b21160297b3e66bf94f3c24f8a8bf1cd3fd51`；源码相关区段阅读，没有编译或运行。不是整仓库形式化审计。 |

这不是系统综述。没有外传项目源码或正在生成的候选；公开检索只包含文献名称、作者和公开机制标识。本文的“已证”指原文或源码直接支持对应的描述，不表示本项目已复现其效果。

## 2. VeriRefine：必须分开的三层保证

以下事实定位到[官方 v1](https://arxiv.org/html/2607.18519v1)相应章节；对实现或逻辑后果的判断单列，避免把论文声称自动升级为代码证明。

| 层次/问题 | 原文可直接支持的内容与 locator | 已证、未证及对本方案的含义 |
| --- | --- | --- |
| ASTF 的含义 | §3.2 定义硬件类别及按优先级排列的 guard/action/provenance；§3.3.2 把它们放入逐 driven-signal 的闭合 JSON 表示 | **已证：表示包含行为语义，不只是端口类型或声明图。** 在其表示范围内，父信号的值规则也可预先给定。不得写“近邻只检查格式”。 |
| 规范锚定 | §3.3.1–§3.3.3：出处、覆盖、声明/表格一致性、FSM 和硬件规则分层审计 | **已证：有生成前语义审计目标及部分具体检查。未证：任意自然语言出处对 guard/action 的形式蕴含证明。** 字符串确实来自规范，与该句足以推出该动作，是不同命题。源码未取得，不能断言全部审计怎样实现。 |
| 实现阶段 | §3.4、Table3：ASTF 作为代码生成输入；逐条 GCA 保真为生成规则；明确列出端口、高阻态、编译等确定性门控 | **已证：受约束的实现流程。未证：对每条生成 RTL 的 GCA 语义执行独立等价证明。** 不能把提示中的保真要求等同于已执行的语义检查，也不能断言作者实现没有额外检查。 |
| 生成后功能证据 | §3.5.1：生成刺激、确定性组装测试平台并比较输出；§3.5.2：区分 ASTF/RTL 问题并路由修复 | **已证：生成后的可执行功能检查及修复。** 所述比较不自动等于任意内部自由值下的局部响应证明。 |
| 初次生成 | §4.1、§4.3：VeriRefine-Direct 移除 Verification & Debug 修复环 | **已证：不能靠“本方案无反馈、首次生成”单独区别于它。** 对其生成前审计或实现门控的重试不能仅凭 single-pass 标签推断为零调用。 |
| 结构范围 | §3.4 Table3 的 self-contained 规则要求不实例化外部子模块 | **已证：原文工作流与本项目固定多模块边界不完全同域。** 这不能证明其 IR 不能扩展到层次结构；移植后应标“VeriRefine式适配”，不能冒称原框架复现。 |

这里的关键区别不是“它有没有 semantics 一词”，而是检查的关系：规范→ASTF 的解释是否合理、ASTF→RTL 的实现是否忠实、以及内部边界被独立释放后父上下文是否遵守响应，分别是三项义务。

**参考 IR 足不足以固定父行为？** 可以足够，但须说明使用方式。完整 ASTF 若经可信的逐条编译，或对每条父赋值在独立输入下做语义核对，就能施加很强的父行为限制；它是应认真比较的强替代方案。相反，只比较闭合 ASTF/RTL 的正常顶层输出，不必然检出重算：当真实子输出始终等于 `f(x)` 时，`parent(child)` 与 `parent(f(x))` 可能完全等价。要区分它们，需保留该局部表达/边界为独立变量，或依靠严格构造保证。这个逻辑判断不依赖作者是否使用了 cutpoint 这个词。

## 3. EQY：自由切点是实际实现能力

源码定位均固定在上述 commit，以下为实现阅读，未执行。

| 机制 | 精确代码与文档位置 | 对应含义 |
| --- | --- | --- |
| 找到实际对象并建立匹配 | [`eqy.py` L581–629](https://github.com/YosysHQ/eqy/blob/fb8b21160297b3e66bf94f3c24f8a8bf1cd3fd51/src/eqy.py#L581) 的 `match_ids`；[`eqy_partition.cc` L164起](https://github.com/YosysHQ/eqy/blob/fb8b21160297b3e66bf94f3c24f8a8bf1cd3fd51/src/eqy_partition.cc#L164) 的 `add_match` 系列 | 匹配实际编译设计中的位/线/单元，处理别名和常量；不是只信任候选写出的名称清单。匹配配置正确性仍是使用者责任。 |
| 真正产生独立 partition 输入 | [`eqy_partition.cc` L571–625](https://github.com/YosysHQ/eqy/blob/fb8b21160297b3e66bf94f3c24f8a8bf1cd3fd51/src/eqy_partition.cc#L571)：匹配位在合适条件下进入 `inbits`，`isinput` 时停止沿驱动追溯；L878–901 创建实际 input ports | 这是切断生成关系后验证下游上下文的具体实现，不只是“通用求解器理论上能表达”。`bind` 会阻止相应内部线变成 PI，不能误当“绑定目标身份”的同义词。 |
| 避免把切断驱动重新接入 | [`eqy_partition.cc` L825–855](https://github.com/YosysHQ/eqy/blob/fb8b21160297b3e66bf94f3c24f8a8bf1cd3fd51/src/eqy_partition.cc#L825) | 在复制单元连接时，切点输入对应的驱动输出另建信号，避免仍驱动独立 PI。具体别名处理有额外逻辑，不能仅凭一个变量名推断完整效果。 |
| 同一自由值进入两侧上下文 | [`eqy_partition.cc` L955–973](https://github.com/YosysHQ/eqy/blob/fb8b21160297b3e66bf94f3c24f8a8bf1cd3fd51/src/eqy_partition.cc#L955)、L1075–1152 | 为 gold/gate 建对应 PI；miter 把同一 PI 接到两侧并断言所选输出。`crossbits` 是另一种导入关系，具有额外 equality assumption，不能把所有 cross point 都泛称无约束自由输入。 |
| 恢复上游关系 | [配置 Collect/Partition](https://yosyshq.readthedocs.io/projects/eqy/en/latest/config.html) 的 `bind`/`merge`/`amend`；[`Partition::import` L474起](https://github.com/YosysHQ/eqy/blob/fb8b21160297b3e66bf94f3c24f8a8bf1cd3fd51/src/eqy_partition.cc#L474) | 某些配置会重新引入上游逻辑或 gold 定义，从而缩小自由域。本方案若以任意 z 为公开合同，不能不检查配置就把这种恢复称为同一义务。 |
| 完成证明及保留证据 | [`eqy.py` L894–904](https://github.com/YosysHQ/eqy/blob/fb8b21160297b3e66bf94f3c24f8a8bf1cd3fd51/src/eqy.py#L894) 的 SAT 脚本、L936–948 的 SBY 路径；[Output Directory Format](https://yosyshq.readthedocs.io/projects/eqy/en/latest/outdir.html) | 真正对 partition miter 的断言执行证明，保留匹配、partition 输入输出、脚本、日志和状态。本文没有运行这些命令，不能报告“EQY已检出本项目候选”。 |

### 一个比抽象类比更直接的近邻

官方 [`examples/simple/ex_bind.sv`](https://github.com/YosysHQ/eqy/blob/fb8b21160297b3e66bf94f3c24f8a8bf1cd3fd51/examples/simple/ex_bind.sv#L1) 定义共同的 `X=A^B`、`Y=B^C`；gold 的 `Z=X^Y`，gate 的 `Z=A^C`。二者在正常关系下等价，但令 X/Y 成为独立 PI 后，gold 的 Z 与直接重算的 gate Z 不再对所有组合相同。对应 [`ex_bind.eqy`](https://github.com/YosysHQ/eqy/blob/fb8b21160297b3e66bf94f3c24f8a8bf1cd3fd51/examples/simple/ex_bind.eqy#L11) 设置 `bind X`、`bind Y`，使相关上游关系纳入后续证明。

这是源码可检查的关系和代数分析，**不是本次运行得到的 PASS/FAIL**。但它已经足以否定“成熟等价工具只能检查正常顶层、无法暴露重算旁路”的论述。官方工具把独立切点过强造成的问题作为需配置处理的情况；本方案把特定独立响应明确声明为合同。区别在义务的选择、来源和工作流，并不产生新的求解能力。

另须遵守 EQY 的 [safe-replacement/X 语义](https://yosyshq.readthedocs.io/projects/eqy/en/latest/xprop.html)：gold 中的 X 可作为 don't-care。若把 z 错写成未定义常量而非受检的已定义 PI，可能无意弱化合同。本项目公开组合 profile 只覆盖已知二值；将来公平移植应保持相同二值域、signed/wrap/sat 数学和明确的输入/切点映射。

## 4. 与现方案重合和未闭合的差异

| 可主张项 | 裁决 | 需要的证据或改写 |
| --- | --- | --- |
| 显式 guard/action IR、生成前审查设计意图、出处锚定 | **已有强重叠**：VeriRefine | 不能作为独立原创点；引用并说明为何只给局部义务而不完整规定每条父赋值。 |
| 自由内部值、实际切点、miter/partition 区分闭合等价与局部响应 | **已有且有源码直接例证**：EQY | 不得声称新的检测算法或以前工具无法检查。现有[独立手工 miter](../../../../artifacts/responsibility-manual-miter-20261021-01/results.md)也应作为同义务的强核对。 |
| 把特定架构承诺预先写成局部响应合同，生成后自动绑定其实际 RTL 目标 | **可能是工作流/工具增量；尚未证成方法独创** | 必须展现比“用户写 assertion + 标准切点工具”少了哪些人工步骤、引入了哪些可验证保证；不是单靠阶段顺序不同。 |
| 不给完整父 ASTF，保留等价实现和 guard 外父逻辑的自由 | **可检验的设计选择** | 需先定义自由度和合法实现族，再确认检查器允许它们，且只拒绝公开合同确实禁止的情况。完整 IR/严格构造更强不构成其缺陷，要比较成本和适用范围。 |
| 初次生成、无工具反馈修复 | **不是充分区别**：VeriRefine-Direct 已提供相关条件 | 同调用预算与信息边界下比较；不得用 full VeriRefine 修复轮数混淆其 Direct 条件。 |
| 当前 profile 能发现普通功能检查放过的强合同违约 | **已有六份手写控制的有限资格支持** | [全宽资格](../../../../artifacts/responsibility-full-profile-qualification-20261021-01/results.md)是工具开发控制，不是模型自然错误率或实际任务总体收益。TD 仅64输入×19探针；不得写全域形式证明。 |

特别注意：完整 ASTF 规定的是逐信号逻辑语义，并不自然等同固定某一物理网表；本方案的“自由”也不能只用不同字符串度量。普通重算可能是合法优化，只有用户明确接受的抽象响应义务才使其在本 profile 中构成违约。

## 5. 应优化的方案与强对照

以下为后续设计建议，不是已实施内容，也不授权新增运行。

1. **把贡献对象收窄成局部义务的可审计降解。** 同时保存合同的语义、公开依据、guard、干预域、响应和不变输出、实际实例/端口/位映射及独立输入完整性。绑定失败、干预无效、域未覆盖与真的违约分别报告。不要把目标存在检查扩称全部结构已验证；当前 checker 不核全部所需实例连接，也不证明每个叶模块全局函数。
2. **先明确“允许改变什么”。** 至少定义一组正常功能且合同兼容的变体：合法输入交换/内部别名、等价父表达、无关 raw-input 输出、guard 外运算。再定义确实违反强合同的重算或错模式传播。严禁由某次候选表现倒改合同；要检查是否误拒合法优化和是否只测到普通功能错误。
3. **用通用证明后端做义务对齐，而不是把模拟器 force 当贡献。** 后续可将公开响应数学降为一个显式 z-input 的 shadow context；从实际 RTL 分离同一边界，使用手工/标准工具 miter 比较。应检查保留的 PI 和 partition、禁止无意 `bind`/`amend` 恢复真实子函数，并核查宽度、有符号数及 X 语义。本文没有实现或运行该 adapter。
4. **把“少规定”变成可测代价，而非空泛优点。** 与完整信号 IR 相比，统计用户/开发者需提供的规则数量和语义范围、适配代码、人工映射/审阅时间、失效/unknown 类型；若本 profile 为了给每个输出写精确响应已接近完整父实现，应直接报告这种退化。

| 强对照 | 它回答什么 | 公平性限制 |
| --- | --- | --- |
| 同一 g/response/domain 的独立手工 cutpoint miter | 自动检查是否等价于成熟手工义务；不是证明新检测能力 | 预期结论一致；出现不一致须判工具/域差异，不能当方法胜利。现有 ALU4 手工 miter 只资格相应旧控制。 |
| 同一公开合同驱动的标准 EQY/形式 miter 适配 | 自动绑定与义务生成比标准流程节约了什么；能否得到一致判定及更强覆盖 | 本次仅源码核查、未移植或运行；必须记录 cutpoint/partition，不能直接用默认 normal-equivalence 配置充当弱对手。 |
| VeriRefine式完整 ASTF + 确定性/独立验证的 lowering | 局部合同是否在较少限制和较低建模代价下足够 | 作者代码未取得，不能称正式复现；多模块适配要公开。只用提示要求逐条保真，会把后端检查差异混入 IR 表达差异。 |
| 严格父模板/受控 leaf 输出 | 构造保证与生成后检查的代价和允许实现族 | 其防旁路可能更强；不要假装它也能自由生成相同父代码。报告约束范围不同及人工模板成本。 |
| 普通功能 + 实际层次/端口绑定 + 依赖/DCE 检查 | 明确只查正常关系或存在性时漏了什么 | 作为消融可用，不能作为唯一强 baseline。不得将增加局部强合同后多拒绝的数量全部称“功能改善”。 |

## 6. 可反驳的贡献陈述和继续条件

候选陈述：**“对用户预先接受的局部组合响应承诺，提供从公开合同到实际生成 RTL 边界的可审计绑定与独立检查；在不完整规定父实现的条件下，测量其与完整信号 IR/严格构造/标准切点验证相比的建模代价、合法实现接纳范围及违约检出一致性。”**

这是一个可被数据否定的软件方法/审计问题：若标准工具的等价移植需要同样或更少工作，完整 ASTF/严格构造也在同代价保留所需自由度，或者局部合同基本等于手写完整父函数且无真实使用收益，就没有证据支撑较强的方法贡献。反之，可靠减少义务编写/绑定负担、接纳明确的合法变体、并在真实初次生成样本中暴露普通检查遗漏的承诺违约，才可能支持有边界的工具或实证论文。

**建议继续已有有界研究，改以“合同检查工具 + 实证审计”作为当前最稳定位；不再把自由切点或 guard/action 本身包装成方法新颖性。** 若坚持新的方法核心，须先补上相对完整 ASTF 和标准切点流程的实质代价/自由度证据。此次近邻审查既没有证明“整个协议零增量”，也没有证明“未找到相同组合所以原创”；更不能给出足够 SCI/SCIE 的结论。

现有六份全宽控制、手工 miter 和其他模型样本是不同证据层。本次没有读取正在生成的模型候选、计算其通过率或根据其结果调整上述判断。
