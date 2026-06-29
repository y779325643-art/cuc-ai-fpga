# SR2FPGA T11 Batch RL Accelerator Shell Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the `composed_batch_rl_accelerator_shell` / `t11_batch_rl_accelerator_shell` task as the two-lane synthetic batch step after T10.

**Architecture:** Extend the deterministic `component_topology` path with shared config, two-lane batch sample capture, dual-lane policy/value compute, dual-lane TD update, result backpressure, and irq reporting.

**Tech Stack:** Python `unittest`, deterministic Verilog string templates in `LLM/src/sr2fpga_agent/project_generator.py`, runner topology expansion in `LLM/src/sr2fpga_agent/runner.py`, System-HIS fidelity checks, and DeepSeek prompt helpers.

---

## File Structure

- Modify `LLM/tests/test_sr2fpga_agent_project_generator.py`: add T11 generator coverage, supported-task coverage, and Icarus simulation coverage.
- Modify `LLM/tests/test_sr2fpga_agent_runner.py`: extend planned component-topology sample expansion to include `t11_batch_rl_accelerator_shell`.
- Modify `LLM/tests/test_sr2fpga_agent_system_his_fidelity.py`: add REQ->HIS fidelity coverage for required T11 config, batch, lane result, and irq ports.
- Modify `LLM/tests/test_sr2fpga_agent_deepseek.py`: add DeepSeek prompt/source expectations for T11.
- Modify `LLM/src/sr2fpga_agent/project_generator.py`: register T11, define topology metadata, interface, state, RTL files, testbench, descriptions, expected behavior, and QoR estimate.
- Modify `LLM/src/sr2fpga_agent/runner.py`: add natural/contract requirement text and generated sample naming for T11.
- Modify `LLM/src/sr2fpga_agent/system_his_fidelity.py`: add T11 required top-port expectations.
- Modify `LLM/src/sr2fpga_agent/deepseek.py`: add T11 expected RTL sources and task-specific prompt/retry guidance.
- Modify `docs/current-status.md`: record T11 as a synthetic two-lane batch RL shell and keep the realistic-reference checkpoint explicit.

## Task 1: Red Tests

**Files:**
- Modify: `LLM/tests/test_sr2fpga_agent_project_generator.py`
- Modify: `LLM/tests/test_sr2fpga_agent_runner.py`
- Modify: `LLM/tests/test_sr2fpga_agent_system_his_fidelity.py`
- Modify: `LLM/tests/test_sr2fpga_agent_deepseek.py`

- [ ] **Step 1: Add generator red test**

Add `test_generates_composed_batch_rl_accelerator_shell_from_t11_component_topology`. It should generate `composed_batch_rl_accelerator_shell`, expect RTL sources `rtl/top.v`, `rtl/batch_config_bank.v`, `rtl/batch_sample_buffer.v`, `rtl/dual_policy_value_core.v`, `rtl/dual_td_update_core.v`, and `rtl/batch_result_stage.v`, assert topology id `t11_batch_rl_accelerator_shell`, tier `T11`, batch-shaped top ports, and testbench checks for lane A `(0, 7, 7)` and lane B `(1, 9, 11)`.

- [ ] **Step 2: Add manifest and Icarus coverage**

Add `("composed_batch_rl_accelerator_shell", 8, "composed_batch_rl_accelerator_shell_8bit")` to `_supported_task_cases()` and `test_multimodule_generated_testbenches_pass_under_icarus`.

- [ ] **Step 3: Add runner red test**

Extend `test_planned_samples_expand_component_topology_ids` to use `count=11`, `max_samples=11`, include `t11_batch_rl_accelerator_shell`, and assert the generated sample has task type `composed_batch_rl_accelerator_shell`, topology id `t11_batch_rl_accelerator_shell`, tier `T11`, and requirement text naming `dual_policy_value_core` and `dual_td_update_core`.

- [ ] **Step 4: Add fidelity red test**

Add a test that removes `cfg_valid`, `batch_valid`, `updated_value_b`, and `irq` from a deterministic T11 System-HIS and expects REQ->HIS fidelity errors for those missing ports.

- [ ] **Step 5: Add DeepSeek red test**

Add `test_system_his_v12_prompt_includes_batch_rl_accelerator_shell_guidance` and assert the prompt includes `Required architecture for composed_batch_rl_accelerator_shell`, `batch_config_bank`, `batch_sample_buffer`, `dual_policy_value_core`, `dual_td_update_core`, `batch_result_stage`, and `rtl/batch_result_stage.v`.

- [ ] **Step 6: Verify RED**

Run:

```bash
python3 -m unittest \
  LLM.tests.test_sr2fpga_agent_project_generator.ProjectGeneratorTest.test_generates_composed_batch_rl_accelerator_shell_from_t11_component_topology \
  LLM.tests.test_sr2fpga_agent_runner.RunnerConfigTest.test_planned_samples_expand_component_topology_ids \
  LLM.tests.test_sr2fpga_agent_system_his_fidelity.SystemHisReqFidelityTest.test_composed_batch_rl_accelerator_shell_requires_config_batch_result_and_irq_ports \
  LLM.tests.test_sr2fpga_agent_deepseek.DeepSeekProviderTest.test_system_his_v12_prompt_includes_batch_rl_accelerator_shell_guidance \
  -q
```

Expected: FAIL until T11 support is added.

## Task 2: Generator Implementation

**Files:**
- Modify: `LLM/src/sr2fpga_agent/project_generator.py`

- [ ] **Step 1: Register T11**

Add `composed_batch_rl_accelerator_shell` to `SUPPORTED_TASK_TYPES` and `COMPONENT_TOPOLOGIES` with topology id `t11_batch_rl_accelerator_shell`, tier `T11`, and submodules `batch_config_bank`, `batch_sample_buffer`, `dual_policy_value_core`, `dual_td_update_core`, and `batch_result_stage`.

- [ ] **Step 2: Add System-HIS metadata**

Add T11 state ownership for shared config registers, captured lane A/B samples, lane A/B result registers, `batch_done`, and `irq_state`. Add the task to the valid-ready control-flow family. Add the T11 interface, description, expected behavior, and QoR estimate.

- [ ] **Step 3: Add RTL and testbench routing**

Route `_rtl_files()` to `_composed_batch_rl_accelerator_shell_rtl_files()` and `_testbench()` to `_composed_batch_rl_accelerator_shell_testbench()`.

- [ ] **Step 4: Add deterministic RTL and testbench helpers**

Add five RTL modules plus top wrapper. The testbench must configure `weight0=2`, `bias0=1`, `weight1=3`, `bias1=0`, `alpha=4`, `enable=1`, send one batch, and verify lane A `(selected=0, value=7, updated=7)`, lane B `(selected=1, value=9, updated=11)`, `batch_done=1`, and `irq=1`.

## Task 3: Integration Implementation

**Files:**
- Modify: `LLM/src/sr2fpga_agent/runner.py`
- Modify: `LLM/src/sr2fpga_agent/system_his_fidelity.py`
- Modify: `LLM/src/sr2fpga_agent/deepseek.py`
- Modify: `docs/current-status.md`

- [ ] **Step 1: Runner text**

Add T11 simple prompt text, natural component title, natural component summary, and topology expected behavior.

- [ ] **Step 2: Fidelity and prompt guidance**

Add T11 top-port expectations in `system_his_fidelity.py`. Add T11 source expectations, System-HIS task guidance, and retry guidance in `deepseek.py`.

- [ ] **Step 3: Status documentation**

Update `docs/current-status.md` to say T11 is implemented as a synthetic two-lane batch RL shell, and that realistic RL accelerator claims still require user-provided or cited workload/interface references.

## Task 4: Verification And Commit

**Files:**
- All modified source, tests, and docs above.

- [ ] **Step 1: Focused tests**

Run:

```bash
python3 -m unittest \
  LLM.tests.test_sr2fpga_agent_project_generator.ProjectGeneratorTest.test_generates_composed_batch_rl_accelerator_shell_from_t11_component_topology \
  LLM.tests.test_sr2fpga_agent_project_generator.ProjectGeneratorTest.test_multimodule_generated_testbenches_pass_under_icarus \
  LLM.tests.test_sr2fpga_agent_runner.RunnerConfigTest.test_planned_samples_expand_component_topology_ids \
  LLM.tests.test_sr2fpga_agent_system_his_fidelity.SystemHisReqFidelityTest.test_composed_batch_rl_accelerator_shell_requires_config_batch_result_and_irq_ports \
  LLM.tests.test_sr2fpga_agent_deepseek.DeepSeekProviderTest.test_system_his_v12_prompt_includes_batch_rl_accelerator_shell_guidance \
  -q
```

Expected: PASS.

- [ ] **Step 2: Full verification**

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
git commit -m "feat: add T11 batch RL accelerator shell topology"
```

## Self-Review

- The plan covers every requirement in the T11 design spec.
- No placeholders or deferred implementation notes remain.
- Type names, topology id, submodule names, port names, and expected testbench values are consistent across tasks.
