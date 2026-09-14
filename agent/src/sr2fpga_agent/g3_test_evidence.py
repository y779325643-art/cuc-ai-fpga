"""Trusted local pytest recorder for excluded G3 engineering evidence.

The recorder observes actual collection and setup/call/teardown reports. It does
not accept caller-provided scenario verdicts. Artifact stores are snapshotted
before negative tests deliberately corrupt their original fixtures.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from importlib.metadata import version
from pathlib import Path
from typing import Any

from sr2fpga_agent.artifact_store import ArtifactRef, ArtifactStore
from sr2fpga_agent.repository_paths import discover_repository_root


def source_fingerprint(root: Path) -> dict[str, str]:
    """Bind executable evidence to the implementation, tests, and contracts."""
    files = []
    for directory in ("agent/src", "agent/tests", "contracts"):
        for parent, directories, names in os.walk(root / directory):
            directories[:] = [name for name in directories
                              if not name.startswith(".") and name != "__pycache__"]
            files.extend(Path(parent) / name for name in names
                         if Path(name).suffix in {".py", ".json"})
    files.extend(root / path for path in (
        "AGENTS.md", "agent/README.md", "contracts/README.md", "agent/pyproject.toml", "pytest.ini",
        "docs/specs/2026-08-14-sr2fpga-paper1-research-program-design.md",
        "docs/specs/2026-08-18-sr2fpga-paper1-code-architecture-development-spec.md",
    ))
    return {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(files)}


class G3TestEvidenceRecorder:
    """pytest plugin; usable only for local deterministic/fake-client tests."""

    def __init__(self, output_root: Path) -> None:
        self.root = output_root.resolve()
        self.store = ArtifactStore(self.root / "evidence")
        self.repository = discover_repository_root()
        self.sources_before = source_fingerprint(self.repository)
        for path, digest in self.sources_before.items():
            content = (self.repository / path).read_bytes()
            if hashlib.sha256(content).hexdigest() != digest:
                raise ValueError("source changed during G3 checkpoint capture")
            self.store.put_blob(f"source-snapshot/{digest}", content)
        self.collected: list[str] = []
        self.reports: list[dict[str, Any]] = []
        self.artifacts: list[dict[str, Any]] = []
        self._recorded_artifacts: set[tuple] = set()
        self.stores: dict[Path, tuple[str, ArtifactStore]] = {}
        self.current_node = "collection"
        self.original_put_blob = ArtifactStore.put_blob
        self.original_put_validated_json = ArtifactStore.put_validated_json

    def pytest_sessionstart(self, session) -> None:
        recorder = self

        def put_blob(store, key, content, *, media_type="application/octet-stream"):
            ref = recorder.original_put_blob(store, key, content, media_type=media_type)
            recorder._snapshot(store, ref, content)
            return ref

        def put_validated_json(store, key, payload, *, contract_key, registry=None):
            ref = recorder.original_put_validated_json(
                store, key, payload, contract_key=contract_key, registry=registry,
            )
            source = recorder._source(store)
            identity = (recorder.current_node, source[0] if source else None, contract_key, ref)
            if source is not None and identity not in recorder._recorded_artifacts:
                recorder._recorded_artifacts.add(identity)
                recorder.artifacts.append({
                    "node_id": recorder.current_node, "store_id": source[0],
                    "contract_key": contract_key, "artifact_ref": ref.to_dict(),
                })
            return ref

        ArtifactStore.put_blob = put_blob
        ArtifactStore.put_validated_json = put_validated_json

    def pytest_collection_finish(self, session) -> None:
        self.collected = [item.nodeid for item in session.items]
        for item in session.items:
            # Older integration fixtures own a module-level scratch directory.
            # Keep this run's evidence and scratch data together under artifacts/.
            module = getattr(item, "module", None)
            if module is not None and isinstance(getattr(module, "_TEST_ROOT", None), Path):
                module._TEST_ROOT = self.root / "test-work" / module.__name__

    def pytest_runtest_setup(self, item) -> None:
        self.current_node = item.nodeid

    def pytest_runtest_logreport(self, report) -> None:
        self.reports.append({
            "node_id": report.nodeid, "phase": report.when,
            "outcome": report.outcome,
            "was_xfail": bool(getattr(report, "wasxfail", False)),
        })

    def pytest_sessionfinish(self, session, exitstatus) -> None:
        ArtifactStore.put_blob = self.original_put_blob
        ArtifactStore.put_validated_json = self.original_put_validated_json
        sources_after = source_fingerprint(self.repository)
        payload = {
            "contract_version": "g3-test-evidence-v1",
            "evaluation_scope": "excluded_development_conformance_only",
            "collected_node_ids": self.collected,
            "test_reports": self.reports,
            "artifact_records": self.artifacts,
            "source_fingerprints": self.sources_before,
            "runtime_versions": _runtime_versions(),
            "source_unchanged": sources_after == self.sources_before,
            "pytest_exit_status": int(exitstatus),
            "official_outcome": False, "official_authority": False,
            "pass_credit_authority": False, "g4b_authorized": False,
        }
        self.manifest_ref = self.store.put_validated_json(
            "g3/test-evidence", payload, contract_key="g3_test_evidence",
        )

    def _source(self, store: ArtifactStore):
        path = store.root.resolve()
        if path == self.store.root or path.is_relative_to(self.root / "snapshots"):
            return None
        if path not in self.stores:
            store_id = f"store-{len(self.stores):05d}"
            self.stores[path] = (store_id, ArtifactStore(self.root / "snapshots" / store_id))
        return self.stores[path]

    def _snapshot(self, store: ArtifactStore, ref: ArtifactRef, content: bytes) -> None:
        source = self._source(store)
        if source is None:
            return
        _, snapshot = source
        # Preserve the first write-once state when a negative fixture later
        # overwrites physical files behind ArtifactStore's back.
        if snapshot.reference(ref.key) is None:
            self.original_put_blob(snapshot, ref.key, content, media_type=ref.media_type)
        freeze_path = store.root.parent / "measurement_freeze.json"
        if freeze_path.is_file() and snapshot.reference("g3/measurement-freeze") is None:
            self.original_put_blob(snapshot, "g3/measurement-freeze", freeze_path.read_bytes(),
                                   media_type="application/json")


def read_test_evidence(root: Path, reference: ArtifactRef) -> dict[str, Any]:
    from sr2fpga_agent.contract_registry import ContractRegistry

    store = ArtifactStore(root / "evidence")
    payload = json.loads(store.read_verified(reference))
    errors = ContractRegistry().load_schema("g3_test_evidence").validate(payload)
    if errors:
        raise ValueError("invalid G3 test evidence: " + "; ".join(errors))
    if payload["runtime_versions"] != _runtime_versions():
        raise ValueError("G3 test evidence belongs to a different runtime")
    if not payload["source_unchanged"] or payload["source_fingerprints"] != source_fingerprint(
        discover_repository_root()
    ):
        raise ValueError("G3 test evidence belongs to a different source snapshot")
    for digest in set(payload["source_fingerprints"].values()):
        content = store.read_verified(f"source-snapshot/{digest}")
        if hashlib.sha256(content).hexdigest() != digest:
            raise ValueError("G3 archived source checksum mismatch")
    return payload


def _runtime_versions() -> dict[str, str]:
    return {"python": ".".join(map(str, sys.version_info[:3])),
            **{name: version(name) for name in ("pytest", "jsonschema", "PyYAML")}}
