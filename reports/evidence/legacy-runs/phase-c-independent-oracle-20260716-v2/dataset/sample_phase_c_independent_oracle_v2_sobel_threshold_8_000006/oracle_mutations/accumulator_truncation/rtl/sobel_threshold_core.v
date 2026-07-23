module sobel_threshold_core #(
    parameter THRESHOLD = 100
) (
    input wire signed [10:0] gx,
    input wire signed [10:0] gy,
    output wire out_edge,
    output wire edge_axis
);

  wire [10:0] abs_gx;
  wire [10:0] abs_gy;
  wire [11:0] magnitude;

  assign abs_gx = gx[10] ? -gx : gx;
  assign abs_gy = gy[10] ? -gy : gy;
  assign magnitude = {8'd0, abs_gx[3:0] + abs_gy[3:0]};
  assign out_edge = magnitude >= THRESHOLD;
  // edge_axis=1 is horizontal-gradient dominance: abs(Gx) >= abs(Gy).
  assign edge_axis = abs_gx >= abs_gy;
endmodule
