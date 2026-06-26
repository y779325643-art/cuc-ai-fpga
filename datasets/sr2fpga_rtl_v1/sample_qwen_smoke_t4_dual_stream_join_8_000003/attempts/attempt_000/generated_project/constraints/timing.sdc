# Timing constraints for qwen_smoke_t4_dual_stream_join_8_000003
create_clock -period 10.0 [get_ports clk]
set_input_delay -clock clk -max 2.0 [get_ports {in0_data in0_valid in1_data in1_valid}]
set_input_delay -clock clk -min 1.0 [get_ports {in0_data in0_valid in1_data in1_valid}]
set_output_delay -clock clk -max 2.0 [get_ports {out_data out_valid}]
set_output_delay -clock clk -min 1.0 [get_ports {out_data out_valid}]
set_false_path -from [get_ports rst_n]
