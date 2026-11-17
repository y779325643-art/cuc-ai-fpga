# SR2FPGA Documentation Map

For a source-grounded Chinese learning path, start with the
[code handbook](code-guide/README.md): runnable examples, architecture,
PC2.1 and M0–M5 mechanisms, LLM arithmetic, diagrams, evaluation/analysis,
and a [deep implementation review](code-guide/09-deep-review.md).
Its [validation record](code-guide/10-validation.md) distinguishes executed
checks, tool/environment failures and unrun research work.

Current case/population authority is the adopted 2026-10-28
[`paper1-v2.3` LLM amendment](specs/2026-10-28-sr2fpga-paper1-llm-case-amendment-v2.3.zh.md),
read together with the v2.2 base plan for methods, metrics and evidence rules.
The three current families are QKV projection, KV-cache decode attention and
gated FFN. Start implementation through the [LLM case guide](../agent/src/sr2fpga_agent/tasks/README.md).
The amendment and [current status](current-status.md) separate current targets
from implemented and verified capabilities.

> [Terminology, 2026-09-08](specs/2026-09-08-sr2fpga-terminology.md): Project Contract (PC),
> now serialized as `sr2fpga-pc-2.1`; FPGA Project Package (FPP).
> DSC names the design-space contract; DP names one design point. Internal
> identifiers and historical evidence names remain unchanged.

`docs/` is the lean current documentation workspace. It contains current
status, normative research specifications, and the Paper-1 reasoning/writing
workspace. Source-grounded literature packets live under `references/`,
machine contracts live with their owning projects, completed run evidence lives
under `reports/`, and retained superseded specifications are indexed under
[`specs/superseded/`](specs/superseded/README.md).

## Active Route and Historical Records

The active local `develop` checkout follows [Paper-1 / PC 2.1](routes/paper1-ai.md).
See [WORKTREE.md](../WORKTREE.md) for the checkout and the [route index](routes/README.md)
for the historical generated-testbench reliability study and its separate evidence.

## Start Here

For current execution code use the [PC2.1 runtime guide](../agent/src/sr2fpga_agent/execution/README.md)
and [offline analysis guide](../agent/src/sr2fpga_agent/analysis/README.md).
Their [implementation record](migrations/pc21-runtime-implementation-20261028.md)
separates verified synthetic/real-tool development checks from unrun model,
container-qualification and official experiments.

For paper-facing names, use the [DSC / DP / PC / FPP terminology ledger](specs/2026-09-08-sr2fpga-terminology.md).
It defines naming only, not implementation or experiment authority.

Read only the entries required by the task; when several apply, use the order
below.

| Order | Entry | Answers | Authority |
| ---: | --- | --- | --- |
| 1 | [Current engineering and evidence status](current-status.md) | What this checkout currently implements, verifies, lacks, and should do next | Current-state summary; mutable facts come from code, tests, and evidence |
| 2 | [Paper-1 LLM case amendment v2.3](specs/2026-10-28-sr2fpga-paper1-llm-case-amendment-v2.3.zh.md) and [v2.2 base plan](specs/2026-09-15-sr2fpga-paper1-research-plan-v2.2.zh.md) | Current QKV, KV-cache decode attention and gated FFN population; inherited M0-M5, B4, comparisons, design clusters, metrics and statistics | Research plan authority, adopted 2026-10-28, not frozen |
| 3 | [Paper-1 code architecture and development specification v2.1](specs/2026-09-15-sr2fpga-paper1-code-architecture-development-spec-v2.1.zh.md) | How the protocol maps to modules, interfaces, state machines, artifacts, work packages, and acceptance tests | Subordinate normative implementation design; a target architecture, not current state |
| 4 | [PC 2.1 contract design](specs/PC-2.1-AI-stream-contract-design.zh.md) and its [registered schemas](../contracts/pc/2.1/) | Tensor, quantization, sequence and bounded relations, and their limits | Typed static checks and deterministic RTL construction exist; actual behavior needs independent execution. See the [development guide](../agent/src/sr2fpga_agent/pc/README.md) |
| 5 | [Migration record](migrations/research-plan-alignment.md) | How far the repository has actually moved toward the current plan, what was verified, and what blocks | Engineering record; tracks decisions and evidence, defines no research semantics |
| 6 | [Superseded specifications](specs/superseded/README.md) | What earlier plans and formats required, and why each is retained | Historical only; never a current instruction |

There are two different north stars:

- `current-status.md` is the engineering north star for **what is true now**.
- `paper1-v2.3` with its v2.2 base is the research north star for **what protocol to implement and
  eventually execute**. It is a plan of record, not a freeze: adoption
  authorized repository migration but no experiment.

Navigation order is not evidence authority. When sources disagree about present
behavior, use contracts and current code/tests first, then the task ledger and
its artifacts, then `current-status.md`. A research specification defines what
must be built or measured; it does not turn an intended condition into a result.

## Choose By Task

| Task | Reading path |
| --- | --- |
| Implement or fix code | [AGENTS.md](../AGENTS.md) -> owning project README -> relevant implementation/contracts/tests; add `current-status.md` for capability or gate claims, the relevant code-architecture section for Paper-1/evaluator work, and the research plan only when research semantics or official evaluation matter |
| Design or run an experiment | `current-status.md` -> `paper1-v2.3` amendment and v2.2 base -> machine contracts and evidence ledger -> work-package acceptance artifacts; do not use dated report commands |
| Write the paper | `paper1-v2.3` amendment and v2.2 base -> [Paper-1 workspace](research-program/paper1-v1/README.md) -> argument map -> section contracts -> style guide; historical workspace aids need scope re-review |
| Compare with HORIZON | [Source-grounded HORIZON reader](../references/paper-readers/2606.28279v1/paper.md) -> [dated SR2FPGA positioning memo](../references/paper-readers/2606.28279v1/sr2fpga-positioning-2026-08-12.md) -> `paper1-v2.2` section 13.1 |
| Audit a claim | task ledger -> referenced stable artifact -> relevant named-run report -> `current-status.md`; preserve `not_run` and infrastructure boundaries |
| Continue the migration | [LLM migration record](migrations/llm-case-migration-20261028.md) -> `paper1-v2.3` -> the specific asset row; retain the earlier migration history |

## Directory Roles

| Directory | Contents | Status rule |
| --- | --- | --- |
| [`specs/`](specs/README.md) | Current Paper-1 research plan, its subordinate code-development specification, superseded Paper-1 specifications, and the retained Project Contract semantic spec | Normative specifications; no experiment results or transient task plans |
| [`research-program/paper1-v1/`](research-program/paper1-v1/README.md) | Foundation snapshot, claim ledger, argument/writing aids, design QA, and workflow metadata | Derived support; never overrides the current research plan or machine facts. Written against v1.7/v1.8; scope re-review pending |
| [`migrations/`](migrations/README.md) | Current LLM v2.3 implementation record and retained v2.2 alignment history | Engineering records of decisions, implementation and validation; they do not define research semantics |
| [`history/engineering/`](history/engineering/README.md) | Completed design and implementation records for retired gates | Historical; not current instructions |

Literature and other external source material are catalogued separately in the
[`references/` index](../references/README.md). This keeps source material out
of the active-guidance namespace without weakening its provenance.

The root of `docs/` intentionally contains only this map and
`current-status.md`.

## Paper-1 Workspace

The [workspace README](research-program/paper1-v1/README.md) is the only entry
point for the local bundle:

- `foundation/` preserves the historical research canon and claim-to-evidence
  table at the 2026-08-14 design cutoff;
- `writing/` contains the active argument map, section contracts, and style
  guide;
- `audit/` contains the active v1.7 design-amendment QA plus historical design-
  time QA snapshots whose old inventory/test counts are not current validation;
- `state.json` is derived workflow metadata, not gate authority.

## Literature Packet

The HORIZON packet separates three roles:

- [`paper.md`](../references/paper-readers/2606.28279v1/paper.md) records what the source paper
  says, with figures, tables, and stable page anchors;
- [`translation_notes.md`](../references/paper-readers/2606.28279v1/translation_notes.md) and
  [`source_map.json`](../references/paper-readers/2606.28279v1/source_map.json) record extraction
  and provenance decisions; and
- [`sr2fpga-positioning-2026-08-12.md`](../references/paper-readers/2606.28279v1/sr2fpga-positioning-2026-08-12.md)
  records a dated SR2FPGA interpretation. Its old method ladder and task list
  are superseded by `paper1-v2.2`.

The seven PNG files in `assets/` belong to this reader packet and are not
standalone project evidence.

## Evidence Lives Under Reports

- [Reports index](../reports/README.md)
- [Repository-reorganization final verification](../reports/reorganization/final-verification.md)
- [Executable task-evidence ledger](../reports/evidence/task-ledger/sr2fpga-task-evidence-v0.1.json)
- [Human-readable evidence status](../reports/evidence/task-ledger/sr2fpga-task-evidence-status.md)
- [Phase C independent-oracle report](../reports/evidence/phase-reports/sr2fpga-phase-c-independent-oracle-evidence-2026-07-14.md)
- [Phase D frozen pilot](../reports/evidence/phase-reports/2026-07-17-sr2fpga-phase-d-pilot-report.md)
- [Phase D failure and H2 analysis](../reports/evidence/phase-reports/2026-07-17-sr2fpga-phase-d-failure-analysis-and-h2-hardening.md)

Named-run reports are authoritative only for their named runs. Commands and
paths retained inside them are historical provenance, not current operating
guidance. An `APPROVED` verdict applies only to its named audit scope;
`not_run` is not a failure, infrastructure failure is not design failure, and a
mutation score qualifies an oracle rather than model performance.

## Machine Authorities Outside Docs

- [Contract registry](../contracts/manifest.json)
- [Canonical task catalog](../contracts/task-catalog/sr2fpga-task-catalog-v0.2.json)
- [Current PC 2.1 Project Contract schema](../contracts/pc/2.1/project-contract-2.1.schema.json)
- [Historical System-HIS v1.2 schema](../contracts/system-his/system-his-v1.2.schema.json)
- [Legacy System-HIS backend capability profile](../contracts/system-his/system-his-backend-capabilities-v1.json)
- [Legacy development deterministic smoke configuration](../agent/configs/current/sr2fpga_deterministic_curriculum_smoke.example.yaml)
- [Dataset release registry](../datasets/manifest.json)

The target catalog describes intended policy; it does not prove verification.
The evidence ledger records executable and verification facts, and its Markdown
status is the derived human-readable view. Test-only fixtures live under
`agent/tests/fixtures/` and are not project authority.

The JSON files in the documentation/reference layer are metadata:
`references/paper-readers/2606.28279v1/source_map.json` preserves literature
provenance, while `docs/research-program/paper1-v1/state.json` records
writing/gate workflow state. Neither is a runtime contract or evidence source.

## Repository Guides

- [Repository overview](../README.md)
- [Coding-agent guidance](../AGENTS.md)
- [Agent project](../agent/README.md)
- [Training project](../training/README.md)
- [Contracts](../contracts/README.md)
- [Dataset releases](../datasets/README.md)
- [Runtime artifacts](../artifacts/README.md)
- [Presentations and reference outputs](../outputs/)

Repository-wide ownership and operating rules are defined in
[AGENTS.md](../AGENTS.md); project-local details live in the linked project
READMEs.

## Lifecycle Rule

- Put current navigation, normative research specifications, and active
  manuscript reasoning under `docs/`.
- Put source papers, source-grounded readers, hardware manuals, and other
  external/background material under `references/`.
- Put immutable machine contracts with their owning project and committed
  evidence or completed named-run reports under `reports/`.
- Put generated runtime output under `artifacts/`.
- Keep retained superseded specifications indexed under `specs/superseded/`;
  completed records retained under `history/engineering/` are historical.
  Use Git history for other retired scratchpads and handoffs.
- Add a dated status banner whenever retained historical material could be
  mistaken for current instructions.
