# agent-task_families：文件、符号与调用表达式

[返回全量索引](README.md)。下列调用是源文本中的语法调用；同名对象或运行分支可能改变实际目标。

## `agent/src/sr2fpga_agent/task_families/__init__.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/task_families/__init__.py) · 27 行 · SHA-256 `9d7d216ddc4545d554cede60483c791e744f875f72a262bbee3318e01755898a`

> Task-family metadata used by the deterministic project generator.

导入模块：`sr2fpga_agent.task_families`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `canonical_task_type` — `canonical_task_type(task_type)` | function / [20](../../../../agent/src/sr2fpga_agent/task_families/__init__.py#L20) | `TASK_TYPE_ALIASES.get` |
| `family_id_for_task_type` — `family_id_for_task_type(task_type)` | function / [25](../../../../agent/src/sr2fpga_agent/task_families/__init__.py#L25) | `canonical_task_type` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`TASK_FAMILY_IDS.values`、`frozenset`、`module.TASK_FAMILY_IDS.items`、`set`

## `agent/src/sr2fpga_agent/task_families/basic.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/task_families/basic.py) · 322 行 · SHA-256 `0baa7a616574c452e1d90740500f1f25ff96dc1acd2eca47ea2b4fde33bfc8d2`

> Stable family metadata for basic deterministic generator tasks.

导入模块：`textwrap`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `counter_rtl` — `counter_rtl(width)` | function / [12](../../../../agent/src/sr2fpga_agent/task_families/basic.py#L12) | `dedent` |
| `counter_testbench` — `counter_testbench(width)` | function / [36](../../../../agent/src/sr2fpga_agent/task_families/basic.py#L36) | `dedent` |
| `simple_fsm_rtl` — `simple_fsm_rtl(width)` | function / [85](../../../../agent/src/sr2fpga_agent/task_families/basic.py#L85) | `dedent`、`max` |
| `simple_fsm_testbench` — `simple_fsm_testbench(width)` | function / [142](../../../../agent/src/sr2fpga_agent/task_families/basic.py#L142) | `dedent`、`max` |
| `ram_read_write_rtl` — `ram_read_write_rtl(width)` | function / [197](../../../../agent/src/sr2fpga_agent/task_families/basic.py#L197) | `dedent` |
| `ram_read_write_testbench` — `ram_read_write_testbench(width)` | function / [232](../../../../agent/src/sr2fpga_agent/task_families/basic.py#L232) | `dedent` |

## `agent/src/sr2fpga_agent/task_families/datapath.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/task_families/datapath.py) · 2983 行 · SHA-256 `7a4d380dfb2150d72e08cd2de429b7660aea2dae81a38d927d17b9f1a60e6cbd`

> Stable family metadata for datapath generator tasks.

导入模块：`textwrap`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `matched_filter_testbench` — `matched_filter_testbench(width)` | function / [17](../../../../agent/src/sr2fpga_agent/task_families/datapath.py#L17) | `dedent` |
| `matched_filter_rtl_files` — `matched_filter_rtl_files(width)` | function / [242](../../../../agent/src/sr2fpga_agent/task_families/datapath.py#L242) | `dedent` |
| `peak_detector_testbench` — `peak_detector_testbench(width)` | function / [378](../../../../agent/src/sr2fpga_agent/task_families/datapath.py#L378) | `dedent` |
| `peak_detector_rtl_files` — `peak_detector_rtl_files(width)` | function / [671](../../../../agent/src/sr2fpga_agent/task_families/datapath.py#L671) | `dedent` |
| `pulse_radar_signal_testbench` — `pulse_radar_signal_testbench(width)` | function / [785](../../../../agent/src/sr2fpga_agent/task_families/datapath.py#L785) | `dedent` |
| `pulse_radar_signal_rtl_files` — `pulse_radar_signal_rtl_files(width)` | function / [1083](../../../../agent/src/sr2fpga_agent/task_families/datapath.py#L1083) | `dedent`、`matched_filter_rtl_files`、`peak_detector_rtl_files`、`rtl_files.pop`、`rtl_files.update` |
| `pwm_controller_testbench` — `pwm_controller_testbench(width)` | function / [1203](../../../../agent/src/sr2fpga_agent/task_families/datapath.py#L1203) | `dedent`、`max` |
| `composed_vector_mac_pipeline_testbench` — `composed_vector_mac_pipeline_testbench(width)` | function / [1264](../../../../agent/src/sr2fpga_agent/task_families/datapath.py#L1264) | `dedent` |
| `pwm_controller_rtl_files` — `pwm_controller_rtl_files(width)` | function / [1397](../../../../agent/src/sr2fpga_agent/task_families/datapath.py#L1397) | `dedent` |
| `composed_vector_mac_pipeline_rtl_files` — `composed_vector_mac_pipeline_rtl_files(width)` | function / [1472](../../../../agent/src/sr2fpga_agent/task_families/datapath.py#L1472) | `dedent` |
| `fir_filter_testbench` — `fir_filter_testbench(width)` | function / [1700](../../../../agent/src/sr2fpga_agent/task_families/datapath.py#L1700) | `dedent` |
| `matrix_vector_mac_testbench` — `matrix_vector_mac_testbench(width)` | function / [1918](../../../../agent/src/sr2fpga_agent/task_families/datapath.py#L1918) | `dedent` |
| `fir_filter_rtl_files` — `fir_filter_rtl_files(width)` | function / [2159](../../../../agent/src/sr2fpga_agent/task_families/datapath.py#L2159) | `dedent` |
| `matrix_vector_mac_rtl_files` — `matrix_vector_mac_rtl_files(width)` | function / [2297](../../../../agent/src/sr2fpga_agent/task_families/datapath.py#L2297) | `dedent` |
| `alu_control_unit_testbench` — `alu_control_unit_testbench(width)` | function / [2442](../../../../agent/src/sr2fpga_agent/task_families/datapath.py#L2442) | `dedent` |
| `crc_stream_checker_testbench` — `crc_stream_checker_testbench(width)` | function / [2554](../../../../agent/src/sr2fpga_agent/task_families/datapath.py#L2554) | `dedent` |
| `alu_control_unit_rtl_files` — `alu_control_unit_rtl_files(width)` | function / [2659](../../../../agent/src/sr2fpga_agent/task_families/datapath.py#L2659) | `dedent`、`min` |
| `crc_stream_checker_rtl_files` — `crc_stream_checker_rtl_files(width)` | function / [2818](../../../../agent/src/sr2fpga_agent/task_families/datapath.py#L2818) | `dedent` |

## `agent/src/sr2fpga_agent/task_families/ga.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/task_families/ga.py) · 3 行 · SHA-256 `37597196f9e81059fb7bf3ccbfe8afd449e12ffd1b159bcd99981568cf2dd829`

> Reserved metadata owner for future genetic-algorithm generator task families.

导入模块：无显式 import

无命名类/函数定义；检查模块级代码和导出符号。

## `agent/src/sr2fpga_agent/task_families/image.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/task_families/image.py) · 1429 行 · SHA-256 `7401ff12ba3f7fcb7ddadb55d011f731a466300b251d64799e14e21630b6d50a`

> Deterministic streaming image task-family generators.

导入模块：`textwrap`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `sobel_threshold_rtl_files` — `sobel_threshold_rtl_files(_width)` | function / [12](../../../../agent/src/sr2fpga_agent/task_families/image.py#L12) | `dedent` |
| `sobel_threshold_testbench` — `sobel_threshold_testbench()` | function / [305](../../../../agent/src/sr2fpga_agent/task_families/image.py#L305) | `_add_image_oracle_mode`、`dedent` |
| `vision_defect_core_rtl_files` — `vision_defect_core_rtl_files(_width)` | function / [608](../../../../agent/src/sr2fpga_agent/task_families/image.py#L608) | `dedent`、`rtl_files.pop`、`rtl_files.update`、`sobel_threshold_rtl_files` |
| `vision_defect_core_testbench` — `vision_defect_core_testbench()` | function / [886](../../../../agent/src/sr2fpga_agent/task_families/image.py#L886) | `_add_image_oracle_mode`、`dedent` |
| `_add_image_oracle_mode` — `_add_image_oracle_mode(testbench, vision)` | function / [1145](../../../../agent/src/sr2fpga_agent/task_families/image.py#L1145) | `_insert_after_once`、`_insert_before_once`、`_oracle_driver_task`、`_replace_once`、`_sobel_oracle_monitor`、`_vision_oracle_monitor`、`dedent` |
| `_sobel_oracle_monitor` — `_sobel_oracle_monitor()` | function / [1209](../../../../agent/src/sr2fpga_agent/task_families/image.py#L1209) | `dedent` |
| `_vision_oracle_monitor` — `_vision_oracle_monitor()` | function / [1240](../../../../agent/src/sr2fpga_agent/task_families/image.py#L1240) | `dedent` |
| `_oracle_driver_task` — `_oracle_driver_task()` | function / [1276](../../../../agent/src/sr2fpga_agent/task_families/image.py#L1276) | `dedent` |
| `_insert_after_once` — `_insert_after_once(source, marker, addition)` | function / [1414](../../../../agent/src/sr2fpga_agent/task_families/image.py#L1414) | `RuntimeError`、`source.count`、`source.replace` |
| `_insert_before_once` — `_insert_before_once(source, marker, addition)` | function / [1420](../../../../agent/src/sr2fpga_agent/task_families/image.py#L1420) | `RuntimeError`、`source.count`、`source.replace` |
| `_replace_once` — `_replace_once(source, old, new)` | function / [1426](../../../../agent/src/sr2fpga_agent/task_families/image.py#L1426) | `RuntimeError`、`source.count`、`source.replace` |

## `agent/src/sr2fpga_agent/task_families/protocol.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/task_families/protocol.py) · 1269 行 · SHA-256 `52eeb3e3262c8627c1ef268cafb7a0cf10df6a9619f2d5bb171e8acf07e916c9`

> Stable family metadata for protocol and interface generator tasks.

导入模块：`textwrap`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `fifo_rtl` — `fifo_rtl(width)` | function / [14](../../../../agent/src/sr2fpga_agent/task_families/protocol.py#L14) | `dedent` |
| `fifo_testbench` — `fifo_testbench(width)` | function / [65](../../../../agent/src/sr2fpga_agent/task_families/protocol.py#L65) | `dedent` |
| `uart_tx_testbench` — `uart_tx_testbench()` | function / [201](../../../../agent/src/sr2fpga_agent/task_families/protocol.py#L201) | `dedent` |
| `uart_tx_rtl_files` — `uart_tx_rtl_files(width)` | function / [301](../../../../agent/src/sr2fpga_agent/task_families/protocol.py#L301) | `dedent` |
| `uart_rx_testbench` — `uart_rx_testbench()` | function / [452](../../../../agent/src/sr2fpga_agent/task_families/protocol.py#L452) | `dedent` |
| `uart_rx_rtl_files` — `uart_rx_rtl_files(width)` | function / [580](../../../../agent/src/sr2fpga_agent/task_families/protocol.py#L580) | `dedent` |
| `uart_fifo_loopback_testbench` — `uart_fifo_loopback_testbench()` | function / [701](../../../../agent/src/sr2fpga_agent/task_families/protocol.py#L701) | `dedent` |
| `uart_fifo_loopback_rtl_files` — `uart_fifo_loopback_rtl_files(width)` | function / [797](../../../../agent/src/sr2fpga_agent/task_families/protocol.py#L797) | `dedent`、`uart_rx_rtl_files` |
| `spi_master_testbench` — `spi_master_testbench()` | function / [1011](../../../../agent/src/sr2fpga_agent/task_families/protocol.py#L1011) | `dedent` |
| `spi_master_rtl_files` — `spi_master_rtl_files(width)` | function / [1124](../../../../agent/src/sr2fpga_agent/task_families/protocol.py#L1124) | `dedent` |

## `agent/src/sr2fpga_agent/task_families/rl.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/task_families/rl.py) · 4095 行 · SHA-256 `89f905ad65af9d72386f499b1221e42eb513df4fed2629141c6c9202f164947d`

> Stable family metadata for RL and host-facing generator tasks.

导入模块：`textwrap`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `batch_config_bank_rtl` — `batch_config_bank_rtl()` | function / [16](../../../../agent/src/sr2fpga_agent/task_families/rl.py#L16) | `dedent` |
| `composed_td_update_core_testbench` — `composed_td_update_core_testbench(width)` | function / [64](../../../../agent/src/sr2fpga_agent/task_families/rl.py#L64) | `_add_td_oracle_mode`、`dedent` |
| `composed_policy_value_shell_testbench` — `composed_policy_value_shell_testbench(width)` | function / [184](../../../../agent/src/sr2fpga_agent/task_families/rl.py#L184) | `dedent` |
| `composed_replay_sample_shell_testbench` — `composed_replay_sample_shell_testbench(width)` | function / [321](../../../../agent/src/sr2fpga_agent/task_families/rl.py#L321) | `dedent` |
| `composed_host_protocol_shell_testbench` — `composed_host_protocol_shell_testbench(width)` | function / [479](../../../../agent/src/sr2fpga_agent/task_families/rl.py#L479) | `dedent` |
| `composed_rl_accelerator_shell_testbench` — `composed_rl_accelerator_shell_testbench(width)` | function / [648](../../../../agent/src/sr2fpga_agent/task_families/rl.py#L648) | `_add_rl_accelerator_oracle_mode`、`dedent` |
| `_add_td_oracle_mode` — `_add_td_oracle_mode(testbench, width)` | function / [815](../../../../agent/src/sr2fpga_agent/task_families/rl.py#L815) | `_rl_insert_after_once`、`_rl_insert_before_once`、`_td_oracle_driver_task`、`dedent` |
| `_td_oracle_driver_task` — `_td_oracle_driver_task(width, reset_bit, stall_lsb)` | function / [861](../../../../agent/src/sr2fpga_agent/task_families/rl.py#L861) | `dedent` |
| `_add_rl_accelerator_oracle_mode` — `_add_rl_accelerator_oracle_mode(testbench, width)` | function / [978](../../../../agent/src/sr2fpga_agent/task_families/rl.py#L978) | `_rl_accelerator_oracle_driver_task`、`_rl_insert_after_once`、`_rl_insert_before_once`、`dedent` |
| `_rl_accelerator_oracle_driver_task` — `_rl_accelerator_oracle_driver_task(width)` | function / [1024](../../../../agent/src/sr2fpga_agent/task_families/rl.py#L1024) | `dedent` |
| `_rl_insert_after_once` — `_rl_insert_after_once(source, marker, addition)` | function / [1228](../../../../agent/src/sr2fpga_agent/task_families/rl.py#L1228) | `RuntimeError`、`source.count`、`source.replace` |
| `_rl_insert_before_once` — `_rl_insert_before_once(source, marker, addition)` | function / [1234](../../../../agent/src/sr2fpga_agent/task_families/rl.py#L1234) | `RuntimeError`、`source.count`、`source.replace` |
| `composed_batch_rl_accelerator_shell_testbench` — `composed_batch_rl_accelerator_shell_testbench(width)` | function / [1240](../../../../agent/src/sr2fpga_agent/task_families/rl.py#L1240) | `dedent` |
| `composed_replay_arbiter_shell_testbench` — `composed_replay_arbiter_shell_testbench(width)` | function / [1428](../../../../agent/src/sr2fpga_agent/task_families/rl.py#L1428) | `dedent` |
| `composed_td_update_core_rtl_files` — `composed_td_update_core_rtl_files(width)` | function / [1596](../../../../agent/src/sr2fpga_agent/task_families/rl.py#L1596) | `dedent` |
| `composed_policy_value_shell_rtl_files` — `composed_policy_value_shell_rtl_files(width)` | function / [1887](../../../../agent/src/sr2fpga_agent/task_families/rl.py#L1887) | `dedent` |
| `composed_replay_sample_shell_rtl_files` — `composed_replay_sample_shell_rtl_files(width)` | function / [2195](../../../../agent/src/sr2fpga_agent/task_families/rl.py#L2195) | `dedent` |
| `composed_host_protocol_shell_rtl_files` — `composed_host_protocol_shell_rtl_files(width)` | function / [2565](../../../../agent/src/sr2fpga_agent/task_families/rl.py#L2565) | `dedent` |
| `composed_rl_accelerator_shell_rtl_files` — `composed_rl_accelerator_shell_rtl_files(width)` | function / [2895](../../../../agent/src/sr2fpga_agent/task_families/rl.py#L2895) | `dedent` |
| `composed_batch_rl_accelerator_shell_rtl_files` — `composed_batch_rl_accelerator_shell_rtl_files(width)` | function / [3270](../../../../agent/src/sr2fpga_agent/task_families/rl.py#L3270) | `batch_config_bank_rtl`、`dedent` |
| `composed_replay_arbiter_shell_rtl_files` — `composed_replay_arbiter_shell_rtl_files(width)` | function / [3712](../../../../agent/src/sr2fpga_agent/task_families/rl.py#L3712) | `dedent` |

## `agent/src/sr2fpga_agent/task_families/stream.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/task_families/stream.py) · 1529 行 · SHA-256 `30dfa0875cc02a3274cbc2e3984b3450f31486128271c815fa97595e11c082fc`

> Stable family metadata for stream and composed generator tasks.

导入模块：`textwrap`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `streaming_valid_ready_testbench` — `streaming_valid_ready_testbench(width)` | function / [17](../../../../agent/src/sr2fpga_agent/task_families/stream.py#L17) | `dedent` |
| `streaming_valid_ready_rtl_files` — `streaming_valid_ready_rtl_files(width)` | function / [116](../../../../agent/src/sr2fpga_agent/task_families/stream.py#L116) | `dedent` |
| `composed_stream_accumulator_testbench` — `composed_stream_accumulator_testbench(width)` | function / [240](../../../../agent/src/sr2fpga_agent/task_families/stream.py#L240) | `dedent` |
| `composed_stream_accumulator_rtl_files` — `composed_stream_accumulator_rtl_files(width)` | function / [335](../../../../agent/src/sr2fpga_agent/task_families/stream.py#L335) | `dedent` |
| `composed_event_counter_testbench` — `composed_event_counter_testbench(width)` | function / [450](../../../../agent/src/sr2fpga_agent/task_families/stream.py#L450) | `dedent` |
| `composed_stream_fork_testbench` — `composed_stream_fork_testbench(width)` | function / [504](../../../../agent/src/sr2fpga_agent/task_families/stream.py#L504) | `dedent`、`min` |
| `composed_dual_stream_join_testbench` — `composed_dual_stream_join_testbench(width)` | function / [585](../../../../agent/src/sr2fpga_agent/task_families/stream.py#L585) | `dedent` |
| `composed_event_counter_rtl_files` — `composed_event_counter_rtl_files(width)` | function / [709](../../../../agent/src/sr2fpga_agent/task_families/stream.py#L709) | `dedent` |
| `composed_stream_fork_rtl_files` — `composed_stream_fork_rtl_files(width)` | function / [779](../../../../agent/src/sr2fpga_agent/task_families/stream.py#L779) | `dedent` |
| `pattern_matcher_testbench` — `pattern_matcher_testbench(width, project_mode)` | function / [964](../../../../agent/src/sr2fpga_agent/task_families/stream.py#L964) | `dedent`、`held_input_check.rstrip` |
| `_pattern_matcher_source` — `_pattern_matcher_source()` | function / [1119](../../../../agent/src/sr2fpga_agent/task_families/stream.py#L1119) | `dedent` |
| `pattern_matcher_rtl_files` — `pattern_matcher_rtl_files(width)` | function / [1181](../../../../agent/src/sr2fpga_agent/task_families/stream.py#L1181) | `_pattern_matcher_source`、`dedent` |
| `stream_trigger_filter_rtl_files` — `stream_trigger_filter_rtl_files(width)` | function / [1206](../../../../agent/src/sr2fpga_agent/task_families/stream.py#L1206) | `_pattern_matcher_source`、`dedent` |
| `composed_dual_stream_join_rtl_files` — `composed_dual_stream_join_rtl_files(width)` | function / [1301](../../../../agent/src/sr2fpga_agent/task_families/stream.py#L1301) | `dedent` |
