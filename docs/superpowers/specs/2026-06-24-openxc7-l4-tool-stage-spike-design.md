# OpenXC7 L4 Tool-Stage Spike Design

## Status

Approved direction (2026-06-24). A de-risking spike to validate the open-source
OpenXC7 flow (Yosys `synth_xilinx` → nextpnr-xilinx → bitstream) on the
XC7Z020CLG484-2, so it can be **added as the L4 stage in the agent's
tool-verification pipeline** — producing batch, license-free, post-place-and-route
labels (real LUT/FF/BRAM/DSP + Fmax) for the dataset. Operationalizes the L4
toolchain decision in `2026-06-22-sr2fpga-research-reframe-design.md`.

## Why this matters

The tool pipeline currently stops at L3 (`agent._run_pipeline`:
lint → sim_compile → sim_run → synth, pass levels L0–L3). Two problems this spike
addresses:

1. **No L4 at scale.** Physical implementation (P&R timing + real utilization) is
   the TCAD core evidence, but Vivado cannot supply it in batch — license limits,
   GUI, minutes-per-run make thousands of parallel implementations infeasible.
   **OpenXC7 is open, license-free, scriptable, and parallelizable**, the only
   economical path to L4 labels across the dataset.
2. **The L3 QoR signal is vacuous (Finding G).** Generic Yosys synthesis emits
   gate-level cells, so measured `lut` is always 0
   (`docs/research-issues-training-data-quality-2026-06-24.md`). Post-P&R OpenXC7
   numbers are the **real** `measured_qor` (LUT/FF/BRAM/DSP + Fmax) that QOR_PRED
   and the L4 contribution need.

The end goal is therefore not a board demo but **wiring OpenXC7 in as the L4 tool
stage**, the same way Verilator/Icarus/Yosys are wired as L1–L3 stages.

## Environment

- **Spike host:** a Windows machine with **WSL2** (a *fresh* box, not the existing
  deploy machine; setting it up anew is acceptable). **Vivado is already installed**
  on it, and the AC820-ZYNQ board attaches there.
- **Toolchain (OpenXC7):** runs in **WSL2 (native Linux)** — the clean host for
  the Linux-first OpenXC7 / nextpnr-xilinx / prjxray stack (no macOS-native build,
  no Docker-USB headaches).
- **Vivado role:** **validation oracle** (Stage 2 trustworthiness comparison) and
  **one-off board loader** (Stage 4) — *not* the batch path and *not* a fallback
  to be relied on for scale.
- **Mac:** development/orchestration only; never touches the toolchain or board.
- **Authoring vs execution:** this spec and its plan are documents; **execution
  (install, run, board) happens on the Windows+WSL2 box** by the user or codex.

## Scope

Two paths, deliberately separated:

```
Automated batch path (the data generator — no board):
  Stage 1  Open flow headless: yosys synth_xilinx -> nextpnr-xilinx (XC7Z020 chipdb)
           -> fasm -> .bit, plus the post-P&R L4 report. Produces a .bit to prove
           the full chain; L4 labels come from the nextpnr report.
  Stage 2  Trustworthiness: same design through Vivado; compare utilization + Fmax.
  Stage 3  Batch readiness + pipeline integration: headless, parallel, deterministic,
           structured L4 output, wired in as the agent's L4 tool stage.

Manual sparse path (the L5 proof — NOT automated):
  Stage 4  One design with real AC820 pin constraints -> .bit -> load on board ->
           observe it runs. Proves req->bitstream->board end-to-end. One-off, manual.
```

### Stage 1 — open flow headless (no board)

- Flow: `yosys` (`synth_xilinx -part xc7z020clg484-2`) → `nextpnr-xilinx`
  (XC7Z020 chipdb) → `fasm` → `xc7frames2bit` → `.bit`.
- A clock-period constraint (XDC `create_clock`) is required so Fmax/slack are
  meaningful; **physical pin placement is NOT required** for L4 labels (it is only
  for Stage 4 board IO).
- **Highest risk — the first wall to hit:** availability of the
  **XC7Z020 prjxray chipdb** for nextpnr-xilinx. The reframe spec asserts the part
  is in OpenXC7's support list; Stage 1 verifies that concretely (prebuilt chipdb,
  or buildable). If the chipdb is unavailable/unbuildable, the open-L4-at-scale
  claim fails here — which is exactly what the spike exists to find out early.
- **Representative design:** a deterministic-generator artifact known to pass
  L0–L3 (e.g. `counter` or `composed_stream_accumulator`) — clean subject; the
  spike validates the toolchain, not the RTL.

### Stage 2 — trustworthiness vs Vivado (no board)

- Run the *same* design through Vivado (installed) → utilization + Fmax/WNS.
- **Judgement is correlation / same-order-of-magnitude / consistent ranking, NOT
  numeric identity** — the two tools use different P&R and timing models. Disagreement
  in absolute numbers is expected; the question is whether OpenXC7's labels are
  trustworthy enough to train on. This doubles as the spec's "OpenXC7-vs-Vivado"
  bonus comparison.

### Stage 3 — batch readiness + tool-pipeline integration (no board)

The integration target. OpenXC7 becomes a new stage in `agent._run_pipeline`:

- New stage `pnr` (or `impl`) after `synth`, run via `CommandRunner`, returning a
  `ToolResult` (missing tools → `missing_tool`, never a crash — same contract as
  L1–L3, so the dataset schema still works without OpenXC7 installed).
- A new report parser (sibling of `parse_yosys_stats`) extracts post-P&R
  **LUT/FF/BRAM/DSP + Fmax/slack** from nextpnr output into `measured_qor` —
  replacing the vacuous L3 `lut:0` with a real number (closes Finding G).
- `agent._labels` gains `l4_timing_pass` and pass level **L4**.
- Must be **headless, deterministic, and parallelizable**; Stage 3 success = run
  unattended on a handful of samples and emit parseable L4 labels.

### Stage 4 — sparse L5 board capstone (manual, not automated)

- For ONE design only: real AC820 pin XDC (clock pin, reset, a few LED outputs),
  confirm the **PL clock source** (independent PL oscillator vs PS-derived — if
  PS-derived, the pure-PL JTAG path is more involved; confirm on the board).
- Generate `.bit` via the OpenXC7 flow; **load via Vivado hardware manager**
  (lowest-risk, board drivers are Windows-native; Vivado programs any valid `.bit`
  regardless of generator). openFPGALoader (usbipd→WSL2 or Windows-native) is the
  all-open alternative, optional.
- Success = the design observably runs on the board (e.g. LED toggles at the
  expected rate). One-off; proves the full req→bitstream→board chain.

## Success criteria

- **Stage 1:** the open flow produces, headless, a `.bit` and a post-P&R report
  for the representative design on XC7Z020 — or a definitive finding that the
  chipdb/flow is unavailable (early de-risk either way).
- **Stage 2:** OpenXC7 utilization + Fmax are in a sane, consistent relationship
  to Vivado's on the same design (documented correlation/deltas).
- **Stage 3:** OpenXC7 runs as a headless, parallelizable L4 stage emitting
  parseable LUT/FF/BRAM/DSP + Fmax into `measured_qor`, demonstrated unattended on
  several samples; the vacuous-LUT issue is resolved.
- **Stage 4:** one OpenXC7-generated bitstream runs observably on the AC820 board.

## Out of scope (YAGNI)

- Automated/batched board loading (L5 stays manual and sparse).
- Zynq PS boot flow / FSBL / SD/QSPI (pure-PL JTAG only).
- AC820 pin constraints for the batch path (only Stage 4's one design needs them).
- Full runner wiring of the L4 stage into large baseline runs — that is a
  follow-on plan once the spike proves the stage works; the spike only needs to
  demonstrate the stage on a handful of samples.

## Risks and fallbacks

- **XC7Z020 chipdb unavailable/unbuildable (Stage 1):** the open-L4-at-scale claim
  is blocked; fallback is Vivado batch on a limited subset (smaller-scale L4) and a
  documented limitation. This is the single most important thing to learn early.
- **OpenXC7 P&R unreliable or far off Vivado (Stage 2):** if labels are not
  trustworthy, L4 labels are flagged provisional and the QoR contribution narrows;
  report honestly rather than overclaim.
- **PL clock is PS-derived (Stage 4):** board bring-up is more involved; Stage 4
  may need a minimal PS clock-enable, or use a board PL oscillator if present.

## Relationship to existing work

- Wires into `agent._run_pipeline` / `agent._labels` / `measured_qor` (the L1–L3
  pattern extends to L4) and adds a parser beside `log_parser.parse_yosys_stats`.
- Closes Finding G in `docs/research-issues-training-data-quality-2026-06-24.md`.
- Realizes the L4 toolchain in the reframe spec
  (`2026-06-22-sr2fpga-research-reframe-design.md`): "L4 timing closure uses
  OpenXC7 on the AC820-ZYNQ, Vivado as fallback/baseline, OpenXC7-vs-Vivado a bonus
  comparison."
