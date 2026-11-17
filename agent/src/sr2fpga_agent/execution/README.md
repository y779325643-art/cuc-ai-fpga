# PC 2.1 six-method development runtime

This package connects current PC 2.1 inputs to M0–M5 generation, repair,
resource accounting and terminal evaluation. It does not execute an official
campaign. The current authority remains the [LLM case amendment](../../../../docs/specs/2026-10-28-sr2fpga-paper1-llm-case-amendment-v2.3.zh.md)
and its v2.2 base. Task qualification, formal splits and scientific budget
values are still unfrozen.

## Method execution

`PairedBlockRuntime` consumes a typed `PublicTask`, a frozen `RuntimeIdentity`,
six explicit `BudgetLimits`, a `TextTransport`, a backend and disjoint control /
evaluator roots. It uses the existing `ArtifactStore`, canonical FPP manifest,
PC checker and structure emitter.

| Initial node | Consumers | Generation |
| --- | --- | --- |
| SD | M0, M1 | One complete Direct project proposal |
| UP | M2 | Untyped plan, then complete project |
| SC | M3, M4, M5 | One PC proposal and shared checker admission |
| M3 branch | M3 | Free canonical project from the shared PC; no structure emitter |
| SB | M4, M5 | Deterministic structure plus one complete batch of required bodies |

The controller balances topologically valid initial order with a local schedule
seed. It shares failures as well as successful artifacts. All consumers receive
the same public facts, assets and ABI; free-project stages also receive the
actual public proposal/manifest schemas. The model never receives a reference
implementation, private suite, evaluator object or host tool handle.

M1 may replace a project or transactionally replace/add/remove model-owned RTL
and its manifest. A file patch binds the exact parent candidate hash. M5 may
replace a design or known behavior units bound to a build plan; changing design
invalidates all old bodies. New behavior needs another charged call. Invalid,
empty or duplicate proposals consume their model call without creating a repair
transition or unregistered early-stop rule. The last complete candidate survives
an incomplete later branch.

Only allowed files are admitted: `manifest.json`, `rtl/*.v|sv`, optional
`README.md`. Models cannot provide executable build scripts or trusted tests.
The restricted HDL subset and additional body-only restrictions are described
in the actual model prompts. Real candidate-only parsing precedes trusted TB
compilation, including a requirement-owned physical ABI check.

## Budgets and persistence

`BudgetLedger` implements reserve → durable dispatch → reconcile/cancel under
thread and OS process locks. B4 logical-call ceilings are M0=1, M1=4,
M2/M3/M4=2, M5=4; public cycles are at most 4 for M1/M5 and 1 for other
conditions. Input/output/context tokens, single output, tool calls, active/EDA
service time, CPU and memory allocations require explicit limits.

Shared operations execute once in the actual view and charge their full cost
to every consumer in the standalone view. Normal shared initial calls are
6 actual / 10 standalone; the full B4 upper bound is 11 / 15. Early failures
and skipped stages reduce actual usage; retries never create a free sample.

`used` combines observed usage with unresolved conservative reservations;
`observed` is measured consumption. Missing provider usage stays unavailable
and retains its bound. A failed request is still charged. Uncertain remote
dispatch is never automatically repeated. Source/contract/public-byte bindings
are rechecked and reopening cannot reset limits or overwrite earlier records.
Preparation also saves a content-verified archive of the actual Agent Python
and contract JSON bytes, including uncommitted files, together with the Git
revision when available. A HEAD label alone does not substitute for those bytes.
Preparation also saves a content-verified archive of the actual Agent Python
and contract JSON bytes, including uncommitted files, together with the Git
revision when available. A HEAD label alone does not substitute for those bytes.

Every external composition parser and public evaluator tool call enters a
budget hook before dispatch. Final read-only public checks and private terminal
tools have a separate explicit ledger with `final_public_tool_calls` and
`hidden_tool_calls`; they cannot create model opportunities or alter selection.
CPU/memory enforcement belongs to the qualified worker backend. Local host CPU
and peak-memory telemetry are unavailable, retained as such, and make budget
qualification `unverifiable`; these allocations are not reported as measured
CPU time or memory. Core active-time accounting covers model/tool/static
operation service, not an independently measured deployment latency.

## Isolation and terminal lifecycle

`ModelGateway` sends only detached, serialized public values through a text-only
transport. Shared-workspace coding agents are not candidate transports.
Public feedback uses the registered `pc21-public-feedback-v2` projection. It
retains the public stage verdict and fixed diagnostic codes, and adds bounded,
allowlisted diagnostic categories and hints. Failed candidate-source parsing or
compilation may identify a declared candidate-relative file and a valid source
line; trusted testbench locations and arbitrary log text are excluded. Public
functional feedback may identify a fixed failure category and public stream,
without inputs, expected/observed vectors, cycles or seeds. Hidden evaluations
cannot produce generation feedback. Raw tool output, testbench content and
private artifact paths remain evaluator-owned. The feedback revision is part
of the tool-policy identity; previous runs retain their original policy.

All model stages receive `pc21-public-guidance-v2`, the same task-independent
HDL compatibility and PC declaration rules. The PC rules distinguish logical
ports, tensor descriptor IDs and physical ABI wires; explain unique main
relation coverage and multi-output `compute`; and state the supported local
FIFO binding and capability limits. They apply when a PC is requested and
do not require Direct to return a PC or copy a particular internal topology.
The existing native-Yosys/Icarus advice covers the supported language subset,
portable constant tables and explicit combinational dependencies.

For every stage with a public task, the gateway also derives a
`public_interface_index` solely from its original entry `boundary`. The index
lists logical ports, directions, local tensor IDs and physical ABI names,
plus domain pins and parameter values. It is a read-only name aid, not a new
requirement, a proposed internal architecture or a semantic proof. Internal
modules use their own signatures. The original boundary remains authoritative.
All six methods receive the same view; both its version and actual content
enter the serialized request identity and input accounting before dispatch.
It cannot be supplied or overridden by the caller.

The [public PC tutorial](../../../tests/fixtures/pc21_public_rules/README.md)
provides small generic declarations and schema-valid semantic counterexamples.
It is an offline development aid; no task-specific reference design or behavior
body is injected into model requests.

JSON proposal stages require one JSON object without Markdown
fences. The untyped plan remains plain text. Repair proposals have a single
repair-schema root; complete-project file rules apply to file actions, while
behavior-body rules apply only to body actions. The builder owns each behavior
module's header and closing `endmodule`. These instructions do not change
strict parsing, candidate admission, oracle mathematics or acceptance rules.
The guidance and name-index revisions change model inputs. Use fresh development
records; existing frozen requests and earlier results retain their original
versions. This revision adds no model calls, retries or repair opportunities
and does not qualify a provider or authorize an experiment.

`LocalDevelopmentBackend` has `isolation_qualified=false` and no hard host
CPU/memory confinement. It is for development tests. `DockerBackend` requires a
local Linux engine, an already present image pinned by digest and successful
synthetic confinement qualification. It uses no network, non-root UID/GID,
read-only rootfs, dropped capabilities, no-new-privileges, bounded resources and
one fresh work mount. It never pulls/installs an image or forwards a remote
Docker endpoint. When unavailable or unqualified, it fails closed.
The flags follow the [Docker run reference](https://docs.docker.com/reference/cli/docker/container/run/).
The flags follow the [Docker run reference](https://docs.docker.com/reference/cli/docker/container/run/).

`finalize_batch` receives no model gateway. All planned slots across the batch
must have an immutable terminal or reasoned terminal-null before the barrier
closes. Slot identity excludes candidate hash, so changing the candidate cannot
create another score. Private semantic submission is one-shot; a repeated call
reads the original verified receipt. Unknown dispatch is not replayed. Only
explicitly bounded infrastructure retries can repeat the same frozen context.
Known public failures close their private slot without execution and preserve
the candidate and denominator. An actual integrity error stops the affected
flow and is not converted into ordinary missingness.

Final public evidence, terminal seals and private commitments are reread for
analysis export. Caller-supplied aggregate scores cannot override them. A
single-family export is a development view; joint analysis requires a complete
three-family manifest, enough independent clusters and qualified inputs.

## Entry points

```powershell
$env:PYTHONPATH = (Resolve-Path agent/src).Path
python -B -m sr2fpga_agent.execution preflight --config CONFIG.json
python -B -m sr2fpga_agent.execution preflight --config CONFIG.json --formal
```

Preflight validates the registered development configuration and selected
public files without loading a live factory, reading its credentials or
dispatching models. It checks local tool/backend prerequisites, not external
model-service behavior. `--formal` reports the unfrozen protocol, unqualified
fixed tasks and any isolation prerequisites and returns nonzero; this entry has
no official-run operation.

```powershell
python -B -m sr2fpga_agent.execution run-development --config CONFIG.json --output artifacts/paper1-ai/FRESH-RUN
```

Repeat `--config` for a same-campaign development batch. Add a trusted
`--terminal-suite-factory module:function` to evaluate terminals after the full
batch closes; the factory is imported only after generation. The supplied
`sr2fpga_agent.execution.development:terminal_suites` uses explicitly synthetic,
different development inputs and is not a formal held-out suite.

The default fixture transport needs no credentials and sends no external model
request. A live client factory additionally requires `--allow-model-calls` and
an independently authorized run scope. `gateway.create_provider_transport`
adapts the retained provider client using environment-selected credentials and
an operator-selected exact message tokenizer. No tokenizer is guessed.

For development without an available exact tokenizer,
`gateway.create_provider_capacity_transport` uses explicit provider capacities.
Its settings require `model`, `base_url`, `api_key_env`, `input_token_bound`,
`context_capacity`, `output_capacity` and `capacity_source`; both factories also
accept `wire_api`, `seed`, `reasoning_effort` and `thinking_mode` where the
provider supports them. Capacity values must come from a verified service
contract or model-capability response. The input bound must equal the full
provider context capacity, and the output capacity must not exceed it. This
mode records `tokenizer_id="unavailable"` and
`kind="provider_capacity_upper_bound"`, not an exact input token count.

The ledger reserves input capacity plus the requested output ceiling as a
conservative context envelope; configure `max_context_tokens` to accommodate
that sum. This envelope can exceed the actual provider context capacity and
does not assert that a request fits. The provider performs request admission;
returned input plus output usage is checked against its actual context
capacity. Reported usage replaces reservations, while missing usage remains
unavailable and retains the full bound. A reported capacity violation preserves
the measured usage and stops new model dispatches in the affected store. The
capacity policy and source are frozen into request and model identities.
Factory availability alone does not qualify a provider or formal execution.

For a runnable zero-model fixture, use the committed
[fixture preparation utility](../../../tests/fixtures/pc21_runtime/README.md).
Its explicit hand-authored responses remain labelled `synthetic_fixture`.

For a runnable zero-model fixture, use the committed
[fixture preparation utility](../../../tests/fixtures/pc21_runtime/README.md).
Its explicit hand-authored responses remain labelled `synthetic_fixture`.

Reusing an output is allowed only for identical frozen configuration, source,
input and replay bindings; already committed operations/results are read back.
An output reports execution closure, not candidate success. Inspect per-method
public/private outcomes and qualification states.

## Offline analysis

The [analysis package](../analysis/README.md) accepts registered
`pc21-analysis-manifest-v1`, `pc21-analysis-results-v1` and an explicit
`pc21-analysis-policy-v1`. It preserves the planned denominator, paired
configuration/replicate structure and design-cluster sampling units. The schema
fixes the current two-test Holm family at alpha 0.05; scientific effect and
missingness thresholds remain explicit policy inputs, not newly frozen values.

No result emitted by this development entry grants an official or confirmatory
claim. Original runs and released datasets are never promoted or rewritten.
