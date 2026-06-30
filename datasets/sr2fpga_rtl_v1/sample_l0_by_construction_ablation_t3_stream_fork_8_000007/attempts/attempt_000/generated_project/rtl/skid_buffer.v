module skid_buffer (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    input wire [DATA_WIDTH-1:0] in_data,
    output wire in_ready,
    output wire out_valid,
    output wire [DATA_WIDTH-1:0] out_data,
    input wire out_ready
);
    reg out_valid_r;
    reg out_valid_buf;
    reg [DATA_WIDTH-1:0] out_data_r;
    reg [DATA_WIDTH-1:0] out_data_buf;

    assign in_ready = !out_valid_buf;
    assign out_valid = out_valid_r;
    assign out_data   = out_data_r;

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        out_valid_r   <= 1'b0;
        out_valid_buf <= 1'b0;
      end else begin
        // output handshake
        if (out_ready && out_valid_r) begin
          if (out_valid_buf) begin
            out_valid_r <= 1'b1;
            out_data_r  <= out_data_buf;
            out_valid_buf <= 1'b0;
          end else begin
            out_valid_r <= 1'b0;
          end
        end
        // input handshake
        if (in_valid && in_ready) begin
          if (!out_valid_r) begin
            out_valid_r <= 1'b1;
            out_data_r  <= in_data;
          end else begin
            out_valid_buf <= 1'b1;
            out_data_buf  <= in_data;
          end
        end
      end
    end
endmodule
