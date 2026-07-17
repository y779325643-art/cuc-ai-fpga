module sync_fifo #(parameter DATA_WIDTH = 8, parameter DEPTH = 16, parameter ADDR_WIDTH = 4) (
    input wire clk,
    input wire rst_n,
    input wire wr_valid,
    output wire wr_ready,
    input wire [DATA_WIDTH-1:0] wr_data,
    output wire rd_valid,
    input wire rd_ready,
    output wire [DATA_WIDTH-1:0] rd_data
);
  wire _unused_clock_reset = &{1'b0, clk, rst_n};
  // SR2FPGA_BEHAVIOR_BEGIN
    reg [ADDR_WIDTH-1:0] wr_ptr;
    reg [ADDR_WIDTH-1:0] rd_ptr;
    reg [ADDR_WIDTH:0]   occupancy;
    reg [DATA_WIDTH-1:0] fifo_mem [0:DEPTH-1];

    // Full level expressed in the occupancy width (ADDR_WIDTH+1 bits).
    localparam [ADDR_WIDTH:0] FULL_LEVEL = DEPTH[ADDR_WIDTH:0];

    // Flow-control status derived from occupancy (control_flow: wr_ready_gate, rd_valid_gate).
    assign wr_ready = (occupancy < FULL_LEVEL);
    assign rd_valid = (occupancy != {(ADDR_WIDTH+1){1'b0}});

    // Registered pointer storage read (data_flow: read_path).
    assign rd_data  = fifo_mem[rd_ptr];

    // Handshake fire terms (control_flow: write_accept, read_accept).
    wire wr_fire = wr_valid & wr_ready;
    wire rd_fire = rd_valid & rd_ready;

    always @(posedge clk) begin
      if (!rst_n) begin
        // control_flow: reset_state
        wr_ptr    <= {ADR_WIDTH{1'b0}};
        rd_ptr    <= {ADDR_WIDTH{1'b0}};
        occupancy <= {(ADDR_WIDTH+1){1'b0}};
      end else begin
        // Write path store + write pointer advance (control_flow: write_accept, write_path).
        if (wr_fire) begin
          fifo_mem[wr_ptr] <= wr_data;
          wr_ptr <= wr_ptr + {{(ADDR_WIDTH-1){1'b0}}, 1'b1};
        end

        // Read pointer advance (control_flow: read_accept, read_path).
        if (rd_fire) begin
          rd_ptr <= rd_ptr + {{(ADDR_WIDTH-1){1'b0}}, 1'b1};
        end

        // Occupancy tracking (control_flow: occupancy_increment, occupancy_decrement).
        case ({wr_fire, rd_fire})
          2'b10:   occupancy <= occupancy + {{ADDR_WIDTH{1'b0}}, 1'b1};
          2'b01:   occupancy <= occupancy - {{ADDR_WIDTH{1'b0}}, 1'b1};
          default: occupancy <= occupancy;
        endcase
      end
    end
  // SR2FPGA_BEHAVIOR_END
endmodule
