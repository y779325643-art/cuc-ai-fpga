# HORIZON（arXiv:2606.28279v1）与 SR2FPGA：借鉴、差异与重新定位

> **状态（2026-08-14）：冻结前的定位备忘。** 文献比较与差异分析仍可使用；
> 方法标签、实验 gate 和论文主张以
> [Paper-1 英文 canonical spec](../../../docs/specs/2026-08-14-sr2fpga-paper1-research-program-design.md)
> 为准。本文中的任务梯和待办不得作为当前执行计划。

> 分析日期：2026-08-12
> 论文：Cunxi Yu, Chenhui Deng, Nathaniel Pinckney, Brucek Khailany, *Agentic Hardware Design as Repository-Level Code Evolution*（HORIZON）
> 本文目的：不是复述论文，而是确定哪些思想可以吸收、哪些主张已不能再使用，以及 SR2FPGA 应如何保持可辩护的研究差异。

## 1. 先给结论

HORIZON 与 SR2FPGA 的重叠很高：二者都反对一次性 `prompt -> Verilog`，都把生成对象放进可执行工程环境，利用编译、仿真或其他工具反馈进行多轮修复，并保存轨迹。

因此，SR2FPGA **不应再把以下内容单独作为新颖性主张**：

- 把硬件设计作为 repository-level 任务；
- 让 agent 在工程中编辑、运行工具并修复；
- 用 evaluator/acceptance gate 驱动 RTL 收敛；
- 保存成功和失败的修复轨迹；
- “首次”实现全自动、无人干预的 RTL 工具闭环。

SR2FPGA 仍然可以形成清晰差异，但必须把主线收紧为：

> **从系统需求出发，以 typed System-HIS 作为需求—工程契约，用分层且相互隔离的工具/oracle 证据监督多文件 FPGA 项目生成，并把这些轨迹转化为可训练的多任务数据。**

用一句对比概括：

- **HORIZON 研究怎样让固定的通用 agent 在 git 仓库中持续演化，直到公开 evaluator 接受。**
- **SR2FPGA 研究怎样让模型从需求契约、失败、修复、综合/实现证据中学习，更好地生成完整 FPGA 项目。**

两者不是“谁包含谁”的关系。HORIZON 的中心是 **repository evolution protocol**；SR2FPGA 应把中心放在 **contract-grounded tool-verified learning**。

## 2. HORIZON 到底做了什么

### 2.1 任务封装

用户提供结构化 Markdown harness。bootstrap agent 将其编译成 project pack：

\[
p=(\pi_{agent}, E_p, A_p, \Gamma_p, \Omega_p)
\]

其中包含 agent policy、可执行 evaluator、acceptance predicate、git/artifact policy 和领域知识。每个问题被放进独立 git worktree；agent 编辑文件、调用工具、读取反馈，并提交通过版本或记录失败版本（论文 pp. 3-5，Fig. 1）。

### 2.2 git 不是日志附件，而是状态系统

HORIZON 把 git tree 当作版本状态，把 commit 当作接受检查点，把 diff 当作状态变化，把 git notes/logs 当作 evaluator 证据和回放记录。论文把轨迹写成：

\[
\tau_{0:D}=\{(s_t,a_t,r_t,s_{t+1},y_t)\}_{t=0}^{D-1}
\]

这点比 SR2FPGA 当前的目录式 attempt 记录更完整：HORIZON 的 repository history 本身就是 experience buffer；SR2FPGA 当前主要依赖 `attempt_*/`、`patch.diff`、`diagnosis.json` 和 `trajectory.json`。

### 2.3 实验结果应怎样读

论文使用固定 GPT-5.3 backbone，以单 agent、无人干预方式运行 ChipBench、RTLLM-2.0、Verilog-Eval-v2 和 9 个 CVDP 代码/验证生成类别。所有 suite 最终报告为 100% 完成，但有几个重要限定：

- ChipBench 的一个未通过任务被作者判定为原 benchmark 的 specification-harness defect，并按“resolved”计入 100%；
- iteration 0 不是独立模型的 Pass@1，而是第一次 agent evolution 之后的仓库状态；
- 这是 best-so-far benchmark convergence，不等于对隐藏语义的泛化正确率；
- agent 在修复期间能查看 simulator messages、failure traces 和 evaluator artifacts；最终 gate 通常仍是同一 benchmark harness；
- 论文自己明确指出 over-solving/reward hacking 风险，并建议把修复期诊断与最终隐藏评分分离。

HORIZON 最值得重视的结果不是“100%”，而是收敛代价：困难类别需要 19-82 轮，总计约 209.9M tokens，约 91% 是 cached input；CID 002、003、012 占据大部分预算。论文由此把研究瓶颈从最终 pass rate 转向 token efficiency、verification quality 和 delayed reward。

### 2.4 尚未完成的内容

论文定义了包含 `∆QoR` 的 reward vector，但本工作只报告 pass、coverage 和 token；QoR/PPA 留待未来。论文没有训练或更新 RL/agent policy，backbone 在 campaign 内固定；轨迹可用于 reward modeling、curriculum 或 offline agent-RL 只是未来用途。覆盖率也不是 acceptance objective，只是对 CID 012/014 的观察指标。

## 3. 差异矩阵

| 维度 | HORIZON | SR2FPGA 当前实现/目标 | 对定位的含义 |
| --- | --- | --- | --- |
| 核心问题 | 如何把硬件问题变成 repository-level self-evolution | 如何从系统需求和工具验证轨迹学习 FPGA RTL 项目生成 | 我们必须突出“学习”和“需求到工程”，不能只讲 agent loop |
| 输入契约 | 人写 structured Markdown harness，经 bootstrap agent 编译 | 自然语言需求 + platform profile，经 REQ2HIS 形成 System-HIS v1.2 | System-HIS 的 typed、可验证、可 lower 是第一差异 |
| 中间表示 | project pack 是控制平面，但论文未给出硬件语义 schema/H0-H3 | `top/components/instances/data_flow/control_flow/state/timing/resources/verification/artifacts` | 我们能研究表示消融、fidelity 和 lowerability；这是 HORIZON 没回答的问题 |
| 生成对象 | 可执行 repo；可包含 RTL、testbench、checker、assertion 等 | 多文件 FPGA project：HIS、manifest、RTL、SDC、testbench、predicted QoR | 我们的“project”边界更具体，也更受跨文件契约约束 |
| 状态与轨迹 | git worktree、diff、commit、notes/log；repo history 即 trace | 目录式 attempts + tool JSON/log + diagnosis + patch.diff + trajectory JSON | HORIZON 的 git-native trace 更强；这是应借鉴的工程机制，不是我们的新颖性 |
| 反馈/验收 | benchmark 原生 harness 的 pass condition；可选 coverage/QoR reward | H0-H3、L0-L4、independent oracle、mutation qualification、measured QoR | 我们应突出多层证据和 verifier separation，而不是笼统的 tool feedback |
| 防过拟合 | 论文明确识别 visible-harness reward hacking，但主要作为 future protocol | 已有 hidden/random/stress scenario 元数据、独立 Python oracle、oracle 修改后禁自动 pass、训练导出脱敏 | 这是最强的可实证差异之一，但必须用正式实验展示 |
| 学习 | 固定 GPT-5.3；不训练 policy；轨迹未来可训练 | 已实现 versioned trajectory/training-view contract 和多种导出；目标是统一模型 | 当前只能声称“学习数据管线已实现”，不能声称学习收益已证明 |
| 物理深度 | 本文不报告 PPA/QoR，后续工作 | L3 综合 QoR；两类代表 family 有 OpenXC7 L4；Vivado 0，L5 0 | 我们物理证据更深，但覆盖面仍窄，不能写成普遍部署能力 |
| 评测广度 | 多个公开 RTL/CVDP suite，任务数和类别广 | 31 个已实现 family；Paper 1 core 14/14 到 L3；公开基准对齐不足 | 对方的 benchmark breadth 更强；我们需要公开、held-out、可复现的对比 |
| 成本报告 | iteration curve、earliest-best、tokens、cache share | 当前状态文档主要报告 pass/evidence coverage，没有统一 token-efficiency 曲线 | 应补齐 attempts/tokens/time/EDA runtime 的收敛报告 |
| 自治方式 | hands-free，persistent session reuse，single agent | autonomous batch runner + configurable generation/repair attempts | 都能无人运行；“hands-free”不能作为独立贡献 |
| 最终研究产物 | framework + benchmark convergence trace | dataset + learned generator/diagnoser/repairer/critic/QoR predictor | 这是最应保持的分叉，但 learned-model 结果尚需闭环 |

## 4. 当前仓库证据：哪些差异已经是真的

### 4.1 已实现、可以据实使用

1. **typed System-HIS 合同与 H0-H3 记录路径**
   当前 canonical schema 位于 `contracts/system-his/system-his-v1.2.schema.json`。freeze spec 把 H0 定义为 schema-valid、H1 为符号/端点/宽度 well-formed、H2 为当前 lowerer 可生成、H3 为 requirement fidelity；运行时在进入 L0-L4 前调用 `validate_system_his_h_stages()`。但现有 H0 是手写结构子集，schema、checker、fixture、reset、lowerability 和 compatibility 仍需闭环，不能写成完整 JSON-Schema/W1-W10 已实现。

2. **跨文件 FPGA project contract**
   项目包含 `system_his.json`、`manifest.json`、RTL、约束、testbench 和 predicted QoR；L0 检查真实 top、端口、实例、SDC 和 testbench 的一致性。

3. **分层验证与独立 oracle**
   `DataGenerationAgent` 依次执行 H stages、L0、lint、simulation、synthesis，并可运行 OpenXC7/Vivado 路径。当前 labels 区分 public、hidden、stress、L3、L4-open 和 L4-commercial；工具/环境失败不直接记为模型失败。

4. **失败—诊断—补丁—复验数据**
   `DatasetRecorder` 持久化每个 attempt 的 generated project、tool logs/JSON、`diagnosis.json`、`patch.diff` 和 patch metadata；最终保存 `labels.json`、`measured_qor.json` 和 `trajectory.json`。

5. **轨迹到训练视图**
   recorder 已导出 `requirement_to_his`、`his_to_project`、`requirement_to_project`、`failure_to_diagnosis`、`failure_to_patch`、predicted/measured QoR 等视图，并对 withheld oracle 内容做训练侧脱敏。

6. **比 visible harness 更严格的信用规则**
   当前代码具有独立 oracle、mutation score、hidden/random/stress 类别，以及 oracle 或不允许的 edit surface 被修改后取消 automatic pass credit 的规则。这直接回应 HORIZON 在 Section 5 提出的 reward-hacking 风险。

### 4.2 仍是目标，不能写成已证明贡献

- 还没有从当前状态文档证明 unified SR2FPGA learned model 已经优于 direct/repair/HIS baselines；
- 还没有证明 family-held-out 或 requirement-held-out 泛化；
- OpenXC7 L4 只有两个代表 family，Vivado 当前为 `not_run`，L5 为 0；
- 当前 agent trace 不是 git-native worktree/commit trace；
- 当前公开 benchmark 广度和 HORIZON 不在一个量级；
- 当前没有与 HORIZON 同口径的 token、cache、iteration、wall-clock 和 evaluator-cost 报告。

## 5. 最值得借鉴的六点

### 5.1 把 episode pack 明确定义为控制平面

可将 HORIZON 的 project pack 思想吸收到 SR2FPGA，但改造成硬件语义更强的 **SR2FPGA episode pack**：

```text
requirement
+ platform profile
+ System-HIS contract
+ artifact/edit policy
+ repair-visible evaluator
+ final hidden oracle policy
+ acceptance vector
+ runtime/token budget
```

它不应替代 System-HIS；System-HIS 表达“要造什么”，episode pack 表达“如何生成、验证和记账”。

### 5.2 把每个 attempt 统一成 state-delta-evidence 决策

在不立即引入完整 git backend 的前提下，先让 `trajectory.json` 对每轮显式记录：

```text
state_before_hash
artifact_delta / patch_id
tool_calls
repair_visible_evidence
acceptance_vector
accepted_or_rejected
state_after_hash
tokens / wall_time / EDA_runtime
```

这样可获得 HORIZON 的可回放性，同时保持当前 immutable dataset contract。

### 5.3 报告收敛，而不只报告最终通过

正式实验至少报告：

- first-attempt、earliest-best、attempts-to-L2/L3/L4；
- cumulative tokens、uncached tokens、wall-clock、EDA runtime；
- 每个 failure family 的修复转移；
- 最后 5%-10% 样本消耗的预算比例；
- 达到相同 pass level 时 M0-M6 的成本差异。

这会让“轨迹学习是否提高效率”成为可检验问题，而不是只比较最终 pass rate。

### 5.4 把 HORIZON 的局限变成我们的正式实验

对每个 repair-visible evaluator，保留独立 final oracle，并增加：

- hidden randomized seeds；
- harness perturbation；
- independent reference model；
- mutation score；
- simulator/tool configuration holdout；
- oracle edit audit。

评价指标应区分 `visible_pass` 与 `hidden_semantic_pass`。这比单纯追求 100% benchmark convergence 更能支持 SR2FPGA 的“tool-verified learning”。

### 5.5 可选的 git-backed trace，不把它包装成论文核心贡献

git worktree 对长轨迹、回放、并行隔离和证据附着很有价值。可以作为 runner 的可选 trace backend：接受 attempt 形成 commit，拒绝 attempt 写 notes/rejection record。但论文中应明确引用 HORIZON，把它描述为基础设施借鉴，而不是 SR2FPGA 的新颖点。

### 5.6 借鉴 persistent session/cache，但把指标做完整

缓存可以降低多轮修复成本，但必须同时报告总 tokens、uncached/billed tokens、cache hit share、wall-clock 和 EDA runtime。否则“token 低”可能只是计费口径差异。

## 6. 不应照搬的内容

1. **不要把 100% pass 当作语义正确。** HORIZON 自己已经说明 visible harness 可能导致 over-solving。
2. **不要复用 iteration 0 作为 Pass@1。** 它包含一次 agent step，不是公平的独立生成基线。
3. **不要把 framework goal 写成已验证能力。** HORIZON 对 broader chip design 的外推是目标，不是实证；SR2FPGA 也应同样克制。
4. **不要把轨迹“可用于训练”写成“已经学会”。** 必须有 held-out 模型实验。
5. **不要用 project/repository 一词掩盖工程深度。** 必须逐项说明是否含 typed requirement、multi-file contract、constraints、independent oracle、synthesis、place-and-route、QoR 和 board evidence。
6. **不要把 git-native tracing 重新包装为我们的原创。** 最多作为被引用的基础设施设计。

## 7. 建议修改论文定位

### 7.1 建议主张

> SR2FPGA is designed as a contract-grounded learning framework for system-requirement-to-FPGA project generation. It uses a typed System-HIS contract and is designed to learn from multi-level, oracle-separated EDA trajectories spanning project consistency, simulation, synthesis, and selected physical implementation evidence; the learned held-out gain remains to be established.

中文：

> SR2FPGA 被设计为面向系统需求到 FPGA 工程生成的契约驱动学习方法。它以 System-HIS 连接需求与多文件工程，并计划从项目一致性、独立功能验证、综合以及代表性物理实现形成的 oracle-separated 轨迹中学习；learned/held-out 收益尚待新冻结实验建立。

### 7.2 与 HORIZON 的关系句

> HORIZON demonstrates that a fixed general-purpose agent can drive RTL benchmark repositories to convergence through git-native executable feedback. SR2FPGA addresses a different question: whether typed requirement/project contracts and oracle-separated physical evidence can be converted into supervision that improves a learned FPGA project generator beyond direct and repair-only agents.

### 7.3 建议实验轴

保留并强化以下方法阶梯：

```text
M0 Direct
M1 Direct-Repair / HORIZON-like repository loop
M2 Structured prompt
M3 HIS-Static
M4 HIS-Online repair
M5 HIS-Skills / memory
M6 SR2FPGA-Learned
```

其中 M1 是与 HORIZON 最接近的 matched baseline。核心检验不是“谁最终能 pass”，而是：

- 在相同 token/tool/attempt budget 下，谁更快达到 hidden L2、L3、L4；
- typed HIS 是否提升 first-attempt project consistency 和 hidden semantic pass；
- 轨迹学习是否减少 repair steps 和 evaluator cost；
- 在 held-out project families 上是否仍成立。

## 8. 近期优先级

### P0：论文与实验设计

- 删除或降级所有“首次 repository-level hardware evolution”“首次工具反馈修复”等主张；
- 把 HORIZON 加入 closest-work 和 M1 baseline 说明；
- 固化 visible-repair / hidden-final 两级评测；
- 补 attempts/tokens/time/EDA-cost 收敛指标；
- 将 family-held-out 设为主泛化切分。

### P1：轨迹合同

- 给 trajectory schema 增加 state hash、accept/reject、token/cache、wall-clock 和 evaluator runtime；
- 明确 repair-visible evidence 与 release-safe/hidden evidence 的边界；
- 加入 harness perturbation 与 oracle-edit audit 汇总。

### P2：基础设施

- 评估 optional git-worktree trace backend；
- 评估 persistent session reuse；
- 若 HORIZON 代码/project packs 可获得，再做严格可执行基线；否则只做 HORIZON-like matched baseline，不能宣称复现原系统。

## 9. 最终判断

HORIZON 不是让 SR2FPGA 失去意义，而是迫使我们停止用“agent + repository + tool feedback”作为宽泛新颖性。它把这个外层闭环变成了强基线。

SR2FPGA 能否形成独立贡献，取决于三件事能否被实验证明：

1. typed System-HIS 是否比 untyped/structured harness 更好地保持需求与跨文件工程一致性；
2. oracle-separated、分层到综合/实现的证据是否减少 visible-harness over-solving；
3. 由这些轨迹训练出的模型是否在 held-out project families 上，以更少修复和更低 EDA 成本达到更高的 hidden L2/L3/L4 通过率。

如果这三点闭环，HORIZON 是 SR2FPGA 最重要的外层基线和动机来源；如果没有 learned/held-out/hidden/physical 证据，SR2FPGA 就很容易被评审理解为 HORIZON 的一个 FPGA-specific engineering variant。

## 10. 仓库依据

- 当前能力与边界：`docs/current-status.md`
- 当前 Paper-1 研究规范：`docs/specs/2026-08-14-sr2fpga-paper1-research-program-design.md`
- System-HIS v1.2 freeze：`docs/specs/2026-06-24-sr2fpga-system-his-v1.2-freeze-design.md`
- canonical schema：`contracts/system-his/system-his-v1.2.schema.json`
- 生成、H-stage、L0-L4、repair loop：`agent/src/sr2fpga_agent/agent.py`
- autonomous campaign：`agent/src/sr2fpga_agent/runner.py`
- attempt、trajectory 和 training-view 持久化：`agent/src/sr2fpga_agent/recorder.py`
