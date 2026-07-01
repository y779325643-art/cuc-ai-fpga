# System-HIS-Constrained Generation Design

## Status

Proposed (2026-06-25); aligned with the 2026-06-26 reframe hardening pass and the
2026-06-30 prompt-information boundary. Expands
the method-novelty candidate in the reframe spec
(`2026-06-22-sr2fpga-research-reframe-design.md`). This is the lever that upgrades
SR2FPGA from a *new methodology* to a *new method* in the strong sense TCAD
requires: a decode-time mechanism that makes cross-file structural consistency hold
**by construction**, rather than only being checked after the fact. It is currently
**partially implemented**: Tier A now has an initial deterministic
contract-preserving skeleton path; Tier B remains design-only and is gated on a
local fine-tuned model with logit access.

## Goal

While an LLM generates the multi-file RTL project, **restrict / steer generation so
the output satisfies the System-HIS structural contract by construction** —
eliminating L0 cross-file-consistency failures at their source instead of repairing
them. Turn "we have an L0 checker that *catches* inconsistency" (evaluation) into
"we have a generation method that *prevents* it" (a method/technique).

## Why this matters

- **The method-novelty lever (TCAD).** The bare pipeline (SFT on tool-verified
  data) is "known techniques in a new domain"; TCAD will not accept it as a method
  contribution. Making L0 consistency hold by construction at decode time, driven by
  a *requirement-level* contract, is a genuinely new technique — and distinct from
  CPPL (which enforces consistency by *compile-time* width inference on a
  *circuit-level* IR).
- **Strengthens RQ1.** It is the strong form of the System-HIS ablation: not just
  "req→HIS→project helps," but "HIS-constrained decoding makes L0 hold by
  construction and improves downstream L1–L4."
- **Strengthens RQ3.** Eliminating structural failures lets the model spend its
  iteration budget on behavior/physics, plausibly improving (c) and reducing repair
  rounds.
- **Empirically targeted.** The baseline-run L0 failures were largely structural
  (wrong port names, reserved-keyword instance names, width mismatch, instance
  aliases) — exactly what this prevents.

## Background / provenance (the technique is established; our novelty is the constraint source)

Constrained decoding is a mature, citable technique — we are **not** inventing a new
primitive. The lineage (citations verified via OpenAlex unless flagged):

- **Classic roots — lexically constrained decoding in machine translation:**
  Hokamp & Liu, "Lexically Constrained Decoding for Sequence Generation Using Grid
  Beam Search," ACL 2017 (doi 10.18653/v1/p17-1141); Post & Vilar, "Fast Lexically
  Constrained Decoding with Dynamic Beam Allocation for NMT," NAACL 2018
  (doi 10.18653/v1/n18-1119). Force/forbid tokens during beam search.
- **Modern grammar/FSM-constrained generation (the LLM wave):** Willard & Louf,
  "Efficient Guided Generation for Large Language Models," arXiv 2307.09702 (2023) —
  the **Outlines** FSM-based logit-masking approach (the canonical recent reference);
  Beurer-Kellner, Fischer & Vechev, "Prompting Is Programming: A Query Language for
  LLMs" (LMQL), 2023 (doi 10.1145/3591300). Practical engines: Guidance, llama.cpp
  GBNF grammars, SGLang.
- **Incremental-parser-constrained decoding (closest precedent to our Tier B):**
  **PICARD** — Scholak, Schucher & Bahdanau, "PICARD: Parsing Incrementally for
  Constrained Auto-Regressive Decoding from Language Models," EMNLP 2021
  (arXiv 2109.05093) — an incremental parser rejects invalid continuations during
  beam search for SQL. *(Confidently known but not surfaced by the OpenAlex query;
  verify the exact citation before formal writing.)*

**Core principle:** at each step, intersect the model's distribution with the
constraint automaton's allowed-token set (mask the rest to −∞) → the output lies in
the constraint language **by construction**.

**Our novelty positioning (honest):** the *technique* (constrained decoding) is
established and citable; our contribution is the **constraint source and
application** — using **System-HIS, a requirement-level contract**, as the
decode-time constraint for **project-level cross-file RTL consistency**. A quick
multi-source search found **no direct precedent for constrained decoding driven by a
requirement-level contract over multi-file HDL/RTL** (not exhaustive — confirm in the
formal related-work pass; the adjacent "LLMs + compilers" survey, Zhang et al. 2026,
doi 10.1007/s42514-025-00270-x, is background). CPPL is the nearest neighbour but
acts at *compile time* on a *circuit-level* IR, not at decode time from a
requirement-level contract. This framing is a strength: a proven technique applied
through a novel representation — consistent with the reframe spec's "technique
standard, representation/application new."

## What gets constrained

System-HIS v1.2 declares `top`, `components`, `instances`, `data_flow`,
`control_flow`, `state`, `timing`, `resources`, `verification`, and `artifacts`.
The structural emission points where consistency breaks map directly to the
contract:

| Emission point | Constraint from System-HIS |
|---|---|
| `module <name>(ports…)` | name = a declared component/top; ports = that component's declared name/dir/width |
| top.v instantiation `<comp> <inst>(.port(net))` | comp / inst / port must be declared |
| testbench instantiates top | uses `top.name` and declared `top.ports` |
| SDC `get_ports` | only real top ports |
| manifest sources / top | consistent with `artifacts` |

The constraint is: **at each structural point, the legal identifier set is
determined by canonical `system-his-v1.2`.** Legacy fields such as v1.1
`connections`/`top_ports` are historical inputs only; new constrained generation
must read the v1.2 aspect fields.

## Mechanism (three tiers, increasing power and cost)

The hard problem: LLM tokens ≠ Verilog identifiers, and the constraint is
context-sensitive (which module/instance we are inside). Three tiers:

### Tier A — Structural skeleton generated deterministically from the contract (do first)

Do **not** let the LLM author structure. Generate the "shell" — module headers,
port lists, instantiations, wiring, manifest, SDC port list, testbench
instantiation — **deterministically from System-HIS**. The LLM fills only the
**behavioral bodies** (`always` blocks / combinational logic). Structural
consistency then holds **by construction trivially** — the LLM never gets to write a
port name. "Structure from the contract, behavior from the model." The existing
deterministic `ProjectGenerator` already does part of this; Tier A generalizes it to
the LLM path. This alone kills most observed L0 failures.

### Tier B — System-HIS-derived constrained decoding (the novel method core)

When the LLM fills behavioral bodies, every time it emits an **identifier reference**
(port / signal / state), the decoder **masks the logits to only contract-declared
names**. This is true constrained decoding: a **context-sensitive grammar derived
dynamically from System-HIS** drives logit masking. Requires:

- an **incremental Verilog parser** tracking position ("we are now in an
  instantiation port-connection / an identifier-reference position");
- a **System-HIS-indexed legal-token oracle** (per-module declared ports; global
  declared modules/instances; per-scope local signals/state);
- **logit masking** integrated into the inference stack.

**Hard constraint:** this needs **logit access → only the local / fine-tuned
model**; closed APIs cannot do it. This is consistent with "the model we fine-tune
is local" — **constrained decoding is a property of our (c) model**, not of the
large-frontier baselines (a)/(b). State this in the measurement (it is part of the
(c) contribution, not a same-condition comparison).

### Tier C — Verification-guided / lookahead decoding (future work)

Use the L0 checker as a pruning/value function in beam search: prune branches that
violate the contract. More expensive; handles cases hard to express as a grammar.
Out of scope for the first cut.

**Adopted design: Tier A as the backbone + Tier B as the method core.** Tier A kills
the structural L0 failures observed in baseline (port names, reserved-keyword
instance names, width, instance aliases); Tier B governs identifier references inside
the model-authored behavioral bodies.

## Decoder state

Current file; current module context; the System-HIS-indexed legal-identifier sets
(per-module declared ports, global declared modules/instances, per-scope local
signals/state); and an incremental parse state to know which structural position is
being emitted.

## Reuse of the L0 checker (one source of truth)

The constraint oracle **reuses the same contract representation as the v1.2 checker**
(`rtl_introspect` + `system_his_v12_checker` declared-port/module logic) to define
the legal sets. So the generator and the checker share **one source of truth** —
which also removes the oracle-drift risk (failure-repair Issue 19). The checker thus
becomes both the **constraint source** ("what is legal") and the **post-hoc
verifier** ("the by-construction property actually holds; catch anything the
constraint missed") and the **metric source** (cross-file-consistency error rate).

## Evaluation and ablations

1. **Primary:** cross-file-consistency error rate, **with vs without** the
   constraint, same model/tasks — by construction it should approach 0 for the
   constrained structural elements.
2. **Research question:** does eliminating L0 failures by construction **improve
   downstream L1–L4 pass rates and reduce repair rounds**? (The model no longer
   wastes attempts on structural errors.) This is the constraint's (b−a)-style delta.
3. **Quality ablation (honest):** does constraining **hurt functional correctness
   (L2)**? (the accessibility–competence risk — over-constraint can push the model
   off-distribution). Measure L2 pass with/without; report honestly.
4. This is the **strong form of the System-HIS ablation** (RQ1): not only "the IR
   helps" but "IR-constrained decoding makes L0 hold by construction and improves
   L1–L4."

## Scope and honest boundaries

- **In scope:** L0 / structural consistency **by construction**.
- **Out of scope:** functional (L2) and physical (L4) correctness — "the port exists"
  ≠ "the logic is right." Those remain the testbench's / P&R's job.
- **Logit access:** local model only; constrained decoding is part of the (c)
  contribution, not a same-condition comparison with API baselines.
- **Engineering cost:** the incremental parser + logit-masking integration is real
  work (Tier B).
- **Risk:** over-constraint can hurt fluency / functional quality — must be measured,
  not assumed away.

## Feasibility and sequencing

- **Tier A is the current System-HIS implementation hardening step**
  (deterministic shell on the LLM path). An initial skeleton/body-merge path now
  exists; the remaining work is to keep artifact metadata explicit about
  deterministic vs model-generated regions so the B2 ablation is auditable.
- **Tier B is the new method core** — needs the local fine-tuned model + a
  constrained-decoding engine (logit masking + incremental parser). Medium
  engineering. This is the step that earns the TCAD "new method" claim.
- **Dependency:** Tier B needs a local model under our control (the RQ3 model) and
  the v1.2 contract representation (done). So Tier A first; Tier B after the first
  local model exists.
- **Honest claim:** "System-HIS-constrained generation makes cross-file structural
  consistency hold by construction (demonstrable) and improves downstream repair
  efficiency" — bounded, falsifiable, does not touch functional/physical.

## Relationship to existing documents

- Expands the reframe spec's method-novelty candidate (i); realizes the
  "new method" path discussed in its Method statement.
- Reuses the v1.2 freeze's checker/contract representation
  (`2026-06-24-sr2fpga-system-his-v1.2-freeze-design.md`); shares one oracle,
  removing failure-repair Issue 19's drift risk. The freeze spec now records
  Tier A contract-preserving generation as a post-ratification hardening gate.
- Distinct from CPPL (compile-time, circuit-level IR) — this acts at decode time
  from a requirement-level contract.
- Gated like RQ3: needs the first local fine-tuned model before Tier B; Tier A can
  continue independently.

## Prompt-information boundary

This design must not turn official prompts into implementation recipes. For
official measurement, use three separate views:

- `simple_prompt`: externally checkable requirements only; no module-level recipe,
  FSM table, always-block sketch, internal register list, or line-level fix hint.
- contract-rich normalized requirement / System-HIS view: may expose the engineering
  contract, ports, obligations, and expected files because that is the treatment
  being evaluated.
- Tier A/Tier B constrained generation: may use the System-HIS contract as the
  constraint source, but reported gains must be separated from the simple-prompt
  baseline by the prompt-information ablation in the reframe spec.
