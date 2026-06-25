module skid_buffer #(
   parameter DATA_WIDTH = 8
)(
   input  wire                     clk,
   input  wire                     rst_n,
   // input stream
   input  wire                     in_valid,
   output reg                      in_ready,
   input  wire [DATA_WIDTH-1:0]    in_data,
   // output stream
   output reg                      out_valid,
   input  wire                     out_ready,
   output reg [DATA_WIDTH-1:0]     out_data
);

   reg [DATA_WIDTH-1:0] skid_data;
   reg skid_valid;

   // in_ready is high when we can accept new data: either out_valid is low or out_ready is high or skid is free
   assign in_ready = ~(out_valid & ~out_ready & skid_valid);

   always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
         out_valid <= 0;
         skid_valid <= 0;
      end else begin
         if (in_valid & in_ready) begin
            if (out_valid & ~out_ready) begin
               // output busy, store in skid
               skid_data <= in_data;
               skid_valid <= 1;
            end else begin
               // output free, pass through
               out_data <= in_data;
               out_valid <= 1;
            end
         end
         if (out_ready) begin
            if (skid_valid) begin
               out_data <= skid_data;
               out_valid <= 1;
               skid_valid <= 0;
            end else begin
               out_valid <= 0;
            end
         end
      end
   end

endmodule
