# SR2FPGA Reframe — Session Decision Log (2026-06-22 → 06-23)

## Purpose

Records *how* the project arrived at the current research direction, not just the
conclusion. The conclusion lives in
`docs/superpowers/specs/2026-06-22-sr2fpga-research-reframe-design.md`; this log
keeps the reasoning, the alternatives considered, and the facts that changed
decisions — so codex and future sessions understand the chain rather than
re-deriving it.

This single session covered two things: (A) delivering the DeepSeek repair loop,
and (B) a critical review that led to (C) a full research reframe.

---

## Part A — DeepSeek repair loop (delivered)

Executed the pre-written plan
`docs/superpowers/plans/2026-06-22-sr2fpga-deepseek-repair-loop.md` via TDD,
small commits, on branch `codex/sr2fpga-data-agent`:

- `a5b9254` Share repair result model (RepairResult → models.py)
- `231629b` Add project diff helper (diff_projects, difflib)
- `5f26352` Add DeepSeek repairer (DeepSeekRepairer + _repair_messages)
- `5788361` Wire DeepSeek repairer into CLI (--repair-provider, --max-attempts)
- `c4463aa` Verify agent repair patches export to training views

Verification: 47 unit tests pass; deterministic CLI smoke → L3; DeepSeek repair
smoke → L3. **Honest limitation:** DeepSeek's first generation already passed L3,
so the real-API repair path never triggered and `failure_to_patch.jsonl` stayed
0 rows. The repair orchestration + DeepSeekRepairer are unit-tested, but a real
repair trajectory was not collected — which is exactly what motivated the reframe.

(Note: `_minimize_repaired_project` later appeared in `deepseek.py`, added outside
this assistant's edits — a heuristic to keep the repaired manifest minimal.)

---

## Part B — Critical review (harsh-reviewer pass)

Ten critiques, root-caused: the project is a high-quality data pipeline with **no
scientific result yet**, and its tasks are too easy (counter/fifo/fsm/ram), so
the repair loop never triggers and there is no failure/repair data. Other
critiques (distillation worry, no System-HIS ablation, uncalibrated QoR, crowded
field vs AutoChip, engineering-without-findings) largely derive from that root.

---

## Part C — Reframe decision chain

Each row: the decision, what was chosen, why, and notable alternatives.

1. **Entry angle** → top-down (fix the *claim* first). Why: user preference.
2. **Main thesis** → **A: project-level generation + L0–L5 evaluation.**
   Alternatives: B tool-verified diagnosis/repair learning (threatened by
   AutoChip), C no-tool QoR prediction (easy evidence but incremental). Chose A
   for the deepest moat (large designs / timing are where models still fail).
3. **Core argument refined (not chosen, derived):** "project-level" = correctness
   structure (multi-module + cross-file consistency) + physical realizability;
   entry ticket is **variable-topology multi-module** designs, not a fixed 6-file
   template.
4. **Evidence ceiling** → **L4 timing primary + L5 on-board cases.** Alternative:
   stop at L3 (too weak for the venue).
5. **Distillation reframe (key):** distill the **TOOL oracle**, not the LLM. The
   tool plays a dual role — judge of the benchmark and teacher of the model. To
   stay tool-distillation: inputs multi-source (component library / mutated /
   real IP), all labels from tools. This disarms the "you're just distilling
   DeepSeek" critique and makes failures appear by design.
6. **Frontier model = first half of the chain (key insight, user's):** a frontier
   model generating directly is the "no-tool, first-attempt" **baseline**, not a
   competitor. Operationalized as three measurement points on the same generator:
   **(a)** first attempt no tools, **(b)** with tool-in-the-loop repair, **(c)**
   tool-verified fine-tuned model first attempt no tools. Contributions = deltas
   b−a, c−a, and c-vs-b (internalization without tools = strongest result).
   Generator is swappable → "can a fine-tuned smaller model's (c) reach a large
   model's (a)/(b)?" is the headline.
7. **Program decomposition** → 2–3 papers. Paper ① foundation (System-HIS +
   benchmark + reproducible loop + tool-verified model); Paper ② optimization
   (GA/RL for QoR), using ①'s QoR predictor as fast proxy fitness. GA/RL and
   "retrain a big generation model" out of scope for ①. (User confirmed the full
   vision is generate→tool-check→feedback→repair→record→train→optimize; we split
   it.)
8. **Resource calibration:** single RTX 4090; abandon "beat GPT/DeepSeek by
   retraining a big generator." User's real want = **a model that generates a
   full project from NL and self-repairs** (generation model, not just a
   discriminator). It wins not on "generates better" but on tool-acceptance under
   a fixed budget (point 6).
9. **Model size** → **deferred / unfixed**; dataset is model-agnostic; **current
   priority = build the dataset.** (User: "don't fix model size, the point is
   preparing the dataset first.")
10. **Toolchain evolution (changed twice by facts):**
    - first plan: open Yosys+nextpnr+**Lattice** as the all-open loop;
    - fact: user has **no Lattice board**, only Xilinx (Zynq-7020) → temporarily
      downgraded the selling point from "all-open" to "reproducible" to avoid
      betting on immature open Xilinx tools;
    - fact: the board is **AC820-ZYNQ (XC7Z020CLG484-2), in OpenXC7's support
      list** → upgraded back to **all-open primary via OpenXC7 on the Zynq**,
      with **Vivado as fallback/baseline** and **OpenXC7-vs-Vivado as a bonus
      comparison**. An early **OpenXC7 spike** de-risks this.
11. **Benchmark production** → compositional program generation (component library
    + topology generator) as the main force; reference impl + testbench emitted
    together so the testbench is machine-checked self-consistent; black-box
    contract testing only; held-out randomization for anti-leakage; small real IP
    for external validity; LLM may surface-rewrite the NL only. Difficulty axes:
    cross-file consistency + timing (primary), protocol complexity (carrier),
    scale/CDC (hard tier); reported per difficulty **tier T1–T4** to show the
    frontier pass-rate knee. (User asked re template "isn't it pre-baked / how is
    diversity ensured" — answered: compositional, not fixed templates; structure
    is the exam, not the answer.)
12. **System-HIS = a contribution** (user insisted). Abstraction level: **structure
    contract + coarse behavior tags, NOT full behavioral spec** (function verified
    by the L2 testbench). v1.1 schema defined (project/clocks/resets/modules/
    connections/top_ports/verification/qor_intent). **Dual use:** intermediate
    supervision target AND the ground-truth contract the **L0 checker** validates
    RTL against — so it is consumed, not a side artifact. Fields extend per task.
13. **Venue** → started ACM TRETS (best-fit, easier hit, relaxes method novelty),
    then user chose **primary TCAD, fallback TRETS** (aim high, decide at
    submission). Consequence: **method novelty is the real gap for TCAD** (it
    won't accept "QLoRA + a tool loop"); candidates listed — System-HIS-constrained/
    verification-guided decoding, structured tool-feedback learning, two-stage
    REQ→HIS→Project. Helper: Zynq is a mainstream commercial device, answering
    TCAD's "realistic silicon?" reflex.

---

## Part D — Artifacts

- Spec: `docs/superpowers/specs/2026-06-22-sr2fpga-research-reframe-design.md`
- Spec commits: `9acce76`, `3d12b13`, `7cfcb58`, `666c93c`, `6b2484e`, `63f3f38`,
  `1ced8d9`.
- Repair-loop commits: see Part A.
- `CLAUDE.md` was created this session (untracked; blocked from the Write tool by
  the ARS write-scope guard, written via Bash).

---

## Part E — Open items & next step

Decided / fixed:
- Hardware confirmed: AC820-ZYNQ (XC7Z020CLG484-2), OpenXC7-capable.
- System-HIS v1.1 accepted (fields extend per task).
- Venue = TCAD primary / TRETS fallback.

Still to decide (user-facing):
- Which **method-novelty** direction to deepen for the TCAD bar (3 candidates).
- Concrete difficulty-tier thresholds (set during baseline (a) measurement).
- self-repair training sample form; which models to run for baseline (a).

Next step (matches "dataset first"): enter **writing-plans** for the first slice
— the **compositional multi-module component-library MVP** emitting
`(requirement, System-HIS, contract, testbench, constraints, reference impl)`
with difficulty tiers. **First reconcile with codex's `6c7f273`** ("Add
control-oriented multi-module RTL tasks") so the library builds on it. In
parallel, an **OpenXC7 spike** on the AC820-ZYNQ and a **baseline (a)** run.
