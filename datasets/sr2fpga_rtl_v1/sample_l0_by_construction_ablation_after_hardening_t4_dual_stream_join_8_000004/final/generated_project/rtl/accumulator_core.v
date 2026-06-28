// accumulator_core.v: accumulates samples and outputs running sum with handshaking
module accumulator_core (
    input clk,
    input rst_n,
    input       sample_valid,
    input [7:0] sample,
    output reg  sample_ready,
    output      out_valid,
    output [7:0] sum,
    input       out_ready
);

reg [7:0] sum_reg;
reg       has_valid;  // flag: output register holds a valid sum waiting to be taken

// sample_ready: we can accept a new sample when we are not busy with an output, or if downstream is ready to take the current output simultaneously
// i.e. we are empty (ready for new sample) or we can accept a new sample at the same time the current output is consumed
wire sample_accept_allowed = !has_valid || out_ready;

always @* begin
    sample_ready = sample_accept_allowed;
end

// output valid and sum logic
assign out_valid = has_valid;
assign sum       = sum_reg;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        sum_reg  <= 8'd0;
        has_valid <= 1'b0;
    end else begin
        if (has_valid && out_ready) begin
            // current sum output is being consumed
            if (sample_valid && sample_ready) begin
                // simultaneously accept new sample and output old sum; update sum_reg with new addition
                sum_reg <= sum_reg + sample;
                // keep has_valid high to output the new sum in the next cycle
                has_valid <= 1'b1;
            end else begin
                // no new sample, become empty
                has_valid <= 1'b0;
                // sum_reg remains unchanged
            end
        end else if (!has_valid && sample_valid && sample_ready) begin
            // accept new sample and immediately prepare to output updated sum
            sum_reg <= sum_reg + sample;
            has_valid <= 1'b1;
        end else begin
            // either has_valid=1 but out_ready=0, or has_valid=0 and no sample, so hold state
            if (has_valid) begin
                // still waiting for out_ready, keep sum_reg and has_valid
            end
            // no change
        end
    end
end

endmodule
