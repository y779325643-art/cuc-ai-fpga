module skid_buffer #(parameter DATA_WIDTH = 8) (
    input wire [None-1:0] clk,
    input wire [None-1:0] rst_n,
    input wire [None-1:0] in_valid,
    input wire [DATA_WIDTH-1:0] in_data,
    output wire [None-1:0] in_ready,
    output wire [None-1:0] out_valid,
    output wire [DATA_WIDTH-1:0] out_data,
    input wire [None-1:0] out_ready
);
  wire _unused_clock_reset = &{1'b0, clk, rst_n};
    localparam IDLE  = 2'd0;
    localparam STORE = 2'd1;
    localparam PASS  = 2'd2;
    reg [DATA_WIDTH-1:0] sample_reg;
    reg                  sample_valid;
    reg [DATA_WIDTH-1:0] skid_reg;
    reg                  skid_valid;
    reg [1:0]            state;

    assign out_data = sample_valid ? sample_reg : {DATA_WIDTH{1'b0}};
    assign out_valid = sample_valid;
    assign in_ready = !skid_valid;

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        sample_reg   <= {DATA_WIDTH{1'b0}};
        sample_valid <= 1'b0;
        skid_reg     <= {DATA_WIDTH{1'b0}};
        skid_valid   <= 1'b0;
        state        <= IDLE;
      end else begin
        if (out_ready && sample_valid) begin
          sample_valid <= 1'b0;
        end
        if (in_valid && in_ready) begin
          if (!sample_valid) begin
            sample_reg   <= in_data;
            sample_valid <= 1'b1;
          end else begin
            skid_reg   <= in_data;
            skid_valid <= 1'b1;
          end
        end
        if (!sample_valid && skid_valid) begin
          sample_reg   <= skid_reg;
          sample_valid <= 1'b1;
          skid_valid   <= 1'b0;
        end
        if (sample_valid && skid_valid) begin
          state <= STORE;
        end else if (sample_valid && !skid_valid) begin
          state <= PASS;
        end else begin
          state <= IDLE;
        end
      end
    end
endmodule
