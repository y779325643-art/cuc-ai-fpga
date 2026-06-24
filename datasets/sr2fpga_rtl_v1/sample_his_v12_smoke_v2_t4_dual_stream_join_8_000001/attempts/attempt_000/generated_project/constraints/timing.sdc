create_clock -period 10.000 -name clk [get_ports clk]
set_output_delay -clock clk 2.0 [get_ports out_data]
set_input_delay -clock clk 2.0 [get_ports in0_data in1_data]
