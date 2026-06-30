module event_gate (
    input wire event_valid,
    output wire count_en
);

  assign count_en = event_valid;

endmodule
