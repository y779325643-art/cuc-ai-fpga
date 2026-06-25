`timescale 1ns / 1ps

module stream_join #(
    parameter DATA_WIDTH = 8
)(
    input  wire                clk,
    input  wire                reset_n,
    input  wire [DATA_WIDTH-1:0] in0_data,
    input  wire                in0_valid,
    output reg                 in0_ready,
    input  wire [DATA_WIDTH-1:0] in1_data /* verilator lint_off UNUSEDSIGNAL */,
    input  wire                in1_valid,
    output reg                 in1_ready,
    output reg  [DATA_WIDTH-1:0] out_data,
    output reg                 out_valid,
    input  wire                out_ready
);

    // When both inputs are valid and we can accept (in0_ready & in1_ready high), capture data.
    // Output one cycle later if out_ready is high or we can hold.
    reg [DATA_WIDTH-1:0] held_data;
    reg held_valid;

    always @(posedge clk) begin
        if (!reset_n) begin
            in0_ready   <= 1'b0;
            in1_ready   <= 1'b0;
            held_data   <= {DATA_WIDTH{1'b0}};
            held_valid  <= 1'b0;
            out_data    <= {DATA_WIDTH{1'b0}};
            out_valid   <= 1'b0;
        end else begin
            // Default: ready when we can accept new data (not holding or output consumed)
            if (!held_valid || (out_valid && out_ready)) begin
                in0_ready <= 1'b1;
                in1_ready <= 1'b1;
            end else begin
                in0_ready <= 1'b0;
                in1_ready <= 1'b0;
            end

            // Input capture
            if (in0_ready && in1_ready && in0_valid && in1_valid) begin
                if (out_valid && out_ready) begin
                    // Output consumed this cycle, so we can output directly
                    out_data  <= in0_data;  // forward in0_data as joined data
                    out_valid <= 1'b1;
                    held_valid <= 1'b0;
                end else begin
                    // Hold for next cycle
                    held_data  <= in0_data;
                    held_valid <= 1'b1;
                    out_valid  <= 1'b0;
                end
            end else begin
                // If holding and output ready, output held data
                if (held_valid && out_ready) begin
                    out_data  <= held_data;
                    out_valid <= 1'b1;
                    held_valid <= 1'b0;
                end else if (!held_valid) begin
                    out_valid <= 1'b0;
                end
            end
        end
    end

endmodule
