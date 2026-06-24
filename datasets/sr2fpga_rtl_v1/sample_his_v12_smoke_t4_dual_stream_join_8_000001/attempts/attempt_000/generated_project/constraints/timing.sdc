# Timing constraints for top module
# Clock definition
create_clock -name clk -period 10.000 [get_ports clk]
# Reset constraints
set_input_delay -clock clk -max 2 [get_ports rst_n]
set_output_delay -clock clk -max 2 [get_ports out_*]
