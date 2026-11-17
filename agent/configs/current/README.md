# Maintained legacy development configurations

These YAML files drive the retained System-HIS development runtime. The directory
name is not a current Paper-1 research designation. Old UART/FIR/Sobel/Q-table,
Line A/B, physical subsets and multi-teacher examples retain their original scope.
They must not be relabelled as paper1-v2.2 or the three AI-family benchmark.

The legacy loader rejects explicit `research_plan_version` or `pc_format` fields
instead of ignoring them. `paper1-b4-v1` aligns the call axis only; it does not
make these configurations complete v2.2 runs. Paid/model/EDA execution needs its
own authorized scope. No new campaign template is provided with invented budgets,
task profiles, splits or qualification.

Current development: `python -m sr2fpga_agent.pc --help` and the
[PC development guide](../../src/sr2fpga_agent/pc/README.md). Retained `assemble/check`
validate input/schema/bindings; typed `validate/build/compose` add static
semantics, deterministic RTL and parser-protected behavior composition. The
separate fixed DW→PW development adapter does not turn these legacy YAML files
into new-protocol configurations.
Resume implementation from the [migration record](../../../docs/migrations/research-plan-alignment.md).
