# 英文 v0.3 新增证据独立核稿

日期：2026-10-21。模式：`review`，限定为新增事实、数值语义、证据单位与 §2.4 的固定版本引用。审阅对象为 [英文 v0.3](../../drafts/structure-responsibility-v0.3.en.md)，读取及原始记录核查结束时 SHA256 均为 `cea64185df23c80cef04af4797e8c4a903703671bbfb1d5559db0902edcf595d`。

**发现：Blocker 0；Major 0。** 在本轮授权范围内，未发现需阻塞整合的事实或语义错误；不为数量补造问题。这个结论仅表示新增文字与所核记录相符，**不确认方法核心创新、SCI充分性、可投稿状态或整个研究完成**。方法增量仍未确立的限制在文首、摘要、§2.4、§7及结论中保留。

本轮没有修改稿件、实验、检查器、候选或进度表，没有运行 HDL、SAT 或模型。仅新增本审查文件。采用 `paper-review-audit` 的有界审计原则，核对实验角色、分母/聚合、公式到源码及正反证据；未创建平行实验记录或进行新的广泛查新。

## 1. 新增结果逐项核查

| 稿件位置与结论 | 独立读取的原始依据 | 裁决 |
| --- | --- | --- |
| §5.5 第134行、§6.4 第175行：标准后端6过程；native ALU证明；wrong_mode反例；旧delegate响应UNKNOWN | `artifacts/responsibility-standard-cutpoint-20261021-01/runs/*/receipt.json` 共6份、其中semantic3；有效 `semantic_scripts_v2/*.ys`、切前/切后JSON、hierarchy、binding-check及两份SAT日志。native两个完成标记均SUCCESS；wrong_mode普通/局部SUCCESS、response FAIL。其反例a=b=0、mode01、z=1时actual=1、expected=0，与公开方程一致 | PASS。三个候选不是三个有效自由响应证明。稿件没有把旧connect适配的伪反例计成delegate真实失败，也没有称执行了EQY、FIR或TD标准适配 |
| §5.5 第136行、§6.5 第179行：16原始局部义务＋8控制＝24过程，12个不同module/source-hash pair | `responsibility-local-domain-proof-20261021-01/equations-and-positions.json`、全部24份原始script/receipt/log、每份pre-flatten `hierarchy.json`，以及prepared-manifest中的69个本地输入和41个原始输入hash。原始模块每类型4份；unique数为adder1、MAC3、return4、update4，共12 | PASS。独立重算20个SUCCESS（16原始＋4正控）、4个FAIL（负控），所有exit0、无timeout。未把exit0单独当证明 |
| §6.5 第183–186行：局部域256、16,384、16,777,216、8,589,934,592 | 逐份实际DUT类型、完整端口集合、direction/width/signed及miter连线；原始脚本只有known-binary输入约束，无取值或top-reachability假设。输入位数分别8、14、24、33 | PASS。这是2^8、2^14、2^24、2^33的符号证明域，不是执行了这些数量的仿真样本。稿件第188行明确区分 |
| §6.5 第179/188行：局部原始功能证明，不是whole TD parent proof | 独立miter仅实例化一个原始child和对应reference；没有top、切点或parent接线。`reference/td_update_core.v` 和实际TD miter的输入是完整signed17 return、signed8 value、unsigned8 alpha | PASS。§7.3 第210行明确“未报告whole-domain TD parent-response proof”；没有把两个child的局部证明自动升级成全系统/额外责任证明 |
| §5.5 第138行、§6.6 第192行：两个手写双输出alias控制，10个HDL过程，force与wrapper均pass | `responsibility-port-alias-qualification-20261021-01/qualify.py`、两份原始child、原parent与replacement miter、binding JSON、checker原始result及miter原始receipt/log。shared的sum/copy位标识同为[6,7]；separate分别[6,7]/[8,9]。每个checker与miter均完成16输入×4替换、128响应scalar比较，失败全0 | PASS。过程数独立重算为2 binding＋4 compile＋4 sim。wrapper保留原child产生copy，只替换sum边；原parent文件与candidate parent逐字节相同。稿件没有把这两个控制当模型样本或普遍alias安全证明 |

局部证明实际过程时长独立相加为 **18.456031499976234秒**，最大 **9.092897299997276秒**；稿件约18.46秒正确。所有24次SAT均具有20秒内部限制和30秒外部限制；没有因慢例扩大时限或重跑。

四个负控的WaveJSON均另按公开整数公式核验：adder的1→0、MAC的1→0、return的1→0、update在R=14336/value=0/alpha=0时E127→126且U0。它们恰为预先定义的首输出bit0翻转，不是模型错误或新的错误发生率。

## 2. 数学与符号方向

已逐份读取 `responsibility-local-domain-proof-20261021-01/reference/{adder4,mac_unit,discounted_return_core,td_update_core}.v`，并核 actual miter 的真实端口绑定。

- Adder以5位无符号和取低4位，对应模16；MAC将sample signed4、coefficient signed3、accum signed7扩至signed8，乘积范围[-28,32]、总和[-92,95]，最后取低7位，对应wrap7。不存在把coefficient改按unsigned处理的方向错误。
- Return将gamma零扩展为非负signed17，next/reward正确符号扩展，signed product算术右移4，体现负数floor；正常乘积和R范围都装得进所用17位。
- TD update先把return/value符号扩展到18位相减，再sat8得到E；alpha零扩展成正signed9，乘E后算术右移4，再sat8得到D；最终value+D用signed9后再sat8。与稿第98行的分步公式、符号、饱和次序一致。
- 这些完整局部域**已在生成前公开**：候选可见 `TD8-C0.txt:12–18` 明确每个signed17 return及至少18位精确差，`FIR4-C0.txt:12–17` 明确完整MAC局部域。公开任务相应位置为 `public-tasks.md:21–33、43–51`。因此此次local proof没有事后给原候选增加该局部义务；也没有把旧历史rl.py的signed17内部减法冒充本次新profile的实现。

标准后端有效v2的response cone无`$anyseq`；另有一个只属于旧local观察辅助cone的`$anyseq`，并未被assume，也不影响response。稿第175行限定的是**response cone**，没有错误宣称整个切后design中不存在该单元。旧delegate的alias split依然单独标UNKNOWN。

## 3. §2.4 对固定近邻记录的忠实程度

本项比对对象是 [architecture-conformance-gap-review](architecture-conformance-gap-review.md) 中已经固定的原文/实现定位；本轮没有重新执行作者工具或做新的独立外部全面复现。

| 稿件 | 固定记录依据 | 裁决 |
| --- | --- | --- |
| 第47行与reference10：SV-Gap检查真实reset pin、排除识别的同步器、区分unknown/tool error，不能弱化为名字存在 | 固定SHA `856c5832b2b5f2dfbeac58a6e4961ecc0550e4df`；该review第17、28–42行给实际Yosys、reset-pin检查、证据合同和native规则范围 | PASS。稿明确是作者软件/公开记录的阅读而非本项目重跑；没有把规则覆盖差别写成框架不可能表达本任务 |
| 第49行与reference11：RTL-Obliger的FSG→CWE/缺失证据→信号义务→两阶段生成；公开树的实现核查上限 | arXiv:2608.26588v1；作者树SHA `4d5d944fb35e5c372b8e9620b5785a91d061f881`；review第18、48–66行区分方法、benchmark/Vanilla代码与未取得的完整方法实现 | PASS。“inspected public repository”保留了范围，不是断言作者不存在其他实现。其省略安全要求的输入与本稿显式义务没有被伪装为同信息性能对照 |
| 第49行与reference12：GRADE-RTL检查I/C/H/M/F；所核completeness不是任意值响应规则 | arXiv:2609.25335v1；作者代码SHA `4feb91a7a8638671c18c3b1c1f62b156f39dc176`；review第19行固定parsing/stages实现位置 | PASS。稿没有说它只编译，也没有从所核M实现推到整个框架无法表示更多合同 |

第51行明确把declared intent、标准工具和存证列为已有能力，并承认尚未证明本稿的具体方法增量；第214行又明确“有界阅读未见精确流程”不构成新颖性证据。因此本轮没有需要纠正的新增宽泛创新断言。完整新颖性和文献完备性仍为 **NEEDS_EXTERNAL_VERIFICATION**，不能由这项局部引用一致性审查升级成确认。

## 4. 统计单位、原件与旧稿

- 原12个project、同child固定父12个construction、局部16个module位置、8个local控制、2个alias手写case、标准后端重复使用的3份ALU源，确属相互重叠或不同类型的证据。稿第106、120、171、179、188、192、210行明确分开；没有把它们加成额外独立模型样本、把SAT域大小当测试量，或把16位置与12种源码身份混为同一分母。
- 原12份candidate的全部capture source hashes均只读复核一致；local proof的原始snapshot还与prepared-manifest保存的原始路径hash一致。旧24评价汇总SHA仍为 `7163d5cb0060978878e39903a3c4017bbe6a7b1f7d0b06d032eab881a2e2564c`，与先前完成记录相同，未重跑它。
- 英文v0.2当前SHA `71ec0c4e8afa499b307eea854514004489daf897eafc1652ee9356e8c12253da`，与 [v0.2独立核稿记录](manuscript-v0.2-independent-review.md) 的最终复核hash相同。
- 中文v0.1本轮没有修改，当前SHA `49136f9f3add681024ffa6c7e44f71daccdd6994f8689c4d36a26a792d9abeb2`。没有其最初创建时独立baseline hash，因此**不作从最初创建到现在一直原字节未变的历史认证**；只能报告当前身份和本轮未改。该限制不是本次新增实验数字的反证。

## 5. 停止理由与保留限制

本轮指定范围未发现未解决Blocker/Major事实或语义问题，故结束审查，不追加实验、改稿循环或为了quota扩展问题。报告不评价最终排版/渲染，不开展全稿语言润色，也不把静态审稿替代外部投稿/作者确认。

方法核心未确认、未显示省工/生成收益、无真实native责任违规、标准wrapper及完整IR等强替代尚未显示劣势，均仍是论文的实质研究边界；它们已被稿件承认，**不能因本轮事实核稿通过而转为正面方法效益或创新结论**。
