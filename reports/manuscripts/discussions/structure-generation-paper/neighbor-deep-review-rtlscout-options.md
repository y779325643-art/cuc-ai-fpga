# RTLScout / Spire：局部架构选择与程序发射深审

日期：2026-10-21。定向读原文与作者代码，不安装或运行框架、模型、综合或仿真。本文不改变研究权威、任务、评分或正文。

## 1. 主源与版本

采用[RTLScout官方v3](https://arxiv.org/html/2606.06530v3)，2026-09-14，完整阅读§3.1–3.4及§4，另读§6对照定义。作者由论文直接链接的仓库是 `huawei-csl/rtlscout` 与 `huawei-csl/spire-hdl`。固定提交分别为 [`e827566dfc3dff8092b16983d78417f2e55030f7`](https://github.com/huawei-csl/rtlscout/commit/e827566dfc3dff8092b16983d78417f2e55030f7)（2026-10-21打包更新）与 [`9e0cd85a24632edf588805410ef8d272d419d5a1`](https://github.com/huawei-csl/spire-hdl/commit/9e0cd85a24632edf588805410ef8d272d419d5a1)（2026-09-09）。这是可定位的当前实现核查，不冒称两个HEAD就是原论文全部实验的代码状态。

## 2. 论文实际流程

The agent writes executable Spire designs and receives correctness and mapped-cost feedback. Source-local decorators delegate selected regions to Boolean optimization or arithmetic-library replacement. An elite pool seeds later runs with designs and lessons. The arithmetic sweep combines partial-product, final-adder and optimization choices; the paper also permits decorator-based selection instead of that sweep. Verification and cost evaluation follow generated implementations. Thus, local architecture choices, programmatic combinations, library instantiation and source-to-RTL emission are already substantive mechanisms here, not merely prompts. The proposed pre-behavior option protocol changes the object and timing of selection, but that difference alone establishes neither novelty nor lower total cost. These statements summarize §§3–4; numerical performance claims were not independently reproduced. [Primary method](https://arxiv.org/html/2606.06530v3#S3)

## 3. 实际代码，而非只读摘要

| 核查点 | 固定源码与已确认处理 |
| --- | --- |
| 局部算术配置自动选择 | Spire [`int_arithmetic_config.py L308–358`](https://github.com/huawei-csl/spire-hdl/blob/9e0cd85a24632edf588805410ef8d272d419d5a1/src/spire/arithmetic/int_arithmetic_config.py#L308)：按算子、位宽、signedness、目标查库；无记录时返回默认配置 |
| 局部目标的含义 | [`auto_config.py L146–166`](https://github.com/huawei-csl/spire-hdl/blob/9e0cd85a24632edf588805410ef8d272d419d5a1/src/spire/arithmetic/eval/auto_config.py#L146)：area/delay/ADP按库中size与AIG depth排序；不能直接当整个设计的最终mapped PPA |
| 图级识别及替换 | [`int_arithmetic_config.py L361–414`](https://github.com/huawei-csl/spire-hdl/blob/9e0cd85a24632edf588805410ef8d272d419d5a1/src/spire/arithmetic/int_arithmetic_config.py#L361)遍历实际表达式DAG；L725–766处理多输入加法、局部配置、宽度适配；不是只输出一个建议名字 |
| 局部交接落到调用图 | [`optimize.py L1180–1291`](https://github.com/huawei-csl/spire-hdl/blob/9e0cd85a24632edf588805410ef8d272d419d5a1/src/spire/optimize/optimize.py#L1180)：捕获函数为Component，替换算术，再连接实际输入并返回输出Expr；此处仍未由本轮独立证明语义健全性 |
| 确有组合，而非全设计重复采样 | RTLScout [`fpmul_sweep_mp.py L246–287`](https://github.com/huawei-csl/rtlscout/blob/e827566dfc3dff8092b16983d78417f2e55030f7/rtlscout/tech_eval/ppa_extract/sweeps/fpmul/fpmul_sweep_mp.py#L246)：枚举PPA/FSA/优化类型的笛卡尔积，同一FSA用于乘法与指数加法，并加入原始算子基线 |
| 参数不能混认论文冻结值 | 同文件L205–208有默认target delays；[stage3 wrapper L123–125](https://github.com/huawei-csl/rtlscout/blob/e827566dfc3dff8092b16983d78417f2e55030f7/artifacts/fpmul_run/stages/stage3_sweep.py#L123)可显式覆盖。未运行时不能由源码默认值反推论文实际配置 |

没有阅读或复算所有库配置与原始Pareto结果；没有将作者的正确性报告当本轮独立复现。

## 4. 对当前局部语义备选的约束

不能把“LLM决定局部结构、程序选库/组合、生成RTL”列为宽泛新点。当前FIR/TD的同型桥可以承载不同数学含义，需协同选择上下游摘要；Spire所核路径的目标是替换已成形算术图中的实现。这个具体差别值得保留在比较表中，但本轮没有证明Spire不能表示或处理该任务。

下一项候选若保留，应比较：同一规划信息下的单一完整合同、完整合同候选、局部合同组合，以及直接AST构造/库发射。程序筛选声明摘要后，仍需验证实际body兑现摘要；提前筛选也未得到真实PPA。新协议的可检验价值只能落在总生成成本、失败开销与首次完整结果上，不能用阶段更早、没有反馈或solver成熟与否代替证据。

关联：[既有FIR/TD结构变体](independent-method-core-review.md#7-最新范围两个保持完整顶层函数的结构变体)、[Stepwise/FormalRTL](neighbor-deep-review-formalrtl-refinement.md)、[SynthTL](neighbor-deep-review-synthtl.md)。未将新静态合同组合升级为正式任务或SCI创新验收。
