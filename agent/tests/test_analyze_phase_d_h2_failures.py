import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from sr2fpga_agent import PlatformProfile, ProjectGenerator, ProjectRequest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "agent" / "scripts" / "analyze_phase_d_h2_failures.py"


class PhaseDH2FailureAnalysisTests(unittest.TestCase):
    def test_cli_replays_h2_and_classifies_generation_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            dataset = root / "dataset"
            output = root / "analysis.json"
            _write_h2_sample(dataset / "sample_h2")
            _write_generation_failure_sample(dataset / "sample_gen")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--dataset-root",
                    str(dataset),
                    "--output",
                    str(output),
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(report["total_samples"], 2)
            self.assertEqual(report["pass_level_distribution"], {"GEN_FAIL": 1, "H2_FAIL": 1})
            self.assertEqual(report["generation_failures"]["categories"], {"invalid_json": 1})
            self.assertEqual(report["h2_replay"]["candidates"], 1)
            self.assertEqual(report["h2_replay"]["after_status"], {"pass": 1})
            self.assertEqual(report["h2_replay"]["changed_to_pass"], ["sample_h2"])


def _write_h2_sample(sample: Path) -> None:
    request = ProjectRequest(task_type="fifo", width=8, project_name="fifo_8bit")
    project = ProjectGenerator().generate(
        request,
        PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
    )
    payload = json.loads(project.files["system_his.json"])
    payload["components"][0]["semantic_kind"] = "synchronous_fifo"
    payload["verification"]["scenarios"] = [{"name": "reset_counter", "kind": "reset"}]
    _write_json(
        sample / "metadata.json",
        {"source": "gpt", "family_id": "sync_fifo", "task_type": "fifo", "width": 8},
    )
    (sample / "requirement.txt").parent.mkdir(parents=True, exist_ok=True)
    (sample / "requirement.txt").write_text("Generate an 8-bit synchronous FIFO.\n", encoding="utf-8")
    _write_json(
        sample / "eval" / "trajectory.json",
        {
            "measurement": {"final": {"pass_level": "H2_FAIL"}},
            "his_validation": {
                "h2": {
                    "status": "fail",
                    "diagnostics": [
                        "H2 lowerability: verification.scenarios[0] unsupported scenario "
                        "'{'name': 'reset_counter', 'kind': 'reset'}'"
                    ],
                }
            },
        },
    )
    _write_json(sample / "final" / "generated_project" / "system_his.json", payload)


def _write_generation_failure_sample(sample: Path) -> None:
    _write_json(
        sample / "metadata.json",
        {"source": "claude", "family_id": "counter", "task_type": "counter", "width": 8},
    )
    (sample / "requirement.txt").parent.mkdir(parents=True, exist_ok=True)
    (sample / "requirement.txt").write_text("Generate an 8-bit counter.\n", encoding="utf-8")
    _write_json(
        sample / "eval" / "trajectory.json",
        {"measurement": {"final": {"pass_level": "GEN_FAIL"}}},
    )
    _write_json(
        sample / "attempts" / "attempt_000" / "diagnosis.json",
        {
            "failure_type": "generation_failed",
            "root_cause": "System-HIS output is not valid JSON: Expecting property name",
        },
    )


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
