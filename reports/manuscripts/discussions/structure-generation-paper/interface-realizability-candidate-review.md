# N28：消费者生成前的接口可实现性——静态候选与强对照

日期：2026-10-21。状态：**数学区分例成立；新增方法核心未成立，暂不开发或启动模型pilot。** 本文是讨论及来源审查，不是实现、实验计划或官方研究定义。设想来自主审讨论与既有文献；数学审查者手工推导后再作反驳式复核，不称被测模型输出或独立发明。

## 1. 这次具体改变什么

候选R2：LLM先提出上游编码`h(x)`及其可见输入；程序在下游行为`Q`尚未生成时，判定是否存在某个允许的确定性`Q(h(x),c)=F(x,c)`。不可能则拒绝这个接口；可行才固定接口并生成下游。目标是避免在已经丢失必要信息的接口上继续写行为，而不是复用N22/R1b的完整自由边界响应保证。

程序必须获得可信的位精确`F`、已确定的`h`、合法域、上下游可见划分与消息语义；这些不是自然语言自动给出的保证，编写和校核成本不能隐去。模型说明不能自行升级为可信事实。给定同一context，两份独立合法上游输入的反例查询为：

\[
X(x_1,c)\land X(x_2,c)\land h(x_1)=h(x_2)
\land F(x_1,c)\ne F(x_2,c).
\]

SAT表示任何允许的无状态`Q`都不能完成任务；UNSAT表示在可达编码上存在这样的`Q`。未知必须保留UNKNOWN。这里不要求h覆盖整个接口域，也不证明已生成Q正确、完整ABI的域外响应、握手、RTL或PPA。

## 2. 只用原有完整公开TD需求的严格区分例

输入为[原TD首次生成公开prompt](../../../../artifacts/codex-native-td-pilot-20261021-01/prompts/global.txt:1)，SHA256 `05f8783799f165488bfa09f68978f0b1fafc7dca7cf72cf6f3f82fe2615ba0dd`；没有读候选、TB或reference来补定义。

`reward,next,value∈[-128,127]`，`gamma,alpha∈[0,255]`：

\[
R=reward+\lfloor gamma\,next/16\rfloor,\quad E=sat8(R-value),
\]
\[
D=sat8(\lfloor alpha\,E/16\rfloor),\quad U=sat8(value+D).
\]

新变体只在设计层允许改变中间消息：上游仅见`x=(reward,next,gamma)`，下游另见`c=(value,alpha)`；唯一跨边界信息是固定长度、无状态的组合消息h。不允许额外透传x、多拍编码或时序侧信道。保持原单槽输出控制及外部E/U要求。**旧prompt明确要求R17和原局部算式；压缩消息不符合旧合同，不能回改或重评旧结果。尚未采纳9bit资源上限。**

### 2.1 9bit足够

令`h=clamp(R,-256,254)`，用signed9表示。R≤−256时，对全部value，E恒为−128；R≥254时，E恒为127；其余R原值保留。因此`E=sat8(h-value)`，进而同一E给出相同D/U。编码有511个值，signed9的255未使用。该推导只说明数值函数可实现；没有实现或验证RTL/控制。

### 2.2 一个明确不足的8bit编码

若`h=sat8(R)`，上游`(reward,next,gamma)=(127,0,16)`和`(127,1,16)`分别给R=127、128，却同码127。在相同`value=1,alpha=15`下：

| R | E | D | U |
| ---: | ---: | ---: | ---: |
| 127 | 126 | 118 | 119 |
| 128 | 127 | 119 | 120 |

任何只见该码及相同context的确定性下游都无法同时恢复这两组输出。这是人工数学见证，不是发现了模型失败。

### 2.3 任意固定8bit编码都不够

取gamma=16，`R=reward+next`覆盖[-256,254]全部511个整数，为每个R选一个合法上游元组。任取p<q：

- p≤−1时，选value=p+128，合法且`E(p)=-128`、`E(q)>-128`。
- p≥0时，选value=127，`E(p)=p-127∈[-127,126]`，`E(q)>E(p)`。

alpha可统一取0，因为E本身也是外部输出。511个代表输入的下游响应两两可区分；不要求同一个context同时区分全部输入。即使h依赖整个x而不只是R，也必须为这511个代表输入分配不同码字，故至少`ceil(log2 511)=9bit`。§2.1达到此界。这是标准函数分解/信息区分类论证，不主张新定理、面积或延迟收益。

## 3. 近邻的实际能力与实现边界

本轮只新增深审两项：CorrectHDL和2024 ACD；固定divisor SAT复用[N23已核论文及代码](bounded-method-core-ideation-review.md#91-固定divisor的sat重代入)。主审独立回读关键方法与源码。均未安装或执行作者软件，不认静态路径为复现实验。

| 对照及实际输入 | 方法和已读实现 | 与R2的关系／限制 |
| --- | --- | --- |
| [CorrectHDL v1，2025-11-20，§3.1–3.3](https://arxiv.org/html/2511.16395v1#S3)；完整C/C++及测试 | 先生成完整C++子模块、重新集成检查，再定义接口、生成HDL并差分验证/修复。作者代码固定`491d0d35166f12f0ca3bee911c038498ad8ce9c1`，不是论文实验冻结版本 | 已有HDL前分解/接口流程；所读路径未展示“消费者未实现时求任意Q是否存在”。不能因此推断全领域缺失；其流式接口宽度不足可多拍，与本例单消息条件不同 |
| [2024 ACD作者论文，§II、IV–V](https://people.eecs.berkeley.edu/~alanmi/publications/2024/tcad24_acd.pdf)；单输出布尔真值表、LUT目标 | 以不同cofactor数μ判可行、编码并构造composition；ABC固定`fba0adf4ccca0be59ddc6e77a85eb0cc64e04a8b`实际有两侧构造。所核路径最多11变量，局部LUT范围，编码搜索有限制 | 511响应类和最短编码在原理上属于既有分解问题。不是已支持本例40bit原始输入、多输出/位精确RTL前端；不能拿其规模限制当R2已解决的优势 |
| [IWLS2007固定divisor SAT](https://people.eecs.berkeley.edu/~alanmi/publications/2007/iwls07_ifs.pdf)，N23源码边界不变 | 给定`(h,c)`直接判函数依赖，可只判存在性、不构造Q，也可插值生成Q；不可达码可自由补全 | 正好覆盖§1判定，不要求满射、手写消费者或完整G。R2不能把这项标准能力算成新增机制 |

CorrectHDL关键实现：作者[pre1_decompose.py:91](https://github.com/AgenticHDL/CorrectHDL/blob/491d0d35166f12f0ca3bee911c038498ad8ce9c1/pre1_decompose.py#L91)规定函数分区/固定宽度，[pre2_generate_modules.py:109](https://github.com/AgenticHDL/CorrectHDL/blob/491d0d35166f12f0ca3bee911c038498ad8ce9c1/pre2_generate_modules.py#L109)要求完整C++实现和显式依赖，[s1_interface_setup.py:25](https://github.com/AgenticHDL/CorrectHDL/blob/491d0d35166f12f0ca3bee911c038498ad8ce9c1/s1_interface_setup.py#L25)读入已有C++再构造stream规格。[pre5_concat_and_test.py:123](https://github.com/AgenticHDL/CorrectHDL/blob/491d0d35166f12f0ca3bee911c038498ad8ce9c1/pre5_concat_and_test.py#L123)是集成及测试的prompt要求；实际subprocess位于L249，失败警告不认证通过。仅据静态源码判断流程，未冒称执行成功。

ACD关键实现：同一固定提交的[ac_decomposition.hpp:575](https://github.com/berkeley-abc/abc/blob/fba0adf4ccca0be59ddc6e77a85eb0cc64e04a8b/src/map/if/acd/ac_decomposition.hpp#L575)合并cofactor形成i-set，[L647](https://github.com/berkeley-abc/abc/blob/fba0adf4ccca0be59ddc6e77a85eb0cc64e04a8b/src/map/if/acd/ac_decomposition.hpp#L647)生成编码LUT，[L693](https://github.com/berkeley-abc/abc/blob/fba0adf4ccca0be59ddc6e77a85eb0cc64e04a8b/src/map/if/acd/ac_decomposition.hpp#L693)按编码和free-set函数构造composition；[L98](https://github.com/berkeley-abc/abc/blob/fba0adf4ccca0be59ddc6e77a85eb0cc64e04a8b/src/map/if/acd/ac_decomposition.hpp#L98)限定最大11变量。[C wrapper:26](https://github.com/berkeley-abc/abc/blob/fba0adf4ccca0be59ddc6e77a85eb0cc64e04a8b/src/map/if/acd/ac_wrapper.cpp#L26)分别连接可行性评估与实际分解/序列化；外层mapper调用本轮未查。单输出cofactor思想用于本例响应向量是本审查的数学对应，不冒称作者接口直接接收多输出RTL。

## 4. 裁决、未解决项与执行门

本轮建立了真实公开功能上的严格可区分例及最小消息宽度，**没有建立新处理机制或完整成本收益**。不能仅将成熟判定提前到LLM下游生成前，就认定核心创新。相对已读CorrectHDL路径的区别存在，但标准同信息SAT本来就能做；自动分解还允许直接构造编码及消费者，不能强迫基线手写Q。

没有实际位宽/带宽约束时，原R17仍是合法强方案。[N20零模型编译](direct-math-compiler-baseline-review.md)只覆盖其已声明的组合normal-only端点，使用后来的外部R/E/U公开profile；它没有验证本文保留单槽周期的E/U变体，不能作为完整端到端覆盖证据。本文9bit夹紧消息也不能移用到必须公开精确R的组合任务，[N30来源复核](specification-acquisition-review.md)给出具体区分。9bit数学最优不证明压缩有现实必要、RTL更省资源或生成更成功。为制造优势而增9bit要求不符合最低补工路线，也没有在本轮采纳。

| 后续门 | 所需输入与任务 | 输出／验收 | 当前状态与依赖 |
| --- | --- | --- | --- |
| R2-A 真实必要性 | 既有公开要求或真实使用方的接口约束；明确标准流程未满足的处理 | 一个可追溯案例，非专为本机制增加的限制；与用户讨论实质取舍 | 未满足；不得用手工下界替代需求 |
| R2-B 新增处理与同信息强基线 | 相同F/h/域/可见性；SAT依赖、自动编码/decoder和直接编译均保留 | 明确哪些输入/错误/成本是新流程多处理的；若只剩次序或字段改名则停止 | 静态评审未找到额外处理；暂不进入开发 |
| R2-C 有界资格及实际成本 | 仅在A/B成立后形成冻结计划与资源上限 | 方案、工具资格、真实总成本与首次功能结果各留账；再判断是否扩大 | 未准备、未运行；不以本文授权campaign |

本轮零模型、零SAT/HDL/数学脚本执行；没有新候选样本或性能分母。N27历史输入未知、N24定位待选均另列，不用任何一项解释为“整个项目无法继续”。正文v0.3、旧合同/评分、数据及历史运行保持原状，SCI/SCIE总目标仍未完成。

独立只读审查复核五份相关文档及原TD公开prompt，未见限定范围的Blocker/Major；9bit充分性、511类下界及旧合同边界成立。两项轻微表述问题已纠正：未定位不写成原件不存在，N26旧下一步与N27收口同步。主审检查五份文件的231条本地文件链接均可解析，清单28行均为6列；三版初稿SHA与本轮开始一致。
