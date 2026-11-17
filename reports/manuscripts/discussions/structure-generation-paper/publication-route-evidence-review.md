# SCIE文章类型与当前稿件交付门槛复核

核查日期：2026-10-21。状态：N25独立准备完成，未选择期刊或新的研究定位。目标是澄清“最低可辩护论文”仍需什么，不以检索期刊代替寻找gap、方法增量和可信证据。N24贡献定位问题仍待用户答复；本轮不开始其S1–S5，不开发新工具、不采纳任务/评分、不运行模型/HDL/solver、不修改正文。

**后续状态：** 用户于2026-10-22选择先评审工具系统贡献，并明确先可靠性、不主张人工省工，见[N37](contract-frontend-task-readiness.md)。上段及N25正文保留当时状态；N41补核SoftwareX官方评审材料见第6节，仍未核实其当前SCIE，不列为已确认目标，也不据栏目代选研究范围。

## 1. 结论及其边界

**没有全新算法，不是本轮已核IEEE Access政策中的统一否决条件；有可运行原型或12份全过结果，也不是达到其贡献标准的充分条件。** 官方审稿要求允许新颖性不必很高，但需区别于已有发表工作、技术可靠并贡献知识；这只是该刊政策，不能推广为所有SCI期刊的统一门槛。[IEEE Access审稿要求](https://ieeeaccess.ieee.org/reviewers/reviewer-guidelines/)

官方列有Applied Research、Methods和Negative Result等类型；应用研究须有量化验证，负结果须非平凡、问题有意义且研究严谨。改类型不能免除证据要求，也不能把“本研究没找到有利结果”自动当作有价值的反证。[文章类型](https://ieeeaccess.ieee.org/authors/submission-guidelines/)

用户仍要求首篇方法本身有新增机制。期刊容许负结果不取消这一偏好；N24若改成验证工具贡献仍需用户选择。当前不推荐直接投稿v0.3，也不恢复已停止的连接、局部分区或R1b核心。

## 2. 主源与实际访问结果

只用期刊、出版商及Clarivate主源。两名研究协作者分别核SoftwareX、Science of Computer Programming（SCP），主审核IEEE Access并回读SCP出版商正文。访问失败按失败保留；不凭搜索摘要、影响因子、Scopus或笼统Web of Science字样确认SCIE。

| 对象 | 实际读到的主源事实 | 未获确认及允许的结论 |
| --- | --- | --- |
| IEEE Access，ISSN2169-3536 | 官方[收录页](https://ieeeaccess.ieee.org/about/bibliometrics/)明确列Science Citation Index Expanded；[作者标准](https://ieeeaccess.ieee.org/authors/preparing-your-article/)、[文章类型](https://ieeeaccess.ieee.org/authors/submission-guidelines/)及[审稿标准](https://ieeeaccess.ieee.org/reviewers/reviewer-guidelines/)均已打开正文 | [MJL按ISSN查询](https://mjl.clarivate.com/search-results?issn=2169-3536)本工具不可访问。当前SCIE依据为期刊明示，不是已完成Clarivate单刊复核；投稿前仍需复核届时覆盖及单位认可 |
| SCP，ISSN0167-6423 | [Elsevier Shop的Description](https://shop.elsevier.com/journals/science-of-computer-programming/0167-6423)正文明确Research Papers/Software两track；Software Track刊登现有、有用软件的Original Software Publications（OSP），范围包括开发工具、验证和硬件设计的软件方面 | 当前Guide、Aims、Insights均403；未确认OSP具体模板/许可/公开/评价条款及当前SCIE。不能把Research Papers下的Descriptive software technology认作名为Software/System Descriptions的独立现行类型；本轮不列为已确认SCIE目标 |
| SoftwareX，ISSN2352-7110 | 当前未取得足以确认投稿细则或具体索引的主源正文 | [Guide](https://www.sciencedirect.com/journal/softwarex/publish/guide-for-authors)、[Aims](https://www.sciencedirect.com/journal/softwarex/about/aims-and-scope)实际访问403；[Elsevier Research Elements](https://www.elsevier.com/en-gb/researcher/author/tools-and-resources/research-elements-journals)读取超时；[MJL](https://mjl.clarivate.com/search-results?issn=2352-7110)不可访问。细则及SCIE均未确认，不等于未收录 |

SCP的三个失败URL分别为[Guide](https://www.sciencedirect.com/journal/science-of-computer-programming/publish/guide-for-authors)、[Aims](https://www.sciencedirect.com/journal/science-of-computer-programming/about/aims-and-scope)、[Insights](https://www.sciencedirect.com/journal/science-of-computer-programming/about/insights)。两名协作者各以4主页面为上限；主审后因SCP商店正文成功而顺带试同结构SoftwareX商店URL，得到404，未据此推定期刊不存在或停刊。没有为凑齐期刊名单继续无效重试、改用第三方排行或降低证据等级。

## 3. 期刊明示要求与本项目判断分开

| 已核要求/政策 | 对当前工作意味着什么 | 分类 |
| --- | --- | --- |
| IEEE Access要求有知识贡献、可靠分析、结论受数据支持及适用相关工作 | 必须说明相对强近邻新增的处理或知识；工具能表达同义务不自动否决系统贡献，但当前“省工”“更有效生成”仍无证据 | 期刊要求＋项目判断；[作者标准](https://ieeeaccess.ieee.org/authors/preparing-your-article/) |
| IEEE Access所有文章类型经过严格同行评审 | Negative Result不是回避贡献、设计与证据审查的快捷标签 | 期刊政策＋项目判断；[类型页](https://ieeeaccess.ieee.org/authors/submission-guidelines/) |
| IEEE Access投稿需匹配的模板源文件与PDF、作者资料/简介、投稿人ORCID及AI文字披露 | 现有Markdown是研究初稿，尚非完整投稿文件；作者和披露最终需要实际作者复核 | 期刊明确交付要求；[清单](https://ieeeaccess.ieee.org/authors/submission-guidelines/) |
| IEEE Access提供发表后代码复核及可复现徽章计划 | 不能把该计划中的DOI、容器或徽章当所有初次投稿的统一强制条款 | 期刊政策边界；[可复现计划](https://ieeeaccess.ieee.org/authors/reproducibility/) |
| SCP出版商确认有OSP轨道，但具体指南未读到 | 可以保留“软件贡献具有独立文章路径”的事实；不能承诺软件公开方式、字数、许可证或SCIE达标 | 已核事实与未知分离；[出版商说明](https://shop.elsevier.com/journals/science-of-computer-programming/0167-6423) |

本轮不采集或重报费用、录用率、工期，也不按“看起来容易”排序。期刊政策没有提供一个适合本项目的统一任务数、模型数或必需板卡数，不能杜撰这类最低标准。

## 4. 对现稿逐项核查：完成了什么，还缺什么

本表回读[v0.3正文](../../drafts/structure-responsibility-v0.3.en.md)、[独立核稿](manuscript-v0.3-independent-review.md)、[跨任务结果](cross-task-pilot-review.md)、[字段/成本审查](handoff-cost-decision-review.md)及[N23停止证据](bounded-method-core-ideation-review.md#11-n23裁决)。它评估当前证据，不预选N24。

| 交付项 | 当前可核事实 | 尚缺的、与主张相称的最小工作 |
| --- | --- | --- |
| 完整研究初稿 | v0.3有摘要、相关工作、方法、实际结果、讨论、结论、可用性与AI说明；限定事实/语义核稿无剩余Blocker/Major | 科学贡献及发表价值仍未验收；不能用事实一致的内部核稿替代编辑/同行评价 |
| 方法或系统增量 | 自由切点、NI及函数依赖已有强先例；本地工具执行明示G，未自动发现角色或域外语义 | 若保留方法论文，应先形成具体新增处理和同信息区分；若转系统贡献，应先核实际作者工作与交付错误/成本端点。两者不能只靠换术语 |
| 原生生成观察 | 3任务×2提示×2尝试，共12份；12固定父复用同一批child；两组有限检查均全过 | 只支持该批零观察差异。若主张“不需要审计”或“提示等效”，还需独立合理设计及充分性依据；当前不事后替12样本补一个更强的检验目标 |
| 工具与语义资格 | 有手工正负控制、标准ALU切点、16局部全域证明及2别名控制；TD父响应仍有限采样 | 按最终主张说明覆盖与未决。当前不要求为了成稿机械补全TD全域，也不把局部证明扩成整个系统证明 |
| 软件可复用交付 | v0.3明确代码/数据只在本地artifacts，未对外发布或存档；原型限定单边界组合有限检查 | 若主张可复用软件，需固定版本、独立可运行入口、依赖/示例/操作说明、分发与依赖许可核查、复现证据。此处是工程判断，不冒称已读到SoftwareX/SCP强制细则 |
| 投稿文件与作者事项 | 尚无当前完整模板源/PDF与最终作者资料；正文已说明需作者复核 | 贡献与证据收敛后再做模板、作者、披露和可用性准备；不外发、不支付、不提交，也不提前公开代码 |

当前的主要缺口是**可信贡献与适当证据**，其次才是稿件格式和可复现交付。上板、PPA、训练、增加模型、强行取得正结果或全部改成形式证明，并非本轮依据期刊政策得出的统一必需项。需要多少新实验由具体研究问题与主张决定，不能倒置为先增加工作再寻找故事。

## 5. 合理执行顺序

1. 保持N23停止结论；等待N24贡献定位选择，原研究目标不缩减为“已有一份初稿”。
2. 在选定范围内，先核真实未满足工作与最接近方法的具体差别；没有差别或可测价值就停止该候选，不直接扩模型调用。
3. 先给同信息、同保证强基线和成本/可靠性端点，再开发与执行有明确资源上限的资格/研究计划。
4. 用实际结果重写贡献与证据主张；允许保留负结果，但其科学意义和研究设计须独立成立，不承诺正效果或录用。
5. 最后准备目标模板、可复核工件、作者事项及准确披露；外部发布/投稿继续单独处理。

这不是新平行进度表；N25状态只记入论文唯一清单。未解决的研究定位不会由期刊栏目自动代选，本轮也未新增相关范围问题或重复催问用户。

独立只读审查核对本文及其引用的主源/已有本地依据，未发现限定范围的实质问题：政策、推断与未知分开，未混同SCIE与其他索引，未将12全过推广为等效或无用，也未强加上板/全域证明等统一门槛。审查不确认科学贡献或录用资格，未修改文件或执行实验。收尾文档检查通过，三版初稿哈希均与本轮开始时一致。

## 6. N41：SoftwareX官方评审材料补核，索引仍未确认

日期：2026-10-22。独立研究者限两次发现查询及官方材料，主审另成功打开[Elsevier Research Elements介绍](https://www.elsevier.com/en-gb/researcher/author/tools-and-resources/research-elements-journals)与[SoftwareX官方评审表](https://legacyfileshare.elsevier.com/promis_misc/softwarex-reviewer-form.pdf)。介绍确认刊登研究软件及应用；评审表明确考察研究贡献/复用、经验评价、安装运行与复现、开源许可、文档/依赖及主要功能测试。

评审表没有把新算法列为统一条目，这是对本表的观察，不是“成熟算法包装即可发表”的政策承诺；软件独特用途、技术质量和实际价值仍须证据。官方Guide及收录页访问失败，Clarivate页面不可读，完整当前投稿硬条件与SCIE仍未确认，不以二手期刊表补齐。新增可读材料替代上表SoftwareX“无主源正文”的历史访问状态，但不消除其收录与完整细则的未知。

这支持继续评审可复用工具系统，而不因后端成熟就一票否决；也不将当前[监测工件方法卡](compiled-monitor-audit-method-review.md)视为已经达标的软件。没有选择期刊、外部发布、支付或投稿。
