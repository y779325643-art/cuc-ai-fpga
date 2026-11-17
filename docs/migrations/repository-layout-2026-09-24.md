# 参考材料目录整理（2026-09-24）

本轮只调整参考材料和历史文档的位置、导航及相关制作路径。共迁移 108 个文件。
研究定义、数据发布、正式证据目录、注册契约路径和运行时代码未随此整理改变。
原有暂存区保持不变。迁移前的工作区文件（包含未提交修改）作为保留基准。

## 路径对应

| 原位置 | 新位置 |
| --- | --- |
| `outputs/project-overview/` 中的 PPT 与 PPT 生成脚本 | `outputs/presentations/project-overview/{deliverables,src}/` |
| `outputs/project-overview/` 中的项目说明、Word 和文档生成脚本 | `outputs/project-notes/project-overview/`，脚本在 `src/` |
| `outputs/manual-20260604-project-overview-redesign/presentations/project-overview-redesign/` | `outputs/presentations/project-overview-redesign/` |
| `outputs/manual-20260604-hnaifpga/presentations/team-task-brief/` | `outputs/presentations/team-task-brief/` |
| `outputs/team-sync-ppt/` | `outputs/presentations/team-sync/` |
| `outputs/team-sync-ppt-redesign/` 及原版目录中的 `slides-redesign/`、改版生成器 | `outputs/presentations/team-sync-redesign/` |
| `outputs/ir_report_extracted.txt` | `outputs/project-notes/ir-discussion/ir_report_extracted.txt` |
| `reports/manuscripts/` 中的 9 个文件 | 同目录下的 `drafts/`、`discussions/`、`reading-notes/`、`technical-notes/`，见[索引](../../reports/manuscripts/README.md) |
| `docs/superpowers/{plans,specs}/` 中的两份 G3b 记录 | `docs/history/engineering/`，见[索引](../history/engineering/README.md) |
| `docs/specs/IMPLEMENTATION_DELTA.zh.md` | [docs/migrations/IMPLEMENTATION_DELTA.zh.md](IMPLEMENTATION_DELTA.zh.md) |

演示项目内的制作脚本和 slides 归入 `src/`，原 `output/` 成品归入 `deliverables/`，
团队技术同步的文本素材归入 `sources/`。内容不同的两个项目讲解 PPT 均保留。

## 历史引用与构建边界

当前索引和迁移文件中的可点击链接按新位置更新。此前的研究计划、迁移日志和历史构建清单
中的旧路径描述保留为历史记录，使用上表定位现在的文件。历史引用哈希不追改。
原构建清单中的绝对路径只表示原构建环境，不是可直接执行的当前配置。

制作脚本的仓库路径改为相对脚本定位。团队任务介绍使用包名导入 `@oai/artifact-tool`；
该依赖需由制作环境提供。团队同步摘录脚本增加输入目录参数并在原件不完整时停止，
避免迁移后运行覆盖成不完整摘录。商业企划书原件缺失，保留现有文本素材。

本轮不重新生成 Word、PPT 或 PDF，不将历史稿件的内容解释为正式实验结果。

## 本轮验证

- 108 个迁移文件逐项核对：99 个 SHA-256 不变，9 个文本文件只调整链接、制作路径或读取保护。
  所有 Word、PPT、PDF 和历史构建清单均保持原字节；移除了 20 个迁移后确认为空的旧目录。
- 228 个 README 本地链接有效；与迁移前对比，没有新增的 Markdown 文件路径断链。
- 12 项现有文档与术语回归测试通过；4 个 Python 文件和 67 个 JavaScript 文件通过语法检查。
- 三个无外部依赖的 slide 生成器在 `artifacts/` 隔离副本中实际运行，分别生成 12、12、37 个模块。
  改版读取器通过 LF 与 CRLF 输入检查，并修复了发现的换行兼容问题。
- 摘录脚本的帮助入口和缺件退出检查通过，保留的文本素材未改变。
- 暂存区与迁移前的二进制 diff 完全一致。未提交或推送。

完整 Word/PPT/PDF 重建未执行：当前环境缺少 python-docx 等制作依赖，商业企划书原件不齐，
本轮也不重建历史成品。只通过语法检查的脚本不视为完整构建已验证。
本地逐文件迁移及 SHA-256 清单位于 `artifacts/layout-20260924/moves.json`，
检查摘要位于 `artifacts/layout-20260924/validation.json`；这些是工程诊断文件，不是研究评测证据。
