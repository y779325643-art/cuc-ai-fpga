# SR2FPGA

SR2FPGA is a tool-verified research system for generating multi-file FPGA RTL
projects from system requirements. Its evaluated unit is a coherent project;
the trajectory is its auditable execution record:

```text
requirement
-> shared disposition: ready / needs_clarification / capability_gap
-> direct / untyped-plan / System-HIS method condition
-> full project or project skeleton + generated behavior
-> condition-applicable H0-H3 and method-neutral L0-L4 verification
-> optional diagnosis / patch / rerun when repair-eligible
-> immutable terminal candidate + evaluator-owned hidden outcome (Paper-1 target)
-> reproducible episode, cost, missingness, and outcome summaries
```

Paper-1 v1.6 targets ACM Transactions on Reconfigurable Technology and Systems
（TRETS）and does not train models. It evaluates M0-M5 and audits requirement
ambiguity on a separate stop-before-generation population; those dispositions
never receive project/VPP credit. RQ4 is secondary representative OpenXC7
physical-depth characterization; target-profile adaptation is a separately
frozen optional extension and never implies general or cross-vendor portability.
The current development working tree has an excluded
fake-provider M0-M5 full-pack reconstruction and Runner-authoritative
development/excluded attempt evaluation, `@1`/`AT_A` terminal selection, exact-
terminal public reevaluation, an optional hash-bound evaluator-owned trusted
public L2 harness, and one-shot hidden dispatch. Development/excluded runs can
now publish a sanitized hidden conformance outcome and reduce a separate
development-only VPP without changing official VPP, which remains
`not_evaluated`. Without a configured trusted harness, public L2 remains
`not_run(needs_oracle)`. The checkout still lacks positive artifact-derived G3
authority, first-class semantic-instance/replicate paired-block closure,
independent execution-schedule control, mode-aware decoding provenance, shared-cost
and two-axis hidden-missingness reconciliation, official hidden/VPP authority,
and the signed G4b campaign verifier; see
[current status](docs/current-status.md).

## Where To Start

| If you need to know... | Read |
|---|---|
| What is verified right now, what is open debt, what gate is active | [`docs/current-status.md`](docs/current-status.md) |
| The research questions, method conditions, information boundaries, metrics, gates | [Paper-1 research-program freeze](docs/specs/2026-08-14-sr2fpga-paper1-research-program-freeze-design.md) |
| How the freeze maps to modules, interfaces, state machines, and work packages (CD1-CD10) | [Paper-1 code-architecture spec](docs/specs/2026-08-18-sr2fpga-paper1-code-architecture-development-spec.md) |
| How to run, own, or extend a specific project | that project's own README (`agent/`, `training/`, `contracts/`, `datasets/`) |
| Rules a coding/research agent must follow before making a change | [`AGENTS.md`](AGENTS.md) |
| Contracts, evidence, and documentation navigation overall | [`docs/README.md`](docs/README.md) |

## Repository Map

- `agent/`: project generation, System-HIS validation, testbench/oracle
  execution, L0-L4 tool orchestration, repair, and trajectory recording.
- `training/`: retained dataset preparation, SFT/LoRA, adapter merge, and model
  serving infrastructure outside Paper-1. Training does not import Agent.
- `contracts/`: versioned System-HIS, trajectory, training-view, and task
  catalog contracts shared through files rather than runtime imports.
- `datasets/`: immutable, versioned dataset releases registered by
  `datasets/manifest.json`.
- `artifacts/`: ignored candidate runs, reports, prepared data, adapters, and
  other reproducible runtime output.
- `app/`: local deterministic UI demo for exercising the current Agent runtime
  and inspecting recorded H0-H3/L0-L4 outcomes.
- `outputs/`: manually produced literature reviews, manuals, presentations, and
  other user-facing deliverables; generated previews and QA artifacts are
  ignored.
- `reports/`: curated, intentionally committed evidence and audit records.
- `docs/`: current navigation, research specifications, evidence
  interpretation, and active paper materials.
- `references/`: source papers, source-grounded readers, hardware manuals, and
  other background material; these do not define current protocol or results.

See the [documentation index](docs/README.md), [current status](docs/current-status.md),
[Paper-1 research freeze](docs/specs/2026-08-14-sr2fpga-paper1-research-program-freeze-design.md),
and [reference-material index](references/README.md).

## Verification Semantics

- `H0-H3`: condition-applicable System-HIS canonical-Schema validation,
  well-formedness, lowerability, and requirement fidelity. They are mechanism
  outcomes, not eligibility requirements for untyped baselines. Full W1-W10 H1
  closure remains an explicit contract gate.
- `L0`: project-contract consistency.
- `L1`: Verilator lint.
- `L2`: evaluator-trusted black-box self-checking simulation with Icarus
  Verilog. A candidate-owned testbench is public smoke/debug only and cannot
  award semantic L2 credit; without a trusted harness, L2 is `not_run`.
- `L3`: the current Yosys synthesis-acceptance flow and its named cell/resource
  statistics. The current scalable path must not be described as calibrated
  FPGA LUT QoR until its generic-versus-`synth_xilinx` semantics are aligned.
- `L4-open`: optional OpenXC7/nextpnr physical implementation.
- `L4-commercial`: optional Vivado reference implementation.
- `L5`: representative board validation; not yet a general dataset stage.

Every trajectory carries an explicit L4 status. `not_run` is not a failure; it
is reported separately with a skip reason. Missing tools and other
infrastructure outcomes are also separated from model failures.

## Install

Install the two projects independently from the repository root:

```powershell
python -m pip install -e "agent[dev]"
python -m pip install -e "training[dev]"
```

The development extras install pytest and Ruff. Run the repository's two
Python-project lint surfaces with:

```powershell
python -m ruff check agent/src agent/tests training/src training/tests
```

The Training development install is lightweight. Install GPU-dependent extras
only on a suitable machine:

```powershell
python -m pip install -e "training[train]"
python -m pip install -e "training[serve]"
```

## Agent Quick Start

Preview the deterministic T0-T4 smoke:

```powershell
python -m sr2fpga_agent.runner `
  --config agent/configs/current/sr2fpga_deterministic_curriculum_smoke.example.yaml `
  --run-id local-deterministic-smoke `
  --preflight
```

Run it:

```powershell
python -m sr2fpga_agent.runner `
  --config agent/configs/current/sr2fpga_deterministic_curriculum_smoke.example.yaml `
  --run-id local-deterministic-smoke
```

Outputs are written beneath `artifacts/agent/`. Released data under `datasets/`
is never modified by a normal Agent run.

## Training Quick Start

Prepare and validate the bundled smoke fixture without loading a model:

```powershell
python -m sr2fpga_training.prepare_dataset `
  --input training/tests/fixtures/smoke_verilog_raw.jsonl `
  --output artifacts/training/prepared-data/smoke/chat.jsonl

python -m sr2fpga_training.training_dry_run `
  --input artifacts/training/prepared-data/smoke/chat.jsonl `
  --max-seq-length 2048
```

REQ2FILE is a retained derived view. It retains its source episode and never
receives standalone project pass credit.

`train_lora` and `merge_lora` are legacy/manual model infrastructure outside
Paper-1. They must not be used for the TRETS Paper-1 campaign; see
[Training](training/README.md).

## Verification Commands

```powershell
python -m pytest contracts/tests agent/tests training/tests compatibility_tests -q -p no:cacheprovider
python -m pytest agent/tests -q
python -m pytest training/tests -q
```

For detailed commands and ownership rules, read
[Agent](agent/README.md), [Training](training/README.md),
[Contracts](contracts/README.md), and [Datasets](datasets/README.md).

## Data And Secret Policy

- Generate candidates under `artifacts/`; promote a release into `datasets/`
  only through an explicit, versioned release operation.
- Do not commit API keys, private provider endpoints, local absolute paths,
  model weights, adapters, raw vendor artifacts, or `.env`.
- Do not let generated DUT code modify trusted hidden tests, golden models,
  protocol checkers, or board constraints.
- Keep stable reports as evidence; use Git history for completed plans and
  superseded designs. Update current guidance in this README, `AGENTS.md`, and
  `docs/current-status.md`.
