module top (
    input wire clk,
    input wire rst_n,
    input wire [11:0] duty,
    output wire pwm_out
);

  wire [11:0] counter;

  pwm_timer #(
    .WIDTH(12)
  ) u_pwm_timer (
    .clk(clk),
    .rst_n(rst_n),
    .counter(counter)
  );

  pwm_channel #(
    .WIDTH(12)
  ) u_pwm_channel (
    .counter(counter),
    .duty(duty),
    .pwm_out(pwm_out)
  );

endmodule
