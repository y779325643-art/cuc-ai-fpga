# SR2FPGA Phase D Frozen Multi-Teacher Pilot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement and execute an auditable 24-episode, four-teacher SR2FPGA Line-B pilot with frozen paired requirements, same-source repair, explicit initial/final measurements, L0-L3 verification for every scoreable episode, and FIR-only OpenXC7 L4 labels.

**Architecture:** Keep the existing runner and agent orchestration, but add focused modules for immutable measurement freezing and paired-result aggregation. Provider transport, repair-source resolution, attempt-level measurement, and L4 selection remain additive and backward compatible. A committed secret-free example config defines the experiment, while an ignored local config supplies endpoints and environment-variable names for live execution.

**Tech Stack:** Python 3 standard library, dataclasses, JSON/YAML runner configuration, pytest, Verilator, Icarus Verilog, Yosys `synth_xilinx`, OpenXC7/nextpnr, OpenAI-compatible Chat Completions API, Anthropic-compatible Messages API with SSE.

## Global Constraints

- The fixed pilot matrix is 6 task families x 4 teachers = exactly 24 LLM episodes.
- Teachers are `claude-opus-4-8`, `gpt-5.5`, `qwen3-coder-plus`, and `deepseek-v4-pro`.
- Each family uses one frozen `simple_prompt`; all four teachers receive byte-identical requirement text for that family.
- Generation is two-stage: REQ2HIS, H0-H3, deterministic skeleton, then HIS2PROJECT behavior fill.
- The maximum is three semantic attempts: attempt 0 plus at most two same-source repair attempts.
- Transport retries never increment semantic attempt count.
- Every scoreable episode runs L0-L3. Only final L3-pass `fir_filter` episodes may run OpenXC7 L4, with a maximum of four L4 attempts.
- Vivado is out of scope for this pilot.
- A scoreable pilot requires 24/24 episodes. Infrastructure failures are retried under the same freeze and sample identity; they are not model failures.
- `not_run` is not `fail`; toolchain environment failures are reported separately from model outcomes.
- Trusted testbenches, hidden vectors, golden models, board constraints, and release metadata are not model-editable.
- Tracked files contain no API keys, authorization headers, private endpoint credentials, hidden test vectors, or vendor-restricted raw artifacts.
- Existing trajectory readers must continue to work when new fields are absent.
- The untracked `tmp/` junction directories in this worktree must never be staged or committed.

---

## File Structure

### New focused modules

- `LLM/src/sr2fpga_agent/measurement_freeze.py`: canonicalize, hash, write, and validate the immutable experiment manifest without secrets.
- `LLM/src/sr2fpga_agent/paired_measurement.py`: normalize attempt outcomes and aggregate four-teacher paired results by requirement and family.
- `scripts/audit_phase_d_pilot.py`: independently audit the completed run against the Phase D acceptance gates.
- `LLM/tests/test_sr2fpga_measurement_freeze.py`: freeze redaction, fingerprint, mismatch, and resume tests.
- `LLM/tests/test_sr2fpga_paired_measurement.py`: initial/final outcome and paired aggregation tests.
- `LLM/tests/test_sr2fpga_phase_d_audit.py`: acceptance-audit tests using synthetic run artifacts.
- `configs/current/sr2fpga_phase_d_multiteacher_pilot.example.yaml`: committed secret-free 24-episode experiment definition.
- `configs/current/sr2fpga_phase_d_control.example.yaml`: committed six-family deterministic B_ref control definition.
- `docs/results/2026-07-17-sr2fpga-phase-d-pilot-report.md`: artifact-grounded live-run report, created only after execution.

### Existing files modified

- `LLM/src/sr2fpga_agent/providers.py`: implement Anthropic Messages SSE and preserve retry semantics.
- `LLM/src/sr2fpga_agent/runner.py`: resolve same-source repair per sample, create/validate freeze manifest, emit paired IDs, enforce FIR-only L4 selection, and write paired results.
- `LLM/src/sr2fpga_agent/agent.py`: record initial/final attempt measurements without changing official verdict semantics.
- `LLM/src/sr2fpga_agent/recorder.py`: preserve additive measurement and paired metadata in episode/training exports.
- `LLM/src/sr2fpga_agent/baseline_report.py`: render Phase D paired initial/final summaries.
- `LLM/tests/test_sr2fpga_agent_multi_teacher.py`: provider SSE and source-resolution tests.
- `LLM/tests/test_sr2fpga_agent_runner.py`: 24-matrix, freeze integration, same-source repair, and L4 allowlist tests.
- `LLM/tests/test_sr2fpga_agent_recorder.py`: additive trajectory/export compatibility tests.
- `LLM/tests/test_sr2fpga_agent_baseline_report.py`: paired report rendering tests.
- `docs/current-status.md`: record implementation and live-run status after evidence exists.

---

### Task 1: Anthropic Messages SSE Transport And Streaming Preflight

**Files:**
- Modify: `LLM/src/sr2fpga_agent/providers.py:143-190`
- Modify: `LLM/src/sr2fpga_agent/runner.py:540-575`
- Test: `LLM/tests/test_sr2fpga_agent_multi_teacher.py`
- Test: `LLM/tests/test_sr2fpga_agent_runner.py`

**Interfaces:**
- Consumes: `AnthropicCompatibleConfig`, `_response_read_deadline()`, transient retry policy, and the existing provider `stream_chat(messages)` protocol.
- Produces: `_read_anthropic_streaming_text(response: Any, timeout_seconds: int) -> str`; `AnthropicCompatibleClient.stream_chat(messages: list[dict[str, str]]) -> str`; streaming provider preflight through the same path used by generation.

- [ ] **Step 1: Add failing Anthropic SSE parser tests**

Add a fake line-oriented response and the following cases to `test_sr2fpga_agent_multi_teacher.py`:

```python
class _SseResponse:
    def __init__(self, lines: list[bytes]) -> None:
        self._lines = lines

    def readline(self) -> bytes:
        return self._lines.pop(0) if self._lines else b""


def test_anthropic_stream_reader_collects_text_deltas() -> None:
    response = _SseResponse([
        b"event: content_block_delta\n",
        b'data: {"type":"content_block_delta","delta":{"type":"text_delta","text":"{\\"ok\\":"}}\n',
        b"\n",
        b"event: content_block_delta\n",
        b'data: {"type":"content_block_delta","delta":{"type":"text_delta","text":"true}"}}\n',
        b"\n",
        b"event: message_stop\n",
        b'data: {"type":"message_stop"}\n',
        b"\n",
    ])
    assert providers._read_anthropic_streaming_text(response, 5) == '{"ok":true}'


def test_anthropic_stream_reader_surfaces_error_event() -> None:
    response = _SseResponse([
        b"event: error\n",
        b'data: {"type":"error","error":{"type":"overloaded_error","message":"busy"}}\n',
        b"\n",
    ])
    with pytest.raises(RuntimeError, match="overloaded_error.*busy"):
        providers._read_anthropic_streaming_text(response, 5)
```

- [ ] **Step 2: Run the parser tests and verify the new helper is missing**

Run:

```powershell
python -m pytest LLM/tests/test_sr2fpga_agent_multi_teacher.py -k "anthropic_stream_reader" -q
```

Expected: FAIL because `_read_anthropic_streaming_text` does not exist.

- [ ] **Step 3: Implement the minimal Anthropic SSE reader and reader-aware retry path**

In `providers.py`, parse only standard Anthropic text deltas, stop on `message_stop`, and reject empty streams:

```python
def _read_anthropic_streaming_text(response: Any, timeout_seconds: int) -> str:
    chunks: list[str] = []
    event_name = ""
    while True:
        raw = response.readline()
        if not raw:
            break
        line = raw.decode("utf-8", errors="replace").strip()
        if line.startswith("event:"):
            event_name = line[6:].strip()
            continue
        if not line.startswith("data:"):
            continue
        payload = json.loads(line[5:].strip())
        event_type = str(payload.get("type") or event_name)
        if event_type == "content_block_delta":
            delta = payload.get("delta") or {}
            if delta.get("type") == "text_delta":
                chunks.append(str(delta.get("text", "")))
        elif event_type == "error":
            error = payload.get("error") or {}
            raise RuntimeError(f"{error.get('type', 'error')}: {error.get('message', '')}")
        elif event_type == "message_stop":
            break
    text = "".join(chunks)
    if not text:
        raise RuntimeError("Anthropic-compatible streaming response contained no text")
    return text
```

Refactor Anthropic request functions to accept a reader exactly as the OpenAI-compatible client does, set `payload["stream"] = True` in `stream_chat`, and wrap the reader in `_response_read_deadline()`.

- [ ] **Step 4: Add failing tests that prove `stream_chat` sends `stream=true` and retries transport without duplicating semantic attempts**

Patch `urllib.request.urlopen` with one transient 502 followed by a valid SSE response. Assert two HTTP calls, `stream` true in both request bodies, and one returned string.

- [ ] **Step 5: Change runner provider preflight to call `stream_chat`**

Use the existing valid JSON preflight messages:

```python
messages = [
    {"role": "system", "content": "Return a tiny JSON object for authentication preflight."},
    {"role": "user", "content": 'Return {"ok": true}.'},
]
response = client.stream_chat(messages)
json.loads(response)
```

The preflight must validate the actual long-generation transport rather than the non-streaming shortcut.

- [ ] **Step 6: Run focused provider and runner tests**

Run:

```powershell
python -m pytest LLM/tests/test_sr2fpga_agent_multi_teacher.py LLM/tests/test_sr2fpga_agent_runner.py -k "anthropic or source_auth" -q
```

Expected: PASS.

- [ ] **Step 7: Commit the provider transport change**

```powershell
git add LLM/src/sr2fpga_agent/providers.py LLM/src/sr2fpga_agent/runner.py LLM/tests/test_sr2fpga_agent_multi_teacher.py LLM/tests/test_sr2fpga_agent_runner.py
git commit -m "fix: stream anthropic-compatible generation"
```

---

### Task 2: Per-Sample Same-Source Repair Resolution

**Files:**
- Modify: `LLM/src/sr2fpga_agent/runner.py:48-116,314-410,1868-1915`
- Test: `LLM/tests/test_sr2fpga_agent_runner.py`

**Interfaces:**
- Consumes: `RunnerConfig.source_connections`, `PlannedSample.source`, and the existing `_repairer_for_config()` provider construction behavior.
- Produces: `_repairer_for_sample(cache: dict[str, object | None], config: RunnerConfig, sample: PlannedSample) -> object | None`; accepted `repair_provider` values `none`, a named source, or `same_as_source`.

- [ ] **Step 1: Add failing config and resolver tests**

Add tests asserting:

```python
def test_same_as_source_repair_uses_each_samples_teacher(tmp_path: Path) -> None:
    config = _runner_config(
        repair_provider="same_as_source",
        sources=[_source("gpt"), _source("claude")],
    )
    cache: dict[str, object | None] = {}
    gpt = runner._repairer_for_sample(cache, config, _planned_sample(source="gpt"))
    claude = runner._repairer_for_sample(cache, config, _planned_sample(source="claude"))
    assert gpt is not None
    assert claude is not None
    assert gpt is not claude
    assert set(cache) == {"gpt", "claude"}


def test_same_as_source_repair_is_none_for_deterministic_sample() -> None:
    config = _runner_config(repair_provider="same_as_source")
    sample = _planned_sample(source="deterministic")
    assert runner._repairer_for_sample({}, config, sample) is None
```

Also assert that auth diagnostics do not try to resolve a literal provider named `same_as_source`.

- [ ] **Step 2: Run the resolver tests and verify failure**

Run:

```powershell
python -m pytest LLM/tests/test_sr2fpga_agent_runner.py -k "same_as_source" -q
```

Expected: FAIL because the per-sample resolver is absent.

- [ ] **Step 3: Implement cached per-sample repair resolution**

Add the minimal resolver:

```python
def _repairer_for_sample(
    cache: dict[str, object | None],
    config: RunnerConfig,
    sample: PlannedSample,
) -> object | None:
    provider_name = config.repair_provider
    if provider_name == "same_as_source":
        provider_name = sample.source
    if provider_name in {"", "none", "deterministic"}:
        return None
    if provider_name not in cache:
        connection = resolve_source_connection(config, provider_name)
        cache[provider_name] = build_repairer_for_connection(connection)
    return cache[provider_name]
```

Use one cache in `run_batch()` and resolve before constructing each `DataGenerationAgent`. Store both policy and resolved source in sample metadata:

```json
{
  "repair_provider_policy": "same_as_source",
  "repair_provider_resolved": "gpt"
}
```

- [ ] **Step 4: Make measurement-point classification understand same-source repair**

`_measurement_point()` returns `b` whenever `max_attempts > 1` and the repair policy is not `none`; it must not require a globally named provider.

- [ ] **Step 5: Add a mocked two-source integration test**

Create two planned samples with distinct fake generator clients. Make attempt 0 fail L2 and repair succeed. Assert each repair call is received by its originating source and no cross-source calls occur.

- [ ] **Step 6: Run focused tests**

```powershell
python -m pytest LLM/tests/test_sr2fpga_agent_runner.py -k "same_as_source or repair_provider or measurement_point" -q
```

Expected: PASS.

- [ ] **Step 7: Commit same-source repair**

```powershell
git add LLM/src/sr2fpga_agent/runner.py LLM/tests/test_sr2fpga_agent_runner.py
git commit -m "feat: resolve repair from each sample source"
```

---

### Task 3: Paired Requirement Identity And Frozen 24-Episode Matrix

**Files:**
- Modify: `LLM/src/sr2fpga_agent/runner.py:120-157,1516-1605`
- Create: `configs/current/sr2fpga_phase_d_multiteacher_pilot.example.yaml`
- Create: `configs/current/sr2fpga_phase_d_control.example.yaml`
- Test: `LLM/tests/test_sr2fpga_agent_runner.py`

**Interfaces:**
- Consumes: deterministic requirement rendering in `planned_samples()` and the six approved runner task/topology identifiers.
- Produces: `PlannedSample.paired_requirement_id: str`; `PlannedSample.requirement_sha256: str`; exactly 24 LLM samples with four identical hashes per family.

- [ ] **Step 1: Add failing paired-identity unit tests**

Add assertions that the identity excludes source/model but includes family and requirement bytes:

```python
def test_paired_requirement_identity_is_source_independent() -> None:
    samples = runner.planned_samples(_phase_d_four_source_config())
    fir = [sample for sample in samples if sample.family_id == "fir_filter"]
    assert len(fir) == 4
    assert len({sample.requirement for sample in fir}) == 1
    assert len({sample.requirement_sha256 for sample in fir}) == 1
    assert len({sample.paired_requirement_id for sample in fir}) == 1
    assert len({sample.source for sample in fir}) == 4
```

- [ ] **Step 2: Run the paired-identity test and verify failure**

```powershell
python -m pytest LLM/tests/test_sr2fpga_agent_runner.py -k "paired_requirement_identity" -q
```

Expected: FAIL because the fields do not exist.

- [ ] **Step 3: Add deterministic identity helpers and metadata**

Implement:

```python
def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _paired_requirement_id(family_id: str, requirement_sha256: str) -> str:
    return f"{family_id}:{requirement_sha256[:16]}"
```

Compute both after rendering each requirement. Add them as frozen `PlannedSample` fields and return them from `PlannedSample.metadata()`.

- [ ] **Step 4: Create the committed secret-free pilot config**

The config must explicitly enumerate these 24 rows, all with `requirement_style: simple_prompt` and four source aliases per family:

```yaml
dataset_root: datasets/sr2fpga_phase_d_v1
export_root: datasets/sr2fpga_phase_d_v1_exports
run_root: tmp/sr2fpga_runs
provider: deterministic
max_attempts: 3
repair_provider: same_as_source
platform: generic_verilog
refresh_exports: true
sample_id_prefix: phase_d
env_file: ""
line_b_targets:
  l3_success_ratio: 0.0
  repair_trajectory_ratio: 0.0
  max_samples: 24
sources:
  claude:
    kind: anthropic_compat
    model: claude-opus-4-8
    base_url: https://example.invalid/v1
    api_key_env: ANTHROPIC_API_KEY
    generation_mode: two_stage
    timeout_seconds: 600
    transport_attempts: 3
    max_tokens: 32768
  gpt:
    kind: openai_compat
    model: gpt-5.5
    base_url: https://example.invalid/v1
    api_key_env: OPENAI_API_KEY
    generation_mode: two_stage
    timeout_seconds: 600
    transport_attempts: 3
    max_tokens: 32768
  qwen:
    kind: openai_compat
    model: qwen3-coder-plus
    base_url: https://example.invalid/v1
    api_key_env: DASHSCOPE_API_KEY
    generation_mode: two_stage
    timeout_seconds: 600
    transport_attempts: 3
    max_tokens: 32768
  deepseek:
    kind: deepseek-his-v12
    model: deepseek-v4-pro
    base_url: https://example.invalid/v1
    api_key_env: DEEPSEEK_API_KEY
    generation_mode: two_stage
    timeout_seconds: 600
    transport_attempts: 3
    max_tokens: 32768
run_l4_open: true
l4_open:
  run_policy: representative_subset
  family_ids: [fir_filter]
  timeout_seconds: 600
tasks:
  - {source: claude, task_type: fifo, widths: [8], count: 1, requirement_style: simple_prompt, evaluation_line: line_b, failure_origin: natural_llm, failure_injectors: []}
  - {source: gpt, task_type: fifo, widths: [8], count: 1, requirement_style: simple_prompt, evaluation_line: line_b, failure_origin: natural_llm, failure_injectors: []}
  - {source: qwen, task_type: fifo, widths: [8], count: 1, requirement_style: simple_prompt, evaluation_line: line_b, failure_origin: natural_llm, failure_injectors: []}
  - {source: deepseek, task_type: fifo, widths: [8], count: 1, requirement_style: simple_prompt, evaluation_line: line_b, failure_origin: natural_llm, failure_injectors: []}
  - {source: claude, task_type: component_topology, topology_ids: [t2_stream_accumulator], widths: [8], count: 1, requirement_style: simple_prompt, evaluation_line: line_b, failure_origin: natural_llm, failure_injectors: []}
  - {source: gpt, task_type: component_topology, topology_ids: [t2_stream_accumulator], widths: [8], count: 1, requirement_style: simple_prompt, evaluation_line: line_b, failure_origin: natural_llm, failure_injectors: []}
  - {source: qwen, task_type: component_topology, topology_ids: [t2_stream_accumulator], widths: [8], count: 1, requirement_style: simple_prompt, evaluation_line: line_b, failure_origin: natural_llm, failure_injectors: []}
  - {source: deepseek, task_type: component_topology, topology_ids: [t2_stream_accumulator], widths: [8], count: 1, requirement_style: simple_prompt, evaluation_line: line_b, failure_origin: natural_llm, failure_injectors: []}
  - {source: claude, task_type: component_topology, topology_ids: [t4_dual_stream_join], widths: [8], count: 1, requirement_style: simple_prompt, evaluation_line: line_b, failure_origin: natural_llm, failure_injectors: []}
  - {source: gpt, task_type: component_topology, topology_ids: [t4_dual_stream_join], widths: [8], count: 1, requirement_style: simple_prompt, evaluation_line: line_b, failure_origin: natural_llm, failure_injectors: []}
  - {source: qwen, task_type: component_topology, topology_ids: [t4_dual_stream_join], widths: [8], count: 1, requirement_style: simple_prompt, evaluation_line: line_b, failure_origin: natural_llm, failure_injectors: []}
  - {source: deepseek, task_type: component_topology, topology_ids: [t4_dual_stream_join], widths: [8], count: 1, requirement_style: simple_prompt, evaluation_line: line_b, failure_origin: natural_llm, failure_injectors: []}
  - {source: claude, task_type: fir_filter, widths: [8], count: 1, requirement_style: simple_prompt, evaluation_line: line_b, failure_origin: natural_llm, failure_injectors: []}
  - {source: gpt, task_type: fir_filter, widths: [8], count: 1, requirement_style: simple_prompt, evaluation_line: line_b, failure_origin: natural_llm, failure_injectors: []}
  - {source: qwen, task_type: fir_filter, widths: [8], count: 1, requirement_style: simple_prompt, evaluation_line: line_b, failure_origin: natural_llm, failure_injectors: []}
  - {source: deepseek, task_type: fir_filter, widths: [8], count: 1, requirement_style: simple_prompt, evaluation_line: line_b, failure_origin: natural_llm, failure_injectors: []}
  - {source: claude, task_type: sobel_threshold, widths: [8], count: 1, requirement_style: simple_prompt, evaluation_line: line_b, failure_origin: natural_llm, failure_injectors: []}
  - {source: gpt, task_type: sobel_threshold, widths: [8], count: 1, requirement_style: simple_prompt, evaluation_line: line_b, failure_origin: natural_llm, failure_injectors: []}
  - {source: qwen, task_type: sobel_threshold, widths: [8], count: 1, requirement_style: simple_prompt, evaluation_line: line_b, failure_origin: natural_llm, failure_injectors: []}
  - {source: deepseek, task_type: sobel_threshold, widths: [8], count: 1, requirement_style: simple_prompt, evaluation_line: line_b, failure_origin: natural_llm, failure_injectors: []}
  - {source: claude, task_type: component_topology, topology_ids: [t6_td_update_core], widths: [8], count: 1, requirement_style: simple_prompt, evaluation_line: line_b, failure_origin: natural_llm, failure_injectors: []}
  - {source: gpt, task_type: component_topology, topology_ids: [t6_td_update_core], widths: [8], count: 1, requirement_style: simple_prompt, evaluation_line: line_b, failure_origin: natural_llm, failure_injectors: []}
  - {source: qwen, task_type: component_topology, topology_ids: [t6_td_update_core], widths: [8], count: 1, requirement_style: simple_prompt, evaluation_line: line_b, failure_origin: natural_llm, failure_injectors: []}
  - {source: deepseek, task_type: component_topology, topology_ids: [t6_td_update_core], widths: [8], count: 1, requirement_style: simple_prompt, evaluation_line: line_b, failure_origin: natural_llm, failure_injectors: []}
```

The full file also sets `dataset_root`, `export_root`, `run_root`, `platform`, `refresh_exports`, `sample_id_prefix`, and `line_b_targets` using the same field names as existing committed runner configs. The committed source table deliberately uses `example.invalid`; the ignored local config replaces it with the user's gateway endpoint. No real endpoint or API key value is committed. The six families and runner mappings are:

```text
sync_fifo -> task_type fifo
valid_ready_stream_accumulator -> topology t2_stream_accumulator
stream_fork_join -> topology t4_dual_stream_join
fir_filter -> task_type fir_filter
sobel_threshold -> task_type sobel_threshold
qtable_update_core -> topology t6_td_update_core
```

- [ ] **Step 5: Create the six-family deterministic control config**

Use the same family parameters, prompts, tool timeouts, and L4 FIR allowlist, but `source: deterministic`, `max_attempts: 1`, and no model repair. Controls are separate from and do not count toward the 24 LLM episodes.

- [ ] **Step 6: Add config expansion tests**

Load both committed configs and assert:

```python
assert len(runner.planned_samples(pilot)) == 24
assert len({sample.family_id for sample in runner.planned_samples(pilot)}) == 6
assert Counter(sample.source for sample in runner.planned_samples(pilot)) == {
    "claude": 6,
    "gpt": 6,
    "qwen": 6,
    "deepseek": 6,
}
assert len(runner.planned_samples(control)) == 6
```

For every family, assert four equal requirement hashes.

- [ ] **Step 7: Run config and pairing tests**

```powershell
python -m pytest LLM/tests/test_sr2fpga_agent_runner.py -k "phase_d or paired_requirement" -q
```

Expected: PASS.

- [ ] **Step 8: Commit the frozen experiment matrix**

```powershell
git add LLM/src/sr2fpga_agent/runner.py LLM/tests/test_sr2fpga_agent_runner.py configs/current/sr2fpga_phase_d_multiteacher_pilot.example.yaml configs/current/sr2fpga_phase_d_control.example.yaml
git commit -m "feat: define phase d paired sample matrix"
```

---

### Task 4: Immutable Measurement-Freeze Manifest And Resume Gate

**Files:**
- Create: `LLM/src/sr2fpga_agent/measurement_freeze.py`
- Create: `LLM/tests/test_sr2fpga_measurement_freeze.py`
- Modify: `LLM/src/sr2fpga_agent/runner.py:242-410`
- Test: `LLM/tests/test_sr2fpga_agent_runner.py`

**Interfaces:**
- Consumes: config fingerprint, planned sample dictionaries, source model metadata, tool versions, timeout policy, repair budget, and L4 selection policy.
- Produces: `build_measurement_freeze(...) -> dict[str, Any]`; `freeze_fingerprint(manifest: dict[str, Any]) -> str`; `write_or_validate_freeze(path: Path, manifest: dict[str, Any], *, resume: bool) -> str`; run-level `measurement_freeze.json`.

- [ ] **Step 1: Write failing canonicalization and secret-rejection tests**

Create `test_sr2fpga_measurement_freeze.py` with:

```python
def test_freeze_fingerprint_ignores_mapping_order() -> None:
    left = {"models": {"gpt": "gpt-5.5", "claude": "claude-opus-4-8"}, "seed": 7}
    right = {"seed": 7, "models": {"claude": "claude-opus-4-8", "gpt": "gpt-5.5"}}
    assert freeze_fingerprint(left) == freeze_fingerprint(right)


@pytest.mark.parametrize("field", ["api_key", "authorization", "access_token", "client_secret"])
def test_measurement_freeze_rejects_secret_fields(field: str) -> None:
    with pytest.raises(ValueError, match="secret-like field"):
        build_measurement_freeze(
            run_id="phase-d",
            config_fingerprint="abc",
            sample_records=[],
            source_records=[{"name": "gpt", field: "forbidden"}],
            max_attempts=3,
            timeouts={"generation": 600},
            tool_versions={},
            l4_family_ids=["fir_filter"],
        )
```

- [ ] **Step 2: Run the new tests and verify module-not-found failure**

```powershell
python -m pytest LLM/tests/test_sr2fpga_measurement_freeze.py -q
```

Expected: FAIL because the module does not exist.

- [ ] **Step 3: Implement canonical JSON, secret scan, and manifest construction**

Use sorted compact JSON for hashing:

```python
def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def freeze_fingerprint(manifest: dict[str, Any]) -> str:
    payload = {key: value for key, value in manifest.items() if key != "freeze_fingerprint"}
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()
```

The manifest contains only stable experiment facts:

```json
{
  "schema_version": "sr2fpga-phase-d-freeze-v1",
  "run_id": "...",
  "config_fingerprint": "...",
  "sample_count": 24,
  "samples": [],
  "sources": [],
  "max_attempts": 3,
  "timeouts": {},
  "tool_versions": {},
  "l4_family_ids": ["fir_filter"],
  "freeze_fingerprint": "..."
}
```

Source records include alias, provider kind, and model ID only. They exclude API keys, resolved authorization, hidden vectors, and credential-bearing URLs.

- [ ] **Step 4: Implement write-once and resume-exact-match behavior**

```python
def write_or_validate_freeze(path: Path, manifest: dict[str, Any], *, resume: bool) -> str:
    fingerprint = freeze_fingerprint(manifest)
    frozen = {**manifest, "freeze_fingerprint": fingerprint}
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing != frozen:
            raise RuntimeError("measurement freeze mismatch; refusing to resume")
        return fingerprint
    if resume:
        raise RuntimeError("measurement freeze missing; refusing to resume")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(frozen, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return fingerprint
```

In `run_batch()`, capture `existing_run = state_path.exists()` before initializing run state and pass `resume=resume and existing_run` to this function. A default runner invocation with a new run ID therefore writes a fresh freeze; only a real resume requires an existing matching freeze.

- [ ] **Step 5: Add runner integration tests before changing runner**

Assert the runner writes the freeze before the first fake LLM call. Record event order in a list and check `freeze_written` precedes `provider_called`. Add resume tests that reject changed model ID, changed prompt/hash, changed repair budget, and changed L4 allowlist.

- [ ] **Step 6: Integrate freeze creation into `run_batch()`**

Build the manifest after planning/preflight and before constructing the first live agent. On a fresh run, write it. On resume, require byte-equivalent normalized content. Add the freeze fingerprint to every sample metadata block and top-level summary.

- [ ] **Step 7: Run freeze and runner tests**

```powershell
python -m pytest LLM/tests/test_sr2fpga_measurement_freeze.py LLM/tests/test_sr2fpga_agent_runner.py -k "freeze or phase_d" -q
```

Expected: PASS.

- [ ] **Step 8: Commit the freeze gate**

```powershell
git add LLM/src/sr2fpga_agent/measurement_freeze.py LLM/src/sr2fpga_agent/runner.py LLM/tests/test_sr2fpga_measurement_freeze.py LLM/tests/test_sr2fpga_agent_runner.py
git commit -m "feat: freeze phase d measurement protocol"
```

---

### Task 5: Attempt-Level Initial/Final Measurement And Paired Reporting

**Files:**
- Create: `LLM/src/sr2fpga_agent/paired_measurement.py`
- Create: `LLM/tests/test_sr2fpga_paired_measurement.py`
- Modify: `LLM/src/sr2fpga_agent/agent.py:105-555,977-1090,1362-1405`
- Modify: `LLM/src/sr2fpga_agent/recorder.py`
- Modify: `LLM/src/sr2fpga_agent/runner.py:314-510`
- Modify: `LLM/src/sr2fpga_agent/baseline_report.py`
- Test: `LLM/tests/test_sr2fpga_agent_recorder.py`
- Test: `LLM/tests/test_sr2fpga_agent_baseline_report.py`

**Interfaces:**
- Consumes: attempt stage entries, H0-H3 validation, L0-L4 tool results, patch metadata, paired IDs, and final episode metadata.
- Produces: `raw_pass_level(...) -> str`; `build_episode_measurement(...) -> dict[str, Any]`; `collect_paired_results(dataset_root: Path) -> dict[str, Any]`; `paired_results.json`; additive `trajectory.measurement`.

- [ ] **Step 1: Add failing raw pass-level and episode measurement tests**

Create tests for three cases:

```python
def test_episode_measurement_records_a_and_b() -> None:
    attempts = [
        {"attempt_id": 0, "pass_level": "L1", "failure_type": "simulation_mismatch"},
        {"attempt_id": 1, "pass_level": "L3", "failure_type": "none"},
    ]
    result = build_episode_measurement(attempts=attempts, patches=[{"regressions": []}])
    assert result["initial"]["attempt_id"] == 0
    assert result["initial"]["pass_level"] == "L1"
    assert result["final"]["attempt_id"] == 1
    assert result["final"]["pass_level"] == "L3"
    assert result["repair_attempts_used"] == 1
    assert result["repair_success"] is True
    assert result["regressions"] == []


def test_episode_measurement_keeps_unrepaired_failure_scoreable() -> None:
    result = build_episode_measurement(
        attempts=[{"attempt_id": 0, "pass_level": "L0", "failure_type": "contract_mismatch"}],
        patches=[],
    )
    assert result["initial"] == result["final"]
    assert result["repair_success"] is False
```

Also test H-stage levels and L4-open separately from highest official L0-L3 level.

- [ ] **Step 2: Run paired-measurement tests and verify module-not-found failure**

```powershell
python -m pytest LLM/tests/test_sr2fpga_paired_measurement.py -q
```

Expected: FAIL.

- [ ] **Step 3: Extract a reusable raw pass-level helper from `_labels()`**

Implement in `agent.py`:

```python
def _raw_tool_pass_level(
    tool_results: dict[str, ToolResult],
    his_validation: dict[str, Any] | None,
) -> str:
    failed_h_stage = first_failed_h_stage(his_validation) if his_validation is not None else None
    if failed_h_stage:
        return f"{failed_h_stage.upper()}_FAIL"
    l0 = tool_results.get("l0_consistency")
    if l0 is not None and l0.status != "passed":
        return "L0_FAIL"
    lint = tool_results.get("lint")
    if lint is None or lint.status != "passed":
        return "L0"
    sim_compile = tool_results.get("sim_compile")
    sim_run = tool_results.get("sim_run")
    if sim_compile is None or sim_compile.status != "passed" or sim_run is None or sim_run.status != "passed":
        return "L1"
    synth = tool_results.get("synth")
    if synth is None or synth.status != "passed":
        return "L2"
    return "L3"
```

Reuse this helper in final `_labels()` so initial and final calculations cannot drift.

- [ ] **Step 4: Implement `build_episode_measurement()`**

The output schema is:

```json
{
  "initial": {
    "attempt_id": 0,
    "pass_level": "L1",
    "failure_type": "simulation_mismatch",
    "automatic_pass_credit": false
  },
  "final": {
    "attempt_id": 1,
    "pass_level": "L3",
    "failure_type": "none",
    "automatic_pass_credit": true
  },
  "repair_attempts_used": 1,
  "repair_success": true,
  "regressions": [],
  "l4_open": {"status": "not_run", "skip_reason": "not_selected_by_policy"}
}
```

No repair opportunity is not an infrastructure failure. Record `repair_eligible` and `repair_skip_reason` when H-stage or edit-surface policy prevents repair.

- [ ] **Step 5: Populate attempt measurements inside `DataGenerationAgent.run_one()`**

After each attempt has H/tool results and diagnosis, append:

```python
attempt_measurements.append({
    "attempt_id": attempt_id,
    "pass_level": _raw_tool_pass_level(tool_results, his_validation),
    "failure_type": (diagnosis or {}).get("failure_type", "none"),
    "automatic_pass_credit": not oracle_infrastructure_failure,
})
```

At episode finalization, set `trajectory["measurement"] = build_episode_measurement(...)`. Keep all existing `attempts` and labels unchanged.

- [ ] **Step 6: Add recorder backward-compatibility tests**

Write one episode with the new measurement block and one legacy episode without it. Assert both export successfully; the new training rows carry `paired_requirement_id`, `requirement_sha256`, and `freeze_fingerprint` when available.

- [ ] **Step 7: Implement paired aggregation**

`collect_paired_results()` must group only by `paired_requirement_id`, require four distinct teacher aliases, and emit:

```json
{
  "schema_version": "sr2fpga-phase-d-paired-v1",
  "episode_count": 24,
  "pair_count": 6,
  "complete_pairs": 6,
  "infrastructure_outcomes": {},
  "pairs": [],
  "by_source": {},
  "by_family": {},
  "initial_vs_final": {}
}
```

Each pair contains the shared requirement hash and four source outcomes. Reject duplicate source rows or mismatched requirement hashes within a pair.

- [ ] **Step 8: Write `paired_results.json` and render report section**

After batch completion, write `paired_results.json` under the run root. Extend `baseline_report.md` with:

```text
Phase D Paired Pilot
Initial (a) vs Final (b)
Per-source L0-L3 survival
Per-family L0-L3 survival
Repair success and regression counts
Infrastructure outcomes excluded from model denominators
FIR OpenXC7 L4 pass/fail/not_run
```

- [ ] **Step 9: Run focused measurement, recorder, and report tests**

```powershell
python -m pytest LLM/tests/test_sr2fpga_paired_measurement.py LLM/tests/test_sr2fpga_agent_recorder.py LLM/tests/test_sr2fpga_agent_baseline_report.py LLM/tests/test_sr2fpga_agent_runner.py -k "measurement or paired or phase_d" -q
```

Expected: PASS.

- [ ] **Step 10: Commit paired measurement and reporting**

```powershell
git add LLM/src/sr2fpga_agent/paired_measurement.py LLM/src/sr2fpga_agent/agent.py LLM/src/sr2fpga_agent/recorder.py LLM/src/sr2fpga_agent/runner.py LLM/src/sr2fpga_agent/baseline_report.py LLM/tests/test_sr2fpga_paired_measurement.py LLM/tests/test_sr2fpga_agent_recorder.py LLM/tests/test_sr2fpga_agent_baseline_report.py LLM/tests/test_sr2fpga_agent_runner.py
git commit -m "feat: record paired initial and repaired outcomes"
```

---

### Task 6: FIR-Only L4 Selection And Phase D Integrity Audit

**Files:**
- Modify: `LLM/src/sr2fpga_agent/runner.py:75-81,1370-1405`
- Create: `scripts/audit_phase_d_pilot.py`
- Create: `LLM/tests/test_sr2fpga_phase_d_audit.py`
- Modify: `LLM/tests/test_sr2fpga_agent_runner.py`

**Interfaces:**
- Consumes: `L4OpenConfig.family_ids`, planned sample family IDs, final L3 status, run artifacts, measurement freeze, and paired results.
- Produces: FIR-only `_l4_open_enabled_for_sample()` behavior; `audit_run(run_root: Path) -> dict[str, Any]`; machine-readable `phase_d_audit.json`; process exit 0 only for `APPROVED`.

- [ ] **Step 1: Add failing L4 allowlist tests**

```python
def test_phase_d_l4_allowlist_selects_only_fir() -> None:
    config = _runner_config(l4_family_ids=["fir_filter"])
    assert runner._l4_open_enabled_for_sample(config, _planned_sample(family_id="fir_filter"))
    assert not runner._l4_open_enabled_for_sample(config, _planned_sample(family_id="sobel_threshold"))
```

At agent integration level, assert an L2-failing FIR receives `status=not_run` and `skip_reason=l3_failed`.

- [ ] **Step 2: Implement the explicit family allowlist**

Add `family_ids: tuple[str, ...] = ()` to `L4OpenConfig`. The matrix contains exactly four FIR episodes, so the allowlist itself bounds the pilot to four possible L4 runs. Selection order is:

```text
disabled -> disabled_by_config
family not in explicit allowlist -> not_selected_by_policy
final L3 not passed -> l3_failed
otherwise run OpenXC7
```

Do not use catalog `representative_subset` policy when an explicit allowlist is present.

- [ ] **Step 3: Write failing audit tests with one valid and several invalid synthetic runs**

The valid fixture has 24 episodes, 6 complete four-source pairs, one freeze fingerprint, at most four FIR L4 records, no secrets, no trusted artifact edits, and no infrastructure outcomes. Invalid fixtures independently test:

```text
23 episodes
duplicate teacher in a pair
requirement hash mismatch
freeze fingerprint mismatch
non-FIR L4 run
more than four L4 runs
trusted artifact touched
secret-like key/value in tracked evidence
infrastructure outcome left unresolved
missing raw OpenXC7 report path for an L4 verdict
```

- [ ] **Step 4: Run audit tests and verify module/script failure**

```powershell
python -m pytest LLM/tests/test_sr2fpga_phase_d_audit.py -q
```

Expected: FAIL because the audit script is absent.

- [ ] **Step 5: Implement the audit as a pure function plus CLI**

The audit result is:

```json
{
  "verdict": "APPROVED",
  "checks": {
    "scoreable_episode_count": {"pass": true, "actual": 24, "expected": 24},
    "complete_pairs": {"pass": true, "actual": 6, "expected": 6},
    "freeze_consistency": {"pass": true},
    "same_requirement_per_pair": {"pass": true},
    "same_source_repair": {"pass": true},
    "fir_only_l4": {"pass": true},
    "trusted_artifacts_untouched": {"pass": true},
    "no_secret_material": {"pass": true},
    "infrastructure_resolved": {"pass": true}
  },
  "blocking_findings": []
}
```

The CLI accepts `--run-root` and `--output`. It prints the verdict and exits 1 on `NOT APPROVED`.

- [ ] **Step 6: Run focused L4 and audit tests**

```powershell
python -m pytest LLM/tests/test_sr2fpga_agent_runner.py LLM/tests/test_sr2fpga_phase_d_audit.py -k "l4 or phase_d or audit" -q
```

Expected: PASS.

- [ ] **Step 7: Commit L4 selection and audit gate**

```powershell
git add LLM/src/sr2fpga_agent/runner.py scripts/audit_phase_d_pilot.py LLM/tests/test_sr2fpga_agent_runner.py LLM/tests/test_sr2fpga_phase_d_audit.py
git commit -m "feat: audit phase d pilot integrity"
```

---

### Task 7: Mocked End-To-End Phase D Verification

**Files:**
- Modify: `LLM/tests/test_sr2fpga_agent_runner.py`
- Modify: `docs/superpowers/specs/2026-07-17-sr2fpga-phase-d-frozen-multiteacher-pilot-design.md`

**Interfaces:**
- Consumes: all Tasks 1-6 interfaces.
- Produces: one network-free 24-episode integration test and an updated design note documenting Anthropic SSE as a live transport prerequisite.

- [ ] **Step 1: Add a network-free 24-episode integration test**

Use four fake source clients, deterministic tool results, and a temporary run root. Program six attempt-0 failures to be repaired and eighteen initial passes. Assert:

```python
assert summary["sample_count"] == 24
assert paired["episode_count"] == 24
assert paired["pair_count"] == 6
assert paired["complete_pairs"] == 6
assert summary["measurement"]["repair_success"] == 6
assert len(l4_actual_runs) <= 4
assert {row["family_id"] for row in l4_actual_runs} <= {"fir_filter"}
assert audit["verdict"] == "APPROVED"
```

Also assert the freeze file existed before the first fake source call.

- [ ] **Step 2: Run the integration test and fix only integration defects**

```powershell
python -m pytest LLM/tests/test_sr2fpga_agent_runner.py -k "phase_d_24_episode_integration" -q
```

Expected: PASS after resolving field-name or ordering mismatches; no new feature scope is added here.

- [ ] **Step 3: Update the design spec transport section**

Add the explicit rule:

```markdown
Anthropic-compatible sources must pass an SSE `stream_chat` preflight using the
same endpoint, model, timeout, and retry policy as generation. A successful
non-streaming probe is insufficient evidence for Phase D readiness.
```

- [ ] **Step 4: Run the full SR2FPGA test suite**

```powershell
python -m pytest LLM/tests -q
```

Expected: 0 failed. Record the exact passed/skipped counts in the implementation notes.

- [ ] **Step 5: Run deterministic config preflight and control smoke**

```powershell
python -m LLM.src.sr2fpga_agent.runner --config configs/current/sr2fpga_phase_d_control.example.yaml --run-id phase-d-control-plan-verification --preflight
python -m LLM.src.sr2fpga_agent.runner --config configs/current/sr2fpga_phase_d_control.example.yaml --run-id phase-d-control-plan-verification --no-resume
```

Expected: six controls complete, summary and baseline report exist, and only FIR is eligible for L4. The current CLI supports `--no-resume`, so the command above is the required fresh-run invocation.

- [ ] **Step 6: Run the audit against the control as a schema smoke**

The control is not expected to pass the 24-episode gate. The command must return `NOT APPROVED` specifically because `scoreable_episode_count=6`; all structural/freeze/secret checks must pass.

- [ ] **Step 7: Commit integration verification and spec amendment**

```powershell
git add LLM/tests/test_sr2fpga_agent_runner.py docs/superpowers/specs/2026-07-17-sr2fpga-phase-d-frozen-multiteacher-pilot-design.md
git commit -m "test: verify phase d pilot end to end"
```

---

### Task 8: Live Four-Teacher Run, Evidence Closure, Independent Audit, And Publication

**Files:**
- Create locally but do not track: `configs/local/sr2fpga_phase_d_multiteacher_pilot.local.yaml`
- Create: `docs/results/2026-07-17-sr2fpga-phase-d-pilot-report.md`
- Modify: `docs/current-status.md`
- Generated run artifacts: runner-selected dataset root for `phase-d-multiteacher-pilot-20260717-v1`

**Interfaces:**
- Consumes: the ignored `.env` in `D:\Project\cuc-ai-fpga`, committed pilot config, provider preflight, runner, audit CLI, raw tool reports, and freeze manifest.
- Produces: six deterministic controls, 24/24 scoreable live LLM episodes, paired/audit artifacts, an artifact-grounded report, `APPROVED` verdict, and pushed Git commits.

- [ ] **Step 1: Verify repository and credential hygiene before any live call**

Run without printing values:

```powershell
git status --short
git check-ignore D:\Project\cuc-ai-fpga\.env
python -c "from pathlib import Path; p=Path(r'D:\Project\cuc-ai-fpga\.env'); names={line.split('=',1)[0].strip() for line in p.read_text(encoding='utf-8').splitlines() if '=' in line and not line.lstrip().startswith('#')}; required={'ANTHROPIC_API_KEY','OPENAI_API_KEY','DASHSCOPE_API_KEY','DEEPSEEK_API_KEY'}; raise SystemExit(0 if required <= names else 1)"
```

Expected: `.env` is ignored and all four variable names exist. Rotate the two keys previously exposed in chat before the publication step; never echo either old or new values.

- [ ] **Step 2: Create ignored local config by copying structure, not secrets**

Copy the committed example to `configs/local/`, then set local endpoint environment-variable names or non-secret endpoint URLs as required by the runner. API keys remain referenced only by environment variable name.

- [ ] **Step 3: Load `.env` into the current process without output**

Use a PowerShell loop that assigns environment variables but emits no values:

```powershell
Get-Content -LiteralPath 'D:\Project\cuc-ai-fpga\.env' | ForEach-Object {
    if ($_ -match '^\s*([^#][^=]*)=(.*)$') {
        [Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), 'Process')
    }
}
```

- [ ] **Step 4: Run four-source streaming live preflight**

```powershell
python -m LLM.src.sr2fpga_agent.runner --config configs/local/sr2fpga_phase_d_multiteacher_pilot.local.yaml --run-id phase-d-multiteacher-pilot-20260717-v1 --preflight --validate-provider
```

Expected: all four aliases pass using streaming transport. Do not start the 24-episode run while Claude, GPT, Qwen, or DeepSeek preflight is unresolved. Repeated transient retries do not change sample IDs or the freeze.

- [ ] **Step 5: Run six deterministic B_ref controls**

```powershell
python -m LLM.src.sr2fpga_agent.runner --config configs/current/sr2fpga_phase_d_control.example.yaml --run-id phase-d-control-20260717-v1 --no-resume
```

Expected: six controls pass their declared oracle and L0-L3 gates; final L3-pass FIR may run L4 according to policy. Archive summary, labels, trajectory, QoR, and raw reports.

- [ ] **Step 6: Start the frozen 24-episode live run**

```powershell
python -m LLM.src.sr2fpga_agent.runner --config configs/local/sr2fpga_phase_d_multiteacher_pilot.local.yaml --run-id phase-d-multiteacher-pilot-20260717-v1 --no-resume
```

Expected: `measurement_freeze.json` is written before the first generation call. Do not edit prompts, models, timeouts, repair budget, task parameters, or L4 policy after this point.

- [ ] **Step 7: Resume only unresolved infrastructure outcomes under the same freeze**

If a source or tool has an infrastructure outcome, repair the environment and resume with the same run ID and unchanged local config:

```powershell
python -m LLM.src.sr2fpga_agent.runner --config configs/local/sr2fpga_phase_d_multiteacher_pilot.local.yaml --run-id phase-d-multiteacher-pilot-20260717-v1
```

Expected: freeze validation passes; completed samples are not regenerated; semantic attempts are unchanged by transport retries. Model failures remain failures and are not rerun merely to improve scores.

- [ ] **Step 8: Run the independent artifact audit**

```powershell
python scripts/audit_phase_d_pilot.py --run-root tmp\sr2fpga_runs\phase-d-multiteacher-pilot-20260717-v1 --output tmp\sr2fpga_runs\phase-d-multiteacher-pilot-20260717-v1\phase_d_audit.json
```

Expected final output: `APPROVED`. If `NOT APPROVED`, resolve only infrastructure/evidence defects allowed by the frozen protocol and rerun the audit.

- [ ] **Step 9: Inspect representative raw artifacts before writing conclusions**

For at least one initial-pass episode, one repaired episode, one unrepaired model failure if present, and every actual L4 FIR episode, inspect and cite:

```text
eval/labels.json
eval/trajectory.json
eval/measured_qor.json
eval/tool_versions.json
raw OpenXC7/nextpnr log and timing/utilization lines
patch metadata and trusted-artifact flags
```

Verify L4 normalized LUT/Fmax values against raw `SLICE_LUTX` and timing/frequency lines; do not rely solely on synchronized QoR summaries.

- [ ] **Step 10: Write the artifact-grounded Phase D report**

Create `docs/results/2026-07-17-sr2fpga-phase-d-pilot-report.md` with:

```text
run identity and freeze fingerprint
models and source aliases, without endpoints or credentials
24-episode and six-pair completeness
initial (a) and final (b) L0-L3 survival by source and family
repair success, attempts used, and regressions
model failures separated from infrastructure outcomes
FIR-only OpenXC7 L4 evidence with raw-report anchors
trusted-artifact and secret scan results
audit verdict
limitations: pilot scale, one prompt per family, OpenXC7-only L4, no Vivado
```

Use `tool-accepted under the frozen contract`, not `correct design` or `fully verified`.

- [ ] **Step 11: Run final tests and audit again**

```powershell
python -m pytest LLM/tests -q
python scripts/audit_phase_d_pilot.py --run-root tmp\sr2fpga_runs\phase-d-multiteacher-pilot-20260717-v1 --output tmp\sr2fpga_runs\phase-d-multiteacher-pilot-20260717-v1\phase_d_audit.json
git diff --check
```

Expected: tests 0 failed, audit `APPROVED`, and `git diff --check` clean.

- [ ] **Step 12: Perform a separate review pass against the approved design spec**

Review the final diff and run artifacts without changing implementation. Check every item in design spec sections 10 and 11, and record the result in the report under `Independent acceptance review`. The reviewer verdict is exactly `APPROVED` or `NOT APPROVED`, with blocking findings listed by artifact path.

- [ ] **Step 13: Update current status**

In `docs/current-status.md`, record only evidence-backed facts: implementation commits, exact test result, live run ID, 24/24 scoreable count, six-pair count, L4 count, audit verdict, and remaining limitations.

- [ ] **Step 14: Commit the evidence-backed documentation**

Stage only tracked source/tests/config/docs; exclude `.env`, local config, dataset outputs governed by release policy, and every untracked `tmp/` junction:

```powershell
git add docs/results/2026-07-17-sr2fpga-phase-d-pilot-report.md docs/current-status.md
git status --short
git commit -m "docs: report phase d multi-teacher pilot"
```

- [ ] **Step 15: Push the Phase D branch**

```powershell
git push -u origin codex/phase-d-frozen-multiteacher-pilot
```

Expected: remote branch points to all implementation and report commits. Report the pushed commit hash and audit verdict to the user.

---

## Final Definition Of Done

- [ ] Provider streaming tests prove Anthropic SSE parsing, transient retry, and generation-path preflight.
- [ ] `same_as_source` repair resolves and records the originating teacher for every semantic repair attempt.
- [ ] Committed config expands to exactly 24 LLM episodes: six families and four sources each.
- [ ] Four requirements within each family are byte-identical and share one requirement hash and paired ID.
- [ ] `measurement_freeze.json` is written before generation, contains no secrets, and blocks mismatched resume.
- [ ] Every episode records initial (a), final (b), repair attempts, repair success, regressions, and L4 status.
- [ ] Every scoreable episode has L0-L3 verdicts; model failures remain scoreable failures.
- [ ] Only final L3-pass FIR episodes run OpenXC7 L4, at most four.
- [ ] `paired_results.json`, `summary.json`, `baseline_report.md`, and `phase_d_audit.json` agree.
- [ ] The run has 24/24 scoreable episodes and six complete four-source pairs.
- [ ] Trusted artifacts are untouched and no secret or hidden vector appears in tracked outputs.
- [ ] Full `LLM/tests` suite passes with zero failures.
- [ ] Independent audit verdict is `APPROVED`.
- [ ] Evidence report and current status are committed, and the branch is pushed.
