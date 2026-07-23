#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 3 ]]; then
  echo "usage: openxc7_pnr.sh <project_dir> <part> <clock_period_ns>" >&2
  exit 2
fi

project_dir_arg="$1"
part="$2"
clock_period_ns="$3"

if command -v wslpath >/dev/null 2>&1 && [[ "$project_dir_arg" =~ ^[A-Za-z]:[\\/] ]]; then
  project_dir="$(wslpath -u "$project_dir_arg")"
else
  project_dir="$project_dir_arg"
fi

if [[ ! -f "$project_dir/manifest.json" ]]; then
  echo "manifest not found: $project_dir/manifest.json" >&2
  exit 1
fi

if [[ -f "$HOME/.nix-profile/etc/profile.d/nix.sh" ]]; then
  # Non-interactive WSL launches do not always load the single-user Nix profile.
  # shellcheck source=/dev/null
  . "$HOME/.nix-profile/etc/profile.d/nix.sh"
fi

flake_path="${OPENXC7_FLAKE_PATH:-}"
if [[ "${OPENXC7_IN_NIX_SHELL:-0}" != "1" && -n "$flake_path" && -d "$flake_path" ]] && command -v nix >/dev/null 2>&1; then
  export OPENXC7_IN_NIX_SHELL=1
  exec nix develop "$flake_path" --option sandbox false -c bash "$0" "$project_dir" "$part" "$clock_period_ns"
fi

for tool in yosys nextpnr-xilinx python3; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "Missing executable: $tool" >&2
    exit 127
  fi
done

part_base="${part%%-*}"
part_base="${part_base,,}"
chipdb_dir="${OPENXC7_CHIPDB_DIR:-}"
if [[ -z "$chipdb_dir" && -n "${NEXTPNR_XILINX_CHIPDB_DIR:-}" ]]; then
  chipdb_dir="${NEXTPNR_XILINX_CHIPDB_DIR%%:*}"
fi
if [[ -z "$chipdb_dir" && -n "$flake_path" && -d "$flake_path" ]] && command -v nix >/dev/null 2>&1; then
  chipdb_dir="$(nix build "$flake_path#nextpnr-xilinx-chipdb.zynq7" --option sandbox false --no-link --print-out-paths)"
fi

chipdb_file=""
if [[ -n "$chipdb_dir" && -f "$chipdb_dir/$part_base.bin" ]]; then
  chipdb_file="$chipdb_dir/$part_base.bin"
elif [[ -n "$chipdb_dir" ]]; then
  chipdb_file="$(find "$chipdb_dir" -maxdepth 2 -name "$part_base.bin" -print -quit)"
fi
if [[ -z "$chipdb_file" || ! -f "$chipdb_file" ]]; then
  echo "OpenXC7 chipdb not found for part base: $part_base" >&2
  exit 1
fi

cd "$project_dir"
mkdir -p eval

python3 - "$part" "$clock_period_ns" <<'PY'
import json
from pathlib import Path
import sys

part = sys.argv[1]
clock_period_ns = sys.argv[2]
manifest = json.loads(Path("manifest.json").read_text(encoding="utf-8"))
sources = manifest["sources"]
top_module = manifest.get("top_module", "top")

with Path("eval/openxc7_yosys.ys").open("w", encoding="utf-8") as handle:
    for source in sources:
        handle.write(f"read_verilog -sv {source}\n")
    handle.write(f"synth_xilinx -family xc7 -top {top_module}\n")
    handle.write("write_json eval/openxc7_design.json\n")

clock_name = "clk"
port_names = []
try:
    system_his = json.loads(Path("system_his.json").read_text(encoding="utf-8"))
    clocks = system_his.get("clocks", [])
    if clocks and isinstance(clocks[0], dict) and clocks[0].get("name"):
        clock_name = str(clocks[0]["name"])
    for port in system_his.get("top_ports", []):
        if isinstance(port, dict) and port.get("name"):
            name = str(port["name"])
            width = port.get("width", 1)
            if isinstance(width, int) and width > 1:
                port_names.extend(f"{name}[{index}]" for index in range(width))
            else:
                port_names.append(name)
except (FileNotFoundError, json.JSONDecodeError):
    pass
if not port_names:
    port_names = [clock_name]

Path("eval/openxc7_clock.xdc").write_text(
    "".join(f"set_property IOSTANDARD LVCMOS33 [get_ports {{{port}}}]\n" for port in port_names)
    + f"create_clock -period {clock_period_ns} [get_ports {{{clock_name}}}]\n",
    encoding="utf-8",
)
PY

freq_mhz="$(python3 - "$clock_period_ns" <<'PY'
import sys
period = float(sys.argv[1])
print(f"{1000.0 / period:.3f}" if period > 0 else "100.000")
PY
)"

print_failure_logs() {
  status=$?
  if [[ $status -ne 0 ]]; then
    for log in eval/openxc7_yosys.log eval/openxc7_nextpnr.log; do
      if [[ -f "$log" ]]; then
        echo "===== $log =====" >&2
        tail -200 "$log" >&2
      fi
    done
  fi
}
trap print_failure_logs EXIT

yosys -q -s eval/openxc7_yosys.ys > eval/openxc7_yosys.log 2>&1
nextpnr-xilinx \
  --chipdb "$chipdb_file" \
  --xdc eval/openxc7_clock.xdc \
  --json eval/openxc7_design.json \
  --write eval/openxc7_routed.json \
  --fasm eval/openxc7_design.fasm \
  --freq "$freq_mhz" \
  > eval/openxc7_nextpnr.log 2>&1

python3 - <<'PY'
import json
from pathlib import Path

log = Path("eval/openxc7_nextpnr.log").read_text(encoding="utf-8")
Path("eval/openxc7_report.json").write_text(
    json.dumps({"tool": "nextpnr-xilinx", "log": log}, indent=2),
    encoding="utf-8",
)
PY

cat eval/openxc7_nextpnr.log
cat eval/openxc7_report.json
