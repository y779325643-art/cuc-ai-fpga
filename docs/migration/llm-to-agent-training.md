# LLM To Agent And Training Migration

The repository now has two canonical implementation projects. `LLM/` remains
for one compatibility cycle and contains only thin wrappers.

## Path Mapping

| Old path | Canonical path |
| --- | --- |
| `LLM/src/sr2fpga_agent/` | `agent/src/sr2fpga_agent/` |
| `LLM/tests/test_sr2fpga_agent_*.py` | `agent/tests/` |
| `configs/current/` | `agent/configs/current/` |
| `configs/archive/` | `agent/configs/archive/` |
| `configs/legacy/` | `agent/configs/legacy/` |
| `LLM/src/prepare_dataset.py` | `training/src/sr2fpga_training/prepare_dataset.py` |
| `LLM/src/training_dry_run.py` | `training/src/sr2fpga_training/training_dry_run.py` |
| `LLM/src/train_lora.py` | `training/src/sr2fpga_training/train_lora.py` |
| `LLM/src/merge_lora.py` | `training/src/sr2fpga_training/merge_lora.py` |
| `LLM/scripts/*.sh` | `training/scripts/*.sh` |
| mixed `LLM/requirements.txt` | `agent/pyproject.toml` and `training/pyproject.toml` |

## Command Mapping

| Deprecated command | Canonical command |
| --- | --- |
| `python -m LLM.src.sr2fpga_agent.runner` | `python -m sr2fpga_agent.runner` |
| `python -m LLM.src.sr2fpga_agent.cli` | `python -m sr2fpga_agent.cli` |
| `python -m LLM.src.req2file_eval` | `python -m sr2fpga_agent.req2file_eval` |
| `python LLM/src/prepare_dataset.py` | `python -m sr2fpga_training.prepare_dataset` |
| `python LLM/src/training_dry_run.py` | `python -m sr2fpga_training.training_dry_run` |
| `python LLM/src/train_lora.py` | `python -m sr2fpga_training.train_lora` |
| `python LLM/src/merge_lora.py` | `python -m sr2fpga_training.merge_lora` |
| `bash LLM/scripts/train_lora.sh` | `bash training/scripts/train_lora.sh` |
| `bash LLM/scripts/serve_vllm.sh` | `bash training/scripts/serve_vllm.sh` |

All retained legacy commands print an exact `DEPRECATED` replacement and
delegate without copying implementation logic.

## Installation

Install only the project needed by the machine:

```powershell
python -m pip install -e "agent[dev]"
python -m pip install -e "training[dev]"
```

Training and serving dependencies are optional:

```powershell
python -m pip install -e "training[train]"
python -m pip install -e "training[serve]"
```

For one-cycle compatibility, `python -m pip install -r LLM/requirements.txt`
installs the lightweight editable Agent and Training projects. It does not
install heavy extras.

## Import Migration

```python
# Deprecated
from LLM.src.sr2fpga_agent.agent import DataGenerationAgent

# Canonical
from sr2fpga_agent.agent import DataGenerationAgent
```

Training code imports only `sr2fpga_training` and reads versioned files from
`contracts/` and `datasets/`. Training does not import Agent.

## Configuration Relocation

| Purpose | Canonical location |
| --- | --- |
| Maintained Agent runs | `agent/configs/current/` |
| Historical Agent evidence | `agent/configs/archive/` |
| Compatibility Agent examples | `agent/configs/legacy/` |
| Local Agent overrides | ignored `agent/configs/local/` |
| Training examples | `training/configs/` |
| Local Training overrides | ignored `training/configs/local/` |

Generated Agent and Training output belongs under `artifacts/`. Released data
under `datasets/` remains immutable.

## Compatibility Policy

- `LLM/` is compatibility-only and must not receive new business logic.
- Python wrappers preserve arguments and exit status.
- Shell wrappers preserve argument order and execute the canonical script.
- Legacy imports and commands are covered by `compatibility_tests/`.
- `not_run` is not a failure in either old or new reporting paths.

Compatibility removal requires a later active-usage review and explicit
approval. This migration makes no unapproved removal-date promise.
