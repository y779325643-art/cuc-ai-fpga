# 01 从零运行当前代码

_目标：从 QKV 公开任务与参考工程入门，再用 attention 回放读懂六方法流程。_

## 🧰 环境与安装

在仓库根目录执行本章命令。示例使用 PowerShell；`python` 必须为 Python 3.11 或更高版本。仅使用 Agent 时，不需要安装训练框架、GPU 依赖或模型权重。

```powershell
git branch --show-current
python --version
python -m venv .venv
& ./.venv/Scripts/Activate.ps1
python -m pip install -e "agent[dev]"
$env:PYTHONPATH = (Resolve-Path agent/src).Path
python -B -c "import sr2fpga_agent; print(sr2fpga_agent.__file__)"
```

如果已经有合适环境，直接使用它，跳过创建和安装。最后一条命令的路径必须指向**当前 worktree**；另一路工作区的 editable 安装可能仍被 Python 选中。[依赖定义](../../agent/pyproject.toml)中基础依赖为 `certifi`、`jsonschema`、`referencing`、`PyYAML`，开发额外依赖为 `pytest`、`ruff`。

| 操作层次 | 所需工具 | 会做什么 |
| --- | --- | --- |
| 阅读、输入检查、准备公开任务 | Python + Agent 基础依赖 | 本地 JSON、哈希、结构检查 |
| 行为体拼装、真实编译与仿真 | Yosys、Icarus Verilog 的 `iverilog` 和 `vvp` | 运行 HDL 子进程 |
| 可选综合 | Yosys | 通用逻辑综合；不产生板级时序结论 |
| 开发回放 | 以上工具 | 重放手工响应，运行工程链路，不请求模型 |
| 自然模型运行 | 经配置的服务与 tokenizer 或显式容量策略 | 需要单独明确运行范围和资源预算 |

```powershell
Get-Command yosys, iverilog, vvp
python -B -m sr2fpga_agent.tasks.llm --help
python -B -m sr2fpga_agent.execution --help
```

工具不存在时，仍可完成公开输入准备与大部分纯 Python 检查。工具安装方式依操作系统而异，本章不自动下载安装工具链。

## 📦 第一步：只准备公开任务

使用时间戳生成新目录，避免覆盖已有运行。

```powershell
$guideRun = "artifacts/paper1-ai/guide-" + (Get-Date -Format "yyyyMMdd-HHmmss")
python -B -m sr2fpga_agent.tasks.llm prepare --case qkv --output "$guideRun-public"
```

成功时输出包含 `status: prepared` 和 `model_calls: 0`。主要文件如下：

```text
<run>-public/
  public/
    requirements.json       # 公开需求、边界、事实记录、资产清单
    target-profile.json     # 工具与开发目标
    capability-profile.json # 允许的 PC 能力
    assets/                 # 原始公开权重/常量资产
  store/                    # 不可变内容、源代码快照、事件
```

只把 `public/` 中允许的内容送入模型。父目录中的源码快照可能含 oracle、参考实现和评估程序，不能因为和公开文件放在同一次运行目录下，就整目录交给候选。准备过程的实现入口是 [prepare_case](../../agent/src/sr2fpga_agent/tasks/llm.py#L61)。

## 🧪 第二步：验证手工参考工程

这一步将参考 PC 和人工 RTL 走一遍真实构建与验证路径。它不生成候选模型成绩。

```powershell
python -B -m sr2fpga_agent.tasks.llm check-reference --case qkv --output "$guideRun-reference"
Get-Content "$guideRun-reference/result.json"
```

若需额外验证通用综合，使用新的目录：

```powershell
python -B -m sr2fpga_agent.tasks.llm check-reference --case qkv --synthesize --output "$guideRun-reference-synth"
```

| `result.json` 字段 | 应如何阅读 |
| --- | --- |
| `static`, `composition` | PC 静态检查和行为拼装的状态，成功通常为 `pass` |
| `compile`, `simulation` | 外部工具结果，成功为 `passed` |
| `semantic` | 独立交易轨迹与数学 oracle 检查，成功为 `pass` |
| `synthesis` | 未加 `--synthesize` 时为 `not_run` |
| `status` | 本次参考验证整体状态，不等于候选成功率 |
| `candidate_generated`, `model_calls`, `official` | 此入口分别为 `false`、`0`、`false` |

失败时先读 `diagnostic`、相应工具 JSON、`parser/` 记录，再判断是输入、RTL、工具崩溃还是超时。已有目录会被拒绝；不要删掉失败证据后在同一路径重跑。`not_run` 表示没有运行，不是一次失败的实测。

## 🔄 第三步：运行六方法回放

这是理解 M0–M5 控制逻辑最直接的例子。这里使用原指南推荐的 attention fixture，它把手写参考响应存为 `tape.json`；运行时读取这些响应，仍执行真实 PC/HDL 检查。QKV 的完整回放在本次环境中遇到综合超时和工具异常，详见验证记录；不得为了教学效果放宽其工具上限。

```powershell
python -B agent/tests/fixtures/pc21_runtime/prepare_fixture.py --case attention --output "$guideRun-fixture"
python -B -m sr2fpga_agent.execution preflight --config "$guideRun-fixture/config.json"
python -B -m sr2fpga_agent.execution run-development --config "$guideRun-fixture/config.json" --output "$guideRun-runtime" --terminal-suite-factory sr2fpga_agent.execution.development:terminal_suites
Get-ChildItem "$guideRun-runtime"
Get-Content "$guideRun-runtime/run.json"
```

正常预检中 `ready=true` 只代表开发配置与本地前置条件可用；`isolation_qualified=false` 是本地后端的明确限制。回放结束后，应查看报告中的每个方法、工具结果与资格状态，而不只看命令退出成功。

`terminal_suites` 使用与公开检查不同的**合成开发输入**，用于验证终态流程，不是正式 held-out 测试集。正常共享初始生成需要 6 次逻辑响应执行，按各方法独立使用成本归属是 10 次；这些是 tape 消费次数，外部模型请求仍为 0。

也可以执行以下只读检查，观察正式门槛如何被拒绝。返回非零是本例预期行为：

```powershell
python -B -m sr2fpga_agent.execution preflight --config "$guideRun-fixture/config.json" --formal
```

以上命令及输出字段来自 [fixture 工具](../../agent/tests/fixtures/pc21_runtime/prepare_fixture.py)、[执行器入口](../../agent/src/sr2fpga_agent/execution/__main__.py)和 [执行指南](../../agent/src/sr2fpga_agent/execution/README.md)。本次实测结果见 [10 验证记录](10-validation.md)，包括任何失败或环境限制。

## 🔍 第四步：运行第一组测试

```powershell
python -B -m pytest agent/tests/test_sr2fpga_pc21_inputs.py agent/tests/test_sr2fpga_pc21_cli.py -q -p no:cacheprovider --basetemp="$guideRun-tests"
```

这组检查验证严格 JSON、PC 输入与 CLI 往返，不要求模型。更全面的测试选择见 [08 开发指南](08-development.md)。不要一开始就安装训练 extras 或启动整个历史回归集合。

## 🛠️ 常见卡点

| 现象 | 首先检查 | 下一步 |
| --- | --- | --- |
| 找不到 `sr2fpga_agent` | 当前解释器、Agent 安装及 `PYTHONPATH` | 打印实际 import 路径 |
| 旧格式被 PC2.1 拒绝 | `contract_version` 与使用入口 | 旧产物保留给 legacy reader，不能改版本号假装迁移 |
| `output must be fresh` | 输出目录是否已存在 | 换新运行名，保留原产物 |
| source/hash binding mismatch | 准备之后是否改了源码、契约或公开文件 | 从新目录重新准备；不改旧哈希 |
| `iverilog` 非正常退出 | 记录的退出码和 stderr | 先判断工具环境；`0xC0000005` 是进程崩溃，不是普通 HDL 断言失败 |
| 工程编译成功但语义失败 | `semantic` 与交易轨迹 | 检查定点运算、顺序、末拍、背压、复位 |
| 运行结束却没有统计结论 | 簇数、missingness、资格标记 | 固定 fixture 只用于开发，不足以进行主比较 |
| UI 看起来通过但找不到真实工具证据 | 是否启动的是 `app/` | demo 状态与真实任务验证必须分别读取 |

完成本章后，继续 [02 架构与代码导航](02-architecture.md)，把刚才见到的文件与源码对应起来。
