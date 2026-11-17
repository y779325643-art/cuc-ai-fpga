# Training Test Fixtures

`smoke_verilog_raw.jsonl` is a small tracked input used to verify dataset
conversion and no-model dry-run behavior. It is test data, not a released
SR2FPGA dataset, and not a benchmark instance under any Paper-1 plan version.

Tests must write converted output to pytest temporary directories. Runtime
prepared data belongs under ignored `artifacts/training/prepared-data/`.
