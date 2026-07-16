# SR2FPGA Task Evidence Status

Generated from the task catalog and evidence ledger. Target intent, current implementation, and ledger-declared verification claims are reported separately.

## Summary

| Measure | Value |
| --- | --- |
| Catalog families | 71 |
| Implemented families | 31 / 71 |
| Paper 1 core implemented | 14 / 14 |
| Mutation-qualified families | 17 |
| Independent Python oracle qualified | 9 |
| OpenXC7 L4 pass | 2 |
| Commercial L4 pass | 2 |
| L5 pass | 0 |

## Target Task Map

| Family | Task kind | Tier | Benchmark role | Intended oracle |
| --- | --- | --- | --- | --- |
| clock_divider | module_family | T0 | smoke | reference_model |
| binary_bcd_counter | module_family | T0 | smoke | reference_model |
| button_debounce | module_family | T0 | smoke | reference_model |
| simple_fsm | module_family | T0 | smoke | reference_model |
| seven_seg_scan | module_family | T0 | smoke | reference_model |
| pwm_generator | module_family | T0 | smoke | reference_model |
| baud_generator | module_family | T0 | smoke | reference_model |
| uart_tx | module_family | T0 | paper1_core | protocol_checker, transaction_scoreboard |
| uart_rx | module_family | T1 | eval_subset | protocol_checker, transaction_scoreboard |
| uart_fifo_loopback | module_family | T1 | paper1_core | protocol_checker, transaction_scoreboard |
| sync_fifo | module_family | T0 | paper1_core | transaction_scoreboard, protocol_checker |
| async_fifo_cdc | module_family | T3 | eval_subset | structural_cdc_checker, transaction_scoreboard |
| single_dual_port_ram | module_family | T0 | paper1_core | reference_model |
| vga_timing | module_family | T1 | eval_subset | protocol_checker |
| pixel_generator_basic | module_family | T1 | eval_subset | frame_object_checker |
| hdmi_tmds_basic | module_family | T4 | future | protocol_checker |
| valid_ready_stream_stage | module_family | T2 | paper1_core | transaction_scoreboard, protocol_checker |
| valid_ready_stream_accumulator | module_family | T2 | paper1_core | transaction_scoreboard, protocol_checker |
| stream_fork_join | module_family | T2 | paper1_core | transaction_scoreboard, protocol_checker |
| mac_array | module_family | T3 | paper1_core | python_numpy_golden |
| matrix_vector_mac | module_family | T3 | paper1_core | python_numpy_golden, transaction_scoreboard |
| fir_filter | module_family | T3 | paper1_core | python_numpy_golden, transaction_scoreboard |
| spi_master | module_family | T1 | paper1_core | protocol_checker, transaction_scoreboard |
| i2c_master | module_family | T3 | eval_subset | protocol_checker |
| line_frame_buffer | module_family | T3 | eval_subset | image_golden, transaction_scoreboard |
| sobel_threshold | module_family | T3 | paper1_core | image_golden |
| matched_filter | module_family | T3 | paper1_core | python_signal_golden, transaction_scoreboard |
| peak_detector | module_family | T3 | paper1_core | python_signal_golden |
| pattern_matcher | module_family | T2 | paper1_core | transaction_scoreboard, protocol_checker |
| conv2d_core | module_family | T3 | eval_subset | python_numpy_golden, image_golden |
| pooling_activation | module_family | T3 | eval_subset | python_numpy_golden |
| image_scale_norm | module_family | T3 | eval_subset | image_golden |
| sprite_object_mapper | module_family | T4 | eval_subset | frame_object_checker |
| collision_detector | module_family | T3 | paper1_core | reference_model |
| font_text_renderer | module_family | T3 | eval_subset | frame_object_checker |
| ga_fitness_eval | module_family | T3 | paper2_bridge | python_ga_golden |
| ga_select_cross_mutate | module_family | T3 | paper2_bridge | python_ga_golden |
| population_eval_parallel | module_family | T4 | paper2_bridge | python_ga_golden |
| fft_ifft_simplified | module_family | T4 | advanced_eval | python_numpy_golden |
| qam_mapping_equalizer | module_family | T4 | future | comms_python_golden |
| qtable_update_core | module_family | T3 | flagship_core | python_rl_golden |
| small_nn_accelerator | module_family | T4 | advanced_eval | python_numpy_golden |
| rl_reward_policy_update | module_family | T4 | flagship_core | python_rl_golden |
| cpu_axi_soc_shell | module_family | T4 | fixed_infrastructure | host_signature |
| sensor_fusion_arbiter | module_family | T4 | flagship_candidate | mixed_oracle |
| memory_interrupt_controller | module_family | T4 | future | protocol_checker, host_signature |
| soc_top_wrapper | module_family | T4 | fixed_infrastructure | host_signature |
| p_led_breath_button | project_family | T0 | smoke_board_demo | reference_model |
| p_seven_seg_stopwatch | project_family | T0 | smoke_board_demo | reference_model |
| p_traffic_light | project_family | T1 | smoke | reference_model |
| p_uart_transceiver | project_family | T2 | paper1_core | protocol_checker, transaction_scoreboard |
| p_vga_simple_graphics | project_family | T2 | demo | frame_object_checker |
| p_fifo_ram_app | project_family | T2 | paper1_core | transaction_scoreboard, reference_model |
| p_fir_filter | project_family | T3 | paper1_core | python_numpy_golden, transaction_scoreboard |
| p_sd_spi_controller | project_family | T3 | eval_subset | protocol_checker, python_numpy_golden |
| p_pulse_radar_signal | project_family | T3 | paper1_core | python_signal_golden, transaction_scoreboard |
| p_vision_defect_core | project_family | T3 | eval_subset | image_golden |
| p_pong_game | project_family | T4 | board_demo | frame_object_checker, host_signature |
| p_simple_cnn_pipeline | project_family | T4 | eval_subset | python_numpy_golden, image_golden |
| p_stream_trigger_filter | project_family | T3 | paper1_core | transaction_scoreboard, protocol_checker |
| p_ga_accelerator | project_family | T4 | paper2_bridge | python_ga_golden |
| p_ofdm_modem_subset | project_family | T4 | future | comms_python_golden |
| p_sensor_fusion_obstacle | project_family | T4 | flagship_candidate | mixed_oracle, host_signature |
| p_riscv_soc_shell | project_family | T4 | external_anchor | host_signature |
| p_rl_qlearning_accel | project_family | T4 | flagship | python_rl_golden, host_signature |
| alu_control_unit | module_family | T1 | smoke | reference_model |
| crc_stream_checker | module_family | T2 | eval_subset | transaction_scoreboard, protocol_checker |
| t1_event_counter | module_family | T1 | smoke | reference_model |
| t8_replay_sample_shell | project_family | T3 | advanced_eval | transaction_scoreboard, host_signature |
| t9_host_protocol_shell | project_family | T4 | flagship_candidate | protocol_checker, host_signature |
| t12_replay_arbiter_shell | project_family | T4 | flagship_candidate | transaction_scoreboard, host_signature |

## Current Implementation Matrix

| Family | Generator | Testbench | Golden model |
| --- | --- | --- | --- |
| clock_divider | not_implemented | not_implemented | none |
| binary_bcd_counter | implemented | implemented | embedded_sv |
| button_debounce | not_implemented | not_implemented | none |
| simple_fsm | implemented | implemented | embedded_sv |
| seven_seg_scan | not_implemented | not_implemented | none |
| pwm_generator | implemented | implemented | embedded_sv |
| baud_generator | not_implemented | not_implemented | none |
| uart_tx | implemented | implemented | embedded_sv |
| uart_rx | implemented | implemented | embedded_sv |
| uart_fifo_loopback | implemented | implemented | embedded_sv |
| sync_fifo | implemented | implemented | embedded_sv |
| async_fifo_cdc | not_implemented | not_implemented | none |
| single_dual_port_ram | implemented | implemented | embedded_sv |
| vga_timing | not_implemented | not_implemented | none |
| pixel_generator_basic | not_implemented | not_implemented | none |
| hdmi_tmds_basic | not_implemented | not_implemented | none |
| valid_ready_stream_stage | implemented | implemented | embedded_sv |
| valid_ready_stream_accumulator | implemented | implemented | embedded_sv |
| stream_fork_join | implemented | implemented | embedded_sv |
| mac_array | implemented | implemented | embedded_sv |
| matrix_vector_mac | implemented | implemented | python_reference |
| fir_filter | implemented | implemented | python_reference |
| spi_master | implemented | implemented | embedded_sv |
| i2c_master | not_implemented | not_implemented | none |
| line_frame_buffer | not_implemented | not_implemented | none |
| sobel_threshold | implemented | implemented | python_reference |
| matched_filter | implemented | implemented | python_reference |
| peak_detector | implemented | implemented | python_reference |
| pattern_matcher | implemented | implemented | embedded_sv |
| conv2d_core | not_implemented | not_implemented | none |
| pooling_activation | not_implemented | not_implemented | none |
| image_scale_norm | not_implemented | not_implemented | none |
| sprite_object_mapper | not_implemented | not_implemented | none |
| collision_detector | not_implemented | not_implemented | none |
| font_text_renderer | not_implemented | not_implemented | none |
| ga_fitness_eval | not_implemented | not_implemented | none |
| ga_select_cross_mutate | not_implemented | not_implemented | none |
| population_eval_parallel | not_implemented | not_implemented | none |
| fft_ifft_simplified | not_implemented | not_implemented | none |
| qam_mapping_equalizer | not_implemented | not_implemented | none |
| qtable_update_core | implemented | implemented | python_reference |
| small_nn_accelerator | not_implemented | not_implemented | none |
| rl_reward_policy_update | implemented | implemented | embedded_sv |
| cpu_axi_soc_shell | not_implemented | not_implemented | none |
| sensor_fusion_arbiter | not_implemented | not_implemented | none |
| memory_interrupt_controller | not_implemented | not_implemented | none |
| soc_top_wrapper | not_implemented | not_implemented | none |
| p_led_breath_button | not_implemented | not_implemented | none |
| p_seven_seg_stopwatch | not_implemented | not_implemented | none |
| p_traffic_light | not_implemented | not_implemented | none |
| p_uart_transceiver | not_implemented | not_implemented | none |
| p_vga_simple_graphics | not_implemented | not_implemented | none |
| p_fifo_ram_app | not_implemented | not_implemented | none |
| p_fir_filter | not_implemented | not_implemented | none |
| p_sd_spi_controller | not_implemented | not_implemented | none |
| p_pulse_radar_signal | implemented | implemented | python_reference |
| p_vision_defect_core | implemented | implemented | python_reference |
| p_pong_game | not_implemented | not_implemented | none |
| p_simple_cnn_pipeline | not_implemented | not_implemented | none |
| p_stream_trigger_filter | implemented | implemented | embedded_sv |
| p_ga_accelerator | not_implemented | not_implemented | none |
| p_ofdm_modem_subset | not_implemented | not_implemented | none |
| p_sensor_fusion_obstacle | not_implemented | not_implemented | none |
| p_riscv_soc_shell | not_implemented | not_implemented | none |
| p_rl_qlearning_accel | implemented | implemented | python_reference |
| alu_control_unit | implemented | implemented | embedded_sv |
| crc_stream_checker | implemented | implemented | embedded_sv |
| t1_event_counter | implemented | implemented | embedded_sv |
| t8_replay_sample_shell | implemented | implemented | embedded_sv |
| t9_host_protocol_shell | implemented | implemented | embedded_sv |
| t12_replay_arbiter_shell | implemented | implemented | embedded_sv |

## Ledger-Declared Verification Claims

This matrix is not an audit of local artifacts. Artifact-backed proof requires `audit_local_run_artifacts()` against the relevant run root.

| Family | Mutation | Score | Independent oracle | Level | L4-open | L4-commercial | L5 | Run |
| --- | --- | --- | --- | --- | --- | --- | --- |
| clock_divider | not_run | - | not_run | not_run | not_run | not_run | not_run | - |
| binary_bcd_counter | not_run | - | not_run | L3 | not_run | not_run | not_run | codex-spec-final-clean-smoke-20260713 |
| button_debounce | not_run | - | not_run | not_run | not_run | not_run | not_run | - |
| simple_fsm | not_run | - | not_run | L3 | not_run | not_run | not_run | codex-spec-final-clean-smoke-20260713 |
| seven_seg_scan | not_run | - | not_run | not_run | not_run | not_run | not_run | - |
| pwm_generator | not_run | - | not_run | L3 | not_run | not_run | not_run | codex-spec-final-clean-smoke-20260713 |
| baud_generator | not_run | - | not_run | not_run | not_run | not_run | not_run | - |
| uart_tx | qualified (line-a-oracle-evidence-20260713-v2) | 1 | not_run | L3 | not_run | not_run | not_run | line-a-oracle-evidence-20260713-v2 |
| uart_rx | qualified (phase-b-core-closure-20260713-v4) | 1 | not_run | L3 | not_run | not_run | not_run | phase-b-core-closure-20260713-v4 |
| uart_fifo_loopback | qualified (phase-b-core-closure-20260713-v4) | 1 | not_run | L3 | not_run | not_run | not_run | phase-b-core-closure-20260713-v4 |
| sync_fifo | qualified (line-a-oracle-evidence-20260713-v2) | 1 | not_run | L3 | not_run | not_run | not_run | line-a-oracle-evidence-20260713-v2 |
| async_fifo_cdc | not_run | - | not_run | not_run | not_run | not_run | not_run | - |
| single_dual_port_ram | not_run | - | not_run | L3 | not_run | not_run | not_run | codex-spec-final-clean-smoke-20260713 |
| vga_timing | not_run | - | not_run | not_run | not_run | not_run | not_run | - |
| pixel_generator_basic | not_run | - | not_run | not_run | not_run | not_run | not_run | - |
| hdmi_tmds_basic | not_run | - | not_run | not_run | not_run | not_run | not_run | - |
| valid_ready_stream_stage | qualified (line-a-oracle-evidence-20260713-v2) | 1 | not_run | L3 | not_run | not_run | not_run | line-a-oracle-evidence-20260713-v2 |
| valid_ready_stream_accumulator | not_run | - | not_run | L3 | not_run | not_run | not_run | codex-spec-final-clean-smoke-20260713 |
| stream_fork_join | not_run | - | not_run | L3 | not_run | not_run | not_run | codex-spec-final-clean-smoke-20260713 |
| mac_array | not_run | - | not_run | L3 | not_run | not_run | not_run | codex-spec-final-clean-smoke-20260713 |
| matrix_vector_mac | qualified (phase-c-independent-oracle-20260714-v1) | 1 | qualified | L4 | pass | pass | not_run | phase-c-independent-oracle-20260714-v1 |
| fir_filter | qualified (phase-c-independent-oracle-20260714-v1) | 1 | qualified | L4 | pass | pass | not_run | phase-c-independent-oracle-20260714-v1 |
| spi_master | qualified (line-a-oracle-evidence-20260713-v2) | 1 | not_run | L3 | not_run | not_run | not_run | line-a-oracle-evidence-20260713-v2 |
| i2c_master | not_run | - | not_run | not_run | not_run | not_run | not_run | - |
| line_frame_buffer | not_run | - | not_run | not_run | not_run | not_run | not_run | - |
| sobel_threshold | qualified (phase-c-independent-oracle-20260714-v1) | 1 | qualified | L3 | not_run | not_run | not_run | phase-c-independent-oracle-20260714-v1 |
| matched_filter | qualified (phase-c-independent-oracle-20260714-v1) | 1 | qualified | L3 | not_run | not_run | not_run | phase-c-independent-oracle-20260714-v1 |
| peak_detector | qualified (phase-c-independent-oracle-20260714-v1) | 1 | qualified | L3 | not_run | not_run | not_run | phase-c-independent-oracle-20260714-v1 |
| pattern_matcher | qualified (phase-b-core-closure-20260713-v4) | 1 | not_run | L3 | not_run | not_run | not_run | phase-b-core-closure-20260713-v4 |
| conv2d_core | not_run | - | not_run | not_run | not_run | not_run | not_run | - |
| pooling_activation | not_run | - | not_run | not_run | not_run | not_run | not_run | - |
| image_scale_norm | not_run | - | not_run | not_run | not_run | not_run | not_run | - |
| sprite_object_mapper | not_run | - | not_run | not_run | not_run | not_run | not_run | - |
| collision_detector | not_run | - | not_run | not_run | not_run | not_run | not_run | - |
| font_text_renderer | not_run | - | not_run | not_run | not_run | not_run | not_run | - |
| ga_fitness_eval | not_run | - | not_run | not_run | not_run | not_run | not_run | - |
| ga_select_cross_mutate | not_run | - | not_run | not_run | not_run | not_run | not_run | - |
| population_eval_parallel | not_run | - | not_run | not_run | not_run | not_run | not_run | - |
| fft_ifft_simplified | not_run | - | not_run | not_run | not_run | not_run | not_run | - |
| qam_mapping_equalizer | not_run | - | not_run | not_run | not_run | not_run | not_run | - |
| qtable_update_core | qualified (phase-c-independent-oracle-20260714-v1) | 1 | qualified | L3 | not_run | not_run | not_run | phase-c-independent-oracle-20260714-v1 |
| small_nn_accelerator | not_run | - | not_run | not_run | not_run | not_run | not_run | - |
| rl_reward_policy_update | not_run | - | not_run | L3 | not_run | not_run | not_run | codex-spec-final-clean-smoke-20260713 |
| cpu_axi_soc_shell | not_run | - | not_run | not_run | not_run | not_run | not_run | - |
| sensor_fusion_arbiter | not_run | - | not_run | not_run | not_run | not_run | not_run | - |
| memory_interrupt_controller | not_run | - | not_run | not_run | not_run | not_run | not_run | - |
| soc_top_wrapper | not_run | - | not_run | not_run | not_run | not_run | not_run | - |
| p_led_breath_button | not_run | - | not_run | not_run | not_run | not_run | not_run | - |
| p_seven_seg_stopwatch | not_run | - | not_run | not_run | not_run | not_run | not_run | - |
| p_traffic_light | not_run | - | not_run | not_run | not_run | not_run | not_run | - |
| p_uart_transceiver | not_run | - | not_run | not_run | not_run | not_run | not_run | - |
| p_vga_simple_graphics | not_run | - | not_run | not_run | not_run | not_run | not_run | - |
| p_fifo_ram_app | not_run | - | not_run | not_run | not_run | not_run | not_run | - |
| p_fir_filter | not_run | - | not_run | not_run | not_run | not_run | not_run | - |
| p_sd_spi_controller | not_run | - | not_run | not_run | not_run | not_run | not_run | - |
| p_pulse_radar_signal | qualified (phase-c-independent-oracle-20260714-v1) | 1 | qualified | L3 | not_run | not_run | not_run | phase-c-independent-oracle-20260714-v1 |
| p_vision_defect_core | qualified (phase-c-independent-oracle-20260714-v1) | 1 | qualified | L3 | not_run | not_run | not_run | phase-c-independent-oracle-20260714-v1 |
| p_pong_game | not_run | - | not_run | not_run | not_run | not_run | not_run | - |
| p_simple_cnn_pipeline | not_run | - | not_run | not_run | not_run | not_run | not_run | - |
| p_stream_trigger_filter | qualified (phase-b-core-closure-20260713-v4) | 1 | not_run | L3 | not_run | not_run | not_run | phase-b-core-closure-20260713-v4 |
| p_ga_accelerator | not_run | - | not_run | not_run | not_run | not_run | not_run | - |
| p_ofdm_modem_subset | not_run | - | not_run | not_run | not_run | not_run | not_run | - |
| p_sensor_fusion_obstacle | not_run | - | not_run | not_run | not_run | not_run | not_run | - |
| p_riscv_soc_shell | not_run | - | not_run | not_run | not_run | not_run | not_run | - |
| p_rl_qlearning_accel | qualified (phase-c-independent-oracle-20260714-v1) | 1 | qualified | L3 | not_run | not_run | not_run | phase-c-independent-oracle-20260714-v1 |
| alu_control_unit | not_run | - | not_run | L3 | not_run | not_run | not_run | codex-spec-final-clean-smoke-20260713 |
| crc_stream_checker | not_run | - | not_run | L3 | not_run | not_run | not_run | codex-spec-final-clean-smoke-20260713 |
| t1_event_counter | not_run | - | not_run | L3 | not_run | not_run | not_run | codex-spec-final-clean-smoke-20260713 |
| t8_replay_sample_shell | not_run | - | not_run | L3 | not_run | not_run | not_run | codex-spec-final-clean-smoke-20260713 |
| t9_host_protocol_shell | not_run | - | not_run | L3 | not_run | not_run | not_run | codex-spec-final-clean-smoke-20260713 |
| t12_replay_arbiter_shell | not_run | - | not_run | L3 | not_run | not_run | not_run | codex-spec-final-clean-smoke-20260713 |

## Paper 1 Closure Gaps

| Family | Generator | Testbench | Highest verified level |
| --- | --- | --- | --- |
