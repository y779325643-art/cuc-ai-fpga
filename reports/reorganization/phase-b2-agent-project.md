# Phase B2 Standalone Agent Project Report

Date: 2026-07-23

Status: PASS

## Scope

Phase B2 separated the data-generation and verification Agent from the legacy
`LLM/` project. The canonical implementation now lives at
`agent/src/sr2fpga_agent/`; Agent tests, configurations, and operational
scripts are owned by `agent/`.

Training migration and the final compatibility cutover are intentionally
deferred to Phases B3 and B4.

## Task Commits

| Task | Commit | Result |
|---|---|---|
| Standalone package boundary | `2e2d8dbe` | Added `agent/pyproject.toml`, repository discovery, and boundary tests |
| Agent source move | `d332b23a` | Moved the canonical implementation into `agent/src/sr2fpga_agent/` |
| Legacy identity compatibility | `e76fb035` | Preserved canonical class/module identity through the old namespace |
| Repository resource paths | `0a555632` | Centralized contract, catalog, evidence, and script path resolution |
| Agent test ownership | `e4945375` | Moved Agent-owned coverage from `LLM/tests/` into `agent/tests/` |
| Config and script ownership | `8784e401` | Moved configs/scripts and redirected active output to ignored artifacts |

## Ownership State

- Canonical Agent source: `agent/src/sr2fpga_agent/` (57 Python files).
- Legacy Agent path: `LLM/src/sr2fpga_agent/__init__.py` only.
- Agent-owned tests: `agent/tests/`.
- Remaining `LLM/tests/` files cover Training or serving behavior only.
- Maintained configs: `agent/configs/current/`.
- Operational scripts: `agent/scripts/`.

Canonical code imports `sr2fpga_agent`; it does not import
`LLM.src.sr2fpga_agent`. The legacy namespace remains executable during the
transition and emits a `DeprecationWarning`.

## Independent Installation

The package installed successfully with:

```powershell
python -m pip install -e "agent[dev]"
```

Only the lightweight Agent runtime dependencies and pytest were installed.
Training dependencies were not installed by the Agent package.

Canonical help entry points passed for:

```text
sr2fpga_agent.cli
sr2fpga_agent.runner
sr2fpga_agent.baseline_report
sr2fpga_agent.req2file_eval
sr2fpga_agent.task_evidence
```

Final regression results:

- Contracts plus Agent: `932 passed, 344 subtests passed in 138.56s`.
- Remaining Training/serving tests under `LLM/tests/`:
  `31 passed, 5 subtests passed in 11.95s`.
- The remaining suite emitted one expected legacy-namespace
  `DeprecationWarning`.
- Legacy module execution exited successfully and emitted one deprecation
  warning:
  `python -W default -m LLM.src.sr2fpga_agent.runner --help`.

## Deterministic Verification

The maintained deterministic curriculum preflight planned 24 samples and
found the required L1-L3 tools. The full smoke run completed in 89.7 seconds:

| Result | Count |
|---|---:|
| Total completed | 24 |
| Highest level L3 | 24 |
| Repair trajectories | 0 |
| Rejected | 0 |

Validation aggregate:

- H0: 24 pass.
- H1: 24 pass.
- H2: 24 pass.
- H3: 14 pass and 10 not applicable.
- L0-L3: 24 pass and 0 fail at every level.
- L4-open: 24 `not_run`, all with `disabled_by_config`.
- L4-commercial: 24 `not_run`.
- Oracle-strength aggregate mutation score: 0.93.
- Toolchain-environment failures: 0.

`not_run` records were reported separately and were not counted as failures.
This run is L0-L3 evidence only; it does not claim L4 physical evidence.

Run outputs were written beneath:

```text
artifacts/agent/runs/phase-b2-agent-smoke
artifacts/agent/candidates/sr2fpga_rtl_v1
```

## EDA Tool Versions

The run-level `measurement_freeze.json` recorded:

- Verilator 5.049 development (`v5.048-335-g2d157b29b`, modified).
- Icarus Verilog 14.0 development
  (`s20260301-220-g78750c51d-dirty`).
- `vvp` runtime 14.0 development.
- Yosys 0.66+154 (`23aadd92a`).
- L4-open disabled by the smoke configuration.

The run-level measurement freeze is the authority for this smoke. Historical
per-sample `tool_versions.json` fields that remain `unknown` are not used to
invent version evidence.

## Repository Integrity

- Active configs write only beneath ignored `artifacts/`.
- No dataset payload or export changed.
- No new tracked file was written beneath `tmp/`.
- Existing tracked `tmp/` cleanup remains a Phase B4 gate.
- Generated editable-install metadata is ignored via `*.egg-info/`.

## Remaining Work

Phase B3 must create the independent `training/` project and move the remaining
Training and serving implementation, tests, configs, and scripts out of
`LLM/`. Phase B4 must complete compatibility cutover, remove obsolete residue,
and run the final repository audit.
