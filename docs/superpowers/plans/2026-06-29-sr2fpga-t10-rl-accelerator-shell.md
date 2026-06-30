# SR2FPGA T10 RL Accelerator Shell Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the `composed_rl_accelerator_shell` / `t10_rl_accelerator_shell` task as the integrated synthetic RL accelerator step after T9.

**Architecture:** Extend the existing deterministic `component_topology` path. T10 combines host configuration, sample capture, policy/value scoring, TD update computation, result-stream backpressure, and irq signaling in one bounded multi-module template.

**Tech Stack:** Python `unittest`, deterministic Verilog string templates in `LLM/src/sr2fpga_agent/project_generator.py`, runner topology expansion in `LLM/src/sr2fpga_agent/runner.py`, System-HIS fidelity checks, and DeepSeek prompt helpers.

---

## File Structure

- Modify `LLM/tests/test_sr2fpga_agent_project_generator.py`: add T10 generator coverage, supported-task coverage, and Icarus simulation coverage.
- Modify `LLM/tests/test_sr2fpga_agent_runner.py`: extend planned component-topology sample expansion to include `t10_rl_accelerator_shell`.
- Modify `LLM/tests/test_sr2fpga_agent_system_his_fidelity.py`: add REQ->HIS fidelity coverage for required T10 config, sample, result, and irq ports.
- Modify `LLM/tests/test_sr2fpga_agent_deepseek.py`: add DeepSeek prompt/source expectations for T10.
- Modify `LLM/src/sr2fpga_agent/project_generator.py`: register T10, define topology metadata, interface, state, RTL files, testbench, descriptions, expected behavior, and QoR estimate.
- Modify `LLM/src/sr2fpga_agent/runner.py`: add natural/contract requirement text and generated sample naming for T10.
- Modify `LLM/src/sr2fpga_agent/system_his_fidelity.py`: add T10 required top-port expectations.
- Modify `LLM/src/sr2fpga_agent/deepseek.py`: add T10 expected RTL sources and task-specific prompt/retry guidance.
- Modify `docs/current-status.md`: record T10 as a synthetic integrated RL accelerator shell and keep the realistic-reference checkpoint explicit.

## Task 1: Generator Red Test For T10

**Files:**
- Modify: `LLM/tests/test_sr2fpga_agent_project_generator.py`

- [ ] **Step 1: Write the failing generator test**

Add this test after the T9 component-topology test:

```python
    def test_generates_composed_rl_accelerator_shell_from_t10_component_topology(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(
                task_type="composed_rl_accelerator_shell",
                width=8,
                project_name="composed_rl_accelerator_shell_8bit",
            ),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )

        _assert_multimodule_task(
            self,
            project,
            "composed_rl_accelerator_shell",
            {
                "rtl/top.v",
                "rtl/host_config_bank.v",
                "rtl/sample_capture_stage.v",
                "rtl/policy_value_core.v",
                "rtl/td_update_core.v",
                "rtl/result_stream_stage.v",
            },
            [
                "host_config_bank",
                "sample_capture_stage",
                "policy_value_core",
                "td_update_core",
                "result_stream_stage",
                ".cfg_valid(cfg_valid)",
                ".sample_valid(sample_valid)",
                ".result_valid(result_valid)",
                ".updated_value(updated_value)",
                ".irq(irq)",
            ],
        )
        system_his = _system_his(project)
        architecture = system_his["architecture"]

        self.assertEqual(architecture["generator"], "component_topology")
        self.assertEqual(architecture["topology_id"], "t10_rl_accelerator_shell")
        self.assertEqual(architecture["difficulty_tier"], "T10")
        self.assertEqual(
            [node["component"] for node in architecture["topology"]["nodes"]],
            [
                "host_config_bank",
                "sample_capture_stage",
                "policy_value_core",
                "td_update_core",
                "result_stream_stage",
            ],
        )
        self.assertIn(
            {"from": "td_update_core.updated_value", "to": "result_stream_stage.updated_value"},
            architecture["topology"]["edges"],
        )
        self.assertIn("input wire sample_valid", project.files["rtl/top.v"])
        self.assertIn("input wire [7:0] next_value", project.files["rtl/top.v"])
        self.assertIn("output wire result_valid", project.files["rtl/top.v"])
        self.assertIn("output wire [7:0] updated_value", project.files["rtl/top.v"])
        self.assertIn("output wire irq", project.files["rtl/top.v"])
        self.assertIn("expect_result(1'b0, 8'd7, 8'd7, 1'b0)", project.files["sim/tb_top.v"])
        self.assertIn("expect_result(1'b1, 8'd9, 8'd11, 1'b1)", project.files["sim/tb_top.v"])
        self.assertGreaterEqual(len(system_his["connections"]), 30)
```

Add this case to `_supported_task_cases()`:

```python
        ("composed_rl_accelerator_shell", 8, "composed_rl_accelerator_shell_8bit"),
```

Add this case to `test_multimodule_generated_testbenches_pass_under_icarus`:

```python
            ("composed_rl_accelerator_shell", 8, "composed_rl_accelerator_shell_8bit"),
```

- [ ] **Step 2: Run the test to verify RED**

Run:

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_project_generator.ProjectGeneratorTest.test_generates_composed_rl_accelerator_shell_from_t10_component_topology -q
```

Expected: FAIL with `ValueError: Unsupported task_type for V1: composed_rl_accelerator_shell`.

## Task 2: Minimal Generator Implementation

**Files:**
- Modify: `LLM/src/sr2fpga_agent/project_generator.py`

- [ ] **Step 1: Register task and topology**

Add `composed_rl_accelerator_shell` to `SUPPORTED_TASK_TYPES`, then add a
`COMPONENT_TOPOLOGIES` entry with `topology_id` `t10_rl_accelerator_shell`,
`difficulty_tier` `T10`, submodules `host_config_bank`,
`sample_capture_stage`, `policy_value_core`, `td_update_core`, and
`result_stream_stage`, and edges matching the T10 design spec.

- [ ] **Step 2: Add routing hooks**

Add branches in `_rtl_files()` and `_testbench()`:

```python
    if request.task_type == "composed_rl_accelerator_shell":
        return _composed_rl_accelerator_shell_rtl_files(request.width)
```

```python
    if request.task_type == "composed_rl_accelerator_shell":
        return _composed_rl_accelerator_shell_testbench(request.width)
```

- [ ] **Step 3: Add interface, state, and descriptions**

Add a T10 `_interface()` branch with `clk`, `rst_n`, `cfg_valid`,
`cfg_ready`, `cfg_addr`, `cfg_data`, `sample_valid`, `sample_ready`, `obs0`,
`obs1`, `reward`, `next_value`, `done_in`, `result_valid`, `result_ready`,
`selected_action`, `value_estimate`, `updated_value`, `episode_done`, and
`irq`.

Add state entries for `weight0`, `bias0`, `weight1`, `bias1`, `alpha`,
`enable`, captured sample tuple fields, result registers, and irq. Update
description, expected behavior, resource shape, natural title/summary, and
topology expected behavior text for T10.

- [ ] **Step 4: Add RTL helper and testbench**

Add `_composed_rl_accelerator_shell_rtl_files(width: int) -> dict[str, str]`
and `_composed_rl_accelerator_shell_testbench(width: int) -> str`. The
testbench must configure `weight0=2`, `bias0=1`, `weight1=3`, `bias1=0`,
`alpha=4`, `enable=1`, then check result tuples `(0, 7, 7, 0)` and
`(1, 9, 11, 1)`.

- [ ] **Step 5: Run focused generator tests**

Run:

```bash
python3 -m unittest \
  LLM.tests.test_sr2fpga_agent_project_generator.ProjectGeneratorTest.test_generates_composed_rl_accelerator_shell_from_t10_component_topology \
  LLM.tests.test_sr2fpga_agent_project_generator.ProjectGeneratorTest.test_multimodule_generated_testbenches_pass_under_icarus \
  -q
```

Expected: PASS.

## Task 3: Runner, Fidelity, And Prompt Integration

**Files:**
- Modify: `LLM/tests/test_sr2fpga_agent_runner.py`
- Modify: `LLM/tests/test_sr2fpga_agent_system_his_fidelity.py`
- Modify: `LLM/tests/test_sr2fpga_agent_deepseek.py`
- Modify: `LLM/src/sr2fpga_agent/runner.py`
- Modify: `LLM/src/sr2fpga_agent/system_his_fidelity.py`
- Modify: `LLM/src/sr2fpga_agent/deepseek.py`

- [ ] **Step 1: Add failing runner coverage**

Extend the planned-sample expansion assertions with:

```python
                (
                    "composed_rl_accelerator_shell",
                    "t10_rl_accelerator_shell",
                    "T10",
                ),
```

Run:

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_runner.RunnerConfigTest.test_planned_samples_expand_component_topology_ids -q
```

Expected: FAIL until runner T10 text is added.

- [ ] **Step 2: Add failing fidelity coverage**

Add:

```python
    def test_composed_rl_accelerator_shell_requires_config_sample_result_and_irq_ports(self) -> None:
        his = _minimal_his(
            task_type="composed_rl_accelerator_shell",
            width=8,
            top_ports=[
                {"name": "clk", "direction": "input"},
                {"name": "rst_n", "direction": "input"},
            ],
        )

        result = validate_req_his_fidelity(
            task_type="composed_rl_accelerator_shell",
            width=8,
            system_his=his,
        )

        self.assertFalse(result.ok)
        self.assertIn("REQ2HIS fidelity: composed_rl_accelerator_shell requires top port 'cfg_valid'", result.errors)
        self.assertIn("REQ2HIS fidelity: composed_rl_accelerator_shell requires top port 'sample_valid'", result.errors)
        self.assertIn("REQ2HIS fidelity: composed_rl_accelerator_shell requires top port 'updated_value'", result.errors)
        self.assertIn("REQ2HIS fidelity: composed_rl_accelerator_shell requires top port 'irq'", result.errors)
```

Run:

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_system_his_fidelity.SystemHisReqFidelityTest.test_composed_rl_accelerator_shell_requires_config_sample_result_and_irq_ports -q
```

Expected: FAIL until fidelity T10 requirements are added.

- [ ] **Step 3: Add failing DeepSeek coverage**

Add prompt/source assertions for `composed_rl_accelerator_shell` that require
`Required architecture for composed_rl_accelerator_shell`,
`host_config_bank`, `sample_capture_stage`, `policy_value_core`,
`td_update_core`, and `result_stream_stage`.

Run:

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_deepseek.DeepSeekProviderTest.test_system_his_v12_prompt_includes_rl_accelerator_shell_guidance -q
```

Expected: FAIL until DeepSeek T10 guidance is added.

- [ ] **Step 4: Implement minimal integration**

Add T10 natural/contract text in `runner.py`, T10 top-port requirements in
`system_his_fidelity.py`, and T10 expected source/prompt/retry guidance in
`deepseek.py`.

- [ ] **Step 5: Run focused integration tests**

Run:

```bash
python3 -m unittest \
  LLM.tests.test_sr2fpga_agent_runner.RunnerConfigTest.test_planned_samples_expand_component_topology_ids \
  LLM.tests.test_sr2fpga_agent_system_his_fidelity.SystemHisReqFidelityTest.test_composed_rl_accelerator_shell_requires_config_sample_result_and_irq_ports \
  LLM.tests.test_sr2fpga_agent_deepseek.DeepSeekProviderTest.test_system_his_v12_prompt_includes_rl_accelerator_shell_guidance \
  -q
```

Expected: PASS.

## Task 4: Status Documentation And Final Verification

**Files:**
- Modify: `docs/current-status.md`

- [ ] **Step 1: Update status**

Record that T10 is implemented as a synthetic integrated RL accelerator shell.
Keep a separate note that realistic RL accelerator generation now needs a user
or external reference package covering algorithm family, observation/action
shape, fixed-point policy, host protocol, fabric/software boundary, and target
board constraints.

- [ ] **Step 2: Run final verification**

Run:

```bash
python3 -m unittest discover -s LLM/tests -q
python3 -m compileall -q LLM/src/sr2fpga_agent
git diff --check
```

Expected: all commands exit 0.

- [ ] **Step 3: Commit**

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
git commit -m "feat: add T10 RL accelerator shell topology"
```

## Self-Review

- The plan covers every requirement in the T10 design spec.
- No placeholders or deferred implementation notes remain.
- Type names, topology id, submodule names, port names, and expected testbench
  values are consistent across tasks.
