import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_PATH = (
    REPO_ROOT
    / "contracts"
    / "task-catalog"
    / "sr2fpga-task-catalog-v0.2.json"
)
COMPATIBILITY_PATH = REPO_ROOT / "docs" / "sr2fpga-task-catalog-v0.2.json"
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


def test_docs_compatibility_copy_is_byte_identical() -> None:
    assert COMPATIBILITY_PATH.is_file()
    assert CANONICAL_PATH.read_bytes() == COMPATIBILITY_PATH.read_bytes()
