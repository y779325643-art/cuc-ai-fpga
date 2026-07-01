module skid_buffer #(
    parameter WIDTH = 8
) (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    output wire in_ready,
    input wire [WIDTH-1:0] in_data,
    output wire out_valid,
    input wire out_ready,
    output wire [WIDTH-1:0] out_data
);

  reg valid_r;
  reg [WIDTH-1:0] data_r;

  assign in_ready = !valid_r || out_ready;
  assign out_valid = valid_r;
  assign out_data = data_r;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      valid_r <= 1'b0;
      data_r <= {WIDTH{1'b0}};
    end else if (in_ready) begin
      valid_r <= in_valid;
      if (in_valid) begin
        data_r <= in_data;
      end
    end
  end

endmodule
