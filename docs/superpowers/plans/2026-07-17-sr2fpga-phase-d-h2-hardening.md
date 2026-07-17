# SR2FPGA Phase D H2 Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Align H2 validation and REQ2HIS prompts with a strict canonical vocabulary, then quantify the effect on the 24 frozen Phase D pilot episodes.

**Architecture:** Keep H2 fail-closed. Add small canonicalization helpers in `his_validation.py`, expose the same vocabulary through prompt text, and add a read-only replay script that calls the production validator against copied in-memory project data. Frozen pilot artifacts are inputs only.

**Tech Stack:** Python standard library, `unittest`/`pytest`, SR2FPGA `GeneratedProject` and H-stage validator.

## Global Constraints

- Do not modify files under `datasets/sr2fpga_phase_d_v1/` or the frozen run root.
- Unknown semantic kinds, protocols, and scenario identifiers must remain H2 failures.
- Do not run model APIs.
- Every behavior change follows RED-GREEN TDD.

---

### Task 1: Strict H2 Canonicalization

**Files:**
- Modify: `LLM/tests/test_sr2fpga_agent_his_validation.py`
- Modify: `LLM/src/sr2fpga_agent/his_validation.py`

**Interfaces:**
- Consumes: `validate_system_his_h_stages(request, project)`
- Produces: H2 diagnostics based on canonical semantic kind, protocol, and scenario identifiers.

- [x] Add failing tests for canonical structured scenarios, unknown structured scenarios, reviewed aliases, and unknown aliases.
- [x] Run `python -m pytest LLM/tests/test_sr2fpga_agent_his_validation.py -q` and verify the new tests fail for the expected reasons.
- [x] Implement minimal fail-closed normalization helpers and alias maps.
- [x] Re-run the targeted test file and verify it passes.

### Task 2: Prompt Alignment

**Files:**
- Modify: `LLM/tests/test_sr2fpga_agent_prompts.py`
- Modify: `LLM/src/sr2fpga_agent/prompts.py`

**Interfaces:**
- Consumes: `_system_his_v12_messages()` and retry prompt construction.
- Produces: prompt text containing exact canonical H2 vocabularies and scenario format rules.

- [x] Add failing assertions for initial and retry prompt vocabulary guidance.
- [x] Run the prompt test file and verify the assertions fail before implementation.
- [x] Add one shared prompt guidance string derived from the H2 canonical sets.
- [x] Re-run prompt tests and verify they pass.

### Task 3: Frozen Pilot Replay And Report

**Files:**
- Create: `scripts/analyze_phase_d_h2_failures.py`
- Create: `LLM/tests/test_analyze_phase_d_h2_failures.py`
- Create: `docs/results/2026-07-17-sr2fpga-phase-d-failure-analysis-and-h2-hardening.md`

**Interfaces:**
- Consumes: frozen dataset root and existing trajectory/metadata/System-HIS artifacts.
- Produces: JSON analysis containing phase/source/family distributions and before/after H2 diagnostics without writing into the dataset root.

- [x] Add a failing test with a temporary miniature pilot dataset and expected aggregate output.
- [x] Verify the test fails because the analysis script is absent.
- [x] Implement the read-only analyzer using structured JSON parsing.
- [x] Run the analyzer on all 24 frozen episodes and save output outside the frozen dataset.
- [x] Write the result report with exact before/after counts and remaining failure classes.

### Task 4: Verification

**Files:**
- Verify all files changed above.

- [x] Run targeted H2, prompt, and analyzer tests.
- [x] Run `python -m pytest LLM/tests -q`.
- [x] Run `git diff --check`.
- [x] Verify frozen pilot tracked/untracked artifact hashes were not changed by checking `git status` and analyzer behavior.
