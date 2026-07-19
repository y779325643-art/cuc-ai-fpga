# SR2FPGA Repository Reorganization Design

**Date:** 2026-07-17
**Status:** Approved design, implementation pending
**Baseline:** `origin/develop@54e2560c`
**Scope:** Workspace cleanup, monorepo boundary split, compatibility migration

## 1. Purpose

This design reorganizes the SR2FPGA repository in two controlled phases:

1. safely archive and remove local workspace clutter without losing research
   evidence or unpublished work;
2. separate the SR2FPGA data agent and the LLM training pipeline into two
   independent top-level subprojects in the same Git repository.

The repository remains a monorepo because agent changes, data-contract changes,
and training changes often need coordinated versioning. Independence is enforced
through package, dependency, test, configuration, and runtime boundaries rather
than separate Git histories.

## 2. Current-State Findings

The following snapshot was observed before this design was written:

- the local `develop` checkout was 23 commits behind `origin/develop`;
- the main worktree contained 251 tracked modifications and 8,622 untracked
  files;
- `tmp/` contained approximately 201 MiB across 9,091 files;
- `datasets/` contained approximately 138 MiB across 8,646 files;
- `tmp/` mixed tracked historical evidence, local-only runs, test caches, and
  scratch files;
- agent implementation, model training, serving scripts, and training
  dependencies were grouped under `LLM/` despite having different ownership;
- the agent package itself does not require the heavy model-training stack;
- `req2file_eval.py` is coupled to agent verification and belongs with the
  evaluation/data-agent side, not with model training.

These values are an audit snapshot, not long-term schema fields.

## 3. Decisions

The approved decisions are:

1. use a two-phase migration: cleanup first, structural split second;
2. keep one Git repository;
3. create `agent/` and `training/` as independent top-level subprojects;
4. use `contracts/` for shared schemas and versioned data contracts, without
   making it a third executable application;
5. keep one compatibility cycle for old `LLM/` commands and imports;
6. archive local state before any destructive cleanup;
7. keep official datasets in Git only when they are frozen, auditable, and
   intentionally publishable;
8. move reproducible runtime output to ignored `artifacts/` paths;
9. avoid unrelated internal refactors during the directory migration;
10. preserve `app/`, `outputs/`, `reports/`, `references/`, and `assets/` in the
    first migration unless a path update is strictly required.

## 4. Goals

### 4.1 Workspace goals

- recover a clean checkout aligned with the published `develop` branch;
- retain a verifiable external backup of every local tracked and untracked file;
- remove cache and scratch content from the version-controlled project surface;
- make generated output locations explicit and consistent.

### 4.2 Architecture goals

- make the data agent installable and testable without training dependencies;
- make the training project consume versioned exported data rather than agent
  implementation modules;
- give each subproject its own source, tests, configurations, scripts, package
  metadata, and dependency declarations;
- keep System-HIS, trajectory, training-view, and catalog contracts stable and
  machine-checkable;
- retain temporary compatibility for existing experiment commands.

## 5. Non-Goals

This migration does not:

- split the monorepo into separate Git repositories;
- redesign System-HIS semantics;
- change H0-H3 or L0-L5 verdict definitions;
- regenerate accepted datasets merely because paths move;
- rewrite `agent.py`, `runner.py`, `project_generator.py`, or other large modules;
- replace the current training algorithm;
- move unrelated presentations, manuscripts, board references, or application
  assets unless required for a working reference;
- make L4 the default for all Line B samples;
- remove compatibility entrypoints in the same release that introduces them.

## 6. Target Repository Map

```text
cuc-ai-fpga/
  agent/
    pyproject.toml
    README.md
    src/
      sr2fpga_agent/
    tests/
    configs/
      current/
      archive/
      legacy/
      local/                 # ignored local overrides
    scripts/

  training/
    pyproject.toml
    README.md
    src/
      sr2fpga_training/
    tests/
    configs/
    scripts/

  contracts/
    README.md
    system-his/
    trajectory/
    training-views/
    task-catalog/

  datasets/
    README.md
    manifest.json
    <frozen-release-id>/

  artifacts/                # ignored local runtime output
    agent/
      runs/
      generated-projects/
      tool-logs/
    training/
      prepared-data/
      checkpoints/
      adapters/
      merged-models/
      logs/
    scratch/

  compatibility_tests/
  docs/
  references/
  assets/
  app/
  outputs/
  reports/
  LLM/                      # temporary forwarding compatibility layer
  README.md
```

`agent/` and `training/` are the only new executable subprojects.
`contracts/` contains data definitions and fixtures, not runtime orchestration.

## 7. Ownership Boundaries

| Area | Owns | Must Not Own |
|---|---|---|
| `agent/` | requirements, System-HIS, generators, trusted oracles, EDA runners, H/L validation, repair, recorder, exports | model training loops, checkpoints, adapter merge, vLLM deployment |
| `training/` | data conversion, dataset validation for training, SFT/QLoRA, adapter merge, serving assets, model-side evaluation | RTL generation oracle, H/L verdict logic, EDA command execution |
| `contracts/` | JSON/JSONL schemas, contract versions, shared fixtures, compatibility policy | provider clients, tool runners, training loops |
| `datasets/` | frozen releases and release metadata | caches, mutable runs, checkpoints, private raw vendor artifacts |
| `artifacts/` | reproducible local outputs | committed source or authoritative contracts |
| `LLM/` | temporary wrappers and migration documentation | duplicate business logic |

## 8. Data Flow and Dependency Direction

The supported flow is:

```text
Requirement
  -> agent
  -> System-HIS and project
  -> H0-H3 / L0-L5 verdicts
  -> trajectory and training-view JSONL
  -> contract validation
  -> frozen dataset release
  -> training
  -> adapter or merged model
  -> model endpoint consumed by agent provider interface
```

Dependency rules:

```text
agent    -> contracts
training -> contracts
training -> frozen dataset exports
agent    -> model endpoint through a provider protocol

training -X-> sr2fpga_agent Python implementation
agent    -X-> torch/transformers/peft/trl/vllm
contracts-X-> agent or training implementation
```

The model endpoint is a runtime service boundary. It does not justify a Python
package dependency from `agent` to `training`.

## 9. Initial Path Mapping

### 9.1 Agent-owned paths

| Current path | Target path |
|---|---|
| `LLM/src/sr2fpga_agent/` | `agent/src/sr2fpga_agent/` |
| agent-related files in `LLM/tests/` | `agent/tests/` |
| `LLM/src/req2file_eval.py` | `agent/src/sr2fpga_agent/req2file_eval.py` |
| `configs/current/` | `agent/configs/current/` |
| `configs/archive/` | `agent/configs/archive/` |
| `configs/legacy/` | `agent/configs/legacy/` |
| `configs/local/` | `agent/configs/local/` |
| `scripts/openxc7_pnr.sh` | `agent/scripts/openxc7_pnr.sh` |

Task-catalog and task-evidence tests move with `agent`, while authoritative
machine-readable contract schemas move or are copied through an explicit version
transition into `contracts/task-catalog/`.

### 9.2 Training-owned paths

| Current path | Target path |
|---|---|
| `LLM/src/prepare_dataset.py` | `training/src/sr2fpga_training/prepare_dataset.py` |
| `LLM/src/train_lora.py` | `training/src/sr2fpga_training/train_lora.py` |
| `LLM/src/training_dry_run.py` | `training/src/sr2fpga_training/training_dry_run.py` |
| `LLM/src/merge_lora.py` | `training/src/sr2fpga_training/merge_lora.py` |
| training-related files in `LLM/tests/` | `training/tests/` |
| `LLM/configs/` | `training/configs/` |
| `LLM/scripts/` | `training/scripts/` |

Files move with `git mv` where possible to preserve history.

## 10. Contract Design

Each shared contract has an explicit version and validator.

### 10.1 Contract groups

- `system-his`: canonical System-HIS schema, examples, and compatibility notes;
- `trajectory`: episode, attempt, verdict, patch, QoR, and tool-version records;
- `training-views`: REQ2HIS, HIS2PROJECT, REQ2FILE, LOG2DIAG,
  FAILURE2PATCH, and QoR view schemas;
- `task-catalog`: family IDs, M/P/T/L taxonomy, target policy, oracle kind,
  mutation suite, and evidence linkage.

### 10.2 Contract invariants

- schema versions are stored in produced records;
- readers reject unsupported major versions;
- additive optional fields remain backward compatible within a major version;
- REQ2FILE remains a derived training view and never gains standalone project
  pass credit;
- OpenXC7 and commercial L4 labels remain distinct;
- `not_run` remains distinct from `fail`;
- environment failures remain distinct from model failures;
- trusted oracle artifacts remain non-editable by model repair.

## 11. Dataset and Artifact Policy

### 11.1 `datasets/`

Only frozen and intentional releases are tracked. Every release must include:

- a stable release ID;
- source commit and configuration fingerprint;
- contract versions;
- sample and label counts;
- tool versions;
- release tier and license metadata;
- a file manifest with hashes;
- known limitations and unavailable labels.

Mutable runs must not write into a frozen release directory.

### 11.2 `artifacts/`

`artifacts/` is ignored and is the default output root for new runs.

Agent defaults:

```text
artifacts/agent/runs/<run-id>/
artifacts/agent/generated-projects/<sample-id>/
artifacts/agent/tool-logs/<run-id>/
```

Training defaults:

```text
artifacts/training/prepared-data/<dataset-id>/
artifacts/training/checkpoints/<run-id>/
artifacts/training/adapters/<run-id>/
artifacts/training/merged-models/<model-id>/
artifacts/training/logs/<run-id>/
```

### 11.3 `tmp/`

`tmp/` is retired as a repository-owned runtime surface. Existing content is
archived externally before tracked temporary files are removed. Compatibility
code may read an explicitly supplied old path, but no new default writes there.

## 12. Phase A: Safe Workspace Recovery

Phase A runs before any source migration.

### 12.1 Capture state

Record:

- repository path;
- current branch and HEAD;
- `origin/develop` HEAD;
- worktree list;
- tracked, staged, untracked, and ignored status counts;
- configured remotes;
- timestamp and tool versions.

### 12.2 Backup layout

Use an external path such as:

```text
<external-backup>/
  manifest.json
  tracked-working-tree.patch
  staged-index.patch
  untracked/
  selected-ignored/
  checksums.sha256
  restore-instructions.md
```

The actual external root is retained out-of-band in the noncommitted Phase A handoff; `manifest.json` contains repository-relative file records and integrity metadata, not that root. A separate Phase B4 session must receive the root explicitly from the handoff and revalidate it before cleanup. Committed documentation contains no private backup root.

### 12.3 Backup validation

Before cleanup:

1. verify every source path is within the intended repository;
2. verify every backup path is within the approved external backup root;
3. compare source and backup file counts and byte totals;
4. validate the SHA256 manifest;
5. parse backed-up JSON and JSONL files where applicable;
6. test-restore at least one file from each major category;
7. keep `.env` and other secrets out of committed files.

### 12.4 Recovery to baseline

Only after backup validation:

- move or remove backed-up untracked files;
- restore tracked files to `origin/develop`;
- preserve local secret files that are intentionally ignored;
- remove verified cache directories;
- confirm `git status` is clean and HEAD matches `origin/develop`;
- create a dedicated implementation branch or worktree.

No cleanup command may run against a computed path until the resolved absolute
path is checked against the repository or backup root.

## 13. Phase B: Structural Migration

Phase B is incremental and must not be one giant move.

### Stage B1: Establish project shells

- add `agent/`, `training/`, and `contracts/` README files and package metadata;
- define lightweight agent dependencies and heavyweight training dependencies;
- add `artifacts/` and local override rules to `.gitignore`;
- keep existing implementation paths working.

### Stage B2: Move the agent

- move the agent package and agent tests;
- update imports from `LLM.src.sr2fpga_agent` to `sr2fpga_agent`;
- move agent configurations and OpenXC7 orchestration;
- preserve generation, oracle, repair, recorder, and report behavior;
- run agent tests and deterministic smoke before continuing.

### Stage B3: Move training

- create the `sr2fpga_training` package;
- move dataset preparation, dry-run, training, merge, and serving assets;
- split training tests and dependencies;
- update training configuration paths;
- prove that training code consumes files/contracts without importing agent
  implementation modules.

### Stage B4: Add compatibility wrappers

- keep old `LLM/` Python modules and shell entrypoints as thin forwarders;
- emit a concise deprecation message naming the replacement command;
- prohibit duplicate logic in wrappers;
- add compatibility tests for the documented old commands.

### Stage B5: Migrate documentation and defaults

- update root README and documentation index;
- add an old-to-new command migration table;
- update configuration examples and CI commands;
- change runtime defaults from `tmp/` to `artifacts/`;
- preserve dated historical plans rather than rewriting their paths as if they
  were authored after the migration.

## 14. Compatibility Policy

The compatibility layer lasts for one explicit migration cycle.

Supported old entrypoints include the documented forms of:

```text
python -m LLM.src.sr2fpga_agent.runner
python LLM/src/prepare_dataset.py
python LLM/src/training_dry_run.py
python LLM/src/train_lora.py
python LLM/src/merge_lora.py
```

Each wrapper:

- forwards arguments unchanged;
- returns the delegated process exit status;
- prints the replacement command to stderr;
- contains no implementation logic;
- is covered by a compatibility test.

Removal of `LLM/` wrappers requires a later approved design or explicit cleanup
task after all active configs, docs, and automation use the new entrypoints.

## 15. Dependency and Packaging Policy

### 15.1 Agent package

The base agent installation contains only dependencies required for contracts,
configuration, provider HTTP access, parsing, and orchestration. EDA binaries are
external tools discovered at runtime.

The base agent dependency graph must not include:

```text
torch
transformers
datasets
peft
trl
vllm
bitsandbytes
```

### 15.2 Training package

Training dependencies are isolated in `training/pyproject.toml` and may be split
into extras for training and serving. Importing lightweight dataset conversion
or dry-run modules must not eagerly import GPU libraries.

### 15.3 Development environment

Repository-level developer commands may install both projects, but CI must also
test each project independently to detect accidental dependency leakage.

## 16. Error Handling and Rollback

- stop immediately if backup counts or hashes disagree;
- stop if the clean baseline tests fail;
- stop after any migration stage if its focused tests fail;
- do not delete old entrypoints while compatibility tests depend on them;
- keep cleanup and structural migration in separate commits;
- keep the external backup unchanged until the final branch is merged, pushed,
  and independently verified;
- record all manual infrastructure adjustments separately from model or agent
  outcomes;
- never weaken trusted tests or change accepted verdict semantics to make a path
  migration pass.

Rollback uses the last passing commit. Phase A local state is restored from the
external manifest, patches, and file snapshot when needed.

## 17. Verification Strategy

### 17.1 Baseline

Before edits:

```text
python -m pytest LLM/tests
```

The design worktree baseline was:

```text
905 passed, 349 subtests passed
```

### 17.2 Agent verification

Required checks include:

```text
python -m pytest agent/tests
python -m sr2fpga_agent.runner --help
```

In addition:

- deterministic H0-H3/L0-L3 smoke passes;
- OpenXC7 parser and mocked L4 path pass;
- task catalog and evidence-ledger audits pass;
- no heavy training dependency is imported or declared by the base agent.

### 17.3 Training verification

Required checks include:

```text
python -m pytest training/tests
python -m sr2fpga_training.prepare_dataset --help
python -m sr2fpga_training.training_dry_run --help
```

In addition:

- representative training-view JSONL converts successfully;
- dry-run token and schema checks remain unchanged;
- training modules do not import `sr2fpga_agent`;
- heavy libraries are imported only when the selected command requires them.

### 17.4 Compatibility verification

```text
python -m pytest compatibility_tests
```

Every retained old command must delegate successfully and print its replacement.

### 17.5 Contract and data verification

- all JSON schemas parse;
- all committed JSON and JSONL release records parse;
- contract-version checks pass;
- an existing frozen episode exports semantically equivalent training views
  before and after migration;
- release manifests contain no secrets or machine-specific private paths;
- `not_run`, tool-environment failures, and model failures retain their original
  classification.

### 17.6 Repository hygiene

- `git status` is clean after each committed stage;
- `tmp/`, caches, checkpoints, and local tool logs are not tracked;
- `.env` remains ignored;
- root-level scripts are repository-wide orchestration only;
- documentation links and documented commands resolve;
- no implementation is duplicated between new packages and compatibility
  wrappers.

## 18. Acceptance Criteria

The reorganization is accepted only when all conditions hold:

1. the pre-cleanup local state has a validated external backup and restore guide;
2. the implementation branch starts from the published `origin/develop` state;
3. `agent/` and `training/` have independent package metadata, dependencies,
   tests, configs, scripts, and READMEs;
4. `training/` has no Python dependency on agent implementation;
5. `agent/` has no heavy model-training dependency;
6. shared records validate through versioned `contracts/` schemas;
7. official datasets remain readable and retain their verdict semantics;
8. runtime output defaults to ignored `artifacts/` paths;
9. the existing full test baseline is preserved or improved;
10. focused agent, training, contract, and compatibility suites pass;
11. deterministic project generation and verification smoke still pass;
12. old documented commands work through forwarding wrappers;
13. root and subproject documentation describe the new ownership model;
14. no secret, private absolute path, checkpoint, or vendor-restricted raw
    artifact is introduced;
15. the branch is committed and pushed with no required work left untracked.

## 19. Commit Boundaries

Use small reviewable commits:

1. `chore: archive and recover local workspace state`
2. `chore: establish agent and training project shells`
3. `refactor: move sr2fpga agent package`
4. `refactor: move sr2fpga training pipeline`
5. `refactor: add shared contracts and compatibility entrypoints`
6. `docs: update repository maps and migration guide`

The external backup itself is not committed. The first commit records only safe
repository policy changes and, where appropriate, a non-sensitive backup audit
summary.

## 20. Completion and Follow-Up

This migration is complete after the acceptance criteria pass, the branch is
reviewed and merged, and the remote contains the verified commits.

A later cleanup may remove `LLM/` compatibility wrappers only after:

- no active config or script references old paths;
- documentation search finds no current old commands;
- compatibility telemetry or usage review shows the migration cycle is complete;
- the removal is explicitly approved.
