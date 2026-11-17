# 论文初稿：证据核对与待完成研究

日期：2026-10-21。当前稿为[英文v0.3](../../drafts/structure-responsibility-v0.3.en.md)；[v0.2](../../drafts/structure-responsibility-v0.2.en.md)和[中文v0.1](../../drafts/structure-responsibility-v0.1.zh.md)保留原字节。当前是已形成完整研究初稿、继续核实方法增量的状态，不是可投稿验收或目标完成。

## 当前v0.3新增核对

- [标准后端](../../../../artifacts/responsibility-standard-cutpoint-20261021-01/results.md)：主审核94文件哈希、实际native脚本/PI绑定/两项SAT证明；wrong_mode有效反例和旧delegate适配UNKNOWN分别保留。不以原始FAIL文字跳过错误绑定解释。
- [完整局部域](../../../../artifacts/responsibility-local-domain-proof-20261021-01/results.md)：主审重算202文件哈希，直接核24个原始SAT判词、退出码及全输入/全输出脚本。16原child义务全证明、12个唯一module/source对；4正控制证明、4负有效见证。独立reference明确符号、floor、sat和TD18位差；未把局部证明扩大为整个TD或父接线证明。
- [双输出别名](../../../../artifacts/responsibility-port-alias-qualification-20261021-01/results.md)：共享与分开表达式控制均获当前checker/标准wrapper一致通过，实际10HDL过程；假设误判未复现，不能用于声称新机制收益。
- 新[架构符合性深审](architecture-conformance-gap-review.md)已纳入§2.4。主审另直接读取SV-Gap固定版本的reset-pin代码及RTL-Obliger原文Alg.1，核对关键重叠；未执行作者框架。
- [v0.3独立审阅](manuscript-v0.3-independent-review.md)完成，指定新增事实/语义范围未发现未解决Blocker/Major；主审仅修正报告内一个本地链接。新证据增加覆盖与可复核性，不使方法增量门自动通过。用户已允许少量结构任务变体，设计与查新另行推进，不把尚未生成/评价的变体写入结果。

## v0.2核对（保留）

- 主审直接核对12原始输出和12统一固定父构造的全部真实评价，均通过。工具退出、scoreboard、七项失败指标、每项结果artifact哈希、绑定receipt、相同child字节与汇总分母一致；证据见[root只读核验](../../../../artifacts/codex-responsibility-transport-20261021-01/root-result-verification.json)。另核558文件最终manifest零差异，没有重复执行已过HDL。
- 12个模型child配置gpt-6.1-sol/ultra，无工具记录或反馈，10组不同源码，原生usage合计373774（含平台上下文）。初始化前并发拒绝另列，实际模型没有重采样。输入加密可见性和非硬隔离限制完整保留。
- 两份[实现深审](neighbor-deep-review-cppl-hint.md)及[VeriRefine/EQY深审](neighbor-deep-review-verirefine-eqy.md)已纳入稿件。主审独立取得CPPL同期compiler、后续patterns与EQY官方ex_bind源码核对关键事实；没有执行这些作者完整系统。
- [独立稿件评审](manuscript-v0.2-independent-review.md)指出一项核心措辞：全部输出响应映射已完整确定所选父上下文(x,z)的外延函数，不能推定比完整IR行为更局部、成本更低或自由度更大。已修正§3与§7.2；内部组织仍未逐信号固定不等于已证方法优势。
- 中文[跨任务结论](cross-task-pilot-review.md)与唯一[进度清单](../2026-10-21-structure-generation-paper-checklist.zh.md)记录本轮结果；真实模型未观察到责任违约或提示/构造收益，手写负例仅用于资格。

当前没有通过的方法贡献门：与同义务标准切点流程、完整行为IR和严格父构造相比，实际建模/绑定成本、合法实现接纳范围与有用的适用差异尚未证明。后续开发资格不自动晋级为模型收益；不得用论文篇幅或“未找到完全相同流程”代替实质增量。SCI目标保持active。

## v0.1历史核对（保留）

## 已核对的主张

| 初稿主张 | 实际证据 | 允许范围 |
| --- | --- | --- |
| 两份原生Codex首次RTL通过本次有限功能检查 | [开发记录](native-codex-development-pilot.md)及其两份result.json、编译/仿真日志、原始response和候选快照 | 一任务、各一输出；不推断总体成功率或定位提示效益 |
| 子模型配置、token与零记录工具调用可观测 | [本线程两子会话审计](../../../../artifacts/codex-native-td-pilot-20261021-01/runtime-audit.md)；最终JSON全部源码字符串与原始子会话输出一致 | 配置为gpt-6.1-sol/ultra；原生usage不是货币账单；零工具调用不证明工具不可访问；加密任务内容未解密 |
| 正常功能通过与额外责任合同通过不同 | [run01](../../../../artifacts/guarded-responsibility-qualification-20261021-01/results.md)；4控制各1024正常输入及16384干预条件，工具守卫通过 | 手写4bit组合夹具；不是模型违约率、普通功能缺陷或任意RTL证明 |
| 一次优化后实例存在仍可漏掉显式责任违约 | [run02](../../../../artifacts/guarded-responsibility-qualification-20261021-02/results.md)及5份postopt JSON | 仅指定Yosys层级/proc/opt/opt_clean序列；wrong-mode正常全过、责任失配7680、adder4实例数1；fake-use实例数实测1而非按直觉改写 |
| 经典切点、层次和vacuity等已有先例 | 稿末4篇原文链接及方法定位，CPPL/HINT/HierSVA/2005切点论文的已读部分 | 不声称自由变量替换是新算法，不指控CPPL合法DCE为缺陷，不推断未读实现行为 |

主审直接检查harness的整数参考、事务事件/复位处理、端口及白名单、实际编译/仿真结果和源快照。四份TD评价记录的harness及候选hash均匹配；run01的57项、run02的32项保留文件hash复核一致。主审还直接读取5份优化后JSON的`modules.alu4.cells`，确认实例计数1/0/1/1/1。未重复运行已经通过的实验。

## 独立评审与修正

独立只读评审查出一项实质定义缺口：初版公式只约束guard成立时的响应，而实际公开合同和实验还要求guard外对自由边界独立。主审已将§3改为对适用域内全部输入/替换值量化的分段响应：guard成立时等于Psi，guard不成立时等于原功能F。并明确本次四位有限域和这项更强公开承诺，不从普通功能规格自动推出它。

该评审未发现将手写控制并入模型分母、把强合同失配称功能错误、把经典切点称新算法或冒充已跑完整typed IR比较的问题。第二轮数据随后由主审加入并直接复核；不将其说成评审已独立批准全部新增内容。

主审另补明：当前原型是人工绑定公开边界和响应、程序化执行检查，没有实现自然语言自动推导合同或通用RTL解析；移除未核实的参考页码，核对CPPL/HierSVA官方作者与年份。文章只述实际工具序列，不泛化所有优化策略或物理资源保持。

## 当前不能通过的验收

核心方法的新颖性仍未确认；与严格固定父层、完整typed IR、标准组合/切点验证的能力或成本边际未证明。原生TD实验没有观察到提示差异，也没有给出真实模型的责任违约发生率。尚缺更多真实任务、重复生成、误拒绝控制、可复用合同绑定、实际开销和可重放的更完整研究方案。

因此初稿可审阅，**SCI研究目标保持active，不标complete**。后续工作应补可复用原型和强基线、按用户接受的显式架构承诺范围准备更多公开任务，再有界运行Codex候选并更新结果。不能用补写篇幅、额外玩具例子或已有控制的重复运行替代这些研究证据。
