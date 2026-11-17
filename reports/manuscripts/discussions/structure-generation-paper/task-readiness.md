# P01 候选任务与静态就绪表

日期：2026-10-21。本表服务于[已选旧版 M3/M4 初始生成范围](../2026-10-21-structure-generation-paper-checklist.zh.md)，不是实验任务清单冻结、运行许可、模型输入或论文正文。候选按多文件责任、接口/握手复杂度及参考可恢复性提出，没有按旧模型通过结果筛选。

**P01 只确认文件存在、源码分支和静态接口匹配；九个候选全部尚未获得本篇 P04 可执行资格。** 本轮没有 import 执行生成器、重跑测试/HDL 工具、运行 oracle、调用模型或新建实验。PC 2.1 迁移不是本篇沿用 System-HIS 旧版实现的前置要求；本表不改变现行 paper1-v2.2。

## 选取与身份

| 编号/用途 | 讨论显示名 | 准确 runtime task_type | family_id | 历史原件配置 | 本篇运行资格 |
| --- | --- | --- | --- | --- | --- |
| D01 调试 | 多文件事件计数 | composed_event_counter | t1_event_counter | width 8，3 RTL 文件 | 未资格，P04 未运行 |
| D02 调试 | 带反压流式累加 | composed_stream_accumulator | valid_ready_stream_accumulator | width 8，3 RTL 文件 | 未资格，P04 未运行 |
| D03 调试 | 帧内峰值选择 | peak_detector | peak_detector | width 8，2 RTL 文件 | 未资格，P04 未运行 |
| M01 主候选 | 三抽头 FIR | fir_filter | fir_filter | width 8，3 RTL 文件 | 未资格，P04 未运行 |
| M02 主候选 | 固定 ROM 四元素点积 | matrix_vector_mac | matrix_vector_mac | width 8，4 RTL 文件 | 未资格，P04 未运行 |
| M03 主候选 | 有符号匹配滤波 | matched_filter | matched_filter | width 8，3 RTL 文件 | 未资格，P04 未运行 |
| M04 主候选 | 相关—阈值—帧峰值流水 | pulse_radar_signal | p_pulse_radar_signal | width 8，5 RTL 文件 | 未资格，P04 未运行 |
| M05 主候选 | 定点 TD 更新流水 | composed_td_update_core | qtable_update_core | width 8，5 RTL 文件 | 未资格，P04 未运行 |
| M06 主候选 | 可配置策略/值更新子系统 | composed_rl_accelerator_shell | p_rl_qlearning_accel | width 8，6 RTL 文件 | 未资格，P04 未运行 |

映射事实来自 [stream](../../../../agent/src/sr2fpga_agent/task_families/stream.py)、[datapath](../../../../agent/src/sr2fpga_agent/task_families/datapath.py)、[rl](../../../../agent/src/sr2fpga_agent/task_families/rl.py)的 TASK_FAMILY_IDS，以及各旧样例 metadata。t1/t2/t6/t10 等目录别名不是可以直接替代 runtime task_type 的承诺。尤其：

- mac_array 在旧 [ProjectGenerator alias](../../../../agent/src/sr2fpga_agent/task_families/__init__.py)映射为 matrix_vector_mac，不能混入 composed_vector_mac_pipeline 的独立模板语义。
- p_rl_qlearning_accel 同时收 T10 与 T11；现有 Python oracle 与本表选择的是 T10/composed_rl_accelerator_shell 的端口及操作格式，不给 batch 变体继承资格。
- qtable_update_core 是历史 family 名；实际选择为无 Q 表存储的有符号 TD tuple 更新流水。M06 也只是声明范围内的算术/控制子系统，不代表完整强化学习训练、策略质量或任务性能。

## 每任务原件、责任与缺口

下述需求/RTL/ABI 路径属于内部审计与 evaluator 参考资产索引，不应整体拷贝到候选模型上下文。M01–M06、D03 的 oracle 文件夹均只有 manifest/evidence，原始 .memh 缺失；本文不抄录非公开向量、seed、期望值或参考实现。source/licence 状态统一为“仓库内模板/旧归档，权利归属未完成核实”，详见[公开范围](release-scope.md)。

### D01 多文件事件计数

- 输入与原件：[requirement.txt](../../../../datasets/sr2fpga_rtl_v1/sample_t0_t4_deterministic_smoke_t1_event_counter_8_000013/requirement.txt)、[metadata](../../../../datasets/sr2fpga_rtl_v1/sample_t0_t4_deterministic_smoke_t1_event_counter_8_000013/metadata.json)、[RTL](../../../../datasets/sr2fpga_rtl_v1/sample_t0_t4_deterministic_smoke_t1_event_counter_8_000013/attempts/attempt_000/generated_project/rtl)、[TB](../../../../datasets/sr2fpga_rtl_v1/sample_t0_t4_deterministic_smoke_t1_event_counter_8_000013/attempts/attempt_000/generated_project/sim/tb_top.v)。metadata 标 deterministic；不能自动绑定到另一个同名重组 summary run。
- 结构责任：top 接线；event_gate 处理事件；counter_core 保存计数/复位。没有复杂流式背压，适合先检查多文件、接口与状态所有权。
- 参数/参考：现有 width 8；embedded-SV TB，非独立 Python oracle；没有本表可引用的 .memh bundle。旧工具日志是恢复线索，不是本篇资格。
- 生成/骨架：旧 stream 模板有明确生成函数；旧骨架可描述 top 级两实例，但需重核共享契约、声明和实际行为洞边界。后续可信 harness 必须单独拥有，不以模型输出 TB 自评。
- 待补/结论：固定计数溢出、复位、事件采样语义及可信用例；仅作调试候选，当前不可声称本篇可执行。

### D02 带反压流式累加

- 输入与原件：[requirement.txt](../../../../datasets/sr2fpga_phase_d_control_v1/sample_phase_d_control_t2_stream_accumulator_8_000002/requirement.txt)、[metadata](../../../../datasets/sr2fpga_phase_d_control_v1/sample_phase_d_control_t2_stream_accumulator_8_000002/metadata.json)、[RTL](../../../../datasets/sr2fpga_phase_d_control_v1/sample_phase_d_control_t2_stream_accumulator_8_000002/attempts/attempt_000/generated_project/rtl)、[TB](../../../../datasets/sr2fpga_phase_d_control_v1/sample_phase_d_control_t2_stream_accumulator_8_000002/attempts/attempt_000/generated_project/sim/tb_top.v)。来源为确定性控制，不能混进 Phase D 模型分母。
- 结构责任：top 连接 skid_buffer 与 accumulator_core；输入缓存、接受条件、累加状态及输出阻塞保持分属不同模块。旧累加器修订增加 accum_ready；不得混用不含此端口的早期样例/TB。
- 参数/参考：width 8；embedded-SV 参考与该控制样例的变异原件；无独立 Python bundle。需固定累加宽度、复位与 valid/ready 时序。
- 生成/骨架：旧模板与对应 System-HIS 结构存在；通用连线推断与显式握手边需重核，不能以模板函数存在判定可运行。
- 待补/结论：恢复精确同修订参考和可信反压检查；用作流控调试，不计主研究 oracle 数。

### D03 帧内峰值选择

- 输入与原件：[requirement.txt](../../../../reports/evidence/legacy-runs/phase-c-independent-oracle-20260716-v2/dataset/sample_phase_c_independent_oracle_v2_peak_detector_8_000004/requirement.txt)、[RTL](../../../../reports/evidence/legacy-runs/phase-c-independent-oracle-20260716-v2/dataset/sample_phase_c_independent_oracle_v2_peak_detector_8_000004/attempts/attempt_000/generated_project/rtl)、[oracle manifest/evidence](../../../../reports/evidence/legacy-runs/phase-c-independent-oracle-20260716-v2/dataset/sample_phase_c_independent_oracle_v2_peak_detector_8_000004/attempts/attempt_000/eval/oracle)。
- 结构责任：top 只包裹 peak_detector_core；core 处理 in_last、帧内最大值、首次最大值 tie、空结果及输出保持。
- 参数/参考 ABI：width 8；记录输入 12 bit（sample、in_last、reset_before、stall_cycles），期望记录 18 bit；顶层 in_sample/in_last/in_valid/in_ready 与 peak_found/value/index、out_valid/out_ready 对应。
- 生成/骨架：模板 [datapath.py](../../../../agent/src/sr2fpga_agent/task_families/datapath.py)，oracle [signal.py](../../../../agent/src/sr2fpga_agent/oracles/signal.py)有对应 builder；静态端口/记录一致。top＋单core可先调通 oracle 隔离。
- 待补/结论：重建受信向量、核对 reset/stall/tie，再真实执行 P04；复杂度低，留在调试域。

### M01 三抽头 FIR

- 输入与原件：[requirement.txt](../../../../reports/evidence/legacy-runs/phase-c-independent-oracle-20260716-v2/dataset/sample_phase_c_independent_oracle_v2_fir_filter_8_000001/requirement.txt)、[RTL](../../../../reports/evidence/legacy-runs/phase-c-independent-oracle-20260716-v2/dataset/sample_phase_c_independent_oracle_v2_fir_filter_8_000001/attempts/attempt_000/generated_project/rtl)、[oracle](../../../../reports/evidence/legacy-runs/phase-c-independent-oracle-20260716-v2/dataset/sample_phase_c_independent_oracle_v2_fir_filter_8_000001/attempts/attempt_000/eval/oracle)。
- 结构责任：top→fir_filter_core→mac_unit；core 的输入历史、接受/复位与结果阻塞保持，MAC 的有符号算术，应明确区分结构与行为。
- 参数/参考 ABI：width 8、三抽头固定系数配置；结果 width+3=11。输入记录 11 bit，期望记录 12 bit 含 expect_output；sample_valid/sample_ready 与 result_valid/result_ready 构成两侧握手。当前 oracle builder 只有 width 参数，不能直接假设任意系数/抽头数已支持。
- 生成/骨架：模板和 [numeric oracle](../../../../agent/src/sr2fpga_agent/oracles/numeric.py)存在且字段静态匹配；旧骨架只保证 top 级实例，内层 MAC 实例责任待定。
- 待补/结论：明确完整层次由谁生成、公开数学事实与数值截断配置；恢复向量并运行 P04。**静态 ABI 可匹配，骨架支持未完成运行核实。**

### M02 固定 ROM 四元素点积

- 输入与原件：[requirement.txt](../../../../reports/evidence/legacy-runs/phase-c-independent-oracle-20260716-v2/dataset/sample_phase_c_independent_oracle_v2_matrix_vector_mac_8_000002/requirement.txt)、[RTL](../../../../reports/evidence/legacy-runs/phase-c-independent-oracle-20260716-v2/dataset/sample_phase_c_independent_oracle_v2_matrix_vector_mac_8_000002/attempts/attempt_000/generated_project/rtl)、[oracle](../../../../reports/evidence/legacy-runs/phase-c-independent-oracle-20260716-v2/dataset/sample_phase_c_independent_oracle_v2_matrix_vector_mac_8_000002/attempts/attempt_000/eval/oracle)。
- 结构责任：top→dot_product_engine，engine 内有 vector_rom/mac_unit；样本分组/ROM索引/累加状态/每四接受样本输出和反压是实质接口义务。
- 参数/参考 ABI：width 8、固定四系数 ROM；结果 width+4=12。输入 11 bit，期望 13 bit 含 expect_output；外部端口与 FIR 名称相同，输出节奏不同。固定点积不是通用矩阵乘、神经网络或 GEMM。
- 生成/骨架：旧模板和 numeric builder 静态匹配；骨架对 ROM/MAC 内层实例没有完整确定性构建保证。
- 待补/结论：声明 ROM 资产与模型可见范围、分组边界/复位/阻塞；不能把更换权重或宽度当现成已支持的新配置。当前只有静态匹配。

### M03 有符号匹配滤波

- 输入与原件：[requirement.txt](../../../../reports/evidence/legacy-runs/phase-c-independent-oracle-20260716-v2/dataset/sample_phase_c_independent_oracle_v2_matched_filter_8_000003/requirement.txt)、[RTL](../../../../reports/evidence/legacy-runs/phase-c-independent-oracle-20260716-v2/dataset/sample_phase_c_independent_oracle_v2_matched_filter_8_000003/attempts/attempt_000/generated_project/rtl)、[oracle](../../../../reports/evidence/legacy-runs/phase-c-independent-oracle-20260716-v2/dataset/sample_phase_c_independent_oracle_v2_matched_filter_8_000003/attempts/attempt_000/eval/oracle)。
- 结构责任：top→matched_filter_core→matched_filter_mac；有符号历史序列、相关和、输出背压；与 FIR 共享滑窗机制但数学与位宽不同。
- 参数/参考 ABI：width 8、固定四tap模板，结果 2×width+2=18；记录输入 11 bit，期望 18 bit。顶层 in_sample/in_valid/in_ready 与 correlation/out_valid/out_ready。
- 生成/骨架：datapath 模板与 signal builder 字段静态匹配；内层 MAC 层次、模板常数作为公开事实及结构责任待定。
- 待补/结论：向量恢复和真实参考执行；与 M04 有代码/算法谱系，不按独立未知任务随意跨 split。

### M04 相关—阈值—帧峰值流水

- 输入与原件：[requirement.txt](../../../../reports/evidence/legacy-runs/phase-c-independent-oracle-20260716-v2/dataset/sample_phase_c_independent_oracle_v2_pulse_radar_signal_8_000005/requirement.txt)、[RTL](../../../../reports/evidence/legacy-runs/phase-c-independent-oracle-20260716-v2/dataset/sample_phase_c_independent_oracle_v2_pulse_radar_signal_8_000005/attempts/attempt_000/generated_project/rtl)、[oracle](../../../../reports/evidence/legacy-runs/phase-c-independent-oracle-20260716-v2/dataset/sample_phase_c_independent_oracle_v2_pulse_radar_signal_8_000005/attempts/attempt_000/eval/oracle)。
- 结构责任：top 下 matched_filter_core→threshold_comparator→peak_detector_core，filter 内含 MAC；各级 valid/ready、in_last/out_last、相关宽度、阈值与峰值索引必须一致。
- 参数/参考 ABI：width 8、固定相关/阈值配置、相关和 18 bit；输入记录 12 bit，期望 38 bit，peak_value/index 均 18 bit。不是完整雷达系统性能任务。
- 生成/骨架：旧 generator 有专用 pulse_radar_data_flow，datapath TB 与 signal builder 静态匹配；顶层显式握手与内部 MAC 责任待核实。
- 待补/结论：恢复帧式参考与跨级阻塞/帧末监视；不能用 matched-filter 单独通过信用替代整条流水资格。

### M05 定点 TD 更新流水

- 输入与原件：[requirement.txt](../../../../reports/evidence/legacy-runs/phase-c-independent-oracle-20260716-v2/dataset/sample_phase_c_independent_oracle_v2_t6_td_update_core_8_000008/requirement.txt)、[RTL](../../../../reports/evidence/legacy-runs/phase-c-independent-oracle-20260716-v2/dataset/sample_phase_c_independent_oracle_v2_t6_td_update_core_8_000008/attempts/attempt_000/generated_project/rtl)、[oracle](../../../../reports/evidence/legacy-runs/phase-c-independent-oracle-20260716-v2/dataset/sample_phase_c_independent_oracle_v2_t6_td_update_core_8_000008/attempts/attempt_000/eval/oracle)。
- 结构责任：top 下 td_input_stage→discount_core→td_update_core→stream_stage；value/alpha 旁带与主流水对齐，更新结果保持，有符号扩展/截断与参数 SCALE_SHIFT 传递。
- 参数/参考 ABI：width 8、Q4移位、有符号TD和饱和；输入tuple记录 43 bit，输出 td_error/updated_value 合计 16 bit；gamma/alpha 为无符号。没有实际 Q-table 存储。
- 生成/骨架：rl 模板、rl oracle TD builder 与既有骨架定向测试存在；定向测试文件存在不等于本轮运行通过，也不替代统一功能资格。
- 待补/结论：固定算术中间宽度、饱和顺序与旁带握手；避免与 M06 的不同 TD 算法/同名模块混用；静态接口匹配。

### M06 可配置策略/值更新子系统

- 输入与原件：[requirement.txt](../../../../reports/evidence/legacy-runs/phase-c-independent-oracle-20260716-v2/dataset/sample_phase_c_independent_oracle_v2_t10_rl_accelerator_shell_8_000009/requirement.txt)、[RTL](../../../../reports/evidence/legacy-runs/phase-c-independent-oracle-20260716-v2/dataset/sample_phase_c_independent_oracle_v2_t10_rl_accelerator_shell_8_000009/attempts/attempt_000/generated_project/rtl)、[oracle](../../../../reports/evidence/legacy-runs/phase-c-independent-oracle-20260716-v2/dataset/sample_phase_c_independent_oracle_v2_t10_rl_accelerator_shell_8_000009/attempts/attempt_000/eval/oracle)。
- 结构责任：top 下 host_config_bank、sample_capture_stage、policy_value_core、td_update_core、result_stream_stage；配置通道、样本接受、enable、结果阻塞保持及 sticky IRQ。top 参考以接线为主，不含图像任务那类完整边界flush控制。
- 参数/参考 ABI：width 8；配置地址 3 bit；输入操作记录 48 bit（reset/config/sample及stall），期望 20 bit；cfg/sample/result各通道必须匹配。其score饱和、负误差钳零、更新回绕与 M05 饱和TD规则不同，不能因同名td_update_core合并。
- 生成/骨架：T10 模板和 rl builder 的静态端口/字段一致；部分模块没有标准ready/valid对，旧自动companion推断与显式控制责任需专门核查。
- 待补/结论：只接T10，核对配置时序、disable与IRQ复位；不包含T11 batch/replay接口，不声称强化学习性能改善。

## 骨架与任务资格的共同缺口

1. [旧 contract_skeleton](../../../../agent/src/sr2fpga_agent/contract_skeleton.py)明确以 System-HIS v1.2 为输入；_top_module 只输出顶层连线/实例，_component_module 输出端口与 BEHAVIOR_HOLE。内层 MAC/ROM 实例可能仍由模型生成，不能称整个层次已经确定性构建。P02 应按模块明确处理变量，P03 再按已授权范围修实现。
2. 旧骨架 _testbench 会调用 ProjectGenerator 的任务族 TB；这是本篇待处理的 M4 信息混杂，不能作为可用捷径。两条件共同公开事实、模型可见代码和 evaluator 受信TB应在 P02/P03 分开处理。
3. 现有 [ProjectGenerator](../../../../agent/src/sr2fpga_agent/project_generator.py)包含上述分支，[oracle registry](../../../../agent/src/sr2fpga_agent/oracles/__init__.py)包含七个涉及的Python builder，但没有本轮执行证明入口、依赖、System-HIS检查、骨架和评估器链路兼容。历史命令不直接复制为当前命令。
4. .memh 缺失必须在 evaluator-owned 范围重建。不能把旧hidden向量/seed或参考代码放入模型可见资料，也不能因旧manifest可读就声称bundle可运行。若无法恢复旧承诺，建新修订并保留旧产物。
5. 初始建议只复用已有 width-8 数学与ABI范围。builder大多只有width参数，其他常数硬编码；改变tap、系数、ROM、阈值、规模或数值语义需要显式任务/参考适配。随机种子或输入向量变化不是新的设计簇。
6. M03/M04共享滤波代码/机制，M05/M06共享算术/控制概念但数学不同；FIR与点积也共享MAC概念。要记录设计谱系和分层，而非把六模板视为六个统计独立大领域。

## 暂不优先的两个独立oracle家族

[Sobel/vision 模板](../../../../agent/src/sr2fpga_agent/task_families/image.py)与[图像 oracle](../../../../agent/src/sr2fpga_agent/oracles/image.py)均有真实资产，但当前参考 top 包含行列计数、边界flush、帧尾/背压行为，旧骨架top没有行为洞，会遗漏必要功能。两者不是“有builder即可以直接接M4”。oracle还固定8-bit、5×5、既有阈值配置，不等价于任意图像管线。

若本篇范围排除 M05/M06，可考虑用 Sobel/vision 替换，但应先预算顶层行为单元与结构责任适配；不能依据旧模型结果决定替换，也不能当作已就绪候选。最终六项及参数仍由 P02/P04 收敛，本文不冻结实验或样本规模。
