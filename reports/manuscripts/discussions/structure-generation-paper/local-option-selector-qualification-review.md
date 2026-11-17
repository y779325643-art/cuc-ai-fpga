# N19前置局部合同选择器：独立源码与封存资格审计

日期：2026-10-21。性质：开发资格的独立只读审计记录，不是正式模型实验、RTL证明或新方法验收。本报告整理此前对冻结源码及封存输出的审计；本次仅复读原manifest、ledger、summary并核文件哈希，没有重跑入口、模型、HDL或solver。唯一新增文件是本报告，既有代码、fixture、运行原件和论文正文均未修改。

**限定结论：通过本轮源码/封存一致性审查，未发现会将已审错误组合认证为正确、以规范式不等直接反驳、或把保守区间不足冒称实际溢出的实质问题。** 实际完成的是2个Python资格入口、39项开发检查，以及4个FIR和6个TD手工数学组合的处理。认证只针对声明的局部数学摘要及其组合；没有生成RTL，也没有证明任何模型body实现该摘要。

## 1. 冻结对象、实际执行与证据身份

审计对象位于[隔离artifact的README](../../../../artifacts/responsibility-local-semantic-selector-prototype-20261021-01/README.md)。[prepared-manifest.json](../../../../artifacts/responsibility-local-semantic-selector-prototype-20261021-01/prepared-manifest.json)记录冻结时间`2026-10-21T19:01:29.4121460Z`，包含10份代码、fixture、预期、说明和公共数学副本的哈希；两入口均在冻结之后启动。审计时仓库为`develop`、HEAD `e20dfd2ce46c5690767e30cb629fb5c58aff073a`，已有大量用户修改保持原状。

[run-ledger.json](../../../../artifacts/responsibility-local-semantic-selector-prototype-20261021-01/run-ledger.json)与[results-summary.json](../../../../artifacts/responsibility-local-semantic-selector-prototype-20261021-01/results-summary.json)一致记录：最多2个资格Python进程，每个外部上限30秒，实际2/2完成，退出码均为0，无重试、无未跑入口、无模型/HDL/SAT/API进程。实际命令由collector执行，审计者没有执行以下入口。

| 已执行入口 | 封存实际耗时 | 结果及可追溯原件 |
| --- | ---: | --- |
| `python -B demo.py` | 0.2517494秒 | [receipt](../../../../artifacts/responsibility-local-semantic-selector-prototype-20261021-01/results/demo.receipt.json)、[stdout](../../../../artifacts/responsibility-local-semantic-selector-prototype-20261021-01/results/demo.stdout.log)、[全部组合结果](../../../../artifacts/responsibility-local-semantic-selector-prototype-20261021-01/results/demo-results.json)，状态`passed` |
| `python -B regression.py` | 0.2879695秒 | [receipt](../../../../artifacts/responsibility-local-semantic-selector-prototype-20261021-01/results/regression.receipt.json)、[stdout](../../../../artifacts/responsibility-local-semantic-selector-prototype-20261021-01/results/regression.stdout.log)、[39项检查](../../../../artifacts/responsibility-local-semantic-selector-prototype-20261021-01/results/regression-results.json)，状态`passed` |

这两个耗时只是各一次资格进程的封存读数，不能用于统计加速或端到端省时主张。39项检查不是39份候选模型输出；10个demo组合也不是10个模型样本。summary记载运行前后冻结输入未改变；本审计另外直接核对了下表所列文件哈希。

## 2. 可信target与候选的实际边界

[selector.py](../../../../artifacts/responsibility-local-semantic-selector-prototype-20261021-01/selector.py) L175–190使用`select(trusted_spec, candidate_pool)`的两个独立调用者输入：

- 可信spec含顶层输入/输出类型、完整`normal`函数、证明profile与预先给定的公共反例探针。候选pool只允许`task_id/groups/parent`三个顶层字段，不接受候选覆盖`normal`、`compatible`或certifier。
- [trusted-specs.json](../../../../artifacts/responsibility-local-semantic-selector-prototype-20261021-01/trusted-specs.json)与[candidate-pools.json](../../../../artifacts/responsibility-local-semantic-selector-prototype-20261021-01/candidate-pools.json)是分别冻结的人工fixture，均非LLM输出。候选标签和option名称没有正确性权威。
- [fixture_io.py](../../../../artifacts/responsibility-local-semantic-selector-prototype-20261021-01/fixture_io.py)读取冻结manifest并核代码/fixture哈希；可信spec所指[public-math-source.md](../../../../artifacts/responsibility-local-semantic-selector-prototype-20261021-01/public-math-source.md)是已有公开数学任务文件的字节副本，来源路径与SHA保留在manifest。它不使此前其他运行获得追溯冻结资格。

这是API和文件管理上的信任分离，不是密码学认证，也没有实现从任意自然语言原文自动证明`normal`正确。调用者仍负责真正冻结、保护与正确编写可信spec；不能让候选自己提供“可信normal”后引用此API宣称独立认证。本轮探针也是公开、固定输入，不是用隐藏评价挑选结构。

## 3. 已审数学规则与判词

| 核查面 | 实际源码位置及审计判断 |
| --- | --- |
| 精确算术/编码 | `selector.py` L46–87：AST仅支持整数add、mul、正整数字面分母的floor、显式sat和signed wrap。Python整数中间值不隐式按端口宽度截位；负数floor不是向零截断。只有AST中的wrap产生相应signed二补码整数。 |
| 区间与精确仿射界 | L90–113：保守interval越界后尝试`linear`的精确仿射上下界。仿射界若证明真实违反独立局部ABI，附可回放赋值并将输入池判`invalid_input`；不能把保守界越界当实际反例。 |
| 范围未证 | L115–116、L256–268：非线性等情形仍不能证范围时记`range_unproven`，仅使用该option的组合UNKNOWN。可信函数或parent范围未证则阻止全部组合认证。parent检查在L225使用`can_refute=False`，避免拿独立中间端口范围内、实际不可达的赋值判原组合非法。 |
| canonical认证 | L129–148、L241–248：整数加法结合/交换、常数归并，乘法交换及0/1归一化保留精确语义；sat、floor、wrap位置保留。canonical相同是充分认证条件，不把其不相同当不等价证明。 |
| FIR模线性认证 | L150–173：仅在双方显式最终wrap位数相同时，比较内部线性系数与常数模`2^bits`的一致性。该规则证明当前完整类型域上的数学编码结果，不借用有限探针作全域证明。 |
| 反驳与UNKNOWN | L249–254：未取得全部输出证书时，用预定公共输入直接计算可信函数和实际闭包；有真实输出差异才`refuted`，否则`unknown`。不把规则不完备写成数学不等价。范围未证的组合在此前已保守记UNKNOWN。 |

冻结[regression.py](../../../../artifacts/responsibility-local-semantic-selector-prototype-20261021-01/regression.py) L78–98及其结果包含两类不同控制：canonical差异但公共探针不反驳时UNKNOWN；`x+(-x)`经精确仿射界认证，而`x*x+(-x*x)`保守范围未证，仅该option组合UNKNOWN，独立零值option仍可选。后者数学上确实为零，但本原型没有相应非线性范围证明，未误标非法。

这是对列明实现与控制的静态审查，不是用39项检查形式证明整个Python程序健全。更广的代数等价、非线性范围和所有合法编码不在当前规则覆盖内；UNKNOWN应保留为方法边界。

## 4. 输入验证、组合限额与完整记账

`selector.py` L18–63、L175–226对未知/缺失字段、未知变量、ABI类型不匹配、漏绑定、循环、重复ID等进行拒绝；`integer`使用精确`type(value) is int`排除bool，JSON载入的`object_pairs_hook`拒绝重复键。验证还限制位宽、端口数、AST节点/深度、字面量与展开后的表达式。

L217设置完整笛卡尔积上限64；L274对通过输入验证且未超过该上限的池逐一保留组合记录，不只输出被选者。实际无认证组合时返回`no_certified_solution`；这既可能是全被反驳，也可能含UNKNOWN，均不等于全局架构不可实现。空option池返回`empty_pool`，不补池、不回退、不重采样。结构/语法错误或已证明的局部范围错误会在验证阶段将整个输入池拒绝，这一点不等于逐组合语义反驳，也不能从其空records推导不存在合法架构。

39项封存检查覆盖上述相关正负控制、64上限之外的拒绝、空池、全无认证解、排序并列、显式早wrap反例等。它们只证明这些已执行控制取得预定结果，没有穷举所有非法JSON、输入结构或完整程序状态。

## 5. 实际10组合状态与合法重算保留

[demo-results.json](../../../../artifacts/responsibility-local-semantic-selector-prototype-20261021-01/results/demo-results.json)保留以下全部状态；[expected.json](../../../../artifacts/responsibility-local-semantic-selector-prototype-20261021-01/expected.json)在运行前已冻结相应预期。表中名称是fixture身份，不是认证依据。

| 任务/索引 | 组合 | 实际状态 |
| --- | --- | --- |
| FIR `[0,0]` | P0/Q0 | certified，选中 |
| FIR `[0,1]` | P0/Q1 | refuted |
| FIR `[1,0]` | P1/Q0 | refuted |
| FIR `[1,1]` | P1/Q1 | certified |
| TD `[0,0]` | P_E/C_E | certified，选中 |
| TD `[0,1]` | P_E/C_D | refuted |
| TD `[0,2]` | P_E/C_R | certified |
| TD `[1,0]` | P_D/C_E | refuted |
| TD `[1,1]` | P_D/C_D | certified |
| TD `[1,2]` | P_D/C_R | certified |

FIR合计2 certified、2 refuted、0 unknown；TD合计4 certified、2 refuted、0 unknown。总计10组合中6认证、4真实输入反驳、0未知；这不与regression中的专门UNKNOWN控制合并成模型通过率。

FIR交叉组合在公开输入`x0=0,x1=1,x2=0`上将正确filtered `−2`变为`−1/−3`。TD交叉组合在`reward=0,next_value=16,gamma=16,value=0,alpha=8`上将正确U `8`变为`16/4`；完整R/E/U均按可信函数保留在闭包和见证记录。

C_R利用额外可用的R/value/alpha重算原E/D，不使用桥b，仍符合当前完整函数与接口要求。因此两种producer搭配C_R均认证，未凭“期望复用桥”增加禁止重算规则；`regression.py` L27–29也单独检查两组合。不能为让选择器显得必要而删去这些合法组合。选中规则为option零基索引和最小、再按索引元组字典序，排名不是校准的成功概率或PPA指标。

## 6. 已有强控制与尚待面对的零模型编译

`selector.py` L285–294的`complete_closure_control`将同池逐项展开为完整数学闭包，仍调用相同的`record`和可信certifier。demo核对其10项状态与选择器一致。这是同信息、预期等价的表示控制，**不是独立证明后端、独立功能oracle或速度对照**；不得拿两者一致作双重独立认证。

L296–301的`direct_contract_control`按预定索引直接取结构，验证索引后使用同样的认证路径，不搜索、不调用模型、不发射RTL。demo已有FIR P0/Q0、TD P_E/C_R的直接数学合同构造，并均获认证。其存在说明当前不要求为了得到一个合法组合必须生成局部候选池；不能把这个已有控制写成尚未面对的弱假想。

进一步，可信输入已经给出完整`normal` AST、类型和编码。**零模型的精确数学编译/普通AST outlining是必须面对的强端到端基线**：它可能固定返回任一允许分解并直接实现数学函数，省去规划甚至行为调用。公平比较需要共享输入，并计入前端、模板、库和新任务适配成本；不能只给编译器更强的人工AST而将该工作隐藏，也不能在两者都拿完整AST时忽略这个基线。

主审本轮通知的新编译器仍在准备，本N19证据包没有其已执行资格结果；本报告没有验证或重跑该新编译器，**不能将其写为已通过**。当前已经完成的是数学合同选择/认证与直接合同控制，而非完整AST→RTL编译。标准工具或同池控制得到相同答案，不自动否定系统贡献；但目前没有实际LLM池、交接工时或端到端成本证据支持新协议优于这些强控制。

## 7. 关键SHA256与审计范围

下列SHA由本审计只读计算文件哈希并与已读封存对象核对；这是文件身份验证，没有启动任何资格入口。

| 文件 | SHA256 |
| --- | --- |
| [prepared-manifest.json](../../../../artifacts/responsibility-local-semantic-selector-prototype-20261021-01/prepared-manifest.json) | `628b7d14a6eee3e3a88357a9e1a153dfc994979c5c23ff5bd8ec2be808b56156` |
| [selector.py](../../../../artifacts/responsibility-local-semantic-selector-prototype-20261021-01/selector.py) | `c57209050974a194c1532d3eb88d0965a4de4e3527aaa902904d528ac6b326de` |
| [run-ledger.json](../../../../artifacts/responsibility-local-semantic-selector-prototype-20261021-01/run-ledger.json) | `7bf1746f523dd94248eb050bf01f1453e760fd29a539fb8abfaf70b828dc7b56` |
| [results-summary.json](../../../../artifacts/responsibility-local-semantic-selector-prototype-20261021-01/results-summary.json) | `dfe5e3390770e42faffd7538e4ae3153435157612d4cc63e06c0de5297f7ed49` |
| [demo-results.json](../../../../artifacts/responsibility-local-semantic-selector-prototype-20261021-01/results/demo-results.json) | `28f546183a70b2a932e458ad17ae2f17eed0d104d343287eb84d4f54aaf0c3eb` |
| [regression-results.json](../../../../artifacts/responsibility-local-semantic-selector-prototype-20261021-01/results/regression-results.json) | `3ba82011038c3fc90c5930653f507ea4a29f90597a0505e5a44e83f8b9f77eae` |

本报告沿用`paper-review-audit`的限定review程序，只读已冻结源码、manifest、fixture、collector及封存结果；没有新增模型/HDL/solver或Python资格运行，没有外部查新。实际信任分离、精确摘要组合与保守判词获得本轮限定审计支持；RTL发射、生成body遵约、完整功能工具证明、模型池必要性、成功率/成本改善、正式研究资格与方法创新均未由本证据包建立。
