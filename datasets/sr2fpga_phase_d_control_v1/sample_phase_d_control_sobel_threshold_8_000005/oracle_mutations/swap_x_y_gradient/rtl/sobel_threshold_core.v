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

  assign abs_gx = gy[10] ? -gy : gy;
  assign abs_gy = gx[10] ? -gx : gx;
  assign magnitude = abs_gx + abs_gy;
  assign out_edge = magnitude >= THRESHOLD;
  // edge_axis=1 is horizontal-gradient dominance: abs(Gx) >= abs(Gy).
  assign edge_axis = abs_gx >= abs_gy;
endmodule
