# SR2FPGA Paper 1 M2 文献与论文定位重新验收

日期：2026-08-29

阶段：M2 — 现有方法与竞品方案分析

结论：**通过；按用户要求停留在 M2，不执行 M3 transition**

## 1. 修复输入

本轮以
[`m2-literature-positioning-audit-2026-08-29.md`](m2-literature-positioning-audit-2026-08-29.md)
为缺口清单，并以 `paper1-freeze-v1.7`、`docs/current-status.md`、当前
Paper-1 workspace 和可复核本地文献证据为权威。

未修改：

- Obsidian 历史日志和文献工作区；
- 历史 TCAD/TRETS BibTeX；
- 代码、实验协议、统计合同、官方 evaluator 或 campaign authority。

## 2. 完成的修复

### 2.1 Canonical citation registry

新增：

- [`../foundation/canonical-citation-registry.md`](../foundation/canonical-citation-registry.md)；
- [`../foundation/canonical-references.bib`](../foundation/canonical-references.bib)。

结果：

- 统一 34 个唯一 canonical keys；
- 消除 `rtlrepo`、`spec2rtl`、`phoenix` 三个历史别名；
- 27 项建立完整
  `key -> reader -> card -> source map -> PDF SHA-256 -> evidence ID`
  链路；
- 当时7项保留为 identity-ready；后续补强已将其中3项升级为 local-PDF
  source-verified、4项升级为 official-primary-page verified；
- discovery-only 工作不进入当前正式事实。

### 2.2 v1.7 当前派生写作材料

新增
[`../writing/m2-literature-positioning-v1.7.md`](../writing/m2-literature-positioning-v1.7.md)。

该派生稿明确：

- `M4-M3`、`M4-M0` 是 RQ1 primary Holm family；
- `M3-M2` 是 mandatory secondary representation-bundle estimate；
- 单个 primary 只激活对应局部主张；完整 RQ1 需要二者均通过；
- RQ2 使用独立 Holm family；
- RQ0 与 VPP population 分离；
- RQ4 是有界 physical-depth characterization；
- Paper-1 无 model training，且当前无 official method result。

### 2.3 检索计划与执行记录分离

新增
[`../foundation/literature-search-plan-and-execution-v1.7.md`](../foundation/literature-search-plan-and-execution-v1.7.md)。

该台账将 Scopus、WoS、IEEE Xplore、ACM DL、arXiv、Google Scholar、
CNKI 的计划检索标为 `待执行`，同时只把具有真实日志的 OpenAlex fallback、
exact-title refinement 和本地 mapping 列为 `已核实` 执行记录。未知命中数
保持 `not_available`，未推测或补写。

## 3. 三项验收

### 3.1 能够明确本文相对谁改进

判断：**满足**。

依据：当前派生稿按 module generation、tool repair、structured IR/intent、
repository evolution、cross-stage/FPGA evidence 分组，分别定义 prior-art
占位、禁止主张和 SR2FPGA 可检验的剩余位置。外部工作不再与 M0-M5
强行合并排名。

### 3.2 不足具体且有可追溯证据

判断：**满足，限于 registry 标明的证据状态**。

依据：27 项 claim-ready 工作有完整内容哈希和 evidence ID；其余工作按
local-PDF source-verified 或 official-primary-page verified 分层。会话型
cite/filecite 未进入当前派生稿。
“未发现”被限制在已执行检索范围和截止日期内。

### 3.3 改进方向与 v1.7 一致

判断：**满足**。

依据：派生稿直接采用当前 RQ1/RQ2 Holm family、secondary/descriptive
层级、RQ0/RQ4 边界、no-training scope 和 result-contingent claim language。
它没有修改 freeze，只将历史材料同步为当前写作口径。

## 4. M2 正式结论

M2 的 source-defined deliverables 已具备：

1. 现有方法对比表；
2. 不足分析；
3. 改进方向；
4. 相关文献清单。

三个 critical acceptance criteria 均通过。M2 因此在当前本地证据范围内
通过。

该通过不表示：

- 已完成截至投稿日的所有数据库增量检索；
- official-primary-page 工作已经具备本地 PDF hash 或完整 reader；
- G3/G4a/G4b 或 official experiment 已完成；
- 已产生任何方法效果、repair 效果或一般 FPGA 物理结果。

## 5. Transition hold

用户明确要求严格停留在 M2。因此本报告：

- 不更新 M3 状态；
- 不创建 M3 方法设计产物；
- 不授权 G5 或 official campaign；
- 只记录“M2 通过、transition held by user instruction”。

## 6. 当前路线卡

```text
当前站：M2——现有方法与竞品方案分析（验收通过，transition hold）
已经完成：canonical citation registry、统一 BibTeX、v1.7 派生定位、检索计划/执行台账
还需要：投稿前按真实平台完成增量检索；external-primary 工作按需补本地 PDF/reader
下一步：保持 M2，等待用户明确决定是否进入 M3 或继续补强 M2
需要你提供：若执行机构数据库检索，需要相应访问条件；当前本地修复无需补充
```
