module skid_buffer #(parameter DATA_WIDTH = 32) (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    input wire [DATA_WIDTH-1:0] in_data,
    output wire in_ready,
    output wire out_valid,
    output wire [DATA_WIDTH-1:0] out_data,
    input wire out_ready
);
  wire _unused_clock_reset = &{1'b0, clk, rst_n};
  // SR2FPGA_BEHAVIOR_BEGIN
    reg buffer_valid;
    reg [DATA_WIDTH-1:0] buffer_data;

    always @(posedge clk) begin
      if (!rst_n) begin
        buffer_valid <= 1'b0;
        buffer_data <= {DATA_WIDTH{1'b0}};
      end else begin
        if (out_ready && buffer_valid) begin
          buffer_valid <= 1'b0;
        end
        if (in_valid && !buffer_valid && in_ready) begin
          buffer_valid <= 1'b1;
          buffer_data <= in_data;
        end
      end
    end

    assign in_ready = !buffer_valid || out_ready;
    assign out_valid = in_valid || buffer_valid;
    assign out_data = buffer_valid ? buffer_data : in_data;
  // SR2FPGA_BEHAVIOR_END
endmodule
