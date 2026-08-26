# AGENTS.md

This is the repository-wide operating guide for SR2FPGA coding and research
work. A more specific nested `AGENTS.md` may override it for that subtree.

## Purpose And Scope

SR2FPGA turns natural-language hardware requirements into coherent multi-file
FPGA projects and evaluates them with artifact-backed evidence. This file tells
agents how to work in the repository; it does not duplicate the research plan.

Research gates, evaluation authority, method definitions, and claim permissions
follow the active
[Paper-1 freeze](docs/specs/2026-08-14-sr2fpga-paper1-research-program-freeze-design.md).
Mutable implementation status follows [`docs/current-status.md`](docs/current-status.md)
and the relevant
[code-architecture section](docs/specs/2026-08-18-sr2fpga-paper1-code-architecture-development-spec.md).

## Task Routing

Before substantial work:

1. Inspect the working tree and preserve unrelated or untracked user changes.
2. Locate the task-local implementation, contracts, tests, artifacts, and
   owning README.
3. Read additional authority only when the task needs it:
   - current capability, debt, gates, or result claims: `docs/current-status.md`;
   - research semantics, metrics, information boundaries, or official
     evaluation: the active Paper-1 freeze;
   - Paper-1 implementation or evaluator architecture: the relevant section of
     the code-architecture spec;
   - navigation or evidence location: [`docs/README.md`](docs/README.md).

Do not preload the full research plan for ordinary `app/`, documentation,
Training compatibility, or local bug-fix work. Historical plans and commands are
provenance, not current instructions.

## Authority And Project Ownership

When sources disagree about current behavior, use this order:

1. registered contracts, current code, and reproducible tests;
2. artifact-backed evidence in the task ledger and curated reports;
3. `docs/current-status.md` and current project READMEs;
4. the active research freeze and implementation specs;
5. historical reports as bounded context only.

A contract, catalog row, plan, or specification is not empirical verification.

- `agent/` owns generation, validation, evaluation, repair, and trajectories.
- `training/` owns retained dataset conversion, training, merge, and serving
  infrastructure outside Paper-1. Training does not import Agent.
- `contracts/` defines stable exchange formats; `datasets/` contains immutable
  versioned releases; `artifacts/` contains ignored runtime output.
- `reports/` contains curated evidence; `docs/` contains current guidance and
  research definitions; `references/` is informative but non-authoritative.
- `app/` and `outputs/` are local demo/reference surfaces, not research evidence.

Projects exchange versioned files through `contracts/` and `datasets/`, not
runtime imports across project boundaries.

## Working Agreements

- State material assumptions and a verifiable success condition. If ambiguity
  would materially change the result or scope, surface it instead of guessing.
- Prefer the simplest solution that satisfies the request. Add no speculative
  feature, abstraction, configurability, or unrelated cleanup.
- Make surgical changes. Match existing style and remove only the orphaned code
  created by the current change.
- For behavior changes, add or update the narrowest regression that would fail
  before the change and pass afterward.
- Run focused validation first, then broaden it in proportion to risk. Separate
  assertion failures from timeout, dependency, and infrastructure failures.
- Report what changed, what was verified, and what remains blocked. Do not turn
  intended behavior or a local smoke into a result claim.

## Autonomy, Authorization, And Git

Proceed without asking again for requested, in-scope local reading, editing,
focused tests, reversible validation, and non-destructive Git. A review,
explanation, diagnosis, or plan does not authorize unrelated implementation.

Local Git is authorized for in-scope work: inspect history, create or switch a
safe task branch, stage only task changes, and create local commits when useful.
Local commits are permitted, not mandatory.

Never discard or overwrite unrelated work. Destructive reset, clean,
checkout-overwrite, ref deletion, or history rewriting requires an explicit
request and a verified recovery path. Push, force-push, publish, release, open a
PR, merge into a shared branch, or otherwise change remote state only when
explicitly requested.

Also require an explicit request before paid or large model runs, heavy
training, outcome-producing campaigns, controlled evidence or dataset
promotion, official held-out evaluation, deployment, or other material external
state changes.
If the user's request already names the action and scope, do not ask for a
second confirmation unless the target is ambiguous or consequences exceed it.

## Candidate And Evaluator Boundary

- Candidate-model outputs and generated repair patches must not modify trusted
  testbenches, hidden cases, golden models, scoring code, board shells,
  constraints, or evaluator-private material.
- A coding Agent may maintain trusted/evaluator implementation when the user's
  task explicitly targets it. State the intended files, reason, research impact,
  and validation plan before editing, then remain within that scope.
- If the task does not target that surface, treat the change as scope expansion
  and request direction. Never expose, weaken, or rewrite an oracle merely to
  make generated RTL pass.
- Evaluator or oracle changes are development work, not candidate-performance
  evidence. Their research interpretation follows the active Paper-1 freeze.

## Evidence, Contract, And Artifact Safety

- Keep `implemented`, `verified`, `target`, and `hypothesis` distinct. Do not
  silently relabel outcome statuses or erase their reasons.
- Schema or catalog conformance is not functional correctness. An audit verdict
  applies only to its named scope.
- Use current counts and checkout facts only from `docs/current-status.md`.
- Preserve backward-compatible readers unless the task is an explicit versioned
  migration. Runtime artifacts must validate against registered schemas.
- Generate candidate output under `artifacts/`. Promotion into `datasets/` or
  `reports/evidence/` is an explicit controlled operation.
- Do not track credentials, private endpoints, local absolute paths, model
  weights, raw vendor artifacts, hidden evaluator content, caches, or unrelated
  generated output.
- Keep claims bounded to the exact measured tool, target, population, artifact,
  and gate authority.

## Validation And Done

Use commands documented by the owning project README or
[`docs/current-status.md`](docs/current-status.md#current-commands); do not copy
command blocks here. Do not install heavy training or serving dependencies for
documentation or lightweight validation.

Before handing work back, confirm that the requested scope and success condition
are satisfied; relevant validation passed or its exact limitation is reported;
links and contracts touched by the change validate; no secret, hidden material,
generated artifact, or unrelated change was introduced; and external side
effects stayed within explicit authorization.
