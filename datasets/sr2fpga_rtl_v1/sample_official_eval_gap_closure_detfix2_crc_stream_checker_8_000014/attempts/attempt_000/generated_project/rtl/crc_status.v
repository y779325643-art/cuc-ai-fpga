module crc_status (
    input wire clk,
    input wire rst_n,
    input wire frame_done,
    input wire out_ready,
    input wire [7:0] frame_crc,
    input wire [7:0] expected_crc,
    output reg out_valid,
    output reg [7:0] crc_value,
    output reg crc_match
);

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      out_valid <= 1'b0;
      crc_value <= 8'h00;
      crc_match <= 1'b0;
    end else if (frame_done) begin
      out_valid <= 1'b1;
      crc_value <= frame_crc;
      crc_match <= (frame_crc == expected_crc);
    end else if (out_valid && out_ready) begin
      out_valid <= 1'b0;
    end
  end

endmodule
