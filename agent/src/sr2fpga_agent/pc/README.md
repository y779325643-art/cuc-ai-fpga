# PC 2.1 development

Authority: [research plan](../../../../docs/specs/2026-09-15-sr2fpga-paper1-research-plan-v2.2.zh.md) and [architecture sections 6–8](../../../../docs/specs/2026-09-15-sr2fpga-paper1-code-architecture-development-spec-v2.1.zh.md).

This package parses PC 2.1, checks its listed static semantics, generates deterministic RTL structure, and composes provided behavior using real Yosys parsing. Family algorithms and the independent reference are separate in [tasks/ai_dw_pw](../tasks/ai_dw_pw/README.md).

The current `paper1-v2.3` population has fixed QKV, KV-cache decode attention
and gated FFN controls. See the [LLM case guide](../tasks/README.md) and
`python -m sr2fpga_agent.tasks.llm --help` for public preparation and actual
PC-emitted control validation. These use the same registered PC2.1 boundary;
the DW/PW external-model adapter below remains a historical development surface,
not an authorization to dispatch models for the new cases.

The [current six-method runtime](../execution/README.md) now provides a shared
PC2.1 initial DAG, model-owned proposal/repair transactions, budgeted frontend
execution and independent terminal workers. Its verified scope is development
fixtures; the old external DW/PW adapter below remains separate.

The [current six-method runtime](../execution/README.md) now provides a shared
PC2.1 initial DAG, model-owned proposal/repair transactions, budgeted frontend
execution and independent terminal workers. Its verified scope is development
fixtures; the old external DW/PW adapter below remains separate.

## Commands

`assemble` accepts a design root and binds three operator-selected original public source files. `check` rechecks that saved PC. These retained input-only commands accept opaque source bytes and explicitly report partial semantics.

`validate`, `build`, and `compose` require the registered development public context v2, PC2.1 development target v1 and capability v1. They validate actual public asset bytes from the operator-selected root and run the semantic checker. `build` emits structure with required behavior interfaces. `compose` accepts a complete `pc21-behavior-bundle-v1` and emits a canonical `project-package-v1` FPP after parser checks.

```powershell
$env:PYTHONPATH = (Resolve-Path agent/src).Path
python -B -m sr2fpga_agent.pc assemble --input DESIGN.json `
  --requirements PUBLIC_REQUIREMENTS.json --requirements-id requirements `
  --target-profile TARGET.json --target-profile-id target-profile `
  --capability-profile CAPABILITY.json --capability-profile-id capability-profile `
  --max-bytes 8000000 --max-depth 128 --output artifacts/PC.json

python -B -m sr2fpga_agent.pc validate --input artifacts/PC.json `
  --requirements PUBLIC_REQUIREMENTS.json --requirements-id requirements `
  --target-profile TARGET.json --target-profile-id target-profile `
  --capability-profile CAPABILITY.json --capability-profile-id capability-profile `
  --asset-root PUBLIC_ASSETS_ROOT --max-bytes 8000000 --max-depth 128
```

For construction replace `validate` with `build` and add `--output artifacts/<fresh-directory>`. For composition use `compose`, add `--behavior-bundle BUNDLE.json`, and choose a fresh output. The bundle must bind the exact build SHA and supply every required unit exactly once. Existing outputs are never overwritten. Raw parser sources and logs persist under the sibling `<output>-parser` directory, including failures. Complete output also records controller-generated construction origins and parser evidence.

Input parsing rejects duplicate keys, floating/nonfinite numbers, invalid Unicode, oversized/deep JSON, old formats, candidate-owned bindings and changed source bytes. The example resource limits are development limits.

## Implemented scope

- Module references, recursion, reachability, signature ownership, explicit parameter coverage, bounded expression evaluation and ranges.
- Domain/reset compatibility, endpoint wiring, driver/direction rules, stream fanout restrictions, exact packed types and public ABI mappings.
- Tensor shape/order/lane/tail, affine/per-axis quantization, dense/partial-sum identities, finite tensor relations and buffer declarations.
- State, numeric/timing declarations, public fact roles, required trace coverage, asset identities and capability limits.
- Deterministic specialization, names/files/instances/constants, record/lane/mask packing, reverse ready wires and dependency-bound behavior units.
- Body-only composition with lexical exclusion of external access/macros, real AST/signature/instance checks, and whole-project elaboration. Extra modules, hidden submodules, hierarchical access and input writes are rejected.

Static success does not prove algorithms, actual arithmetic/layout/reset/transactions, liveness, timing or resources. Those obligations remain explicitly deferred to independent execution. Generic synthesis does not establish FPGA mapping, physical timing or L4.

## External-model development

`development.prepare_dw_pw(Path("artifacts/paper1-ai/<fresh-run>"), max_model_calls=6)` materializes the fixed public task. `DevelopmentSession` reuses immutable `ArtifactStore` blobs/events, reserves calls before dispatch, and retains invalid raw responses. Reopening does not reset the budget. Six calls is the authorized development diagnostic ceiling, not the formal B4 setting.

The external model receives public facts/assets and the requested schema or body interfaces, then returns text for host admission. Oracle source, expected values and evaluator stimuli are absent from the prompt. This adapter does not implement an OS sandbox for the external model: a collaboration agent with shared host tools remains an excluded development diagnostic with the limitation recorded. Frozen public bytes and trusted source snapshots are checked before dispatch/build/evaluation. Unmeasured provider token usage remains unavailable.

`evaluate_public` persists compiler/simulator/synthesis logs and checks complete transaction traces independently. Optional terminal replay uses different development inputs on the identical candidate; it is not official hidden evaluation.

## Validation

```powershell
python -B -m pytest agent/tests/test_sr2fpga_pc21_inputs.py `
  agent/tests/test_sr2fpga_pc21_cli.py agent/tests/test_sr2fpga_pc21_semantic_checker.py `
  agent/tests/test_sr2fpga_pc21_context.py agent/tests/test_sr2fpga_pc21_emitter.py `
  agent/tests/test_sr2fpga_pc21_development_tools.py agent/tests/test_sr2fpga_ai_dw_pw_reference.py `
  -q -p no:cacheprovider --basetemp=artifacts/paper1-ai/<fresh-test-directory>
```

Emitter/reference tests invoke real Yosys/Icarus/vvp. On the investigated Windows installation Icarus access-violated inside the sandbox while identical tests passed outside through the host approval mechanism. Preserve that environment distinction instead of classifying tool crashes as candidate failures.
