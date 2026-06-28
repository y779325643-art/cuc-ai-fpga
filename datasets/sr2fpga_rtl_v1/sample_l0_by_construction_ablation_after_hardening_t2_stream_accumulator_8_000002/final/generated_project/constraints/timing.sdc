create_clock -period 10.000 -name clk [get_ports clk]
set_false_path -to [get_ports rst_n]
