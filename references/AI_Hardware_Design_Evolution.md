# AI驱动硬件自动设计技术发展脉络综述
## ——从RTL设计到MLIR/CIRCT自动架构生成

# 一、引言

集成电路设计长期依赖人工完成硬件架构设计、RTL编码和验证工作。随着芯片复杂度不断提高，传统设计方法面临开发周期长、设计成本高以及跨层协同优化困难等问题。

近年来，人工智能特别是大语言模型（Large Language Models, LLM）的快速发展，为自动化芯片设计提供了新的可能性。研究方向逐渐从传统的RTL手工开发演化到AI辅助硬件设计，并进一步向自动架构生成与跨层协同优化发展。

从发展历程来看，该领域大致经历了以下几个阶段：

text 手工RTL设计 ↓ 高层次综合（HLS） ↓ 设计空间探索（DSE） ↓ LLM直接生成RTL ↓ RTL专用模型 ↓ Agent自动设计系统 ↓ MLIR/CIRCT硬件中间表示 ↓ AI驱动自动架构设计 

---

# 二、技术发展时间线

| 时间 | 阶段 | 代表团队 | 代表工作 |
|--------|--------|--------|--------|
| 1980s-至今 | RTL设计 | 工业界 | Verilog / VHDL |
| 2000s-至今 | HLS | Xilinx、Intel | Vitis HLS、Intel HLS |
| 2010s-至今 | DSE | UCLA VAST等 | AutoDSE、AutoSA |
| 2023 | LLM生成RTL | NVIDIA | VerilogEval |
| 2023-2025 | RTL专用LLM | HKUST | RTLCoder |
| 2024 | 自动修复闭环 | NVIDIA等 | Generate-Compile-Repair |
| 2025 | Agent设计系统 | NVIDIA | Spec2RTL-Agent |
| 2024-2025 | Graph/IR设计 | 多团队 | RTL++ |
| 2020-至今 | 硬件IR框架 | LLVM社区 | CIRCT |
| 未来 | 自动架构设计 | 学术界探索 | LLM+MLIR+CIRCT |

---

# 三、第一阶段：手工RTL设计

## 时间

1980年代至今

## 核心流程

text 需求分析 ↓ 架构设计 ↓ RTL编码 ↓ 仿真验证 ↓ 综合实现 

## 特点

工程师直接设计：

- 状态机(FSM)
- 数据通路(Datapath)
- Pipeline
- Cache
- BRAM
- 接口协议

典型RTL：

verilog always @(posedge clk) begin     q <= d; end 

## 优势

- 完全可控
- 性能最优

## 缺点

- 开发周期长
- 设计成本高

---

# 四、第二阶段：高层次综合（HLS）

## 时间

2000年代至今

## 代表工具

- AMD Vitis HLS
- Intel HLS Compiler
- LegUp
- Bambu

## 核心流程

text C/C++ ↓ Scheduling ↓ Binding ↓ FSM ↓ RTL 

## 示例

cpp for(int i=0;i<N;i++) {     y[i]=a*x[i]+b; } 

自动生成RTL。

## 优势

- 提高开发效率
- 降低RTL开发门槛

## 局限

只能自动实现设计。

无法自动发明架构。

---

# 五、第三阶段：设计空间探索（DSE）

## 时间

2010年代至今

## 代表工作

- AutoDSE
- AutoSA
- FINN
- hls4ml

## 核心思想

自动搜索：

- Pipeline深度
- PE数量
- Tile大小
- Buffer规模

形成：

text 参数空间 ↓ 搜索 ↓ 综合评估 ↓ Pareto最优解 

## 本质

自动调参。

不是自动设计。

---

# 六、第四阶段：LLM直接生成RTL

## 时间

2023

## 标志性工作

### VerilogEval

团队：

NVIDIA Research

论文：

VerilogEval: Evaluating Large Language Models for Verilog Code Generation

ICCAD 2023

## 流程

text Prompt ↓ LLM ↓ Verilog ↓ iverilog ↓ testbench 

## 意义

首次系统评估：

LLM是否能生成RTL。

---

# 七、第五阶段：RTL专用大模型

## 时间

2023-2025

## 标志性工作

### RTLCoder

团队：

HKUST

## 核心流程

text RTL代码 ↓ 自动生成描述 ↓ 训练数据 ↓ 微调LLM ↓ RTL生成 

## 创新

引入：

Code Quality Feedback

text 生成RTL ↓ 语法检查 ↓ 综合检查 ↓ 评分反馈 

## 局限

解决：

代码生成问题

未解决：

架构设计问题

---

# 八、第六阶段：生成-验证-修复闭环

## 时间

2024

## 核心思想

text Generate ↓ Compile ↓ Repair 

即：

text 生成RTL ↓ iverilog ↓ 报错 ↓ 反馈给LLM ↓ 重新生成 

## 优势

显著提高RTL正确率。

---

# 九、第七阶段：Agent自动设计系统

## 时间

2025

## 标志性工作

### Spec2RTL-Agent

团队：

NVIDIA Research

## 流程

text Specification ↓ Reasoning Agent ↓ Implementation Plan ↓ Coding Agent ↓ Reflection Agent ↓ HLS ↓ RTL 

## 特点

引入：

- 多Agent协同
- 自动规划
- 自动反思

## 意义

开始处理真实规格文档。

---

# 十、第八阶段：结构化硬件表示

## 时间

2024-2025

## 代表方向

- Graph-based RTL Generation
- RTL++
- AST-guided Generation
- IR-guided Generation

## 核心思想

不直接生成RTL：

text Specification ↓ Graph / AST / IR ↓ RTL 

## 原因

真正重要的是：

- 数据流
- 并行结构
- 架构关系

而不是RTL文本本身。

---

# 十一、第九阶段：MLIR/CIRCT

## 时间

2020年至今

## 团队

LLVM社区

参与方：

- Google
- Intel
- AMD
- SiFive

## 核心思想

建立：

硬件版LLVM

流程：

text Hardware IR ↓ CIRCT ↓ Verilog ↓ 综合 

---

## 核心Dialect

### HW Dialect

模块结构

### Comb Dialect

组合逻辑

### Seq Dialect

寄存器

### FSM Dialect

状态机

### Handshake Dialect

数据流

---

## 意义

首次实现：

硬件设计过程结构化表达。

---

# 十二、未来发展趋势

未来研究重点将从：

text AI写RTL 

转向：

text AI设计硬件架构 

可能形成：

text Specification ↓ LLM ↓ Hardware MLIR ↓ Architecture Optimization ↓ CIRCT ↓ RTL ↓ Simulation ↓ PPA Feedback ↓ LLM优化 

形成：

自动设计闭环。

---

# 十三、对课题的启示

当前主流路线：

text 自然语言 ↓ RTL 

属于代码生成。

可进一步扩展为：

text 自然语言 ↓ Hardware MLIR ↓ Architecture Search ↓ RTL ↓ Simulation ↓ Performance Feedback ↓ LLM优化 

最终实现：

text 软件 ↓ 操作系统 ↓ 编译器 ↓ ISA ↓ 硬件架构 ↓ RTL ↓ FPGA/ASIC 

全流程协同优化。

---

# 总结

该领域的发展逻辑可以概括为：

text RTL设计 ↓ HLS ↓ DSE ↓ LLM生成RTL ↓ RTL专用模型 ↓ Agent设计系统 ↓ Graph/IR表示 ↓ MLIR/CIRCT ↓ 自动架构设计 

未来研究重点将从：

"AI生成代码"

转向：

"AI生成硬件架构并自动优化"。