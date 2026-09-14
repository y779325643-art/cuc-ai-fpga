# RQ5 Contract-Preserving Evolutionary Architecture Search — v1.8 Design

> Historical design: superseded as the active candidate direction on 2026-09-08
> by [`contract-guided-evolutionary-dse-v1.9-candidate.md`](contract-guided-evolutionary-dse-v1.9-candidate.md).
> It remains part of the decision history and does not govern implementation.

## Status

This is the working design record for the user-approved v1.8 Paper-1 amendment.
It defines no implementation, model run, pilot, official evaluation, or empirical
outcome. The canonical authority remains the English Paper-1 specification.

## Scientific question

Given the same frozen requirement facts, FPGA target profile, generated
System-HIS seed, public evaluator, and real-tool budget, does a
contract-preserving evolutionary architecture search select a terminal FPGA
project with better bounded verified physical feasibility than equal-budget
random architecture search, while retaining one-shot hidden functional
conformance?

This is not a claim that evolutionary search, typed intent, or FPGA DSE is new.
The claimed mechanism is the combination of a compact evolvable architecture
genotype, deterministic requirement-preserving decoding to System-HIS, complete
project materialization, fixed-budget real-tool selection, and evaluator-side
final validation.

## Conditions

| ID | Condition | Only differing factor |
| --- | --- | --- |
| `B_EA` | Frozen architecture seed decoded once | Reference; no search claim |
| `E0` | Uniform random samples from the registered genotype grammar | Non-adaptive search policy |
| `E1` | `(1+lambda)` evolutionary search over the same grammar | Adaptive parent selection and mutation |

`E0` and `E1` share the same initial genotype, frozen requirement/profile,
decoder, mutation domain, candidate count, public tools, tool-call ceiling,
wall/EDA-time ceiling, terminal selector, and one-shot hidden evaluator. No
comparison may use an unequal number of candidates or a different public
fitness definition. `E1` is an EA condition, not M6, not a learned treatment,
and not an RL condition.

## Representation and boundaries

`Architecture-HIS v0.1` is a compact, indexed genotype. A deterministic decoder
must emit a valid System-HIS phenotype before the existing HIS-to-project path
runs. The phenotype must preserve the frozen requirement facts and declared
functional invariants; its content hash, parent identifiers, mutation record,
decoder version, and decoded System-HIS hash are append-only lineage fields.

The genotype may contain inactive nodes. The decoder must remove nodes and flows
unreachable from declared top outputs before emitting System-HIS. Measured QoR,
fitness, generation number, parent links, and selection decisions live in
sidecar search/evaluation records, never in System-HIS itself.

System-HIS v1.2 remains unchanged. Any future Architecture-HIS or System-HIS
extension requires a separately registered schema version and compatibility
tests; v1.2 must not be repurposed as an EA genotype.

## Evaluation and information boundary

Population selection may use only frozen public checks and actual public tool
outputs. The fitness is frozen before G5 and is lexicographic: contract and
public feasibility first, then declared resource-binding/timing feasibility,
then a predeclared deterministic tie-break. It may not use a learned proxy or a
predicted-QoR surrogate.

The hidden evaluator may execute exactly once, only after the public terminal
selector seals one candidate per condition. Its identity, cases, logs, scores,
and outcome cannot influence mutation, generation count, parent selection,
fitness, terminal replacement, or any later search decision.

## RQ5 analysis contract

The primary contrast is `E1 - E0` on the predeclared terminal bounded physical
feasibility endpoint. The G4a amendment must freeze the exact endpoint,
minimum effect, cluster-level estimator, interval method, one-sided test,
candidate/tool budget, terminal-selector tie-break, and missingness treatment.
The family uses one primary hypothesis unless a later pre-outcome amendment adds
another contrast. Resource/timing vectors, public-fitness trajectories,
invalid-decode rate, diversity, public-to-hidden divergence, and `B_EA` are
descriptive diagnostics; they do not rescue a failed primary result.

Every selected or failed individual contributes to cost, failure, and
missingness accounting. An EA result cannot be described as hidden-correctness,
general PPA improvement, or cross-device portability unless the exact signed
endpoint and final hidden result support that narrower claim.

## Additional gates

`EA-G3` verifies schema registration, deterministic decode, invariant checks,
unreachable-node pruning, public-fitness visibility, lineage/cost accounting,
terminal sealing, and no hidden-feedback path using excluded fixtures.

`EA-G4a` freezes the grammar, seed construction, mutation policy, `lambda`,
candidate and tool budgets, fitness, selector, endpoint, analysis code, and
hidden-evaluator commitment. `EA-G5` is an excluded feasibility/power pilot.
`EA-G4b` signs the complete design. Only then may `EA-G7` execute the official
RQ5 experiment. These gates add no authority to the existing M0--M5 results.

## EA-G3 implementation boundary

EA-G3 must be implemented as an independent extension path. It must not add an
`E0` or `E1` member to `MethodConditionId`, alter `METHOD_CONTRACTS`, or relax
the M0--M5 terminal-selection rules.

| Surface | EA-G3 responsibility | Existing boundary to reuse |
| --- | --- | --- |
| `contracts/architecture-his/` | Register `architecture-his-v0.1`, an EA search-plan contract, and append-only lineage/evaluation records | `contracts/manifest.json` and `ContractRegistry` |
| `agent/.../architecture_his.py` | Validate indexed genotype, mutate/sample it, prune unreachable nodes, and deterministically decode System-HIS | System-HIS v1.2 validation and `contract_skeleton.py` |
| `agent/.../ea_search.py` | Execute `B_EA`, `E0`, and `(1+lambda)` `E1` under the same frozen public budget | Artifact store and cost-accounting primitives |
| `agent/.../ea_terminal_selection.py` | Apply the precommitted public-fitness selector and seal exactly one terminal candidate | Artifact-store candidate seals; do not modify M0--M5 selection |
| `agent/.../public_evaluator.py` | Evaluate each immutable candidate only with public L0--L3/tool outputs | `DevelopmentAttemptPublicEvaluationAuthority` |
| `agent/tests/` and `contracts/tests/` | Prove deterministic decode, invariant preservation, pruning, equal budgets, no hidden-feedback path, lineage integrity, and terminal immutability | Existing System-HIS, public-evaluator, terminal-selection, and artifact-store tests |

The EA selector cannot reuse `select_development_terminal_candidate` unchanged:
that helper accepts only M0--M5 and selects the earliest public acceptance. RQ5
instead requires a separately contract-validated, deterministic best-public-
fitness selector. Both selectors must share the same artifact integrity and
sealing invariants.

### EA-G3 acceptance criteria

1. Every accepted Architecture-HIS decodes to a valid, requirement-preserving
   System-HIS v1.2 and then to a buildable project skeleton.
2. Genotype pruning changes only inactive genotype material; the emitted
   phenotype contains no unreachable instance or flow.
3. `E0` and `E1` consume identical public candidate/tool budgets and the same
   seed, grammar, decoder, public fitness, and terminal selector.
4. Search lineage binds every parent, mutation, decoded System-HIS, public
   evaluation record, and cost record by content hash.
5. Hidden evaluator references are unavailable to sampling, mutation, parent
   selection, fitness, and terminal selection; the hidden call remains outside
   EA-G3 fixture tests.
