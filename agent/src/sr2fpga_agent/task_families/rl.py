"""Stable family metadata for RL and host-facing generator tasks."""

from textwrap import dedent

TASK_FAMILY_IDS = {
    "composed_td_update_core": "qtable_update_core",
    "composed_policy_value_shell": "rl_reward_policy_update",
    "composed_replay_sample_shell": "t8_replay_sample_shell",
    "composed_host_protocol_shell": "t9_host_protocol_shell",
    "composed_rl_accelerator_shell": "p_rl_qlearning_accel",
    "composed_batch_rl_accelerator_shell": "p_rl_qlearning_accel",
    "composed_replay_arbiter_shell": "t12_replay_arbiter_shell",
}


def batch_config_bank_rtl() -> str:
    return dedent(
        """\
        module batch_config_bank #(
            parameter DATA_WIDTH = 8
        ) (
            input wire clk,
            input wire rst_n,
            input wire cfg_valid,
            output wire cfg_ready,
            input wire [2:0] cfg_addr,
            input wire [DATA_WIDTH-1:0] cfg_data,
            output reg [DATA_WIDTH-1:0] weight0,
            output reg [DATA_WIDTH-1:0] bias0,
            output reg [DATA_WIDTH-1:0] weight1,
            output reg [DATA_WIDTH-1:0] bias1,
            output reg [DATA_WIDTH-1:0] alpha,
            output reg enable
        );

          assign cfg_ready = 1'b1;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              weight0 <= {DATA_WIDTH{1'b0}};
              bias0 <= {DATA_WIDTH{1'b0}};
              weight1 <= {DATA_WIDTH{1'b0}};
              bias1 <= {DATA_WIDTH{1'b0}};
              alpha <= {DATA_WIDTH{1'b0}};
              enable <= 1'b0;
            end else if (cfg_valid && cfg_ready) begin
              case (cfg_addr)
                3'd0: weight0 <= cfg_data;
                3'd1: bias0 <= cfg_data;
                3'd2: weight1 <= cfg_data;
                3'd3: bias1 <= cfg_data;
                3'd4: alpha <= cfg_data;
                3'd5: enable <= cfg_data[0];
                default: enable <= enable;
              endcase
            end
          end

        endmodule
        """
    )


def composed_td_update_core_testbench(width: int) -> str:
    msb = width - 1
    legacy = dedent(
        f"""\
        `timescale 1ns/1ps

        module tb_top;
          reg clk;
          reg rst_n;
          reg in_valid;
          wire in_ready;
          reg signed [{msb}:0] reward;
          reg signed [{msb}:0] value;
          reg signed [{msb}:0] next_value;
          reg [{msb}:0] gamma;
          reg [{msb}:0] alpha;
          wire out_valid;
          reg out_ready;
          wire signed [{msb}:0] td_error;
          wire signed [{msb}:0] updated_value;
          integer wait_cycles;

          top dut (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(in_valid),
            .in_ready(in_ready),
            .reward(reward),
            .value(value),
            .next_value(next_value),
            .gamma(gamma),
            .alpha(alpha),
            .out_valid(out_valid),
            .out_ready(out_ready),
            .td_error(td_error),
            .updated_value(updated_value)
          );

          initial begin
            clk = 1'b0;
            forever #5 clk = ~clk;
          end

          task send_update;
            input signed [{msb}:0] reward_i;
            input signed [{msb}:0] value_i;
            input signed [{msb}:0] next_value_i;
            input [{msb}:0] gamma_i;
            input [{msb}:0] alpha_i;
            begin
              @(negedge clk);
              in_valid = 1'b1;
              reward = reward_i;
              value = value_i;
              next_value = next_value_i;
              gamma = gamma_i;
              alpha = alpha_i;
              while (!in_ready) begin
                @(negedge clk);
              end
              @(negedge clk);
              in_valid = 1'b0;
            end
          endtask

          task expect_update;
            input signed [{msb}:0] expected_error;
            input signed [{msb}:0] expected_value;
            begin
              wait_cycles = 0;
              while (out_valid !== 1'b1 && wait_cycles < 16) begin
                @(posedge clk);
                #1;
                wait_cycles = wait_cycles + 1;
              end
              if (out_valid !== 1'b1) begin
                $display("TEST_FAIL output did not become valid");
                $finish;
              end
              if (td_error !== expected_error || updated_value !== expected_value) begin
                $display(
                  "TEST_FAIL expected td=%0d value=%0d got td=%0d value=%0d",
                  expected_error,
                  expected_value,
                  td_error,
                  updated_value
                );
                $finish;
              end
              @(negedge clk);
            end
          endtask

          initial begin
            rst_n = 1'b0;
            in_valid = 1'b0;
            reward = {width}'sd0;
            value = {width}'sd0;
            next_value = {width}'sd0;
            gamma = {width}'d0;
            alpha = {width}'d0;
            out_ready = 1'b1;
            repeat (2) @(posedge clk);
            rst_n = 1'b1;

            send_update({width}'sd4, {width}'sd10, {width}'sd20, {width}'d8, {width}'d4);
            expect_update({width}'sd4, {width}'sd11);

            send_update({width}'sd2, {width}'sd6, {width}'sd16, {width}'d8, {width}'d8);
            expect_update({width}'sd4, {width}'sd8);

            $display("TEST_PASS");
            $finish;
          end
        endmodule
        """
    )
    return _add_td_oracle_mode(legacy, width)


def composed_policy_value_shell_testbench(width: int) -> str:
    msb = width - 1
    return dedent(
        f"""\
        `timescale 1ns/1ps

        module tb_top;
          reg clk;
          reg rst_n;
          reg cfg_valid;
          wire cfg_ready;
          reg [2:0] cfg_addr;
          reg [{msb}:0] cfg_data;
          reg obs_valid;
          wire obs_ready;
          reg [{msb}:0] obs0;
          reg [{msb}:0] obs1;
          wire action_valid;
          reg action_ready;
          wire selected_action;
          wire [{msb}:0] value_estimate;
          integer wait_cycles;

          top dut (
            .clk(clk),
            .rst_n(rst_n),
            .cfg_valid(cfg_valid),
            .cfg_ready(cfg_ready),
            .cfg_addr(cfg_addr),
            .cfg_data(cfg_data),
            .obs_valid(obs_valid),
            .obs_ready(obs_ready),
            .obs0(obs0),
            .obs1(obs1),
            .action_valid(action_valid),
            .action_ready(action_ready),
            .selected_action(selected_action),
            .value_estimate(value_estimate)
          );

          initial begin
            clk = 1'b0;
            forever #5 clk = ~clk;
          end

          task write_cfg;
            input [2:0] addr_i;
            input [{msb}:0] data_i;
            begin
              @(negedge clk);
              cfg_valid = 1'b1;
              cfg_addr = addr_i;
              cfg_data = data_i;
              while (!cfg_ready) begin
                @(negedge clk);
              end
              @(negedge clk);
              cfg_valid = 1'b0;
            end
          endtask

          task send_observation;
            input [{msb}:0] obs0_i;
            input [{msb}:0] obs1_i;
            begin
              @(negedge clk);
              obs_valid = 1'b1;
              obs0 = obs0_i;
              obs1 = obs1_i;
              while (!obs_ready) begin
                @(negedge clk);
              end
              @(negedge clk);
              obs_valid = 1'b0;
            end
          endtask

          task expect_action;
            input expected_action;
            input [{msb}:0] expected_value;
            begin
              wait_cycles = 0;
              while (action_valid !== 1'b1 && wait_cycles < 16) begin
                @(posedge clk);
                #1;
                wait_cycles = wait_cycles + 1;
              end
              if (action_valid !== 1'b1) begin
                $display("TEST_FAIL action output did not become valid");
                $finish;
              end
              if (selected_action !== expected_action || value_estimate !== expected_value) begin
                $display(
                  "TEST_FAIL expected action=%0d value=%0d got action=%0d value=%0d",
                  expected_action,
                  expected_value,
                  selected_action,
                  value_estimate
                );
                $finish;
              end
              @(negedge clk);
            end
          endtask

          initial begin
            rst_n = 1'b0;
            cfg_valid = 1'b0;
            cfg_addr = 3'd0;
            cfg_data = {width}'d0;
            obs_valid = 1'b0;
            obs0 = {width}'d0;
            obs1 = {width}'d0;
            action_ready = 1'b1;
            repeat (2) @(posedge clk);
            rst_n = 1'b1;

            write_cfg(3'd0, {width}'d2);
            write_cfg(3'd1, {width}'d1);
            write_cfg(3'd2, {width}'d3);
            write_cfg(3'd3, {width}'d0);
            write_cfg(3'd4, {width}'d1);

            send_observation({width}'d4, {width}'d2);
            expect_action(1'b0, {width}'d7);

            send_observation({width}'d1, {width}'d5);
            expect_action(1'b1, {width}'d9);

            $display("TEST_PASS");
            $finish;
          end
        endmodule
        """
    )


def composed_replay_sample_shell_testbench(width: int) -> str:
    msb = width - 1
    return dedent(
        f"""\
        `timescale 1ns/1ps

        module tb_top;
          reg clk;
          reg rst_n;
          reg host_valid;
          wire host_ready;
          reg [{msb}:0] host_state;
          reg host_action;
          reg [{msb}:0] host_reward;
          reg [{msb}:0] host_next_state;
          reg host_done;
          wire sample_valid;
          reg sample_ready;
          wire [{msb}:0] sample_state;
          wire sample_action;
          wire [{msb}:0] sample_reward;
          wire [{msb}:0] sample_next_state;
          wire sample_done;
          wire [2:0] occupancy;
          integer wait_cycles;

          top dut (
            .clk(clk),
            .rst_n(rst_n),
            .host_valid(host_valid),
            .host_ready(host_ready),
            .host_state(host_state),
            .host_action(host_action),
            .host_reward(host_reward),
            .host_next_state(host_next_state),
            .host_done(host_done),
            .sample_valid(sample_valid),
            .sample_ready(sample_ready),
            .sample_state(sample_state),
            .sample_action(sample_action),
            .sample_reward(sample_reward),
            .sample_next_state(sample_next_state),
            .sample_done(sample_done),
            .occupancy(occupancy)
          );

          initial begin
            clk = 1'b0;
            forever #5 clk = ~clk;
          end

          task write_sample;
            input [{msb}:0] state_i;
            input action_i;
            input [{msb}:0] reward_i;
            input [{msb}:0] next_state_i;
            input done_i;
            begin
              @(negedge clk);
              host_valid = 1'b1;
              host_state = state_i;
              host_action = action_i;
              host_reward = reward_i;
              host_next_state = next_state_i;
              host_done = done_i;
              while (!host_ready) begin
                @(negedge clk);
              end
              @(negedge clk);
              host_valid = 1'b0;
            end
          endtask

          task expect_sample;
            input [{msb}:0] expected_state;
            input expected_action;
            input [{msb}:0] expected_reward;
            input [{msb}:0] expected_next_state;
            input expected_done;
            begin
              wait_cycles = 0;
              while (sample_valid !== 1'b1 && wait_cycles < 16) begin
                @(posedge clk);
                #1;
                wait_cycles = wait_cycles + 1;
              end
              if (sample_valid !== 1'b1) begin
                $display("TEST_FAIL sample output did not become valid");
                $finish;
              end
              if (
                sample_state !== expected_state ||
                sample_action !== expected_action ||
                sample_reward !== expected_reward ||
                sample_next_state !== expected_next_state ||
                sample_done !== expected_done
              ) begin
                $display(
                  "TEST_FAIL expected s=%0d a=%0d r=%0d ns=%0d d=%0d got s=%0d a=%0d r=%0d ns=%0d d=%0d",
                  expected_state,
                  expected_action,
                  expected_reward,
                  expected_next_state,
                  expected_done,
                  sample_state,
                  sample_action,
                  sample_reward,
                  sample_next_state,
                  sample_done
                );
                $finish;
              end
              @(posedge clk);
              #1;
            end
          endtask

          initial begin
            rst_n = 1'b0;
            host_valid = 1'b0;
            host_state = {width}'d0;
            host_action = 1'b0;
            host_reward = {width}'d0;
            host_next_state = {width}'d0;
            host_done = 1'b0;
            sample_ready = 1'b0;
            repeat (2) @(posedge clk);
            rst_n = 1'b1;

            write_sample({width}'d3, 1'b1, {width}'d4, {width}'d5, 1'b0);
            write_sample({width}'d8, 1'b0, {width}'d2, {width}'d9, 1'b1);
            write_sample({width}'d1, 1'b1, {width}'d7, {width}'d6, 1'b0);
            @(posedge clk);
            #1;
            if (occupancy !== 3'd3) begin
              $display("TEST_FAIL expected occupancy 3 got %0d", occupancy);
              $finish;
            end

            sample_ready = 1'b1;
            expect_sample({width}'d3, 1'b1, {width}'d4, {width}'d5, 1'b0);
            expect_sample({width}'d8, 1'b0, {width}'d2, {width}'d9, 1'b1);
            expect_sample({width}'d1, 1'b1, {width}'d7, {width}'d6, 1'b0);
            @(posedge clk);
            #1;
            if (occupancy !== 3'd0) begin
              $display("TEST_FAIL expected occupancy 0 got %0d", occupancy);
              $finish;
            end

            $display("TEST_PASS");
            $finish;
          end
        endmodule
        """
    )


def composed_host_protocol_shell_testbench(width: int) -> str:
    msb = width - 1
    stream_msb = width * 2 - 1
    return dedent(
        f"""\
        `timescale 1ns/1ps

        module tb_top;
          reg clk;
          reg rst_n;
          reg s_axi_awvalid;
          wire s_axi_awready;
          reg [3:0] s_axi_awaddr;
          reg s_axi_wvalid;
          wire s_axi_wready;
          reg [{msb}:0] s_axi_wdata;
          reg s_axi_wstrb;
          wire s_axi_bvalid;
          reg s_axi_bready;
          reg s_axi_arvalid;
          wire s_axi_arready;
          reg [3:0] s_axi_araddr;
          wire s_axi_rvalid;
          reg s_axi_rready;
          wire [{msb}:0] s_axi_rdata;
          wire m_axis_tvalid;
          reg m_axis_tready;
          wire [{stream_msb}:0] m_axis_tdata;
          wire m_axis_tlast;
          wire irq;
          integer wait_cycles;

          top dut (
            .clk(clk),
            .rst_n(rst_n),
            .s_axi_awvalid(s_axi_awvalid),
            .s_axi_awready(s_axi_awready),
            .s_axi_awaddr(s_axi_awaddr),
            .s_axi_wvalid(s_axi_wvalid),
            .s_axi_wready(s_axi_wready),
            .s_axi_wdata(s_axi_wdata),
            .s_axi_wstrb(s_axi_wstrb),
            .s_axi_bvalid(s_axi_bvalid),
            .s_axi_bready(s_axi_bready),
            .s_axi_arvalid(s_axi_arvalid),
            .s_axi_arready(s_axi_arready),
            .s_axi_araddr(s_axi_araddr),
            .s_axi_rvalid(s_axi_rvalid),
            .s_axi_rready(s_axi_rready),
            .s_axi_rdata(s_axi_rdata),
            .m_axis_tvalid(m_axis_tvalid),
            .m_axis_tready(m_axis_tready),
            .m_axis_tdata(m_axis_tdata),
            .m_axis_tlast(m_axis_tlast),
            .irq(irq)
          );

          initial begin
            clk = 1'b0;
            forever #5 clk = ~clk;
          end

          task axi_write;
            input [3:0] addr_i;
            input [{msb}:0] data_i;
            begin
              @(negedge clk);
              s_axi_awvalid = 1'b1;
              s_axi_awaddr = addr_i;
              s_axi_wvalid = 1'b1;
              s_axi_wdata = data_i;
              s_axi_wstrb = 1'b1;
              s_axi_bready = 1'b1;
              while (!s_axi_awready || !s_axi_wready) begin
                @(negedge clk);
              end
              @(negedge clk);
              s_axi_awvalid = 1'b0;
              s_axi_wvalid = 1'b0;
              while (!s_axi_bvalid) begin
                @(negedge clk);
              end
              @(negedge clk);
              s_axi_bready = 1'b0;
            end
          endtask

          task axi_read_expect;
            input [3:0] addr_i;
            input [{msb}:0] mask_i;
            input [{msb}:0] expected_i;
            begin
              @(negedge clk);
              s_axi_arvalid = 1'b1;
              s_axi_araddr = addr_i;
              s_axi_rready = 1'b1;
              while (!s_axi_arready) begin
                @(negedge clk);
              end
              @(negedge clk);
              s_axi_arvalid = 1'b0;
              wait_cycles = 0;
              while (!s_axi_rvalid && wait_cycles < 16) begin
                @(posedge clk);
                #1;
                wait_cycles = wait_cycles + 1;
              end
              if (!s_axi_rvalid) begin
                $display("TEST_FAIL read response did not become valid");
                $finish;
              end
              if ((s_axi_rdata & mask_i) !== expected_i) begin
                $display("TEST_FAIL expected read masked %0h got %0h", expected_i, s_axi_rdata & mask_i);
                $finish;
              end
              @(negedge clk);
              s_axi_rready = 1'b0;
            end
          endtask

          initial begin
            rst_n = 1'b0;
            s_axi_awvalid = 1'b0;
            s_axi_awaddr = 4'h0;
            s_axi_wvalid = 1'b0;
            s_axi_wdata = {width}'h00;
            s_axi_wstrb = 1'b0;
            s_axi_bready = 1'b0;
            s_axi_arvalid = 1'b0;
            s_axi_araddr = 4'h0;
            s_axi_rready = 1'b0;
            m_axis_tready = 1'b1;
            repeat (2) @(posedge clk);
            rst_n = 1'b1;

            axi_write(4'h4, {width}'h12);
            axi_write(4'h8, {width}'h34);
            axi_write(4'h0, {width}'h01);

            wait_cycles = 0;
            while (!m_axis_tvalid && wait_cycles < 16) begin
              @(posedge clk);
              #1;
              wait_cycles = wait_cycles + 1;
            end
            if (!m_axis_tvalid || m_axis_tdata !== {width * 2}'h3412 || m_axis_tlast !== 1'b1) begin
              $display("TEST_FAIL expected stream payload 0x3412 got valid=%0d data=%0h last=%0d",
                       m_axis_tvalid, m_axis_tdata, m_axis_tlast);
              $finish;
            end
            repeat (2) @(posedge clk);
            #1;
            if (irq !== 1'b1) begin
              $display("TEST_FAIL expected irq set");
              $finish;
            end

            axi_read_expect(4'hc, {width}'h06, {width}'h06);
            axi_write(4'h0, {width}'h02);
            axi_read_expect(4'hc, {width}'h04, {width}'h00);

            $display("TEST_PASS");
            $finish;
          end
        endmodule
        """
    )


def composed_rl_accelerator_shell_testbench(width: int) -> str:
    msb = width - 1
    legacy = dedent(
        f"""\
        `timescale 1ns/1ps

        module tb_top;
          reg clk;
          reg rst_n;
          reg cfg_valid;
          wire cfg_ready;
          reg [2:0] cfg_addr;
          reg [{msb}:0] cfg_data;
          reg sample_valid;
          wire sample_ready;
          reg [{msb}:0] obs0;
          reg [{msb}:0] obs1;
          reg [{msb}:0] reward;
          reg [{msb}:0] next_value;
          reg done_in;
          wire result_valid;
          reg result_ready;
          wire selected_action;
          wire [{msb}:0] value_estimate;
          wire [{msb}:0] updated_value;
          wire episode_done;
          wire irq;
          integer wait_cycles;

          top dut (
            .clk(clk),
            .rst_n(rst_n),
            .cfg_valid(cfg_valid),
            .cfg_ready(cfg_ready),
            .cfg_addr(cfg_addr),
            .cfg_data(cfg_data),
            .sample_valid(sample_valid),
            .sample_ready(sample_ready),
            .obs0(obs0),
            .obs1(obs1),
            .reward(reward),
            .next_value(next_value),
            .done_in(done_in),
            .result_valid(result_valid),
            .result_ready(result_ready),
            .selected_action(selected_action),
            .value_estimate(value_estimate),
            .updated_value(updated_value),
            .episode_done(episode_done),
            .irq(irq)
          );

          initial begin
            clk = 1'b0;
            forever #5 clk = ~clk;
          end

          task write_cfg;
            input [2:0] addr_i;
            input [{msb}:0] data_i;
            begin
              @(negedge clk);
              cfg_valid = 1'b1;
              cfg_addr = addr_i;
              cfg_data = data_i;
              while (!cfg_ready) begin
                @(negedge clk);
              end
              @(negedge clk);
              cfg_valid = 1'b0;
            end
          endtask

          task send_sample;
            input [{msb}:0] obs0_i;
            input [{msb}:0] obs1_i;
            input [{msb}:0] reward_i;
            input [{msb}:0] next_value_i;
            input done_i;
            begin
              @(negedge clk);
              sample_valid = 1'b1;
              obs0 = obs0_i;
              obs1 = obs1_i;
              reward = reward_i;
              next_value = next_value_i;
              done_in = done_i;
              while (!sample_ready) begin
                @(negedge clk);
              end
              @(negedge clk);
              sample_valid = 1'b0;
            end
          endtask

          task expect_result;
            input expected_action;
            input [{msb}:0] expected_value;
            input [{msb}:0] expected_updated;
            input expected_done;
            begin
              wait_cycles = 0;
              while (!result_valid && wait_cycles < 16) begin
                @(posedge clk);
                #1;
                wait_cycles = wait_cycles + 1;
              end
              if (!result_valid) begin
                $display("TEST_FAIL result did not become valid");
                $finish;
              end
              if (selected_action !== expected_action ||
                  value_estimate !== expected_value ||
                  updated_value !== expected_updated ||
                  episode_done !== expected_done) begin
                $display("TEST_FAIL expected action=%0d value=%0d updated=%0d done=%0d got action=%0d value=%0d updated=%0d done=%0d",
                         expected_action, expected_value, expected_updated, expected_done,
                         selected_action, value_estimate, updated_value, episode_done);
                $finish;
              end
              @(posedge clk);
              #1;
            end
          endtask

          initial begin
            rst_n = 1'b0;
            cfg_valid = 1'b0;
            cfg_addr = 3'd0;
            cfg_data = {width}'d0;
            sample_valid = 1'b0;
            obs0 = {width}'d0;
            obs1 = {width}'d0;
            reward = {width}'d0;
            next_value = {width}'d0;
            done_in = 1'b0;
            result_ready = 1'b1;
            repeat (2) @(posedge clk);
            rst_n = 1'b1;

            write_cfg(3'd0, {width}'d2);
            write_cfg(3'd1, {width}'d1);
            write_cfg(3'd2, {width}'d3);
            write_cfg(3'd3, {width}'d0);
            write_cfg(3'd4, {width}'d4);
            write_cfg(3'd5, {width}'d1);

            send_sample({width}'d4, {width}'d2, {width}'d1, {width}'d8, 1'b0);
            expect_result(1'b0, 8'd7, 8'd7, 1'b0);

            send_sample({width}'d1, {width}'d5, {width}'d2, {width}'d15, 1'b1);
            expect_result(1'b1, 8'd9, 8'd11, 1'b1);

            if (irq !== 1'b1) begin
              $display("TEST_FAIL expected irq after done result");
              $finish;
            end

            $display("TEST_PASS");
            $finish;
          end
        endmodule
        """
    )
    return _add_rl_accelerator_oracle_mode(legacy, width)


def _add_td_oracle_mode(testbench: str, width: int) -> str:
    input_width = (5 * width) + 3
    expected_width = 2 * width
    reset_bit = 5 * width
    stall_lsb = reset_bit + 1
    declarations = dedent(
        f"""\
          string oracle_input_path;
          string oracle_expected_path;
          string oracle_scenario_id;
          string oracle_scenario_class;
          integer oracle_transaction_count;
          integer oracle_mode;
          reg [{input_width - 1}:0] oracle_input_memory [0:4095];
          reg [{expected_width - 1}:0] oracle_expected_memory [0:4095];
          reg [{input_width - 1}:0] oracle_input_record;
          reg [{expected_width - 1}:0] oracle_expected_record;
          reg signed [{width - 1}:0] oracle_held_error;
          reg signed [{width - 1}:0] oracle_held_value;
          integer oracle_wait_count;
          integer oracle_stall_index;
          integer oracle_stall_cycles;
        """
    )
    testbench = _rl_insert_after_once(testbench, "  integer wait_cycles;\n", declarations)
    task_marker = "  initial begin\n    rst_n = 1'b0;\n"
    testbench = _rl_insert_before_once(
        testbench,
        task_marker,
        _td_oracle_driver_task(width, reset_bit, stall_lsb),
    )
    oracle_start = dedent(
        """\
            oracle_mode = $value$plusargs("ORACLE_INPUT=%s", oracle_input_path) &&
                $value$plusargs("ORACLE_EXPECTED=%s", oracle_expected_path) &&
                $value$plusargs("ORACLE_SCENARIO_ID=%s", oracle_scenario_id) &&
                $value$plusargs("ORACLE_SCENARIO_CLASS=%s", oracle_scenario_class) &&
                $value$plusargs("ORACLE_TRANSACTION_COUNT=%d", oracle_transaction_count);
            if (oracle_mode) begin
              run_td_oracle_scenario;
            end
        """
    )
    return _rl_insert_after_once(testbench, task_marker, oracle_start)


def _td_oracle_driver_task(width: int, reset_bit: int, stall_lsb: int) -> str:
    return dedent(
        rf"""
          task run_td_oracle_scenario;
            integer oracle_item_index;
            begin
              if (oracle_transaction_count <= 0 || oracle_transaction_count > 4096) begin
                $display("ORACLE_ERROR invalid RL TD transaction count=%0d", oracle_transaction_count);
                $finish;
              end
              $readmemh(oracle_input_path, oracle_input_memory, 0, oracle_transaction_count - 1);
              $readmemh(oracle_expected_path, oracle_expected_memory, 0, oracle_transaction_count - 1);
              rst_n = 1'b0;
              in_valid = 1'b0;
              reward = {width}'sd0;
              value = {width}'sd0;
              next_value = {width}'sd0;
              gamma = {width}'d0;
              alpha = {width}'d0;
              out_ready = 1'b0;
              repeat (2) @(posedge clk);
              @(negedge clk);
              rst_n = 1'b1;
              for (oracle_item_index = 0; oracle_item_index < oracle_transaction_count;
                   oracle_item_index = oracle_item_index + 1) begin
                oracle_input_record = oracle_input_memory[oracle_item_index];
                oracle_expected_record = oracle_expected_memory[oracle_item_index];
                if (oracle_input_record[{reset_bit}]) begin
                  @(negedge clk);
                  rst_n = 1'b0;
                  in_valid = 1'b0;
                  out_ready = 1'b0;
                  repeat (2) @(posedge clk);
                  if (out_valid !== 1'b0) begin
                    $display("SR2FPGA_MISMATCH {{\"scenario_id\":\"%0s\",\"class\":\"%0s\",\"item_index\":%0d,\"field\":\"reset_out_valid\",\"expected\":0,\"actual\":\"%0b\"}}",
                             oracle_scenario_id, oracle_scenario_class, oracle_item_index, out_valid);
                    $display("TEST_FAIL reset did not clear output valid");
                    $finish;
                  end
                  @(negedge clk);
                  rst_n = 1'b1;
                end
                out_ready = 1'b0;
                in_valid = 1'b1;
                reward = oracle_input_record[{width - 1}:0];
                value = oracle_input_record[{(2 * width) - 1}:{width}];
                next_value = oracle_input_record[{(3 * width) - 1}:{2 * width}];
                gamma = oracle_input_record[{(4 * width) - 1}:{3 * width}];
                alpha = oracle_input_record[{(5 * width) - 1}:{4 * width}];
                oracle_wait_count = 0;
                while (in_ready !== 1'b1 && oracle_wait_count < 500) begin
                  @(negedge clk);
                  oracle_wait_count = oracle_wait_count + 1;
                end
                if (in_ready !== 1'b1) begin
                  $display("SR2FPGA_MISMATCH {{\"scenario_id\":\"%0s\",\"class\":\"%0s\",\"item_index\":%0d,\"field\":\"in_ready\",\"expected\":1,\"actual\":\"%0b\"}}",
                           oracle_scenario_id, oracle_scenario_class, oracle_item_index, in_ready);
                  $display("TEST_FAIL input timeout");
                  $finish;
                end
                @(posedge clk);
                @(negedge clk);
                in_valid = 1'b0;
                oracle_wait_count = 0;
                while (out_valid !== 1'b1 && oracle_wait_count < 500) begin
                  @(posedge clk);
                  #1;
                  oracle_wait_count = oracle_wait_count + 1;
                end
                if (out_valid !== 1'b1) begin
                  $display("SR2FPGA_MISMATCH {{\"scenario_id\":\"%0s\",\"class\":\"%0s\",\"item_index\":%0d,\"field\":\"out_valid\",\"expected\":1,\"actual\":\"%0b\"}}",
                           oracle_scenario_id, oracle_scenario_class, oracle_item_index, out_valid);
                  $display("TEST_FAIL output timeout");
                  $finish;
                end
                if (td_error !== oracle_expected_record[{width - 1}:0] ||
                    updated_value !== oracle_expected_record[{(2 * width) - 1}:{width}]) begin
                  $display("SR2FPGA_MISMATCH {{\"scenario_id\":\"%0s\",\"class\":\"%0s\",\"item_index\":%0d,\"expected\":{{\"td_error\":%0d,\"updated_value\":%0d}},\"actual\":{{\"td_error\":%0d,\"updated_value\":%0d}}}}",
                           oracle_scenario_id, oracle_scenario_class, oracle_item_index,
                           $signed(oracle_expected_record[{width - 1}:0]),
                           $signed(oracle_expected_record[{(2 * width) - 1}:{width}]),
                           td_error, updated_value);
                  $display("TEST_FAIL functional mismatch");
                  $finish;
                end
                oracle_held_error = td_error;
                oracle_held_value = updated_value;
                oracle_stall_cycles = oracle_input_record[{stall_lsb + 1}:{stall_lsb}];
                if (oracle_stall_cycles > 0) begin
                  for (oracle_stall_index = 0; oracle_stall_index < oracle_stall_cycles;
                       oracle_stall_index = oracle_stall_index + 1) begin
                    @(posedge clk);
                    #1;
                    if (td_error !== oracle_held_error || updated_value !== oracle_held_value ||
                        out_valid !== 1'b1) begin
                      $display("SR2FPGA_MISMATCH {{\"scenario_id\":\"%0s\",\"class\":\"%0s\",\"item_index\":%0d,\"field\":\"output_stability\",\"expected\":\"stable\",\"actual\":\"changed\"}}",
                               oracle_scenario_id, oracle_scenario_class, oracle_item_index);
                      $display("TEST_FAIL output changed under stall");
                      $finish;
                    end
                  end
                end
                out_ready = 1'b1;
                @(posedge clk);
                #1;
                @(negedge clk);
                out_ready = 1'b0;
              end
              $display("TEST_PASS");
              $finish;
            end
          endtask

        """
    )


def _add_rl_accelerator_oracle_mode(testbench: str, width: int) -> str:
    input_width = (5 * width) + 8
    expected_width = (2 * width) + 4
    declarations = dedent(
        f"""\
          string oracle_input_path;
          string oracle_expected_path;
          string oracle_scenario_id;
          string oracle_scenario_class;
          integer oracle_transaction_count;
          integer oracle_mode;
          reg [{input_width - 1}:0] oracle_input_memory [0:4095];
          reg [{expected_width - 1}:0] oracle_expected_memory [0:4095];
          reg [{input_width - 1}:0] oracle_input_record;
          reg [{expected_width - 1}:0] oracle_expected_record;
          reg oracle_held_action;
          reg [{width - 1}:0] oracle_held_value;
          reg [{width - 1}:0] oracle_held_updated;
          reg oracle_held_done;
          integer oracle_wait_count;
          integer oracle_stall_index;
          integer oracle_stall_cycles;
        """
    )
    testbench = _rl_insert_after_once(testbench, "  integer wait_cycles;\n", declarations)
    task_marker = "  initial begin\n    rst_n = 1'b0;\n"
    testbench = _rl_insert_before_once(
        testbench,
        task_marker,
        _rl_accelerator_oracle_driver_task(width),
    )
    oracle_start = dedent(
        """\
            oracle_mode = $value$plusargs("ORACLE_INPUT=%s", oracle_input_path) &&
                $value$plusargs("ORACLE_EXPECTED=%s", oracle_expected_path) &&
                $value$plusargs("ORACLE_SCENARIO_ID=%s", oracle_scenario_id) &&
                $value$plusargs("ORACLE_SCENARIO_CLASS=%s", oracle_scenario_class) &&
                $value$plusargs("ORACLE_TRANSACTION_COUNT=%d", oracle_transaction_count);
            if (oracle_mode) begin
              run_rl_oracle_scenario;
            end
        """
    )
    return _rl_insert_after_once(testbench, task_marker, oracle_start)


def _rl_accelerator_oracle_driver_task(width: int) -> str:
    cfg_data_lsb = 5
    obs0_lsb = cfg_data_lsb + width
    obs1_lsb = obs0_lsb + width
    reward_lsb = obs1_lsb + width
    next_value_lsb = reward_lsb + width
    done_bit = next_value_lsb + width
    stall_lsb = done_bit + 1
    value_lsb = 2
    updated_lsb = value_lsb + width
    episode_done_bit = updated_lsb + width
    irq_bit = episode_done_bit + 1
    return dedent(
        rf"""
          task run_rl_oracle_scenario;
            integer oracle_item_index;
            begin
              if (oracle_transaction_count <= 0 || oracle_transaction_count > 4096) begin
                $display("ORACLE_ERROR invalid RL accelerator transaction count=%0d", oracle_transaction_count);
                $finish;
              end
              $readmemh(oracle_input_path, oracle_input_memory, 0, oracle_transaction_count - 1);
              $readmemh(oracle_expected_path, oracle_expected_memory, 0, oracle_transaction_count - 1);
              rst_n = 1'b0;
              cfg_valid = 1'b0;
              cfg_addr = 3'd0;
              cfg_data = {width}'d0;
              sample_valid = 1'b0;
              obs0 = {width}'d0;
              obs1 = {width}'d0;
              reward = {width}'d0;
              next_value = {width}'d0;
              done_in = 1'b0;
              result_ready = 1'b0;
              repeat (2) @(posedge clk);
              @(negedge clk);
              rst_n = 1'b1;
              for (oracle_item_index = 0; oracle_item_index < oracle_transaction_count;
                   oracle_item_index = oracle_item_index + 1) begin
                oracle_input_record = oracle_input_memory[oracle_item_index];
                oracle_expected_record = oracle_expected_memory[oracle_item_index];
                case (oracle_input_record[1:0])
                  2'd0: begin
                    @(negedge clk);
                    rst_n = 1'b0;
                    cfg_valid = 1'b0;
                    sample_valid = 1'b0;
                    result_ready = 1'b0;
                    repeat (2) @(posedge clk);
                    #1;
                    if (result_valid !== 1'b0 || irq !== oracle_expected_record[{irq_bit}]) begin
                      $display("SR2FPGA_MISMATCH {{\"scenario_id\":\"%0s\",\"class\":\"%0s\",\"item_index\":%0d,\"field\":\"reset_state\",\"expected\":{{\"result_valid\":0,\"irq\":%0d}},\"actual\":{{\"result_valid\":\"%0b\",\"irq\":\"%0b\"}}}}",
                               oracle_scenario_id, oracle_scenario_class, oracle_item_index,
                               oracle_expected_record[{irq_bit}], result_valid, irq);
                      $display("TEST_FAIL reset did not clear result/irq");
                      $finish;
                    end
                    @(negedge clk);
                    rst_n = 1'b1;
                  end
                  2'd1: begin
                    @(negedge clk);
                    cfg_valid = 1'b1;
                    cfg_addr = oracle_input_record[4:2];
                    cfg_data = oracle_input_record[{cfg_data_lsb + width - 1}:{cfg_data_lsb}];
                    oracle_wait_count = 0;
                    while (cfg_ready !== 1'b1 && oracle_wait_count < 500) begin
                      @(negedge clk);
                      oracle_wait_count = oracle_wait_count + 1;
                    end
                    if (cfg_ready !== 1'b1) begin
                      $display("SR2FPGA_MISMATCH {{\"scenario_id\":\"%0s\",\"class\":\"%0s\",\"item_index\":%0d,\"field\":\"cfg_ready\",\"expected\":1,\"actual\":\"%0b\"}}",
                               oracle_scenario_id, oracle_scenario_class, oracle_item_index, cfg_ready);
                      $display("TEST_FAIL config timeout");
                      $finish;
                    end
                    @(posedge clk);
                    @(negedge clk);
                    cfg_valid = 1'b0;
                    if (irq !== oracle_expected_record[{irq_bit}]) begin
                      $display("SR2FPGA_MISMATCH {{\"scenario_id\":\"%0s\",\"class\":\"%0s\",\"item_index\":%0d,\"field\":\"irq_after_config\",\"expected\":%0d,\"actual\":\"%0b\"}}",
                               oracle_scenario_id, oracle_scenario_class, oracle_item_index,
                               oracle_expected_record[{irq_bit}], irq);
                      $display("TEST_FAIL irq changed on config write");
                      $finish;
                    end
                  end
                  2'd2: begin
                    result_ready = 1'b0;
                    @(negedge clk);
                    sample_valid = 1'b1;
                    obs0 = oracle_input_record[{obs0_lsb + width - 1}:{obs0_lsb}];
                    obs1 = oracle_input_record[{obs1_lsb + width - 1}:{obs1_lsb}];
                    reward = oracle_input_record[{reward_lsb + width - 1}:{reward_lsb}];
                    next_value = oracle_input_record[{next_value_lsb + width - 1}:{next_value_lsb}];
                    done_in = oracle_input_record[{done_bit}];
                    oracle_wait_count = 0;
                    while (sample_ready !== 1'b1 && oracle_wait_count < 500) begin
                      @(negedge clk);
                      oracle_wait_count = oracle_wait_count + 1;
                    end
                    if (sample_ready !== 1'b1) begin
                      $display("SR2FPGA_MISMATCH {{\"scenario_id\":\"%0s\",\"class\":\"%0s\",\"item_index\":%0d,\"field\":\"sample_ready\",\"expected\":1,\"actual\":\"%0b\"}}",
                               oracle_scenario_id, oracle_scenario_class, oracle_item_index, sample_ready);
                      $display("TEST_FAIL sample timeout");
                      $finish;
                    end
                    @(posedge clk);
                    @(negedge clk);
                    sample_valid = 1'b0;
                    if (!oracle_expected_record[0]) begin
                      repeat (8) begin
                        @(posedge clk);
                        #1;
                        if (result_valid === 1'b1) begin
                          $display("SR2FPGA_MISMATCH {{\"scenario_id\":\"%0s\",\"class\":\"%0s\",\"item_index\":%0d,\"field\":\"disabled_output\",\"expected\":0,\"actual\":1}}",
                                   oracle_scenario_id, oracle_scenario_class, oracle_item_index);
                          $display("TEST_FAIL disabled accelerator emitted output");
                          $finish;
                        end
                      end
                      if (irq !== oracle_expected_record[{irq_bit}]) begin
                        $display("SR2FPGA_MISMATCH {{\"scenario_id\":\"%0s\",\"class\":\"%0s\",\"item_index\":%0d,\"field\":\"disabled_irq\",\"expected\":%0d,\"actual\":\"%0b\"}}",
                                 oracle_scenario_id, oracle_scenario_class, oracle_item_index,
                                 oracle_expected_record[{irq_bit}], irq);
                        $display("TEST_FAIL disabled accelerator changed irq");
                        $finish;
                      end
                    end else begin
                      oracle_wait_count = 0;
                      while (result_valid !== 1'b1 && oracle_wait_count < 500) begin
                        @(posedge clk);
                        #1;
                        oracle_wait_count = oracle_wait_count + 1;
                      end
                      if (result_valid !== 1'b1) begin
                        $display("SR2FPGA_MISMATCH {{\"scenario_id\":\"%0s\",\"class\":\"%0s\",\"item_index\":%0d,\"field\":\"result_valid\",\"expected\":1,\"actual\":\"%0b\"}}",
                                 oracle_scenario_id, oracle_scenario_class, oracle_item_index, result_valid);
                        $display("TEST_FAIL result timeout");
                        $finish;
                      end
                      if (selected_action !== oracle_expected_record[1] ||
                          value_estimate !== oracle_expected_record[{value_lsb + width - 1}:{value_lsb}] ||
                          updated_value !== oracle_expected_record[{updated_lsb + width - 1}:{updated_lsb}] ||
                          episode_done !== oracle_expected_record[{episode_done_bit}]) begin
                        $display("SR2FPGA_MISMATCH {{\"scenario_id\":\"%0s\",\"class\":\"%0s\",\"item_index\":%0d,\"expected\":{{\"selected_action\":%0d,\"value_estimate\":%0d,\"updated_value\":%0d,\"episode_done\":%0d}},\"actual\":{{\"selected_action\":\"%0b\",\"value_estimate\":%0d,\"updated_value\":%0d,\"episode_done\":\"%0b\"}}}}",
                                 oracle_scenario_id, oracle_scenario_class, oracle_item_index,
                                 oracle_expected_record[1],
                                 oracle_expected_record[{value_lsb + width - 1}:{value_lsb}],
                                 oracle_expected_record[{updated_lsb + width - 1}:{updated_lsb}],
                                 oracle_expected_record[{episode_done_bit}],
                                 selected_action, value_estimate, updated_value, episode_done);
                        $display("TEST_FAIL functional mismatch");
                        $finish;
                      end
                      oracle_held_action = selected_action;
                      oracle_held_value = value_estimate;
                      oracle_held_updated = updated_value;
                      oracle_held_done = episode_done;
                      oracle_stall_cycles = oracle_input_record[{stall_lsb + 1}:{stall_lsb}];
                      if (oracle_stall_cycles > 0) begin
                        for (oracle_stall_index = 0; oracle_stall_index < oracle_stall_cycles;
                             oracle_stall_index = oracle_stall_index + 1) begin
                          @(posedge clk);
                          #1;
                          if (selected_action !== oracle_held_action || value_estimate !== oracle_held_value ||
                              updated_value !== oracle_held_updated || episode_done !== oracle_held_done ||
                              result_valid !== 1'b1) begin
                            $display("SR2FPGA_MISMATCH {{\"scenario_id\":\"%0s\",\"class\":\"%0s\",\"item_index\":%0d,\"field\":\"output_stability\",\"expected\":\"stable\",\"actual\":\"changed\"}}",
                                     oracle_scenario_id, oracle_scenario_class, oracle_item_index);
                            $display("TEST_FAIL output changed under stall");
                            $finish;
                          end
                        end
                      end
                      result_ready = 1'b1;
                      @(posedge clk);
                      #1;
                      if (irq !== oracle_expected_record[{irq_bit}]) begin
                        $display("SR2FPGA_MISMATCH {{\"scenario_id\":\"%0s\",\"class\":\"%0s\",\"item_index\":%0d,\"field\":\"irq\",\"expected\":%0d,\"actual\":\"%0b\"}}",
                                 oracle_scenario_id, oracle_scenario_class, oracle_item_index,
                                 oracle_expected_record[{irq_bit}], irq);
                        $display("TEST_FAIL irq mismatch");
                        $finish;
                      end
                      @(negedge clk);
                      result_ready = 1'b0;
                    end
                  end
                  default: begin
                    $display("ORACLE_ERROR unsupported RL operation=%0d", oracle_input_record[1:0]);
                    $finish;
                  end
                endcase
              end
              $display("TEST_PASS");
              $finish;
            end
          endtask

        """
    )


def _rl_insert_after_once(source: str, marker: str, addition: str) -> str:
    if source.count(marker) != 1:
        raise RuntimeError(f"expected one RL testbench marker, found {source.count(marker)}")
    return source.replace(marker, marker + addition, 1)


def _rl_insert_before_once(source: str, marker: str, addition: str) -> str:
    if source.count(marker) != 1:
        raise RuntimeError(f"expected one RL testbench marker, found {source.count(marker)}")
    return source.replace(marker, addition + marker, 1)


def composed_batch_rl_accelerator_shell_testbench(width: int) -> str:
    msb = width - 1
    return dedent(
        f"""\
        `timescale 1ns/1ps

        module tb_top;
          reg clk;
          reg rst_n;
          reg cfg_valid;
          wire cfg_ready;
          reg [2:0] cfg_addr;
          reg [{msb}:0] cfg_data;
          reg batch_valid;
          wire batch_ready;
          reg [{msb}:0] obs0_a;
          reg [{msb}:0] obs1_a;
          reg [{msb}:0] reward_a;
          reg [{msb}:0] next_value_a;
          reg done_a;
          reg [{msb}:0] obs0_b;
          reg [{msb}:0] obs1_b;
          reg [{msb}:0] reward_b;
          reg [{msb}:0] next_value_b;
          reg done_b;
          wire result_valid;
          reg result_ready;
          wire selected_action_a;
          wire [{msb}:0] value_estimate_a;
          wire [{msb}:0] updated_value_a;
          wire selected_action_b;
          wire [{msb}:0] value_estimate_b;
          wire [{msb}:0] updated_value_b;
          wire batch_done;
          wire irq;
          integer wait_cycles;

          top dut (
            .clk(clk),
            .rst_n(rst_n),
            .cfg_valid(cfg_valid),
            .cfg_ready(cfg_ready),
            .cfg_addr(cfg_addr),
            .cfg_data(cfg_data),
            .batch_valid(batch_valid),
            .batch_ready(batch_ready),
            .obs0_a(obs0_a),
            .obs1_a(obs1_a),
            .reward_a(reward_a),
            .next_value_a(next_value_a),
            .done_a(done_a),
            .obs0_b(obs0_b),
            .obs1_b(obs1_b),
            .reward_b(reward_b),
            .next_value_b(next_value_b),
            .done_b(done_b),
            .result_valid(result_valid),
            .result_ready(result_ready),
            .selected_action_a(selected_action_a),
            .value_estimate_a(value_estimate_a),
            .updated_value_a(updated_value_a),
            .selected_action_b(selected_action_b),
            .value_estimate_b(value_estimate_b),
            .updated_value_b(updated_value_b),
            .batch_done(batch_done),
            .irq(irq)
          );

          initial begin
            clk = 1'b0;
            forever #5 clk = ~clk;
          end

          task write_cfg;
            input [2:0] addr_i;
            input [{msb}:0] data_i;
            begin
              @(negedge clk);
              cfg_valid = 1'b1;
              cfg_addr = addr_i;
              cfg_data = data_i;
              while (!cfg_ready) begin
                @(negedge clk);
              end
              @(negedge clk);
              cfg_valid = 1'b0;
            end
          endtask

          task send_batch;
            begin
              @(negedge clk);
              batch_valid = 1'b1;
              obs0_a = {width}'d4;
              obs1_a = {width}'d2;
              reward_a = {width}'d1;
              next_value_a = {width}'d8;
              done_a = 1'b0;
              obs0_b = {width}'d1;
              obs1_b = {width}'d5;
              reward_b = {width}'d2;
              next_value_b = {width}'d15;
              done_b = 1'b1;
              while (!batch_ready) begin
                @(negedge clk);
              end
              @(negedge clk);
              batch_valid = 1'b0;
            end
          endtask

          task expect_batch_result;
            input expected_action_a;
            input [{msb}:0] expected_value_a;
            input [{msb}:0] expected_updated_a;
            input expected_action_b;
            input [{msb}:0] expected_value_b;
            input [{msb}:0] expected_updated_b;
            input expected_batch_done;
            begin
              wait_cycles = 0;
              while (!result_valid && wait_cycles < 16) begin
                @(posedge clk);
                #1;
                wait_cycles = wait_cycles + 1;
              end
              if (!result_valid) begin
                $display("TEST_FAIL batch result did not become valid");
                $finish;
              end
              if (selected_action_a !== expected_action_a ||
                  value_estimate_a !== expected_value_a ||
                  updated_value_a !== expected_updated_a ||
                  selected_action_b !== expected_action_b ||
                  value_estimate_b !== expected_value_b ||
                  updated_value_b !== expected_updated_b ||
                  batch_done !== expected_batch_done) begin
                $display("TEST_FAIL unexpected batch result");
                $finish;
              end
              @(posedge clk);
              #1;
            end
          endtask

          initial begin
            rst_n = 1'b0;
            cfg_valid = 1'b0;
            cfg_addr = 3'd0;
            cfg_data = {width}'d0;
            batch_valid = 1'b0;
            obs0_a = {width}'d0;
            obs1_a = {width}'d0;
            reward_a = {width}'d0;
            next_value_a = {width}'d0;
            done_a = 1'b0;
            obs0_b = {width}'d0;
            obs1_b = {width}'d0;
            reward_b = {width}'d0;
            next_value_b = {width}'d0;
            done_b = 1'b0;
            result_ready = 1'b1;
            repeat (2) @(posedge clk);
            rst_n = 1'b1;

            write_cfg(3'd0, {width}'d2);
            write_cfg(3'd1, {width}'d1);
            write_cfg(3'd2, {width}'d3);
            write_cfg(3'd3, {width}'d0);
            write_cfg(3'd4, {width}'d4);
            write_cfg(3'd5, {width}'d1);

            send_batch();
            expect_batch_result(1'b0, 8'd7, 8'd7, 1'b1, 8'd9, 8'd11, 1'b1);

            if (irq !== 1'b1) begin
              $display("TEST_FAIL expected irq after batch done result");
              $finish;
            end

            $display("TEST_PASS");
            $finish;
          end
        endmodule
        """
    )


def composed_replay_arbiter_shell_testbench(width: int) -> str:
    msb = width - 1
    return dedent(
        f"""\
        `timescale 1ns/1ps

        module tb_top;
          reg clk;
          reg rst_n;
          reg host_valid;
          wire host_ready;
          reg [{msb}:0] host_state;
          reg host_action;
          reg [{msb}:0] host_reward;
          reg [{msb}:0] host_next_state;
          reg host_done;
          reg sample_req_valid;
          wire sample_req_ready;
          reg [1:0] sample_index;
          wire sample_valid;
          reg sample_ready;
          wire [{msb}:0] sample_state;
          wire sample_action;
          wire [{msb}:0] sample_reward;
          wire [{msb}:0] sample_next_state;
          wire sample_done;
          wire [2:0] occupancy;
          wire [1:0] write_index;
          wire irq;
          integer wait_cycles;

          top dut (
            .clk(clk),
            .rst_n(rst_n),
            .host_valid(host_valid),
            .host_ready(host_ready),
            .host_state(host_state),
            .host_action(host_action),
            .host_reward(host_reward),
            .host_next_state(host_next_state),
            .host_done(host_done),
            .sample_req_valid(sample_req_valid),
            .sample_req_ready(sample_req_ready),
            .sample_index(sample_index),
            .sample_valid(sample_valid),
            .sample_ready(sample_ready),
            .sample_state(sample_state),
            .sample_action(sample_action),
            .sample_reward(sample_reward),
            .sample_next_state(sample_next_state),
            .sample_done(sample_done),
            .occupancy(occupancy),
            .write_index(write_index),
            .irq(irq)
          );

          initial begin
            clk = 1'b0;
            forever #5 clk = ~clk;
          end

          task write_host_packet;
            input [{msb}:0] state_i;
            input action_i;
            input [{msb}:0] reward_i;
            input [{msb}:0] next_state_i;
            input done_i;
            begin
              @(negedge clk);
              host_valid = 1'b1;
              host_state = state_i;
              host_action = action_i;
              host_reward = reward_i;
              host_next_state = next_state_i;
              host_done = done_i;
              while (!host_ready) begin
                @(negedge clk);
              end
              @(negedge clk);
              host_valid = 1'b0;
            end
          endtask

          task request_sample;
            input [1:0] index_i;
            begin
              @(negedge clk);
              sample_req_valid = 1'b1;
              sample_index = index_i;
              while (!sample_req_ready) begin
                @(negedge clk);
              end
              @(negedge clk);
              sample_req_valid = 1'b0;
            end
          endtask

          task expect_sample;
            input [{msb}:0] expected_state;
            input expected_action;
            input [{msb}:0] expected_reward;
            input [{msb}:0] expected_next_state;
            input expected_done;
            begin
              wait_cycles = 0;
              while (!sample_valid && wait_cycles < 16) begin
                @(posedge clk);
                #1;
                wait_cycles = wait_cycles + 1;
              end
              if (!sample_valid) begin
                $display("TEST_FAIL sample did not become valid");
                $finish;
              end
              if (sample_state !== expected_state ||
                  sample_action !== expected_action ||
                  sample_reward !== expected_reward ||
                  sample_next_state !== expected_next_state ||
                  sample_done !== expected_done) begin
                $display("TEST_FAIL unexpected sample packet");
                $finish;
              end
              @(posedge clk);
              #1;
            end
          endtask

          initial begin
            rst_n = 1'b0;
            host_valid = 1'b0;
            host_state = {width}'h00;
            host_action = 1'b0;
            host_reward = {width}'h00;
            host_next_state = {width}'h00;
            host_done = 1'b0;
            sample_req_valid = 1'b0;
            sample_index = 2'd0;
            sample_ready = 1'b1;
            repeat (2) @(posedge clk);
            rst_n = 1'b1;

            write_host_packet(8'h12, 1'b0, 8'h03, 8'h21, 1'b0);
            write_host_packet(8'h34, 1'b1, 8'h05, 8'h43, 1'b1);

            if (occupancy !== 3'd2 || write_index !== 2'd2) begin
              $display("TEST_FAIL expected occupancy=2 write_index=2");
              $finish;
            end

            request_sample(2'd0);
            expect_sample(8'h12, 1'b0, 8'h03, 8'h21, 1'b0);

            request_sample(2'd1);
            expect_sample(8'h34, 1'b1, 8'h05, 8'h43, 1'b1);

            if (irq !== 1'b1) begin
              $display("TEST_FAIL expected irq after sample accepted");
              $finish;
            end

            $display("TEST_PASS");
            $finish;
          end
        endmodule
        """
    )


def composed_td_update_core_rtl_files(width: int) -> dict[str, str]:
    msb = width - 1
    top = dedent(
        f"""\
        module top (
            input wire clk,
            input wire rst_n,
            input wire in_valid,
            output wire in_ready,
            input wire signed [{msb}:0] reward,
            input wire signed [{msb}:0] value,
            input wire signed [{msb}:0] next_value,
            input wire [{msb}:0] gamma,
            input wire [{msb}:0] alpha,
            output wire out_valid,
            input wire out_ready,
            output wire signed [{msb}:0] td_error,
            output wire signed [{msb}:0] updated_value
        );

          wire input_valid;
          wire input_ready;
          wire signed [{msb}:0] reward_s;
          wire signed [{msb}:0] value_s;
          wire signed [{msb}:0] next_value_s;
          wire [{msb}:0] gamma_s;
          wire [{msb}:0] alpha_s;
          wire discount_valid;
          wire discount_ready;
          wire signed [{2 * width}:0] discounted_return;
          wire update_valid;
          wire update_ready;
          wire signed [{msb}:0] update_td_error;
          wire signed [{msb}:0] update_value;

          td_input_stage #(
            .DATA_WIDTH({width})
          ) u_td_input_stage (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(in_valid),
            .in_ready(in_ready),
            .reward(reward),
            .value(value),
            .next_value(next_value),
            .gamma(gamma),
            .alpha(alpha),
            .out_valid(input_valid),
            .out_ready(input_ready),
            .reward_out(reward_s),
            .value_out(value_s),
            .next_value_out(next_value_s),
            .gamma_out(gamma_s),
            .alpha_out(alpha_s)
          );

          discount_core #(
            .DATA_WIDTH({width}),
            .SCALE_SHIFT(4)
          ) u_discount_core (
            .in_valid(input_valid),
            .in_ready(input_ready),
            .reward(reward_s),
            .next_value(next_value_s),
            .gamma(gamma_s),
            .out_valid(discount_valid),
            .out_ready(discount_ready),
            .discounted_return(discounted_return)
          );

          td_update_core #(
            .DATA_WIDTH({width}),
            .SCALE_SHIFT(4)
          ) u_td_update_core (
            .in_valid(discount_valid),
            .in_ready(discount_ready),
            .discounted_return(discounted_return),
            .value(value_s),
            .alpha(alpha_s),
            .out_valid(update_valid),
            .out_ready(update_ready),
            .td_error(update_td_error),
            .updated_value(update_value)
          );

          stream_stage #(
            .DATA_WIDTH({width})
          ) u_stream_stage (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(update_valid),
            .in_ready(update_ready),
            .td_error(update_td_error),
            .updated_value(update_value),
            .out_valid(out_valid),
            .out_ready(out_ready),
            .td_error_out(td_error),
            .updated_value_out(updated_value)
          );

        endmodule
        """
    )
    td_input_stage = dedent(
        """\
        module td_input_stage #(
            parameter DATA_WIDTH = 8
        ) (
            input wire clk,
            input wire rst_n,
            input wire in_valid,
            output wire in_ready,
            input wire signed [DATA_WIDTH-1:0] reward,
            input wire signed [DATA_WIDTH-1:0] value,
            input wire signed [DATA_WIDTH-1:0] next_value,
            input wire [DATA_WIDTH-1:0] gamma,
            input wire [DATA_WIDTH-1:0] alpha,
            output reg out_valid,
            input wire out_ready,
            output reg signed [DATA_WIDTH-1:0] reward_out,
            output reg signed [DATA_WIDTH-1:0] value_out,
            output reg signed [DATA_WIDTH-1:0] next_value_out,
            output reg [DATA_WIDTH-1:0] gamma_out,
            output reg [DATA_WIDTH-1:0] alpha_out
        );

          assign in_ready = !out_valid || out_ready;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              out_valid <= 1'b0;
              reward_out <= {DATA_WIDTH{1'b0}};
              value_out <= {DATA_WIDTH{1'b0}};
              next_value_out <= {DATA_WIDTH{1'b0}};
              gamma_out <= {DATA_WIDTH{1'b0}};
              alpha_out <= {DATA_WIDTH{1'b0}};
            end else if (in_ready) begin
              out_valid <= in_valid;
              if (in_valid) begin
                reward_out <= reward;
                value_out <= value;
                next_value_out <= next_value;
                gamma_out <= gamma;
                alpha_out <= alpha;
              end
            end
          end

        endmodule
        """
    )
    discount_core = dedent(
        """\
        module discount_core #(
            parameter DATA_WIDTH = 8,
            parameter SCALE_SHIFT = 4
        ) (
            input wire in_valid,
            output wire in_ready,
            input wire signed [DATA_WIDTH-1:0] reward,
            input wire signed [DATA_WIDTH-1:0] next_value,
            input wire [DATA_WIDTH-1:0] gamma,
            output wire out_valid,
            input wire out_ready,
            output wire signed [(2*DATA_WIDTH):0] discounted_return
        );

          wire signed [(2*DATA_WIDTH)-1:0] gamma_next_product;
          wire signed [(2*DATA_WIDTH)-1:0] discounted_next_full;
          wire discounted_next_round;

          assign in_ready = out_ready;
          assign out_valid = in_valid | (discounted_next_round & in_valid);
          assign gamma_next_product = $signed({1'b0, gamma}) * next_value;
          assign discounted_next_full = gamma_next_product >>> SCALE_SHIFT;
          assign discounted_next_round = |gamma_next_product[SCALE_SHIFT-1:0];
          assign discounted_return =
            {{(DATA_WIDTH+1){reward[DATA_WIDTH-1]}}, reward} +
            {discounted_next_full[(2*DATA_WIDTH)-1], discounted_next_full};

        endmodule
        """
    )
    td_update_core = dedent(
        """\
        module td_update_core #(
            parameter DATA_WIDTH = 8,
            parameter SCALE_SHIFT = 4
        ) (
            input wire in_valid,
            output wire in_ready,
            input wire signed [(2*DATA_WIDTH):0] discounted_return,
            input wire signed [DATA_WIDTH-1:0] value,
            input wire [DATA_WIDTH-1:0] alpha,
            output wire out_valid,
            input wire out_ready,
            output wire signed [DATA_WIDTH-1:0] td_error,
            output wire signed [DATA_WIDTH-1:0] updated_value
        );

          wire signed [(2*DATA_WIDTH):0] td_error_full;
          wire td_error_positive_overflow;
          wire td_error_negative_overflow;
          wire signed [(2*DATA_WIDTH):0] alpha_error_product;
          wire signed [(2*DATA_WIDTH):0] scaled_error_full;
          wire signed [DATA_WIDTH-1:0] scaled_error;
          wire signed [DATA_WIDTH:0] updated_value_full;
          wire scaled_error_round;
          wire scaled_error_positive_overflow;
          wire scaled_error_negative_overflow;

          assign in_ready = out_ready;
          assign out_valid = in_valid | (scaled_error_round & in_valid);
          assign td_error_full = discounted_return -
            {{(DATA_WIDTH+1){value[DATA_WIDTH-1]}}, value};
          assign td_error_positive_overflow =
            !td_error_full[2*DATA_WIDTH] && |td_error_full[(2*DATA_WIDTH)-1:DATA_WIDTH-1];
          assign td_error_negative_overflow =
            td_error_full[2*DATA_WIDTH] && ~&td_error_full[(2*DATA_WIDTH)-1:DATA_WIDTH-1];
          assign td_error = td_error_positive_overflow ? {1'b0, {(DATA_WIDTH-1){1'b1}}} :
                            (td_error_negative_overflow ? {1'b1, {(DATA_WIDTH-1){1'b0}}} :
                             td_error_full[DATA_WIDTH-1:0]);
          assign alpha_error_product = $signed({1'b0, alpha}) * td_error;
          assign scaled_error_full = alpha_error_product >>> SCALE_SHIFT;
          assign scaled_error_round = |alpha_error_product[SCALE_SHIFT-1:0];
          assign scaled_error_positive_overflow =
            !scaled_error_full[(2*DATA_WIDTH)-1] &&
            |scaled_error_full[(2*DATA_WIDTH)-1:DATA_WIDTH-1];
          assign scaled_error_negative_overflow =
            scaled_error_full[(2*DATA_WIDTH)-1] &&
            ~&scaled_error_full[(2*DATA_WIDTH)-1:DATA_WIDTH-1];
          assign scaled_error = scaled_error_positive_overflow ? {1'b0, {(DATA_WIDTH-1){1'b1}}} :
                                (scaled_error_negative_overflow ? {1'b1, {(DATA_WIDTH-1){1'b0}}} :
                                 scaled_error_full[DATA_WIDTH-1:0]);
          assign updated_value_full =
            {value[DATA_WIDTH-1], value} + {scaled_error[DATA_WIDTH-1], scaled_error};
          assign updated_value =
            (!updated_value_full[DATA_WIDTH] && updated_value_full[DATA_WIDTH-1]) ?
              {1'b0, {(DATA_WIDTH-1){1'b1}}} :
            (updated_value_full[DATA_WIDTH] && !updated_value_full[DATA_WIDTH-1]) ?
              {1'b1, {(DATA_WIDTH-1){1'b0}}} :
              updated_value_full[DATA_WIDTH-1:0];

        endmodule
        """
    )
    stream_stage = dedent(
        """\
        module stream_stage #(
            parameter DATA_WIDTH = 8
        ) (
            input wire clk,
            input wire rst_n,
            input wire in_valid,
            output wire in_ready,
            input wire signed [DATA_WIDTH-1:0] td_error,
            input wire signed [DATA_WIDTH-1:0] updated_value,
            output reg out_valid,
            input wire out_ready,
            output reg signed [DATA_WIDTH-1:0] td_error_out,
            output reg signed [DATA_WIDTH-1:0] updated_value_out
        );

          assign in_ready = !out_valid || out_ready;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              out_valid <= 1'b0;
              td_error_out <= {DATA_WIDTH{1'b0}};
              updated_value_out <= {DATA_WIDTH{1'b0}};
            end else if (in_ready) begin
              out_valid <= in_valid;
              if (in_valid) begin
                td_error_out <= td_error;
                updated_value_out <= updated_value;
              end
            end
          end

        endmodule
        """
    )
    return {
        "rtl/top.v": top,
        "rtl/td_input_stage.v": td_input_stage,
        "rtl/discount_core.v": discount_core,
        "rtl/td_update_core.v": td_update_core,
        "rtl/stream_stage.v": stream_stage,
    }


def composed_policy_value_shell_rtl_files(width: int) -> dict[str, str]:
    msb = width - 1
    top = dedent(
        f"""\
        module top (
            input wire clk,
            input wire rst_n,
            input wire cfg_valid,
            output wire cfg_ready,
            input wire [2:0] cfg_addr,
            input wire [{msb}:0] cfg_data,
            input wire obs_valid,
            output wire obs_ready,
            input wire [{msb}:0] obs0,
            input wire [{msb}:0] obs1,
            output wire action_valid,
            input wire action_ready,
            output wire selected_action,
            output wire [{msb}:0] value_estimate
        );

          wire [{msb}:0] weight0;
          wire [{msb}:0] weight1;
          wire [{msb}:0] bias0;
          wire [{msb}:0] bias1;
          wire enable;
          wire obs_stage_valid;
          wire obs_stage_ready;
          wire [{msb}:0] obs0_s;
          wire [{msb}:0] obs1_s;
          wire score_valid;
          wire score_ready;
          wire [{msb}:0] policy_score0;
          wire [{msb}:0] policy_score1;
          wire select_valid;
          wire select_ready;
          wire select_action;
          wire [{msb}:0] select_value;

          config_reg_bank #(
            .DATA_WIDTH({width})
          ) u_config_reg_bank (
            .clk(clk),
            .rst_n(rst_n),
            .cfg_valid(cfg_valid),
            .cfg_ready(cfg_ready),
            .cfg_addr(cfg_addr),
            .cfg_data(cfg_data),
            .weight0(weight0),
            .weight1(weight1),
            .bias0(bias0),
            .bias1(bias1),
            .enable(enable)
          );

          observation_stage #(
            .DATA_WIDTH({width})
          ) u_observation_stage (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(obs_valid),
            .in_ready(obs_ready),
            .obs0(obs0),
            .obs1(obs1),
            .out_valid(obs_stage_valid),
            .out_ready(obs_stage_ready),
            .obs0_out(obs0_s),
            .obs1_out(obs1_s)
          );

          policy_score_core #(
            .DATA_WIDTH({width})
          ) u_policy_score_core (
            .in_valid(obs_stage_valid),
            .in_ready(obs_stage_ready),
            .obs0(obs0_s),
            .obs1(obs1_s),
            .weight0(weight0),
            .weight1(weight1),
            .bias0(bias0),
            .bias1(bias1),
            .enable(enable),
            .out_valid(score_valid),
            .out_ready(score_ready),
            .score0(policy_score0),
            .score1(policy_score1)
          );

          action_select_core #(
            .DATA_WIDTH({width})
          ) u_action_select_core (
            .in_valid(score_valid),
            .in_ready(score_ready),
            .score0(policy_score0),
            .score1(policy_score1),
            .out_valid(select_valid),
            .out_ready(select_ready),
            .selected_action(select_action),
            .value_estimate(select_value)
          );

          stream_stage #(
            .DATA_WIDTH({width})
          ) u_stream_stage (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(select_valid),
            .in_ready(select_ready),
            .selected_action(select_action),
            .value_estimate(select_value),
            .out_valid(action_valid),
            .out_ready(action_ready),
            .selected_action_out(selected_action),
            .value_estimate_out(value_estimate)
          );

        endmodule
        """
    )
    config_reg_bank = dedent(
        """\
        module config_reg_bank #(
            parameter DATA_WIDTH = 8
        ) (
            input wire clk,
            input wire rst_n,
            input wire cfg_valid,
            output wire cfg_ready,
            input wire [2:0] cfg_addr,
            input wire [DATA_WIDTH-1:0] cfg_data,
            output reg [DATA_WIDTH-1:0] weight0,
            output reg [DATA_WIDTH-1:0] weight1,
            output reg [DATA_WIDTH-1:0] bias0,
            output reg [DATA_WIDTH-1:0] bias1,
            output reg enable
        );

          assign cfg_ready = 1'b1;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              weight0 <= {{(DATA_WIDTH-1){1'b0}}, 1'b1};
              weight1 <= {{(DATA_WIDTH-1){1'b0}}, 1'b1};
              bias0 <= {DATA_WIDTH{1'b0}};
              bias1 <= {DATA_WIDTH{1'b0}};
              enable <= 1'b0;
            end else if (cfg_valid) begin
              case (cfg_addr)
                3'd0: weight0 <= cfg_data;
                3'd1: bias0 <= cfg_data;
                3'd2: weight1 <= cfg_data;
                3'd3: bias1 <= cfg_data;
                3'd4: enable <= cfg_data[0];
                default: enable <= enable;
              endcase
            end
          end

        endmodule
        """
    )
    observation_stage = dedent(
        """\
        module observation_stage #(
            parameter DATA_WIDTH = 8
        ) (
            input wire clk,
            input wire rst_n,
            input wire in_valid,
            output wire in_ready,
            input wire [DATA_WIDTH-1:0] obs0,
            input wire [DATA_WIDTH-1:0] obs1,
            output reg out_valid,
            input wire out_ready,
            output reg [DATA_WIDTH-1:0] obs0_out,
            output reg [DATA_WIDTH-1:0] obs1_out
        );

          assign in_ready = !out_valid || out_ready;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              out_valid <= 1'b0;
              obs0_out <= {DATA_WIDTH{1'b0}};
              obs1_out <= {DATA_WIDTH{1'b0}};
            end else if (in_ready) begin
              out_valid <= in_valid;
              if (in_valid) begin
                obs0_out <= obs0;
                obs1_out <= obs1;
              end
            end
          end

        endmodule
        """
    )
    policy_score_core = dedent(
        """\
        module policy_score_core #(
            parameter DATA_WIDTH = 8
        ) (
            input wire in_valid,
            output wire in_ready,
            input wire [DATA_WIDTH-1:0] obs0,
            input wire [DATA_WIDTH-1:0] obs1,
            input wire [DATA_WIDTH-1:0] weight0,
            input wire [DATA_WIDTH-1:0] weight1,
            input wire [DATA_WIDTH-1:0] bias0,
            input wire [DATA_WIDTH-1:0] bias1,
            input wire enable,
            output wire out_valid,
            input wire out_ready,
            output wire [DATA_WIDTH-1:0] score0,
            output wire [DATA_WIDTH-1:0] score1
        );

          wire [(2*DATA_WIDTH)-1:0] score0_full;
          wire [(2*DATA_WIDTH)-1:0] score1_full;

          assign in_ready = out_ready;
          assign out_valid = in_valid;
          assign score0_full = (obs0 * weight0) + {{DATA_WIDTH{1'b0}}, bias0};
          assign score1_full = (obs1 * weight1) + {{DATA_WIDTH{1'b0}}, bias1};
          assign score0 = !enable ? {DATA_WIDTH{1'b0}} :
                          (|score0_full[(2*DATA_WIDTH)-1:DATA_WIDTH] ? {DATA_WIDTH{1'b1}} :
                           score0_full[DATA_WIDTH-1:0]);
          assign score1 = !enable ? {DATA_WIDTH{1'b0}} :
                          (|score1_full[(2*DATA_WIDTH)-1:DATA_WIDTH] ? {DATA_WIDTH{1'b1}} :
                           score1_full[DATA_WIDTH-1:0]);

        endmodule
        """
    )
    action_select_core = dedent(
        """\
        module action_select_core #(
            parameter DATA_WIDTH = 8
        ) (
            input wire in_valid,
            output wire in_ready,
            input wire [DATA_WIDTH-1:0] score0,
            input wire [DATA_WIDTH-1:0] score1,
            output wire out_valid,
            input wire out_ready,
            output wire selected_action,
            output wire [DATA_WIDTH-1:0] value_estimate
        );

          wire [DATA_WIDTH:0] score_sum;
          wire average_discard;

          assign in_ready = out_ready;
          assign out_valid = in_valid;
          assign score_sum = {1'b0, score0} + {1'b0, score1};
          assign average_discard = score_sum[0];
          assign selected_action = (score1 > score0) | (average_discard & (score1 > score0));
          assign value_estimate = score_sum[DATA_WIDTH:1];

        endmodule
        """
    )
    stream_stage = dedent(
        """\
        module stream_stage #(
            parameter DATA_WIDTH = 8
        ) (
            input wire clk,
            input wire rst_n,
            input wire in_valid,
            output wire in_ready,
            input wire selected_action,
            input wire [DATA_WIDTH-1:0] value_estimate,
            output reg out_valid,
            input wire out_ready,
            output reg selected_action_out,
            output reg [DATA_WIDTH-1:0] value_estimate_out
        );

          assign in_ready = !out_valid || out_ready;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              out_valid <= 1'b0;
              selected_action_out <= 1'b0;
              value_estimate_out <= {DATA_WIDTH{1'b0}};
            end else if (in_ready) begin
              out_valid <= in_valid;
              if (in_valid) begin
                selected_action_out <= selected_action;
                value_estimate_out <= value_estimate;
              end
            end
          end

        endmodule
        """
    )
    return {
        "rtl/top.v": top,
        "rtl/config_reg_bank.v": config_reg_bank,
        "rtl/observation_stage.v": observation_stage,
        "rtl/policy_score_core.v": policy_score_core,
        "rtl/action_select_core.v": action_select_core,
        "rtl/stream_stage.v": stream_stage,
    }


def composed_replay_sample_shell_rtl_files(width: int) -> dict[str, str]:
    msb = width - 1
    top = dedent(
        f"""\
        module top (
            input wire clk,
            input wire rst_n,
            input wire host_valid,
            output wire host_ready,
            input wire [{msb}:0] host_state,
            input wire host_action,
            input wire [{msb}:0] host_reward,
            input wire [{msb}:0] host_next_state,
            input wire host_done,
            output wire sample_valid,
            input wire sample_ready,
            output wire [{msb}:0] sample_state,
            output wire sample_action,
            output wire [{msb}:0] sample_reward,
            output wire [{msb}:0] sample_next_state,
            output wire sample_done,
            output wire [2:0] occupancy
        );

          wire host_stage_valid;
          wire host_stage_ready;
          wire [{msb}:0] host_stage_state;
          wire host_stage_action;
          wire [{msb}:0] host_stage_reward;
          wire [{msb}:0] host_stage_next_state;
          wire host_stage_done;
          wire store_read_valid;
          wire store_read_ready;
          wire [{msb}:0] store_read_state;
          wire store_read_action;
          wire [{msb}:0] store_read_reward;
          wire [{msb}:0] store_read_next_state;
          wire store_read_done;
          wire [{msb}:0] sample_pack_state;
          wire sample_pack_action;
          wire [{msb}:0] sample_pack_reward;
          wire [{msb}:0] sample_pack_next_state;
          wire sample_pack_done;
          wire [2:0] store_occupancy;

          host_sample_stage #(
            .DATA_WIDTH({width})
          ) u_host_sample_stage (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(host_valid),
            .in_ready(host_ready),
            .state(host_state),
            .action(host_action),
            .reward(host_reward),
            .next_state(host_next_state),
            .done(host_done),
            .out_valid(host_stage_valid),
            .out_ready(host_stage_ready),
            .state_out(host_stage_state),
            .action_out(host_stage_action),
            .reward_out(host_stage_reward),
            .next_state_out(host_stage_next_state),
            .done_out(host_stage_done)
          );

          replay_store #(
            .DATA_WIDTH({width}),
            .DEPTH(4)
          ) u_replay_store (
            .clk(clk),
            .rst_n(rst_n),
            .write_valid(host_stage_valid),
            .write_ready(host_stage_ready),
            .write_state(host_stage_state),
            .write_action(host_stage_action),
            .write_reward(host_stage_reward),
            .write_next_state(host_stage_next_state),
            .write_done(host_stage_done),
            .read_valid(store_read_valid),
            .read_ready(store_read_ready),
            .read_state(store_read_state),
            .read_action(store_read_action),
            .read_reward(store_read_reward),
            .read_next_state(store_read_next_state),
            .read_done(store_read_done),
            .occupancy(store_occupancy)
          );

          sample_pack_core #(
            .DATA_WIDTH({width})
          ) u_sample_pack_core (
            .state(store_read_state),
            .action(store_read_action),
            .reward(store_read_reward),
            .next_state(store_read_next_state),
            .done(store_read_done),
            .sample_state(sample_pack_state),
            .sample_action(sample_pack_action),
            .sample_reward(sample_pack_reward),
            .sample_next_state(sample_pack_next_state),
            .sample_done(sample_pack_done)
          );

          sample_read_stage #(
            .DATA_WIDTH({width})
          ) u_sample_read_stage (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(store_read_valid),
            .read_ready(store_read_ready),
            .sample_state(sample_pack_state),
            .sample_action(sample_pack_action),
            .sample_reward(sample_pack_reward),
            .sample_next_state(sample_pack_next_state),
            .sample_done(sample_pack_done),
            .out_valid(sample_valid),
            .out_ready(sample_ready),
            .sample_state_out(sample_state),
            .sample_action_out(sample_action),
            .sample_reward_out(sample_reward),
            .sample_next_state_out(sample_next_state),
            .sample_done_out(sample_done)
          );

          occupancy_counter u_occupancy_counter (
            .occupancy_in(store_occupancy),
            .occupancy_out(occupancy)
          );

        endmodule
        """
    )
    host_sample_stage = dedent(
        """\
        module host_sample_stage #(
            parameter DATA_WIDTH = 8
        ) (
            input wire clk,
            input wire rst_n,
            input wire in_valid,
            output wire in_ready,
            input wire [DATA_WIDTH-1:0] state,
            input wire action,
            input wire [DATA_WIDTH-1:0] reward,
            input wire [DATA_WIDTH-1:0] next_state,
            input wire done,
            output reg out_valid,
            input wire out_ready,
            output reg [DATA_WIDTH-1:0] state_out,
            output reg action_out,
            output reg [DATA_WIDTH-1:0] reward_out,
            output reg [DATA_WIDTH-1:0] next_state_out,
            output reg done_out
        );

          assign in_ready = !out_valid || out_ready;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              out_valid <= 1'b0;
              state_out <= {DATA_WIDTH{1'b0}};
              action_out <= 1'b0;
              reward_out <= {DATA_WIDTH{1'b0}};
              next_state_out <= {DATA_WIDTH{1'b0}};
              done_out <= 1'b0;
            end else if (in_ready) begin
              out_valid <= in_valid;
              if (in_valid) begin
                state_out <= state;
                action_out <= action;
                reward_out <= reward;
                next_state_out <= next_state;
                done_out <= done;
              end
            end
          end

        endmodule
        """
    )
    replay_store = dedent(
        """\
        module replay_store #(
            parameter DATA_WIDTH = 8,
            parameter DEPTH = 4
        ) (
            input wire clk,
            input wire rst_n,
            input wire write_valid,
            output wire write_ready,
            input wire [DATA_WIDTH-1:0] write_state,
            input wire write_action,
            input wire [DATA_WIDTH-1:0] write_reward,
            input wire [DATA_WIDTH-1:0] write_next_state,
            input wire write_done,
            output wire read_valid,
            input wire read_ready,
            output wire [DATA_WIDTH-1:0] read_state,
            output wire read_action,
            output wire [DATA_WIDTH-1:0] read_reward,
            output wire [DATA_WIDTH-1:0] read_next_state,
            output wire read_done,
            output reg [2:0] occupancy
        );

          reg [DATA_WIDTH-1:0] state_mem [0:DEPTH-1];
          reg action_mem [0:DEPTH-1];
          reg [DATA_WIDTH-1:0] reward_mem [0:DEPTH-1];
          reg [DATA_WIDTH-1:0] next_state_mem [0:DEPTH-1];
          reg done_mem [0:DEPTH-1];
          reg [1:0] write_ptr;
          reg [1:0] read_ptr;
          wire write_fire;
          wire read_fire;

          assign write_ready = occupancy < 3'd4;
          assign read_valid = occupancy != 3'd0;
          assign write_fire = write_valid && write_ready;
          assign read_fire = read_valid && read_ready;
          assign read_state = state_mem[read_ptr];
          assign read_action = action_mem[read_ptr];
          assign read_reward = reward_mem[read_ptr];
          assign read_next_state = next_state_mem[read_ptr];
          assign read_done = done_mem[read_ptr];

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              write_ptr <= 2'd0;
              read_ptr <= 2'd0;
              occupancy <= 3'd0;
              state_mem[0] <= {DATA_WIDTH{1'b0}};
              state_mem[1] <= {DATA_WIDTH{1'b0}};
              state_mem[2] <= {DATA_WIDTH{1'b0}};
              state_mem[3] <= {DATA_WIDTH{1'b0}};
              action_mem[0] <= 1'b0;
              action_mem[1] <= 1'b0;
              action_mem[2] <= 1'b0;
              action_mem[3] <= 1'b0;
              reward_mem[0] <= {DATA_WIDTH{1'b0}};
              reward_mem[1] <= {DATA_WIDTH{1'b0}};
              reward_mem[2] <= {DATA_WIDTH{1'b0}};
              reward_mem[3] <= {DATA_WIDTH{1'b0}};
              next_state_mem[0] <= {DATA_WIDTH{1'b0}};
              next_state_mem[1] <= {DATA_WIDTH{1'b0}};
              next_state_mem[2] <= {DATA_WIDTH{1'b0}};
              next_state_mem[3] <= {DATA_WIDTH{1'b0}};
              done_mem[0] <= 1'b0;
              done_mem[1] <= 1'b0;
              done_mem[2] <= 1'b0;
              done_mem[3] <= 1'b0;
            end else begin
              if (write_fire) begin
                state_mem[write_ptr] <= write_state;
                action_mem[write_ptr] <= write_action;
                reward_mem[write_ptr] <= write_reward;
                next_state_mem[write_ptr] <= write_next_state;
                done_mem[write_ptr] <= write_done;
                write_ptr <= write_ptr + 2'd1;
              end
              if (read_fire) begin
                read_ptr <= read_ptr + 2'd1;
              end
              if (write_fire && !read_fire) begin
                occupancy <= occupancy + 3'd1;
              end else if (!write_fire && read_fire) begin
                occupancy <= occupancy - 3'd1;
              end
            end
          end

        endmodule
        """
    )
    sample_pack_core = dedent(
        """\
        module sample_pack_core #(
            parameter DATA_WIDTH = 8
        ) (
            input wire [DATA_WIDTH-1:0] state,
            input wire action,
            input wire [DATA_WIDTH-1:0] reward,
            input wire [DATA_WIDTH-1:0] next_state,
            input wire done,
            output wire [DATA_WIDTH-1:0] sample_state,
            output wire sample_action,
            output wire [DATA_WIDTH-1:0] sample_reward,
            output wire [DATA_WIDTH-1:0] sample_next_state,
            output wire sample_done
        );

          assign sample_state = state;
          assign sample_action = action;
          assign sample_reward = reward;
          assign sample_next_state = next_state;
          assign sample_done = done;

        endmodule
        """
    )
    sample_read_stage = dedent(
        """\
        module sample_read_stage #(
            parameter DATA_WIDTH = 8
        ) (
            input wire clk,
            input wire rst_n,
            input wire in_valid,
            output wire read_ready,
            input wire [DATA_WIDTH-1:0] sample_state,
            input wire sample_action,
            input wire [DATA_WIDTH-1:0] sample_reward,
            input wire [DATA_WIDTH-1:0] sample_next_state,
            input wire sample_done,
            output reg out_valid,
            input wire out_ready,
            output reg [DATA_WIDTH-1:0] sample_state_out,
            output reg sample_action_out,
            output reg [DATA_WIDTH-1:0] sample_reward_out,
            output reg [DATA_WIDTH-1:0] sample_next_state_out,
            output reg sample_done_out
        );

          assign read_ready = out_ready;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              out_valid <= 1'b0;
              sample_state_out <= {DATA_WIDTH{1'b0}};
              sample_action_out <= 1'b0;
              sample_reward_out <= {DATA_WIDTH{1'b0}};
              sample_next_state_out <= {DATA_WIDTH{1'b0}};
              sample_done_out <= 1'b0;
            end else if (read_ready) begin
              out_valid <= in_valid;
              if (in_valid) begin
                sample_state_out <= sample_state;
                sample_action_out <= sample_action;
                sample_reward_out <= sample_reward;
                sample_next_state_out <= sample_next_state;
                sample_done_out <= sample_done;
              end
            end
          end

        endmodule
        """
    )
    occupancy_counter = dedent(
        """\
        module occupancy_counter (
            input wire [2:0] occupancy_in,
            output wire [2:0] occupancy_out
        );

          assign occupancy_out = occupancy_in;

        endmodule
        """
    )
    return {
        "rtl/top.v": top,
        "rtl/host_sample_stage.v": host_sample_stage,
        "rtl/replay_store.v": replay_store,
        "rtl/sample_pack_core.v": sample_pack_core,
        "rtl/sample_read_stage.v": sample_read_stage,
        "rtl/occupancy_counter.v": occupancy_counter,
    }


def composed_host_protocol_shell_rtl_files(width: int) -> dict[str, str]:
    msb = width - 1
    stream_msb = width * 2 - 1
    top = dedent(
        f"""\
        module top (
            input wire clk,
            input wire rst_n,
            input wire s_axi_awvalid,
            output wire s_axi_awready,
            input wire [3:0] s_axi_awaddr,
            input wire s_axi_wvalid,
            output wire s_axi_wready,
            input wire [{msb}:0] s_axi_wdata,
            input wire s_axi_wstrb,
            output wire s_axi_bvalid,
            input wire s_axi_bready,
            input wire s_axi_arvalid,
            output wire s_axi_arready,
            input wire [3:0] s_axi_araddr,
            output wire s_axi_rvalid,
            input wire s_axi_rready,
            output wire [{msb}:0] s_axi_rdata,
            output wire m_axis_tvalid,
            input wire m_axis_tready,
            output wire [{stream_msb}:0] m_axis_tdata,
            output wire m_axis_tlast,
            output wire irq
        );

          wire write_valid;
          wire [3:0] write_addr;
          wire [{msb}:0] write_data;
          wire read_valid;
          wire [3:0] read_addr;
          wire start_pulse;
          wire [{msb}:0] sample0;
          wire [{msb}:0] sample1;
          wire stream_done;
          wire irq_state;

          axi_lite_write_ctrl #(
            .DATA_WIDTH({width})
          ) u_axi_lite_write_ctrl (
            .clk(clk),
            .rst_n(rst_n),
            .awvalid(s_axi_awvalid),
            .awready(s_axi_awready),
            .awaddr(s_axi_awaddr),
            .wvalid(s_axi_wvalid),
            .wready(s_axi_wready),
            .wdata(s_axi_wdata),
            .wstrb(s_axi_wstrb),
            .bvalid(s_axi_bvalid),
            .bready(s_axi_bready),
            .write_valid(write_valid),
            .write_addr(write_addr),
            .write_data(write_data)
          );

          axi_lite_read_ctrl u_axi_lite_read_ctrl (
            .clk(clk),
            .rst_n(rst_n),
            .arvalid(s_axi_arvalid),
            .arready(s_axi_arready),
            .araddr(s_axi_araddr),
            .rvalid(s_axi_rvalid),
            .rready(s_axi_rready),
            .read_valid(read_valid),
            .read_addr(read_addr)
          );

          control_reg_bank #(
            .DATA_WIDTH({width})
          ) u_control_reg_bank (
            .clk(clk),
            .rst_n(rst_n),
            .write_valid(write_valid),
            .write_addr(write_addr),
            .write_data(write_data),
            .read_valid(read_valid),
            .read_addr(read_addr),
            .read_data(s_axi_rdata),
            .stream_done(stream_done),
            .start_pulse(start_pulse),
            .sample0(sample0),
            .sample1(sample1),
            .irq_state(irq_state)
          );

          sample_stream_adapter #(
            .DATA_WIDTH({width})
          ) u_sample_stream_adapter (
            .clk(clk),
            .rst_n(rst_n),
            .start(start_pulse),
            .sample0(sample0),
            .sample1(sample1),
            .tvalid(m_axis_tvalid),
            .tready(m_axis_tready),
            .tdata(m_axis_tdata),
            .tlast(m_axis_tlast),
            .stream_done(stream_done)
          );

          irq_status u_irq_status (
            .irq_in(irq_state),
            .irq_out(irq)
          );

        endmodule
        """
    )
    axi_lite_write_ctrl = dedent(
        """\
        module axi_lite_write_ctrl #(
            parameter DATA_WIDTH = 8
        ) (
            input wire clk,
            input wire rst_n,
            input wire awvalid,
            output wire awready,
            input wire [3:0] awaddr,
            input wire wvalid,
            output wire wready,
            input wire [DATA_WIDTH-1:0] wdata,
            input wire wstrb,
            output reg bvalid,
            input wire bready,
            output wire write_valid,
            output wire [3:0] write_addr,
            output wire [DATA_WIDTH-1:0] write_data
        );

          wire accept_write;

          assign awready = !bvalid;
          assign wready = !bvalid;
          assign accept_write = awvalid && wvalid && awready && wready && wstrb;
          assign write_valid = accept_write;
          assign write_addr = awaddr;
          assign write_data = wdata;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              bvalid <= 1'b0;
            end else begin
              if (accept_write) begin
                bvalid <= 1'b1;
              end else if (bvalid && bready) begin
                bvalid <= 1'b0;
              end
            end
          end

        endmodule
        """
    )
    axi_lite_read_ctrl = dedent(
        """\
        module axi_lite_read_ctrl (
            input wire clk,
            input wire rst_n,
            input wire arvalid,
            output wire arready,
            input wire [3:0] araddr,
            output reg rvalid,
            input wire rready,
            output wire read_valid,
            output wire [3:0] read_addr
        );

          wire accept_read;

          assign arready = !rvalid;
          assign accept_read = arvalid && arready;
          assign read_valid = accept_read;
          assign read_addr = araddr;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              rvalid <= 1'b0;
            end else begin
              if (accept_read) begin
                rvalid <= 1'b1;
              end else if (rvalid && rready) begin
                rvalid <= 1'b0;
              end
            end
          end

        endmodule
        """
    )
    control_reg_bank = dedent(
        """\
        module control_reg_bank #(
            parameter DATA_WIDTH = 8
        ) (
            input wire clk,
            input wire rst_n,
            input wire write_valid,
            input wire [3:0] write_addr,
            input wire [DATA_WIDTH-1:0] write_data,
            input wire read_valid,
            input wire [3:0] read_addr,
            output reg [DATA_WIDTH-1:0] read_data,
            input wire stream_done,
            output reg start_pulse,
            output reg [DATA_WIDTH-1:0] sample0,
            output reg [DATA_WIDTH-1:0] sample1,
            output reg irq_state
        );

          reg [DATA_WIDTH-1:0] ctrl;
          reg busy;
          reg done;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              ctrl <= {DATA_WIDTH{1'b0}};
              sample0 <= {DATA_WIDTH{1'b0}};
              sample1 <= {DATA_WIDTH{1'b0}};
              busy <= 1'b0;
              done <= 1'b0;
              irq_state <= 1'b0;
              start_pulse <= 1'b0;
              read_data <= {DATA_WIDTH{1'b0}};
            end else begin
              start_pulse <= 1'b0;
              if (write_valid) begin
                case (write_addr)
                  4'h0: begin
                    ctrl <= write_data;
                    if (write_data[0]) begin
                      start_pulse <= 1'b1;
                      busy <= 1'b1;
                      done <= 1'b0;
                    end
                    if (write_data[1]) begin
                      irq_state <= 1'b0;
                    end
                  end
                  4'h4: sample0 <= write_data;
                  4'h8: sample1 <= write_data;
                  default: ctrl <= ctrl;
                endcase
              end
              if (stream_done) begin
                busy <= 1'b0;
                done <= 1'b1;
                irq_state <= 1'b1;
              end
              if (read_valid) begin
                case (read_addr)
                  4'h0: read_data <= ctrl;
                  4'h4: read_data <= sample0;
                  4'h8: read_data <= sample1;
                  4'hc: read_data <= {{(DATA_WIDTH-3){1'b0}}, irq_state, done, busy};
                  default: read_data <= {DATA_WIDTH{1'b0}};
                endcase
              end
            end
          end

        endmodule
        """
    )
    sample_stream_adapter = dedent(
        """\
        module sample_stream_adapter #(
            parameter DATA_WIDTH = 8
        ) (
            input wire clk,
            input wire rst_n,
            input wire start,
            input wire [DATA_WIDTH-1:0] sample0,
            input wire [DATA_WIDTH-1:0] sample1,
            output reg tvalid,
            input wire tready,
            output reg [(2*DATA_WIDTH)-1:0] tdata,
            output reg tlast,
            output reg stream_done
        );

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              tvalid <= 1'b0;
              tdata <= {(2*DATA_WIDTH){1'b0}};
              tlast <= 1'b0;
              stream_done <= 1'b0;
            end else begin
              stream_done <= 1'b0;
              if (start && !tvalid) begin
                tvalid <= 1'b1;
                tdata <= {sample1, sample0};
                tlast <= 1'b1;
              end else if (tvalid && tready) begin
                tvalid <= 1'b0;
                tlast <= 1'b0;
                stream_done <= 1'b1;
              end
            end
          end

        endmodule
        """
    )
    irq_status = dedent(
        """\
        module irq_status (
            input wire irq_in,
            output wire irq_out
        );

          assign irq_out = irq_in;

        endmodule
        """
    )
    return {
        "rtl/top.v": top,
        "rtl/axi_lite_write_ctrl.v": axi_lite_write_ctrl,
        "rtl/axi_lite_read_ctrl.v": axi_lite_read_ctrl,
        "rtl/control_reg_bank.v": control_reg_bank,
        "rtl/sample_stream_adapter.v": sample_stream_adapter,
        "rtl/irq_status.v": irq_status,
    }


def composed_rl_accelerator_shell_rtl_files(width: int) -> dict[str, str]:
    msb = width - 1
    top = dedent(
        f"""\
        module top (
            input wire clk,
            input wire rst_n,
            input wire cfg_valid,
            output wire cfg_ready,
            input wire [2:0] cfg_addr,
            input wire [{msb}:0] cfg_data,
            input wire sample_valid,
            output wire sample_ready,
            input wire [{msb}:0] obs0,
            input wire [{msb}:0] obs1,
            input wire [{msb}:0] reward,
            input wire [{msb}:0] next_value,
            input wire done_in,
            output wire result_valid,
            input wire result_ready,
            output wire selected_action,
            output wire [{msb}:0] value_estimate,
            output wire [{msb}:0] updated_value,
            output wire episode_done,
            output wire irq
        );

          wire [{msb}:0] weight0;
          wire [{msb}:0] bias0;
          wire [{msb}:0] weight1;
          wire [{msb}:0] bias1;
          wire [{msb}:0] alpha;
          wire enable;
          wire sample_stage_valid;
          wire sample_consume_ready;
          wire [{msb}:0] captured_obs0;
          wire [{msb}:0] captured_obs1;
          wire [{msb}:0] captured_reward;
          wire [{msb}:0] captured_next_value;
          wire captured_done;
          wire policy_valid;
          wire policy_selected_action;
          wire [{msb}:0] policy_value_estimate;
          wire update_valid;
          wire [{msb}:0] update_updated_value;

          host_config_bank #(
            .DATA_WIDTH({width})
          ) u_host_config_bank (
            .clk(clk),
            .rst_n(rst_n),
            .cfg_valid(cfg_valid),
            .cfg_ready(cfg_ready),
            .cfg_addr(cfg_addr),
            .cfg_data(cfg_data),
            .weight0(weight0),
            .bias0(bias0),
            .weight1(weight1),
            .bias1(bias1),
            .alpha(alpha),
            .enable(enable)
          );

          sample_capture_stage #(
            .DATA_WIDTH({width})
          ) u_sample_capture_stage (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(sample_valid),
            .in_ready(sample_ready),
            .obs0(obs0),
            .obs1(obs1),
            .reward(reward),
            .next_value(next_value),
            .done_in(done_in),
            .consume_ready(sample_consume_ready),
            .out_valid(sample_stage_valid),
            .obs0_out(captured_obs0),
            .obs1_out(captured_obs1),
            .reward_out(captured_reward),
            .next_value_out(captured_next_value),
            .done_out(captured_done)
          );

          policy_value_core #(
            .DATA_WIDTH({width})
          ) u_policy_value_core (
            .in_valid(sample_stage_valid),
            .obs0(captured_obs0),
            .obs1(captured_obs1),
            .weight0(weight0),
            .bias0(bias0),
            .weight1(weight1),
            .bias1(bias1),
            .enable(enable),
            .out_valid(policy_valid),
            .selected_action(policy_selected_action),
            .value_estimate(policy_value_estimate)
          );

          td_update_core #(
            .DATA_WIDTH({width})
          ) u_td_update_core (
            .in_valid(policy_valid),
            .reward(captured_reward),
            .next_value(captured_next_value),
            .value_estimate(policy_value_estimate),
            .alpha(alpha),
            .out_valid(update_valid),
            .updated_value(update_updated_value)
          );

          result_stream_stage #(
            .DATA_WIDTH({width})
          ) u_result_stream_stage (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(update_valid),
            .out_ready(sample_consume_ready),
            .selected_action(policy_selected_action),
            .value_estimate(policy_value_estimate),
            .updated_value(update_updated_value),
            .done_in(captured_done),
            .result_valid(result_valid),
            .result_ready(result_ready),
            .selected_action_out(selected_action),
            .value_estimate_out(value_estimate),
            .updated_value_out(updated_value),
            .episode_done_out(episode_done),
            .irq(irq)
          );

        endmodule
        """
    )
    host_config_bank = dedent(
        """\
        module host_config_bank #(
            parameter DATA_WIDTH = 8
        ) (
            input wire clk,
            input wire rst_n,
            input wire cfg_valid,
            output wire cfg_ready,
            input wire [2:0] cfg_addr,
            input wire [DATA_WIDTH-1:0] cfg_data,
            output reg [DATA_WIDTH-1:0] weight0,
            output reg [DATA_WIDTH-1:0] bias0,
            output reg [DATA_WIDTH-1:0] weight1,
            output reg [DATA_WIDTH-1:0] bias1,
            output reg [DATA_WIDTH-1:0] alpha,
            output reg enable
        );

          assign cfg_ready = 1'b1;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              weight0 <= {DATA_WIDTH{1'b0}};
              bias0 <= {DATA_WIDTH{1'b0}};
              weight1 <= {DATA_WIDTH{1'b0}};
              bias1 <= {DATA_WIDTH{1'b0}};
              alpha <= {DATA_WIDTH{1'b0}};
              enable <= 1'b0;
            end else if (cfg_valid && cfg_ready) begin
              case (cfg_addr)
                3'd0: weight0 <= cfg_data;
                3'd1: bias0 <= cfg_data;
                3'd2: weight1 <= cfg_data;
                3'd3: bias1 <= cfg_data;
                3'd4: alpha <= cfg_data;
                3'd5: enable <= cfg_data[0];
                default: enable <= enable;
              endcase
            end
          end

        endmodule
        """
    )
    sample_capture_stage = dedent(
        """\
        module sample_capture_stage #(
            parameter DATA_WIDTH = 8
        ) (
            input wire clk,
            input wire rst_n,
            input wire in_valid,
            output wire in_ready,
            input wire [DATA_WIDTH-1:0] obs0,
            input wire [DATA_WIDTH-1:0] obs1,
            input wire [DATA_WIDTH-1:0] reward,
            input wire [DATA_WIDTH-1:0] next_value,
            input wire done_in,
            input wire consume_ready,
            output wire out_valid,
            output reg [DATA_WIDTH-1:0] obs0_out,
            output reg [DATA_WIDTH-1:0] obs1_out,
            output reg [DATA_WIDTH-1:0] reward_out,
            output reg [DATA_WIDTH-1:0] next_value_out,
            output reg done_out
        );

          reg valid_reg;

          assign in_ready = !valid_reg || consume_ready;
          assign out_valid = valid_reg;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              valid_reg <= 1'b0;
              obs0_out <= {DATA_WIDTH{1'b0}};
              obs1_out <= {DATA_WIDTH{1'b0}};
              reward_out <= {DATA_WIDTH{1'b0}};
              next_value_out <= {DATA_WIDTH{1'b0}};
              done_out <= 1'b0;
            end else begin
              if (in_valid && in_ready) begin
                valid_reg <= 1'b1;
                obs0_out <= obs0;
                obs1_out <= obs1;
                reward_out <= reward;
                next_value_out <= next_value;
                done_out <= done_in;
              end else if (consume_ready) begin
                valid_reg <= 1'b0;
              end
            end
          end

        endmodule
        """
    )
    policy_value_core = dedent(
        """\
        module policy_value_core #(
            parameter DATA_WIDTH = 8
        ) (
            input wire in_valid,
            input wire [DATA_WIDTH-1:0] obs0,
            input wire [DATA_WIDTH-1:0] obs1,
            input wire [DATA_WIDTH-1:0] weight0,
            input wire [DATA_WIDTH-1:0] bias0,
            input wire [DATA_WIDTH-1:0] weight1,
            input wire [DATA_WIDTH-1:0] bias1,
            input wire enable,
            output wire out_valid,
            output wire selected_action,
            output wire [DATA_WIDTH-1:0] value_estimate
        );

          wire [(2*DATA_WIDTH)-1:0] score0_full;
          wire [(2*DATA_WIDTH)-1:0] score1_full;
          wire [DATA_WIDTH-1:0] score0;
          wire [DATA_WIDTH-1:0] score1;
          wire [DATA_WIDTH:0] value_sum;
          wire average_discard;

          assign score0_full = (obs0 * weight0) + {{DATA_WIDTH{1'b0}}, bias0};
          assign score1_full = (obs1 * weight1) + {{DATA_WIDTH{1'b0}}, bias1};
          assign score0 = |score0_full[(2*DATA_WIDTH)-1:DATA_WIDTH] ? {DATA_WIDTH{1'b1}} :
                          score0_full[DATA_WIDTH-1:0];
          assign score1 = |score1_full[(2*DATA_WIDTH)-1:DATA_WIDTH] ? {DATA_WIDTH{1'b1}} :
                          score1_full[DATA_WIDTH-1:0];
          assign value_sum = {1'b0, score0} + {1'b0, score1};
          assign average_discard = value_sum[0];
          assign selected_action = (score1 > score0) | (average_discard & (score1 > score0));
          assign value_estimate = value_sum[DATA_WIDTH:1];
          assign out_valid = in_valid && enable;

        endmodule
        """
    )
    td_update_core = dedent(
        """\
        module td_update_core #(
            parameter DATA_WIDTH = 8
        ) (
            input wire in_valid,
            input wire [DATA_WIDTH-1:0] reward,
            input wire [DATA_WIDTH-1:0] next_value,
            input wire [DATA_WIDTH-1:0] value_estimate,
            input wire [DATA_WIDTH-1:0] alpha,
            output wire out_valid,
            output wire [DATA_WIDTH-1:0] updated_value
        );

          wire signed [DATA_WIDTH+1:0] td_error_full;
          wire [DATA_WIDTH:0] td_error_nonnegative;
          wire [(2*DATA_WIDTH):0] update_product;
          wire [(2*DATA_WIDTH):0] update_delta_full;
          wire [DATA_WIDTH-1:0] update_delta;
          wire update_delta_round;
          wire update_delta_overflow;

          assign td_error_full = $signed({2'b00, reward}) +
                                 $signed({2'b00, next_value}) -
                                 $signed({2'b00, value_estimate});
          assign td_error_nonnegative = td_error_full[DATA_WIDTH+1] ?
                                        {(DATA_WIDTH+1){1'b0}} :
                                        td_error_full[DATA_WIDTH:0];
          assign update_product = alpha * td_error_nonnegative;
          assign update_delta_full = update_product >> 4;
          assign update_delta_round = |update_product[3:0];
          assign update_delta_overflow = |update_delta_full[(2*DATA_WIDTH):DATA_WIDTH];
          assign update_delta = update_delta_overflow ? {DATA_WIDTH{1'b1}} :
                                update_delta_full[DATA_WIDTH-1:0];
          assign updated_value = value_estimate + update_delta;
          assign out_valid = in_valid | (update_delta_round & in_valid);

        endmodule
        """
    )
    result_stream_stage = dedent(
        """\
        module result_stream_stage #(
            parameter DATA_WIDTH = 8
        ) (
            input wire clk,
            input wire rst_n,
            input wire in_valid,
            output wire out_ready,
            input wire selected_action,
            input wire [DATA_WIDTH-1:0] value_estimate,
            input wire [DATA_WIDTH-1:0] updated_value,
            input wire done_in,
            output reg result_valid,
            input wire result_ready,
            output reg selected_action_out,
            output reg [DATA_WIDTH-1:0] value_estimate_out,
            output reg [DATA_WIDTH-1:0] updated_value_out,
            output reg episode_done_out,
            output reg irq
        );

          assign out_ready = !result_valid || result_ready;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              result_valid <= 1'b0;
              selected_action_out <= 1'b0;
              value_estimate_out <= {DATA_WIDTH{1'b0}};
              updated_value_out <= {DATA_WIDTH{1'b0}};
              episode_done_out <= 1'b0;
              irq <= 1'b0;
            end else begin
              if (result_valid && result_ready) begin
                if (episode_done_out) begin
                  irq <= 1'b1;
                end
                result_valid <= 1'b0;
              end
              if (in_valid && out_ready) begin
                result_valid <= 1'b1;
                selected_action_out <= selected_action;
                value_estimate_out <= value_estimate;
                updated_value_out <= updated_value;
                episode_done_out <= done_in;
              end
            end
          end

        endmodule
        """
    )
    return {
        "rtl/top.v": top,
        "rtl/host_config_bank.v": host_config_bank,
        "rtl/sample_capture_stage.v": sample_capture_stage,
        "rtl/policy_value_core.v": policy_value_core,
        "rtl/td_update_core.v": td_update_core,
        "rtl/result_stream_stage.v": result_stream_stage,
    }


def composed_batch_rl_accelerator_shell_rtl_files(width: int) -> dict[str, str]:
    msb = width - 1
    top = dedent(
        f"""\
        module top (
            input wire clk,
            input wire rst_n,
            input wire cfg_valid,
            output wire cfg_ready,
            input wire [2:0] cfg_addr,
            input wire [{msb}:0] cfg_data,
            input wire batch_valid,
            output wire batch_ready,
            input wire [{msb}:0] obs0_a,
            input wire [{msb}:0] obs1_a,
            input wire [{msb}:0] reward_a,
            input wire [{msb}:0] next_value_a,
            input wire done_a,
            input wire [{msb}:0] obs0_b,
            input wire [{msb}:0] obs1_b,
            input wire [{msb}:0] reward_b,
            input wire [{msb}:0] next_value_b,
            input wire done_b,
            output wire result_valid,
            input wire result_ready,
            output wire selected_action_a,
            output wire [{msb}:0] value_estimate_a,
            output wire [{msb}:0] updated_value_a,
            output wire selected_action_b,
            output wire [{msb}:0] value_estimate_b,
            output wire [{msb}:0] updated_value_b,
            output wire batch_done,
            output wire irq
        );

          wire [{msb}:0] weight0;
          wire [{msb}:0] bias0;
          wire [{msb}:0] weight1;
          wire [{msb}:0] bias1;
          wire [{msb}:0] alpha;
          wire enable;
          wire batch_stage_valid;
          wire batch_consume_ready;
          wire [{msb}:0] captured_obs0_a;
          wire [{msb}:0] captured_obs1_a;
          wire [{msb}:0] captured_reward_a;
          wire [{msb}:0] captured_next_value_a;
          wire captured_done_a;
          wire [{msb}:0] captured_obs0_b;
          wire [{msb}:0] captured_obs1_b;
          wire [{msb}:0] captured_reward_b;
          wire [{msb}:0] captured_next_value_b;
          wire captured_done_b;
          wire policy_valid;
          wire policy_selected_action_a;
          wire [{msb}:0] policy_value_estimate_a;
          wire policy_selected_action_b;
          wire [{msb}:0] policy_value_estimate_b;
          wire update_valid;
          wire [{msb}:0] update_updated_value_a;
          wire [{msb}:0] update_updated_value_b;

          batch_config_bank #(
            .DATA_WIDTH({width})
          ) u_batch_config_bank (
            .clk(clk),
            .rst_n(rst_n),
            .cfg_valid(cfg_valid),
            .cfg_ready(cfg_ready),
            .cfg_addr(cfg_addr),
            .cfg_data(cfg_data),
            .weight0(weight0),
            .bias0(bias0),
            .weight1(weight1),
            .bias1(bias1),
            .alpha(alpha),
            .enable(enable)
          );

          batch_sample_buffer #(
            .DATA_WIDTH({width})
          ) u_batch_sample_buffer (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(batch_valid),
            .in_ready(batch_ready),
            .obs0_a(obs0_a),
            .obs1_a(obs1_a),
            .reward_a(reward_a),
            .next_value_a(next_value_a),
            .done_a(done_a),
            .obs0_b(obs0_b),
            .obs1_b(obs1_b),
            .reward_b(reward_b),
            .next_value_b(next_value_b),
            .done_b(done_b),
            .consume_ready(batch_consume_ready),
            .out_valid(batch_stage_valid),
            .obs0_a_out(captured_obs0_a),
            .obs1_a_out(captured_obs1_a),
            .reward_a_out(captured_reward_a),
            .next_value_a_out(captured_next_value_a),
            .done_a_out(captured_done_a),
            .obs0_b_out(captured_obs0_b),
            .obs1_b_out(captured_obs1_b),
            .reward_b_out(captured_reward_b),
            .next_value_b_out(captured_next_value_b),
            .done_b_out(captured_done_b)
          );

          dual_policy_value_core #(
            .DATA_WIDTH({width})
          ) u_dual_policy_value_core (
            .in_valid(batch_stage_valid),
            .obs0_a(captured_obs0_a),
            .obs1_a(captured_obs1_a),
            .obs0_b(captured_obs0_b),
            .obs1_b(captured_obs1_b),
            .weight0(weight0),
            .bias0(bias0),
            .weight1(weight1),
            .bias1(bias1),
            .enable(enable),
            .out_valid(policy_valid),
            .selected_action_a(policy_selected_action_a),
            .value_estimate_a(policy_value_estimate_a),
            .selected_action_b(policy_selected_action_b),
            .value_estimate_b(policy_value_estimate_b)
          );

          dual_td_update_core #(
            .DATA_WIDTH({width})
          ) u_dual_td_update_core (
            .in_valid(policy_valid),
            .reward_a(captured_reward_a),
            .next_value_a(captured_next_value_a),
            .value_estimate_a(policy_value_estimate_a),
            .reward_b(captured_reward_b),
            .next_value_b(captured_next_value_b),
            .value_estimate_b(policy_value_estimate_b),
            .alpha(alpha),
            .out_valid(update_valid),
            .updated_value_a(update_updated_value_a),
            .updated_value_b(update_updated_value_b)
          );

          batch_result_stage #(
            .DATA_WIDTH({width})
          ) u_batch_result_stage (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(update_valid),
            .out_ready(batch_consume_ready),
            .selected_action_a(policy_selected_action_a),
            .value_estimate_a(policy_value_estimate_a),
            .updated_value_a(update_updated_value_a),
            .selected_action_b(policy_selected_action_b),
            .value_estimate_b(policy_value_estimate_b),
            .updated_value_b(update_updated_value_b),
            .done_a(captured_done_a),
            .done_b(captured_done_b),
            .result_valid(result_valid),
            .result_ready(result_ready),
            .selected_action_a_out(selected_action_a),
            .value_estimate_a_out(value_estimate_a),
            .updated_value_a_out(updated_value_a),
            .selected_action_b_out(selected_action_b),
            .value_estimate_b_out(value_estimate_b),
            .updated_value_b_out(updated_value_b),
            .batch_done_out(batch_done),
            .irq(irq)
          );

        endmodule
        """
    )
    batch_config_bank = batch_config_bank_rtl()
    batch_sample_buffer = dedent(
        """\
        module batch_sample_buffer #(
            parameter DATA_WIDTH = 8
        ) (
            input wire clk,
            input wire rst_n,
            input wire in_valid,
            output wire in_ready,
            input wire [DATA_WIDTH-1:0] obs0_a,
            input wire [DATA_WIDTH-1:0] obs1_a,
            input wire [DATA_WIDTH-1:0] reward_a,
            input wire [DATA_WIDTH-1:0] next_value_a,
            input wire done_a,
            input wire [DATA_WIDTH-1:0] obs0_b,
            input wire [DATA_WIDTH-1:0] obs1_b,
            input wire [DATA_WIDTH-1:0] reward_b,
            input wire [DATA_WIDTH-1:0] next_value_b,
            input wire done_b,
            input wire consume_ready,
            output wire out_valid,
            output reg [DATA_WIDTH-1:0] obs0_a_out,
            output reg [DATA_WIDTH-1:0] obs1_a_out,
            output reg [DATA_WIDTH-1:0] reward_a_out,
            output reg [DATA_WIDTH-1:0] next_value_a_out,
            output reg done_a_out,
            output reg [DATA_WIDTH-1:0] obs0_b_out,
            output reg [DATA_WIDTH-1:0] obs1_b_out,
            output reg [DATA_WIDTH-1:0] reward_b_out,
            output reg [DATA_WIDTH-1:0] next_value_b_out,
            output reg done_b_out
        );

          reg valid_reg;

          assign in_ready = !valid_reg || consume_ready;
          assign out_valid = valid_reg;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              valid_reg <= 1'b0;
              obs0_a_out <= {DATA_WIDTH{1'b0}};
              obs1_a_out <= {DATA_WIDTH{1'b0}};
              reward_a_out <= {DATA_WIDTH{1'b0}};
              next_value_a_out <= {DATA_WIDTH{1'b0}};
              done_a_out <= 1'b0;
              obs0_b_out <= {DATA_WIDTH{1'b0}};
              obs1_b_out <= {DATA_WIDTH{1'b0}};
              reward_b_out <= {DATA_WIDTH{1'b0}};
              next_value_b_out <= {DATA_WIDTH{1'b0}};
              done_b_out <= 1'b0;
            end else begin
              if (in_valid && in_ready) begin
                valid_reg <= 1'b1;
                obs0_a_out <= obs0_a;
                obs1_a_out <= obs1_a;
                reward_a_out <= reward_a;
                next_value_a_out <= next_value_a;
                done_a_out <= done_a;
                obs0_b_out <= obs0_b;
                obs1_b_out <= obs1_b;
                reward_b_out <= reward_b;
                next_value_b_out <= next_value_b;
                done_b_out <= done_b;
              end else if (consume_ready) begin
                valid_reg <= 1'b0;
              end
            end
          end

        endmodule
        """
    )
    dual_policy_value_core = dedent(
        """\
        module dual_policy_value_core #(
            parameter DATA_WIDTH = 8
        ) (
            input wire in_valid,
            input wire [DATA_WIDTH-1:0] obs0_a,
            input wire [DATA_WIDTH-1:0] obs1_a,
            input wire [DATA_WIDTH-1:0] obs0_b,
            input wire [DATA_WIDTH-1:0] obs1_b,
            input wire [DATA_WIDTH-1:0] weight0,
            input wire [DATA_WIDTH-1:0] bias0,
            input wire [DATA_WIDTH-1:0] weight1,
            input wire [DATA_WIDTH-1:0] bias1,
            input wire enable,
            output wire out_valid,
            output wire selected_action_a,
            output wire [DATA_WIDTH-1:0] value_estimate_a,
            output wire selected_action_b,
            output wire [DATA_WIDTH-1:0] value_estimate_b
        );

          wire [(2*DATA_WIDTH)-1:0] score0_a_full;
          wire [(2*DATA_WIDTH)-1:0] score1_a_full;
          wire [(2*DATA_WIDTH)-1:0] score0_b_full;
          wire [(2*DATA_WIDTH)-1:0] score1_b_full;
          wire [DATA_WIDTH-1:0] score0_a;
          wire [DATA_WIDTH-1:0] score1_a;
          wire [DATA_WIDTH-1:0] score0_b;
          wire [DATA_WIDTH-1:0] score1_b;
          wire [DATA_WIDTH:0] value_sum_a;
          wire [DATA_WIDTH:0] value_sum_b;
          wire average_discard_a;
          wire average_discard_b;

          assign score0_a_full = (obs0_a * weight0) + {{DATA_WIDTH{1'b0}}, bias0};
          assign score1_a_full = (obs1_a * weight1) + {{DATA_WIDTH{1'b0}}, bias1};
          assign score0_b_full = (obs0_b * weight0) + {{DATA_WIDTH{1'b0}}, bias0};
          assign score1_b_full = (obs1_b * weight1) + {{DATA_WIDTH{1'b0}}, bias1};
          assign score0_a = |score0_a_full[(2*DATA_WIDTH)-1:DATA_WIDTH] ? {DATA_WIDTH{1'b1}} :
                            score0_a_full[DATA_WIDTH-1:0];
          assign score1_a = |score1_a_full[(2*DATA_WIDTH)-1:DATA_WIDTH] ? {DATA_WIDTH{1'b1}} :
                            score1_a_full[DATA_WIDTH-1:0];
          assign score0_b = |score0_b_full[(2*DATA_WIDTH)-1:DATA_WIDTH] ? {DATA_WIDTH{1'b1}} :
                            score0_b_full[DATA_WIDTH-1:0];
          assign score1_b = |score1_b_full[(2*DATA_WIDTH)-1:DATA_WIDTH] ? {DATA_WIDTH{1'b1}} :
                            score1_b_full[DATA_WIDTH-1:0];
          assign value_sum_a = {1'b0, score0_a} + {1'b0, score1_a};
          assign value_sum_b = {1'b0, score0_b} + {1'b0, score1_b};
          assign average_discard_a = value_sum_a[0];
          assign average_discard_b = value_sum_b[0];
          assign selected_action_a = (score1_a > score0_a) |
                                     (average_discard_a & (score1_a > score0_a));
          assign selected_action_b = (score1_b > score0_b) |
                                     (average_discard_b & (score1_b > score0_b));
          assign value_estimate_a = value_sum_a[DATA_WIDTH:1];
          assign value_estimate_b = value_sum_b[DATA_WIDTH:1];
          assign out_valid = in_valid && enable;

        endmodule
        """
    )
    dual_td_update_core = dedent(
        """\
        module dual_td_update_core #(
            parameter DATA_WIDTH = 8
        ) (
            input wire in_valid,
            input wire [DATA_WIDTH-1:0] reward_a,
            input wire [DATA_WIDTH-1:0] next_value_a,
            input wire [DATA_WIDTH-1:0] value_estimate_a,
            input wire [DATA_WIDTH-1:0] reward_b,
            input wire [DATA_WIDTH-1:0] next_value_b,
            input wire [DATA_WIDTH-1:0] value_estimate_b,
            input wire [DATA_WIDTH-1:0] alpha,
            output wire out_valid,
            output wire [DATA_WIDTH-1:0] updated_value_a,
            output wire [DATA_WIDTH-1:0] updated_value_b
        );

          wire [DATA_WIDTH:0] td_error_a_full;
          wire [DATA_WIDTH:0] td_error_b_full;
          wire [(2*DATA_WIDTH)-1:0] update_product_a;
          wire [(2*DATA_WIDTH)-1:0] update_product_b;
          wire [DATA_WIDTH-1:0] td_error_a_limited;
          wire [DATA_WIDTH-1:0] td_error_b_limited;
          wire [DATA_WIDTH-1:0] update_delta_a;
          wire [DATA_WIDTH-1:0] update_delta_b;
          wire update_delta_a_round;
          wire update_delta_b_round;
          wire update_delta_a_overflow;
          wire update_delta_b_overflow;

          assign td_error_a_full = {1'b0, reward_a} + {1'b0, next_value_a} - {1'b0, value_estimate_a};
          assign td_error_b_full = {1'b0, reward_b} + {1'b0, next_value_b} - {1'b0, value_estimate_b};
          assign td_error_a_limited = td_error_a_full[DATA_WIDTH] ? {DATA_WIDTH{1'b1}} :
                                      td_error_a_full[DATA_WIDTH-1:0];
          assign td_error_b_limited = td_error_b_full[DATA_WIDTH] ? {DATA_WIDTH{1'b1}} :
                                      td_error_b_full[DATA_WIDTH-1:0];
          assign update_product_a = alpha * td_error_a_limited;
          assign update_product_b = alpha * td_error_b_limited;
          assign update_delta_a_round = |update_product_a[3:0];
          assign update_delta_b_round = |update_product_b[3:0];
          assign update_delta_a_overflow = |update_product_a[(2*DATA_WIDTH)-1:DATA_WIDTH+4];
          assign update_delta_b_overflow = |update_product_b[(2*DATA_WIDTH)-1:DATA_WIDTH+4];
          assign update_delta_a = update_delta_a_overflow ? {DATA_WIDTH{1'b1}} :
                                  update_product_a[DATA_WIDTH+3:4];
          assign update_delta_b = update_delta_b_overflow ? {DATA_WIDTH{1'b1}} :
                                  update_product_b[DATA_WIDTH+3:4];
          assign updated_value_a = value_estimate_a + update_delta_a;
          assign updated_value_b = value_estimate_b + update_delta_b;
          assign out_valid = in_valid |
                             ((update_delta_a_round | update_delta_b_round) & in_valid);

        endmodule
        """
    )
    batch_result_stage = dedent(
        """\
        module batch_result_stage #(
            parameter DATA_WIDTH = 8
        ) (
            input wire clk,
            input wire rst_n,
            input wire in_valid,
            output wire out_ready,
            input wire selected_action_a,
            input wire [DATA_WIDTH-1:0] value_estimate_a,
            input wire [DATA_WIDTH-1:0] updated_value_a,
            input wire selected_action_b,
            input wire [DATA_WIDTH-1:0] value_estimate_b,
            input wire [DATA_WIDTH-1:0] updated_value_b,
            input wire done_a,
            input wire done_b,
            output reg result_valid,
            input wire result_ready,
            output reg selected_action_a_out,
            output reg [DATA_WIDTH-1:0] value_estimate_a_out,
            output reg [DATA_WIDTH-1:0] updated_value_a_out,
            output reg selected_action_b_out,
            output reg [DATA_WIDTH-1:0] value_estimate_b_out,
            output reg [DATA_WIDTH-1:0] updated_value_b_out,
            output reg batch_done_out,
            output reg irq
        );

          assign out_ready = !result_valid || result_ready;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              result_valid <= 1'b0;
              selected_action_a_out <= 1'b0;
              value_estimate_a_out <= {DATA_WIDTH{1'b0}};
              updated_value_a_out <= {DATA_WIDTH{1'b0}};
              selected_action_b_out <= 1'b0;
              value_estimate_b_out <= {DATA_WIDTH{1'b0}};
              updated_value_b_out <= {DATA_WIDTH{1'b0}};
              batch_done_out <= 1'b0;
              irq <= 1'b0;
            end else begin
              if (result_valid && result_ready) begin
                if (batch_done_out) begin
                  irq <= 1'b1;
                end
                result_valid <= 1'b0;
              end
              if (in_valid && out_ready) begin
                result_valid <= 1'b1;
                selected_action_a_out <= selected_action_a;
                value_estimate_a_out <= value_estimate_a;
                updated_value_a_out <= updated_value_a;
                selected_action_b_out <= selected_action_b;
                value_estimate_b_out <= value_estimate_b;
                updated_value_b_out <= updated_value_b;
                batch_done_out <= done_a | done_b;
              end
            end
          end

        endmodule
        """
    )
    return {
        "rtl/top.v": top,
        "rtl/batch_config_bank.v": batch_config_bank,
        "rtl/batch_sample_buffer.v": batch_sample_buffer,
        "rtl/dual_policy_value_core.v": dual_policy_value_core,
        "rtl/dual_td_update_core.v": dual_td_update_core,
        "rtl/batch_result_stage.v": batch_result_stage,
    }


def composed_replay_arbiter_shell_rtl_files(width: int) -> dict[str, str]:
    msb = width - 1
    top = dedent(
        f"""\
        module top (
            input wire clk,
            input wire rst_n,
            input wire host_valid,
            output wire host_ready,
            input wire [{msb}:0] host_state,
            input wire host_action,
            input wire [{msb}:0] host_reward,
            input wire [{msb}:0] host_next_state,
            input wire host_done,
            input wire sample_req_valid,
            output wire sample_req_ready,
            input wire [1:0] sample_index,
            output wire sample_valid,
            input wire sample_ready,
            output wire [{msb}:0] sample_state,
            output wire sample_action,
            output wire [{msb}:0] sample_reward,
            output wire [{msb}:0] sample_next_state,
            output wire sample_done,
            output wire [2:0] occupancy,
            output wire [1:0] write_index,
            output wire irq
        );

          wire packet_valid;
          wire packet_ready;
          wire [{msb}:0] packet_state;
          wire packet_action;
          wire [{msb}:0] packet_reward;
          wire [{msb}:0] packet_next_state;
          wire packet_done;
          wire mem_write_valid;
          wire [1:0] mem_write_addr;
          wire [{msb}:0] mem_write_state;
          wire mem_write_action;
          wire [{msb}:0] mem_write_reward;
          wire [{msb}:0] mem_write_next_state;
          wire mem_write_done;
          wire mem_read_valid;
          wire [1:0] mem_read_addr;
          wire write_accepted;
          wire read_valid_out;
          wire [{msb}:0] read_state;
          wire read_action;
          wire [{msb}:0] read_reward;
          wire [{msb}:0] read_next_state;
          wire read_done;
          wire sample_stage_ready;

          host_transition_packetizer #(
            .DATA_WIDTH({width})
          ) u_host_transition_packetizer (
            .host_valid(host_valid),
            .host_ready(host_ready),
            .host_state(host_state),
            .host_action(host_action),
            .host_reward(host_reward),
            .host_next_state(host_next_state),
            .host_done(host_done),
            .packet_ready(packet_ready),
            .packet_valid(packet_valid),
            .packet_state(packet_state),
            .packet_action(packet_action),
            .packet_reward(packet_reward),
            .packet_next_state(packet_next_state),
            .packet_done(packet_done)
          );

          replay_index_allocator u_replay_index_allocator (
            .clk(clk),
            .rst_n(rst_n),
            .write_accepted(write_accepted),
            .write_index(write_index),
            .occupancy(occupancy)
          );

          replay_request_arbiter #(
            .DATA_WIDTH({width})
          ) u_replay_request_arbiter (
            .write_valid(packet_valid),
            .write_ready(packet_ready),
            .write_index(write_index),
            .occupancy(occupancy),
            .write_state(packet_state),
            .write_action(packet_action),
            .write_reward(packet_reward),
            .write_next_state(packet_next_state),
            .write_done(packet_done),
            .read_req_valid(sample_req_valid),
            .sample_index(sample_index),
            .sample_stage_ready(sample_stage_ready),
            .sample_req_ready(sample_req_ready),
            .mem_write_valid(mem_write_valid),
            .mem_write_addr(mem_write_addr),
            .mem_write_state(mem_write_state),
            .mem_write_action(mem_write_action),
            .mem_write_reward(mem_write_reward),
            .mem_write_next_state(mem_write_next_state),
            .mem_write_done(mem_write_done),
            .mem_read_valid(mem_read_valid),
            .mem_read_addr(mem_read_addr),
            .write_accepted(write_accepted)
          );

          replay_memory_bank #(
            .DATA_WIDTH({width})
          ) u_replay_memory_bank (
            .clk(clk),
            .rst_n(rst_n),
            .write_valid(mem_write_valid),
            .write_addr(mem_write_addr),
            .write_state(mem_write_state),
            .write_action(mem_write_action),
            .write_reward(mem_write_reward),
            .write_next_state(mem_write_next_state),
            .write_done(mem_write_done),
            .read_valid(mem_read_valid),
            .read_addr(mem_read_addr),
            .read_valid_out(read_valid_out),
            .read_state(read_state),
            .read_action(read_action),
            .read_reward(read_reward),
            .read_next_state(read_next_state),
            .read_done(read_done)
          );

          sample_packet_stage #(
            .DATA_WIDTH({width})
          ) u_sample_packet_stage (
            .clk(clk),
            .rst_n(rst_n),
            .in_valid(read_valid_out),
            .in_ready(sample_stage_ready),
            .sample_state(read_state),
            .sample_action(read_action),
            .sample_reward(read_reward),
            .sample_next_state(read_next_state),
            .sample_done(read_done),
            .sample_valid(sample_valid),
            .sample_ready(sample_ready),
            .sample_state_out(sample_state),
            .sample_action_out(sample_action),
            .sample_reward_out(sample_reward),
            .sample_next_state_out(sample_next_state),
            .sample_done_out(sample_done),
            .irq(irq)
          );

        endmodule
        """
    )
    host_transition_packetizer = dedent(
        """\
        module host_transition_packetizer #(
            parameter DATA_WIDTH = 8
        ) (
            input wire host_valid,
            output wire host_ready,
            input wire [DATA_WIDTH-1:0] host_state,
            input wire host_action,
            input wire [DATA_WIDTH-1:0] host_reward,
            input wire [DATA_WIDTH-1:0] host_next_state,
            input wire host_done,
            input wire packet_ready,
            output wire packet_valid,
            output wire [DATA_WIDTH-1:0] packet_state,
            output wire packet_action,
            output wire [DATA_WIDTH-1:0] packet_reward,
            output wire [DATA_WIDTH-1:0] packet_next_state,
            output wire packet_done
        );

          assign host_ready = packet_ready;
          assign packet_valid = host_valid && packet_ready;
          assign packet_state = host_state;
          assign packet_action = host_action;
          assign packet_reward = host_reward;
          assign packet_next_state = host_next_state;
          assign packet_done = host_done;

        endmodule
        """
    )
    replay_index_allocator = dedent(
        """\
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
        """
    )
    replay_request_arbiter = dedent(
        """\
        module replay_request_arbiter #(
            parameter DATA_WIDTH = 8
        ) (
            input wire write_valid,
            output wire write_ready,
            input wire [1:0] write_index,
            input wire [2:0] occupancy,
            input wire [DATA_WIDTH-1:0] write_state,
            input wire write_action,
            input wire [DATA_WIDTH-1:0] write_reward,
            input wire [DATA_WIDTH-1:0] write_next_state,
            input wire write_done,
            input wire read_req_valid,
            input wire [1:0] sample_index,
            input wire sample_stage_ready,
            output wire sample_req_ready,
            output wire mem_write_valid,
            output wire [1:0] mem_write_addr,
            output wire [DATA_WIDTH-1:0] mem_write_state,
            output wire mem_write_action,
            output wire [DATA_WIDTH-1:0] mem_write_reward,
            output wire [DATA_WIDTH-1:0] mem_write_next_state,
            output wire mem_write_done,
            output wire mem_read_valid,
            output wire [1:0] mem_read_addr,
            output wire write_accepted
        );

          wire read_index_valid;

          assign write_ready = 1'b1;
          assign write_accepted = write_valid && write_ready;
          assign read_index_valid = {1'b0, sample_index} < occupancy;
          assign sample_req_ready = !write_valid && read_index_valid && sample_stage_ready;
          assign mem_write_valid = write_accepted;
          assign mem_write_addr = write_index;
          assign mem_write_state = write_state;
          assign mem_write_action = write_action;
          assign mem_write_reward = write_reward;
          assign mem_write_next_state = write_next_state;
          assign mem_write_done = write_done;
          assign mem_read_valid = read_req_valid && sample_req_ready;
          assign mem_read_addr = sample_index;

        endmodule
        """
    )
    replay_memory_bank = dedent(
        """\
        module replay_memory_bank #(
            parameter DATA_WIDTH = 8
        ) (
            input wire clk,
            input wire rst_n,
            input wire write_valid,
            input wire [1:0] write_addr,
            input wire [DATA_WIDTH-1:0] write_state,
            input wire write_action,
            input wire [DATA_WIDTH-1:0] write_reward,
            input wire [DATA_WIDTH-1:0] write_next_state,
            input wire write_done,
            input wire read_valid,
            input wire [1:0] read_addr,
            output reg read_valid_out,
            output reg [DATA_WIDTH-1:0] read_state,
            output reg read_action,
            output reg [DATA_WIDTH-1:0] read_reward,
            output reg [DATA_WIDTH-1:0] read_next_state,
            output reg read_done
        );

          reg [DATA_WIDTH-1:0] state_mem [0:3];
          reg action_mem [0:3];
          reg [DATA_WIDTH-1:0] reward_mem [0:3];
          reg [DATA_WIDTH-1:0] next_state_mem [0:3];
          reg done_mem [0:3];

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              read_valid_out <= 1'b0;
              read_state <= {DATA_WIDTH{1'b0}};
              read_action <= 1'b0;
              read_reward <= {DATA_WIDTH{1'b0}};
              read_next_state <= {DATA_WIDTH{1'b0}};
              read_done <= 1'b0;
            end else begin
              read_valid_out <= read_valid;
              if (write_valid) begin
                state_mem[write_addr] <= write_state;
                action_mem[write_addr] <= write_action;
                reward_mem[write_addr] <= write_reward;
                next_state_mem[write_addr] <= write_next_state;
                done_mem[write_addr] <= write_done;
              end
              if (read_valid) begin
                read_state <= state_mem[read_addr];
                read_action <= action_mem[read_addr];
                read_reward <= reward_mem[read_addr];
                read_next_state <= next_state_mem[read_addr];
                read_done <= done_mem[read_addr];
              end
            end
          end

        endmodule
        """
    )
    sample_packet_stage = dedent(
        """\
        module sample_packet_stage #(
            parameter DATA_WIDTH = 8
        ) (
            input wire clk,
            input wire rst_n,
            input wire in_valid,
            output wire in_ready,
            input wire [DATA_WIDTH-1:0] sample_state,
            input wire sample_action,
            input wire [DATA_WIDTH-1:0] sample_reward,
            input wire [DATA_WIDTH-1:0] sample_next_state,
            input wire sample_done,
            output reg sample_valid,
            input wire sample_ready,
            output reg [DATA_WIDTH-1:0] sample_state_out,
            output reg sample_action_out,
            output reg [DATA_WIDTH-1:0] sample_reward_out,
            output reg [DATA_WIDTH-1:0] sample_next_state_out,
            output reg sample_done_out,
            output reg irq
        );

          assign in_ready = !sample_valid || sample_ready;

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              sample_valid <= 1'b0;
              sample_state_out <= {DATA_WIDTH{1'b0}};
              sample_action_out <= 1'b0;
              sample_reward_out <= {DATA_WIDTH{1'b0}};
              sample_next_state_out <= {DATA_WIDTH{1'b0}};
              sample_done_out <= 1'b0;
              irq <= 1'b0;
            end else begin
              if (sample_valid && sample_ready) begin
                irq <= 1'b1;
                sample_valid <= 1'b0;
              end
              if (in_valid && in_ready) begin
                sample_valid <= 1'b1;
                sample_state_out <= sample_state;
                sample_action_out <= sample_action;
                sample_reward_out <= sample_reward;
                sample_next_state_out <= sample_next_state;
                sample_done_out <= sample_done;
              end
            end
          end

        endmodule
        """
    )
    return {
        "rtl/top.v": top,
        "rtl/host_transition_packetizer.v": host_transition_packetizer,
        "rtl/replay_index_allocator.v": replay_index_allocator,
        "rtl/replay_request_arbiter.v": replay_request_arbiter,
        "rtl/replay_memory_bank.v": replay_memory_bank,
        "rtl/sample_packet_stage.v": sample_packet_stage,
    }
