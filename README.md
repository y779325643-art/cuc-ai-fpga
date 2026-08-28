# SR2FPGA

SR2FPGA is a research repository for generating coherent multi-file FPGA
projects from system requirements and evaluating them with tool- and
artifact-backed evidence.

```text
requirement
-> ready / needs_clarification / capability_gap disposition
-> direct / untyped-plan / System-HIS method condition
-> full project or skeleton + generated behavior
-> condition-applicable H0-H3 and method-neutral L0-L4 validation
-> optional diagnosis / patch / rerun
-> immutable terminal candidate and evaluator-owned outcome
-> reproducible episode, cost, missingness, and outcome records
```

The active
[`paper1-freeze-v1.7`](docs/specs/2026-08-14-sr2fpga-paper1-research-program-freeze-design.md)
protocol targets ACM TRETS, evaluates M0-M5, and does not train models.
Current implementation, evidence, open debt, regression counts, and active gate
are summarized in [current status](docs/current-status.md); this README is an
entry point, not protocol or outcome authority.

## Where To Start

| If you need to know... | Read |
| --- | --- |
| What this checkout implements, verifies, or still lacks | [`docs/current-status.md`](docs/current-status.md) |
| Research questions, methods, information boundaries, metrics, and gates | [Paper-1 freeze v1.7](docs/specs/2026-08-14-sr2fpga-paper1-research-program-freeze-design.md) |
| Implementation architecture, interfaces, artifacts, and CD1-CD10 work packages | [Paper-1 code-architecture spec v1.11](docs/specs/2026-08-18-sr2fpga-paper1-code-architecture-development-spec.md) |
| Canonical machine-readable task families, IDs, and target intent | [Task catalog v0.2](contracts/task-catalog/sr2fpga-task-catalog-v0.2.json) |
| Research and writing support behind the canonical freeze | [Paper-1 workspace](docs/research-program/paper1-v1/README.md) |
| How to work safely in this repository | [`AGENTS.md`](AGENTS.md) |
| Contracts, evidence, literature, and documentation navigation | [`docs/README.md`](docs/README.md) |
| Project-specific setup and commands | [Agent](agent/README.md), [Training](training/README.md), [Contracts](contracts/README.md), or [Datasets](datasets/README.md) |

## Repository Map

- [`agent/`](agent/README.md): project generation, System-HIS validation,
  L0-L4 orchestration, trusted evaluation, repair, and trajectory recording.
- [`training/`](training/README.md): retained dataset preparation, SFT/LoRA,
  merge, and serving infrastructure outside Paper-1. Training does not import
  Agent.
- [`contracts/`](contracts/README.md): versioned schemas, registries, and the
  canonical task catalog shared through files rather than runtime imports.
- [`datasets/`](datasets/README.md): immutable versioned releases registered by
  `datasets/manifest.json`.
- `artifacts/`: ignored runtime output for candidates, reports, prepared data,
  adapters, and other reproducible local products.
- [`app/`](app/README.md): local deterministic UI demo; it is not research
  evidence or an official evaluation surface.
- `reports/`: curated, intentionally committed evidence and named-run audits.
- [`docs/`](docs/README.md): current navigation, research specifications,
  evidence interpretation, and active paper materials.
- [`references/`](references/README.md): source papers, source-grounded readers,
  and hardware manuals; these do not define current protocol or results.
- `outputs/`: manually produced user-facing reference material; dated artifacts
  there are not current protocol, implementation-status, or outcome authority.

Projects exchange versioned files through `contracts/` and `datasets/`, not
runtime Python imports across project boundaries.

## Minimal Setup And Validation

Install the lightweight development packages from the repository root:

```powershell
python -m pip install -e "agent[dev]"
python -m pip install -e "training[dev]"
```

Preview the deterministic Agent smoke without creating a run:

```powershell
python -m sr2fpga_agent.runner `
  --config agent/configs/current/sr2fpga_deterministic_curriculum_smoke.example.yaml `
  --run-id local-deterministic-smoke `
  --preflight
```

Remove `--preflight` to execute the deterministic smoke. Generated runs are
written beneath `artifacts/agent/`.

Run the full lightweight repository test surface:

```powershell
python -m pytest contracts/tests agent/tests training/tests compatibility_tests -q -p no:cacheprovider
```

Use the owning project README for focused tests, lint, real-provider setup,
Training dry runs, and optional toolchain instructions. Do not install GPU-heavy
Training extras merely to validate repository documentation or lightweight code.

## Working In The Repository

- Follow [`AGENTS.md`](AGENTS.md) for task routing, minimal-change discipline,
  Git authorization, trusted/evaluator boundaries, and validation expectations.
- Generate normal runtime output under `artifacts/`. Promoting content into
  `datasets/` or `reports/evidence/` is a separate controlled operation.
- Do not infer implementation or empirical verification from a contract,
  catalog row, specification, local smoke, or UI display alone.
- Do not commit credentials, private endpoints, local absolute paths, model
  weights, raw vendor artifacts, or hidden evaluator content.
- Keep stable overview material here, mutable checkout facts in
  `docs/current-status.md`, research semantics in the active freeze, and
  superseded plans in Git history.
