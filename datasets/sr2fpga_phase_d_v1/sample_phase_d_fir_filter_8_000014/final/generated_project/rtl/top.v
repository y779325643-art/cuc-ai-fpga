module top #(parameter DATA_WIDTH = 8, parameter COEFF_WIDTH = 8, parameter TAP_COUNT = 4, parameter ACC_WIDTH = 18, parameter COEFF_0 = 1, parameter COEFF_1 = 2, parameter COEFF_2 = 2, parameter COEFF_3 = 1) (
    input wire clk,
    input wire rst_n,
    input wire s_axis_valid,
    output wire s_axis_ready,
    input wire [DATA_WIDTH-1:0] s_axis_data,
    output wire m_axis_valid,
    input wire m_axis_ready,
    output wire [DATA_WIDTH-1:0] m_axis_data
);

  wire u_fir_core__sample_in_valid;
  wire u_fir_core__sample_in_ready;
  wire [DATA_WIDTH-1:0] u_fir_core__sample_in_data;
  wire u_fir_core__sample_out_valid;
  wire u_fir_core__sample_out_ready;
  wire [DATA_WIDTH-1:0] u_fir_core__sample_out_data;

  assign u_fir_core__sample_in_data = s_axis_data;
  assign u_fir_core__sample_in_valid = s_axis_valid;
  assign s_axis_ready = u_fir_core__sample_in_ready;
  assign m_axis_data = u_fir_core__sample_out_data;
  assign m_axis_valid = u_fir_core__sample_out_valid;
  assign u_fir_core__sample_out_ready = m_axis_ready;

  fir_core #(.DATA_WIDTH(DATA_WIDTH), .COEFF_WIDTH(COEFF_WIDTH), .TAP_COUNT(TAP_COUNT), .ACC_WIDTH(ACC_WIDTH), .COEFF_0(COEFF_0), .COEFF_1(COEFF_1), .COEFF_2(COEFF_2), .COEFF_3(COEFF_3)) u_fir_core (
    .clk(clk),
    .rst_n(rst_n),
    .sample_in_valid(u_fir_core__sample_in_valid),
    .sample_in_ready(u_fir_core__sample_in_ready),
    .sample_in_data(u_fir_core__sample_in_data),
    .sample_out_valid(u_fir_core__sample_out_valid),
    .sample_out_ready(u_fir_core__sample_out_ready),
    .sample_out_data(u_fir_core__sample_out_data)
  );

endmodule
