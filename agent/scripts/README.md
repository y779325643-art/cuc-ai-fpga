# Agent Scripts

- `analyze_phase_d_h2_failures.py` replays frozen Phase D System-HIS inputs
  through the current H2 validator.
- `audit_phase_d_pilot.py` checks the integrity of a frozen Phase D run.
- `openxc7_pnr.sh` runs the caller-selected generated project through the
  OpenXC7/nextpnr flow.

Python scripts import the canonical `sr2fpga_agent` package. When executed
directly from this repository, they resolve `agent/src` from their own location
or from `SR2FPGA_REPO_ROOT`. OpenXC7 project and output paths remain
caller-controlled.

`openxc7_pnr.sh` does not contain a machine-specific toolchain path. Set
`OPENXC7_FLAKE_PATH` for a Nix flake, or provide `OPENXC7_CHIPDB_DIR` /
`NEXTPNR_XILINX_CHIPDB_DIR` when the tools are already installed.
