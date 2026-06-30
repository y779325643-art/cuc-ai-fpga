# SR2FPGA T5 Vector MAC Feature Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the `composed_vector_mac_pipeline` / `t5_vector_mac_pipeline` task as the next component-topology step toward the reinforcement-learning accelerator case.

**Architecture:** Extend the existing deterministic `component_topology` path instead of creating a new runner mode. T5 adds a dual-stream feature/weight input, a new `vector_mac_core`, an existing `stream_stage` output, System-HIS v1.2 metadata, REQ->HIS fidelity checks, and DeepSeek two-stage guidance.

**Tech Stack:** Python `unittest`, deterministic Verilog string templates in `LLM/src/sr2fpga_agent/project_generator.py`, runner topology expansion in `LLM/src/sr2fpga_agent/runner.py`, System-HIS fidelity checks, and DeepSeek prompt helpers.

---

## File Structure

- Modify `LLM/tests/test_sr2fpga_agent_project_generator.py`: add failing generator tests for the T5 package, System-HIS metadata, manifest sources, and deterministic simulation coverage.
- Modify `LLM/tests/test_sr2fpga_agent_runner.py`: add failing coverage for `t5_vector_mac_pipeline` expansion from `component_topology`.
- Modify `LLM/tests/test_sr2fpga_agent_system_his_fidelity.py`: add failing REQ->HIS fidelity coverage for missing T5 ports.
- Modify `LLM/tests/test_sr2fpga_agent_deepseek.py`: add failing prompt/source expectations for T5.
- Modify `LLM/src/sr2fpga_agent/project_generator.py`: add T5 task registration, topology metadata, interface, System-HIS, RTL files, testbench, descriptions, and predicted QoR.
- Modify `LLM/src/sr2fpga_agent/system_his_fidelity.py`: add T5 top-port expectations.
- Modify `LLM/src/sr2fpga_agent/deepseek.py`: add T5 expected RTL sources and task-specific prompt/retry guidance.

## Task 1: Generator Red Test For T5

**Files:**
- Modify: `LLM/tests/test_sr2fpga_agent_project_generator.py`

- [ ] **Step 1: Write the failing generator test**

Add this test after `test_generates_composed_dual_stream_join_from_t4_component_topology`:

```python
    def test_generates_composed_vector_mac_pipeline_from_t5_component_topology(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(
                task_type="composed_vector_mac_pipeline",
                width=8,
                project_name="composed_vector_mac_pipeline_8bit",
            ),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )

        _assert_multimodule_task(
            self,
            project,
            "composed_vector_mac_pipeline",
            {
                "rtl/top.v",
                "rtl/skid_buffer.v",
                "rtl/vector_mac_core.v",
                "rtl/stream_stage.v",
            },
            [
                "skid_buffer",
                "vector_mac_core",
                "stream_stage",
                ".feature_valid(feature_valid)",
                ".weight_valid(weight_valid)",
                ".score_valid(score_valid)",
            ],
        )
        system_his = _system_his(project)
        architecture = system_his["architecture"]

        self.assertEqual(architecture["generator"], "component_topology")
        self.assertEqual(architecture["topology_id"], "t5_vector_mac_pipeline")
        self.assertEqual(architecture["difficulty_tier"], "T5")
        self.assertEqual(
            [node["component"] for node in architecture["topology"]["nodes"]],
            ["skid_buffer", "skid_buffer", "vector_mac_core", "stream_stage"],
        )
        self.assertIn(
            {"from": "vector_mac_core.score_data", "to": "stream_stage.in_data"},
            architecture["topology"]["edges"],
        )
        self.assertIn("input wire [7:0] feature_data", project.files["rtl/top.v"])
        self.assertIn("input wire [7:0] weight_data", project.files["rtl/top.v"])
        self.assertIn("input wire [15:0] bias", project.files["rtl/top.v"])
        self.assertIn("output wire [15:0] score_data", project.files["rtl/top.v"])
        self.assertIn("TEST_PASS", project.files["sim/tb_top.v"])
        self.assertGreaterEqual(len(system_his["connections"]), 18)
```

Also add this case to `_supported_task_cases()`:

```python
        ("composed_vector_mac_pipeline", 8, "composed_vector_mac_pipeline_8bit"),
```

- [ ] **Step 2: Run the test to verify RED**

Run:

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_project_generator.ProjectGeneratorTests.test_generates_composed_vector_mac_pipeline_from_t5_component_topology -q
```

Expected: FAIL with `ValueError: Unsupported task_type for V1: composed_vector_mac_pipeline`.

## Task 2: Minimal Generator Implementation

**Files:**
- Modify: `LLM/src/sr2fpga_agent/project_generator.py`

- [ ] **Step 1: Register task and topology**

Add `composed_vector_mac_pipeline` to `SUPPORTED_TASK_TYPES`, then add this entry to `COMPONENT_TOPOLOGIES`:

```python
    "composed_vector_mac_pipeline": {
        "topology_id": "t5_vector_mac_pipeline",
        "difficulty_tier": "T5",
        "submodules": ["skid_buffer", "vector_mac_core", "stream_stage"],
        "nodes": [
            {"id": "feature_buffer", "component": "skid_buffer"},
            {"id": "weight_buffer", "component": "skid_buffer"},
            {"id": "mac", "component": "vector_mac_core"},
            {"id": "score_stage", "component": "stream_stage"},
        ],
        "edges": [
            {"from": "top.feature_valid", "to": "skid_buffer.in_valid"},
            {"from": "top.feature_data", "to": "skid_buffer.in_data"},
            {"from": "top.weight_valid", "to": "skid_buffer.in_valid"},
            {"from": "top.weight_data", "to": "skid_buffer.in_data"},
            {"from": "skid_buffer.out_valid", "to": "vector_mac_core.feature_valid"},
            {"from": "skid_buffer.out_data", "to": "vector_mac_core.feature_data"},
            {"from": "skid_buffer.out_valid", "to": "vector_mac_core.weight_valid"},
            {"from": "skid_buffer.out_data", "to": "vector_mac_core.weight_data"},
            {"from": "vector_mac_core.feature_ready", "to": "skid_buffer.out_ready"},
            {"from": "vector_mac_core.weight_ready", "to": "skid_buffer.out_ready"},
            {"from": "top.bias", "to": "vector_mac_core.bias"},
            {"from": "vector_mac_core.score_valid", "to": "stream_stage.in_valid"},
            {"from": "vector_mac_core.score_data", "to": "stream_stage.in_data"},
            {"from": "stream_stage.in_ready", "to": "vector_mac_core.score_ready"},
            {"from": "stream_stage.out_valid", "to": "top.score_valid"},
            {"from": "stream_stage.out_data", "to": "top.score_data"},
            {"from": "top.score_ready", "to": "stream_stage.out_ready"},
        ],
    },
```

- [ ] **Step 2: Add routing hooks**

Add these branches beside the existing composed topology branches:

```python
    if request.task_type == "composed_vector_mac_pipeline":
        return _composed_vector_mac_pipeline_rtl_files(request.width)
```

```python
    if request.task_type == "composed_vector_mac_pipeline":
        return _composed_vector_mac_pipeline_testbench(request.width)
```

- [ ] **Step 3: Add RTL helper**

Add `_composed_vector_mac_pipeline_rtl_files(width: int) -> dict[str, str]` near the other composed RTL helpers. It must return `rtl/top.v`, `rtl/skid_buffer.v`, `rtl/vector_mac_core.v`, and `rtl/stream_stage.v`. The top module must expose feature/weight/bias/score valid-ready ports and instantiate two skid buffers, one `vector_mac_core`, and one `stream_stage`.

- [ ] **Step 4: Add testbench helper**

Add `_composed_vector_mac_pipeline_testbench(width: int) -> str` near the other composed testbench helpers. The testbench must send two four-beat vectors and check:

```verilog
// Vector 1: bias 3 + 1*2 + 2*3 + 3*4 + 4*5 = 43
// Vector 2: bias 1 + 2*1 + 1*2 + 0*3 + 3*4 = 17
```

It must print `TEST_PASS` only after both expected scores are observed.

- [ ] **Step 5: Add descriptions**

Update `_description`, `_natural_component_title`, `_natural_component_summary`, and `_topology_expected_behavior` with T5 text:

```python
"composed_vector_mac_pipeline": "streaming vector MAC feature pipeline"
```

Use behavior text:

```python
"paired feature and weight streams are buffered, multiplied and accumulated over a fixed vector length, biased, and staged as score output"
```

- [ ] **Step 6: Run the focused generator test**

Run:

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_project_generator.ProjectGeneratorTests.test_generates_composed_vector_mac_pipeline_from_t5_component_topology -q
```

Expected: PASS.

## Task 3: System-HIS And Runner Red Tests

**Files:**
- Modify: `LLM/tests/test_sr2fpga_agent_runner.py`
- Modify: `LLM/tests/test_sr2fpga_agent_system_his_fidelity.py`

- [ ] **Step 1: Extend runner topology expansion red test**

In `test_planned_samples_expand_component_topology_ids`, change `line_b_targets` to `{"max_samples": 5}`, `count` to `5`, add `"t5_vector_mac_pipeline"` to `topology_ids`, and append this expected sample:

```python
                (
                    "sample_runner_t5_vector_mac_pipeline_8_000005",
                    "composed_vector_mac_pipeline",
                    "t5_vector_mac_pipeline",
                    "T5",
                ),
```

Also add:

```python
        self.assertEqual(samples[4].metadata(config)["topology_id"], "t5_vector_mac_pipeline")
        self.assertIn("component topology t5_vector_mac_pipeline", samples[4].requirement)
        self.assertIn("vector_mac_core", samples[4].requirement)
```

- [ ] **Step 2: Add fidelity red test**

Add this test to `LLM/tests/test_sr2fpga_agent_system_his_fidelity.py`:

```python
    def test_composed_vector_mac_pipeline_requires_feature_weight_and_score_ports(self) -> None:
        request = ProjectRequest(
            task_type="composed_vector_mac_pipeline",
            width=8,
            project_name="vector_mac_8bit",
        )
        system_his = _system_his_for(request)
        system_his["interfaces"]["top"]["inputs"] = [
            port for port in system_his["interfaces"]["top"]["inputs"] if port["name"] != "feature_data"
        ]
        system_his["interfaces"]["top"]["outputs"] = [
            port for port in system_his["interfaces"]["top"]["outputs"] if port["name"] != "score_data"
        ]

        result = check_system_his_req_fidelity(request, system_his)

        self.assertFalse(result.passed)
        self.assertIn("REQ2HIS fidelity: composed_vector_mac_pipeline requires top port 'feature_data'", result.errors)
        self.assertIn("REQ2HIS fidelity: composed_vector_mac_pipeline requires top port 'score_data'", result.errors)
```

- [ ] **Step 3: Run the red tests**

Run:

```bash
python3 -m unittest \
  LLM.tests.test_sr2fpga_agent_runner.RunnerTests.test_planned_samples_expand_component_topology_ids \
  LLM.tests.test_sr2fpga_agent_system_his_fidelity.SystemHisFidelityTests.test_composed_vector_mac_pipeline_requires_feature_weight_and_score_ports \
  -q
```

Expected before implementation: at least the runner test fails because `t5_vector_mac_pipeline` is unsupported, and the fidelity test fails until T5 top-port expectations exist.

## Task 4: Runner And Fidelity Implementation

**Files:**
- Modify: `LLM/src/sr2fpga_agent/project_generator.py`
- Modify: `LLM/src/sr2fpga_agent/system_his_fidelity.py`

- [ ] **Step 1: Let runner expansion inherit T5**

No runner code should be necessary if `COMPONENT_TOPOLOGIES` has the T5 entry. Confirm this by rerunning the runner test after Task 2.

- [ ] **Step 2: Add T5 top-port expectations**

Add this entry to `_TASK_TOP_PORTS` in `system_his_fidelity.py`:

```python
    "composed_vector_mac_pipeline": {
        "clk": {"direction": "input"},
        "rst_n": {"direction": "input"},
        "feature_valid": {"direction": "input"},
        "feature_data": {"direction": "input", "width": "request"},
        "weight_valid": {"direction": "input"},
        "weight_data": {"direction": "input", "width": "request"},
        "bias": {"direction": "input"},
        "score_ready": {"direction": "input"},
        "feature_ready": {"direction": "output"},
        "weight_ready": {"direction": "output"},
        "score_valid": {"direction": "output"},
        "score_data": {"direction": "output"},
    },
```

- [ ] **Step 3: Run the focused tests**

Run:

```bash
python3 -m unittest \
  LLM.tests.test_sr2fpga_agent_runner.RunnerTests.test_planned_samples_expand_component_topology_ids \
  LLM.tests.test_sr2fpga_agent_system_his_fidelity.SystemHisFidelityTests.test_composed_vector_mac_pipeline_requires_feature_weight_and_score_ports \
  -q
```

Expected: PASS.

## Task 5: DeepSeek Red Test And Prompt Implementation

**Files:**
- Modify: `LLM/tests/test_sr2fpga_agent_deepseek.py`
- Modify: `LLM/src/sr2fpga_agent/deepseek.py`

- [ ] **Step 1: Add DeepSeek red test**

Add a test near the existing task-guidance prompt tests:

```python
    def test_system_his_prompt_includes_vector_mac_pipeline_guidance(self) -> None:
        request = ProjectRequest(
            task_type="composed_vector_mac_pipeline",
            width=8,
            project_name="vector_mac_8bit",
        )
        messages = _system_his_messages(
            request,
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )
        user_prompt = messages[-1]["content"]

        self.assertIn("Required architecture for composed_vector_mac_pipeline", user_prompt)
        self.assertIn("vector_mac_core", user_prompt)
        self.assertIn("feature_buffer", user_prompt)
        self.assertIn("weight_buffer", user_prompt)
        self.assertIn("rtl/vector_mac_core.v", user_prompt)
```

- [ ] **Step 2: Run the red test**

Run:

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_deepseek.DeepSeekTests.test_system_his_prompt_includes_vector_mac_pipeline_guidance -q
```

Expected: FAIL because the T5 prompt guidance does not exist.

- [ ] **Step 3: Add T5 expected RTL sources**

Add to `MULTIMODULE_RTL_EXAMPLES`:

```python
    "composed_vector_mac_pipeline": [
        "rtl/top.v",
        "rtl/skid_buffer.v",
        "rtl/vector_mac_core.v",
        "rtl/stream_stage.v",
    ],
```

- [ ] **Step 4: Add task guidance**

Add a `composed_vector_mac_pipeline` branch in `_system_his_v12_task_guidance()`:

```python
    if task_type == "composed_vector_mac_pipeline":
        return (
            "Required architecture for composed_vector_mac_pipeline:\n"
            "- components: skid_buffer, vector_mac_core, stream_stage\n"
            "- instances: feature_buffer, weight_buffer, mac_core, score_stage\n"
            "- feature_buffer and weight_buffer must both reference component skid_buffer.\n"
            "- vector_mac_core owns vector index, accumulator, and pending score state.\n"
            "- top ports must include feature_valid, feature_data, feature_ready, weight_valid, "
            "weight_data, weight_ready, bias, score_valid, score_data, and score_ready.\n"
            "- data_flow must pair feature and weight streams into vector_mac_core and stage score output.\n"
            "- artifacts.rtl_sources must include rtl/top.v, rtl/skid_buffer.v, "
            "rtl/vector_mac_core.v, and rtl/stream_stage.v."
        )
```

- [ ] **Step 5: Add retry guidance**

Add a `composed_vector_mac_pipeline` branch in `_system_his_v12_retry_guidance()`:

```python
    if task_type == "composed_vector_mac_pipeline":
        return (
            common
            + "- Required top ports: clk, rst_n, feature_valid, feature_data, weight_valid, "
            "weight_data, bias, score_ready, feature_ready, weight_ready, score_valid, score_data\n"
            "- Do not rename these ports to AXI-style names such as s_axis_tvalid, s_axis_tdata, "
            "m_axis_tvalid, or m_axis_tdata.\n"
        )
```

- [ ] **Step 6: Run the DeepSeek test**

Run:

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_deepseek.DeepSeekTests.test_system_his_prompt_includes_vector_mac_pipeline_guidance -q
```

Expected: PASS.

## Task 6: Verification And Commit

**Files:**
- Verify all touched files.

- [ ] **Step 1: Run focused tests**

Run:

```bash
python3 -m unittest \
  LLM.tests.test_sr2fpga_agent_project_generator \
  LLM.tests.test_sr2fpga_agent_runner.RunnerTests.test_planned_samples_expand_component_topology_ids \
  LLM.tests.test_sr2fpga_agent_system_his_fidelity \
  LLM.tests.test_sr2fpga_agent_deepseek.DeepSeekTests.test_system_his_prompt_includes_vector_mac_pipeline_guidance \
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

- [ ] **Step 4: Check staged diff**

Run:

```bash
git diff --check
git status --short
```

Expected: no whitespace errors; only intended T5 implementation/test/doc files changed.

- [ ] **Step 5: Commit**

Run:

```bash
git add LLM/src/sr2fpga_agent/project_generator.py \
  LLM/src/sr2fpga_agent/system_his_fidelity.py \
  LLM/src/sr2fpga_agent/deepseek.py \
  LLM/tests/test_sr2fpga_agent_project_generator.py \
  LLM/tests/test_sr2fpga_agent_runner.py \
  LLM/tests/test_sr2fpga_agent_system_his_fidelity.py \
  LLM/tests/test_sr2fpga_agent_deepseek.py
git commit -m "feat: add T5 vector MAC topology"
```

Expected: commit succeeds.

## Self-Review

- Spec coverage: T5 task type, topology id, difficulty tier, dual input streams, vector MAC core, output stage, System-HIS fields, runner expansion, REQ->HIS fidelity, DeepSeek guidance, and verification commands are covered.
- Human input: no user-provided reference project is required for T5; the plan preserves the later T7/full-RL checkpoint where real workload shape and fabric/software boundary should be requested.
- Placeholder scan: the plan contains concrete steps, commands, and expected results without open-ended fill-ins.
- Scope check: this plan implements one deterministic intermediate topology, not the full RL accelerator.
