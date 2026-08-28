# HNAI-FPGA 项目介绍

> **状态：历史项目介绍材料。** 本文保留原始 HNAI-FPGA 构想，不代表当前
> SR2FPGA 实现、Paper-1 方法或实验计划。当前事实见
> [`docs/current-status.md`](../../docs/current-status.md)，研究协议以
> [`paper1-freeze-v1.7`](../../docs/specs/2026-08-14-sr2fpga-paper1-research-program-freeze-design.md)
> 为准。

## 面向非 DNN AI 算法的、基于分层硬件意图 IR 的自然语言到 FPGA 自动设计与约束优化框架

---

## 一、一句话定位

HNAI-FPGA 不是一个单纯的「AI 写 Verilog」工具，而是一个从自然语言/功能需求出发，经过分层硬件意图表示 HIS、算法模板实例化、IR 层约束检查、CIRCT/RTL lowering、EDA 工具验证与反馈优化，最终生成可验证 FPGA 工程包的自动设计框架。

项目的核心研究对象不是 Agent 循环本身，而是循环中可解释、可检查、可优化的硬件中间表示与工具链反馈抽象。

---

## 二、背景与技术演进

### 2.1 FPGA 开发的现实困境

FPGA 适合低时延、低功耗、确定性执行和非标准计算结构，但开发通常需要 HDL/HLS、时序约束、资源预算、板级验证等多方面经验。主要有五座大山：HDL/HLS 编写、时序约束、资源预算、板级验证、多工具协同。

### 2.2 AI 驱动硬件自动设计的技术演进

该领域大致经历了九个阶段：

| 阶段 | 时间 | 代表工作 | 核心贡献 | 局限 |
|------|------|----------|----------|------|
| 手工 RTL | 1980s-至今 | Verilog/VHDL | 完全可控、性能最优 | 周期长、成本高 |
| 高层次综合 HLS | 2000s-至今 | Vitis HLS, Intel HLS, Bambu | C/C++ → RTL 自动化 | 只能实现设计，不能发明架构 |
| 设计空间探索 DSE | 2010s-至今 | AutoDSE, AutoSA, FINN, hls4ml | 自动搜索 Pipeline/PE/Tile 参数 | 本质是自动调参，不是自动设计 |
| LLM 生成 RTL | 2023 | NVIDIA VerilogEval (ICCAD) | 首次系统评估 LLM 生成 RTL 能力 | 仅评估，未形成工具 |
| RTL 专用大模型 | 2023-25 | HKUST RTLCoder | 引入 Code Quality Feedback | 解决代码生成问题，未解决架构设计 |
| 生成-验证-修复闭环 | 2024 | Generate-Compile-Repair | 显著提高 RTL 正确率 | 仍为片段级 |
| Agent 自动设计系统 | 2025 | NVIDIA Spec2RTL-Agent | 多 Agent 协同，处理真实规格文档 | 缺分层 IR、约束检查、EDA 反馈闭环、不覆盖非 DNN AI |
| 结构化硬件表示 | 2024-25 | RTL++, Graph/AST/IR-based | 用图结构增强生成质量 | 缺少编译链路和验证闭环 |
| MLIR/CIRCT | 2020-至今 | LLVM 社区 | 硬件版 LLVM——结构化表达硬件设计 | 缺少上层意图表达和自动架构搜索 |

**演进趋势**：从「AI 帮人写代码」转向「AI 设计硬件架构并自动优化」。HNAI-FPGA 瞄准的是未来——融合结构化表示、MLIR/CIRCT、Agent 调度和 EDA 反馈闭环，形成面向非 DNN AI 的完整 FPGA 自动设计框架。

### 2.3 现有方案为什么不够

**DNN 专用工具**（Vitis AI, hls4ml, FINN）：架构假设绑定 DNN 计算图（规整张量运算），无法泛化到 GA/RL/路径规划/调度优化等非 DNN AI 工作负载。

**通用 LLM 直接生成 RTL**：缺少硬件意图表示（功能不匹配）、缺少物理约束检查（资源超限）、缺少 EDA 反馈闭环（时序失败不可解释）、缺少接口/验证体系（不可部署）。

**Spec2RTL**：目前最接近的 Agent 设计系统。证明了从自然语言到 RTL 的方向可行，但 Spec 直接到 RTL 中间无可检查的 IR 层，没有 EDA 反馈回写架构参数的闭环，不覆盖 GA/RL 等非 DNN AI 算法，输出是 RTL 片段而非可部署 FPGA 工程包。

### 2.4 为什么非 DNN AI 是一个特殊的问题

| 维度 | DNN 推理 | 非 DNN AI（GA/RL/调度/规划） |
|------|---------|------------------------------|
| 计算模式 | 规整的张量运算 | 不规则的控制流 + 数据流 |
| 存储访问 | 规则的层级 buffer | 随机的、依赖数据的访问模式 |
| 工具覆盖 | Vitis AI/hls4ml/FINN | **空白** |
| 算法模板 | Conv/MatMul/Activation 固定 | 种群维护、适应度评估、Q-table 更新、路径搜索 |

非 DNN AI 需要 FPGA 的低时延、低功耗、确定性执行特性，但现有工具的架构假设系统性排除了这些算法。这个空白既有学术价值，也有工程价值。

---

## 三、核心概念

| 概念 | 定位 | 在项目中的作用 |
|------|------|---------------|
| SPEC | 人类可读需求规格 | 对齐目标、场景、验收和交付边界 |
| HIS | 分层硬件意图 IR | 核心研究对象——表达需求、架构、约束、接口、验证和实现映射 |
| MLIR | 多层中间表示框架 | 承载自定义 dialect、verifier、pass 和 lowering 基础设施 |
| CIRCT | 硬件领域 MLIR 工具链 | 提供 hw/comb/seq/fsm/sv dialect 与 SystemVerilog 输出能力 |
| RTL/HLS | 硬件实现形式 | 可综合 Verilog/SystemVerilog 或 HLS C++ 代码 |
| Vivado/Verilator | 验证与实现工具层 | 提供语法检查、仿真、综合、时序、功耗和功能验证的结构化反馈 |
| UVM | 通用验证方法学 | 将 sequence/driver/monitor/scoreboard 组织成专业验证环境 |
| Agent | 工具调度与决策层 | 调度工具、维护状态、解释诊断、发起下一轮——但不是核心研究对象 |

---

## 四、核心技术：分层 HIS 设计

### 4.1 为什么需要 HIS

在自然语言和 RTL 之间，缺少一层可检查、可追踪的中间表示。HIS 的设计哲学不是把需求翻译成 JSON，而是建立一层**语义足够丰富、可被机器检查和优化、同时保留自然语言可追溯性**的硬件中间表示。

| 没有 HIS | 有 HIS |
|----------|--------|
| LLM 生成什么就是什么 | 生成前 HIS 层约束检查（并行度、流水线、资源预算、接口宽度） |
| 需求变化无法追溯 | L0 → L1 → L2 逐层可追踪，改需求知道改哪里 |
| 架构决策隐式在代码中 | L1 显式表达模块划分、数据流、控制流、状态机 |
| EDA 反馈不知回写给谁 | 结构化诊断 → 定位到具体 HIS 参数 → 精准回写 |

### 4.2 HIS-L0：需求意图层

回答「要做什么、在什么约束下做」。不涉及任何硬件实现细节。

包含维度：
- **算法维度**：算法类别、问题规模、数据类型、精度要求、终止条件
- **平台维度**：目标 FPGA 型号、目标频率、可用资源上限（LUT/FF/BRAM/DSP）
- **性能目标**：吞吐量、延迟、功耗上限
- **接口维度**：输入输出接口类型（AXI/AXI-Stream/GPIO/BRAM 接口）、数据位宽
- **验证维度**：验证方式（Golden Model 对比/UVM/形式验证）、验证指标

**示例**（GA-Knapsack）：算法=遗传算法，问题=0/1 背包 N=256，FPGA=Artix-7 xc7a35t，频率=100MHz，接口=AXI-Stream 输入 + GPIO 输出 + AXI-Lite 控制，验证=Python Golden Model。

### 4.3 HIS-L1：架构意图层

回答「硬件怎么组织、数据怎么流动」。这是 HIS 的核心层，也是约束检查的**主战场**。

包含维度：
- **模块划分**：顶层模块列表及其职责
- **数据流图**：模块间数据通路、流向、位宽、握手协议
- **控制流与状态机**：FSM 状态定义与转移条件
- **存储结构**：BRAM/Distributed RAM 分配、Bank 数量、读写端口数
- **并行与流水**：并行度、流水线级数、stall 条件
- **时序预算**：关键路径预估、跨时钟域策略
- **接口协议绑定**：AXI 地址映射、burst 长度、data width、handshake

**示例**（GA-Knapsack L1）：
- PopulationMemory: 双端口 BRAM, 深度=128, 位宽=256, Bank=1
- FitnessArray: 4 并行 PE, 3 级流水线, 32bit 输出
- SelectionUnit: 锦标赛选择(tournament=4), 流水线化
- CrossoverUnit: 单点交叉, 可配置交叉率
- MutationUnit: 按位变异, LFSR 随机数生成
- ControlFSM: 5 状态 (INIT→EVAL→SELECT→CROSSOVER_MUTATE→CHECK)
- AXI_Interface: AXI-Stream Slave + AXI-Lite + GPIO 输出

### 4.4 HIS-L2：实现映射层

回答「如何映射到具体工具链和实现策略」。不引入新架构信息，把 L1 的架构意图绑定到具体实现路径。

包含维度：
- **IR 路径选择**：CIRCT hw/comb/seq/fsm/sv 路径 或 模板化 RTL/HLS 路径 或混合
- **RTL 生成策略**：模板参数实例化 / HLS pragma / CIRCT lowering pass
- **XDC 约束映射**：时钟定义、IO 标准、管脚映射、时序例外
- **Testbench 策略**：激励生成方式、Golden Vector 格式、结果对比逻辑
- **EDA 工具绑定**：Vivado Tcl 脚本模板、Verilator 参数、UVM 组件映射
- **报告解析规则**：utilization/timing/power/DRC 报告到结构化诊断的解析规则

MVP 阶段选择模板化 RTL 路径（可控性高、调试方便），中长期逐步引入 CIRCT 后端。

### 4.5 三层协同：约束向下传递，反馈向上追溯

```
HIS-L0 (需求约束) → HIS-L1 (架构约束) → HIS-L2 (实现约束)
                                                ↓
                                           RTL / CIRCT
                                                ↓
                                           EDA 验证
                                                ↓
                               结构化诊断 → 回写 HIS-L1 参数空间
```

每层的检查：
- **L0**：需求完整性、一致性（parse_his 阶段）
- **L1**：架构合法性、资源预算、并行合法性、时序可行性（instantiate_template 阶段）
- **L2**：实现可行性、工具兼容性（lowering 前）
- **反馈**：物理实现正确性（EDA 运行后，回写 HIS-L1）

---

## 五、Lowering 机制：从意图到硬件

### 5.1 为什么要程序化 Lowering

| LLM 直接生成 RTL | 程序化 Lowering |
|------------------|----------------|
| 输出不可控——每次生成可能不同 | 输出确定性——相同 HIS 输入产生相同 RTL |
| 错误不可定位——RTL 错了不知道哪层的问题 | 错误可定位——每层 lowering 独立可验证 |
| 语法/类型错误——LLM 不保证 SSA 合法性 | 类型安全——程序化 pass 保证 IR 合法性 |
| 优化不可重现——依赖 prompt 工程 | 优化可系统化——pass pipeline 可组合、可复用 |

### 5.2 五层 Lowering

**Lowering-1：Intent Lowering**（需求 → 架构意图）
- 输入：SPEC/HIS-L0
- 过程：算法模板匹配 + 约束传播 + 架构参数实例化
- 输出：HIS-L1 JSON

**Lowering-2：Architecture Lowering**（算法块 → 硬件块）
- 输入：HIS-L1
- 过程：算法结构到硬件结构的映射（如 Population → PopulationMemory, 适应度函数 → FitnessArray）
- 输出：硬件模块清单 + 互联关系表

**Lowering-3：Compiler Lowering**（硬件块 → CIRCT IR / 模板化 DSL）
- 路径 A（中长期）：硬件模块 → CIRCT hw/comb/seq/fsm/sv dialect
- 路径 B（MVP）：硬件模块 → 参数化 Verilog 模板实例化
- 关键设计：LLM 生成 HIS（结构简单，不易出错），程序化 pass 生成 RTL/CIRCT（语法保证正确）

**Lowering-4：RTL Lowering**（IR → SystemVerilog）
- CIRCT 路径：ExportVerilog pass 生成 .sv 文件
- 模板路径：模板引擎渲染 SystemVerilog
- 输出物：top.sv + 各子模块 .sv + constraints.xdc + testbench.sv

**Lowering-5：Feedback Lowering**（EDA 报告 → 结构化诊断 → 回写 HIS）
- 输入：Vivado/Verilator/UVM 报告
- 过程：parse_feedback 程序化解析 → 结构化诊断 JSON
- 输出：timing/resource/power/function 诊断 → 回写 HIS-L1 参数空间

### 5.3 MLIR/CIRCT 的项目定位

**定位三原则**：
1. **CIRCT 不替代 HIS**：HIS 是高层硬件意图 IR（表达架构），CIRCT 是低层硬件 IR（表达电路实现）
2. **不在 MVP 中强依赖**：MVP 用 HIS JSON + 模板化 RTL 跑通全链路，验证 HIS 设计的正确性
3. **LLM 不直接生成 MLIR**：直接让 LLM 生成 MLIR 文本容易出现 SSA、类型和连接错误。正确做法是 LLM → HIS → 程序化 pass → CIRCT IR

**三阶段演进**：
- **MVP**：HIS JSON → 模板化 RTL/HLS → SystemVerilog → Vivado/Verilator
- **中期**：HIS JSON → CIRCT hw/sv + 模板化 RTL（混合）→ UVM + XDC 自动检查 + RTL++ CFG/DFG 增强
- **长期**：HNAI MLIR Dialect → verifier/canonicalization/DSE/lowering pass → CIRCT → 跨层协同优化 → FPGA/ASIC

### 5.4 反馈闭环的核心机制

EDA 报告不是给 LLM 看的日志，而是可回写 HIS 的结构化诊断。诊断到回写的映射规则：

| 诊断信号 | 诊断含义 | 回写目标 | 调整策略 |
|---------|---------|---------|---------|
| WNS < 0 | 关键路径时序违规 | HIS-L1 流水线级数 | 增加 1-2 级流水 |
| LUT > 100% | 逻辑资源超限 | HIS-L1 并行度 | 减少 PE 数量 |
| WNS<0 且 LUT>100% | 时序+资源同时超限 | HIS-L0 目标频率或模板 | 降频或切换模板 |
| power > budget | 功耗超标 | HIS-L0 目标频率 | 降频，启用门控时钟 |
| function mismatch | 功能不正确 | HIS-L1 架构结构 | 检查 FSM 转移、数据通路 |
| DRC failure | 设计规则违规 | HIS-L2 XDC 约束 | 修正 IO 标准、时钟定义 |

---

## 六、端到端案例：GA-Knapsack

### 6.1 案例设定

自然语言需求：「用遗传算法求解 0/1 背包问题，256 个物品，种群规模 128，100 代终止。部署到 Xilinx Artix-7 xc7a35t，目标频率 100MHz，资源不超过 FPGA 的 80%。通过 AXI-Stream 输入物品列表，结果通过 GPIO 输出。」

### 6.2 全链路流转

**第一步：自然语言 → SPEC → HIS-L0**

提取算法维度（GA, 0/1 Knapsack, N=256）、平台维度（Artix-7, 100MHz）、接口维度（AXI-Stream + GPIO + AXI-Lite）、验证维度（Python Golden Model）。

**第二步：HIS-L0 → HIS-L1（模板匹配 + 架构实例化）**

匹配 GA-Knapsack 模板，推导架构参数：
- PopulationMemory: 128×256bit, 双端口 BRAM
- FitnessArray: 4 并行 PE, 3 级流水
- 资源预估：LUT 12.5K ≤ 16.6K ✓
- 约束检查：并行合法性 ✓、时序预估 ✓、接口匹配 ✓

**第三步：HIS-L1/L2 → RTL 生成**

参数化 Verilog 模板引擎生成：top.sv, population_memory.sv, fitness_array.sv, selection_unit.sv, crossover_unit.sv, mutation_unit.sv, control_fsm.sv, axi_interface.sv + constraints.xdc + testbench.sv。

**第四步：Golden Model 验证**

Python 参考实现产出 expected vectors → Verilator 仿真 DUT → 逐周期对比 → 功能匹配确认（最优解 3847, 收敛 78 代, mismatch=0）。

**第五步：Vivado 综合与反馈**

Vivado Batch Tcl 运行综合、布局、布线 → 报告解析 → 结构化诊断。若时序不收敛（如 WNS=-1.8ns），诊断定位到 FitnessArray/pipeline_s2，回写策略（增加流水线/降频/DSP 映射），重新生成通过。

---

## 七、工具链与 Agent 设计

### 7.1 工具白名单

每个工具必须有确定的输入/输出、边界和可审计的记录：

| 工具 | 输入 | 输出 |
|------|------|------|
| parse_his | 自然语言/SPEC | HIS-L0 JSON |
| instantiate_template | HIS-L0 + 算法模板 | HIS-L1 架构意图 JSON |
| generate_rtl | HIS-L1/L2 | RTL + XDC + Testbench |
| run_simulation | RTL + Golden Vectors | 功能匹配报告 |
| run_vivado_batch | Vivado project + Tcl | utilization/timing/power/DRC 报告 |
| parse_feedback | EDA 原始日志 | 结构化诊断 JSON |
| check_timing | timing 报告 | {wns, tns, critical_paths} |
| analyze_resources | utilization 报告 | {lut, ff, bram, dsp: pct} |
| analyze_power | power 报告 | {total, dynamic, static} |

每个工具的硬性约束：固定 I/O Schema、timeout、项目目录隔离、结构化日志、错误即数据。

### 7.2 EDA 工具调用链

1. **Verilator --lint-only**（< 30s）：快速语法检查
2. **Verilator 仿真**（< 2min）：Golden Vector 对比 → 功能验证
3. **Vivado Batch Tcl**（< 10min）：synth → place → route → 时序/资源/功耗/DRC 全报告
4. **UVM 环境**（成熟后）：sequence/driver/monitor/scoreboard/coverage + DPI-C 实时 Golden Model 对比

### 7.3 Agent 的角色边界

Agent 是调度者，不是核心研究对象。它负责：维护状态（轮次、HIS 参数空间、历史诊断）、调度工具（根据阶段选择、管理顺序、处理 timeout）、解释诊断（按规则匹配故障模式、确定性调整/建议探索/升级人工）、发起下一轮（回写参数、触发生成-验证循环、判断终止）。

Agent 不能做的事：不相信工具结果（必须以工具输出为准）、自由发挥生成策略、绕过 HIS 约束检查。

**核心论点**：项目的核心研究对象不是 Agent 循环本身，而是循环中可解释、可检查、可优化的硬件中间表示（HIS）与工具链反馈抽象。

---

## 八、生成模型与 RTL++ 的关系

RTL++ 的贡献是利用 RTL 的 CFG/DFG 图表示增强 LLM 的 RTL 生成能力。它适合作为本项目第 3 层 RTL 生成器的增强后端，但不是完整 FPGA 设计平台。

本项目可以吸收 RTL++ 的图增强思想：从 HIS-L1 生成预期数据流/控制流图，再用图结构约束 RTL 生成；生成后再从 RTL 反向提取 CFG/DFG，与预期图进行一致性检查。

RTL++ 与 HIS/MLIR/CIRCT 的关系是互补的：RTL++ 改善生成模型的结构理解，HIS/MLIR/CIRCT 提供可验证中间表示和编译路径。

---

## 九、验证体系

### 9.1 Golden Model 验证

Golden Model 是功能正确性的参考实现：
- GA-Knapsack golden model：Python/C++ 版背包遗传算法参考实现
- RL-GridWorld golden model：Python/C++ 版 GridWorld Q-learning 参考实现

MVP 阶段：Python golden model 生成 expected vectors → SV testbench 或 Verilator 仿真读取并对比。成熟后升级为 UVM + DPI-C 的验证体系。

### 9.2 UVM 的引入路径

UVM 的价值在于把 sequence、driver、monitor、scoreboard、coverage 组织成专业验证环境。Scoreboard 将 DUT 输出与 golden model 对比，并把 mismatch 转换为结构化诊断，回写 HIS 或架构参数。

---

## 十、创新点

五大创新点不是孤立的愿望清单，而是一条环环相扣的技术链：

**创新点 1：分层硬件意图 IR（HIS-L0/L1/L2）**
将自然语言需求、算法架构、资源约束、接口协议、验证条件和实现映射统一到可追踪的中间表示中。区别于 Spec2RTL 的纯需求 JSON 和 RTL++ 的代码级图表示。

**创新点 2：IR 层约束验证与架构搜索**
在生成 RTL 前，对并行度、流水线、存储 bank、接口宽度、资源预算、时钟和状态机合法性进行前置检查。与传统 DSE（搜索 HLS pragma 参数空间）不同，HNAI 在 HIS-L1 架构层做设计空间探索。

**创新点 3：HIS 到 CIRCT/RTL 的程序化 Lowering**
设计五层 Lowering 机制，将高层算法架构意图程序化下沉到硬件 IR 或模板化 RTL/HLS，降低直接 LLM-to-RTL 的不可控性。

**创新点 4：EDA 反馈到 IR 参数的闭环优化**
将 Verilator/Vivado/UVM 输出抽象成可回写 HIS 的结构化诊断信号（而非把日志直接交给 LLM），建立诊断类型 → HIS 参数 → 调整策略的确定映射规则。

**创新点 5：面向非 DNN AI 算法的 FPGA 自动设计**
聚焦 GA、RL、路径规划、调度优化等现有 DNN FPGA 工具（Vitis AI, hls4ml, FINN）覆盖不足的算法类别。通过算法模板机制将硬件结构知识编码为可复用模板。

---

## 十一、MVP 与路线图

### 11.1 MVP 阶段（当前）

| 模块 | 内容 |
|------|------|
| HIS 层 | HIS JSON Schema (L0/L1/L2), parse_his 模块 |
| 算法模板 | GA-Knapsack ✓, RL-GridWorld |
| 生成层 | 参数化 Verilog 模板引擎, generate_rtl |
| 验证层 | Python Golden Model ×2, Verilator 仿真集成, SV testbench |
| EDA 集成 | Vivado batch Tcl, 资源/时序/功耗/DRC 报告解析, summary.json |
| 反馈层 | parse_feedback 模块, 结构化诊断生成 |

### 11.2 中期阶段

- XDC 自动检查：验证 IO 标准、管脚映射、时钟定义、时序例外（优先级：高）
- UVM 验证环境：sequence/driver/monitor/scoreboard 组件化（优先级：高）
- RTL++ 风格 CFG/DFG 增强：预期图 → 约束生成 → 一致性检查（优先级：中）
- CIRCT hw/sv 后端：替换模板化 RTL 为 CIRCT lowering pass（优先级：中）
- 性能预测器：基于 HIS-L1 参数预测 PPA，减少 Vivado 调用（优先级：中）
- 更多算法模板：A* 路径规划、GA-Scheduling（优先级：低）

### 11.3 长期阶段

定义 HNAI MLIR dialect，开发 verifier、canonicalization、DSE pass、lowering pass，实现从 HIS 到 FPGA/ASIC 实现的跨层协同优化系统。

---

## 十二、学术表达

博士研究学术表达：

> **面向非 DNN AI 算法的、基于分层硬件意图 IR 的自然语言到 FPGA 自动设计与约束优化方法研究**

关键词拆解：

| 关键词 | 学术含义 |
|--------|---------|
| 非 DNN AI 算法 | 限定应用领域，区别于现有 DNN FPGA 工具 |
| 分层硬件意图 IR | 核心贡献——HIS-L0/L1/L2 |
| 自然语言到 FPGA | 输入（自然语言需求）到输出（可验证 FPGA 工程包）的跨度 |
| 自动设计 | 非人工设计硬件架构，而是由框架自动生成 |
| 约束优化 | EDA 反馈闭环 + IR 层约束检查驱动的迭代优化 |

---

## 十三、相关文件

- 项目概述文档：`HNAI-FPGA_项目整体梳理文档.md`
- 技术演进综述：`AI_Hardware_Design_Evolution.md`
- 项目讲解 PPT：`HNAI-FPGA_项目讲解.pptx`
- PPT 生成脚本：`generate_ppt.py`
