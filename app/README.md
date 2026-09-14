# SR2FPGA UI demo

Display terminology follows the [2026-09-08 naming table](../docs/specs/2026-09-08-sr2fpga-terminology.md):
Project Contract (PC), 工程契约; FPGA Project Package (FPP), FPGA 工程包.
Internal `system_his` fields and the System-HIS v1.2 serialization stay unchanged.

This local demo connects the existing static interface to the current Agent
runtime. It uses the deterministic reference generator, runs the normal
requirement boundary and H0-H3/L0-L4 pipeline, and reads the resulting files and
statuses from the recorded sample artifacts.

It is a local demonstration surface, not a Paper-1 method condition, official
evaluation path, or research-evidence producer.

From the repository root:

```powershell
python app/server.py
```

Then open <http://127.0.0.1:8000>.

Generated samples are written under `artifacts/agent/ui-demo/`. The default
flow makes no model API call and needs no API key. Local Verilator, Icarus, and
Yosys availability determines which tool stages can run; unavailable stages
remain `not_run`. L2 also remains `not_run` when there is no evaluator-trusted
oracle, even if the generated project contains a candidate smoke testbench.

The UART option intentionally demonstrates the current requirement-boundary
`capability_gap` outcome. It is not reported as a generated-project failure.

The demo validates engineering context against the selected deterministic
template before generation. Clock frequency is passed into the platform and
generated constraints. The current templates use `top`, active-low asynchronous
reset, their declared ports, the generic Verilog target, and the complete
RTL/testbench/constraints/README bundle. Requests for other interfaces, reset
strategies, targets or delivery scopes stop with `capability_gap`; conflicting
text and form facts require clarification. The sample button obtains supported
settings from the backend registry. Submitted context is retained in sample
metadata, and README is created before evaluation and recording.
