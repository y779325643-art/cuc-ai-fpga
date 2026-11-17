# P01 资产审计：旧版共享契约结构生成研究

日期：2026-10-21。范围依据[进度清单 P01](../2026-10-21-structure-generation-paper-checklist.zh.md)：为旧版 M3/M4、共享生成契约、首次生成且无修复的独立缩减研究准备材料。本文是内部审计，不是论文正文、候选模型输入、实验结果发布或运行许可。

本篇沿用旧版 System-HIS 研究范围；PC 2.1 迁移不是本篇前置条件。仓库现行 paper1-v2.2 及其官方实验边界不因本文改变。P01 验收是可追溯的资产与候选表；**静态资格不等于运行资格，本文不验收 P04。** 本轮只读取文件、计数、核对归档及哈希，没有调用生成模型、导入执行生成器、重跑 HDL 工具、执行研究评估或修改实现。

## 证据分级与审计口径

| 等级 | 本文含义 | 允许的使用 |
| --- | --- | --- |
| A：原件存在且可静态交叉核对 | 需求、候选字节、阶段 JSON/日志、轨迹或校验清单可对应；不保证 provenance 完整 | 作为 P04 恢复输入与核查对象；限于实际保存范围描述旧执行记录 |
| B：只有摘要或缺少运行绑定 | 报告/summary 存在，缺完整命名 run 包，或同名样例没有配置/字节绑定 | 历史线索，不能替代原始通过证据 |
| C：元数据声明或来源不完整 | source、natural_llm、L3 等标签存在，但真实调用出处、独立功能验证或配置缺失 | 资产发现与案例筛查，不能直接计算方法效果 |
| D：目标/尚未实现 | 目录身份、规范、计划，没有对应执行产物 | 说明范围与缺口，不计入结果 |

A 不意味着本轮重放成功，也不意味着候选行为正确。SHA-256 一致证明与现有清单一致，不证明最初生成过程或功能正确。所有数量均由对应文件/目录计算；不同运行、变异、模板和模型样例不合并为一个实验分母。

## 资产矩阵

| 资产 | 实际保存与数量 | 等级及可支持内容 | 本篇的最小后续工作 |
| --- | --- | --- | --- |
| 历史任务实现 | [机器账本](../../../../reports/evidence/task-ledger/sr2fpga-task-evidence-v0.1.json)共 74 家族：旧 71 加新 AI 3；31 generator/testbench implemented，43 not_implemented；31 中 22 embedded-SV、9 Python reference；最高级别标签为 29 L3、2 L4 | 账本声明；有原件部分为 A，其余需逐项分级。目录身份不是执行资格 | 使用[任务候选表](task-readiness.md)的明确 task_type 与原件；不把 74 或 31 当本篇已资格任务数 |
| 独立 Python oracle | [Phase C 原件](../../../../reports/evidence/legacy-runs/phase-c-independent-oracle-20260716-v2/dataset)保留 9 个样例、每家 4 类场景的 manifest/evidence、RTL、轨迹和工具记录；该批 9/9 参考记录到 L3 | A：参考与 oracle 的历史资格，不是 LLM 生成效果；每家只覆盖一个 width-8 配置 | 受信重建向量，核对数值/协议与正确参考，再取得本篇 P04 运行资格 |
| 变异检验 | 4 个命名 run 的原件合计 87 个：Line A 13、Phase B 14、Phase C core 15、Phase C independent 45；覆盖 21 个家族。逐项 JSON 显示 87 编译 passed/exit_code=0，87 仿真 failed 且含 TEST_FAIL | A：指定已知错误集合的检出记录；不是 87 个独立任务，也不是模型修复率 | 复核错误真值、等价性、覆盖局限及本篇采用修订；需要运行时另取得对应范围 |
| OpenXC7 物理案例 | [L4 run](../../../../reports/evidence/legacy-runs/line-a-l4-dual-tool-20260713-v2/dataset)有 FIR、matrix-vector MAC 两例；账本所列 8 个文件哈希均匹配；两份 openxc7_yosys.log 为空 | A，限 OpenXC7 logical_only。商业 L4、L5 在账本均为 0；run 名含 dual-tool 不证明两工具均通过 | 可作历史工具流背景或补充材料；不为本篇功能比较增加 PPA/上板主张，不补造空日志 |
| Phase D live pilot | [24 个归档样例](../../../../datasets/sr2fpga_phase_d_v1)：四来源 × 六配对需求；24 metadata/labels 均在，重算 12 GEN_FAIL、12 H2_FAIL，进入 L0–L3 为 0；release 清单 462/462 文件哈希匹配 | A：样例与阶段失败原件；B：原始完整 run/audit 包未找到。模型 ID 仅为 gateway 报告 | 单独保留为失败案例；不能拿 0/24 推断新方法效果，也不能把 repair_trajectory 桶当执行过修复 |
| Phase D controls | [6 个确定性样例](../../../../datasets/sr2fpga_phase_d_control_v1)均记录到 L3，FIR 另有 L4；其中 3 个 labels 声明 independent_oracle_status=pass。28/28 变异编译通过且仿真检出；861/861 清单文件哈希匹配 | A：基础设施与参考控制；不属于 24 个模型样本；与既有 21 家族重叠 | 作为参考恢复输入，不能加成额外独立家族或模型成功数 |
| H2 离线兼容分析 | [报告](../../../../reports/evidence/phase-reports/2026-07-17-sr2fpga-phase-d-failure-analysis-and-h2-hardening.md)、[分析器](../../../../agent/scripts/analyze_phase_d_h2_failures.py)、[测试](../../../../agent/tests/test_analyze_phase_d_h2_failures.py)存在。报告记载 H2 仍 0/12→0/12；语义标签诊断 31→21、协议诊断 18→9 | B：原始 analysis JSON 未找到；诊断减少不等于候选通过率提高 | 若引用数字，恢复指定修订的离线记录；不得用当前代码输出回填旧结果 |
| 旧通用数据归档 | [sr2fpga_rtl_v1](../../../../datasets/sr2fpga_rtl_v1)有 241 样例目录、231 labels、193 metadata | A/C 混合，多协议多阶段资产；没有统一实验资格 | 按来源/协议/原件完整度建立本篇纳入规则，不直接汇总历史成功率 |
| 旧自然模型标签 | 193 metadata 中 113 条 failure_origin=natural_llm；旧标签：L3 13、L0 45、L1 9、L0_FAIL 18、GEN_FAIL 18、L2 1、缺 labels 9 | C：自然来源标签不等于可证明的实际 API 调用；113 不是统一模型效果分母 | 新 M3/M4 对照使用新版本、共享契约和完整运行记录；旧样例仅作开发案例 |
| 重组 smoke | [reorganization summary](../../../../reports/evidence/legacy-runs/reorganization-final-smoke-fresh/runs/reorganization-final-smoke-fresh/summary.json)记载 24/24 确定性样例；该 run 目录没有 dataset | B。旧 dataset 中有同名 sample_t0_t4_deterministic_smoke 样例原件，不能因 run 包缺失否认这些原件存在；但没有 run/config/字节绑定，不能自动当作该命名 run 原件 | 分开记录“任务原件存在”和“命名运行谱系未绑定”；不补造对应关系 |
| 新 AI 三家族 | 账本三个新家族均 not_implemented/not_run，evidence_refs 为空 | D；不属于本篇范围 | 不作为首篇前置工作或效果结果 |

87 个变异的原件分别在 [Line A](../../../../reports/evidence/legacy-runs/line-a-oracle-evidence-20260713-v2/dataset)、[Phase B](../../../../reports/evidence/legacy-runs/phase-b-core-closure-20260713-v4/dataset)、[Phase C core](../../../../reports/evidence/legacy-runs/phase-c-core-mutation-closure-20260716-v2/dataset)、[Phase C independent](../../../../reports/evidence/legacy-runs/phase-c-independent-oracle-20260716-v2/dataset)各样例的 oracle_mutations。28 个 Phase D control 变异是另一批记录，不与 87 相加声称更多独立任务。

## 旧 L3 标签的关键限制

13 条 natural_llm/L3 标签中，静态文件扫描发现 8 条最终 TB 没有条件检查、TEST_FAIL 或时间/事件控制，仅打印 TEST_PASS。直接抽核的 [T4 TB](../../../../datasets/sr2fpga_rtl_v1/sample_l0_by_construction_t3_t4_after_width_parameters_t4_dual_stream_join_8_000002/attempts/attempt_000/generated_project/sim/tb_top.v)与 [T6 TB](../../../../datasets/sr2fpga_rtl_v1/sample_official_eval_gap_closure_llm17_t6_td_update_core_8_000001/attempts/attempt_000/generated_project/sim/tb_top.v)确为这种结构；两者轨迹将 TB 列为 model_generated，hidden/stress 为 not_run。

这证明自测验证不足，**不直接证明 RTL 错误，也不是 8/13 的功能误接受率**。须用独立真值确认正确/错误后才能量化。其余 5 条有刺激/条件检查也不自动成为可信功能通过。

另抽核 [T1 旧修复样例](../../../../datasets/sr2fpga_rtl_v1/sample_baseline_b_smoke_t1_event_counter_8_000001)：保留两次 L0 诊断/patch 和最后 lint/sim/synth 日志，TB 检查五个事件后的计数。它可作为窄覆盖工程案例，不能支持修复总体效果。三个抽核样例全部文件分别与旧清单 56/56、40/40、40/40 匹配；均未找到保存的 API 请求/响应、调用收据或完整运行配置，tool_versions 记录 unknown。T6 来源还是 oracle-HIS 条件，不能当作完整自然需求到模型契约的成功。

## 可重用原件与恢复边界

- 九家族 oracle 文件夹各保存 manifest.json 与 evidence.json，没有原始 .memh。实际 [load_oracle_bundle](../../../../agent/src/sr2fpga_agent/oracles/bundle.py)要求向量文件及哈希；只读 commitment 的入口不等价于可执行 bundle。
- Phase D 报告引用的原始 phase_d_audit.json、完整命名 run 包，以及 H2 hardening analysis JSON，在本次检查的 artifacts/datasets/reports 归档及报告指定旧 tmp 位置未找到。报告仍在，不能说这些报告或样例原件不存在；也不能把报告 APPROVED 当成现存可重放回执。
- 旧命名报告里的 tmp 路径、旧 LLM 包名、历史命令不是当前执行入口。当前代码与这些运行的确切版本绑定需 P02/P04 核查；本轮没有用 import、测试或工具执行证明兼容性。
- 当前 release 均为 internal_only、review_required，配置指纹标为 legacy_unavailable。参见 [release-scope](release-scope.md)；缺失的旧 provenance 不反向补造。

## P01 交付边界

本文件与[候选任务表](task-readiness.md)、[来源和公开范围](release-scope.md)共同完成资产盘点交付。待 P02 决定本篇准入、共同信息和结构责任，P04 才可恢复受信输入并运行资格检查。现有数字不支持新 M3/M4 效果、修复增益、物理优势或论文创新性主张；本篇仍无新增模型效果结果。
