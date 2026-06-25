# Timing constraints for top module
# Generated from System-HIS v1.2

create_clock -name clk -period 10.000 [get_ports clk] ;# 100 MHz
set_input_delay -clock clk -max 2.0 [get_ports in0_data* in1_data* in0_valid in1_valid out_ready]
set_input_delay -clock clk -min 0.5 [get_ports in0_data* in1_data* in0_valid in1_valid out_ready]
set_output_delay -clock clk -max 2.0 [get_ports in0_ready in1_ready out_data* out_valid]
set_output_delay -clock clk -min 0.5 [get_ports in0_ready in1_ready out_data* out_valid]
