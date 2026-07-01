# SR2FPGA Official Eval Set Gap Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the approved official eval set gap closure by adding deterministic support for `alu_control_unit` and `crc_stream_checker`, then update prompt guidance, tests, docs, and eval config scaffolding.

**Status note (2026-06-30):** This is an implementation plan and historical execution record for the gap-closure scaffold, not the final frozen official-eval aggregate. The actual scaffold file is `configs/sr2fpga_official_eval_gap_closure.example.yaml`. The public/reporting curriculum is compressed to T0-T4; legacy topology IDs t5-t12 remain implementation IDs. If the scaffold includes integrated T4 shell samples, report them as supplemental complexity evidence unless a later approved design grounds them in real workload references.

**Prompt-information boundary:** Architecture guidance added here is valid for deterministic generation, REQ2HIS checks, and contract-rich/System-HIS treatment arms. Do not use module-level file lists, FSM tables, internal register names, always-block sketches, or line-level fix hints in the official `simple_prompt` baseline.

**Architecture:** Follow the existing deterministic generator pattern in `LLM/src/sr2fpga_agent/project_generator.py`: register the task type, emit a multi-file RTL project, emit a self-checking testbench, and rely on existing System-HIS v1.2/L0 consistency builders. The new families are ordinary task types, not component topologies, so runner component-topology expansion should not change.

**Tech Stack:** Python unittest, deterministic Verilog generation strings, System-HIS v1.2 checker, Icarus Verilog, optional Verilator, existing DeepSeek prompt guidance utilities.

---

## File Structure

- Modify: `LLM/src/sr2fpga_agent/project_generator.py`
  - Add `alu_control_unit` and `crc_stream_checker` to `SUPPORTED_TASK_TYPES`.
  - Add module lists, requirement descriptions, behavior summaries, interface metadata, RTL emitters, and testbench emitters.
- Modify: `LLM/src/sr2fpga_agent/deepseek.py`
  - Add multi-module file expectations and architecture prompt guidance for both new families.
- Modify: `LLM/src/sr2fpga_agent/system_his_fidelity.py`
  - Add top-port fidelity requirements for both new families if the fidelity gate should enforce them for REQ2HIS.
- Modify: `LLM/tests/test_sr2fpga_agent_project_generator.py`
  - Add generator, L0, manifest, simulation, and optional Verilator coverage for both families.
- Modify: `LLM/tests/test_sr2fpga_agent_deepseek.py`
  - Add prompt-guidance tests for the two new task families.
- Modify: `LLM/tests/test_sr2fpga_agent_system_his_fidelity.py`
  - Add fidelity-gate tests if `system_his_fidelity.py` is updated.
- Create: `configs/sr2fpga_official_eval_gap_closure.example.yaml`
  - Add a gap-closure scaffold after deterministic support passes. Derive a
    frozen official aggregate from it only after separating primary families from
    supplemental integrated-shell results.
- Modify: `README.md`
  - Add the two new task families and note that official eval coverage is broader
    than the legacy t1-t4 topology IDs.
- Modify: `docs/current-status.md`
  - Record the gap-closure implementation and next official eval freeze step.

---

### Task 1: Add Failing Generator Tests

**Files:**
- Modify: `LLM/tests/test_sr2fpga_agent_project_generator.py`

- [ ] **Step 1: Add individual project package tests**

Add these tests near the existing multi-module task tests:

```python
    def test_generates_alu_control_unit_multimodule_project_package(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="alu_control_unit", width=8, project_name="alu_control_unit_8bit"),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )

        _assert_multimodule_task(
            self,
            project,
            "alu_control_unit",
            {"rtl/top.v", "rtl/alu_core.v", "rtl/control_decode.v", "rtl/status_flags.v"},
            ["alu_core", "control_decode", "status_flags", ".result(result)", ".zero(zero)", ".carry(carry)"],
        )
        self.assertIn("input wire [2:0] op", project.files["rtl/top.v"])
        self.assertIn("output wire negative", project.files["rtl/top.v"])
        self.assertIn("expect_result(3'b000", project.files["sim/tb_top.v"])
        self.assertIn("expect_result(3'b111", project.files["sim/tb_top.v"])
        self.assertIn("TEST_PASS", project.files["sim/tb_top.v"])

    def test_generates_crc_stream_checker_multimodule_project_package(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="crc_stream_checker", width=8, project_name="crc_stream_checker_8bit"),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )

        _assert_multimodule_task(
            self,
            project,
            "crc_stream_checker",
            {"rtl/top.v", "rtl/crc8_update.v", "rtl/stream_frame_accumulator.v", "rtl/crc_status.v"},
            ["crc8_update", "stream_frame_accumulator", "crc_status", ".crc_value(crc_value)", ".crc_match(crc_match)"],
        )
        self.assertIn("input wire frame_start", project.files["rtl/top.v"])
        self.assertIn("input wire frame_end", project.files["rtl/top.v"])
        self.assertIn("input wire out_ready", project.files["rtl/top.v"])
        self.assertIn("send_byte(8'h12", project.files["sim/tb_top.v"])
        self.assertIn("TEST_PASS", project.files["sim/tb_top.v"])
```

- [ ] **Step 2: Add both families to aggregate test cases**

Update `_supported_task_cases()`:

```python
        ("alu_control_unit", 8, "alu_control_unit_8bit"),
        ("crc_stream_checker", 8, "crc_stream_checker_8bit"),
```

Update `test_multimodule_families_emit_valid_system_his_v12`:

```python
            ("alu_control_unit", 8, "alu_control_unit_8bit"),
            ("crc_stream_checker", 8, "crc_stream_checker_8bit"),
```

Update `test_multimodule_generated_testbenches_pass_under_icarus`:

```python
            ("alu_control_unit", 8, "alu_control_unit_8bit"),
            ("crc_stream_checker", 8, "crc_stream_checker_8bit"),
```

Update `test_multimodule_task_sources_are_verilator_wall_clean`:

```python
            ("alu_control_unit", 8, "alu_control_unit_8bit"),
            ("crc_stream_checker", 8, "crc_stream_checker_8bit"),
```

- [ ] **Step 3: Run tests to verify they fail for unsupported task type**

Run:

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_project_generator.ProjectGeneratorTest.test_generates_alu_control_unit_multimodule_project_package -q
python3 -m unittest LLM.tests.test_sr2fpga_agent_project_generator.ProjectGeneratorTest.test_generates_crc_stream_checker_multimodule_project_package -q
```

Expected: both fail with `ValueError: Unsupported task_type for V1`.

- [ ] **Step 4: Commit failing tests**

```bash
git add LLM/tests/test_sr2fpga_agent_project_generator.py
git commit -m "test: cover official eval gap task families"
```

---

### Task 2: Implement `alu_control_unit`

**Files:**
- Modify: `LLM/src/sr2fpga_agent/project_generator.py`
- Test: `LLM/tests/test_sr2fpga_agent_project_generator.py`

- [ ] **Step 1: Register the task type**

Add to `SUPPORTED_TASK_TYPES`:

```python
    "alu_control_unit",
```

- [ ] **Step 2: Add submodule metadata**

In the existing submodule mapping used by the System-HIS architecture builder, add:

```python
        "alu_control_unit": ["alu_core", "control_decode", "status_flags"],
```

- [ ] **Step 3: Add request assumptions and behavior metadata**

In the existing request-assumption builder, add:

```python
    elif request.task_type == "alu_control_unit":
        registers.extend(
            [
                {"name": "result_reg", "owner": top_module, "width": request.width},
                {"name": "flag_reg", "owner": top_module, "width": 3},
            ]
        )
```

In the task requirement map, add:

```python
        "alu_control_unit": (
            f"Generate a {request.width}-bit ALU control unit with a 3-bit operation selector, "
            "registered result output, and zero/carry/negative status flags."
        ),
```

In the expected behavior map, add:

```python
        "alu_control_unit": (
            "valid input operands are decoded by op, the selected ALU operation produces a registered result, "
            "and status flags reflect zero, carry, and result sign"
        ),
```

- [ ] **Step 4: Dispatch RTL and testbench emitters**

Add to the RTL file dispatcher:

```python
    if request.task_type == "alu_control_unit":
        return _alu_control_unit_rtl_files(request.width)
```

Add to the testbench dispatcher:

```python
    if request.task_type == "alu_control_unit":
        return _alu_control_unit_testbench(request.width)
```

- [ ] **Step 5: Implement `_alu_control_unit_rtl_files`**

Use this structure:

```python
def _alu_control_unit_rtl_files(width: int) -> dict[str, str]:
    msb = width - 1
    top = dedent(
        f"""
        module top #(
            parameter WIDTH = {width}
        ) (
            input wire clk,
            input wire rst_n,
            input wire valid,
            output wire ready,
            input wire [2:0] op,
            input wire [WIDTH-1:0] lhs,
            input wire [WIDTH-1:0] rhs,
            output wire result_valid,
            output wire [WIDTH-1:0] result,
            output wire zero,
            output wire carry,
            output wire negative
        );
          wire [2:0] decoded_op;
          wire [WIDTH-1:0] alu_result;
          wire alu_carry;

          assign ready = 1'b1;

          control_decode u_control_decode (
            .op(op),
            .decoded_op(decoded_op)
          );

          alu_core #(
            .WIDTH(WIDTH)
          ) u_alu_core (
            .op(decoded_op),
            .lhs(lhs),
            .rhs(rhs),
            .result(alu_result),
            .carry(alu_carry)
          );

          status_flags #(
            .WIDTH(WIDTH)
          ) u_status_flags (
            .clk(clk),
            .rst_n(rst_n),
            .valid(valid),
            .alu_result(alu_result),
            .alu_carry(alu_carry),
            .result_valid(result_valid),
            .result(result),
            .zero(zero),
            .carry(carry),
            .negative(negative)
          );
        endmodule
        """
    ).strip() + "\n"
```

Add `control_decode`, `alu_core`, and `status_flags` strings in the same function. `alu_core` must implement operations `000` through `111`; add/subtract should compute one extra carry bit:

```verilog
wire [WIDTH:0] add_ext = {1'b0, lhs} + {1'b0, rhs};
wire [WIDTH:0] sub_ext = {1'b0, lhs} - {1'b0, rhs};
```

Return:

```python
    return {
        "rtl/top.v": top,
        "rtl/control_decode.v": control_decode,
        "rtl/alu_core.v": alu_core,
        "rtl/status_flags.v": status_flags,
    }
```

- [ ] **Step 6: Implement `_alu_control_unit_testbench`**

The testbench must include:

```verilog
task expect_result;
  input [2:0] op_i;
  input [WIDTH-1:0] lhs_i;
  input [WIDTH-1:0] rhs_i;
  input [WIDTH-1:0] expected_result;
  input expected_zero;
  input expected_carry;
  input expected_negative;
  begin
    @(negedge clk);
    valid = 1'b1;
    op = op_i;
    lhs = lhs_i;
    rhs = rhs_i;
    @(negedge clk);
    valid = 1'b0;
    if (!result_valid || result !== expected_result || zero !== expected_zero ||
        carry !== expected_carry || negative !== expected_negative) begin
      $display("TEST_FAIL alu op=%0d result=%0h zero=%0b carry=%0b negative=%0b",
               op_i, result, zero, carry, negative);
      $finish;
    end
  end
endtask
```

Use these cases for WIDTH=8:

```verilog
expect_result(3'b000, 8'hff, 8'h01, 8'h00, 1'b1, 1'b1, 1'b0);
expect_result(3'b001, 8'h03, 8'h01, 8'h02, 1'b0, 1'b0, 1'b0);
expect_result(3'b010, 8'haa, 8'h0f, 8'h0a, 1'b0, 1'b0, 1'b0);
expect_result(3'b011, 8'ha0, 8'h0f, 8'haf, 1'b0, 1'b0, 1'b1);
expect_result(3'b100, 8'hff, 8'h0f, 8'hf0, 1'b0, 1'b0, 1'b1);
expect_result(3'b101, 8'h11, 8'h01, 8'h22, 1'b0, 1'b0, 1'b0);
expect_result(3'b110, 8'h80, 8'h02, 8'h20, 1'b0, 1'b0, 1'b0);
expect_result(3'b111, 8'h5a, 8'h00, 8'h5a, 1'b0, 1'b0, 1'b0);
```

- [ ] **Step 7: Run focused tests**

Run:

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_project_generator.ProjectGeneratorTest.test_generates_alu_control_unit_multimodule_project_package -q
python3 -m unittest LLM.tests.test_sr2fpga_agent_project_generator.ProjectGeneratorTest.test_manifest_sources_exist_for_all_supported_task_types -q
python3 -m unittest LLM.tests.test_sr2fpga_agent_project_generator.ProjectGeneratorTest.test_system_his_architecture_submodules_match_emitted_rtl_modules -q
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add LLM/src/sr2fpga_agent/project_generator.py LLM/tests/test_sr2fpga_agent_project_generator.py
git commit -m "feat: add deterministic ALU control unit task"
```

---

### Task 3: Implement `crc_stream_checker`

**Files:**
- Modify: `LLM/src/sr2fpga_agent/project_generator.py`
- Test: `LLM/tests/test_sr2fpga_agent_project_generator.py`

- [ ] **Step 1: Register the task type**

Add to `SUPPORTED_TASK_TYPES`:

```python
    "crc_stream_checker",
```

- [ ] **Step 2: Add submodule metadata**

In the existing submodule mapping used by the System-HIS architecture builder, add:

```python
        "crc_stream_checker": ["crc8_update", "stream_frame_accumulator", "crc_status"],
```

- [ ] **Step 3: Add request assumptions and behavior metadata**

In the request-assumption builder, add:

```python
    elif request.task_type == "crc_stream_checker":
        registers.extend(
            [
                {"name": "crc_reg", "owner": top_module, "width": 8},
                {"name": "crc_result_reg", "owner": top_module, "width": 8},
            ]
        )
```

In the task requirement map, add:

```python
        "crc_stream_checker": (
            "Generate a CRC-8 valid-ready stream checker with frame_start/frame_end, "
            "expected CRC comparison, and held result output under backpressure."
        ),
```

In the expected behavior map, add:

```python
        "crc_stream_checker": (
            "input bytes update a CRC-8 accumulator during a frame, frame_end publishes crc_value, "
            "and crc_match compares the result against expected_crc while respecting output backpressure"
        ),
```

- [ ] **Step 4: Dispatch RTL and testbench emitters**

Add to the RTL file dispatcher:

```python
    if request.task_type == "crc_stream_checker":
        return _crc_stream_checker_rtl_files(request.width)
```

Add to the testbench dispatcher:

```python
    if request.task_type == "crc_stream_checker":
        return _crc_stream_checker_testbench(request.width)
```

- [ ] **Step 5: Implement `_crc_stream_checker_rtl_files`**

The top module must have this interface:

```verilog
module top (
    input wire clk,
    input wire rst_n,
    input wire in_valid,
    output wire in_ready,
    input wire [7:0] in_data,
    input wire frame_start,
    input wire frame_end,
    input wire [7:0] expected_crc,
    input wire out_ready,
    output wire [7:0] crc_value,
    output wire crc_match,
    output wire crc_valid
);
```

Module responsibilities:

```text
crc8_update.v:
  combinational next CRC calculation using polynomial 0x07, initial convention handled by accumulator.

stream_frame_accumulator.v:
  owns crc_reg and in_ready; resets crc to 0 at frame_start; updates on in_valid && in_ready.

crc_status.v:
  owns crc_value/crc_match/crc_valid; captures final CRC at frame_end and holds while out_ready is low.
```

The CRC update logic should use a function with fixed 8-cycle byte update:

```verilog
function [7:0] next_crc8;
  input [7:0] crc_in;
  input [7:0] data_in;
  integer i;
  reg [7:0] crc;
  begin
    crc = crc_in ^ data_in;
    for (i = 0; i < 8; i = i + 1) begin
      if (crc[7])
        crc = (crc << 1) ^ 8'h07;
      else
        crc = crc << 1;
    end
    next_crc8 = crc;
  end
endfunction
```

- [ ] **Step 6: Implement `_crc_stream_checker_testbench`**

The testbench must include byte sender and held-output checks:

```verilog
task send_byte;
  input [7:0] data_i;
  input start_i;
  input end_i;
  begin
    @(negedge clk);
    in_valid = 1'b1;
    in_data = data_i;
    frame_start = start_i;
    frame_end = end_i;
    @(negedge clk);
    in_valid = 1'b0;
    frame_start = 1'b0;
    frame_end = 1'b0;
  end
endtask
```

Use a deterministic known sequence. For CRC-8 polynomial `0x07`, initial `0x00`,
non-reflected update, the sequence `8'h12, 8'h34` produces `8'hF1`.

Add checks:

```verilog
expected_crc = 8'hF1;
out_ready = 1'b0;
send_byte(8'h12, 1'b1, 1'b0);
send_byte(8'h34, 1'b0, 1'b1);
repeat (2) @(negedge clk);
if (!crc_valid || crc_value !== 8'hF1 || !crc_match) begin
  $display("TEST_FAIL crc held result mismatch value=%0h match=%0b valid=%0b",
           crc_value, crc_match, crc_valid);
  $finish;
end
out_ready = 1'b1;
@(negedge clk);
if (crc_valid) begin
  $display("TEST_FAIL crc_valid should clear after out_ready");
  $finish;
end
```

- [ ] **Step 7: Run focused tests**

Run:

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_project_generator.ProjectGeneratorTest.test_generates_crc_stream_checker_multimodule_project_package -q
python3 -m unittest LLM.tests.test_sr2fpga_agent_project_generator.ProjectGeneratorTest.test_multimodule_generated_testbenches_pass_under_icarus -q
```

Expected: PASS, including the new CRC case.

- [ ] **Step 8: Commit**

```bash
git add LLM/src/sr2fpga_agent/project_generator.py LLM/tests/test_sr2fpga_agent_project_generator.py
git commit -m "feat: add deterministic CRC stream checker task"
```

---

### Task 4: Add DeepSeek Prompt Guidance And Fidelity Gates

**Files:**
- Modify: `LLM/src/sr2fpga_agent/deepseek.py`
- Modify: `LLM/src/sr2fpga_agent/system_his_fidelity.py`
- Modify: `LLM/tests/test_sr2fpga_agent_deepseek.py`
- Modify: `LLM/tests/test_sr2fpga_agent_system_his_fidelity.py`

- [ ] **Step 1: Add multi-module file expectations**

In `MULTIMODULE_RTL_EXAMPLES`, add:

```python
    "alu_control_unit": ["rtl/top.v", "rtl/control_decode.v", "rtl/alu_core.v", "rtl/status_flags.v"],
    "crc_stream_checker": [
        "rtl/top.v",
        "rtl/crc8_update.v",
        "rtl/stream_frame_accumulator.v",
        "rtl/crc_status.v",
    ],
```

- [ ] **Step 2: Add architecture prompt guidance**

In the task-specific guidance helper, add:

```python
    if task_type == "alu_control_unit":
        return (
            "Required architecture for alu_control_unit:\n"
            "- components: control_decode, alu_core, status_flags\n"
            "- instances: decode, alu, flags\n"
            "- top ports must include clk, rst_n, valid, ready, op, lhs, rhs, result_valid, "
            "result, zero, carry, and negative.\n"
            "- control_decode must preserve the 3-bit op selector.\n"
            "- alu_core must implement add, subtract, and/or/xor, logical shifts, and pass lhs.\n"
            "- status_flags owns registered result, result_valid, zero, carry, and negative outputs.\n"
            "- artifacts.rtl_sources must include rtl/top.v, rtl/control_decode.v, rtl/alu_core.v, "
            "and rtl/status_flags.v."
        )
    if task_type == "crc_stream_checker":
        return (
            "Required architecture for crc_stream_checker:\n"
            "- components: crc8_update, stream_frame_accumulator, crc_status\n"
            "- instances: update, accumulator, status\n"
            "- top ports must include clk, rst_n, in_valid, in_ready, in_data, frame_start, "
            "frame_end, expected_crc, out_ready, crc_value, crc_match, and crc_valid.\n"
            "- crc8_update must implement CRC-8 polynomial 0x07 with initial value handled by the accumulator.\n"
            "- stream_frame_accumulator owns crc_reg and byte-stream update state.\n"
            "- crc_status owns held crc_value, crc_match, and crc_valid outputs under out_ready backpressure.\n"
            "- artifacts.rtl_sources must include rtl/top.v, rtl/crc8_update.v, "
            "rtl/stream_frame_accumulator.v, and rtl/crc_status.v."
        )
```

- [ ] **Step 3: Add DeepSeek unit tests**

Add tests next to existing prompt-guidance tests:

```python
    def test_req2his_prompt_guides_alu_control_unit_architecture(self) -> None:
        client = FakeOpenAICompatibleClient(
            responses=[
                {
                    "system_his": _minimal_valid_system_his_for_task("alu_control_unit"),
                }
            ]
        )
        request = ProjectRequest(task_type="alu_control_unit", width=8, project_name="alu_control_unit_8bit")

        with self.assertRaises(ValueError):
            DeepSeekSystemHisGenerator(client, max_attempts=1).generate(
                request,
                PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
            )

        user_prompt = client.requests[0]["messages"][-1]["content"]
        self.assertIn("Required architecture for alu_control_unit", user_prompt)
        self.assertIn("control_decode", user_prompt)
        self.assertIn("status_flags", user_prompt)
```

Add the CRC guidance test in the same file:

```python
    def test_req2his_prompt_guides_crc_stream_checker_architecture(self) -> None:
        client = FakeOpenAICompatibleClient(
            responses=[
                {
                    "system_his": _minimal_valid_system_his_for_task("crc_stream_checker"),
                }
            ]
        )
        request = ProjectRequest(task_type="crc_stream_checker", width=8, project_name="crc_stream_checker_8bit")

        with self.assertRaises(ValueError):
            DeepSeekSystemHisGenerator(client, max_attempts=1).generate(
                request,
                PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
            )

        user_prompt = client.requests[0]["messages"][-1]["content"]
        self.assertIn("Required architecture for crc_stream_checker", user_prompt)
        self.assertIn("crc8_update", user_prompt)
        self.assertIn("stream_frame_accumulator", user_prompt)
        self.assertIn("crc_status", user_prompt)
```

- [ ] **Step 4: Add fidelity expectations**

In `system_his_fidelity.py`, add entries that require these top ports:

```python
    "alu_control_unit": {
        "clk": {"direction": "input"},
        "rst_n": {"direction": "input"},
        "valid": {"direction": "input"},
        "ready": {"direction": "output"},
        "op": {"direction": "input", "width": 3},
        "lhs": {"direction": "input", "width": "request"},
        "rhs": {"direction": "input", "width": "request"},
        "result_valid": {"direction": "output"},
        "result": {"direction": "output", "width": "request"},
        "zero": {"direction": "output"},
        "carry": {"direction": "output"},
        "negative": {"direction": "output"},
    },
    "crc_stream_checker": {
        "clk": {"direction": "input"},
        "rst_n": {"direction": "input"},
        "in_valid": {"direction": "input"},
        "in_ready": {"direction": "output"},
        "in_data": {"direction": "input", "width": 8},
        "frame_start": {"direction": "input"},
        "frame_end": {"direction": "input"},
        "expected_crc": {"direction": "input", "width": 8},
        "out_ready": {"direction": "input"},
        "crc_value": {"direction": "output", "width": 8},
        "crc_match": {"direction": "output"},
        "crc_valid": {"direction": "output"},
    },
```

- [ ] **Step 5: Add fidelity tests**

Add tests:

```python
    def test_alu_control_unit_requires_operand_result_and_flag_ports(self) -> None:
        request = ProjectRequest(task_type="alu_control_unit", width=8, project_name="alu_control_unit_8bit")
        system_his = _deterministic_system_his(request)
        system_his["top"]["ports"] = [
            port
            for port in system_his["top"]["ports"]
            if port["name"] not in {"op", "result", "negative"}
        ]

        result = check_system_his_req_fidelity(request, system_his)

        self.assertFalse(result.passed)
        self.assertIn("REQ2HIS fidelity: alu_control_unit requires top port 'op'", result.errors)
        self.assertIn("REQ2HIS fidelity: alu_control_unit requires top port 'result'", result.errors)
        self.assertIn("REQ2HIS fidelity: alu_control_unit requires top port 'negative'", result.errors)

    def test_crc_stream_checker_requires_stream_frame_and_crc_ports(self) -> None:
        request = ProjectRequest(task_type="crc_stream_checker", width=8, project_name="crc_stream_checker_8bit")
        system_his = _deterministic_system_his(request)
        system_his["top"]["ports"] = [
            port
            for port in system_his["top"]["ports"]
            if port["name"] not in {"in_valid", "frame_end", "crc_value"}
        ]

        result = check_system_his_req_fidelity(request, system_his)

        self.assertFalse(result.passed)
        self.assertIn("REQ2HIS fidelity: crc_stream_checker requires top port 'in_valid'", result.errors)
        self.assertIn("REQ2HIS fidelity: crc_stream_checker requires top port 'frame_end'", result.errors)
        self.assertIn("REQ2HIS fidelity: crc_stream_checker requires top port 'crc_value'", result.errors)
```

- [ ] **Step 6: Run focused tests**

Run:

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_deepseek -q
python3 -m unittest LLM.tests.test_sr2fpga_agent_system_his_fidelity -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add LLM/src/sr2fpga_agent/deepseek.py LLM/src/sr2fpga_agent/system_his_fidelity.py LLM/tests/test_sr2fpga_agent_deepseek.py LLM/tests/test_sr2fpga_agent_system_his_fidelity.py
git commit -m "feat: guide official eval gap tasks through REQ2HIS"
```

---

### Task 5: Add Official Eval Config Scaffold And Docs

**Files:**
- Create: `configs/sr2fpga_official_eval_gap_closure.example.yaml`
- Modify: `README.md`
- Modify: `docs/current-status.md`

- [ ] **Step 1: Add official eval config scaffold**

Create `configs/sr2fpga_official_eval_gap_closure.example.yaml`:

```yaml
dataset_root: datasets/sr2fpga_rtl_v1
export_root: datasets/sr2fpga_rtl_v1_exports
run_root: tmp/sr2fpga_runs
provider: deterministic
repair_provider: none
max_attempts: 1
refresh_exports: true

line_b_targets:
  max_samples: 16

tasks:
  - source: deterministic
    task_type: simple_fsm
    widths: [4]
    count: 1
    difficulty_tier: T0
    failure_origin: deterministic_reference
    measurement_point: a_first_attempt_no_tools
    requirement_style: contract
  - source: deterministic
    task_type: composed_event_counter
    widths: [8]
    count: 1
    difficulty_tier: T1
    failure_origin: deterministic_reference
    measurement_point: a_first_attempt_no_tools
    requirement_style: contract
  - source: deterministic
    task_type: composed_stream_accumulator
    widths: [8]
    count: 1
    difficulty_tier: T1
    failure_origin: deterministic_reference
    measurement_point: a_first_attempt_no_tools
    requirement_style: contract
  - source: deterministic
    task_type: composed_stream_fork
    widths: [8]
    count: 1
    difficulty_tier: T2
    failure_origin: deterministic_reference
    measurement_point: a_first_attempt_no_tools
    requirement_style: contract
  - source: deterministic
    task_type: composed_dual_stream_join
    widths: [8]
    count: 1
    difficulty_tier: T2
    failure_origin: deterministic_reference
    measurement_point: a_first_attempt_no_tools
    requirement_style: contract
  - source: deterministic
    task_type: fir_filter
    widths: [8]
    count: 1
    difficulty_tier: T0
    failure_origin: deterministic_reference
    measurement_point: a_first_attempt_no_tools
    requirement_style: contract
  - source: deterministic
    task_type: matrix_vector_mac
    widths: [8]
    count: 1
    difficulty_tier: T0
    failure_origin: deterministic_reference
    measurement_point: a_first_attempt_no_tools
    requirement_style: contract
  - source: deterministic
    task_type: composed_vector_mac_pipeline
    widths: [8]
    count: 1
    difficulty_tier: T3
    failure_origin: deterministic_reference
    measurement_point: a_first_attempt_no_tools
    requirement_style: contract
  - source: deterministic
    task_type: fifo
    widths: [8]
    count: 1
    difficulty_tier: T0
    failure_origin: deterministic_reference
    measurement_point: a_first_attempt_no_tools
    requirement_style: contract
  - source: deterministic
    task_type: ram_read_write
    widths: [16]
    count: 1
    difficulty_tier: T0
    failure_origin: deterministic_reference
    measurement_point: a_first_attempt_no_tools
    requirement_style: contract
  - source: deterministic
    task_type: composed_replay_sample_shell
    widths: [8]
    count: 1
    difficulty_tier: T3
    failure_origin: deterministic_reference
    measurement_point: a_first_attempt_no_tools
    requirement_style: contract
  - source: deterministic
    task_type: uart_tx
    widths: [8]
    count: 1
    difficulty_tier: T0
    failure_origin: deterministic_reference
    measurement_point: a_first_attempt_no_tools
    requirement_style: contract
  - source: deterministic
    task_type: spi_master
    widths: [8]
    count: 1
    difficulty_tier: T0
    failure_origin: deterministic_reference
    measurement_point: a_first_attempt_no_tools
    requirement_style: contract
  - source: deterministic
    task_type: composed_host_protocol_shell
    widths: [8]
    count: 1
    difficulty_tier: T4
    failure_origin: deterministic_reference
    measurement_point: a_first_attempt_no_tools
    requirement_style: contract
  - source: deterministic
    task_type: alu_control_unit
    widths: [8]
    count: 1
    difficulty_tier: T0
    failure_origin: deterministic_reference
    measurement_point: a_first_attempt_no_tools
    requirement_style: contract
  - source: deterministic
    task_type: crc_stream_checker
    widths: [8]
    count: 1
    difficulty_tier: T0
    failure_origin: deterministic_reference
    measurement_point: a_first_attempt_no_tools
    requirement_style: contract
```

- [ ] **Step 2: Update README task list**

Add:

```markdown
- `alu_control_unit`
- `crc_stream_checker`
```

Add one sentence under the task list:

```markdown
The official evaluation set is organized by literature-facing RTL categories
such as control/FSM, stream handshake, arithmetic/datapath, memory/buffering,
protocol/host interface, processor-like control, and checksum/data integrity.
```

- [ ] **Step 3: Update current status**

Add a compact bullet under current code state or current capability:

```markdown
- Official eval set gap closure now adds `alu_control_unit` and
  `crc_stream_checker` as the only new V1 task families needed to cover
  processor-like control and checksum/data-integrity categories. Integrated T4
  shell tasks remain supplemental complexity evidence rather than primary
  aggregate metrics.
```

- [ ] **Step 4: Run config preflight**

Run:

```bash
python3 -m LLM.src.sr2fpga_agent.runner --config configs/sr2fpga_official_eval_gap_closure.example.yaml --run-id official-eval-gap-closure-dry-run --preflight
```

Expected for the minimal deterministic scaffold: `ok: true` and `planned_samples: 16`.
The current gap-closure scaffold may plan more samples if it also includes
DeepSeek or supplemental integrated-shell arms.

- [ ] **Step 5: Commit**

```bash
git add configs/sr2fpga_official_eval_gap_closure.example.yaml README.md docs/current-status.md
git commit -m "docs: scaffold official eval set config"
```

---

### Task 6: Full Verification

**Files:**
- Verify all modified code and docs.

- [ ] **Step 1: Run focused unit suite**

Run:

```bash
python3 -m unittest \
  LLM.tests.test_sr2fpga_agent_project_generator \
  LLM.tests.test_sr2fpga_agent_deepseek \
  LLM.tests.test_sr2fpga_agent_system_his_fidelity \
  LLM.tests.test_sr2fpga_agent_runner \
  -q
```

Expected: all tests pass.

- [ ] **Step 2: Run complete LLM test suite**

Run:

```bash
python3 -m unittest discover -s LLM/tests -q
```

Expected: all tests pass.

- [ ] **Step 3: Compile Python files**

Run:

```bash
python3 -m compileall LLM/src LLM/tests
```

Expected: compile succeeds with no syntax errors.

- [ ] **Step 4: Run deterministic official eval preflight**

Run:

```bash
python3 -m LLM.src.sr2fpga_agent.runner --config configs/sr2fpga_official_eval_gap_closure.example.yaml --run-id official-eval-gap-closure-dry-run --preflight
```

Expected for the minimal deterministic scaffold: `ok: true` and `planned_samples: 16`.
The current gap-closure scaffold may plan more samples if it also includes
DeepSeek or supplemental integrated-shell arms.

- [ ] **Step 5: Inspect final git diff**

Run:

```bash
git status --short
git log --oneline -6
```

Expected: worktree clean after commits; latest commits correspond to the tasks above.

---

## Self-Review Checklist

- Spec coverage: implements the two approved new families, keeps integrated T4 shells supplemental, avoids a post-T4 synthetic tier without a new design, and separates deterministic support from scaled experiments.
- Unresolved marker scan: no open-ended markers remain in the plan.
- Scope control: does not add CPU, RISC-V, AES, DDR, PCIe, Ethernet, or vendor IP.
- Verification coverage: includes generator tests, L0/System-HIS consistency via existing aggregate tests, Icarus simulation, optional Verilator, DeepSeek prompt guidance, fidelity gates, and runner config preflight.
