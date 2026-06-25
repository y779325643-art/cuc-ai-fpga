module event_gate (
    input wire clk,
    input wire rst_n,
    input wire event_valid,
    output reg count_en
);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            count_en <= 1'b0;
        else
            count_en <= event_valid;
    end

endmodule
