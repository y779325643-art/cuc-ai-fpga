create_clock -period 10.000 -name clk [get_ports clk]
set_input_delay -clock clk 2.0 [get_ports in_valid]
set_input_delay -clock clk 2.0 [get_ports in_data]
set_output_delay -clock clk 2.0 [get_ports sum]
