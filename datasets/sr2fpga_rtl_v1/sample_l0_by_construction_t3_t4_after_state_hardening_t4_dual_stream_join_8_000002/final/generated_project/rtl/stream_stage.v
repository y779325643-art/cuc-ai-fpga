module stream_stage #(parameter DATA_WIDTH = 8) (
    input wire in_valid,
    input wire [DATA_WIDTH-1:0] in_data,
    output wire in_ready,
    output wire out_valid,
    output wire [DATA_WIDTH-1:0] out_data,
    input wire out_ready
);
  module stream_stage #(parameter DATA_WIDTH = 8) (
      input wire clk,
      input wire rst_n,
      input wire in_valid,
      input wire [DATA_WIDTH-1:0] in_data,
      output wire in_ready,
      output wire out_valid,
      output wire [DATA_WIDTH-1:0] out_data,
      input wire out_ready
  );
    reg valid_r;
    reg [DATA_WIDTH-1:0] data_r;

    assign in_ready = !valid_r || out_ready;
    assign out_valid = valid_r;
    assign out_data = data_r;

    always @(posedge clk) begin
      if (!rst_n) begin
        valid_r <= 1'b0;
        data_r <= 0;
      end else begin
        if (in_valid && in_ready) begin
          data_r <= in_data;
          valid_r <= 1'b1;
        end
        if (out_ready && valid_r) begin
          valid_r <= 1'b0;
        end
      end
    end
  endmodule
endmodule
