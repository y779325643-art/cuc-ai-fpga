# SR2FPGA UI demo

This local demo connects the existing static interface to the current Agent
runtime. It uses the deterministic reference generator, runs the normal
requirement boundary and H0-H3/L0-L4 pipeline, and reads the resulting files and
statuses from the recorded sample artifacts.

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
