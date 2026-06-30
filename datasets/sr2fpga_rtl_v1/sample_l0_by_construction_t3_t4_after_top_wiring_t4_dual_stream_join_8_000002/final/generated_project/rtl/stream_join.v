module stream_join #(parameter DATA_WIDTH = 8) (
    input wire clk,
    input wire rst_n,
    input wire in0_valid,
    output wire in0_ready,
    input wire [DATA_WIDTH-1:0] in0_data,
    input wire in1_valid,
    output wire in1_ready,
    input wire [DATA_WIDTH-1:0] in1_data,
    output wire out_valid,
    input wire out_ready,
    output wire [DATA_WIDTH-1:0] out_data
);
  wire _unused_clock_reset = &{1'b0, clk, rst_n};
  localparam IDLE = 3'd0;
  localparam GOT_IN0 = 3'd1;
  localparam GOT_IN1 = 3'd2;
  localparam OUTPUT_IN0 = 3'd3;
  localparam OUTPUT_IN1 = 3'd4;

  reg [2:0] state;
  reg in0_valid_r, in1_valid_r;
  reg [DATA_WIDTH-1:0] in0_data_r, in1_data_r;
  reg out_valid_r;
  reg [DATA_WIDTH-1:0] out_data_r;

  assign in0_ready = (state == IDLE) || (state == GOT_IN1);
  assign in1_ready = (state == IDLE) || (state == GOT_IN0);
  assign out_valid = out_valid_r;
  assign out_data = out_data_r;

  always @(posedge clk) begin
      if (!rst_n) begin
          state <= IDLE;
          in0_valid_r <= 1'b0;
          in1_valid_r <= 1'b0;
          in0_data_r <= {DATA_WIDTH{1'b0}};
          in1_data_r <= {DATA_WIDTH{1'b0}};
          out_valid_r <= 1'b0;
          out_data_r <= {DATA_WIDTH{1'b0}};
      end else begin
          // input capture (priority: input handshake)
          if (in0_ready && in0_valid) begin
              in0_valid_r <= 1'b1;
              in0_data_r <= in0_data;
          end else if (state == OUTPUT_IN0 && out_ready) begin
              in0_valid_r <= 1'b0;
          end

          if (in1_ready && in1_valid) begin
              in1_valid_r <= 1'b1;
              in1_data_r <= in1_data;
          end else if (state == OUTPUT_IN1 && out_ready) begin
              in1_valid_r <= 1'b0;
          end

          // FSM next state logic
          case (state)
              IDLE: begin
                  if (in0_valid_r && !in1_valid_r)
                      state <= GOT_IN0;
                  else if (!in0_valid_r && in1_valid_r)
                      state <= GOT_IN1;
                  else if (in0_valid_r && in1_valid_r)
                      state <= OUTPUT_IN0;
              end
              GOT_IN0: begin
                  if (in1_valid_r)
                      state <= OUTPUT_IN0;
              end
              GOT_IN1: begin
                  if (in0_valid_r)
                      state <= OUTPUT_IN0;
              end
              OUTPUT_IN0: begin
                  if (out_ready)
                      state <= OUTPUT_IN1;
              end
              OUTPUT_IN1: begin
                  if (out_ready)
                      state <= IDLE;
              end
              default: state <= IDLE;
          endcase

          // output generation
          if (state == OUTPUT_IN0 && out_ready) begin
              out_data_r <= in0_data_r;
              out_valid_r <= 1'b1;
          end else if (state == OUTPUT_IN1 && out_ready) begin
              out_data_r <= in1_data_r;
              out_valid_r <= 1'b1;
          end else if (out_valid_r && out_ready) begin
              out_valid_r <= 1'b0;
          end
      end
  end
endmodule
