# Research canon

This canon separates present facts from intended experiments. Its evidence
cut-off is 2026-08-14.

> Historical foundation snapshot created under `paper1-freeze-v1.3`. The active
> `paper1-v2.1` is the current research plan; this canon predates it and was
> written against `paper1-freeze-v1.7`. Training facts below
> remain repository inventory only and this snapshot is not rewritten.

## Literature facts

- HORIZON frames hardware design as repository-level code evolution: a Markdown
  harness is compiled into a project pack containing an executable evaluator,
  acceptance predicate, domain guidance, and git/runtime policy; a fixed agent
  then edits and evaluates an isolated repository until convergence. See the
  local [source-grounded reader](../../../../references/paper-readers/2606.28279v1/paper.md).
- HORIZON reports best-so-far convergence to 100% on its selected suites, not an
  independent Pass@1 result. It uses one fixed GPT-5.3 backbone, reports roughly
  209.9M tokens through earliest-best convergence, and does not train or update a
  policy.
- HORIZON explicitly warns that repair-visible evaluator feedback can cause
  over-solving and recommends final scoring with hidden randomized tests,
  independent references, formal/property checks, or held-out tool settings.
- HORIZON defines QoR as a possible reward component but does not report PPA/QoR
  experiments in the paper.
- Therefore repository-level workspaces, hands-free tool use, iterative repair,
  executable acceptance gates, and saved trajectories are baseline capabilities,
  not sufficient SR2FPGA novelty claims.

## Experimental facts in the current repository

- The local `develop` checkout is at `bd516c110862`; the locally known
  `origin/develop` ref points to the same commit. This is not remote CI, review,
  or published-merge evidence.
- The final reorganization report records 1,059 passing tests plus 349 passing
  subtests, 24/24 deterministic L3 samples, H0/H1/H2 at 24/24, H3 at 14 pass and
  10 not-applicable, and zero tracked `tmp/` paths.
- The canonical task catalog contains 71 target families. The evidence ledger
  records 31 implemented families, 31 at L3 or higher, 21 mutation-qualified
  families, nine with independent Python references, two OpenXC7 L4 passes, no
  Vivado pass, and no L5 pass.
- All 14 catalog-designated Paper-1 core families are implemented, reach L3, and
  are mutation-qualified. This is deterministic/reference-path evidence, not a
  learned-model result.
- Phase C records 9/9 independent-Python-oracle passes and 45/45 scoreable
  mutations killed.
- Phase D is an integrity-valid negative pilot: 12 generation failures, 12 H2
  failures, 0/24 L0-L3 passes, zero repair attempts, and no live L4 result.
- `agent/` implements deterministic and model-backed generation, two-stage
  `REQ2HIS -> HIS2PROJECT`, H0-H3 recording, L0-L4 orchestration, repair hooks,
  independent oracles, mutation checks, and trajectory/training-view export.
- `training/` implements dataset conversion, dry-run validation, LoRA training,
  adapter merge, and serving configuration without importing `agent/`. No
  trained adapter or merged model is present under `artifacts/training/`.
- The current registered datasets are `internal_only`, require license review,
  and have legacy-unavailable configuration fingerprints.

## Contract and taxonomy debts

- Runtime H0 is a handwritten structural subset; it is not demonstrated to
  execute the full canonical JSON Schema.
- The canonical v1.2 fixture contains a `priority_rule` accepted by contract
  tests but rejected by the Agent H-stage semantics.
- The freeze spec's full W1-W10 H1 ambition is not implemented as one complete
  runtime gate.
- Reset semantics and compatibility-field handling are not yet one closed,
  versioned rule.
- The canonical catalog's `clock_divider.core_modules` incorrectly names Sobel
  modules.
- T7 is T3 in historical compressed/topology material but T4 in the canonical
  catalog and current runtime metadata.
- T10 and T11 are distinct topology aliases but share one
  `p_rl_qlearning_accel` catalog/evidence row; T10 evidence cannot be attributed
  to T11 without alias-level evidence.
- Catalog `implementation_status` describes target intent and must never replace
  the evidence ledger plus referenced artifacts.

## Terminology definitions

- **Project generation:** generation of a coherent multi-file RTL project
  package. Do not call it project synthesis, which is easily confused with EDA
  logic synthesis.
- **System-HIS:** a typed requirement/project semantic contract. It specifies
  what must be generated; it is not the episode control plane and is not itself
  empirical verification.
- **Episode pack:** the frozen control plane for one run: requirement, platform,
  information privileges, edit policy, repair-visible evaluator, hidden scoring
  policy, budgets, seeds, and provenance.
- **Visible pass:** acceptance by repair-visible checks. It is diagnostic and can
  be optimized against.
- **Verified project pass (VPP):** method-neutral project-level success under the
  common L0/L1/public-L2/one-shot hidden-L2/L3 definition. H-stages are
  conditional mechanism outcomes for HIS-producing methods.
- **Implemented:** code/configuration exists.
- **Verified:** named artifacts demonstrate the bounded claim.
- **Target/hypothesis:** intended capability or expected effect that still needs
  an outcome-producing experiment.
- **`not_run`:** no result was produced; it is neither pass nor design failure.

## Supervisor and project constraints

- Make the multi-file project, not a single Verilog file, the evaluation unit.
- Use code, contracts, ledgers, and real artifacts before narrative documents.
- Preserve failed attempts and negative results.
- Separate local state from remote/published state.
- Preserve the ownership boundaries among `agent/`, `training/`, `contracts/`,
  `datasets/`, `artifacts/`, and `reports/`.

## Forbidden claims

- “first repository-level hardware agent,” “first autonomous RTL repair loop,”
  or equivalent claims already covered by HORIZON and adjacent systems;
- “full JSON-Schema H0,” “complete W1-W10 H1,” or “general System-HIS
  guarantee” before contract closure;
- “trained SR2FPGA model,” “held-out generalization,” “repair improvement,” or
  “QoR predictor” before corresponding artifacts exist;
- “24/24 L4,” “Vivado-verified,” “bitstream complete,” or “board validated” from
  current evidence;
- transferring T10 evidence to T11 or target-catalog intent to runtime evidence;
- interpreting Phase D `APPROVED` as generation quality; or
- describing application-themed shells as full application accelerators.

## Unresolved claims

- Whether generated System-HIS improves hidden project correctness beyond an
  untyped two-stage plan with equal information and budget.
- Whether contract-guided repair improves success or only catches errors earlier.
- Whether any gain persists when cost, public-tool calls, and oracle privileges
  are matched.
- Whether L0 improvements translate to L2/L3 rather than merely shifting the
  failure frontier.
- Whether successful L3 candidates retain their advantage on a predeclared
  OpenXC7 L4 subset.
