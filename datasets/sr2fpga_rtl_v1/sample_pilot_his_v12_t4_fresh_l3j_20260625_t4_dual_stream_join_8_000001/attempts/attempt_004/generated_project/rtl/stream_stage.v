module stream_stage #(
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

    reg valid_reg;
    reg [DATA_WIDTH-1:0] data_reg;

    assign ready_in = !valid_reg || ready_out;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            valid_reg <= 1'b0;
        end else begin
            if (ready_in) begin
                if (valid_in) begin
                    valid_reg <= 1'b1;
                    data_reg <= data_in;
                end else begin
                    valid_reg <= 1'b0;
                end
            end else begin
                // stalled: keep current state
            end
        end
    end

    assign valid_out = valid_reg;
    assign data_out = data_reg;

endmodule
