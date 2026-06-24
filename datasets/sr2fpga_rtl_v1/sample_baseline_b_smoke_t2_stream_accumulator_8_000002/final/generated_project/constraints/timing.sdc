create_clock -period 10.000 -name clk [get_ports clk]
set_clock_groups -asynchronous -group [get_clocks clk]
