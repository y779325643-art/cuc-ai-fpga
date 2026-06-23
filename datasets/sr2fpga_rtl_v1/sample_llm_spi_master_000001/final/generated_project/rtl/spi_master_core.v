module spi_master_core (
    input sclk,
    input rst_n,
    input start,
    input [7:0] data_in,
    output reg cs_n,
    output reg mosi,
    output reg busy,
    output reg done
);

reg [7:0] shift_reg;
reg [2:0] bit_count;
reg [1:0] state;

localparam IDLE = 0, SHIFT = 1, DONE = 2;

// State machine on posedge sclk
always @(posedge sclk or negedge rst_n) begin
    if (!rst_n) begin
        state <= IDLE;
        cs_n <= 1;
        busy <= 0;
        done <= 0;
    end else begin
        case (state)
            IDLE: begin
                done <= 0;
                if (start) begin
                    state <= SHIFT;
                    cs_n <= 0;
                    busy <= 1;
                end
            end
            SHIFT: begin
                if (bit_count == 0) begin
                    state <= DONE;
                    cs_n <= 1;
                    busy <= 0;
                    done <= 1;
                end
            end
            DONE: begin
                done <= 0;
                state <= IDLE;
            end
        endcase
    end
end

// Shift and load on negedge sclk
always @(negedge sclk or negedge rst_n) begin
    if (!rst_n) begin
        mosi <= 0;
        shift_reg <= 0;
        bit_count <= 0;
    end else begin
        if (state == IDLE && start) begin
            shift_reg <= data_in;
            bit_count <= 7;
        end else if (state == SHIFT) begin
            mosi <= shift_reg[7];
            shift_reg <= shift_reg << 1;
            bit_count <= bit_count - 1;
        end
    end
end

endmodule
