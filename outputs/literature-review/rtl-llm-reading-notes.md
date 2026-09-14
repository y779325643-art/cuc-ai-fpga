# RTL LLM 重点论文与项目阅读笔记

> **状态：2026-06-06 文献阅读快照。** 本文中的训练与系统设想是背景研究，
> 不属于当前 Paper-1 方法或执行计划。当前 Paper-1 不训练模型；研究协议以
> [`paper1-freeze-v1.7`](../../docs/specs/2026-08-14-sr2fpga-paper1-research-program-design.md)
> 为准。

更新日期：2026-06-06

## 0. 阅读目标

本轮阅读围绕 HNAI-FPGA 的三个核心问题展开：

1. 如何评测自然语言到 Verilog/RTL 的生成能力？
2. 如何构造可用于 7B 级模型训练的高质量数据？
3. 如何把规格分解、结构化中间表示、验证反馈和 EDA 目标引入模型，同时使最终推理尽量不依赖外部工具？

需要先明确一个边界：

- `训练阶段使用仿真、综合、等价检查产生标签，推理阶段不调用外部工具`，是可研究且相对合理的目标。
- `训练和推理都不使用任何验证工具，同时保证可综合、功能正确和时序闭合`，缺少可信监督信号，也无法形成严格验证。
- Alpha-RTL 在测试时直接使用 EDA 反馈并更新模型，因此不符合“最终推理不调用外部工具”的要求，但适合作为教师系统或数据生产系统。

## 1. VerilogEval

论文：[VerilogEval: Evaluating Large Language Models for Verilog Code Generation](https://arxiv.org/abs/2309.07544)  
代码：[NVlabs/verilog-eval](https://github.com/NVlabs/verilog-eval)

### 它解决什么问题

VerilogEval 首次把 RTL 生成评测组织成接近 HumanEval 的可执行评测：

```text
自然语言描述 + 固定模块头
→ 模型补全模块体
→ Icarus Verilog 编译与仿真
→ 与黄金实现比较
→ pass@k
```

原始版本从 HDLBits 选择自包含模块，排除了需要实例化其他模块的任务。它包含两套描述：

- `VerilogEval-human`：人工把波形、K-map、状态图等转换为文本，共 156 题。
- `VerilogEval-machine`：由 GPT-3.5 根据黄金 RTL 反向生成描述，并用生成代码能否通过测试进行筛选，最终约 143 道评测题。

其训练集还包含 8,502 个从 GitHub RTL 反向生成的描述—代码对。

### 评测设计

- 功能指标采用 `pass@k`，而不是 BLEU 或代码文本相似度。
- 组合逻辑在输入变化时检查，时序逻辑在时钟边沿检查。
- 测试向量结合人工关键样例和随机样例。
- 使用 Docker 沙箱执行不可信代码。

### 关键局限

- 主要是短小、单模块、自包含问题。
- 测试平台不完备时，`pass` 只意味着通过当前测试，不等价于形式等价。
- 不衡量多模块集成、资源、时序、功耗、接口协议和板级可部署性。
- machine 描述偏低层，容易接近逐行解释，与真实高层需求存在分布差异。

### 对 HNAI-FPGA 的启示

HNAI-FPGA 不应只报告一个“生成成功率”。建议建立分层指标：

```text
L0：结构化需求/HIS schema 合法率
L1：架构约束合法率
L2：RTL 编译率
L3：功能仿真通过率
L4：接口/CDC/位宽规则通过率
L5：预测资源及时序误差
L6：真实综合和板级验证率（仅研究评测阶段）
```

第一项复现任务应是固定 VerilogEval 版本、采样参数和 pass@k 计算方式，建立不可随意变动的评测底座。

## 2. RTLLM

论文：[RTLLM: An Open-Source Benchmark for Design RTL Generation with Large Language Model](https://arxiv.org/abs/2308.05345)  
代码：[hkust-zhiyao/RTLLM](https://github.com/hkust-zhiyao/RTLLM)

### 它比 VerilogEval 多了什么

RTLLM 更接近完整自然语言到设计 RTL：

- V1.0 约 29 个设计。
- 每个设计包含自然语言描述、testbench、人工验证 RTL 和模型生成 RTL。
- 评价目标分为语法、功能和设计质量三个层次。
- 引入 `self-planning`：模型先输出设计计划，再生成 RTL。

### 应重点理解的评测结构

RTLLM 的价值不在题量，而在评价维度：

1. `Syntax`：是否能够编译或综合解析。
2. `Functionality`：是否通过给定 testbench。
3. `Design quality`：生成实现相对于参考设计的综合质量。

这比 VerilogEval 更适合 HNAI-FPGA，因为项目目标不是补全 HDLBits，而是从功能描述生成有设计意义的模块。

### 关键局限

- 设计数量较少，统计稳定性弱。
- 自然语言描述仍比真实标准文档短。
- testbench 覆盖率决定功能结论的可信度。
- 版本之间的任务和评测脚本有变化，复现实验必须明确使用 V1.0、V1.1 或 V2.0。

### 对 HNAI-FPGA 的启示

应借用其“三层目标”，但扩展为：

```text
语法正确
→ 功能正确
→ HIS 一致
→ 架构约束满足
→ 预测 PPA 合理
→ 实际 FPGA 实现可行
```

同时保留 self-planning 作为一个基线，用来证明 HIS-L0/L1 并不只是“让模型多想一步”，而是具有 schema、合法性检查和确定性 lowering 的正式表示。

## 3. VeriGen

论文：[VeriGen: A Large Language Model for Verilog Code Generation](https://arxiv.org/abs/2308.00708)  
项目：[shailja-thakur/VGen](https://github.com/shailja-thakur/VGen)

### 核心方法

VeriGen 属于早期领域继续预训练/微调路线：

- 从 GitHub 和 Verilog 教材收集语料。
- 在 CodeGen 系列模型上继续训练，重点模型为 CodeGen-16B。
- 使用自建题目和 testbench 评估语法与功能正确性。

相关工作中，CodeGen-Verilog 语料约由 300 MB GitHub Verilog 和 400 MB 教材数据组成。结果证明领域语料确实可以显著提升 Verilog 语法和局部功能生成能力。

### 真正值得学习的地方

- 它证明“通用代码模型 + HDL 领域适配”是可行的。
- 它把语法正确与功能正确分开，避免把能编译等同于设计正确。
- 公开了模型、语料获取和评测资源，适合了解最早期训练管线。

### 不应直接照搬的地方

- 16B 模型训练成本高于当前必要水平。
- 原始语料混合代码、注释和教材文本，质量控制较粗。
- 训练目标偏代码续写，不是严格的自然语言规格到 RTL 对齐。
- 数据污染和训练/评测泄漏控制不如后续 CodeV 完善。

### 对 HNAI-FPGA 的启示

VeriGen 更适合作为历史基线。当前项目没有必要从 16B CodeGen 复刻起步；应使用较新的 7B 代码模型，并把预算放在 HIS 数据质量、结构化输出和验证标签上。

## 4. RTLCoder

论文：[RTLCoder](https://arxiv.org/abs/2312.08617)  
代码、数据、训练脚本：[hkust-zhiyao/RTL-Coder](https://github.com/hkust-zhiyao/RTL-Coder)

### 为什么最适合先复现

RTLCoder 提供了相对完整的开放链路：

```text
领域关键词
→ GPT 生成设计指令
→ 指令扩展/变异
→ GPT 生成参考 RTL
→ 构造约 27K 指令—RTL 对
→ 7B 模型微调
→ 代码质量反馈训练
→ VerilogEval + RTLLM 评测
```

官方仓库提供：

- `Resyn-27k.json`
- 数据生成脚本
- Mistral 7B 和 DeepSeek-Coder 6.7B 模型
- 推理与 benchmark 脚本
- 质量反馈训练实现
- 4-bit 量化版本

### 代码质量反馈

其关键思想不是只对所有 token 使用等权交叉熵，而是为训练代码计算质量分数，并将质量信号反馈到训练损失中，使模型更偏向高质量 RTL。该方法在工程上比直接进行昂贵 RL 更容易复现。

### 数据方面的主要问题

- 训练答案本身由 GPT-3.5 生成，功能正确性不能保证。
- 指令先生成、代码后生成，容易产生不真实的“教材式问题”。
- 仓库明确提醒 27K 数据中可能存在错误。
- 后处理依赖截断 `endmodule` 等启发式规则，说明模型输出协议并不稳定。

### 对 HNAI-FPGA 的直接借鉴

建议把 RTLCoder 作为第一个训练基线，但将训练对改为：

```text
HIS-L0 → HIS-L1
HIS-L1 → RTL
失败诊断 + 旧 HIS-L1 → 新 HIS-L1
```

代码质量分数也应升级为多项质量向量：

```text
schema_valid
rule_valid
compile_pass
simulation_pass
resource_margin
timing_margin
interface_consistency
```

不要过早把它们压成单个标量，否则难以解释模型究竟学会了哪类约束。

## 5. CodeV

论文：[CodeV: Empowering LLMs for Verilog Generation through Multi-Level Summarization](https://arxiv.org/abs/2407.10424)  
代码与模型：[IPRC-DIP/CodeV](https://github.com/IPRC-DIP/CodeV)

### 数据构造的核心转向

CodeV 对 RTLCoder 的关键批评是：既然 GPT 不擅长生成 Verilog，就不应让 GPT 生成训练答案。

它改为：

```text
真实开源 Verilog
→ 过滤、去重、语法检查
→ GPT 先生成细粒度功能解释
→ 再从解释抽象出高层需求
→ 高层需求—真实 Verilog 配对
→ 7B 模型 SFT
```

这是一种反向指令构造。模型只负责它更擅长的“代码理解与摘要”，目标 RTL 始终来自真实代码。

### 多层级摘要

先生成低层功能描述，再生成高层规格摘要，可以缓解两个问题：

- 直接摘要容易逐行复述代码。
- 直接写高层描述容易遗漏关键时序、端口和状态行为。

CodeV 最终构造约 165K 描述—代码对，并对 VerilogEval、RTLLM 做相似度去污染。其数据规模消融显示，7B 模型从 27K 增长到 100K/165K 后收益逐渐减小，说明后续重点应转向质量与任务覆盖，而非无限扩量。

### 对 HIS 的最佳映射

CodeV 的方法可以直接升级为：

```text
真实 RTL
→ AST/CFG/DFG/模块层次抽取
→ LLM 生成低层行为描述
→ 程序 + LLM 共同生成 HIS-L2
→ 汇总生成 HIS-L1
→ 汇总生成 HIS-L0/SPEC
```

关键改进是：HIS-L1/L2 不能完全依赖自然语言摘要，应由 RTL parser 提取的端口、位宽、时钟、状态、模块实例和数据依赖提供硬约束。

### 复现建议

CodeV 的数据路线比 RTLCoder 更适合成为 HNAI-FPGA 的主训练集生产方法。推荐先复现 RTLCoder 跑通训练，再立即转向 CodeV 式“真实 RTL 反向构造”，不要长期依赖 GPT 生成 RTL 标签。

## 6. BetterV

论文：[BetterV: Controlled Verilog Generation with Discriminative Guidance](https://arxiv.org/abs/2402.03375)

### 核心贡献

BetterV 在普通 SFT 模型之外增加任务特定的生成式判别器。训练阶段使用 EDA 工具为样本打标签，例如：

- 语法是否通过。
- 是否与参考设计功能等价。
- 综合后网表节点是否更少。
- SAT 验证运行时间是否更短。

推理时，判别器通过调整下一 token 的概率，引导基础模型生成具有目标属性的 RTL。

### 为什么它与“无外部工具推理”高度相关

BetterV 的重要意义是把外部工具产生的偏好蒸馏到一个判别模型中：

```text
训练阶段：EDA 工具 → 属性标签 → 判别器
推理阶段：生成模型 + 判别器 → 受控 RTL
```

因此，推理时可以不再实时运行综合或等价检查。它比“让主模型自己声称时序满足”更可信，因为存在独立属性模型。

### 局限

- 判别器学习的是训练分布内的代理目标，不是真实证明。
- 网表节点数和 SAT 时间不等价于 FPGA 上的 LUT、BRAM、DSP、WNS 和功耗。
- 每种目标通常需要专门的标签和判别器。
- token 级引导计算成本高，且可能损害功能正确性。

### 对 HNAI-FPGA 的直接方案

可以训练一组 FPGA 属性预测头或轻量判别器：

```text
P(compile)
P(function_correct)
LUT/FF/DSP/BRAM regression
WNS/Fmax regression
P(interface_valid)
P(HIS_consistent)
```

Agent 在最终推理中使用这些内置预测器筛选和反思，而不调用 Vivado。论文表述必须称其为“预测性约束评估”，不能称为真实时序闭合验证。

## 7. Spec2RTL-Agent

论文：[Spec2RTL-Agent](https://arxiv.org/abs/2506.13905)  
官方页面：[NVIDIA Research](https://research.nvidia.com/publication/2025-06_spec2rtl-agent-automated-hardware-code-generation-complex-specifications-using)

### 它真正做了什么

Spec2RTL-Agent 面向 AES、DSS、HMAC 等复杂标准规格文档，包含三个关键模块：

1. 推理与理解：把非结构化规格拆成分步实现计划和子功能。
2. 渐进编码：在伪代码、Python、C++ 等表示间逐步细化。
3. 自适应反思：定位错误来自规格理解、算法实现还是 HLS 可综合性。

它没有直接生成 Verilog，而是生成可综合 C++，再通过 HLS 得到 RTL。

### 评测中最值得关注的指标

论文以三份规格文档评测，重点不是 pass@k，而是：

- 最终正确任务数。
- 人工干预次数。
- 代码尝试次数。
- 去掉理解、渐进编码、反思模块后的消融。

完整系统在三个任务上得到正确实现，并报告相较人工流程最多减少约 75% 的人工干预。

### 局限

- 只有三类规格，外部有效性有限。
- 走 C++/HLS 路线，不等同于直接 RTL 架构生成。
- Agent 的成功依赖 HLS 和执行反馈，因此不是无工具推理。
- “复杂规格理解”与“FPGA 物理约束优化”仍是两个不同问题。

### 对 HNAI-FPGA 的借鉴

最值得借鉴的是错误归因，而不是多 Agent 数量。建议 Agent 状态明确记录：

```text
spec_error
his_l0_error
architecture_error
lowering_error
rtl_error
verification_error
physical_prediction_error
```

HIS 可以取代自由文本 implementation plan，使每次反思落在确定字段上。HNAI-FPGA 与 Spec2RTL-Agent 的差异应表述为：

> Spec2RTL-Agent 解决长规格到 HLS 实现的流程自动化；HNAI-FPGA 研究分层硬件意图 IR、IR 约束检查以及非 DNN 算法到 FPGA 架构的映射。

## 8. CPPL

论文：[CPPL: A Circuit Prompt Programming Language](https://arxiv.org/abs/2605.17892)  
代码：[SawyDust1228/CPPL](https://github.com/SawyDust1228/CPPL)

### 与 HIS 最接近的思想

CPPL 认为：

- 直接生成 RTL 难以静态检查和优化。
- 直接生成 CIRCT/MLIR 又受 SSA、类型、dialect 和位宽规则限制。
- 应在 LLM 与 CIRCT 之间设计一个更容易生成的 JSON 电路 IR。

其结构为：

```text
Python frontend DSL：声明模块接口与层次
→ LLM 生成 CPPL JSON IR
→ 编译器推导位宽、检查层次和端口绑定
→ 确定性 lowering 到 CIRCT
→ SystemVerilog
```

### 对 HIS 的关键挑战

CPPL 在 2026 年 5 月 18 日才公开，但它已经占据了“LLM 友好 JSON IR + 静态检查 + CIRCT lowering”这一研究位置。HNAI-FPGA 不能再仅以“提出 JSON 中间表示”作为创新。

HIS 必须明确超出 CPPL：

| CPPL | HIS 应承担 |
| --- | --- |
| 电路操作和模块连接 | 算法、架构、资源、接口、验证和实现映射 |
| 位宽、层次、端口合法性 | 并行度、流水、存储 banking、吞吐、资源预算、时序目标 |
| 通用 RTL benchmark | GA/RL/路径规划等非 DNN 算法到架构映射 |
| CIRCT lowering | 约束驱动架构搜索与反馈回写 |

### 当前证据状态

这是非常新的 arXiv v1 工作，尚需检查：

- JSON schema 的表达完备性。
- 是否支持时序逻辑、FSM、存储和多模块复杂结构。
- RTLLM 中提升来自 IR 本身还是更强的约束提示。
- 编译失败和功能失败分别发生在哪一层。

但无论结果如何，CPPL 都应成为 HNAI-FPGA 最重要的直接相关工作之一。

## 9. CodeV-R1 与 Alpha-RTL

### 9.1 CodeV-R1

论文：[QiMeng-CodeV-R1: Reasoning-Enhanced Verilog Generation](https://arxiv.org/abs/2505.24183)  
代码、模型、数据：[IPRC-DIP/CodeV-R1](https://github.com/IPRC-DIP/CodeV-R1)

CodeV-R1 将 Verilog 生成转化为带可验证奖励的强化学习任务，主要包含：

1. 规则驱动 testbench 生成和黄金参考等价检查。
2. round-trip 数据构造：

```text
真实 Verilog
→ 生成自然语言描述
→ 根据描述重新生成 Verilog
→ testbench 检查与原设计是否等价
→ 过滤不一致数据
```

3. `distill-then-RL`：
   - 先蒸馏推理轨迹，提供冷启动。
   - 再使用自适应 DAPO 进行 RLVR，降低采样成本。

论文报告 7B 模型在 VerilogEval v2 和 RTLLM v1.1 上达到较强 pass@1。官方仓库已开放 SFT、RL、测试平台生成和数据，复现价值高。

对 HNAI-FPGA 最重要的不是照搬“长思维链”，而是设计分层可验证奖励：

```text
R = R_schema
  + R_his_constraint
  + R_compile
  + R_function
  + R_resource_prediction
  + R_timing_prediction
```

应采用门控奖励：只有 schema 和功能通过后，才计算 PPA 优化奖励，避免模型用错误设计换取低资源。

### 9.2 Alpha-RTL

论文：[Alpha-RTL: Test-Time Training for RTL Hardware Optimization](https://arxiv.org/abs/2606.05253)

Alpha-RTL 于 2026 年 6 月 3 日提交，当前仅是非常新的 arXiv v1。它提出 TTT-RTL：

```text
针对一个具体 RTL 任务采样候选
→ 语法与仿真验证
→ 综合得到 PPA 奖励
→ PUCT 状态池复用优质设计
→ 测试时策略梯度更新模型
```

与普通 Agent 搜索不同，它不是冻结模型后反复提示，而是在每个待设计问题上进行测试时训练。论文报告 RTLLM v2.0 上 PPA product 相对参考实现显著降低，并在工业 FPU 子模块上报告 ADP 改善。

### 与当前项目目标的关系

- 它非常适合训练阶段生成“设计—反馈—改进”轨迹。
- 它可以作为教师或上界系统，产生用于蒸馏的优化样本。
- 它不符合最终无外部工具推理，因为测试时持续调用语法、仿真和综合工具。
- 其最新结果必须等待代码、重复实验和同行评审后再作强结论。

## 10. 横向比较

| 工作 | 核心问题 | 数据来源 | 外部验证 | 最值得借鉴 |
| --- | --- | --- | --- | --- |
| VerilogEval | 如何评测 | HDLBits | 推理评测时仿真 | pass@k 与功能测试 |
| RTLLM | 如何评测真实设计 | 29 个设计 | 仿真/综合 | 语法—功能—质量三级目标 |
| VeriGen | 领域微调是否有效 | GitHub + 教材 | 评测时 testbench | HDL 继续训练基线 |
| RTLCoder | 如何低成本训练 7B | GPT 合成 27K | 质量反馈与评测 | 完整开放复现链 |
| CodeV | 如何提高训练标签质量 | 真实 RTL 反向摘要 | 语法过滤 | 多层描述与反向数据构造 |
| BetterV | 如何控制生成属性 | 真实/增强 RTL | 训练阶段 EDA 打标 | 将 EDA 偏好内化到判别器 |
| Spec2RTL-Agent | 如何处理长规格 | 标准文档 | HLS/执行反馈 | 规格分解与错误归因 |
| CPPL | 如何连接 LLM 与 CIRCT | RTLLM 等 | 编译器静态检查 | LLM 友好 JSON IR |
| CodeV-R1 | 如何使用可验证奖励 | round-trip 数据 | RL 阶段 testbench | 分层 RLVR |
| Alpha-RTL | 如何优化单个设计 PPA | 在线候选轨迹 | 测试时 EDA | 教师系统与测试时适应 |

## 11. 对 HNAI-FPGA 的综合结论

### 建议的研究主线

```text
CodeV 式真实 RTL 反向构造
        ↓
SPEC → HIS-L0 → HIS-L1 → HIS-L2 数据
        ↓
RTLCoder 式 7B SFT 基线
        ↓
CPPL/CIRCT 式静态合法性与确定性 lowering
        ↓
BetterV 式内置属性预测器
        ↓
CodeV-R1 式分层可验证奖励
        ↓
Agent 基于 HIS 字段进行反思和修正
```

### 建议的创新边界

不能再把以下内容单独作为主要创新：

- 自然语言生成 Verilog。
- 使用 Agent 多轮修复代码。
- 提出一个 JSON 电路 IR。
- 使用仿真结果作为奖励。

更有辨识度的贡献应是：

1. 面向非 DNN AI 算法的分层硬件意图表示，而不是通用门级/RTL JSON。
2. 从算法语义到并行、流水、存储和接口架构的可检查映射。
3. 真实 EDA 反馈蒸馏得到的 FPGA 属性预测器，使部署推理无需调用外部 EDA。
4. 以 HIS 字段为动作空间的约束驱动 Agent 修正，而非自由文本 RTL 重写。
5. 同时评估生成正确性、属性预测误差和实际 EDA 迭代减少量。

### 推荐复现顺序

1. 固定 VerilogEval 与 RTLLM 评测环境。
2. 复现 RTLCoder 7B SFT，得到训练与评测基线。
3. 复现 CodeV 数据构造，在相同基础模型和样本规模下对比数据质量。
4. 实现 HIS-L0/L1 schema，并将 CodeV 多层摘要改造为 SPEC/HIS 反向构造。
5. 复现 BetterV 的一个简单属性判别器，例如编译成功率或 LUT 档位预测。
6. 复现 CPPL 的 RTLLM lowering 流程，明确 HIS 与 CPPL 的功能边界。
7. 构建 Spec2RTL 风格的单 Agent/多模块消融。
8. 最后再进行 CodeV-R1 风格 RL；没有稳定 verifier 前不要先做 RL。

## 12. 建议的第一个可发表实验

使用同一个 7B 基础模型、相同样本数和相同评测集，对比四种训练数据：

```text
A. RTLCoder：GPT 指令 → GPT RTL
B. CodeV：真实 RTL → 单层描述
C. CodeV：真实 RTL → 多层描述
D. HNAI：真实 RTL → HIS-L2 → HIS-L1 → HIS-L0
```

评价：

- VerilogEval pass@1/pass@5
- RTLLM syntax/function score
- HIS schema 合法率
- RTL 与 HIS 的端口、位宽、时钟和模块一致率
- 未调用 EDA 时的资源/WNS 预测误差
- 实际综合验证的首次成功率

这个实验能够直接回答：

> 结构化分层硬件意图表示是否比普通自然语言描述更有利于 RTL 生成、约束一致性和物理属性预测？

这比单纯再做一个 Agent 或再训练一个 Verilog 7B 模型更容易形成清晰的学术贡献。

