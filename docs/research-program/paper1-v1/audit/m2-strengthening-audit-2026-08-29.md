# SR2FPGA Paper 1 M2 补强审计

日期：2026-08-29

状态：M2 已通过并继续补强；不进入 M3

## 1. 本轮目标

对上一轮 registry 中 7 项 identity-ready 工作检查本地原文，升级可直接
核验的证据，同时保持没有原文的工作为 `待核实`。

## 2. 完成结果

### 2.1 三项原文升级

HINT、RTLCoder、CVDP 的本地 primary PDF 已直接读取并固定 SHA-256，
新增
[`../foundation/supplemental-source-verified-evidence.md`](../foundation/supplemental-source-verified-evidence.md)
记录 page-level bounded claims：

- HINT：5 条 evidence claims；
- RTLCoder：4 条 evidence claims；
- CVDP：5 条 evidence claims。

它们的状态由 `待核实` 升为 `原文已核实`，但未冒充完整
reader/card/source-map chain。

### 2.2 RTLCoder 元数据修正

统一 BibTeX 中 RTLCoder 从历史 arXiv 简表升级为 PDF 直接核实的正式
出版元数据：IEEE TCAD 44(4), 1448–1461, 2025，DOI
`10.1109/TCAD.2024.3483089`。

### 2.3 Related Work 补强

[`../writing/m2-literature-positioning-v1.7.md`](../writing/m2-literature-positioning-v1.7.md)
新增/修正：

- RTLCoder 的 model-training/module-benchmark 边界；
- CVDP 的任务覆盖、容器化 harness 和从 project inception 到 fabrication
  仍不完整的原文限制；
- HINT 作为 closest executable-intent neighbor 的定位；
- HINT route-level bundle、ASIC synthesis backend 和缺少 public/hidden
  evaluator separation 的边界。

## 3. 当前证据分层

| 层级 | 数量 | 可用范围 |
|---|---:|---|
| Claim-ready | 27 | 受 evidence card 约束的 claim-level 正文事实 |
| Source-verified | 3 | 仅限 supplemental evidence 中的 page-level bounded claims |
| Official-primary-page verified | 4 | 当前 arXiv 版本与 section-bounded claims；尚无本地 PDF hash |
| Discovery-only | 未冻结 | 检索线索，不进入正式事实 |

`realbench`、`hwebench`、`closerbench`、`chipverilog` 已通过当前 arXiv
abstract/full-HTML 一手页面核验并建立版本化 evidence IDs；本地资料库仍
没有其 primary PDF，因此没有填造 PDF hash 或本地 page anchors。

## 4. M2 影响

本轮不改变 M2 已通过结论，但显著收紧了三个容易过度主张的位置：

1. HINT 已占据 executable hardware-intent prior art，System-HIS 不能靠
   “typed intent”本身主张创新；
2. HINT 的效果是完整 route-level bundle，反而支持 SR2FPGA 对
   `M4-M3` 联合干预的谨慎解释；
3. CVDP 虽显著扩展 benchmark 广度，但原文明示未覆盖从项目创始到
   fabrication 的全部任务，不能替代完整 FPGA project endpoint；
4. RTLCoder 是模型训练和模块生成强基线，不是 no-training project-level
   方法。

## 5. 保留缺口

1. 如需本地离线复核，为4项 official-primary-page verified 工作保存合法
   primary PDF、hash 和完整 reader；
2. 如需将3项 source-verified 工作提升为 claim-ready，仍需生成完整
   reader、evidence card、source map 和图表/段落锚点；
3. 投稿前仍需执行有真实返回数和筛选记录的增量检索；
4. 不以本轮文献补强授权 M3、G5 或 official campaign。

## 6. 路线卡

```text
当前站：M2（已通过，继续补强）
已经完成：27项claim-ready + 3项source-verified + 4项identity-ready分层
还需要：4项原文获取、按需补完整reader/card、投稿前增量检索
下一步：继续M2文献补强或由用户决定是否解除transition hold
需要你提供：如需机构数据库或付费全文，再提供合法访问条件
```
