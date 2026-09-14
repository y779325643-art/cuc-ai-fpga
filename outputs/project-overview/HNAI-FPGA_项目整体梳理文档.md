# HNAI-FPGA 项目整体梳理文档

> **状态：历史项目梳理材料。** 本文保留原始 HNAI-FPGA 路线，不代表当前
> SR2FPGA 实现、Paper-1 方法或实验计划。当前事实见
> [`docs/current-status.md`](../../docs/current-status.md)，研究协议以
> [`paper1-freeze-v1.7`](../../docs/specs/2026-08-14-sr2fpga-paper1-research-program-design.md)
> 为准。

面向非 DNN AI 算法的、基于分层硬件意图 IR 的自然语言到 FPGA 自动设计与约束优化框架

## 1. 项目一句话定位

HNAI-FPGA 不是一个单纯的“AI 写 Verilog”工具，而是一个从自然语言/功能需求出发，经过分层硬件意图表示 HIS、算法模板实例化、IR 层约束检查、CIRCT/RTL lowering、EDA 工具验证与反馈优化，最终生成可验证 FPGA 工程包的自动设计框架。

项目的核心研究对象不是 agent 循环本身，而是循环中可解释、可检查、可优化的硬件中间表示与工具链反馈抽象。

## 2. 背景问题

FPGA 适合低时延、低功耗、确定性执行和非标准计算结构，但开发通常需要 HDL/HLS、时序约束、资源预算、板级验证等多方面经验。

现有 Vitis AI、hls4ml、FINN 等工具主要服务 DNN 推理部署，难以覆盖遗传算法、强化学习、路径规划、调度优化等非 DNN AI 工作负载。

通用 LLM 可以生成 RTL 片段，但如果缺少硬件意图表示、物理约束检查和 EDA 工具反馈，容易出现功能不匹配、资源超限、时序失败和接口不可部署等问题。

## 3. 核心概念统一

SPEC 是人类可读的项目需求说明，负责对齐目标、场景、验收标准和交付边界。

HIS（Hardware Intent Specification）应被定义为本项目的分层硬件意图 IR，而不只是需求 JSON。它连接自然语言需求与可综合硬件实现，表达算法目标、平台约束、架构结构、资源预算、接口协议、验证条件和实现映射。

MLIR 是承载自定义 IR、验证器、优化 pass 和 lowering pass 的通用框架；CIRCT 是基于 MLIR 的硬件编译工具链，可承载 hw、comb、seq、fsm、sv 等硬件 dialect，并生成 SystemVerilog。

Vivado、Verilator、UVM 等不是生成模型，而是验证、综合、时序、功耗和功能正确性闭环中的工具执行层。

## 4. 分层 HIS 设计

HIS-L0：需求意图层。描述算法类别、问题规模、目标 FPGA、目标频率、性能目标、资源预算、功耗上限、接口类型和验证方式。

HIS-L1：架构意图层。描述硬件模块、数据流、控制流、存储结构、并行度、流水线深度、状态机和模块间连接关系。

HIS-L2：实现映射层。描述如何映射到 CIRCT/MLIR、RTL/HLS、XDC、testbench、UVM 组件、Vivado Tcl 和报告解析规则。

通过这种分层，HIS 既保留自然语言需求的可追踪性，又能承担高层硬件 IR 的语义表达任务。

## 5. 总体技术路线

自然语言或功能描述首先转换为 SPEC，再提取为 HIS-L0；随后通过算法模板和架构映射器生成 HIS-L1；再由 lowering 过程生成 CIRCT/MLIR 或模板化 RTL/HLS；最后通过 Verilator、Vivado、UVM 和 XDC 检查形成结构化反馈。

推荐流程为：自然语言需求 -> SPEC -> HIS-L0 -> HIS-L1 -> HIS-L2 -> CIRCT/MLIR 或 RTL/HLS -> SystemVerilog/XDC/Testbench -> Verilator/UVM/Vivado -> 结构化诊断 -> 回写 HIS 参数。

Agent 在其中负责调度工具、维护状态、解释诊断和发起下一轮生成；真正的核心是 HIS 表示、IR 层合法性检查、lowering 规则和 EDA 反馈抽象。

## 6. Lowering 的实现思路

Lowering-1：Intent Lowering。将 SPEC/HIS-L0 转成 HIS-L1，完成算法模板选择和架构参数实例化。

Lowering-2：Architecture Lowering。将 HIS-L1 中的算法块转成硬件块，例如 PopulationMemory、FitnessArray、ControlFSM、QTable、ArgmaxPolicy、AXI Interface。

Lowering-3：Compiler Lowering。将硬件块转成 CIRCT 的 hw、comb、seq、fsm、sv dialect，或先转成受控 DSL/JSON 后再程序化生成 CIRCT IR。

Lowering-4：RTL Lowering。通过 CIRCT 生成 SystemVerilog，或在 MVP 阶段使用模板化 RTL/HLS 生成。

Lowering-5：Feedback Lowering。将 Vivado/Verilator/UVM 报告解析为 timing/resource/power/function 诊断，并回写到 HIS-L1 的参数空间。

## 7. MLIR/CIRCT 的项目定位

MLIR/CIRCT 不应替代 HIS，也不应在第一版中强行成为所有模块的硬依赖。更合理的定位是：HIS 是高层硬件意图 IR，MLIR/CIRCT 是低层硬件 IR 和 Verilog emission 后端。

MVP 可先采用 HIS JSON + 模板化 RTL/HLS；中期引入 CIRCT hw/comb/seq/fsm/sv 作为受控后端；长期可定义 HNAI MLIR dialect，把 HIS 的架构意图正式升级为可验证、可优化、可 lowering 的 MLIR dialect。

如果直接让 LLM 生成复杂 MLIR 文本，容易出现语法、SSA、类型和连接错误。更稳的方式是让 LLM 生成 HIS 或受控 DSL，再由程序化 lowering pass 生成 CIRCT IR。

## 8. 生成模型与 RTL++ 的关系

RTL++ 的贡献是利用 RTL 的 CFG/DFG 图表示增强 LLM 的 RTL 生成能力。它适合作为本项目第 3 层 RTL 生成器的增强后端，而不是完整 FPGA 设计平台。

本项目可以吸收 RTL++ 的图增强思想：从 HIS-L1 生成预期数据流/控制流图，再用图结构约束 RTL 生成；生成后再从 RTL 反向提取 CFG/DFG，与预期图进行一致性检查。

因此 RTL++ 与 HIS/MLIR/CIRCT 的关系是互补的：RTL++ 改善生成模型的结构理解，HIS/MLIR/CIRCT 提供可验证中间表示和编译路径。

## 9. 工具链与 Agent 实现

工具层应封装为白名单 Tool API，包括 syntax_check、run_simulation、run_vivado_synth、analyze_resources、analyze_power、parse_xdc、check_timing、run_uvm_test 等。

每个工具必须有固定输入输出、timeout、项目目录隔离、日志记录和结构化结果。Agent 不能直接相信生成模型，而应以工具结果和 HIS 约束作为下一步决策依据。

Vivado 可通过 batch Tcl 调用 report_utilization、report_timing_summary、report_power、report_drc、check_timing；Verilator 可用于轻量语法和功能仿真；XDC 检查用于确认端口、时钟、IO 标准、时序例外和板卡 pin map。

## 10. 验证体系：Golden Model 与 UVM

Golden model 是功能正确性的参考模型。GA-Knapsack golden model 是 Python/C++ 版背包遗传算法参考实现；RL-GridWorld golden model 是 Python/C++ 版 GridWorld Q-learning 参考实现。

第一版可由 Python golden model 生成 expected vectors，普通 SystemVerilog testbench 或 Verilator 仿真读取并对比。成熟后可升级为 UVM + DPI-C 的验证体系。

UVM 的价值在于把 sequence、driver、monitor、scoreboard、coverage 组织成专业验证环境。Scoreboard 将 DUT 输出与 golden model 对比，并把 mismatch 转换为结构化诊断，回写 HIS 或架构参数。

## 11. 创新点重新凝练

创新点 1：分层硬件意图 IR。提出 HIS-L0/L1/L2，将自然语言需求、算法架构、资源约束、接口协议、验证条件和实现映射统一到可追踪的中间表示中。

创新点 2：IR 层约束验证与架构搜索。在生成 RTL 前，对并行度、流水线、存储 bank、接口宽度、资源预算、时钟和状态机合法性进行检查与设计空间探索。

创新点 3：HIS 到 CIRCT/RTL 的 lowering 机制。将高层算法架构意图程序化下沉到硬件 IR 或模板化 RTL/HLS，降低直接 LLM-to-RTL 的不可控性。

创新点 4：EDA 反馈到 IR 参数的闭环优化。将 Verilator/Vivado/UVM 输出抽象成可回写 HIS 的结构化诊断信号，而不是简单把日志交给 LLM。

创新点 5：面向非 DNN AI 算法的 FPGA 自动设计。聚焦 GA、RL、路径规划、调度优化等现有 DNN FPGA 工具覆盖不足的算法类别。

## 12. MVP 与长期路线

MVP 阶段：完成 HIS JSON、GA-Knapsack 和 RL-GridWorld 两个模板、Python golden model、轻量 testbench、Verilator/Vivado batch、资源/时序/功耗报告解析和 summary.json 输出。

中期阶段：引入 XDC 自动检查、UVM 验证环境、RTL++ 风格 CFG/DFG 图增强生成、CIRCT hw/sv 后端和性能预测器。

长期阶段：定义 HNAI MLIR dialect，开发 verifier、canonicalization、DSE pass、lowering pass，并实现从 HIS 到 FPGA/ASIC 实现的跨层协同优化系统。

博士研究表达可聚焦为：面向非 DNN AI 算法的、基于分层硬件意图 IR 的自然语言到 FPGA 自动设计与约束优化方法研究。

## 关键概念对照表

| 概念 | 定位 | 在项目中的作用 |
| --- | --- | --- |
| SPEC | 人类可读需求规格 | 对齐目标、场景、验收和交付边界 |
| HIS | 分层硬件意图 IR | 表达需求、架构、约束、接口、验证和实现映射 |
| MLIR | 多层中间表示框架 | 承载 dialect、verifier、pass 和 lowering 基础设施 |
| CIRCT | 硬件领域 MLIR 工具链 | 提供 hw/comb/seq/fsm/sv dialect 与 SV 输出能力 |
| RTL/HLS | 硬件实现形式 | 生成可综合 Verilog/SystemVerilog 或 HLS C++ |
| Vivado/Verilator/UVM | 验证与实现工具层 | 提供语法、仿真、综合、时序、功耗和功能验证反馈 |

## MVP 工具模块建议

| 模块 | 输入 | 输出 |
| --- | --- | --- |
| parse_his | 自然语言/SPEC | HIS-L0 JSON |
| instantiate_template | HIS-L0 + 算法模板 | HIS-L1 架构意图 |
| generate_rtl | HIS-L1/HIS-L2 | RTL/HLS/Testbench/XDC |
| run_simulation | RTL + golden vectors | 功能匹配报告 |
| run_vivado_batch | Vivado project/Tcl | utilization/timing/power/DRC 报告 |
| parse_feedback | EDA 原始日志 | 可回写 HIS 的结构化诊断 |
