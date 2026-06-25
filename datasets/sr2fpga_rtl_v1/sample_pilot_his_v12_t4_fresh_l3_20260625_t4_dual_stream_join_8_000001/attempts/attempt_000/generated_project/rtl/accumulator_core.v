// accumulator_core: accumulates input values, outputs running sum
// When valid_in and ready_in are high, adds data_in to accumulator and outputs result

module accumulator_core #(
    parameter DATA_WIDTH = 8
) (
    input  wire                    clk,
    input  wire                    rst_n,
    input  wire [DATA_WIDTH-1:0]   data_in,
    input  wire                    valid_in,
    output wire                    ready_out,
    output wire [DATA_WIDTH-1:0]   data_out,
    output wire                    valid_out,
    input  wire                    ready_in
);

    reg [DATA_WIDTH-1:0] acc_reg;
    reg                  acc_valid;

    wire fire = valid_in & ready_out;
    wire transfer_out = acc_valid & ready_in;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            acc_reg   <= {DATA_WIDTH{1'b0}};
            acc_valid <= 1'b0;
        end else if (fire) begin
            acc_reg   <= acc_reg + data_in;
            acc_valid <= 1'b1;
        end else if (transfer_out) begin
            acc_valid <= 1'b0;
        end
    end

    assign ready_out = ~acc_valid | transfer_out;
    assign data_out  = acc_reg;
    assign valid_out = acc_valid;

endmodule
