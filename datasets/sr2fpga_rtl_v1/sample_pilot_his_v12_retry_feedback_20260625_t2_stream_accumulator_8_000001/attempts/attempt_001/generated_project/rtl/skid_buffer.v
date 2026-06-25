`timescale 1ns / 1ps
module skid_buffer (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        in_valid,
    output wire        in_ready,
    input  wire [7:0]  in_data,
    output wire        out_valid,
    input  wire        out_ready,
    output wire [7:0]  out_data
);
    parameter DATA_WIDTH = 8;
    reg [DATA_WIDTH-1:0] buf0_data, buf1_data;
    reg buf0_valid, buf1_valid;
    wire [1:0] count = buf0_valid + buf1_valid;
    assign in_ready = (count < 2);
    assign out_valid = buf0_valid | buf1_valid;
    assign out_data = buf0_valid ? buf0_data : buf1_data;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            buf0_valid <= 1'b0;
            buf1_valid <= 1'b0;
            buf0_data <= {DATA_WIDTH{1'b0}};
            buf1_data <= {DATA_WIDTH{1'b0}};
        end else begin
            if (out_valid && out_ready) begin
                if (buf0_valid) begin
                    buf0_valid <= 1'b0;
                    if (buf1_valid) begin
                        buf0_data <= buf1_data;
                        buf0_valid <= 1'b1;
                        buf1_valid <= 1'b0;
                    end
                end else begin
                    buf1_valid <= 1'b0;
                end
            end
            if (in_valid && in_ready) begin
                if (!buf0_valid) begin
                    buf0_data <= in_data;
                    buf0_valid <= 1'b1;
                end else if (!buf1_valid) begin
                    buf1_data <= in_data;
                    buf1_valid <= 1'b1;
                end
            end
        end
    end
endmodule
