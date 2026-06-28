module skid_buffer #(parameter DATA_WIDTH = 8) (
    input wire [None-1:0] clk,
    input wire [None-1:0] rst_n,
    input wire [None-1:0] in_valid,
    input wire [DATA_WIDTH-1:0] in_data,
    output wire [None-1:0] in_ready,
    input wire [None-1:0] out_ready,
    output wire [None-1:0] out_valid,
    output wire [DATA_WIDTH-1:0] out_data
);
  module skid_buffer #(parameter DATA_WIDTH = 8) (
      input wire [None-1:0] clk,
      input wire [None-1:0] rst_n,
      input wire [None-1:0] in_valid,
      input wire [DATA_WIDTH-1:0] in_data,
      output wire [None-1:0] in_ready,
      input wire [None-1:0] out_ready,
      output wire [None-1:0] out_valid,
      output wire [DATA_WIDTH-1:0] out_data
  );
     reg buf_valid;
     reg [DATA_WIDTH-1:0] buf_data;

     assign out_data = (buf_valid) ? buf_data : in_data;
     assign out_valid = in_valid || buf_valid;
     assign in_ready = !buf_valid || out_ready;

     always @(posedge clk or negedge rst_n) begin
         if (!rst_n) begin
             buf_valid <= 1'b0;
         end else begin
             if (!buf_valid && in_valid && !out_ready) begin
                 buf_valid <= 1'b1;
                 buf_data <= in_data;
             end else if (out_ready) begin
                 buf_valid <= 1'b0;
             end
         end
     end
  endmodule
endmodule
