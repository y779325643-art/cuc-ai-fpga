"""Exercise the public development entry point, never internal-only assembly."""

import json
import subprocess
import sys
from pathlib import Path


def test_public_input_roundtrip_and_no_overwrite(tmp_path):
    fixture = Path(__file__).parent / "fixtures" / "pc21_input_smoke" / "design.json"
    sources = []
    for name in ("requirements", "target-profile", "capability-profile"):
        source = tmp_path / f"{name}.txt"
        source.write_bytes(f"public schema-fixture {name}\n".encode())
        sources.extend([f"--{name}", str(source), f"--{name}-id", name])
    common = [*sources, "--max-bytes", "100000", "--max-depth", "64"]
    output = tmp_path / "pc.json"
    command = [sys.executable, "-m", "sr2fpga_agent.pc"]

    def run(*args):
        return subprocess.run([*command, *args, *common], capture_output=True,
                              text=True, timeout=20, check=False)

    result = run("assemble", "--input", str(fixture), "--output", str(output))
    assert result.returncode == 0, result.stderr
    receipt = json.loads(result.stdout)
    assert receipt["input_schema_and_bindings"] == "pass"
    assert receipt["semantic_validation"] == "partial"
    assert receipt["semantic_checks"] == {
        "entry_module_exists": "pass",
        "instance_modules_exist": "pass",
        "module_hierarchy_acyclic": "pass",
        "all_modules_reachable": "pass",
        "signature_sources_valid": "pass",
        "instance_parameter_names_valid": "pass",
        "instance_parameter_bindings_complete": "pass",
    }
    assert receipt["rtl_construction"] == "not_run"
    original = output.read_bytes()
    assert run("check", "--input", str(output)).returncode == 0
    assert run("assemble", "--input", str(fixture), "--output", str(output)).returncode == 2
    assert output.read_bytes() == original
    (tmp_path / "requirements.txt").write_bytes(b"changed public input")
    result = run("check", "--input", str(output))
    assert result.returncode == 2
    assert "binding mismatch" in result.stderr


def test_public_command_rejects_old_format(tmp_path):
    source = tmp_path / "source"
    source.write_bytes(b"public")
    old = tmp_path / "old.json"
    old.write_text('{"schema_version":"system-his-v1.2"}', encoding="utf-8")
    args = [sys.executable, "-m", "sr2fpga_agent.pc", "check", "--input", str(old),
            "--max-bytes", "10000", "--max-depth", "64"]
    for name in ("requirements", "target-profile", "capability-profile"):
        args.extend([f"--{name}", str(source), f"--{name}-id", name])
    result = subprocess.run(args, capture_output=True, text=True, timeout=20, check=False)
    assert result.returncode == 2
    assert "PC2.1 input rejected" in result.stderr


def test_public_command_rejects_missing_entry_without_writing_output(tmp_path):
    invalid_design = tmp_path / "invalid-design.json"
    invalid_design.write_text(json.dumps({
        "entry": "MissingTop",
        "modules": {
            "Top": {
                "signature": {"source": "requirement_boundary"},
                "implementation": {"kind": "structural", "instances": {}, "nets": {}},
            },
        },
        "requirement_map": [],
    }), encoding="utf-8")
    output = tmp_path / "pc.json"
    args = [
        sys.executable, "-m", "sr2fpga_agent.pc", "assemble",
        "--input", str(invalid_design), "--output", str(output),
        "--max-bytes", "10000", "--max-depth", "64",
    ]
    for name in ("requirements", "target-profile", "capability-profile"):
        source = tmp_path / f"{name}.txt"
        source.write_bytes(b"public")
        args.extend([f"--{name}", str(source), f"--{name}-id", name])

    result = subprocess.run(args, capture_output=True, text=True, timeout=20, check=False)

    assert result.returncode == 2
    assert "entry module is not defined: MissingTop" in result.stderr
    assert not output.exists()


def test_public_command_rejects_missing_parameter_without_output(tmp_path):
    fixture = Path(__file__).parent / "fixtures" / "pc21_input_smoke" / "design.json"
    design = json.loads(fixture.read_text(encoding="utf-8"))
    design["modules"]["Top"]["implementation"]["instances"]["ram_a"] = {
        "module": "RamWrapper", "parameters": {}, "domains": {},
    }
    design["modules"]["RamWrapper"] = {
        "signature": {
            "source": "declared",
            "parameters": {"DEPTH": {"minimum": 1, "maximum": 4096}},
            "domains": {}, "ports": {},
        },
        "implementation": {
            "kind": "behavioral", "execution": "combinational",
            "intent": "Parameter binding fixture only; no RAM implementation.",
        },
    }
    candidate = tmp_path / "design.json"
    candidate.write_text(json.dumps(design), encoding="utf-8")
    output = tmp_path / "pc.json"
    args = [sys.executable, "-m", "sr2fpga_agent.pc", "assemble",
            "--input", str(candidate), "--output", str(output),
            "--max-bytes", "100000", "--max-depth", "64"]
    for name in ("requirements", "target-profile", "capability-profile"):
        source = tmp_path / f"{name}.txt"
        source.write_bytes(b"public schema-only fixture")
        args.extend([f"--{name}", str(source), f"--{name}-id", name])
    result = subprocess.run(args, capture_output=True, text=True, timeout=20, check=False)
    assert result.returncode == 2
    assert "instance parameter bindings are missing: Top.ram_a -> RamWrapper: DEPTH" in result.stderr
    assert not output.exists()
