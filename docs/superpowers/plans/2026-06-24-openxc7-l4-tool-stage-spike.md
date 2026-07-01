# OpenXC7 L4 Tool-Stage Spike Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> **Authoring note:** Written by the planning session; **executed by the user / codex on the Windows+WSL2 box** (the Mac cannot run OpenXC7 or touch the board). This is a *spike*: Tasks 1, 2, 4, 5 are toolchain/hardware **runbook** steps with explicit go/no-go gates — not TDD — and several values (exact OpenXC7 install steps, the XC7Z020 chipdb source, the precise nextpnr report format) are **discoveries the spike must resolve and record**, not pre-known. Task 3 is the **code** integration (parser + L4 stage), which IS TDD and is implementable/testable on any machine with canned fixtures.

**Goal:** Validate the open-source OpenXC7 flow on XC7Z020 and add it as the L4 stage of the agent tool pipeline, producing batch, license-free, post-P&R labels (real LUT/FF/BRAM/DSP + Fmax).

**Architecture:** A headless WSL2 OpenXC7 flow (Yosys `synth_xilinx` → nextpnr-xilinx → fasm → `.bit`) is wrapped by a single script; a new parser turns its report into `measured_qor`; a new `pnr` stage in the current runner/local-tool pipeline runs the wrapper via the existing `CommandRunner`-style tool contract (degrading to `missing_tool` where OpenXC7 is absent) and yields pass level L4. Vivado (already installed) is the trustworthiness oracle and the one-off board loader.

**Status note (2026-06-30):** This plan was written before the current runner/local-tool architecture settled. Treat any remaining `agent.py` / `_run_pipeline` references below as historical placeholders to remap during implementation, not as the authoritative integration target.

**Tech Stack:** WSL2 (Ubuntu) + OpenXC7 (Yosys/nextpnr-xilinx/prjxray); Python 3 stdlib + `unittest` for the parser/stage; Vivado (Windows) for comparison and board loading.

**Source spec:** `docs/superpowers/specs/2026-06-24-openxc7-l4-tool-stage-spike-design.md`

## Global Constraints

- Spike host = Windows + **WSL2**; OpenXC7 runs in WSL2; Vivado on Windows is oracle + loader; the Mac never runs OpenXC7 or touches the board.
- Run Python from the repo root; absolute imports `from LLM.src.sr2fpga_agent...`; tests via `python3 -m unittest discover -s LLM/tests -q`.
- The L4 stage MUST degrade to `status="missing_tool"` when OpenXC7 is absent (the existing `CommandRunner` contract) — same as L1–L3, so the agent still runs on machines without it.
- `predicted_qor` stays model-only; the OpenXC7 numbers go only into `measured_qor`.
- LF line endings; never commit `.env`, keys, bitstreams, or large run artifacts. Commit small captured report fixtures only.
- Batch path needs NO board/pin constraints; only Task 4 (L5) uses AC820 pins.
- Representative design: a deterministic-generator artifact known to pass L0–L3 (default `counter`; `matrix_vector_mac` if a DSP-bearing QoR signal is wanted — decide in Task 1).

## File structure (code, Task 3)

- Create `LLM/src/sr2fpga_agent/openxc7_report.py` — parse nextpnr-xilinx report/log → `{lut, ff, bram, dsp, fmax_mhz, wns_ns}` (sibling of `log_parser.parse_yosys_stats`).
- Create `scripts/openxc7_pnr.sh` — headless flow wrapper invoked by the `pnr` stage; defined contract below.
- Modify the current runner/local-tool pipeline — add `pnr` stage after `synth`; merge the pnr report into measured QoR; add `l4_timing_pass` + pass level `L4` in the current label builder. Re-check the exact files before implementation instead of assuming the older `LLM/src/sr2fpga_agent/agent.py` entry point.
- Test `LLM/tests/test_sr2fpga_agent_openxc7_report.py`; extend an agent pipeline test for the L4 stage + missing_tool degradation.

---

### Task 1: WSL2 OpenXC7 bring-up + one design headless (Stage 1) — RUNBOOK, go/no-go

**Nature:** toolchain discovery on WSL2. **This is the spike's most important de-risk: does an XC7Z020 chipdb exist/build?** Resolve and record; do not assume.

**Deliverable:** a documented working command sequence + a captured nextpnr report committed as a parser fixture.

- [ ] **Step 1: Install OpenXC7 in WSL2.** Install Yosys, nextpnr-xilinx, and prjxray (via the OpenXC7 distribution — prebuilt release, Nix, or Docker-in-WSL2; **record which method actually worked**). Confirm `yosys -V`, `nextpnr-xilinx --version` run.

- [ ] **Step 2: Acquire the XC7Z020CLG484-2 chipdb (THE risk gate).** Obtain or build the prjxray chipdb / nextpnr-xilinx `.bin` for `xc7z020`. Record the exact source/command.
  - **GO:** chipdb obtained → continue.
  - **NO-GO:** chipdb unavailable and not buildable → **stop the open-L4-at-scale path here**, record the finding in `docs/current-status.md`, and fall back to Vivado-batch-on-a-subset (a separate, smaller-scale plan). This early stop is a successful spike outcome, not a failure.

- [ ] **Step 3: Generate the representative design.** From the repo root (on WSL2), produce one deterministic sample:
  ```bash
  python3 -m LLM.src.sr2fpga_agent.cli --dataset-root /tmp/openxc7_spike \
    --sample-id spike_counter --task-type counter --width 8 --project-name counter_8bit
  ```
  Collect the RTL sources from `/tmp/openxc7_spike/spike_counter/final/generated_project/rtl/`.

- [ ] **Step 4: Run the open flow headless and capture the report.** Confirm the exact working invocation (flags are part of the discovery) and record it. Expected shape:
  ```bash
  yosys -p "synth_xilinx -flatten -part xc7z020clg484-2; write_json design.json" rtl/*.v
  nextpnr-xilinx --chipdb xc7z020.bin --xdc clock_only.xdc \
    --json design.json --fasm design.fasm --report report.json --freq 100
  # then fasm -> frames -> .bit (prjxray fasm2frames + xc7frames2bit, or the openXC7 bit step)
  ```
  Use a clock-only XDC (`create_clock -period 10.0 [get_ports clk]`) — **no pin placement** (L4 labels don't need it).
  - **GO:** a `.bit` is produced AND `report.json` + the nextpnr log contain utilization (LUT/FF/BRAM/DSP) and a max-frequency/slack number.
  - **NO-GO:** flow breaks → record the failing stage and error; that is the de-risk finding.

- [ ] **Step 5: Commit the captured report as a fixture.** Save the real `report.json` (and the relevant Fmax log lines) to `LLM/tests/fixtures/openxc7_counter_report.json` — this becomes the authoritative parser fixture for Task 3.
  ```bash
  git add LLM/tests/fixtures/openxc7_counter_report.json
  git commit -m "Capture real OpenXC7 nextpnr report fixture for XC7Z020 counter"
  ```

- [ ] **Step 6: Record the working runbook** (install method, chipdb source, exact commands) in `docs/current-status.md` under an "OpenXC7 spike" note.

---

### Task 2: Vivado trustworthiness comparison (Stage 2) — RUNBOOK

**Nature:** comparison on Windows Vivado. **Deliverable:** a recorded utilization + Fmax comparison.

- [ ] **Step 1: Run the same design through Vivado** (synth + implementation) on Windows; capture post-implementation utilization (LUT/FF/BRAM/DSP) and the timing summary (Fmax/WNS).

- [ ] **Step 2: Tabulate OpenXC7 vs Vivado** for the same design: LUT, FF, BRAM, DSP, Fmax, WNS.

- [ ] **Step 3: Judge trustworthiness — correlation, NOT identity.** Document deltas and whether the numbers are same-order-of-magnitude and directionally consistent. Record the conclusion in the current-status OpenXC7 note.
  - **GO:** numbers are sane/consistent → OpenXC7 labels are trustworthy enough to train on.
  - **CAUTION:** large/unexplained divergence → flag L4 labels provisional; narrow the QoR claim; report honestly.

---

### Task 3: OpenXC7 report parser + L4 pipeline stage (Stage 3) — TDD, code

**Files:**
- Create: `LLM/src/sr2fpga_agent/openxc7_report.py`
- Create: `scripts/openxc7_pnr.sh`
- Modify: `LLM/src/sr2fpga_agent/agent.py`
- Test: `LLM/tests/test_sr2fpga_agent_openxc7_report.py`

**Interfaces:**
- Produces: `parse_openxc7_report(report_text: str) -> dict` with keys `lut, ff, bram, dsp` (ints) and `fmax_mhz, wns_ns` (floats or `None`).
- Produces: `scripts/openxc7_pnr.sh <project_dir> <part> <clock_period_ns>` → runs the headless flow, writes `<project_dir>/eval/openxc7_report.json`, exits 0 on success.
- Consumes (agent): the existing `CommandRunner.run(...)` and `_measured_qor`/`_labels` patterns.

- [ ] **Step 1: Write the failing parser test** (fixture from Task 1, Step 5; if Task 1 is not yet run, use the realistic sample below and replace it with the captured fixture once available):

```python
# test_sr2fpga_agent_openxc7_report.py
from LLM.src.sr2fpga_agent.openxc7_report import parse_openxc7_report

SAMPLE = '''
Info: Device utilisation:
Info:            SLICE_LUTX:    42/53200    0%
Info:            SLICE_FFX:     31/106400   0%
Info:               RAMB36:      0/140      0%
Info:               DSP48E1:     2/220      0%
Info: Max frequency for clock 'clk': 142.31 MHz (PASS at 100.00 MHz)
'''

def test_parse_openxc7_report_extracts_utilization_and_fmax():
    r = parse_openxc7_report(SAMPLE)
    assert r["lut"] == 42
    assert r["ff"] == 31
    assert r["bram"] == 0
    assert r["dsp"] == 2
    assert abs(r["fmax_mhz"] - 142.31) < 0.01

def test_parse_openxc7_report_missing_fmax_is_none():
    r = parse_openxc7_report("Info: Device utilisation:\nInfo: SLICE_LUTX: 5/53200 0%\n")
    assert r["lut"] == 5
    assert r["fmax_mhz"] is None
```

- [ ] **Step 2: Run to verify it fails** — `python3 -m unittest LLM.tests.test_sr2fpga_agent_openxc7_report -q` → FAIL (module not found).

- [ ] **Step 3: Implement `parse_openxc7_report`** — regex-extract the utilisation lines (map `LUT`→lut, `FF`→ff, `RAMB`→bram, `DSP`→dsp, taking the used count before `/`) and the "Max frequency for clock" line (→ `fmax_mhz`); compute `wns_ns` if a slack line is present, else `None`. Match the resilient style of `log_parser.parse_yosys_stats`. **Adjust the regexes to the real fixture captured in Task 1 — the sample above is the expected shape, not authoritative.**

- [ ] **Step 4: Run to verify it passes.**

- [ ] **Step 5: Write the flow wrapper `scripts/openxc7_pnr.sh`** to the contract in Interfaces, using the exact working commands recorded in Task 1. It must be headless, deterministic, exit non-zero on any sub-step failure, and write `eval/openxc7_report.json`. (Executable on WSL2; on the Mac it simply won't be invoked because the tools are absent — see Step 7.)

- [ ] **Step 6: Write the failing agent L4-stage test** (testable on any machine — no OpenXC7 needed):

```python
def test_pipeline_records_l4_missing_tool_when_openxc7_absent(tmp_path):
    # synth passes (Yosys present or stubbed), pnr stage runs the wrapper which is absent -> missing_tool
    results = run_pipeline_through_synth_then_pnr(project_dir)  # helper builds a synth-passing project
    assert results["pnr"].status == "missing_tool"
    labels = _labels(results, final_attempt_id=0, failure_count=0)
    assert labels["checks"]["l4_timing_pass"] is False
    # L3 still reported; absence of L4 must not crash or regress L0-L3
    assert labels["pass_level"] in {"L3", "L0", "L1", "L2"}

def test_pipeline_records_l4_when_pnr_passes(monkeypatch):
    # stub CommandRunner so the pnr stage "passes" and an openxc7_report.json is present
    labels = _labels(results_with_passing_pnr, final_attempt_id=0, failure_count=0)
    assert labels["checks"]["l4_timing_pass"] is True
    assert labels["pass_level"] == "L4"
```

- [ ] **Step 7: Implement the `pnr` stage in `agent.py`** — after `synth` passes, run `scripts/openxc7_pnr.sh` via `CommandRunner` as stage `pnr`; on `passed`, read `eval/openxc7_report.json`, parse with `parse_openxc7_report`, merge real LUT/FF/BRAM/DSP + Fmax into `_measured_qor` (overriding the vacuous Yosys `lut`); add `l4_timing_pass` to `_labels` and pass level `L4` when synth+pnr pass. `missing_tool`/`failed` → no L4, L3 unchanged. Preserve the short-circuit contract.

- [ ] **Step 8: Run full suite** — `python3 -m unittest discover -s LLM/tests -q` → all pass (on the Mac too: the missing_tool path is what runs there).

- [ ] **Step 9: Commit** — `git add LLM/src/sr2fpga_agent/openxc7_report.py scripts/openxc7_pnr.sh LLM/src/sr2fpga_agent/agent.py LLM/tests/test_sr2fpga_agent_openxc7_report.py && git commit -m "Add OpenXC7 L4 pnr stage + report parser to the tool pipeline"`

---

### Task 4: Batch demonstration of the L4 stage (Stage 3 cont.) — RUNBOOK, on WSL2

**Deliverable:** the L4 stage runs unattended on several samples, emitting parseable L4 labels.

- [ ] **Step 1: Generate a handful of deterministic samples** (e.g. 4–8 across task families) on WSL2.
- [ ] **Step 2: Run the agent/runner over them with OpenXC7 present**, confirming each reaches pass level `L4` (or records a real pnr `failed`/timing miss — both are valid labels).
- [ ] **Step 3: Verify the exports** — `project_to_measured_qor.jsonl` rows now carry real LUT/FF/BRAM/DSP + Fmax (Finding G closed). Record counts and a sample row in the current-status OpenXC7 note.
  - **GO:** unattended run produces parseable L4 labels at small batch → Stage 3 ratified.

---

### Task 5: Manual sparse L5 board capstone (Stage 4) — RUNBOOK, one-off

**Nature:** manual, not automated. **Deliverable:** one OpenXC7-generated bitstream observably running on the AC820.

- [ ] **Step 1: Get the AC820 pin map** (clock pin, reset, ≥1 LED) from the 小梅哥 schematic/board files; write a real XDC with those pin assignments for one observable design (e.g. a blinker/counter driving an LED).
- [ ] **Step 2: Confirm the PL clock source** — independent PL oscillator vs PS-derived. If PS-derived, note the extra bring-up needed (minimal PS clock enable) before pure-PL loading.
- [ ] **Step 3: Generate the `.bit`** via the OpenXC7 flow (Task 3 wrapper, with the real-pin XDC).
- [ ] **Step 4: Load via Vivado hardware manager** over JTAG (lowest-risk; programs any valid `.bit`). openFPGALoader is the optional all-open alternative.
- [ ] **Step 5: Observe** the design runs (LED toggles at the expected rate). Record the result (and a photo/log) in the current-status OpenXC7 note. This proves req→bitstream→board end-to-end.

---

## Self-review

**Spec coverage:** Stage 1 → Task 1 ✓ (with chipdb go/no-go); Stage 2 → Task 2 ✓; Stage 3 (parser + L4 stage + batch) → Tasks 3, 4 ✓ (closes Finding G via Step 7/Task 4 Step 3); Stage 4 L5 board → Task 5 ✓; missing_tool degradation → Task 3 Step 6/7 ✓; division of labor (WSL2 vs Mac) → Global Constraints + Task 3 testability ✓; Vivado as oracle+loader → Tasks 2, 5 ✓; out-of-scope (PS boot, automated L5, pins in batch) respected ✓.

**Placeholder scan:** Toolchain "discoveries" (install method, chipdb source, exact nextpnr flags, real report format) are explicitly labeled as spike findings to record, not lazy placeholders — that is the spike's purpose. The parser test ships a concrete realistic fixture and instructs replacing it with Task 1's captured real report. No TODO/TBD in the code task.

**Type consistency:** `parse_openxc7_report(report_text) -> {lut, ff, bram, dsp, fmax_mhz, wns_ns}` used consistently in Tasks 3–4; `scripts/openxc7_pnr.sh <project_dir> <part> <clock_period_ns>` and its `eval/openxc7_report.json` output used consistently; `l4_timing_pass` + pass level `L4` consistent in Task 3 Steps 6–7.

## Reconciliation note for codex

Task 3 touches the active runner/local-tool pipeline, measured-QoR merge path, and label builder. The older `agent.py` (`_run_pipeline`/`_measured_qor`/`_labels`) names are retained only as historical hints from the first draft. Coordinate with the System-HIS v1.2 freeze changes before wiring L4. The parser (`openxc7_report.py`) and wrapper (`scripts/openxc7_pnr.sh`) are new files with no collision.
