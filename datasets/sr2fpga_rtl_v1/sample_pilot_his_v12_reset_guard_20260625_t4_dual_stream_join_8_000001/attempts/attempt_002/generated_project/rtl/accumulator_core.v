module accumulator_core #(
   parameter DATA_WIDTH = 8
)(
   input  wire                     clk,
   input  wire                     rst_n,
   // Input stream
   input  wire                     in_valid,
   output reg                      in_ready,
   input  wire [DATA_WIDTH-1:0]    in_data,
   // Output stream
   output reg                      out_valid,
   input  wire                     out_ready,
   output reg [DATA_WIDTH-1:0]     out_data
);

   reg [DATA_WIDTH-1:0] acc_reg;

   // in_ready: accept if output is not valid or output ready
   assign in_ready = out_ready | ~out_valid;

   always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
         acc_reg <= 0;
         out_valid <= 0;
         out_data <= 0;
      end else begin
         if (in_valid & in_ready) begin
            acc_reg <= acc_reg + in_data;
            out_data <= acc_reg + in_data;
            out_valid <= 1;
         end else if (out_ready) begin
            out_valid <= 0;
         end
      end
   end

endmodule
