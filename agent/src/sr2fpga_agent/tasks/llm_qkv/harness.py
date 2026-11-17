"""Evaluator-owned QKV driver and exact multi-stream transaction checker."""

from __future__ import annotations

from dataclasses import dataclass
import random

from .oracle import evaluate_token, pack_tensor, unpack_tensor
from .task import INPUT_DIM, TOKENS, HEAD_DIM, MODULES

TESTBENCH_TOP = "trusted_llm_qkv_tb"


def development_frames() -> tuple[tuple[int, ...], ...]:
    rng = random.Random(28491)
    return ((-2,) * 10, (3,) + (-2,) * 9,
            tuple(rng.choice((-128, -127, -3, -2, -1, 0, 1, 126, 127)) for _ in range(10)))


@dataclass(frozen=True)
class TraceResult:
    cycles: int
    completed_invocations: int
    input_beats: int
    output_beats: dict[str, int]
    resets: int
    cancelled_invocations: int


def check_trace(stdout: str, *, expected_completed: int = 3) -> TraceResult:
    """Compute answers from accepted input tokens; inspect offered output beats.

    An invocation may stream outputs before its second input token arrives.
    The checker never requires the reference's full-frame buffering schedule.
    Deadline checking precedes completion-state cleanup, including the last beat.
    """
    incoming: list[int] = []
    pending: dict[str, list[int]] = {branch: [] for branch in MODULES}
    previous: dict[str, int | None] = {branch: None for branch in MODULES}
    output_count = {branch: 0 for branch in MODULES}
    previous_input = None
    start_cycle = None
    last_cycle = completed = input_count = resets = cancelled = 0
    was_reset = ended = False
    for line in stdout.splitlines():
        if line.startswith("TRACE_END "):
            fields = line.split()
            if len(fields) != 2 or ended or int(fields[1]) != last_cycle:
                raise ValueError("invalid trace completion")
            ended = True
            continue
        if not line.startswith("TRACE "):
            continue
        fields = line.split()
        if ended or len(fields) != 15:
            raise ValueError("malformed trace or trace after completion")
        try:
            cycle, reset = map(int, fields[1:3])
            if cycle != last_cycle + 1 or reset not in (0, 1):
                raise ValueError("noncontiguous cycle or invalid reset")
            if not reset:
                if was_reset and any(fields[index] != "0" for index in (6, 9, 12)):
                    raise ValueError("output valid persisted following a reset edge")
                iv = ir = ip = 0
                outputs = {branch: (0, 0, 0) for branch in MODULES}
            else:
                iv, ir = map(int, fields[3:5])
                ip = int(fields[5], 16) if iv else 0
                outputs = {}
                for branch, index in zip(MODULES, (6, 9, 12)):
                    valid, ready = map(int, fields[index:index + 2])
                    payload = int(fields[index + 2], 16) if valid else 0
                    outputs[branch] = (valid, ready, payload)
                controls = [iv, ir] + [item for valid, ready, _ in outputs.values() for item in (valid, ready)]
                if any(control not in (0, 1) for control in controls):
                    raise ValueError("nonbinary control")
                if not 0 <= ip < 1 << 18 or any(not 0 <= item[2] < 1 << 18 for item in outputs.values()):
                    raise ValueError("invalid packed payload width")
        except ValueError as error:
            raise ValueError("invalid or unknown trace signal: " + str(error)) from error
        last_cycle = cycle
        if not reset:
            if not was_reset:
                resets += 1
                cancelled += start_cycle is not None
            incoming.clear()
            for branch in MODULES:
                pending[branch].clear()
                previous[branch] = None
            previous_input = start_cycle = None
            was_reset = True
            continue
        was_reset = False
        if iv and start_cycle is None:
            start_cycle = cycle
        if start_cycle is not None and cycle - start_cycle > 512:
            raise ValueError("bounded completion exceeded")
        if previous_input is not None and (not iv or ip != previous_input):
            raise ValueError("source changed a stalled token")
        previous_input = ip if iv and not ir else None
        if iv and ir:
            if len(incoming) >= 6:
                raise ValueError("next invocation input before all outputs completed")
            incoming.append(ip)
            input_count += 1
            if len(incoming) % 3 == 0:
                token = unpack_tensor(incoming[-3:], INPUT_DIM)
                for branch, values in evaluate_token(token).items():
                    pending[branch].extend(pack_tensor(values, HEAD_DIM))
        for branch, (valid, ready, payload) in outputs.items():
            if previous[branch] is not None and (not valid or payload != previous[branch]):
                raise ValueError("changed stalled " + branch + " token")
            previous[branch] = payload if valid and not ready else None
            if valid:
                if not pending[branch] or payload != pending[branch][0]:
                    raise ValueError("unexpected or wrong " + branch + " output")
                if ready:
                    pending[branch].pop(0)
                    output_count[branch] += 1
        if len(incoming) == 6 and not any(pending.values()):
            completed += 1
            incoming.clear()
            start_cycle = None
    if not ended or not last_cycle or incoming or any(pending.values()) or any(x is not None for x in previous.values()) or previous_input is not None:
        raise ValueError("incomplete trusted simulation schedule")
    if completed != expected_completed:
        raise ValueError(f"expected {expected_completed} completed invocations, observed {completed}")
    return TraceResult(last_cycle, completed, input_count, output_count, resets, cancelled)


def render_testbench(frames: tuple[tuple[int, ...], ...] | None = None) -> str:
    frames = frames if frames is not None else development_frames()
    if len(frames) != 3 or any(len(frame) != INPUT_DIM * TOKENS for frame in frames):
        raise ValueError("exactly three complete development invocations required")
    beats = [pack_tensor(frame, INPUT_DIM) for frame in frames]
    assignments = "\n".join(f"stimulus[{i * 6 + j}]=18'h{beat:05x};"
                            for i, invocation in enumerate(beats) for j, beat in enumerate(invocation))
    return """module trusted_llm_qkv_tb;
reg clk=0,rst_n=0,in_valid=0;
reg [17:0] in_payload=0;
wire in_ready,q_valid,k_valid,v_valid;
wire [17:0] q_payload,k_payload,v_payload;
reg q_ready=0,k_ready=0,v_ready=0,forced_stall=0,drain=0;
integer cycle=0,q_accepted=0,k_accepted=0,v_accepted=0,i;
reg [17:0] stimulus[0:17];
LlmQkvDev dut(.clk(clk),.rst_n(rst_n),.in_payload(in_payload),.in_valid(in_valid),.in_ready(in_ready),
 .q_payload(q_payload),.q_valid(q_valid),.q_ready(q_ready),
 .k_payload(k_payload),.k_valid(k_valid),.k_ready(k_ready),
 .v_payload(v_payload),.v_valid(v_valid),.v_ready(v_ready));
always #5 clk=~clk;
always @(negedge clk) begin
 q_ready=!forced_stall && (drain || (cycle%7!=0 && cycle%7!=1));
 k_ready=!forced_stall && (drain || (cycle%5!=1 && cycle%5!=2));
 v_ready=!forced_stall && (drain || (cycle%6!=3 && cycle%6!=4));
end
always @(posedge clk) begin
 cycle=cycle+1;
 $display("TRACE %0d %0d %0d %0d %05h %0d %0d %05h %0d %0d %05h %0d %0d %05h",
 cycle,rst_n,in_valid,in_ready,in_payload,q_valid,q_ready,q_payload,k_valid,k_ready,k_payload,v_valid,v_ready,v_payload);
 if(!rst_n) begin q_accepted=0;k_accepted=0;v_accepted=0;end
 else begin
  if(q_valid && q_ready) q_accepted=q_accepted+1;
  if(k_valid && k_ready) k_accepted=k_accepted+1;
  if(v_valid && v_ready) v_accepted=v_accepted+1;
 end
 if(cycle>10000) begin $display("TRUSTED_TIMEOUT");$finish;end
end
task reset_dut;
begin
 @(negedge clk);rst_n=0;in_valid=0;
 repeat(3) @(negedge clk);
 rst_n=1;
end
endtask
task send_beat(input [17:0] value);
begin
 @(negedge clk);in_valid=1;in_payload=value;
 @(posedge clk);while(in_ready !== 1'b1) @(posedge clk);
 @(negedge clk);in_valid=0;
end
endtask
initial begin
""" + assignments + """
 reset_dut;
 for(i=0;i<2;i=i+1) send_beat(stimulus[i]);
 reset_dut;
 forced_stall=1;
 fork : pending_output_probe
  begin
   for(i=0;i<6;i=i+1) send_beat(stimulus[i]);
   forever @(negedge clk);
  end
  begin
   wait(q_valid === 1'b1 || k_valid === 1'b1 || v_valid === 1'b1);
   repeat(2) @(negedge clk);
  end
 join_any
 disable pending_output_probe;
 reset_dut;
 forced_stall=0;
 for(i=0;i<6;i=i+1) send_beat(stimulus[i]);
 wait(q_accepted==16 && k_accepted==8 && v_accepted==8);
 for(i=6;i<12;i=i+1) send_beat(stimulus[i]);
 wait(q_accepted==32 && k_accepted==16 && v_accepted==16);
 for(i=12;i<18;i=i+1) send_beat(stimulus[i]);
 wait(q_accepted==48 && k_accepted==24 && v_accepted==24);
 @(negedge clk);drain=1;
 repeat(12) @(negedge clk);
 $display("TRACE_END %0d",cycle);
 $finish;
end
endmodule
"""
