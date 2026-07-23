# CLAUDE.md

This file is the current coding-agent guide for SR2FPGA. Read
[`docs/current-status.md`](docs/current-status.md) and the active reorganization
design and plans before substantial work:

- [`docs/superpowers/specs/2026-07-17-sr2fpga-repository-reorganization-design.md`](docs/superpowers/specs/2026-07-17-sr2fpga-repository-reorganization-design.md)
- [`docs/superpowers/plans/2026-07-17-sr2fpga-repository-reorganization-roadmap.md`](docs/superpowers/plans/2026-07-17-sr2fpga-repository-reorganization-roadmap.md)
- [`docs/superpowers/plans/2026-07-17-sr2fpga-reorganization-phase-b4-compatibility-cutover-cleanup.md`](docs/superpowers/plans/2026-07-17-sr2fpga-reorganization-phase-b4-compatibility-cutover-cleanup.md)

## Project Boundaries

- `agent/` owns generation, H0-H3 validation, L0-L4 verification, oracles,
  repair, and trajectory recording.
- `training/` owns dataset conversion, SFT/LoRA, merge, and serving. Training
  does not import Agent.
- `contracts/` owns versioned, language-neutral cross-project contracts and the
  canonical task catalog.
- `datasets/` contains immutable releases; normal code must not rewrite them.
- `artifacts/` contains ignored runtime output for Agent and Training.
- `LLM/` is compatibility-only. Never add business logic there.

The projects communicate through versioned files under `contracts/` and
`datasets/`, not Python imports across project boundaries.

## Research Invariants

The evaluated unit is a multi-file FPGA project:

```text
requirement
-> System-HIS
-> deterministic contract skeleton
-> model-generated behavior
-> H0-H3
-> L0-L4
-> diagnosis and patch trajectory
```

- Do not reduce official evaluation to a single Verilog file.
- REQ2FILE is a derived training view and receives no standalone pass credit.
- Trusted testbenches, hidden tests, golden models, checkers, board shells, and
  board constraints are not model-editable.
- `not_run` is not a failure. Report it separately with a skip reason.
- Missing tools and provider/toolchain infrastructure failures are not model
  failures.
- L4-open and L4-commercial are separate labels.

## Canonical Commands

Install:

```powershell
python -m pip install -e "agent[dev]"
python -m pip install -e "training[dev]"
```

Run tests:

```powershell
python -m pytest contracts/tests agent/tests training/tests compatibility_tests -q
```

Run deterministic Agent preflight:

```powershell
python -m sr2fpga_agent.runner `
  --config agent/configs/current/sr2fpga_deterministic_curriculum_smoke.example.yaml `
  --run-id local-deterministic-smoke `
  --preflight
```

Run lightweight Training validation:

```powershell
python -m sr2fpga_training.prepare_dataset `
  --input training/tests/fixtures/smoke_verilog_raw.jsonl `
  --output artifacts/training/prepared-data/smoke/chat.jsonl

python -m sr2fpga_training.training_dry_run `
  --input artifacts/training/prepared-data/smoke/chat.jsonl `
  --max-seq-length 2048
```

Heavy extras are opt-in:

```powershell
python -m pip install -e "training[train]"
python -m pip install -e "training[serve]"
```

## Change Discipline

- Make scoped changes with tests that prove the requested behavior.
- Preserve backward-compatible contract readers unless a versioned migration is
  explicitly approved.
- Do not weaken an oracle to make generated RTL pass.
- Do not stage generated `artifacts/`, caches, credentials, model outputs, or
  unrelated dataset changes.
- Do not rewrite dated plans/specs to hide historical paths.
- Any deletion or relocation of tracked `tmp/` evidence requires the Phase A
  external backup check, reviewed inventory totals, and explicit approval.

Legacy command and import mappings are documented in
[`docs/migration/llm-to-agent-training.md`](docs/migration/llm-to-agent-training.md).
