# AGENTS.md

SR2FPGA turns natural-language hardware requirements into coherent multi-file FPGA projects and evaluates them using tool-execution artifacts as evidence. This file guides repository development agents. It does not replace the research specification.

**Default: complete the authorized task end to end — code, tests, docs, validation — and report what you actually ran. Proceed without asking unless an action is irreversible, outward-facing, or changes what the research counts as evidence.**

## Start

- Check `git status`, the branch, and [WORKTREE.md](WORKTREE.md) before editing. The local `develop` worktree is the active Paper-1 checkout. See the [route index](docs/routes/README.md) for the current entry point and historical records.
- Locate files and owners through the [documentation index](docs/README.md); find commands in the owning README or the [current command reference](docs/current-status.md#current-commands). Read only what can change the current decision.
- Research semantics: [paper1-v2.3 amendment](docs/specs/2026-10-28-sr2fpga-paper1-llm-case-amendment-v2.3.zh.md) with the [v2.2 base plan](docs/specs/2026-09-15-sr2fpga-paper1-research-plan-v2.2.zh.md). Chinese-authoritative, **not frozen**; implementation and local development validation are authorized, official experiments are not. Skip this unless the task touches research meaning, metrics, or evidence.

## Layout

| Path | Purpose |
| --- | --- |
| `agent/` | Generation, validation, evaluation, repair, trajectories |
| `training/` | Dataset conversion, training, merge, serving outside Paper-1; Training does not import Agent |
| `contracts/` | Registered exchange formats and `manifest.json` |
| `datasets/` | Immutable versioned releases |
| `artifacts/` | Ignored runtime and candidate output |
| `reports/`, `docs/` | Curated evidence; current guidance and research definitions |
| `app/`, `outputs/`, `references/` | Demo and reference surfaces, not research authority |

Projects exchange versioned files through contracts, never runtime imports.

## Validate

| Change | Run |
| --- | --- |
| `agent/src/**` | `agent/tests` |
| `contracts/**` | `contracts/tests`; keep `manifest.json` in sync |
| `training/**` | `training/tests` and `python -m ruff check training/src training/tests` |
| Core docs or project READMEs | `compatibility_tests` |
| Cross-module, public interface, runtime behavior | full surface: `contracts/tests agent/tests training/tests compatibility_tests` |

- Make the smallest complete change that solves the problem; reuse existing patterns and tests.
- `pytest.ini` has no `testpaths` — always pass explicit paths.
- Real HDL tests need `SR2FPGA_OSS_CAD_SUITE_ROOT=<oss-cad-suite root>`; see `agent/src/sr2fpga_agent/local_tools.py`.
- Prefer existing tests. Add one narrow test only for behavior a contract defines and no test covers.
- Report the command and its result; state anything you did not run.

## Hold these lines

- Candidate outputs and repair patches may change only candidate files — not trusted testbenches, hidden cases, golden models, scoring, or evaluator-private material. Fixing RTL never authorizes weakening its oracle.
- Candidate and runtime output goes under `artifacts/`. Promotion into `datasets/` or `reports/evidence/` is a separate authorized operation; never overwrite historical runs.
- Never commit credentials, local absolute paths, model weights, hidden evaluation content, or unrelated caches.
- Preserve uncommitted user work — no reset, clean, restore, stash, or overwrite. Local commits on a task branch are fine; push, PR, shared-branch merge, deploy, paid model runs, heavy training, and official experiments only when requested with a scope.

## Finish

Scope complete; matching tests run and reported; docs, links, and contracts you touched validate; no secret or unrelated change; external side effects inside authorization. Reply to the user in Chinese.
