module top #(parameter DATA_WIDTH = 8, parameter COEFF_WIDTH = 8, parameter NUM_TAPS = 3, parameter OUTPUT_WIDTH = 8, parameter DEPTH = 3) (
    input wire clk,
    input wire rst_n,
    input wire s_axis_tvalid,
    output wire s_axis_tready,
    input wire [DATA_WIDTH-1:0] s_axis_tdata,
    output wire m_axis_tvalid,
    input wire m_axis_tready,
    output wire [OUTPUT_WIDTH-1:0] m_axis_tdata
);

  wire u_shift__shift_en;
  wire [DATA_WIDTH-1:0] u_shift__data_in;
  wire [DATA_WIDTH-1:0] u_shift__tap_0;
  wire [DATA_WIDTH-1:0] u_shift__tap_1;
  wire [DATA_WIDTH-1:0] u_shift__tap_2;
  wire [COEFF_WIDTH-1:0] u_coeff_rom__coeff_0;
  wire [COEFF_WIDTH-1:0] u_coeff_rom__coeff_1;
  wire [COEFF_WIDTH-1:0] u_coeff_rom__coeff_2;
  wire [DATA_WIDTH-1:0] u_mac__data_0;
  wire [DATA_WIDTH-1:0] u_mac__data_1;
  wire [DATA_WIDTH-1:0] u_mac__data_2;
  wire [COEFF_WIDTH-1:0] u_mac__coeff_0;
  wire [COEFF_WIDTH-1:0] u_mac__coeff_1;
  wire [COEFF_WIDTH-1:0] u_mac__coeff_2;
  wire [OUTPUT_WIDTH-1:0] u_mac__result;
  wire u_out_reg__s_axis_tvalid;
  wire u_out_reg__s_axis_tready;
  wire [DATA_WIDTH-1:0] u_out_reg__s_axis_tdata;
  wire u_out_reg__m_axis_tvalid;
  wire u_out_reg__m_axis_tready;
  wire [DATA_WIDTH-1:0] u_out_reg__m_axis_tdata;

  assign u_shift__data_in = s_axis_tdata;
  assign u_mac__data_0 = u_shift__tap_0;
  assign u_out_reg__s_axis_tdata = u_mac__result;
  assign m_axis_tdata = u_out_reg__m_axis_tdata;
  assign u_mac__coeff_0 = u_coeff_rom__coeff_0;
  assign u_mac__coeff_1 = u_coeff_rom__coeff_1;
  assign u_mac__coeff_2 = u_coeff_rom__coeff_2;

  shift_register #(.DATA_WIDTH(DATA_WIDTH), .DEPTH(DEPTH)) u_shift (
    .clk(clk),
    .rst_n(rst_n),
    .shift_en(u_shift__shift_en),
    .data_in(u_shift__data_in),
    .tap_0(u_shift__tap_0),
    .tap_1(u_shift__tap_1),
    .tap_2(u_shift__tap_2)
  );

  coefficient_rom #(.COEFF_WIDTH(COEFF_WIDTH), .NUM_TAPS(NUM_TAPS)) u_coeff_rom (
    .clk(clk),
    .rst_n(rst_n),
    .coeff_0(u_coeff_rom__coeff_0),
    .coeff_1(u_coeff_rom__coeff_1),
    .coeff_2(u_coeff_rom__coeff_2)
  );

  multiply_add_tree #(.DATA_WIDTH(DATA_WIDTH), .COEFF_WIDTH(COEFF_WIDTH), .NUM_TAPS(NUM_TAPS), .OUTPUT_WIDTH(OUTPUT_WIDTH)) u_mac (
    .clk(clk),
    .rst_n(rst_n),
    .data_0(u_mac__data_0),
    .data_1(u_mac__data_1),
    .data_2(u_mac__data_2),
    .coeff_0(u_mac__coeff_0),
    .coeff_1(u_mac__coeff_1),
    .coeff_2(u_mac__coeff_2),
    .result(u_mac__result)
  );

  pipeline_register #(.DATA_WIDTH(DATA_WIDTH)) u_out_reg (
    .clk(clk),
    .rst_n(rst_n),
    .s_axis_tvalid(u_out_reg__s_axis_tvalid),
    .s_axis_tready(u_out_reg__s_axis_tready),
    .s_axis_tdata(u_out_reg__s_axis_tdata),
    .m_axis_tvalid(u_out_reg__m_axis_tvalid),
    .m_axis_tready(u_out_reg__m_axis_tready),
    .m_axis_tdata(u_out_reg__m_axis_tdata)
  );

endmodule
