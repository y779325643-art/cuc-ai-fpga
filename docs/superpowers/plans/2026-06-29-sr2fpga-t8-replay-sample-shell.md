# SR2FPGA T8 Replay Sample Shell Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the `composed_replay_sample_shell` / `t8_replay_sample_shell` task as the next component-topology step toward the reinforcement-learning accelerator case.

**Architecture:** Extend the existing deterministic `component_topology` path. T8 adds a host write side, a small replay store, fabric sample readout, occupancy reporting, System-HIS v1.2 metadata, REQ->HIS fidelity checks, and DeepSeek two-stage guidance.

**Tech Stack:** Python `unittest`, deterministic Verilog string templates in `LLM/src/sr2fpga_agent/project_generator.py`, runner topology expansion in `LLM/src/sr2fpga_agent/runner.py`, System-HIS fidelity checks, and DeepSeek prompt helpers.

---

## File Structure

- Modify `LLM/tests/test_sr2fpga_agent_project_generator.py`: add failing generator coverage for the T8 package, topology metadata, top ports, state ownership, manifest sources, deterministic simulation coverage, and supported-task coverage.
- Modify `LLM/tests/test_sr2fpga_agent_runner.py`: extend component-topology expansion to include `t8_replay_sample_shell`.
- Modify `LLM/tests/test_sr2fpga_agent_system_his_fidelity.py`: add failing REQ->HIS fidelity coverage for missing T8 host/sample/occupancy ports.
- Modify `LLM/tests/test_sr2fpga_agent_deepseek.py`: add failing prompt/source expectations for T8.
- Modify `LLM/src/sr2fpga_agent/project_generator.py`: add T8 task registration, topology metadata, interface, state, control-flow membership, RTL files, testbench, descriptions, expected behavior, and predicted QoR.
- Modify `LLM/src/sr2fpga_agent/runner.py`: add T8 natural/contract requirement text.
- Modify `LLM/src/sr2fpga_agent/system_his_fidelity.py`: add T8 top-port expectations.
- Modify `LLM/src/sr2fpga_agent/deepseek.py`: add T8 expected RTL sources and task-specific prompt/retry guidance.
- Modify `docs/current-status.md`: record that T8 is implemented as a synthetic replay/sample shell and keep the full-RL reference-input requirements explicit.

## Task 1: Generator Red Test For T8

**Files:**
- Modify: `LLM/tests/test_sr2fpga_agent_project_generator.py`

- [ ] **Step 1: Write the failing generator test**

Add this test after the T7 component-topology test:

```python
    def test_generates_composed_replay_sample_shell_from_t8_component_topology(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(
                task_type="composed_replay_sample_shell",
                width=8,
                project_name="composed_replay_sample_shell_8bit",
            ),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )

        _assert_multimodule_task(
            self,
            project,
            "composed_replay_sample_shell",
            {
                "rtl/top.v",
                "rtl/host_sample_stage.v",
                "rtl/replay_store.v",
                "rtl/sample_pack_core.v",
                "rtl/sample_read_stage.v",
                "rtl/occupancy_counter.v",
            },
            [
                "host_sample_stage",
                "replay_store",
                "sample_pack_core",
                "sample_read_stage",
                "occupancy_counter",
                ".host_valid(host_valid)",
                ".write_valid(host_stage_valid)",
                ".read_valid(store_read_valid)",
                ".sample_state(sample_pack_state)",
                ".sample_state_out(sample_state)",
                ".occupancy_out(occupancy)",
            ],
        )
        system_his = _system_his(project)
        architecture = system_his["architecture"]

        self.assertEqual(architecture["generator"], "component_topology")
        self.assertEqual(architecture["topology_id"], "t8_replay_sample_shell")
        self.assertEqual(architecture["difficulty_tier"], "T8")
        self.assertEqual(
            [node["component"] for node in architecture["topology"]["nodes"]],
            ["host_sample_stage", "replay_store", "sample_pack_core", "sample_read_stage", "occupancy_counter"],
        )
        self.assertIn(
            {"from": "replay_store.read_valid", "to": "sample_read_stage.in_valid"},
            architecture["topology"]["edges"],
        )
        self.assertIn("input wire host_valid", project.files["rtl/top.v"])
        self.assertIn("input wire [7:0] host_state", project.files["rtl/top.v"])
        self.assertIn("input wire host_action", project.files["rtl/top.v"])
        self.assertIn("output wire sample_valid", project.files["rtl/top.v"])
        self.assertIn("output wire [7:0] sample_next_state", project.files["rtl/top.v"])
        self.assertIn("output wire [2:0] occupancy", project.files["rtl/top.v"])
        self.assertIn("TEST_PASS", project.files["sim/tb_top.v"])
        self.assertGreaterEqual(len(system_his["connections"]), 28)
```

Add this case to `_supported_task_cases()`:

```python
        ("composed_replay_sample_shell", 8, "composed_replay_sample_shell_8bit"),
```

Add this case to `test_multimodule_generated_testbenches_pass_under_icarus`:

```python
            ("composed_replay_sample_shell", 8, "composed_replay_sample_shell_8bit"),
```

- [ ] **Step 2: Run the test to verify RED**

Run:

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_project_generator.ProjectGeneratorTest.test_generates_composed_replay_sample_shell_from_t8_component_topology -q
```

Expected: FAIL with `ValueError: Unsupported task_type for V1: composed_replay_sample_shell`.

## Task 2: Minimal Generator Implementation

**Files:**
- Modify: `LLM/src/sr2fpga_agent/project_generator.py`

- [ ] **Step 1: Register task and topology**

Add `composed_replay_sample_shell` to `SUPPORTED_TASK_TYPES`, then add a `COMPONENT_TOPOLOGIES` entry:

```python
    "composed_replay_sample_shell": {
        "topology_id": "t8_replay_sample_shell",
        "difficulty_tier": "T8",
        "submodules": [
            "host_sample_stage",
            "replay_store",
            "sample_pack_core",
            "sample_read_stage",
            "occupancy_counter",
        ],
        "nodes": [
            {"id": "host_stage", "component": "host_sample_stage"},
            {"id": "store", "component": "replay_store"},
            {"id": "pack", "component": "sample_pack_core"},
            {"id": "read_stage", "component": "sample_read_stage"},
            {"id": "occupancy", "component": "occupancy_counter"},
        ],
        "edges": [
            {"from": "top.host_valid", "to": "host_sample_stage.in_valid"},
            {"from": "top.host_state", "to": "host_sample_stage.state"},
            {"from": "top.host_action", "to": "host_sample_stage.action"},
            {"from": "top.host_reward", "to": "host_sample_stage.reward"},
            {"from": "top.host_next_state", "to": "host_sample_stage.next_state"},
            {"from": "top.host_done", "to": "host_sample_stage.done"},
            {"from": "host_sample_stage.in_ready", "to": "top.host_ready"},
            {"from": "host_sample_stage.out_valid", "to": "replay_store.write_valid"},
            {"from": "host_sample_stage.state_out", "to": "replay_store.write_state"},
            {"from": "host_sample_stage.action_out", "to": "replay_store.write_action"},
            {"from": "host_sample_stage.reward_out", "to": "replay_store.write_reward"},
            {"from": "host_sample_stage.next_state_out", "to": "replay_store.write_next_state"},
            {"from": "host_sample_stage.done_out", "to": "replay_store.write_done"},
            {"from": "replay_store.write_ready", "to": "host_sample_stage.out_ready"},
            {"from": "top.sample_ready", "to": "sample_read_stage.out_ready"},
            {"from": "sample_read_stage.read_ready", "to": "replay_store.read_ready"},
            {"from": "replay_store.read_valid", "to": "sample_read_stage.in_valid"},
            {"from": "replay_store.read_state", "to": "sample_pack_core.state"},
            {"from": "replay_store.read_action", "to": "sample_pack_core.action"},
            {"from": "replay_store.read_reward", "to": "sample_pack_core.reward"},
            {"from": "replay_store.read_next_state", "to": "sample_pack_core.next_state"},
            {"from": "replay_store.read_done", "to": "sample_pack_core.done"},
            {"from": "sample_pack_core.sample_state", "to": "sample_read_stage.sample_state"},
            {"from": "sample_pack_core.sample_action", "to": "sample_read_stage.sample_action"},
            {"from": "sample_pack_core.sample_reward", "to": "sample_read_stage.sample_reward"},
            {"from": "sample_pack_core.sample_next_state", "to": "sample_read_stage.sample_next_state"},
            {"from": "sample_pack_core.sample_done", "to": "sample_read_stage.sample_done"},
            {"from": "sample_read_stage.out_valid", "to": "top.sample_valid"},
            {"from": "sample_read_stage.sample_state_out", "to": "top.sample_state"},
            {"from": "sample_read_stage.sample_action_out", "to": "top.sample_action"},
            {"from": "sample_read_stage.sample_reward_out", "to": "top.sample_reward"},
            {"from": "sample_read_stage.sample_next_state_out", "to": "top.sample_next_state"},
            {"from": "sample_read_stage.sample_done_out", "to": "top.sample_done"},
            {"from": "replay_store.occupancy", "to": "occupancy_counter.occupancy_in"},
            {"from": "occupancy_counter.occupancy_out", "to": "top.occupancy"},
        ],
    },
```

- [ ] **Step 2: Add routing hooks**

Add branches in `_rtl_files()` and `_testbench()`:

```python
    if request.task_type == "composed_replay_sample_shell":
        return _composed_replay_sample_shell_rtl_files(request.width)
```

```python
    if request.task_type == "composed_replay_sample_shell":
        return _composed_replay_sample_shell_testbench(request.width)
```

- [ ] **Step 3: Add interface, state, and descriptions**

Add a T8 `_interface()` branch with top ports `clk`, `rst_n`, `host_valid`,
`host_ready`, `host_state`, `host_action`, `host_reward`, `host_next_state`,
`host_done`, `sample_valid`, `sample_ready`, `sample_state`, `sample_action`,
`sample_reward`, `sample_next_state`, `sample_done`, and `occupancy`.

Add T8 state in `_v12_state()`:

```python
registers.extend([
    {"name": "staged_state", "owner": host_owner, "width": request.width},
    {"name": "staged_reward", "owner": host_owner, "width": request.width},
    {"name": "staged_next_state", "owner": host_owner, "width": request.width},
    {"name": "write_ptr", "owner": store_owner, "width": 2},
    {"name": "read_ptr", "owner": store_owner, "width": 2},
    {"name": "occupancy", "owner": store_owner, "width": 3},
    {"name": "sample_state", "owner": read_owner, "width": request.width},
    {"name": "sample_reward", "owner": read_owner, "width": request.width},
    {"name": "sample_next_state", "owner": read_owner, "width": request.width},
])
buffers.append({"name": "replay_entries", "owner": store_owner, "width": request.width * 3 + 2, "depth": 4})
```

Add T8 to the streaming valid-ready control-flow task set.

Update `_default_description()`, `_expected_behavior()`, `_resource_shape()`,
`_natural_component_title()`, `_natural_component_summary()`, and
`_topology_expected_behavior()` with T8 text.

- [ ] **Step 4: Add RTL helper**

Add `_composed_replay_sample_shell_rtl_files(width: int) -> dict[str, str]`. It
must return `rtl/top.v`, `rtl/host_sample_stage.v`, `rtl/replay_store.v`,
`rtl/sample_pack_core.v`, `rtl/sample_read_stage.v`, and
`rtl/occupancy_counter.v`. The generated RTL should use a depth-4 replay store,
FIFO readback, 3-bit occupancy, and deterministic valid-ready behavior.

- [ ] **Step 5: Add testbench helper**

Add `_composed_replay_sample_shell_testbench(width: int) -> str`. It must write
three samples:

```text
state=3, action=1, reward=4, next_state=5, done=0
state=8, action=0, reward=2, next_state=9, done=1
state=1, action=1, reward=7, next_state=6, done=0
```

Then it must check `occupancy == 3`, read back the three samples in FIFO order,
check all fields, check `occupancy == 0`, and print `TEST_PASS`.

- [ ] **Step 6: Run the focused generator and Icarus tests**

Run:

```bash
python3 -m unittest \
  LLM.tests.test_sr2fpga_agent_project_generator.ProjectGeneratorTest.test_generates_composed_replay_sample_shell_from_t8_component_topology \
  LLM.tests.test_sr2fpga_agent_project_generator.ProjectGeneratorTest.test_multimodule_generated_testbenches_pass_under_icarus \
  -q
```

Expected: PASS.

## Task 3: Runner And Fidelity Red Tests

**Files:**
- Modify: `LLM/tests/test_sr2fpga_agent_runner.py`
- Modify: `LLM/tests/test_sr2fpga_agent_system_his_fidelity.py`

- [ ] **Step 1: Extend runner topology expansion test**

In `test_planned_samples_expand_component_topology_ids`, change
`line_b_targets` to `{"max_samples": 8}`, change `count` to `8`, add
`"t8_replay_sample_shell"` to `topology_ids`, and append expected sample:

```python
                (
                    "sample_runner_t8_replay_sample_shell_8_000008",
                    "composed_replay_sample_shell",
                    "t8_replay_sample_shell",
                    "T8",
                ),
```

Also assert:

```python
        self.assertEqual(samples[7].metadata(config)["topology_id"], "t8_replay_sample_shell")
        self.assertIn("component topology t8_replay_sample_shell", samples[7].requirement)
        self.assertIn("replay_store", samples[7].requirement)
```

- [ ] **Step 2: Add fidelity red test**

Add a fidelity test:

```python
    def test_composed_replay_sample_shell_requires_host_sample_and_occupancy_ports(self) -> None:
        request = ProjectRequest(
            task_type="composed_replay_sample_shell",
            width=8,
            project_name="replay_sample_shell_8bit",
        )
        system_his = _deterministic_system_his(request)
        system_his["top"]["ports"] = [
            port for port in system_his["top"]["ports"] if port["name"] not in {"host_valid", "sample_state", "occupancy"}
        ]

        result = check_system_his_req_fidelity(request, system_his)

        self.assertFalse(result.passed)
        self.assertIn("REQ2HIS fidelity: composed_replay_sample_shell requires top port 'host_valid'", result.errors)
        self.assertIn("REQ2HIS fidelity: composed_replay_sample_shell requires top port 'sample_state'", result.errors)
        self.assertIn("REQ2HIS fidelity: composed_replay_sample_shell requires top port 'occupancy'", result.errors)
```

- [ ] **Step 3: Run red tests**

Run:

```bash
python3 -m unittest \
  LLM.tests.test_sr2fpga_agent_runner.RunnerConfigTest.test_planned_samples_expand_component_topology_ids \
  LLM.tests.test_sr2fpga_agent_system_his_fidelity.SystemHisReqFidelityTest.test_composed_replay_sample_shell_requires_host_sample_and_occupancy_ports \
  -q
```

Expected: FAIL because the runner does not map `t8_replay_sample_shell` and
fidelity has no T8 port requirements.

## Task 4: Runner And Fidelity Implementation

**Files:**
- Modify: `LLM/src/sr2fpga_agent/runner.py`
- Modify: `LLM/src/sr2fpga_agent/system_his_fidelity.py`

- [ ] **Step 1: Add runner mappings**

Add `t8_replay_sample_shell` to topology expansion through the shared
`COMPONENT_TOPOLOGIES` lookup by ensuring `runner.py` text helpers include task
`composed_replay_sample_shell`, tier `T8`, and requirement text that names
`host_sample_stage`, `replay_store`, `sample_pack_core`, `sample_read_stage`,
and `occupancy_counter`.

- [ ] **Step 2: Add fidelity port contract**

Add `_TASK_TOP_PORTS["composed_replay_sample_shell"]` requiring:

```python
{
    "host_valid": {"direction": "input", "width": 1},
    "host_ready": {"direction": "output", "width": 1},
    "host_state": {"direction": "input", "width": "request"},
    "host_action": {"direction": "input", "width": 1},
    "host_reward": {"direction": "input", "width": "request"},
    "host_next_state": {"direction": "input", "width": "request"},
    "host_done": {"direction": "input", "width": 1},
    "sample_valid": {"direction": "output", "width": 1},
    "sample_ready": {"direction": "input", "width": 1},
    "sample_state": {"direction": "output", "width": "request"},
    "sample_action": {"direction": "output", "width": 1},
    "sample_reward": {"direction": "output", "width": "request"},
    "sample_next_state": {"direction": "output", "width": "request"},
    "sample_done": {"direction": "output", "width": 1},
    "occupancy": {"direction": "output", "width": 3},
}
```

- [ ] **Step 3: Run runner/fidelity focused tests**

Run the Task 3 command again.

Expected: PASS.

## Task 5: DeepSeek Red Test And Implementation

**Files:**
- Modify: `LLM/tests/test_sr2fpga_agent_deepseek.py`
- Modify: `LLM/src/sr2fpga_agent/deepseek.py`

- [ ] **Step 1: Write the failing DeepSeek test**

Add this test after the T7 prompt test:

```python
    def test_system_his_v12_prompt_includes_replay_sample_shell_guidance(self) -> None:
        request = ProjectRequest(
            task_type="composed_replay_sample_shell",
            width=8,
            project_name="replay_sample_shell_8bit",
            description="Generate a replay sample shell.",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        user_prompt = _system_his_v12_messages(request, platform)[1]["content"]

        self.assertIn("Required architecture for composed_replay_sample_shell", user_prompt)
        self.assertIn("host_sample_stage", user_prompt)
        self.assertIn("replay_store", user_prompt)
        self.assertIn("sample_pack_core", user_prompt)
        self.assertIn("sample_read_stage", user_prompt)
        self.assertIn("rtl/replay_store.v", user_prompt)
```

- [ ] **Step 2: Run RED**

Run:

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_deepseek.DeepSeekProviderTest.test_system_his_v12_prompt_includes_replay_sample_shell_guidance -q
```

Expected: FAIL because the T8 prompt guidance is absent.

- [ ] **Step 3: Implement prompt/source guidance**

Add `composed_replay_sample_shell` to `MULTIMODULE_RTL_EXAMPLES`,
`_system_his_v12_task_guidance()`, and retry guidance. The guidance must name
the five T8 submodules, host write ports, sample read ports, `occupancy`, and
expected source files.

- [ ] **Step 4: Run GREEN**

Run the Step 2 command again.

Expected: PASS.

## Task 6: Status Update And Final Verification

**Files:**
- Modify: `docs/current-status.md`

- [ ] **Step 1: Update status document**

Record that the deterministic component-topology ladder now includes T8
`composed_replay_sample_shell` / `t8_replay_sample_shell`. Keep a separate note
that realistic RL accelerator generation still requires user-provided algorithm,
observation/action, replay schema, fixed-point, fabric/host boundary, and
resource-reference inputs.

- [ ] **Step 2: Run focused verification**

Run:

```bash
python3 -m unittest \
  LLM.tests.test_sr2fpga_agent_project_generator.ProjectGeneratorTest.test_generates_composed_replay_sample_shell_from_t8_component_topology \
  LLM.tests.test_sr2fpga_agent_project_generator.ProjectGeneratorTest.test_multimodule_generated_testbenches_pass_under_icarus \
  LLM.tests.test_sr2fpga_agent_runner.RunnerConfigTest.test_planned_samples_expand_component_topology_ids \
  LLM.tests.test_sr2fpga_agent_system_his_fidelity.SystemHisReqFidelityTest.test_composed_replay_sample_shell_requires_host_sample_and_occupancy_ports \
  LLM.tests.test_sr2fpga_agent_deepseek.DeepSeekProviderTest.test_system_his_v12_prompt_includes_replay_sample_shell_guidance \
  -q
```

Expected: PASS.

- [ ] **Step 3: Run full verification**

Run:

```bash
python3 -m unittest discover -s LLM/tests -q
python3 -m compileall -q LLM/src/sr2fpga_agent
git diff --check
```

Expected: all commands exit 0.

- [ ] **Step 4: Commit implementation**

Run:

```bash
git add LLM/src/sr2fpga_agent/project_generator.py \
  LLM/src/sr2fpga_agent/runner.py \
  LLM/src/sr2fpga_agent/system_his_fidelity.py \
  LLM/src/sr2fpga_agent/deepseek.py \
  LLM/tests/test_sr2fpga_agent_project_generator.py \
  LLM/tests/test_sr2fpga_agent_runner.py \
  LLM/tests/test_sr2fpga_agent_system_his_fidelity.py \
  LLM/tests/test_sr2fpga_agent_deepseek.py \
  docs/current-status.md
git commit -m "feat: add T8 replay sample shell topology"
```

## Self-Review

- Spec coverage: generator, runner, fidelity, DeepSeek guidance, System-HIS metadata, deterministic RTL/testbench, Icarus simulation coverage, and status documentation are each covered by a task.
- Placeholder scan: no task uses open-ended placeholder instructions.
- Type consistency: task type, topology id, submodule names, top ports, sample fields, and expected source filenames match the T8 design spec.
