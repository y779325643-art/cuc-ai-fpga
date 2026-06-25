# SR2FPGA Guidance Docs Review - 2026-06-23

## Purpose

This is a confirmation draft for reorganizing the project's guidance documents.
It does not replace existing specs, plans, README files, or handoff notes yet.

The goal is to make the repository easier to pick up by separating:

- stable project direction;
- current engineering state;
- implementation history;
- operational commands;
- deployment/fine-tuning guidance;
- archived presentation/report work.

## Recommended Reading Order

For a new agent or collaborator, use this order:

1. `README.md`
   - Project entry point.
   - Explains SR2FPGA framing, current capability, runner usage, dataset layout,
     repository layout, tooling, and git hygiene.

2. `docs/research-objective-sr2fpga-tcad.md`
   - North-star research objective.
   - Defines what the project is and is not.
   - Should remain the highest-level research guidance.

3. `docs/sr2fpga-agent-handoff-2026-06-22.md`
   - Current work log and near-term handoff.
   - Should be cleaned so only the newest state is authoritative.

4. `CLAUDE.md`
   - Agent working instructions.
   - Should be updated to match the current active work rather than the older
     DeepSeek repair-loop state.

5. `LLM/README.md`
   - Operational guide for model deployment, fine-tuning, and SR2FPGA agent CLI
     usage.

6. Latest relevant spec and plan in `docs/superpowers/specs/` and
   `docs/superpowers/plans/`.
   - Read only the active or directly related slice.
   - Older plans should be treated as implementation history.

## Proposed Document Roles

### Stable Entry Documents

Keep and maintain:

- `README.md`
  - Public/project overview.
  - Should stay concise and current.
  - Avoid detailed commit history.

- `docs/research-objective-sr2fpga-tcad.md`
  - Research north star.
  - Should contain stable framing, target venues, evaluation levels, and what to
    avoid.
  - Should not carry short-term task lists except a compact "current mapping"
    section.

- `CLAUDE.md`
  - Agent instructions.
  - Should include invariants, commands, architecture map, and current active
    handoff pointer.
  - Should not claim an old active thread as current.

### Current Engineering State

Keep but rewrite/trim:

- `docs/sr2fpga-agent-handoff-2026-06-22.md`
  - Should become the single current handoff for the SR2FPGA data agent.
  - Recommended structure:
    - Current status as of 2026-06-23.
    - Current branch and uncommitted work.
    - Verification commands and latest passing counts.
    - Current capabilities.
    - Known issues and next work.
    - Dataset policy.
    - Historical notes moved lower or to an archive section.

Consider adding:

- `docs/current-status.md`
  - Short living status page with only the latest state.
  - This would prevent the handoff from accumulating contradictory history.

### Design Specs

Keep as historical design records:

- `docs/superpowers/specs/2026-06-18-sr2fpga-generation-boundary-design.md`
  - Stable and important. Defines generation/evaluation boundary.

- `docs/superpowers/specs/2026-06-18-sr2fpga-data-generation-agent-design.md`
  - Stable V1 agent architecture.

- `docs/superpowers/specs/2026-06-22-sr2fpga-llm-generation-entry-design.md`
  - Delivered slice: DeepSeek generation entry.

- `docs/superpowers/specs/2026-06-22-sr2fpga-deepseek-repair-loop-design.md`
  - Delivered slice: repair loop.

- `docs/superpowers/specs/2026-06-22-sr2fpga-multimodule-task-families-design.md`
  - Delivered slice: multi-module deterministic task families.

- `docs/superpowers/specs/2026-06-23-sr2fpga-autonomous-trajectory-runner-design.md`
  - Mostly delivered first runner shell.
  - Needs a status note pointing to the current failure-injector extension.

- `docs/superpowers/specs/2026-06-22-sr2fpga-research-reframe-design.md`
  - Important research rationale.
  - Should be referenced from the research objective, not duplicated in README.

Archive or separate from core SR2FPGA agent guidance:

- `docs/superpowers/specs/2026-06-04-hnai-fpga-project-overview-redesign-design.md`
  - Presentation deliverable, not active data-agent guidance.
  - Proposed location: keep in place but mark as "presentation/archive", or move
    later to `docs/archive/presentations/` if you want a cleaner docs tree.

### Implementation Plans

Keep as execution history, not current instructions:

- `docs/superpowers/plans/2026-06-18-sr2fpga-data-generation-agent.md`
- `docs/superpowers/plans/2026-06-22-sr2fpga-llm-generation-entry.md`
- `docs/superpowers/plans/2026-06-22-sr2fpga-deepseek-repair-loop.md`
- `docs/superpowers/plans/2026-06-22-sr2fpga-multimodule-task-families.md`
- `docs/superpowers/plans/2026-06-23-sr2fpga-autonomous-trajectory-runner.md`
- `docs/superpowers/plans/2026-06-08-llm-cloud-finetune-deploy.md`
- `docs/superpowers/plans/2026-06-04-hnai-fpga-project-overview-redesign.md`

Recommended treatment:

- Add a short `docs/superpowers/README.md` index.
- Mark plans as "historical implementation plan" unless explicitly active.
- Do not edit old step-by-step plans to match current code; instead add status
  notes in the index or handoff.

### Decision Logs

Keep:

- `docs/superpowers/decisions/2026-06-22-sr2fpga-reframe-decision-log.md`
  - Useful reasoning trail.
  - Should remain separate from the stable objective.

Recommended addition:

- `docs/superpowers/decisions/README.md`
  - One-line explanation of decision logs.

### Deployment And Training Docs

Keep:

- `LLM/README.md`
  - Cloud deployment, fine-tuning, and SR2FPGA agent operational guide.

- `LLM/DEPLOY.md`
  - Detailed Windows/WSL deployment runbook.

- `LLM/data/README.md`
  - Training data format and conversion instructions.

Recommended treatment:

- Root `README.md` should link to these but not duplicate deployment details.
- `LLM/README.md` can remain long because it is operational.

### Configs

Keep:

- `configs/sr2fpga_agent.example.yaml`
  - Safe runner example.
  - Should show all common fields, including `failure_injectors: []`.
  - Should not contain API keys or local absolute paths.

## Problems Found

### 1. Handoff Contains Conflicting Time Layers

`docs/sr2fpga-agent-handoff-2026-06-22.md` contains a newest 2026-06-23 update,
then older "Current Branch And Code State" content. Some older text says
dataset deletions should not be restored, but the workspace has since been
cleaned. This makes the file hard to trust.

Recommendation:

- Rewrite the top half as the current truth.
- Move old generated-data details into a "Historical run notes" section.
- Remove or clearly label obsolete warnings.

### 2. CLAUDE.md Active Thread Is Outdated

`CLAUDE.md` says the active thread is the DeepSeek repair loop. The actual work
has moved through runner integration and failure injection.

Recommendation:

- Replace that paragraph with:
  - "Check `docs/sr2fpga-agent-handoff-2026-06-22.md` for current active work."
  - Mention current active slice: autonomous runner hardening and failure
    injector coverage.

### 3. Specs And Plans Are Mixed With Presentation Work

The `2026-06-04-hnai-fpga-project-overview-redesign` spec/plan are useful
project deliverables but not core SR2FPGA data-agent guidance.

Recommendation:

- Leave files in place for now.
- In the new index, classify them as presentation/archive.

### 4. No Single Docs Index

Root README lists some important docs, but there is no dedicated map explaining
which specs/plans are current, historical, or archival.

Recommendation:

- Add `docs/README.md` or `docs/project-docs-index.md`.
  - If you prefer simple navigation, use `docs/README.md`.
  - If you prefer minimal disturbance, keep this draft as
    `docs/guidance-docs-review-2026-06-23.md` and later promote it.

### 5. Dataset Policy Is Repeated

README, CLAUDE, specs, and plans all mention dataset commit rules, sometimes
with different phrasing.

Recommendation:

- Keep one canonical policy in root `README.md` and `CLAUDE.md`.
- Other docs should say "see root README / CLAUDE.md for current git hygiene."

## Proposed Cleanup Actions

### Minimal Cleanup

No file moves.

1. Add a docs index.
2. Update `CLAUDE.md` active-thread paragraph.
3. Rewrite the first 80 lines of the handoff into current truth.
4. Add status labels to specs/plans through the index only.

Pros:

- Low risk.
- Preserves all existing paths.
- Easy to review.

Cons:

- `docs/superpowers/` remains a little crowded.

### Medium Cleanup

Keep paths, add indexes and status notes.

1. Do everything in Minimal Cleanup.
2. Add `docs/superpowers/README.md`.
3. Add `docs/superpowers/specs/README.md`.
4. Add `docs/superpowers/plans/README.md`.
5. Add a "Historical run notes" section to the handoff.

Pros:

- Best balance.
- Makes future navigation much clearer.
- No path-breaking moves.

Cons:

- Adds several index files.

### Larger Cleanup

Move archival presentation work and old completed plans.

1. Do Medium Cleanup.
2. Move presentation docs to `docs/archive/presentations/`.
3. Move completed plans to `docs/archive/plans/` or keep symlinks.

Pros:

- Cleanest tree.

Cons:

- Higher churn.
- Can break existing references in docs and commit history.

## Recommended Choice

Use Medium Cleanup.

It improves navigation without moving historical files, and it lets future
agents know which documents are current without rewriting every old plan.

## Confirmation Needed

Please confirm these choices before I apply the cleanup:

1. Should I create `docs/README.md` as the canonical docs index, or keep the
   index under a more explicit name like `docs/project-docs-index.md`?

2. Should `docs/sr2fpga-agent-handoff-2026-06-22.md` remain as the living
   handoff, or should I create a cleaner `docs/current-status.md` and leave the
   dated handoff as history?

3. Should presentation-related superpowers docs stay where they are and be
   labeled as archive, or should they be moved later?

4. Should root `README.md` stay broad and concise, with operational detail in
   `LLM/README.md`, or should the root README include more current task status?

## My Proposed Answers

1. Create `docs/README.md`.
2. Create `docs/current-status.md`, and keep the dated handoff as detailed
   history.
3. Do not move presentation docs now; label them in the index.
4. Keep root `README.md` broad and concise.
