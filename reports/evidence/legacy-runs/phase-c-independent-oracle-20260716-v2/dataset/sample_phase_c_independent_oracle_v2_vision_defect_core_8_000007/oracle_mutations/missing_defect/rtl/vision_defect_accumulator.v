module vision_defect_accumulator (
    input wire clk,
    input wire rst_n,
    input wire pixel_accept,
    input wire pixel_edge,
    input wire [15:0] pixel_x,
    input wire [15:0] pixel_y,
    input wire frame_end,
    output reg defect_present,
    output reg [15:0] first_defect_x,
    output reg [15:0] first_defect_y
);

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      defect_present <= 1'b0;
      first_defect_x <= 16'd0;
      first_defect_y <= 16'd0;
    end else if (frame_end) begin
      defect_present <= 1'b0;
      first_defect_x <= 16'd0;
      first_defect_y <= 16'd0;
    end else if (pixel_accept && pixel_edge && !defect_present && 1'b0) begin
      defect_present <= 1'b1;
      first_defect_x <= pixel_x;
      first_defect_y <= pixel_y;
    end
  end
endmodule
