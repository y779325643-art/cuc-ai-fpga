import importlib.util
import json
from pathlib import Path
import subprocess

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
TOOL_PATH = REPO_ROOT / "contracts" / "tools" / "inventory_tracked_tmp.py"
SPEC = importlib.util.spec_from_file_location(
    "inventory_tracked_tmp",
    TOOL_PATH,
)
assert SPEC is not None and SPEC.loader is not None
inventory_tracked_tmp = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(inventory_tracked_tmp)


def _git(root: Path, *arguments: str) -> None:
    subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=True,
        capture_output=True,
    )


def _repository(tmp_path: Path) -> Path:
    _git(tmp_path, "init", "--quiet")
    (tmp_path / "tmp" / "run").mkdir(parents=True)
    (tmp_path / "tmp" / "run" / "summary.json").write_text(
        '{"status":"pass"}\n',
        encoding="utf-8",
    )
    (tmp_path / "tmp" / "scratch.log").write_text(
        "scratch\n",
        encoding="utf-8",
    )
    _git(tmp_path, "add", "--", "tmp")
    return tmp_path


def _classification(root: Path, destination: str) -> Path:
    path = root / "classification.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": (
                    "sr2fpga-legacy-tmp-classification-v1"
                ),
                "moved_to_curated_reports": [
                    {
                        "source_root": "tmp/run",
                        "destination_root": destination,
                        "include_paths": ["summary.json"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


def test_inventory_classifies_only_explicit_curated_files(
    tmp_path: Path,
) -> None:
    root = _repository(tmp_path)
    classification = _classification(
        root,
        "reports/evidence/legacy-runs/run",
    )

    inventory = inventory_tracked_tmp.build_inventory(
        root,
        classification_path=classification,
        external_backup_manifest="manifest.json",
    )

    assert inventory["tracked_path_count"] == 2
    assert inventory["disposition_counts"] == {
        "moved_to_curated_reports": 1,
        "external_backup_only": 1,
    }
    records = {record["path"]: record for record in inventory["records"]}
    assert records["tmp/run/summary.json"]["destination"] == (
        "reports/evidence/legacy-runs/run/summary.json"
    )
    assert records["tmp/scratch.log"]["external_backup_manifest"] == (
        "manifest.json"
    )
    assert all(record["blob_size"] > 0 for record in records.values())
    assert all(record["blob_oid"] for record in records.values())


def test_inventory_rejects_destination_outside_curated_reports(
    tmp_path: Path,
) -> None:
    root = _repository(tmp_path)
    classification = _classification(root, "reports/arbitrary")

    with pytest.raises(
        ValueError,
        match="destination must be a run directory",
    ):
        inventory_tracked_tmp.build_inventory(
            root,
            classification_path=classification,
            external_backup_manifest="manifest.json",
        )


def test_inventory_output_is_deterministic(tmp_path: Path) -> None:
    root = _repository(tmp_path)
    inventory = inventory_tracked_tmp.build_inventory(
        root,
        classification_path=None,
        external_backup_manifest="manifest.json",
    )
    first = root / "first.json"
    second = root / "second.json"

    inventory_tracked_tmp.write_inventory(first, inventory)
    inventory_tracked_tmp.write_inventory(second, inventory)

    assert first.read_bytes() == second.read_bytes()
