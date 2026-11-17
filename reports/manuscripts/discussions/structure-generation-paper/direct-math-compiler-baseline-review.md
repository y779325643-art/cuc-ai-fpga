# 完整数学输入的直接编译强基线

日期：2026-10-21。N20开发资格审查，非正式研究结果晋级。本文先于执行记录解释规则，现补录实际完成结果；规则保持原意。本轮不新增被测模型调用，不修改旧候选、评价器、任务评分或稿件正文。

## 输入与比较对象

[N19可信输入](../../../../artifacts/responsibility-local-semantic-selector-prototype-20261021-01/trusted-specs.json)已逐输出包含完整normal AST、输入输出位宽及signedness。FIR的wrap与TD的floor，以及E、D、U三处sat都已经明确。把自然语言转为这份可信目标的成本尚未测量；候选协议与本基线必须获得相同输入，不能只向协议免费提供完整数学，再让基线从裸自然语言起步。

用户允许少量保持顶层函数、开放分解/接口的变体。本基线因此采用每个输出一个非空算术helper，父层接线，允许合法重算。FIR为两个helper，TD为三个；它不承诺旧公开文档中的命名模块、特定切点自由响应、共享资源或固定拓扑。旧责任合同与本轮normal-only变体的验收不可互换。

N30补明确切来源身份：上述TD目标是`public-tasks.md`的组合TD8（外部输出R/E/U），不是更早`codex-native-td-pilot-20261021-01/prompts/global.txt`的单槽TD（外部输出E/U、内部R17）。公开组合profile明确移除握手/状态并增加return_value；N19 AST据此手工给normal，N20只编译该AST。没有丢失已纳入本基线的周期语义，但本结果也不验证原单槽握手或N28接口变体；详见[来源与规格获取复核](specification-acquisition-review.md)。原执行计划、产物及结果不改。

实现仅复制上述trusted文件及同字节公开数学，不读取候选池、旧生成RTL或旧TB。[新基线目录](../../../../artifacts/responsibility-direct-math-compiler-baseline-20261021-01/README.md)保存代码、输入来源、预定期望、冻结文件及后续原始日志。

## 执行前固定的资格与解释

最多一个Python发射入口、两个iverilog编译和两个vvp仿真，每过程外部30秒；第一次失败即停止，零重试、零模型/SAT/API/安装。主审先查冻结代码，再核发射字节，最后才允许HDL资格。

FIR检查4096个三signed4输入，覆盖完整二值函数域。TD检查327680个合法E/alpha嵌入位置，加32个公共极值角点和8个预先指定位置，共327720位置；不是完整顶层输入域，也不保证位置互不重复。独立TB直接编码公共原式，不调用编译器求值器；每题重放一个已知数学错配，负控制不是另行编译的错误DUT。逐节点保守区间必须证明signed64安全，不能把范围证明误称RTL全域功能证明。

若通过，结论限于：**在当前完整可信数学、无固定内部责任约束的两个变体上，零模型的普通编译流程已经可实际生成并通过所列功能资格。** 这会削弱“必须再采样局部合同并调用LLM实现行为”的必要性，但不单凭传统算法可用就否决系统贡献。协议仍可用真实覆盖、可靠性或完整成本增量建立价值；当前没有这样的配对数据。

若失败，先区分lowering错误、TB错误、依赖/工具问题和超时；一个开发基线失败不构成候选方法胜出。不得改任务、排除失败或追加运行到通过。

无论结果如何，本轮都不能声称TD全域证明、自然语言自动建模、实测LLM速度/费用优势、PPA优化、最优模块分解、旧架构遵约或SCI创新已经成立。人工可信AST的获得成本依旧缺失。

## 实际结果与核对

**实现与资格均已完成，全部预定5个入口exit0，零重试、零超时、零未跑、零模型/SAT/API。** 实际发射不是复用手写答案文件：编译器遍历完整normal AST、提取自由变量，为FIR生成两个helper共16节点，为TD生成三个helper共47节点。63节点记录signed64区间，所有最终窄输出均有范围证明；父层只有实例接线。模板化的是独立数学TB，不是DUT答案。

| 预定入口 | 实际退出码 | 秒 | 结果 |
| --- | ---: | ---: | --- |
| `generate.py` | 0 | 0.3824633 | 发射7个RTL及2个TB文件；执行后、HDL前核9个生成字节hash |
| FIR `iverilog` | 0 | 0.2018453 | 编译完成 |
| FIR `vvp` | 0 | 0.1782727 | 4096/4096完整二值输入通过，两个输出逐项一致 |
| TD `iverilog` | 0 | 0.1691651 | 编译完成 |
| TD `vvp` | 0 | 13.4253147 | 327720/327720预定位置通过，三个输出逐项一致 |

原件见[运行账本](../../../../artifacts/responsibility-direct-math-compiler-baseline-20261021-01/run-ledger.json)、[结果JSON](../../../../artifacts/responsibility-direct-math-compiler-baseline-20261021-01/results.json)、[结果说明](../../../../artifacts/responsibility-direct-math-compiler-baseline-20261021-01/results.md)、[FIR原始仿真日志](../../../../artifacts/responsibility-direct-math-compiler-baseline-20261021-01/results/FIR-vvp.stdout.log)及[TD原始仿真日志](../../../../artifacts/responsibility-direct-math-compiler-baseline-20261021-01/results/TD-vvp.stdout.log)。两份数学错配回放分别为FIR正确−2/错误−1、TD正确8/错误16；没有另外编译错误RTL，不能说mutation资格通过。

主审在发射前读全部源码、TB生成器、预定期望及runner并核9冻结文件和3工具SHA；发射后逐字读7个RTL与2个TB并核9个生成hash，之后才允许4个HDL入口。完成后再次核9冻结文件、41封存文件hash、5项原始日志/退出状态和全部marker一致。没有主审另行重跑的资格入口。独立审查者先只读数学/lowering/TB与最终runner：未见限定数学阻断，入口预算和禁止重试在串行唯一执行下成立。另一名独立审查者完成封存后审计，逐一核7个RTL、2个TB、9冻结/9生成/41封存hash、输入与N19同字节及5份receipt/raw/ledger一致，未见实质问题；未重跑、未修改文件。runner的30秒是父工具等待/终止机制，没有进程树硬上限或并发互斥；实际五入口均在30秒内完成，无超时路径发生，不能把本次结果扩张成进程隔离认证。

| 关键原件 | SHA256 |
| --- | --- |
| [预冻结manifest](../../../../artifacts/responsibility-direct-math-compiler-baseline-20261021-01/prepared-manifest.json) | `f88ba6a2b8426efa7139112d65b58be894227abddc7f84c6543b62dfef7ca3e1` |
| [compiler.py](../../../../artifacts/responsibility-direct-math-compiler-baseline-20261021-01/compiler.py) | `748b60870a632ad2b9a40a25707f0b3b9c5759c76aedc427e64a5998521e2150` |
| [生成物manifest](../../../../artifacts/responsibility-direct-math-compiler-baseline-20261021-01/generated-manifest.json) | `f1bed0f4fa27f89bc34a524449e6ffcbe9f26f40a16772760ffd04d29e635941` |
| [结果JSON](../../../../artifacts/responsibility-direct-math-compiler-baseline-20261021-01/results.json) | `1c7cfe4a8870f263328bc32d37cbe1b8ce11113ac839a87229943ed142212d2e` |
| [41文件封存表](../../../../artifacts/responsibility-direct-math-compiler-baseline-20261021-01/postexecution-sha256.json) | `196889e09701e2a00d9db29c20afe40b5bdb45adb76b04343fdb36327e5a4460` |

N19的摘要资格与本轮RTL功能结果是不同证据，不合并成模型成功率。以上耗时只是单次开发资格入口读数，不是与LLM协议的时间/费用配对实验；没有人工工时或PPA测量。TD仍是有限子域，不补称全域形式证明。

## 与方法核心判断的关系

[Parsel深审](neighbor-deep-review-parsel-local-options.md)已经核到局部候选body池的实际笛卡尔组合；[RTLScout/Spire深审](neighbor-deep-review-rtlscout-options.md)已核到配置选择、库替换与RTL发射。不能将这些强近邻弱化为仅完整项目重试或提示词。当前合同选择器的对象与时点有所不同，但这些差别尚未形成独立收益证据。

**当前裁决：不继续把N18/N19作为已成立或即将成立的SCI方法核心，不追加其完整LLM链或模型pilot。** 原因是近邻已覆盖局部备选组合等主机制，而当前完整可信数学与自由分解条件下，普通编译已有实际端到端构造；尚无额外任务目标、真实模型候选覆盖或完整成本数据支持选择协议的增量。这个判断既不说全领域绝无新意，也不以传统工具存在就自动否决系统贡献；它只是当前最小工作量路线未通过继续投入门槛。

选择器保留为可复核开发工具和机制控制，两个数学例保留为语义兼容反例。恢复方法研究需先识别来自真实需求、尚未被同信息直接编译流程满足的具体工作或成本/可靠性瓶颈，并明确新增处理及公平主指标；结构取舍只是可能来源之一，不要求先证明通用编译理论上不能完成。N33[比较起点审计](comparison-endpoint-audit.md)收窄此门，维持当前停止扩大N18/N19的决定。已向用户提出是否只读审查现有带状态/握手任务并开放内部结构的范围问题；等待答复不改变本轮完成结论。未采纳新流量、PPA或时序要求，未启动新的被测生成。整体论文目标仍未完成，既有v0.3初稿不据本轮负向结果冒称可投稿。
