module replay_index_allocator (
    input wire clk,
    input wire rst_n,
    input wire write_accepted,
    output reg [1:0] write_index,
    output reg [2:0] occupancy
);

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      write_index <= 2'd0;
      occupancy <= 3'd0;
    end else if (write_accepted) begin
      write_index <= write_index + 2'd1;
      if (occupancy < 3'd4) begin
        occupancy <= occupancy + 3'd1;
      end
    end
  end

endmodule
