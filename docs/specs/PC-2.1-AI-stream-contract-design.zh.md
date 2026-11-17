# SR2FPGA Project Contract 2.1
## 面向量化 AI 数据通路的张量、数值与事务契约

**日期：** 2026-09-15  
**状态：** **当前 PC 表示设计**（2026-09-15 由用户随 `paper1-v2.2` 一并采纳）。机器格式 `sr2fpga-pc-2.1` 为当前 Project Contract 序列化，取代 System-HIS v1.2 与 PC 2.0。
> **实现事实（2026-09-15 核查）：** 本稿所述“已实现的局部静态检查与 Python 语义辅助函数”**不在本仓库中**，随包的 149 项 conformance 报告也不在；`reports/conformance.json` 是 PC 2.0 的 70 项报告。采纳授予格式权威，不使这些能力成为实现事实。见 `paper1-v2.2` §21.3。  
**机器格式：** `sr2fpga-pc-2.1`。  
**直接底稿：** PC 2.0 clean-slate 设计、schema 和参考检查器 [B0–B2]。  
**研究边界：** 本稿撰写时不改变研究计划 v2.1 的核心总体；该条已被后续采纳的 `paper1-v2.2` 取代——主总体改为三个量化 AI 家族。**M0–M5、B4、主要比较、独立隐藏评测与无生成模型训练的规定继续有效。** 本稿只规定 PC 表示和静态机制；格式版本与研究版本分别管理。

> 本稿实施的是上一轮讨论的有限增量：把 AI 加速子系统中“数据代表什么、按什么顺序传、在哪个数值与事务边界转换”变成可解释的声明。它不是通用神经网络编译器，不声称解决所有跨模块语义错误。新增设计、检查和算例均是本次工作；历史文件只是依据，不能替代新实验结果。

---

## 1. 核心改动与不变项

保留 PC 2.0 的三个顶层字段 `schema_version / bindings / design`。模型只输出 `design`；受信控制器注入原始公开需求、target profile 和 capability profile 的身份及字节哈希。入口模块继续使用 `signature.source=requirement_boundary`，不能另造一份外部接口。结构模块与行为模块、有限参数 AST、点对点流连接和证据分离继续成立。[B0]

本次只增加三组设计责任：

| 位置 | 新内容 | 目的 |
|---|---|---|
| `signature.tensor_contracts` | 签名局部的命名张量契约 | 定义逻辑形状、元素编码、量化、遍历／并行 lane、事务序列 |
| `stream.payload` 的 `tensor_beat` 分支 | 通过局部名字引用契约 | 从语义推导一拍的物理类型，不维护另一份易冲突的位宽 |
| `behavioral.tensor_rules / buffer_rules` | 有限的模块输入输出关系及 FIFO 绑定 | 检查声明之间是否自洽，形成仍待独立验证的责任清单 |

**没有增加** `vision_mode / rl_mode / cnn_type` 等应用开关，没有神经网络算子模板库，没有让构建器自动插入转换器、FIFO、残差分发器或 MAC。普通 value／标量／record 流继续使用 PC 核心；不涉及张量的任务不必填写 AI 字段。

本包不读取 PC 2.0 或 System-HIS v1.2，不提供兼容 reader、自动迁移或别名。旧源文件保留；重新编写的开发样例使用新版本并重新测试，不继承旧通过信用。

## 2. 为什么增量放在接口与边界，而不是完整计算图

上一轮讨论提出三类典型任务：Depthwise→Pointwise、量化残差块、分块 GEMM。它们需要协调布局、尺度、对应位置、部分和与缓冲。

外部依据支持问题的工程意义，但不证明当前模型经常失败，也不证明本方法已有性能收益：FINN 文档说明并行度与打包布局有关 [E1]；LiteRT 量化规范说明 scale／zero-point 及 per-axis 参数的含义 [E2]；hls4ml 通过协同仿真估计 FIFO 占用 [E3]。

本版刻意不编码完整 Conv、GEMM 或每条算术指令。局部算法仍由公开任务与独立参考定义，模型负责实现。PC 只对已定义的接口关系做静态检查；无法比较的任意算法语义仍列为 deferred。

## 3. 字段组织：局部命名、一个语义来源

以下是模块签名片段，不是完整 PC：

```json
{
  "tensor_contracts": {
    "Features": {
      "shape": [
        {"axis": "N", "extent": 1},
        {"axis": "H", "extent": 2},
        {"axis": "W", "extent": 2},
        {"axis": "C", "extent": 3}
      ],
      "element": {"kind": "sint", "width": 8},
      "quantization": {
        "kind": "affine",
        "granularity": "per_tensor",
        "scale": {"numerator": 1, "denominator": 8},
        "zero_point": 0,
        "range": {"min": -128, "max": 127}
      },
      "layout": {
        "order": ["N", "H", "W", "C"],
        "lane_axis": "C",
        "lanes": 2,
        "tail": "zero_pad_mask"
      },
      "sequence": {
        "kind": "dense",
        "frame_fact": "F_FRAME",
        "reset_fact": "F_RESET"
      }
    }
  },
  "ports": {
    "x": {
      "kind": "stream",
      "direction": "input",
      "protocol": "ready_valid_v1",
      "domain": "d",
      "payload": {"kind": "tensor_beat", "contract": "Features"}
    }
  }
}
```

`Features` 只在该签名内有意义；改名并同步引用不会改变语义。同一模块内多个端口或 FIFO 可引用同一契约，不重复填写一份 type 和另一份 layout。不同模块之间比较展开后的内容，而不是要求局部名字相同。

形状与 lane 参数使用现有有限 AST，在当前模块的显式参数环境中求值。入口契约来自已绑定公开边界。只验证本次实例化配置，不因此证明整个参数域。

未引用的局部契约拒绝；引用不存在的契约也拒绝。定义的顺序和 JSON object 键顺序不应变成隐含语义。

## 4. 逻辑形状与物理传输明确分开

### 4.1 命名轴与遍历

`shape` 定义唯一命名轴及正整数 extent。轴定义的列举顺序不决定传输；检查器按命名轴规范化。`layout.order` 必须恰好是这些轴的一个排列，方向为**最慢变化→最快变化**。

本有限 profile 要求 `lane_axis == order[-1]`：一拍并行的 lane 沿最快变化轴展开。Lane 0 放在最低有效位。轴重排是数据重排，不是改一个字段名称即可完成的硬件行为。

例如，N,H,W,C 与 N,C,H,W 可以具有相同的 shape、总元素数和每拍位宽，但其传输位置对应的坐标不同。直接连线时必须拒绝这种声明不匹配；有需要时声明 `repack` 行为模块。

### 4.2 尾部与掩码

`tail=exact` 要求最快轴的长度能被 lane 数整除。

`tail=zero_pad_mask` 允许最后一拍不足一组：有效 lane 由一个与 lane 数等宽的 mask 表示；mask 位 j 对应 lane j。无效 lane 的物理 raw bits 为零、mask 为零，不能参与运算。**这不是把 raw 0 解释为量化实数零**；非零 zero-point 的无效 lane 同样由 mask 排除，per-axis 表也不为不存在的坐标提供条目。

物理布局为：低位连续存放各 lane 的元素，高位存放 mask（仅 zero_pad_mask 存在）。例如两个 INT8 lane 加两位 mask，总宽为 `2×8+2=18 bit`，不是 16 bit。

设最快轴长度为 D、lane 数为 L，其他轴大小乘积为 P，则 dense 每次完整调用的拍数为 `P×ceil(D/L)`。示例 N=1,H=W=2,C=3,L=2 得到 12 个有效元素、8 拍。拍数和 mask 按被接受的传输计数，不按时钟周期计数。

### 4.3 当前不支持的编码

本次仅处理固定实例化形状、密集张量、整齐的轴遍历及一个 lane 轴。不支持任意 stride/gather、稀疏／ragged、动态尺寸、不同调用交织、运行时乱序坐标、任意显式标签、嵌套 tensor-in-record，或直接声称 AXI Video ABI。

缺少某类能力时需明确扩展和验证，不能把它改名为普通 bits 后宣称仍有张量检查。普通网络对 tensor 与 raw payload 直接互连会拒绝；行为模块内部是否遵守语义依然需要工具验证。

## 5. 数值语义：INT8 不再是唯一信息

### 5.1 编码

`quantization.kind=integer` 表示 raw 整数本身，取值范围为元素存储类型的完整范围。

`kind=affine` 表示：

```text
real_value = (raw_code - zero_point) × scale
```

scale 采用正的最简有理数 `{numerator, denominator}`，保留 PC 的整数 JSON 编码。该选择用于可重复比较，不声称所有外部模型的尺度都能直接放入当前有界整数范围。

量化分为 per_tensor 和 per_axis。Per-axis 参数必须按**逻辑轴坐标**索引，scale 与 zero-point 数组长度各自必须等于该轴 extent，而不是物理 lane 数；校验 axis 是否存在、表长度、尺度最简性、零点与代码范围。

`range` 是有效代码范围，不是资源指标。它必须被 uint/sint 的实际存储范围包含，可表达不同模型的窄量化区间。当前 tensor element 限于不超过 32 位的 uint/sint；PC 核心的其他类型没有被重新定义。

### 5.2 重量化与加法的精确定义

`exact_affine_v1` 声明：由输入编码得到精确有理数实值，除以输出尺度，对**中心化的结果**执行一次指定舍入，然后加输出 zero-point；最后按 `saturate` 或 `error` 处理输出范围。

`exact_affine_sum_v1` 先将各输入解码、精确相加，再执行上述一次输出量化：

```text
qout = overflow(round(sum((qi - zi) × si) / sout) + zout)
```

支持的舍入为 `toward_zero / floor / nearest_even`。负数及正负半整数的行为由辅助函数和测试明确。不会把“每支路先舍入再相加”视为同一公式。

`same_scale_centered_sum` 要求所有输入和输出的元素表示、量化配置完全相同，计算 `sum(qi - z) + z` 后处理范围。非零 zero-point 不能当成简单 raw 相加。不同尺度不是非法任务，但必须使用显式的 affine-sum 或先声明 requantize。

**这些是本次 PC profile 的数学约定，不是 LiteRT 的整数 kernel 逐位实现。** 外部 kernel 可能采用不同的整数乘数、移位、中间截断和容差。[E2] 真正导入模型时要冻结其运算算法；不能根据一个 scale 自动宣称 bit-exact 兼容。本包没有实现通用模型 importer、乘数／移位选取或算术 RTL。

### 5.3 接口相等与数值转换不同

直接 net 的两端比较 shape、element、quantization、layout、sequence；不同量化配置的同位宽端口不能直连。

`requantize` 是行为关系，不是连线自动 cast。构建器不生成它的算法，不私下加 saturation 或改变 rounding。

## 6. 事务身份：坐标、调用与部分和

### 6.1 Dense 流

`sequence.kind=dense` 声明一次完整调用覆盖一个固定形状张量，按 layout 顺序传输。`frame_fact / reset_fact` 必须引用真实存在的公开 guarantee，说明调用边界及复位取消规则。

坐标和调用编号是逻辑身份，**不强制每拍携带完整硬件标签**。当前 profile 使用固定拍数和有序传输隐式定位。提供相同 fact ID 只能建立来源关联，不能证明两条 RTL 支路真的对应同一次调用。

`zip_add.pairing=same_invocation_and_coordinate` 要求按同一调用、同一逻辑坐标配对，不允许用固定经过时钟数替代。检查器能检查声明的 shape／layout／sequence 相容；实际背压下是否错位仍由独立 scoreboard 检查。

### 6.2 Partial-sum 流

`kind=partial_sum` 增加 `reduction_axis / groups / group_order`。Shape 表示输出坐标，reduction_axis 是额外的部分和组身份，不得与输出轴重名。

- `outermost`：先发完 group 0 的全部 dense 拍，再发 group 1，以此类推。
- `innermost`：对每个 dense 拍位置依次发各 group，然后进入下一个拍位置。同拍各 lane 共享 group 身份。

每次调用拍数是对应 dense 拍数乘 groups。复位后的新调用不得接续旧 partial-sum 累加状态；该行为来自公开 reset 义务，静态声明不会证明 RTL 已落实。

`reduce_sum` 要求 partial_sum 输入、dense 输出、相同输出坐标／布局／调用身份、保留数值尺度且不缩窄存储类型。Affine partial sum 必须零点为 0。声明清零在 group0 前、提交在所有组完成后、提交前禁止 requantization；累加溢出按指定 error/wrap/saturate 规则。

归约的数学目标先精确求和全部组，再处理最终溢出：error 要求最终结果可表示，saturate 对输出合法范围夹紧，wrap 仅允许完整存储范围并按输出位宽做模运算。不能提前逐组饱和或舍入；静态检查不推导所有所需中间 guard bits，实际实现必须符合冻结算法。

这可拒绝矛盾的声明或连接，不证明真实调度器真的使用了正确组号、只清零一次、最后才提交。完整计算正确性仍依赖 oracle。

## 7. 有限 tensor_rules，不是完整算子 IR

| kind | 声明关系 | 静态检查重点 | 仍需实际验证 |
|---|---|---|---|
| `identity` | 一入一出，值和顺序保持 | 两侧完整张量契约相同 | 数据保持、丢失／重复、复位 |
| `fork` | 一入多出，每路收到一次 | 每路完整契约相同 | 独立停顿、复制次数与活性 |
| `repack` | 同一逻辑张量改变遍历／lane 布局 | 除 layout 外保持逻辑／数值含义 | 正确重排、缓存和吞吐 |
| `requantize` | dense 张量改变元素数值编码 | 保持形状／布局／序列；显式 affine 算术 | 舍入、溢出及真实实现 |
| `zip_add` | 相同调用与坐标配对后相加 | 相容 shape/layout/sequence；数值模式合法 | 错拍、数值结果与死锁 |
| `reduce_sum` | 部分和组归并为最终输出 | 组与输出关系、尺度、宽度、提交顺序声明 | group 身份、状态生命周期、溢出 |
| `compute` | 任意任务定义的计算 | 端口存在、方向、域、fact 引用 | Conv/GEMM 等数学、张量映射与全部行为 |

每个行为模块的每个 tensor 端口必须恰好属于一个主关系；不能重复列同一个输入伪造双支路，也不能遗漏输出。所有规则引用公开 guarantee；它们并不拥有评测标准。

`compute` 不从模块名推导算子、不自动检查卷积公式，也不会因为叫 Depthwise 而注入 kernel。它是有意识保留的行为边界，不应在论文中计作“已证明的张量计算语义”。模型可以选择更粗的行为模块，但这不增加静态机制信用。

## 8. 缓冲只绑定可检查责任，不假装已经解决死锁

Tensor FIFO 的 `element_type` 可以引用签名局部 `tensor_beat`。`buffer_rules` 把该状态绑定到相同契约的输入与输出；状态必须是本地 FIFO、同域、完整 beat 类型相同，并明确 `capacity_unit=beats`。

深度 16 表示 16 个完整传输拍，不自动表示 16 个像素、字节或张量。实际占用、初始化、满空同时事件和复位仍沿用 PC 核心的声明责任，并需实际验证。

**本版没有以 latency、II 或张量大小推算“最小安全 FIFO 深度”。** 生产消费调度、分发策略和环境停顿都会影响活性；hls4ml 的相关工作用仿真分析占用 [E3]。无有界服务条件时不能承诺无条件实时或有限缓存零丢失。

测试刻意包含把旁路深度改为 1 仍静态通过的用例，报告继续列出 `startup_and_steady_state_liveness: not_evaluated` 的待验证责任。这说明检查范围，不是该配置已经安全。

完整双缓冲所有权、DMA completion、最末读取与 bank 交接本次不增加一套空泛事件语言；若进入下一阶段，需先冻结实际接口事件和验证规则。部分和生命周期已按上节落实有限声明。

## 9. 检查结果与实际证据分开

检查器依次处理现有 schema／绑定／引用／参数／域检查，以及本次 tensor descriptor 与关系检查。报告仍使用 `schema_and_listed_static_checks_only`，不写 `project_pass` 或 `vpp_l3`。

新增输出包括每个实例端口的已解析类型、派生位宽／拍数，以及 `verification_obligations`。后者所有条目都标为 `not_evaluated`，列出实际布局、接受次数、背压保持、配对、算术、partial-sum 和缓冲活性等待验证内容。

**这份清单不是自动生成的独立 oracle。** 公共 checker 可以用它辅助定位；最终评测规则与期望输出必须从冻结的公开任务及评测域建立，不能读取模型的 `compute` 意图后修改判题。候选删除／弱化关系也不能删除公开任务的义务。

本包能发现“生产者声明 HWC、消费者声明 CHW”，但不能发现“双方都声明 HWC，实际某个 RTL 发 CHW”。同理，双方把错误尺度抄成相同值可能逃过接口比较；对外边界绑定和独立位精确参考才负责实际任务正确性。

## 10. 本次三个示例的准确身份

| 示例 | 本次展示 | 没有交付／没有证明 |
|---|---|---|
| `depthwise_pointwise` | Depthwise、显式 Reorder、Pointwise；输出 per-axis 量化 | 卷积 RTL、完整 kernel／舍入任务卡、独立 oracle、推理效果 |
| `quantized_residual` | 显式 fork、两段主支路、tensor FIFO、异尺度 zip_add、激活 | 主支路权重与完整数值任务卡、无死锁、正确推理、物理性能 |
| `tiled_gemm` | 4×6 与 6×4；三组部分和、INT32 累加、最终 /8 重量化 | RTL、真实数据装载、buffer bank 实现、综合及完整任务资格 |

这些是人工构造的表示与检查开发示例，不是模型生成、不是正式 held-out 样本，也不是三个已经实现的 AI 加速器。前两个示例明确保留需要最终冻结的算子／权重语义；第三个虽给出小规模数学定义，也没有对应硬件或 oracle 资格证据。

下一步优先用较小的 Depthwise→Pointwise 任务完成实际闭环；残差块作为事务／数值组合重点；GEMM 保留为数值状态案例。是否纳入论文仍在结果前另行确定，不把三个新名字直接加进原核心总体。

## 11. 代码与工具交付

| 文件 | 责任 |
|---|---|
| `tools/build_schema.py` | 同源生成完整 PC 与模型输出两份 schema |
| `tools/validate_pc.py` | PC 核心与 tensor 检查的统一入口；真实字节绑定、受控展开 |
| `tools/tensor_semantics.py` | descriptor 求解、边界匹配、有限关系／FIFO 绑定检查 |
| `tools/tensor_reference.py` | 精确有理数舍入／重量化／加法、有限坐标拍序列辅助函数 |
| `tools/build_ai_examples.py` | 构造说明性公开输入和 PC，不是运行时家族生成器 |
| `tools/build_counterexamples.py` | 保存人工错误声明与实际静态结果 |
| `tools/run_tests.py` | 运行当前测试并写报告及受测源码哈希 |

语义辅助函数不生成 RTL，也没有通过真实 HDL 波形验证。测试中用其计算正确与错误表达式的差异，只证明局部 Python 语义，不证明加速器。

完整 schema 和模型投影是格式规则；`examples/*.pc.json` 才是具体 PC；`reports/conformance.json` 是测试报告。不能把三类 JSON 混为一谈。

## 12. 实验公平与集成边界

公开 tensor shape、模型参数、数值／时间规则、ABI 和输入域对所有方法等价提供。M0/M1 不必输出 PC，但仍知道同样的任务；M3/M4 共享生成 PC 与同样的静态检查，M3 不消费 M4 的构建源码。额外检查不会成为对照分支必须拥有 PC 的共同准入条件。

没有自动启用结构化解码、增加模型调用、调整主要对照或开放隐藏数据。B4 仍按原方法解释；多个行为模块不因此得到多次免费首发调用。

AI 检查诊断不代表已有修复效果。人工变异只用于检验检查器；自然 Agent 错误频率和收益必须通过独立真实实验获得。当前样例、counterexamples 及工具脚本不能进入正式模型提示或冒充未见任务。

## 13. 本次实际测试范围

合并报告记录 **149 项本地测试，0 失败、0 错误、0 跳过**。包括按新版本重建并重新运行的 70 项核心测试，以及 79 项 tensor／关系／辅助函数测试。实际环境和逐项结果见 `reports/conformance.json`；本句与随包受测版本绑定，不代表后续修改仍自动通过。

覆盖包括同位宽错布局、错尺度、量化表长度与零点、尾部掩码、部分和组顺序、提前提交声明、tensor 编码擦除、FIFO 条目类型、未覆盖关系、root 绑定、profile 限额、负数舍入、各 INT8 code 的重定标和待验证标记。

七个选定说明性反例另见 `reports/mismatch_examples.json`，其中六个按预期拒绝、一个低容量 FIFO 仅获得静态接受且保留活性待验证。

**未执行：** 模型/API、RTL emitter、AST 保护、RTL 仿真、综合、布局布线、实际图像／权重加载、板级运行、死锁证明、运行时沙箱或正式 hidden campaign。Schema 和 checker 的 pass 均不等于这些能力。

## 14. 下一步实施顺序与限制

先把真实 Requirement Envelope 的边界接入本格式，固定一份完整小型任务卡和独立整数参考；不要把示例适配器当成新的仓库需求权威。随后实现 tensor beat 的 deterministic ABI／mask 展开，更新 unit/cache 身份包含量化、遍历、lane、组顺序和规则版本，拒绝复用已不匹配的行为结果。

保持转换、fork、FIFO、算术为模型行为，不调用示例 builder 当运行时答案库。先验证结构和 parser/AST 保护，再做真实生成与受预算修复。对布局与配对错误使用定向不对称数据、停顿、复位和连续调用；对部分和检查多 K 组及清零／提交时刻；这些测试从冻结任务产生，而不是候选自己的通过条件。

本包仍是参考原型：只保证列明输入域及规则的局部测试，不是生产级输入攻击面审计。任意自然语言义务、算子数学、所有参数配置、任意量化 kernel、平台资源和活性没有普适证明。

---

## 来源与版本身份

[B0] `PC-2.0-clean-slate-design.zh.md`：继承职责分离、有限接口、有限静态保证和无旧兼容政策。  
[B1] 用户会话交付的两份 PC 2.0 schema 与 `SR2FPGA-PC-2.0-clean-slate.zip`：本次代码编辑底稿。原文件哈希见 `provenance.json`。  
[B2] `2026-09-14-sr2fpga-paper1-code-architecture-development-spec-v2.0.zh.md`：保留批量行为、M0–M5、B4、共享和评测权限；本次没有直接修改该文档。  
[B3] `2026-09-14-sr2fpga-paper1-research-plan-v2.1.zh.md`：应用义务与结果分开、有限案例与正式总体分开；本次没有直接修改该文档。

[E1] FINN 官方 FAQ，数据打包与并行度相关内容。2026-09-15 查阅。`https://finn.readthedocs.io/en/latest/faq.html`  
[E2] Google LiteRT，8-bit quantization specification，2026-09-15 查阅；页面显示更新于 2026-05-28。只用作 affine/per-axis 量化依据，不作为本包逐位实现兼容证据。`https://developers.google.com/edge/litert/conversion/tensorflow/quantization/quantization_spec`  
[E3] hls4ml 官方 FIFO Buffer Depth Optimization 文档，2026-09-15 查阅。只说明容量与行为需实际分析，不构成本包的死锁证明。`https://fastmachinelearning.org/hls4ml/advanced/fifo_depth.html`

外部资料提供问题背景；本次字段组织、profile、静态规则和算例是新增设计。来源身份不等于实际工具已安装，也不授予任何 SR2FPGA 研究结果。
