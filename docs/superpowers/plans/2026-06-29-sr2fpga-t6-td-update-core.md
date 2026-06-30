# SR2FPGA T6 TD-Update Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the `composed_td_update_core` / `t6_td_update_core` task as the next component-topology step toward the reinforcement-learning accelerator case.

**Architecture:** Extend the existing deterministic `component_topology` path. T6 adds a valid-ready TD update tuple input, `td_input_stage`, `discount_core`, `td_update_core`, an output `stream_stage`, System-HIS v1.2 metadata, REQ->HIS fidelity checks, and DeepSeek two-stage guidance.

**Tech Stack:** Python `unittest`, deterministic Verilog string templates in `LLM/src/sr2fpga_agent/project_generator.py`, runner topology expansion in `LLM/src/sr2fpga_agent/runner.py`, System-HIS fidelity checks, and DeepSeek prompt helpers.

---

## File Structure

- Modify `LLM/tests/test_sr2fpga_agent_project_generator.py`: add failing generator coverage for T6 package, topology metadata, top ports, manifest sources, and deterministic simulation coverage.
- Modify `LLM/tests/test_sr2fpga_agent_runner.py`: extend component-topology expansion to include `t6_td_update_core`.
- Modify `LLM/tests/test_sr2fpga_agent_system_his_fidelity.py`: add failing REQ->HIS fidelity coverage for missing T6 ports.
- Modify `LLM/tests/test_sr2fpga_agent_deepseek.py`: add failing prompt/source expectations for T6.
- Modify `LLM/src/sr2fpga_agent/project_generator.py`: add T6 task registration, topology metadata, interface, state, control-flow membership, RTL files, testbench, descriptions, expected behavior, and predicted QoR.
- Modify `LLM/src/sr2fpga_agent/runner.py`: add T6 natural/contract requirement text.
- Modify `LLM/src/sr2fpga_agent/system_his_fidelity.py`: add T6 top-port expectations.
- Modify `LLM/src/sr2fpga_agent/deepseek.py`: add T6 expected RTL sources and task-specific prompt/retry guidance.
- Modify `docs/current-status.md`: record that T6 is implemented as a synthetic TD-update ladder step and keep T7/full-RL reference-input requirements explicit.

## Task 1: Generator Red Test For T6

**Files:**
- Modify: `LLM/tests/test_sr2fpga_agent_project_generator.py`

- [ ] **Step 1: Write the failing generator test**

Add this test after the T5 component-topology test:

```python
    def test_generates_composed_td_update_core_from_t6_component_topology(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(
                task_type="composed_td_update_core",
                width=8,
                project_name="composed_td_update_core_8bit",
            ),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )

        _assert_multimodule_task(
            self,
            project,
            "composed_td_update_core",
            {
                "rtl/top.v",
                "rtl/td_input_stage.v",
                "rtl/discount_core.v",
                "rtl/td_update_core.v",
                "rtl/stream_stage.v",
            },
            [
                "td_input_stage",
                "discount_core",
                "td_update_core",
                "stream_stage",
                ".reward(reward)",
                ".next_value(next_value)",
                ".td_error(td_error)",
                ".updated_value(updated_value)",
            ],
        )
        system_his = _system_his(project)
        architecture = system_his["architecture"]

        self.assertEqual(architecture["generator"], "component_topology")
        self.assertEqual(architecture["topology_id"], "t6_td_update_core")
        self.assertEqual(architecture["difficulty_tier"], "T6")
        self.assertEqual(
            [node["component"] for node in architecture["topology"]["nodes"]],
            ["td_input_stage", "discount_core", "td_update_core", "stream_stage"],
        )
        self.assertIn(
            {"from": "discount_core.discounted_return", "to": "td_update_core.discounted_return"},
            architecture["topology"]["edges"],
        )
        self.assertIn("input wire signed [7:0] reward", project.files["rtl/top.v"])
        self.assertIn("input wire [7:0] gamma", project.files["rtl/top.v"])
        self.assertIn("output wire signed [7:0] td_error", project.files["rtl/top.v"])
        self.assertIn("output wire signed [7:0] updated_value", project.files["rtl/top.v"])
        self.assertIn("TEST_PASS", project.files["sim/tb_top.v"])
        self.assertGreaterEqual(len(system_his["connections"]), 18)
```

Add this case to `_supported_task_cases()`:

```python
        ("composed_td_update_core", 8, "composed_td_update_core_8bit"),
```

- [ ] **Step 2: Run the test to verify RED**

Run:

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_project_generator.ProjectGeneratorTest.test_generates_composed_td_update_core_from_t6_component_topology -q
```

Expected: FAIL with `ValueError: Unsupported task_type for V1: composed_td_update_core`.

## Task 2: Minimal Generator Implementation

**Files:**
- Modify: `LLM/src/sr2fpga_agent/project_generator.py`

- [ ] **Step 1: Register task and topology**

Add `composed_td_update_core` to `SUPPORTED_TASK_TYPES`, then add a `COMPONENT_TOPOLOGIES` entry:

```python
    "composed_td_update_core": {
        "topology_id": "t6_td_update_core",
        "difficulty_tier": "T6",
        "submodules": ["td_input_stage", "discount_core", "td_update_core", "stream_stage"],
        "nodes": [
            {"id": "input_stage", "component": "td_input_stage"},
            {"id": "discount", "component": "discount_core"},
            {"id": "update", "component": "td_update_core"},
            {"id": "output_stage", "component": "stream_stage"},
        ],
        "edges": [
            {"from": "top.in_valid", "to": "td_input_stage.in_valid"},
            {"from": "top.reward", "to": "td_input_stage.reward"},
            {"from": "top.value", "to": "td_input_stage.value"},
            {"from": "top.next_value", "to": "td_input_stage.next_value"},
            {"from": "top.gamma", "to": "td_input_stage.gamma"},
            {"from": "top.alpha", "to": "td_input_stage.alpha"},
            {"from": "td_input_stage.out_valid", "to": "discount_core.in_valid"},
            {"from": "td_input_stage.reward_out", "to": "discount_core.reward"},
            {"from": "td_input_stage.next_value_out", "to": "discount_core.next_value"},
            {"from": "td_input_stage.gamma_out", "to": "discount_core.gamma"},
            {"from": "discount_core.out_valid", "to": "td_update_core.in_valid"},
            {"from": "discount_core.discounted_return", "to": "td_update_core.discounted_return"},
            {"from": "td_input_stage.value_out", "to": "td_update_core.value"},
            {"from": "td_input_stage.alpha_out", "to": "td_update_core.alpha"},
            {"from": "td_update_core.out_valid", "to": "stream_stage.in_valid"},
            {"from": "td_update_core.td_error", "to": "stream_stage.td_error"},
            {"from": "td_update_core.updated_value", "to": "stream_stage.updated_value"},
            {"from": "stream_stage.out_valid", "to": "top.out_valid"},
            {"from": "stream_stage.td_error_out", "to": "top.td_error"},
            {"from": "stream_stage.updated_value_out", "to": "top.updated_value"},
            {"from": "top.out_ready", "to": "stream_stage.out_ready"},
        ],
    },
```

- [ ] **Step 2: Add routing hooks**

Add branches in `_rtl_files()` and `_testbench()`:

```python
    if request.task_type == "composed_td_update_core":
        return _composed_td_update_core_rtl_files(request.width)
```

```python
    if request.task_type == "composed_td_update_core":
        return _composed_td_update_core_testbench(request.width)
```

- [ ] **Step 3: Add interface, state, and descriptions**

Add a T6 `_interface()` branch with top ports `clk`, `rst_n`, `in_valid`, `reward`, `value`, `next_value`, `gamma`, `alpha`, `out_ready`, `in_ready`, `out_valid`, `td_error`, and `updated_value`.

Add T6 state in `_v12_state()`:

```python
registers.extend([
    {"name": "captured_reward", "owner": input_owner, "width": request.width},
    {"name": "captured_value", "owner": input_owner, "width": request.width},
    {"name": "captured_next_value", "owner": input_owner, "width": request.width},
    {"name": "td_error", "owner": update_owner, "width": request.width},
    {"name": "updated_value", "owner": update_owner, "width": request.width},
])
```

Add T6 to the streaming valid-ready control-flow task set.

Update `_default_description()`, `_expected_behavior()`, `_resource_shape()`, `_natural_component_title()`, `_natural_component_summary()`, and `_topology_expected_behavior()` with T6 text.

- [ ] **Step 4: Add RTL helper**

Add `_composed_td_update_core_rtl_files(width: int) -> dict[str, str]`. It must return `rtl/top.v`, `rtl/td_input_stage.v`, `rtl/discount_core.v`, `rtl/td_update_core.v`, and `rtl/stream_stage.v`. The generated RTL should use signed data arithmetic and unsigned `gamma`/`alpha`, with `SCALE_SHIFT=4`.

- [ ] **Step 5: Add testbench helper**

Add `_composed_td_update_core_testbench(width: int) -> str`. It must send two valid-ready update tuples and check:

```text
reward=4, value=10, next_value=20, gamma=8, alpha=4 -> td_error=4, updated_value=11
reward=2, value=6, next_value=16, gamma=8, alpha=8 -> td_error=4, updated_value=8
```

- [ ] **Step 6: Run the focused generator test**

Run:

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_project_generator.ProjectGeneratorTest.test_generates_composed_td_update_core_from_t6_component_topology -q
```

Expected: PASS.

## Task 3: Runner And Fidelity Red Tests

**Files:**
- Modify: `LLM/tests/test_sr2fpga_agent_runner.py`
- Modify: `LLM/tests/test_sr2fpga_agent_system_his_fidelity.py`

- [ ] **Step 1: Extend runner topology expansion test**

In `test_planned_samples_expand_component_topology_ids`, change `line_b_targets` to `{"max_samples": 6}`, `count` to `6`, add `"t6_td_update_core"` to `topology_ids`, and append expected sample:

```python
                (
                    "sample_runner_t6_td_update_core_8_000006",
                    "composed_td_update_core",
                    "t6_td_update_core",
                    "T6",
                ),
```

Also assert:

```python
        self.assertEqual(samples[5].metadata(config)["topology_id"], "t6_td_update_core")
        self.assertIn("component topology t6_td_update_core", samples[5].requirement)
        self.assertIn("td_update_core", samples[5].requirement)
```

- [ ] **Step 2: Add fidelity red test**

Add a fidelity test:

```python
    def test_composed_td_update_core_requires_reward_value_and_update_ports(self) -> None:
        request = ProjectRequest(
            task_type="composed_td_update_core",
            width=8,
            project_name="td_update_8bit",
        )
        system_his = _deterministic_system_his(request)
        system_his["top"]["ports"] = [
            port for port in system_his["top"]["ports"] if port["name"] not in {"reward", "updated_value"}
        ]

        result = check_system_his_req_fidelity(request, system_his)

        self.assertFalse(result.passed)
        self.assertIn("REQ2HIS fidelity: composed_td_update_core requires top port 'reward'", result.errors)
        self.assertIn("REQ2HIS fidelity: composed_td_update_core requires top port 'updated_value'", result.errors)
```

- [ ] **Step 3: Run red tests**

Run:

```bash
python3 -m unittest \
  LLM.tests.test_sr2fpga_agent_runner.RunnerConfigTest.test_planned_samples_expand_component_topology_ids \
  LLM.tests.test_sr2fpga_agent_system_his_fidelity.SystemHisReqFidelityTest.test_composed_td_update_core_requires_reward_value_and_update_ports \
  -q
```

Expected before implementation: runner/fidelity fail until mappings and top-port expectations exist.

## Task 4: Runner And Fidelity Implementation

**Files:**
- Modify: `LLM/src/sr2fpga_agent/runner.py`
- Modify: `LLM/src/sr2fpga_agent/system_his_fidelity.py`

- [ ] **Step 1: Add runner text mappings**

Add T6 entries to `_simple_prompt_requirement()`, `_natural_component_title()`, `_natural_component_summary()`, and `_topology_expected_behavior()`.

- [ ] **Step 2: Add fidelity port expectations**

Add `_TASK_TOP_PORTS["composed_td_update_core"]` requiring:

```python
{
    "clk": {"direction": "input"},
    "rst_n": {"direction": "input"},
    "in_valid": {"direction": "input"},
    "reward": {"direction": "input", "width": "request"},
    "value": {"direction": "input", "width": "request"},
    "next_value": {"direction": "input", "width": "request"},
    "gamma": {"direction": "input", "width": "request"},
    "alpha": {"direction": "input", "width": "request"},
    "out_ready": {"direction": "input"},
    "in_ready": {"direction": "output"},
    "out_valid": {"direction": "output"},
    "td_error": {"direction": "output", "width": "request"},
    "updated_value": {"direction": "output", "width": "request"},
}
```

- [ ] **Step 3: Run focused tests**

Run the same two tests from Task 3.

Expected: PASS.

## Task 5: DeepSeek Red Test And Prompt Implementation

**Files:**
- Modify: `LLM/tests/test_sr2fpga_agent_deepseek.py`
- Modify: `LLM/src/sr2fpga_agent/deepseek.py`

- [ ] **Step 1: Add DeepSeek red test**

Add a prompt test:

```python
    def test_system_his_v12_prompt_includes_td_update_core_guidance(self) -> None:
        request = ProjectRequest(
            task_type="composed_td_update_core",
            width=8,
            project_name="td_update_8bit",
            description="Generate a TD update core.",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        user_prompt = _system_his_v12_messages(request, platform)[1]["content"]

        self.assertIn("Required architecture for composed_td_update_core", user_prompt)
        self.assertIn("td_input_stage", user_prompt)
        self.assertIn("discount_core", user_prompt)
        self.assertIn("td_update_core", user_prompt)
        self.assertIn("rtl/td_update_core.v", user_prompt)
```

- [ ] **Step 2: Run red test**

Run:

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_deepseek.DeepSeekProviderTest.test_system_his_v12_prompt_includes_td_update_core_guidance -q
```

Expected: FAIL until T6 prompt guidance exists.

- [ ] **Step 3: Add prompt/source mappings**

Add `composed_td_update_core` to `MULTIMODULE_RTL_EXAMPLES`, `_system_his_v12_task_guidance()`, and `_system_his_v12_retry_guidance()`.

- [ ] **Step 4: Run DeepSeek focused test**

Run the same DeepSeek test.

Expected: PASS.

## Task 6: Verification, Status, Commit

**Files:**
- Verify all touched files.
- Modify `docs/current-status.md`.

- [ ] **Step 1: Run focused tests**

Run:

```bash
python3 -m unittest \
  LLM.tests.test_sr2fpga_agent_project_generator \
  LLM.tests.test_sr2fpga_agent_runner.RunnerConfigTest.test_planned_samples_expand_component_topology_ids \
  LLM.tests.test_sr2fpga_agent_system_his_fidelity \
  LLM.tests.test_sr2fpga_agent_deepseek.DeepSeekProviderTest.test_system_his_v12_prompt_includes_td_update_core_guidance \
  -q
```

Expected: PASS.

- [ ] **Step 2: Run full unit suite**

Run:

```bash
python3 -m unittest discover -s LLM/tests -q
```

Expected: PASS.

- [ ] **Step 3: Compile package**

Run:

```bash
python3 -m compileall -q LLM/src/sr2fpga_agent
```

Expected: no output and exit code 0.

- [ ] **Step 4: Update current status**

Update `docs/current-status.md` to say T6 is implemented as a synthetic TD-update ladder step and that T7/full RL accelerator still needs real workload and FPGA/ARM boundary inputs.

- [ ] **Step 5: Check and commit**

Run:

```bash
git diff --check
git status --short
git add LLM/src/sr2fpga_agent/project_generator.py \
  LLM/src/sr2fpga_agent/runner.py \
  LLM/src/sr2fpga_agent/system_his_fidelity.py \
  LLM/src/sr2fpga_agent/deepseek.py \
  LLM/tests/test_sr2fpga_agent_project_generator.py \
  LLM/tests/test_sr2fpga_agent_runner.py \
  LLM/tests/test_sr2fpga_agent_system_his_fidelity.py \
  LLM/tests/test_sr2fpga_agent_deepseek.py \
  docs/current-status.md
git commit -m "feat: add T6 TD update topology"
```

Expected: no whitespace errors; commit succeeds.

## Self-Review

- Spec coverage: T6 task type, topology id, difficulty tier, fixed-point TD formula, interfaces, data flow, System-HIS requirements, runner expansion, REQ->HIS fidelity, DeepSeek guidance, verification, and human-input boundary are covered.
- Scope check: this plan implements one deterministic TD-update topology, not the full RL accelerator.
- Human input: no real reference project is required for T6; T7/full RL remains the checkpoint for workload shape and fabric/software boundary.
- Placeholder scan: this plan uses concrete paths, tests, commands, and expected outcomes.
