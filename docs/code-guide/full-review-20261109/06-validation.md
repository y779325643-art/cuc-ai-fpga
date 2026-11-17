# 本次实际验证、证据与限制

日期：2026-11-09。对象为路线 A 的当前工作区；本章只记录代码说明/审查任务的开发验证，不代表候选模型成绩、正式任务资格或证据发布。

## 1. 代码状态与保护

分支为 `codex/paper1-ai`，HEAD 为 `e20dfd2ce46c5690767e30cb629fb5c58aff073a`。开始时工作区已有 108 个删除、57 个修改、375 个未跟踪文件，以及 6 个已暂存重命名（其中 5 个同时有工作区修改）；统计来自当时 porcelain status 的路径记录，不是本次产生的改动。

本次没有 reset、clean、stash、切换分支、修改暂存区或提交。工作区原有改动保留。自有代码库存为每个文件记录 SHA-256；额外为 Agent/Training/Contracts/app/测试/既有手册保留保护哈希，收尾核对见下方文档检查结果。

本地底稿：状态快照（本地 `artifacts/documentation/full-review-20261109-01/baseline-status.txt`）、暂存差异（本地 `artifacts/documentation/full-review-20261109-01/baseline-staged.diff`）、保护哈希（本地 `artifacts/documentation/full-review-20261109-01/protected-hashes.json`）。这些是本地维护材料，不是新的研究 provenance 格式。

## 2. 实际执行结果

| 检查 | 结果 | 能证明的范围 |
| --- | --- | --- |
| 全量代码库存 | 3,810 个代码文件；440 个自有实现/测试/展示，3,370 个历史数据/候选文件 | 约定文件范围内的实际路径覆盖；不是所有文件正确性 |
| Python AST | 363/363 文件解析成功，5,958 个命名定义 | 当前 Python 解释器能解析这些源文本；不导入、不执行业务逻辑 |
| JavaScript / MJS AST | 68/68 文件解析成功，795 个函数/箭头回调，3,909 个调用位置 | 使用本机 Node 内置 Acorn，只解析、不执行页面或制作脚本 |
| 选定轻量回归 | **363 passed in 42.24s** | 下列 14 个测试文件所覆盖的合同/边界/账本/静态语义/统计/数据预检场景 |
| Docker 目录恢复探针 | 首次成功，第二次同目录 `FileExistsError` | 合成后端下的目录冲突；没有启动实际 Docker |
| UI 自由交接探针 | 后端审查为 ready，四类工程上下文标记均未进入交接文件 | 实际 helper 在 Node vm 与合成 DOM 值下的行为；不是完整浏览器测试 |
| 训练旧消息探针 | null turn 转成 `"None"` | 旧 messages 兼容路径的类型问题；不推断 canonical v2 同样错误 |
| dry-run 探针 | 数组行 `AttributeError`；空集零行且 fits=true | StringIO 合成输入下的当前函数行为 |
| 模型 smoke 测试发现风险 | 名称匹配、无 testpaths、顶层两处 from_pretrained | 仅静态确认；未收集或导入该脚本 |
| 精确 AST 重复检查 | 确认 3 组跨文件、至少 10 行的相同函数 | 仅该精确比较规则下的重复；不是全仓库相似性穷举 |

测试原件：日志（本地 `artifacts/documentation/full-review-20261109-01/review-tests.log`）、JUnit XML（本地 `artifacts/documentation/full-review-20261109-01/review-tests.xml`）。14 个文件内收集到的 363 个测试均通过，没有跳过或 deselect；这不包括没有选择的其他测试文件。

库存：生成脚本（本地 `artifacts/documentation/full-review-20261109-01/build_inventory.py`）、统计摘要（本地 `artifacts/documentation/full-review-20261109-01/inventory-summary.json`）、[文档索引](indexes/README.md)。源文本行总数 162,820 行含空行、注释、字符串内嵌 RTL、测试和展示脚本，不是生产代码复杂度指标。

## 3. 精确测试范围与命令

选择前检查了这些测试的 import 和子进程路径，使用本 worktree 的 Agent/Training 源码。预算测试中的两个子进程只运行本地 Python，用于账本与进程锁验证；gateway 测试使用本地 fake provider，调用次数不是自然模型请求。

实际 pytest 目标如下；`--basetemp` 指定了本次新建目录。复做时更换为新的、此前不存在的输出目录，避免 pytest 清理既有 basetemp。

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONPATH = "$((Resolve-Path 'agent/src').Path);$((Resolve-Path 'training/src').Path)"

python -B -m pytest `
  contracts/tests/test_contract_manifest.py `
  contracts/tests/test_project_dependency_boundaries.py `
  contracts/tests/test_repository_boundaries.py `
  compatibility_tests/test_active_documentation_paths.py `
  compatibility_tests/test_project_terminology.py `
  agent/tests/test_sr2fpga_pc21_inputs.py `
  agent/tests/test_sr2fpga_pc21_semantic_checker.py `
  agent/tests/test_sr2fpga_cluster_analysis.py `
  agent/tests/test_sr2fpga_pc21_runtime_budgets.py `
  agent/tests/test_sr2fpga_pc21_public_feedback.py `
  agent/tests/test_sr2fpga_pc21_runtime_gateway.py `
  agent/tests/test_sr2fpga_legacy_runtime_boundary.py `
  agent/tests/test_sr2fpga_current_population.py `
  training/tests/test_training_dry_run.py `
  -q -p no:cacheprovider `
  --basetemp=artifacts/documentation/full-review-20261109-01/pytest-temp `
  --junitxml=artifacts/documentation/full-review-20261109-01/review-tests.xml
```

执行时还将 TMP/TEMP 指向该运行目录内新建的 temp，stdout/stderr 保存到 review-tests.log。没有安装依赖，也没有扩大资源或更改断言/阈值。

没有使用裸 `pytest`，因为仓库包含导入即加载模型的手动 smoke；也没有执行可能 source 私有 serving env 的 shell 测试、读取 ignored local config 的配置扫描测试，或触发实际 Agent/HDL 的 UI 用例。

## 4. 专项探针怎样复核

外围探针为periphery-probes.py（本地 `artifacts/documentation/full-review-20261109-01/periphery-probes.py`），结果为periphery-probes.json（本地 `artifacts/documentation/full-review-20261109-01/periphery-probes.json`）。它保存相关 7 个源码文件的 SHA-256，使用 StringIO、公开合成请求和 Node vm，没有网络或模型调用。

Docker 恢复问题先由分项审查生成首次结果（本地 `artifacts/documentation/full-review-20261109/docker-resume-64e703c0/probe-result.json`），再由主审查用单独可复做脚本（本地 `artifacts/documentation/full-review-20261109-01/docker_resume_probe.py`）重现，结果位于独立复核（本地 `artifacts/documentation/full-review-20261109-01/docker-probe-8974cfc4/result.json`）。后者替换 `available()` 与 `_run_process()`，仅写专用 synthetic 工作目录；没有执行 Docker command 或删除历史探测目录。重复复现不是两个研究样本，也不计入上述 363 个测试。

专项探针最初尝试使用系统临时目录时遇到 Windows sandbox 权限错误。改用纯内存或本仓库 artifacts 专用目录后完成；环境错误不计为产品缺陷，也没有通过放宽权限解决。

## 5. 静态复核与历史证据分开

反馈投影与工具异常分类两项，本次是直接阅读当前源码并核对旧发现仍适用。历史复现位于 [10 月 29 日审查](../09-deep-review.md)及其[验证记录](../10-validation.md)。这些旧运行没有重新算作本次测试或本次 HDL 结果。

本次引用研究规范只用于解释要求与实现边界，引用 status/旧手册只用于定位。具体实现陈述回到当前源码，注册格式回到 manifest/schema，历史实测仍绑定原始记录。

## 6. 文档与源码一致性检查

收尾使用文档校验脚本（本地 `artifacts/documentation/full-review-20261109-01/validate_documentation.py`）核对本次 Markdown 的本地链接、源码行范围、围栏配对、库存数量、符号索引与源码哈希，以及暂存差异和受保护文件是否保持原状。结果写入documentation-validation.json（本地 `artifacts/documentation/full-review-20261109-01/documentation-validation.json`）。

实际检查通过：32 篇 Markdown、9,193 个本地链接、6,960 个源码行链接；440 个库存源码文件与 516 个受保护既有文件的哈希均未变化，暂存差异保持相同，未发现校验错误。

源码引用通过文件清单复核，排除了把目标架构的文件名写成现存文件的情况。Mermaid 图以源码形式交付，未在本次启动浏览器或图形渲染器，因此文档检查不声称完成了图形视觉验收。

静态索引不执行项目 import，名称解析仅采用本地定义、显式 import、self/cls 的语法线索。动态工厂、回调、对象真实类型和运行分支可能改变实际调用。索引中的“没有静态调用方”绝不能直接用作死代码删除依据。

## 7. 没有执行的验证

未运行全仓库回归、真实模型/付费请求、GPU 训练、LoRA 合并、模型服务、完整浏览器交互、实际 Docker 资格、HDL 编译/仿真/综合、正式 hidden、族 mutation 资格、器件映射、布局布线或上板。

没有改研究定义、可信评估、oracle、契约和评分；没有发布数据或证据，没有 Git 提交、推送或 PR。报告里的问题是待修复项，不能因为说明文档已经完成就写成已修复。
