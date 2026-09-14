# SR2FPGA System-HIS v1.2 Freeze Design

> Paper-facing name: Project Contract (PC). This retained technical specification
> keeps the System-HIS v1.2 serialization name and identifiers for compatibility.
> See the [2026-09-08 terminology ledger](2026-09-08-sr2fpga-terminology.md).

> **Current boundary (2026-08-14):** Retained as the Tier-1 System-HIS semantic
> design authority, but not as proof of complete runtime conformance. The JSON
> Schema, H0/H1/H2 checker, canonical fixtures/examples, reset semantics,
> lowerability, and compatibility envelope must pass G1 of the active Paper-1
> freeze before a new model campaign.

## Status

**Approved direction (2026-06-24); updated from the reframe hardening pass
(2026-06-26).** This document commits `system-his-v1.2` as the single canonical
schema and stops the dual-schema (v1.1 + v1.2-topdown) drift — that decision is
in force now. The **Tier-1 structural freeze is ratified**: the canonical fields,
deterministic v1.2 emission, legacy quarantine, and HIS↔RTL L0 cross-check are
the stable clean-data contract. The **Tier-2 behavioral/timing fields remain
provisional until exercised end-to-end** by real pipelined/FSM tasks (see
"Freeze ratification gate"). It supersedes the retired
`system-his-v1.2-topdown` prototype and the earlier inline `system-his-v1.1`
schema, both preserved in Git history. Where they differ, this document
governs.

> **What is frozen now vs still gated:** the Tier-1 schema shape and HIS↔RTL
> structural cross-check are frozen. The richer Tier-2 semantics —
> `data_flow.timing`, structured `control_flow` (`fsm_transition`/`enable_rule`),
> `state.fsms`, and the guard grammar — are implemented as schema/checker shapes
> but remain **provisional** until a real pipelined/FSM task proves the fields
> useful and L2-measurable. The 2026-06-26 reframe also adds hardening gates
> outside the raw JSON schema: REQ→HIS fidelity, measurement freeze, hidden/stress
> tests, and contract-preserving generation.

## Why freeze now

System-HIS is the **REQ2HIS training target** and the **L0 ground-truth
contract**. Once trajectories are generated at scale, schema churn invalidates or
forces migration of already-produced data. The freeze was needed because the repo
had begun to drift between `system-his-v1.1` and the prototype
`system-his-v1.2-topdown`, making the REQ2HIS target ambiguous. This document
picks one canonical schema, defines what its checker must enforce, and sets the
migration/quarantine policy, so clean data generation runs against a stable
target.

## Decision summary

1. `system-his-v1.2` (dropping the `-topdown` prototype suffix) is the **single
   canonical schema**. The deterministic `ProjectGenerator` migrates to it.
2. The v1.2 checker **must gain HIS↔RTL cross-checks** (currently it does IR
   self-consistency only) to preserve the cross-file-consistency metric.
3. Cross-check strictness: **port existence + direction strict; width
   semantic-equivalence**.
4. `data_flow` carries an optional **timing contract** (latency / II /
   throughput) so pipeline depth and throughput are first-class.
5. `control_flow` is **load-bearing, verified at L2** (not advisory); FSMs are
   represented with structure in `state.fsms` and behavior in `control_flow`.
6. Guard expressions use a **shallow structured grammar (depth ≤ 2)**.
7. Legacy + v1.1 data is **quarantined** (labeled, kept for traceability, not
   mixed into the clean REQ2HIS training split).
8. System-HIS is evaluated by two orthogonal checks: **REQ→HIS fidelity** and
   **HIS↔RTL consistency**. A coherent-but-wrong HIS is a failure, even if its
   generated RTL and testbench agree with it.
9. Measurement protocol is part of the freeze boundary: prompts, seeds, repair
   budget, timeouts, tool versions, hidden tests, split policy, and pass/warn/fail
   semantics must be frozen before official evaluation data is generated.
10. L2 is not a single directed smoke test. Official claims require hidden,
    randomized, and stress scenarios, coverage/assertion targets where applicable,
    and optional L2S post-synthesis netlist simulation for RTL-vs-synth sanity.
11. Contract-preserving generation is the preferred next implementation path:
    System-HIS deterministically emits the project skeleton; the model fills
    behavior holes. This is the B2 ablation and the Tier-A constrained-generation
    backbone.
12. L4/L5 physical evidence is outside the schema fields but inside the research
    contract: QoR and timing claims must be tied to meaningful FPGA mapping
    (`synth_xilinx`, OpenXC7, and representative Vivado reference where used),
    not generic/vacuous LUT counts.

## Freeze ratification gate

The freeze is staged. Tier 1 is ratified; Tier 2 and the reviewer-hardening gates
remain evidence-gated. The original implementation plan is preserved in Git
history:

- **Tier 1 — structural core** (`schema_version`, `intent`, `top`, `components`,
  `instances`, `data_flow` path/endpoints, `state` (non-FSM), `timing`,
  `resources`, `verification`, `artifacts`) + the HIS↔RTL cross-check.
  **Status:** ratified. The deterministic generator emits valid
  `system-his-v1.2` for current task families, the L0 checker routes v1.2 through
  HIS↔RTL cross-checks, and legacy/v1.1 samples are quarantined rather than mixed
  into the clean REQ2HIS target.

- **Tier 2 — provisional new fields** (`data_flow.timing` latency/II/throughput;
  structured `control_flow` `fsm_transition`/`enable_rule`; the guard grammar;
  `state.fsms`). These are now represented in the schema and structurally
  validated by the checker, but remain **provisional** because they have not yet
  been ratified by a real pipelined/FSM task with L2-measured behavior. They are
  **not required in the REQ2HIS training target** until a real task exercises each
  one end-to-end. **Ratified when:** a pipelined task carries a
  `data_flow.timing` contract checkable at L2 (latency/II measured), and an
  FSM-bearing task (the RL agent FSM is the reference) round-trips through
  `state.fsms` + structured `control_flow` with auto-derived testbench
  liveness/stall scenarios. Until ratified, the guard grammar and FSM/timing
  shapes may still be revised based on what running them reveals — that is the
  point of keeping them provisional rather than frozen.

**Consequence for data collection:** the first clean training split may begin on
the **Tier-1 core** without waiting for Tier 2. However, the official paper
measurement split still waits on the measurement-freeze and oracle-hardening gates
from the reframe spec; otherwise the data is useful engineering evidence but not
reviewer-grade scaled evidence.

### Post-ratification hardening gates

These do not change the canonical v1.2 top-level fields, but they change what
counts as acceptable System-HIS evidence:

- **REQ→HIS fidelity gate:** generated System-HIS must match the original
  requirement or an oracle/manual HIS, not only the emitted RTL.
- **Measurement freeze gate:** official runs freeze prompt family, seeds, timeout,
  repair budget, tool versions, task split, hidden tests, and pass/warn/fail
  semantics before data collection.
- **Oracle-hardening gate:** L2 includes hidden/random/stress cases plus coverage
  or assertions where the family supports them; optional L2S catches RTL that
  simulates but diverges after synthesis.
- **Contract-preserving generation gate:** run B1/B2 ablations where B2 emits a
  deterministic skeleton from System-HIS and lets the model fill behavior holes.
- **Physical-evidence gate:** L4 claims require real FPGA mapping/timing reports;
  OpenXC7 is the reproducible open path, with representative Vivado reference
  validation for TCAD-strong claims.

## Canonical schema and migration

- **Schema version string:** `system-his-v1.2`. Code, generators, and the
  checker emit/expect exactly this value. The `-topdown` suffix was the prototype
  marker and is retired.
- **Deterministic generator migration:** `ProjectGenerator` stops emitting
  `system-his-v1.1` and emits `system-his-v1.2`. This is the larger code change
  the freeze implies; it is in scope for the implementation plan, not optional.
  The deterministic generator is the trusted baseline, so its v1.2 output doubles
  as golden fixtures for the checker and as REQ2HIS supervision.
- **One checker, version-dispatched:** the project-level L0 checker keeps
  dispatching by `schema_version`. `system-his-v1.2` files go through the v1.2
  checker (now with cross-checks, below); `system-his-v1.1` / legacy files are
  accepted only for the quarantine/traceability path, never as clean training
  targets.

## Schema shape (canonical v1.2)

Organized as orthogonal architecture aspects (the way an FPGA architect reasons):

```json
{
  "schema_version": "system-his-v1.2",
  "intent":       {"user_prompt": "...", "design_goal": "...", "assumptions": []},
  "top":          {"name": "...", "parameters": [], "clocks": [], "resets": [],
                   "ports": [], "interfaces": []},
  "components":   [],
  "instances":    [],
  "data_flow":    [],
  "control_flow": [],
  "state":        {"registers": [], "counters": [], "fsms": [],
                   "buffers": [], "memories": []},
  "timing":       {"primary_clock": "...", "target_fmax_mhz": 0, "constraints": []},
  "resources":    {"optimization_goal": "balanced", "expected": {}},
  "verification": {"testbench": "...", "scenarios": [], "pass_condition": "..."},
  "artifacts":    {"top_module": "...", "rtl_sources": [], "testbench": "...",
                   "constraints": [], "manifest": "...", "predicted_qor": "..."}
}
```

Aspect roles: `top` = boundary; `components`/`instances` = composition (definition
vs concrete instance — the v1.2 split that resolves repeated-instance ambiguity);
`data_flow` = datapath + timing; `control_flow` = control logic; `state` =
architectural state; `timing`/`resources` = QoR/physical intent; `verification` =
acceptance; `artifacts` = mapping to the project package.

## Typed IR discipline and validation levels

System-HIS v1.2 is frozen at the **core schema level**: field names, required
top-level aspects, JSON/YAML shape, and REQ2HIS training-target format.
Non-breaking validation extensions — well-formedness checks, enum refinements,
optional advisory fields, and lowering-time diagnostics — may evolve without a
schema version bump.

### IR discipline

Six principles make System-HIS a typed IR rather than a structured prompt:

1. **Typed contract fields, not prose.** `intent` (`user_prompt`,
   `design_goal`, `assumptions`) is provenance and explanatory context only. It
   is **not** an implicit semantic source for L0/L2 checkers. Machine-checkable
   semantics must appear in typed fields: `top`, `interfaces`, `components`,
   `instances`, `data_flow`, `control_flow`, `state`, `timing`, `resources`,
   `verification`, and `artifacts`.
2. **Well-formedness.** Every instance resolves to a component; every data-flow
   endpoint resolves to a port or interface; widths, directions, clocks, resets,
   and protocols are compatible; CDC paths carry synchronizer intent; memory and
   protocol intents must be supported by the lowerer.
3. **Interface-first FPGA semantics.** Ports are physical signal boundaries;
   interfaces are semantic bundles. Protocols (`valid_ready`, AXI-stream,
   AXI-lite, BRAM, GPIO) carry role, channels, ordering, backpressure, reset
   behavior, and checker templates. L0 checks ports; L2/L2-UVM/L5 depend on
   interfaces.
4. **Bounded control grammar.** `control_flow.when` and `control_flow.effect`
   use a bounded, typed guard/effect language with guard nesting depth <= 2.
   Free-text intent may explain a rule, but only typed guards/effects are
   checked or lowered.
5. **Contract-preserving lowering.** System-HIS lowers to: symbol table ->
   project manifest -> top shell -> module declarations -> interface bundles ->
   testbench scaffold -> assertion/checker templates -> logical constraints ->
   board-shell binding -> model-fillable behavior holes. This guarantees
   cross-file structural consistency by construction; behavioral correctness is
   L2's responsibility.
6. **Canonicalization.** Canonical JSON serialization, stable IDs independent of
   human-readable names, deterministic field ordering, and normalized parameter
   expressions are used for hashing, diffing, REQ→HIS fidelity scoring, L0
   checking, and training targets.

### Intent / Contract / Advisory classification

| Class | Fields | Checker role |
|---|---|---|
| **Intent** | `intent.*`, explanatory strings | Provenance only; not used by L0/L2. |
| **Contract** | `top`, `interfaces`, `components`, `instances`, `data_flow`, `control_flow`, `state`, `verification.pass_condition` | Must be satisfied by L0/L2. |
| **Advisory** | `resources.expected`, `timing.target_fmax_mhz`, `predicted_qor` | QoR/optimization hints; misses are soft budget misses, not functional failures. |

### Well-formedness rules (W1-W10)

- **W1.** Every `instance.component` references exactly one declared
  `component`.
- **W2.** Every `data_flow.path` endpoint resolves through the symbol table to
  an existing top port or instance port.
- **W3.** Port widths and directions are type-compatible along every connection.
- **W4.** Every state-owning instance binds to a declared clock and reset.
- **W5.** A component declared combinational does not own state, clock, or
  reset.
- **W6.** Every `cdc:true` data-flow crosses two distinct clock domains and
  passes through a synchronizer component or explicitly declared CDC primitive.
- **W7.** Every memory intent declares `depth`, `width`, `read_latency`,
  `read_type`, and `memory_style` if BRAM/distributed/register mapping is
  evaluated.
- **W8.** Every verification scenario references existing interfaces/signals and
  maps to a lowerer-supported stimulus/checker template.
- **W9.** Every logical constraint references declared clocks/ports and does not
  override board constraints.
- **W10.** Every artifact path listed in `artifacts` is reproducible from
  `manifest.json` plus `top_module`.

### H0/H1/H2 System-HIS validation levels

These levels run before the L0 RTL checker:

- **H0 — schema-valid:** JSON/YAML shape, required fields, and enum values.
- **H1 — well-formed:** symbols resolve, endpoints exist, widths/types are
  compatible, and W1-W10 pass.
- **H2 — lowerable:** all components, protocols, and scenarios are supported by
  the current lowerer and testbench generator.

REQ2HIS model outputs are evaluated at H0/H1/H2 before entering the L0-L3
pipeline. Failures at H0/H1/H2 have independent `req_his_*` diagnosis classes
and can be repaired by the FAILURE2PATCH actor without running EDA tools.

REQ→HIS fidelity failure modes:

`req_his_missing_requirement` | `req_his_wrong_width` |
`req_his_wrong_protocol` | `req_his_wrong_reset_kind` |
`req_his_wrong_latency` | `req_his_missing_corner_case` |
`req_his_over_specified_behavior` | `req_his_under_specified_interface`

### Non-goals

System-HIS v1.2 does **not** aim to replace FIRRTL/CIRCT/LLHD/Calyx as a
circuit/compiler IR; fully specify cycle-accurate behavior; encode board-level
physical implementation details; serve as an IP-packaging standard; make tool
execution unnecessary; or prove functional correctness without
testbenches/properties.

## L0 cross-check (v1.2 checker extension)

The v1.2 checker keeps its IR self-consistency checks and **adds HIS↔RTL
cross-checks** by parsing the generated RTL. This restores the metric the v1.1
checker provided and the prototype v1.2 checker dropped.

**Strict (hard failure on mismatch):**

- every `component` corresponds to an RTL module definition in its declared
  `source` file; every `instance` corresponds to an instantiation in `rtl/top.v`;
- **port existence and direction**: every port a component declares must exist in
  the RTL module with the same direction (`input`/`output`/`inout`); no extra,
  no missing;
- `data_flow.path` endpoints resolve to `top.<port>` or `<instance>.<port>` that
  actually exist;
- `artifacts` match `manifest.json`; the testbench instantiates the real top;
  `timing.constraints` reference only real top ports;
- (FSM cross-check) every `state.fsms[].states` set has a matching state
  enumeration in the RTL of its owner module (name-level match).

**Semantic-equivalence (not literal):**

- **port width**: `[7:0]`, `8`, and a parameterized form resolving to 8 are all
  equal. The checker compares resolved/normalized widths, never raw strings, so
  System-HIS stays an intent abstraction rather than an RTL mirror.

The principle: **structure (existence, direction, connectivity) is strict;
surface notation (width spelling) is normalized.**

## REQ→HIS fidelity (new reframe hardening gate)

HIS↔RTL consistency is necessary but insufficient. A model can misread the
requirement, emit a wrong-but-coherent HIS, and then generate RTL/testbench that
faithfully follows that wrong HIS. Such a sample may pass L0/L2 while still
failing the user requirement. Therefore System-HIS is measured by two axes:

- **REQ→HIS fidelity:** does the contract preserve the original requirement's
  required topology, ports, directions, widths, protocols, state, timing intent,
  and verification obligations?
- **HIS↔RTL consistency:** does the generated project implement the contract it
  claims to implement?

For synthetic/component-topology tasks, the deterministic oracle HIS is the
reference: required nodes, edges, top ports, directions, selected widths, and
protocols must match. For natural tasks without a deterministic oracle, fidelity
is judged against a manually reviewed/oracle HIS or a structured requirement
record. REQ→HIS fidelity becomes an RQ1 sub-metric and an official data-quality
filter before samples enter clean REQ2HIS supervision.

The canonical fidelity dimensions are:

- **interface extraction accuracy:** port names, directions, widths, and protocols;
- **clock/reset fidelity:** polarity, synchronous/asynchronous kind, and
  deassertion rule;
- **parameter fidelity:** width, depth, latency, parallelism, and memory banking;
- **behavior-intent fidelity:** FIFO, arbiter, MAC, pipeline, AXI-lite, and stream
  semantics;
- **verification-intent fidelity:** required scenarios and corner cases;
- **constraint fidelity:** target Fmax, resource budget, and board shell/profile.

Trajectory records use this shape so REQ→HIS can be scored independently of the
generated RTL:

```json
"req_his_fidelity": {
  "interface_extraction": null,
  "clock_reset_fidelity": null,
  "parameter_fidelity": null,
  "behavior_intent_fidelity": null,
  "verification_intent_fidelity": null,
  "constraint_fidelity": null
}
```

## data_flow timing contract (pipeline / throughput)

Each `data_flow` path may carry an optional `timing` object:

```json
{
  "name": "main_stream",
  "path": ["top.in_data", "skid.out_data", "accum.sum", "top.sum"],
  "width": 8, "protocol": "valid_ready", "cdc": false,
  "timing": {"latency_cycles": 3, "initiation_interval": 1,
             "throughput": "1 sample/cycle"}
}
```

- `latency_cycles` = input→output latency (pipeline depth); `initiation_interval`
  (II) = cycles between accepted inputs (II=1 ⇒ fully pipelined); `throughput`
  derives from II.
- **Optional**: simple/unpipelined designs omit `timing`; pipelined designs
  include it. This keeps the REQ2HIS target stable for easy tasks.
- **Verification venue**: latency/II are measured at **L2** (simulation), Fmax at
  **L4** (P&R) — not vacuous.
- **Forward-compatible with Paper ②**: pipeline depth and II are exactly the QoR
  search variables, so first-classing them now avoids a later schema change.

Provenance: the rate/latency vocabulary is borrowed from dataflow models of
computation (SDF/KPN) as realized in HLS dataflow frameworks (TAPA, Stream-HLS,
HIDA, Calyx). The schema absorbs that vocabulary into `data_flow` without adopting
a pure dataflow MoC (see "Paradigm").

## control_flow (load-bearing, verified at L2)

`control_flow` is **not advisory**. Its correctness is verified at **L2** (the
testbench it drives), mirroring the v1.2 principle "L0 checks structure, L2 checks
function." data_flow is the structural aspect (L0-verifiable); control_flow is the
behavioral aspect (L2-verifiable).

### FSM representation (structure vs behavior split)

- **Structure** in `state.fsms`:

  ```json
  {"name": "agent_fsm", "owner": "agent_controller",
   "states": ["OBSERVE","INFER","SELECT","STEP","STORE","SAMPLE","UPDATE"],
   "initial": "OBSERVE", "reset_state": "OBSERVE"}
  ```

  L0 checks: states declared; `initial`/`reset_state` ∈ states; (cross-check) RTL
  contains a matching state enumeration.

- **Behavior** in `control_flow`:

  - `fsm_transition` — `{fsm, from, to, when, effect?}`. `from`/`to` must be
    declared states of `fsm`. Branches = multiple transitions from one state with
    different guards (e.g. ε-greedy explore vs exploit). Probabilistic sources
    (RNG) are modeled as components/state, not in the guard.
  - `enable_rule` ("conductor" pattern) — `when: fsm.state == X → assert
    datapath.start`. This explicitly links control to data_flow ("in INFER,
    start q_network") and is L2-checkable.

### Guard grammar (the intent/RTL boundary)

Guards use form **(b)**: structured, reference-checked, **nesting depth ≤ 2**.

```json
"when": {"all_of": [
  {"signal": "q_network.valid_out", "op": "==", "value": 1},
  {"signal": "agent_fsm.state",     "op": "==", "value": "INFER"}
]}
```

- Atoms: `{signal, op, value}` where `signal` references a declared port / state /
  flow (checked), `op` ∈ `{==, !=, <, >, &&, ||}`.
- Combinators: `all_of` / `any_of`, **at most 2 levels deep**.
- **Forbidden**: arbitrary nested boolean/arithmetic/bit expressions. The depth
  cap is the hard line that keeps System-HIS an intent abstraction, not Verilog.

### Why structured control_flow matters

A structured FSM + guards lets the testbench generator auto-derive **liveness**
scenarios (drive guards in sequence, assert the FSM walks the phases) and
**stall** scenarios (hold a guard low, assert the FSM stays). This makes the
failures of control-heavy designs measurable at L2, connecting control_flow to
the hardware-semantic failure taxonomy (backpressure / FSM-stall) in the reframe
spec. Free-text control_flow would make those failures un-generatable and
un-measurable.

## L2 oracle hardening

`verification.scenarios` and `control_flow` are now treated as inputs to a
stronger L2 oracle, not as descriptive prose. The default L2-core remains a
deterministic black-box self-checking simulation, but official claims require:

- **L2a** directed smoke tests;
- **L2b** randomized/stress scenarios;
- **L2c** required protocol/value coverage;
- public directed scenarios plus hidden tests that are not exposed in the input
  prompt;
- randomized/stress variants for valid-ready, FIFO/skid, FSM-stall, reset, and
  backpressure-heavy families;
- coverage/assertion targets where they can be generated from System-HIS without
  hand-writing a full environment;
- optional **L2S** post-synthesis netlist simulation for selected samples, to
  catch RTL that passes behavioral simulation but changes after synthesis;
- optional **L2-UVM** only for protocol-heavy subsets, generated from System-HIS
  and trusted templates, not free-form LLM-authored UVM.

This preserves the schema boundary: L0 checks structural consistency; L2 checks
behavior under a declared oracle; L4 checks physical timing/resource evidence.

Minimum coverage targets by family:

- **valid-ready / stream:** valid held while ready is low, randomized stalls,
  bursts, idle cycles, reset during transaction;
- **FIFO / skid buffer:** full, empty, almost_full/empty, simultaneous push-pop,
  overflow/underflow attempts;
- **pipeline:** different latency paths, stalls, flush/reset during in-flight data;
- **arithmetic:** signed/unsigned, boundary values, overflow/truncation cases;
- **memory/BRAM:** read-after-write, same-address conflict, sync vs async read
  behavior;
- **AXI-lite/stream subset:** ordering, WSTRB, response channel, back-to-back
  transactions.

Each evaluation item may contain multiple scenario classes:

- **public:** visible to the generation/repair loop;
- **hidden:** used only for final acceptance;
- **randomized:** fixed seeds, recorded in the trajectory;
- **stress:** reset during transaction, backpressure, boundary values, full/empty,
  resource/timing stress.

Final L2 acceptance is based on hidden + stress coverage, not only public smoke
tests. Seeds and scenario profiles are recorded for reproducibility. Protocol-heavy
families should also emit assertions/checkers from System-HIS protocol intent,
for example payload stability while `valid && !ready`, FIFO no-read-empty /
no-write-full, reset-clears-state, and no data drop/duplication.

## Contract-preserving generation

The reframe makes contract-preserving generation the next System-HIS method step:

```text
requirement -> System-HIS -> deterministic project skeleton -> model fills behavior holes
```

The deterministic skeleton owns top/module headers, declared ports, instances,
basic wiring, manifest entries, SDC `get_ports`, and testbench top instantiation.
The model owns behavioral bodies and any explicitly marked behavior holes. Artifact
metadata must record which regions are deterministic vs model-generated. This is
the B2 baseline/ablation and Tier A of the constrained-generation design. It is
separate from Tier B logit-masked constrained decoding, which requires a local
model with logit access.

Every trajectory must record the generation provenance explicitly:

```json
"project": {
  "files": {},
  "deterministic_artifacts": [
    "manifest",
    "filelist",
    "top shell",
    "testbench scaffold",
    "constraints from board profile"
  ],
  "model_generated_artifacts": [
    "module internals",
    "control/datapath implementation",
    "patches"
  ],
  "model_token_fraction": null,
  "behavior_hole_count": null
}
```

Core claim discipline: cross-file structure is generated or constrained from
System-HIS; behavioral RTL is generated by the model; tools judge both.

## Episode metadata and release discipline

The reframe treats each sample as a trajectory episode, not a single prompt/output
pair. The v1.2-related episode fields are:

```json
{
  "sample_id": "string",
  "requirement": "string",
  "oracle_his": {},
  "generated_his": {},
  "req_his_fidelity": {},
  "project": {
    "files": {},
    "deterministic_artifacts": [],
    "model_generated_artifacts": [],
    "model_token_fraction": null,
    "behavior_hole_count": null
  },
  "verification": {
    "l0": {"status": "pass|fail", "errors": []},
    "l1": {"status": "pass|fail|missing_tool", "warnings": [], "errors": []},
    "l2_core": {
      "status": "pass|fail|missing_tool",
      "public": {"status": null, "mismatch_detail": []},
      "hidden": {"status": null},
      "stress": {"status": null},
      "coverage": {"scenario_profile": null, "seeds": []}
    },
    "l2s": {"status": "pass|fail|not_run", "divergences": []},
    "l3": {"status": "pass|fail|missing_tool"},
    "l4_open": {"tool": "openxc7_nextpnr", "status": "pass|fail|not_run"},
    "l4_commercial": {"tool": "vivado", "status": "pass|fail|not_run"},
    "l4_agreement": {"class": "D0|D1|D2|D3|D4|not_applicable"},
    "l5": {"status": "pass|fail|not_run", "log_path": null}
  }
}
```

Every episode field must be marked with a data-release tier before official
release:

- `open_public`: generated code, open-tool labels, open-flow logs that are safe to
  publish;
- `restricted_reference`: commercial-reference metadata or artifacts that require
  license/legal review;
- `internal_only`: raw Vivado artifacts, credentials, local paths, and any data
  that cannot be redistributed.

Vivado labels are commercial-reference labels on a representative L4 subset. They
do not replace the open OpenXC7 label stream and are not public training data unless
license-cleared.

## Paradigm: datapath+control backbone, dataflow timing absorbed

Three ways to organize a hardware-architecture IR were considered:

- **A — datapath + control** (Calyx-style): data_flow and control_flow as
  separate aspects. Checker- and testbench-implementable today.
- **B — dataflow actor/channel MoC** (SDF/KPN; TAPA/Stream-HLS/HIDA): actors with
  firing rules + production/consumption rates; throughput/pipeline native.
  Elegant for streaming, **awkward for control-heavy designs**.
- **C — orthogonal aspects**: organize the schema into independent aspects
  (boundary/composition/dataflow/control/state/timing/verification).

**Chosen: A as the primitive backbone + B's rate/latency vocabulary absorbed into
`data_flow.timing` + C's aspect organization.** Rationale: the benchmark body is
streaming valid-ready designs (B fits the datapath), but FSM/arbiter/controller
designs are coming (pure B cannot express them), so control_flow must stay an
independent first-class aspect.

### Stress test: RL accelerator (forward-compat, not specced now)

A reinforcement-learning accelerator (the T4/Stress flagship on the AC820-ZYNQ,
220 DSP + ARM) is the decisive case because it is **inherently hybrid**:

- streaming datapath (Q/policy-network inference = MAC array = the existing
  `matrix_vector_mac` task) → `data_flow.timing` (II / pipeline depth);
- control-heavy core (agent loop FSM: OBSERVE→INFER→SELECT→STEP→STORE→SAMPLE→
  UPDATE; ε-greedy branch; Bellman update; ARM/env handshake; replay-memory
  arbitration) → `control_flow` (irreducible to dataflow firing rules).

This confirms the hybrid choice: pure B is insufficient. The schema must be able
to **express** the RL accelerator (verified by mapping it onto v1.2 aspects), but
the freeze does **not** fully spec it. It also ties to existing assets
(`matrix_vector_mac`) and Paper ② (QoR search over the inference pipeline depth /
II / DSP allocation living in `data_flow.timing` + `resources`).

## Data migration / quarantine policy

- **Legacy** (no `schema_version`) and **`system-his-v1.1`** samples — including
  the committed baseline (a)/(b) snapshot — are **quarantined**: labeled by their
  schema, kept for traceability and as a comparison baseline, **never mixed into
  the clean REQ2HIS training split**.
- No migration tool is built (the v1.1 data volume is small; re-running under
  frozen v1.2 is cleaner than a lossy converter). Re-generation under v1.2 is the
  path to clean data.
- A derived/migrated view may be produced later for diagnostics only, explicitly
  marked as derived.

## Scope (freeze) vs out-of-scope (v1.3+)

**In the freeze:**

- `system-his-v1.2` schema (aspects above) + deterministic generator migration;
- v1.2 checker HIS↔RTL cross-checks (strict existence/direction, semantic width,
  FSM state-name cross-check);
- REQ→HIS fidelity as a required measurement/data-quality axis;
- `data_flow.timing` (latency / II / throughput, optional);
- structured `control_flow` (fsm_transition / enable_rule) + guard grammar
  (depth ≤ 2);
- quarantine labeling for legacy/v1.1 data;
- the measurement/oracle-hardening requirements that determine whether v1.2 data
  is clean enough for official evaluation.

**Out of scope (later, v1.3+):**

- richer control_flow scheduling semantics beyond the rule kinds;
- behavioral (not structural) CDC verification;
- a v1.1→v1.2 migration tool;
- Tier B logit-masked constrained decoding engine and incremental Verilog parser;
- full RL-accelerator specification.

## Success criteria

- The deterministic generator emits valid `system-his-v1.2` for all current task
  families and passes the extended L0 checker.
- The v1.2 checker reports a cross-file-consistency error rate (the metric) on
  v1.2 samples.
- Generated System-HIS contracts report REQ→HIS fidelity against deterministic
  oracle HIS or manually reviewed structured requirements.
- A pipelined task carries a `data_flow.timing` contract checkable at L2.
- An FSM-bearing task (RL agent FSM as the reference) is expressible with
  `state.fsms` + structured `control_flow`, and its testbench liveness/stall
  scenarios are auto-derivable.
- Official evaluation runs use frozen prompts/seeds/timeouts/repair budgets/tool
  versions/splits and an L2 oracle with hidden/random/stress coverage appropriate
  to the task family.
- The contract-preserving skeleton ablation records deterministic vs
  model-generated artifact regions and shows whether L0 structural failures are
  eliminated without hurting L2.
- Trajectory episodes include `oracle_his`, `generated_his`,
  `req_his_fidelity`, deterministic/model-generated artifact provenance,
  L2-core public/hidden/stress/coverage fields, optional L2S, and L4-open /
  L4-commercial / agreement fields.
- Each episode field is assigned a data-release tier before release
  (`open_public`, `restricted_reference`, or `internal_only`); Vivado raw artifacts
  never enter public training data unless license-cleared.
- Legacy/v1.1 samples are schema-labeled and excluded from the clean training
  split.

## Relationship to existing documents

This freeze operationalizes the System-HIS portions of the earlier reframe
proposal preserved in Git history and incorporates its 2026-06-26 hardening
updates for REQ→HIS fidelity, measurement freeze, oracle hardening,
contract-preserving generation, and physical-evidence claim discipline. It
supersedes the v1.2-topdown prototype. The earlier inline v1.1 schema block is
historical; its hardware-semantic failure taxonomy is realized through this
schema (`data_flow.cdc`, `control_flow`
stall/handshake rules, state-based seq/comb) and through the hardened L2/L4
measurement protocol.
