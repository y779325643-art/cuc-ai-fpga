module skid_buffer #(parameter DATA_WIDTH = 0) (
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
    reg [DATA_WIDTH-1:0] buf_data;
    reg buf_valid;

    assign out_valid = buf_valid | in_valid;
    assign out_data  = buf_valid ? buf_data : in_data;
    assign in_ready  = (!buf_valid) || out_ready;

    always @(posedge clk) begin
      if (!rst_n) begin
        buf_valid <= 1'b0;
        buf_data  <= '0;
      end else begin
        if (out_ready && out_valid) begin
          if (buf_valid) buf_valid <= 1'b0;
        end
        if (in_valid && in_ready) begin
          if (!buf_valid) begin
            if (!out_ready) begin
              buf_data  <= in_data;
              buf_valid <= 1'b1;
            end
          end else begin
            buf_data  <= in_data;
            buf_valid <= 1'b1;
          end
        end
      end
    end
endmodule
