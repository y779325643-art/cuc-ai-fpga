# Timing constraints for top module
create_clock -name clk -period 10.000 [get_ports clk]
set_input_delay -clock clk -max 2.0 [get_ports in0_*]
set_input_delay -clock clk -max 2.0 [get_ports in1_*]
set_output_delay -clock clk -max 2.0 [get_ports out_*]
