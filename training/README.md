# SR2FPGA Training

This project owns dataset preparation, SFT and LoRA training, adapter merging,
and serving smoke assets.

It consumes released datasets and versioned contracts. It does not import the
Agent implementation.

## Installation

Install the lightweight data-preparation and test surface from the repository
root:

```powershell
python -m pip install -e "training[dev]"
```

This path installs PyYAML and pytest only. Install heavy backends explicitly
when a training or serving machine needs them:

```powershell
python -m pip install -e "training[train]"
python -m pip install -e "training[serve]"
```

The `train` extra contains Accelerate, bitsandbytes, Datasets, PEFT, PyTorch,
Transformers, and TRL. The `serve` extra contains vLLM.

## Commands

Canonical module entry points:

```text
python -m sr2fpga_training.prepare_dataset
python -m sr2fpga_training.training_dry_run
python -m sr2fpga_training.train_lora
python -m sr2fpga_training.merge_lora
```

Editable installation also provides:

```text
sr2fpga-prepare-dataset
sr2fpga-training-dry-run
sr2fpga-train-lora
sr2fpga-merge-lora
```

Example lightweight conversion and validation:

```powershell
python -m sr2fpga_training.prepare_dataset `
  --input training/tests/fixtures/smoke_verilog_raw.jsonl `
  --output artifacts/training/prepared-data/smoke/chat.jsonl

python -m sr2fpga_training.training_dry_run `
  --input artifacts/training/prepared-data/smoke/chat.jsonl `
  --max-seq-length 2048
```

These commands do not load a model or initialize CUDA.

## Data And Contracts

Released dataset locations are registered in `datasets/manifest.json`.
Training reads release exports as immutable inputs; it does not generate or
modify releases. Prepared chat JSONL belongs under ignored
`artifacts/training/prepared-data/`.

Training-view rules are read from `contracts/manifest.json`. A canonical
`requirement_to_file` row must:

- name its `source_episode_id`;
- set `official_eval_unit` to `false`;
- set `standalone_pass_credit` to `false`.

REQ2FILE is a derived training view. It never receives standalone project pass
credit. Historical rows without `view_type` remain supported for existing
release conversion.

## Configuration And Output

- Committed examples live in `training/configs/*.example.yaml`.
- Machine-local overrides live in ignored `training/configs/local/`.
- Prepared data goes to `artifacts/training/prepared-data/`.
- Adapters go to `artifacts/training/adapters/`.
- Merged models go to `artifacts/training/merged/`.

Public model identifiers are used in committed examples. Local model paths,
API keys, provider endpoints, and credentials must be supplied through local
configuration or environment variables and must not be committed.

## Project Boundary

`sr2fpga_training` may read versioned files under `contracts/` and
`datasets/`, but it must not import `sr2fpga_agent` or the legacy `LLM`
namespace. Agent generation and verification remain owned by `agent/`.

## Tests

```powershell
python -m pytest training/tests -q
python -m pytest contracts/tests agent/tests training/tests -q
```
