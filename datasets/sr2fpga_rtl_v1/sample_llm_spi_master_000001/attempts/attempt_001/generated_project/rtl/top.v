module top (
    input clk,
    input rst_n,
    input start,
    input [7:0] data_in,
    output sclk,
    output mosi,
    output cs_n,
    output busy,
    output done
);

wire sclk_int;
wire start_sync;
reg [1:0] start_sync_reg;
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) start_sync_reg <= 2'b00;
    else start_sync_reg <= {start_sync_reg[0], start};
end
assign start_sync = start_sync_reg[1];

clock_divider #(.DIV(100)) u_div (
    .clk(clk),
    .rst_n(rst_n),
    .sclk(sclk_int)
);

spi_master_core u_core (
    .sclk(sclk_int),
    .rst_n(rst_n),
    .start(start_sync),
    .data_in(data_in),
    .cs_n(cs_n),
    .mosi(mosi),
    .busy(busy),
    .done(done)
);

assign sclk = sclk_int;

endmodule
