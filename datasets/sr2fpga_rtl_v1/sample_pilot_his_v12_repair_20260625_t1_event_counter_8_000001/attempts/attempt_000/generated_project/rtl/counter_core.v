////////////////////////////////////////////////////////////////////////////////
// counter_core.v
// 8-bit event counter. Increments on rising edge of event_pulse_in.
// Outputs count and a single-cycle count_valid pulse.
////////////////////////////////////////////////////////////////////////////////

`timescale 1ns / 1ps

module counter_core (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       event_pulse_in,
    output reg  [7:0] count,
    output reg        count_valid
);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count        <= 8'd0;
            count_valid  <= 1'b0;
        end else begin
            count_valid  <= event_pulse_in;
            if (event_pulse_in) begin
                count <= count + 1'b1;
            end
        end
    end

endmodule
