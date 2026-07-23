# Training Configuration

Committed `*.example.yaml` and `*.env.example` files are reproducible examples.
They use public model identifiers and write only beneath ignored
`artifacts/training/`.

Machine-local model paths, provider endpoints, and other overrides belong in
ignored `training/configs/local/` files or environment variables. Do not commit
API keys or private absolute paths.
