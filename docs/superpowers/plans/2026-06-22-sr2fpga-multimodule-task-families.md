# SR2FPGA Multi-Module Task Families Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add six deterministic multi-module RTL task families to the SR2FPGA data-generation agent and verify they produce complete, tool-checkable project packages.

**Architecture:** Keep the current generator surface unchanged: `ProjectGenerator.generate(request, platform) -> GeneratedProject`. Add a file-map layer inside `project_generator.py` so new task families can emit multiple RTL sources while old single-file tasks continue to emit `rtl/top.v` only. Metadata helpers (`manifest`, `system_his`, interface, expected behavior, predicted QoR) must be updated together so every generated package is cross-file consistent.

**Tech Stack:** Python stdlib, `unittest`, Verilog-2005/SystemVerilog-compatible RTL syntax, Verilator lint, Icarus Verilog/vvp simulation, Yosys synthesis.

---

## File Structure

- Modify `LLM/src/sr2fpga_agent/project_generator.py`
  - Add `SUPPORTED_TASK_TYPES`.
  - Add `_rtl_files(request)` returning `dict[str, str]`.
  - Change `generate()` to merge common files with `_rtl_files()`.
  - Change `_manifest()` to list all generated RTL sources.
  - Add architecture metadata under `system_his.json` for multi-module tasks.
  - Add RTL and testbench builders for:
    - `uart_tx`
    - `spi_master`
    - `pwm_controller`
    - `fir_filter`
    - `streaming_valid_ready`
    - `matrix_vector_mac`
- Modify `LLM/tests/test_sr2fpga_agent_project_generator.py`
  - Add reusable assertions for multi-module packages.
  - Add one unit test per new task family.
  - Add a manifest/source consistency test across all supported tasks.
- Modify `docs/sr2fpga-agent-handoff-2026-06-22.md`
  - Append implementation and data-generation results after samples are generated.
- Do not commit `datasets/`, `tmp/`, API keys, model weights, or generated tool outputs.

## Task 1: Multi-Source Project Contract

**Files:**
- Modify: `LLM/tests/test_sr2fpga_agent_project_generator.py`
- Modify: `LLM/src/sr2fpga_agent/project_generator.py`

- [ ] **Step 1: Write failing tests for the multi-source contract**

Add these helper functions near the bottom of `LLM/tests/test_sr2fpga_agent_project_generator.py`, above `if __name__ == "__main__":`.

```python
def _manifest(project) -> dict:
    return json.loads(project.files["manifest.json"])


def _system_his(project) -> dict:
    return json.loads(project.files["system_his.json"])


def _assert_manifest_sources_exist(testcase: unittest.TestCase, project) -> None:
    manifest = _manifest(project)
    testcase.assertIn("rtl/top.v", manifest["sources"])
    for source in manifest["sources"]:
        testcase.assertIn(source, project.files)
        testcase.assertTrue(source.startswith("rtl/"), source)
        testcase.assertIn("module ", project.files[source])
```

Add this test method inside `ProjectGeneratorTest`.

```python
def test_manifest_sources_exist_for_all_supported_task_types(self) -> None:
    platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
    cases = [
        ("counter", 8, "counter_8bit"),
        ("fifo", 8, "fifo_8bit"),
        ("simple_fsm", 4, "fsm_sequence_4bit"),
        ("ram_read_write", 16, "ram_rw_16bit"),
        ("uart_tx", 8, "uart_tx_8bit"),
        ("spi_master", 8, "spi_master_8bit"),
        ("pwm_controller", 8, "pwm_controller_8bit"),
        ("fir_filter", 8, "fir_filter_8bit"),
        ("streaming_valid_ready", 8, "streaming_valid_ready_8bit"),
        ("matrix_vector_mac", 8, "matrix_vector_mac_8bit"),
    ]

    for task_type, width, project_name in cases:
        with self.subTest(task_type=task_type):
            project = ProjectGenerator().generate(
                ProjectRequest(task_type=task_type, width=width, project_name=project_name),
                platform,
            )
            _assert_manifest_sources_exist(self, project)
            self.assertEqual(_manifest(project)["simulation"]["testbench"], "sim/tb_top.v")
            self.assertIn("TEST_PASS", project.files["sim/tb_top.v"])
```

- [ ] **Step 2: Run the contract test and verify it fails**

Run:

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_project_generator.ProjectGeneratorTest.test_manifest_sources_exist_for_all_supported_task_types -q
```

Expected: fails with `ValueError: Unsupported task_type for V1: uart_tx`.

- [ ] **Step 3: Add supported task declarations and RTL source map plumbing**

In `LLM/src/sr2fpga_agent/project_generator.py`, add this constant after imports:

```python
SUPPORTED_TASK_TYPES = {
    "counter",
    "fifo",
    "simple_fsm",
    "ram_read_write",
    "uart_tx",
    "spi_master",
    "pwm_controller",
    "fir_filter",
    "streaming_valid_ready",
    "matrix_vector_mac",
}
```

Replace the `ProjectGenerator.generate()` method body with this version:

```python
    def generate(self, request: ProjectRequest, platform: PlatformProfile) -> GeneratedProject:
        if request.task_type not in SUPPORTED_TASK_TYPES:
            raise ValueError(f"Unsupported task_type for V1: {request.task_type}")
        if request.width <= 0:
            raise ValueError("width must be positive")

        rtl_files = _rtl_files(request)
        files = {
            "system_his.json": _to_json(_system_his(request, platform)),
            "manifest.json": _to_json(_manifest(request, platform, rtl_files)),
            **rtl_files,
            "constraints/timing.sdc": _timing_sdc(platform),
            "sim/tb_top.v": _testbench(request),
            "reports/predicted_qor.json": _to_json(_predicted_qor(request, platform)),
        }
        return GeneratedProject(project_name=request.project_name, files=files)
```

Replace `_manifest(request, platform)` with:

```python
def _manifest(
    request: ProjectRequest,
    platform: PlatformProfile,
    rtl_files: dict[str, str] | None = None,
) -> dict[str, object]:
    sources = list((rtl_files or {"rtl/top.v": ""}).keys())
    return {
        "project_name": request.project_name,
        "top_module": "top",
        "language": "verilog",
        "target": {
            "vendor": platform.vendor,
            "family": platform.family,
            "part": platform.part,
            "board": platform.board,
            "toolchain": platform.toolchain,
        },
        "sources": sources,
        "constraints": {"timing": "constraints/timing.sdc"},
        "simulation": {"testbench": "sim/tb_top.v", "type": "self_checking"},
        "reports": {"predicted_qor": "reports/predicted_qor.json"},
        "clock": {"name": "clk", "frequency_hz": platform.clock_hz},
        "reset": {"name": "rst_n", "polarity": platform.reset_polarity},
    }
```

Add this function above `_rtl(request)`:

```python
def _rtl_files(request: ProjectRequest) -> dict[str, str]:
    if request.task_type == "counter":
        return {"rtl/top.v": _counter_rtl(request.width)}
    if request.task_type == "fifo":
        return {"rtl/top.v": _fifo_rtl(request.width)}
    if request.task_type == "simple_fsm":
        return {"rtl/top.v": _simple_fsm_rtl(max(2, request.width))}
    if request.task_type == "ram_read_write":
        return {"rtl/top.v": _ram_read_write_rtl(request.width)}
    if request.task_type == "uart_tx":
        return _uart_tx_rtl_files(request.width)
    if request.task_type == "spi_master":
        return _spi_master_rtl_files(request.width)
    if request.task_type == "pwm_controller":
        return _pwm_controller_rtl_files(request.width)
    if request.task_type == "fir_filter":
        return _fir_filter_rtl_files(request.width)
    if request.task_type == "streaming_valid_ready":
        return _streaming_valid_ready_rtl_files(request.width)
    if request.task_type == "matrix_vector_mac":
        return _matrix_vector_mac_rtl_files(request.width)
    raise ValueError(f"Unsupported task_type for V1: {request.task_type}")
```

Replace `_rtl(request)` with:

```python
def _rtl(request: ProjectRequest) -> str:
    return _rtl_files(request)["rtl/top.v"]
```

- [ ] **Step 4: Add explicit transitional multi-module builders so the contract can pass incrementally**

Add these intentionally simple builders after `_ram_read_write_testbench()`. They are concrete transitional implementations used only to establish the multi-source contract before Tasks 2 and 3 replace them with task-specific RTL.

```python
def _simple_passthrough_multimodule(task_name: str, width: int, submodule_name: str) -> dict[str, str]:
    msb = width - 1
    top = dedent(
        f"""\
        module top (
            input wire clk,
            input wire rst_n,
            input wire [{msb}:0] din,
            output wire [{msb}:0] dout
        );

          {submodule_name} u_core (
            .din(din),
            .dout(dout)
          );

        endmodule
        """
    )
    core = dedent(
        f"""\
        module {submodule_name} (
            input wire [{msb}:0] din,
            output wire [{msb}:0] dout
        );

          assign dout = din;

        endmodule
        """
    )
    return {
        "rtl/top.v": top,
        f"rtl/{task_name}_core.v": core,
    }


def _uart_tx_rtl_files(width: int) -> dict[str, str]:
    return _simple_passthrough_multimodule("uart_tx", width, "uart_tx_core")


def _spi_master_rtl_files(width: int) -> dict[str, str]:
    return _simple_passthrough_multimodule("spi_master", width, "spi_master_core")


def _pwm_controller_rtl_files(width: int) -> dict[str, str]:
    return _simple_passthrough_multimodule("pwm_controller", width, "pwm_channel")


def _fir_filter_rtl_files(width: int) -> dict[str, str]:
    return _simple_passthrough_multimodule("fir_filter", width, "fir_filter_core")


def _streaming_valid_ready_rtl_files(width: int) -> dict[str, str]:
    return _simple_passthrough_multimodule("streaming_valid_ready", width, "stream_stage")


def _matrix_vector_mac_rtl_files(width: int) -> dict[str, str]:
    return _simple_passthrough_multimodule("matrix_vector_mac", width, "dot_product_engine")
```

Add temporary testbench routing by appending these branches to `_testbench(request)` before the final raise:

```python
    if request.task_type in {
        "uart_tx",
        "spi_master",
        "pwm_controller",
        "fir_filter",
        "streaming_valid_ready",
        "matrix_vector_mac",
    }:
        return _passthrough_testbench(request.width)
```

Add `_passthrough_testbench(width)` after `_ram_read_write_testbench(width)`:

```python
def _passthrough_testbench(width: int) -> str:
    msb = width - 1
    return dedent(
        f"""\
        `timescale 1ns/1ps

        module tb_top;
          reg clk;
          reg rst_n;
          reg [{msb}:0] din;
          wire [{msb}:0] dout;

          top dut (
            .clk(clk),
            .rst_n(rst_n),
            .din(din),
            .dout(dout)
          );

          initial begin
            clk = 1'b0;
            forever #5 clk = ~clk;
          end

          initial begin
            rst_n = 1'b0;
            din = {width}'d0;
            repeat (2) @(posedge clk);
            rst_n = 1'b1;
            din = {width}'d7;
            #1;
            if (dout !== {width}'d7) begin
              $display("TEST_FAIL passthrough expected 7 got %0d", dout);
              $finish;
            end
            $display("TEST_PASS");
            $finish;
          end
        endmodule
        """
    )
```

Update `_default_description()`, `_interface()`, `_expected_behavior()`, and `_resource_shape()` so the temporary new tasks do not crash:

```python
        "uart_tx": f"Generate a {request.width}-bit UART transmitter with a baud tick generator.",
        "spi_master": f"Generate a {request.width}-bit SPI master with divided serial clock.",
        "pwm_controller": f"Generate a {request.width}-bit PWM controller with configurable duty cycle.",
        "fir_filter": f"Generate a {request.width}-bit fixed-coefficient FIR filter.",
        "streaming_valid_ready": f"Generate a {request.width}-bit valid-ready streaming pipeline.",
        "matrix_vector_mac": f"Generate a {request.width}-bit matrix-vector multiply-accumulate engine.",
```

For `_interface()`, initially route these new tasks to a generic `din/dout` interface:

```python
    elif request.task_type in {
        "uart_tx",
        "spi_master",
        "pwm_controller",
        "fir_filter",
        "streaming_valid_ready",
        "matrix_vector_mac",
    }:
        common.update(
            {
                "inputs": [
                    {"name": "clk", "width": 1},
                    {"name": "rst_n", "width": 1},
                    {"name": "din", "width": request.width},
                ],
                "outputs": [{"name": "dout", "width": request.width}],
            }
        )
```

For `_expected_behavior()` add:

```python
        "uart_tx": "UART transmitter serializes input data with start and stop bits",
        "spi_master": "SPI master shifts transmit data while sampling receive data",
        "pwm_controller": "PWM output stays high for the configured duty portion of each period",
        "fir_filter": "FIR filter produces fixed-coefficient convolution outputs",
        "streaming_valid_ready": "valid-ready pipeline preserves data order under backpressure",
        "matrix_vector_mac": "MAC engine computes a fixed dot product and raises done",
```

For `_resource_shape()` add:

```python
    if request.task_type == "uart_tx":
        return {"lut": max(12, request.width * 2), "ff": request.width + 16, "bram": 0, "dsp": 0}
    if request.task_type == "spi_master":
        return {"lut": max(16, request.width * 2), "ff": request.width * 2 + 16, "bram": 0, "dsp": 0}
    if request.task_type == "pwm_controller":
        return {"lut": max(8, request.width), "ff": request.width * 2, "bram": 0, "dsp": 0}
    if request.task_type == "fir_filter":
        return {"lut": max(20, request.width * 3), "ff": request.width * 3, "bram": 0, "dsp": 2}
    if request.task_type == "streaming_valid_ready":
        return {"lut": max(10, request.width), "ff": request.width * 2 + 4, "bram": 0, "dsp": 0}
    if request.task_type == "matrix_vector_mac":
        return {"lut": max(24, request.width * 4), "ff": request.width * 4, "bram": 0, "dsp": 2}
```

- [ ] **Step 5: Run the contract tests**

Run:

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_project_generator.ProjectGeneratorTest.test_manifest_sources_exist_for_all_supported_task_types -q
```

Expected: `OK`.

- [ ] **Step 6: Commit the multi-source contract**

Run:

```bash
python3 -m unittest discover -s LLM/tests -q
git add LLM/src/sr2fpga_agent/project_generator.py LLM/tests/test_sr2fpga_agent_project_generator.py
git commit -m "Add multi-source SR2FPGA project contract"
```

Expected: all tests pass and commit succeeds.

## Task 2: UART TX, PWM, And Valid-Ready Multi-Module Tasks

**Files:**
- Modify: `LLM/tests/test_sr2fpga_agent_project_generator.py`
- Modify: `LLM/src/sr2fpga_agent/project_generator.py`

- [ ] **Step 1: Write failing tests for three concrete multi-module tasks**

Add this helper near the other test helpers:

```python
def _assert_multimodule_task(
    testcase: unittest.TestCase,
    project,
    task_type: str,
    expected_sources: set[str],
    top_markers: list[str],
) -> None:
    manifest = _manifest(project)
    system_his = _system_his(project)
    testcase.assertEqual(system_his["task_type"], task_type)
    testcase.assertTrue(expected_sources.issubset(set(manifest["sources"])))
    testcase.assertTrue(expected_sources.issubset(set(project.files)))
    testcase.assertGreater(len(manifest["sources"]), 1)
    testcase.assertIn("architecture", system_his)
    testcase.assertIn("submodules", system_his["architecture"])
    for marker in top_markers:
        testcase.assertIn(marker, project.files["rtl/top.v"])
    testcase.assertIn("TEST_PASS", project.files["sim/tb_top.v"])
```

Add these tests inside `ProjectGeneratorTest`:

```python
def test_generates_uart_tx_multimodule_project_package(self) -> None:
    project = ProjectGenerator().generate(
        ProjectRequest(task_type="uart_tx", width=8, project_name="uart_tx_8bit"),
        PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
    )

    _assert_multimodule_task(
        self,
        project,
        "uart_tx",
        {"rtl/top.v", "rtl/uart_tx_core.v", "rtl/baud_tick_gen.v"},
        ["uart_tx_core", "baud_tick_gen", ".tx(tx)", ".busy(busy)"],
    )
    self.assertIn("output wire tx", project.files["rtl/top.v"])
    self.assertIn("TEST_PASS", project.files["sim/tb_top.v"])


def test_generates_pwm_controller_multimodule_project_package(self) -> None:
    project = ProjectGenerator().generate(
        ProjectRequest(task_type="pwm_controller", width=8, project_name="pwm_controller_8bit"),
        PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
    )

    _assert_multimodule_task(
        self,
        project,
        "pwm_controller",
        {"rtl/top.v", "rtl/pwm_timer.v", "rtl/pwm_channel.v"},
        ["pwm_timer", "pwm_channel", ".pwm_out(pwm_out)"],
    )
    self.assertIn("input wire [7:0] duty", project.files["rtl/top.v"])
    self.assertIn("TEST_PASS", project.files["sim/tb_top.v"])


def test_generates_streaming_valid_ready_multimodule_project_package(self) -> None:
    project = ProjectGenerator().generate(
        ProjectRequest(
            task_type="streaming_valid_ready",
            width=8,
            project_name="streaming_valid_ready_8bit",
        ),
        PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
    )

    _assert_multimodule_task(
        self,
        project,
        "streaming_valid_ready",
        {"rtl/top.v", "rtl/stream_stage.v", "rtl/skid_buffer.v"},
        ["stream_stage", "skid_buffer", ".in_valid(in_valid)", ".out_ready(out_ready)"],
    )
    self.assertIn("out_valid", project.files["rtl/top.v"])
    self.assertIn("TEST_PASS", project.files["sim/tb_top.v"])
```

- [ ] **Step 2: Run the new tests and verify they fail for the right reason**

Run:

```bash
python3 -m unittest \
  LLM.tests.test_sr2fpga_agent_project_generator.ProjectGeneratorTest.test_generates_uart_tx_multimodule_project_package \
  LLM.tests.test_sr2fpga_agent_project_generator.ProjectGeneratorTest.test_generates_pwm_controller_multimodule_project_package \
  LLM.tests.test_sr2fpga_agent_project_generator.ProjectGeneratorTest.test_generates_streaming_valid_ready_multimodule_project_package \
  -q
```

Expected: failures showing missing expected source files or missing top markers.

- [ ] **Step 3: Add architecture metadata**

Update `_system_his()` to include architecture metadata. Add this key after `"interface": _interface(request, platform),`:

```python
        "architecture": _architecture(request),
```

Add this helper before `_manifest()`:

```python
def _architecture(request: ProjectRequest) -> dict[str, object]:
    submodules = {
        "counter": [],
        "fifo": [],
        "simple_fsm": [],
        "ram_read_write": [],
        "uart_tx": ["baud_tick_gen", "uart_tx_core"],
        "spi_master": ["clock_divider", "spi_master_core"],
        "pwm_controller": ["pwm_timer", "pwm_channel"],
        "fir_filter": ["mac_unit", "fir_filter_core"],
        "streaming_valid_ready": ["skid_buffer", "stream_stage"],
        "matrix_vector_mac": ["vector_rom", "mac_unit", "dot_product_engine"],
    }
    return {
        "style": "multi_module" if submodules[request.task_type] else "single_module",
        "top_module": "top",
        "submodules": submodules[request.task_type],
    }
```

- [ ] **Step 4: Implement `uart_tx`**

Replace `_uart_tx_rtl_files(width)` with a real multi-module implementation containing:

- `rtl/top.v`
  - ports: `clk`, `rst_n`, `start`, `data[7:0]`, `tx`, `busy`, `done`
  - instantiates `baud_tick_gen` and `uart_tx_core`
- `rtl/baud_tick_gen.v`
  - ports: `clk`, `rst_n`, `enable`, `tick`
  - fixed divisor 4 for fast simulation
- `rtl/uart_tx_core.v`
  - ports: `clk`, `rst_n`, `baud_tick`, `start`, `data[7:0]`, `tx`, `busy`, `done`
  - sends start bit, 8 data bits LSB-first, stop bit

Use this top-level template exactly:

```python
def _uart_tx_rtl_files(width: int) -> dict[str, str]:
    top = dedent(
        """\
        module top (
            input wire clk,
            input wire rst_n,
            input wire start,
            input wire [7:0] data,
            output wire tx,
            output wire busy,
            output wire done
        );

          wire baud_tick;

          baud_tick_gen u_baud_tick_gen (
            .clk(clk),
            .rst_n(rst_n),
            .enable(busy),
            .tick(baud_tick)
          );

          uart_tx_core u_uart_tx_core (
            .clk(clk),
            .rst_n(rst_n),
            .baud_tick(baud_tick),
            .start(start),
            .data(data),
            .tx(tx),
            .busy(busy),
            .done(done)
          );

        endmodule
        """
    )
```

Complete the same function with `baud_tick_gen` and `uart_tx_core` strings. The core must use a 10-bit shift register loaded as `{1'b1, data, 1'b0}`, shift right on each baud tick, drive `tx <= shift_reg[0]`, count 10 bits, set `done` for one cycle, and return `tx` high when idle.

Replace the `uart_tx` branch in `_testbench()` with:

```python
    if request.task_type == "uart_tx":
        return _uart_tx_testbench()
```

Add `_uart_tx_testbench()` that:

- resets the design;
- sends `8'hA5`;
- waits for `busy`;
- samples `tx` after each 4-cycle baud interval;
- checks start bit `0`, data bits `1,0,1,0,0,1,0,1`, stop bit `1`;
- checks `done == 1'b1`;
- prints `TEST_PASS`.

- [ ] **Step 5: Implement `pwm_controller`**

Replace `_pwm_controller_rtl_files(width)` with:

- `rtl/top.v`
  - ports: `clk`, `rst_n`, `duty[width-1:0]`, `pwm_out`
  - instantiates `pwm_timer` and `pwm_channel`
- `rtl/pwm_timer.v`
  - increments a `counter[width-1:0]`
- `rtl/pwm_channel.v`
  - assigns `pwm_out = counter < duty`

Replace the `pwm_controller` branch in `_testbench()` with:

```python
    if request.task_type == "pwm_controller":
        return _pwm_controller_testbench(request.width)
```

Add `_pwm_controller_testbench(width)` that sets `duty = width'd3`, waits one reset cycle, counts output-high cycles over 8 clock cycles for `width >= 3`, and checks the high count equals 3.

- [ ] **Step 6: Implement `streaming_valid_ready`**

Replace `_streaming_valid_ready_rtl_files(width)` with:

- `rtl/top.v`
  - ports: `clk`, `rst_n`, `in_valid`, `in_ready`, `in_data[width-1:0]`,
    `out_valid`, `out_ready`, `out_data[width-1:0]`
  - instantiates `skid_buffer` then `stream_stage`
- `rtl/skid_buffer.v`
  - one-entry buffer with valid-ready handshake
- `rtl/stream_stage.v`
  - registered stage that preserves data order

Replace the `streaming_valid_ready` branch in `_testbench()` with:

```python
    if request.task_type == "streaming_valid_ready":
        return _streaming_valid_ready_testbench(request.width)
```

Add `_streaming_valid_ready_testbench(width)` that sends two values, stalls `out_ready` for two cycles between them, checks outputs arrive in order, and prints `TEST_PASS`.

- [ ] **Step 7: Update interfaces for the three tasks**

In `_interface()`, add task-specific branches for `uart_tx`, `pwm_controller`, and `streaming_valid_ready` before the generic branch. Use these port names:

```python
"uart_tx": inputs clk/rst_n/start/data[8], outputs tx/busy/done
"pwm_controller": inputs clk/rst_n/duty[width], output pwm_out
"streaming_valid_ready": inputs clk/rst_n/in_valid/in_data[width]/out_ready, outputs in_ready/out_valid/out_data[width]
```

- [ ] **Step 8: Run tests**

Run:

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_project_generator -q
python3 -m unittest discover -s LLM/tests -q
```

Expected: all tests pass.

- [ ] **Step 9: Commit**

Run:

```bash
git add LLM/src/sr2fpga_agent/project_generator.py LLM/tests/test_sr2fpga_agent_project_generator.py
git commit -m "Add control-oriented multi-module RTL tasks"
```

## Task 3: SPI, FIR, And Matrix-Vector MAC Multi-Module Tasks

**Files:**
- Modify: `LLM/tests/test_sr2fpga_agent_project_generator.py`
- Modify: `LLM/src/sr2fpga_agent/project_generator.py`

- [ ] **Step 1: Write failing tests for the remaining three tasks**

Add these tests inside `ProjectGeneratorTest`:

```python
def test_generates_spi_master_multimodule_project_package(self) -> None:
    project = ProjectGenerator().generate(
        ProjectRequest(task_type="spi_master", width=8, project_name="spi_master_8bit"),
        PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
    )

    _assert_multimodule_task(
        self,
        project,
        "spi_master",
        {"rtl/top.v", "rtl/spi_master_core.v", "rtl/clock_divider.v"},
        ["spi_master_core", "clock_divider", ".mosi(mosi)", ".miso(miso)", ".cs_n(cs_n)"],
    )
    self.assertIn("output wire sclk", project.files["rtl/top.v"])
    self.assertIn("TEST_PASS", project.files["sim/tb_top.v"])


def test_generates_fir_filter_multimodule_project_package(self) -> None:
    project = ProjectGenerator().generate(
        ProjectRequest(task_type="fir_filter", width=8, project_name="fir_filter_8bit"),
        PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
    )

    _assert_multimodule_task(
        self,
        project,
        "fir_filter",
        {"rtl/top.v", "rtl/fir_filter_core.v", "rtl/mac_unit.v"},
        ["fir_filter_core", "mac_unit", ".sample_valid(sample_valid)", ".result_valid(result_valid)"],
    )
    self.assertIn("result", project.files["rtl/top.v"])
    self.assertIn("TEST_PASS", project.files["sim/tb_top.v"])


def test_generates_matrix_vector_mac_multimodule_project_package(self) -> None:
    project = ProjectGenerator().generate(
        ProjectRequest(task_type="matrix_vector_mac", width=8, project_name="matrix_vector_mac_8bit"),
        PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
    )

    _assert_multimodule_task(
        self,
        project,
        "matrix_vector_mac",
        {"rtl/top.v", "rtl/dot_product_engine.v", "rtl/mac_unit.v", "rtl/vector_rom.v"},
        ["dot_product_engine", "mac_unit", "vector_rom", ".done(done)"],
    )
    self.assertIn("result", project.files["rtl/top.v"])
    self.assertIn("TEST_PASS", project.files["sim/tb_top.v"])
```

- [ ] **Step 2: Run the new tests and verify they fail for the right reason**

Run:

```bash
python3 -m unittest \
  LLM.tests.test_sr2fpga_agent_project_generator.ProjectGeneratorTest.test_generates_spi_master_multimodule_project_package \
  LLM.tests.test_sr2fpga_agent_project_generator.ProjectGeneratorTest.test_generates_fir_filter_multimodule_project_package \
  LLM.tests.test_sr2fpga_agent_project_generator.ProjectGeneratorTest.test_generates_matrix_vector_mac_multimodule_project_package \
  -q
```

Expected: failures showing missing expected source files or missing top markers.

- [ ] **Step 3: Implement `spi_master`**

Replace `_spi_master_rtl_files(width)` with:

- `rtl/top.v`
  - ports: `clk`, `rst_n`, `start`, `tx_data[7:0]`, `miso`, `rx_data[7:0]`,
    `busy`, `done`, `sclk`, `mosi`, `cs_n`
  - instantiates `clock_divider` and `spi_master_core`
- `rtl/clock_divider.v`
  - produces `shift_tick` every 2 clocks while enabled
- `rtl/spi_master_core.v`
  - CPOL=0, CPHA=0 style simple shift engine
  - lowers `cs_n` while busy
  - shifts out MSB first on `mosi`
  - samples `miso` into `rx_data`
  - raises `done` for one cycle after 8 bits

Replace the `spi_master` branch in `_testbench()` with:

```python
    if request.task_type == "spi_master":
        return _spi_master_testbench()
```

Add `_spi_master_testbench()` that drives `miso` with a known sequence, starts a transfer with `tx_data = 8'hA5`, waits for `done`, checks `cs_n == 1'b1`, checks `rx_data` equals the sampled sequence, and prints `TEST_PASS`.

- [ ] **Step 4: Implement `fir_filter`**

Replace `_fir_filter_rtl_files(width)` with:

- `rtl/top.v`
  - ports: `clk`, `rst_n`, `sample_valid`, `sample[width-1:0]`,
    `result_valid`, `result[(width+3)-1:0]`
  - instantiates `fir_filter_core`
- `rtl/fir_filter_core.v`
  - 3 taps with coefficients 1, 2, 1
  - shift register for the last three samples
  - instantiates two or three `mac_unit` instances
  - emits result on each valid input after registers update
- `rtl/mac_unit.v`
  - combinational multiply-add helper

Replace the `fir_filter` branch in `_testbench()` with:

```python
    if request.task_type == "fir_filter":
        return _fir_filter_testbench(request.width)
```

Add `_fir_filter_testbench(width)` that feeds `1, 2, 3`, then checks outputs match `1`, `4`, and `8` for coefficients `[1, 2, 1]`.

- [ ] **Step 5: Implement `matrix_vector_mac`**

Replace `_matrix_vector_mac_rtl_files(width)` with:

- `rtl/top.v`
  - ports: `clk`, `rst_n`, `start`, `busy`, `done`, `result[(width+4)-1:0]`
  - instantiates `dot_product_engine`
- `rtl/dot_product_engine.v`
  - fixed vector input `[1, 2, 3, 4]`
  - gets coefficients from `vector_rom`
  - instantiates `mac_unit`
  - accumulates over four cycles
- `rtl/vector_rom.v`
  - returns coefficients `[2, 1, 3, 1]`
- `rtl/mac_unit.v`
  - combinational multiply-add helper

Replace the `matrix_vector_mac` branch in `_testbench()` with:

```python
    if request.task_type == "matrix_vector_mac":
        return _matrix_vector_mac_testbench(request.width)
```

Add `_matrix_vector_mac_testbench(width)` that asserts `start`, waits for `done`, checks result equals `17`, and prints `TEST_PASS`.

- [ ] **Step 6: Update interfaces for the three tasks**

In `_interface()`, add task-specific branches:

```python
"spi_master": inputs clk/rst_n/start/tx_data[8]/miso, outputs rx_data[8]/busy/done/sclk/mosi/cs_n
"fir_filter": inputs clk/rst_n/sample_valid/sample[width], outputs result_valid/result[width+3]
"matrix_vector_mac": inputs clk/rst_n/start, outputs busy/done/result[width+4]
```

- [ ] **Step 7: Run tests**

Run:

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_project_generator -q
python3 -m unittest discover -s LLM/tests -q
```

Expected: all tests pass.

- [ ] **Step 8: Commit**

Run:

```bash
git add LLM/src/sr2fpga_agent/project_generator.py LLM/tests/test_sr2fpga_agent_project_generator.py
git commit -m "Add DSP and protocol multi-module RTL tasks"
```

## Task 4: Tool Smoke, Dataset Generation, And Handoff

**Files:**
- Modify: `docs/sr2fpga-agent-handoff-2026-06-22.md`
- No source changes unless a tool smoke reveals a real generator bug.

- [ ] **Step 1: Run full unit tests**

Run:

```bash
python3 -m unittest discover -s LLM/tests -q
```

Expected: all tests pass.

- [ ] **Step 2: Generate deterministic samples for the new task families**

Run this from the repo root:

```bash
python3 - <<'PY'
from pathlib import Path
from LLM.src.sr2fpga_agent.agent import DataGenerationAgent
from LLM.src.sr2fpga_agent.models import PlatformProfile, ProjectRequest

root = Path("datasets/sr2fpga_rtl_v1")
platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
cases = [
    ("sample_multimodule_000001", "uart_tx", 8, "uart_tx_8bit"),
    ("sample_multimodule_000002", "uart_tx", 12, "uart_tx_control_12width"),
    ("sample_multimodule_000003", "spi_master", 8, "spi_master_8bit"),
    ("sample_multimodule_000004", "spi_master", 12, "spi_master_control_12width"),
    ("sample_multimodule_000005", "pwm_controller", 8, "pwm_controller_8bit"),
    ("sample_multimodule_000006", "pwm_controller", 12, "pwm_controller_12bit"),
    ("sample_multimodule_000007", "fir_filter", 8, "fir_filter_8bit"),
    ("sample_multimodule_000008", "fir_filter", 12, "fir_filter_12bit"),
    ("sample_multimodule_000009", "streaming_valid_ready", 8, "streaming_valid_ready_8bit"),
    ("sample_multimodule_000010", "streaming_valid_ready", 12, "streaming_valid_ready_12bit"),
    ("sample_multimodule_000011", "matrix_vector_mac", 8, "matrix_vector_mac_8bit"),
    ("sample_multimodule_000012", "matrix_vector_mac", 12, "matrix_vector_mac_12bit"),
]

for sample_id, task_type, width, project_name in cases:
    requirement = (
        f"Design a multi-module Verilog RTL {task_type} project package with width {width}, "
        "active-low reset rst_n, self-checking testbench, manifest, timing constraint, and predicted QoR."
    )
    result = DataGenerationAgent(root).run_one(
        sample_id=sample_id,
        requirement=requirement,
        request=ProjectRequest(
            task_type=task_type,
            width=width,
            project_name=project_name,
            description=requirement,
        ),
        platform=platform,
    )
    print(sample_id, task_type, result["pass_level"])
PY
```

Expected: all generated samples should print `L3` when Verilator, Icarus Verilog, vvp, and Yosys are installed.

- [ ] **Step 3: Refresh exported training views**

Run:

```bash
python3 - <<'PY'
from pathlib import Path
from LLM.src.sr2fpga_agent.recorder import DatasetRecorder

DatasetRecorder(Path("datasets/sr2fpga_rtl_v1")).export_training_views(
    Path("datasets/sr2fpga_rtl_v1_exports")
)
for path in sorted(Path("datasets/sr2fpga_rtl_v1_exports").glob("*.jsonl")):
    print(path.name, sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip()))
PY
```

Expected: each project-level JSONL count increases by 12.

- [ ] **Step 4: Inspect generated samples**

Run:

```bash
python3 - <<'PY'
import json
from pathlib import Path

root = Path("datasets/sr2fpga_rtl_v1")
for sample_dir in sorted(root.glob("sample_multimodule_*")):
    labels = json.loads((sample_dir / "eval/labels.json").read_text(encoding="utf-8"))
    manifest = json.loads((sample_dir / "final/generated_project/manifest.json").read_text(encoding="utf-8"))
    system_his = json.loads((sample_dir / "final/generated_project/system_his.json").read_text(encoding="utf-8"))
    print(
        sample_dir.name,
        system_his["task_type"],
        labels["pass_level"],
        len(manifest["sources"]),
        ",".join(manifest["sources"]),
    )
PY
```

Expected: every `sample_multimodule_*` has more than one RTL source and pass level `L3`.

- [ ] **Step 5: Update handoff note**

Append this section to `docs/sr2fpga-agent-handoff-2026-06-22.md` with actual counts from Step 3:

```markdown
## Multi-Module Task Family Implementation

Implemented after spec:

`docs/superpowers/specs/2026-06-22-sr2fpga-multimodule-task-families-design.md`

New deterministic multi-module task families:

- `uart_tx`
- `spi_master`
- `pwm_controller`
- `fir_filter`
- `streaming_valid_ready`
- `matrix_vector_mac`

Generated local samples:

- `sample_multimodule_000001` through `sample_multimodule_000012`

Observed local labels:

- Record each sample's pass level here after running the inspection command.

Export counts after refresh:

- Record each JSONL file count here after running the export command.

Notes:

- Datasets remain untracked local artifacts.
- API keys were not used for deterministic generation.
- Next useful work: add failure injectors for multi-module-specific errors.
```

- [ ] **Step 6: Final verification**

Run:

```bash
python3 -m unittest discover -s LLM/tests -q
git diff --check -- LLM/src/sr2fpga_agent/project_generator.py LLM/tests/test_sr2fpga_agent_project_generator.py docs/sr2fpga-agent-handoff-2026-06-22.md
git status --short --branch
```

Expected:

- tests pass;
- `git diff --check` has no output;
- only intended source/doc files are modified;
- `datasets/` remains untracked.

- [ ] **Step 7: Commit**

Run:

```bash
git add LLM/src/sr2fpga_agent/project_generator.py LLM/tests/test_sr2fpga_agent_project_generator.py docs/sr2fpga-agent-handoff-2026-06-22.md
git commit -m "Generate multi-module SR2FPGA task samples"
```

Expected: commit succeeds without adding `datasets/`.

## Self-Review Checklist

- Spec coverage:
  - Six selected task families are included.
  - Multi-source manifest behavior is included.
  - System-HIS architecture metadata is included.
  - Unit tests and local tool smoke are included.
  - Dataset generation and export refresh are included.
- Completeness scan:
  - This plan contains no unresolved implementation gaps.
  - The temporary passthrough builders in Task 1 are explicit transitional code and are replaced by concrete task implementations in Tasks 2 and 3.
- Type consistency:
  - All code uses existing `ProjectRequest`, `PlatformProfile`, and `GeneratedProject`.
  - `manifest["sources"]` remains a list of POSIX-style relative paths.
  - `system_his["architecture"]["submodules"]` is consistently a list of module names.
