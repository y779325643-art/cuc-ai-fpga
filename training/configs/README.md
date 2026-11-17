# Training Configuration

These configure the standalone Training project, which
[`paper1-v2.2`](../../docs/specs/2026-09-15-sr2fpga-paper1-research-plan-v2.2.zh.md)
section 1.3 places outside the Paper-1 minimum scope. No configuration here may
be used by a Paper-1 work package, campaign, or claim.

Committed `*.example.yaml` and `*.env.example` files are reproducible examples.
They use public model identifiers and write only beneath ignored
`artifacts/training/`.

Machine-local model paths, provider endpoints, and other overrides belong in
ignored `training/configs/local/` files or environment variables. Do not commit
API keys or private absolute paths.
