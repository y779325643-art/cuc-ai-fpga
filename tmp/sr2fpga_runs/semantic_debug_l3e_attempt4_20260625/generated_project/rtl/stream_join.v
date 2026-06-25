module stream_join #(
    parameter DATA_WIDTH = 8
) (
    input  wire                 clk,
    input  wire                 reset_n,
    input  wire                 in0_valid,
    output reg                  in0_ready,
    input  wire [DATA_WIDTH-1:0] in0_data,
    input  wire                 in1_valid,
    output reg                  in1_ready,
    input  wire [DATA_WIDTH-1:0] in1_data,
    output reg                  out_valid,
    input  wire                 out_ready,
    output reg [DATA_WIDTH-1:0] out_data
);

    reg [DATA_WIDTH-1:0] buf0_data;
    reg                  buf0_valid;
    reg [DATA_WIDTH-1:0] buf1_data;
    reg                  buf1_valid;
    reg                  have_both;

    always @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            in0_ready <= 1'b0;
            in1_ready <= 1'b0;
            out_valid <= 1'b0;
            out_data <= {DATA_WIDTH{1'b0}};
            buf0_valid <= 1'b0;
            buf1_valid <= 1'b0;
            have_both <= 1'b0;
        end else begin
            // Default assignments
            in0_ready <= !buf0_valid || (out_ready && have_both);
            in1_ready <= !buf1_valid || (out_ready && have_both);
            // Input capture
            if (in0_valid && in0_ready) begin
                buf0_data <= in0_data;
                buf0_valid <= 1'b1;
            end
            if (in1_valid && in1_ready) begin
                buf1_data <= in1_data;
                buf1_valid <= 1'b1;
            end
            // Check if both are valid and not already have_both
            if (buf0_valid && buf1_valid && !have_both) begin
                have_both <= 1'b1;
            end
            // Output logic - fixed to clear after output
            if (have_both) begin
                if (out_ready) begin
                    out_valid <= 1'b1;
                    out_data <= buf0_data + buf1_data;
                    have_both <= 1'b0;
                    buf0_valid <= 1'b0;
                    buf1_valid <= 1'b0;
                end else begin
                    out_valid <= 1'b1;
                    out_data <= buf0_data + buf1_data;
                end
            end else begin
                out_valid <= 1'b0;
            end
        end
    end

endmodule
