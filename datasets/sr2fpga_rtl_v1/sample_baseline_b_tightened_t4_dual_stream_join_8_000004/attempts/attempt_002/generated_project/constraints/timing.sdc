# 100MHz clock constraint
create_clock -period 10.000 -name clk [get_ports clk]
set_clock_uncertainty 0.200 [get_clocks clk]
set_input_delay -clock clk 2.000 [get_ports in0_*]
set_input_delay -clock clk 2.000 [get_ports in1_*]
set_output_delay -clock clk 2.000 [get_ports out_*]
