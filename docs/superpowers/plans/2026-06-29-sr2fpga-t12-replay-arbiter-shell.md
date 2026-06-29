# SR2FPGA T12 Replay Arbiter Shell Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the `composed_replay_arbiter_shell` / `t12_replay_arbiter_shell` task as the synthetic replay packetization and arbitration step after T11.

**Architecture:** Extend the deterministic `component_topology` path with host transition packetization, write-index allocation, read/write arbitration, replay memory storage, valid-ready sample output staging, occupancy status, and irq reporting.

**Tech Stack:** Python `unittest`, deterministic Verilog string templates in `LLM/src/sr2fpga_agent/project_generator.py`, runner topology expansion in `LLM/src/sr2fpga_agent/runner.py`, System-HIS fidelity checks, and DeepSeek prompt helpers.

---

## File Structure

- Modify `LLM/tests/test_sr2fpga_agent_project_generator.py`: add T12 generator coverage, supported-task coverage, and Icarus simulation coverage.
- Modify `LLM/tests/test_sr2fpga_agent_runner.py`: extend planned component-topology sample expansion to include `t12_replay_arbiter_shell`.
- Modify `LLM/tests/test_sr2fpga_agent_system_his_fidelity.py`: add REQ->HIS fidelity coverage for required T12 host, request, sample, status, and irq ports.
- Modify `LLM/tests/test_sr2fpga_agent_deepseek.py`: add DeepSeek prompt/source expectations for T12.
- Modify `LLM/src/sr2fpga_agent/project_generator.py`: register T12, define topology metadata, interface, state, RTL files, testbench, descriptions, expected behavior, and QoR estimate.
- Modify `LLM/src/sr2fpga_agent/runner.py`: add natural/contract requirement text and generated sample naming for T12.
- Modify `LLM/src/sr2fpga_agent/system_his_fidelity.py`: add T12 required top-port expectations.
- Modify `LLM/src/sr2fpga_agent/deepseek.py`: add T12 expected RTL sources and task-specific prompt/retry guidance.
- Modify `docs/current-status.md`: record T12 as a synthetic replay arbiter shell and keep the realistic-reference checkpoint explicit.

## Task 1: Red Tests

**Files:**
- Modify: `LLM/tests/test_sr2fpga_agent_project_generator.py`
- Modify: `LLM/tests/test_sr2fpga_agent_runner.py`
- Modify: `LLM/tests/test_sr2fpga_agent_system_his_fidelity.py`
- Modify: `LLM/tests/test_sr2fpga_agent_deepseek.py`

- [ ] **Step 1: Add generator red test**

Add `test_generates_composed_replay_arbiter_shell_from_t12_component_topology`. It should generate `composed_replay_arbiter_shell`, expect RTL sources `rtl/top.v`, `rtl/host_transition_packetizer.v`, `rtl/replay_index_allocator.v`, `rtl/replay_request_arbiter.v`, `rtl/replay_memory_bank.v`, and `rtl/sample_packet_stage.v`, assert topology id `t12_replay_arbiter_shell`, tier `T12`, replay-arbiter top ports, and testbench checks for packet 0 and packet 1.

- [ ] **Step 2: Add manifest and Icarus coverage**

Add `("composed_replay_arbiter_shell", 8, "composed_replay_arbiter_shell_8bit")` to `_supported_task_cases()` and `test_multimodule_generated_testbenches_pass_under_icarus`.

- [ ] **Step 3: Add runner red test**

Extend `test_planned_samples_expand_component_topology_ids` to use `count=12`, `max_samples=12`, include `t12_replay_arbiter_shell`, and assert the generated sample has task type `composed_replay_arbiter_shell`, topology id `t12_replay_arbiter_shell`, tier `T12`, and requirement text naming `replay_request_arbiter` and `replay_memory_bank`.

- [ ] **Step 4: Add fidelity red test**

Add a test that removes `host_valid`, `sample_req_valid`, `sample_state`, `occupancy`, and `irq` from a deterministic T12 System-HIS and expects REQ->HIS fidelity errors for those missing ports.

- [ ] **Step 5: Add DeepSeek red test**

Add `test_system_his_v12_prompt_includes_replay_arbiter_shell_guidance` and assert the prompt includes `Required architecture for composed_replay_arbiter_shell`, `host_transition_packetizer`, `replay_index_allocator`, `replay_request_arbiter`, `replay_memory_bank`, `sample_packet_stage`, and `rtl/replay_memory_bank.v`.

- [ ] **Step 6: Verify RED**

Run:

```bash
python3 -m unittest \
  LLM.tests.test_sr2fpga_agent_project_generator.ProjectGeneratorTest.test_generates_composed_replay_arbiter_shell_from_t12_component_topology \
  LLM.tests.test_sr2fpga_agent_runner.RunnerConfigTest.test_planned_samples_expand_component_topology_ids \
  LLM.tests.test_sr2fpga_agent_system_his_fidelity.SystemHisReqFidelityTest.test_composed_replay_arbiter_shell_requires_host_request_sample_status_and_irq_ports \
  LLM.tests.test_sr2fpga_agent_deepseek.DeepSeekProviderTest.test_system_his_v12_prompt_includes_replay_arbiter_shell_guidance \
  -q
```

Expected: FAIL until T12 support is added.

## Task 2: Generator Implementation

**Files:**
- Modify: `LLM/src/sr2fpga_agent/project_generator.py`

- [ ] **Step 1: Register T12**

Add `composed_replay_arbiter_shell` to `SUPPORTED_TASK_TYPES` and `COMPONENT_TOPOLOGIES` with topology id `t12_replay_arbiter_shell`, tier `T12`, and submodules `host_transition_packetizer`, `replay_index_allocator`, `replay_request_arbiter`, `replay_memory_bank`, and `sample_packet_stage`.

- [ ] **Step 2: Add System-HIS metadata**

Add T12 state ownership for `write_index`, `occupancy`, replay entry memory, staged sample packet, and irq. Add the task to the valid-ready control-flow family. Add the T12 interface, description, expected behavior, and QoR estimate.

- [ ] **Step 3: Add RTL and testbench routing**

Route `_rtl_files()` to `_composed_replay_arbiter_shell_rtl_files()` and `_testbench()` to `_composed_replay_arbiter_shell_testbench()`.

- [ ] **Step 4: Add deterministic RTL and testbench helpers**

Add five RTL modules plus top wrapper. The testbench must write packet 0 `(0x12, 0, 0x03, 0x21, 0)`, write packet 1 `(0x34, 1, 0x05, 0x43, 1)`, check `occupancy=2`, `write_index=2`, read index 0, read index 1, and check `irq=1` after accepted sample output.

## Task 3: Integration Implementation

**Files:**
- Modify: `LLM/src/sr2fpga_agent/runner.py`
- Modify: `LLM/src/sr2fpga_agent/system_his_fidelity.py`
- Modify: `LLM/src/sr2fpga_agent/deepseek.py`
- Modify: `docs/current-status.md`

- [ ] **Step 1: Runner text**

Add T12 simple prompt text, natural component title, natural component summary, and topology expected behavior.

- [ ] **Step 2: Fidelity and prompt guidance**

Add T12 top-port expectations in `system_his_fidelity.py`. Add T12 source expectations, System-HIS task guidance, and retry guidance in `deepseek.py`.

- [ ] **Step 3: Status documentation**

Update `docs/current-status.md` to say T12 is implemented as a synthetic replay arbiter shell, and that realistic RL accelerator claims still require user-provided or cited workload/interface references.

## Task 4: Verification And Commit

**Files:**
- All modified source, tests, and docs above.

- [ ] **Step 1: Focused tests**

Run:

```bash
python3 -m unittest \
  LLM.tests.test_sr2fpga_agent_project_generator.ProjectGeneratorTest.test_generates_composed_replay_arbiter_shell_from_t12_component_topology \
  LLM.tests.test_sr2fpga_agent_project_generator.ProjectGeneratorTest.test_multimodule_generated_testbenches_pass_under_icarus \
  LLM.tests.test_sr2fpga_agent_runner.RunnerConfigTest.test_planned_samples_expand_component_topology_ids \
  LLM.tests.test_sr2fpga_agent_system_his_fidelity.SystemHisReqFidelityTest.test_composed_replay_arbiter_shell_requires_host_request_sample_status_and_irq_ports \
  LLM.tests.test_sr2fpga_agent_deepseek.DeepSeekProviderTest.test_system_his_v12_prompt_includes_replay_arbiter_shell_guidance \
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
git commit -m "feat: add T12 replay arbiter shell topology"
```

## Self-Review

- The plan covers every requirement in the T12 design spec.
- No placeholders or deferred implementation notes remain.
- Type names, topology id, submodule names, port names, and expected testbench values are consistent across tasks.
