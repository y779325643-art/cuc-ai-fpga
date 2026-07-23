import json
from pathlib import Path, PurePosixPath


REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / "contracts" / "manifest.json"


def load_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def test_contract_manifest_declares_required_contracts() -> None:
    manifest = load_manifest()
    assert manifest["contract_registry_version"] == "1.0"
    assert set(manifest["contracts"]) == {
        "system_his",
        "trajectory",
        "training_view_row",
        "task_catalog",
    }


def test_registered_contract_paths_are_repository_relative() -> None:
    for record in load_manifest()["contracts"].values():
        path = record["path"]
        posix_path = PurePosixPath(path)
        assert path
        assert not Path(path).is_absolute()
        assert not posix_path.is_absolute()
        assert ".." not in posix_path.parts
        assert (REPO_ROOT / path).resolve().is_relative_to(REPO_ROOT)


def test_all_registered_contracts_exist() -> None:
    for name, record in load_manifest()["contracts"].items():
        assert (REPO_ROOT / record["path"]).is_file(), name
