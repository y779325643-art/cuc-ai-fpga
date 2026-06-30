module event_gate (
    input wire [1-1:0] clk,
    input wire [1-1:0] rst_n,
    input wire [1-1:0] event_valid,
    output wire [1-1:0] count_en
);
    reg count_en_reg;
    always @(posedge clk) begin
      if (!rst_n)
        count_en_reg <= 1'b0;
      else
        count_en_reg <= event_valid;
    end
    assign count_en = count_en_reg;
endmodule
