# SR2FPGA Repository Reorganization Implementation Roadmap

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Reorganize SR2FPGA into independent `agent/` and `training/` subprojects while preserving contracts, datasets, verification behavior, compatibility, and recoverability.

**Architecture:** Execute five ordered plans. First create and validate an external backup of the dirty main worktree, then establish shared contracts and artifact policy, migrate the agent, migrate training, and finally cut over documentation and compatibility entrypoints. Each plan ends with an independently reviewable commit and a stop gate.

**Tech Stack:** Git worktrees, PowerShell 7, Python 3.11+, pytest, setuptools `pyproject.toml` packages, JSON/JSONL, YAML, Verilator, Icarus Verilog, Yosys, optional OpenXC7/nextpnr.

## Global Constraints

- Baseline implementation commit: `origin/develop@54e2560c`.
- The approved design is `docs/superpowers/specs/2026-07-17-sr2fpga-repository-reorganization-design.md`.
- Keep one Git repository with two executable top-level subprojects: `agent/` and `training/`.
- `contracts/` stores shared schemas and fixtures; it is not a third executable application.
- Keep one compatibility cycle for documented `LLM/` commands.
- Back up and verify the dirty main worktree before any cleanup.
- Do not modify hidden tests, golden models, trusted checkers, or accepted verdict semantics to make migration tests pass.
- `training/` must not import `sr2fpga_agent` implementation modules.
- `agent/` must not depend on `torch`, `transformers`, `datasets`, `peft`, `trl`, `vllm`, or `bitsandbytes`.
- `REQ2FILE` remains a derived training view without standalone project pass credit.
- `not_run` remains distinct from `fail`; tool-environment failures remain distinct from model failures.
- Line B keeps L0-L3 as the default; L4 remains policy-controlled.
- Runtime output defaults to ignored `artifacts/` paths.
- Old dated plans and specifications retain their historical commands and paths.
- No API key, `.env` content, private absolute path, checkpoint, bitstream, DCP, or vendor-restricted raw artifact may enter a commit.
- Stop at the first failed gate. Do not continue to the next plan with a red test suite.
- Use `git mv` for tracked path changes so history remains attributable.
- Every commit must leave its implementation worktree clean.

---

## Plan Suite

Execute these documents in order:

| Order | Plan | Primary deliverable | Exit gate |
|---:|---|---|---|
| 1 | `2026-07-17-sr2fpga-reorganization-phase-a-workspace-recovery.md` | Validated external backup and clean main checkout | Main `develop` clean and equal to `origin/develop` |
| 2 | `2026-07-17-sr2fpga-reorganization-phase-b1-contracts-and-artifacts.md` | Contract registry, dataset metadata, artifact policy | Contract and dataset-policy tests pass |
| 3 | `2026-07-17-sr2fpga-reorganization-phase-b2-agent-project.md` | Installable lightweight `sr2fpga_agent` project | Agent suite and deterministic smoke pass |
| 4 | `2026-07-17-sr2fpga-reorganization-phase-b3-training-project.md` | Independent `sr2fpga_training` project | Training suite and data dry-run pass |
| 5 | `2026-07-17-sr2fpga-reorganization-phase-b4-compatibility-cutover-cleanup.md` | Compatibility wrappers, active docs, evidence relocation, final audit | Full suite, compatibility suite, and hygiene audit pass |

## Repository Map Locked by This Plan

```text
cuc-ai-fpga/
  agent/
    pyproject.toml
    README.md
    src/sr2fpga_agent/
    tests/
    configs/{current,archive,legacy,local}/
    scripts/
  training/
    pyproject.toml
    README.md
    src/sr2fpga_training/
    tests/
    tests/fixtures/
    configs/
    scripts/
  contracts/
    README.md
    manifest.json
    system-his/
    trajectory/
    training-views/
    task-catalog/
    tests/
  datasets/
    README.md
    manifest.json
    manifests/
  artifacts/                  # ignored
  compatibility_tests/
  LLM/                        # one-cycle forwarding layer
```

## Cross-Plan Interfaces

The plans use these stable interfaces:

- Agent import root: `sr2fpga_agent`.
- Training import root: `sr2fpga_training`.
- Agent runner: `python -m sr2fpga_agent.runner`.
- Agent REQ2FILE evaluator: `python -m sr2fpga_agent.req2file_eval`.
- Training converter: `python -m sr2fpga_training.prepare_dataset`.
- Training dry run: `python -m sr2fpga_training.training_dry_run`.
- Canonical catalog: `contracts/task-catalog/sr2fpga-task-catalog-v0.2.json`.
- Contract registry: `contracts/manifest.json`.
- Mutable agent output root: `artifacts/agent/`.
- Mutable training output root: `artifacts/training/`.
- Frozen releases remain under `datasets/`.
- Compatibility warning helper: `LLM.src._compat.warn_replacement(old_command, new_command)`.

## Global Verification Commands

Run these from the repository root after Plan 5:

```powershell
python -m pytest agent/tests
python -m pytest training/tests
python -m pytest contracts/tests
python -m pytest compatibility_tests
python -m pytest
python -m sr2fpga_agent.runner --help
python -m sr2fpga_training.prepare_dataset --help
python -m sr2fpga_training.training_dry_run --help
```

Run the deterministic preflight with the new path:

```powershell
python -m sr2fpga_agent.runner `
  --config agent/configs/current/sr2fpga_deterministic_curriculum_smoke.example.yaml `
  --run-id repository-reorganization-preflight `
  --preflight
```

Expected conditions:

- all pytest commands exit 0;
- the full suite has no fewer tests than the `905 passed, 349 subtests passed` baseline unless a test is explicitly replaced by an equivalent boundary or compatibility test;
- preflight exits 0;
- `git status --short` is empty;
- `git grep -n "from LLM.src.sr2fpga_agent" -- agent training` returns no matches;
- `git grep -n "import sr2fpga_agent" -- training` returns no matches;
- `git ls-files -- tmp` returns no paths;
- `git check-ignore artifacts/agent/runs/probe.json` reports the probe path as ignored;
- no active command in `README.md`, `CLAUDE.md`, `docs/README.md`, or `docs/current-status.md` uses the old entrypoint without labeling it as compatibility syntax.

## Design Acceptance Traceability

| Approved-design requirement | Owning plan and gate |
|---|---|
| Verified backup before cleanup | Phase A Tasks 1-5 and Phase A Exit Criteria |
| Independent Agent and Training projects | Phase B2 and Phase B3 exit criteria |
| No duplicate business logic under LLM | Phase B4 Tasks 1-2 compatibility AST tests |
| Enforced dependency direction | Phase B2 boundary tests and Phase B3 Task 6 |
| One-cycle old command/import compatibility | Phase B4 Tasks 1-2 |
| Versioned shared contracts | Phase B1 Tasks 2-4 and Task 6 fixtures |
| Frozen dataset readability and auditability | Phase B1 Task 5 and Phase B4 Task 5 revalidation |
| Runtime output under ignored artifacts | Phase B1 Task 1, Phase B2 Task 5, Phase B3 Task 3 |
| Baseline test coverage preserved | Every phase stop gate and Phase B4 Task 5 |
| Focused project suites pass | Phase B1-B4 exit criteria |
| Deterministic generation/verification smoke passes | Phase B2 Task 6 and Phase B4 Task 5 |
| Documented old commands forward | Phase B4 Tasks 1-2 compatibility matrix |
| Root and subproject documentation updated | Phase B4 Task 3 |
| No secrets, private paths, or restricted raw artifacts | Phase B3 Task 3 and Phase B4 Task 5 scans |
| Clean reviewed branch ready for publication | Phase B4 Task 6 |
## Stop Conditions

Stop execution and report the evidence when any condition occurs:

1. backup file counts or SHA256 values disagree;
2. the clean baseline suite does not reproduce;
3. an existing frozen dataset file changes content unexpectedly;
4. a migration stage changes H0-H3 or L0-L5 semantics;
5. training imports agent implementation;
6. agent acquires a heavy training dependency;
7. a trusted oracle file is changed solely to recover a passing test;
8. a compatibility wrapper contains business logic instead of delegation;
9. an evidence path is removed without either a repository relocation or a verified external-backup record;
10. the implementation worktree contains unrelated changes.

## Execution Tracking

- [ ] Phase A backup and recovery completed and audited.
- [ ] Phase B1 contracts and artifact policy completed.
- [ ] Phase B2 agent migration completed.
- [ ] Phase B3 training migration completed.
- [ ] Phase B4 compatibility and cutover completed.
- [ ] Full verification evidence recorded.
- [ ] Branch reviewed, pushed, and ready for merge.


## Roadmap Completion Criteria

The roadmap is complete only when all phase exit criteria pass, no original test assertion is silently lost, canonical Agent and Training commands work, documented legacy commands forward with deprecation messages, datasets remain immutable, tracked tmp content is retired through the audited backup gate, the final verification report says APPROVED, and the reviewed branch is ready for explicitly approved publication.
