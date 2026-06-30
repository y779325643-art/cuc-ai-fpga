module stream_stage #(parameter DATA_WIDTH = 8) (
    input wire [None-1:0] clk,
    input wire [None-1:0] rst_n,
    input wire [None-1:0] in_valid,
    input wire [DATA_WIDTH-1:0] in_data,
    output wire [None-1:0] in_ready,
    input wire [None-1:0] out_ready,
    output wire [None-1:0] out_valid,
    output wire [DATA_WIDTH-1:0] out_data
);
  module stream_stage #(parameter DATA_WIDTH = 8) (
      input wire [None-1:0] clk,
      input wire [None-1:0] rst_n,
      input wire [None-1:0] in_valid,
      input wire [DATA_WIDTH-1:0] in_data,
      output wire [None-1:0] in_ready,
      input wire [None-1:0] out_ready,
      output wire [None-1:0] out_valid,
      output wire [DATA_WIDTH-1:0] out_data
  );
     reg valid_reg;
     reg [DATA_WIDTH-1:0] data_reg;

     assign out_valid = valid_reg;
     assign out_data = data_reg;
     assign in_ready = !valid_reg || out_ready;

     always @(posedge clk or negedge rst_n) begin
         if (!rst_n) begin
             valid_reg <= 1'b0;
         end else begin
             if (in_ready) begin
                 valid_reg <= in_valid;
                 if (in_valid) begin
                     data_reg <= in_data;
                 end
             end
         end
     end
  endmodule
endmodule
