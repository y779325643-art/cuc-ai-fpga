# PC 字段责任与确定性装配规则 v1

## 状态和适用范围

- 版本：`pc-field-responsibility-v1`。
- 本文细化已确认的 [分层研究设计](2026-09-11-pc-layered-study-design-v1.md)。
- 状态：**已按用户“继续执行”的授权实现独立开发接口，离线示例、完整 G3 及独立重放通过；不替换旧 Runner**。
- 实现与已注册字段集见 [PC decision interface v1](../../contracts/pc/README.md)。
- 现有 PC 序列化仍为 `System-HIS v1.2`，旧接口及历史 M0–M5 记录保持原定义。
- 仅规定新 PC 生成接口的责任划分，不改变 EA 主研究问题、全局生成/拒绝策略或实验权限。

设计依据为当前注册的 [PC Schema](../../contracts/system-his/system-his-v1.2.schema.json)、
[冻结需求上下文](../../agent/src/sr2fpga_agent/frozen_context.py)、
[PC 生成边界](../../agent/src/sr2fpga_agent/generation/context_his.py) 和
[H1 检查器](../../agent/src/sr2fpga_agent/system_his_v12_checker.py)。
本表规定责任边界；新装配器位于 `agent/src/sr2fpga_agent/pc_assembly.py`。
只有新决策 Schema 显式声明的字段得到支持，不宣称已迁移所有旧 PC 扩展字段。

## 四类责任

| 类别 | 含义 | 允许的操作 |
| --- | --- | --- |
| F：冻结事实 | 已授权的公开需求及目标 profile 中的确定值 | 原样复制，不推断新事实 |
| M：模型决策 | 架构、语义、接口补充和需求到结构的选择 | 模型输出，程序检查，不偷偷纠正 |
| D：确定性派生 | 从 F/M 唯一计算的重复信息 | 机械派生，记录规则版本与来源 |
| E：外部证据 | 实际工具输出、评测结果和运行记账 | 由对应生产者记录，不由模型或装配器声称通过 |

混合对象逐叶子分配责任，不能因一部分来自需求而让程序填完整个对象。
F 必须来自 generation-visible 的冻结输入；内部任务族、方法、划分、复本、隐藏用例
和参考工程信息不得混入 PC 或模型提示。运行身份与共享费用放在独立台账中。

## 字段责任矩阵

| PC 字段 / 字段组 | 责任 | 规则 |
| --- | --- | --- |
| `schema_version` | D | 装配器固定为目标序列化版本，不要求模型填写 |
| `project_name` 等身份字段 | D/F | 使用冻结上下文的身份规则；不让不同实验条件产生不同 PC 身份 |
| `intent.user_prompt` | F | 复制公开需求文本，不作为结构/行为映射的自证材料 |
| `intent.requirement_trace.requirement_id/required_facts` | F | 从冻结 Envelope 复制，保持值、类型、单位、大小写和事实来源 |
| `intent.design_goal/assumptions` | M | 只能解释已接受需求；新增假设不能自动升级为已确认事实 |
| `top.name/ports/interfaces/parameters` | F 或 M | 明确的公开接口逐字段复制；未规定部分由模型选择并满足需求，程序不猜接口 |
| `top.clocks/resets` | F 或 M | 复制明确的频率/极性等；内部域选择仍是模型决策，不能把所有时钟默认成同一值 |
| `components[].name/semantic_kind/ports/parameters/intent/combinational` | M | 与公开约束一致；不能仅凭“没有列出状态”自动推断组合逻辑 |
| `components[].source` | M，受公共路径规则约束 | v1 保留源文件布局选择，检查安全路径；不能为某一对照条件额外固定布局 |
| `instances[].name/component/clock/reset/parameter_values` | M | 实例及绑定必须显式给出，未知引用报错，不代选组件或时钟 |
| `state.{registers,counters,fsms,buffers,memories}[]` | M | 状态集合、name、owner、宽度/深度、FSM 转移等由模型决定 |
| `instances[].owns_state` | D | 唯一来源为 state 中的 owner/name，不接受模型重复填写 |
| `data_flow` | M | 连接端点、方向、协议、CDC 等关系不是装配器推断的内容 |
| `control_flow` | M | 条件、作用和关联状态由模型决定，不生成缺失的功能规则 |
| `timing.primary_clock` | M 或明确 F | 多时钟下不自动选择；目标频率按已确认 profile/需求约束检查 |
| `timing.constraints` 与工件路径别名 | D | 使用所有条件共同冻结的路径策略；路径存在不代表时序约束已实现或通过 |
| `resources.optimization_goal` | F 或 M | 有明确用户偏好则复制，否则保留模型选择及其来源，不宣称用户已同意 |
| `resources.expected` | M，可缺少估计 | 只能标为预测；缺失不得填测量零值；实际 QoR 属于 E |
| `verification.acceptance_obligation` | F | 复制已接受验收义务，不代表验证已执行 |
| `verification.scenarios/pass_condition` | M | 具体场景和判定描述仍由模型提供，不变成可信 oracle |
| `verification.testbench` | D | 仅为候选工件路径，不指向隐藏或可信评测材料 |
| `artifacts.top_module` | D | 来自最终 `top.name` |
| `artifacts.rtl_sources` | D | 按源声明顺序收集 `components[].source`，同一路径只列一次；不随意重排有依赖的编译顺序 |
| `artifacts.testbench/constraints/manifest/predicted_qor` | D | 从共同工件路径规则和对应字段生成，避免重复独立填写；不生成虚假的报告内容 |
| 事实到结构的语义绑定 | M | 模型选择事实落到哪个语义对象/字段；程序不能替换成碰巧数值相同的字段 |
| 绑定的 RFC 6901 编码、数组索引 | D | 只把已明确且唯一的对象选择编码成最终 PC 指针，不决定绑定含义 |
| `unresolved_facts` | D，基于检查结果 | 不能无条件置空；缺少或冲突的绑定必须显式保留失败 |
| 运行状态、实际 QoR、验证通过、计费、隐藏结果 | E | 不属于模型决策输入；保留独立记录及原有权限边界 |

Schema 中保留的兼容根字段和额外属性不自动成为新接口的可写面。
新决策 Schema 采用显式白名单：未分类字段不得默认归 M，也不得静默丢弃。
需要扩展时先记录字段责任、语义和版本，再更新接口。

## 所有权派生规则

1. 模型显式声明每个状态的 name 和 owner。owner 必须为 `top` 或已声明实例的精确名称。
2. 新决策接口不接收 `owns_state`。误发受控字段时记录输入契约错误，而不是覆盖后继续。
3. 每个实例的 `owns_state` 由其拥有的状态生成，采用 `<instance>.<state-name>` 引用。
   无状态实例生成空数组；top-owned 状态不挂到任何子实例下。
4. v1 保留当前全局状态名称唯一性要求，拒绝重名和歧义；不自动重命名或合并状态。
   未来若支持各 owner 下的局部同名状态，应单独版本化并验证全部引用/下降规则。
5. 新输入使用未限定的 state.name 与显式 owner，不同时使用两套相互矛盾的命名。
   旧 PC 的限定名称兼容读取仍由旧接口处理，不借此静默迁移历史输入。
6. 保留有语义的数组次序，包括 FSM 转移优先级和数据流顺序；只对明确的派生集合
   使用固定顺序。不能把全 PC 数组排序当作无害格式化。

以下仅演示局部派生关系，不是完整的新接口或可执行 PC：

```json
{"state":{"counters":[{"name":"count_reg","owner":"u_counter","width":8}]}}
```

程序为已声明的 `u_counter` 生成 `owns_state: ["u_counter.count_reg"]`。
若模型选择 `owner: "top"`，程序不会把它改成 `u_counter`，只会生成对应的空实例
所有权集合。架构是否正确、组件功能是否实现，仍须接受 PC/FPP 检查与独立功能验证。
不存在的 owner、重复实例或缺少必要绑定不得通过补假节点来修复。

## 决策输入与装配流程

新输入结构为 `decisions` 和 `fact_bindings` 两个部分，协议版本由请求端配置
绑定，不让模型自行选择；现已注册为 `pc-decisions-v1`。

- `decisions` 仅包含 M 字段及混合对象中的 M 叶子，结构尽量对应现有 PC 对象。
- `fact_bindings` 使用明确的对象选择和字段，程序转换为最终 JSON Pointer。
  例如选择名为 `count` 的 top port 的 `width`；如果不存在或不唯一，必须失败。
- 对复制的目标平台、验收义务等固定字段，规范指针可由程序生成，标为 host-copy
  绑定；这只证明复制一致性，不计作模型完成了结构/行为映射。
- 其余绑定由模型选择，按原 H3 要求检查位置和语义值。不能将错误的 state-width
  绑定自动换成正确的 port-width 绑定。

```text
冻结公开输入 + 模型原始回答
  → 新决策输入的解析与 Schema 检查
  → 引用唯一性、字段权限与冻结事实冲突检查
  → 按已批准规则复制 F / 合并 M / 计算 D
  → 完整 PC 的既有 H0–H3 检查
  → FPP 生成与独立评测
```

输入错误不能自动重试或扣成“程序装配成功”。是否使用一次 PC 修正由所属研究层的
既定政策决定，并单独计费。第二层冻结 PC 的 A/B/A-R/B-R 不重新生成或修改 PC。

## 记录、失败与统计

每次尝试保留公开输入哈希、原始回答哈希、决策接口版本、装配规则版本、装配后 PC
哈希（未产出则为 null）、错误路径及字段来源记录。模型调用和程序执行成本分开计账。
装配侧记录为 `pc-assembly-record-v1`，其执行来源为 `pc-assembly-execution-v1`；
不回写原始回答或覆盖历史 trajectory。

至少区分输入解析失败、输入 Schema 失败、禁止字段、冻结事实冲突、未知/歧义引用、
装配失败、H0–H3 失败及工具/服务异常。新输入阶段失败时，后续 H0–H3 为 `not_run`，
但该尝试仍留在全部输入分母中。必须报告“原始输入到最终 PC 合规”的整体结果，
不能只展示装配后 H0 的条件通过率。

host-copy/派生字段与模型决策、模型语义绑定的诊断分别报告。
所有研究条件使用相同的固定事实、装配规则版本和 H0–H3 检查器。
阶段性通过不等于硬件功能证明；本研究的合法 PC 准入也不自动成为框架的全局拒绝策略。

## 实施前验收清单

| 用例 | 必须观察到的结果 |
| --- | --- |
| 同一冻结输入与同一决策重复装配 | PC 内容哈希一致，不嵌入时间戳或方法身份 |
| 不同方法条件使用同一输入 | PC 相同，运行条件仅在侧面台账区分 |
| owner 正确 | 派生所有权正确，现有 H1 可验证 |
| owner 不存在 / 实例重名 / 状态重名 | 明确失败，不猜测、不重命名 |
| 模型发送受控字段或旧完整 PC | 拒绝并记录接口不匹配，不静默裁剪 |
| 位宽/时钟等多目标事实 | 按角色与对象绑定，不把一个值广播到所有端口/时钟 |
| 缺失语义绑定或错误绑定 | 保留失败，不补出看似正确的指针 |
| 自定义验收单位或信号大小写改变 | 不被归一化掩盖 |
| FPP、实测 QoR 或隐藏结果被塞进决策输入 | 拒绝越权字段，不产生通过状态 |
| 数组顺序含优先级或编译依赖 | 装配不改变其语义顺序 |
| 程序装配后仍不满足 H0/H1 | 保留失败，不把装配动作当成功证明 |
| 旧接口回放与新接口结果 | 分开版本、分开统计，不重标历史结果 |

当前执行授权覆盖新接口的实现、注册和离线验证；不自动迁移旧条件或历史数据。
后续 2×2 实验的操作性协议、预算和真实模型执行授权仍单独管理。
