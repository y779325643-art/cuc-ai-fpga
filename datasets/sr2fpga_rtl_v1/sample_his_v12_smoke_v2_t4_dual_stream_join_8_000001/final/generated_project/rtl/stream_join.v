module stream_join #(
    parameter DATA_WIDTH = 8
) (
    input  wire                clk,
    input  wire                rst_n,
    input  wire                in0_valid,
    input  wire [DATA_WIDTH-1:0] in0_data,
    output wire                in0_ready,
    input  wire                in1_valid,
    input  wire [DATA_WIDTH-1:0] in1_data,
    output wire                in1_ready,
    output wire                out_valid,
    output wire [DATA_WIDTH-1:0] out_data,
    input  wire                out_ready
);

    localparam IDLE = 2'b00;
    localparam WAIT_BOTH = 2'b01;
    localparam PASS = 2'b10;

    reg [1:0] state, next_state;
    reg in0_valid_reg, in1_valid_reg;
    reg [DATA_WIDTH-1:0] in0_data_reg, in1_data_reg;
    reg out_valid_reg;
    reg [DATA_WIDTH-1:0] out_data_reg;

    assign in0_ready = (state == IDLE || state == WAIT_BOTH);
    assign in1_ready = (state == IDLE || state == WAIT_BOTH);
    assign out_valid = out_valid_reg;
    assign out_data = out_data_reg;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            in0_valid_reg <= 1'b0;
            in1_valid_reg <= 1'b0;
            out_valid_reg <= 1'b0;
        end else begin
            state <= next_state;
            // capture data on handshake
            if (in0_valid && in0_ready) begin
                in0_valid_reg <= 1'b1;
                in0_data_reg <= in0_data;
            end
            if (in1_valid && in1_ready) begin
                in1_valid_reg <= 1'b1;
                in1_data_reg <= in1_data;
            end
            // output generation
            if (next_state == PASS) begin
                out_valid_reg <= 1'b1;
                // Join operation: sum of two inputs (truncated to DATA_WIDTH)
                out_data_reg <= in0_data_reg + in1_data_reg;
            end else if (out_valid_reg && out_ready) begin
                out_valid_reg <= 1'b0;
            end
            // clear captured valid after PASS
            if (next_state != state && state == PASS) begin
                in0_valid_reg <= 1'b0;
                in1_valid_reg <= 1'b0;
            end
        end
    end

    always @(*) begin
        next_state = state;
        case (state)
            IDLE: begin
                if (in0_valid && in0_ready && in1_valid && in1_ready) begin
                    next_state = PASS;
                end else if ((in0_valid && in0_ready) || (in1_valid && in1_ready)) begin
                    next_state = WAIT_BOTH;
                end
            end
            WAIT_BOTH: begin
                if (in0_valid_reg && in1_valid_reg) begin
                    next_state = PASS;
                end
            end
            PASS: begin
                if (out_ready) begin
                    next_state = IDLE;
                end
            end
        endcase
    end

endmodule
