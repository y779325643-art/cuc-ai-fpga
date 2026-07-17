module stream_control #(parameter IMG_WIDTH = 640, parameter IMG_HEIGHT = 480) (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    input wire in_ready,
    input wire in_last,
    output wire advance,
    output wire boundary,
    output wire last_aligned
);
  wire _unused_clock_reset = &{1'b0, clk, rst_n};
  // SR2FPGA_BEHAVIOR_BEGIN
    localparam integer X_WIDTH = (IMG_WIDTH <= 2) ? 1 : $clog2(IMG_WIDTH);
    localparam integer Y_WIDTH = (IMG_HEIGHT <= 2) ? 1 : $clog2(IMG_HEIGHT);

    reg [X_WIDTH-1:0] pix_x_count;
    reg [Y_WIDTH-1:0] pix_y_count;
    reg boundary_flag_reg;
    reg [3:0] last_pipeline_reg;
    reg [1:0] stream_fsm;

    wire accept_pixel = in_valid & in_ready;
    wire at_last_column = (pix_x_count == IMG_WIDTH[X_WIDTH-1:0] - {{(X_WIDTH-1){1'b0}}, 1'b1});
    wire at_last_row = (pix_y_count == IMG_HEIGHT[Y_WIDTH-1:0] - {{(Y_WIDTH-1){1'b0}}, 1'b1});
    wire next_boundary = (pix_x_count == {X_WIDTH{1'b0}}) ||
                         (pix_y_count == {Y_WIDTH{1'b0}}) ||
                         at_last_column || at_last_row;

    assign advance = accept_pixel;
    assign boundary = boundary_flag_reg;
    assign last_aligned = last_pipeline_reg[3];

    always @(posedge clk) begin
      if (!rst_n) begin
        pix_x_count <= {X_WIDTH{1'b0}};
        pix_y_count <= {Y_WIDTH{1'b0}};
        boundary_flag_reg <= 1'b1;
        last_pipeline_reg <= 4'b0000;
        stream_fsm <= IDLE[1:0];
      end else begin
        if (accept_pixel) begin
          boundary_flag_reg <= next_boundary;
          last_pipeline_reg <= {last_pipeline_reg[2:0], in_last};
          if (at_last_column) begin
            pix_x_count <= {X_WIDTH{1'b0}};
            if (at_last_row || in_last) begin
              pix_y_count <= {Y_WIDTH{1'b0}};
            end else begin
              pix_y_count <= pix_y_count + {{(Y_WIDTH-1){1'b0}}, 1'b1};
            end
          end else begin
            pix_x_count <= pix_x_count + {{(X_WIDTH-1){1'b0}}, 1'b1};
          end
        end else begin
          last_pipeline_reg <= {last_pipeline_reg[2:0], 1'b0};
        end

        case (stream_fsm)
          IDLE[1:0]: begin
            if (accept_pixel) begin
              stream_fsm <= in_last ? FLUSH[1:0] : ACTIVE[1:0];
            end
          end
          ACTIVE[1:0]: begin
            if (accept_pixel && in_last) begin
              stream_fsm <= FLUSH[1:0];
            end
          end
          FLUSH[1:0]: begin
            if (last_pipeline_reg[3]) begin
              stream_fsm <= IDLE[1:0];
            end
          end
          default: begin
            stream_fsm <= IDLE[1:0];
          end
        endcase
      end
    end
  // SR2FPGA_BEHAVIOR_END
  localparam IDLE = 0;
  localparam ACTIVE = 0;
  localparam FLUSH = 0;
  wire _unused_fsm_states = &{1'b0, (IDLE == IDLE), (ACTIVE == ACTIVE), (FLUSH == FLUSH)};
endmodule
