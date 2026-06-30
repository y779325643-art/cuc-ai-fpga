# timing.sdc: basic clock constraint for 100 MHz
create_clock -name clk -period 10.000 -waveform {0 5} [get_ports clk]
set_input_delay -clock clk -max 3.0 [all_inputs]
set_input_delay -clock clk -min 1.0 [all_inputs]
set_output_delay -clock clk -max 3.0 [all_outputs]
set_output_delay -clock clk -min 1.0 [all_outputs]
