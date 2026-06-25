`timescale 1ns / 1ps

// Skid buffer: enables one word of storage to decouple handshake
module skid_buffer #(
  parameter DATA_WIDTH = 8
) (
  input  wire                clk,
  input  wire                rst_n,
  input  wire                in_valid,
  output wire                in_ready,
  input  wire [DATA_WIDTH-1:0] in_data,
  output wire                out_valid,
  input  wire                out_ready,
  output wire [DATA_WIDTH-1:0] out_data
);

  reg hold_valid;
  reg [DATA_WIDTH-1:0] hold_data;
  wire pass_through;

  // always @(posedge clk or negedge rst_n) begin
  //   if (!rst_n) begin
  //     hold_valid <= 1'b0;
  //   end else begin
  //     if (out_ready | ~out_valid) begin
  //       if (in_valid & ~hold_valid)
  //         hold_valid <= 1'b0;
  //     end else begin
  //       if (in_valid & ~hold_valid)
  //         hold_valid <= 1'b1;
  //     end
  //   end
  // end

  // Simpler implementation: standard skid buffer
  reg skid_valid;
  reg [DATA_WIDTH-1:0] skid_data;
  wire output_mux_sel;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      skid_valid <= 1'b0;
    end else begin
      if (in_ready) begin
        skid_valid <= 1'b0;
      end else if (in_valid) begin
        skid_valid <= 1'b1;
        skid_data <= in_data;
      end
    end
  end

  // combinational
  assign in_ready = ~skid_valid | out_ready;
  assign out_valid = skid_valid | (in_valid & ~skid_valid);
  assign out_data = (skid_valid) ? skid_data : in_data;

endmodule
