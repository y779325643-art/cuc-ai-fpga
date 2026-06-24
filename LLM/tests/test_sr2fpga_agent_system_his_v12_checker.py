import copy
import json
import unittest
from pathlib import Path

from LLM.src.sr2fpga_agent.system_his_v12_checker import check_system_his_v12


FIXTURE = Path("docs/system_his_examples/t4_dual_stream_join.system-his-v1.2.json")


class SystemHisV12CheckerTest(unittest.TestCase):
    def test_accepts_t4_topdown_example(self) -> None:
        result = check_system_his_v12(_fixture())

        self.assertTrue(result.passed, result.errors)
        self.assertEqual(result.errors, [])

    def test_rejects_instance_that_references_missing_component(self) -> None:
        payload = _fixture()
        payload["instances"][0]["component"] = "missing_component"

        result = check_system_his_v12(payload)

        self.assertFalse(result.passed)
        self.assertIn("instances[0] references missing component 'missing_component'", result.errors)

    def test_rejects_verilog_reserved_instance_name(self) -> None:
        payload = _fixture()
        payload["instances"][2]["name"] = "join"

        result = check_system_his_v12(payload)

        self.assertFalse(result.passed)
        self.assertIn("instances[2].name 'join' is a Verilog reserved keyword", result.errors)

    def test_rejects_verilog_gate_primitive_instance_name(self) -> None:
        payload = _fixture()
        payload["instances"][2]["name"] = "buf"

        result = check_system_his_v12(payload)

        self.assertFalse(result.passed)
        self.assertIn("instances[2].name 'buf' is a Verilog reserved keyword", result.errors)

    def test_rejects_data_flow_endpoint_that_uses_component_instead_of_instance(self) -> None:
        payload = _fixture()
        payload["data_flow"][0]["path"][1] = "skid_buffer.in_data"

        result = check_system_his_v12(payload)

        self.assertFalse(result.passed)
        self.assertIn(
            "data_flow 'input0_payload_to_join' endpoint 'skid_buffer.in_data' is not a valid top or instance port",
            result.errors,
        )

    def test_rejects_control_rule_references_to_missing_state_and_flow(self) -> None:
        payload = _fixture()
        payload["control_flow"][0]["related_state"].append("missing_state")
        payload["control_flow"][0]["related_flows"].append("missing_flow")

        result = check_system_his_v12(payload)

        self.assertFalse(result.passed)
        self.assertIn("control_flow 'reset_all_state' references missing state 'missing_state'", result.errors)
        self.assertIn("control_flow 'reset_all_state' references missing data_flow 'missing_flow'", result.errors)

    def test_accepts_owner_qualified_state_references(self) -> None:
        payload = _fixture()
        payload["state"]["buffers"][0]["name"] = "skid_register"
        payload["state"]["buffers"][0]["owner"] = "in0_buffer"
        payload["instances"][0]["owns_state"] = ["in0_buffer.skid_register"]
        payload["control_flow"][0]["related_state"][0] = "in0_buffer.skid_register"
        payload["control_flow"][1]["related_state"][0] = "in0_buffer.skid_register"

        result = check_system_his_v12(payload)

        self.assertTrue(result.passed, result.errors)

    def test_rejects_missing_required_sections(self) -> None:
        payload = _fixture()
        del payload["top"]

        result = check_system_his_v12(payload)

        self.assertFalse(result.passed)
        self.assertIn("system_his.top is required", result.errors)


def _fixture() -> dict[str, object]:
    return copy.deepcopy(json.loads(FIXTURE.read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
