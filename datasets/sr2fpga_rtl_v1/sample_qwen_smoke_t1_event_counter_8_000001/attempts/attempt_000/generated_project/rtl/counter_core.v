// counter_core.v - Synchronous 8-bit counter with active-low reset
// System-HIS v1.2 compliant

module counter_core #(
    parameter DATA_WIDTH = 8
)(
    input  wire                  clk,
    input  wire                  rst_n,
    input  wire                  inc,
    output wire [DATA_WIDTH-1:0] count
);

    reg [DATA_WIDTH-1:0] event_count_reg;

    always @(posedge clk) begin
        if (!rst_n) begin
            event_count_reg <= {DATA_WIDTH{1'b0}};
        end else if (inc) begin
            event_count_reg <= event_count_reg + 1'b1;
        end
    end

    assign count = event_count_reg;

endmodule
