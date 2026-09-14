# SR2FPGA 术语表（2026-09-08 命名，2026-09-10 同步）

来源：用户指定的 `26.09.08 术语最新命名.md`。本表统一论文、现行说明和
界面用词，不改变研究问题、方法条件、执行权限、指标、合约版本或历史结果。

## 固定命名

| 旧称 / 对象 | 正式英文名称 | 缩写 | 中文名称 | 对象边界 |
| --- | --- | --- | --- | --- |
| Architecture-HIS | Design-Space Contract | DSC | 设计空间契约 | 定义变量、取值域、语义变换、不变量和跨变量约束 |
| Architecture-HIS 的一个实例 | Design Point | DP | 架构设计点 | 搜索实际采样、变异和选择的单个候选，不是整个空间 |
| System-HIS | Project Contract | PC | 工程契约 | 一个设计点的接口、层次、数据流、时序、资源、验证和工件义务 |
| 生成的完整工程 | FPGA Project Package | FPP | FPGA 工程包 | RTL、约束、manifest、build metadata 和相关产物 |

首次使用写全称和缩写，此后使用缩写。不要为了避免重复而另造同义名称。
DSC 约束整个空间，DP 是该空间中的单个候选；不要把 DP 的 genotype 职责写成 DSC。
具体版本对对象附加的字段和语义仍由原规范约束，本次只同步名称。

## 流程与实现边界

命名表的研究设计流程如下，不表示整个搜索流程已经实现或获得实验授权：

```text
Requirement Envelope
  → Design-Space Contract (DSC)
  → Design Point (DP)
  → Project Contract (PC)
  → FPGA Project Package (FPP)
  → Public Evaluation
  → Sealed Terminal Project
  → One-Shot Hidden Evaluation
```

现有 M0–M5 条件并非全部经过 DSC/DP 搜索：M0/M1 直接生成 FPP，M2 先生成
非类型化计划再生成 FPP，M3–M5 通过 PC 生成 FPP。方法编号、差分条件和预算不变。
H0–H3 是 PC 相关检查，分别检查格式、内部一致性、可降低性和需求忠实度；
检查通过不等于独立功能验证或正式 VPP 通过。

PC 不应被改称 circuit IR、executable semantics 或功能证明。
论文首次涉及实现格式时使用：

> Project Contract (PC), serialized by the current implementation as System-HIS v1.2.

## 保持兼容的内部名称

- 保留 `System-HIS v1.2` 作为现有序列化格式名称，不创造 `PC v1.2` 新版本。
- 保留 `system_his`、`system-his-v1.2`、`schema_version`、`REQ2HIS`、
  `HIS2PROJECT` 及既有 Python/API/CLI/Schema 标识、路径和 JSON 字段。
- FPP 的现有 manifest 格式仍为 `project-package-v1`。方法中立的工程包交付
  约束不等于 PC；Direct 条件不因此被要求生成 PC。
- 论文显示名称可写 M3 PC-Free、M4 PC-Skeleton、M5 PC-Online；内部条件始终为
  `M3`、`M4`、`M5`，旧显示名 HIS-Free、HIS-Skeleton、HIS-Online 仅用于历史追溯。
- 技术格式文档、代码示例、原始诊断、历史报告、运行产物和外部文献原文可以保留旧称。
  不回写历史记录，不把命名同步当成证据升级。
- Vault 源笔记保持原样。现行仓库文档引用本表；稿件之间不进行双向覆盖。

当前研究与执行状态仍以 [current-status](../current-status.md)、
[Paper-1 规范](2026-08-14-sr2fpga-paper1-research-program-design.md)
及其最新状态声明为准。DSC/DP 叙事不能静默改变现有 RQ、M0–M5 或实验门。
