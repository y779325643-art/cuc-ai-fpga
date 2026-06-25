module skid_buffer #(
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

    reg skid_valid;
    reg [DATA_WIDTH-1:0] skid_data;

    assign ready_in = !skid_valid || ready_out;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            skid_valid <= 1'b0;
        end else begin
            if (valid_in && ready_in) begin
                skid_data <= data_in;
                skid_valid <= 1'b1;
            end else if (ready_out && skid_valid) begin
                skid_valid <= 1'b0;
            end
        end
    end

    assign valid_out = skid_valid;
    assign data_out = skid_data;

endmodule
