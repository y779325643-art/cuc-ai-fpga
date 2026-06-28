# SR2FPGA Research Reframe Design

## Status

Approved direction; **last updated 2026-06-26.** The agreed research line for Paper ①,
scoped from `docs/research-objective-sr2fpga-tcad.md`, decomposed into a publishable
program with full spec. The Chinese companion
(`2026-06-22-sr2fpga-research-reframe-design.zh.md`) is kept in sync. Where this
spec and the objective doc differ, this reframe governs near-term work.

**Current state (as of 2026-06-26):**
- System-HIS v1.2 frozen and implemented (Tier-1 ratification gate met)
- L0–L3 data-generation agent runs with objective tool oracle; multi-teacher source merged
- Discovery-level pilot findings documented (N≈1/tier, exploratory, not scaled evidence)
- **Not yet:** scaled trajectory data, trained model (c) / RQ3, L4 physical (OpenXC7 spike), data-quality fixes (F/E/G)
- **Three gates to TCAD:** (1) train model at scale under frozen protocol; (2) build constrained decoding; (3) land verified L4/L5 with Vivado commercial reference

See **Changelog** at the end for dated update history.

---

## Table of Contents

- [§1 Program Overview](#1-program-overview)
- [§2 Motivation](#2-motivation)
- [§3 Core Research Principle](#3-core-research-principle)
- [§4 Research Questions](#4-research-questions)
- [§5 Related Work & Differentiation](#5-related-work--differentiation)
- [§6 System-HIS Intermediate Representation](#6-system-his-intermediate-representation)
- [§7 Evaluation Framework (L0–L5)](#7-evaluation-framework-l0l5)
- [§8 Benchmark Design](#8-benchmark-design)
- [§9 Data Engine](#9-data-engine)
- [§10 Method: Tool-Internalizing Model Stack](#10-method-tool-internalizing-model-stack)
- [§11 Experimental Design](#11-experimental-design)
- [§12 Validity, Claims & Review](#12-validity-claims--review)
- [§13 Paper ② Overview](#13-paper--overview)
- [§14 Artifacts & Reproducibility](#14-artifacts--reproducibility)
- [§15 Immediate Next Steps](#15-immediate-next-steps)
- [§16 Document Relations & Companion Specs](#16-document-relations--companion-specs)
- [Changelog](#changelog)

---

## §1 Program Overview

### 1.1 One-sentence thesis

SR2FPGA generates multi-module, cross-file-consistent RTL **projects** from
system requirements **through a System-HIS intermediate representation**, drives
them through a **reproducible flow** to **L4 timing closure** (plus L5 on-board
cases on the AC820-ZYNQ), and quantifies each level with an **L0–L5 project-level
evaluation**; on this evaluation, a tool-verified fine-tuned model
internalizes tool acceptance and improves generation + self-repair
under a fixed iteration budget.

中文定位：**面向系统需求的项目级 RTL 工程生成——以 System-HIS 中间表示 + 项目级 L0–L5
评测 + 可复现 req→bitstream→上板闭环（AC820-ZYNQ）为贡献，并以工具验证轨迹微调一个
模型，使其内化工具接受度、在固定迭代预算下提升生成与自修复。**

### 1.2 Program decomposition

This is a 2–3 paper program, not one paper:

```
Paper ①  Foundation: the tool oracle's dual role
         ├─ System-HIS + project-level L0–L5 benchmark + reproducible
         │  req→bitstream→board closed loop      (evaluation / data contribution)
         └─ tool-verified fine-tuned model: generation + self-repair  (method contribution)
                    │  produces: reproducible eval + trajectory data + QoR predictor
                    ▼
Paper ②  Optimization: tool-in-the-loop QoR search (LUT / performance / power)
         └─ GA over architecture params / RL with tool reward,
            using Paper ①'s QoR predictor as a fast proxy fitness
```

The dependency is organic: Paper ②'s killer is that tools are too slow for the
thousands of evaluations GA/RL need; Paper ①'s QoR predictor (a tool
distillation) is exactly the fast proxy fitness that unblocks Paper ②. So doing
① first is not a delay — it is ②'s prerequisite and accelerator.

GA/RL and "retrain a large generation model" are **out of scope for Paper ①**
(a teaser + future work paragraph only).

### 1.3 Target venue

**Primary target: IEEE TCAD**, with **ACM TRETS as the fallback** — aim high,
decide at submission by what was actually achieved. Both reward the
physical-realization + reproducibility story; TCAD additionally demands the
method novelty TRETS relaxes (see §12.1). A helper for either: the
**AC820-ZYNQ (XC7Z020) is a mainstream commercial Xilinx device**, so TCAD's
"is this realistic silicon?" reflex is already answered.

- **Physical realization is the main dish, not a garnish:** L4 timing closure +
  L5 on-board runs + resource/Fmax/power reporting are core evidence.
- **A fully open, reproducible closed loop** (req→bitstream→board) is a primary
  selling point TRETS rewards. The author's **AC820-ZYNQ board (chip
  XC7Z020CLG484-2) is in OpenXC7's support list**, so an all-open
  Yosys→nextpnr-xilinx (OpenXC7)→bitstream→board flow on a *real Xilinx device*
  is feasible — pending a spike verification. All code/data/scripts/device public,
  tool versions pinned.
- **Open primary flow + commercial reference:** OpenXC7 remains the primary
  reproducible open flow. However, for the **TCAD-strong** version, a
  representative L4 subset must also be validated with **Vivado** as the
  commercial Xilinx reference flow. Vivado is **not** used for every Line-B
  training trajectory and does **not** replace the open flow; it is an industrial
  sanity check for timing, QoR, DRC/methodology warnings, and constraint validity.
  (For **TRETS-safe** work, Vivado stays an optional fallback/baseline.)
- **For TCAD, SR2FPGA should not claim physical FPGA realizability from an open
  flow alone. The defensible position is: OpenXC7 provides the reproducible open
  path; Vivado provides commercial reference validation on a representative L4
  subset; L5 provides sparse end-to-end board feasibility evidence.**
- **Method novelty is the gap to close for TCAD:** TCAD will not accept "QLoRA
  fine-tuning + a tool loop" as the method contribution — it needs a genuine
  methodological idea (see §10.6), plus scale beyond the TRETS minimum. If
  novelty/scale do not land, drop to TRETS; the rest of the paper is unchanged.

### 1.4 Hard constraints

- **Compute:** single RTX 4090 24 GB for any local fine-tuning. **Not feasible:**
  pretraining or training a generation model that beats GPT-5 / DeepSeek
  head-to-head — that ambition is abandoned. **Model size is deliberately not
  fixed now:** dataset and benchmark design must stay model-agnostic; model and
  scale are chosen at the modeling stage from whatever compute is available then.
  **Current priority is building the dataset.**
- **Data:** none exists; all trajectories are generated from scratch by running
  tools locally. **Public training labels come primarily from open-source tools**
  (Verilator/Icarus/Yosys for L0–L3, OpenXC7 for L4-open), so "tool-verified
  learning" is literally true — the supervision is the tool, not another LLM.
  **Vivado labels are commercial-reference labels** on a representative L4 subset,
  separated from the `open_public` training tier unless institutional license review
  permits release. Labels are never sourced from another LLM. *Tool internalization
  means learning from tool-verified labels under declared tool flows; it does not
  mean reverse-engineering or reproducing proprietary EDA software.*
- **Hardware:** on-board validation uses the author's **AC820-ZYNQ board** —
  chip **XC7Z020CLG484-2** (~53k LUT, 220 DSP, dual-core ARM; large enough for
  big designs and an RL flagship case). The device is **in OpenXC7's support
  list**, enabling an all-open req→bitstream→board flow (subject to spike
  verification); **Vivado is the fallback/baseline**.

---

## §2 Motivation

### 2.1 Why this question matters (the external case)

The driving question — *can the judgement of the EDA toolchain be internalized
into a model so it generates, diagnoses, repairs, and predicts the quality of
project-level, multi-file, physically-realizable FPGA RTL from a requirement,
without calling the tools at inference?* — is worth asking for three compounding
reasons:

- **The tool is ground truth, but unusable at inference scale.** EDA tools
  (Verilator/Yosys/nextpnr/board) give an *objective* pass/fail verdict, not
  another model's opinion — but they are expensive, slow, external, and
  non-differentiable. Today's LLM-RTL flows are therefore stuck between (a)
  ignoring tools (generate + pass@k on simulation — but "sim-pass ≠ silicon":
  Representation Bottleneck reports 48% unconditional end-to-end, and the field's
  own practitioners note "fast isn't the skill, board-ready is") and (b) calling
  tools in a loop every inference (mature but slow/costly, and **un-scalable for
  L4 P&R at minutes/sample** — exactly Paper ②'s blocker). Internalizing the tool
  verdict would give *tool-quality output at LLM speed/cost*, unblocking
  large-scale QoR-proxy search, toolchain-free generation, and accessibility for
  domain experts.
- **It tests a genuine, measurable scientific claim.** "Is hardware
  correctness/realizability a *learnable function* of the design, or does it
  fundamentally require running the tool?" is a true/false question answerable
  against objective ground truth (the tool), not self-reported quality.
- **The field's easy region is saturated; the hard region is exactly this.**
  Single-module simulation benchmarks (VerilogEval) are near ceiling; the unsolved
  region is **cross-file consistency + physical realizability** — which the
  TODAES'25 survey, the ChipSeek-R1/MasterRTL/POET future-work statements, and
  Representation Bottleneck's explicit call for "an LLM-native IR separating intent
  from implementation" all point to. Project-level + physical is where models
  actually fail and where the science is.

**Honest framing of the question (a threat-aware reformulation):** the right
question is *how much* of the tool verdict is internalizable and *where it stops*
— not whether the tool can be fully replaced. Some quantities are physics-bound
and out of reach (CDC metastability, board signal integrity; see §12.1). So success
is **not** "replace the tool"; it is the measured deltas **(b−a)** and **(c−a)**
— how much tool-in-the-loop feedback and tool-verified fine-tuning each add — plus
mapping the L0–L5 boundary of what internalizes vs what must stay with the tool.
A partial answer is still a result.

### 2.2 Why the reframe (the internal trigger)

A harsh-reviewer pass over the current state found a real risk: the project has
a high-quality data pipeline but **no scientific result yet**, and its initial
tasks (`counter`, `fifo`, `simple_fsm`, `ram_read_write`) are too easy — strong
base models pass them at L3 in one shot, so the repair loop never triggers and
`failure_to_patch` stays empty. Fixing the task difficulty is the root that
relieves most downstream symptoms.

This reframe keeps the author's true goal — **a model that generates a complete
RTL project from a natural-language requirement and repairs it from tool
feedback** — but makes it defensible and feasible under the real resource budget.

### 2.3 Practical significance (real-world impact)

Distinct from the academic "why this question" above — who benefits, concretely:

- **Lowers the FPGA barrier for domain experts.** Fewer than 100k hardware
  designers exist, yet the people who best understand the workload (robotics,
  signal processing, embedded, edge-AI) mostly cannot write HDL. A reliable
  requirement→board-ready-project path lets them get custom hardware *without HDL
  fluency* — concrete targets: edge IoT, medical wearables, robotics control,
  small AI kernels, where ASICs are too costly and general-purpose processors too
  slow.
- **Time and license cost for teams already doing FPGA.** EDA flows are slow
  (sim minutes, P&R minutes–hours) and licensed (per-seat Vivado). Internalizing
  the tool verdict means *fewer tool iterations*, no license/compute at inference,
  and shorter design cycles — and if (c) approaches (b), tool-quality output
  without the expensive loop.
- **PPA optimization at small-team scale (Paper ②).** Searching architecture
  params (pipeline depth, parallelism, memory banks) for best power/area/Fmax today
  needs thousands of slow tool runs. A distilled fast QoR proxy makes that search
  feasible on one GPU — better-optimized, lower-power edge designs reachable
  without large compute.
- **Public goods that survive even if the model under-delivers.** A tool-verified
  project-trajectory dataset + L0–L5 benchmark + an **all-open, license-free
  req→bitstream→board flow** on a cheap real device (OpenXC7 on the AC820-ZYNQ)
  democratizes FPGA EDA for researchers and small companies that cannot afford
  commercial tools.
- **A concrete application anchor.** The edge-RL accelerator flagship on the
  AC820-ZYNQ lands the full chain on a real control/robotics workload.

**Honest ceiling (do not overclaim):** this does **not** replace FPGA engineers —
the realistic role is assistant + automated verification + first draft, not
autonomous tape-out. Physics-bound work (large-design timing closure, CDC
metastability, board signal integrity) stays with the tools/humans (see §12.1).
Real-world reach at PhD scope = **small/medium designs + an assisted workflow +
the dataset/benchmark/open-flow as public goods**, not a deployed product.

---

## §3 Core Research Principle

### 3.1 Distill the TOOL, not the LLM

The earlier worry was "you use DeepSeek to generate and repair, then train on
that → you are distilling DeepSeek." The author's actual intent is the opposite
and stronger: **distill the EDA tool oracle into a model.** EDA tools
(Verilator / Yosys / Vivado / board) are an expensive, slow, external,
non-differentiable oracle. The research question is whether their judgement can
be internalized so a model can generate, predict, diagnose, and repair RTL
*without* calling the tools at inference time.

The same tool oracle plays a **dual role**:

- it is the **judge** of the benchmark (evaluation / data contribution), and
- it is the **teacher** of the model (method contribution).

Evaluation and method share one tool judge, which keeps the story self-consistent.

To stay a *tool* distillation (not an LLM distillation):

- **inputs must be multi-source** — combinational component-library assembly,
  deliberately mutated/broken designs, real IP — not only one LLM's outputs;
- **all labels come from tools.**

This input distribution naturally produces many failures, which revives the
failure/repair trajectories by design rather than by luck.

### 3.2 Frontier models as the baseline (not a competitor)

A frontier model generating a complete project directly is **not a competitor —
it is a measurement point inside the chain**: it is exactly the
"first-half, no-tool-feedback, first-attempt generation" baseline. So "competing
with GPT" turns from a threat into the **baseline + ablation** of this work. A
stronger frontier model only raises the starting point; the scientific
contribution is **how much tool feedback adds on top of it**.

Frontier-model status (qualitative, **to be measured, not asserted from
numbers** — see §11.1): today's frontier models reliably handle
single-file / small RTL (this is why DeepSeek passed the smoke counter at L3 in
one shot) and can emit *formally* multi-file projects, but they do **not
reliably** produce large, strongly cross-file-consistent, timing-closing,
board-ready projects — cross-file/cross-module contract errors and L4 timing are
their failure region. That failure region is the open space this work targets,
and it is why benchmark difficulty must be calibrated to where the frontier pass
rate starts to drop.

---

## §4 Research Questions

The thesis decomposes into five concrete, answerable questions. Each names how it
is answered, the field gap it fills, and current status.

- **RQ1 — Representation.** Does inserting a requirement-level IR (System-HIS)
  between requirement and multi-file project improve cross-file consistency and
  physical realizability over direct req→project?
  *Answered by:* the System-HIS ablation (req→HIS→project vs req→project) on the
  cross-file-consistency error rate + L1–L4 pass. *Gap:* Representation Bottleneck
  (2026) shows IR choice > model and explicitly poses "an LLM-native IR separating
  intent from implementation" as future work; TODAES'25 lists NL↔RTL IR as
  unsolved; CPPL is circuit-level, not requirement-level. *Caveat:* the
  accessibility–competence paradox means this must be *measured*, not assumed.
  *Status:* the v1.2 generator + L0 HIS↔RTL cross-check are now implemented
  (Tier-1 ratified); the ablation still needs a trained model + the req→project
  arm; not yet run.
  *REQ→HIS fidelity sub-metric (added):* System-HIS must be faithful to the
  **original requirement**, not merely internally consistent with the generated
  RTL — otherwise a model can misread the requirement, emit a wrong-but-coherent
  HIS, and have RTL + testbench all follow the wrong HIS while L0/L2 still pass.
  For synthetic tasks the generator-emitted oracle HIS enables field-level
  comparison; for real/external tasks a small manually reviewed set is used.
  **REQ-HIS fidelity metrics:**
  - interface extraction accuracy: port names, directions, widths, protocols
  - clock/reset fidelity: polarity, synchronous/asynchronous kind, deassertion rule
  - parameter fidelity: width, depth, latency, parallelism, memory banking
  - behavior-intent fidelity: FIFO / arbiter / MAC / pipeline / AXI-lite / stream semantics
  - verification-intent fidelity: required scenarios and corner cases
  - constraint fidelity: target Fmax, resource budget, board shell/profile
- **RQ2 — Value of tool feedback (b−a).** How much does an EDA tool-in-the-loop
  repair loop raise project-level tool acceptance over a no-tool first attempt, and
  at which level / difficulty tier most?
  *Answered by:* (b)−(a) under a fixed iteration budget, per tier. *Gap:* repair
  loops are mature (AutoChip/MAGE/VerilogCoder/PEFA-AI) but single-module/sim, not
  project-level/physical with a reusable trajectory. *Status:* baseline (a)/(b)
  pilot ran (T1/T2 repair→L3, knee at T3); prompt-leakage already observed
  empirically (failure-repair Issue 4) → needs scale + a frozen prompt.
- **RQ3 — Internalization (c−a, c vs b).** Can tool-verified fine-tuning
  internalize tool acceptance so first-attempt-no-tool (c) approaches the
  tool-in-loop (b)? And can a fine-tuned *small* model's (c) reach a *large*
  frontier model's (a)/(b)?
  *Answered by:* (c) vs (a)/(b) on the same swappable generator. *Gap:* ChipSeek-R1
  internalizes via per-attempt RL, ASIC/single-module, no reusable dataset;
  Representation Bottleneck argues "IR-aware training > model scaling." *Scope of
  internalization:* generation + repair where the verdict is a function of what the
  model produced — **L0–L3, plus L4 *failure* diagnosis/repair**: nextpnr/Vivado
  emit structured P&R errors (`resource_overflow`, `routing_congestion`,
  `timing_violation` with the critical path, `constraint_error`) that map to
  actionable patches (reduce resource / restructure / add pipeline registers / fix
  XDC) — the same diagnosis→patch shape as L1–L3. What stays *outside* RQ3 (handled
  by RQ5 as prediction) is the continuous, seed-noisy *exact* Fmax margin for
  timing-pressured designs. *Status:* no model trained yet — the largest open piece,
  and the headline result.
- **RQ4 — Failure structure / difficulty calibration.** At project scale, where do
  frontier models start failing across (i) the difficulty axes and (ii) the L0–L5
  verification depth / hardware-semantic gap (seq-comb, backpressure, memory, CDC,
  timing)?
  *Answered by:* baseline (a) across T1–T4 + the per-level failure taxonomy
  (cross-file-consistency error rate + the hardware-semantic failure distribution).
  *Gap:* Representation Bottleneck only tested tiny single-module on Lattice
  (synthesis "transparent"); project-level/Zynq is the excluded regime where L4
  binds; their seq (2.3×)/memory (43%) gradient backs our axes. *Status:* pilot +
  taxonomy exist; the T4 failure frontier pushed L0→lexical→lint→sim→functional is
  recorded as discovery; needs the full-level diagnostic mode + scale.
- **RQ5 — QoR prediction / shift-left.** Can the model predict QoR
  (LUT/FF/BRAM/DSP/Fmax) before tool execution, and how well does predicted
  correlate with tool-measured?
  *Answered by:* predicted_qor vs measured_qor calibration. *Training signal:* the
  **OpenXC7 batch L4 reports** (license-free + batchable is what makes enough L4
  labels collectable). *Learnability split:* post-P&R **utilization (LUT/FF/BRAM/DSP)
  is largely a function of the RTL × synthesis → more learnable**; **Fmax depends on
  the seed-noisy, backend-heuristic critical path → learnable as a predictor but with
  a noise floor / calibration gap** (report it honestly). *Gap:* MasterRTL does
  pre-synthesis PPA as a separate ASIC predictor; the shift-left survey names the
  predicted↔physical correlation as the open challenge. *Status:* gated — needs
  real measured QoR (OpenXC7 L4; Yosys L3 LUT is vacuous, Finding G); the OpenXC7
  spike now has a spec + plan; this predictor is also Paper ②'s proxy fitness.
  *Tool-flow split (added):* RQ5 predicts tool-measured QoR **under a declared
  tool flow** — **OpenXC7-QoR** and **Vivado-QoR** are separate labels. The
  OpenXC7 label supports the reproducible open flow and potentially larger-scale
  L4 labeling; the Vivado label is the commercial reference label on the
  L4-commercial subset. Cross-tool transfer/calibration is reported on the
  L4-agreement subset.

**Core vs gated:** RQ1, RQ2, RQ4 are the must-answer minimum publishable core;
RQ3 is the headline but needs a trained model; RQ5 is nice-to-have and gated on the
OpenXC7 L4 spike. All five are operationalized by the enabling infrastructure
contribution — the tool-verified project-trajectory dataset + L0–L5 benchmark +
reproducible req→bitstream→board loop — which is what makes them measurable.

**Principle — preserve the structured tool signal (do not binarize).** Every tool
stage emits far richer learnable signal than pass/fail + a coarse label, and the
trajectory dataset must capture the *structure*, not flatten it:

- **L2 sim:** not just `TEST_FAIL` but the **mismatch detail** (signal, expected vs
  actual, cycle; ideally the VCD) — exactly the diagnosis→patch signal (this is
  what VerilogCoder's AST waveform tracing exploits).
- **L1/L3/L4 warnings on *pass*:** "passed-but-warned" is *soft* signal (latch risk,
  width-extension, unused/undriven nets, BRAM-miss, timing-met-but-tight) — quality/
  risk labels we must not discard by binarizing.
- **L3 synth-time diagnostics** (inferred latch, comb loop, multi-driven) and **L4
  critical-path detail** (which nets/cells, telling the model *where* to pipeline) —
  beyond the headline cell counts / Fmax number.
- **predicted vs measured residual** is itself the RQ5 calibration signal.

Raw logs are already persisted per stage; the gap is *extraction* — the diagnosis
record and training views currently reduce rich logs to one `failure_type` string
(see the training-data-quality issue log). Enriching that extraction is what makes
LOG2DIAG/FAILURE2PATCH targeted and widens what is internalizable.

---

## §5 Related Work & Differentiation

### 5.1 How prior work addresses each RQ (and what it leaves open)

A view organized by RQ. Per RQ: how the field solves it, and the opening we take.

- **RQ1 (representation).** *Field:* direct req→code with no IR (VerilogEval,
  RTLLM, RTLCoder, OpenLLM-RTL); circuit-level IR (CPPL: Python-DSL→circuit-JSON,
  consistency by compile-time width inference); software-level intermediate
  (Spec2RTL-Agent via HLS C); compiler hardware IRs not meant as NL targets
  (FIRRTL/CIRCT/LLHD/HIR/Calyx); output-HDL-as-IR study (Representation
  Bottleneck). *Open:* none learns/evaluates a **requirement-intent IR** with an
  ablation; Representation Bottleneck explicitly poses it as future work →
  System-HIS. **Status: open.**
- **RQ2 (tool feedback, b−a).** *Field (mature):* compile/sim feedback loops —
  AutoChip (+24.2%), RTLFixer (syntax), MAGE (multi-agent), VerilogCoder (graph
  planning + AST waveform tool), PEFA-AI (progressive error feedback). *Open:* all
  single-module / functional / sim; none isolate a clean (b−a) delta on the same
  generator across difficulty tiers at **project/physical** level. **Status:
  crowded — differentiate by level + clean measurement.**
- **RQ3 (internalization, c−a / c vs b).** *Field (most crowded):* RL with tool
  reward — ChipSeek-R1 (hierarchical syntax→sim→synth-PPA reward, ASIC),
  VeriRL (trace-back rescore), VeriReason (RL+testbench+reasoning), RTLSeek; SFT
  (RTLCoder, Veribench-53K); inference-time steering (MeltRTL, CASS-RTL). *Open:*
  per-attempt reward, **no reusable trajectory dataset**, single-module, ASIC/sim;
  none frame "(c) without tools matches (b)" or "small model reaches large model."
  Representation Bottleneck's "IR-aware training > model scaling" supports us.
  **Status: most crowded — our moat is project-level + physical + reusable
  tool-verified trajectory + (a)/(b)/(c) + swappable generator. (Highest risk; no
  model trained yet.)**
- **RQ4 (failure structure / difficulty).** *Field:* pass-rate-by-complexity
  benchmarks (ArchXBench's 6 levels, RTL-Repo, ResBench, CVDP); failure-mode
  analysis (Representation Bottleneck: combinational 1.3–1.4× / sequential 2.3× /
  memory 43%; RTLFixer on syntax). *Open:* no **L0–L5 verification-depth ×
  hardware-semantic** cross-index at project scale; their seq/memory gradient backs
  our axes. **Status: half-open.**
- **RQ5 (QoR prediction / shift-left).** *Field:* dedicated pre-synthesis PPA
  predictors, usually a separate GNN, mostly ASIC — MasterRTL, DeepCircuitX,
  self-supervised circuit encoder; HLS DSE predictors (IronMan, Chimera, AutoHLS,
  Intelligent4DSE); POET. *Open:* our predictor is **part of the same tool-distilled
  model** (not a separate GNN), on **FPGA physical (L4)**, and feeds Paper ② as
  proxy fitness, with strict predicted/measured separation. **Status: half-open.**

**Crowding summary:** RQ1 open; RQ2 crowded (loops are mature); **RQ3 most crowded
(the RL cluster) — the differentiation must be sharpest here**; RQ4/RQ5 half-open.

### 5.2 Field map (what each line is, and why it is not us)

Three support points, stated honestly against the *current* field (not the
field as of VerilogEval):

1. **System-HIS as a requirement-level front-end IR** — req→System-HIS→project
   instead of req→code; an explicit, learnable, evaluable intermediate
   representation that sits **above** the hardware-IR spectrum (FIRRTL / CIRCT /
   LLHD / HIR / Calyx) and can *lower to* it — it does not replace or
   re-implement CIRCT. (Decision: **shallow CIRCT coupling** — position + an
   optional lowering bridge, not a deep dependency.) Gain **proven by ablation**.
2. **Tool-verified trajectory dataset + L0–L5 project evaluation** — NOT
   "project-level" as the moat: multi-file/project benchmarks **already exist
   (RTL-Repo, CktEvo, ArchXBench)**, so that alone is no longer novel. The moat
   is the *unit of data* = a **project trajectory**
   (generate→tool→fail→diagnose→patch, with L0–L5 labels), which those
   benchmarks do not produce.
3. **Reproducible req→bitstream→board closed loop** to L4/L5 (code/data/scripts/
   device public, versions pinned) — almost no prior RTL-LLM work reaches
   P&R/timing, on-board, or full reproducibility.

**Field map:**

- **LLM-to-RTL benchmarks / models:** VerilogEval, RTLLM, **RTLCoder (TCAD'25)**,
  OpenLLM-RTL — single module / RTL code, pass@k. (RTLCoder is the closest TCAD
  baseline: code-gen model vs our tool-verified project generation.)
- **Project-level RTL benchmarks:** **RTL-Repo** (repo-context Verilog
  *completion*; no synthesis/physical, no trajectory) and **ArchXBench**
  (MLCAD'25; **6 levels by *design complexity***, frontier models already fail
  from its Level 4 — cite as motivation; note its levels ≠ our L0–L5, which are
  *verification/physical depth* to P&R+board). Neither does physical closure or
  tool-verified trajectories.
- **Tool-feedback / agentic:** AutoChip, RTLFixer, MAGE, **Spec2RTL-Agent**
  (spec→C++→HLS→RTL), **VerilogCoder** (AAAI'25, arXiv 2408.08927; autonomous
  agents with graph-based planning + an AST-based waveform-tracing *tool*) —
  repair/agent loops are mature → not a selling point.
- **Representation-choice study (key motivation, not a competitor):**
  **"From Natural Language to Silicon: The Representation Bottleneck in LLM
  Hardware Design"** (2026, arXiv 2604.17097) — 3 frontier LLMs × 6 IRs
  (Verilog/VHDL/Chisel/Bluespec/PyMTL3/HLS-C) over 202 tasks; finds **"IR choice,
  not model choice, is the dominant factor"** (sim pass 3%→88% by IR; <1.25×
  across models within an IR). **Empirically backs our premise that the lever is
  representation, not the model** (hence frontier models = baselines). *Critical
  distinction:* their "IR" = the **output HDL** (single-module, tiny Lattice
  iCE40UP5K, no trajectory); System-HIS = a **requirement-level intermediate IR
  above the HDL** (project-level, multi-file, XC7Z020) — an orthogonal,
  complementary axis, not the same thing. **Strongest positioning (their own
  Discussion):** they explicitly call for "an **LLM-native IR that explicitly
  separates intent from implementation**" as the way to further reduce the
  bottleneck — i.e. **System-HIS is the IR their paper poses as future work.**
  Two of their findings also empirically back our design: the bottleneck widens
  for **sequential (2.3×) and memory (43% aggregate) designs vs combinational
  (1.3–1.4×)** — backing our seq/comb + memory difficulty axes — and they conclude
  improvement should come from **IR-aware training, not model scaling** — backing
  "frontier model = baseline, fine-tune on tool-verified data." Their
  **"accessibility–competence paradox"** (friendlier IRs → worse LLM performance)
  is a design caution for System-HIS, recorded under §12.1.
  **Honest threat to address (not bury):** they find FPGA **synthesis "nearly
  transparent"** — once a design passes simulation, it maps to silicon at 83–100% —
  so the bottleneck is a *frontend* problem, which on its face questions our
  L4-physical emphasis. The answer is regime: their designs are **educational-scale,
  single-module, median <50 lines, on a 5,280-LUT Lattice iCE40**, and they concede
  "industrial designs with complex hierarchies / IP integration may shift the
  ranking" and "commercial Xilinx/Intel flows may yield different numbers."
  Synthesis transparency is a consequence of *tiny design size*, not a general
  truth. **Our project-level multi-module regime on the XC7Z020 (53k LUT, real
  timing closure) is exactly the regime they excluded — where L4 becomes the
  binding filter.** (Their headline 86.5% iCE40 pass is *conditional* on sim
  success; unconditional end-to-end is 48.1%.)
- **Hardware IRs:** FIRRTL / CIRCT / LLHD / HIR / Calyx, and **CPPL**
  (LLM→circuit-IR JSON→CIRCT→Verilog; input is a **Python DSL with fixed ports +
  docstrings, NOT natural language**; consistency by compile-time width
  inference; no physical/PnR). CPPL is at circuit-structure level, System-HIS at
  requirement-intent level (input = NL requirement, lowers *to* CIRCT/CPPL).
  **System-HIS is also distinct from IP-XACT / SysML / FuseSoC-style engineering
  metadata:** those describe IP packaging, system models, or build integration,
  whereas System-HIS is an LLM-facing requirement-level generation contract —
  evaluated by generation and verification outcomes, not by documentation
  completeness. It is used as (a) a supervised target for REQ→HIS, (b) the
  ground-truth contract for L0 HIS↔RTL cross-checking, and (c) the data anchor
  for tool-trajectory learning. Its evaluation criterion is whether the generated
  project passes L0–L5, not whether the HIS document is complete.
- **Repo-level PPA optimization (closest to Paper ②):** **CktEvo** — closed-loop
  LLM+toolchain edits that preserve function while improving PPA on existing
  repos; no L4/L5 physical labels. We differ by searching the System-HIS
  architecture-parameter space (not editing repos) with a distilled QoR proxy.
- **HLS DSE:** NSGA-II, Chimera, IronMan, AutoHLS — optimize a given design point
  (directly relevant to Paper ②, e.g. predictor-as-proxy-fitness).
- **FPGA-specific benchmark:** **ResBench** (2025, arXiv 2503.08823) — 56 problems /
  12 categories, functional correctness + LUT resource estimation on FPGA; but
  **single-module, stops at resource estimation** (no PnR, no timing closure, no
  board, no multi-file project structure). The nearest existing FPGA benchmark;
  its evidence ceiling is exactly where our L3–L5 begin.
- **RL for RTL generation (single-module cluster):** **ChipSeek-R1** (hierarchical
  reward RL, ASIC synthesis), **VeriRL** (trace-back rescore for sparse reward +
  Veribench-53K, arXiv 2508.18462), **VeriReason** (RL + testbench feedback +
  chain-of-thought reasoning) — all single-module / functional; none produce a
  persistent tool-verified trajectory dataset or reach FPGA physical. Their
  shared stated future work: FPGA, multi-file, physical — our design space.
- **Synthetic RTL data generation:** **SynCircuit** (HKUST 2025, arXiv 2509.00071)
  — diffusion-based graph generation + MCTS for synthetic RTL circuits, aimed at
  ML4EDA data augmentation. Circuit-graph level: no NL requirement input, no
  testbench, no project structure. Conceptually adjacent to our compositional
  benchmark production but orthogonal in purpose.

The model/data is a method contribution riding on these, **not** a SOTA-model
claim.

### 5.3 Gaps we fill (acknowledged by the field)

This is not "integration for its own sake": the LLM-for-EDA survey (TODAES'25,
arXiv 2501.09655) lists these as open, and the strongest RL/PPA works concede
them as future work.

| Acknowledged gap (survey / competitor's own words) | Our contribution |
|---|---|
| "complete multi-file / end-to-end system-spec generation … remains unexplored" | req→System-HIS→multi-file project |
| "bridging NL and RTL … future work, not solved" | System-HIS requirement-level front-end IR |
| "no systematic validation / reproducibility standard" | reproducible req→bitstream→board loop |
| "FPGA LLM applications remain limited" | FPGA physical implementation (L4/L5) |
| ChipSeek-R1 / MasterRTL / POET are ASIC, single-module, stop at synthesis (their own future work) | FPGA, multi-file, to P&R + on-board |
| ChipSeek-R1 has **no reusable trajectory dataset** (per-attempt RL reward) | a persistent **tool-verified trajectory dataset** |
| ResBench (2025): closest FPGA LLM benchmark, but single-module + stops at LUT resource estimation (no PnR / timing / board) | L3 measured QoR (Yosys) + L4 timing (OpenXC7/Vivado) + L5 on-board |
| SynCircuit (2025, HKUST): synthetic RTL generation at circuit-graph level; no NL requirements, no testbench, no verifiable project structure | requirement-level compositional generation with machine-checked testbenches + tool trajectories |
| All LLM-to-RTL works use black-box pass/fail; none categorize errors by **hardware-semantic type** | SR2FPGA **hardware-semantic failure taxonomy cross-indexed against L0–L5** (see §8.4) |

**Caveat (the honest catch):** these are *acknowledged* gaps, so the contribution
is real only if execution actually reaches L4/on-board and a real trajectory
dataset is built — otherwise it collapses to "porting known methods to FPGA."

### 5.4 Core argument

The point of "project-level" is **not** "bigger code." It is **correctness
structure (multi-module + cross-file/cross-module consistency) + physical
realizability (synthesis / timing closure)**. System-HIS is the bridge from a
requirement to that structure (function, ports, widths, clock/reset, FSMs,
datapaths, storage, interfaces). Entry ticket: the generated object must be a
**variable-topology multi-module design** (a top instantiating several submodules
with consistent ports/params across files), not a fixed 6-file template —
otherwise "project-level" collapses.

---

## §6 System-HIS Intermediate Representation

**The canonical schema is `system-his-v1.2`, frozen and implemented** (full field
definitions in `docs/superpowers/specs/2026-06-24-sr2fpga-system-his-v1.2-freeze-design.md`;
the prototype `-topdown` and the inline v1.1 are superseded). This section keeps
the *argument*, aspect skeleton, principles, and well-formedness rules; the freeze
spec is the field authority.

### 6.1 Schema (v1.2, canonical)

**Abstraction level (decided):** structure contract + coarse behavior tags, NOT
a full behavioral spec. System-HIS captures components / instances / interfaces /
connections / params plus a one-line behavior intent; **functional correctness is
verified by the L2 testbench, not described in HIS**. This keeps HIS an *intent*
abstraction (not another RTL), keeps REQ→HIS learnable, and lets the compositional
generator emit it reliably. L0 checks structure against HIS; L2 checks function.

**v1.2 aspect skeleton** (organized the way an FPGA architect reasons):

```
schema_version: "system-his-v1.2"
intent:       {user_prompt, design_goal, assumptions}      # preserve the request above the contract
top:          {name, parameters, clocks, resets, ports, interfaces}   # design boundary first
components:   [{name, semantic_kind, source, parameters, ports, intent}]   # reusable module definitions
instances:    [{name, component, parameter_values, clock, reset, owns_state}]  # concrete blocks (repeated instances OK)
data_flow:    [{name, path:[top.x|inst.port], width, protocol, cdc, timing:{latency_cycles, initiation_interval, throughput}?}]
control_flow: [{kind, when:<guard depth≤2>, effect, related_state, related_flows}]  # fsm_transition / enable_rule / stall_rule …
state:        {registers, counters, fsms:[{states, initial, reset_state}], buffers, memories}
timing:       {primary_clock, target_fmax_mhz, constraints}
resources:    {optimization_goal, expected:{lut?, ff?, bram?, dsp?}}    # model-side → predicted_qor.json
verification: {testbench, scenarios, pass_condition}       # acceptance guiding the auto testbench
artifacts:    {top_module, rtl_sources, testbench, constraints, manifest, predicted_qor}   # maps to the project package
```

**Default clock/reset discipline (pins the label semantics — Finding F):**
- default task family is **single-clock**;
- default reset is **synchronous, active-high**;
- asynchronous reset appears only in explicitly labeled task families;
- reset **deassertion must be synchronous**;
- multi-clock / CDC tasks are **separate difficulty families**, not mixed into normal tasks.

Canonical shape in System-HIS:

```
clocks:
  - name: clk
    frequency_mhz: 100
resets:
  - name: rst
    polarity: active_high
    kind: synchronous
    deassertion: synchronous
```

L0/L2 check that reset polarity/kind matches System-HIS and that valid/state
outputs reach the declared reset state.

**Memory intent fields (makes BRAM inference a checkable item, not a vibe):**
- `memory_style: block | distributed | registers`
- `depth`, `width`, `read_latency`, `read_type: sync | async`
- `read_during_write` behavior, `byte_enable` (optional)

L3 checks: expected BRAM/DSP usage vs measured mapping; unexpected FF/LUT memory
expansion; BRAM miss as a **soft QoR failure** even if function passes.

**Dual use** (why System-HIS is a contribution, not a side artifact): it is the
**intermediate supervision target** (REQ→HIS) for generation, AND the
**ground-truth contract** the L0 checker validates generated RTL against.

**Quarantine:** legacy / `system-his-v1.1` samples are labeled and kept for
traceability, **excluded from the clean REQ2HIS training split** (no migration
tool; re-generation under v1.2 is the path to clean data).

Fields are extended per task as new design families are added — e.g. Paper ②'s
searchable architecture params (parallelism / pipeline depth / memory banks)
will live here later.

### 6.2 Six principles: System-HIS as a typed IR

System-HIS v1.2 is frozen at the **core schema level** (field names, required
top-level aspects, JSON/YAML shape, and training-target format). Non-breaking
validation extensions may evolve without a schema version bump.

1. **Typed contract fields, not prose.** `intent` (user_prompt, design_goal,
   assumptions) is provenance and explanatory context only — it is **not used as an
   implicit semantic source** by L0/L2 checkers. All machine-checkable semantics must
   appear in typed fields: `top`, `interfaces`, `components`, `instances`,
   `data_flow`, `control_flow`, `state`, `timing`, `resources`, `verification`, and
   `artifacts`.

2. **Well-formedness.** Every instance resolves to a component; every data-flow
   endpoint resolves to a port or interface; widths, directions, clocks, resets, and
   protocols are compatible; CDC paths carry synchronizer intent; memory and protocol
   intents must be lowerer-supported. (See well-formedness rules W1–W10 in §6.3.)

3. **Interface-first FPGA semantics.** Ports are physical signal boundaries;
   interfaces are semantic bundles. Protocols (valid-ready, AXI-stream, AXI-lite,
   BRAM, GPIO) carry role, channels, ordering, backpressure, reset behavior, and
   checker templates. L0 checks ports; L2/L2-UVM/L5 depend on interfaces.

4. **Bounded control grammar.** `control_flow.when` and `control_flow.effect` use a
   bounded, typed guard/effect language (guard nesting ≤ depth 2). Free-text `intent`
   may explain a rule, but only typed guards/effects are checked or lowered.

5. **Contract-preserving lowering.** System-HIS lowers to: symbol table → project
   manifest → top shell → module declarations → interface bundles → testbench scaffold
   → assertion/checker templates → logical constraints → board-shell binding →
   model-fillable behavior holes. It guarantees cross-file structural consistency by
   construction; full behavioral correctness is L2's responsibility.

6. **Canonicalization.** A canonical JSON serialization, stable IDs (independent of
   human-readable names), deterministic field ordering, and normalized parameter
   expressions are used for hashing, diffing, REQ→HIS fidelity scoring, L0 checking,
   and training targets.

**Intent / Contract / Advisory field classification:**

| Class | Fields | Checker role |
|---|---|---|
| **Intent** | `intent.*`, explanatory strings | provenance only — not used by L0/L2 |
| **Contract** | `top`, `interfaces`, `components`, `instances`, `data_flow`, `control_flow`, `state`, `verification.pass_condition` | L0/L2 must satisfy |
| **Advisory** | `resources.expected`, `timing.target_fmax_mhz`, `predicted_qor` | QoR/optimization hints — failure is a soft budget miss, not a functional failure |

### 6.3 Well-formedness rules (W1–W10)

- W1. Every `instance.component` must reference exactly one declared `component`.
- W2. Every `data_flow.path` endpoint must resolve through the symbol table to an
  existing top port or instance port.
- W3. Port widths and directions must be type-compatible along every connection.
- W4. Every state-owning instance must bind to a declared clock and reset.
- W5. A component declared combinational must not own state, clock, or reset.
- W6. Every `cdc:true` data-flow must cross two distinct clock domains and must pass
  through a synchronizer component or an explicitly declared CDC primitive.
- W7. Every memory intent must declare `depth`, `width`, `read_latency`, `read_type`,
  and `memory_style` if BRAM/distributed/register mapping is evaluated.
- W8. Every verification scenario must reference existing interfaces/signals and map
  to a lowerer-supported stimulus/checker template.
- W9. Every logical constraint must reference declared clocks/ports and must not
  override board constraints.
- W10. Every artifact path listed in `artifacts` must be reproducible from
  `manifest.json` + `top_module`.

### 6.4 H0/H1/H2 validation levels

Evaluated before the L0 RTL checker runs:

- **H0** — schema-valid: JSON/YAML shape, required fields, enum values.
- **H1** — well-formed: symbols resolve, endpoints exist, widths/types compatible,
  W1–W10 pass.
- **H2** — lowerable: all components/protocols/scenarios are supported by the current
  lowerer and testbench generator.

REQ2HIS model outputs are evaluated at H0/H1/H2 before entering the L0–L3 pipeline.
Failures at H0/H1/H2 have their own `req_his_*` diagnosis class and can be repaired
by the FAILURE2PATCH actor without running EDA tools.

### 6.5 REQ→HIS fidelity failure modes

`req_his_missing_requirement` | `req_his_wrong_width` | `req_his_wrong_protocol` |
`req_his_wrong_reset_kind` | `req_his_wrong_latency` | `req_his_missing_corner_case` |
`req_his_over_specified_behavior` | `req_his_under_specified_interface`

### 6.6 Non-goals of System-HIS v1.2

System-HIS does **not** aim to: replace FIRRTL/CIRCT/LLHD/Calyx as a circuit or
compiler IR; fully specify cycle-accurate behavior; encode board-level physical
implementation details; serve as an IP-packaging standard (cf. IP-XACT); make tool
execution unnecessary; or prove functional correctness without testbenches/properties.

---

## §7 Evaluation Framework (L0–L5)

### 7.1 Level overview

- **L0** project contract + cross-file consistency (HIS↔RTL checker)
- **L1** lint (Verilator; synthesizable-subset enforcement)
- **L2** functional simulation (Icarus Verilog; coverage-qualified)
- **L3** synthesis + measured QoR (Yosys `synth_xilinx`)
- **L4** place-and-route timing closure (OpenXC7 primary + Vivado commercial reference)
- **L5** sparse representative on-board runs (AC820-ZYNQ XC7Z020CLG484-2)

**Toolchain (all-open primary, Vivado fallback):** L0–L3 use open tools (Verilator /
Icarus / Yosys), fitting thousands of samples; L4/L5 use OpenXC7 (nextpnr-xilinx) on
the AC820-ZYNQ, subject to a spike verification. Vivado is the fallback/baseline — for
**TRETS-safe** work it stays optional; for **TCAD-strong**, a minimal Vivado
commercial-reference subset is required. All code/data/scripts/device public, tool
versions pinned.

### 7.2 L0: project contract & cross-file consistency

**L0 consistency checker (a named component, not a side note):** validates the
generated RTL against the System-HIS contract — top instantiates the declared
modules; every port name/direction/width, parameter, and cross-module
connection matches System-HIS; the testbench instantiates the real top;
constraints reference real ports. This automates the cross-file-consistency
verdict and yields the **"cross-file consistency error rate"** metric — the
structural check single-file benchmarks structurally cannot do.

### 7.3 L1: lint

L1 checks implicit nets, width truncation, unused/undriven signals, inferred
latches, combinational loops, blocking assignment in sequential logic, and
nonblocking assignment in combinational logic — enforcing the SR2FPGA
synthesizable RTL subset defined in §8.5.

### 7.4 L2: functional simulation

**L2 pass is not a bare "simulation finished" verdict.** For benchmark/evaluation
items, L2 is reported as **coverage-qualified functional acceptance**:
- **L2a** directed smoke tests;
- **L2b** randomized/stress scenarios;
- **L2c** required protocol/value coverage.

A design is syntactically and functionally accepted only **under the declared
test contract**; we therefore report the scenario/coverage profile alongside the
L2 pass/fail verdict.

**Minimum coverage targets by family:**
- **valid-ready / stream:** valid held while ready is low, randomized stalls,
  bursts, idle cycles, reset during transaction;
- **FIFO / skid buffer:** full, empty, almost_full/empty, simultaneous push-pop,
  overflow/underflow attempts;
- **pipeline:** different latency paths, stalls, flush/reset during in-flight data;
- **arithmetic:** signed/unsigned, boundary values, overflow/truncation cases;
- **memory/BRAM:** read-after-write, same-address conflict, sync vs async read behavior;
- **AXI-lite/stream subset:** ordering, WSTRB, response channel, back-to-back transactions.

**Public/hidden/stress test split:** each evaluation item may contain multiple
scenario classes:
- **public** scenarios: visible to the generation/repair loop;
- **hidden** scenarios: used only for final acceptance;
- **randomized** scenarios: fixed seeds, recorded in the trajectory;
- **stress** scenarios: reset during transaction, backpressure, boundary values,
  full/empty, resource/timing stress.

Final **L2 acceptance is based on the hidden + stress suite**, not merely the
public smoke tests — this prevents the model or the repair loop from "fixing to
just pass the visible testbench." All seeds are recorded for reproducibility.

**Protocol assertion library:** for protocol-heavy designs the generator emits
**assertions/checkers from System-HIS protocol intent** (`protocol_agents`; SVA or
immediate assertions). These checks complement scoreboards. Examples:
- valid high and ready low ⇒ payload must remain stable;
- FIFO: no read when empty; no write when full;
- reset clears valid/state outputs;
- no data drop or duplication;
- AXI-lite/stream ordering and response checks for the supported subset;
- no combinational ready-valid loop, where structurally checkable.

**Checker provenance:** assertions/checkers are **trusted verification artifacts
generated from templates**, not model-authored oracle logic. The generator, not
the LLM, owns checker correctness.

**L2F — optional property checks:** for selected protocol-heavy task families,
SR2FPGA can run **bounded formal / property sanity checks** generated from
System-HIS protocol intent. This is an optional representative layer — not a full
formal-verification scope expansion:
- FIFO: no overflow / underflow under any bounded sequence;
- valid-ready: payload stability under stall for bounded transaction windows;
- reset convergence within a bounded cycle count;
- one-hot FSM invariant;
- no data duplication / drop for bounded transaction windows;
- AXI-lite response ordering for the supported subset.

L2F is **not required for every Line-B trajectory** and does not gate L2 pass.
It is run on benchmark/eval items and reported as a supplementary property
acceptance score.

**L2S — optional post-synthesis netlist simulation:** run the **same black-box
testbench** on a synthesized netlist emitted by Yosys `synth_xilinx` /
`write_verilog`, and compare RTL-sim vs netlist-sim behavior. This catches RTL
constructs whose simulation behavior diverges after synthesis: incomplete `case`,
latch inference, RAM read semantics, uninitialized state, X-optimism,
blocking/nonblocking misuse, and memory-mapping differences. **L2S is not required
for every large-scale Line-B trajectory**, but should be run on the benchmark/eval
set and representative subsets.

**L2-core vs optional L2-UVM:**
- **L2-core:** deterministic black-box self-checking simulation — the default for Line B;
- **L2-UVM:** optional transaction-level UVM verification for selected
  protocol-heavy tasks (valid-ready stream, FIFO/skid buffer, AXI-stream subset,
  AXI-lite register block, RL-accelerator host interface).

UVM environments are generated from **System-HIS + trusted templates**, not freely
authored by LLMs. **L2-core vs L2-UVM stress ablation:** report cases where
directed L2 passes but randomized/coverage-driven L2-UVM fails, plus coverage deltas.

### 7.5 L3: synthesis + QoR

Synthesis uses Yosys `synth_xilinx`. L3 checks:
- expected BRAM/DSP usage vs measured mapping;
- unexpected FF/LUT memory expansion;
- BRAM miss as a **soft QoR failure** even if function passes.

**Do not use generic Yosys-L3 LUT as a strong QoR claim;** meaningful FPGA QoR
uses `synth_xilinx` and/or OpenXC7/Vivado L4 reports (Finding G).

### 7.6 L4: place-and-route timing closure

**L4 is reported as three sub-verdicts:**

- **L4-open:** place-and-route timing closure with OpenXC7 / nextpnr-xilinx on
  the AC820-ZYNQ (`XC7Z020CLG484-2`). This is the **primary reproducible open
  physical flow**, subject to the board-specific OpenXC7 spike.
- **L4-commercial:** Vivado synthesis + implementation on the **same RTL, same
  generated core, same fixed board shell, same part `XC7Z020CLG484-2`, and same
  logical timing constraints**. L4-commercial is **required for the TCAD-strong
  version on a representative subset**, but **not** for every Line-B trajectory.
- **L4-agreement:** report OpenXC7/Vivado agreement and disagreement on
  pass/fail, utilization, WNS/Fmax, DRC/methodology warnings, and runtime.

**L4 pass requires all of the following, not merely bitstream generation:**
1. place-and-route completed;
2. target clock met: **WNS ≥ 0** under the declared target frequency;
3. no unconstrained clocks;
4. no unconstrained endpoints, unless explicitly justified and recorded;
5. no black boxes;
6. no critical warnings that invalidate implementation;
7. post-P&R utilization fits the declared resource budget;
8. the generated core is connected through the board shell and is **not optimized away**;
9. timing/utilization/DRC reports are archived.

For **Vivado** runs, archive: `report_timing_summary`, `report_utilization`,
`report_clock_utilization`, `report_drc`, `report_methodology`, `report_io`, and
(optional) `report_power`. For **OpenXC7/nextpnr** runs, archive: placement/routing
logs, timing summary, device utilization, constraint/IO errors, and bitstream
generation status.

L4 pass is reported separately as:
- **L4-open-pass:** OpenXC7/nextpnr completes P&R and timing under the declared constraints.
- **L4-commercial-pass:** Vivado completes synthesis, implementation, DRC/methodology
  checks, and timing under the declared target clock.
- **L4-agreement:** OpenXC7 and Vivado agree on the physical verdict, or the
  disagreement is explicitly classified and explained.

A design is considered **commercially validated** only if Vivado completes:
synthesis; opt/place/route; timing summary; utilization report; DRC report;
methodology report; **no black boxes; no unconstrained clocks; no unjustified
unconstrained endpoints; WNS ≥ 0 under the declared target clock**.

**OpenXC7: feasible, pending spike — not completed evidence.** OpenXC7 provides a
**plausible all-open L4/L5 path** for the Zynq-7 target, but this is **not assumed
as evidence until the board-specific spike lands**. The **OpenXC7 spike must validate**:
exact part/package/speed grade `XC7Z020CLG484-2`; board clock/reset/pin profile;
XDC/PCF constraint correctness; bitstream generation; bitstream loading; a
board-shell smoke test; comparison against Vivado on the same RTL and logical constraints.

**For TCAD, SR2FPGA should not claim physical FPGA realizability from an open
flow alone.** The defensible position is: OpenXC7 provides the reproducible open
path; Vivado provides commercial reference validation on a representative L4 subset;
L5 provides sparse end-to-end board feasibility evidence.

**Commercial-tool reference validation:** SR2FPGA includes Vivado as a commercial
reference flow for a representative L4 subset. OpenXC7 remains the primary
reproducible open flow and the scalable source of physical labels where feasible;
Vivado is used to validate that SR2FPGA-generated projects are **accepted by a
mainstream commercial Xilinx FPGA flow** and that timing/QoR conclusions are not
merely artifacts of the open toolchain.

This comparison is **not** a full commercial-scale benchmark. It uses the same
RTL, same generated core, same fixed board shell, same Xilinx part
`XC7Z020CLG484-2`, and the same logical timing constraints. The paper reports
OpenXC7/Vivado agreement on pass/fail, utilization, WNS/Fmax, DRC/methodology
warnings, and runtime, and explicitly analyzes disagreement cases.

**OpenXC7/Vivado disagreement taxonomy:**

Disagreement cases are **not discarded** — they are labeled because they are
useful tool-chain evidence:
- **D0** both_pass;
- **D1** OpenXC7_pass / Vivado_fail;
- **D2** OpenXC7_fail / Vivado_pass;
- **D3** both_fail_same_reason;
- **D4** both_fail_different_reason.

Reason labels: `synthesis_mapping_difference`, `BRAM/DSP_inference_difference`,
`constraint_interpretation_difference`, `timing_model_difference`,
`routing_heuristic_difference`, `unsupported_primitive`,
`invalid_XDC_or_board_constraint`, `unconstrained_path_detected_by_one_tool`,
`critical_warning_policy_difference`.

### 7.7 L5: board validation

L5 uses a **fixed, manually reviewed board harness**. The model does **not**
generate the entire board project — separating the three layers keeps board-level
noise out of the pass-rate metric:
- **generated core:** the RTL generated/repaired/evaluated by SR2FPGA;
- **fixed board shell:** clock/reset, pin constraints, AXI-lite/BRAM/UART/GPIO
  bridge, reset synchronizer, debug/status registers; **version-locked and manually audited**;
- **host harness:** Python/C script that writes input vectors, starts the core,
  reads outputs/status/signature, and compares against a golden checksum/model.

**L5 pass requires:** bitstream loaded successfully; host script completed without
timeout; the generated core received inputs and produced outputs **through the
fixed shell**; output signature/checksum matches the golden model; board log and
host log archived.

**L5-min (the on-board scope):** 1–3 representative designs; fixed board shell;
host script; golden checksum/signature; archived logs.

**L5-scale is explicitly out of scope for Paper ①.** L5 is reported as end-to-end
physical-feasibility evidence, **not** a large-scale pass-rate metric.

### 7.8 Verdict mode vs full-level diagnostic mode

To stop an early L0 failure from censoring the L1–L4 hardware-semantic failure
distribution (Issue 5), two evaluation modes are run:
- **Official verdict mode:** the **first failing level** determines the official
  `Lk` acceptance level.
- **Full-level diagnostic mode:** best-effort continue after an early failure,
  using wrappers/normalization where safe, to collect additional L1–L4 signals.

Diagnostic signals **do not upgrade the official pass level**; they are used only
for the failure taxonomy, LOG2DIAG, and deeper failure-distribution analysis.

---

## §8 Benchmark Design

### 8.1 Item form

**Single item form (verification-based, NOT reference-matching):** RTL has no
unique correct answer, so ground truth is "passes the acceptance criteria,"
never "matches a reference file." Input = NL requirement + machine-readable
interface contract. Judgement = L0–L5 tool verdicts + functional testbench.

### 8.2 Production mechanism (compositional)

- a **component library** of parameterized primitives (FIFO, arbiter, CDC
  synchronizer, pipeline stage, ALU slice, register file, protocol adapter,
  decoder, …);
- a **topology generator** that wires components into multi-module systems
  (chain / tree / bus-attached / producer-consumer) and auto-guarantees
  interface-contract consistency;
- diversity = component types × parameter space × topology × protocol variant ×
  name randomization (combinatorial explosion, not a fixed template count);
- the generator emits `(requirement, System-HIS, contract, testbench,
  constraints, reference impl)` together. The reference impl passing the
  testbench gives a **machine-checked self-consistency** of the testbench — the
  load-bearing reason to prefer program generation over LLM-authored tests.
- **Golden model for algorithm-family tasks:** self-consistency proves the RTL
  reference and testbench *agree*, not that they compute the *right* math. For
  algorithm modules (FIR, FFT, matrix-multiply, CORDIC, accumulators, MAC), the
  generator must also emit a **software golden model** (Python/NumPy) that
  produces the testbench's expected values, so L2 catches "runs but the numbers
  are wrong" bugs.
- *(Distinction from SynCircuit, HKUST 2025):* SynCircuit generates synthetic
  RTL at the circuit-graph level (diffusion + MCTS) for ML4EDA data augmentation
  — no NL input, no testbench, no project structure. Our generation is at the
  requirement-intent level, producing verifiable multi-file projects + acceptance
  testbenches + tool trajectories.

**Testbench discipline:** test the **black-box interface contract only** (port
behavior, protocol timing, functional correctness); never depend on internal
signal names / implementation details — this is what keeps the benchmark fair to
any implementation.

**Anti-leakage:** held-out parameter combinations + randomization make concrete
instances effectively unseen in any training corpus. (Real open-source IP is the
leakage risk, not synthetic instances.)

**Sources (mixed):** compositional synthetic tasks as the main body (controlled
difficulty, scalable, leakage-safe), plus a small set of real open-source IP
(OpenCores / LiteX …) as external-validity anchors. An LLM may **surface-rewrite**
the program-generated requirement text into more natural language — wording only,
never touching semantics or acceptance — to mitigate the "synthetic NL" critique.

**Scale:** thousands to ~10k samples, not millions (data-volume-realistic). Benchmark
items are mostly small/medium multi-module designs (an RL-sized accelerator is a
*flagship case*, not the body). The existing deterministic `ProjectGenerator` is
the seed of the component library.

### 8.3 Difficulty tiers T1–T4

**Difficulty axes (all four, with the first two primary):**
1. cross-module / cross-file consistency (number of interface/param contracts) — primary
2. timing pressure (target Fmax / critical-path depth) — primary
3. protocol/control complexity (register → valid/ready → backpressured pipeline → AXI4-Lite/Stream)
4. structural scale (submodule count / hierarchy depth) and CDC — high-difficulty tier

**Difficulty tiers** map the axes onto **T1 Easy / T2 Medium / T3 Hard / T4 Stress**
by submodule count, number of cross-module contracts, protocol class, and target Fmax
(concrete thresholds fixed during the baseline (a) measurement). Pass rates are
reported **per tier** so the knee where frontier models start failing is visible.

**Freeze protocol:** difficulty thresholds are calibrated once on a pilot set
(using baseline (a) frontier-model pass rates) and **frozen before the official
evaluation**. They are not tuned after seeing fine-tuned model results. The
calibration run records for each tier: expected submodule count, cross-file
contract count, protocol class, target Fmax range, and observed frontier pass-rate
range — to allow reviewers to verify the freeze was prior to the (c) measurement.

### 8.4 Hardware-semantic gap taxonomy (a named contribution)

**What it is:** LLMs are pre-trained on software (sequential-execution) semantics
and systematically fail at hardware's concurrent/physical semantics. Crucially,
**each class of this gap surfaces at a different verification depth**, so the L0–L5
hierarchy is not only "verification depth" but "depth of hardware-semantic
understanding required." This reframes the failure-taxonomy contribution from "we
have a taxonomy" to "we map the software→hardware semantic gap onto a
verification-depth hierarchy" — and shows why prior work (stopping at L2/L3)
covers only the front half of the gap.

| Semantic-gap class | Surfaces at | Observable with our tools? | How |
|---|---|---|---|
| seq/comb confusion | **L1** lint | yes (now) | Verilator named warnings: `MULTIDRIVEN`, `LATCH`, `COMBDLY`, `BLKSEQ` |
| valid-ready backpressure | **L2** sim | yes, **iff our testbench applies backpressure** | we emit the testbench → controllable by design |
| memory/BRAM inference miss | **L3** synth | yes (now) | Yosys `stat`: `$mem` mapped to BRAM vs flattened to FF/LUT |
| CDC missing synchronizer | **L0** (structural) + L5 (metastability) | structural only | L0 checks a `cdc_sync` instance exists on a `cdc:true` path |
| combinational loop | **L1** lint | yes (now) | Verilator `UNOPTFLAT` / Yosys (e.g. a ready/valid comb loop) |
| reset polarity/kind mismatch | **L0** | yes (now) | System-HIS `resets[].polarity/kind` vs RTL reset usage |
| FSM unreachable / no-safe-state | **L0** (structural) + L1 | partial | `state.fsms` reachability + lint default/full-case |
| internal width truncation | **L2** sim | yes, **iff testbench checks values** | golden-value testbench catches `8b×8b` silently kept at 8b |
| signedness error | **L2** sim | yes, **iff testbench checks values** | golden-value testbench catches signed/unsigned mishandling |
| timing / SDC closure / multicycle | **L4** P&R | gated on OpenXC7 spike | nextpnr/Vivado timing report (Fmax/slack) |
| resource_overflow (placement fails) | **L4** P&R | yes (when L4 runs) | nextpnr "failed to place": cells exceed device |
| routing_congestion | **L4** P&R | yes (when L4 runs) | nextpnr routing failure / congestion |
| timing_violation (negative slack) | **L4** P&R | yes (when L4 runs) | nextpnr/Vivado slack + critical path → where to pipeline |
| constraint_error (unconstrained/illegal IO) | **L4** P&R | yes (when L4 runs) | nextpnr IO/constraint error vs XDC |

(The last six rows extend the original three after auditing our taxonomy against
a practitioner failure checklist — FPGA手记, "AI写RTL", 2026-06, a non-peer-reviewed
industry blog used only as a completeness check / motivation corroboration. Only
tool-detectable classes were added; each carries its detection venue.)

**Toolchain/environment failure category:** a separate class
`toolchain_environment_failure` covers: tool timeout; tool crash; missing
dependency; license unavailable (Vivado seat/server); filesystem or path error;
unsupported syntax due to tool version; OpenXC7 chipdb issue; Vivado license/server
issue. These are **excluded from model pass/fail numerator / denominator** and
reported as a separate infrastructure-health metric.

**Honest boundaries (state in the paper, do not overclaim):**
- CDC: structural only (synchronizer present), **not** behavioral — metastability
  is not verifiable in sim (aligned clocks) and only sparsely/nondeterministically on-board.
- backpressure / BRAM / internal-width / signedness are vacuous **unless the
  testbench (or QoR machinery) actually stresses them** — coverage is a
  generator-quality property, not automatic.
- L4 timing/multicycle is gated on the OpenXC7 spike landing.
- Board-level signal integrity / on-board "玄学" debugging is **out of scope** —
  that is human L5 work, not something the pipeline detects.
- Detection ≠ prevention: the pipeline *labels* these as tool-verified failures
  and feeds repair trajectories; whether a trained model stops making them is the
  empirical (a)/(b)/(c) question, not a guarantee.
- **Accessibility–competence paradox (System-HIS design risk):** the
  Representation-Bottleneck study (2026, arXiv 2604.17097) found that *friendlier*
  representations can yield *worse* LLM performance. So a high-level System-HIS is
  not automatically easier to generate — REQ→HIS and HIS→project difficulty
  depends on the representation's design, and the System-HIS ablation must report
  this honestly.

**Priority tiers for the hardware-semantic taxonomy:**
- **Tier A (Paper ① core — observable now at L0–L3, low marginal cost):**
  seq/comb (L1), memory/BRAM inference (L3), valid-ready backpressure (L2). Each
  feeds a *different* training view — seq/comb → `LOG2DIAG`/`FAILURE2PATCH`,
  BRAM-miss → `QOR_PRED` (a *soft* failure: passes L3 but blows the resource
  budget, a live shift-left predicted-vs-measured sample), backpressure →
  functional `FAILURE2PATCH` that sim-pass benchmarks miss because their
  testbenches never apply backpressure.
- **Tier B (structural now, physical later):** CDC — do the L0 structural check
  + a synthetic injector ("remove synchronizer") now; defer metastability/L5 to nice-to-have.
- **Tier C (gated on L4):** SDC/timing closure — defer to after the OpenXC7
  spike; port-name checks against constraints already live in the L0 checker.

`classify_failure()` detects the Tier-A classes from Verilator/Icarus/Yosys logs
without manual annotation; the labels are recorded as named sub-categories of
`failure_to_diagnosis`.

**Failure-label validation (the regex classifier must be calibrated, not trusted):**
- sample 200–300 tool logs across L1/L2/L3/L4;
- manually label primary failure class, secondary class, tool stage, and patch category;
- compare `classify_failure()` against the manual labels;
- report precision, recall, and a confusion matrix;
- optional: two annotators or adjudication for ambiguous logs.

**Where these land in System-HIS v1.2 (no schema redesign needed):**
- seq/comb: captured **structurally** — a combinational component owns no
  `state`, no `clock`, no `reset_rule`; a future L0 extension flags "declared
  combinational but RTL has `always @(posedge clk)`."
- memory/BRAM: extend `state.memories[]` with `memory_style: block|distributed`
  and `read_type: sync|async`; L3 compares intent against Yosys-measured BRAM.
- CDC: `instances[].semantic_kind: cdc_sync` + a `cdc` flag on the crossing
  `data_flow`; L0 verifies a synchronizer instance sits on the crossing path.
- backpressure: `verification.scenarios[]` includes a backpressure stimulus;
  `control_flow` already enumerates `handshake_rule` and `stall_rule`.

### 8.5 SR2FPGA synthesizable RTL subset

All model-generated RTL is expected to follow a restricted synthesizable subset,
so the benchmark does not reward RTL that simulates but does not synthesize (or
behaves differently across tools).

**Required:** `` `default_nettype none ``; explicit widths; explicit reset
behavior for stateful modules; single-driver registers/nets; supported RAM/DSP
inference templates for memory/arithmetic tasks.

**Allowed:** parameter/localparam; generate blocks; `always_ff` / `always_comb`
or strict `always @*` / `always @(posedge clk)`; packed arrays with documented
restrictions; synchronous memories in supported templates.

**Forbidden:** `#` delays; force/release; DPI; classes/dynamic arrays in
synthesizable RTL; unsynthesizable `initial` blocks (except the explicitly
supported ROM/init policy); implicit nets; intentional latches unless the task
explicitly requires them; multiple drivers.

### 8.6 Constraint classes: logical vs board

Constraints are split into two classes:
- **logical constraints:** `create_clock`, target period, generated clocks,
  max delay, false paths, multicycle paths, timing intent;
- **board constraints:** package pins, IOSTANDARD, physical clock source, reset
  pin, board IO profile.

The model / System-HIS may **select a board profile and emit logical timing
intent**. Board constraints are generated from **trusted board profiles, not
freely written by the LLM**. L0 checks that constraints reference real ports and
that the selected board profile is compatible with the top-level shell, but does
**not** treat arbitrary LLM-written board XDC as trusted.

### 8.7 Real-IP external anchor policy

The real-IP set is a **small, curated set of 5–10 open-source IP cases**, used for
**external validation only; not used for training**. Each case records license,
repository URL, commit hash, modifications, wrapper changes, original testbench
availability, and tool-compatibility patches.

---

## §9 Data Engine

### 9.1 Two production lines (Line A / Line B)

- **Line A — benchmark eval set:** quality first, modest size (tens to ~hundreds
  of items), each with requirement + System-HIS + contract + functional testbench
  + constraints + difficulty label.
- **Line B — training/trajectory data:** scale first, fully automatic; run
  generate → tools → fail → repair at volume, collecting L0–L5 labels, diagnoses,
  patch trajectories. Hard tasks drop first-pass rates, so failure/repair
  trajectories appear by design. **Machine-time discipline:** run the large-scale
  loop only through **L3 (Yosys, seconds/sample)**; reserve the slow **L4 (Vivado,
  minutes/sample)** for the eval set and representative subsets, not every sample.
- **Candidate sources for inputs:** prefer the compositional component library
  (free, controllable, large, leakage-safe) + a small amount of DeepSeek/local
  candidates. **All labels come from tools** (tool-distillation purity).

### 9.2 Trajectory episode schema

Each trajectory is an **episode**, not a single input-output pair. The unit of
data is: requirement → generate → tool verdict → fail → diagnose → patch →
re-verify → record outcome. The schema below is the canonical episode skeleton;
the L4 cross-tool block is expanded separately.

```json
{
  "sample_id": "string",
  "requirement": "string",
  "oracle_his": {},
  "generated_his": {},
  "req_his_fidelity": {
    "interface_extraction": null,
    "clock_reset_fidelity": null,
    "parameter_fidelity": null,
    "behavior_intent_fidelity": null,
    "verification_intent_fidelity": null,
    "constraint_fidelity": null
  },
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
    "l3": {
      "status": "pass|fail|missing_tool",
      "lut": null, "ff": null, "bram": null, "dsp": null, "cells": null,
      "bram_miss": false
    },
    "l4_open": {
      "tool": "openxc7_nextpnr",
      "status": "pass|fail|not_run",
      "wns_ns": null, "fmax_mhz": null,
      "lut": null, "ff": null, "bram": null, "dsp": null,
      "drc_warnings": [], "critical_warnings": [],
      "runtime_sec": null, "report_paths": []
    },
    "l4_commercial": {
      "tool": "vivado",
      "status": "pass|fail|not_run",
      "wns_ns": null, "fmax_mhz": null,
      "lut": null, "ff": null, "bram": null, "dsp": null,
      "drc_warnings": [], "methodology_warnings": [], "critical_warnings": [],
      "runtime_sec": null, "report_paths": []
    },
    "l4_agreement": {
      "class": "D0|D1|D2|D3|D4|not_applicable",
      "reason": "synthesis_mapping_difference|BRAM_DSP_inference_difference|constraint_interpretation_difference|timing_model_difference|routing_heuristic_difference|unsupported_primitive|invalid_XDC_or_board_constraint|unconstrained_path_detected_by_one_tool|critical_warning_policy_difference|null"
    },
    "l5": {"status": "pass|fail|not_run", "log_path": null}
  },
  "diagnosis": {
    "failure_level": "L0|L1|L2|L3|L4",
    "failure_type": "string",
    "failure_origin": "natural_model_failure|injected_mutation|toolchain_environment_failure",
    "structured_diagnosis": {}
  },
  "patches": [
    {
      "patch": "string",
      "diagnosis": {},
      "result_after_patch": {"l0": {}, "l1": {}, "l2_core": {}, "l3": {}}
    }
  ],
  "qor": {
    "predicted": {},
    "measured_open": {},
    "measured_commercial": {}
  },
  "data_release": {
    "tier": "open_public|restricted_reference|internal_only",
    "license_notes": []
  }
}
```

`failure_origin` distinguishes: model-generated designs that failed naturally
(`natural_model_failure`), designs produced by deliberate mutation for failure
coverage (`injected_mutation`), and failures caused by the toolchain environment
itself (`toolchain_environment_failure` — timeout, license unavailable, missing
dependency, tool crash, OpenXC7 chipdb issue). Only `natural_model_failure` and
`injected_mutation` samples count toward model pass/fail numerator/denominator;
`toolchain_environment_failure` is reported separately and excluded from the model
accuracy metric.

Key v1.2 properties (full rationale in the freeze spec): `components` vs
`instances` resolves the repeated-instance ambiguity v1.1 had; the seq/comb
distinction is **structural** (a combinational component owns no `state`/`clock`/
`reset_rule`); `data_flow.timing` makes pipeline depth + throughput first-class
(forward-compatible with Paper ②); `control_flow` is load-bearing, verified at L2,
and drives testbench generation; guard nesting is capped at depth 2 (the intent/RTL
line). **Provisional fields** (`data_flow.timing`, structured `control_flow`/FSM,
guard grammar) are Tier-2 of the ratification gate — implemented and checked, but
not required in the REQ2HIS target until a real task exercises each.

### 9.3 Failure injection suite

To ensure training coverage of rare but important failure classes, SR2FPGA
deliberately **injects controlled mutations** into known-good projects. Injected
failures are separated from natural model failures in all analysis (via the
`failure_origin` field in the episode schema).

Representative injected mutation classes:
- port width mismatch (parameter value changed in one file, not propagated);
- reset polarity mismatch (active-low RTL with active-high HIS declaration);
- missing `ready` stall (valid-ready protocol: `ready` ignored in datapath);
- async memory read in a BRAM template (forces LUT/FF mapping);
- signedness cast removal (`$signed()` stripped, silent arithmetic error);
- missing CDC synchronizer (crossing data_flow with `cdc:true` but no sync instance);
- combinational ready-valid loop (ready depends on valid combinationally);
- invalid logical constraint (wrong clock period, unconstrained path);
- removed pipeline register (causes timing pressure at L4);
- one-hot FSM corruption (encoding changed to binary in RTL).

**Protocol:** injected failures are injected **after** the reference project
passes L0–L3 (or L4 where applicable), ensuring the pre-mutation baseline is
clean. The injection point, mutation type, and expected failure level are recorded
in the episode. Injected samples are used for LOG2DIAG and FAILURE2PATCH training
coverage; they are reported separately from natural failures in the failure heatmap.

### 9.4 Split policy (generalization regimes S1–S5)

Results are reported under multiple generalization regimes, not just
parameter-heldout:
- **S1 parameter-heldout:** same family/topology, unseen width/depth/latency/parallelism;
- **S2 topology-heldout:** unseen wiring/topology patterns;
- **S3 component-combination-heldout:** unseen combinations of known components;
- **S4 family-heldout:** entire design family held out from training;
- **S5 real-IP external:** real open-source IP used only for external validation,
  **never training**.

Main results should at least separate in-distribution, parameter-heldout,
topology-heldout, and family-heldout performance.

### 9.5 IP/licensing/data-release discipline

SR2FPGA generates its own RTL projects and uses EDA tools as objective oracles.
The data-release policy separates what may be publicly released from what is
restricted or internal-only.

**Data-release tiers:**

| Tier | Contents | Default disposition |
|---|---|---|
| `open_public` | generated requirements, System-HIS, RTL, testbenches; open-tool (Verilator/Icarus/Yosys/OpenXC7) logs and structured labels; L0–L4-open metadata; failure taxonomy | publicly released with the dataset |
| `restricted_reference` | Vivado commercial-reference structured metadata (timing/utilization summaries normalized from reports); L4-commercial labels | released only if institutional license review and Xilinx/AMD EULA permit |
| `internal_only` | raw Vivado timing/utilization/DRC/methodology reports; Vivado DCP / checkpoints; bitstreams; generated databases; LogiCORE artifacts; vendor IP; encrypted IP | archived for internal audit and paper-table derivation; **not publicly released** |

**Principles:**
- **Archiving ≠ public release.** Commercial-tool raw reports are archived for
  internal audit and rebuttal; they are summarized into normalized metadata for
  paper tables, subject to license review.
- **Vivado raw artifacts are not used for public model training** unless the
  applicable license and institutional legal review explicitly permit it.
- **Public training data is based primarily on generated designs and open-source
  tool labels.** Vivado is a commercial-reference validation flow, not the default
  public training-label source.
- Real open-source IP (S5 external-validation set) retains the license of the
  original repository; the wrapper and tool-compatibility patches are open under
  the project license. Real IP is not used for training.
- The dataset card (see §14.2) records the release tier for every field of every
  trajectory version.

---

## §10 Method: Tool-Internalizing Model Stack

### 10.1 What it distills

SR2FPGA trains a **project-level tool-internalizing model stack**, not just a
collection of SFT tasks. The actor generates and repairs FPGA projects; the
critic distills L0–L5 tool-acceptance boundaries into no-tool pass/risk/QoR
predictions. This framing elevates the method from "we do SFT" to "we train an
actor + critic to internalize the EDA toolchain."

- **What it distills:** tool capability internalized — focus Paper ① on
  **generation + self-repair** (read tool errors and fix), the form closest to
  the author's intent. Discrimination (QoR/pass prediction = the QoR predictor
  for Paper ②) is the natural companion task. **(Shift-left framing):** the
  Shift-Left EDA survey (2025, arXiv 2509.14551) identifies "correlating
  early RTL-stage predictions with downstream physical outcomes" as the central
  open challenge in EDA; SR2FPGA's `predicted_qor.json` (model-side, before tool
  execution) vs `measured_qor.json` (Yosys/Vivado-measured) separation + QoR
  calibration is a direct instantiation of shift-left — and the correlation gap
  is an honest limitation to report.
- **Base model (deferred to the modeling stage):** family and size are chosen
  later from then-available compute — the dataset is model-agnostic. Likely
  candidates: code/RTL bases (Qwen2.5-Coder, DeepSeek-Coder, CodeLlama,
  StarCoder2, …) at whatever scale fits (QLoRA on one 4090 is the floor, not a
  ceiling). Base choice can itself be a small comparison experiment.

### 10.2 Actor

Trained on tool-verified trajectories; responsible for generation and repair:

- `REQ2HIS` — requirement → System-HIS (structured requirement understanding);
- `HIS2PROJECT` — System-HIS → multi-file RTL project (skeleton-filling);
- `LOG2DIAG` — tool log → structured diagnosis (internalizes tool error semantics);
- `FAILURE2PATCH` — structured diagnosis → patch (internalizes repair heuristics);
- `ARCH_MUTATE` — HIS architecture-parameter mutation (feeds Paper ② search).

### 10.3 Critic

Trained to internalize tool verdicts; responsible for prediction and risk estimation:

- `PROJECT2RISK` — project → L0–L3 risk score (tool-acceptance prediction);
- `PROJECT2LEVEL` — project → predicted highest passing level L0–L5;
- `PATCH2VERIFY` — proposed patch → pass/fail prediction without running tools;
- `PROJECT2QOR` — project → predicted LUT/FF/BRAM/DSP/Fmax (= `QOR_PRED`).

The critic tasks are what make internalization testable: if `PROJECT2LEVEL` is
accurate, the model has internalized the tool's acceptance boundary; if
`PROJECT2QOR` correlates with measured QoR, the model has internalized resource
utilization. **This claim is valid only if the model-generated behavioral holes
are non-trivial** — recorded by `behavior_hole_count` and `model_token_fraction`;
otherwise the method degenerates into a deterministic generator with a trivial critic.

### 10.4 QoR-search head (Paper ② prerequisite)

Designed now for continuity:
- `HIS2QOR` — HIS architecture params → predicted QoR (fast proxy fitness);
- `ARCH2RANK` — rank HIS variants by Pareto dominance on QoR axes;
- Pareto/risk filtering to reduce expensive L4 tool calls during search.

### 10.5 Contract-preserving generation transparency

To pre-empt "your deterministic generator builds the project and the LLM only
fills trivial holes," **every sample/trajectory records which artifacts are
deterministic and which are model-generated**:

```
{
  "deterministic_artifacts": [
    "manifest", "filelist", "top shell", "testbench scaffold",
    "constraints from board profile"
  ],
  "model_generated_artifacts": [
    "module internals", "control/datapath implementation", "patches"
  ],
  "model_token_fraction": 0.64,
  "behavior_hole_count": 5
}
```

Core statement: **cross-file structure is generated or constrained from
System-HIS; behavioral RTL is generated by the model; tools judge both.** The
method target is **cross-file consistency by construction, functional/physical
correctness by verification**.

### 10.6 Method-novelty candidates

To clear the TCAD bar — choose/deepen one:

(i) **System-HIS-constrained / verification-guided decoding** — generation
constrained by the System-HIS contract so cross-file consistency holds by
construction (differs from CPPL, which enforces consistency by compile-time
checks on a circuit-level IR; ours acts at *decode time* from a
*requirement-level* contract);

(ii) **structured tool-feedback learning** — tool diagnoses as a structured
training signal (diagnosis→patch), not plain SFT on trajectories;

(iii) **two-stage REQ→HIS→Project with consistency constraints**.

Pick/deepen one for TCAD; if none lands, the (a)/(b)/(c) framework still carries
a TRETS paper.

### 10.7 TCAD-strong method claim

The single sentence that must run through Method / Contributions / the abstract
draft: **System-HIS-constrained project synthesis** — deterministic lowering
guarantees cross-file consistency *by construction*, while model-generated
behavioral holes are trained and repaired using **structured EDA-tool
trajectories**. The experiments must show, against this claim:
- L0 structural error rate decreases toward zero;
- L2 functionality does not regress;
- repair iterations decrease;
- structured diagnosis→patch beats raw-log repair.

### 10.8 Method statement (how to articulate it; is it "new"?)

**One-line answer ("what method did you use?"):** *tool-verified learning* — distil
the EDA toolchain's objective judgement into a model, via a **System-HIS
requirement-level IR** (REQ→HIS→multi-file project), with **L0–L5 tool feedback as
supervision**, **structured diagnosis→patch** repair trajectories persisted as a
reusable dataset, and an **(a)/(b)/(c)** measurement of how much tool feedback vs
fine-tuning each add. Anchor: *distil the tool, not the LLM.*

**Three registers (separate them when pressed):** (1) **data-generation method** —
the tool-verified trajectory factory (done); (2) **evaluation method** — project-
level L0–L5 + the L0 consistency checker + (a)/(b)/(c) (done); (3) **model-training
method** — SFT on the trajectory tasks (REQ2HIS/HIS2PROJECT/LOG2DIAG/FAILURE2PATCH/
QOR_PRED) (designed, not yet trained).

**Is it a "new method"? — honest, granularity-dependent:**

- **As a new technique/algorithm: no.** The optimizer is standard (SFT/QLoRA), the
  repair loop is mature (AutoChip…), intermediate representations exist (HLS, CPPL,
  FIRRTL), and distilling tool/test feedback exists (the RL cluster, ChipSeek-R1).
  No single brick is invented here; a sharp reviewer will (correctly) say "known
  techniques applied to a new domain," and TCAD will not accept "QLoRA + a tool
  loop" as the method contribution.
- **As a new methodology / framework: yes, defensibly.** The specific composition —
  tool-oracle distillation + System-HIS *requirement-level* IR + *project-level*
  L0–L5 + the (a)/(b)/(c) decomposition — has not been done; the bricks are old, the
  construction is new. This is a new *way of doing it*, not a new *tool*.
- **To be a "new method" in the strong (TCAD) sense:** one of the method-novelty
  candidates above must be developed into a real technical contribution — best bet
  **System-HIS-constrained / verification-guided decoding** (cross-file consistency
  by *construction* at decode time, distinct from CPPL's compile-time circuit-IR
  checks). That is genuinely new *if built*; today it is a candidate, not done.

**Honest claim discipline (for the defense):** claim "a new **methodology** for
project-level tool-verified RTL generation" and "the method novelty I am deepening
is System-HIS-constrained generation"; do **not** claim "a new training algorithm."
Venue calibration: TRETS rewards the framework + reproducibility + dataset (low
novelty pressure); TCAD requires landing one method-novelty candidate.

---

## §11 Experimental Design

### 11.1 Measurement structure (the fair fights)

The model is NOT sold as "generates better." Everything is measured as **tool
acceptance under a fixed iteration budget**, against the same generator at three
points (this is the operational form of "frontier model = first half of the
chain = baseline"):

- **(a) first attempt, no tools** — the first-half-of-chain baseline;
- **(b) with the tool-in-the-loop feedback/repair loop** — full chain, tools called at inference;
- **(c) the tool-verified fine-tuned model, first attempt, no tools** — tool
  ability internalized into the weights.

The contributions are the deltas:
- **b − a:** does the tool-in-the-loop framework help?
- **c − a:** does tool-verified fine-tuning help?
- **c vs b:** can internalization match the loop *without* calling tools at inference — the strongest result if it holds.

The generator is **swappable**, which yields a strong headline result: use a
large model (GPT/DeepSeek) as the chain's first half for a high baseline, but the
model you can actually fine-tune is a smaller, local one. Then ask: **can a
tool-verified fine-tuned smaller model's (c) reach a large model's (a) or even
(b)?** A small model matching a large one with fewer tool calls is a hard,
publishable result.

Plus one purity ablation that disarms critique #3: **tool-verified trajectories
vs same-source un-filtered distillation trajectories** — does the tool filter
itself add gain? A negative result is still reportable, and either way no one can
call this "just distilling an LLM."

**Optional learned-critic mode** — if the critic tasks are trained, the
measurement can be extended with two additional points:

- **(c1)** fine-tuned **actor**, first attempt, no real tools (= current (c));
- **(c2)** fine-tuned **actor + learned critic** self-check / self-repair, no
  real tools (critic judges the actor's output without calling the tool).

Interpretation:
- **c1 − a:** how much tool-verified fine-tuning improves generation;
- **c2 − c1:** whether the learned critic adds no-tool self-diagnosis value;
- **b − c2:** the gap that real tools still close that the learned critic cannot.

This decomposition is not required for the TRETS-safe version; it is a
TCAD-strong strengthening if the critic tasks are trained.

### 11.2 Statistical measurement protocol

All (a)/(b)/(c) comparisons use the **same** task set, split, hidden tests, repair
budget, timeout, tool versions, prompt family (frozen before official evaluation),
and random seeds where applicable. Report:
- **pass@1**; **pass@k** where applicable;
- repair success within N iterations; median repair iterations;
- **L0/L1/L2/L3/L4 survival curve**;
- per-tier T1–T4 results; per-family results;
- paired comparison for **b−a** and **c−a**;
- bootstrap **95% confidence intervals** where sample size permits.

**Do not collapse L0–L5 into a single averaged ordinal score** — report per-level
pass rates / survival curves instead.

### 11.3 Baselines (B0–B6)

- **B0** direct req→project;
- **B1** req→HIS→project, no deterministic skeleton;
- **B2** req→HIS→skeleton→model fills behavior holes;
- **B3** AutoChip-style raw-log repair;
- **B4** SR2FPGA structured LOG2DIAG→PATCH repair;
- **B5** fine-tuned small model, first attempt;
- **B6** fine-tuned small model + repair.

**Non-LLM sanity baselines** (not compared as LLM baselines; used to validate
the benchmark and anchor QoR targets):

- **B_ref:** deterministic reference implementation emitted by the generator;
  used to validate that the oracle HIS, testbench, and constraints are internally
  consistent and that the task is actually implementable. B_ref passing L0–L3 (or
  L4) is a prerequisite before the task enters the evaluation set.
- **B_template:** deterministic skeleton + component-library composition without
  model-generated behavioral holes; used to calibrate task feasibility and
  establish the reference QoR (LUT/FF/BRAM/DSP/Fmax budgets). QoR reported for
  model-generated designs is measured relative to B_template QoR.

### 11.4 Planned ablations

- **System-HIS:** req→HIS→project vs req→project (proves System-HIS is a
  contribution, not decoration — this is what backs differentiation point 1).
- **QoR prediction calibration:** predicted vs tool-measured correlation /
  calibration curve (predicted QoR must stay model-only, never leak measured
  results — preserve the existing `predicted_qor.json` / `measured_qor.json`
  separation). Note: generic Yosys-L3 LUT is vacuous (Finding G), so a real
  resource/timing calibration needs `synth_xilinx` or the OpenXC7 L4 report.
- **REQ→HIS fidelity:** generated System-HIS vs oracle/manual System-HIS.
- **Contract-preserving (L0-by-construction):** System-HIS-constrained skeleton
  generation vs free generation — show it drives the L0 structural error rate
  toward zero without hurting L2.
- **OpenXC7 vs Vivado commercial-reference validation:** on the same
  representative L4 subset, compare open-flow and commercial-flow pass/fail,
  utilization, WNS/Fmax, DRC/methodology warnings, and runtime. Report
  disagreement cases explicitly using the OpenXC7/Vivado disagreement taxonomy (§7.6).

**Full ablation list:**
- with vs without System-HIS;
- with vs without contract-preserving skeleton generation;
- raw tool log vs structured diagnosis;
- public-only tests vs hidden/random/stress tests;
- tool-filtered trajectories vs unfiltered LLM trajectories;
- L2-core vs L2-UVM on the protocol-heavy subset;
- generic Yosys QoR vs `synth_xilinx`/L4 QoR where applicable.

### 11.5 QoR results: budget / reference / ratio (not raw counts)

QoR is reported **relative to task budgets and reference implementations**, not
only as raw counts. **Do not use generic Yosys-L3 LUT as a strong QoR claim;
meaningful FPGA QoR uses `synth_xilinx` and/or OpenXC7/Vivado L4 reports.** Each
task may declare `resource_budget` (max_lut/ff/bram/dsp), `timing_budget`
(target_fmax_mhz), and `reference_qor` (a deterministic reference implementation).
Report: budget pass rate; generated/reference LUT, FF, BRAM/DSP, and Fmax ratios;
and Pareto dominance / non-dominated count where applicable.

### 11.6 P&R noise and QoR calibration protocol

Post-P&R **utilization is relatively stable** and may be reported from a single
run. **Timing metrics (WNS/Fmax) are backend-heuristic and seed-sensitive**: for
the representative L4 subset, run multiple seeds where supported and report
**mean, std, best, worst**. QoR prediction is evaluated primarily as
**ranking/filtering/risk estimation**: Spearman rank correlation, calibration
error, top-k design-selection accuracy, bad-design filtering accuracy — with
**MAPE only as a secondary metric**.

### 11.7 Scope variants

Two clean exits remove the internal inconsistency between "RQ1/RQ2/RQ4 are the
minimum core" and "the (a)/(b)/(c) fine-tuning is must-have." The dataset +
benchmark + trajectory factory carry a paper either way; what differs is whether
the trained model and one physical result land.

**TRETS-safe version:**
- System-HIS;
- L0–L5 benchmark definition;
- tool-verified trajectory factory;
- L0–L3 scaled results;
- tool-in-loop repair **b−a**;
- failure taxonomy / semantic-gap heatmap;
- **OpenXC7 primary open flow; Vivado fallback optional**;
- L4/L5-min representative physical evidence if available.

**TCAD-strong version:**
- all TRETS-safe components;
- System-HIS-constrained / contract-preserving generation;
- the trained model **(c)**;
- System-HIS ablation;
- structured diagnosis→patch ablation;
- **OpenXC7 primary open flow + Vivado commercial-reference validation on a
  representative L4 subset**;
- at least one verified **L4 / L5-min** physical result;
- **OpenXC7/Vivado agreement/disagreement analysis**.

**RQ5 QoR prediction:** not a Paper ① must-have conclusion; can be reported as a
calibration preview / Paper ② bridge **if L4 labels are available**.

**Out of scope (YAGNI):** retraining a large generation model (insufficient
compute); GA/RL / heavy QoR optimization (Paper ②, needs the QoR predictor as
proxy fitness); commercial-scale large-device results.

---

## §12 Validity, Claims & Review

### 12.1 Threats to validity & the three gates (referee-aware)

A simulated referee-side review (`docs/research-threats-to-validity-2026-06-25.md`,
+ `.zh.md`) found the program is currently a strong, honest **plan + infrastructure +
discovery pilots, not yet an evidence-bearing contribution**. Three reviewers with
different emphasis (evidence/rigor; originality; methodology/reproducibility)
converge on **three gates** that must be cleared for a defensible TCAD method paper —
each is exactly an item the spec already marks as gated:

1. **Train a model under a frozen protocol, at scale** — the (c) / RQ3 headline does
   not exist yet (no model trained); pilots are N≈1/tier, single model, exploratory.
   Report (a)/(b)/(c) per tier with confidence intervals; freeze the prompt
   (prompt-leakage already observed, failure-repair Issue 4).
2. **Build and validate constrained decoding** — the method-novelty core
   (`2026-06-25-system-his-constrained-decoding-design.md`) is design-only; without
   it the contribution is a *methodology*, not a *method*. Show it drives L0→~0 by
   construction without hurting L2.
3. **Land verified physical L4/L5 evidence with commercial reference.** The TCAD
   physical-realization claim cannot rely only on an unverified OpenXC7 spike.
   The minimum TCAD-strong gate is: one OpenXC7 L4/L5-min result, plus Vivado
   commercial-reference validation on a representative L4 subset using the same
   RTL, same fixed board shell, same part, and same logical constraints. Pin tool
   versions; archive timing/utilization/DRC/methodology reports; and explicitly
   classify OpenXC7/Vivado disagreement cases.

Plus the enabling fixes referees will require: data-quality (noisy labels, vacuous
LUT — F/E/G/DQ-H0) and a full-level diagnostic mode so L0 short-circuit does not censor
the L1–L4 distribution (Issue 5). **Honest strength to preserve:** the program does
not overclaim — it labels discovery vs evidence and scopes physics-bound limits out;
keep that discipline in the manuscript.

### 12.2 Claim discipline

Use **"tool-accepted under the specified contract"**, **"functionally accepted by
the generated golden-model testbench"**, **"physically implemented under the
specified constraints"**, or **"Lk-pass"**. Avoid overclaiming: "correct design",
"fully verified", "silicon-proven", "tool replacement". The tools and testbenches
are **objective oracles under a declared contract, not complete proofs of
correctness**.

### 12.3 Reviewer-question checklist

The spec should be able to answer each of these directly:

1. **Is System-HIS more than a prompt template?** → REQ→HIS fidelity + System-HIS ablation.
2. **Does contract-preserving generation make the task trivial?** → deterministic
   vs model-generated artifact metadata + L2/L3/L4 results.
3. **Is the testbench too weak?** → hidden/random/stress tests + coverage +
   assertions + optional L2-UVM.
4. **Does RTL simulation survive synthesis?** → L2S post-synthesis netlist simulation.
5. **Is L4 timing real?** → WNS ≥ 0, no unconstrained paths, no black boxes,
   archived DRC/timing reports.
6. **Does OpenXC7 actually work on this board?** → board-specific spike + Vivado
   reference flow.
7. **Is QoR meaningful?** → `synth_xilinx`/L4 QoR, budgets, reference ratios, P&R
   noise protocol.
8. **Is the data leaking generator templates?** → topology/family/component-heldout
   splits (S1–S5).
9. **Is the failure taxonomy real?** → manual log-label validation.
10. **Is SFT merely distilling an LLM?** → multi-source inputs + tool-filtered vs
    unfiltered ablation + tool-only labels.

---

## §13 Paper ② Overview

Tool-in-the-loop QoR optimization (LUT / performance / power): GA over
architecture/System-HIS parameters and/or RL with a tool-derived reward, using
Paper ①'s QoR predictor as a fast proxy fitness to make large-scale search
feasible on one GPU. GA optimizes architecture parameters, not raw Verilog
tokens (consistent with the research-objective document). The RL flagship case
naturally lives here, on the AC820-ZYNQ (220 DSP + ARM). Closest prior work:
**CktEvo** (repo-level closed-loop LLM+toolchain PPA optimization) — differentiate
by searching the System-HIS architecture-parameter space (not editing existing
repos), using a distilled QoR predictor as proxy fitness, with physical (L4)
labels CktEvo lacks.

---

## §14 Artifacts & Reproducibility

### 14.1 Artifact and reproducibility checklist

For artifact review (TCAD / TRETS / ACM artifact track), the public artifact
should include or reference:

**Environment:**
- Docker / Nix environment reproducing L0–L3 (exact Verilator, Icarus, Yosys versions);
- OpenXC7 / nextpnr-xilinx version for L4-open;
- Vivado version recorded for the restricted commercial-reference subset;
- board profile version (AC820-ZYNQ XC7Z020CLG484-2);
- System-HIS schema version (`system-his-v1.2`);
- generator commit hash and random seeds.

**Data:**
- task split manifest (S1–S5, T1–T4 assignments);
- prompt versions (frozen before official evaluation);
- repair budget, timeout, and tool-call accounting;
- per-trajectory `data_release` tier markers;
- dataset card (see §14.2).

**Reproducing results:**
- command lines for L0–L3 evaluation on the eval set;
- expected runtime per stage (L0/L1/L2/L3, typical);
- representative L4-open (OpenXC7) and L4-commercial (Vivado) script;
- L5 board-shell harness (fixed shell version-locked, host script, golden checksums).

### 14.2 Dataset / benchmark card

For each released dataset version, report and archive:

| Field | Required |
|---|---|
| Version | yes |
| Number of tasks by family and difficulty tier | yes |
| Number of trajectories by split S1–S5 | yes |
| % generated vs real-IP external (S5) | yes |
| Tool versions (Verilator/Icarus/Yosys/OpenXC7/Vivado) | yes |
| L0–L4-open label availability | yes |
| L4-commercial label availability | conditional (if license-cleared) |
| Hidden-test policy | yes |
| Coverage / scenario profile | yes |
| Data-release tier per field | yes |
| Known limitations | yes |
| License of generated data and code | yes |
| Citation | yes |

The dataset card is a named deliverable, not an afterthought — it is what
makes the data contribution reviewable and reproducible by others.

---

## §15 Immediate Next Steps

The framing premise and the component-library MVP are validated; the v1.2 freeze is
implemented (Tier-1). Ordered so oracle hardening precedes scale, and scale
precedes training. Steps 1–6 gate the official (a)/(b)/(c) measurement; step 7
(OpenXC7/Vivado L4-min) runs in parallel and is independent. Specs/plans for the
schema freeze and the OpenXC7 spike already exist; the remaining gate is execution +
scale, not more design.

1. **Measurement freeze** — freeze prompts, seeds, timeout, repair budget, tool
   versions, hidden tests, split policy, and pass/warn/fail semantics. Also ratify
   v1.2 Tier-2 by exercising the provisional fields — `data_flow.timing`, structured
   `control_flow`/FSM, guard grammar — on a real FSM/pipeline task; the RL-agent FSM
   is the reference.

2. **Oracle hardening** — add REQ→HIS fidelity; add L2 hidden/random/stress tests +
   coverage targets; add the assertion library; add optional L2S post-synthesis
   netlist simulation; finalize the L2-core / optional L2-UVM split.

3. **IP/data-release discipline** — finalize the open_public / restricted_reference /
   internal_only tier assignment for each trajectory field; decide whether Vivado
   structured metadata can be released under license; mark all episode schema fields
   with their release tier; document institutional legal review status.

4. **Data-quality fixes** — F (reset/clock label noise), E (taxonomy name drift),
   G (vacuous Yosys-L3 LUT → use `synth_xilinx` or defer QoR to L4), DQ-H0
   (structured tool-signal extraction: L2 mismatch detail, L4 failure families,
   pass-time warnings).

5. **Contract-preserving generation** — System-HIS → deterministic project
   skeleton; model fills behavior holes; record deterministic vs model-generated
   artifact metadata; run the L0-by-construction ablation.

6. **Full-level diagnostic mode** — official verdict mode stays first-failing-level;
   diagnostic mode collects deeper L1–L4 signals (Issue 5).

7. **Scale Line B through L3** — generate enough trajectories for RQ3; report under
   split policy S1–S5. (Current data is N≈1/tier — discovery, not evidence.)

8. **OpenXC7 + Vivado L4 reference spike**
   - run one generated design through OpenXC7 to bitstream
   - run the same RTL/core/board-shell/logical-constraints through Vivado
   - verify exact part `XC7Z020CLG484-2`
   - archive timing/utilization/DRC/methodology reports
   - classify OpenXC7/Vivado agreement or disagreement
   - use the result to define the first L4-open/L4-commercial labels

9. **First SFT model** — produce the first (c) point; start with REQ2HIS,
   HIS2PROJECT, LOG2DIAG, FAILURE2PATCH; evaluate under the frozen (a)/(b)/(c)
   protocol (SFT on one 4090).

10. **Artifact packaging** — create the dataset card (§14.2); create the
    tool-version manifest; create reproduce-L0-L3 script with Docker/Nix
    environment; create representative L4-open / L4-commercial evaluation script;
    version-lock the board shell.

---

## §16 Document Relations & Companion Specs

This document scopes and operationalizes `docs/research-objective-sr2fpga-tcad.md`.
Where they differ, this reframe (compute-calibrated, decomposed into ①/②, tool
oracle as the explicit distillation target, Zynq reproducible flow) governs
near-term work. Update the research-objective document if this direction is adopted.

**Companion specs (to be split out once main sections stabilize):**
This document currently serves as both design spec and paper-protocol reference.
As sections stabilize, the following companion specs should be extracted to keep
the main document executable:

| Companion spec | Contents |
|---|---|
| `sr2fpga-data-release-and-licensing.md` | Full data-release policy, license review checklist, field-level tier assignments |
| `sr2fpga-trajectory-schema.md` | Versioned full episode schema, field definitions, migration notes |
| `sr2fpga-model-stack.md` | Actor/Critic/QoR-head architecture, training task definitions, loss formulations |
| `sr2fpga-artifact-reproducibility.md` | Full artifact checklist, Docker/Nix environment spec, command-line reference |
| `sr2fpga-l4-openxc7-vivado-protocol.md` | L4 run protocol, board shell spec, agreement taxonomy, report archive format |

Until then, the main spec carries summary versions of all these topics (as above)
and the companion specs are forward pointers, not blockers.

---

## Changelog

| Date | Summary |
|---|---|
| 2026-06-22 | Original reframe spec. Research line approved, Paper ①/② decomposed, System-HIS framed, L0–L5 defined, (a)/(b)/(c) measurement structure, target venue (TCAD/TRETS), hard constraints, motivation, and differentiation. |
| 2026-06-25 | Reviewer-hardening update. Tightens verification oracle (L2 coverage-qualified, coverage targets, protocol assertion library), measurement protocol (frozen protocol, per-tier CI, survival curves), L4 physical-pass definition (WNS≥0, 9 criteria, no unconstrained paths, archived reports), data split policy (S1–S5), and claim discipline. Also adds L2F optional property checks, L2S post-synthesis netlist simulation, L2-core vs L2-UVM distinction, OpenXC7/Vivado commercial-reference requirement for TCAD-strong, and REQ→HIS fidelity sub-metric. |
| 2026-06-26 | Artifact/data-release/model-stack update. Adds: (1) explicit IP/licensing/data-release policy (open_public / restricted_reference / internal_only tiers); (2) SR2FPGA tool-internalizing model stack definition (Actor / Critic / QoR-search head, with rationale for why this is a model *stack*); (3) full trajectory episode schema; (4) optional (c1)/(c2) measurement separating generation internalization from learned no-tool diagnosis; (5) failure-injection suite and natural/injected/toolchain failure-origin field; (6) L2F optional property-check layer; (7) artifact reproducibility + dataset card checklists. |
| 2026-06-27 | **Document reorganized.** Content unchanged; sections restructured for navigability. `Paper ① Design` h2 (1527 lines) broken into 12 top-level sections (§1–§12). Episode schema moved from System-HIS to Data Engine (§9.2). Hardware-semantic gap taxonomy moved from Data Engine to Benchmark Design (§8.4). All L4 definition consolidated into §7.6 (previously split across 6 sub-sections). Immediate Next Steps renumbered 1–10. Changelog added. |
