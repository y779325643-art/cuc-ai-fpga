# Timing constraints for 100 MHz clock
create_clock -period 10.0 -name sysclk [get_ports clk]
set_input_delay -clock sysclk 0.5 [get_ports in_*]
set_output_delay -clock sysclk 0.5 [get_ports out_*]
