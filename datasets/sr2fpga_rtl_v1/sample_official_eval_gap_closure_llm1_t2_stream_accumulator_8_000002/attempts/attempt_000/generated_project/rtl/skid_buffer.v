module skid_buffer #(parameter DATA_WIDTH = 8) (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    input wire [DATA_WIDTH-1:0] in_data,
    output wire in_ready,
    output wire out_valid,
    output wire [DATA_WIDTH-1:0] out_data,
    input wire out_ready
);
  wire _unused_clock_reset = &{1'b0, clk, rst_n};
    reg [DATA_WIDTH-1:0] fifo_mem [0:1];
    reg [0:0] write_ptr;
    reg [0:0] read_ptr;
    reg [1:0] count;
    assign out_valid = (count > 0);
    assign in_ready = (count < 2);
    assign out_data = fifo_mem[read_ptr];
    wire wr_en = in_valid && in_ready;
    wire rd_en = out_valid && out_ready;
    always @(posedge clk) begin
      if (!rst_n) begin
        write_ptr <= 1'b0;
        read_ptr <= 1'b0;
        count <= 2'd0;
      end else begin
        if (wr_en) begin
          fifo_mem[write_ptr] <= in_data;
          write_ptr <= write_ptr + 1'b1;
        end
        if (rd_en) begin
          read_ptr <= read_ptr + 1'b1;
        end
        if (wr_en && !rd_en)
          count <= count + 2'd1;
        else if (!wr_en && rd_en)
          count <= count - 2'd1;
      end
    end
endmodule
