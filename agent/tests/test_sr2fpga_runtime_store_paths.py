"""Portable store identities cannot acquire Windows drive or device semantics."""
import pytest

from sr2fpga_agent.artifact_store import ArtifactStore


@pytest.mark.parametrize("key", ["C:escape", "D:escape", "scope/item:stream", "CON", "aux.txt",
                                  "scope/COM1", "scope/LPT9.log", "scope/end.", "../escape"])
def test_store_rejects_unsafe_keys_before_external_write(tmp_path, key):
    store = ArtifactStore(tmp_path / "store")
    with pytest.raises(ValueError):
        store.put_blob(key, b"untrusted")
    assert not list(tmp_path.rglob("*.ref.json"))


def test_reference_path_is_contained(tmp_path):
    store = ArtifactStore(tmp_path / "store")
    ref = store.put_blob("safe/record-1", b"source")
    assert store.read_verified(ref) == b"source"
    assert store._ref_path(ref.key).is_relative_to((store.root / "refs").resolve())


def test_symlink_escape_is_rejected_when_os_allows_probe(tmp_path):
    store = ArtifactStore(tmp_path / "store")
    (store.root / "refs").mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    link = store.root / "refs" / "link"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("OS does not permit creating this synthetic symlink probe")
    with pytest.raises(ValueError, match="escapes"):
        store.put_blob("link/escape", b"source")
    assert not list(outside.iterdir())
