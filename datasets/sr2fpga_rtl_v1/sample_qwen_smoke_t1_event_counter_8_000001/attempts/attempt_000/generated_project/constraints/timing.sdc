# Timing constraints for qwen_smoke_t1_event_counter_8_000001
# Target clock: 100 MHz (10 ns period)

create_clock -name clk -period 10.0 [get_ports clk]

# Input delays
set_input_delay -clock clk 2.0 [get_ports rst_n]
set_input_delay -clock clk 2.0 [get_ports event_in]

# Output delays
set_output_delay -clock clk 2.0 [get_ports count_out*]

# False path on reset (synchronous, but allow extra margin)
set_false_path -from [get_ports rst_n]
