// skid_buffer: single-level buffer with valid-ready handshake
// Asserts ready_out when not holding data, else after transfer

module skid_buffer #(
    parameter DATA_WIDTH = 8
) (
    input  wire                    clk,
    input  wire                    rst_n,
    input  wire [DATA_WIDTH-1:0]   data_in,
    input  wire                    valid_in,
    output wire                    ready_out,
    output wire [DATA_WIDTH-1:0]   data_out,
    output wire                    valid_out,
    input  wire                    ready_in
);

    reg [DATA_WIDTH-1:0] buf_data;
    reg                  buf_valid;

    wire load_to_buffer = valid_in & ready_out;
    wire transfer_out   = valid_out & ready_in;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            buf_valid <= 1'b0;
            buf_data  <= {DATA_WIDTH{1'b0}};
        end else if (load_to_buffer & ~transfer_out) begin
            // store incoming data while not transferring out
            buf_data  <= data_in;
            buf_valid <= 1'b1;
        end else if (transfer_out) begin
            // if we transfer out, clear buffer valid if no new load
            buf_valid <= load_to_buffer ? 1'b1 : 1'b0;
            if (load_to_buffer)
                buf_data <= data_in;
        end
    end

    assign ready_out = ~buf_valid | transfer_out;
    assign valid_out = buf_valid | (valid_in & ready_out & ~buf_valid);
    assign data_out  = buf_valid ? buf_data : data_in;

endmodule
