// stream_stage: a simple pipeline register with valid-ready handshake

module stream_stage #(
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

    reg [DATA_WIDTH-1:0] stage_data;
    reg                  stage_valid;

    wire load = valid_in & ready_out;
    wire transfer_out = stage_valid & ready_in;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            stage_data  <= {DATA_WIDTH{1'b0}};
            stage_valid <= 1'b0;
        end else if (load) begin
            stage_data  <= data_in;
            stage_valid <= 1'b1;
        end else if (transfer_out) begin
            stage_valid <= 1'b0;
        end
    end

    assign ready_out = ~stage_valid | transfer_out;
    assign data_out  = stage_data;
    assign valid_out = stage_valid;

endmodule
