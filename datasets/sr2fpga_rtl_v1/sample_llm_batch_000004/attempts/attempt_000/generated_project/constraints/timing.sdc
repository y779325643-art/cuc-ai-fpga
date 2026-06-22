create_clock -period 10.0 -name clk [get_ports clk]
set_output_delay -clock clk -max 5.0 [get_ports rd_data]
set_input_delay -clock clk -max 5.0 [get_ports wr_data]
