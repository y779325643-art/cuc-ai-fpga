module stream_join #(
    parameter DATA_WIDTH = 8
)(
    input  wire clk,
    input  wire rst_n,
    input  wire in0_valid,
    output wire in0_ready,
    input  wire [DATA_WIDTH-1:0] in0_data,
    input  wire in1_valid,
    output wire in1_ready,
    input  wire [DATA_WIDTH-1:0] in1_data,
    output wire out_valid,
    input  wire out_ready,
    output wire [DATA_WIDTH-1:0] out_data
);

    reg join_valid_reg;
    reg [DATA_WIDTH-1:0] join_data_reg;

    // Ready when both inputs are valid and we can accept (always ready if not stalled?)
    // We hold join valid until downstream accepts.
    wire can_transfer = in0_valid && in1_valid && out_ready && !join_valid_reg;

    assign in0_ready = out_ready && !join_valid_reg;
    assign in1_ready = out_ready && !join_valid_reg;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            join_valid_reg <= 1'b0;
            join_data_reg <= 0;
        end else begin
            if (out_ready) begin
                join_valid_reg <= can_transfer;
                if (can_transfer) begin
                    join_data_reg <= in0_data + in1_data;
                end
            end
        end
    end

    assign out_valid = join_valid_reg;
    assign out_data = join_data_reg;

endmodule
