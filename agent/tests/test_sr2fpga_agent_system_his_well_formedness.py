import copy
import json
import unittest
from pathlib import Path

from sr2fpga_agent.his_validation import validate_system_his_h_stages
from sr2fpga_agent.models import PlatformProfile, ProjectRequest
from sr2fpga_agent.project_generator import ProjectGenerator
from sr2fpga_agent.system_his_v12_checker import check_system_his_well_formedness
from sr2fpga_agent.task_families import SUPPORTED_TASK_TYPES


REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE = Path(__file__).parent / "fixtures" / "t4_dual_stream_join.system-his-v1.2.json"
MATRIX = REPO_ROOT / "contracts" / "system-his" / "system-his-well-formedness-v1.json"


class SystemHisWellFormednessTests(unittest.TestCase):
    def test_registered_matrix_matches_checker_rule_set(self) -> None:
        manifest = json.loads((REPO_ROOT / "contracts" / "manifest.json").read_text(encoding="utf-8"))
        entry = manifest["contracts"]["system_his_well_formedness"]
        matrix = json.loads(MATRIX.read_text(encoding="utf-8"))

        self.assertEqual(entry["version"], matrix["contract_version"])
        self.assertEqual((REPO_ROOT / entry["path"]).resolve(), MATRIX.resolve())
        self.assertEqual(
            [rule["rule_id"] for rule in matrix["rules"]],
            list(check_system_his_well_formedness(_fixture())),
        )

    def test_w1_component_reference_positive_and_negative(self) -> None:
        payload = _fixture()
        self.assertEqual(_rule(payload, "W1"), "pass")
        payload["instances"][0]["component"] = "missing_component"
        self.assertEqual(_rule(payload, "W1"), "fail")

    def test_w2_endpoint_reference_positive_and_negative(self) -> None:
        payload = _fixture()
        self.assertEqual(_rule(payload, "W2"), "pass")
        payload["data_flow"][0]["path"][0] = "top.missing"
        self.assertEqual(_rule(payload, "W2"), "fail")

    def test_w3_typed_connection_positive_and_negative(self) -> None:
        payload = _fixture()
        self.assertEqual(_rule(payload, "W3"), "not_applicable")
        payload["data_flow"][0]["connections"] = [
            {"from": "top.in0_data", "to": "in0_buffer.in_data"}
        ]
        self.assertEqual(_rule(payload, "W3"), "pass")
        payload["data_flow"][0]["connections"][0]["from"] = "top.in0_ready"
        self.assertEqual(_rule(payload, "W3"), "fail")

    def test_w4_state_clock_reset_positive_and_negative(self) -> None:
        payload = _fixture()
        self.assertEqual(_rule(payload, "W4"), "pass")
        payload["instances"][0]["clock"] = "missing_clock"
        self.assertEqual(_rule(payload, "W4"), "fail")

    def test_w5_combinational_declaration_positive_and_negative(self) -> None:
        payload = _fixture()
        self.assertEqual(_rule(payload, "W5"), "not_applicable")
        join = next(component for component in payload["components"] if component["name"] == "stream_join")
        join["combinational"] = True
        payload["state"]["fsms"] = []
        self.assertEqual(_rule(payload, "W5"), "pass")
        payload["instances"][2]["owns_state"] = ["unexpected_state"]
        self.assertEqual(_rule(payload, "W5"), "fail")

    def test_w6_cdc_positive_and_negative(self) -> None:
        payload = _fixture()
        self.assertEqual(_rule(payload, "W6"), "not_applicable")
        payload["top"]["clocks"].append({"name": "clk_aux", "target_fmax_mhz": 50})
        payload["instances"][0]["clock"] = "clk_aux"
        payload["data_flow"][0]["cdc"] = True
        self.assertEqual(_rule(payload, "W6"), "fail")
        next(component for component in payload["components"] if component["name"] == "skid_buffer")[
            "semantic_kind"
        ] = "synchronizer"
        self.assertEqual(_rule(payload, "W6"), "pass")

    def test_w7_memory_intent_positive_and_negative(self) -> None:
        payload = _fixture()
        self.assertEqual(_rule(payload, "W7"), "not_applicable")
        payload["state"]["memories"] = [{"name": "mem", "owner": "accumulator", "depth": 16}]
        self.assertEqual(_rule(payload, "W7"), "fail")
        payload["state"]["memories"][0].update(
            {"width": 8, "read_latency": 1, "read_type": "sync", "memory_style": "block"}
        )
        self.assertEqual(_rule(payload, "W7"), "pass")

    def test_w8_verification_reference_positive_and_negative(self) -> None:
        payload = _fixture()
        self.assertEqual(_rule(payload, "W8"), "pass")
        payload["verification"]["scenarios"][0]["related_flows"] = ["missing_flow"]
        self.assertEqual(_rule(payload, "W8"), "fail")

    def test_w9_constraint_reference_positive_and_negative(self) -> None:
        payload = _fixture()
        self.assertEqual(_rule(payload, "W9"), "pass")
        payload["timing"]["constraints"].append("constraints/missing.sdc")
        self.assertEqual(_rule(payload, "W9"), "fail")

    def test_w10_artifact_reproducibility_positive_and_negative(self) -> None:
        payload = _fixture()
        self.assertEqual(_rule(payload, "W10"), "pass")
        payload["artifacts"]["top_module"] = "wrong_top"
        self.assertEqual(_rule(payload, "W10"), "fail")

    def test_all_deterministic_system_his_payloads_have_no_failed_w_rule(self) -> None:
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
        for task_type in sorted(SUPPORTED_TASK_TYPES):
            with self.subTest(task_type=task_type):
                project = ProjectGenerator().generate(
                    ProjectRequest(task_type=task_type, width=8, project_name=f"conformance_{task_type}"),
                    platform,
                )
                report = check_system_his_well_formedness(json.loads(project.files["system_his.json"]))
                failures = {rule_id: result.diagnostics for rule_id, result in report.items() if result.status == "fail"}
                self.assertEqual(failures, {})
                self.assertEqual(report["W5"].status, "pass")
                payload = json.loads(project.files["system_his.json"])
                expected_w3 = "pass" if payload.get("connections") else "not_applicable"
                self.assertEqual(report["W3"].status, expected_w3)

    def test_all_deterministic_system_his_payloads_pass_h0_h1_h2(self) -> None:
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
        for task_type in sorted(SUPPORTED_TASK_TYPES):
            with self.subTest(task_type=task_type):
                request = ProjectRequest(
                    task_type=task_type,
                    width=8,
                    project_name=f"stage_conformance_{task_type}",
                )
                project = ProjectGenerator().generate(request, platform)
                report = validate_system_his_h_stages(request, project, platform=platform)
                self.assertEqual(report["h0"]["status"], "pass", report["h0"]["diagnostics"])
                self.assertEqual(report["h1"]["status"], "pass", report["h1"]["diagnostics"])
                self.assertEqual(report["h2"]["status"], "pass", report["h2"]["diagnostics"])


def _fixture() -> dict:
    return copy.deepcopy(json.loads(FIXTURE.read_text(encoding="utf-8")))


def _rule(payload: dict, rule_id: str) -> str:
    return check_system_his_well_formedness(payload)[rule_id].status


if __name__ == "__main__":
    unittest.main()
