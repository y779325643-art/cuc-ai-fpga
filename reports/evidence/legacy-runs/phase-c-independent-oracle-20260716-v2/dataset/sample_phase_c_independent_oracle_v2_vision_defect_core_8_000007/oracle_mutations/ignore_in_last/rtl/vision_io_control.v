module vision_io_control (
    input wire clk,
    input wire rst_n,
    input wire frame_report_accept,
    input wire defect_present,
    input wire [15:0] first_defect_x,
    input wire [15:0] first_defect_y,
    output reg reported_defect_present,
    output reg [15:0] reported_first_defect_x,
    output reg [15:0] reported_first_defect_y
);

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      reported_defect_present <= 1'b0;
      reported_first_defect_x <= 16'd0;
      reported_first_defect_y <= 16'd0;
    end else if (frame_report_accept) begin
      reported_defect_present <= defect_present;
      reported_first_defect_x <= first_defect_x;
      reported_first_defect_y <= first_defect_y;
    end
  end
endmodule
