# Training Scripts

These scripts operate the standalone `sr2fpga-training` project, which is
outside the Paper-1 minimum scope under
[`paper1-v2.2`](../../docs/specs/2026-09-15-sr2fpga-paper1-research-plan-v2.2.zh.md)
section 1.3. Running any of them produces no Paper-1 evidence. They resolve
the repository root from their own location and use
`training/.venv` by default. Set `TRAINING_VENV_PATH` to use another
environment.

Serving scripts accept `MODEL_PATH` or `QWEN_MODEL_PATH` overrides. Values may
be public model identifiers or complete local snapshots.
