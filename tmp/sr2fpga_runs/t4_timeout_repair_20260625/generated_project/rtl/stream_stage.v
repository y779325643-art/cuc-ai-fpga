module stream_stage #(
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

   // in_ready: accept if we are not holding a valid output or downstream is ready
   assign in_ready = out_ready | ~out_valid;

   always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
         out_valid <= 0;
      end else begin
         if (in_ready) begin
            if (in_valid) begin
               out_valid <= 1;
               out_data <= in_data;
            end else begin
               out_valid <= 0;
            end
         end
      end
   end

endmodule
