import json
import unittest

from sr2fpga_agent.requirement_envelope import (
    build_requirement_envelope,
    build_request_requirement_envelope,
    route_requirement,
)
from sr2fpga_agent.models import PlatformProfile, ProjectRequest
from sr2fpga_agent.requirement_boundary import evaluate_requirement_boundary


class RequirementEnvelopeTests(unittest.TestCase):
    def test_async_fifo_spellings_cannot_bypass_cdc_boundary(self) -> None:
        for phrase in ("asynchronous FIFO", "async FIFO", "async-FIFO", "异步FIFO"):
            with self.subTest(phrase=phrase):
                decision = evaluate_requirement_boundary(
                    ProjectRequest("fifo", 8, "cdc_probe", f"Generate an 8-bit {phrase} with reset."),
                    PlatformProfile("generic_verilog", "generic", "open_source"),
                )
                self.assertIn("clock_domain_crossing", decision.envelope.capability_labels)
                self.assertEqual(decision.envelope.explicit_facts["cdc_policy"], "async_fifo")
                self.assertEqual(decision.disposition, "capability_gap")

    def test_clarification_answer_is_explicit_and_resolves_only_named_fact(self) -> None:
        envelope = build_requirement_envelope(
            "Build an 8-bit ADC interface.",
            defaults={
                "clock_frequencies_hz": (100_000_000,),
                "reset_polarity": "active_low",
                "target_platform": "generic_verilog",
                "acceptance_criteria": "independent verification",
            },
            clarifications={"adc_interface_contract": "sample_timing"},
        )

        fact = next(item for item in envelope.facts if item.key == "adc_interface_contract")
        self.assertEqual(fact.origin, "explicit")
        self.assertEqual(fact.evidence, ("clarification_answer:adc_interface_contract",))
        self.assertNotIn("adc_interface_contract", envelope.unknown_facts)
        self.assertEqual(envelope.critical_ambiguities, ())

    def test_real_open_requirement_records_fact_provenance_and_capabilities(self) -> None:
        envelope = build_requirement_envelope(
            "设计一个双时钟 ADC 采集系统，16 位数据经 DMA 写入 DDR，再通过 PCIe 上报。",
            defaults={
                "clock_frequencies_hz": (100_000_000,),
                "reset_polarity": "active_low",
                "target_platform": "generic_verilog",
            },
        )

        self.assertEqual(envelope.explicit_facts["data_width_bits"], 16)
        self.assertEqual(envelope.explicit_facts["clock_domain_count"], 2)
        self.assertEqual(envelope.default_facts["reset_polarity"], "active_low")
        self.assertEqual(
            envelope.capability_labels,
            (
                "adc_interface",
                "clock_domain_crossing",
                "dma",
                "external_memory",
                "pcie",
            ),
        )
        self.assertIn("acceptance_criteria", envelope.unknown_facts)
        self.assertIn("cdc_policy", envelope.unknown_facts)
        self.assertIn("dma_transfer_contract", envelope.unknown_facts)
        self.assertIn("memory_access_contract", envelope.unknown_facts)
        self.assertIn("pcie_endpoint_contract", envelope.unknown_facts)

        ambiguity_keys = tuple(item.key for item in envelope.critical_ambiguities)
        self.assertIn("cdc_policy", ambiguity_keys)
        self.assertIn("dma_transfer_contract", ambiguity_keys)
        self.assertIn("memory_access_contract", ambiguity_keys)
        self.assertIn("pcie_endpoint_contract", ambiguity_keys)

    def test_explicit_facts_override_caller_defaults(self) -> None:
        envelope = build_requirement_envelope(
            "Build a 12-bit unsigned block at 80 MHz with an active-high reset.",
            defaults={
                "clock_frequencies_hz": (100_000_000,),
                "data_width_bits": 8,
                "reset_polarity": "active_low",
            },
        )

        self.assertEqual(envelope.explicit_facts["data_width_bits"], 12)
        self.assertEqual(envelope.explicit_facts["clock_frequencies_hz"], (80_000_000,))
        self.assertEqual(envelope.explicit_facts["reset_polarity"], "active_high")
        self.assertEqual(envelope.explicit_facts["numeric_representation"], "unsigned")
        self.assertNotIn("data_width_bits", envelope.default_facts)
        self.assertNotIn("clock_frequencies_hz", envelope.default_facts)
        self.assertNotIn("reset_polarity", envelope.default_facts)

    def test_request_helper_uses_structured_width_and_platform_defaults(self) -> None:
        envelope = build_request_requirement_envelope(
            ProjectRequest(
                task_type="customer_block",
                width=24,
                project_name="customer_block_24bit",
                description="Build a FIFO.",
            ),
            PlatformProfile(
                name="portable_rtl",
                vendor="generic",
                toolchain="open_source",
                clock_hz=75_000_000,
                reset_polarity="active_high",
            ),
        )

        self.assertEqual(envelope.default_facts["data_width_bits"], 24)
        self.assertEqual(envelope.default_facts["clock_frequencies_hz"], (75_000_000,))
        self.assertEqual(envelope.default_facts["reset_polarity"], "active_high")
        self.assertEqual(envelope.default_facts["target_platform"], "portable_rtl")
        self.assertEqual(envelope.default_facts["declared_task_type"], "customer_block")
        self.assertEqual(envelope.explicit_facts["functional_capabilities"], ("fifo",))
        self.assertEqual(
            envelope.default_facts["acceptance_criteria"],
            "independent evaluator must verify every explicit functional and protocol clause",
        )
        self.assertEqual(envelope.critical_ambiguities, ())
        trace = envelope.requirement_trace_template()
        self.assertEqual(trace["requirement_id"], envelope.requirement_id)
        self.assertEqual(trace["required_facts"]["data_width_bits"]["origin"], "default")
        self.assertEqual(
            trace["required_facts"]["functional_capabilities"]["value"],
            ["fifo"],
        )
        self.assertEqual(
            trace["required_facts"]["declared_task_type"]["value"],
            "customer_block",
        )
        self.assertEqual(trace["fact_to_his"]["data_width_bits"], [])
        self.assertEqual(trace["unresolved_facts"], [])
        self.assertNotIn("numeric_representation", trace["required_facts"])

    def test_unclassified_cli_sentinel_is_not_promoted_to_a_requirement_fact(self) -> None:
        envelope = build_request_requirement_envelope(
            ProjectRequest(
                task_type="unclassified",
                width=8,
                project_name="customer_fifo",
                description="Build an 8-bit valid-ready FIFO.",
            ),
            PlatformProfile(
                name="generic_verilog",
                vendor="generic",
                toolchain="open_source",
            ),
        )

        self.assertNotIn("declared_task_type", envelope.default_facts)
        self.assertNotIn(
            "declared_task_type",
            envelope.requirement_trace_template()["required_facts"],
        )

    def test_custom_counter_is_a_mappable_supported_capability(self) -> None:
        envelope = build_request_requirement_envelope(
            ProjectRequest(
                task_type="customer_event_counter",
                width=12,
                project_name="customer_event_counter",
                description="Build a 12-bit event counter.",
            ),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )
        route = route_requirement(
            envelope,
            declared_family="customer_event_counter",
            exact_family_aliases={"counter": "binary_bcd_counter"},
        )

        self.assertEqual(envelope.explicit_facts["functional_capabilities"], ("counter",))
        self.assertEqual(route.strategy, "capability_composition")
        self.assertEqual(route.readiness, "ready")

    def test_explicit_opaque_bus_is_preserved_as_required_protocol(self) -> None:
        envelope = build_request_requirement_envelope(
            ProjectRequest(
                task_type="counter",
                width=8,
                project_name="wishbone_counter",
                description="Build an 8-bit counter with a Wishbone bus.",
            ),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )

        self.assertEqual(envelope.explicit_facts["interface_protocols"], ("wishbone",))
        self.assertEqual(
            envelope.explicit_facts["functional_capabilities"],
            ("counter", "wishbone"),
        )
        self.assertIn("interface_protocols", envelope.requirement_trace_template()["required_facts"])
        self.assertEqual(envelope.critical_ambiguities, ())

    def test_vague_interface_clause_requires_clarification(self) -> None:
        envelope = build_request_requirement_envelope(
            ProjectRequest(
                task_type="counter",
                width=8,
                project_name="host_counter",
                description="Build an 8-bit counter with a host interface.",
            ),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )

        self.assertIn("interface_protocols", envelope.unknown_facts)
        self.assertEqual(
            tuple(item.key for item in envelope.critical_ambiguities),
            ("interface_protocols",),
        )

    def test_requirement_id_includes_declared_task_type_fact(self) -> None:
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
        first = build_request_requirement_envelope(
            ProjectRequest(
                task_type="customer_fifo_a",
                width=8,
                project_name="fifo_a",
                description="Build an 8-bit FIFO.",
            ),
            platform,
        )
        second = build_request_requirement_envelope(
            ProjectRequest(
                task_type="customer_fifo_b",
                width=8,
                project_name="fifo_b",
                description="Build an 8-bit FIFO.",
            ),
            platform,
        )

        self.assertNotEqual(first.requirement_id, second.requirement_id)

    def test_unrecognized_declared_family_is_not_coerced_to_nearest_family(self) -> None:
        envelope = build_requirement_envelope(
            "Stream sensor samples through a configurable filter.",
            defaults={
                "clock_frequencies_hz": (100_000_000,),
                "reset_polarity": "active_low",
                "target_platform": "generic_verilog",
            },
        )

        route = route_requirement(
            envelope,
            declared_family="stream_filter",
            exact_family_aliases={"fir": "fir_filter", "fifo": "sync_fifo"},
        )

        self.assertEqual(route.strategy, "capability_composition")
        self.assertIsNone(route.exact_family)
        self.assertEqual(route.unmatched_declared_family, "stream_filter")

    def test_unknown_family_can_be_ready_when_critical_facts_are_resolved(self) -> None:
        envelope = build_requirement_envelope(
            "Build an 8-bit FIFO.",
            defaults={
                "clock_frequencies_hz": (100_000_000,),
                "reset_polarity": "active_low",
                "target_platform": "generic_verilog",
                "acceptance_criteria": "preserve FIFO ordering without overflow or underflow",
            },
        )

        route = route_requirement(
            envelope,
            declared_family="customer_packet_queue",
            exact_family_aliases={"fifo": "sync_fifo"},
        )

        self.assertEqual(route.strategy, "capability_composition")
        self.assertEqual(route.readiness, "ready")
        self.assertEqual(route.unmatched_declared_family, "customer_packet_queue")
        self.assertEqual(route.critical_ambiguity_keys, ())

    def test_declared_family_uses_only_an_exact_normalized_alias(self) -> None:
        envelope = build_requirement_envelope(
            "16-bit FIR filter",
            defaults={
                "clock_frequencies_hz": (100_000_000,),
                "reset_polarity": "active_low",
                "target_platform": "generic_verilog",
            },
        )

        route = route_requirement(
            envelope,
            declared_family="FIR-filter",
            exact_family_aliases={"fir_filter": "fir_filter", "fifo": "sync_fifo"},
        )

        self.assertEqual(route.strategy, "exact_family")
        self.assertIsNotNone(route.exact_family)
        assert route.exact_family is not None
        self.assertEqual(route.exact_family.family_id, "fir_filter")
        self.assertEqual(route.exact_family.matched_alias, "fir_filter")
        self.assertIsNone(route.unmatched_declared_family)

    def test_exact_family_removes_only_functional_decomposition_ambiguity(self) -> None:
        envelope = build_requirement_envelope(
            "Divide an input clock.",
            defaults={
                "data_width_bits": 8,
                "clock_frequencies_hz": (100_000_000,),
                "reset_polarity": "active_low",
                "target_platform": "generic_verilog",
                "acceptance_criteria": "independent evaluator verifies every explicit clause",
            },
        )

        exact = route_requirement(
            envelope,
            declared_family="clock_divider",
            exact_family_aliases={"clock_divider": "clock_divider"},
        )
        custom = route_requirement(
            envelope,
            declared_family="customer_clock_divider",
            exact_family_aliases={"clock_divider": "clock_divider"},
        )

        self.assertEqual(exact.readiness, "ready")
        self.assertEqual(exact.critical_ambiguity_keys, ())
        self.assertEqual(custom.readiness, "needs_clarification")
        self.assertEqual(custom.critical_ambiguity_keys, ("functional_decomposition",))

    def test_unknown_requirement_enumerates_critical_ambiguities(self) -> None:
        envelope = build_requirement_envelope("Create a sensor fusion engine.")

        self.assertEqual(envelope.capability_labels, ())
        self.assertEqual(
            tuple(item.key for item in envelope.critical_ambiguities),
            (
                "functional_decomposition",
                "data_width_bits",
                "clock_frequencies_hz",
                "reset_polarity",
                "target_platform",
                "acceptance_criteria",
            ),
        )

    def test_output_is_deterministic_and_json_serializable(self) -> None:
        kwargs = {
            "defaults": {
                "target_platform": "generic_verilog",
                "reset_polarity": "active_low",
                "clock_frequencies_hz": (100_000_000,),
            }
        }
        first = build_requirement_envelope("AXI-Stream FIFO with 32-bit data", **kwargs)
        second = build_requirement_envelope("AXI-Stream FIFO with 32-bit data", **kwargs)

        self.assertEqual(first, second)
        self.assertEqual(first.requirement_id, second.requirement_id)
        self.assertEqual(first.to_dict(), second.to_dict())
        json.dumps(first.to_dict(), sort_keys=True)
        prompt_payload = first.to_prompt_payload()
        self.assertEqual(prompt_payload["requirement_id"], first.requirement_id)
        self.assertEqual(prompt_payload["explicit_facts"]["data_width_bits"], 32)
        self.assertEqual(prompt_payload["default_facts"]["reset_polarity"], "active_low")
        json.dumps(prompt_payload, sort_keys=True)

    def test_requirement_id_is_stable_across_default_mapping_order(self) -> None:
        first = build_requirement_envelope(
            "Build an 8-bit FIFO.",
            defaults={"reset_polarity": "active_low", "clock_frequencies_hz": (50_000_000,)},
        )
        second = build_requirement_envelope(
            "Build an 8-bit FIFO.",
            defaults={"clock_frequencies_hz": (50_000_000,), "reset_polarity": "active_low"},
        )
        changed_default = build_requirement_envelope(
            "Build an 8-bit FIFO.",
            defaults={"clock_frequencies_hz": (100_000_000,), "reset_polarity": "active_low"},
        )

        self.assertEqual(first.requirement_id, second.requirement_id)
        self.assertNotEqual(first.requirement_id, changed_default.requirement_id)

    def test_empty_requirement_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "requirement description must not be empty"):
            build_requirement_envelope("  ")

    def test_conflicting_normalized_family_aliases_are_rejected(self) -> None:
        envelope = build_requirement_envelope("Build a FIFO.")

        with self.assertRaisesRegex(ValueError, "conflicting exact family alias"):
            route_requirement(
                envelope,
                declared_family="sync-fifo",
                exact_family_aliases={
                    "sync-fifo": "sync_fifo",
                    "sync_fifo": "another_fifo",
                },
            )


if __name__ == "__main__":
    unittest.main()
