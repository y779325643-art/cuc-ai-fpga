# Timing constraints for 100 MHz clock
create_clock -period 10.000 -name clk [get_ports clk]
set_clock_uncertainty -setup 0.200 [get_clocks clk]
set_clock_uncertainty -hold 0.100 [get_clocks clk]
set_input_delay -clock clk -max 2.000 [get_ports in0_valid in1_valid in0_data in1_data out_ready]
set_input_delay -clock clk -min 0.500 [get_ports in0_valid in1_valid in0_data in1_data out_ready]
set_output_delay -clock clk -max 2.000 [get_ports in0_ready in1_ready out_valid out_data]
set_output_delay -clock clk -min 0.500 [get_ports in0_ready in1_ready out_valid out_data]
