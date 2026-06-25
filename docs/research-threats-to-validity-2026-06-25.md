# SR2FPGA Threats to Validity — Referee-Side Review (2026-06-25)

A simulated referee-side assessment of the SR2FPGA research program (reframe spec +
today's infrastructure + discovery-level pilots), produced via the nature-reviewer
skill. Kept as a living threats-to-validity record for paper planning, ablation
design, and honest scoping. Chinese version: `...-2026-06-25.zh.md`.

**Framing:** there is no manuscript draft — this reviews the *research plan +
early infrastructure*, and the target venue is **IEEE TCAD / TRETS, not Nature**.
The Nature-specific axes (broad interdisciplinary readership, readability for
nonspecialists) apply weakly; EDA method-novelty + reproducibility are weighted
instead.

## Review setup

- **Input scope:** reframe spec + System-HIS v1.2 freeze, L0–L5 design, baseline
  pilots, failure-repair log, constrained-decoding design. No results manuscript;
  no trained model; no L4 data.
- **Assessment boundary:** bounded review of a *plan + infrastructure + discovery
  pilots*, not a completed results paper. Anything needing a trained model, scaled
  data, or physical L4/L5 is **not yet assessable**.
- **Shared claim:** tool-verified learning — distil the EDA tool oracle into a model
  that generates/diagnoses/repairs/predicts project-level, multi-file, physically-
  realizable FPGA RTL via System-HIS + L0–L5 + tool-verified trajectories +
  (a)/(b)/(c), with System-HIS-constrained decoding as the method-novelty core.
- **Visible evidence:** v1.2 schema implemented; L0 cross-check verified to catch
  injected mismatches; ~30 runs + 25-issue failure-repair log; baseline (a)/(b)
  pilots (repair knee at T3; failure frontier pushed L0→functional on T4). N≈1/tier,
  single model, exploratory protocol.
- **Missing materials:** trained model / (c) results; scaled dataset; any L4/L5
  result; constrained-decoding implementation; frozen-protocol measurement; CIs.

## Reviewer 1 — emphasis: empirical evidence & rigor

- **Overall:** sound infrastructure, but as a results contribution **not yet
  established** — central claims rest on unrun experiments.
- **Interested readers:** LLM-for-EDA / FPGA-CAD researchers (reusable trajectory
  dataset + L0–L5 evaluation).
- **Strengths:** objective tool supervision; clean (a)/(b)/(c) design; honest
  discovery-vs-evidence separation.
- **Concerns:** the headline RQ3 (c) point **does not exist (no trained model)**;
  pilots N≈1/tier, single model, "discovery not evidence" by the authors' own words;
  the T3 knee + failure-layer progression are anecdotes until replicated at scale.
- **Technical failings:** (1) train ≥1 model, report (a)/(b)/(c) with CIs per tier;
  (2) scale Line B beyond single-digit/tier; (3) freeze the prompt — prompt-tightening
  leakage (Issue 4) confounds b−a/c−a; (4) fix data-quality (noisy reset/clock labels;
  vacuous Yosys-L3 LUT) before any LOG2DIAG/QOR_PRED claim.
- **Posture:** not ready as a results paper; reconsider after scaled execution.

## Reviewer 2 — emphasis: originality & positioning

- **Overall:** framing is original; whether it is a *method* contribution depends on
  an unbuilt component.
- **Interested readers:** IR-for-hardware and tool-feedback-learning researchers.
- **Strengths:** "distil the tool, not the LLM" makes frontier models baselines;
  System-HIS as a requirement-level IR is the "intent/implementation-separating IR"
  Representation Bottleneck (2026) poses as future work; hardware-semantic taxonomy ×
  L0–L5 is a novel organizing contribution.
- **Concerns:** the bare pipeline is component-wise assembled from established
  techniques (RL-with-tool-reward, repair loops, constrained decoding — all exist;
  the authors concede this). The claimed *method* novelty — System-HIS-constrained
  decoding — is **design only, not implemented/validated** → strongest novelty claim
  currently unsupported.
- **Technical failings:** (1) implement + validate constrained decoding (L0→~0 by
  construction; downstream help without L2 harm); (2) a head-to-head vs the RL cluster
  on a shared task; (3) the "no prior HDL constrained-decoding precedent" claim needs
  an exhaustive search.
- **Posture:** conditionally promising for a specialist venue; novelty hinges on the
  constrained-decoding core.

## Reviewer 3 — emphasis: methodology, reproducibility, practical significance

- **Overall:** methodology + reproducibility is the strongest part; physical
  realization is the biggest unverified risk.
- **Interested readers:** FPGA practitioners / small teams without commercial-EDA
  budgets (open license-free flow + public dataset).
- **Strengths:** L0 checker yields the "cross-file consistency error rate" metric
  single-file benchmarks cannot; unusually threat-aware (CDC metastability / board SI
  conceded out of scope; detection≠prevention; accessibility–competence paradox);
  one checker reused as constraint source + verifier.
- **Concerns:** physical L4/L5 — the core TCAD selling point — is **entirely gated on
  an unverified OpenXC7 spike** (XC7Z020 chipdb = single point of failure); current
  "measured QoR" is vacuous (Yosys-L3 LUT=0); many contributions are "acknowledged
  gaps" that collapse to "porting known methods to FPGA" if execution stalls.
- **Technical failings:** (1) one design end-to-end to bitstream + board on real
  silicon, pinned versions; (2) replace vacuous L3 LUT with synth_xilinx/L4 before any
  resource/QoR figure; (3) full-level diagnostic mode so L0 short-circuit (Issue 5)
  doesn't censor the L1–L4 distribution.
- **Posture:** publishable at a reproducibility-weighted venue once one physical result
  + a scaled measurement exist.

## Cross-review synthesis

- **Consensus strengths:** objective tool supervision + (a)/(b)/(c) fair-fight design;
  System-HIS requirement-level IR with an explicit future-work anchor; hardware-semantic
  taxonomy × L0–L5; honest, reproducible, all-open framing; unusual threat-awareness.
- **Consensus technical risks:** (1) no executed results — the headline (c)/RQ3 needs a
  trained model that doesn't exist; (2) the method-novelty core (constrained decoding)
  is unbuilt → methodology, not method; (3) physical L4/L5 gated on an unverified spike
  with single-point chipdb risk; (4) measurement validity — prompt leakage observed,
  data-quality defects recorded, N≈1/tier.
- **Where emphasis differs:** R1 = run at scale; R2 = build + prove the novel technique;
  R3 = land one physical result + reproducibility. All three are prerequisites, not
  alternatives.
- **Broad-interest readout:** for a specialist EDA venue, significance is real;
  Nature-style broad-interest fit is not the relevant axis and is not claimed.
- **Most important issues before a strong case:** (i) scaled, frozen-protocol
  (a)/(b)/(c) with a trained model + CIs; (ii) constrained decoding implemented and shown
  to make L0 hold by construction without hurting L2; (iii) one verified physical L4/L5
  result; (iv) fix data-quality + add full-level diagnostics.

## Risk / unsupported claims

- **Not assessable (no evidence):** any (c)/internalization result; small-reaches-large;
  QoR-prediction correlation; L4 physical claims; that constrained decoding works.
- **Asserted but unverified:** "no prior HDL constrained-decoding precedent" (quick
  search only); OpenXC7 XC7Z020 chipdb availability; PICARD exact citation.
- **Conceded-but-load-bearing:** "acknowledged gap" contributions are real only if
  L4/board + a real trajectory dataset are delivered (the spec's own caveat).
- **Honest-strength to preserve:** the program does not overclaim — it labels discovery
  vs evidence and scopes physics-bound limits out.

## Bottom line

Strong, honest *plan + infrastructure*; **not yet an evidence-bearing contribution.**
The three things converting it from "promising methodology" to "defensible TCAD method
paper" are exactly the three the spec already lists as gated: **train a model (scaled,
frozen protocol), build constrained decoding, and land one physical L4/L5 result.**
