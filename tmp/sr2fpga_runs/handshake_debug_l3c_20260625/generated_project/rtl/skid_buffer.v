// skid_buffer.v - Skid buffer with depth 2 for valid-ready handshake
`timescale 1ns/1ps

module skid_buffer #(
    parameter DATA_WIDTH = 8,
    parameter DEPTH = 2
) (
    input  wire                    clk,
    input  wire                    reset_n,
    input  wire [DATA_WIDTH-1:0]   data_in,
    input  wire                    valid_in,
    output wire                    ready_out,
    output wire [DATA_WIDTH-1:0]   data_out,
    output wire                    valid_out,
    input  wire                    ready_in
);

    // Compute pointer width based on DEPTH
    localparam PTR_WIDTH = $clog2(DEPTH);

    // Internal registers and wires
    reg [DATA_WIDTH-1:0] buffer [0:DEPTH-1];
    reg [DEPTH-1:0] valid;
    reg [PTR_WIDTH-1:0] read_ptr;
    reg [PTR_WIDTH-1:0] write_ptr;
    integer i;

    // Combinational outputs
    assign ready_out = (valid[write_ptr] == 1'b0);
    assign data_out = buffer[read_ptr];
    assign valid_out = valid[read_ptr];

    // Buffer management
    always @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            for (i = 0; i < DEPTH; i = i + 1) begin
                valid[i] <= 1'b0;
                buffer[i] <= {DATA_WIDTH{1'b0}};
            end
            read_ptr <= 0;
            write_ptr <= 0;
        end else begin
            // Write operation
            if (valid_in && ready_out) begin
                buffer[write_ptr] <= data_in;
                valid[write_ptr] <= 1'b1;
                write_ptr <= write_ptr + 1;
            end
            // Read operation
            if (valid_out && ready_in) begin
                valid[read_ptr] <= 1'b0;
                read_ptr <= read_ptr + 1;
            end
        end
    end

endmodule
