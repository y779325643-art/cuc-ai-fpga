module control_reg_bank #(
    parameter DATA_WIDTH = 8
) (
    input wire clk,
    input wire rst_n,
    input wire write_valid,
    input wire [3:0] write_addr,
    input wire [DATA_WIDTH-1:0] write_data,
    input wire read_valid,
    input wire [3:0] read_addr,
    output reg [DATA_WIDTH-1:0] read_data,
    input wire stream_done,
    output reg start_pulse,
    output reg [DATA_WIDTH-1:0] sample0,
    output reg [DATA_WIDTH-1:0] sample1,
    output reg irq_state
);

  reg [DATA_WIDTH-1:0] ctrl;
  reg busy;
  reg done;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      ctrl <= {DATA_WIDTH{1'b0}};
      sample0 <= {DATA_WIDTH{1'b0}};
      sample1 <= {DATA_WIDTH{1'b0}};
      busy <= 1'b0;
      done <= 1'b0;
      irq_state <= 1'b0;
      start_pulse <= 1'b0;
      read_data <= {DATA_WIDTH{1'b0}};
    end else begin
      start_pulse <= 1'b0;
      if (write_valid) begin
        case (write_addr)
          4'h0: begin
            ctrl <= write_data;
            if (write_data[0]) begin
              start_pulse <= 1'b1;
              busy <= 1'b1;
              done <= 1'b0;
            end
            if (write_data[1]) begin
              irq_state <= 1'b0;
            end
          end
          4'h4: sample0 <= write_data;
          4'h8: sample1 <= write_data;
          default: ctrl <= ctrl;
        endcase
      end
      if (stream_done) begin
        busy <= 1'b0;
        done <= 1'b1;
        irq_state <= 1'b1;
      end
      if (read_valid) begin
        case (read_addr)
          4'h0: read_data <= ctrl;
          4'h4: read_data <= sample0;
          4'h8: read_data <= sample1;
          4'hc: read_data <= {{(DATA_WIDTH-3){1'b0}}, irq_state, done, busy};
          default: read_data <= {DATA_WIDTH{1'b0}};
        endcase
      end
    end
  end

endmodule
