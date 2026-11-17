# SynthTL：局部备选、来源确认与机械组合的实现深审

日期：2026-10-21。仅定向阅读主源与固定作者代码；未运行框架、模型或形式工具，不改变任务、评分或正文。

主源为 Mendoza、Hahn、Trippel 的 FMCAD 2024 [论文](https://cs.stanford.edu/~trippel/pubs/mendoza_FMCAD24.pdf)，DOI `10.34727/2024/isbn.978-3-85448-065-5_17`。已读 §III、§IV、Algorithms 1–3 与 §V 对照定义；没有重算其结果。作者 [README](https://github.com/dmmendo/synthTL/blob/904fd779f44076315d62b30056b3d707498b4bf3/README.md)及 `synthTL.py` 固定于提交 `904fd779f44076315d62b30056b3d707498b4bf3`。下列源码均为该版本，行号不是浮动 main。

| 核查点 | 论文与实现对应 |
| --- | --- |
| 局部备选 | §III-A：每节点提出多个分解和 TL 备选；[`Node`](https://github.com/dmmendo/synthTL/blob/904fd779f44076315d62b30056b3d707498b4bf3/synthTL.py#L286)保存子句与分解，L341–343机械替换占位符 |
| 来源及采纳 | §III-A1：oracle逐项确认；[L2154–2183](https://github.com/dmmendo/synthTL/blob/904fd779f44076315d62b30056b3d707498b4bf3/synthTL.py#L2154)只核子串条件，[L2621–2690](https://github.com/dmmendo/synthTL/blob/904fd779f44076315d62b30056b3d707498b4bf3/synthTL.py#L2621)另收人工接受/拒绝，未把位置匹配等同语义正确 |
| 联合搜索 | §IV-A/Algorithm 1；[L2311–2387](https://github.com/dmmendo/synthTL/blob/904fd779f44076315d62b30056b3d707498b4bf3/synthTL.py#L2311)先用较弱候选剪枝，再递归组合 |
| 共享检查 | Algorithm 2；[L2057–2112](https://github.com/dmmendo/synthTL/blob/904fd779f44076315d62b30056b3d707498b4bf3/synthTL.py#L2057)按共同合取子句建索引并排除失败组合 |
| 最终交接 | [L2948–3010](https://github.com/dmmendo/synthTL/blob/904fd779f44076315d62b30056b3d707498b4bf3/synthTL.py#L2948)：生成→确认→搜索，返回在既有 DUT 上成立的较强规格，否则返回可能肇因 |

**对当前候选的判断：** “模型给局部备选、程序组合筛选”“原句锚点＋人工确认”“程序机械组合而不再让模型重写整体”均不足以单独立新。这是对已读处理的重合判断，不是找到了完全相同的 RTL 架构生成论文。

SynthTL检查已有DUT的时序逻辑规格；[N15](feasibility-assumption-method-card.md)拟在行为生成前分析结构容量与获准环境。这个对象差别本身不证明增量。SynthTL也没有用子串匹配替代人工语义确认，不能把它弱化为只有来源标签。N15若要减少这类人工工作，仍需实际自动处理与独立错误控制；当前[标准对照](feasibility-standard-baseline-review.md)只有手工可信输入，未证明这种收益。

本轮未读完作者所有辅助函数、notebook或保存案例；未复现搜索、人工审阅量或模型效果。这里不裁定其所有版本都缺少环境域保全，也不以该单篇代表整个领域。
