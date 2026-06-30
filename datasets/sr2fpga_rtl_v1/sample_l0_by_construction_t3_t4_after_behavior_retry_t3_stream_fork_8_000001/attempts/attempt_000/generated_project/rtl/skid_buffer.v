module skid_buffer #(parameter DATA_WIDTH = 8) (
    input wire clk,
    input wire rst_n,
    input wire [DATA_WIDTH-1:0] in_data,
    input wire in_valid,
    output wire in_ready,
    output wire [DATA_WIDTH-1:0] out_data,
    output wire out_valid,
    input wire out_ready
);
      reg [DATA_WIDTH-1:0] mem [0:1];
      reg wr_ptr, rd_ptr;
      reg [1:0] count;

      assign in_ready = (count < 2'd2);
      assign out_valid = (count > 0);
      assign out_data = mem[rd_ptr];

      always @(posedge clk or negedge rst_n) begin
          if (!rst_n) begin
              wr_ptr <= 0;
              rd_ptr <= 0;
              count <= 0;
          end else begin
              if (in_valid && in_ready) begin
                  mem[wr_ptr] <= in_data;
                  wr_ptr <= wr_ptr + 1'b1;
                  count <= count + 1;
              end
              if (out_valid && out_ready) begin
                  rd_ptr <= rd_ptr + 1'b1;
                  count <= count - 1;
              end
          end
      end
endmodule
