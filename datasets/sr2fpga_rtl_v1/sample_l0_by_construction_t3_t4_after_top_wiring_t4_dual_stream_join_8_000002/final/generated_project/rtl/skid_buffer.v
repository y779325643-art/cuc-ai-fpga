module skid_buffer #(parameter DATA_WIDTH = 8) (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    output wire in_ready,
    input wire [DATA_WIDTH-1:0] in_data,
    output wire out_valid,
    input wire out_ready,
    output wire [DATA_WIDTH-1:0] out_data
);
  wire _unused_clock_reset = &{1'b0, clk, rst_n};
    reg buf_valid;
    reg [DATA_WIDTH-1:0] buf_data;

    assign in_ready = !buf_valid;
    assign out_valid = buf_valid;
    assign out_data = buf_data;

    always @(posedge clk) begin
        if (!rst_n) begin
            buf_valid <= 1'b0;
            buf_data <= {DATA_WIDTH{1'b0}};
        end else begin
            if (in_valid && in_ready) begin
                buf_valid <= 1'b1;
                buf_data <= in_data;
            end
            else if (out_valid && out_ready) begin
                buf_valid <= 1'b0;
            end
        end
    end
endmodule
