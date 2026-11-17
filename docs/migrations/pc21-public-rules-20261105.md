# PC 2.1 public rule guidance and interface-name index

Date: 2026-11-05. Scope: the user authorized progress on PC expression burden,
model-visible rules and LLM case coverage, while deferring changes to repair
mechanisms. This increment changes development prompt inputs and supporting
documentation. It does not change the adopted research definitions, candidate
repair actions, checker rules, task mathematics, trusted evaluators or scores.

## Delivered behavior

- `pc21-public-guidance-v2` preserves the existing native-Yosys/Icarus guidance
  and explains task-independent PC semantics: three name spaces, complete unique
  tensor-port main relations, multi-output `compute`, behavioral state ownership,
  local complete-beat FIFO bindings, direct-net compatibility and capability
  bounds. The same guidance reaches every initial and repair stage. Direct
  stages retain their own output format and need not return a PC.
- `execution/public_interfaces.py` derives `pc21-public-interface-index-v1`
  solely from an already admitted public entry boundary. Every runtime model
  request receives the same logical-port / tensor-ID / physical-ABI index,
  domain pins and public parameter values. It does not select internal modules,
  propose a design, load evaluator material or replace the original boundary.
- `ModelGateway` adds the index before serialization and input accounting.
  Its version and content enter the frozen request bytes. A caller cannot
  substitute an index. Source/request drift remains an error; old outputs
  cannot silently continue under revised prompt inputs.
- [Public declaration examples](../../agent/tests/fixtures/pc21_public_rules/README.md)
  use existing registered formats and actual static admission. They explain
  legal multi-output computation and FIFO declarations, reject schema-valid
  namespace/coverage/binding/type/domain mistakes, and preserve legal naming
  and structural alternatives. No behavior implementation or case answer is
  added to model context.
- [LLM case coverage](../code-guide/llm-case-coverage.zh.md) maps existing
  obligations and tests and gives a bounded next-development order. It is a
  source audit, not a new qualification result or a new design-cluster release.

The rule text is intentionally generic. The actual request grows, and these
additional inputs consume the configured input/context budget. No budget is
raised automatically. Whether the clarification reduces natural-model failures
or total cost requires a separately scoped development comparison; static
admission and synthetic response tests do not establish that benefit.

## Validation and evidence

The development record is
`artifacts/paper1-ai/pc21-public-rules-20261105-01/`. Its `before/` directory
preserves affected existing file contents, and `staged-before.patch` preserves
the original staging diff. Original runs and their scores are retained.

`combined-01.xml` records **142 passing tests, no skips or failures** across the
new public-index, semantic-guidance and declaration-example tests, existing
prompt tests, and gateway/budget regressions. Tests exercise all eight model
stages using explicit synthetic transports, binding drift, charged input size,
registered schema validation and the real static checker. Ruff passes for all
changed Python files. Tests made zero external model requests and ran no EDA
tools or independent terminal suite.

The final `final-checks-01.xml` records **321 passing tests, no skips or
failures**, adding existing static PC input/semantic/registration and runtime
integration checks. This includes the earlier 142; counts from overlapping
runs must not be added. The normal `tasks.llm prepare --case all` CLI also
prepared fresh public inputs for all three cases without model/tool execution.
The three `public-interface-index-<case>.json` files show the resulting name
views. Documentation links and staging-preservation checks accompany the
completion record.

No natural-model rerun, official experiment, new hidden suite, physical run,
dataset/evidence promotion, external publication, Git commit or push is part
of this increment. Existing formal-readiness and qualification limits remain.
