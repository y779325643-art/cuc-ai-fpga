module stream_join #(
   parameter DATA_WIDTH = 8
)(
   input  wire                     clk,
   input  wire                     rst_n,
   // Input stream 0
   input  wire                     in0_valid,
   output reg                      in0_ready,
   input  wire [DATA_WIDTH-1:0]    in0_data,
   // Input stream 1
   input  wire                     in1_valid,
   output reg                      in1_ready,
   input  wire [DATA_WIDTH-1:0]    in1_data,
   // Output stream
   output reg                      out_valid,
   input  wire                     out_ready,
   output reg [DATA_WIDTH-1:0]     out_data
);

   always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
         out_valid <= 0;
      end else begin
         if (out_ready) begin
            if (in0_valid & in1_valid) begin
               out_valid <= 1;
               out_data <= in0_data + in1_data;
            end else begin
               out_valid <= 0;
            end
         end
         // else hold
      end
   end

   assign in0_ready = out_ready & in1_valid;
   assign in1_ready = out_ready & in0_valid;

endmodule
