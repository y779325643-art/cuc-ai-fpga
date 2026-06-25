# SR2FPGA Research Reframe Design

## Status

Proposed (2026-06-22). Refines and scopes the direction in
`docs/research-objective-sr2fpga-tcad.md`. This document is the agreed research
line after a critical review of the current data-agent work. It decomposes the
vision into a publishable program and specifies Paper ① in detail.

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
  *Status:* needs the v1.2 generator/checker + a model; not yet run.
- **RQ2 — Value of tool feedback (b−a).** How much does an EDA tool-in-the-loop
  repair loop raise project-level tool acceptance over a no-tool first attempt, and
  at which level / difficulty tier most?
  *Answered by:* (b)−(a) under a fixed iteration budget, per tier. *Gap:* repair
  loops are mature (AutoChip/MAGE/VerilogCoder/PEFA-AI) but single-module/sim, not
  project-level/physical with a reusable trajectory. *Status:* baseline (a)/(b)
  pilot ran (T1/T2→L3, knee at T3); needs scale + prompt freeze.
- **RQ3 — Internalization (c−a, c vs b).** Can tool-verified fine-tuning
  internalize tool acceptance so first-attempt-no-tool (c) approaches the
  tool-in-loop (b)? And can a fine-tuned *small* model's (c) reach a *large*
  frontier model's (a)/(b)?
  *Answered by:* (c) vs (a)/(b) on the same swappable generator. *Gap:* ChipSeek-R1
  internalizes via per-attempt RL, ASIC/single-module, no reusable dataset;
  Representation Bottleneck argues "IR-aware training > model scaling." *Status:*
  no model trained yet — the largest open piece, and the headline result.
- **RQ4 — Failure structure / difficulty calibration.** At project scale, where do
  frontier models start failing across (i) the difficulty axes and (ii) the L0–L5
  verification depth / hardware-semantic gap (seq-comb, backpressure, memory, CDC,
  timing)?
  *Answered by:* baseline (a) across T1–T4 + the per-level failure taxonomy
  (cross-file-consistency error rate + the hardware-semantic failure distribution).
  *Gap:* Representation Bottleneck only tested tiny single-module on Lattice
  (synthesis "transparent"); project-level/Zynq is the excluded regime where L4
  binds; their seq (2.3×)/memory (43%) gradient backs our axes. *Status:* pilot +
  taxonomy exist; needs the full-level diagnostic mode + scale.
- **RQ5 — QoR prediction / shift-left.** Can the model predict QoR
  (LUT/FF/BRAM/DSP/Fmax) before tool execution, and how well does predicted
  correlate with tool-measured?
  *Answered by:* predicted_qor vs measured_qor calibration. *Gap:* MasterRTL does
  pre-synthesis PPA as a separate ASIC predictor; the shift-left survey names the
  predicted↔physical correlation as the open challenge. *Status:* gated — needs
  real measured QoR (OpenXC7 L4; Yosys L3 LUT is vacuous, Finding G); this
  predictor is also Paper ②'s proxy fitness.

**Core vs gated:** RQ1, RQ2, RQ4 are the must-answer minimum publishable core;
RQ3 is the headline but needs a trained model; RQ5 is nice-to-have and gated on the
OpenXC7 L4 spike. All five are operationalized by the enabling infrastructure
contribution — the tool-verified project-trajectory dataset + L0–L5 benchmark +
reproducible req→bitstream→board loop — which is what makes them measurable.

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

### System-HIS schema (v1.1 — structure-contract level; fields extended per task)

**Abstraction level (decided):** structure contract + coarse behavior tags, NOT
a full behavioral spec. System-HIS captures modules / interfaces / connections /
params plus a one-line behavior intent; **functional correctness is verified by
the L2 testbench, not described in HIS**. This keeps HIS an *intent* abstraction
(not another RTL), keeps REQ→HIS learnable, and lets the compositional generator
emit it reliably. L0 checks structure against HIS; L2 checks function.

```
project:   {name, description, top}                 # top = top-level module name
clocks:    [{name, target_fmax_mhz}]                # clock domains + target freq (authoritative for L4/SDC)
resets:    [{name, polarity: active_low|active_high, kind: sync|async}]
modules:   [{
   name, role,                  # role = fifo|arbiter|pipeline|alu|regfile|cdc_sync|decoder|…
   clock, reset,                # which clock/reset domain this module belongs to
   ports:  [{name, dir: in|out|inout, width}],  # width = resolved integer (or "PARAM" ref) so L0 can compare
   params: [{name, value}],
   intent: "<one-line behavior intent, tag-level, not executable>"
}]
# NOTE: the seq/comb distinction is NOT a separate field. In the v1.2 top-down
# schema it is captured structurally — a combinational component owns no `state`,
# has no `clock` domain, and has no `reset_rule` in `control_flow`. See the
# "Hardware-semantic gap" subsection and the v1.2 spec
# (2026-06-24-sr2fpga-system-his-v1.2-topdown-design.md).
connections: [{                 # cross-module contracts = the core of cross-file consistency
   from: "mod.port" | "TOP.port", to: "mod.port" | "TOP.port",
   protocol: register|valid_ready|axi_lite|axi_stream,
   width, cdc: true|false       # cdc=true marks a clock-domain crossing (difficulty axis 4)
}]
top_ports: [{name, dir, width}]                     # top-level external IO
verification: {checks: [...], test_pass_means: "..."}   # acceptance semantics guiding the auto testbench
qor_intent:  {resources: {lut?, ff?, bram?, dsp?}}      # model-side prediction → predicted_qor.json (freq lives in clocks)
```

**Dual use** (why System-HIS is a contribution, not a side artifact): it is the
**intermediate supervision target** (REQ→HIS) for generation, AND the
**ground-truth contract** the L0 checker validates generated RTL against.

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
- **QoR prediction calibration:** predicted vs Yosys-measured correlation /
  calibration curve (predicted QoR must stay model-only, never leak measured
  results — preserve the existing `predicted_qor.json` / `measured_qor.json`
  separation).

### Scope (must-have core vs nice-to-have)

**Must-have core** (the minimum publishable paper):

- compositional multi-module component library + topology generator with
  verification-based testbenches and System-HIS;
- benchmark eval set (tens–hundreds of items, difficulty graded);
- Yosys L0–L3 at scale + baseline (a) across difficulty tiers;
- tool-verified QLoRA fine-tuning with the (a)/(b)/(c) measurement;
- System-HIS ablation.

**Nice-to-have** (only if time/compute allow):

- L4 timing at scale and L5 on-board beyond a few cases;
- the RL-sized flagship case on the AC820-ZYNQ;
- OpenXC7-vs-Vivado comparison depth; QoR calibration depth.

**Out of scope (YAGNI):** retraining a large generation model (insufficient
compute); GA/RL / heavy QoR optimization (Paper ②, needs the QoR predictor as
proxy fitness); commercial-scale large-device results.

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

First, **reconcile with codex's in-flight work**: commit `6c7f273` ("Add
control-oriented multi-module RTL tasks") already moves toward multi-module
tasks, so the component-library slice must build on it — inspect it before
writing code to avoid collisions.

Then the first concrete experiment is **measuring baseline (a)**: run existing
frontier/local LLMs over multiple difficulty tiers through the existing tool
pipeline, recording cross-file consistency error rate and L3/L4 pass rates. It is
the cheapest slice (API/inference + the tool flow that mostly exists), and it
simultaneously (1) validates the framing premise (frontier models fail in the
hard region), (2) calibrates where benchmark difficulty must sit (the pass-rate
knee), and (3) becomes the paper's baseline + motivating experiment. Producing a
small graded multi-module task set (the component-library MVP) is the prerequisite
that feeds this measurement.

In parallel, run an **OpenXC7 spike** on the AC820-ZYNQ — push one
representative multi-module design all the way to bitstream + on-board — to
de-risk the all-open L4/L5 claim early, since the open-flow selling point rests
on it (Vivado stays the fallback if the spike exposes gaps).

Write the implementation plan for the chosen first slice with the writing-plans
skill once this spec is approved.
