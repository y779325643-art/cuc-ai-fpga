////////////////////////////////////////////////////////////////////////////////
// event_gate.v
// Rising edge detector for event_in. Outputs a single-cycle pulse on
// event_pulse_out when a rising edge is detected.
////////////////////////////////////////////////////////////////////////////////

`timescale 1ns / 1ps

module event_gate (
    input  wire clk,
    input  wire rst_n,
    input  wire event_in,
    output reg  event_pulse_out
);

    reg event_in_delay;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            event_in_delay   <= 1'b0;
            event_pulse_out  <= 1'b0;
        end else begin
            event_in_delay   <= event_in;
            event_pulse_out  <= event_in & ~event_in_delay;  // rising edge
        end
    end

endmodule
