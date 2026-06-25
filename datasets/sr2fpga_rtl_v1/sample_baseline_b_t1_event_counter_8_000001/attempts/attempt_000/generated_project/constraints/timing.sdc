# Clock constraint
create_clock -name clk -period 10.000 [get_ports clk]

# Input delays (dummy)
set_input_delay -clock clk 2.0 [get_ports event_valid]

# Output delays (dummy)
set_output_delay -clock clk 2.0 [get_ports count]
