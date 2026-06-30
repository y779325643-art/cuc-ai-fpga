`timescale 1ns / 1ps

module skid_buffer #(
    parameter WIDTH = 8
) (
    input  wire        clk,
    input  wire        nreset,
    input  wire        in_valid,
    input  wire [WIDTH-1:0] in_data,
    output wire        in_ready,
    output wire        out_valid,
    output wire [WIDTH-1:0] out_data,
    input  wire        out_ready
);

    reg        valid_r;
    reg [WIDTH-1:0] data_r;

    // Output combinational logic
    assign out_valid = valid_r || in_valid;
    assign out_data  = valid_r ? data_r : in_data;
    assign in_ready  = !valid_r || out_ready;

    // Register logic
    always @(posedge clk or negedge nreset) begin
        if (!nreset) begin
            valid_r <= 1'b0;
            data_r  <= {WIDTH{1'b0}};
        end else begin
            if (in_ready && in_valid) begin
                if (!out_ready) begin
                    // stash incoming data
                    valid_r <= 1'b1;
                    data_r  <= in_data;
                end else begin
                    // pass through, no stash needed
                    valid_r <= 1'b0;
                end
            end else if (valid_r && out_ready) begin
                // stash consumed, no new data
                valid_r <= 1'b0;
            end
            // otherwise no change
        end
    end

endmodule
