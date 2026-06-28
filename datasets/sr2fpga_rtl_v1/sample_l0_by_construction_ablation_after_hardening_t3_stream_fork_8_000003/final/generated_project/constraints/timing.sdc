# System clock
create_clock -name clk -period 10.000 [get_ports clk]

# Input delays
set_input_delay -clock clk -max 2.0 [get_ports {in_valid in_data out0_ready out1_ready}]
set_input_delay -clock clk -min 0.5 [get_ports {in_valid in_data out0_ready out1_ready}]

# Output delays
set_output_delay -clock clk -max 2.0 [get_ports {in_ready out0_valid out0_data out1_valid out1_data}]
set_output_delay -clock clk -min 0.5 [get_ports {in_ready out0_valid out0_data out1_valid out1_data}]

# Reset as false path (or set_input_delay)
set_false_path -from [get_ports nreset]
