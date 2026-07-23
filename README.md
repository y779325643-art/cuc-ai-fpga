# SR2FPGA

SR2FPGA is a tool-verified research system for generating multi-file FPGA RTL
projects from system requirements. Its primary unit is a project trajectory,
not an isolated Verilog file:

```text
requirement
-> System-HIS
-> project skeleton and model-generated behavior
-> H0-H3 and L0-L4 verification
-> diagnosis and patch trajectory
-> released dataset and training views
```

## Repository Map

- `agent/`: project generation, System-HIS validation, testbench/oracle
  execution, L0-L4 tool orchestration, repair, and trajectory recording.
- `training/`: dataset preparation, SFT/LoRA training, adapter merge, and model
  serving assets. Training does not import Agent.
- `contracts/`: versioned System-HIS, trajectory, training-view, and task
  catalog contracts shared through files rather than runtime imports.
- `datasets/`: immutable, versioned dataset releases registered by
  `datasets/manifest.json`.
- `artifacts/`: ignored candidate runs, reports, prepared data, adapters, and
  other reproducible runtime output.
- `docs/`: current navigation, research specifications, evidence reports, and
  historical plans.
- `LLM/`: one-cycle compatibility wrappers only; it is not an implementation
  project.

See the [documentation index](docs/README.md), [current status](docs/current-status.md),
and [legacy migration guide](docs/migration/llm-to-agent-training.md).

## Verification Semantics

- `H0-H3`: System-HIS schema validity, well-formedness, lowerability, and
  requirement fidelity.
- `L0`: project-contract consistency.
- `L1`: Verilator lint.
- `L2`: black-box self-checking simulation with Icarus Verilog.
- `L3`: Yosys `synth_xilinx` synthesis and measured resource labels.
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

REQ2FILE is a derived training view. It retains its source episode and never
receives standalone project pass credit.

## Verification Commands

```powershell
python -m pytest contracts/tests agent/tests training/tests compatibility_tests -q
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
- Keep dated plans and reports as historical evidence; update current guidance
  in this README, `CLAUDE.md`, and `docs/current-status.md`.
