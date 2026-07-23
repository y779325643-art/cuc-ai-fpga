# Training Scripts

These scripts operate the standalone `sr2fpga-training` project. They resolve
the repository root from their own location and use
`training/.venv` by default. Set `TRAINING_VENV_PATH` to use another
environment.

Serving scripts accept `MODEL_PATH` or `QWEN_MODEL_PATH` overrides. Values may
be public model identifiers or complete local snapshots.
