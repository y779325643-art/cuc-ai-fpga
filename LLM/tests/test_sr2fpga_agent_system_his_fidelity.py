import copy
import json
import unittest

from LLM.src.sr2fpga_agent.models import PlatformProfile, ProjectRequest
from LLM.src.sr2fpga_agent.project_generator import ProjectGenerator
from LLM.src.sr2fpga_agent.system_his_fidelity import check_system_his_req_fidelity


class SystemHisReqFidelityTest(unittest.TestCase):
    def test_composed_event_counter_accepts_deterministic_his(self) -> None:
        request = ProjectRequest(
            task_type="composed_event_counter",
            width=8,
            project_name="event_counter_8bit",
        )
        system_his = _deterministic_system_his(request)

        result = check_system_his_req_fidelity(request, system_his)

        self.assertTrue(result.passed, result.errors)

    def test_fidelity_result_reports_reframe_metric_dimensions(self) -> None:
        request = ProjectRequest(
            task_type="composed_stream_accumulator",
            width=8,
            project_name="stream_accum_8bit",
        )
        system_his = _deterministic_system_his(request)

        result = check_system_his_req_fidelity(request, system_his)

        self.assertEqual(
            set(result.metrics),
            {
                "interface_extraction",
                "clock_reset_fidelity",
                "parameter_fidelity",
                "behavior_intent_fidelity",
                "verification_intent_fidelity",
                "constraint_fidelity",
            },
        )
        self.assertEqual(result.metrics["interface_extraction"]["status"], "pass")
        self.assertEqual(result.metrics["parameter_fidelity"]["status"], "pass")
        self.assertEqual(result.metrics["clock_reset_fidelity"]["status"], "pass")
        self.assertEqual(result.metrics["verification_intent_fidelity"]["status"], "pass")
        self.assertEqual(result.metrics["constraint_fidelity"]["status"], "pass")

    def test_fidelity_flags_clock_reset_verification_and_constraint_drift(self) -> None:
        request = ProjectRequest(
            task_type="composed_stream_accumulator",
            width=8,
            project_name="stream_accum_8bit",
        )
        system_his = _deterministic_system_his(request)
        system_his["top"]["resets"][0]["polarity"] = "active_high"
        system_his["verification"]["pass_condition"] = ""
        system_his["timing"]["target_fmax_mhz"] = 0

        result = check_system_his_req_fidelity(request, system_his)

        self.assertFalse(result.passed)
        self.assertEqual(result.metrics["clock_reset_fidelity"]["status"], "fail")
        self.assertEqual(result.metrics["verification_intent_fidelity"]["status"], "fail")
        self.assertEqual(result.metrics["constraint_fidelity"]["status"], "fail")
        self.assertIn("REQ2HIS fidelity: reset rst_n polarity must be active_low", result.errors)
        self.assertIn("REQ2HIS fidelity: verification.pass_condition is required", result.errors)
        self.assertIn("REQ2HIS fidelity: timing.target_fmax_mhz must be positive", result.errors)

    def test_composed_event_counter_requires_expected_components(self) -> None:
        request = ProjectRequest(
            task_type="composed_event_counter",
            width=8,
            project_name="event_counter_8bit",
        )
        system_his = _deterministic_system_his(request)
        system_his["components"] = [
            component for component in system_his["components"] if component["name"] != "event_gate"
        ]

        result = check_system_his_req_fidelity(request, system_his)

        self.assertFalse(result.passed)
        self.assertIn("REQ2HIS fidelity: composed_event_counter requires component 'event_gate'", result.errors)

    def test_composed_event_counter_requires_count_width_from_request(self) -> None:
        request = ProjectRequest(
            task_type="composed_event_counter",
            width=8,
            project_name="event_counter_8bit",
        )
        system_his = _deterministic_system_his(request)
        _set_top_port_width(system_his, "count", 4)

        result = check_system_his_req_fidelity(request, system_his)

        self.assertFalse(result.passed)
        self.assertIn("REQ2HIS fidelity: top.count width must match requested width 8", result.errors)

    def test_composed_dual_stream_join_requires_two_skid_buffer_instances(self) -> None:
        request = ProjectRequest(
            task_type="composed_dual_stream_join",
            width=8,
            project_name="join_8bit",
        )
        system_his = _deterministic_system_his(request)
        first_skid_seen = False
        instances = []
        for instance in system_his["instances"]:
            if instance["component"] == "skid_buffer":
                if first_skid_seen:
                    continue
                first_skid_seen = True
            instances.append(instance)
        system_his["instances"] = instances

        result = check_system_his_req_fidelity(request, system_his)

        self.assertFalse(result.passed)
        self.assertIn(
            "REQ2HIS fidelity: composed_dual_stream_join requires 2 instance(s) of component 'skid_buffer'",
            result.errors,
        )

    def test_unsupported_tasks_are_not_blocked_by_req_fidelity_gate(self) -> None:
        request = ProjectRequest(task_type="counter", width=8, project_name="counter_8bit")
        system_his = _deterministic_system_his(request)

        result = check_system_his_req_fidelity(request, system_his)

        self.assertTrue(result.passed, result.errors)


def _deterministic_system_his(request: ProjectRequest) -> dict[str, object]:
    platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
    project = ProjectGenerator().generate(request, platform)
    return copy.deepcopy(json.loads(project.files["system_his.json"]))


def _set_top_port_width(system_his: dict[str, object], name: str, width: object) -> None:
    top = system_his["top"]
    assert isinstance(top, dict)
    ports = top["ports"]
    assert isinstance(ports, list)
    for port in ports:
        assert isinstance(port, dict)
        if port.get("name") == name:
            port["width"] = width
            return
    raise AssertionError(f"top port {name!r} not found")
