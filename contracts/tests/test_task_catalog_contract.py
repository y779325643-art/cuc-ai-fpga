import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_PATH = (
    REPO_ROOT
    / "contracts"
    / "task-catalog"
    / "sr2fpga-task-catalog-v0.2.json"
)
REQUIRED_TASK_FIELDS = {
    "family_id",
    "sr2fpga_tier",
    "system_his_profile",
    "skeleton_level",
    "oracle_kind",
    "target_l_level",
    "mutation_suite",
    "benchmark_role",
}
OFFICIAL_LEVELS = {f"L{level}" for level in range(6)}
L4_OPEN_POLICIES = {
    "none",
    "optional",
    "representative_subset",
    "required_for_flagship",
}


def load_catalog() -> dict:
    return json.loads(CANONICAL_PATH.read_text(encoding="utf-8"))


def test_canonical_task_catalog_exists_and_parses() -> None:
    assert CANONICAL_PATH.is_file()
    catalog = load_catalog()
    assert isinstance(catalog["task_families"], list)
    assert catalog["task_families"]


def test_task_family_ids_are_non_empty_and_unique() -> None:
    family_ids = [task["family_id"] for task in load_catalog()["task_families"]]
    assert all(isinstance(family_id, str) and family_id for family_id in family_ids)
    assert len(family_ids) == len(set(family_ids))


def test_each_task_family_declares_required_metadata() -> None:
    for task in load_catalog()["task_families"]:
        assert REQUIRED_TASK_FIELDS <= set(task), task.get("family_id")
        target = task["target_l_level"]
        assert target["official"] in OFFICIAL_LEVELS, task["family_id"]
        assert target["l4_open_policy"] in L4_OPEN_POLICIES, task["family_id"]


def test_catalog_declares_its_canonical_repository_path() -> None:
    assert load_catalog()["intended_path"] == (
        CANONICAL_PATH.relative_to(REPO_ROOT).as_posix()
    )


def test_historical_heldout_set_is_retained_for_regression() -> None:
    catalog = load_catalog()
    candidate_ids = catalog["recommended_sets"]["legacy_candidate_primary_family_heldout"]
    canonical_ids = {family["family_id"] for family in catalog["task_families"]}

    assert catalog["catalog_version"] == "0.4.0"
    assert candidate_ids == [
        "uart_fifo_loopback",
        "stream_fork_join",
        "matched_filter",
        "sobel_threshold",
    ]
    assert len(candidate_ids) == len(set(candidate_ids))
    assert set(candidate_ids) <= canonical_ids
    assert set(candidate_ids) < set(catalog["recommended_sets"]["legacy_paper1_core"])


def test_family_recipe_policy_is_explicitly_historical() -> None:
    catalog = load_catalog()
    policy = catalog["global_policies"]["family_recipe_selection"]

    assert policy == {
        "policy_id": "sr2fpga-family-recipe-deny",
        "policy_version": "2.0.0",
        "status": "historical_development_only",
        "deny_recommended_set": "legacy_candidate_primary_family_heldout",
        "deny_reason": "historical_family_recipe_restriction",
    }
