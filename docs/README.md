# SR2FPGA Documentation Map

> [Terminology, 2026-09-08](specs/2026-09-08-sr2fpga-terminology.md): Project Contract (PC),
> currently serialized as System-HIS v1.2; FPGA Project Package (FPP).
> DSC names the design-space contract; DP names one design point. Internal
> identifiers and historical evidence names remain unchanged.

`docs/` is the lean current documentation workspace. It contains current
status, normative research specifications, and the Paper-1 reasoning/writing
workspace. Source-grounded literature packets live under `references/`,
machine contracts live with their owning projects, completed run evidence lives
under `reports/`, and superseded plans remain available through Git history.

## Start Here

For paper-facing names, use the [DSC / DP / PC / FPP terminology ledger](specs/2026-09-08-sr2fpga-terminology.md).
It defines naming only, not implementation or experiment authority.

Read only the entries required by the task; when several apply, use the order
below.

| Order | Entry | Answers | Authority |
| ---: | --- | --- | --- |
| 1 | [Current engineering and evidence status](current-status.md) | What this checkout currently implements, verifies, lacks, and should do next | Current-state summary; mutable facts come from code, tests, and evidence |
| 2 | [Paper-1 English canonical specification v1.7](specs/2026-08-14-sr2fpga-paper1-research-program-design.md) | What TRETS-targeted bounded requirement audit, M0-M5 core conditions, optional target-profile extension, privileges, metrics, statistics, and gates govern the no-training experiment | Research and experiment protocol authority |
| 3 | [Paper-1 code architecture and development specification v1.12](specs/2026-08-18-sr2fpga-paper1-code-architecture-development-spec.md) | How the frozen protocol maps to modules, interfaces, state machines, artifacts, work packages, and acceptance tests | Subordinate normative implementation design; does not change the estimand or create results |
| 4 | [Paper-1 Chinese companion](specs/2026-08-14-sr2fpga-paper1-research-program-design.zh.md) | How to read the canonical protocol in Chinese | Reading companion; English wins on conflict |
| 5 | [System-HIS v1.2 semantic specification](specs/2026-06-24-sr2fpga-system-his-v1.2-freeze-design.md) | What the retained Project Contract schema, W1-W10, H0-H2, and lowering semantics mean | Narrow semantic authority; not proof of runtime conformance |

There are two different north stars:

- `current-status.md` is the engineering north star for **what is true now**.
- The English Paper-1 freeze is the research north star for **what protocol to
  implement and eventually execute**.

Navigation order is not evidence authority. When sources disagree about present
behavior, use contracts and current code/tests first, then the task ledger and
its artifacts, then `current-status.md`. A research specification defines what
must be built or measured; it does not turn an intended condition into a result.

## Choose By Task

| Task | Reading path |
| --- | --- |
| Implement or fix code | [AGENTS.md](../AGENTS.md) -> owning project README -> relevant implementation/contracts/tests; add `current-status.md` for capability or gate claims, the relevant code-architecture section for Paper-1/evaluator work, and the freeze only when research semantics or official evaluation matter |
| Design or run an experiment | `current-status.md` -> English Paper-1 freeze -> machine contracts and evidence ledger -> signed gate artifacts; do not use dated report commands |
| Write the paper | English Paper-1 freeze -> [Paper-1 workspace](research-program/paper1-v1/README.md) -> argument map -> section contracts -> style guide |
| Compare with HORIZON | [Source-grounded HORIZON reader](../references/paper-readers/2606.28279v1/paper.md) -> [dated SR2FPGA positioning memo](../references/paper-readers/2606.28279v1/sr2fpga-positioning-2026-08-12.md) -> current Paper-1 freeze |
| Audit a claim | task ledger -> referenced stable artifact -> relevant named-run report -> `current-status.md`; preserve `not_run` and infrastructure boundaries |

## Directory Roles

| Directory | Contents | Status rule |
| --- | --- | --- |
| [`specs/`](specs/README.md) | Paper-1 canonical protocol, its subordinate code-development specification, Chinese companion, and retained Project Contract semantic spec | Normative specifications; no experiment results or transient task plans |
| [`research-program/paper1-v1/`](research-program/paper1-v1/README.md) | Frozen foundation, claim ledger, argument/writing aids, design QA, and workflow metadata | Derived support; never overrides the English freeze or machine facts |

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
  are superseded by `paper1-freeze-v1.7`.

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
- [Canonical Project Contract schema](../contracts/system-his/system-his-v1.2.schema.json)
- [Project Contract backend capability profile](../contracts/system-his/system-his-backend-capabilities-v1.json)
- [Current deterministic smoke configuration](../agent/configs/current/sr2fpga_deterministic_curriculum_smoke.example.yaml)
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
- Preserve completed plans, superseded designs, handoffs, and process
  scratchpads in Git history rather than restoring them to the working tree.
- Add a dated status banner whenever retained historical material could be
  mistaken for current instructions.
