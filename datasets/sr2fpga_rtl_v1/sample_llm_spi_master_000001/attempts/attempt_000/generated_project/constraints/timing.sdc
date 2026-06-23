# Timing constraints for 100 MHz clock
create_clock -period 10.000 -name clk [get_ports clk]
set_input_delay -clock clk -max 2.0 [get_ports data_in]
set_output_delay -clock clk -max 4.0 [get_ports {sclk mosi cs_n}]
set_false_path -from [get_clocks clk] -to [get_pins */*/sclk]
