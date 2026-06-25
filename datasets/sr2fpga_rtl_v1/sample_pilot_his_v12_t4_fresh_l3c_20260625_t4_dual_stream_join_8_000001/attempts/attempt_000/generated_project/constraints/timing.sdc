# timing.sdc
# Clock constraint
create_clock -name clk -period 10.000 [get_ports clk]
# Input delays
set_input_delay -clock clk 2.0 [get_ports in0_data]
set_input_delay -clock clk 2.0 [get_ports in0_valid]
set_input_delay -clock clk 2.0 [get_ports in1_data]
set_input_delay -clock clk 2.0 [get_ports in1_valid]
set_input_delay -clock clk 2.0 [get_ports out_ready]
# Output delays
set_output_delay -clock clk 2.0 [get_ports in0_ready]
set_output_delay -clock clk 2.0 [get_ports in1_ready]
set_output_delay -clock clk 2.0 [get_ports out_data]
set_output_delay -clock clk 2.0 [get_ports out_valid]
