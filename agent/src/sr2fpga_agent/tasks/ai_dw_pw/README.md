# Fixed DW→PW development control

This exposed engineering task fixes N=1, H=4, W=5, Cin=3, Cout=5 and two INT8
lanes. `build_development_task()` returns public facts, boundary, asset bytes and
local profile metadata. Its exact algorithm and scales are public; its original
weight JSON bytes have a stable SHA-256 in the public facts. Internal module
decomposition remains free. It does not change the task catalog or qualify a
formal task population.

`reference_design()` is a hand-authored PC control. `reference.py` supplies two
explicit reference behavior bodies and a separate manual wrapper. These are
never inserted by the generic emitter and are not model results. The oracle
uses exact Python integer/Fraction math; the RTL independently implements a
serial frame/pixel machine and signed integer quotient/remainder rounding.
Both consume the same public constants, without using expected-output tables
in RTL. Accumulator bounds and a distinct patch/dot-product reference are
checked by the dedicated tests.

`harness.py` is evaluator-owned and must not be placed in candidate context.
It drives three complete frames, partial-input and stalled-output resets,
source pauses, two-cycle output stalls, tail masks and a twelve-cycle drain.
The scoreboard reconstructs expected math from accepted inputs and checks
every offered output, complete counts, reset cancellation, stable stalled
tokens and the 2048-cycle per-invocation bound. PASS strings, early finish and
successful simulator exit cannot replace trace completion.

The hand-calculated packing/bias example is in
`agent/tests/fixtures/ai_dw_pw_dev/hand_golden.json`. Run the dedicated tests
with this checkout's `agent/src` on `PYTHONPATH`, a new artifact-directory
`--basetemp`, and `-p no:cacheprovider`. HDL tests require the actual Icarus and
vvp tools; tool crashes fail and are retained. No model, held-out or physical
evaluation is part of these tests. This fixed suite is not a proof of all
possible INT8 tensors, time/resource performance, general quantization support,
or qualification of all three AI families.

Initial development validation on 2026-10-26: 13 math/boundary/packing/trace tests passed.
The dedicated HDL test passed once outside the execution sandbox: actual Icarus
compile and vvp simulation both exited 0. The independently checked trace has
1025 cycles, three completed invocations, 167 accepted input beats (including
7+40 cancelled by reset), 180 output beats, three resets and two cancellations.
The same test also rejects a corrupted real output trace. This is a manual
control result, with no model call or official task qualification.

The preserved run directory is
`artifacts/paper1-ai/validation-20261026/reference-external-01/test_manual_control_hdl_end_to0/`.
Its original tool-record content hashes are:

| Artifact | SHA-256 |
| --- | --- |
| `compile.json` | `3066f18f238833a8cd72d70ccfa734c1b769b2289e032353b48f2d0867dbbd48` |
| `simulation.json` | `de86a10c9d1510a6b54052507cd94db2971e02b7e94b9a551e9ed0d51a02310d` |

Earlier sandboxed test compilations returned Windows access violation
3221225477, including verbose and nonverbose invocations; these failures remain
under the separate `task-02` through `task-05` validation directories. They were
not converted to passes and their leftover output files were not executed.
A separate successful standalone verbose compile/simulation is retained under
`task-02`; its output also passes the strengthened reset monitor. An independent
Yosys read/hierarchy/process/check completed with zero reported problems, but
that parse check alone does not establish full synthesis or L3 qualification.
A subsequent full-synthesis subprocess did not return through the sandboxed
runner's timeout path and was interrupted; it supplies no synthesis result.

Later on 2026-10-26 the reference was implemented with one DW kernel MAC per
clock. The actual PC-emitted reference then passed full generic synthesis,
compilation and a 2936-cycle complete schedule, under the unchanged 2048-cycle
per-invocation limit. See `artifacts/paper1-ai/dw-pw-reference-20261026-04/`.
This supersedes the earlier synthesis limitation for that exact reference.

Before candidate evaluation, the monitor was corrected to ignore payload bits
when valid=0; the dedicated mathematical/trace subset now has 14 passing tests.
The reference trace also passes the corrected monitor. A generated candidate
then passed both public and distinct-input terminal development suites, each
with three completed invocations and 180 output beats, plus full generic
synthesis. See `artifacts/paper1-ai/dw-pw-candidate-20261026-02/README.md` for
the three candidate calls, first schema failure, exact sources, tool logs,
evaluator continuation, and shared-agent isolation limitations.
