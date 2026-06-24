module event_gate (
  input wire event_valid,
  output wire count_en
);
  // Simple pass-through gate
  assign count_en = event_valid;

endmodule
