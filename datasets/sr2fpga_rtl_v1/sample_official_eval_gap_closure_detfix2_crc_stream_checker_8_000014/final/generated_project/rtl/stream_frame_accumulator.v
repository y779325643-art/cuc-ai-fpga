module stream_frame_accumulator (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    output wire in_ready,
    input wire frame_end,
    input wire out_ready,
    input wire [7:0] crc_next,
    output reg [7:0] crc_state,
    output reg frame_done,
    output reg [7:0] frame_crc
);

  wire accept;

  assign in_ready = !frame_done || out_ready;
  assign accept = in_valid && in_ready;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      crc_state <= 8'h00;
      frame_done <= 1'b0;
      frame_crc <= 8'h00;
    end else begin
      if (frame_done && out_ready) begin
        frame_done <= 1'b0;
      end
      if (accept) begin
        crc_state <= crc_next;
        if (frame_end) begin
          frame_done <= 1'b1;
          frame_crc <= crc_next;
        end
      end
    end
  end

endmodule
