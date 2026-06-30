module top (
    input wire clk,
    input wire rst_n,
    input wire feature_valid,
    output wire feature_ready,
    input wire [7:0] feature_data,
    input wire weight_valid,
    output wire weight_ready,
    input wire [7:0] weight_data,
    input wire [15:0] bias,
    output wire score_valid,
    input wire score_ready,
    output wire [15:0] score_data
);

  wire feature_buf_valid;
  wire feature_buf_ready;
  wire [7:0] feature_buf_data;
  wire weight_buf_valid;
  wire weight_buf_ready;
  wire [7:0] weight_buf_data;
  wire mac_score_valid;
  wire mac_score_ready;
  wire [15:0] mac_score_data;

  skid_buffer #(
    .WIDTH(8)
  ) u_feature_buffer (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(feature_valid),
    .in_ready(feature_ready),
    .in_data(feature_data),
    .out_valid(feature_buf_valid),
    .out_ready(feature_buf_ready),
    .out_data(feature_buf_data)
  );

  skid_buffer #(
    .WIDTH(8)
  ) u_weight_buffer (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(weight_valid),
    .in_ready(weight_ready),
    .in_data(weight_data),
    .out_valid(weight_buf_valid),
    .out_ready(weight_buf_ready),
    .out_data(weight_buf_data)
  );

  vector_mac_core #(
    .DATA_WIDTH(8),
    .SCORE_WIDTH(16),
    .VECTOR_LEN(4)
  ) u_vector_mac_core (
    .clk(clk),
    .rst_n(rst_n),
    .feature_valid(feature_buf_valid),
    .feature_ready(feature_buf_ready),
    .feature_data(feature_buf_data),
    .weight_valid(weight_buf_valid),
    .weight_ready(weight_buf_ready),
    .weight_data(weight_buf_data),
    .bias(bias),
    .score_valid(mac_score_valid),
    .score_ready(mac_score_ready),
    .score_data(mac_score_data)
  );

  stream_stage #(
    .WIDTH(16)
  ) u_score_stage (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(mac_score_valid),
    .in_ready(mac_score_ready),
    .in_data(mac_score_data),
    .out_valid(score_valid),
    .out_ready(score_ready),
    .out_data(score_data)
  );

endmodule
