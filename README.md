# SR2FPGA

中文上手与源码说明：[完整代码手册](docs/code-guide/README.md)覆盖当前入口、
PC 2.1、M0–M5、LLM 算子、流程图和[方法实现深度审查](docs/code-guide/09-deep-review.md)。
实际执行范围见[本次验证记录](docs/code-guide/10-validation.md)。

> [Terminology, 2026-09-08](docs/specs/2026-09-08-sr2fpga-terminology.md): Project Contract (PC),
> now serialized as [`sr2fpga-pc-2.1`](docs/specs/PC-2.1-AI-stream-contract-design.zh.md);
> FPGA Project Package (FPP). DSC names the design-space contract; DP names one
> design point. Internal identifiers and historical evidence names remain
> unchanged — System-HIS v1.2 stays the format of record for existing artifacts.

SR2FPGA is a research repository for generating coherent multi-file FPGA
Project Packages from system requirements and evaluating them with tool- and
artifact-backed evidence.

```text
requirement
-> ready / needs_clarification / capability_gap disposition
-> direct / untyped-plan / Project Contract method condition
-> FPGA Project Package (FPP), emitted directly or from skeleton + generated behavior
-> condition-applicable H0-H3 and method-neutral L0-L4 validation
-> optional diagnosis / patch / rerun
-> immutable terminal candidate and evaluator-owned outcome
-> reproducible episode, cost, missingness, and outcome records
```

## Paper-1 Worktree

[WORKTREE.md](WORKTREE.md) identifies the active local `develop` checkout.
[Paper-1 / PC 2.1](docs/routes/paper1-ai.md) is the FPGA project-generation
route. The [route index](docs/routes/README.md) also links to historical records
of the independent generated-testbench reliability study.

## Current Research Plan

The [current PC2.1 execution runtime](agent/src/sr2fpga_agent/execution/README.md)
connects M0–M5 generation/repair, persistent budgets and terminal boundaries;
the [analysis package](agent/src/sr2fpga_agent/analysis/README.md) provides offline
design-cluster inference. Development validation used explicit replay fixtures
and real tools, with zero natural-model calls and no official experiment.

The current population is governed by the adopted 2026-10-28
[`paper1-v2.3` LLM case amendment](docs/specs/2026-10-28-sr2fpga-paper1-llm-case-amendment-v2.3.zh.md).
Its three families are `llm_quantized_qkv_projection`,
`llm_kv_cache_decode_attention` and `llm_gated_ffn`. Fixed development controls
now include public synthetic assets, independent integer oracles, explicit
reference RTL and transaction harnesses. They do not constitute a qualified
family population, checkpoint-quality benchmark or official result.

```powershell
python -B -m sr2fpga_agent.tasks.llm prepare --case all --output artifacts/paper1-ai/<fresh-public-run>
python -B -m sr2fpga_agent.tasks.llm check-reference --case all --output artifacts/paper1-ai/<fresh-reference-run>
```

`prepare` performs no model or tool call. `check-reference` constructs the
hand-authored controls through PC 2.1 and runs real compilation, simulation and
independent trace checks; add `--synthesize` explicitly for bounded generic
synthesis. See the [LLM case guide](agent/src/sr2fpga_agent/tasks/README.md).

M0–M5, PC 2.1, comparisons, budget and evidence rules are inherited from v2.2.
The following v2.2 description records the preceding CNN/residual/GEMM baseline;
its population and case-status paragraphs are superseded by the amendment.

### Retained v2.2 baseline

[`paper1-v2.2`](docs/specs/2026-09-15-sr2fpga-paper1-research-plan-v2.2.zh.md)
(Chinese, adopted 2026-09-15) targets ACM TRETS and does not train models.

| | |
| --- | --- |
| Task population | Three quantized-AI accelerator subsystems: `ai_dw_pw_block`, `ai_quantized_residual_block`, `ai_tiled_gemm_pipeline` |
| Project Contract | [`sr2fpga-pc-2.1`](docs/specs/PC-2.1-AI-stream-contract-design.zh.md) — tensor, quantization, sequence and bounded-relation semantics. No reader for older formats |
| Primary comparisons | `M5-M1@B4` (system value at equal total budget) and `M4-M3@initial` (deterministic materialization on a shared generated PC), in **one** Holm family |
| Budget fairness | **B4** — matched total logical model calls, not matched repair counts, plus matched token/tool/time axes |
| Independent unit | `design_cluster_id`; configurations and replicates nest inside it |
| Sequencing | Seven acceptable work packages `WP0`-`WP6` |
| Optional, disabled by default | Requirement-ambiguity audit (A_req), EA search, model training, Q-table, board bring-up |
| Planned secondary | Native coding-agent comparison (C0/C1), second model, tensor-check ablation, natural-failure repair probe |

Adoption fixed the research direction and **authorized repository migration**.
**Official-experiment authorization was not granted** and the plan is not
frozen. Adoption itself did not authorize model/pilot/hidden/physical campaigns.
The separately authorized 2026-10-26 fixed DW→PW development diagnostic has
completed with 3 candidate subagent invocations, independent simulation and
generic synthesis. The [development check history](docs/current-status.md#latest-migration-verification)
records the scope and limitations.

Migration to this plan is **in progress** — see the
[migration record](docs/migrations/research-plan-alignment.md) before starting
work. The three AI identities remain unqualified in the catalog; a fixed DW→PW
development task now has an independent integer reference and executable
control, while residual/GEMM remain unimplemented.
PC 2.1 has strict JSON/schema and original-byte binding validation plus the
first semantic hierarchy checks (the entry and every instantiated module must
exist, the module graph must not recurse, and every definition must be reachable
from the entry). The entry signature is requirement-owned and internal module
signatures are declared by the design, and supplied instance parameter names
must exactly match their target declarations, with no missing bindings. The typed
`validate/build/compose` development commands additionally check parameters,
domains, wiring, types and tensor declarations, emit deterministic structure and
compose behavior with real parser checks. Fixed-task development success does
not establish benchmark-wide qualification or official results. Superseded plans are retained under
[`docs/specs/superseded/`](docs/specs/superseded/). Current implementation,
evidence, and open debt are summarized in
[current status](docs/current-status.md); this README is an entry point, not
protocol or outcome authority.

## Where To Start

| If you need to know... | Read |
| --- | --- |
| What this checkout implements, verifies, or still lacks | [`docs/current-status.md`](docs/current-status.md) |
| Research questions, methods, information boundaries, metrics, budgets, and work packages | [LLM case amendment v2.3](docs/specs/2026-10-28-sr2fpga-paper1-llm-case-amendment-v2.3.zh.md) and its [v2.2 base plan](docs/specs/2026-09-15-sr2fpga-paper1-research-plan-v2.2.zh.md) |
| Implementation architecture, interfaces, artifacts, and WP0-WP6 work packages | [Paper-1 code-architecture spec v2.1](docs/specs/2026-09-15-sr2fpga-paper1-code-architecture-development-spec-v2.1.zh.md) — target architecture, not current state |
| The Project Contract format and its bounded static semantics | [PC 2.1 design](docs/specs/PC-2.1-AI-stream-contract-design.zh.md) and the [registered schemas](contracts/pc/2.1/) |
| How far the repository has moved toward the current plan | [Migration record](docs/migrations/research-plan-alignment.md) |
| Canonical machine-readable task families, IDs, and target intent | [Task catalog](contracts/task-catalog/sr2fpga-task-catalog-v0.2.json) — data revision 0.4.0; three LLM families in `paper1_core`, previous AI selection in `legacy_quantized_ai_core_v2_2`; development implementation is partial and formal qualification is not ready |
| Research and writing support behind earlier plan versions | [Paper-1 workspace](docs/research-program/paper1-v1/README.md) — written against v1.7/v1.8 |
| How to work safely in this repository | [`AGENTS.md`](AGENTS.md) |
| Contracts, evidence, literature, and documentation navigation | [`docs/README.md`](docs/README.md) |
| Project-specific setup and commands | [Agent](agent/README.md), [Training](training/README.md), [Contracts](contracts/README.md), or [Datasets](datasets/README.md) |

## Repository Map

- [`agent/`](agent/README.md): project generation, Project Contract validation,
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
- [`reports/`](reports/README.md): curated, intentionally committed evidence and named-run audits.
- [`docs/`](docs/README.md): current navigation, research specifications,
  evidence interpretation, and active paper materials.
- [`references/`](references/README.md): source papers, source-grounded readers,
  and hardware manuals; these do not define current protocol or results.
- `compatibility_tests/`: cross-project checks that documentation, terminology,
  and shared file contracts stay consistent; they test agreements between
  projects, not hardware behaviour.
- [`outputs/`](outputs/): manually produced user-facing reference material; dated artifacts
  there are not current protocol, implementation-status, or outcome authority.

Projects exchange versioned files through `contracts/` and `datasets/`, not
runtime Python imports across project boundaries.

## Minimal Setup And Validation

Install the lightweight development packages from the repository root:

```powershell
python -m pip install -e "agent[dev]"
python -m pip install -e "training[dev]"
```

Inspect the current PC 2.1 input development entry point:

```powershell
python -m sr2fpga_agent.pc --help
python -m pytest agent/tests/test_sr2fpga_pc21_inputs.py agent/tests/test_sr2fpga_pc21_cli.py -q -p no:cacheprovider
```

The `assemble` and `check` subcommands assemble and recheck schema-valid,
byte-bound PC inputs. The typed `validate`, `build`, and `compose` subcommands
also provide semantic checking, deterministic RTL structure and behavior
composition. Independent functional validation remains separate. See the
[PC command guide](agent/src/sr2fpga_agent/pc/README.md).

Preview the retained **legacy development** deterministic smoke:

```powershell
python -m sr2fpga_agent.runner `
  --config agent/configs/current/sr2fpga_deterministic_curriculum_smoke.example.yaml `
  --run-id local-deterministic-smoke `
  --preflight
```

Remove `--preflight` to execute the deterministic smoke. Generated runs are
written beneath `artifacts/agent/`.

The full repository regression command is below. It includes RTL/tool tests
and can take substantially longer than the focused input checks:

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
  `docs/current-status.md`, and research semantics in the current research plan.
  Version labels inside historical QA reports, audits, and writing aids record
  the state at the time of writing and are deliberately not rewritten.
