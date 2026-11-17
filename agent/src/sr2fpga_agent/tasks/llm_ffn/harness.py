"""Evaluator-owned FFN development inputs, reset/stall driver and scoreboard."""

from __future__ import annotations

from dataclasses import dataclass
import random

from .oracle import evaluate_token, pack_tensor, unpack_tensor
from .task import INPUT_BEATS, OUTPUT_BEATS, COMPLETION_CYCLES

TESTBENCH_TOP = "trusted_llm_ffn_tb"


def development_frames() -> tuple[tuple[int, ...], ...]:
    rng = random.Random(1817)
    return ((0,) * 10, (-128, 127, -4, 3, 11, 31, -17, 0, 1, -2),
            tuple(rng.randrange(-128, 128) for _ in range(10)))


@dataclass(frozen=True)
class TraceResult:
    cycles: int
    completed_invocations: int
    input_beats: int
    output_beats: int
    resets: int
    cancelled_invocations: int


def check_trace(stdout: str, *, expected_completed: int = 3) -> TraceResult:
    """Reconstruct answers from accepted inputs; a PASS line grants no credit."""
    incoming, pending = [], []
    complete = resets = cancelled = input_count = output_count = last_cycle = frame_output_count = 0
    previous_input = previous_output = None
    start_cycle = None
    was_reset = ended = False
    for line in stdout.splitlines():
        if line.startswith("TRACE_END "):
            if ended or line.split() != ["TRACE_END", str(last_cycle)]:
                raise ValueError("invalid trace completion")
            ended = True
            continue
        if not line.startswith("TRACE "):
            continue
        if ended:
            raise ValueError("trace after completion")
        fields = line.split()
        if len(fields) != 9:
            raise ValueError("malformed trace")
        try:
            cycle, reset = map(int, fields[1:3])
            if not reset:
                if was_reset and fields[6] != "0":
                    raise ValueError("output valid persisted after reset")
                iv = ir = ip = ov = ready = op = 0
            else:
                iv, ir = map(int, fields[3:5])
                ov, ready = map(int, fields[6:8])
                ip = int(fields[5], 16) if iv else 0
                op = int(fields[8], 16) if ov else 0
        except ValueError as error:
            raise ValueError("unknown or invalid trace signal: " + str(error)) from error
        if cycle != last_cycle + 1 or any(value not in (0, 1) for value in (reset, iv, ir, ov, ready)):
            raise ValueError("noncontiguous trace or nonbinary control")
        if not 0 <= ip < 2**18 or not 0 <= op < 2**18:
            raise ValueError("invalid packed payload width")
        last_cycle = cycle
        if not reset:
            if not was_reset:
                resets += 1
                cancelled += bool(incoming or pending)
            incoming.clear()
            pending.clear()
            frame_output_count = 0
            previous_input = previous_output = start_cycle = None
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
        # Check before completing/clearing the invocation, including its last beat.
        if start_cycle is not None and cycle - start_cycle > COMPLETION_CYCLES:
            raise ValueError("bounded completion exceeded")
        if iv and ir:
            if len(incoming) >= INPUT_BEATS:
                raise ValueError("new input before previous output completed")
            incoming.append(ip)
            input_count += 1
            if len(incoming) % 3 == 0:
                pending.extend(pack_tensor(evaluate_token(unpack_tensor(incoming[-3:]))))
        if ov:
            if not pending:
                raise ValueError("unexpected or premature output")
            if op != pending[0]:
                raise ValueError(f"output mismatch at cycle {cycle}: got {op:05x}, expected {pending[0]:05x}")
            if ready:
                pending.pop(0)
                output_count += 1
                frame_output_count += 1
        if len(incoming) == INPUT_BEATS and not pending and frame_output_count == OUTPUT_BEATS:
            complete += 1
            incoming.clear()
            frame_output_count = 0
            start_cycle = None
    if not ended or not last_cycle or incoming or pending or previous_input is not None or previous_output is not None:
        raise ValueError("incomplete trusted simulation schedule")
    if complete != expected_completed:
        raise ValueError(f"expected {expected_completed} complete invocations, got {complete}")
    return TraceResult(last_cycle, complete, input_count, output_count, resets, cancelled)


def render_testbench(frames: tuple[tuple[int, ...], ...] | None = None) -> str:
    frames = frames if frames is not None else development_frames()
    if len(frames) != 3:
        raise ValueError("fixed suite requires three complete frames")
    packed = [pack_tensor(frame) for frame in frames]
    if any(len(frame) != INPUT_BEATS for frame in packed):
        raise ValueError("fixed FFN requires six input beats")
    assignments = "\n".join(f"stimulus[{i * INPUT_BEATS + j}]=18'h{value:05x};"
                              for i, frame in enumerate(packed) for j, value in enumerate(frame))
    return """module trusted_llm_ffn_tb;
reg clk=0,rst_n=0,in_valid=0;
reg [17:0] in_payload=0;
wire in_ready,out_valid;
wire [17:0] out_payload;
reg out_ready=0,forced_stall=0,drain=0;
integer cycle=0,completed_beats=0,i;
reg [17:0] stimulus[0:17];
LlmGatedFfnDev dut(.clk(clk),.rst_n(rst_n),.in_payload(in_payload),.in_valid(in_valid),
 .in_ready(in_ready),.out_payload(out_payload),.out_valid(out_valid),.out_ready(out_ready));
always #5 clk=~clk;
always @(negedge clk) out_ready=!forced_stall && (drain || (cycle%7!=0 && cycle%7!=1));
always @(posedge clk) begin
 cycle=cycle+1;
 $display("TRACE %0d %0d %0d %0d %05h %0d %0d %05h",cycle,rst_n,in_valid,in_ready,in_payload,out_valid,out_ready,out_payload);
 if(!rst_n) completed_beats=0;
 else if(out_valid && out_ready) completed_beats=completed_beats+1;
 if(cycle>4000) begin $display("TRUSTED_TIMEOUT"); $finish; end
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
 while(in_ready!==1'b1) @(posedge clk);
 @(negedge clk); in_valid=0;
end
endtask
initial begin
""" + assignments + f"""
 reset_dut;
 for(i=0;i<2;i=i+1) send_beat(stimulus[i]);
 reset_dut;
 forced_stall=1;
 fork : stalled_reset_probe
  begin
   for(i=0;i<{INPUT_BEATS};i=i+1) send_beat(stimulus[i]);
  end
  begin
   wait(out_valid===1'b1);
   repeat(2) @(negedge clk);
   disable stalled_reset_probe;
  end
 join
 reset_dut;
 forced_stall=0;
 for(i=0;i<{INPUT_BEATS};i=i+1) send_beat(stimulus[i]);
 wait(completed_beats=={OUTPUT_BEATS});
 for(i={INPUT_BEATS};i<{2 * INPUT_BEATS};i=i+1) send_beat(stimulus[i]);
 wait(completed_beats=={2 * OUTPUT_BEATS});
 for(i={2 * INPUT_BEATS};i<{3 * INPUT_BEATS};i=i+1) send_beat(stimulus[i]);
 wait(completed_beats=={3 * OUTPUT_BEATS});
 @(negedge clk); drain=1;
 repeat(12) @(negedge clk);
 $display("TRACE_END %0d",cycle);
 $finish;
end
endmodule
"""
