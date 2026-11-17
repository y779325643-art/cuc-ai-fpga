# Codex原生子agent作为被测生成模型：首轮开发实验

日期：2026-10-21。用户已明确要求使用Codex子agent作被测生成模型，并授权持续研究、实验和SCI初稿。本记录是开发实验，不晋级为官方证据，不替代现行研究权威。[唯一进度清单](../2026-10-21-structure-generation-paper-checklist.zh.md)维护整体状态。

## 1. 预先范围与实际调用

预先写入[plan.md](../../../../artifacts/codex-native-td-pilot-20261021-01/plan.md)：一个新明确的公开signed 8bit/Q4 TD三模块任务；全局义务、模块定位义务两种提示，各生成一次。所有数学、握手和两个公开区分例在两组各出现一次；改变的是排序与模块标签，不能称输入token严格相等。

生成使用`collaboration.spawn_agent`，均`fork_turns=none`，未指定模型或推理覆盖。任务身份：`/root/candidate_td_global_01`和`/root/candidate_td_located_01`。两者只收到完整公开提示，没有父对话、源码、评价器、测试向量或反馈。两份最终JSON均被保留，无修复、补采样或选择最好结果。

候选工具被明确禁止，但原生spawn接口不能硬禁用工具。生成后的[只读运行审计](../../../../artifacts/codex-native-td-pilot-20261021-01/runtime-audit.md)定位本线程的两份子会话记录，逐份确认`turn_context`配置为`gpt-6.1-sol`、`effort=ultra`，记录的function/custom工具调用数均为0；原生最终JSON的全部源码字符串与保留响应一致。审计没有导出开发提示、推理或其他对话。原始任务部分在本地记录中含加密内容，公开明文输入由父dispatch保存，不声称解密或字节审计了加密输入。这些观察不等于硬访问拒绝或provider权重快照证明。采样参数、原生调用时长及货币成本仍未知；不能把当前调用写成零成本，也不能仅凭零工具调用宣称正式基准隔离完备。

原生记录的turn_token_usage分别为：global输入30287（缓存12032）、输出1888、总32175；located输入30412（缓存12032）、输出1883、总32295。输出内的推理token分别851、868，不重复加到total。它们包含运行上下文，不等于公开提示字符数或可计价API账单；单个配对不能支持成本优势。

## 2. 输入与保存边界

输入见[全局提示](../../../../artifacts/codex-native-td-pilot-20261021-01/prompts/global.txt)、[定位提示](../../../../artifacts/codex-native-td-pilot-20261021-01/prompts/located.txt)。原生final消息分别保存为[global.json](../../../../artifacts/codex-native-td-pilot-20261021-01/responses/global.json)和[located.json](../../../../artifacts/codex-native-td-pilot-20261021-01/responses/located.json)。仅捕获消息载荷，不声称保留不可见的网络帧。

程序严格校验JSON重复键、唯一`files`键、三文件白名单、字符串类型、大小和行数，然后写出原文UTF-8字节；结果分别105、108行。父进程元数据移到独立receipts目录，候选目录只含三份RTL。候选与仿真快照的源字节一致；未作格式纠正、代码编辑或自动重试。

提示保存时Windows文本换行形成CRLF，而工具消息使用LF；两者逻辑文本一致，不能混淆文件字节hash与请求文本hash。LF逻辑请求长度分别3853、3969字符；逻辑SHA256分别`b5a7abca67bc74dbfb9f250158572555e1ca65c0a1870313c7cc7006d5be5712`、`31c9b961588d9e36f2a9ddd8690e6be9e8140cd135a528091921fc9fed27e0a1`。物理文件hash分别`05f8783799f165488bfa09f68978f0b1fafc7dca7cf72cf6f3f82fe2615ba0dd`、`48e88ae71e44b3c92513925f47e29e747943b3f6b741513dd0988abf782e3e8f`。

## 3. 独立评价与控制资格

[评价器](../../../../artifacts/codex-native-td-pilot-20261021-01/harness/evaluate.py)由开发agent独立编写，只使用本次公开数学/事务规格，没有导入生产oracle或私有刺激。源SHA256为`0ea952e504cb12e45a9362c5f24abd15420b75733c9656ea65970a76e64e39d4`。

数学为整数floor与sat8，TD误差先饱和再缩放；顶层是单槽弹性寄存器。每个控制/候选均使用16个边界tuple、64个固定seed随机tuple，132周期，含背压、替换、气泡和两次运行中复位。实际接受80、输出78、复位丢弃2；40周期输出阻塞。不能把复位取消的2笔记为无故丢失，或只报78而删除接受分母。逐周期比较ready/valid、两数据、接受和消费事件，并核对完整计数。

工具为Icarus/vvp 14.0 devel（s20260301-220-g78750c51d-dirty），每编译/仿真30秒上限，无综合、训练、hidden评价或额外API。评价器先通过3项开发单测，并真实执行正确参考及late-saturation错误控制；原始控制与日志见[harness验证](../../../../artifacts/codex-native-td-pilot-20261021-01/harness/verification.md)。

## 4. 实际结果

| 对象 | 是否模型样本 | 编译退出码 | 仿真退出码 | 有限检查结果 |
| --- | --- | ---: | ---: | --- |
| 手写正确参考 | 否 | 0 | 0 | 通过 |
| 手写延后饱和错误控制 | 否 | 0 | 1 | 正确拒绝；首错cycle5，updated_value实际15、预期7 |
| 全局义务Codex首次输出 | 是，1次 | 0 | 0 | 通过全部本次检查 |
| 模块定位义务Codex首次输出 | 是，1次 | 0 | 0 | 通过全部本次检查 |

模型计划分母2，实际输出2、解析通过2、编译通过2、有限功能检查通过2，无重试或被丢弃位置。手写控制不加入这2个模型样本。每组仅一个输出、同一任务，不能报告总体成功率提高、统计显著或方法优越。

模型原始结果：[global](../../../../artifacts/codex-native-td-pilot-20261021-01/harness/results/20261021T161227228453Z-native-global-01/result.json)、[located](../../../../artifacts/codex-native-td-pilot-20261021-01/harness/results/20261021T161234577644Z-native-located-01/result.json)。两者共有刺激hash为`93c296cd42eba4dc8baada3d2486070c38403393e915a0baa6e43c9eb7d14bd8`，评价器源hash一致。

## 5. 结论与下一步

已经实际验证：原生Codex子agent能够作为本次公开开发任务的首次生成端，输出可以通过主进程白名单保存并由独立HDL评价链检查。当前任务中没有观察到两种提示的结果差异；不将其写成定位义务方法有效，也不能据此证明该方法无效。

来源与有限功能通过尚不能完整证明内部计算责任。签名/实例扫描不是完整解析，不证明所有算术都在承诺模块内，或必需实例对结果有实际贡献。接下来核查“模块存在但被行为重算旁路”的责任缺口，先做有公开承诺的正反例及强模板基线资格，再决定是否值得扩大模型实验。这项后续工作仍是候选，不因本轮两份通过就确认为SCI创新。
