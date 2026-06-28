# Timing constraints for 100MHz
create_clock -name clk -period 10.000 [get_ports clk]
set_input_delay -clock clk 1.0 [all_inputs]
set_output_delay -clock clk 1.0 [all_outputs]
