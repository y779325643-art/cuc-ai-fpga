// stream_join: waits for both inputs to be valid together, then produces output
// Implements ready/valid handshake on all interfaces

module stream_join #(
    parameter DATA_WIDTH = 8
) (
    input  wire                    clk,
    input  wire                    rst_n,
    input  wire [DATA_WIDTH-1:0]   data_in0,
    input  wire                    valid_in0,
    output wire                    ready_out0,
    input  wire [DATA_WIDTH-1:0]   data_in1,
    input  wire                    valid_in1,
    output wire                    ready_out1,
    output wire [DATA_WIDTH-1:0]   data_out,
    output wire                    valid_out,
    input  wire                    ready_in
);

    reg [DATA_WIDTH-1:0] join_data_reg;
    reg                  join_valid_reg;

    wire fire = valid_in0 & valid_in1 & ready_in;
    wire load = fire;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            join_data_reg  <= {DATA_WIDTH{1'b0}};
            join_valid_reg <= 1'b0;
        end else if (load) begin
            join_data_reg  <= data_in0 + data_in1;
            join_valid_reg <= 1'b1;
        end else if (ready_in & join_valid_reg) begin
            join_valid_reg <= 1'b0;
        end
    end

    assign ready_out0 = ready_in;
    assign ready_out1 = ready_in;
    assign data_out   = join_data_reg;
    assign valid_out  = join_valid_reg;

endmodule
