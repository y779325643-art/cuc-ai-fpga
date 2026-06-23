# SR2FPGA Multi-Module Task Families Design

## Purpose

Extend the SR2FPGA data-generation agent from small single-file RTL examples to
multi-module FPGA project packages. The next dataset stage should teach the
model to generate realistic project structure: top-level integration, reusable
submodules, cross-file source lists, protocol timing, data paths, testbenches,
constraints, predicted QoR, and tool-verified labels.

This remains inside the current SR2FPGA boundary:

- Generate Verilog RTL, not HLS.
- Do not use vendor IP, encrypted IP, DDR, PCIe, or board-specific primitives.
- Do not generate bitstreams.
- Validate with open-source tools first: Verilator, Icarus Verilog, vvp, and
  Yosys.
- Keep predicted QoR model-generated before tools run; keep measured QoR parsed
  from tool output after synthesis.

## Selected Task Families

Add six balanced task families:

1. `uart_tx`
2. `spi_master`
3. `pwm_controller`
4. `fir_filter`
5. `streaming_valid_ready`
6. `matrix_vector_mac`

These cover protocol control, timed serial output, flow control, DSP-style
multiply-accumulate, and small structured compute. They are more complex than
`counter`, `fifo`, `simple_fsm`, and `ram_read_write`, but remain portable and
tool-checkable.

## Generated Project Shape

Every task still emits the same project package contract:

```text
generated_project/
  system_his.json
  manifest.json
  rtl/top.v
  rtl/<submodule_1>.v
  rtl/<submodule_2>.v
  ...
  constraints/timing.sdc
  sim/tb_top.v
  reports/predicted_qor.json
```

`rtl/top.v` should be an integration wrapper. It should expose the task-level
interface, instantiate submodules, and avoid hiding the whole implementation
inside the top module. `manifest.json["sources"]` must include every RTL source
file in dependency order where possible, with `rtl/top.v` included.

## Task-Level Module Decomposition

### `uart_tx`

Suggested files:

- `rtl/top.v`
- `rtl/uart_tx_core.v`
- `rtl/baud_tick_gen.v`

Behavior:

- Active-low reset.
- `start`, parallel `data`, `busy`, and serial `tx` interface.
- Emits start bit, 8 data bits, and stop bit.
- Testbench checks bit order and busy behavior using a small baud divisor.

### `spi_master`

Suggested files:

- `rtl/top.v`
- `rtl/spi_master_core.v`
- `rtl/clock_divider.v`

Behavior:

- Active-low reset.
- `start`, `tx_data`, `rx_data`, `busy`, `done`, `sclk`, `mosi`, `miso`,
  `cs_n`.
- Use one simple SPI mode for V1, preferably CPOL=0 and CPHA=0.
- Testbench drives `miso`, observes `mosi`, and checks `done` plus received
  byte.

### `pwm_controller`

Suggested files:

- `rtl/top.v`
- `rtl/pwm_timer.v`
- `rtl/pwm_channel.v`

Behavior:

- Active-low reset.
- Configurable duty input and PWM output.
- Counter period can be derived from `width`.
- Testbench checks that output is high for the expected number of cycles within
  one period.

### `fir_filter`

Suggested files:

- `rtl/top.v`
- `rtl/fir_filter_core.v`
- `rtl/mac_unit.v`

Behavior:

- Active-low reset.
- Valid input sample stream and valid output.
- Use a small fixed coefficient set in RTL for portability.
- Testbench feeds a short input sequence and checks exact output values after
  pipeline latency.

### `streaming_valid_ready`

Suggested files:

- `rtl/top.v`
- `rtl/stream_stage.v`
- `rtl/skid_buffer.v`

Behavior:

- Active-low reset.
- Input `valid/ready/data` and output `valid/ready/data`.
- Preserve order under backpressure.
- Testbench applies stalls and checks no data is lost or duplicated.

### `matrix_vector_mac`

Suggested files:

- `rtl/top.v`
- `rtl/dot_product_engine.v`
- `rtl/mac_unit.v`
- `rtl/vector_rom.v`

Behavior:

- Active-low reset.
- `start`, `busy`, `done`, and result output.
- Compute a small fixed dot product or matrix-vector row product.
- Keep dimensions tiny for fast simulation and synthesis.
- Testbench checks the exact final accumulated result.

## System-HIS And Manifest Requirements

`system_his.json` should include:

- `task_type`
- natural-language requirement
- interface ports
- reset and clock assumptions
- expected behavior summary
- submodule list or architecture summary for multi-module tasks

`manifest.json` should include:

- `top_module: "top"`
- all RTL files under `sources`
- timing constraint path
- self-checking testbench path
- predicted QoR path
- clock and reset metadata

The generator and tests should reject or fail if a source listed in the manifest
is missing, or if a generated submodule is not listed in the manifest.

## Validation Flow

The existing pipeline remains unchanged:

```text
Verilator lint -> Icarus compile -> vvp simulation -> Yosys synth
```

Expected pass target for deterministic samples is L3. L4 timing and board-level
evaluation stay out of scope for this task-family expansion.

## Dataset Impact

After implementation, generate deterministic samples for each new task family
across a small width/configuration set. The initial target should be modest:

- at least 2 width/config variants per new task family;
- all deterministic samples reaching L3;
- exported JSONL views refreshed under `datasets/sr2fpga_rtl_v1_exports`;
- no generated datasets committed to Git.

The next repair-data pass can apply failure injectors to these multi-module
projects, especially:

- missing source in `manifest.json`;
- submodule port mismatch;
- wrong testbench expectation;
- valid-ready data loss;
- arithmetic width mismatch;
- missing reset propagation.

## Error Handling

Unsupported task types should continue to raise `ValueError`. Non-positive
widths should continue to raise `ValueError`.

For new tasks, prefer simple deterministic parameters derived from `width` over
adding new request fields. If a task needs an internal fixed parameter, document
it in `system_his.json` and `predicted_qor.json`.

## Testing Requirements

Add tests that prove:

- each new task family generates a complete project package;
- `manifest.json["sources"]` contains `rtl/top.v` and all submodule files;
- every listed source exists in `GeneratedProject.files`;
- `rtl/top.v` instantiates at least one task-specific submodule;
- `sim/tb_top.v` contains `TEST_PASS`;
- the open-source tool pipeline can generate L3 samples for representative
  cases when the local tools are installed;
- existing single-file task families still pass their current tests.

## Acceptance Criteria

The implementation is complete when:

1. The deterministic generator supports all six new task types.
2. Each new task emits more than one RTL source file.
3. Existing and new unit tests pass.
4. A small batch of new samples is generated locally and reaches L3 where tools
   are available.
5. Training views are refreshed and counts are recorded in a handoff note.
6. API keys, generated datasets, model weights, and tool output directories are
   not committed.

## Out Of Scope

- Vendor-specific IP blocks.
- AXI full protocol, DDR, PCIe, Ethernet MAC, or board pin planning.
- Bitstream generation.
- Timing closure with Vivado or Quartus.
- New model fine-tuning runs.
- Refactoring the entire generator architecture unless needed to keep the new
  task-family code maintainable.
