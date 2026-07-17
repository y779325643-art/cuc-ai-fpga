module fifo_core #(parameter DATA_WIDTH = 8, parameter DEPTH = 4, parameter ADDR_WIDTH = 2) (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    output wire in_ready,
    input wire [DATA_WIDTH-1:0] in_data,
    output wire out_valid,
    input wire out_ready,
    output wire [DATA_WIDTH-1:0] out_data
);
  wire _unused_clock_reset = &{1'b0, clk, rst_n};
  // SR2FPGA_BEHAVIOR_BEGIN
    localparam [ADDR_WIDTH-1:0] FIFO_ZERO_ADDR = {ADDR_WIDTH{1'b0}};
    localparam [ADDR_WIDTH-1:0] FIFO_LAST_ADDR = {ADDR_WIDTH{1'b1}};
    localparam [ADDR_WIDTH:0] FIFO_ZERO_COUNT = {(ADDR_WIDTH+1){1'b0}};
    localparam [ADDR_WIDTH:0] FIFO_ONE_COUNT = {{ADDR_WIDTH{1'b0}}, 1'b1};
    localparam [ADDR_WIDTH:0] FIFO_DEPTH_COUNT = {1'b1, {ADDR_WIDTH{1'b0}}};

    reg [DATA_WIDTH-1:0] fifo_storage [0:DEPTH-1];
    reg [DATA_WIDTH-1:0] fifo_out_data_reg;
    reg fifo_out_valid_reg;
    reg [ADDR_WIDTH-1:0] fifo_wr_ptr;
    reg [ADDR_WIDTH-1:0] fifo_rd_ptr;
    reg [ADDR_WIDTH:0] fifo_count;

    wire fifo_push;
    wire fifo_pop;
    wire [ADDR_WIDTH-1:0] fifo_wr_ptr_next;
    wire [ADDR_WIDTH-1:0] fifo_rd_ptr_next;

    reg [ADDR_WIDTH:0] fifo_count_next;
    reg [DATA_WIDTH-1:0] fifo_out_data_next;

    assign in_ready = (fifo_count != FIFO_DEPTH_COUNT);
    assign out_valid = fifo_out_valid_reg;
    assign out_data = fifo_out_data_reg;

    assign fifo_push = in_valid & in_ready;
    assign fifo_pop = fifo_out_valid_reg & out_ready;

    assign fifo_wr_ptr_next = (fifo_wr_ptr == FIFO_LAST_ADDR) ? FIFO_ZERO_ADDR : (fifo_wr_ptr + {{(ADDR_WIDTH-1){1'b0}}, 1'b1});
    assign fifo_rd_ptr_next = (fifo_rd_ptr == FIFO_LAST_ADDR) ? FIFO_ZERO_ADDR : (fifo_rd_ptr + {{(ADDR_WIDTH-1){1'b0}}, 1'b1});

    always @* begin
      fifo_count_next = fifo_count;
      case ({fifo_push, fifo_pop})
        2'b00: fifo_count_next = fifo_count;
        2'b01: fifo_count_next = fifo_count - {{ADDR_WIDTH{1'b0}}, 1'b1};
        2'b10: fifo_count_next = fifo_count + {{ADDR_WIDTH{1'b0}}, 1'b1};
        2'b11: fifo_count_next = fifo_count;
        default: fifo_count_next = fifo_count;
      endcase
    end

    always @* begin
      fifo_out_data_next = fifo_out_data_reg;
      if (fifo_count_next == FIFO_ZERO_COUNT) begin
        fifo_out_data_next = {DATA_WIDTH{1'b0}};
      end else if ((fifo_count == FIFO_ZERO_COUNT) && fifo_push) begin
        fifo_out_data_next = in_data;
      end else if (fifo_pop) begin
        if (fifo_push && (fifo_count == FIFO_ONE_COUNT)) begin
          fifo_out_data_next = in_data;
        end else begin
          fifo_out_data_next = fifo_storage[fifo_rd_ptr_next];
        end
      end
    end

    always @(posedge clk) begin
      if (!rst_n) begin
        fifo_out_data_reg <= {DATA_WIDTH{1'b0}};
        fifo_out_valid_reg <= 1'b0;
        fifo_wr_ptr <= FIFO_ZERO_ADDR;
        fifo_rd_ptr <= FIFO_ZERO_ADDR;
        fifo_count <= FIFO_ZERO_COUNT;
      end else begin
        if (fifo_push) begin
          fifo_storage[fifo_wr_ptr] <= in_data;
          fifo_wr_ptr <= fifo_wr_ptr_next;
        end

        if (fifo_pop) begin
          fifo_rd_ptr <= fifo_rd_ptr_next;
        end

        fifo_count <= fifo_count_next;
        fifo_out_valid_reg <= (fifo_count_next != FIFO_ZERO_COUNT);
        fifo_out_data_reg <= fifo_out_data_next;
      end
    end
  // SR2FPGA_BEHAVIOR_END
endmodule
