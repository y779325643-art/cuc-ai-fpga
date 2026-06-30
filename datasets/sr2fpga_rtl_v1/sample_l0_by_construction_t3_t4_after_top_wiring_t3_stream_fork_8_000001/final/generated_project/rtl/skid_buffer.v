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
    reg [1:0] skid_items;
    reg [1:0] wr_ptr, rd_ptr;
    reg [DATA_WIDTH-1:0] buf [0:1];

    wire in_handshake;
    wire out_handshake;
    assign in_handshake = in_valid && in_ready;
    assign out_handshake = out_valid && out_ready;

    assign in_ready = (skid_items < 2) || (skid_items == 2 && out_ready);
    assign out_valid = (skid_items > 0);
    assign out_data = buf[rd_ptr];

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        skid_items <= 2'd0;
        wr_ptr <= 1'b0;
        rd_ptr <= 1'b0;
      end else begin
        if (in_handshake && !out_handshake) begin
          buf[wr_ptr] <= in_data;
          wr_ptr <= wr_ptr + 1;
          skid_items <= skid_items + 2'd1;
        end else if (!in_handshake && out_handshake) begin
          rd_ptr <= rd_ptr + 1;
          skid_items <= skid_items - 2'd1;
        end else if (in_handshake && out_handshake) begin
          buf[wr_ptr] <= in_data;
          wr_ptr <= wr_ptr + 1;
          rd_ptr <= rd_ptr + 1;
        end
      end
    end
endmodule
