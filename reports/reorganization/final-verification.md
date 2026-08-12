# SR2FPGA Repository Reorganization Final Verification

Date: 2026-08-12

## Verdict

**APPROVED**

The repository reorganization satisfies the local Phase B4 acceptance criteria.
The canonical executable projects are `agent/` and `training/`, shared contracts
are owned by `contracts/`, tracked temporary content has been retired after a
verified external backup, and the complete post-cleanup test and smoke matrix
passes.

This verdict applies to the local feature branch described below. It does not
claim that the branch has already been pushed, reviewed on the remote, passed
remote CI, or merged. Those publication steps remain separate controlled actions.

## Verification Scope

| Item | Value |
| --- | --- |
| Formal migration baseline | `origin/develop@54e2560c` |
| Verified implementation head | `d98dfe9b` |
| Feature branch | `codex/reorganization-phase-b1` |
| Commits after baseline | 38 implementation and cleanup commits |
| Verification mode | Fresh post-cleanup local acceptance |

The implementation head is the cleanup commit against which all executable
checks in this report were run. This report is committed afterward as the final
documentation-only acceptance commit.

## Result Summary

| Gate | Result |
| --- | --- |
| Full Contracts + Agent + Training + Compatibility suite | **PASS**: 1,059 tests and 349 subtests |
| Phase A comparison | **PASS**: baseline was 905 tests and 349 subtests; no silent coverage loss |
| Compatibility suite alone | **PASS**: 31 tests |
| Contract/dataset/dependency focused suite | **PASS**: 16 tests |
| Tracked `tmp/` retirement suite | **PASS**: 4 tests |
| Deterministic Agent preflight | **PASS**: 24 samples planned, all tools discovered |
| Fresh deterministic Agent smoke | **PASS**: 24/24 through L3 |
| Lightweight Training conversion and dry run | **PASS**: 6/6 rows valid |
| Dataset inventory reproduction | **PASS**: no manifest, payload, or export diff |
| Task-evidence audit | **PASS** |
| Tracked `tmp/` paths | **PASS**: 0 |
| Tracked runtime files under `artifacts/` | **PASS**: 0, excluding the policy README |
| Canonical secret/private-value scan | **PASS**: 0 actual values |
| Canonical stale `LLM.` imports | **PASS**: 0 |
| Git whitespace check | **PASS** |

## Commit List By Phase

### Planning And Recovery Baseline

- `5945ad19` `docs: plan repository reorganization`
- `27732a25` `chore: record workspace recovery audit`
- `841f97f5` `docs: record cleanup deviation waiver`

### Phase B1: Contracts, Catalog, And Dataset Boundaries

- `14b25013` `chore: establish repository project boundaries`
- `a5e93d69` `feat: add canonical System-HIS contract`
- `db7e64f5` `feat: define trajectory and training-view contracts`
- `1f4e94da` `chore: establish canonical task catalog`
- `c7d99b7d` `chore: inventory immutable dataset releases`
- `f0a4fd87` `test: verify repository contracts and dataset policy`

### Phase B2: Standalone Agent Project

- `2e2d8dbe` `build: define standalone Agent project`
- `d332b23a` `refactor: move Agent implementation to standalone project`
- `e76fb035` `fix: preserve legacy Agent module identity`
- `0a555632` `refactor: centralize Agent repository paths`
- `e4945375` `test: move Agent coverage to Agent project`
- `8784e401` `refactor: move Agent configs and scripts`
- `2d34a314` `test: verify standalone Agent project`

### Phase B3: Standalone Training Project

- `23feb2c2` `build: define standalone Training project`
- `63159a6e` `refactor: move Training implementation to standalone project`
- `6df037b8` `refactor: move Training configs and serving assets`
- `c447f059` `feat: enforce training-view provenance`
- `19025243` `test: verify standalone Training project`
- `40c32316` `test: verify Agent and Training separation`

### Phase B4: Compatibility, Evidence, And Cleanup

- `1a9310a5` `refactor: add Python compatibility entrypoints`
- `3a8effab` `refactor: add shell compatibility entrypoints`
- `91e8808a` `docs: cut over to Agent and Training projects`
- `c83fec46` `test: preserve reorganization cutover contracts`
- `b3eab026` `chore: inventory legacy temporary evidence`
- `cd23606c` `fix: remove machine-specific OpenXC7 path`
- `40a1f8fb` `docs: record pre-cleanup verification`
- `13276680` `feat: automate Phase A backup recheck`
- `e47a2c3b` `fix: harden backup recheck boundaries`
- `cd1cb58b` `feat: add verified legacy evidence curation`
- `c3bbae7d` `fix: pin backup manifest for evidence curation`
- `b19a6fe6` `fix: harden independent oracle vector staging`
- `80575285` `feat: promote auditable reorganization evidence`
- `57128272` `test: align recorder with isolated oracle staging`
- `f5aeb5ea` `fix: preserve training dry-run CLI compatibility`
- `d98dfe9b` `chore: retire tracked temporary artifacts`

## Repository And Dependency Boundaries

The final ownership map is:

- `agent/`: project generation, verification, repair, trajectories, and reports.
- `training/`: dataset preparation, dry-run validation, training, merge, and serving assets.
- `contracts/`: versioned System-HIS, task-catalog, trajectory, and training-view boundaries.
- `datasets/`: immutable release payloads, exports, and checksum manifests.
- `reports/`: curated, reviewable evidence only.
- `artifacts/`: ignored runtime output only.
- `LLM/`: one-cycle compatibility wrappers and migration documentation only.

Dependency tests prove that Agent does not import Training or the heavy ML stack,
Training does not import Agent or `LLM`, and both projects discover the shared
contract registry. Compatibility tests also prove that `LLM/` contains no copied
business logic.

## Compatibility Command Matrix

The legacy surface is deliberately retained for one migration cycle. Each entry
prints its exact replacement and delegates arguments without reimplementing the
target behavior.

| Legacy command | Canonical command |
| --- | --- |
| `python -m LLM.src.sr2fpga_agent.runner` | `python -m sr2fpga_agent.runner` |
| `python -m LLM.src.sr2fpga_agent.cli` | `python -m sr2fpga_agent.cli` |
| `python -m LLM.src.req2file_eval` | `python -m sr2fpga_agent.req2file_eval` |
| `python LLM/src/prepare_dataset.py` | `python -m sr2fpga_training.prepare_dataset` |
| `python LLM/src/training_dry_run.py` | `python -m sr2fpga_training.training_dry_run` |
| `python LLM/src/train_lora.py` | `python -m sr2fpga_training.train_lora` |
| `python LLM/src/merge_lora.py` | `python -m sr2fpga_training.merge_lora` |
| `LLM/scripts/setup_server.sh` | `training/scripts/setup_server.sh` |
| `LLM/scripts/serve_qwen_vllm.sh` | `training/scripts/serve_qwen_vllm.sh` |
| `LLM/scripts/serve_vllm.sh` | `training/scripts/serve_vllm.sh` |
| `LLM/scripts/train_lora.sh` | `training/scripts/train_lora.sh` |
| `LLM/scripts/merge_lora.sh` | `training/scripts/merge_lora.sh` |
| `LLM/scripts/test_api.sh` | `training/scripts/test_api.sh` |

Independent compatibility verification: **31 passed**. The legacy surface has
20 tracked files totaling 10,148 Git blob bytes. Its later removal requires a
new explicit approval after active usage is reviewed.

## Backup And Tracked Temporary Retirement

The destructive gate was executed only after the operator supplied the external
Phase A backup root and the repository reverified it.

| Backup measure | Result |
| --- | ---: |
| Status | `pass` |
| Files checked | 14,841 |
| Bytes checked | 336,542,906 |
| Checksum lines | 14,841 |
| Integrity failures | 0 |
| Restore samples | 6 |
| Manifest SHA-256 | `0f92ce7b1d289cee351c145c924f7cb27d4ec861acf04dc23f56caadaa00cc42` |

The retained historical inventory at
`reports/reorganization/legacy-tmp-inventory.json` accounts for all 590 paths
that were tracked before cleanup, totaling 3,050,197 Git blob bytes. All 590 are
classified `external_backup_only`; auditable evidence required by active claims
had already been regenerated and promoted to stable `reports/evidence/` paths.

Post-cleanup results:

- `git ls-files -- tmp` returns zero paths.
- Root `.gitignore` contains `/tmp/`.
- Canonical configs do not write runtime output under `tmp/`.
- Active evidence references do not point to live `tmp/` paths.
- `compatibility_tests/test_tmp_retirement.py` reports 4 passed.
- The external backup remains unchanged and must be retained until the merged
  remote commit is independently verified.

## Full Test Verification

Command:

```text
python -m pytest contracts/tests agent/tests training/tests compatibility_tests -q
```

Result:

```text
1059 passed, 349 subtests passed in 197.81s
```

The Phase A baseline was 905 tests and 349 subtests. The reorganized suite adds
migration, contract, compatibility, evidence, and retirement coverage without
losing baseline assertions.

Focused results:

- Compatibility: 31 passed.
- Dataset release policy, contract fixtures, and dependency boundaries: 16 passed.
- Tracked temporary retirement: 4 passed.
- Task-evidence audit: exit code 0.

## Deterministic Agent Verification

The canonical preflight command planned 24 samples and found Verilator, Icarus,
VVP, and Yosys. It returned no warning or error.

Fresh isolated smoke artifact:

```text
artifacts/reorganization/final-acceptance-20260812/agent-runs/
reorganization-final-smoke-post-cleanup-20260812/
```

| Measure | Result |
| --- | ---: |
| Planned / completed | 24 / 24 |
| Rejected / repair trajectories | 0 / 0 |
| H0 / H1 / H2 pass | 24 / 24 / 24 |
| H3 pass / not applicable / fail | 14 / 10 / 0 |
| L0 / L1 / L2 / L3 pass | 24 / 24 / 24 / 24 |
| L4-open pass / fail / not run | 0 / 0 / 24 |
| L4-open skip reason | `disabled_by_config`: 24 |
| Toolchain environment failures | 0 |
| Mutation score | 0.93 (43/46 scoreable mutations killed) |
| Line A ready / not ready | 10 / 14 |

`not_run` is kept separate from failure. The default Line B smoke therefore
preserves the intended L0-L3 scale policy rather than pretending to exercise L4.
Runtime task tiers are catalog-driven: the fresh summary places SPI in T1,
valid-ready streaming in T2, and FIR plus matrix-vector MAC in T3.

Stable curated evidence independently retains two OpenXC7 L4 passes:

| Sample | WNS (ns) | Fmax (MHz) | LUT | FF | BRAM | DSP |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| FIR filter | 7.638 | 423.37 | 30 | 28 | 0 | 3 |
| Matrix-vector MAC | 8.011 | 502.77 | 48 | 27 | 0 | 1 |

These are OpenXC7 labels. Commercial Vivado status remains separately recorded
and is not inferred from open-tool success.

## Lightweight Training Verification

Canonical commands converted the preserved fixture and ran only token/format
validation; no model was trained or downloaded.

| Measure | Result |
| --- | ---: |
| Converted rows | 6 |
| Valid rows | 6 |
| Minimum tokens | 45 |
| Maximum tokens | 164 |
| Mean tokens | 87.0 |
| Rows over 2,048 tokens | 0 |

The dry-run compatibility fix preserves the existing `--train-file` CLI while
the canonical Training project owns the implementation.

## Contracts And Dataset Immutability

The inventory tool rebuilt all three release manifests and produced no Git diff
in the manifests, payloads, or exports.

| Manifest | File SHA-256 after reproduction |
| --- | --- |
| `sr2fpga_rtl_v1.sha256` | `7247ed8d9692d4c2346fbf1155335d66cd2fee643181dcddb2316ee87b05554f` |
| `sr2fpga_phase_d_control_v1.sha256` | `5fa48cfa05649ef8433d553b91d6716ca05526068b26045160215339bf3d5d33` |
| `sr2fpga_phase_d_v1.sha256` | `d852272397aeecea0b2dfaf3fc11a16ecc6265ba72373e471585ef8d910594e3` |

`REQ2FILE` remains a derived training view: it has no standalone or project-level
pass credit until files are assembled into a complete project and judged through
the normal verification pipeline.

## Security, Path, And Repository Hygiene

- Canonical Agent and Training source contains no private absolute path or API key value.
- Canonical configs contain no machine-specific default output path.
- Contract tooling contains generic regular expressions that detect private paths;
  those patterns are scanners, not embedded machine-specific values.
- No canonical Agent, Training, or Contracts implementation imports `LLM.`.
- No runtime file is tracked below `artifacts/`; only the policy README is tracked.
- `git diff --check` reports no whitespace error.
- The tracked worktree is clean at the verified implementation head.

## Review Findings And Known Residuals

The local review focused on lost tests, duplicate implementation, dependency
direction, dataset immutability, temporary-data retirement, compatibility
behavior, and Windows/WSL path handling. No blocking finding remains.

Known residuals are intentional and bounded:

1. `LLM/` remains for one explicit compatibility cycle. It must not receive new
   business logic and cannot be removed without later approval.
2. The deterministic scale smoke deliberately records L4 as `not_run`; physical
   claims use separate representative OpenXC7 evidence.
3. Remote push, pull-request review, CI, and merge are not part of this local
   acceptance verdict and must be reported separately when performed.
4. The external Phase A backup must remain intact until the merged remote commit
   is independently verified.

## Final Decision

Every required local Phase B4 acceptance check passed. The feature branch is
clean at the verified implementation head, committed through tracked temporary
retirement, locally reviewed, and ready for an explicitly approved publication
step.

**APPROVED**
