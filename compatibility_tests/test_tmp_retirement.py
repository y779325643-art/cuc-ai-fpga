import json
from pathlib import Path
import re
import subprocess


REPO_ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = (
    REPO_ROOT / "reports" / "reorganization" / "legacy-tmp-inventory.json"
)
ACTIVE_EVIDENCE_PATHS = (
    REPO_ROOT / "README.md",
    REPO_ROOT / "CLAUDE.md",
    REPO_ROOT / "docs" / "README.md",
    REPO_ROOT / "docs" / "current-status.md",
    REPO_ROOT / "docs" / "sr2fpga-task-evidence-v0.1.json",
    REPO_ROOT / "docs" / "sr2fpga-task-evidence-status.md",
)


def test_no_tmp_content_remains_tracked() -> None:
    completed = subprocess.run(
        ["git", "ls-files", "--", "tmp"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )

    assert completed.stdout.splitlines() == []


def test_tmp_is_ignored_and_canonical_configs_do_not_write_there() -> None:
    ignore_lines = (
        REPO_ROOT / ".gitignore"
    ).read_text(encoding="utf-8").splitlines()
    assert "/tmp/" in ignore_lines

    config_paths = (
        list((REPO_ROOT / "agent" / "configs" / "current").glob("*.yaml"))
        + list((REPO_ROOT / "training" / "configs").glob("*.yaml"))
        + list((REPO_ROOT / "training" / "configs").glob("*.example"))
    )
    for path in config_paths:
        assert "tmp/" not in path.read_text(encoding="utf-8"), str(path)


def test_active_evidence_does_not_reference_live_tmp_paths() -> None:
    live_tmp_pattern = re.compile(r"(?<!tracked `)tmp/sr2fpga")

    for path in ACTIVE_EVIDENCE_PATHS:
        source = path.read_text(encoding="utf-8")
        assert live_tmp_pattern.search(source) is None, str(path)


def test_inventory_accounts_for_every_pre_cleanup_path() -> None:
    inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
    records = inventory["records"]

    assert inventory["schema_version"] == "sr2fpga-legacy-tmp-inventory-v1"
    assert inventory["tracked_path_count"] == len(records)
    assert inventory["tracked_path_count"] > 0
    assert inventory["total_blob_bytes"] == sum(
        record["blob_size"] for record in records
    )
    assert [record["path"] for record in records] == sorted(
        record["path"] for record in records
    )
    assert len({record["path"] for record in records}) == len(records)

    allowed = {"moved_to_curated_reports", "external_backup_only"}
    assert {record["disposition"] for record in records} <= allowed

    for record in records:
        if record["disposition"] == "moved_to_curated_reports":
            destination = REPO_ROOT / record["destination"]
            assert record["destination"].startswith(
                "reports/evidence/legacy-runs/"
            )
            assert destination.exists(), destination
        else:
            assert (
                record["external_backup_manifest"]
                == inventory["external_backup_manifest"]
            )
            assert not record["external_backup_manifest"].startswith(
                ("tmp/", "reports/", "artifacts/")
            )
