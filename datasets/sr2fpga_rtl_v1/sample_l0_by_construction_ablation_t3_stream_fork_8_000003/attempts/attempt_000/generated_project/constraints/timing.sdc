create_clock -period 10.000 -name clk [get_ports clk]
set_input_delay  -clock clk  2.0 [get_ports {in_valid in_data out0_ready out1_ready}]
set_output_delay -clock clk  2.0 [get_ports {in_ready out0_valid out0_data out1_valid out1_data}]
