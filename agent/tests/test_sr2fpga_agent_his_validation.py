import json
import unittest

from sr2fpga_agent import GeneratedProject, PlatformProfile, ProjectGenerator, ProjectRequest
from sr2fpga_agent.his_validation import h_stage_labels, validate_system_his_h_stages


class SystemHisHStageValidationTests(unittest.TestCase):
    def test_h0_rejects_missing_schema_required_field(self) -> None:
        project = _counter_project_with(lambda payload: payload.pop("schema_version"))

        report = validate_system_his_h_stages(_counter_request(), project)

        self.assertEqual(report["h0"]["status"], "fail")
        self.assertEqual(report["h1"]["status"], "not_run")
        self.assertFalse(report["passed"])

    def test_h0_rejects_wrong_top_level_field_type(self) -> None:
        project = _counter_project_with(lambda payload: payload.update({"top": "not-a-mapping"}))

        report = validate_system_his_h_stages(_counter_request(), project)

        self.assertEqual(report["h0"]["status"], "fail")
        self.assertIn("system_his.top must be an object", "\n".join(report["h0"]["diagnostics"]))
        self.assertEqual(report["h1"]["status"], "not_run")

    def test_h0_rejects_nested_schema_field_type_error(self) -> None:
        project = _counter_project_with(lambda payload: payload["top"].update({"ports": "not-a-list"}))

        report = validate_system_his_h_stages(_counter_request(), project)

        self.assertEqual(report["h0"]["status"], "fail")
        self.assertIn("system_his.top.ports must be a list", "\n".join(report["h0"]["diagnostics"]))
        self.assertEqual(report["h1"]["status"], "not_run")

    def test_h0_rejects_nested_schema_list_item_type_error(self) -> None:
        project = _counter_project_with(lambda payload: payload["top"]["ports"].__setitem__(0, "not-an-object"))

        report = validate_system_his_h_stages(_counter_request(), project)

        self.assertEqual(report["h0"]["status"], "fail")
        self.assertIn("system_his.top.ports[0] must be an object", "\n".join(report["h0"]["diagnostics"]))
        self.assertEqual(report["h1"]["status"], "not_run")

    def test_h0_rejects_top_level_list_item_type_error(self) -> None:
        project = _counter_project_with(lambda payload: payload["components"].__setitem__(0, "not-an-object"))

        report = validate_system_his_h_stages(_counter_request(), project)

        self.assertEqual(report["h0"]["status"], "fail")
        self.assertIn("system_his.components[0] must be an object", "\n".join(report["h0"]["diagnostics"]))
        self.assertEqual(report["h1"]["status"], "not_run")

    def test_h1_rejects_unresolved_component_reference(self) -> None:
        def mutate(payload):
            payload["instances"][0]["component"] = "missing_component"

        project = _project_with(
            ProjectRequest(task_type="composed_stream_accumulator", width=8, project_name="stream_accum_8bit"),
            mutate,
        )

        report = validate_system_his_h_stages(_counter_request(), project)

        self.assertEqual(report["h0"]["status"], "pass")
        self.assertEqual(report["h1"]["status"], "fail")
        self.assertEqual(report["h2"]["status"], "not_run")
        self.assertFalse(report["passed"])
        self.assertEqual(report["h1"]["well_formedness_rules"]["W1"]["status"], "fail")

    def test_h1_records_all_well_formedness_rule_statuses(self) -> None:
        report = validate_system_his_h_stages(
            _counter_request(),
            _counter_project_with(lambda payload: None),
        )

        self.assertEqual(
            list(report["h1"]["well_formedness_rules"]),
            [f"W{index}" for index in range(1, 11)],
        )
        self.assertEqual(report["h1"]["well_formedness_rules"]["W1"]["status"], "pass")
        self.assertEqual(report["h1"]["well_formedness_rules"]["W3"]["status"], "not_applicable")

    def test_h2_rejects_unsupported_protocol_and_scenario(self) -> None:
        def mutate(payload):
            payload["data_flow"][0]["protocol"] = "mystery_bus"
            payload["verification"]["scenarios"] = ["unsupported_magic_scenario"]

        project = _counter_project_with(mutate)

        report = validate_system_his_h_stages(_counter_request(), project)

        self.assertEqual(report["h0"]["status"], "pass")
        self.assertEqual(report["h1"]["status"], "pass")
        self.assertEqual(report["h2"]["status"], "fail")
        self.assertIn("unsupported protocol", "\n".join(report["h2"]["diagnostics"]))
        self.assertFalse(report["passed"])

    def test_h2_rejects_declared_protocols_and_scenarios_not_supported_by_current_lowerer(self) -> None:
        def mutate(payload):
            payload["data_flow"][0]["protocol"] = "bram"
            payload["verification"]["scenarios"] = ["random_backpressure"]

        project = _counter_project_with(mutate)

        report = validate_system_his_h_stages(_counter_request(), project)

        self.assertEqual(report["h0"]["status"], "pass")
        self.assertEqual(report["h1"]["status"], "pass")
        self.assertEqual(report["h2"]["status"], "fail")
        diagnostics = "\n".join(report["h2"]["diagnostics"])
        self.assertIn("unsupported protocol 'bram'", diagnostics)
        self.assertIn("unsupported scenario 'random_backpressure'", diagnostics)

    def test_h2_rejects_unsupported_component_semantic_kind(self) -> None:
        project = _counter_project_with(
            lambda payload: payload["components"][0].update({"semantic_kind": "unlowerable_magic_component"})
        )

        report = validate_system_his_h_stages(_counter_request(), project)

        self.assertEqual(report["h0"]["status"], "pass")
        self.assertEqual(report["h1"]["status"], "pass")
        self.assertEqual(report["h2"]["status"], "fail")
        self.assertIn("unsupported semantic_kind", "\n".join(report["h2"]["diagnostics"]))

    def test_h2_accepts_structured_scenario_with_canonical_kind(self) -> None:
        project = _counter_project_with(
            lambda payload: payload["verification"].update(
                {
                    "scenarios": [
                        {
                            "name": "reset_counter_state",
                            "kind": "reset",
                            "description": "Reset the counter before nominal operation.",
                        }
                    ]
                }
            )
        )

        report = validate_system_his_h_stages(_counter_request(), project)

        self.assertEqual(report["h2"]["status"], "pass")

    def test_h2_reports_unknown_structured_scenario_by_identifier(self) -> None:
        project = _counter_project_with(
            lambda payload: payload["verification"].update(
                {
                    "scenarios": [
                        {
                            "name": "unsupported_magic_scenario",
                            "description": "This scenario has no lowering profile.",
                        }
                    ]
                }
            )
        )

        report = validate_system_his_h_stages(_counter_request(), project)

        diagnostics = "\n".join(report["h2"]["diagnostics"])
        self.assertEqual(report["h2"]["status"], "fail")
        self.assertIn("unsupported scenario 'unsupported_magic_scenario'", diagnostics)
        self.assertNotIn("description", diagnostics)

    def test_h2_rejects_structured_scenario_without_identifier(self) -> None:
        project = _counter_project_with(
            lambda payload: payload["verification"].update(
                {"scenarios": [{"description": "Missing canonical kind and name."}]}
            )
        )

        report = validate_system_his_h_stages(_counter_request(), project)

        diagnostics = "\n".join(report["h2"]["diagnostics"])
        self.assertEqual(report["h2"]["status"], "fail")
        self.assertIn("scenario object requires canonical 'kind' or 'name'", diagnostics)

    def test_h2_accepts_reviewed_semantic_kind_and_protocol_aliases(self) -> None:
        fifo_project = _project_with(
            ProjectRequest(task_type="fifo", width=8, project_name="fifo_8bit"),
            lambda payload: payload["components"][0].update({"semantic_kind": "synchronous_fifo"}),
        )
        counter_project = _counter_project_with(
            lambda payload: payload["data_flow"][0].update({"protocol": "combinational"})
        )

        fifo_report = validate_system_his_h_stages(
            ProjectRequest(task_type="fifo", width=8, project_name="fifo_8bit"),
            fifo_project,
        )
        counter_report = validate_system_his_h_stages(_counter_request(), counter_project)

        self.assertEqual(fifo_report["h2"]["status"], "pass")
        self.assertEqual(counter_report["h2"]["status"], "pass")

    def test_h2_keeps_unknown_aliases_fail_closed(self) -> None:
        def mutate(payload):
            payload["components"][0]["semantic_kind"] = "mystery_compute"
            payload["data_flow"][0]["protocol"] = "mystery_transport"

        project = _counter_project_with(mutate)

        report = validate_system_his_h_stages(_counter_request(), project)

        diagnostics = "\n".join(report["h2"]["diagnostics"])
        self.assertEqual(report["h2"]["status"], "fail")
        self.assertIn("unsupported semantic_kind 'mystery_compute'", diagnostics)
        self.assertIn("unsupported protocol 'mystery_transport'", diagnostics)

    def test_h3_rejects_requirement_width_mismatch_after_lowerable_his(self) -> None:
        request = ProjectRequest(
            task_type="counter",
            width=8,
            project_name="counter_8bit",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
        project = ProjectGenerator().generate(
            request,
            platform,
        )
        files = dict(project.files)
        payload = json.loads(files["system_his.json"])
        next(port for port in payload["top"]["ports"] if port["name"] == "count")["width"] = 7
        files["system_his.json"] = json.dumps(payload) + "\n"
        broken = GeneratedProject(project_name=project.project_name, files=files)

        report = validate_system_his_h_stages(
            request,
            broken,
            platform=platform,
        )

        self.assertEqual(report["h0"]["status"], "pass")
        self.assertEqual(report["h1"]["status"], "pass")
        self.assertEqual(report["h2"]["status"], "pass")
        self.assertEqual(report["h3"]["status"], "fail")
        self.assertEqual(report["h3"]["scores"]["interface_extraction"], 0.0)
        self.assertTrue(
            any("data_width_bits" in diagnostic for diagnostic in report["h3"]["diagnostics"])
        )
        self.assertFalse(report["passed"])

    def test_h3_rejects_reset_fidelity_mismatch_after_lowerable_his(self) -> None:
        request = ProjectRequest(
            task_type="composed_stream_accumulator",
            width=8,
            project_name="stream_accum_8bit",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
        project = _project_with(
            request,
            lambda payload: payload["top"]["resets"][0].update({"polarity": "active_high"}),
        )

        report = validate_system_his_h_stages(
            request,
            project,
            platform=platform,
        )

        self.assertEqual(report["h0"]["status"], "pass")
        self.assertEqual(report["h1"]["status"], "pass")
        self.assertEqual(report["h2"]["status"], "pass")
        self.assertEqual(report["h3"]["status"], "fail")
        self.assertEqual(report["h3"]["scores"]["clock_reset_fidelity"], 0.0)

    def test_oracle_fallback_source_removes_generated_his_pass_credit(self) -> None:
        report = validate_system_his_h_stages(
            _counter_request(),
            _counter_project_with(lambda payload: None),
            his_source_used_for_generation="oracle_fallback",
        )

        labels = h_stage_labels(report)

        self.assertEqual(report["his_source_used_for_generation"], "oracle_fallback")
        self.assertFalse(labels["generated_his_pass_credit"])


def _counter_request() -> ProjectRequest:
    return ProjectRequest(task_type="counter", width=8, project_name="counter_8bit")


def _counter_project_with(mutate) -> GeneratedProject:
    return _project_with(_counter_request(), mutate)


def _project_with(request: ProjectRequest, mutate) -> GeneratedProject:
    project = ProjectGenerator().generate(
        request,
        PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
    )
    files = dict(project.files)
    payload = json.loads(files["system_his.json"])
    mutate(payload)
    files["system_his.json"] = json.dumps(payload) + "\n"
    return GeneratedProject(project_name=project.project_name, files=files)


if __name__ == "__main__":
    unittest.main()
