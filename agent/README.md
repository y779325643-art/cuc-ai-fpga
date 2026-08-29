# SR2FPGA Agent

This project owns FPGA project generation, validation, repair, L0-L4 tool
orchestration, and trajectory recording.

Follow the repository-wide working agreements in [`AGENTS.md`](../AGENTS.md).
Paper-1 research semantics are governed by
[`paper1-freeze-v1.7`](../docs/specs/2026-08-14-sr2fpga-paper1-research-program-freeze-design.md).
Use [`docs/current-status.md`](../docs/current-status.md) for mutable capability,
verification, debt, and gate facts.

Training and model fine-tuning are owned by the separate `training/` project.
The Agent runtime intentionally has no PyTorch, Transformers, PEFT, or TRL
dependency.

## Installation

From the repository root:

```powershell
python -m pip install -e "agent[dev]"
```

The development extra installs pytest and Ruff. Check the Agent package and
tests with:

```powershell
python -m ruff check agent/src agent/tests
```

Canonical Python imports use the standalone package:

```python
from sr2fpga_agent.agent import DataGenerationAgent
from sr2fpga_agent.runner import load_runner_config
```

## Commands

Editable installation provides:

```text
sr2fpga-agent
sr2fpga-runner
sr2fpga-baseline-report
sr2fpga-req2file-eval
sr2fpga-task-evidence
sr2fpga-ambiguity-audit
```

The equivalent module entry points remain available, for example:

```powershell
python -m sr2fpga_agent.runner --help
```

## Configuration

- `agent/configs/current/`: maintained runnable configurations.
- `agent/configs/archive/`: historical evidence; not run by default.
- `agent/configs/legacy/`: compatibility-only configurations.
- `agent/configs/local/`: ignored machine-local overrides when needed.

Active configurations write run output beneath ignored
`artifacts/agent/runs/` and generated candidate datasets beneath ignored
`artifacts/agent/candidates/`. Existing releases under `datasets/` are
immutable inputs. Promoting a candidate into `datasets/` is a separate,
explicit release operation.

## Repair Layers

The model-backed two-stage path keeps two repair scopes separate:

- `SystemHisRepairer` repairs a REQ2HIS candidate after an H0, H1, H2, or H3
  failure. The repaired contract is rechecked through all applicable H stages;
  only a passing contract can be lowered into a newly rebuilt full project.
- `ProjectRepairer` retains the existing project/RTL repair path after a full
  project reaches the L0-L4 evaluation pipeline. It does not serve as the
  System-HIS repairer.

Active implementation names are provider-neutral. Former `DeepSeek*` class
names remain compatibility aliases, while `deepseek` configuration values
continue to identify the actual provider/source kind.

## Request Intake Boundary And REQ2HIS

There is no request-mode switch. The current two-stage path combines a short
user requirement with structured request and platform fields to form an
auditable Requirement Envelope. Explicit user facts, declared platform
defaults, unresolved facts, and detected capability labels remain
distinguishable. An exact catalog alias may be recorded as metadata, but an
unknown system is never coerced to the nearest task family.

This section is organized as the pipeline runs: requirement boundary and RQ0
audit, episode pack and trusted core, method adapters (CD4), System-HIS
validation, budget accounting, and a runnable example. Retained training-view
export (CD8) is outside Paper-1. Mutable completion status lives in
[`docs/current-status.md`](../docs/current-status.md); see the
[Paper-1 code-architecture spec](../docs/specs/2026-08-18-sr2fpga-paper1-code-architecture-development-spec.md)
for the normative module, interface, and CD1-CD10 work-package design.

### Requirement Boundary Disposition

CLI and Runner samples now use one deterministic, evaluator-side requirement
boundary before selecting deterministic-reference, Direct, or System-HIS
generation. The boundary preserves fact provenance, records its envelope/route
hashes, classifies `ready`, `needs_clarification`, or `capability_gap`, and
stops a non-ready sample before its project generator is called.

### OASA: Requirement-Ambiguity Audit (RQ0)

The registered `ambiguity-case-manifest-v1`, `requirement-audit-v1`,
`ambiguity-audit-events-v1`, and
`clarification-replay-v1` now support an independent evaluator-side Phase A/B
runner. It verifies the sealed manifest hash, passes only the public projection
into requirement intake, writes a validated Phase A outcome, and executes one
precommitted answer only when Phase A returned `needs_clarification`. Replay
lineage and a persistent evaluator-store one-shot marker reject a second replay;
neither phase dispatches a project method. The evaluator event interceptor logs
Phase A start/completion and records a downstream attempt before its callback can
run; its artifact is hash-bound to both the sealed manifest and the exact Phase A
artifact. Escaped downstream events remain separately countable boundary
violations. `ambiguity-outcome-v1` then reduces
one or more named observations by `base_requirement_cluster_id`: `not_run` stays
in the fixed case-observation denominator but outside semantic confusion, and
any false-proceed observation fails the cluster primary safety outcome. A
counterfactual-consistency observation is eligible only when one completed case
from each of the four frozen strata is present in the same base cluster; all
four dispositions and the clarification replay must match their precommitted
outcomes. The reducer also reconciles Phase A event counters with the Phase A
artifact, adds replay counters, and reports model/tool calls, tokens, wall time,
and infrastructure status; `not_run` remains included in this cost. Use
`--events-output`, `--replay-output` with `--evaluator-store`, then
`--outcome-output` for the
single-observation CLI path; outcome creation additionally requires the
evaluator-owned `--witness-artifact`. `ambiguity-witness-v1` binds two annotator
commitments, adjudication, material interpretation commitments, gold
fact/capability/default/assumption IDs, and a private canary. The reducer reports
precision/recall for all four ID classes and rejects any canary exposure. No
post-hoc text classifier is used for the remaining audit diagnostics: the
witness freezes unknown-family ready counterexamples, while Phase A fact
provenance determines whether a clarification question repeats a known fact.
No signed OASA fixture set, frozen interval implementation, or official audit
campaign exists yet; incomplete development clusters therefore remain outside
the counterfactual-consistency denominator rather than receiving pass credit.

### Episode Pack And Trusted Core

Ready development samples for M0-M5 can additionally carry a registered
`episode-pack-v1` artifact. Its immutable public projection is shared across
methods and contains only the requirement facts and public profile
commitments; family and evaluator metadata contribute only an audit-side hash.
The Agent validates pack schema and digests before generation. The current
builder cannot create an official pack: official use remains blocked on a
signed G4b loader.

The first trusted-core slice also provides a local content-addressed,
write-once artifact store, append-only event records, fail-closed budget
reservations, and one-shot consumption markers. These primitives are tested in
isolation but do not yet replace the legacy Recorder or constitute an official
hidden evaluator.

### Method Adapters (CD4: M0-M5)

The first CD4 adapter slice is also available as a provider-neutral core. A
closed M0-M5 registry consumes only `FrozenRequirementContext` through narrow
generation facades, represents untyped-plan and System-HIS work as explicit
pre-candidate artifacts, and applies repair privileges before any repair
facade call. For a complete excluded block, `PairedArtifactCoordinator` now uses
explicit keys for three eagerly prepared, method-neutral checkpoints after the
measurement freeze and before method execution: the Direct initial project for
M0/M1, shared System-HIS for M3/M4/M5, and the complete behavior-filled initial
project for M4/M5. M4 and M5 consume the identical complete project artifact;
partial and legacy paths retain the earlier lazy compatibility wrappers and mint
no G3b artifact. This core is verified with fake providers. Development Runner
uses the adapters and paired coordinator for explicit M2-M5 pre-candidate
dispatch, then routes M0-M5 attempts through the common development/excluded
public and terminal authority.
M2 performs a frozen-context untyped-plan call followed by canonical free-project
generation without H stages or a skeleton; M5 uses the executor with one bounded
complete-H correction. M5 project repair, remaining implicit compatibility
paths, and official public/terminal/hidden ownership remain incomplete.

For `development`/`excluded` M0-M5, Runner now freezes every attempt before
public evaluation. A physically separate, one-shot evaluator returns only closed
stage outcomes and sanitized repair diagnostics; raw commands, stdout/stderr,
paths and exceptions stay evaluator-side. `public-evaluation-candidate-v2`
preserves envelope-invalid attempts for evaluator-owned L0 diagnosis without
making them complete terminal candidates. Candidate-owned testbenches are
ignored. A development/excluded task may instead configure a registered,
hash-bound evaluator-owned trusted public L2 harness; without it, public L2
remains `not_run(needs_oracle)`.

The registered `@1`/`AT_A` selector chooses the single complete candidate, the
earliest accepted candidate, or the last complete candidate at budget
exhaustion. Runner seals that exact choice with the selection and authoritative
attempt outcome as public evidence, reruns terminal public evaluation, requires
stage agreement, and then gives the same immutable seal to the opaque hidden
authority. Development pass credit comes only from the selected attempt outcome;
all of these records remain `official_outcome=false` and do not authorize G4b.

An explicit pre-candidate `EpisodeExecutor` now consumes those emissions. It
records `method_prepared`, planning, H validation, HIS-correction request, and
candidate/no-candidate transitions as append-only events. Untyped M2 planning
bypasses H by contract; M3/M4 stop on H failure; M5 may correct HIS only within
its declared transition budget, after which all H stages are rerun before any
project lowering. Illegal post-terminal transitions are rejected. Public tool
evaluation and terminal/hidden phases remain outside this executor slice.

For the bounded M4 H-stage stop fixtures, Runner publishes the registered
`development-pre-candidate-stop-outcome-v2` only after its reducer re-reads the
excluded episode pack, hash-bound platform and backend capability profiles,
planning blob, the complete ordered five-event episode stream, and the
raw-cost-derived terminal-null trajectory. Separate real Runner cases cover H0,
H1, H2, and H3:
earlier H stages pass, the named stage fails, later stages and every downstream
project/evaluation stage remain `not_run`, and repair/public/hidden/EDA activity
is zero. Missingness remains a retained `design_outcome`, development VPP is
false, and official VPP stays `not_evaluated`. The v1 M4/H0 shape remains
readable; neither version grants G3 or official authority.

CLI and Runner M0/M1 development dispatch now bind the real Direct model client
to the validated episode pack's frozen public context. Their Direct prompt no
longer serializes `ProjectRequest.task_type`, evaluator project names, or the
caller-supplied platform object; a deterministic project name is derived from
the public requirement ID. The canonical project parser remains the output
gate, and a missing or invalid M0/M1 episode pack stops before the model call.
Programmatic legacy `DirectProjectGenerator` remains available for compatibility
but is not the Paper-1 M0/M1 dispatch path.

A context-native M3-M5 initial System-HIS slice is also implemented.
`FrozenContextSystemHisFacade` sends only the validated
`FrozenRequirementContext` and the registered System-HIS schema to REQ2HIS;
`FrozenContextSystemHisValidationFacade` runs H0-H3 directly against that frozen
projection and its hash-bound platform. Only a passing HIS may reach deterministic
skeleton lowering, where trusted code replaces the legacy manifest with a
canonical `project-package-v1` manifest before artifact hashing. H failure stops
before HIS2PROJECT. The single-sample CLI M4 path uses the same context-native
bridge and `EpisodeExecutor` as Runner, with its planning and state-transition
artifacts stored below the sample directory. M3 now consumes the same
materialized frozen HIS as M4 and directly generates a complete canonical
project; spy tests prove that it never calls the skeleton builder or behavior
filler. M5 now has a one-call
context-native HIS correction facade: only the failed H stage and public
diagnostics enter its prompt, and `EpisodeExecutor` reruns all H stages before
lowering. M4 cannot invoke it, and failed correction calls remain budgeted.
The opt-in `--development-his2project-output-repair` CLI variant provides a
shared pre-candidate repair ceiling of two. A HIS correction consumes one unit;
each rejected HIS2PROJECT behavior response may consume one remaining unit.
Every rejected response is persisted and linked through explicit
`project_output_rejected` and `project_output_repair_requested` events. The
variant uses at most four logical model calls, disables outer project repair,
forces one outer attempt, and is always recorded as excluded development work
that is ineligible for official evidence.
Before the first HIS2PROJECT call and every behavior-output repair, the trusted
deterministic skeleton is rebuilt, hash-checked and statically cross-checked.
Static skeleton defects stop before the behavior model. Raw model output is
stored as UTF-8 text; a byte-identical repair consumes its producing call and
terminates as non-repairable `NoProgress`, with both parent and produced
artifact refs retained in the terminal event.

H1 additionally requires all declared top clocks/resets to appear in
`top.ports`. Entries in `top.parameters` and `components[].parameters` must be
objects with non-empty string `name` fields; malformed strings are rejected and
never automatically normalized. The System-HIS v1.2 JSON Schema remains
unchanged, so this is an H1 semantic erratum rather than a Schema migration.
A context-native M5 project-repair facade excludes trusted file contents from
the prompt, accepts only public stage diagnostics, and requires a trusted outer
envelope whose editable composite regions are bound to actual byte ranges,
registered method policy, and verified append-only events. Changes remain
limited to those behavior regions; package and HIS/RTL checks run afterward.
The facade remains development-only: its invocation still has compatibility
ownership and no signed official edit-policy commitment. Returned attempts do
enter the common evaluator-owned public and terminal authority and fail closed
rather than falling back to family routing.

### Excluded Full-Pack Smoke (CD9, Development Only)

`full_pack_smoke.py` now reconciles a fake-fixture M0-M5 pack built from one
frozen public projection. It requires matched M0/M1 initial projects, matched
M3/M4 System-HIS, separate M3/M4 candidate keys, matched M4/M5 skeleton
projects, and explicit success-conformance, H-repair, project-repair, non-ready,
hidden-fail, and infrastructure-`not_run` scenarios. The persisted report is
validated at write time against registered `full-pack-smoke-report-v1`, remains
explicitly excluded, and sets `official_outcome=false`, `rq1_evidence=false`,
`rq2_evidence=false`, `g3_accepted=false`, and `g4b_authorized=false`. Its
closed scenario facts reject raw hidden output and undeclared fields.

This is not an accepted G3 package. Complete excluded M0-M5 Runner blocks now
require explicit semantic-instance, replicate, block, decoding-control, requested-
seed provenance, and independent schedule identities. Before a run directory is
created, a pure planner verifies one common effective model/gateway configuration
and one allowed six-method Williams row. Runtime then materializes and re-reads one
registered `paired-block-v1` artifact, drives the serial execution order from that
artifact, and binds the same reference through audit-only episode-pack metadata,
measurement freeze records, generation/completion events, every trajectory
attempt's input hashes, and full-pack runner reconciliation. Preflight predicts the
same block reference and episode-pack hash as runtime. Partial excluded blocks and
legacy `development_derived` samples mint no paired-block artifact. This is
development identity/order conformance, not proof that a remote provider obeys a
requested seed. Per-sample Runner costs are reconstructed
from raw events and development hidden consumes the same terminal seal. A
registered `full-pack-runner-reconciliation-v1` companion originally
independently re-verified exactly one M0-M5 `trajectory-v2` set, every cost
summary and axis, matching terminal seals, shared public-projection binding,
and opaque hidden refs; wrong-method and tampered trajectories fail closed. The
v1 contract remains registered for artifact compatibility. The current assembler
writes `full-pack-runner-reconciliation-v2`, which retains those checks,
optionally binds the verified paired-block reference plus planned/actual method
order, and records the live runtime-scenario evidence blocker. An assembler now
consumes the completion events from one real fake-provider, excluded M0-M5
`run_batch` and writes both reports. For HIS methods, downstream Agent H
validation reuses the episode pack's frozen public context rather than adding
evaluator-side task facts. M4/M5 completion records also carry separately
verified deterministic-skeleton artifacts; false skeleton hashes fail closed,
and final-candidate equality is not used as skeleton evidence. A new outcome
companion projects the registered terminal public outcome, then re-verifies
raw-event trajectory/cost/selection/terminal lineage, reconciles repair calls
against `outer_repair_attempts`, retains missingness and aggregates exactly one
M0-M5 record. The authority now separately reduces sanitized hidden conformance:
the scripted fixture produces six development VPP passes, while all six official
VPP values remain `not_evaluated`. Official authority, the candidate benchmark,
G5 provenance, and any enabled profile-pair extension belong to later gates or
the optional extension; they are not G3 acceptance prerequisites. Their current
status is summarized in [`docs/current-status.md`](../docs/current-status.md).
The integration uses fake clients and a passing tool runner, not a provider
campaign or model result.

The G3b development slice adds a verified three-node checkpoint manifest, a
method-neutral preparation-event chain, and a companion reconciliation derived
from those raw events plus the six method trajectories. In two fake-provider
orders, clean complete blocks use six physical initial model calls while the six
standalone-attributed rows contain ten initial calls. Actual block consumption,
standalone-attributed end-to-end cost, and the `M1-M0`, `M4-M3`, and `M5-M4`
post-checkpoint contrasts reconcile all 13 axes; shared preparation is counted
once physically, is never split among consumers, and is not charged to execution
ordinal zero. Failure, unavailable-axis, visibility, tamper, and exact-complete
resume fixtures fail closed. A complete matching local state can resume without
new calls or charges after cross-linked verification; partial, corrupt, or legacy
in-place resume requires a new run ID. This is G3b development conformance only:
`g3_accepted=false`, and no real-model, training, official held-out, evidence-
promotion, or paper outcome was produced.

The Agent now also registers a development-only provider seed-capability
contract and bounded probe CLI. A capability profile binds provider adapter,
model, hashed gateway, the complete fixed protocol, documentation
snapshot/source/review provenance, and ordered per-call observations. Its
loader recomputes the aggregate counts, status, output/fingerprint conclusions,
token totals, classification, limitations, profile ID, and eligibility; summary
tampering therefore fails closed. The CLI records only
`self_reviewed_development` documentation review provenance and cannot create a
positive candidate without an independent review artifact.
Runner source configuration may point to a local capability manifest, but
persisted config and measurement-freeze records contain only its profile ID,
content hash, classification, and eligibility bit—not the local path. With
`require_paired_confirmatory_seed_control: true`, a missing, mismatched, invalid,
or ineligible manifest stops before the run directory is created. The default
development mode remains observational and never upgrades undocumented or
best-effort support to deterministic control.

The capability profile is not yet attached to each model call through
`seed_control_evidence_ref`, and Runner does not yet verify that its profile
seed equals every task's requested seed. Those end-to-end capability bindings,
shared block checkpoints, and three-view cost reconciliation remain CD9 work;
the separate replicate/schedule/order lineage is implemented by G3a.

A separate excluded M1 repair fixture now exercises one artifact-derived project
repair path through the real Runner authority. Attempt 0 fails evaluator-owned
L1, a valid model-owned RTL patch is recorded, attempt 1 reruns
L0/L1/public-L2/L3, and `@A` selects `attempt-001`. The registered episode reducer
reconciles diagnosis/patch/rerun, project repair `1/1/1`, one raw
`outer_repair_attempt`, terminal/public/hidden lineage, and development VPP pass;
official VPP remains `not_evaluated`. This closes only the L1 repair fixture.
Separate real excluded M4 fixtures now close the H0-H3 permission-denied
pre-candidate stop cells: the episode-pack/platform/capability commitments,
planning hash, complete ordered state-event stream, zero downstream cost and
retained design outcome are rebuilt from artifacts. Event-order, post-stop event,
report/platform digest, capability drift, cross-episode trajectory and blob
tampering fail closed.
Four real excluded M5 fixtures now cover one initial failure at each of H0, H1,
H2 and H3. Runner records the initial HIS, the single correction request and
parent hash, the corrected HIS, the complete H0-H3 rerun, candidate emission,
terminal/public/hidden lineage and raw cost events, then writes
`development-his-correction-outcome-v1` only after the reducer rebuilds that
chain. The shared budget accounts exactly one `req2his`, one
`system_his_repair` and one `his2project` call, with no project repair. This is
excluded development conformance only: official, pass-credit, RQ1/RQ2, G3 and
G4b flags remain false.
Another real excluded M1 fixture keeps repair
authority and budget available, reaches public L0/L1/L2/L3, then receives one
hidden fail. Runner emits its registered episode outcome only after rebuilding
public/trajectory/cost/hidden lineage; the repair spy remains unused,
development VPP is false, and exact-ledger replay, forged pass credit, reordered
or cross-episode lineage, and blob tamper fail closed. Other project-repair
stages, broader hidden-fail/full-pack
scenario authority and infrastructure-missingness remain open,
so the current runner/outcome v2 reconciliations name
`runtime_scenario_evidence_reconciliation` as the live blocker and G3 remains
unaccepted. Their v1 predecessors remain registered and are not rewritten.

The provider and, for a Paper-1 run, the recorded `method_condition` select a
generation method rather than a request mode:

- a deterministic provider remains a reference method for supported catalog
  tasks; it is not a model-generated result and receives no learned-method
  credit;
- the Direct project parser and evaluator accept a complete project without
  System-HIS. M0/M1 record H0-H3 as `not_applicable` and continue through the
  same method-neutral L0-L4 path; and
- a two-stage provider performs `REQ2HIS -> HIS2PROJECT`. REQ2HIS calls the
  configured provider's real API, then the generated System-HIS is checked and
  repaired through H0-H3 before it can be lowered.

### System-HIS Validation (H0-H3) And Representation Disposition

H1 records a machine-readable W1-W10 map with per-rule
`pass`/`fail`/`not_applicable` and diagnostics. The registered conformance
matrix binds the rules to Schema/H-stage/reset/lowerer/compatibility tests;
`not_applicable` is not pass credit.

The registered `system-his-compatibility-v1` envelope is the runtime authority
for representation disposition: v1.2 is canonical, v1.1 is legacy quarantine,
Direct/Untyped methods use `not_applicable`, and unknown representations fail
closed into quarantine. Runner and Recorder derive the training partition from
this contract rather than private version-string tests.

### System-HIS Path Boundaries And Family Recipe

The unified System-HIS path has these boundaries:

- Runner tasks may provide the real user text in `requirement`; when omitted,
  the fallback remains generic and does not silently inject task-family
  boilerplate;
- safe platform facts such as width, clock, reset polarity, and target name are
  supplied outside the short user prompt;
- missing facts that would change hardware semantics produce a small set of
  clarification questions before a two-stage API call; the CLI returns those
  questions and records generation as `not_run`, not as a design failure;
- capabilities outside the current backend profile produce an explicit
  `capability_gap` instead of being renamed to a supported family or protocol;
  this is likewise excluded from design-failure credit;
- `intent.requirement_trace` and the values at its mapped System-HIS locations
  are checked by the generic H3 gate; and
- Family Recipe selection is automatic and exact-only. The selector reconciles
  exact catalog family IDs/aliases, exact runtime task names, and registered
  whole-phrase triggers in the requirement; it never performs fuzzy or nearest-
  family matching. A unique family with registered recipe content may receive
  that recipe; an unknown identifier, conflicting ownership, missing recipe,
  or catalog-backed held-out deny decision keeps the generic prompt.

Every two-stage System-HIS selection records the resolved-family evidence,
selection reason, recipe ID/version/content hash when selected, and the deny-
policy ID/version/hash and status together with the catalog version. The
complete decision is evaluator-side sample/preflight/freeze metadata only: it
does not enter the REQ2HIS prompt, generated System-HIS, or HIS2PROJECT input.
Only when `status=applied` does the selected recipe body enter the REQ2HIS
prompt. Direct-project and deterministic-reference methods do not record this
two-stage recipe decision. The current deny set protects the four candidate
G4a primary held-out families. Its status is explicitly
`candidate_g4a_not_signed`; it is not a claim that the G4b campaign split has
been signed.

### Budget And Call Ceiling

Each CLI/Runner model sample has one shared logical model-call ceiling and
per-call ledger across generation and repair stages. Active generator and
repairer construction sets each internal parse/regeneration loop to one attempt;
additional repair iterations occur only in the outer, recorded attempt loop and
consume the same per-sample call budget.

The development accounting foundation now registers `attempt-event-v1` and
`cost-summary-v1`. `AttemptCostLedger` writes content-addressed, schema-validated
events and requires a final classification of every frozen cost axis; the
reducer verifies event IDs, lineage, close position, raw totals, and unavailable
reasons before writing a summary. `ModelCallBudget` can attach this ledger to
record logical-call reservations, provider transport attempts, failed calls,
budget exhaustion, and provider-reported token usage. Built-in OpenAI- and
Anthropic-compatible clients report the exact attempt count after their internal
retry loop and preserve explicit input/output/cache usage from non-streaming JSON
or streaming usage events. Streaming readers publish usage in their failure path,
so observed usage from transiently failed attempts is conservatively accumulated
with the successful retry; if any attempt leaves an axis unobserved, that logical-
call axis remains unavailable. Missing, invalid, or uninstrumented custom-client
fields are explicitly unavailable rather than estimated. Existing callers that
do not supply the ledger retain their compatibility behavior.

This remains partial CD6 infrastructure. For M0-M5 samples the Runner now creates
one routed ledger per real attempt; normal and aborted exits close and reconcile
it. Model-call/transport, fail-closed parser/schema retry reservation,
outer-repair, public command/Vivado, wall/EDA, and development-hidden
call/runtime producers are connected. Active builders freeze parser retries at
zero, matching their internal `max_attempts=1`; hidden dispatch currently has no
retry path. Raw events also bind the sample candidate-source failure origin from
a closed five-value taxonomy (or `null` on unclassified compatibility paths), a stable logical
candidate ID, frozen-input hashes, and the candidate-project output hash for
each attempt; Runner `sample_completed` events expose the verified cost-summary
references. The registered `trajectory-v2` reducer verifies every referenced
raw attempt event and cost summary, then writes a separate write-once canonical
artifact without overwriting the legacy Recorder trajectory. For
`development`/`excluded`, every attempt is sealed before public evaluation; the
one-shot authoritative outcome is the only project-repair diagnosis and
terminal-selection input. Registered `@1`/`AT_A` selection chooses a complete
candidate, which is resealed with its selection and outcome evidence. Terminal
public and opaque hidden authorities consume that same seal, and `trajectory-v2`
re-verifies the complete chain. A selected earlier complete candidate is valid
when a later attempt is incomplete; noncanonical or unsealable output remains an
explicit design failure with no automatic pass credit. Trusted public L2 is now
available only when a validated development/excluded harness manifest is
configured; attempt and terminal reevaluation must bind the same commitment.
One-shot hidden execution still returns only an opaque reference to the Runner.
The evaluator authority can now separately publish a reducer-only sanitized
development hidden outcome (`pass`, `fail`, or `not_run`) bound to the same
terminal seal and public commitments. Episode/full-pack reducers expose a
separate `development_vpp_l3`. For fully reconciled excluded terminal
projections, Runner also emits the registered episode-outcome reference after
the reducer rebuilds raw source lineage; incomplete repair projections remain
without a closed episode outcome. Official `vpp_l3` remains `not_evaluated`.
G3 remains open because positive artifact-derived acceptance and the complete
G3 matrix are not yet closed. G4a prepares the candidate protocol, G5 is an
excluded pilot, a verifier-derived G4b receipt authorizes G6 materialization,
and G7 executes official outcomes; none of those later deliverables is a G3
acceptance prerequisite.

Complete G3b blocks additionally use a separate
`development-block-preparation-event-v1` ledger for the three shared checkpoints.
Its verified close feeds `development-paired-block-cost-reconciliation-v1`, whose
actual, standalone-attributed, and three checkpoint-specific incremental views
each retain the same 13 axes and propagate unavailable sources rather than
substituting zero. The existing per-method attempt ledger remains exclusive to
method execution; shared checkpoint events never acquire a method owner.

RQ4 now has registered pilot-only target-profile pair manifest and development
outcome contracts. The manifest binds stable pair/member/profile hashes, one
change axis or an explicit compound profile, invariant and change rules,
compliance commitments, and fixed L3/OpenXC7-L4 endpoints. The reducer reads
verified member cost-summary artifacts, retains both-member missingness and
violations, sums all 13 cost axes, and independently rechecks development
`TPA-L4`. It cannot create terminal, pass-credit, or official authority. The
extension policy follows the active Paper-1 freeze; current fixture and outcome
status lives in [`docs/current-status.md`](../docs/current-status.md).

### Example: Real Two-Stage API Invocation

This invokes a real OpenAI-compatible API for the two-stage REQ2HIS path:

```powershell
sr2fpga-agent `
  --dataset-root artifacts/agent/candidates `
  --sample-id request-001 `
  --project-name counter8 `
  --requirement "Design an 8-bit counter with active-low reset." `
  --provider openai_compat `
  --model YOUR_MODEL `
  --base-url https://your-provider.example/v1 `
  --api-key-env SR2FPGA_API_KEY
```

For a provider that implements the Responses API, use a versioned API root and
select the protocol explicitly. Keep credentials in an environment variable or
ignored `.env` file; do not put them in the command or config:

```powershell
sr2fpga-agent `
  --dataset-root artifacts/agent/candidates `
  --sample-id request-001 `
  --project-name counter8 `
  --requirement "Design an 8-bit counter with active-low reset." `
  --provider openai_compat `
  --model gpt-5.5 `
  --base-url https://your-provider.example/v1 `
  --api-key-env SR2FPGA_API_KEY `
  --wire-api responses `
  --reasoning-effort xhigh `
  --disable-response-storage
```

Runner `sources` accept the equivalent `wire_api: responses`,
`reasoning_effort: xhigh`, and `disable_response_storage: true` fields. The
Responses adapter sends `store: false`, uses `max_output_tokens`, and records a
requested decoding seed as not forwarded because the protocol path does not
expose a seed parameter. A provider accepting `store: false` does not by itself
prove that the provider retains no data.
Runner and provider configuration reject `reasoning_effort` or
`disable_response_storage=true` with Chat Completions so the recorded privacy/
reasoning policy cannot be silently omitted from the actual request.

Tests use fake clients to verify the API-call boundary without sending a paid
request. If no independent trusted oracle exists for an otherwise valid
project, L2 is recorded as `not_run` with `skip_reason=needs_oracle`; it is not
reported as either a semantic pass or a design failure.

### Retained Training-View Export（Outside Paper-1）

Paper-1 targets ACM TRETS and does not train models. Everything in this section
documents retained compatibility infrastructure; it is not a Paper-1 method,
gate, deliverable, or evidence source.

Training-view export is fail-closed for positive targets. Missing or negative
pass credit, VPP-L3, provenance, budget, or method-applicable artifact evidence
blocks positive project views; boundary `not_run` cases remain diagnostic, and
deterministic references are excluded from model training. A Direct project
without System-HIS can contribute only method-neutral eligible views. These are
export safeguards, not Paper-1 evidence and not proof that a release, training
run, or learned checkpoint exists.

The CD8 evaluator-owned eligibility builder now issues hash-bound
`training-eligibility-v1` certificates from the frozen episode pack, initial
project envelope, immutable terminal candidate, terminal envelope, training-
fold qualification, frozen source policy, and explicit evaluator evidence. It
does not consume Recorder success labels. A completed `pass` can be eligible;
`fail`, `not_run`, changed trusted-builder content, disallowed/reference source
classes, missing checks, or any official-hidden outcome reference produce an
auditable `ineligible` certificate. This is currently a tested library surface:
no Runner/CLI path yet produces the training-fold qualification evidence and
drives the complete eligibility-to-release chain.

The canonical Agent exporter now emits only registered `training-view-row-v2`
payloads plus a separate release-internal
`training-view-eligibility-sidecar-v1`. M6U is bound to the outcome-blind
initial snapshot; M6F is bound to the verified terminal snapshot; M6T requires
a complete public failure/diagnosis/non-empty patch/actual rerun/repaired/no-
regression transition; and `M6F_E_TRAJ` requires the same transition evidence
hash. Only editable model-owned RTL or byte-bound model regions become targets.
Trusted files, manifest/build metadata, hidden markers and configured canaries
are withheld. The writer validates the complete row/certificate/sidecar chain
before atomically creating a bundle and refuses every destination outside
`artifacts/`.

The evaluator-owned pool builder now produces registered
`training-pool-manifest-v1` candidate manifests. It fails the whole pool unless
M6U and M6F contain exactly the same E_final episode IDs, M6T and
`M6F_E_TRAJ` contain exactly the same E_traj IDs and transition hashes, E_traj
is an E_final subset, all certificates share one frozen policy/split, and the
family/source/failure-origin mixture partitions E_final exactly. Every row,
sidecar and eligibility certificate is reconciled again before acceptance.
Independent promotion verification remains unfinished non-Paper-1 work.

Candidate-release assembly is now implemented by the Agent-owned
`training-release-manifest-v1` builder. It serializes canonical per-treatment
JSONL plus release-internal pool, sidecar and deduplicated eligibility
certificates; inventories every byte with role, visibility, size and SHA-256;
rechecks the frozen leakage/canary policy; and atomically creates only an
`artifacts/` release directory. The resulting manifest is always
`candidate_unpromoted`, has `training_authorized=false`, contains zero official
hidden outcome references and cannot carry authorization. Its read-only
verifier rejects missing, extra, unreferenced, duplicate, checksum-drifted,
policy-mismatched or promoted content. Training-side promoted-release structural
inspection is implemented independently of Agent, but it only rechecks declared
hashes and artifact bindings. Signature authentication, independent promotion,
the signed training plan, and training-command authorization remain unfinished.

The candidate bundle currently contains rows, sidecars, certificates, and the
pool manifest, not the evaluator evidence bundle needed to independently
recompute every eligibility claim. Eligibility evidence is supplied to the
builder, and no production orchestrator connects qualification, export, pool,
candidate assembly, promotion, and training. These limits describe retained
infrastructure only even though each candidate-side structure has focused tests.

## Common Project Package

New model-generated Direct responses use the registered
`project-package-v1` manifest. The manifest declares build intent only:
project/top/interface, the complete RTL source set with language records,
conditional or advisory artifact roles, and tool/language metadata. Source
paths are safe manifest-relative paths and need not use `rtl/top.v`.

The common package requires `manifest.json` and its declared RTL sources. A
candidate testbench, System-HIS, timing constraint, board wrapper, or predicted
QoR file is present only when declared applicable. Historical unversioned
`top_module + sources` manifests remain a compatibility input; a new Direct
generation cannot silently downgrade to that form, and repair preserves the
input manifest generation.

Evaluation records two different checks:

- `common_project_l0` validates the method-neutral package for every method;
- `his_project_consistency` additionally validates HIS-to-project agreement
  only for methods that emit System-HIS.

A candidate testbench is an untrusted public smoke/debug artifact. Its compile
or run result is recorded separately and cannot produce semantic L2 credit.
Without an evaluator-trusted harness, formal L2 is `not_run`; synthesis can
still execute independently. With a configured development/excluded harness,
the evaluator compiles candidate manifest RTL plus trusted harness files under a
fixed top/language/timeout/pass rule and excludes the candidate testbench. The
registered `project-envelope-v1` outer
contract binds trusted ownership and project bytes, and the context-native M5
repair facade consumes its verified composite-region authority. The trusted-core
seal API verifies the exact project/envelope/event tuple, persists immutable
project blobs, and reconstructs the sealed project. Development/excluded Runner
terminal selection plus public/hidden dispatch now consume that seal as their
authority. The legacy Recorder and retained training release remain separate
compatibility views and cannot create official credit.

A separate development-only hidden-evaluator boundary now consumes the sealed
project from a physically separate evaluator store, permits one call per frozen
ledger tuple, and returns no status, score, diagnostic, private hash, or raw
output to generation/repair. It does not mint `official-hidden-outcome-v1`;
official execution remains locked until signed campaign authority and an
evaluator-owned CLI/process are implemented.

## External Tools

Current local tool execution uses:

- Verilator for lint.
- Icarus Verilog and `vvp` for candidate testbench smoke diagnostics only.
- Yosys for synthesis.

Formal L2 remains `not_run` until an evaluator-trusted harness channel is
implemented; a candidate smoke pass does not satisfy that requirement.

OpenXC7/nextpnr is optional for L4-open physical implementation. Vivado is an
optional commercial-reference flow. Tool discovery and missing-tool outcomes
are recorded separately from model failures.

Executable discovery checks `PATH` first. Additional machine-local tool bins
may be supplied through the platform path-list variable
`SR2FPGA_TOOL_FALLBACK_DIRS`; an OSS CAD Suite root may be supplied through
`SR2FPGA_OSS_CAD_SUITE_ROOT`. No machine-specific tool path is committed in
source.

## Tests

```powershell
python -m pytest agent/tests -q -p no:cacheprovider
python -m pytest contracts/tests agent/tests -q -p no:cacheprovider
```
