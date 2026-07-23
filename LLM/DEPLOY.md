# Deprecated Deployment Guide

`LLM/` no longer owns model training or serving. Use the standalone Training
project:

- [Training overview](../training/README.md)
- [Training scripts](../training/scripts/README.md)
- [Training configuration](../training/configs/README.md)
- [Migration guide](../docs/migration/llm-to-agent-training.md)

Canonical setup:

```powershell
python -m pip install -e "training[dev]"
python -m pip install -e "training[train]"
python -m pip install -e "training[serve]"
```

Run the canonical scripts from `training/scripts/`. Machine-local model paths,
virtual environments, provider endpoints, and caches must be supplied through
environment variables or ignored local configuration.

This file is retained for one compatibility cycle. Historical machine-specific
deployment instructions remain available in Git history and are not current
repository guidance.
