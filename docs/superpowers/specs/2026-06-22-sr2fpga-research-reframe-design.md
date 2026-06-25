# SR2FPGA Research Reframe Design

## Status

Approved direction; **originally 2026-06-22, last updated 2026-06-25.** The agreed
research line, refining/scoping `docs/research-objective-sr2fpga-tcad.md`,
decomposing the vision into a publishable program and specifying Paper ① in detail.
A Chinese companion (`2026-06-22-sr2fpga-research-reframe-design.zh.md`) is kept in
sync. Where this spec and the objective doc differ, this reframe governs near-term
work.

**Infrastructure & evidence state (2026-06-25):** the data-generation agent runs
L0–L3 with an objective tool oracle; **System-HIS v1.2 is frozen and implemented**
(deterministic generator emits v1.2 for all task families; the v1.2 L0 checker does
HIS↔RTL cross-checks with verified teeth — it catches injected port/testbench
mismatches; legacy/v1.1 quarantined) — **Tier-1 of the freeze ratification gate is
met.** An extensive **exploratory experimental process is documented** — baseline
(a)/(b) pilots, ~30 runs, and a 25-issue failure-repair research log with paper
hooks — yielding **discovery-level findings**: cross-file consistency is the repair
knee; the T4 failure frontier was pushed L0→lexical→lint→sim→functional;
prompt-tightening can leak; L0 can mask deeper RTL failures. These are **discovery,
not yet scaled evidence** (N≈1/tier, single model, exploratory protocol). **Not
yet:** scaled trajectory data, the trained-model (c) point (RQ3), L4 physical
(OpenXC7 spike), and the data-quality fixes (F/E/G).

## Target Venue

**Primary target: IEEE TCAD**, with **ACM TRETS as the fallback** — aim high,
decide at submission by what was actually achieved. Both reward the
physical-realization + reproducibility story; TCAD additionally demands the
method novelty TRETS relaxes (see the last point). A helper for either: the
**AC820-ZYNQ (XC7Z020) is a mainstream commercial Xilinx device**, so TCAD's
"is this realistic silicon?" reflex is already answered — a better fit here than
a small Lattice part. Emphasis:

- **Physical realization is the main dish, not a garnish:** L4 timing closure +
  L5 on-board runs + resource/Fmax/power reporting are core evidence.
- **A fully open, reproducible closed loop** (req→bitstream→board) is a primary
  selling point TRETS rewards. The author's **AC820-ZYNQ board (chip
  XC7Z020CLG484-2) is in OpenXC7's support list**, so an all-open
  Yosys→nextpnr-xilinx (OpenXC7)→bitstream→board flow on a *real Xilinx device*
  is feasible — pending a spike verification. **Vivado is kept as a
  fallback/baseline**, and the **OpenXC7-vs-Vivado comparison is itself a bonus**
  (usability/QoR of open tools on LLM-generated RTL). All code/data/scripts/
  device public, tool versions pinned.
- **Method novelty is the gap to close for TCAD** (not relaxed): TCAD will not
  accept "QLoRA fine-tuning + a tool loop" as the method contribution — it needs
  a genuine methodological idea (see Method → "Method-novelty candidates"), plus
  scale beyond the TRETS minimum. If novelty/scale do not land, drop to TRETS
  (which gates far less on novelty); the rest of the paper is unchanged.

## Motivation

### Why this question matters (the external case)

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
and out of reach (CDC metastability, board signal integrity; see threats to
validity). So success is **not** "replace the tool"; it is the measured deltas
**(b−a)** and **(c−a)** — how much tool-in-the-loop feedback and tool-verified
fine-tuning each add — plus mapping the L0–L5 boundary of what internalizes vs
what must stay with the tool. A partial answer is still a result.

### Why the reframe (the internal trigger)

A harsh-reviewer pass over the current state found a real risk: the project has
a high-quality data pipeline but **no scientific result yet**, and its initial
tasks (`counter`, `fifo`, `simple_fsm`, `ram_read_write`) are too easy — strong
base models pass them at L3 in one shot, so the repair loop never triggers and
`failure_to_patch` stays empty. Fixing the task difficulty is the root that
relieves most downstream symptoms.

This reframe keeps the author's true goal — **a model that generates a complete
RTL project from a natural-language requirement and repairs it from tool
feedback** — but makes it defensible and feasible under the real resource budget.

## Practical significance (real-world impact)

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
metastability, board signal integrity) stays with the tools/humans (see threats
to validity). Real-world reach at PhD scope = **small/medium designs + an assisted
workflow + the dataset/benchmark/open-flow as public goods**, not a deployed
product.

## Hard Constraints (shape every decision below)

- **Compute:** single RTX 4090 24 GB for any local fine-tuning. **Not feasible:**
  pretraining or training a generation model that beats GPT-5 / DeepSeek
  head-to-head — that ambition is abandoned. **Model size is deliberately not
  fixed now:** dataset and benchmark design must stay model-agnostic; model and
  scale are chosen at the modeling stage from whatever compute is available then.
  **Current priority is building the dataset.**
- **Data:** none exists; all trajectories are generated from scratch by running
  tools locally. **Labels come entirely from tools** (open-source Yosys/Verilator/
  Icarus for L0–L3, OpenXC7/Vivado for L4–L5), so "tool-verified learning" is literally
  true — the supervision is the tool, not another LLM.
- **Hardware:** on-board validation uses the author's **AC820-ZYNQ board** —
  chip **XC7Z020CLG484-2** (~53k LUT, 220 DSP, dual-core ARM; large enough for
  big designs and an RL flagship case). The device is **in OpenXC7's support
  list**, enabling an all-open req→bitstream→board flow (subject to spike
  verification); **Vivado is the fallback/baseline**.

## Core Reframe: distill the TOOL, not the LLM

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

## Frontier Models Are the First Half of the Chain (the baseline)

A frontier model generating a complete project directly is **not a competitor —
it is a measurement point inside the chain**: it is exactly the
"first-half, no-tool-feedback, first-attempt generation" baseline. So "competing
with GPT" turns from a threat into the **baseline + ablation** of this work. A
stronger frontier model only raises the starting point; the scientific
contribution is **how much tool feedback adds on top of it**.

Frontier-model status (qualitative, **to be measured, not asserted from
numbers** — see "Immediate next step"): today's frontier models reliably handle
single-file / small RTL (this is why DeepSeek passed the smoke counter at L3 in
one shot) and can emit *formally* multi-file projects, but they do **not
reliably** produce large, strongly cross-file-consistent, timing-closing,
board-ready projects — cross-file/cross-module contract errors and L4 timing are
their failure region. That failure region is the open space this work targets,
and it is why benchmark difficulty must be calibrated to where the frontier pass
rate starts to drop.

## Program Decomposition (this is a 2–3 paper program, not one paper)

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

## Paper ① Design

### One-sentence thesis

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

### Research questions

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

### How prior work addresses each RQ (and what it leaves open)

A view organized by RQ (complementary to the work-type field map below). Per RQ:
how the field solves it, and the opening we take.

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

### Differentiation (related-work map; full lit-review in the author's vault)

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

Field map (what each line is, and why it is not us):

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
  bottleneck, and offer their framework as the infrastructure to assess such
  future IRs — i.e. **System-HIS is the IR their paper poses as future work.**
  Two of their findings also empirically back our design: the bottleneck widens
  for **sequential (2.3×) and memory (43% aggregate) designs vs combinational
  (1.3–1.4×)** — backing our seq/comb + memory difficulty axes — and they conclude
  improvement should come from **IR-aware training, not model scaling** — backing
  "frontier model = baseline, fine-tune on tool-verified data." Their
  **"accessibility–competence paradox"** (friendlier IRs → worse LLM performance)
  is a design caution for System-HIS, recorded under threats to validity.
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
  benchmark production but orthogonal in purpose (circuit-level ML data vs
  requirement-level verifiable project + trajectory).

The model/data is a method contribution riding on these, **not** a SOTA-model
claim.

### Gaps we fill (acknowledged by the field)

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
| All LLM-to-RTL works use black-box pass/fail; none categorize errors by **hardware-semantic type** (the software→hardware gap) nor train with semantics-aware supervision (MeltRTL "hardware-specific inaccuracy" is closest but still uses simulation pass rate) | SR2FPGA **hardware-semantic failure taxonomy cross-indexed against L0–L5** (seq/comb at L1, backpressure at L2, memory inference at L3, CDC structurally at L0, timing at L4) — see "Hardware-semantic gap" below |

**Caveat (the honest catch):** these are *acknowledged* gaps, so the contribution
is real only if execution actually reaches L4/on-board and a real trajectory
dataset is built — otherwise it collapses to "porting known methods to FPGA."

### Core argument

The point of "project-level" is **not** "bigger code." It is **correctness
structure (multi-module + cross-file/cross-module consistency) + physical
realizability (synthesis / timing closure)**. System-HIS is the bridge from a
requirement to that structure (function, ports, widths, clock/reset, FSMs,
datapaths, storage, interfaces). Entry ticket: the generated object must be a
**variable-topology multi-module design** (a top instantiating several submodules
with consistent ports/params across files), not a fixed 6-file template —
otherwise "project-level" collapses.

### System-HIS schema (canonical: v1.2 — frozen; see the freeze spec)

**The canonical schema is `system-his-v1.2`, frozen and implemented** (full field
definitions in `docs/superpowers/specs/2026-06-24-sr2fpga-system-his-v1.2-freeze-design.md`;
the prototype `-topdown` and the inline v1.1 below are superseded). This subsection
keeps only the *argument* and the aspect skeleton; the freeze spec is the field
authority.

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

Key v1.2 properties (full rationale in the freeze spec): `components` vs
`instances` resolves the repeated-instance ambiguity v1.1 had; the seq/comb
distinction is **structural** (a combinational component owns no `state`/`clock`/
`reset_rule`); `data_flow.timing` makes pipeline depth + throughput first-class
(forward-compatible with Paper ②); `control_flow` is load-bearing, verified at L2,
and drives testbench generation; guard nesting is capped at depth 2 (the intent/RTL
line). **Provisional fields** (`data_flow.timing`, structured `control_flow`/FSM,
guard grammar) are Tier-2 of the ratification gate — implemented and checked, but
not required in the REQ2HIS target until a real task exercises each.

**Dual use** (why System-HIS is a contribution, not a side artifact): it is the
**intermediate supervision target** (REQ→HIS) for generation, AND the
**ground-truth contract** the L0 checker validates generated RTL against.

**Quarantine:** legacy / `system-his-v1.1` samples are labeled and kept for
traceability, **excluded from the clean REQ2HIS training split** (no migration
tool; re-generation under v1.2 is the path to clean data).

Fields are extended per task as new design families are added — e.g. Paper ②'s
searchable architecture params (parallelism / pipeline depth / memory banks)
will live here later.

### Benchmark design

- **Single item form (verification-based, NOT reference-matching):** RTL has no
  unique correct answer, so ground truth is "passes the acceptance criteria,"
  never "matches a reference file." Input = NL requirement + machine-readable
  interface contract. Judgement = L0–L5 tool verdicts + functional testbench.
- **Production mechanism — compositional program generation as the main force:**
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
    load-bearing reason to prefer program generation over LLM-authored tests (no
    one can certify an LLM-written testbench).
  - **Golden model for algorithm-family tasks:** self-consistency proves the RTL
    reference and testbench *agree*, not that they compute the *right* math. For
    algorithm modules (FIR, FFT, matrix-multiply, CORDIC, accumulators, MAC), the
    generator must also emit a **software golden model** (Python/NumPy) that
    produces the testbench's expected values, so L2 catches "runs but the numbers
    are wrong" bugs (e.g. width truncation `8b×8b` kept at 8b, signedness errors).
    Without a golden source, value-checking tasks degrade to self-consistency only
    and miss exactly the silent-numeric failures the taxonomy's
    `internal_width_truncation` / `signedness_error` classes target.
  - **(Distinction from SynCircuit, HKUST 2025):** SynCircuit generates synthetic
    RTL at the circuit-graph level (diffusion + MCTS) for ML4EDA data augmentation
    — no NL input, no testbench, no project structure. Our generation is at the
    requirement-intent level, producing verifiable multi-file projects + acceptance
    testbenches + tool trajectories. Different purpose and different abstraction
    level; SynCircuit demonstrates that purely synthetic RTL generation is feasible
    and that data scarcity is a shared problem.
- **Testbench discipline:** test the **black-box interface contract only**
  (port behavior, protocol timing, functional correctness); never depend on
  internal signal names / implementation details — this is what keeps the
  benchmark fair to any implementation.
- **Anti-leakage:** held-out parameter combinations + randomization make
  concrete instances effectively unseen in any training corpus. (Real open-source
  IP is the leakage risk, not synthetic instances.)
- **Sources (mixed):** compositional synthetic tasks as the main body (controlled
  difficulty, scalable, leakage-safe), plus a small set of real open-source IP
  (OpenCores / LiteX …) as external-validity anchors. An LLM may **surface-rewrite**
  the program-generated requirement text into more natural language — wording only,
  never touching semantics or acceptance — to mitigate the "synthetic NL" critique.
- **Difficulty axes (all four, with the first two primary):**
  1. cross-module / cross-file consistency (number of interface/param contracts) — primary
  2. timing pressure (target Fmax / critical-path depth) — primary
  3. protocol/control complexity (register → valid/ready → backpressured pipeline → AXI4-Lite/Stream) — the carrier that drives axis 1 up
  4. structural scale (submodule count / hierarchy depth) and CDC — high-difficulty tier
- **Difficulty tiers (to report the frontier pass-rate knee):** map the axes onto
  **T1 Easy / T2 Medium / T3 Hard / T4 Stress** by submodule count, number of
  cross-module contracts, protocol class, and target Fmax (concrete thresholds
  fixed during the baseline (a) measurement). Pass rates are reported **per tier**
  so the knee where frontier models start failing is visible.
- **Scale:** thousands to ~10k samples, not millions (data-volume-realistic). Benchmark
  items are mostly small/medium multi-module designs (an RL-sized accelerator is
  a *flagship case*, not the body — see scope). The existing deterministic
  `ProjectGenerator` is the seed of the component library.

### Evaluation levels and toolchain

- **L0** project contract + cross-file consistency; **L1** lint (Verilator);
  **L2** functional simulation (Icarus Verilog); **L3** synthesis + measured QoR
  (Yosys); **L4** place-and-route timing closure (**OpenXC7 on the AC820-ZYNQ /
  XC7Z020CLG484-2, Vivado as fallback/baseline**, report Fmax/slack); **L5**
  sparse representative on-board runs (AC820-ZYNQ).
- **L0 consistency checker (a named component, not a side note):** validates the
  generated RTL against the System-HIS contract — top instantiates the declared
  modules; every port name/direction/width, parameter, and cross-module
  connection matches System-HIS; the testbench instantiates the real top;
  constraints reference real ports. This automates the cross-file-consistency
  verdict and yields the **"cross-file consistency error rate"** metric — the
  structural check single-file benchmarks structurally cannot do.
- **Toolchain (all-open primary, Vivado fallback):** synthesis and large-scale
  data through **L3 use Yosys** (open, fast, free — fits thousands of samples);
  **L4 timing closure + L5 on-board use OpenXC7 (nextpnr-xilinx) on the
  AC820-ZYNQ** (XC7Z020CLG484-2, in OpenXC7's support list; 220 DSP / ARM host
  the larger designs incl. an RL flagship case), giving an all-open
  req→bitstream→board loop — **subject to an early spike verification**.
  **Vivado is the fallback/baseline** so L4/L5 results are never lost to
  open-tool immaturity, and **OpenXC7-vs-Vivado (usability/QoR) is a bonus
  comparison** TRETS readers value. All code/data/scripts/device public, tool
  versions pinned.

### Data engine (two production lines)

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
- **Hardware-semantic gap — failure taxonomy cross-indexed against L0–L5
  (a named contribution, not just "more error types"):** LLMs are pre-trained on
  software (sequential-execution) semantics and systematically fail at hardware's
  concurrent/physical semantics. Crucially, **each class of this gap surfaces at a
  different verification depth**, so the L0–L5 hierarchy is not only "verification
  depth" but "depth of hardware-semantic understanding required." This reframes the
  failure-taxonomy contribution from "we have a taxonomy" to "we map the
  software→hardware semantic gap onto a verification-depth hierarchy" — and shows
  why prior work (stopping at L2/L3) covers only the front half of the gap.

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

  **Honest boundaries (threats to validity — state in the paper, do not overclaim):**
  - CDC: structural only (synchronizer present), **not** behavioral — metastability
    is not verifiable in sim (aligned clocks) and only sparsely/nondeterministically
    on-board.
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
    this honestly (it does not assume "add a higher-level IR ⇒ better" — it
    *measures* it).

- **Priority tiers for the hardware-semantic taxonomy:**
  - **Tier A (Paper ① core — observable now at L0–L3, low marginal cost):**
    seq/comb (L1), memory/BRAM inference (L3), valid-ready backpressure (L2). Each
    feeds a *different* training view — seq/comb → `LOG2DIAG`/`FAILURE2PATCH`,
    BRAM-miss → `QOR_PRED` (a *soft* failure: passes L3 but blows the resource
    budget, a live shift-left predicted-vs-measured sample), backpressure →
    functional `FAILURE2PATCH` that sim-pass benchmarks miss because their
    testbenches never apply backpressure.
  - **Tier B (structural now, physical later):** CDC — do the L0 structural check
    + a synthetic injector ("remove synchronizer") now; defer metastability/L5 to
    nice-to-have.
  - **Tier C (gated on L4):** SDC/timing closure — defer to after the OpenXC7
    spike; port-name checks against constraints already live in the L0 checker.

  `classify_failure()` detects the Tier-A classes from Verilator/Icarus/Yosys logs
  without manual annotation; the labels are recorded as named sub-categories of
  `failure_to_diagnosis`.

- **Where these land in System-HIS v1.2 (no schema redesign needed):**
  - seq/comb: captured **structurally** — a combinational component owns no
    `state`, no `clock`, no `reset_rule`; a future L0 extension flags "declared
    combinational but RTL has `always @(posedge clk)`."
  - memory/BRAM: extend `state.memories[]` with `memory_style: block|distributed`
    and `read_type: sync|async`; L3 compares intent against Yosys-measured BRAM.
  - CDC: `instances[].semantic_kind: cdc_sync` + a `cdc` flag on the crossing
    `data_flow`; L0 verifies a synchronizer instance sits on the crossing path.
  - backpressure: `verification.scenarios[]` includes a backpressure stimulus;
    `control_flow` already enumerates `handshake_rule` and `stall_rule`.

### Method (the model)

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
- **Framework:** tool-in-the-loop (generate → tool check → feedback on
  errors/resources → regenerate/repair → record), matching the author's
  steps 1–4.
- **Method-novelty candidates (to clear the TCAD bar — choose/deepen later):**
  (i) **System-HIS-constrained / verification-guided decoding** — generation
  constrained by the System-HIS contract so cross-file consistency holds by
  construction (differs from CPPL, which enforces consistency by compile-time
  checks on a circuit-level IR; ours acts at *decode time* from a
  *requirement-level* contract); (ii) **structured tool-feedback learning** — tool
  diagnoses as a structured training signal (diagnosis→patch), not plain SFT on
  trajectories; (iii) **two-stage REQ→HIS→Project with consistency constraints**.
  Pick/deepen one for TCAD; if none lands, the (a)/(b)/(c) framework still
  carries a TRETS paper.

### Method statement (how to articulate it; is it "new"?)

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

### Measurement structure (the fair fights)

The model is NOT sold as "generates better." Everything is measured as **tool
acceptance under a fixed iteration budget**, against the same generator at three
points (this is the operational form of "frontier model = first half of the
chain = baseline"):

- **(a) first attempt, no tools** — the first-half-of-chain baseline (what a
  frontier/base model alone does);
- **(b) with the tool-in-the-loop feedback/repair loop** — full chain, tools
  called at inference;
- **(c) the tool-verified fine-tuned model, first attempt, no tools** — tool
  ability internalized into the weights.

The contributions are the deltas:

- **b − a:** does the tool-in-the-loop framework help?
- **c − a:** does tool-verified fine-tuning help?
- **c vs b:** can internalization match the loop *without* calling tools at
  inference — the strongest result if it holds.

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

### Planned ablations

- **System-HIS:** req→HIS→project vs req→project (proves System-HIS is a
  contribution, not decoration — this is what backs differentiation point 1).
- **QoR prediction calibration:** predicted vs tool-measured correlation /
  calibration curve (predicted QoR must stay model-only, never leak measured
  results — preserve the existing `predicted_qor.json` / `measured_qor.json`
  separation). Note: generic Yosys-L3 LUT is vacuous (Finding G), so a real
  resource/timing calibration needs `synth_xilinx` or the OpenXC7 L4 report.

### Scope (must-have core vs nice-to-have)

**Must-have core** (the minimum publishable paper):

- compositional multi-module component library + topology generator with
  verification-based testbenches and System-HIS;
- benchmark eval set (tens–hundreds of items, difficulty graded);
- Yosys L0–L3 at scale + baseline (a) across difficulty tiers (real measured QoR
  needs `synth_xilinx` / L4 — Finding G);
- tool-verified QLoRA fine-tuning with the (a)/(b)/(c) measurement;
- System-HIS ablation.

**Nice-to-have** (only if time/compute allow):

- L4 timing at scale and L5 on-board beyond a few cases;
- the RL-sized flagship case on the AC820-ZYNQ;
- OpenXC7-vs-Vivado comparison depth; QoR calibration depth.

**Out of scope (YAGNI):** retraining a large generation model (insufficient
compute); GA/RL / heavy QoR optimization (Paper ②, needs the QoR predictor as
proxy fitness); commercial-scale large-device results.

### Threats to validity & the three gates (referee-aware)

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
3. **Land one verified physical L4/L5 result** — the core TCAD selling point is gated
   on the unverified OpenXC7 spike (XC7Z020 chipdb = single point of failure); current
   measured QoR is vacuous (Finding G). Pin tool versions; one design to bitstream +
   board.

Plus the enabling fixes referees will require: data-quality (noisy labels, vacuous
LUT — F/E/G/H0) and a full-level diagnostic mode so L0 short-circuit does not censor
the L1–L4 distribution (Issue 5). **Honest strength to preserve:** the program does
not overclaim — it labels discovery vs evidence and scopes physics-bound limits out;
keep that discipline in the manuscript.

## Paper ② (brief)

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

## Relationship to existing documents

This document scopes and operationalizes `docs/research-objective-sr2fpga-tcad.md`.
Where they differ, this reframe (compute-calibrated, decomposed into ①/②, tool
oracle as the explicit distillation target, Zynq reproducible flow) governs
near-term work. Update the research-objective document if this direction is
adopted.

## Immediate next step

The framing premise and the component-library MVP are validated; the v1.2 freeze is
implemented (Tier-1). Near-term, dependency-ordered:

1. **Finish + commit the v1.2 freeze** (codex). Tier-1 is met; ratify Tier-2 by
   exercising the provisional fields (`data_flow.timing`, structured `control_flow`/
   FSM, guard grammar) on a real FSM/pipeline task (the RL-agent FSM is the
   reference).
2. **Fix the data-quality debts before scaling** — F (noisy reset/clock labels),
   E (taxonomy name drift), G (vacuous Yosys-L3 LUT → use `synth_xilinx` or defer
   LUT to L4), H0 (extract structured tool signal: L2 mismatch detail, L4 failure
   families, pass-time warnings). See the training-data-quality issue log.
3. **Set the measurement discipline** — freeze the generation + repair prompt
   (prompt-leakage was observed, failure-repair Issue 4) and add a full-level
   diagnostic mode so an L0 failure does not mask the L1–L4 distribution (Issue 5).
4. **Scale the trajectory data (Line B)** through L3 — the biggest blocker for RQ3;
   current data is N≈1/tier (discovery, not evidence).
5. **OpenXC7 spike** on the AC820-ZYNQ (Windows+WSL2; spec + plan ready) → unblocks
   L4 + RQ5 (real measured QoR; the report becomes RQ5's training signal).
6. **Train the first model** on the scaled tool-verified data → the (c) point /
   RQ3 headline (start with L0–L3 generation + repair; SFT on one 4090).

Steps 2–4 gate the official (a)/(b)/(c) measurement; the OpenXC7 spike (5) runs in
parallel and is independent. Specs/plans for the schema freeze and the OpenXC7
spike already exist (writing-plans done); the remaining gate is execution + scale,
not more design.
