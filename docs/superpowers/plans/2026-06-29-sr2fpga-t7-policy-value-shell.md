# SR2FPGA T7 Policy/Value Shell Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the `composed_policy_value_shell` / `t7_policy_value_shell` task as the next component-topology step toward the reinforcement-learning accelerator case.

**Architecture:** Extend the existing deterministic `component_topology` path. T7 adds configuration registers, a two-observation policy score datapath, action selection, value-estimate output staging, System-HIS v1.2 metadata, REQ->HIS fidelity checks, and DeepSeek two-stage guidance.

**Tech Stack:** Python `unittest`, deterministic Verilog string templates in `LLM/src/sr2fpga_agent/project_generator.py`, runner topology expansion in `LLM/src/sr2fpga_agent/runner.py`, System-HIS fidelity checks, and DeepSeek prompt helpers.

---

## File Structure

- Modify `LLM/tests/test_sr2fpga_agent_project_generator.py`: add failing generator coverage for the T7 package, topology metadata, top ports, state ownership, manifest sources, and deterministic simulation coverage.
- Modify `LLM/tests/test_sr2fpga_agent_runner.py`: extend component-topology expansion to include `t7_policy_value_shell`.
- Modify `LLM/tests/test_sr2fpga_agent_system_his_fidelity.py`: add failing REQ->HIS fidelity coverage for missing T7 config/action ports.
- Modify `LLM/tests/test_sr2fpga_agent_deepseek.py`: add failing prompt/source expectations for T7.
- Modify `LLM/src/sr2fpga_agent/project_generator.py`: add T7 task registration, topology metadata, interface, state, control-flow membership, RTL files, testbench, descriptions, expected behavior, and predicted QoR.
- Modify `LLM/src/sr2fpga_agent/runner.py`: add T7 natural/contract requirement text.
- Modify `LLM/src/sr2fpga_agent/system_his_fidelity.py`: add T7 top-port expectations.
- Modify `LLM/src/sr2fpga_agent/deepseek.py`: add T7 expected RTL sources and task-specific prompt/retry guidance.
- Modify `docs/current-status.md`: record that T7 is implemented as a synthetic policy/value shell and keep the full-RL reference-input requirements explicit.

## Task 1: Generator Red Test For T7

**Files:**
- Modify: `LLM/tests/test_sr2fpga_agent_project_generator.py`

- [ ] **Step 1: Write the failing generator test**

Add this test after the T6 component-topology test:

```python
    def test_generates_composed_policy_value_shell_from_t7_component_topology(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(
                task_type="composed_policy_value_shell",
                width=8,
                project_name="composed_policy_value_shell_8bit",
            ),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )

        _assert_multimodule_task(
            self,
            project,
            "composed_policy_value_shell",
            {
                "rtl/top.v",
                "rtl/config_reg_bank.v",
                "rtl/observation_stage.v",
                "rtl/policy_score_core.v",
                "rtl/action_select_core.v",
                "rtl/stream_stage.v",
            },
            [
                "config_reg_bank",
                "observation_stage",
                "policy_score_core",
                "action_select_core",
                "stream_stage",
                ".cfg_valid(cfg_valid)",
                ".obs0(obs0)",
                ".score1(policy_score1)",
                ".selected_action(select_action)",
                ".value_estimate(select_value)",
                ".selected_action_out(selected_action)",
                ".value_estimate_out(value_estimate)",
            ],
        )
        system_his = _system_his(project)
        architecture = system_his["architecture"]

        self.assertEqual(architecture["generator"], "component_topology")
        self.assertEqual(architecture["topology_id"], "t7_policy_value_shell")
        self.assertEqual(architecture["difficulty_tier"], "T7")
        self.assertEqual(
            [node["component"] for node in architecture["topology"]["nodes"]],
            ["config_reg_bank", "observation_stage", "policy_score_core", "action_select_core", "stream_stage"],
        )
        self.assertIn(
            {"from": "policy_score_core.score1", "to": "action_select_core.score1"},
            architecture["topology"]["edges"],
        )
        self.assertIn("input wire cfg_valid", project.files["rtl/top.v"])
        self.assertIn("input wire [2:0] cfg_addr", project.files["rtl/top.v"])
        self.assertIn("input wire [7:0] cfg_data", project.files["rtl/top.v"])
        self.assertIn("input wire obs_valid", project.files["rtl/top.v"])
        self.assertIn("output wire action_valid", project.files["rtl/top.v"])
        self.assertIn("output wire selected_action", project.files["rtl/top.v"])
        self.assertIn("output wire [7:0] value_estimate", project.files["rtl/top.v"])
        self.assertIn("TEST_PASS", project.files["sim/tb_top.v"])
        self.assertGreaterEqual(len(system_his["connections"]), 24)
```

Add this case to `_supported_task_cases()`:

```python
        ("composed_policy_value_shell", 8, "composed_policy_value_shell_8bit"),
```

- [ ] **Step 2: Run the test to verify RED**

Run:

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_project_generator.ProjectGeneratorTest.test_generates_composed_policy_value_shell_from_t7_component_topology -q
```

Expected: FAIL with `ValueError: Unsupported task_type for V1: composed_policy_value_shell`.

## Task 2: Minimal Generator Implementation

**Files:**
- Modify: `LLM/src/sr2fpga_agent/project_generator.py`

- [ ] **Step 1: Register task and topology**

Add `composed_policy_value_shell` to `SUPPORTED_TASK_TYPES`, then add a `COMPONENT_TOPOLOGIES` entry:

```python
    "composed_policy_value_shell": {
        "topology_id": "t7_policy_value_shell",
        "difficulty_tier": "T7",
        "submodules": [
            "config_reg_bank",
            "observation_stage",
            "policy_score_core",
            "action_select_core",
            "stream_stage",
        ],
        "nodes": [
            {"id": "config", "component": "config_reg_bank"},
            {"id": "observation", "component": "observation_stage"},
            {"id": "score", "component": "policy_score_core"},
            {"id": "select", "component": "action_select_core"},
            {"id": "output_stage", "component": "stream_stage"},
        ],
        "edges": [
            {"from": "top.cfg_valid", "to": "config_reg_bank.cfg_valid"},
            {"from": "top.cfg_addr", "to": "config_reg_bank.cfg_addr"},
            {"from": "top.cfg_data", "to": "config_reg_bank.cfg_data"},
            {"from": "config_reg_bank.cfg_ready", "to": "top.cfg_ready"},
            {"from": "top.obs_valid", "to": "observation_stage.in_valid"},
            {"from": "top.obs0", "to": "observation_stage.obs0"},
            {"from": "top.obs1", "to": "observation_stage.obs1"},
            {"from": "observation_stage.in_ready", "to": "top.obs_ready"},
            {"from": "observation_stage.out_valid", "to": "policy_score_core.in_valid"},
            {"from": "observation_stage.obs0_out", "to": "policy_score_core.obs0"},
            {"from": "observation_stage.obs1_out", "to": "policy_score_core.obs1"},
            {"from": "config_reg_bank.weight0", "to": "policy_score_core.weight0"},
            {"from": "config_reg_bank.weight1", "to": "policy_score_core.weight1"},
            {"from": "config_reg_bank.bias0", "to": "policy_score_core.bias0"},
            {"from": "config_reg_bank.bias1", "to": "policy_score_core.bias1"},
            {"from": "config_reg_bank.enable", "to": "policy_score_core.enable"},
            {"from": "policy_score_core.out_valid", "to": "action_select_core.in_valid"},
            {"from": "policy_score_core.score0", "to": "action_select_core.score0"},
            {"from": "policy_score_core.score1", "to": "action_select_core.score1"},
            {"from": "action_select_core.out_valid", "to": "stream_stage.in_valid"},
            {"from": "action_select_core.selected_action", "to": "stream_stage.selected_action"},
            {"from": "action_select_core.value_estimate", "to": "stream_stage.value_estimate"},
            {"from": "stream_stage.out_valid", "to": "top.action_valid"},
            {"from": "top.action_ready", "to": "stream_stage.out_ready"},
            {"from": "stream_stage.selected_action_out", "to": "top.selected_action"},
            {"from": "stream_stage.value_estimate_out", "to": "top.value_estimate"},
        ],
    },
```

- [ ] **Step 2: Add routing hooks**

Add branches in `_rtl_files()` and `_testbench()`:

```python
    if request.task_type == "composed_policy_value_shell":
        return _composed_policy_value_shell_rtl_files(request.width)
```

```python
    if request.task_type == "composed_policy_value_shell":
        return _composed_policy_value_shell_testbench(request.width)
```

- [ ] **Step 3: Add interface, state, and descriptions**

Add a T7 `_interface()` branch with top ports `clk`, `rst_n`, `cfg_valid`, `cfg_addr`, `cfg_data`, `cfg_ready`, `obs_valid`, `obs_ready`, `obs0`, `obs1`, `action_valid`, `action_ready`, `selected_action`, and `value_estimate`.

Add T7 state in `_v12_state()`:

```python
registers.extend([
    {"name": "weight0", "owner": config_owner, "width": request.width},
    {"name": "weight1", "owner": config_owner, "width": request.width},
    {"name": "bias0", "owner": config_owner, "width": request.width},
    {"name": "bias1", "owner": config_owner, "width": request.width},
    {"name": "enable", "owner": config_owner, "width": 1},
    {"name": "captured_obs0", "owner": observation_owner, "width": request.width},
    {"name": "captured_obs1", "owner": observation_owner, "width": request.width},
    {"name": "selected_action", "owner": output_owner, "width": 1},
    {"name": "value_estimate", "owner": output_owner, "width": request.width},
])
```

Add T7 to the streaming valid-ready control-flow task set.

Update `_default_description()`, `_expected_behavior()`, `_resource_shape()`, `_natural_component_title()`, `_natural_component_summary()`, and `_topology_expected_behavior()` with T7 text.

- [ ] **Step 4: Add RTL helper**

Add `_composed_policy_value_shell_rtl_files(width: int) -> dict[str, str]`. It must return `rtl/top.v`, `rtl/config_reg_bank.v`, `rtl/observation_stage.v`, `rtl/policy_score_core.v`, `rtl/action_select_core.v`, and `rtl/stream_stage.v`. The generated RTL should use unsigned fixed-width data, two `DATA_WIDTH*2` multiplication intermediates, and deterministic truncation back to `DATA_WIDTH`.

- [ ] **Step 5: Add testbench helper**

Add `_composed_policy_value_shell_testbench(width: int) -> str`. It must configure `weight0=2`, `bias0=1`, `weight1=3`, `bias1=0`, `enable=1`, then send two observation tuples and check:

```text
obs0=4, obs1=2 -> selected_action=0, value_estimate=7
obs0=1, obs1=5 -> selected_action=1, value_estimate=9
```

- [ ] **Step 6: Run the focused generator test**

Run:

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_project_generator.ProjectGeneratorTest.test_generates_composed_policy_value_shell_from_t7_component_topology -q
```

Expected: PASS.

## Task 3: Runner And Fidelity Red Tests

**Files:**
- Modify: `LLM/tests/test_sr2fpga_agent_runner.py`
- Modify: `LLM/tests/test_sr2fpga_agent_system_his_fidelity.py`

- [ ] **Step 1: Extend runner topology expansion test**

In `test_planned_samples_expand_component_topology_ids`, change `line_b_targets` to `{"max_samples": 7}`, change `count` to `7`, add `"t7_policy_value_shell"` to `topology_ids`, and append expected sample:

```python
                (
                    "sample_runner_t7_policy_value_shell_8_000007",
                    "composed_policy_value_shell",
                    "t7_policy_value_shell",
                    "T7",
                ),
```

Also assert:

```python
        self.assertEqual(samples[6].metadata(config)["topology_id"], "t7_policy_value_shell")
        self.assertIn("component topology t7_policy_value_shell", samples[6].requirement)
        self.assertIn("action_select_core", samples[6].requirement)
```

- [ ] **Step 2: Add fidelity red test**

Add a fidelity test:

```python
    def test_composed_policy_value_shell_requires_config_observation_and_action_ports(self) -> None:
        request = ProjectRequest(
            task_type="composed_policy_value_shell",
            width=8,
            project_name="policy_value_shell_8bit",
        )
        system_his = _deterministic_system_his(request)
        system_his["top"]["ports"] = [
            port for port in system_his["top"]["ports"] if port["name"] not in {"cfg_valid", "selected_action"}
        ]

        result = check_system_his_req_fidelity(request, system_his)

        self.assertFalse(result.passed)
        self.assertIn("REQ2HIS fidelity: composed_policy_value_shell requires top port 'cfg_valid'", result.errors)
        self.assertIn("REQ2HIS fidelity: composed_policy_value_shell requires top port 'selected_action'", result.errors)
```

- [ ] **Step 3: Run red tests**

Run:

```bash
python3 -m unittest \
  LLM.tests.test_sr2fpga_agent_runner.RunnerConfigTest.test_planned_samples_expand_component_topology_ids \
  LLM.tests.test_sr2fpga_agent_system_his_fidelity.SystemHisReqFidelityTest.test_composed_policy_value_shell_requires_config_observation_and_action_ports \
  -q
```

Expected: FAIL because the runner does not map `t7_policy_value_shell` and fidelity has no T7 port requirements.

## Task 4: Runner And Fidelity Implementation

**Files:**
- Modify: `LLM/src/sr2fpga_agent/runner.py`
- Modify: `LLM/src/sr2fpga_agent/system_his_fidelity.py`

- [ ] **Step 1: Add runner mappings**

Add `t7_policy_value_shell` to topology expansion with task `composed_policy_value_shell`, tier `T7`, and requirement text that names `config_reg_bank`, `observation_stage`, `policy_score_core`, `action_select_core`, and `stream_stage`.

- [ ] **Step 2: Add fidelity port contract**

Add `_TASK_TOP_PORTS["composed_policy_value_shell"]` requiring:

```python
{
    "cfg_valid": {"direction": "input", "width": 1},
    "cfg_addr": {"direction": "input", "width": 3},
    "cfg_data": {"direction": "input", "width": request.width},
    "cfg_ready": {"direction": "output", "width": 1},
    "obs_valid": {"direction": "input", "width": 1},
    "obs_ready": {"direction": "output", "width": 1},
    "obs0": {"direction": "input", "width": request.width},
    "obs1": {"direction": "input", "width": request.width},
    "action_valid": {"direction": "output", "width": 1},
    "action_ready": {"direction": "input", "width": 1},
    "selected_action": {"direction": "output", "width": 1},
    "value_estimate": {"direction": "output", "width": request.width},
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

Add this test after the T6 prompt test:

```python
    def test_system_his_v12_prompt_includes_policy_value_shell_guidance(self) -> None:
        messages = _system_his_v12_messages(
            requirement="Generate a policy/value shell.",
            task_type="composed_policy_value_shell",
            width=8,
        )
        user_prompt = messages[-1]["content"]

        self.assertIn("Required architecture for composed_policy_value_shell", user_prompt)
        self.assertIn("config_reg_bank", user_prompt)
        self.assertIn("observation_stage", user_prompt)
        self.assertIn("policy_score_core", user_prompt)
        self.assertIn("action_select_core", user_prompt)
        self.assertIn("rtl/action_select_core.v", user_prompt)
```

- [ ] **Step 2: Run RED**

Run:

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_deepseek.DeepSeekProviderTest.test_system_his_v12_prompt_includes_policy_value_shell_guidance -q
```

Expected: FAIL because the T7 prompt guidance is absent.

- [ ] **Step 3: Implement prompt/source guidance**

Add `composed_policy_value_shell` to `MULTIMODULE_RTL_EXAMPLES`, `_system_his_v12_task_guidance()`, and retry guidance. The guidance must name the five T7 submodules, the config ports, observation ports, `selected_action`, `value_estimate`, and expected source files.

- [ ] **Step 4: Run GREEN**

Run the Step 2 command again.

Expected: PASS.

## Task 6: Status Update And Final Verification

**Files:**
- Modify: `docs/current-status.md`

- [ ] **Step 1: Update status document**

Record that the deterministic component-topology ladder now includes T7 `composed_policy_value_shell` / `t7_policy_value_shell`. Keep a separate note that realistic RL accelerator generation still requires user-provided algorithm, observation/action, fixed-point, fabric/host boundary, and resource-reference inputs.

- [ ] **Step 2: Run focused verification**

Run:

```bash
python3 -m unittest \
  LLM.tests.test_sr2fpga_agent_project_generator.ProjectGeneratorTest.test_generates_composed_policy_value_shell_from_t7_component_topology \
  LLM.tests.test_sr2fpga_agent_runner.RunnerConfigTest.test_planned_samples_expand_component_topology_ids \
  LLM.tests.test_sr2fpga_agent_system_his_fidelity.SystemHisReqFidelityTest.test_composed_policy_value_shell_requires_config_observation_and_action_ports \
  LLM.tests.test_sr2fpga_agent_deepseek.DeepSeekProviderTest.test_system_his_v12_prompt_includes_policy_value_shell_guidance \
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
git commit -m "feat: add T7 policy value shell topology"
```

## Self-Review

- Spec coverage: generator, runner, fidelity, DeepSeek guidance, System-HIS metadata, deterministic RTL/testbench, and status documentation are each covered by a task.
- Placeholder scan: no task uses open-ended placeholder instructions.
- Type consistency: task type, topology id, submodule names, top ports, and expected source filenames match the T7 design spec.
