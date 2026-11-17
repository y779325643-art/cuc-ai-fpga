# 10 本次审查与文档验证记录

_2026-10-29 · 开发验证，不构成候选模型成绩或官方实验。_

## 🧾 代码状态与运行边界

- 工作区路线 A，分支 `codex/paper1-ai`，起始 HEAD `e20dfd2ce46c5690767e30cb629fb5c58aff073a`。
- 起始时已有大量暂存、未暂存与未跟踪实现。本文依据工作区实际文件，不声称只检出该提交就包含所有功能。
- Python 3.13.2；可用工具为 Yosys、Icarus/vvp。没有安装训练/服务依赖，没有自然模型请求。
- 本次运行根目录：[artifacts/documentation/code-guide-20261029-01](../../artifacts/documentation/code-guide-20261029-01/)。其中日志是本地维护记录，随 Git 忽略的 artifacts 保留；不是 `reports/evidence/` 晋级。
- 公开准备与 runtime 用既有 ArtifactStore 保存源码/契约原始字节、公开来源、配置、预算和事件。文档没有另造研究结果格式。

起始 Git 状态和暂存差异保存在本地运行目录。收尾复核确认暂存差异未变，fixture快照绑定的249份Agent源码与契约文件字节均未改变。当前测试结果仅适用于该工作区源码、这些固定输入和本次工具环境。

## 🧪 执行结果

| 检查 | 实际结果 | 证据与解释 |
| --- | --- | --- |
| 当前 `pc/execution/analysis/tasks.llm --help` | 成功 | 确认真正存在的操作和参数 |
| QKV replay fixture 准备与开发预检 | `ready=true`, `model_calls=0` | [preflight.log](../../artifacts/documentation/code-guide-20261029-01/preflight.log) |
| 同配置 `preflight --formal` | 非零退出，`ready=false` | [formal-preflight.log](../../artifacts/documentation/code-guide-20261029-01/formal-preflight.log)：正式入口不支持、协议未冻结、任务未资格、隔离未资格；属于预期拒绝 |
| QKV `check-reference` CLI | static/composition/compile/simulation/semantic通过，synthesis未运行 | [result.json](../../artifacts/documentation/code-guide-20261029-01/qkv-reference/result.json)：3次完整调用、Q/K/V输出48/24/24拍，2次调用被reset取消 |
| PC输入/上下文、集成、统计、四个LLM测试文件 | 受限环境 **175 passed / 7 failed** | [core-tests.log](../../artifacts/documentation/code-guide-20261029-01/core-tests.log)、[JUnit](../../artifacts/documentation/code-guide-20261029-01/core-tests.xml) |
| 上述7项原用例主机环境复核 | **7 passed** | [hdl-host-tests.log](../../artifacts/documentation/code-guide-20261029-01/hdl-host-tests.log)：未改用例/断言/阈值，原失败均为Icarus退出码3221225477（0xC0000005） |
| Training、项目边界与UI轻量子集 | **100 passed / 22 deselected** | [peripheral-tests.log](../../artifacts/documentation/code-guide-20261029-01/peripheral-tests.log)：主动排除HTTP/真实生成与服务脚本检查，非 skipped |
| Training smoke 转换与干跑 | 6条有效chat，估计45–164 token，均≤2048 | [peripheral-dry-run-probes.json](../../artifacts/documentation/code-guide-20261029-01/peripheral-dry-run-probes.json)：未加载tokenizer/训练框架 |
| 行为拼装反馈探针 | 初次及归档脚本重做均复现 | [简明结果](../../artifacts/documentation/code-guide-20261029-01/runtime-review-feedback-probe/probe-summary.json)、[独立重做](../../artifacts/documentation/code-guide-20261029-01/runtime-review-feedback-rerun/probe-result.json)；零模型网络/零HDL子进程 |
| Yosys异常分类探针 | 真实异常记录被重现为普通候选拒绝 | [分类摘要](../../artifacts/documentation/code-guide-20261029-01/runtime-review-bad-alloc-classification.json)，详见R3 |
| Mermaid 真渲染 | **12/12 成功** | [diagram-validation.json](../../artifacts/documentation/code-guide-20261029-01/diagram-validation.json)，SVG随手册交付 |
| 文档结构、链接与源行号检查 | 11篇、12个SVG，检查无错误 | [handbook-validation.json](../../artifacts/documentation/code-guide-20261029-01/handbook-validation.json)，包含暂存差异未变检查 |
| 现有文档路径/术语回归 | **12 passed** | [document-tests.log](../../artifacts/documentation/code-guide-20261029-01/document-tests.log) |

核心回归共182个独立用例：175项首次通过，7项在相同用例的主机复核通过。不能把两次执行加成189个独立测试，也不能把这些用例算作研究样本。与外围100项合计有282个不同用例的通过记录；这里未把另行文档检查或CLI回放折算成测试数。

12张SVG经过真实浏览器渲染并查看[合成预览](../../artifacts/documentation/code-guide-20261029-01/diagrams.png)，未发现文字裁切或节点覆盖。首次渲染检出一处菱形节点语法错误，修正后全数通过；受限环境的浏览器崩溃记录另存，最终渲染在获准的主机环境完成。

## 🔄 三次完整回放应分别解释

| 回放 | 公开接受 | 终态 | 结论 |
| --- | --- | --- | --- |
| QKV，受限环境 | 0/6方法槽位 | 流程关闭 | 存在原生工具崩溃和工具超时；不是RTL失败率 |
| QKV，主机环境 | 1/6（M3） | 6槽位关闭，无最终通过 | 共享SD遇到Yosys `std::bad_alloc`，其他分支/终态有60秒综合超时；不能描述成“六方法验证通过” |
| Attention，主机环境 | 6/6 | 6个终态均 `value=1` | 成功完成固定人工响应的开发回放 |

原件分别为 [runtime/run.json](../../artifacts/documentation/code-guide-20261029-01/runtime/run.json)、[runtime-host/run.json](../../artifacts/documentation/code-guide-20261029-01/runtime-host/run.json)、[attention-runtime/run.json](../../artifacts/documentation/code-guide-20261029-01/attention-runtime/run.json)。QKV 工具异常分类见 [R3](09-deep-review.md)；未调高60秒工具限额，也未覆盖失败目录。

Attention 回放实际共享逻辑调用为 **6**，六方法 standalone 归属为 **10**；`natural_model_dispatches=0`，source class 为 `synthetic_fixture`。公开检查使用真实 parser、Icarus/vvp、独立交易检查和通用综合，终态使用不同合成开发输入。

终态原件在 [attention-runtime/private/terminal-analysis.json](../../artifacts/documentation/code-guide-20261029-01/attention-runtime/private/terminal-analysis.json)：六槽位均 `reason=terminal_evaluated`、`value=1`，但 `budget_status` 与 `integrity_status` 均为 `unverifiable`。所以“6/6”仅是该开发控制的槽位结果，不能声称正式方法资格或自然模型成功率。

## 🛠️ 可复做的主要命令

从仓库根目录，使用当前 `agent/src`。替换为新的输出路径；不要直接复用已存在的 basetemp/run 目录。

```powershell
$env:PYTHONPATH = (Resolve-Path agent/src).Path
python -B -m pytest agent/tests/test_sr2fpga_pc21_inputs.py agent/tests/test_sr2fpga_pc21_cli.py agent/tests/test_sr2fpga_pc21_context.py agent/tests/test_sr2fpga_pc21_runtime_integration.py agent/tests/test_sr2fpga_cluster_analysis.py agent/tests/test_sr2fpga_llm_qkv.py agent/tests/test_sr2fpga_llm_attention.py agent/tests/test_sr2fpga_llm_ffn.py agent/tests/test_sr2fpga_llm_suite.py -q -p no:cacheprovider --basetemp=artifacts/documentation/FRESH/core-tests
```

只复核原来的7项HDL失败：

```powershell
python -B -m pytest agent/tests/test_sr2fpga_llm_qkv.py::test_qkv_manual_reference_hdl agent/tests/test_sr2fpga_llm_qkv.py::test_qkv_token_streaming_reference_hdl_does_not_deadlock_reset_probe agent/tests/test_sr2fpga_llm_attention.py::test_manual_reference_hdl_checks_persistence_gqa_stalls_and_resets agent/tests/test_sr2fpga_llm_attention.py::test_reference_hdl_ratio_extremes_with_denominator_1024 agent/tests/test_sr2fpga_llm_attention.py::test_pc_emitted_reference_real_parser_and_hdl agent/tests/test_sr2fpga_llm_ffn.py::test_ffn_real_hdl_math_stalls_reset_and_trace_corruption -q -p no:cacheprovider --basetemp=artifacts/documentation/FRESH/hdl-tests
```

外围子集的选择规则：

```powershell
python -B -m pytest training/tests contracts/tests/test_project_dependency_boundaries.py contracts/tests/test_repository_boundaries.py app/test_server.py --ignore=training/tests/test_serving_entrypoints.py -k "not static_server and not internal_error and not endpoint and not clock_context_reaches_recorded_project" -q -p no:cacheprovider --basetemp=artifacts/documentation/FRESH/peripheral-tests
```

六方法完整回放命令见 [01 上手](01-quickstart.md)。本次对环境崩溃使用主机批准机制复核，不能把环境差异隐藏为一次全绿执行。

## 🚫 没有执行的验证

没有自然模型/付费调用、GPU训练、LoRA合并、模型服务、Docker实机资格、正式held-out、族mutation资格、真实checkpoint、FPGA mapping、布局布线或上板测试。没有运行全仓库回归，也没有启动完整UI HTTP交互测试。

文档链接和图形渲染只能证明文档可导航、图形语法有效；静态检查、mock和synthetic回放各自有范围，不能替代上述未执行验证。本次没有修改研究评分、trusted oracle或候选运行逻辑，没有晋级数据/证据，没有提交、推送或创建PR。
