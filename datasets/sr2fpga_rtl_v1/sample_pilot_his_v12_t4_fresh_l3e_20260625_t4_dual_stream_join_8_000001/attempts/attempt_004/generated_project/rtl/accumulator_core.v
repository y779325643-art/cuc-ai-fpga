module accumulator_core #(
    parameter DATA_WIDTH = 8
) (
    input  wire                 clk,
    input  wire                 reset_n,
    input  wire                 in_valid,
    output reg                  in_ready,
    input  wire [DATA_WIDTH-1:0] in_data,
    output reg                  out_valid,
    input  wire                 out_ready,
    output reg [DATA_WIDTH-1:0] out_data
);

    reg [DATA_WIDTH-1:0] acc_reg;

    always @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            in_ready <= 1'b0;
            out_valid <= 1'b0;
            out_data <= {DATA_WIDTH{1'b0}};
            acc_reg <= {DATA_WIDTH{1'b0}};
        end else begin
            in_ready <= !out_valid || out_ready;
            out_valid <= 1'b1;  // always ready to output
            out_data <= acc_reg;
            if (in_valid && in_ready) begin
                acc_reg <= acc_reg + in_data;
            end
        end
    end

endmodule
