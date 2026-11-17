# N38：正式发表状态与创新性判据分离

核对日期：2026-10-22。**按用户最新判据，只有已核实正式期刊或会议发表的工作，才能据其已发表内容讨论创新是否已被占用。** 预印本、软件、录用声明和会议日程保留技术比较与应有引用；不单凭这些身份作占用裁决。“发表未确认”也不等于已证明未发表。

本轮有界核查七项当前关键近邻，不是全部文献的发表状态普查。正式身份不替代方法深审；有正式发表也不自动证明完整方案重复，仍须对应具体处理、输入、输出和保证。

## 1. 七项状态

| 工作 | 已核主源与版本 | 本轮可成立的身份及用途 |
| --- | --- | --- |
| AutoSVA | DOI `10.1109/DAC18074.2021.9586118`；[Crossref注册记录](https://api.crossref.org/works/10.1109/DAC18074.2021.9586118)及[作者机构出版记录](https://collaborate.princeton.edu/en/publications/autosva-democratizing-formal-verification-of-rtl-module-interacti/)一致；DAC 2021、IEEE、535–540页，Published 2021-12-05。 | **正式发表确认**，可逐项裁定其已发表机制覆盖的主张。主审打开机构记录，IEEE页受访问限制，DOI解析未取得正文；方法依据另见下节原文/固定源码，不把访问限制写成未发表。 |
| CPPL | [arXiv:2605.17892](https://arxiv.org/abs/2605.17892)，v1 2026-05-18；摘要页未列journal-ref或出版社DOI。 | **正式发表未确认**；保留已深审的方法对照，本轮未找到正式出版记录，不由此单独认定创新被占用。 |
| HINT | [arXiv:2608.07625](https://arxiv.org/abs/2608.07625)，v1 2026-08-07、v2 2026-08-19；[ASP-DAC 2027日程](https://easychair.org/smart-program/ASP-DAC2027/2027-01-28.html)列2027-01-28 Session 12D 17:20。 | **预印本与会议日程确认，正式发表未确认**。日程题名多出Intermediate，九名作者对应；未来排程不是截至核对日已出版论文集的证据。 |
| VeriGraphi | [arXiv:2604.14550](https://arxiv.org/abs/2604.14550)，v1 2026-04-16、v2 2026-04-19；未列journal-ref或出版社DOI。 | **正式发表未确认**；[N36固定输出复核](generated-artifact-binding-review.md)仍是技术证据，不变成正式发表身份或已认证运行失败。 |
| VeriRefine | [arXiv:2607.18519](https://arxiv.org/abs/2607.18519)，v1 2026-07-20；未列journal-ref或出版社DOI。 | **正式发表未确认**；保留实际方法比较，不将预印本身份升级。 |
| EQY | [YosysHQ官方文档](https://yosyshq.readthedocs.io/projects/eqy/en/latest/)确认工具身份；已有固定源码复核见[N37](contract-frontend-task-readiness.md#4-最接近的能力已存在贡献须落在具体交接)。 | **工具存在确认，自身对应正式论文未确认**。其他论文使用EQY、Yosys已有论文，不能替代EQY自身的出版证明。仍是实现强对照。 |
| SV-Gap | [DataCite注册记录](https://api.datacite.org/dois/10.5281/zenodo.21198938)：Shraddha Sridhar，2026，Zenodo，`resourceTypeGeneral=Software`；已有固定源码及方法深审。 | **软件归档确认，期刊／会议论文发表未确认**。软件DOI不是期刊／会议论文DOI，不单凭归档作创新占用裁决。 |

四项arXiv摘要页给出的`10.48550/arXiv.…`是arXiv经DataCite分配的DOI，不能代替出版社记录。CPPL/HINT/VeriGraphi/VeriRefine各完成一次标题发现查询并打开官方摘要；AutoSVA/EQY/SV-Gap共三次发现查询及身份主源核对，主审另核AutoSVA机构记录。未取得出版证据的项保留未确认，不通过扩大猜测填空。

## 2. 已发表AutoSVA究竟覆盖了什么

方法判断复用已核[论文§III](https://arxiv.org/html/2104.04003v1#S3)与作者库`cfeb42d827fa80282db552aac2a9ee917ad04dcd`的[义务实现L556–663](https://github.com/PrincetonUniversity/AutoSVA/blob/cfeb42d827fa80282db552aac2a9ee917ad04dcd/autosva.py#L556)，详见[此前深审](feasibility-assumption-neighbor-review.md#2-复用近邻已有交接不能弱化)。本轮核发表身份，没有运行框架或重做完整实现审计。

| 拟议主张 | AutoSVA已发表方法及对应实现 | 当前可作的判断 |
| --- | --- | --- |
| 从接口意图自动生成验证义务 | 事务注释生成辅助模型、假设、断言和工具文件，包含活性、稳定性及数据完整性；方向决定assume/assert。 | “声明合同→自动验证义务”这一宽主张已有正式发表先例，不能单列为本篇新增机制。 |
| 在层次间交接假设和责任 | 可将子模块的环境假设交到父层核对；允许pre-RTL产生属性。 | 不能说已有方法都只做生成后的普通仿真，或把前置交接本身当新核心。 |
| 关联实际DUT并发射工具工件 | 作者实现已有自动化验证脚手架与绑定；并不以替换DUT为必要步骤。 | 审核原件是合理研究对象，但这点本身不足以区别AutoSVA。 |
| 特定自由边界响应及变换可靠性 | 当前原型的完整F/h/G自由边界响应、数学角色及别名/变换资格与其事务注释不是同一合同。 | 这是待比较的具体差别；未核到等价入口不证明缺失，合同不同也不自动成立创新。需新增处理和实际资格／可靠性证据。 |

因此，当前不能仅靠“AutoSVA已发表”否决整个工具问题；也不能仅靠其未明列本原型合同而宣布新核心成立。

## 3. 修正哪些裁决，不恢复哪些投入

本文件是后续创新性判断的当前口径。历史深审保留当时范围和原文，不再把其中关于CPPL、HINT、VeriGraphi、VeriRefine、SV-Gap等的技术重叠，直接读作已发表创新占用。它们的实现能力仍须如实比较和引用。

N36所核“Learn the Interface…”的VLSID 2027录用表述也不自动达到正式发表门槛；本轮未重查其出版身份。[OpenTitan本轮固定工程框架](external-architecture-audit-task-review.md)同样只确立工程需求和已有实现，没有借代码直接裁定论文占用。

已有停止投入结论按原因保留：[N20](direct-math-compiler-baseline-review.md)的同信息直接编译结果、[N33](comparison-endpoint-audit.md)的比较起点、[N35](state-adapter-standard-baseline-review.md)的普通控制构造、真实任务适配及缺少区别处理/效益证据，都不因某近邻发表未确认而消失。若某一历史判断**仅**凭未核正式发表的重叠作占用结论，该理由不继续有效；恢复开发仍需具体工作、区别处理和适用范围，不能由“未确认发表”反推原创。

目前状态为：**宽泛义务前端已有正式发表先例；本篇具体增量仍未成立，也未被本轮判定全部占用。** 接下来先完成可靠性工具的S1/S2，不为刷新发表状态重复检索，不把身份核验替代方法评审或实验资格。

独立收尾者核本文、外部需求报告及既有AutoSVA方法记录，无Blocker/Major/Minor；其直接复用本轮已核AutoSVA/EQY/SV-Gap身份，未另核其余四项的发表状态。没有新增框架执行或正文修改。

**N39后续：** [交付可靠性审查](verification-delivery-reliability-review.md#2-已发表的空泛性检查已处理哪一层)另确认Kupferman–Vardi的STTT正式论文，核到公式空泛性与见证方法；不把公式检查扩成全部绑定或干预变换保证。上文七项是N38原有核查集合，不随这项后续证据重写其分母。

**N40后续：** [配置义务复核](configuration-obligation-completeness-review.md#2-正式发表ocra方法及当前工具能力分开)确认OCRA的SCP2015论文，回读实际合同细化及义务生成方法；2.1.0手册的参数扩展另列技术能力，不自动算2015已发表机制。本文的N38七项集合仍保留原分母，不将后续新近邻混入该表的计数。

**N41后续：** [实际监测工件评审](compiled-monitor-audit-method-review.md#2-正式发表近邻验证参考监测器再检查实际监测器)确认Basin等IJCAR2020正式定稿，区分参考核心的正确性证明与对其他监测器的有限差分。不再把“参考语义→监测器验证”宽流程当新；其未验证适配层和不同语言范围也不自动成立本篇gap。固定Yosys代码仅作实现强对照，不借软件身份直接作正式论文占用裁决。
