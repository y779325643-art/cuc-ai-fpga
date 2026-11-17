# N15 同信息标准强对照：有限容量资格结果与差异判断

日期：2026-10-21。新增工件独占 `artifacts/responsibility-capacity-standard-baseline-20261021-01/`。这是标准 SMT-LIB + Z3 + 小型可信手工 manifest 的开发资格对照，不是 Pacti 复现、被测模型实验或 N15 的正式采纳。未改原任务、评分、正文、旧 artifacts 或原型，未运行 HDL/模型，未安装依赖。用户对新机制范围的选择仍不由本次执行代替。

**结果：7/7 个预定 Z3 过程均完成并符合数学控制；另 2 个元数据控制均 UNKNOWN，且未调用 solver。标准流程覆盖了本轮有限队列的来源/采纳门、环境一致性、溢出见证和保守充分条件非必要性诊断。当前没有据此保留一个必须由新增生成机制才能完成的判定能力。** 该结果不证明人工工时相同，也不否定其他系统贡献或完整领域的创新空间。

## 1. 模型、同信息输入与信任边界

固定容量 C=4、窗口 H=6、每事件到达 aᵢ∈{0,1}、blackout 下 dᵢ=0、`qᵢ₊₁=qᵢ+aᵢ`。q 表示要求完整保存的 backlog，而不是一个已自动丢弃超量数据的截断计数。检查环境是否非空之后，再问是否存在某 qᵢ>C。没有将 `q<=C` 作为全局前提隐藏溢出。这个数学模型没有声明原 UART 的正式环境语义，也没有证明 RTL 有效容量。

`fixtures.json` 和 `origin-adoption-manifest.json` 使用候选卡同名概念字段：`predicate, origin, locator, adoption, derivation_dependencies`。另有 typed kind/value 用于构造封闭的有限 SMT 公式，程序不执行 predicate 字符串。`origin` 是 public/library/proposal；`adoption` 是 existing/explicitly_accepted/unadopted。**这些标签由可信 fixture 作者手工给出**；程序没有从原文自动证明来源/蕴含，也没有鉴别真实硬件库的容量承诺。

本工件中的 explicitly_accepted 只描述手工数学 fixture 内已采纳的条件，不表示用户采纳了新的 UART 流量限制。源文件的哈希冻结保证本次输入未变，不把声明标签升级为语义证明或通用身份认证。模型自报 public/accepted 保留为未验证数据，不覆盖 fixture 的 authority/verification 决定。

实际代码定位：`artifacts/responsibility-capacity-standard-baseline-20261021-01/run_baseline.py:27`–`:53` 构造声明与控制；`:55`–`:58` 只提取可信且已采纳的环境条件；`:91`–`:106` 生成队列公式；`:181`–`:186` 对容量 unknown/未验证模型承诺直接返回 UNKNOWN。即使给定同一文本 bound，未采纳 proposal 也不进入断言。这些控制是明确的调用方数据边界，不是自动溯源成果。

## 2. 冻结配置与实际完整分母

所有 7 份 SMT 脚本、9 个 fixture、来源/采纳 manifest、独立数学预期、runner/collector 代码先冻结，再执行。c1/c2 为资格门，均符合预期后才继续 c3–c7。预算为最多 7 次 Z3，每过程外部 10 秒、每 query 内部 8000 ms；没有重试或额外 help/version 过程。版本 `Z3 4.15.5` 由 c1 同一预算过程内的 `get-info :version` 记录。

| Case | q₀及可信环境 A0 | Env | Overflow | 其他实际查询 | 最终判定 | 过程秒数 |
|---|---|---|---|---|---|---:|
| c1 | q₀=0；无总到达界，单步仍为 0/1 | SAT | SAT | — | 窗口内溢出见证 | 0.281142700 |
| c2 | q₀=0；已采纳 Σa≤4 | SAT | UNSAT | — | 窗口内安全 | 0.034671600 |
| c3 | q₀=0；Σa≤4 仅为 proposal，未断言 | SAT | SAT | — | 窗口内溢出见证 | 0.033077300 |
| c4 | q₀=2；已采纳 Σa≤4 | SAT | SAT | — | 窗口内溢出见证 | 0.034527200 |
| c5 | q₀=2；已采纳 Σa≤2 | SAT | UNSAT | — | 窗口内安全 | 0.033361400 |
| c6 | q₀=0；A0 为已采纳 Σa≤4 | SAT | UNSAT | A0∧¬(Σa≤3) SAT | 窗口内安全；Areq 非必要 | 0.034210800 |
| c7 | q₀=0；已采纳 Σa≤0 且 Σa≥1 | UNSAT | UNSAT | — | inconsistent，不记安全成功 | 0.039038900 |
| m1 | 总容量未知 | 未运行 | 未运行 | 元数据门 | UNKNOWN | — |
| m2 | 容量仅来自未验证模型承诺 | 未运行 | 未运行 | 自报标签不构成权限 | UNKNOWN | — |

分母：7 个 solver 控制、2 个无 solver 元数据控制；没有被测模型样本。3 个溢出见证、3 个窗口内安全、1 个空环境 inconsistent、2 个预定 UNKNOWN、0 个未跑的预定控制。7 过程均 exit 0，无 timeout 或工具 UNKNOWN；完成判据读取实际 SAT/UNSAT 标志而非仅看退出码。累计 Z3 过程 wall time 为 **0.490029900 秒**，不是人工工时，也不作为速度优势证据。

共有 15 次实际 query：10 次 SAT、5 次 UNSAT。每个 SAT model 均独立回放二值到达、初始占用、逐步守恒和已采纳条件；overflow query 还核实际超容量步骤。另一个纯 Python 整数实现穷举窗口内全部 64 条到达序列，得到预先固定的 env/bad 数：c1=64/7、c2=57/0、c3=64/7、c4=57/35、c5=22/0、c6=57/0、c7=0/0。这里没有将序列或工具 query 当成独立研究样本。

## 3. 两个决定性语义控制

**c6：不蕴含保守充分条件，不等于不可实现。** 手工提供的 Areq=Σa≤3 是本 fixture 的保守充分条件。检查 overflow 时只断言 A0=Σa≤4，没有偷偷加入 Areq；实际结果为 UNSAT。另一个查询得到 `a=[1,1,1,1,0,0]`、`q=[0,1,2,3,4,4,4]`，满足 A0∧¬Areq 且未溢出。独立枚举也得到 15 条这种到达序列。见 `runs/c6/{script.smt2,z3.log,witness-replay.json}`。因此本次并未把 A0⇒Areq 失败标为计划不可实现，也没有把一个保守条件称为最弱/必要假设。

**c7：空环境不能给出安全 credit。** 环境查询先得到 UNSAT，后面的 overflow UNSAT 是空前提造成的真空结果。实际输出 `status=inconsistent, assessment=unknown, credited_safe=false`；没有并入三个窗口安全项。见 `runs/c7/{script.smt2,z3.log,receipt.json}` 与 `classify()`（`:176`–`:179`）。

结果中的 feasible/infeasible 标签始终受 `finite_blackout_queue_H6` scope 限定：前者仅说明该窗口无 overflow，后者仅说明固定模型存在 overflow 反例。它们不是所有实现架构的可实现/不可实现结论，不是无限时域活性，也不是原 UART 已发生缺陷的实测。

## 4. 对新增机制的交接结论

在同一手工规范、同一 capacity/initial/backlog 动力学及同一采纳权限下，标准 SMT 流程能够完成本轮候选所需的这些诊断。一个小 manifest 也能避免把 proposal 当环境事实、把模型自报当授权、把空环境当安全，未出现只有新“模型—程序”机制才能消除的判定差别。

当前仍未实现的内容包括：从用户原文自动证明环境谓词、从 RTL/body 证明有效总容量、一般最弱假设综合、复杂协议抽象的完备性以及端到端生成交接。这些不因命名为 N15 就已完成，也不能把标准 baseline 没有在本次固定输入外实现的能力自动登记为候选新增成果。若要主张系统增量，应明确候选实际补了其中哪一项，以及同信息强基线的差异；本次只支持有限数学资格结果。

结论不涉及人工成本相等：没有计时规范编写、来源裁决、模型建立或集成调试；标准能力相同也不能推出整个领域没有创新。本文同样没有修改用户待选择的研究方向或把开发控制提升成正式论文证据。

## 5. 可复核记录

实际执行入口为 `run_baseline.py prepare`、`run_baseline.py run`、`run_baseline.py collect`，路径均在上述新 artifact 内。prepare/run 拒绝覆盖已有冻结/执行；collector 不调用 solver，只核对原始日志、模型、数学控制和文件哈希。完整命令、实际分母与限制在同目录 `results.md/json`。

- 冻结配置 SHA256：`888b761d5c7a511995b26d01530b55784a83a8a717d9497bbe620a83dbc782e3`。
- runner/collector SHA256：`3de9d584841e9e3ad3cbf2e0b91fb07a07b0b1b2af79b1cd422e20abc79e4d47`。
- Z3 可执行文件 SHA256：`c6b3a30e434d95242078b90ee9c39da76c4ab5cbc968638e2fff61576cc0df2f`。
- `results.json` SHA256：`edd6db60e03d9c9b92988213e039090f3f8622da27fb0d8fb5c0e673d798ced9`。
- 工件 checksum manifest SHA256：`b05c70cbfa662aa2246633faab8532d213f32583658a0fd9bdd73ede867581c3`，不包含 manifest 自身。

原始脚本、日志、return code/秒数、逐项 receipt、见证回放、来源声明、完整预定/未跑分母及 collector 的最终复核均保留。它们是此手工 finite fixture 的开发记录，不是新注册研究合同、Pacti 作者复现或正式 evidence promotion。
