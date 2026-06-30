module top (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    output wire in_ready,
    input wire [7:0] in_data,
    input wire frame_start,
    input wire frame_end,
    input wire [7:0] expected_crc,
    output wire out_valid,
    input wire out_ready,
    output wire [7:0] crc_value,
    output wire crc_match
);

  wire [7:0] crc_state;
  wire [7:0] crc_base;
  wire [7:0] crc_next;
  wire [7:0] frame_crc;
  wire frame_done;

  assign crc_base = frame_start ? 8'h00 : crc_state;

  crc8_update u_crc8_update (
    .crc_in(crc_base),
    .data_in(in_data[7:0]),
    .crc_out(crc_next)
  );

  stream_frame_accumulator u_stream_frame_accumulator (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(in_valid),
    .in_ready(in_ready),
    .frame_end(frame_end),
    .out_ready(out_ready),
    .crc_next(crc_next),
    .crc_state(crc_state),
    .frame_done(frame_done),
    .frame_crc(frame_crc)
  );

  crc_status u_crc_status (
    .clk(clk),
    .rst_n(rst_n),
    .frame_done(frame_done),
    .out_ready(out_ready),
    .frame_crc(frame_crc),
    .expected_crc(expected_crc),
    .out_valid(out_valid),
    .crc_value(crc_value),
    .crc_match(crc_match)
  );

endmodule
