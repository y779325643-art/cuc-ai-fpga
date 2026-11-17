# N30：可信规格怎样获得——源身份、转换边界与真实近邻案例

日期：2026-10-21。状态：**完成定向复核，补清基线适用范围；没有保留新的生成机制。** N29新增原件和方法审查属于进展。本轮不把“可信F准备成本未知”直接改称创新，也不把不能形式证明任意自然语言解释等同于现有方法没有经验价值。

只读本地公开需求、N19手工AST及N20编译入口；独立审查者分别核来源和构思，主审回读关键材料。外部定向复核VeriRefine/SynthTL，并新增RTL-BenchMT的论文与修订文本案例；没有运行模型、数学脚本、HDL、solver或作者代码，没有读本项目候选RTL、TB、reference或隐藏评价。下列手算均为静态推导。

## 1. 先区分三个TD对象

| 对象／实际来源 | 完整任务中规定的内容 | 本轮结论 |
| --- | --- | --- |
| [原单槽TD prompt](../../../../artifacts/codex-native-td-pilot-20261021-01/prompts/global.txt:6) | 外部E/U；内部精确R17；两个无状态核、固定连接；单槽accept/hold/bubble/reset | 原始两份哨兵的任务；不是N19 AST绑定的来源 |
| [后来的公开组合TD8](../../../../artifacts/codex-responsibility-cross-task-20261021-01/public-tasks.md:37) | 外部R/E/U；去掉状态/握手；保留精确算术，另规定完整自由边界和模块责任 | L51明确这些改动；不能视为原单槽任务原样复用 |
| [N19 trusted-specs.json](../../../../artifacts/responsibility-local-semantic-selector-prototype-20261021-01/trusted-specs.json:3)与[N20 compiler](../../../../artifacts/responsibility-direct-math-compiler-baseline-20261021-01/compiler.py:109) | JSON绑定后者的路径/SHA；手工normal AST有三输出。编译器只消费normal，逐输出发组合helper | [N20](direct-math-compiler-baseline-review.md)实际限定资格有效；不验证原单槽周期、旧责任合同或N28完整变体 |

主审核公开组合文档SHA仍为`b6a76d0a7b012f315676d40ffa505d1714ddd8c0d4f3942fae4a0a1e6412482c`，与JSON所列一致。这认证当前来源字节，不认证NL→AST语义转换。控制未进入N19 normal是公开组合任务的有意范围，不是发现转录漏项。完整组合profile的局部/自由响应也不是本轮normal-only编译要验证的内容。

N28只研究保留原单槽外部E/U的静态接口变体。其`h=clamp(R,-256,254)`不能搬到公开R的组合TD8：合法上游`(reward,next,gamma)=(127,127,16)`和`(127,127,17)`产生R=254与261，却同码254；组合任务的return_value必须区分它们。这只否定该具体夹紧编码的迁移，不另外主张组合任务的最优消息宽度。N28数学结论与停止理由不改；已澄清其引用N20处的覆盖范围。

## 2. 明确语义的转录工作仍然存在，但未发现转录错误

| 字段／操作 | 后来公开组合源 | N19手工输入与N20处理 |
| --- | --- | --- |
| 位宽、signedness、二值域 | public-tasks L5、L41 | JSON L17–18列类型；compiler L41–46推整数区间，L92–94扩展位宽 |
| R、负数floor | L43、L49 | JSON L20显式add/mul/floor；compiler L67–71只支持正二次幂分母，L100发有符号移位 |
| E及减法 | L44–45 | JSON L21把减法写成加负乘法并包sat；不是编译器理解TD概念 |
| 饱和次序、D/U | L44–45、L49 | JSON L22人工嵌套三层sat和floor；compiler L101忠实发给定结构，不自动纠正解释 |
| 证明profile及见证 | 数学与元数据需另区分 | JSON L16、L24由作者提供；不是从公开句子自动导出，也没有单凭两个见证认证全文的声明 |

JSON L2明确为手工trusted fixtures。编译入口是`load_json(text)`和`compile_spec(spec)`，没有自然语言解析或原句→AST的语义认证。普通类型/范围检查、lowering忠实及AST/RTL一致，均不证明最初AST来自需求的正确解释。双方应共享同准备度输入并承担同样整理成本；未测人工工时，不用节点数代替时间。

在这两个公开TD版本共有的算术部分，负数floor、unsigned系数与分阶段sat已经明示。风险主要是违背明确要求的转录/实现，而不是存在未定的数学含义。例如原单槽prompt的W1：R=254、value=0、alpha=8，正确E=127、U=63；若缩放未饱和差值则U=127。该手算区分两种表达式，不是发现N19写错或模型失败。普通表达式parser、类型化定义及逐定义展开已是强替代；加出处、回译或多模型一致性不自动产生新的语义真值。

## 3. 近邻实际检查什么

### 3.1 VeriRefine：前置审计有实质内容，也明确承认解释不可辨识

本轮回读[v1 §3.3.1–3.3.3、Tables1–2](https://arxiv.org/html/2607.18519v1#S3.SS3)及[§4.4](https://arxiv.org/html/2607.18519v1#S4.SS4)。schema、声明一致、表格/边界证据、FSM及组合覆盖/环都在审计范围，不能弱化成引文字符串检查。§4.4的serial2parallel案例明确说两种输出有效周期都符合文本，审计无法替TB选择。经验Direct提升是报告证据，不能单独解释成每条NL蕴含已获形式证明。作者实现仍未定位，保留无源码SHA、未复现的限制，沿用[原深审](neighbor-deep-review-verirefine-eqy.md)。

### 3.2 SynthTL：新增可配对的公开保存翻译案例

固定作者SHA `904fd779f44076315d62b30056b3d707498b4bf3`（2024-09-20）。[tutorial L44–56](https://github.com/dmmendo/synthTL/blob/904fd779f44076315d62b30056b3d707498b4bf3/test_TranslationGeneration.ipynb#L44)给GRANT/REQUEST的条件式自然语言及一个预先提供的LTL DUT。设A为GRANT高、B为REQUEST高：

- 预给DUT与最终返回为`P=G(A→(B∧X¬B))`。
- 保存输出[L306–335](https://github.com/dmmendo/synthTL/blob/904fd779f44076315d62b30056b3d707498b4bf3/test_TranslationGeneration.ipynb#L306)对P及`Q=G(A→B)∧X¬B`的抽象候选均记录stdin答y。
- 手工令A恒假、B恒真，P成立、Q不成立，故两者不等价；给定DUT也不能蕴含Q。这是公式静态区分，不对任意自然语言标一个未经确认的唯一含义。
- 保存记录[L515](https://github.com/dmmendo/synthTL/blob/904fd779f44076315d62b30056b3d707498b4bf3/test_TranslationGeneration.ipynb#L515)最终输出P。因此这里没有最终系统错误；已给DUT的检查与oracle候选确认承担不同任务。没有逐候选执行日志证明每一条实际剪枝路径。

[synthTL.py L2621–2690](https://github.com/dmmendo/synthTL/blob/904fd779f44076315d62b30056b3d707498b4bf3/synthTL.py#L2621)实际用input询问分解/翻译是否接受；[L2154](https://github.com/dmmendo/synthTL/blob/904fd779f44076315d62b30056b3d707498b4bf3/synthTL.py#L2154)的子串规则不取代它。保存stdin说明存在交互确认记录，不认证答复者身份或外部盲审。该PoC的DUT是预给LTL，不能包装成无需oracle自动获得F；[原论文与实现深审](neighbor-deep-review-synthtl.md)的强组合能力仍保留。

### 3.3 RTL-BenchMT：修订前后文本可核，但属于有参考/反馈的维护问题

新核[论文v1 §2.1–2.4、Algorithm1](https://arxiv.org/html/2605.15537v1#S2)，2026-05-15：分析读取生成件、参考代码和需求，结合失败反馈提修订，工程师审核；不是无参考的首次生成协议。

作者仓库固定`4a773170f80b80a216a6ecb6b5948f53684eee22`，2026-09-03。只选首个排序的RTLLM修订案例adder_pipe_64bit，直接读[original](https://github.com/hkust-zhiyao/RTL-BenchMT/blob/4a773170f80b80a216a6ecb6b5948f53684eee22/per-case-analysis/rtllm_v2.1/adder_pipe_64bit/original.txt)、[fixed](https://github.com/hkust-zhiyao/RTL-BenchMT/blob/4a773170f80b80a216a6ecb6b5948f53684eee22/per-case-analysis/rtllm_v2.1/adder_pipe_64bit/fixed.txt)、[analysis](https://github.com/hkust-zhiyao/RTL-BenchMT/blob/4a773170f80b80a216a6ecb6b5948f53684eee22/per-case-analysis/rtllm_v2.1/adder_pipe_64bit/analysis.md)：原文未规定两命名参数、每段宽度或级数；修订加入默认64/16、四段及四周期完成。analysis称这些与TB要求有关，本轮没有读取TB验证该原因；直接可核的是文本确实增加这些约束，不只是同义改写。

当前[README 2.0](https://github.com/hkust-zhiyao/RTL-BenchMT/blob/4a773170f80b80a216a6ecb6b5948f53684eee22/README.md)另声明SpecIR和人工发布审阅；它晚于v1论文。本次没有取得并深审扩展工作的SpecIR方法/实现，不能把README声明回填为v1已实现、已复现能力，也不据此断言没有实现。公开修订案例是开发线索，不加入本项目任务或效果分母。

## 4. 裁决与仍需满足的门

本轮补齐了具体的输入获取工作、两个公开交接案例及任务身份限制。**没有证据支持“来源锚定、人工确认、回译、一致性或先转规格”本身是新机制。** SynthTL/VeriRefine已有实质处理；RTL-BenchMT已有需求修订。也没有据此否决它们的经验效果。

不为当前明确数学TD新增NL解析原型或被测实验，不把任务版本差别当生成收益，不恢复已停止候选。若后续提出语义获取机制，必须说明实际存在的解释/转录问题、程序比标准parser/审计多处理什么、谁提供最终语义真值、各比较方相同可见信息，以及可被否定的成本/可靠性端点。引入参考驱动修订、人工交互或新任务须作为具体范围讨论，不从本次只读核查自动采纳。

旧N20执行证据仍成立于其原范围；三版初稿、候选/评价器、任务定义、数据及既有结果保持原字节。未以未知成本宣称创新，也未将此困难或N24待选当整个目标阻塞。SCI/SCIE核心仍未验收，整体目标继续。

后续若评审“以区分反例辅助确认规格”，先核对交互消歧的强近邻，再决定是否有值得讨论的额外处理。本轮只定位到[nl2spec原论文](https://arxiv.org/abs/2303.04864)及其[作者仓库](https://github.com/realChrisHahn2/nl2spec)，尚未完成方法/实现深审，不能据搜索摘要判新旧或主张能力空白。生成前增加用户交互尚未采纳，不把它默认为首次生成协议的一部分。

独立工程审查复核本报告、N20/N28更正和三处索引，确认源身份、254/261手算与覆盖边界，未见Blocker/Major；N20原“两个sat”的歧义已明确为E/D/U三处。另一审查者核§3–4及必要主源，确认保存记录、静态反例、最终输出、论文/README版本和未取得源码边界未混用。主审检查六份文件的230条本地文件链接可达，清单30个N行均为6列，三版初稿SHA和Git状态计数与本轮开始一致。未提交、暂存、推送或晋级证据。
