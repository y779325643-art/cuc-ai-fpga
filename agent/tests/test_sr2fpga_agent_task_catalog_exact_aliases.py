import re
import unittest

from sr2fpga_agent.task_catalog import (
    ExactTaskFamilyResolution,
    FamilyRecipeDenyPolicy,
    load_exact_task_family_aliases,
    load_family_recipe_deny_policy,
    load_task_family_specs,
    resolve_exact_task_family,
)


class ExactTaskFamilyAliasTests(unittest.TestCase):
    def test_map_includes_family_ids_and_declared_generator_aliases(self) -> None:
        aliases = load_exact_task_family_aliases()

        for spec in load_task_family_specs():
            self.assertEqual(aliases[spec.family_id], spec.family_id)
            for alias in spec.current_generator_aliases:
                self.assertEqual(aliases[alias], spec.family_id)

    def test_candidate_primary_heldout_recipe_deny_policy_is_canonical(self) -> None:
        policy = load_family_recipe_deny_policy()

        self.assertIsInstance(policy, FamilyRecipeDenyPolicy)
        self.assertEqual(policy.policy_id, "sr2fpga-family-recipe-deny")
        self.assertEqual(policy.policy_version, "1.0.0")
        self.assertEqual(policy.catalog_version, "0.2.2")
        self.assertEqual(policy.status, "candidate_g4a_not_signed")
        self.assertEqual(
            policy.recommended_set,
            "paper1_candidate_primary_family_heldout",
        )
        self.assertEqual(
            policy.family_ids,
            (
                "uart_fifo_loopback",
                "stream_fork_join",
                "matched_filter",
                "sobel_threshold",
            ),
        )
        self.assertEqual(policy.deny_reason, "candidate_primary_family_heldout")
        self.assertIsNotNone(re.fullmatch(r"[0-9a-f]{64}", policy.policy_sha256))

    def test_candidate_primary_heldout_set_contains_family_ids_not_topology_aliases(self) -> None:
        policy = load_family_recipe_deny_policy()
        family_ids = {spec.family_id for spec in load_task_family_specs()}

        self.assertTrue(set(policy.family_ids) <= family_ids)
        self.assertNotIn("t4_dual_stream_join", policy.family_ids)

    def test_exact_resolution_accepts_catalog_and_runtime_identifiers(self) -> None:
        topology_alias = resolve_exact_task_family("t4_dual_stream_join")
        runtime_task = resolve_exact_task_family("composed_dual_stream_join")

        self.assertIsInstance(topology_alias, ExactTaskFamilyResolution)
        self.assertEqual(topology_alias.status, "exact")
        self.assertEqual(topology_alias.family_id, "stream_fork_join")
        self.assertEqual(topology_alias.reason, "exact_catalog_alias")
        self.assertEqual(runtime_task.status, "exact")
        self.assertEqual(runtime_task.family_id, "stream_fork_join")
        self.assertEqual(runtime_task.reason, "exact_runtime_task_type")

    def test_exact_resolution_keeps_unknown_identifier_generic(self) -> None:
        resolution = resolve_exact_task_family("customer_packet_engine")

        self.assertEqual(resolution.status, "unknown")
        self.assertIsNone(resolution.family_id)
        self.assertEqual(resolution.reason, "unknown_alias")

    def test_exact_resolution_exposes_catalog_runtime_owner_conflict(self) -> None:
        resolution = resolve_exact_task_family("mac_array")

        self.assertEqual(resolution.status, "conflict")
        self.assertIsNone(resolution.family_id)
        self.assertEqual(resolution.catalog_family_id, "mac_array")
        self.assertEqual(resolution.runtime_family_id, "matrix_vector_mac")
        self.assertEqual(resolution.reason, "conflicting_exact_owners")


if __name__ == "__main__":
    unittest.main()
