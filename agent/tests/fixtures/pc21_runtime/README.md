# Explicit PC 2.1 runtime replay fixtures

`prepare_fixture.py` serializes the existing hand-authored controls as declared
synthetic responses. It prepares registered public inputs, full free-project
proposals, a PC proposal and the exact behavior bundle; no model, parser or
simulation is called while preparing. The runtime itself contains no such
answer-generation hook.

From the repository root:

```powershell
$env:PYTHONPATH = (Resolve-Path agent/src).Path
python -B agent/tests/fixtures/pc21_runtime/prepare_fixture.py --case attention --output artifacts/paper1-ai/runtime-fixture-01
python -B -m sr2fpga_agent.execution preflight --config artifacts/paper1-ai/runtime-fixture-01/config.json
python -B -m sr2fpga_agent.execution run-development --config artifacts/paper1-ai/runtime-fixture-01/config.json --output artifacts/paper1-ai/runtime-replay-01 --terminal-suite-factory sr2fpga_agent.execution.development:terminal_suites
```

The last command runs real tools and can take several minutes, with per-tool
60-second limits. It makes zero natural-model requests. `--case all` prepares
three independent config files; repeat `--config` to execute a complete
three-family batch. Each output must be fresh. Fixture budget numbers are
test allocations, not a frozen scientific B4 configuration.

Only one fixed design per family is present, so these data cannot support
cluster-level statistical inference. They exercise the plumbing and external
tool behavior. For numeric analysis tests use the explicitly synthetic
datasets from `sr2fpga_agent.analysis.simulation`; its reports never grant
official claims or a real-population power guarantee.
