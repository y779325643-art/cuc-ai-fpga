create_clock -name clk -period 10.000 [get_ports clk]
set_clock_uncertainty 0.500
set_input_delay -clock clk 2.000 [all_inputs]
set_output_delay -clock clk 2.000 [all_outputs]
