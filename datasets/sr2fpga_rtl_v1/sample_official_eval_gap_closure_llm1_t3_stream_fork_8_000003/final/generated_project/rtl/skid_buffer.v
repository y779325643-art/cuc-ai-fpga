module skid_buffer #(parameter DATA_WIDTH = 8) (
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
    localparam IDLE = 2'd0;
    localparam PASS = 2'd1;
    localparam SKID = 2'd2;

    reg [DATA_WIDTH-1:0] out_data_reg;
    reg                  out_valid_reg;
    reg [DATA_WIDTH-1:0] skid_data_reg;
    reg                  skid_valid_reg;
    reg [1:0]            state, next_state;

    assign out_valid = (state == SKID) ? skid_valid_reg : out_valid_reg;
    assign out_data  = (state == SKID) ? skid_data_reg  : out_data_reg;
    assign in_ready  = (state != SKID) || out_ready;

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        state          <= IDLE;
        out_valid_reg  <= 1'b0;
        skid_valid_reg <= 1'b0;
      end else begin
        state <= next_state;
        case (state)
          IDLE: begin
            if (in_valid && out_ready) begin
              out_data_reg   <= in_data;
              out_valid_reg  <= 1'b1;
              skid_valid_reg <= 1'b0;
            end else if (in_valid && !out_ready) begin
              skid_data_reg  <= in_data;
              skid_valid_reg <= 1'b1;
            end
          end
          PASS: begin
            if (in_valid && out_ready) begin
              out_data_reg   <= in_data;
              out_valid_reg  <= 1'b1;
            end else if (in_valid && !out_ready) begin
              skid_data_reg  <= in_data;
              skid_valid_reg <= 1'b1;
            end else if (!in_valid && out_ready) begin
              out_valid_reg <= 1'b0;
            end
          end
          SKID: begin
            if (out_ready) begin
              out_data_reg   <= skid_data_reg;
              out_valid_reg  <= 1'b1;
              skid_valid_reg <= 1'b0;
              if (in_valid) begin
                out_data_reg <= in_data;
              end
            end
          end
        endcase
      end
    end

    always @* begin
      next_state = state;
      case (state)
        IDLE: begin
          if (in_valid && out_ready)       next_state = PASS;
          else if (in_valid && !out_ready) next_state = SKID;
          else                             next_state = IDLE;
        end
        PASS: begin
          if (in_valid && !out_ready)      next_state = SKID;
          else if (!in_valid && out_ready) next_state = IDLE;
          else                             next_state = PASS;
        end
        SKID: begin
          if (out_ready)                   next_state = PASS;
          else                             next_state = SKID;
        end
        default: next_state = IDLE;
      endcase
    end
endmodule
