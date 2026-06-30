module accumulator_core #(parameter DATA_WIDTH = 8) (
    input wire clk,
    input wire rst_n,
    input wire sample_valid_in,
    output wire sample_ready_out,
    input wire [DATA_WIDTH-1:0] sample,
    output wire [DATA_WIDTH-1:0] sum,
    output wire sample_valid_out
);
  wire _unused_clock_reset = &{1'b0, clk, rst_n};
    // Treat sample_ready_out as downstream ready input (not driven here)
    wire downstream_ready = sample_ready_out;
    reg [DATA_WIDTH-1:0] sum_r;
    reg valid_r;
    wire input_fire = sample_valid_in && (downstream_ready || !valid_r);

    assign sum = sum_r;

    always @(posedge clk) begin
      if (!rst_n) begin
        sum_r <= 0;
        valid_r <= 0;
      end else begin
        if (input_fire) begin
          sum_r <= sum_r + sample;
          valid_r <= 1'b1;
        end else if (valid_r && downstream_ready) begin
          valid_r <= 1'b0;
        end
      end
    end

    assign sample_valid_out = valid_r;
endmodule
