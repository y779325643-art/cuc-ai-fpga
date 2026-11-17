# Explicit Boundary-Response Contracts for Auditing First-Generation Multi-Module RTL

Research draft v0.2 · 21 October 2026 · Development evidence; not a submission-ready manuscript

## Abstract

A generated RTL project can reproduce its required outputs while using a named submodule differently from an explicitly agreed architectural role. This distinction matters only when that role is part of the specification: ordinary functional equivalence does not by itself prohibit recomputation or other valid optimizations. We study an explicit boundary-response contract that states how all designated parent outputs must respond when one child output is replaced by an independent value, including behavior outside an activation guard. An artifact-local checker combines a closed integer-expression representation, actual RTL-target binding, finite response checks, and guards for effective intervention, unchanged inputs, and restoration. The method uses established cutpoint verification. Three candidate-visible combinational profiles cover conditional ALU delegation, a composed MAC path, and staged saturated temporal-difference arithmetic. Six independent handwritten controls qualify the implementation: faithful versions pass, whereas ordinary-equivalent recomputation controls fail the additional contract. A manual ALU miter confirms the mature verification baseline. All twelve fresh native model outputs pass the finite checks, as do twelve same-child fixed-parent constructions. No contract violation or pass-count difference between the two prompt organizations is observed. The study supplies an inspectable audit prototype and a bounded null finding, not evidence of common model failures, physical resource preservation, or superiority to complete typed representations.

**Keywords:** RTL generation; explicit contracts; compositional verification; cutpoints; reproducibility; large language models.

## 1. Introduction

Generating a multi-module hardware project requires agreement about interfaces, arithmetic, and the responsibilities assigned to each module. A conventional output test answers whether the assembled design produces expected values on the tested inputs. It does not necessarily answer whether the parent uses a designated child result in the manner explicitly requested. For example, a parent may retain an adder instance yet recompute addition from the same operands. Both implementations can be normally equivalent. Whether the transformation is acceptable depends on the specification, rather than on the presence of an instance name.

This paper addresses an additional, deliberately explicit obligation. Before generation, the task author states the parent response to an arbitrary replacement at one child output. A guard identifies the inputs under which delegation applies; an inactive mapping states the required behavior otherwise. All designated external outputs are covered. The parent can still use raw operands for legitimate operations, and an independent output can remain unaffected. The contract therefore concerns a specified logical relationship, not ownership of a physical adder or proof that redundant arithmetic is absent.

Neither the verification principle nor the general idea of architectural intent is new. Cutpoint miters already expose differences hidden by a component's normal input/output relationship. Modern hardware-generation systems also construct hierarchy, constrain operations, and validate executable intent [1]–[8]. Our question is narrower: can an explicit local contract be represented, bound to actual generated RTL, and checked reproducibly without fully prescribing the parent's implementation? Any useful answer must compare against strict construction and established verification, and must retain failures that originate in the checking tools themselves.

The present contribution is an inspectable development study: three public arithmetic profiles with precise additional obligations; a closed-expression checker with actual-target binding and intervention guards; independently prepared positive and negative controls; and a bounded first-generation pilot with a uniform fixed-parent diagnostic. We do not claim the first architecture-aware RTL verifier, a new cutpoint algorithm, or a demonstrated general generation advantage. Establishing practical benefit over complete intermediate representations remains an empirical question.

## 2. Related work

### 2.1. Compiler-mediated and executable hardware intent

CPPL combines a frontend language for interfaces and hierarchy with a circuit IR and deterministic CIRCT lowering [1]. Its v1 hierarchy theorem concerns the projected instance tree; its frontend also implements real input bindings. The paper's ALU example already combines a child adder in one mode with raw-operand subtraction and bitwise operations in others. It is therefore a direct antecedent, not a naming-only baseline. The contemporaneous implementation preplaces instances whose input references are available and checks deferred instances against their module, identifier and arguments, while leaving remaining parent operations to generation [2]. Its constant-output child stubs support static validation; they are not independent replacement variables with a parent-response scoreboard.

Version separation is essential. The later fixed CPPL repository revision adds executable patterns, hierarchical evaluation, and internal probes [3]. Its worker validates and infers the candidate IR before pattern execution; the interpreter computes real dependencies and reads internal values through probes. Those capabilities cannot be attributed automatically to the earlier experiment snapshot, nor can current CPPL be described as static validation only. Reading normal internal values differs from independently replacing a child output, but we have not executed a counterexample through CPPL. Its deterministically lowered correct parent graph, or a stricter graph supplied in advance, can prevent the behavior considered here.

HINT explicitly represents hardware-relevant units, interfaces, ownership, state, resources, and lowering obligations [4, §§3–4]. Reference/native transaction checks accept the representation before RTL lowering; HINT–RTL cosimulation checks data and transaction timing afterward. Its lowering is agentic, not merely a deterministic compiler pass. The paper distinguishes observable behavior and transaction timing from formal internal structural equivalence, while reporting a specific netlist-equivalence check for Hif8_mul. Its controlled RQ1 uses a shared 20-revision correctness budget without HINT Lint; checker-enabled workflow results must not be conflated with that condition. These are substantial existing guarantees. They do not establish our exact additional free-boundary relation, but neither do they imply that accepted HINT implementations permit recomputation. A sufficiently complete accepted representation can remove that freedom. The complete author specification and implementation were not available for our audit.

### 2.2. Signal-level refinement and hierarchical generation

VeriRefine represents each driven signal using a hardware class and prioritized guarded actions anchored to specification text [5, §§3.2–3.4]. Its audit addresses interpretation before generation; its implementation rules require fidelity to those actions. The documented deterministic gates include interface validation, internal tri-state checking, and compilation. The inspected paper does not establish an independent proof of every generated action's RTL semantics, and an attributable author implementation was not located in our bounded review. This is an evidence limitation, not evidence that such implementation checks are absent. A complete faithfully realized signal representation is a strong alternative to our local obligations. Moreover, VeriRefine-Direct omits the simulation-repair loop, so first-generation evaluation alone is not a new distinction.

VeriGraphi builds a specification-anchored representation of hierarchy, interfaces, and connections, then progressively generates modules and assembles the parent with feedback [6, §III, Algorithm 1]. Its architectural scaffold also goes beyond informal prompting. We do not reproduce these systems or compare our small arithmetic profiles with their published benchmark results.

### 2.3. Established cutpoint verification

Cutpoints long predate LLM-based generation. In adapting the established hardware technique to embedded-software equivalence, Feng and Hu describe replacing equivalent internal logic by new primary inputs and explain false inequivalence caused by unreachable value combinations [9]. This distinction motivates explicitly agreeing on the replacement domain rather than treating every free-boundary mismatch as a normal functional defect.

EQY matches actual elaborated designs and creates partitions with corresponding inputs on the gold and gate sides [7], [8]. Its source turns suitable matched, non-bound internal bits into partition inputs and emits comparison miters. The official `ex_bind` example is especially relevant: both designs compute `X=A^B` and `Y=B^C`, but one computes `Z=X^Y` and the other `Z=A^C`. Normal functions agree; independently varying the intermediate values changes the relation. Its configuration uses `bind` to retain upstream constraints [7]. This is direct prior capability, not merely hypothetical solver expressiveness.

Our contract deliberately selects an independent-response obligation that ordinary equivalence may not require. Standard miters can express it. The potential practical increment concerns explicit obligation preparation, reliable RTL binding, supported implementation freedom, and audit effort. We have not implemented an EQY adapter or shown an advantage over it. The bounded source review and unresolved implementation questions are recorded separately in the [two review reports](../discussions/structure-generation-paper/neighbor-deep-review-cppl-hint.md) and the [VeriRefine/EQY review](../discussions/structure-generation-paper/neighbor-deep-review-verirefine-eqy.md).

## 3. Problem definition

Let a combinational design D have ordinary inputs x, output vector y, and a selected child-output boundary b. In the intact design, the child produces h(x), while the parent context produces P(x,h(x)). The normal specification is N(x). Normal conformance requires the intact outputs to equal N(x); the checked target's intact value must also match its declared local expectation on the selected ordinary inputs.

Let P_D^b(x,z) denote the actual generated context after replacing only boundary b by an independently supplied value z. The task author declares an ordinary-input domain X, a replacement domain Z, a guard g(x), an active response A(x,z), and an inactive response I(x). The additional obligation is

\[
\forall x\in X,\ \forall z\in Z:\quad
P_D^b(x,z)=
\begin{cases}
A(x,z), & g(x)=1,\\
I(x), & g(x)=0.
\end{cases}
\]

Both response mappings cover every designated external output. In these profiles, they completely specify the external parent-context function of (x,z). "Local" refers to the selected boundary, not to an incomplete specification of that external function. Internal signal organization and physical realization remain open; a minimal complete IR may permit the same choices. No reduction in specification work follows from this distinction alone. Inactive behavior is independent of z. A constant-true guard is valid; a guard never exercised by a finite evaluation cannot support a passing verdict. Fixed-width encoding occurs at explicitly declared outputs, and signed replacements are decoded before mathematical evaluation.

This contract is stronger than intact functional equivalence and is not inferred from an instruction such as “use the adder.” Replacements may create combinations impossible for the real child. A mismatch is therefore an explicit profile violation, not automatically an ordinary functional defect. The obligation neither proves unique computational responsibility nor prohibits every redundant expression. Equivalent expressions that retain the same response are acceptable. Physical utilization, timing, and post-synthesis topology are separate questions.

## 4. Checker and public profiles

### 4.1. Closed mathematical representation

The development API, `public-comb-free-boundary-v0.1`, stores ports, sources, the target path/type, normal mathematics, a target-value expectation, guard, active/inactive mappings, and finite input/probe selection. Expected expressions use a closed JSON AST of input, integer, and probe atoms, arithmetic and bitwise operators, comparisons, conditional selection, floor division, and saturation. There are no candidate callbacks or Python evaluation. Arbitrary-precision integer expectations avoid accidental reference-model overflow; results are encoded to the declared port widths only for comparison.

The schema validates operator arity, identifiers, complete output mappings, explicit source paths, and bounded domains. Metadata describing additional instances is descriptive rather than executable. This distinction matters: the implemented binding checks the selected target and top-level types, not every architectural declaration in metadata.

### 4.2. Binding and tool guards

`build_catalog` snapshots the selected sources, invokes Yosys elaboration and process lowering without optimization or flattening, and stores a module/cell/port catalog. `evaluate` checks source hashes and resolves the actual instance path through cell types. It verifies top ports and the target's output direction, width, signedness, and parent connection width. Sequential or memory cells are outside the combinational profile.

A generated Icarus testbench first checks intact external outputs and the selected child's normal value. For every chosen replacement, it forces the actual target, confirms the forced value, compares the declared response, and verifies that both the DUT inputs and testbench drives remain unchanged. It then releases the target, checks restoration, and rechecks intact outputs. An input-integrity failure takes priority over response mismatches and is classified as an unknown intervention outcome. This prevents a tool-induced change of ordinary inputs from being called a contract violation.

The checker retains commands, logs, vectors, testbenches, catalog connections, counts, timings, and hashes. Each tool stage has a 30-second limit; intervention selection is capped at one million input/probe pairs. Invalid input, missing binding, incomplete coverage, compilation diagnosis, timeout, and ineffective intervention remain distinct from a completed response failure. Source scanning restricts the accepted HDL surface, but is not a general adversarial sandbox. Snapshots and hashes provide provenance, not authenticated external catalogs or operating-system isolation.

### 4.3. Three newly defined profiles

The [public specification](../../../artifacts/codex-responsibility-cross-task-20261021-01/public-tasks.md) was frozen before generation. Here “public” identifies the candidate-visible information boundary and fully specified development tasks, not an external dataset or software release. These new combinational profiles adapt existing arithmetic concepts; they do not inherit qualification of historical clocked FPGA tasks.

| Profile | Normal mathematics | Selected boundary and required response | Evaluated domain |
| --- | --- | --- | --- |
| ALU4 | Unsigned4 add/subtract modulo16, AND, OR selected by mode | `u_add.sum`, unsigned4; add mode returns z; other modes retain their functions independently of z | 1,024 inputs ×16 replacements |
| FIR4 | `filtered=wrap7(3*x0-2*x1+x2)`; signed5 `edge_value=x0-x2` | Signed7 `u_prev.result` in a three-MAC chain; `filtered=wrap7(z+x2)`, edge unchanged | 4,096 inputs ×128 replacements |
| TD8 | Q4 discounted return and staged sat8 update | Signed17 `u_return.discounted_return`; expose z and recompute downstream error/update from it | 64 sampled inputs ×19 public replacements |

FIR samples are signed4, coefficients signed3, and MAC accumulators/results signed7. Its contract exercises propagation through a downstream component while preserving a raw-input output. TD8 has signed8 reward, next value and value, with unsigned8 gamma and alpha. Define `sat8(t)=min(127,max(-128,t))` and floor division by 16. Its return is `R=reward+floor(gamma*next_value/16)`; downstream values are `E=sat8(R-value)`, `D=sat8(floor(alpha*E/16))`, and `U=sat8(value+D)`. Replacing R by any signed17 z requires exact subtraction before saturation: z−value needs at least 18 signed bits. The finite TD probes include extreme signed17 patterns but do not exhaust that domain.

## 5. Experimental design

### 5.1. Questions and evidence units

RQ1 asks whether the checker accepts faithful controls and rejects ordinary-equivalent controls that violate the explicit response. RQ2 asks what conformance is observed in a small first-generation model pilot and whether reorganizing the same obligations changes those observations. RQ3 asks what changes when a fixed faithful parent is substituted while preserving each generated child's bytes. The questions distinguish implementation qualification, observed generation behavior, and construction guarantees.

Three evidence populations remain separate: independently handwritten qualification controls; a manual ALU miter over two earlier handwritten parents; and twelve newly generated projects. Earlier native TD sentinels are process-development background and do not enter the twelve-position denominator. A negative control is not a sampled model error.

### 5.2. Qualification and independent miter

Before model generation, one faithful and one recomputing bypass implementation were prepared independently for each full-width profile. They retained the selected instances; the bypass parent recomputed ordinary outputs from raw inputs. Controls, profiles and checker bytes were frozen before six sequential binding/compile/simulation evaluations. Each faithful control had to pass before its negative control was evaluated. Unexpected tool or binding outcomes would stop the sequence without retrying or adjusting expectations.

The separate manual ALU baseline excludes the real adder and provides an independently driven replacement module. It enumerates all operands, modes and replacement values without importing the automated checker or using force/release. It compares a faithful delegate with a handwritten wrong-mode implementation that normally agrees but routes the child contribution into the wrong mode. Agreement with this established miter is a correctness check, not new detection power.

### 5.3. First-generation pilot and fixed-parent diagnostic

The frozen scope comprises three tasks, two prompt organizations and two fresh attempts per organization: twelve positions. The global prompt expresses the complete additional obligation in prose. The located prompt reorganizes identical public facts under boundary, guard, active, inactive and output-scope fields. Both receive all normal mathematics, interfaces, hierarchy and response obligations. Thus the comparison concerns presentation, not withholding the contract from a baseline. It is not a reproduction of CPPL, HINT or VeriRefine.

Fresh native child sessions received the prepared prompt, no forked conversation history, no reference RTL, no test vectors and no evaluation feedback. Final JSON and source strings were captured before parsing and were not repaired. Limits covered allowed paths, file lines/bytes and total response bytes. They were validation limits, not native token caps. The fixed dispatch order was recorded before generation; no best-output selection was permitted. Every planned position, including invalid or unrun positions, belongs in the accounting.

For all accepted outputs, the predeclared diagnostic replaces the top with the same faithful qualification parent while retaining that output's unchanged child files. These constructions are materialized uniformly before inspecting candidate HDL outcomes. They are separate program-owned designs, never repaired first outputs. This strong comparison can eliminate parent freedom by construction. Because the children came from whole-project calls, it cannot measure an optimized child-only generation cost.

### 5.4. Runtime provenance and analysis

The [runtime audit](../../../artifacts/codex-responsibility-transport-20261021-01/runtime-audit.json) records twelve initialized fresh children with observed configuration `gpt-6.1-sol`, effort `ultra`, and zero recorded tool calls or later parent feedback. Thirteen wrapper invocations include one thread-limit refusal before child initialization; there were twelve actual model generations and no generation retries. Ten distinct source bundles occur among the twelve outputs. Duplicate attempts remain in the denominator but are not ten or twelve independent task designs.

Native dispatch offers no hard tool-denial field. Zero observed calls is therefore a trace observation, not an enforced impossibility. Configuration records are not provider snapshot attestation. Opaque/encrypted runtime input records were not decrypted, so prompt hashes and prepared dispatch records do not establish an end-to-end plaintext-input attestation.

Reported usage is 363,002 input tokens, including 333,056 cached input tokens, and 10,772 output tokens, including 4,336 reasoning-output tokens; total 373,774. Reasoning tokens are a subset, not an additional total. Global and located totals are 186,980 and 186,794, respectively, with different cache/input counts. Counts include native platform context rather than only the task prompt. These observations do not establish equal cost, monetary savings or a prompting benefit.

Analysis reports task/arm counts and each status reason. Scalar mismatches, failed projects and independent tasks are different denominators. The pilot is descriptive: two attempts per task/arm, common infrastructure, duplicate bundles and only three deliberately constructed profiles do not support a population-level error rate or causal generalization.

## 6. Results

### 6.1. Full-width handwritten controls

All six controls met their predefined qualification conditions under checker SHA256 `2e589ea4d2241582db5af80439a5bbc898dc4ac66234fe21bd4bd5c69c5f7e24`. Faithful controls passed intact and response comparisons. Bypasses passed all intact external and selected-target comparisons but failed the additional response. Each force, input-integrity, release and restored-output failure counter was zero.

| Profile | Ordinary vectors per control | Response scalar comparisons per control | Faithful response mismatches | Bypass response mismatches |
| --- | ---: | ---: | ---: | ---: |
| ALU4 | 1,024 | 16,384 | 0 | 3,840 |
| FIR4 | 4,096 | 1,048,576 | 0 | 520,192 |
| TD8 | 64 | 3,648 | 0 | 2,845 |

FIR compares two outputs and TD three, so scalar comparison totals exceed input/probe-pair totals. Exactly six Yosys bindings and six compile/simulation pairs were executed without retry or timeout. The negative simulations' nonzero exits are retained as expected completed profile rejections. All frozen inputs and original disabled public profiles remained unchanged; only local copies were enabled. The [qualification report](../../../artifacts/responsibility-full-profile-qualification-20261021-01/results.md) supplies raw commands, logs and hashes. These results establish finite discrimination on six handwritten designs, not natural model failure prevalence.

### 6.2. Independent manual-miter agreement

The manual ALU delegate passed 16,384/16,384 free-boundary combinations. The wrong-mode control passed 8,704 and failed 7,680: 3,840 mismatches in add mode and 3,840 in subtract mode, with none in the bitwise modes. Both passed the 1,024-case normal projection where z equals the real sum. The independently constructed check agrees with the expected earlier development verdicts. It covers this finite ALU obligation and these two parents; it does not prove arbitrary automated binding or qualify every full-width profile.

### 6.3. Native outputs and uniform construction

The completed [machine-readable summary](../../../artifacts/codex-responsibility-transport-20261021-01/evaluation-summary.json), marked `complete: true`, and [evaluation report](../../../artifacts/codex-responsibility-transport-20261021-01/evaluation-results.md) record all twelve original positions and twelve uniform fixed-parent constructions. Every position passed the declared finite checks. No position was failed, invalid, unknown, disabled or unrun, and the frozen-input verification succeeded.

| Profile | Original first outputs passed/planned | Same-child fixed-parent designs passed/planned | Normal scalar comparisons per evaluation arm | Response scalar comparisons per evaluation arm |
| --- | ---: | ---: | ---: | ---: |
| ALU4 | 4/4 | 4/4 | 4,096 | 65,536 |
| FIR4 | 4/4 | 4/4 | 32,768 | 4,194,304 |
| TD8 | 4/4 | 4/4 | 768 | 14,592 |
| Total | 12/12 | 12/12 | 37,632 | 4,274,432 |

Each evaluation arm also completed 20,736 intact target-port comparisons, 2,167,552 input/probe pairs and 6,512,384 input-integrity scalar comparisons, with zero normal, targeted-local, response, force, release, restored-output or input-integrity failures. The original global and located conditions each passed 6/6; each task/condition contributes two attempts. Thus the pilot observed zero response violations and no pass-count improvement from located presentation or the fixed-parent construction. It does not establish statistical equivalence of the prompting conditions or eliminate untested failures.

The 24 completed evaluations used 24 Yosys bindings and 24 compile/simulation pairs. They comprise twelve model outputs and twelve program-owned constructions, not 24 independent model generations. Construction required no new model calls. The comparison demonstrates no conformance advantage for either implementation route on these finite checks; it does not establish equal generation cost or superiority of the auditing workflow. Handwritten negative-control mismatches remain outside this native denominator.

## 7. Discussion

### 7.1. What an audit adds

The qualification controls separate ordinary functionality from an additional agreed relationship. They do not show that ordinary equivalence is defective: it answers a different question and can legitimately accept recomputation. Likewise, an instance retained after some optimization or a live dependency somewhere in a design does not imply a particular mode-dependent response. Explicit contracts make that distinction reviewable without calling every legal optimization an error.

The implementation contribution is limited but concrete: a shared mathematical representation, binding against actual elaborated objects, and retained evidence of both response and tool validity. Input-integrity checks are necessary because intervention can interact with aliases. Passing their qualification fixtures is an observation about the selected tools, not a theorem about all simulators. A formal backend using explicit replacement inputs could strengthen coverage, but would still implement an established obligation rather than create a new cutpoint technique.

### 7.2. Strong alternatives and unresolved value

A fixed faithful parent can prevent the relevant response violations directly. CPPL can deterministically lower a correct parent graph; complete ASTF or HINT intent can constrain substantial behavior before RTL exists. Our checker is not structurally more comprehensive than those systems. Its possible value lies in representing and auditing explicit boundary obligations with traceable RTL binding. The current all-output mappings already determine the entire external context function; they do not demonstrate a behaviorally smaller specification. They omit internal signal-by-signal organization, but a minimal complete IR may do so as well. Neither lower modeling cost nor a larger useful implementation space has been established. Writing the response mappings may require as much work as specifying the parent directly.

A fair follow-up must compare obligation-writing effort, actual-object mapping, accepted legal variations, unknown outcomes and coverage against a standard miter/EQY adaptation and a complete-IR construction. It should preserve identical mathematical domains rather than handicap the stronger alternatives. If those approaches achieve the same freedom and reliability with no additional effort, the case for a distinct method weakens. A workflow label or different call order is insufficient evidence of originality.

### 7.3. Threats to validity

The profiles were manually added, selected for clarity, and made the strong obligations unusually explicit. They are not an unbiased benchmark sample or direct reuse of released task qualification. ALU and FIR exhaust their stated finite input/probe domains, but neither task diversity nor sequential behavior follows. TD samples only 64 ordinary inputs and 19 replacement values, despite a full signed17 contract. No whole-domain TD proof is reported.

Catalog binding covers one target, its type and connection width, plus the top interface. It does not separately prove every required instance/input binding or every leaf's complete local function. Normal target checks cover only values induced by selected top inputs. Contract validity and the author's reason for requiring off-manifold behavior remain external responsibilities. Source scanning and native traces do not establish security isolation or immutable model identity.

The small repeated pilot cannot establish that violations are common or that one prompt organization generally helps. The observed zero-violation result provides no demonstrated incremental detection benefit on these twelve first outputs. It limits the observed need for this audit on these tasks rather than justifying an efficacy claim. The fixed-parent diagnostic changes implementation freedom and is not an equivalent generative cost comparison. No PPA, board execution, timing, clock/reset protocol or synthesis-preserved resource result is measured. Published neighboring frameworks have broader aims; absence of an exact described workflow in our bounded review is not proof of novelty.

## 8. Conclusion

Explicit boundary-response contracts distinguish a deliberately agreed local architectural obligation from ordinary functional equivalence. The artifact-local implementation qualifies on three combinational profiles and independent handwritten controls, with a manual ALU miter confirming the established baseline. All twelve native first outputs and twelve same-child fixed-parent designs passed their finite evaluations. There were no observed violations or pass-count gains from prompt organization or fixed-parent construction. These findings support a reproducible audit object and tool prototype, while leaving general generation improvement, reduced engineering effort and incremental methodological value unestablished. Further work should compare setup cost, supported coverage and accepted implementation freedom against standard compositional verification and strict construction.

## Data, code, and research status

The data and code are locally inspectable in this repository's development artifacts; they have not been externally released or deposited. An external release remains subject to the authors' decision. [Candidate-visible profiles and input manifest](../../../artifacts/codex-responsibility-cross-task-20261021-01/input-manifest.json), [execution scope](../../../artifacts/codex-responsibility-transport-20261021-01/execution-scope.md), [runtime audit](../../../artifacts/codex-responsibility-transport-20261021-01/runtime-audit.json), [completed native/construction evaluation](../../../artifacts/codex-responsibility-transport-20261021-01/evaluation-summary.json), [full-width qualification](../../../artifacts/responsibility-full-profile-qualification-20261021-01/results.md), and [manual miter](../../../artifacts/responsibility-manual-miter-20261021-01/results.md) preserve distinct evidence populations. No official evidence promotion is claimed. AI assistance was used for research, code preparation and drafting; the generator configurations are described separately from this development role. Author names, affiliations, venue formatting and final disclosure require author review.

## References

1. S. Yin et al., “CPPL: A Circuit Prompt Programming Language,” arXiv:2605.17892v1, 2026. [Official version](https://arxiv.org/html/2605.17892v1).
2. CPPL authors, frontend compiler, prompt and validator, commit `838aab3d81237baefdd4807ce0d09a8146192efc`, 17 May 2026. [Compiler](https://github.com/SawyDust1228/CPPL/blob/838aab3d81237baefdd4807ce0d09a8146192efc/cppl/frontend/compiler.py#L75), [prompt](https://github.com/SawyDust1228/CPPL/blob/838aab3d81237baefdd4807ce0d09a8146192efc/cppl/frontend/prompt.py#L227), [validator](https://github.com/SawyDust1228/CPPL/blob/838aab3d81237baefdd4807ce0d09a8146192efc/cppl/ir/validator.py#L21).
3. CPPL authors, executable patterns and interpreter, commit `d7ebbb5f4036ac57a768bc362996ab05e8c39b9f`, 19 August 2026. [Pattern execution](https://github.com/SawyDust1228/CPPL/blob/d7ebbb5f4036ac57a768bc362996ab05e8c39b9f/cppl/ir/patterns.py#L71), [interpreter](https://github.com/SawyDust1228/CPPL/blob/d7ebbb5f4036ac57a768bc362996ab05e8c39b9f/cppl/ir/interpreter.py#L132).
4. T. Cheng et al., “HINT: Toward an Executable Hardware-Intent Representation Layer for LLM-Driven RTL Generation,” arXiv:2608.07625v2, 2026. [Official version](https://arxiv.org/html/2608.07625v2).
5. X. Kong, T. Tabassum, M. Abdelwahab, and H. Zheng, “A Progressive Approach to Synthesizable RTL Design Generation Using LLMs,” arXiv:2607.18519v1, 2026. [Official version](https://arxiv.org/html/2607.18519v1).
6. S. Islam, T. Tabassum, and H. Zheng, “VeriGraphi: A Multi-Agent Framework of Hierarchical RTL Generation for Large Hardware Designs,” arXiv:2604.14550v2, 2026. [Official version](https://arxiv.org/html/2604.14550v2).
7. YosysHQ, EQY source, commit `fb8b21160297b3e66bf94f3c24f8a8bf1cd3fd51`, accessed 21 October 2026. [Partition implementation](https://github.com/YosysHQ/eqy/blob/fb8b21160297b3e66bf94f3c24f8a8bf1cd3fd51/src/eqy_partition.cc#L571), [miter generation](https://github.com/YosysHQ/eqy/blob/fb8b21160297b3e66bf94f3c24f8a8bf1cd3fd51/src/eqy_partition.cc#L1075), [ex_bind design](https://github.com/YosysHQ/eqy/blob/fb8b21160297b3e66bf94f3c24f8a8bf1cd3fd51/examples/simple/ex_bind.sv), [configuration](https://github.com/YosysHQ/eqy/blob/fb8b21160297b3e66bf94f3c24f8a8bf1cd3fd51/examples/simple/ex_bind.eqy).
8. YosysHQ, “EQY Documentation,” accessed 21 October 2026. [Configuration](https://yosyshq.readthedocs.io/projects/eqy/en/latest/config.html), [output artifacts](https://yosyshq.readthedocs.io/projects/eqy/en/latest/outdir.html), [equivalence and X-propagation](https://yosyshq.readthedocs.io/projects/eqy/en/latest/xprop.html).
9. X. Feng and A. J. Hu, “Cutpoints for Formal Equivalence Verification of Embedded Software,” EMSOFT 2005. Technique and false-inequivalence discussion: PDF pp. 1–2. [Author-hosted paper](https://www.cs.ubc.ca/~ajh/mypapers/2005FH.pdf).
