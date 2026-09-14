# SR2FPGA Training

This project owns dataset preparation, SFT and LoRA training, adapter merging,
and serving smoke assets.

It consumes released datasets and versioned contracts. It does not import the
Agent implementation.

Under the active
[`paper1-freeze-v1.7`](../docs/specs/2026-08-14-sr2fpga-paper1-research-program-design.md),
this entire project is retained repository infrastructure outside the research
scope. Paper-1 targets ACM TRETS and does not train models.

## Installation

Install the lightweight data-preparation and test surface from the repository
root:

```powershell
python -m pip install -e "training[dev]"
```

This path installs the lightweight runtime dependencies, pytest, and Ruff.
Check the Training package and tests with:

```powershell
python -m ruff check training/src training/tests
```

Install heavy backends explicitly when a training or serving machine needs
them:

```powershell
python -m pip install -e "training[train]"
python -m pip install -e "training[serve]"
```

The `train` extra contains Accelerate, bitsandbytes, Datasets, PEFT, PyTorch,
Transformers, and TRL. The `serve` extra contains vLLM.

## Development Utilities

Available module entry points:

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

`prepare_dataset` and `training_dry_run` are lightweight validation tools and
do not load a model or initialize CUDA. `train_lora` and `merge_lora` are
legacy/manual model infrastructure outside Paper-1 — read
[Paper-1 Scope: No Training](#paper-1-scope-no-training) below before using either one.

Example lightweight conversion and validation:

```powershell
python -m sr2fpga_training.prepare_dataset `
  --input training/tests/fixtures/smoke_verilog_raw.jsonl `
  --output artifacts/training/prepared-data/smoke/chat.jsonl

python -m sr2fpga_training.training_dry_run `
  --input artifacts/training/prepared-data/smoke/chat.jsonl `
  --max-seq-length 2048
```

## Paper-1 Scope: No Training

RQ3 and M6U/M6F/M6T/M6TR are withdrawn from Paper-1. No Paper-1 gate, campaign,
or claim may invoke `train_lora`, `merge_lora`, a training release, or a learned
checkpoint.

The current `train_lora` accepts an arbitrary
YAML configuration and `train_file`, does not consume a promoted release or
signed `training-plan-v1`, and does not require the frozen seed set, development
artifact, checkpoint metric, or run/checkpoint provenance. It also loads both
the tokenizer and model with `trust_remote_code=True`; `merge_lora` has the same
remote-code default. **Neither command may be used for Paper-1** — even as a
small exploratory pilot. The current dry-run uses a
lightweight token estimate and only fails on truncation when explicitly
requested.

CD8 contracts and structural inspectors remain compatibility surfaces for
possible future work under a separate research protocol. Their incomplete
authorization chain is not a Paper-1 blocker or deliverable.

Training also has a read-only promoted-release inspector. It rejects
`candidate_unpromoted`, requires `training_authorized=true`, and compares the
manifest authorization against caller-supplied expected campaign-freeze,
training-plan and promotion-record hashes. It independently revalidates file
inventory/checksums, pool sets and mixture, every row/sidecar/eligibility
certificate binding, initial-versus-terminal snapshot selection, and the
expected leakage/canary policy without importing Agent. Inspection returns
immutable paths to the four treatment views; it does not authenticate a
signature, verify the referenced authority artifacts, promote a release,
prepare data, or start training. It is not currently invoked by `train_lora`.

## Data And Contracts

Released dataset locations are registered in `datasets/manifest.json`. The
formal Training path must read promoted release exports as immutable inputs and
must not generate or modify releases. The current legacy converter and manual
training utilities still accept caller-supplied file paths, so they do not yet
constitute that formal path. Prepared chat JSONL belongs under ignored
`artifacts/training/prepared-data/`.

Training-view rules are read from `contracts/manifest.json`.
`training-view-row-v1` is retained only under the
`training_view_row_legacy` registry key for historical conversion. Formal
candidate releases use the closed `training-view-row-v2` contract registered as
`training_view_row`; each row binds `row_id`, `source_episode_id`, `snapshot_id`,
and treatment to a canonical `row_sha256`, while the renderer consumes only its
model-visible `payload`.

The v2 reader rejects the whole JSONL file on a Schema/hash/duplicate-row error,
accepts only `M6U`, `M6F`, `M6T`, or `M6F_E_TRAJ`, restricts assistant project
targets to model RTL/region/delta roles, and rejects audit/hidden canaries. M6U
additionally rejects verdict/status, diagnosis, patch, tool feedback,
terminal-selection, eligibility, and `verified*` fields. The legacy
`requirement_to_file` row must still:

- name its `source_episode_id`;
- set `official_eval_unit` to `false`;
- set `standalone_pass_credit` to `false`.

REQ2FILE is a derived training view. It never receives standalone project pass
credit. Historical rows without `view_type` remain supported for existing
conversion only. No candidate release or dataset promotion is implied by
successful legacy conversion.

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
python -m pytest training/tests -q -p no:cacheprovider
python -m pytest contracts/tests agent/tests training/tests -q -p no:cacheprovider
```
