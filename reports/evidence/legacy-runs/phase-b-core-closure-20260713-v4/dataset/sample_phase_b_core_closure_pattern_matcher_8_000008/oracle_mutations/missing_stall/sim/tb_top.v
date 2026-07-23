        `timescale 1ns/1ps

        module tb_top;
          reg clk;
          reg rst_n;
          reg in_valid;
          wire in_ready;
          reg [7:0] in_data;
          wire out_valid;
          reg out_ready;
          wire [31:0] out_match_index;
          wire [31:0] out_match_word;
          reg [31:0] held_index;
          reg [31:0] held_word;

          top dut (
            .clk(clk), .rst_n(rst_n), .in_valid(in_valid), .in_ready(in_ready), .in_data(in_data),
            .out_valid(out_valid), .out_ready(out_ready), .out_match_index(out_match_index), .out_match_word(out_match_word)
          );

          initial begin
            clk = 1'b0;
            forever #5 clk = ~clk;
          end

          task reset_dut;
            begin
              rst_n = 1'b0;
              in_valid = 1'b0;
              in_data = 8'd0;
              out_ready = 1'b1;
              repeat (2) @(posedge clk);
              rst_n = 1'b1;
              @(negedge clk);
            end
          endtask

          task send_token;
            input [7:0] value;
            begin
              @(negedge clk);
              in_data = value;
              in_valid = 1'b1;
              while (in_ready !== 1'b1) @(negedge clk);
              @(negedge clk);
              in_valid = 1'b0;
            end
          endtask

          task expect_held_match;
            input [31:0] expected_index;
            input [31:0] expected_word;
            integer cycles;
            begin
              cycles = 0;
              while (out_valid !== 1'b1 && cycles < 30) begin
                @(posedge clk);
                cycles = cycles + 1;
              end
              #1;
              if (out_valid !== 1'b1 || out_match_index !== expected_index || out_match_word !== expected_word) begin
                $display("TEST_FAIL match expected index=%0d word=%h got valid=%b index=%0d word=%h", expected_index, expected_word, out_valid, out_match_index, out_match_word);
                $finish;
              end
              held_index = out_match_index;
              held_word = out_match_word;
              repeat (2) @(posedge clk);
              #1;
              if (out_valid !== 1'b1 || out_match_index !== held_index || out_match_word !== held_word) begin
                $display("TEST_FAIL output changed while stalled");
                $finish;
              end
            end
          endtask

          task release_match;
            begin
              out_ready = 1'b1;
              @(posedge clk);
              @(negedge clk);
            end
          endtask

          initial begin
            reset_dut;
            out_ready = 1'b0;
            send_token(8'h11);
            send_token(8'h22);
            send_token(8'h33);
            send_token(8'h12);
            repeat (3) @(posedge clk);
            if (out_valid !== 1'b0) begin
              $display("TEST_FAIL false positive after partial pattern");
              $finish;
            end

            reset_dut;
            send_token(8'h11);
            send_token(8'h22);
            reset_dut;
            out_ready = 1'b0;
            send_token(8'h11);
            send_token(8'h22);
            send_token(8'h33);
            send_token(8'h11);
            expect_held_match(32'd3, 32'h11223311);
if (in_ready !== 1'b0) begin
  $display("TEST_FAIL matcher did not backpressure occupied output");
  $finish;
end
@(negedge clk);
in_valid = 1'b1;
in_data = 8'hff;
repeat (2) @(posedge clk);
if (in_ready !== 1'b0) begin
  $display("TEST_FAIL matcher accepted input while output stalled");
  $finish;
end
@(negedge clk);
in_valid = 1'b0;
            release_match;

            out_ready = 1'b0;
            send_token(8'h22);
            send_token(8'h33);
            send_token(8'h11);
            expect_held_match(32'd6, 32'h11223311);
            release_match;

            reset_dut;
            out_ready = 1'b0;
            send_token(8'h11);
            send_token(8'h22);
            send_token(8'h33);
            send_token(8'h11);
            expect_held_match(32'd3, 32'h11223311);
            release_match;

            $display("TEST_PASS");
            $finish;
          end
        endmodule
