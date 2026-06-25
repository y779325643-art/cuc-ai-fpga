module accumulator_core #(
    parameter DATA_WIDTH = 8
)(
    input  wire clk,
    input  wire rst_n,
    input  wire valid_in,
    output wire ready_in,
    input  wire [DATA_WIDTH-1:0] data_in,
    output wire valid_out,
    input  wire ready_out,
    output wire [DATA_WIDTH-1:0] data_out
);

    reg [DATA_WIDTH-1:0] accumulator_reg;
    reg acc_valid_reg;

    assign ready_in = !acc_valid_reg || ready_out; // ready when not full or downstream ready

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            accumulator_reg <= 0;
            acc_valid_reg <= 1'b0;
        end else begin
            if (valid_in && ready_in) begin
                accumulator_reg <= accumulator_reg + data_in;
                acc_valid_reg <= 1'b1;
            end else if (acc_valid_reg && ready_out) begin
                // output transferred, clear valid if no new data
                // Actually we need to track when new data arrives while outputting
                // Simpler: hold valid until transferred
                if (!valid_in || !ready_in) begin
                    acc_valid_reg <= 1'b0;
                end
            end
        end
    end

    assign valid_out = acc_valid_reg;
    assign data_out = accumulator_reg;

endmodule
