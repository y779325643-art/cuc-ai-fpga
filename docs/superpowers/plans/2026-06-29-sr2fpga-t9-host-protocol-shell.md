# SR2FPGA T9 Host Protocol Shell Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the `composed_host_protocol_shell` / `t9_host_protocol_shell` task as the next component-topology step toward the reinforcement-learning accelerator case.

**Architecture:** Extend the existing deterministic `component_topology` path. T9 adds an AXI-lite-style single-beat write/read control shell, a small control/status register bank, an AXI-stream-style one-beat sample output, irq reporting, System-HIS v1.2 metadata, REQ->HIS fidelity checks, and DeepSeek two-stage guidance.

**Tech Stack:** Python `unittest`, deterministic Verilog string templates in `LLM/src/sr2fpga_agent/project_generator.py`, runner topology expansion in `LLM/src/sr2fpga_agent/runner.py`, System-HIS fidelity checks, and DeepSeek prompt helpers.

---

## File Structure

- Modify `LLM/tests/test_sr2fpga_agent_project_generator.py`: add failing generator coverage for the T9 package, topology metadata, protocol-shaped top ports, state ownership, manifest sources, deterministic simulation coverage, and supported-task coverage.
- Modify `LLM/tests/test_sr2fpga_agent_runner.py`: extend component-topology expansion to include `t9_host_protocol_shell`.
- Modify `LLM/tests/test_sr2fpga_agent_system_his_fidelity.py`: add failing REQ->HIS fidelity coverage for missing T9 AXI-lite/stream/irq ports.
- Modify `LLM/tests/test_sr2fpga_agent_deepseek.py`: add failing prompt/source expectations for T9.
- Modify `LLM/src/sr2fpga_agent/project_generator.py`: add T9 task registration, topology metadata, interface, state, control-flow membership, RTL files, testbench, descriptions, expected behavior, and predicted QoR.
- Modify `LLM/src/sr2fpga_agent/runner.py`: add T9 natural/contract requirement text.
- Modify `LLM/src/sr2fpga_agent/system_his_fidelity.py`: add T9 top-port expectations.
- Modify `LLM/src/sr2fpga_agent/deepseek.py`: add T9 expected RTL sources and task-specific prompt/retry guidance.
- Modify `docs/current-status.md`: record that T9 is implemented as a synthetic host protocol shell and keep the full-RL reference-input requirements explicit.

## Task 1: Generator Red Test For T9

**Files:**
- Modify: `LLM/tests/test_sr2fpga_agent_project_generator.py`

- [ ] **Step 1: Write the failing generator test**

Add this test after the T8 component-topology test:

```python
    def test_generates_composed_host_protocol_shell_from_t9_component_topology(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(
                task_type="composed_host_protocol_shell",
                width=8,
                project_name="composed_host_protocol_shell_8bit",
            ),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )

        _assert_multimodule_task(
            self,
            project,
            "composed_host_protocol_shell",
            {
                "rtl/top.v",
                "rtl/axi_lite_write_ctrl.v",
                "rtl/axi_lite_read_ctrl.v",
                "rtl/control_reg_bank.v",
                "rtl/sample_stream_adapter.v",
                "rtl/irq_status.v",
            },
            [
                "axi_lite_write_ctrl",
                "axi_lite_read_ctrl",
                "control_reg_bank",
                "sample_stream_adapter",
                "irq_status",
                ".s_axi_awvalid(s_axi_awvalid)",
                ".write_valid(write_valid)",
                ".read_valid(read_valid)",
                ".m_axis_tdata(m_axis_tdata)",
                ".irq_out(irq)",
            ],
        )
        system_his = _system_his(project)
        architecture = system_his["architecture"]

        self.assertEqual(architecture["generator"], "component_topology")
        self.assertEqual(architecture["topology_id"], "t9_host_protocol_shell")
        self.assertEqual(architecture["difficulty_tier"], "T9")
        self.assertEqual(
            [node["component"] for node in architecture["topology"]["nodes"]],
            ["axi_lite_write_ctrl", "axi_lite_read_ctrl", "control_reg_bank", "sample_stream_adapter", "irq_status"],
        )
        self.assertIn(
            {"from": "sample_stream_adapter.tvalid", "to": "top.m_axis_tvalid"},
            architecture["topology"]["edges"],
        )
        self.assertIn("input wire s_axi_awvalid", project.files["rtl/top.v"])
        self.assertIn("input wire [3:0] s_axi_awaddr", project.files["rtl/top.v"])
        self.assertIn("input wire [7:0] s_axi_wdata", project.files["rtl/top.v"])
        self.assertIn("output wire s_axi_rvalid", project.files["rtl/top.v"])
        self.assertIn("output wire [15:0] m_axis_tdata", project.files["rtl/top.v"])
        self.assertIn("output wire irq", project.files["rtl/top.v"])
        self.assertIn("TEST_PASS", project.files["sim/tb_top.v"])
        self.assertGreaterEqual(len(system_his["connections"]), 30)
```

Add this case to `_supported_task_cases()`:

```python
        ("composed_host_protocol_shell", 8, "composed_host_protocol_shell_8bit"),
```

Add this case to `test_multimodule_generated_testbenches_pass_under_icarus`:

```python
            ("composed_host_protocol_shell", 8, "composed_host_protocol_shell_8bit"),
```

- [ ] **Step 2: Run the test to verify RED**

Run:

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_project_generator.ProjectGeneratorTest.test_generates_composed_host_protocol_shell_from_t9_component_topology -q
```

Expected: FAIL with `ValueError: Unsupported task_type for V1: composed_host_protocol_shell`.

## Task 2: Minimal Generator Implementation

**Files:**
- Modify: `LLM/src/sr2fpga_agent/project_generator.py`

- [ ] **Step 1: Register task and topology**

Add `composed_host_protocol_shell` to `SUPPORTED_TASK_TYPES`, then add a `COMPONENT_TOPOLOGIES` entry:

```python
    "composed_host_protocol_shell": {
        "topology_id": "t9_host_protocol_shell",
        "difficulty_tier": "T9",
        "submodules": [
            "axi_lite_write_ctrl",
            "axi_lite_read_ctrl",
            "control_reg_bank",
            "sample_stream_adapter",
            "irq_status",
        ],
        "nodes": [
            {"id": "write_ctrl", "component": "axi_lite_write_ctrl"},
            {"id": "read_ctrl", "component": "axi_lite_read_ctrl"},
            {"id": "regs", "component": "control_reg_bank"},
            {"id": "stream", "component": "sample_stream_adapter"},
            {"id": "irq", "component": "irq_status"},
        ],
        "edges": [
            {"from": "top.s_axi_awvalid", "to": "axi_lite_write_ctrl.awvalid"},
            {"from": "top.s_axi_awaddr", "to": "axi_lite_write_ctrl.awaddr"},
            {"from": "top.s_axi_wvalid", "to": "axi_lite_write_ctrl.wvalid"},
            {"from": "top.s_axi_wdata", "to": "axi_lite_write_ctrl.wdata"},
            {"from": "top.s_axi_wstrb", "to": "axi_lite_write_ctrl.wstrb"},
            {"from": "axi_lite_write_ctrl.awready", "to": "top.s_axi_awready"},
            {"from": "axi_lite_write_ctrl.wready", "to": "top.s_axi_wready"},
            {"from": "axi_lite_write_ctrl.bvalid", "to": "top.s_axi_bvalid"},
            {"from": "top.s_axi_bready", "to": "axi_lite_write_ctrl.bready"},
            {"from": "axi_lite_write_ctrl.write_valid", "to": "control_reg_bank.write_valid"},
            {"from": "axi_lite_write_ctrl.write_addr", "to": "control_reg_bank.write_addr"},
            {"from": "axi_lite_write_ctrl.write_data", "to": "control_reg_bank.write_data"},
            {"from": "top.s_axi_arvalid", "to": "axi_lite_read_ctrl.arvalid"},
            {"from": "top.s_axi_araddr", "to": "axi_lite_read_ctrl.araddr"},
            {"from": "axi_lite_read_ctrl.arready", "to": "top.s_axi_arready"},
            {"from": "axi_lite_read_ctrl.read_valid", "to": "control_reg_bank.read_valid"},
            {"from": "axi_lite_read_ctrl.read_addr", "to": "control_reg_bank.read_addr"},
            {"from": "control_reg_bank.read_data", "to": "top.s_axi_rdata"},
            {"from": "axi_lite_read_ctrl.rvalid", "to": "top.s_axi_rvalid"},
            {"from": "top.s_axi_rready", "to": "axi_lite_read_ctrl.rready"},
            {"from": "control_reg_bank.start_pulse", "to": "sample_stream_adapter.start"},
            {"from": "control_reg_bank.sample0", "to": "sample_stream_adapter.sample0"},
            {"from": "control_reg_bank.sample1", "to": "sample_stream_adapter.sample1"},
            {"from": "sample_stream_adapter.tvalid", "to": "top.m_axis_tvalid"},
            {"from": "top.m_axis_tready", "to": "sample_stream_adapter.tready"},
            {"from": "sample_stream_adapter.tdata", "to": "top.m_axis_tdata"},
            {"from": "sample_stream_adapter.tlast", "to": "top.m_axis_tlast"},
            {"from": "sample_stream_adapter.stream_done", "to": "control_reg_bank.stream_done"},
            {"from": "control_reg_bank.irq_state", "to": "irq_status.irq_in"},
            {"from": "irq_status.irq_out", "to": "top.irq"},
        ],
    },
```

- [ ] **Step 2: Add routing hooks**

Add branches in `_rtl_files()` and `_testbench()`:

```python
    if request.task_type == "composed_host_protocol_shell":
        return _composed_host_protocol_shell_rtl_files(request.width)
```

```python
    if request.task_type == "composed_host_protocol_shell":
        return _composed_host_protocol_shell_testbench(request.width)
```

- [ ] **Step 3: Add interface, state, and descriptions**

Add a T9 `_interface()` branch with top ports `clk`, `rst_n`,
`s_axi_awvalid`, `s_axi_awready`, `s_axi_awaddr`, `s_axi_wvalid`,
`s_axi_wready`, `s_axi_wdata`, `s_axi_wstrb`, `s_axi_bvalid`,
`s_axi_bready`, `s_axi_arvalid`, `s_axi_arready`, `s_axi_araddr`,
`s_axi_rvalid`, `s_axi_rready`, `s_axi_rdata`, `m_axis_tvalid`,
`m_axis_tready`, `m_axis_tdata`, `m_axis_tlast`, and `irq`.

Add T9 state in `_v12_state()`:

```python
registers.extend([
    {"name": "ctrl", "owner": reg_owner, "width": request.width},
    {"name": "sample0", "owner": reg_owner, "width": request.width},
    {"name": "sample1", "owner": reg_owner, "width": request.width},
    {"name": "busy", "owner": reg_owner, "width": 1},
    {"name": "done", "owner": reg_owner, "width": 1},
    {"name": "irq_state", "owner": reg_owner, "width": 1},
])
```

Add T9 to the streaming valid-ready control-flow task set.

Update `_default_description()`, `_expected_behavior()`, `_resource_shape()`,
`_natural_component_title()`, `_natural_component_summary()`, and
`_topology_expected_behavior()` with T9 text.

- [ ] **Step 4: Add RTL helper**

Add `_composed_host_protocol_shell_rtl_files(width: int) -> dict[str, str]`. It
must return `rtl/top.v`, `rtl/axi_lite_write_ctrl.v`,
`rtl/axi_lite_read_ctrl.v`, `rtl/control_reg_bank.v`,
`rtl/sample_stream_adapter.v`, and `rtl/irq_status.v`. The generated RTL should
use a single-beat AXI-lite-style write/read subset and a one-beat AXI-stream
output.

- [ ] **Step 5: Add testbench helper**

Add `_composed_host_protocol_shell_testbench(width: int) -> str`. It must:

```text
write addr 0x04 = 0x12
write addr 0x08 = 0x34
write addr 0x00 = 0x01
expect m_axis_tvalid=1, m_axis_tdata=0x3412, m_axis_tlast=1
read addr 0x0c, expect status bit1=done and bit2=irq
write addr 0x00 = 0x02
read addr 0x0c, expect irq bit cleared
print TEST_PASS
```

- [ ] **Step 6: Run the focused generator and Icarus tests**

Run:

```bash
python3 -m unittest \
  LLM.tests.test_sr2fpga_agent_project_generator.ProjectGeneratorTest.test_generates_composed_host_protocol_shell_from_t9_component_topology \
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
`line_b_targets` to `{"max_samples": 9}`, change `count` to `9`, add
`"t9_host_protocol_shell"` to `topology_ids`, and append expected sample:

```python
                (
                    "sample_runner_t9_host_protocol_shell_8_000009",
                    "composed_host_protocol_shell",
                    "t9_host_protocol_shell",
                    "T9",
                ),
```

Also assert:

```python
        self.assertEqual(samples[8].metadata(config)["topology_id"], "t9_host_protocol_shell")
        self.assertIn("component topology t9_host_protocol_shell", samples[8].requirement)
        self.assertIn("axi_lite_write_ctrl", samples[8].requirement)
```

- [ ] **Step 2: Add fidelity red test**

Add a fidelity test:

```python
    def test_composed_host_protocol_shell_requires_axi_stream_and_irq_ports(self) -> None:
        request = ProjectRequest(
            task_type="composed_host_protocol_shell",
            width=8,
            project_name="host_protocol_shell_8bit",
        )
        system_his = _deterministic_system_his(request)
        system_his["top"]["ports"] = [
            port
            for port in system_his["top"]["ports"]
            if port["name"] not in {"s_axi_awvalid", "m_axis_tdata", "irq"}
        ]

        result = check_system_his_req_fidelity(request, system_his)

        self.assertFalse(result.passed)
        self.assertIn("REQ2HIS fidelity: composed_host_protocol_shell requires top port 's_axi_awvalid'", result.errors)
        self.assertIn("REQ2HIS fidelity: composed_host_protocol_shell requires top port 'm_axis_tdata'", result.errors)
        self.assertIn("REQ2HIS fidelity: composed_host_protocol_shell requires top port 'irq'", result.errors)
```

- [ ] **Step 3: Run red tests**

Run:

```bash
python3 -m unittest \
  LLM.tests.test_sr2fpga_agent_runner.RunnerConfigTest.test_planned_samples_expand_component_topology_ids \
  LLM.tests.test_sr2fpga_agent_system_his_fidelity.SystemHisReqFidelityTest.test_composed_host_protocol_shell_requires_axi_stream_and_irq_ports \
  -q
```

Expected: FAIL because the runner does not map `t9_host_protocol_shell` and
fidelity has no T9 port requirements.

## Task 4: Runner And Fidelity Implementation

**Files:**
- Modify: `LLM/src/sr2fpga_agent/runner.py`
- Modify: `LLM/src/sr2fpga_agent/system_his_fidelity.py`

- [ ] **Step 1: Add runner mappings**

Add `composed_host_protocol_shell`, tier `T9`, and requirement text that names
`axi_lite_write_ctrl`, `axi_lite_read_ctrl`, `control_reg_bank`,
`sample_stream_adapter`, and `irq_status`.

- [ ] **Step 2: Add fidelity port contract**

Add `_TASK_TOP_PORTS["composed_host_protocol_shell"]` requiring the T9 AXI-lite
subset, stream subset, and irq ports:

```python
{
    "s_axi_awvalid": {"direction": "input"},
    "s_axi_awready": {"direction": "output"},
    "s_axi_awaddr": {"direction": "input", "width": 4},
    "s_axi_wvalid": {"direction": "input"},
    "s_axi_wready": {"direction": "output"},
    "s_axi_wdata": {"direction": "input", "width": "request"},
    "s_axi_wstrb": {"direction": "input"},
    "s_axi_bvalid": {"direction": "output"},
    "s_axi_bready": {"direction": "input"},
    "s_axi_arvalid": {"direction": "input"},
    "s_axi_arready": {"direction": "output"},
    "s_axi_araddr": {"direction": "input", "width": 4},
    "s_axi_rvalid": {"direction": "output"},
    "s_axi_rready": {"direction": "input"},
    "s_axi_rdata": {"direction": "output", "width": "request"},
    "m_axis_tvalid": {"direction": "output"},
    "m_axis_tready": {"direction": "input"},
    "m_axis_tdata": {"direction": "output"},
    "m_axis_tlast": {"direction": "output"},
    "irq": {"direction": "output"},
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

Add this test after the T8 prompt test:

```python
    def test_system_his_v12_prompt_includes_host_protocol_shell_guidance(self) -> None:
        request = ProjectRequest(
            task_type="composed_host_protocol_shell",
            width=8,
            project_name="host_protocol_shell_8bit",
            description="Generate a host protocol shell.",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        user_prompt = _system_his_v12_messages(request, platform)[1]["content"]

        self.assertIn("Required architecture for composed_host_protocol_shell", user_prompt)
        self.assertIn("axi_lite_write_ctrl", user_prompt)
        self.assertIn("axi_lite_read_ctrl", user_prompt)
        self.assertIn("control_reg_bank", user_prompt)
        self.assertIn("sample_stream_adapter", user_prompt)
        self.assertIn("rtl/axi_lite_write_ctrl.v", user_prompt)
```

- [ ] **Step 2: Run RED**

Run:

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_deepseek.DeepSeekProviderTest.test_system_his_v12_prompt_includes_host_protocol_shell_guidance -q
```

Expected: FAIL because the T9 prompt guidance is absent.

- [ ] **Step 3: Implement prompt/source guidance**

Add `composed_host_protocol_shell` to `MULTIMODULE_RTL_EXAMPLES`,
`_system_his_v12_task_guidance()`, and retry guidance. The guidance must name
the five T9 submodules, AXI-lite-style control ports, AXI-stream output ports,
`irq`, and expected source files.

- [ ] **Step 4: Run GREEN**

Run the Step 2 command again.

Expected: PASS.

## Task 6: Status Update And Final Verification

**Files:**
- Modify: `docs/current-status.md`

- [ ] **Step 1: Update status document**

Record that the deterministic component-topology ladder now includes T9
`composed_host_protocol_shell` / `t9_host_protocol_shell`. Keep a separate note
that realistic RL accelerator generation still requires user-provided algorithm,
observation/action, replay schema, fixed-point, fabric/host boundary, protocol
map, and resource-reference inputs.

- [ ] **Step 2: Run focused verification**

Run:

```bash
python3 -m unittest \
  LLM.tests.test_sr2fpga_agent_project_generator.ProjectGeneratorTest.test_generates_composed_host_protocol_shell_from_t9_component_topology \
  LLM.tests.test_sr2fpga_agent_project_generator.ProjectGeneratorTest.test_multimodule_generated_testbenches_pass_under_icarus \
  LLM.tests.test_sr2fpga_agent_runner.RunnerConfigTest.test_planned_samples_expand_component_topology_ids \
  LLM.tests.test_sr2fpga_agent_system_his_fidelity.SystemHisReqFidelityTest.test_composed_host_protocol_shell_requires_axi_stream_and_irq_ports \
  LLM.tests.test_sr2fpga_agent_deepseek.DeepSeekProviderTest.test_system_his_v12_prompt_includes_host_protocol_shell_guidance \
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
git commit -m "feat: add T9 host protocol shell topology"
```

## Self-Review

- Spec coverage: generator, runner, fidelity, DeepSeek guidance, System-HIS metadata, deterministic RTL/testbench, Icarus simulation coverage, and status documentation are each covered by a task.
- Placeholder scan: no task uses open-ended placeholder instructions.
- Type consistency: task type, topology id, submodule names, AXI-lite-style ports, AXI-stream-style ports, irq behavior, and expected source filenames match the T9 design spec.
