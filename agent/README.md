# SR2FPGA Agent

中文阅读入口：[仓库代码手册](../docs/code-guide/README.md)、
[上手流程](../docs/code-guide/01-quickstart.md)和
[方法实现审查](../docs/code-guide/09-deep-review.md)。

Current case authority is the adopted
[`paper1-v2.3` LLM amendment](../docs/specs/2026-10-28-sr2fpga-paper1-llm-case-amendment-v2.3.zh.md),
with the v2.2 base plan retaining method, budget, metric and isolation rules.
The current families are QKV projection, KV-cache decode attention and gated
FFN. Their executable fixed development controls and commands are documented
in the [LLM task guide](src/sr2fpga_agent/tasks/README.md). Older case/status
paragraphs below describe the retained v2.2 development baseline.

The current [PC 2.1 six-method runtime](src/sr2fpga_agent/execution/README.md)
connects generation/repair, persistent budgets, terminal isolation and the
[offline cluster analysis package](src/sr2fpga_agent/analysis/README.md).
Inspect `python -m sr2fpga_agent.execution --help` and
`python -m sr2fpga_agent.analysis --help`. Validation used explicit replay
fixtures; no natural-model request or official experiment was executed.

`agent/` owns multi-file **FPGA Project Package (FPP)** generation, checking, repair, evaluation orchestration, and execution records. Paper-1 studies **Project Contract (PC) + deterministic materialization + bounded public-feedback repair**, starting from independently adjudicated, frozen public requirement facts.

Models propose designs and patches; a deterministic controller owns actions, budgets, state, terminal selection, and provenance. This runtime is distinct from the repository development agent governed by root [`AGENTS.md`][agents]. Development-agent instructions and privileges must not become candidate-model instructions or permissions.

Terminology: [PC and FPP ledger](../docs/specs/2026-09-08-sr2fpga-terminology.md).

## 1. Start here: scope and authority

| Question | Read |
| --- | --- |
| How do I install, configure, or check this subproject? | This README, [configuration guide][configs], actual entry points and tests |
| What defines methods, budgets, metrics, and information boundaries? | [Paper-1 v2.2 research plan][plan], then the applicable approved protocol |
| What is actually implemented or verified? | [Current status][status], followed by the referenced code and immutable evidence |
| Which serialized formats are valid? | [Registered contracts][contracts] and their applicable versions |
| Where are implementation responsibilities described? | [Code-architecture specification][architecture], subject to its v2.1 migration status |

**Version alignment.** This README follows the `paper1-v2.3` LLM amendment and its Chinese-authoritative v2.2 base. Case migration and local development validation are authorized; the plan remains unfrozen and official experiments unauthorized. Old gate results do not qualify the current LLM families.

Paper-1 targets ACM TRETS with frozen model weights and no task-specific training. Full requirement auditing, EA, and target-profile adaptation are default-disabled extensions. Representative fixed-target **L4 evidence belongs to the minimum research scope**; Vivado references are optional. Bitstreams, L5, and complete host/camera/SoC deployment are outside that minimum. Planned application cases have separate populations and evidence.

`training/` and retained export utilities are outside the Paper-1 core. Cross-project exchange uses registered, versioned files, not runtime imports.

## Current PC 2.1 development entry

`python -m sr2fpga_agent.pc --help` exposes `assemble` and `check` for strict
JSON/schema, original-byte binding validation and the first semantic reference
checks: `design.entry` and every structural instance must name an exactly
defined module, without recursive or unreachable definitions; the entry alone
uses the requirement-owned signature, and instance parameter names must be
declared by their targets with every declared parameter explicitly bound. See the
[development command guide](src/sr2fpga_agent/pc/README.md). The additional
`validate/build/compose` commands consume typed public context, check static
semantics, emit deterministic structure and compose body-only responses with
real parser protection. A fixed DW→PW development reference is available under
`tasks/ai_dw_pw`; official task qualification remains separate. The runner and single-sample generation commands below remain
legacy development tools and reject explicit current-protocol bindings.

## 2. Install and inspect the entry points

Run these package-development commands **from the repository root**, in an environment compatible with the actual package metadata:

```powershell
python -m pip install -e "agent[dev]"
python -m sr2fpga_agent.runner --help
```

The Runner and `DataGenerationAgent` below are retained legacy development paths, not the PC 2.1 main path or a v2.2 campaign recipe. `python -m sr2fpga_agent.pc --help` exposes input-only `assemble/check` and typed `validate/build/compose`. The latter implement configuration-level parameter/domain/wiring/type/tensor checks and RTL construction; algorithm and execution correctness require independent tools. Verify commands against the checkout and [current command reference][commands]. Python installation does not qualify FPGA tools, trusted harnesses, or target profiles.

The documented Python entry points are:

```python
from sr2fpga_agent.agent import DataGenerationAgent
from sr2fpga_agent.runner import load_runner_config
```

Before a model-backed run, use the [configuration guide][configs] and Runner help to bind the authorized scope, method, public inputs, model, budgets, evaluator, target, and output location. Keep credentials out of committed files. Legacy API examples do not establish a budgeted v2.2 run configuration.

## 3. Configuration and output locations

| Location, relative to the repository root | Purpose |
| --- | --- |
| `agent/src/`, `agent/tests/` | Runtime implementation and local regression tests |
| `agent/configs/current/` | Maintained configurations; inspect their actual protocol and side effects before use |
| `agent/configs/archive/`, `agent/configs/legacy/` | Historical and compatibility configurations, not default v2.2 experiments |
| `agent/configs/local/` | Ignored machine-local overrides |
| `contracts/` | Registered exchange formats; no parallel schema authority in this README |
| `artifacts/agent/runs/`, `artifacts/agent/candidates/` | Ignored runtime output and generated candidates |
| `datasets/` | Immutable releases, not a scratch or ordinary run-output directory |

Evaluator-private artifacts must remain inaccessible to candidates; an `artifacts/` directory name is not isolation. Dataset/evidence promotion is a separate authorized operation.

## 4. Paper-1 execution contract

The following is the **v2.2 target workflow**, not a statement that every current runtime path implements it:

```text
Frozen public requirement facts, independently adjudicated ready
    -> Method-specific planning or direct project generation
    -> Applicable PC checks and materialization / free generation
    -> FPP attempt or explicit failure checkpoint
    -> Budgeted public checks and method-permitted repair
    -> One terminal FPP sealed, or a retained no-candidate outcome
    -> Independent hidden semantic submission + specified L3 confirmation
    -> Fixed-target L4 for eligible, preselected positions
    -> Offline evidence, outcome, and cost reduction
```

Public checks may include L3; final confirmation may reuse valid reports for the identical candidate/tool/configuration. Hidden results cannot guide generation, repair, selection, or tuning across methods, tasks, and cases.

Core tasks are independently `ready` before dispatch. Intake may stop other requests as `needs_clarification` or `capability_gap`; it must not remove failed formal instances after observing outcomes. Full A_req/RQ0 is not a prerequisite.

### Methods and shared starting points

| Method | Initial generation | Public-feedback repair |
| --- | --- | --- |
| M0 Direct | Frozen facts -> complete FPP; one model call | None |
| M1 Direct-Repair | Shares M0's initial attempt | Patch or regenerate within the total budget |
| M2 Structured-Direct | Untyped plan -> freely generated FPP; two stages | None; no PC-specific checks or skeleton |
| M3 PC-Free | Generated PC -> freely generated FPP; two stages | None; common PC admission, no skeleton |
| M4 PC-Skeleton | Same generated PC -> deterministic structure -> model behavior; two model stages | No model-level internal retry or outer repair |
| M5 PC-Online | Shares M4's initial attempt/checkpoint | Correct permitted PC decisions or behavior within the same total budget |

M3/M4 share their initial PC and admission checks; M0/M1 and M4/M5 share their initial attempts, **including failure**. Retain `pc_failure_checkpoint`, `project_failure_checkpoint`, and `project_checkpoint` outcomes. A complete M4/M5 checkpoint includes behavior, not only a skeleton. Repaired successors never overwrite or flow back into shared initial artifacts.

**Primary comparisons:** M5−M1 at equal total budget and M4−M3 with a shared initial PC. M4−M0 and repair deltas are secondary. Statistical definitions remain in the plan.

### Budget and terminal selection

**B4 is a proposed plan setting, not an asserted runtime default:** at most four logical model calls per independent M1/M5 run. Normally M1 uses 1 initial + up to 3 correction calls; M5 uses 2 initial + up to 2. Earlier failures use actual accounting; model-based format repair and regeneration also consume calls.

The proposal allows at most four public-check cycles. Freeze token, response, subtool, runtime, and EDA limits before the relevant pilot/campaign. Equal repair rounds are not equal total budgets.

Seal the earliest publicly accepted candidate, otherwise the last complete boundary-valid FPP at exhaustion; a rejected final patch may leave an earlier valid candidate. If no complete FPP exists, retain a design failure. Do not select using hidden results or predicted QoR. Use `@initial` and an explicit budget endpoint; retain historical `@1`/`@A` version bindings.

## 5. PC, materialization, and edit boundaries

The active format is **PC 2.1**, with `schema_version`, controller-owned `bindings` and model-proposed `design`. Model output is the design root itself. System-HIS and its older decision/assembly contracts remain legacy-only; they are rejected by the new input path. The development implementation now includes tensor declaration checks, ABI construction, structure emission and parser-protected composition; execution obligations remain deferred to independent verification. Preserve H0–H3 identifiers and explicitly version semantic changes.

Preserve frozen interface, parameter, clock/reset, protocol, numeric, storage, concurrency, timing, and environmental obligations. Models choose only permitted implementation decisions. Declarations and traces are not RTL correctness proofs; semantic obligations still require independent verification.

Materialization supplies PC-derived structure and dependencies, not undeclared family-specific algorithms. Public behavioral components require provenance and equivalent method access/costs. Retrieval, persistent cross-task memory, skills, and Family Recipes are default-disabled in the core.

Validate patches against authorized regions/AST nodes and recheck structure/dependencies; comment markers alone are insufficient. M5 PC changes require a new version/hash, revalidation, rebuilding, and regeneration of affected behavior, all budgeted. Candidates cannot change frozen requirements or trusted evaluator/target assets.

Distinguish requirement-bound structure, generic materialization, public components/platform services, and model behavior in construction provenance. Trusted shells, DMA, and drivers are not automatically model-generated work.

## 6. Evaluation and FPGA evidence

Treat FPPs as untrusted. Use a declarative manifest for complete RTL, top/interface, metadata, constraint references, and initialization data. A trusted launcher—not candidate scripts—controls execution. Enforce path/include/dependency containment, allowed HDL features, and declared, hashed initialization reads.

Candidate testbenches are debugging aids, not independent oracles. Only permitted public diagnostics may guide repair; hidden material remains inaccessible. Pass text and exit codes alone cannot grant acceptance. Enforce access controls and feedback filtering in code, not only documentation.

| Tool family documented by this subproject | Role, subject to the qualified run configuration |
| --- | --- |
| Verilator | Specified L1 lint/checks |
| Icarus Verilog / `vvp` | Simulation; semantic L2 requires an evaluator-owned trusted harness |
| Yosys | Specified L3 synthesis; generic synthesis and device-mapped synthesis are different evidence |
| OpenXC7 / nextpnr | Open physical implementation where the target/tool flow is qualified |
| Vivado | Optional commercial-reference implementation |

Bind tool versions, scripts, device/package/speed grade, and constraints. This table does not certify availability or results. Generic cells are not FPGA LUTs; RAM attributes are not BRAM mapping evidence.

**VPP-L3** requires one terminal candidate to pass the common FPP/interface standard, L0, specified L1, public L2, independent hidden semantics, and specified L3, without unresolved boundary/provenance/budget violations. H stages are internal PC outcomes; M0/M1/M2 use `not_applicable`. `not_run(needs_oracle)` is not semantic success or complete VPP-L3.

Core official L4 follows VPP-L3 for the same sealed candidate at preselected positions. Keep L3 failures in the full physical denominator and separately report survivor results; never replace failures. L3 does not satisfy unverified physical/application obligations. L4 does not imply bitstreams, board execution, unmeasured power, or untested I/O timing.

## 7. Outcomes, recovery, and provenance

Separate design failures, infrastructure missingness, and integrity incidents. No terminal candidate retains its upstream design failure and VPP=0 even when hidden execution is `not_run`. Infrastructure outages are not automatically model failures. Do not turn missing evidence/cost into success or zero.

Keep hidden execution and semantics separate, with **one semantic submission per campaign/population/instance/replicate/condition**, as defined in plan section 15.3. Design-cluster identities govern dependencies, not additional scoring slots. Retrieve an already committed result after a lost receipt; do not rescore. Allowed precommit infrastructure retries preserve candidate/configuration. Committed semantic failure cannot reopen repair.

Derive results from append-only events and immutable artifacts, retaining failed attempts and unknown costs. Model diagnoses are hypotheses, not tool findings. Avoid blind resampling after uncertain provider execution.

Report actual deduplicated, full standalone-attributed, and post-checkpoint incremental costs. Shared preparation is executed once but is not free to an independent method. Separate hidden and physical verification costs from generation/public repair.

## 8. Validate and maintain this subproject

Start with the narrowest relevant checks. The documented broader alternatives are:

```powershell
python -m ruff check agent/src agent/tests
python -m pytest agent/tests -q -p no:cacheprovider
```

For changes spanning registered contracts and Agent behavior, the broader test alternative is:

```powershell
python -m pytest contracts/tests agent/tests -q -p no:cacheprovider
```

The broader command includes Agent tests. Inspect unfamiliar side effects before running checks. Mocks and historical G3 fixtures do not prove real-model performance or v2.2 WP0–WP6 completion. See [current commands][commands] for specialized procedures.

Keep local usage here, research definitions in the plan, formats in contracts, progress in current status, and evidence in existing records. Do not accumulate fixture histories or export manuals here. Add local `AGENTS.md` only for genuinely subtree-specific development instructions, not a copy of the root guide.

[agents]: ../AGENTS.md
[plan]: ../docs/specs/2026-09-15-sr2fpga-paper1-research-plan-v2.2.zh.md
[status]: ../docs/current-status.md
[commands]: ../docs/current-status.md#current-commands
[contracts]: ../contracts/README.md
[configs]: configs/README.md
[architecture]: ../docs/specs/2026-09-15-sr2fpga-paper1-code-architecture-development-spec-v2.1.zh.md
