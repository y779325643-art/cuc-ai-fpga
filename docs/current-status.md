# SR2FPGA Current Status - 2026-08-30

## Current Checkout

- Branch reviewed: `codex/g3b-shared-checkpoints-cost-views`.
- G3b development baseline reviewed: `810240dd2910`.
- The implementation reviewed below is the local G3b branch candidate including
  the completed code/contract/test slices and this documentation synchronization.
  It is not a release, remote CI result, or statement about a published branch.
- Repository reorganization is complete. No dated reorganization plan is active.

The final local acceptance report is
[`reports/reorganization/final-verification.md`](../reports/reorganization/final-verification.md).
It records an `APPROVED` reorganization verdict, 1,059 passing tests plus 349
passing subtests, a 24/24 deterministic L3 smoke, and zero tracked `tmp/` paths.
The report preserves its original feature-branch verification scope; this
refreshed status supersedes its historical branch label for current navigation.
The latest completed full lightweight regression snapshot, completed on 2026-08-30
for the v1.7/v1.12 G3b branch candidate with a repository-external pytest
basetemp, reports 2,055 passing tests plus 435 passing subtests. The eight-file
focused G3b matrix separately reports 272 passing tests. These commands validate
the test-covered current branch code and contracts; link/readback and diff checks
cover the changed documentation separately. This is not remote CI, an official
gate signature or a model outcome. The increase from the historical
reorganization acceptance count reflects new Paper-1 contracts, trusted-core,
method, OASA, and candidate-release tests; it is implementation verification,
not a model, training, hidden-evaluation, or research outcome. This remains
local verification rather than remote CI/review evidence.

## Canonical Ownership

- `agent/`: generation, H0-H3 validation, L0-L4 verification, trusted oracles,
  repair, and trajectory production.
- `training/`: dataset conversion, SFT/LoRA, merge, and serving. Training does
  not import Agent.
- `contracts/`: versioned cross-project schemas and the canonical task catalog.
- `datasets/`: immutable versioned releases.
- `artifacts/`: ignored runtime output.
- `reports/`: intentionally committed evidence and human-readable audits.

The projects communicate through versioned files under `contracts/` and
`datasets/`, not Python imports across project boundaries.

## Current Research Authority

The canonical Paper-1 research question, matched M0-M5 baseline ladder, held-out
benchmark design, information privileges, metrics, and ordered experiment gates
are frozen in
[`2026-08-14-sr2fpga-paper1-research-program-freeze-design.md`](specs/2026-08-14-sr2fpga-paper1-research-program-freeze-design.md).
Its pre-outcome v1.7 amendment, effective 2026-08-27, targets ACM Transactions on
Reconfigurable Technology and Systems（TRETS）, keeps model training outside
Paper-1, retains RQ0 as a disjoint bounded audit, and treats representative
OpenXC7 L4 as secondary depth evidence. RQ1 now has a two-member primary Holm
family (`M4-M3`, `M4-M0`); `M3-M2` is a mandatory prespecified secondary
estimation contrast. The complete RQ1 claim uses gate-conditional joint power,
while each retained RQ2 contrast uses Holm-adjusted marginal power within its
separate Holm family. The v1.6 decoding-control rules remain in force: they
separate `replicate_id`, provider requested-seed provenance, and local execution-
schedule randomization, and require G4b to freeze either
`documented_seed_control` or `stochastic_blocked`. Target-profile adaptation
remains an optional separately frozen
extension, not a minimum G4b or submission gate. RQ3 and M6U/M6F/M6T/M6TR remain
withdrawn from the Paper-1 method and result matrix. This amendment changes no
implementation status or empirical result; execution remains blocked at G3.
Existing training code and contracts remain repository infrastructure only;
they neither block nor support Paper-1 claims.

Implementation work is governed by the subordinate
[`Paper-1 code architecture and development specification v1.13`](specs/2026-08-18-sr2fpga-paper1-code-architecture-development-spec.md).
It maps the frozen protocol to modules, interfaces, state machines, artifacts,
work packages, and acceptance tests; it neither changes the research estimand
nor turns target architecture into current capability or results.

Relevant rationale from earlier reframe, official-evaluation, and constrained-
decoding proposals is absorbed into the active freeze; the superseded files are
available through Git history, not as parallel authorities. Machine facts still
come from contracts, code/tests, the evidence ledger, and stable artifacts.

## Reorganization Status

| Phase | State | Current evidence |
| --- | --- | --- |
| B1 contracts and artifact boundaries | Complete | Contract registry, canonical task catalog, dataset manifests, policy tests |
| B2 standalone Agent project | Complete | Canonical Agent source/config/scripts/tests and 24/24 deterministic L3 smoke |
| B3 standalone Training project | Complete | Independent lightweight package, provenance checks, conversion and dry-run validation |
| B4 compatibility and cleanup | Complete | Compatibility suite, stable evidence promotion, zero tracked `tmp/`, final verification `APPROVED` |

The former B4 roadmap and cleanup plan were removed from the working tree. Do
not recover and rerun their historical commands; use the final verification and
current project guides instead.

The verified external Phase A backup remains a controlled recovery artifact.
Do not delete it until the published `develop` commit and remote integration
state have been independently verified; equality with the locally known
`origin/develop` ref is not, by itself, remote-CI or review evidence.

## Current Verified Capability

- Versioned System-HIS v1.2, backend-capability, requirement-audit,
  project-package, project-envelope, terminal-candidate, official-hidden-
  outcome, training-qualification-outcome, trajectory, training-view, and
  task-catalog contracts exist.
- Runtime H0 now executes the manifest-registered System-HIS Draft 2020-12
  JSON Schema, while H2 consumes the separately registered backend capability
  profile instead of maintaining private allowlists.
- The Agent supports the two-stage `REQ2HIS -> HIS2PROJECT` path, deterministic
  and LLM-backed multi-file project generation, and H0-H3 result recording.
- The model-backed two-stage path can repair failures at any H0-H3 stage with a
  dedicated System-HIS repairer, revalidate the repaired contract, and rebuild
  the complete project before the separate project/RTL repair path.
- H1 additionally requires every declared top clock/reset to exist in
  `top.ports`, and treats top/component parameter declarations as objects with
  non-empty string names. The registered System-HIS v1.2 Schema remains
  unchanged; malformed strings are rejected at H1 rather than normalized.
- Deterministic skeleton generation runs a static HIS/project consistency
  preflight before HIS2PROJECT. Canonical constraint and predicted-QoR paths are
  deterministic-lowerer layout invariants shared by the builder, H2 and prompt,
  rather than undeclared backend-capability fields.
- Direct M0/M1 projects no longer require `system_his.json`: H0-H3 are recorded
  as `not_applicable`, while the same method-neutral L0-L4 project path remains
  applicable. Focused tests cover Direct common-L0/lint/synthesis execution,
  L0 failure, repair, generation failure, and stop-before-generation
  requirement decisions; a candidate-owned testbench is not counted as L2.
- New model-generated Direct packages must use the registered
  `project-package-v1` manifest. It declares the top source/interface, complete
  RTL source set, build intent, and conditional/advisory artifacts by role.
  Historical unversioned manifests remain readable only through the legacy
  compatibility path. Common L0 no longer fixes the top path at `rtl/top.v` or
  universally requires a candidate testbench, QoR prediction, or timing file;
  the separate HIS/project consistency check runs only for HIS-emitting methods.
- A candidate-owned testbench can produce public smoke diagnostics, but it does
  not create semantic L2 credit. Without an evaluator-trusted harness, L2 stays
  `not_run` with an explicit reason while independent synthesis may still run.
- Trusted black-box testbenches, protocol/numeric/image/RL oracles, independent
  Python references, mutation qualification, and oracle-edit protections exist.
- The default scalable development path executes common L0, L1 lint,
  candidate-owned smoke simulation when declared, and independent L3
  synthesis. Formal L2 is currently `not_run` because the evaluator-trusted
  harness channel is still a G3 deliverable.
- Request handling has no request-mode switch. Every CLI/Runner sample now
  receives the same deterministic, evaluator-side requirement boundary before
  deterministic-reference, Direct, or System-HIS generation. It preserves the
  Requirement Envelope and route projection, does not coerce unknown tasks to a
  nearest family, and stops `needs_clarification` or `capability_gap` before the
  project generator. The boundary decision is persisted in sample/preflight/
  freeze metadata; only a ready two-stage path proceeds to the configured real
  REQ2HIS API and generic H3.
- The registered Draft 2020-12 `ambiguity-case-manifest-v1`,
  `requirement-audit-v1`, and `ambiguity-audit-events-v1` schemas now support a
  separate evaluator-side Phase A runner, while `clarification-replay-v1`
  records Phase B. The runner validates
  the sealed input hash, gives requirement intake only the public projection,
  executes one precommitted answer only after an actual
  `needs_clarification`, and persists a lineage-bound one-shot marker that
  rejects a second replay. Its event interceptor records Phase A boundaries and
  downstream attempts before callback execution; the event artifact is bound to
  the sealed manifest and exact Phase A hash, while any escaped attempt is
  reported separately as a generation-boundary violation.
  `ambiguity-outcome-v1` reduces named repeated
  observations without inflating base-cluster `n`, keeps `not_run` outside
  semantic confusion, separates the two ready strata, and makes any
  false-proceed observation fail cluster primary safety.
  `ambiguity-witness-v1` binds two annotation commitments, adjudication,
  material-interpretation commitments, gold provenance IDs, and a private
  canary; the reducer reports critical-fact/capability/permitted-default/
  explicit-assumption precision and recall and fails on canary exposure.
  It also derives repeated-known-fact question rate from Phase A provenance and
  unknown-family coercion from private, pre-adjudicated ready-counterexample
  labels rather than post-hoc requirement text classification. Counterfactual
  consistency is computed only for a completed within-observation quartet with
  exactly one case from each frozen stratum; it requires all dispositions and
  the precommitted clarification replay to agree. Phase A event counters are
  reconciled against the Phase A artifact, replay counters are added, and the
  outcome reports model/tool calls, tokens, wall time, and infrastructure status
  while retaining `not_run` cost.
  Neither phase dispatches M0-M5. This is a tested development execution path,
  not a signed or official ambiguity audit.
- Per-sample logical model calls now share one ceiling and emit stage/status/
  duration records across generation and repair. CLI/Runner-created internal
  generators and repairers use one internal attempt; outer project/System-HIS
  repair remains explicit and consumes the same ledger.
- When no independent trusted test oracle exists, public L2 is recorded as
  `not_run` with `skip_reason=needs_oracle`; synthesis may still run, but the
  candidate receives no semantic L2 pass credit.
- Development/excluded tasks may now name a registered, evaluator-owned trusted
  public L2 harness manifest. The loader validates its schema, confined relative
  paths, file hashes, fixed top/language/timeout/pass rule, and manifest/bundle
  commitments before execution. This does not create an official oracle.
- The earlier final 24-sample deterministic smoke reached L0-L3 for 24/24
  samples. Under the H3 semantics recorded by that run, H3 reported 14 pass, 10
  not-applicable, and 0 fail; not-applicable is not counted as a pass, and the
  historical artifact is not retroactively reinterpreted by the unified path.
- Stable evidence retains OpenXC7 post-route L4 passes for two representative
  families: FIR filter and matrix-vector MAC.
- Training can consume versioned views, prepare chat data, and perform no-model
  dry-run validation independently of Agent. Agent positive-view export now
  fails closed unless pass/VPP, provenance, budget, and method-applicable
  artifact evidence are explicit; boundary non-runs and deterministic references
  cannot silently become positive model-training targets.
- The manifest now quarantines `training-view-row-v1` under a legacy registry
  key and registers closed `training-view-row-v2` as canonical. Training has an
  Agent-independent v2 JSONL reader that validates Schema, canonical row hashes,
  duplicate IDs, treatment/target shape, hidden/audit canaries, and the stricter
  M6U outcome-blind denylist before rendering only the model-visible payload.
  This is candidate-release input validation, not an `E_final`/`E_traj` release.

These statements have important boundaries:

- Runtime H0 executes the canonical JSON Schema. H1 now emits independently
  attributable W1-W10 `pass`/`fail`/`not_applicable` results, with a registered
  stage/applicability matrix and positive/negative rule fixtures. All 34
  deterministic System-HIS writers have no failed W rule. Their RTL-derived
  declarations exercise W3 on the 27 projects with actual inter-component
  connections; the seven single-module projects remain explicitly
  `not_applicable`. W5 is exercised and passes on all 34 projects. These are
  contract-conformance results, not functional-correctness evidence.
- Generic H3 verifies Requirement Envelope facts, trace identity, and the values
  at resolvable fact-specific System-HIS mappings for System-HIS-emitting paths.
  That is stronger than the old unknown-family `not_applicable` fallback, but it
  is not proof of arbitrary open-ended requirement correctness or a substitute
  for an independent functional oracle.
- Family Recipe prompt guidance is now selected automatically only from an
  exact catalog/runtime identifier or a registered whole-phrase trigger.
  Unknown names, owner conflicts, families without registered recipe content,
  and the catalog-backed candidate primary held-out deny set all use the generic
  prompt. For a two-stage System-HIS request, the complete decision records
  recipe identity/version/hash or its fallback reason plus the deny-policy
  identity/version/hash/status and catalog version, but remains evaluator-side
  sample/preflight/freeze metadata: it is not inserted into the REQ2HIS prompt,
  generated System-HIS, or HIS2PROJECT input. Only an `applied` decision adds
  the recipe body to the REQ2HIS prompt. Direct-project and deterministic-
  reference methods do not record this decision. Recipe content is a generation-
  information privilege, not a request mode.
- The recipe deny set contains the four candidate G4a primary held-out families
  named by the active freeze and is marked `candidate_g4a_not_signed`. No signed
  G4b split manifest currently exists, so this conservative runtime guard must
  not be described as the final frozen campaign split.
- OpenXC7 evidence is representative post-route evidence, not a general L4
  dataset and not a `.bit` or board-validation claim.
- Vivado commercial-reference success and L5 board validation remain at zero.
- Training infrastructure exists, but no unified learned SR2FPGA model result,
  held-out-family gain, or QoR-prediction result has been established.
- Tier-B logit-masked constrained decoding remains design-only.
- The retained independent-oracle path is diagnostic, not the hidden authority:
  it can still execute through candidate-stage plumbing and cannot create formal
  hidden/randomized/stress pass fields. The separate terminal hidden boundary is
  now one-shot and evaluator-owned and returns only an opaque reference to the
  Runner. A second reducer-only artifact publishes sanitized development
  `pass/fail/not_run` without exposing hidden data to generation or repair.
- A separate development-only hidden-evaluator authority consumes a verified
  `terminal-candidate-v1`, uses physically separate candidate/evaluator stores,
  and returns only an opaque development outcome ID. The intended one-shot key
  binds episode/method/seed/candidate/commitment, but current Runner pairing still
  substitutes `family_id`/`task_type` for `semantic_instance_id` and hard-codes
  pairing seed `0`; the Agent compatibility wrapper can also catch a hidden
  exception and return `None` without a sanitized two-axis closure artifact.
  Raw private material remains evaluator-side, but v1.6 replicate/schedule and missingness closure
  is not implemented. This is non-official boundary infrastructure: no signed
  G4b authority or official outcome producer exists.
- The development/excluded Runner now invokes an evaluator-owned public
  authority for every immutable attempt and again for the selected terminal.
  Each attempt is sealed before evaluation; an envelope-invalid attempt uses a
  non-crediting v2 seal so L0 diagnostics remain evaluator-owned. Sanitized
  public diagnostics are the only public-tool input to project repair. The
  registered `AT_A` reducer selects the earliest public acceptance, otherwise
  the last complete candidate at budget exhaustion; `@1` selects its single
  complete candidate. The selected attempt outcome and selection record are
  embedded as public evidence in the terminal seal.
- The terminal public authority consumes that exact verified terminal seal
  through physically separate candidate/evaluator stores,
  reconstructs the project in an evaluator-owned workspace, runs method-neutral
  common L0/L1/L3 and ignores candidate-owned testbenches. When a validated
  evaluator-owned harness is configured, it compiles only candidate manifest RTL
  plus trusted harness files and can produce development-only public L2
  `pass/fail`; otherwise L2 remains `not_run(needs_oracle)`. Its registered
  outcome exposes only sanitized
  status/reason codes; raw logs, paths and exceptions remain evaluator-private.
  It is one-shot and explicitly cannot drive repair or official outcomes. It
  must agree with the selected-attempt public stages before hidden dispatch.
  Development pass credit comes only from the selected authoritative attempt
  outcome, requires the same harness commitment at terminal reevaluation, and
  remains false when public L2 is `not_run`; official VPP remains unavailable.
- `public-evaluation-candidate-v1` now freezes one
  attempt with exact attempt/method/episode identity, full project-envelope and
  creation-event artifact references, and immutable project blobs. Its matching
  authoritative development attempt evaluator is physically store-separated,
  one-shot and raw-output-sanitized. A v2 seal preserves envelope-invalid
  attempts for evaluator-owned L0 diagnosis but can never be a complete terminal.
  This authority is restricted to `development`/`excluded`, sets
  `official_outcome=false`, and does not authorize G4b.
- `project-envelope-v1` has fail-closed whole-file and composite trusted builders.
  Composite skeleton RTL regions are derived from actual UTF-8 byte ranges,
  hashed, bound to the registered method-policy digest and content-verified
  append-only events, and rechecked against behavior markers. The context-native
  M5 repair facade now requires that verified envelope before a model call. The
  trusted-core seal API now verifies the exact terminal project against that
  envelope, validates the creation event and episode, stores every project file
  as an immutable content-addressed blob, and reconstructs the candidate from
  the seal. The development Runner maps every attempt into this authority when
  the project package is canonical: M0-M3 become
  immutable model-owned snapshots, while M4/M5 preserve composite trusted-
  skeleton/model-behavior ownership. Terminal selection is now derived from
  registered evaluator outcomes. Signed
  official evaluator commitments and campaign authority remain absent.
- The first CD3 trusted-core slice is implemented: `episode-pack-v1` is
  registered; ready development M0-M5 metadata can carry a frozen,
  method-neutral public requirement projection plus audit-only commitments;
  Agent intake validates its schema and hashes before generation. A local
  content-addressed write-once store now supplies verified reads, append-only
  events, minimal fail-closed budget reservations, byte-verified immutable
  candidate seals, sealed-project reconstruction, and one-shot consumption
  markers. The development builder explicitly refuses to
  mint unsigned official packs.
- The common requirement boundary is deterministic policy, not proof of open-
  world requirement understanding. The OASA sealed-manifest loader and Phase
  A/B runner exist, including stateful exactly-one replay and a raw
  cluster-aware reducer plus witness/adjudication commitments, but signed
  fixtures, a registered exact interval/threshold implementation, and official
  RQ0 outcomes do not. The active-freeze scientific thresholds are protocol targets, not
  current runtime evidence.
- A closed M0-M5 method-contract vocabulary now records representation,
  declared model stages, H applicability, skeleton policy, visibility, and
  repair privileges. A provider-neutral adapter registry and closed generation
  facades now implement the M0-M5 core, including explicit M2 untyped-plan and
  M3 free-from-HIS emissions. Complete excluded G3b blocks eagerly materialize
  and verified-read the method-neutral S_D Direct project, S_H System-HIS and S_P
  complete behavior-filled project before method execution. M0/M1 consume S_D,
  M3/M4/M5 consume S_H as applicable, and M4/M5 consume the identical complete
  S_P ArtifactRef. Partial, legacy and other non-G3b paths retain bounded
  compatibility behavior and receive no G3b/G3 credit. Unauthorized repair is
  rejected before the repair facade.
  Explicit development Runner dispatch now binds M2, M3, M4 and M5 to this
  authority. M2 performs a frozen-context untyped-plan call followed by a
  canonical free-project call without H stages or a skeleton. M5 pre-candidate
  execution uses the same executor with one bounded complete-H correction.
  M5 project repair and remaining implicit compatibility paths are not yet
  unified, so source/model/method decoupling is still incomplete.
- A separate pre-candidate `EpisodeExecutor` now records legal method/planning/
  H-validation/H-correction/candidate transitions. It prevents M3/M4 H repair,
  bounds M5 HIS correction, reruns the complete H validator after correction,
  and cannot lower a System-HIS project until H passes. M2 bypasses H by its
  closed contract. The executor now owns explicit M2-M5 pre-candidate Runner
  generation, but not public evaluation, terminal selection, hidden evaluation,
  or the remaining legacy dispatch paths.
- Development CLI/Runner M0/M1 dispatch now binds the real Direct client to the
  validated frozen public context. Its prompt does not serialize evaluator
  `task_type`, family ID, private project name, or the caller's platform object;
  canonical project-package parsing remains mandatory. Missing or tampered
  M0/M1 episode packs fail before generation. Programmatic legacy
  `DirectProjectGenerator` remains a compatibility API, not the Paper-1
  dispatch path. A context-native M2 facade now emits a plain untyped planning
  artifact and then a complete canonical project from only that plan plus the
  frozen public context. Separate context-native M3-M5 initial System-HIS facades now
  perform one frozen-context REQ2HIS call and complete H0-H3 validation; H
  failure prevents HIS2PROJECT. M3 directly generates a full canonical project
  without invoking skeleton or behavior-fill code, while M4/M5 lower through a
  deterministic skeleton. Paired M3/M4 tests consume the same materialized HIS
  SHA-256 after one REQ2HIS call. Explicit M2-M5 samples now use the method
  adapters and executor; paired M3/M4 samples in one development Runner batch
  use the coordinator, produce distinct
  method-artifact references, and fail closed on unknown conditions. This does
  not provide public/terminal/hidden campaign authority. M5 HIS correction now
  consumes only frozen public context plus the
  failed H stage and public diagnostics, makes one budgeted call, and must pass
  a complete outer H0-H3 rerun before lowering. M4 cannot invoke this facade.
  An opt-in, formally non-conformant development variant can additionally repair
  rejected HIS2PROJECT behavior output under the same pre-candidate ceiling.
  Raw responses are immutable text artifacts; byte-identical repair output
  consumes its call and stops as `NoProgress` with parent/produced lineage.
  One real Runner `run_batch` test now executes an excluded, fake-provider M0-M5
  pack from the same frozen projection. When an episode pack is present, the
  Agent's downstream H validation reuses that frozen public context rather than
  reconstructing evaluator-side `task_type` facts; this removes the earlier
  pre-candidate-pass/legacy-H3-fail inconsistency. Every completion carries its
  episode pack, method artifacts, canonical trajectory, costs, terminal seal and
  opaque development-hidden lineage. This is an engineering integration test,
  not a provider campaign or result.
  A first context-native M5 project-repair facade now exposes only manifest,
  frozen HIS, editable RTL and public diagnostics; trusted testbench/constraint/
  report contents are withheld, and only byte-bound composite behavior-region
  edits survive envelope, package, edit-surface and HIS/RTL revalidation. It is
  still a development facade, not campaign authority: its M5 repair invocation
  remains on a compatibility path. Every returned attempt nevertheless enters
  the common evaluator-owned public and terminal authority; selection and
  dispatch are intentionally outside the repair facade.
- A Runner-level repair engineering smoke now covers a controlled
  `synthetic_injected` undefined-signal failure through diagnosis, one budgeted
  fake-provider repair call, rerun, and regression accounting. A valid patch can
  be patch-creditable, but the episode receives no automatic pass credit unless
  it also has a complete authoritative terminal and public acceptance. A paired
  rejection episode attempts to edit the trusted candidate
  testbench, records `touched_trusted_artifacts=true`, stops without a repair
  transition, and receives no automatic pass credit. This is ignored-artifact
  engineering evidence only; no natural model failures were selected or run,
  and it is not RQ2 evidence. The B2 natural-failure pilot now has a review-only
  preregistration plan covering evaluator-owned frozen selection, paired repair,
  missingness, denominators, and the required G5 review packet; sample count,
  provider/model, authorization, and execution remain deliberately unset.
- Legacy Recorder trajectory export is not demonstrated to validate against
  `trajectory-v1` and remains a non-canonical compatibility view. A separate
  registered, write-once `trajectory-v2` is now rebuilt from verified attempt
  events and cost summaries for M0-M5 Runner attempts. For
  `development`/`excluded`, it re-verifies the registered `@1`/`AT_A` selection,
  selected authoritative attempt outcome, exact terminal seal, terminal-public
  reevaluation and optional opaque hidden reference. The selected complete
  terminal may precede a later incomplete attempt; noncanonical output, missing
  identity or unavailable composite ownership remains explicit incomplete
  lineage. Registered development public-evaluation, episode-outcome and full-
  pack-outcome reducers project terminal-authority stages, rebuild repair facts,
  reconcile raw-event costs and retain missingness without replacement. Public
  L2 can now be scoreable for a configured trusted development harness, and a
  reducer-only hidden conformance artifact can produce a separate development
  VPP. The scripted M0-M5 fixture yields 6/6 development VPP pass while official
  VPP remains `not_evaluated`. For a fully reconciled excluded terminal
  projection, Runner now emits the registered episode-outcome reference only
  after rebuilding it from the public projection, trajectory, raw cost events
  and hidden lineage; an incomplete repair projection receives no such closed
  outcome. Four excluded M4 Runner fixtures now bind H0-H3 failures to the
  frozen episode pack, committed platform/backend capability profiles, planning
  artifact, complete ordered trusted-event stream and raw cost trajectory. Each
  stops before project emission and derives development VPP false; digest,
  capability, ordering, post-stop event, cross-episode and physical-blob
  tampering fail closed. A separate
  set of four excluded M5 Runner fixtures now binds initial H0-H3 failures to
  one correction, a complete H0-H3 rerun, corrected candidate/terminal lineage
  and raw-event costs. The registered correction outcome requires distinct
  initial/corrected HIS refs, exact ordered method events, one each of
  `req2his`/`system_his_repair`/`his2project`, zero project repair, and keeps all
  official/pass-credit/RQ/G3/G4b flags false. A separate
  repair-capable M1 Runner fixture reaches public
  L0/L1/L2/L3, receives one hidden fail, performs no repair, and derives
  development VPP false while official VPP remains unavailable. The
  same terminal seal is the only candidate consumed by terminal public and
  development hidden authorities, without exposing hidden status, score or
  private content to generation or repair. The
  canonical v2 Training reader and evaluator-owned `training-eligibility-v1`
  certificate builder are tested: eligibility is hash-bound to the frozen
  episode, initial/terminal envelopes, terminal candidate, training-fold
  qualification, source policy, and evaluator checks; `fail`, `not_run`,
  trusted-surface changes, reference sources, and official-hidden references
  are ineligible. The canonical Agent v2 exporter and registered eligibility
  sidecar are also tested: M6U uses the initial snapshot, M6F uses the terminal
  snapshot, M6T and `M6F_E_TRAJ` bind complete matching public-transition
  evidence, and only model-owned editable RTL/regions enter the payload. Its
  atomic writer is restricted to `artifacts/`. Registered
  `training-pool-manifest-v1` now builds E_final/E_traj candidate pools: M6U/M6F
  sets must match, M6T/`M6F_E_TRAJ` sets and transition hashes must match,
  E_traj must be an E_final subset, mixture strata must partition E_final, and
  every artifact is reconciled against one policy/split. Candidate-release
  assembly is now implemented under `artifacts/`: the registered public
  checksum manifest distinguishes unpromoted candidates from promoted
  releases, inventories every view/internal artifact, rechecks leakage policy
  and fails on missing/extra/unreferenced/checksum-drifted content. Agent emits
  only `training_authorized=false`. Training now independently inspects only a
  promoted shape whose campaign-freeze/training-plan/promotion-record hashes
  and leakage policy match caller-supplied expectations, and redoes inventory,
  pool, row, sidecar, certificate and snapshot reconciliation without importing
  Agent. This inspector is not an authorization verifier and cannot start
  training; independent promotion verification remains non-Paper-1 work.
- The CD8 components above are library/test surfaces, not an operational
  release command chain. No current Runner or CLI produces a real evaluator-
  owned `training-qualification-outcome-v1`, drives qualification through pool
  and candidate assembly, or invokes the Training inspector before a model run.
  Eligibility checks are currently built from caller-supplied evaluator-evidence
  assertions, and the candidate bundle carries the resulting certificates and
  hashes rather than the underlying evidence bundle needed to recompute every
  claim independently.
- The exposed `train_lora` command remains an ungated manual utility: it accepts
  an arbitrary YAML `train_file`, does not consume a promoted release or signed
  training plan, and loads model/tokenizer code with `trust_remote_code=True`.
  `merge_lora` has the same remote-code default. Neither command is a Paper-1
  entry, and Paper-1 does not run either command.
- The model-call ledger counts logical calls, including failures. The built-in
  OpenAI- and Anthropic-compatible providers now expose the exact per-call
  transport-attempt count, including transient retries, to the raw cost stream;
  uninstrumented custom clients are marked
  `provider_transport_attempt_count_unavailable` instead of being miscounted as
  one attempt. Built-in provider responses now retain explicit input/output/cache
  usage when supplied, for both non-streaming JSON and streaming OpenAI-compatible
  usage chunks or Anthropic message usage events. Streaming failure paths publish
  usage already observed before an error; internal retries accumulate every
  observed attempt, while any unobserved attempt keeps the affected logical-call
  axis unavailable. Each absent or invalid field and uninstrumented custom-client
  usage stays `provider_token_usage_unavailable` rather than being estimated.
  A registered `model-gateway-provenance-v1` artifact now separates requested
  seed, actual adapter forwarding, provider seed-control support, and provider
  system fingerprint. OpenAI-compatible Chat Completions calls forward the
  frozen non-negative seed but remain `requested_unverified` unless a separate
  hash-bound capability artifact proves deterministic support. OpenAI-compatible
  Responses calls and Anthropic-compatible calls record
  `not_forwarded/unsupported`. `wire_api`, `reasoning_effort`, response-storage
  policy and `max_tokens` now enter the measurement freeze and paired model-
  provenance identity; Responses cannot use seed-capability v1 to pass the
  strict paired-confirmatory guard. Runner persists this provenance for completed and
  failed development/excluded model calls with official, pass-credit, G3, and
  G4b authority fixed false. A registered
  `development-provider-seed-capability-v1` contract and bounded probe now bind
  the complete fixed protocol, documentation snapshot/source/review provenance,
  and ordered per-call observations. The loader recomputes counts, status,
  output/fingerprint conclusions, token totals, classification, limitations,
  profile ID and eligibility from those raw fields, so aggregate-field tampering
  fails closed. Runner can require an eligible,
  exact provider/model/gateway profile before creating a run directory; stored
  config/freeze records retain only the profile ID, content hash,
  classification and eligibility bit, not the local manifest path. A bounded
  real DeepSeek diagnostic on 2026-08-26 produced three matching non-empty
  outputs and fingerprints under seed 17, but remains `unverified` because the
  provider page does not document deterministic seed control and the CLI review
  is only `self_reviewed_development`. The
  OpenAI snapshot documents only best-effort behavior and its live probe stopped
  with a sanitized `authentication` infrastructure error. Both profiles are
  paired-confirmatory ineligible; neither is a campaign, determinism proof, G3
  acceptance artifact or research outcome. An initial 32-token DeepSeek
  diagnostic exposed empty-output false matching; the probe now rejects empty
  responses and the final analytical protocol uses 128 output tokens. Missing
  or inconsistent fingerprints are fail-closed as
  `backend_identity_unverified`, not mislabeled output nonrepeatability.
  Complete coverage for all possible custom/provider responses remains open.
- G3b development conformance is implemented and verified in offline fake-
  provider fixtures; G3 is not accepted. Complete excluded blocks eagerly create
  the method-neutral S_D Direct project, S_H System-HIS and S_P complete behavior-
  filled project after measurement freeze and before method execution, then
  content-verify all three. M4/M5 use the identical complete initial S_P
  ArtifactRef; their terminal candidates may diverge only through legitimate
  repair. Strict verification is anchored to an independently supplied,
  fingerprint-verified preparation policy and recomputes exact paired identity,
  keys, graph, consumers, contents, event chain and close totals. Two method
  orders each use six physical initial calls while standalone attribution
  contains ten. A registered reducer reconstructs actual, six standalone-
  attributed and three checkpoint-specific incremental views across all 13 axes
  from raw preparation events, six method trajectories and full-pack-v2 lineage.
  Count axes remain integers, duration axes remain numeric, and unavailable
  values retain reasons rather than becoming zero. Shared preparation is counted
  once physically and never charged to execution ordinal zero. Ordinary failed
  or `not_run` methods preserve valid trajectory/event/cost lineage in incomplete
  companions; checkpoint-blocked methods have null trajectories and closed
  measured-zero exclusive cost. Clean interrupted runs resume every frozen
  completed-method prefix `k=0..6` without repeated preparation calls, events or
  charges. Inconsistent, partial-next-method, corrupt, incomplete-manifest or
  legacy-in-place state requires a new run ID. Supported standalone model-call
  ceiling overrides remain valid; malformed policies fail before preparation
  effects. Legacy readers remain compatible without G3b/G3 credit. These tests
  produced no real-model, training, official held-out, evidence-promotion or
  paper outcome and do not establish external cryptographic immutability; all
  official/pass-credit/RQ/G3/G4b fields remain false.
- A bounded real DeepSeek R9 diagnostic on 2026-08-28 used the opt-in
  `m5-his2project-output-repair-dev-v1` variant and is explicitly
  `formal_method_conformant=false`. Its corrected HIS passed generic H0-H3 and
  emitted an L1/lint/synthesis-clean candidate, while official public L2 stayed
  `not_run(needs_oracle)` and the separate family-specific fidelity audit failed
  the prescribed interface/topology obligations. An unregistered evaluator-side
  black-box replay passed, but the run remains ignored and excluded. It is not
  promotable into official/G3/G5/VPP/RQ authority, is not formal M5 evidence,
  and has no revision/prompt-hash authority; a controlled development archive
  would remain a separate explicit operation.
- Outside Paper-1, positive candidate-pool eligibility is fail-closed at both export and the new
  candidate eligibility-certificate boundary, but no signed `E_final` or `E_traj`
  release, matched M6U/M6F/M6T training campaign, checkpoint, or learned result
  has been produced.
- Among the four candidate primary held-out families, only `matched_filter` and
  `sobel_threshold` currently have qualified independent-oracle evidence.

## Task Contract And Evidence

The machine-authoritative target catalog is
[`contracts/task-catalog/sr2fpga-task-catalog-v0.2.json`](../contracts/task-catalog/sr2fpga-task-catalog-v0.2.json),
registered by [`contracts/manifest.json`](../contracts/manifest.json). There is
no compatibility copy under `docs/`.

The [v0.1 evidence ledger](../reports/evidence/task-ledger/sr2fpga-task-evidence-v0.1.json)
records executable and verified facts; the generated
[status document](../reports/evidence/task-ledger/sr2fpga-task-evidence-status.md)
is its human-readable view. Direct parsing of the current ledger gives:

| Evidence measure | Current verified count |
| --- | ---: |
| Evidence ledger coverage | 71/71 |
| Implemented families | 31 |
| L3-or-higher families | 31 |
| Paper 1 core implemented | 14/14 (denominator: v0.2 catalog `recommended_sets.paper1_core`) |
| Paper 1 core executable / L3 | 14/14 |
| Paper 1 core mutation-qualified | 14/14 |
| Mutation-qualified families | 21 |
| Independent Python oracle qualified | 9 |
| OpenXC7 L4 pass | 2 |
| Vivado commercial-reference L4 pass | 0 |
| L5 pass | 0 |

These counts were recomputed from the current ledger. G2 is locally closed on
this checkout: catalog v0.2.2 corrects `clock_divider`, records T7 as T3, and
aligns L3 with the runtime `Yosys synth -top` plus `stat` stage. The ledger now
uses stable run artifacts instead of this status page as evidence, records
multi-alias evidence per sample (T3 and T11 have L3 smoke evidence but no
mutation/oracle qualification), and binds
the two bounded L4-open claims to measured-QoR and raw-tool artifacts by SHA-256.
The generated status page is still a derived view, not a newly frozen evidence
release or a new model result.

## Phase C And Phase D Evidence

Phase C independent-oracle closure is complete:

- 9/9 families completed through L3;
- 9/9 independent Python oracle passes;
- 45/45 scoreable mutations killed;
- 0 local evidence-audit issues.

See the bounded
[`Phase C independent-oracle report`](../reports/evidence/phase-reports/sr2fpga-phase-c-independent-oracle-evidence-2026-07-14.md).

The frozen Phase D pilot is also complete and independently audited, but its
`APPROVED` verdict concerns protocol and artifact integrity, not model quality:

- 24/24 live episodes completed;
- 12 generation failures and 12 H2 failures;
- 0/24 reached L0, L1, L2, or L3;
- 0 repair attempts and 0 repair successes;
- no live OpenXC7 or Vivado result.

Consequently, Phase D does not measure repair effectiveness or demonstrate LLM
L0-L4 performance. See the
[`Phase D pilot report`](../reports/evidence/phase-reports/2026-07-17-sr2fpga-phase-d-pilot-report.md) and
[`H2 hardening analysis`](../reports/evidence/phase-reports/2026-07-17-sr2fpga-phase-d-failure-analysis-and-h2-hardening.md).

## Paper-1 Implementation Audit

This is the 2026-08-30 G3b code-facing work-package assessment. `implemented`
means the named bounded behavior has focused tests; it does not imply an
official gate signature or research result.

| Work package | Current state | Verified local surface | Blocking remainder |
| --- | --- | --- | --- |
| CD1 / G1 common project and System-HIS closure | `implemented`; G1 locally closed | Canonical project package/envelope, H0-H3 applicability, W1-W10 and deterministic-writer conformance | No remaining G1 conformance blocker; this is not functional proof |
| CD2 / G2 catalog, evidence and stage semantics | `implemented`; G2 locally closed | Catalog v0.2.2, corrected aliases/stages, ledger-backed evidence and L4 hash provenance | Preserve historical-artifact migration/exclusion decisions at G4b |
| CD3 frozen context and trusted core | `partial` | Episode packs, manifest resolver, write-once store, append-only events, budget reservations, per-attempt candidate seals, registered terminal selection, terminal seal/reconstruction and one-shot primitives are consumed by development/excluded Runner authority | Legacy Recorder remains a compatibility view; no signed official pack loader, evaluator commitment loader, or official command gate exists |
| CD4 first-class M0-M5 adapters | `partial` | Closed method contracts, provider-neutral adapters, explicit M2-M5 development Runner pre-candidate dispatch, M2 untyped-plan/no-H/no-skeleton path, M3 no-skeleton path, M5 bounded H correction, paired artifacts and executor; downstream public diagnosis now comes from the evaluator-owned development authority | M5 project repair facade ownership and remaining implicit compatibility paths are not fully unified; official method dispatch remains locked |
| CD5 public/hidden/L4 and optional profile-adaptation separation | `partial` | Development/excluded Runner seals every attempt, uses evaluator-owned sanitized repair diagnostics, selects `@1`/`AT_A`, reruns the exact terminal, and dispatches the same seal to one-shot hidden evaluation. A registered hash-bound trusted harness can produce development-only public L2; a reducer-only hidden outcome can publish sanitized development `pass/fail/not_run`; neither grants official credit. Pilot target-profile contracts remain non-official optional-extension prototypes | No official hidden/VPP producer, two-axis hidden missingness closure, signed G4b authority, or official outcome producer. Profile-compliance/pair/`TPA-L4` authority is additionally required only if the optional extension is enabled |
| CD6 budgets, events and reducers | `partial`; G3b development accounting implemented | Shared logical-call ceiling; registered closed attempt/cost contracts; write-once ledgers verify hashes, sequence, lineage, close, totals and unavailable reasons. M0-M5 development/excluded attempts account evaluator-owned public tool calls, including trusted-L2 compile/sim when configured. G3b adds a method-neutral block-preparation ledger and verified cost companion: clean fake blocks reconcile 6 physical versus 10 standalone-attributed initial calls and all 13 actual/standalone/three incremental axes without charging shared work to ordinal zero. `trajectory-v2` continues to bind method-exclusive selection, terminal and hidden lineage. Failure, unavailable-axis, resume and cost tamper paths fail closed; legacy/partial inputs remain readable without G3b/G3 credit | No authorized real L4-version snapshot has been produced on this checkout; official hidden/VPP production and positive G3 acceptance remain incomplete. Official full-pack VPP remains `not_evaluated` |
| CD7 OASA replay runner | `partial` | Sealed loader, Phase A/B, exactly-one replay, event interception, witness and cluster-aware reducer | No signed fixture population, frozen interval/threshold implementation or official RQ0 execution |
| CD8 retained training release | `out of Paper-1 scope` | Eligibility certificate, v2 exporter/reader, matched E_final/E_traj candidate pools, artifacts-only unpromoted bundle, Training-side structural inspector | No Paper-1 deliverable; retain compatibility tests only |
| CD9 G3 full-pack and G4a/G5 support | `partial`; G3a and G3b implemented, G3 not accepted | G3a's registered non-authoritative `paired-block-v1` binds the exact six-member semantic/replicate block, common effective model/gateway and decoding provenance, independent schedule seed and Williams row through freeze, events, trajectories and full-pack v2. G3b eagerly materializes and verifies S_D/S_H/S_P before method execution; M4/M5 consume the identical complete initial project. Three registered development contracts bind the method-neutral preparation chain, checkpoint DAG and artifact-derived cost companion. Two fake-provider orders preserve six physical and ten standalone-attributed initial calls, method-keyed 13-axis actual/standalone/three incremental views, visibility boundaries and fail-closed failure/missingness/resume/tamper behavior. Partial/legacy readers remain compatible without G3b/G3 credit. Existing repair/H-stage/hidden fixtures and development-only 6/6 VPP smoke remain bounded; official VPP is `not_evaluated` | No positive artifact-derived `g3-acceptance-v1` authority exists. M5 H-stage scenario/episode outcome authority, per-call capability binding, two-axis hidden missingness closure and remaining G3c/G3d repair probes are open. No real-model, training, official held-out, evidence-promotion or paper outcome was produced; `g3_accepted=false` |
| CD10 G4b verifier and run unlock | `missing` | No authorization surface | Must add core campaign-freeze verification, prerequisite/side-effect checks, verifier-derived authorization receipt and official command gate; optional profile-pair verification applies only when enabled |

## Current Closure Priorities

The dated G3b design and implementation plan record completed development work;
they do not replace the active research freeze, which defines the following gate
order. G1 and G2 are locally closed
on this checkout. G1's registered compatibility envelope classifies v1.2 as canonical,
v1.1 as legacy quarantine, Direct/Untyped HIS as method-inapplicable, and
unknown representations as fail-closed quarantine. The 17 authoritative G1
nodes and the fresh 2026-08-30 full lightweight regression snapshot
(`2,055 passed`, `435 subtests passed`) were green at that snapshot. This is an
implementation/conformance gate, not model or functional-correctness evidence,
and it does not freshly validate later working-tree edits.

1. G3: replace caller-declared scenario facts with artifact-derived acceptance
   evidence. Retain the implemented G3a replicate/schedule/order lineage and G3b
   eager shared checkpoints plus actual/standalone/incremental cost views. G3c/G3d
   must still bind dereferenceable per-call capability evidence to the task/profile
   seed, close M5 H-stage scenario and episode-outcome authority, complete two-axis
   hidden missingness, add the remaining required L0/public-L2/L3 and repair probes,
   reconcile broader hidden/infrastructure scenarios, and produce a positive
   `g3-acceptance-v1` reducer and acceptance decision. Observed repeatability is
   not proof, and development conformance is not an official result. A further
   real-provider diagnostic would remain excluded and cannot substitute for these
   G3c/G3d blockers or positive G3 authority.
2. G4a: build the candidate VPP split/protocol and a disjoint candidate
   ambiguity-audit manifest; seal evaluator content and Recipe information
   policy. Freeze the RQ1 and RQ2 Holm/test/interval implementations, the RQ1
   gate-conditional full-claim joint-power rule, each retained RQ2 contrast's
   Holm-adjusted marginal-power rule, contrast-specific minimum effects/design
   alternatives, and the secondary M3-M2 reporting contract before any G5
   outcome. Build target-profile pairs/compliance commitments only if the
   optional extension is explicitly enabled.
3. G5: run only excluded non-official generation and ambiguity pilots; any
   method/prompt/visibility/default/profile change invalidates the affected G4a
   protocol.
4. G4b: sign the final VPP and ambiguity sample sizes, splits, oracle
   commitments, budgets, models, analysis, effect/safety thresholds,
   RQ1/RQ2 Holm families, the RQ1 gate-conditional joint/marginal-power report,
   each retained RQ2 contrast's Holm-adjusted marginal-power report, paired-
   block/cost and missingness rules before official runs; independently verify
   an authorization receipt. Add pair/compliance fields only for an enabled
   optional extension.
5. G6: materialize the signed campaign and complete no-outcome dry-run and
   integrity checks; do not produce official outcomes.
6. G7: execute the official M0-M5 held-out experiment and the separate signed
   ambiguity audit.
7. G8: perform representative OpenXC7 confirmation and run paired target-profile
   adaptation only when that extension was signed before outcomes.
8. G9: freeze TRETS paper claims against the signed artifacts. No model training
   occurs anywhere in Paper-1.

## Verdict Rules

- `not_run` is not a failure; report it separately with a skip reason.
- Toolchain and provider infrastructure failures are not model failures.
- REQ2FILE is a retained derived view and has no standalone evaluation credit.
- A candidate cannot receive automatic pass credit after modifying its trusted
  oracle.
- L4-open and L4-commercial labels remain separate.
- An audit `APPROVED` verdict does not imply that every measured model or
  physical-design stage passed.

## Current Commands

Install:

```powershell
python -m pip install -e "agent[dev]"
python -m pip install -e "training[dev]"
```

Full test surface:

```powershell
python -m pytest contracts/tests agent/tests training/tests compatibility_tests -q -p no:cacheprovider
```

Deterministic Agent preflight:

```powershell
python -m sr2fpga_agent.runner `
  --config agent/configs/current/sr2fpga_deterministic_curriculum_smoke.example.yaml `
  --run-id local-deterministic-smoke `
  --preflight
```

Retained repository-only Training smoke（not a Paper-1 step）:

```powershell
python -m sr2fpga_training.prepare_dataset `
  --input training/tests/fixtures/smoke_verilog_raw.jsonl `
  --output artifacts/training/prepared-data/smoke/chat.jsonl

python -m sr2fpga_training.training_dry_run `
  --input artifacts/training/prepared-data/smoke/chat.jsonl `
  --max-seq-length 2048
```

These are conversion/shape checks for retained repository infrastructure only.
The exposed `train_lora` and `merge_lora` utilities are not Paper-1 commands and
must not be used for the TRETS Paper-1 campaign.
