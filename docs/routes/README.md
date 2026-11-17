# 研究路线与工作区

当前本地唯一工作树为 `cuc-ai-fpga`，分支为 `develop`，入口为 [Paper-1 v2.3 / PC 2.1](paper1-ai.md)。从 [WORKTREE.md](../../WORKTREE.md) 确认当前工作区，再按 [AGENTS.md](../../AGENTS.md) 开发。

原路线 B 的并行工作树和本地分支已移除。[测试台可靠性研究入口](tb-reliability.md)保留其历史进展和证据导航。

## 历史双工作树布局

以下记录对应 2026-10-26 的并行工作区安排。表内分支、目录和 Codex 打开方式属于该时点。

| 路线 | 入口 | 长期工作区目录名 | 分支 |
| --- | --- | --- | --- |
| A：契约驱动的 LLM 推理子系统 FPGA 工程生成 | [Paper-1 v2.3 / PC 2.1](paper1-ai.md) | `cuc-ai-fpga`（原目录） | `codex/paper1-ai` |
| B：AI 生成 RTL 测试台的可靠性研究 | [实际轨迹与漏报审计](tb-reliability.md) | `cuc-ai-fpga-tb`（原目录的同级目录） | `codex/tb-reliability` |

先读当前目录根部的 [WORKTREE.md](../../WORKTREE.md)，确认本次工作的路线，再按相应入口继续。根部 [AGENTS.md](../../AGENTS.md) 的保护规则在两路均适用。Paper-1 的研究定义适用于路线 A；路线 B 按自身已确认的协议和原始记录开展工作，不继承 A 的任务总体、统计分母或结论。

### 当时的工作区保存方式

2026-10-26 的整理保留了原目录和全部既有工作内容。原目录转入 A 分支；B 使用同一仓库的独立 Git worktree。两路从相同提交及当时尚未提交的文件状态起步，保留原有暂存条目；这不表示既有修改已经提交或审查完成。

可读取的历史 `artifacts/` 文件按原相对路径复制到 B，各自拥有独立文件。历史报告、冻结清单、工具记录和实验结果没有搬移或重写；复制不是一次新运行。原目录内一处无法读取的历史 pytest 缓存保持原状，没有将其复制为已验证数据。

本地保存清单位于原目录的 `artifacts/reorganization/worktrees-20261026-01/`，包括整理前的 Git 状态、暂存区备份、未提交文件备份和文件哈希。该目录属于本地维护记录，不是研究结果或官方证据。

### 当时的并行工作约定

1. 两条路线分别打开各自目录；同一时刻只安排一个写入任务修改同一个 worktree。
2. 开始工作先核对 `git branch --show-current` 和 `WORKTREE.md`。不要将一条路线的聊天直接接到另一条路线的目录继续写入。
3. 源码继续按 `agent/`、`contracts/`、`training/` 等既有职责维护。两路文件不会自动同步；通用修复应形成可审查的独立提交，再按需要合并或 cherry-pick。不要直接跨目录覆盖文件或整体覆盖另一条路线的暂存区。
4. 两路的研究问题、协议、任务资格、预算、停止条件、结果和稿件分别维护。新的普通运行可分别放入 `artifacts/paper1-ai/<run-id>/` 与 `artifacts/tb-reliability/<run-id>/`；协议已绑定的历史路径继续保留，不能为了目录整齐改写冻结包。
5. 每次实际运行仍按现有协议记录代码状态和未提交差异。工作区整理本身没有授权新模型、HDL 资格重跑、训练、官方实验、投稿或证据晋级。

### Python 与本地配置

虚拟环境、忽略的私有配置、密钥和全局 editable 安装未复制到 B。进行源码验证时使用当前目录的源码或独立环境；全局的 `pip install -e` 可能仍指向另一个 worktree，不能仅凭当前终端目录判断实际导入位置。

对无需安装额外依赖的 Agent 开发命令，可以在当前 PowerShell 会话中显式选择本目录源码：

```powershell
$env:PYTHONPATH = (Resolve-Path agent/src).Path
python -B -c "import sr2fpga_agent; print(sr2fpga_agent.__file__)"
```

输出必须属于正在操作的 worktree。后续修改源码可能使历史冻结包的字节绑定校验失败；应保留旧版本并按原协议准备新版本，不能改旧清单来消除差异。

### 当时在 Codex 中打开两个工作区的方式

在 Codex 中使用添加项目／打开文件夹入口，分别选择原目录和同级的 `cuc-ai-fpga-tb`，可命名为“SR2FPGA－工程生成”和“SR2FPGA－TB可靠性”。这两个目录已经是长期工作区，日常在各自项目中使用 Local 模式即可。

新聊天可从以下提示开始，再补充具体任务：

> 先读当前目录的 WORKTREE.md、AGENTS.md 和对应的 docs/routes 路线入口，确认目录与分支一致，然后继续我指定的任务；保留既有修改和实验记录。

这里创建的是自行管理的长期 Git worktree，不依赖一次性聊天的临时目录。Codex 的工作树与永久工作区说明见 [OpenAI 官方文档](https://learn.chatgpt.com/docs/environments/git-worktrees)。
