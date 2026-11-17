# Quantized LLM QKV projection development case

This fixed synthetic decoder-subsystem task projects two INT8 tokens of input
dimension five into four query heads and two key/value heads, each dimension
three. It exposes three independently stalled output streams, explicit head
order, signed round-to-nearest ties-to-even, saturation and nonzero affine
zero-points. It does not load a model checkpoint, apply RoPE, run attention or
establish language-model accuracy.

`task.py` contains candidate-visible facts and original weight asset bytes.
`reference_design()` declares a structural wrapper, explicit exactly-once input
broadcast and three projection behavior units. The generic emitter does not
contain the broadcast implementation or linear arithmetic. `reference.py`
provides hand-authored control bodies and a separate manual wrapper.

Each input token uses three 18-bit beats for five INT8 values. Each head uses
two beats for three values; the last lane is raw zero with mask zero. Q has
sixteen output beats per invocation, K and V each eight. Output order is
token, head, dimension; input order is token, channel. The input scale is 1/4,
input zero-point -2 and weight scale 1/2 with zero-point 0. Accumulation adds
bias once, then uses divisors Q=2/K=4/V=2, signed exact ties-even, output
zero-points Q=1/K=-1/V=3 and INT8 saturation. Public weights are deliberately
asymmetric synthetic constants, not a claim of compatibility with a released
LLM checkpoint.

The evaluator-owned `oracle.py` uses Python integers and Fraction independently
of the RTL's sign/magnitude quotient/remainder implementation. `harness.py`
drives source pauses, different two-cycle stalls for each output, partial-input
reset, pending-output reset, three complete invocations and a drain. Its
checker reconstructs expected outputs when each actual input token is accepted;
streaming candidates need not copy the control's full-frame buffering. It
checks all offered outputs, masks, stable stalled tokens and the 512-cycle bound
from first offer to final acceptance across all branches. Final-beat deadline
checks happen before completion cleanup. This file, stimuli and oracle remain
outside candidate prompts.

The stalled-output reset probe sends input concurrently with waiting for the
first offered output on any branch, then stops the source and resets. It does
not wait for the entire input frame or for all three branches to assert valid.
An additional explicit per-token RTL reference uses the same arithmetic and
verifies that an implementation which blocks later inputs while producing an
early token can complete this schedule without deadlock. The default reference
still buffers both input tokens before producing its first output.

Run the focused development tests from the repository root with this checkout's
`agent/src` on `PYTHONPATH`:

```powershell
python -B -m pytest agent/tests/test_sr2fpga_llm_qkv.py -q -p no:cacheprovider --basetemp=artifacts/paper1-ai/llm-case-migration-20261028/qkv-tests
```

Real parser and HDL tests require Yosys and Icarus/vvp. This fixed control is a
development case, not a qualified family, official candidate result, inference
latency benchmark or physical timing result. Prior CNN cases and evidence stay
historical and do not validate this case.
