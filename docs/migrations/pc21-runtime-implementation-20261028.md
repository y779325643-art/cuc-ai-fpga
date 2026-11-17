# PC 2.1 六方法执行与统计基础设施实现记录

用户明确授权补齐 PC2.1 M0–M5 生成/修复、预算、评测隔离和统计分析，并要求暂不运行正式实验。本记录描述代码与实际开发验证，不改变 `paper1-v2.3` 研究定义，不授予任何实验或证据晋级权限。

## 已实现的范围

| 范围 | 实际实现 |
| --- | --- |
| `agent/src/sr2fpga_agent/execution/` | 当前 PC2.1 六条件初始共享 DAG、M1 工程/文件替换、M5 design/body 修正、最后完整候选、缓存恢复与生成封存 |
| `execution/gateway.py` | 只接收序列化公开值的 text transport、显式 synthetic replay、既有 provider client 适配、计数/调用前预留、原始响应保留、未知执行不自动重发 |
| `execution/budgets.py` | 多轴持久事务、共享完整归因、B4 calls/cycles、token/context/单次输出、工具/active/EDA/CPU/memory、独立终态工具额度 |
| `execution/isolation.py` | 公共投影、共同候选 HDL 子集、最小环境、本地未资格后端、固定本地 Linux 镜像的 Docker fail-closed 后端 |
| `execution/evaluation.py` | 方法中立真实 parser/ABI/仿真/oracle/综合，公开反馈投影，受信 suite 源承诺，终态批次屏障和一次语义提交 |
| `analysis/` | 全槽位左连接、失败/未知/不适用、簇/配置/重复权重、两主比较、joint cluster bootstrap、Holm、区间、缺失界限和合成模拟 |
| PC emitter | 可注入预算/隔离 frontend runner；旧默认真实解析保护回归保留 |
| ArtifactStore | 拒绝 Windows 盘符/ADS/device/trailing-dot 标识，最终 ref 路径包含性检查 |
| 契约 | 注册 runtime config/report、project/repair proposal、replay fixture、analysis manifest/results/policy/report 共9个实际边界 |

运行说明见 [execution README](../../agent/src/sr2fpga_agent/execution/README.md) 和 [analysis README](../../agent/src/sr2fpga_agent/analysis/README.md)。旧 Runner 与 System-HIS adapters 保留为 legacy 路径，没有给它们添加当前协议别名。Training 未引入 Agent runtime import。

## 方法与边界约束

SD 共享 M0/M1，SC 共享 M3/M4/M5，SB 共享 M4/M5；SC 准入不调用 M4 emitter。M3 不受信构造自由工程。自由工程阶段收到完整公开 project/proposal schemas，不靠未披露格式规则造成失败。

M1 文件交易绑定父候选摘要，允许模型拥有的 RTL 和 manifest 一致新增/删除/替换，不自动修连线或算法。M5 design 变化清空旧 body；另一次行为调用继续占用总额度。非法/no-op 输出占用调用但不记有效修复，未完成的新分支保留原最后完整候选。预算边界不再开放新模型机会。

每个外部 parser/工具都进入预留/派发/观察；终态固定只读 public 补检及 private 工具有独立额度，生成封存后不能反馈模型或挑候选。实际完整性故障停止流程，不按普通 NA 继续比较。所有私有槽闭合后，分析适配器重读 barrier/seal/one-shot/evaluator 绑定来产生结果，不能相信调用方填写的成功数值。

控制记录保存实际 Agent Python/contract JSON 字节归档及 SHA256，包含未提交文件，并记录可读取的 Git HEAD；重新打开不得重置 budget 或换源/输入/tape 身份。原始响应、非法候选和工具失败留存，历史记录不覆盖。

## 实际验证

运行产物均在 `artifacts/paper1-ai/pc21-runtime-implementation-20261028/`。用 JUnit classname/name 去重，当前 **842 个不同用例有通过记录**，另有 **1 个符号链接探针因 OS 权限跳过**：

| 检查 | 实际结果 | 产物 |
| --- | --- | --- |
| 新预算/gateway/隔离/统计、contracts、compatibility 和相关旧核心/PC 回归 | 821 passed，1 skipped；6个真实parser/worker用例在该命令另行排除 | `combined-final-01.xml`、同名日志 |
| 六方法共享、M1/M5修复、partial恢复、身份/隐私/格式公平与parser环境失败 | 14 passed，使用真实PC/Yosys、synthetic transport及受控public verdict | `methods-final-03.xml` |
| 独立实际attention评测worker | 1 passed，真实parser、ABI、Icarus/vvp、独立oracle、完整通用综合 | `evaluator-real-host-01.xml` |
| 原PC真实解析保护 | 5 passed，含输入写入/实例/签名拒绝与合法函数 | `pc-parser-host-final.xml` |
| 公共准备/正式拒绝/封存派发门禁/终态导出/实际源码归档 | 7 passed，前6项与综合套件重叠 | `adapter-final-03.xml` |

Ruff 与任务差异 whitespace 检查通过。真实 Icarus 回归使用宿主审批机制的主机环境，保留 sandbox 中历史访问冲突的解释；没有跳过失败断言。

### 真实工具的六方法 CLI 集成

`offline-fixture-01/` 的所有响应明确来自手写参考 fixture，标签为 `synthetic_fixture`。统一 CLI 实际经过 PC2.1 shared admission、M4 emitter/body compose、公共 parser/compile/simulation/oracle/synth、6个终态封存、不同合成输入的终态重放及分析导出。

`cli-replay-final-03/run.json` 和其 private/control stores 保存最终带源码归档版本的结果：初始6次实际逻辑执行，六方法独立归因分别1/1/2/2/2/2，合计10；6个终态槽闭合。全部自然模型派发为0，未出现模型真实性能样本。先前 `cli-replay-01`、`-02` 与恢复检查不覆盖。

私有终态数据仅为本次开发生成的不同合成输入，不是正式 held-out。本地后端未获OS资格、worker CPU/peak memory未实测，因此预算/完整性资格保留 `unverifiable`；功能结果继续保存，没有给这些开发检查正式 VPP 信用。

可重做的 fixture 工具在 [agent/tests/fixtures/pc21_runtime](../../agent/tests/fixtures/pc21_runtime/README.md)，不是运行时生成服务。统计 CLI 的真实离线 `validate/analyze/simulate` 以合成多簇数据验证，`calibration_validated=false`，不宣称新 LLM 总体功效或错误率已标定。

### 保留的诊断与修正

Windows 深目录令真实存在的内部SV路径达到270字符，Yosys无法打开；composition 与 worker 的物理目录现用短名，逻辑ID/完整hash仍在控制记录。该环境失败未被当成模型自然错误。

首次重开测试发现首次返回tuple与JSON缓存list不一致，现统一JSON返回，严格内容断言保留。模型输出超额保留原响应/超额账本并停止后续；缺少或崩溃的composition parser按基础设施原因停止修复，不消耗剩余模型调用去修工具环境。源快照变化、错绑候选或重复语义提交均保留明确拒绝路径。

## 尚未获得的资格

- 本机无Docker，真实容器canary/CPU/memory强制隔离未运行；代码构造/负路径已测，本地后端始终未资格，正式preflight拒绝。
- 没有真实provider/tokenizer联调或候选生成。本轮未读取实际凭据、未调用外部模型或运行正式/实际held-out实验。
- 分析拒绝跨多个设计簇共享的dependency group，尚未实现协调组bootstrap；exact-task-hash guard也不替代语义近重复和来源审计。
- 科学预算数值、δ/Δ*、缺失门槛、任务簇与split仍需正式前按研究计划冻结。现有三个固定任务尚非正式benchmark总体。
- 没有训练、物理L4、上板、发布、数据/证据晋级。既有暂存和历史case/结果保持原状。
