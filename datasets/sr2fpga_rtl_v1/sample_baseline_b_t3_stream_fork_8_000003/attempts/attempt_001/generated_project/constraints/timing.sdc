create_clock -name clk -period 10.000 [get_ports clk]
set_input_delay -clock clk -max 4.0 [get_ports in_*]
set_output_delay -clock clk -max 4.0 [get_ports out_*]
