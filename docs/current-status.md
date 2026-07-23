# SR2FPGA Current Status - 2026-07-23

## Current Work

Repository reorganization is active on branch
`codex/reorganization-phase-b1`. The target is one repository with two
independent Python projects and shared file contracts:

- `agent/`: generation, verification, repair, and trajectory production.
- `training/`: dataset preparation, training, merge, and serving. Training does
  not import Agent.
- `contracts/`: shared versioned contracts.
- `datasets/`: immutable releases.
- `artifacts/`: ignored runtime output.

The old `LLM/` directory is now a one-cycle compatibility surface, not an
implementation owner. See the
[migration guide](migration/llm-to-agent-training.md).

## Reorganization Progress

| Phase | State | Evidence |
| --- | --- | --- |
| B1 contracts and artifact boundaries | Complete | Contract registry, canonical task catalog, dataset manifests and policy tests |
| B2 standalone Agent project | Complete | Agent source/config/scripts/tests moved; deterministic 24-sample smoke reached L3 |
| B3 standalone Training project | Complete | Lightweight package, provenance enforcement, serving/training assets moved |
| B4 compatibility and cleanup | In progress | Stable evidence promotion is complete; tracked `tmp/` deletion still requires explicit approval |

The last complete B3 regression was `989 passed, 349 subtests passed`. B4
focused compatibility suites are run after each migration slice; a new full
regression is required before final approval.

## Current Technical Capability

- Canonical System-HIS v1.2 with H0 schema, H1 well-formedness, H2
  lowerability, and H3 requirement-fidelity records.
- Deterministic and LLM-backed multi-file project generation.
- Trusted black-box testbenches, protocol/numeric/image/RL oracles, mutation
  qualification, and patch-as-PR controls.
- L0 project-contract checking, L1 lint, L2 simulation, L3 synthesis.
- Optional OpenXC7 L4 and Vivado reference paths. Current artifact-backed
  evidence proves OpenXC7 L4 for two representative families; Vivado was not
  available in the current environment and is recorded as `not_run`.
- Versioned trajectory and training-view contracts.
- Independent Training conversion and dry-run validation without loading
  PyTorch or Transformers.

L5 board validation is not yet a general dataset stage.

## Task Contract And Evidence

The v0.2 task catalog is the intended target contract and target policy. The
v0.1 evidence ledger records executable and verified facts; the generated
status document is its human-readable view.

| Evidence measure | Current verified count |
| --- | --- |
| Evidence ledger coverage | 71/71 |
| Implemented families | 31 |
| Paper 1 core implemented | 14/14 (denominator: v0.2 catalog `recommended_sets.paper1_core`) |
| Paper 1 core executable / L3 | 14/14 |
| Paper 1 core mutation-qualified | 14/14 |
| Mutation-qualified families | 21 |
| Independent Python oracle qualified | 9 |
| OpenXC7 L4 families | 2 |
| Vivado commercial-reference L4 families | 0 (`not_run`: 2) |
| L5 families | 0 |

## Verdict Rules

- `not_run` is not a failure; it is reported separately with a skip reason.
- Toolchain and provider infrastructure failures are not model failures.
- REQ2FILE is derived training data and has no standalone evaluation credit.
- A candidate cannot receive automatic pass credit after modifying its trusted
  oracle.
- L4-open and L4-commercial labels remain separate.

## Current Commands

Install:

```powershell
python -m pip install -e "agent[dev]"
python -m pip install -e "training[dev]"
```

Full test surface:

```powershell
python -m pytest contracts/tests agent/tests training/tests compatibility_tests -q
```

Deterministic Agent preflight:

```powershell
python -m sr2fpga_agent.runner `
  --config agent/configs/current/sr2fpga_deterministic_curriculum_smoke.example.yaml `
  --run-id reorganization-final-smoke `
  --preflight
```

Lightweight Training smoke:

```powershell
python -m sr2fpga_training.prepare_dataset `
  --input training/tests/fixtures/smoke_verilog_raw.jsonl `
  --output artifacts/training/prepared-data/reorganization-smoke/chat.jsonl

python -m sr2fpga_training.training_dry_run `
  --input artifacts/training/prepared-data/reorganization-smoke/chat.jsonl `
  --max-seq-length 2048
```

## Remaining B4 Gates

1. Present the 590-path tracked-`tmp/` inventory totals and obtain explicit
   approval before moving or
   deleting any tracked `tmp/` evidence.
2. Run compatibility, full regression, deterministic Agent, and lightweight
   Training acceptance checks.
3. Produce the final reorganization audit and publication-ready branch.

No tracked `tmp/` evidence may be removed before the external-backup and
explicit-approval gate.

Completed B4 evidence gates:

- The Phase A external backup was rechecked successfully.
- 69 active legacy references (87 ledger occurrences) were replaced with
  sanitized stable evidence under `reports/evidence/legacy-runs/`.
- Hidden oracle `.memh` vectors and binary simulator/P&R products were not
  promoted.
- The local task-evidence artifact audit passes with no issues.
