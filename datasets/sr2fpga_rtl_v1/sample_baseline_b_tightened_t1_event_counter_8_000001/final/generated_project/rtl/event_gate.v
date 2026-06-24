module event_gate (
    input wire event_valid,
    output reg count_en
);

always @* begin
    count_en = event_valid;
end

endmodule
