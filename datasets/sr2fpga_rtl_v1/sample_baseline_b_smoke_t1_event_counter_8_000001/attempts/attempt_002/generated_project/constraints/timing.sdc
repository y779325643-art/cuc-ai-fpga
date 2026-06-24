create_clock -name clk -period 10.000 -waveform {0 5} [get_ports clk]
set_input_delay -clock clk -max 2.0 [get_ports event_valid]
set_output_delay -clock clk -max 3.0 [get_ports count]
