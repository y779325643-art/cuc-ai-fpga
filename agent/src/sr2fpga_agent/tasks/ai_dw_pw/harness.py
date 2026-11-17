"""Evaluator-owned development simulation driver and complete-transaction checker.

Only the public task data is candidate-visible. This harness, test frames and
expected outputs belong to the evaluator, and never enter behavior prompts.
"""

from __future__ import annotations

from dataclasses import dataclass
import random

from .oracle import evaluate, pack_tensor, unpack_tensor


def development_frames() -> tuple[tuple[int, ...], ...]:
    rng = random.Random(4217)
    return ((-3,) * 60,
            tuple(((h * 41 + w * 17 + c * 67 + 11) % 256) - 128
                  for h in range(4) for w in range(5) for c in range(3)),
            tuple(rng.choice((-128, -127, -4, -3, -2, 0, 1, 126, 127)) for _ in range(60)))


@dataclass(frozen=True)
class TraceResult:
    cycles: int
    completed_invocations: int
    input_beats: int
    output_beats: int
    resets: int
    cancelled_invocations: int


def check_trace(stdout: str, *, expected_completed: int = 3) -> TraceResult:
    """Fail closed on malformed/unknown/stalled/wrong/extra/incomplete traces.

    Expected math is reconstructed from actual accepted input data. A candidate's
    PASS marker or exit status cannot satisfy this checker. TRACE_END must occur
    after every cycle in the complete trusted driver's schedule.
    """
    incoming: list[int] = []
    pending: list[int] = []
    input_count = output_count = complete = resets = cancelled = 0
    previous_input = previous_output = None
    last_cycle = 0
    ended = False
    was_reset = False
    start_cycle: int | None = None
    for line in stdout.splitlines():
        if line.startswith("TRACE_END "):
            if ended or int(line.split()[1]) != last_cycle:
                raise ValueError("invalid trace completion")
            ended = True
            continue
        if not line.startswith("TRACE "):
            continue
        if ended:
            raise ValueError("trace after completion")
        parts = line.split()
        if len(parts) != 9:
            raise ValueError("malformed trace")
        reset_output_violation = False
        try:
            cycle, reset = map(int, parts[1:3])
            if reset == 0:
                # Outputs may be unknown before the very first reset edge.
                # They are cancelled and cannot transfer while reset is active.
                reset_output_violation = was_reset and parts[6] != "0"
                iv = ir = ip = ov = ready = op = 0
            else:
                iv, ir = map(int, parts[3:5])
                ov, ready = map(int, parts[6:8])
                # Payload is meaningful only while valid is asserted. Idle X
                # bits are legal and must not become false DUT failures.
                ip = int(parts[5], 16) if iv else 0
                op = int(parts[8], 16) if ov else 0
        except ValueError as exc:
            raise ValueError("unknown or invalid signal in trace") from exc
        if reset_output_violation:
            raise ValueError("DUT output valid persisted after a reset edge")
        if cycle != last_cycle + 1 or any(v not in (0, 1) for v in (reset, iv, ir, ov, ready)):
            raise ValueError("noncontiguous cycle or nonbinary control")
        if not 0 <= ip < (1 << 18) or not 0 <= op < (1 << 18):
            raise ValueError("invalid packed payload width")
        last_cycle = cycle
        if not reset:
            if not was_reset:
                resets += 1
                cancelled += bool(incoming or pending)
            incoming.clear()
            pending.clear()
            previous_input = previous_output = None
            start_cycle = None
            was_reset = True
            continue
        was_reset = False
        if previous_input is not None and (not iv or ip != previous_input):
            raise ValueError("source changed a stalled token")
        if previous_output is not None and (not ov or op != previous_output):
            raise ValueError("DUT changed a stalled output token")
        previous_input = ip if iv and not ir else None
        previous_output = op if ov and not ready else None
        if iv and start_cycle is None:
            start_cycle = cycle
        if iv and ir:
            if pending:
                raise ValueError("new input invocation before previous output completed")
            incoming.append(ip)
            input_count += 1
            if len(incoming) == 40:
                pending = list(pack_tensor(evaluate(unpack_tensor(incoming, 3)), 5))
                incoming.clear()
        if ov:
            if not pending:
                raise ValueError("unexpected or premature output")
            if op != pending[0]:
                raise ValueError(f"output mismatch at cycle {cycle}: got {op:05x}, expected {pending[0]:05x}")
            if ready:
                pending.pop(0)
                output_count += 1
                if not pending:
                    complete += 1
                    start_cycle = None
        if start_cycle is not None and cycle - start_cycle > 2048:
            raise ValueError("bounded completion exceeded")
    if not ended or not last_cycle or incoming or pending or previous_output is not None:
        raise ValueError("incomplete trusted simulation schedule")
    if complete != expected_completed:
        raise ValueError(f"expected {expected_completed} completed invocations, observed {complete}")
    return TraceResult(last_cycle, complete, input_count, output_count, resets, cancelled)


def render_testbench(frames: tuple[tuple[int, ...], ...] | None = None) -> str:
    """Fixed public-development schedule: tails, pauses, backpressure and two aborts.

    Mid-input reset and stalled-output reset are followed by three complete
    invocations, then twelve ready drain cycles to detect duplicate/late outputs.
    """
    frames = frames if frames is not None else development_frames()
    if len(frames) != 3:
        raise ValueError("this bounded schedule needs exactly three complete frames")
    beats = [pack_tensor(frame, 3) for frame in frames]
    if any(len(frame) != 40 for frame in beats):
        raise ValueError("fixed profile requires forty input beats")
    assignments = "\n".join(f"stimulus[{i*40+j}] = 18'h{beat:05x};" for i, frame in enumerate(beats) for j, beat in enumerate(frame))
    return """module trusted_dw_pw_tb;
reg clk=0, rst_n=0, in_valid=0;
reg [17:0] in_payload=0;
wire in_ready, out_valid;
wire [17:0] out_payload;
reg out_ready=0, forced_stall=0, drain=0;
integer cycle=0, completed_beats=0, i;
reg [17:0] stimulus[0:119];
AiDwPwDev dut(.clk(clk),.rst_n(rst_n),.in_payload(in_payload),.in_valid(in_valid),
 .in_ready(in_ready),.out_payload(out_payload),.out_valid(out_valid),.out_ready(out_ready));
always #5 clk=~clk;
always @(negedge clk) out_ready = !forced_stall && (drain || (cycle%7 != 0 && cycle%7 != 1));
always @(posedge clk) begin
 cycle=cycle+1;
 $display("TRACE %0d %0d %0d %0d %05h %0d %0d %05h",cycle,rst_n,in_valid,in_ready,in_payload,out_valid,out_ready,out_payload);
 if(!rst_n) completed_beats=0;
 else if(out_valid && out_ready) completed_beats=completed_beats+1;
 if(cycle>12000) begin $display("TRUSTED_TIMEOUT"); $finish; end
end
task reset_dut;
begin
 @(negedge clk); rst_n=0; in_valid=0;
 repeat(3) @(negedge clk);
 rst_n=1;
end
endtask
task send_beat(input [17:0] value);
begin
 @(negedge clk); in_valid=1; in_payload=value;
 @(posedge clk);
 while(in_ready !== 1'b1) @(posedge clk);
 @(negedge clk); in_valid=0;
end
endtask
initial begin
""" + assignments + """
 reset_dut;
 for(i=0;i<7;i=i+1) send_beat(stimulus[i]);
 reset_dut;
 forced_stall=1;
 for(i=0;i<40;i=i+1) send_beat(stimulus[i]);
 wait(out_valid === 1'b1);
 repeat(2) @(negedge clk);
 reset_dut;
 forced_stall=0;
 for(i=0;i<40;i=i+1) send_beat(stimulus[i]);
 wait(completed_beats==60);
 for(i=40;i<80;i=i+1) send_beat(stimulus[i]);
 wait(completed_beats==120);
 for(i=80;i<120;i=i+1) send_beat(stimulus[i]);
 wait(completed_beats==180);
 @(negedge clk); drain=1;
 repeat(12) @(negedge clk);
 $display("TRACE_END %0d",cycle);
 $finish;
end
endmodule
"""
