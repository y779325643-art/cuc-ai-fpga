`timescale 1ns / 1ps
module accumulator_core #(parameter NUM_SAMPLES = 4, parameter WIDTH = 16) (
  input clk,
  input rst_n,
  input sample_valid,
  input [WIDTH-1:0] sample,
  output sample_ready,
  output sum_valid,
  output [WIDTH-1:0] sum,
  input sum_ready
);

  localparam IDLE   = 2'd0;
  localparam ACCUM  = 2'd1;
  localparam OUTPUT = 2'd2;

  reg [1:0] state;
  reg [WIDTH-1:0] sum_reg;
  reg [$clog2(NUM_SAMPLES):0] count;
  reg sum_valid_r;

  assign sample_ready = (state == IDLE) || (state == ACCUM && count < NUM_SAMPLES);
  assign sum_valid = sum_valid_r;
  assign sum = sum_reg;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state <= IDLE;
      sum_reg <= 0;
      count <= 0;
      sum_valid_r <= 0;
    end else begin
      case (state)
        IDLE: begin
          sum_valid_r <= 0;
          if (sample_valid && sample_ready) begin
            sum_reg <= sample;
            count <= 1;
            state <= ACCUM;
          end
        end
        ACCUM: begin
          if (sample_valid && sample_ready) begin
            sum_reg <= sum_reg + sample;
            count <= count + 1;
            if (count == NUM_SAMPLES-1)
              state <= OUTPUT;
          end
        end
        OUTPUT: begin
          sum_valid_r <= 1;
          if (sum_ready) begin
            sum_reg <= 0;
            count <= 0;
            sum_valid_r <= 0;
            state <= IDLE;
          end
        end
      endcase
    end
  end

endmodule
