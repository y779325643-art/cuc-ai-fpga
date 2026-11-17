# 路线 A：契约驱动的量化 AI FPGA 工程生成

2026-10-28 起，当前任务总体遵循 [Paper 1 v2.3 LLM 案例修订](../specs/2026-10-28-sr2fpga-paper1-llm-case-amendment-v2.3.zh.md)：量化 QKV 投影、KV cache decode attention、门控 FFN。方法与评测规则继承 v2.2，正式实验仍未授权。可执行固定开发入口见 [LLM case guide](../../agent/src/sr2fpga_agent/tasks/README.md)。下方 v2.2 案例与整理时点说明保留历史范围。

工作区为 `cuc-ai-fpga`，本地分支为 `develop`。先核对根部 [WORKTREE.md](../../WORKTREE.md) 与 `git branch --show-current`。

## 目标与当前入口

本路线实现当前已采纳的 `paper1-v2.3` 及 v2.2 基础方法：利用 Project Contract、确定性结构构造和有预算的反馈修复，生成并验证量化 QKV、KV-cache decode attention、门控 FFN 的多文件 FPGA 工程。

| 当前问题 | 应读取的入口 |
| --- | --- |
| 实际能力、验证范围与缺口 | [当前工程状态](../current-status.md)，随后核对对应实现和证据 |
| 研究问题、总体、方法条件、预算与统计 | [LLM case amendment v2.3](../specs/2026-10-28-sr2fpga-paper1-llm-case-amendment-v2.3.zh.md) 与 [v2.2 基础计划](../specs/2026-09-15-sr2fpga-paper1-research-plan-v2.2.zh.md) |
| 目标架构与实现分工 | [代码架构规范 v2.1](../specs/2026-09-15-sr2fpga-paper1-code-architecture-development-spec-v2.1.zh.md) |
| PC 2.1 格式 | [合同设计](../specs/PC-2.1-AI-stream-contract-design.zh.md)、[注册 schema](../../contracts/pc/2.1/) |
| 从哪里继续迁移 | [迁移记录](../migrations/research-plan-alignment.md) |
| 开发命令与模块职责 | [Agent README](../../agent/README.md)、[PC 输入命令](../../agent/src/sr2fpga_agent/pc/README.md) |

## 保留的 2026-10-26 整理时点边界

- PC 2.1 已实现类型化公开源加载、配置级参数／域／连线／tensor 静态检查、确定性 RTL 结构构造和真实 parser 保护的行为装配；行为与物理正确性仍需实际评测。
- 三个 AI 家族的目录身份仍未获得总体资格；首个固定 DW→PW 开发参考现有独立整数 oracle、编译、完整仿真及通用综合证据。残差与 GEMM 尚待实现，开发结果不自动晋级目录账本。
- v2.2 已采纳但尚未冻结；迁移授权不等于官方实验授权。Training 位于 Paper-1 范围之外。
- 路线 B 的 DOT4-8 / PEAK8 测试台审计记录不能转成这三个 AI 家族的性能或资格证据。

下一步从迁移记录中选择明确的未完成切片，完成实现及其轻量开发验证。本次整理没有替换研究计划、启动实验或改变评价语义。

运行产物继续进入本 worktree 的 `artifacts/`。新的一般运行可使用 `artifacts/paper1-ai/<run-id>/`；已有协议和历史运行目录保持原样。路线 B 的入口见 [TB 可靠性](tb-reliability.md)。
