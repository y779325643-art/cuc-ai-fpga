module accumulator_core #(
    parameter DATA_WIDTH = 8,
    parameter ACCUM_WIDTH = 16
) (
    input  wire                clk,
    input  wire                rst_n,
    input  wire                in_valid,
    input  wire [DATA_WIDTH-1:0] in_data,
    output wire                in_ready,
    output wire                out_valid,
    output wire [ACCUM_WIDTH-1:0] out_data,
    input  wire                out_ready
);

    localparam IDLE = 2'b00;
    localparam ACCUMULATE = 2'b01;
    localparam OUTPUT = 2'b10;

    reg [1:0] state, next_state;
    reg [ACCUM_WIDTH-1:0] accum_reg;
    reg [ACCUM_WIDTH-1:0] out_reg;
    reg out_valid_reg;

    assign in_ready = (state == IDLE);
    assign out_valid = out_valid_reg;
    assign out_data = out_reg;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            accum_reg <= 0;
            out_valid_reg <= 1'b0;
        end else begin
            state <= next_state;
            if (state == ACCUMULATE) begin
                accum_reg <= accum_reg + in_data;
                out_reg <= accum_reg + in_data; // precompute for next cycle
            end
            if (next_state == OUTPUT) begin
                out_valid_reg <= 1'b1;
            end else if (out_valid_reg && out_ready) begin
                out_valid_reg <= 1'b0;
            end
        end
    end

    always @(*) begin
        next_state = state;
        case (state)
            IDLE: begin
                if (in_valid) begin
                    next_state = ACCUMULATE;
                end
            end
            ACCUMULATE: begin
                next_state = OUTPUT;
            end
            OUTPUT: begin
                if (out_ready) begin
                    next_state = IDLE;
                end
            end
        endcase
    end

endmodule
