create_clock -period 10.000 -name clk [get_ports clk]
set_input_delay -clock clk 0.5 [get_ports rst_n]
set_output_delay -clock clk 0.5 [get_ports {state out}]
