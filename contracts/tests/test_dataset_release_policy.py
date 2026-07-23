import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
DATASET_MANIFEST = REPO_ROOT / "datasets" / "manifest.json"
INVENTORY_TOOL = REPO_ROOT / "contracts" / "tools" / "build_dataset_inventory.py"
GIT_ATTRIBUTES = REPO_ROOT / ".gitattributes"
EXPECTED_RELEASE_IDS = {
    "sr2fpga_rtl_v1",
    "sr2fpga_phase_d_control_v1",
    "sr2fpga_phase_d_v1",
}
REQUIRED_RELEASE_FIELDS = {
    "release_id",
    "payload_path",
    "exports_path",
    "checksum_manifest",
    "release_tier",
    "license_status",
    "config_fingerprint",
    "config_fingerprint_status",
}


def load_manifest() -> dict:
    return json.loads(DATASET_MANIFEST.read_text(encoding="utf-8"))


def repository_path(relative_path: str) -> Path:
    posix_path = PurePosixPath(relative_path)
    assert relative_path
    assert not Path(relative_path).is_absolute()
    assert not posix_path.is_absolute()
    assert ".." not in posix_path.parts
    resolved = (REPO_ROOT / relative_path).resolve()
    assert resolved.is_relative_to(REPO_ROOT)
    return resolved


def parse_inventory(path: Path) -> list[tuple[str, str]]:
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        digest, separator, relative_path = line.partition("  ")
        assert separator == "  "
        assert len(digest) == 64
        int(digest, 16)
        records.append((digest, relative_path))
    return records


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def test_dataset_manifest_declares_exact_legacy_releases() -> None:
    manifest = load_manifest()
    assert manifest["dataset_manifest_version"] == "1.0"
    releases = manifest["releases"]
    assert {release["release_id"] for release in releases} == EXPECTED_RELEASE_IDS
    assert len(releases) == len(EXPECTED_RELEASE_IDS)


def test_checksum_manifests_are_pinned_to_lf_in_git() -> None:
    rules = {
        line.strip()
        for line in GIT_ATTRIBUTES.read_text(encoding="utf-8").splitlines()
    }
    assert "*.sha256 text eol=lf" in rules


def test_dataset_release_metadata_and_paths_are_safe() -> None:
    for release in load_manifest()["releases"]:
        assert REQUIRED_RELEASE_FIELDS <= set(release)
        assert release["release_tier"] == "internal_only"
        assert release["license_status"] == "review_required"
        assert release["config_fingerprint"] is None
        assert release["config_fingerprint_status"] == "legacy_unavailable"
        for key in ("payload_path", "exports_path", "checksum_manifest"):
            assert repository_path(release[key]).exists(), (release["release_id"], key)


def test_checksum_manifests_match_deterministic_samples() -> None:
    for release in load_manifest()["releases"]:
        inventory_path = repository_path(release["checksum_manifest"])
        records = parse_inventory(inventory_path)
        assert records
        assert [relative_path for _, relative_path in records] == sorted(
            relative_path for _, relative_path in records
        )
        assert any(
            relative_path.startswith(f'{release["payload_path"]}/')
            for _, relative_path in records
        )
        assert any(
            relative_path.startswith(f'{release["exports_path"]}/')
            for _, relative_path in records
        )
        for index in sorted({0, len(records) // 2, len(records) - 1}):
            expected_digest, relative_path = records[index]
            assert sha256(repository_path(relative_path)) == expected_digest


def test_inventory_tool_writes_sorted_lf_manifest(tmp_path: Path) -> None:
    payload = tmp_path / "datasets" / "demo"
    exports = tmp_path / "datasets" / "demo_exports"
    payload.mkdir(parents=True)
    exports.mkdir(parents=True)
    (payload / "z.txt").write_bytes(b"z")
    (payload / "a.txt").write_bytes(b"a")
    (exports / "middle.bin").write_bytes(b"middle")

    result = subprocess.run(
        [
            sys.executable,
            str(INVENTORY_TOOL),
            "--root",
            str(tmp_path),
            "--release",
            "demo",
        ],
        capture_output=True,
        check=False,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    output_path = tmp_path / "datasets" / "manifests" / "demo.sha256"
    raw = output_path.read_bytes()
    assert b"\r\n" not in raw
    records = parse_inventory(output_path)
    assert [relative_path for _, relative_path in records] == [
        "datasets/demo/a.txt",
        "datasets/demo/z.txt",
        "datasets/demo_exports/middle.bin",
    ]


def test_inventory_tool_rejects_missing_or_unsafe_releases(tmp_path: Path) -> None:
    for release in ("missing", "../escape"):
        result = subprocess.run(
            [
                sys.executable,
                str(INVENTORY_TOOL),
                "--root",
                str(tmp_path),
                "--release",
                release,
            ],
            capture_output=True,
            check=False,
            text=True,
        )
        assert result.returncode != 0
