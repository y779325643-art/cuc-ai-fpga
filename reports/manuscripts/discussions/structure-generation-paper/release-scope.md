# P01 来源、许可与可公开范围审计

日期：2026-10-21。本文是[旧版结构生成论文准备](../2026-10-21-structure-generation-paper-checklist.zh.md)的内部材料盘点，不是法律意见、公开许可、数据 promotion 或投稿批准。P01 只确定已找到什么、尚缺什么；本轮没有公开文件、上传内容、外部写入或修改许可/研究定义。

本篇沿用旧 System-HIS 范围，不以 PC 2.1 迁移为前提。范围调整不解除既有 dataset、evaluator-private 或第三方材料边界。本文及所列内部审计文件不直接进入候选模型输入。

## 检查方法和发现

检查了仓库根文件名、tracked LICENSE/LICENCE/COPYING/NOTICE/CITATION 文件名、选定 task_families/oracles 的源码头部与来源/许可标记、[Agent 包元数据](../../../../agent/pyproject.toml)、[Training 包元数据](../../../../training/pyproject.toml)、[数据注册表](../../../../datasets/manifest.json)、[数据指南](../../../../datasets/README.md)、[参考资料索引](../../../../references/README.md)、[稿件索引](../../README.md)及所选样例元数据。本轮未读取凭据文件、秘密值、私有端点或账户配置；也未将原始调用包送往外部服务。

在上述检查范围内：

- **未找到仓库根 LICENSE/LICENCE、COPYING、NOTICE 或 CITATION.cff 文件；tracked 同类文件名检索也没有结果。** 选定 task_families/oracles 文件头未找到 SPDX、copyright 或明确第三方来源/许可说明。
- Agent/Training 的 pyproject 没有 project.license 或 project.authors 声明。没有找到可用于核实这些任务模板/参考实现完整权利归属的作者授权记录；文件在本仓库不等于已确认自有且可再许可。
- [canonical-citation-registry](../../../../docs/research-program/paper1-v1/foundation/canonical-citation-registry.md)是文献与论证来源索引，不能替代软件 CITATION、代码许可证或第三方材料转载许可。
- 三个已注册数据 release 均为 internal_only、license_status=review_required、config_fingerprint=null/legacy_unavailable。文件可本地读取、存在 SHA 清单，不构成可公开授权。

本轮是静态来源审计，没有向作者、数据所有者、模型提供方或工具厂商核实权利，也没有做外部依赖许可证审查。以下“候选公开”均是后续可准备的方向，不是已批准状态。

## 来源和分发矩阵

| 材料类别 | 已知来源事实 | 当前公开结论 | 最小待补 |
| --- | --- | --- | --- |
| Agent/controller、旧 System-HIS 骨架、任务模板 | 本地 Python 源码；路径、Git 工作区和历史原件存在；未找到明确著作权/许可证链 | **归属待核实；不默认“自有可开源”** | 确认作者/贡献来源和可再许可范围，选择准确许可证并保留必要 notices；P01不代签、不新增license |
| 独立 Python reference/oracle | 仓库内 numeric/signal/image/rl 实现；有历史manifest/hash和证据，但来源说明不完整 | **内部受信评估资产**；不整包复制到模型上下文或默认公开包 | 确认代码权利、公开与私有suite分层；公开部分采用独立范围和版本 |
| 正确参考 RTL/可信 TB | 确定性模板生成与旧归档并存；参考与候选文件须区分 | 来源/许可待审；公开参考可能暴露后续任务答案 | 记录生成/改写来源、算法引用与人工修改；决定是否作为已暴露开发任务公开，而非继续称未见评测 |
| 旧模型生成 RTL/契约/TB/patch | metadata含gateway报告来源；抽核样例无完整API调用原件/当时条款快照；模型生成不等于权利清晰 | **内部旧归档**；不能凭natural_llm标签宣称调用可重放或权利保证 | 保存可取得的合法调用出处/适用条款；缺失项保留未知，不补造；逐文件审查敏感信息与第三方代码 |
| 三个 datasets release 与 JSONL exports | 注册表明确 internal_only/review_required；旧样例与导出非统一实验 | **不得按现成公共benchmark分发** | 后续若确需公开，建立新版本release、来源许可审查、内容/边界核查与显式promotion目标；保持旧payload和清单不变 |
| 自行编写的任务需求与参数 | 本地requirement.txt及元数据/哈希存在；早期样例来源与配置绑定不完整 | 可作为本篇任务定义的候选材料，不自动继承发布许可 | 明确任务卡作者/来源、公开数学事实、接口与数值语义；不要拷贝evaluator答案填需求 |
| 工具原始日志与结构化指标 | Icarus、Verilator、Yosys、OpenXC7等执行记录；有些含旧绝对路径；个别日志为空 | 可提取必要指标作为内部证据；原始日志需审查后再决定 | 核对工具版本与许可、路径/个人标识/私有数据；不能将哈希一致当可再分发许可，也不补造空日志 |
| 第三方运行依赖/工具分发包 | Agent声明certifi/jsonschema/referencing/PyYAML，dev声明pytest/ruff；HDL工具来自外部安装 | 使用依赖不等于依赖实现归本项目；本轮不打包依赖、二进制、工具安装或vendor资产 | 若后续分发环境，检查实际选定版本许可证/notices及允许分发范围；不以本轮推断各版本法律状态 |
| 板卡手册、原理图、厂商资料 | [AC820资料](../../../../references/AC820开发板)为vendor/reference输入 | **排除于最小公开复现包**；不当作自有材料再发布 | 需要时引用合法来源与必要信息；原件/截图/图纸另核转载范围，本篇不以板级实验为前提 |
| 论文原件、reader、翻译和图 | [references](../../../../references/README.md)是第三方/来源材料区；有reader provenance，不是转载权证明 | **排除整篇、整图及翻译包的默认分发** | 文献引用与必要转述依原始来源；使用原图需另核许可，不以来源链接替代许可 |
| 历史稿件、Word/PDF、演示输出 | [稿件索引](../../README.md)区分草稿/讨论/阅读/技术笔记；不是执行证据 | 不作为新稿实证数据或公共复现包默认内容 | 逐项确认作者、原图与素材来源；不得沿用无证据高性能数字 |

## evaluator-private 与 hidden 的实际位置

1. 旧九家族 oracle 归档只有manifest/evidence而无.memh，不表示全部私有信息已经脱敏。静态检查发现归档manifest仍含seed字段；[numeric](../../../../agent/src/sr2fpga_agent/oracles/numeric.py)、[signal](../../../../agent/src/sr2fpga_agent/oracles/signal.py)、[image](../../../../agent/src/sr2fpga_agent/oracles/image.py)、[rl](../../../../agent/src/sr2fpga_agent/oracles/rl.py)源码均声明固定私有场景种子常量。本文只记录存在性，不复制数值、向量、期望输出或参考代码。
2. 因此，旧oracle源码、manifest、参考RTL和原始日志不能因为位于Git目录就整体送给候选模型或随包公开后仍称其suite为未暴露hidden。若后续公开，需明确退休/暴露范围及将来私有评估的独立修订；不能重命名旧文件来维持未见声明。
3. 旧[Phase C报告](../../../../reports/evidence/phase-reports/sr2fpga-phase-c-independent-oracle-evidence-2026-07-14.md)的训练导出leakage检查仅适用于其命名范围；“未在训练导出发现hidden内容”不是“全仓库可给模型读取”或“全仓库可公开”。
4. 候选模型只能接收P02规定的公开需求/契约与允许代码；public开发评估、evaluator-private输入/答案、正确参考实现与日志分层。九任务参考索引属于研究准备，不是候选可见任务包manifest。
5. 某些旧trajectory的data_release字段写open_public，但全局[release注册表](../../../../datasets/manifest.json)仍为internal_only/review_required；局部标签不提供额外公开或promotion许可。遇到不一致应保留较窄实际边界并记录待审。

## 本篇最小复现包的候选边界

在后续获得明确分发目标与许可后，可准备：已确认权利的controller/契约/构建代码、准确依赖与工具版本说明、本篇公开任务卡、公开开发harness、与结果表相符的脱敏结构化记录和允许公开的封存候选。本文只列准备范围，尚未制作或发布该包。

不自动纳入：旧三个完整数据集、私有suite与seed、reference答案库、原始provider请求包、凭据/端点、本地绝对路径、工具二进制、权重、厂商原始资产、板卡文档、论文PDF/reader图、历史稿件及未核来源的代码。可复现所需内容若不能公开，应明确访问限制或受信重放办法，不用“开源”概括未授权材料。

## 未决项与交接

| 未决项 | 需要的决定/证据 | 对当前P01的影响 |
| --- | --- | --- |
| 本地代码/模板的权利归属 | 作者/贡献来源及拟许可范围 | 可完成审计，不能声称可开源 |
| 旧模型输出的来源与权利 | 可取得的原始调用出处、提供方条款、第三方代码核查 | 旧数据仍是内部案例；不补造缺失provenance |
| 本篇公开材料与private suite切分 | P02协议、模型输入allowlist和后续发布范围 | 不妨碍只读准备；P03/P04需实际控制 |
| 精确代码/依赖/工具版本 | 选定旧版实现与本篇新修订、环境记录 | 历史标签不产生当前运行资格 |
| 数据公开/证据promotion | 新release目标、来源许可审查、显式授权 | 当前保持internal_only，P01不执行 |

关联：[资产证据等级与统计](asset-audit.md)、[九任务候选与静态缺口](task-readiness.md)。本轮没有新增论文正文、实验结果、许可证、公开数据集或外部发布。
