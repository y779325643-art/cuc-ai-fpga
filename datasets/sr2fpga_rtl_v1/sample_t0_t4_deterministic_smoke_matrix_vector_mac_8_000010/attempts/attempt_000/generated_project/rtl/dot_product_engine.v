module dot_product_engine #(
    parameter WIDTH = 8,
    parameter RESULT_WIDTH = 12
) (
    input wire clk,
    input wire rst_n,
    input wire start,
    output reg busy,
    output reg done,
    output reg [RESULT_WIDTH-1:0] result
);

  reg [1:0] index;
  reg [RESULT_WIDTH-1:0] accum;
  reg [WIDTH-1:0] vector_value;
  wire [1:0] coefficient;
  wire [RESULT_WIDTH-1:0] next_accum;

  vector_rom u_vector_rom (
    .addr(index),
    .coefficient(coefficient)
  );

  mac_unit #(
    .WIDTH(WIDTH),
    .ACC_WIDTH(RESULT_WIDTH)
  ) u_mac_unit (
    .sample(vector_value),
    .coefficient(coefficient),
    .accum(accum),
    .result(next_accum)
  );

  always @* begin
    case (index)
      2'd0: vector_value = {{(WIDTH-1){1'b0}}, 1'b1};
      2'd1: vector_value = {{(WIDTH-2){1'b0}}, 2'd2};
      2'd2: vector_value = {{(WIDTH-2){1'b0}}, 2'd3};
      default: vector_value = {{(WIDTH-3){1'b0}}, 3'd4};
    endcase
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      index <= 2'd0;
      accum <= {RESULT_WIDTH{1'b0}};
      busy <= 1'b0;
      done <= 1'b0;
      result <= {RESULT_WIDTH{1'b0}};
    end else begin
      done <= 1'b0;
      if (!busy) begin
        index <= 2'd0;
        accum <= {RESULT_WIDTH{1'b0}};
        if (start) begin
          busy <= 1'b1;
        end
      end else begin
        accum <= next_accum;
        if (index == 2'd3) begin
          result <= next_accum;
          busy <= 1'b0;
          done <= 1'b1;
          index <= 2'd0;
        end else begin
          index <= index + 2'd1;
        end
      end
    end
  end

endmodule
