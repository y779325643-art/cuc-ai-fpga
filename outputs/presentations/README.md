# 演示材料

| 项目 | 制作源文件 | 保留成品 |
| --- | --- | --- |
| 项目讲解 | [project-overview/src/](project-overview/src/) | [project-overview/deliverables/](project-overview/deliverables/) |
| 项目讲解清晰重排版（2026-06-04） | [project-overview-redesign/src/](project-overview-redesign/src/) | [project-overview-redesign/deliverables/](project-overview-redesign/deliverables/) |
| 团队任务介绍（2026-06-04） | [team-task-brief/src/](team-task-brief/src/) | [team-task-brief/deliverables/](team-task-brief/deliverables/) |
| 团队技术同步 | [team-sync/src/](team-sync/src/) | [team-sync/deliverables/](team-sync/deliverables/) |
| 团队技术同步改版 | [team-sync-redesign/src/](team-sync-redesign/src/) | [team-sync-redesign/deliverables/](team-sync-redesign/deliverables/) |

团队技术同步的历史摘录保存在 [team-sync/sources/](team-sync/sources/)。
项目讲解的文字说明与 Word 文件位于 [project-notes/project-overview/](../project-notes/project-overview/)。
两个“项目讲解”PPT 字节不同，均保留，不把“副本”视为重复件。

## 制作脚本

以下是历史制作源文件，其依赖和完整构建环境未随目录整理重新验证。
运行生成器会改写对应输出，应先保留需要的版本。

- `project-overview/src/generate_ppt.py` 使用 `python-pptx`，输出到本项目 `deliverables/`。
- `project-overview-redesign/src/create_redesign_modules.mjs` 生成本项目 `src/slides/`；
  `make_pdf_from_previews.py` 使用 Pillow，从项目 `preview/` 读取 37 张图片，输出 PDF 到 `deliverables/`。
- `team-task-brief/src/build_hnai_fpga_team_brief.mjs` 需要可解析的 `@oai/artifact-tool` 包，输出到本项目 `deliverables/`。
- `team-sync/src/create_slide_modules.mjs` 生成本项目 `src/slides/`。
- `team-sync-redesign/src/create_redesign_slide_modules.mjs` 读取原版生成器中的数据，生成改版的 `src/slides/`。
- `team-sync/src/extract_sources.py --source-dir SOURCE_DIR` 要求三份完整的原始 Word 文档。
  默认查找仓库的 `reports/manuscripts/drafts/`；商业企划书原件未在此目录中提供，
  缺件时脚本退出，不覆盖已有摘录。仅整理目录时无需执行。

`deliverables/artifact-build-manifest.json` 是原构建的历史记录，保留其旧绝对路径和原字节；
它不是当前机器的构建配置。路径对应关系见[迁移记录](../../docs/migrations/repository-layout-2026-09-24.md)。
