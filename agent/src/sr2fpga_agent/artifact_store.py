"""Small local write-once authority for CD3 artifacts and events."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

from sr2fpga_agent.contract_registry import ContractRegistry
from sr2fpga_agent.models import GeneratedProject
from sr2fpga_agent.path_safety import validate_project_relative_path
from sr2fpga_agent.project_contract import verify_project_envelope


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_EVENT_ID_RE = re.compile(r"^event-[0-9a-f]{64}$")


class ArtifactConflictError(RuntimeError):
    pass


class ArtifactIntegrityError(RuntimeError):
    pass


class OneShotViolation(RuntimeError):
    pass


class BudgetReservationError(RuntimeError):
    pass


@dataclass(frozen=True)
class ArtifactRef:
    key: str
    sha256: str
    size_bytes: int
    media_type: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ArtifactStore:
    """Filesystem store with immutable keys and content-verified reads."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def put_blob(
        self,
        key: str,
        content: bytes,
        *,
        media_type: str = "application/octet-stream",
    ) -> ArtifactRef:
        normalized = _safe_key(key)
        if not isinstance(content, bytes):
            raise TypeError("artifact content must be bytes")
        digest = hashlib.sha256(content).hexdigest()
        blob_path = self.root / "blobs" / digest[:2] / digest
        blob_path.parent.mkdir(parents=True, exist_ok=True)
        if blob_path.exists():
            if hashlib.sha256(blob_path.read_bytes()).hexdigest() != digest:
                raise ArtifactIntegrityError(f"corrupt blob: {digest}")
        else:
            _write_exclusive(blob_path, content)
        reference = ArtifactRef(normalized, digest, len(content), media_type)
        ref_path = self._ref_path(normalized)
        encoded = _canonical_json(reference.to_dict())
        if ref_path.exists():
            existing = json.loads(ref_path.read_text(encoding="utf-8"))
            if existing != reference.to_dict():
                raise ArtifactConflictError(
                    f"artifact key already names different content: {normalized}"
                )
        else:
            ref_path.parent.mkdir(parents=True, exist_ok=True)
            _write_exclusive(ref_path, encoded)
        return reference

    def put_validated_json(
        self,
        key: str,
        payload: Any,
        *,
        contract_key: str,
        registry: ContractRegistry | None = None,
    ) -> ArtifactRef:
        contract = (registry or ContractRegistry()).load_schema(contract_key)
        errors = contract.validate(payload)
        if errors:
            raise ValueError("invalid registered JSON artifact: " + "; ".join(errors))
        return self.put_blob(
            key,
            _canonical_json(payload),
            media_type="application/json",
        )

    def read_verified(self, key_or_ref: str | ArtifactRef) -> bytes:
        reference = (
            key_or_ref
            if isinstance(key_or_ref, ArtifactRef)
            else self._read_ref(_safe_key(key_or_ref))
        )
        if not _SHA256_RE.fullmatch(reference.sha256):
            raise ArtifactIntegrityError("artifact reference has invalid sha256")
        blob_path = self.root / "blobs" / reference.sha256[:2] / reference.sha256
        if not blob_path.is_file():
            raise ArtifactIntegrityError(f"artifact blob is missing: {reference.key}")
        content = blob_path.read_bytes()
        if len(content) != reference.size_bytes:
            raise ArtifactIntegrityError(f"artifact size mismatch: {reference.key}")
        if hashlib.sha256(content).hexdigest() != reference.sha256:
            raise ArtifactIntegrityError(f"artifact sha256 mismatch: {reference.key}")
        return content

    def reference(self, key: str) -> ArtifactRef | None:
        """Resolve an immutable key without exposing the store layout."""

        normalized = _safe_key(key)
        if not self._ref_path(normalized).is_file():
            return None
        return self._read_ref(normalized)

    def append_event(
        self,
        episode_id: str,
        event_type: str,
        payload: Mapping[str, Any],
    ) -> ArtifactRef:
        episode = _safe_segment(episode_id)
        kind = _safe_segment(event_type)
        event_dir = self.root / "refs" / "events" / episode
        sequence = len(tuple(event_dir.glob("*.json"))) if event_dir.exists() else 0
        event = {
            "event_version": "trusted-core-event-v1",
            "episode_id": episode,
            "sequence": sequence,
            "event_type": kind,
            "payload": dict(payload),
        }
        event["event_id"] = "event-" + hashlib.sha256(
            _canonical_json(event)
        ).hexdigest()
        return self.put_blob(
            f"events/{episode}/{sequence:06d}-{event['event_id']}",
            _canonical_json(event),
            media_type="application/json",
        )

    def event_refs(self, episode_id: str) -> tuple[ArtifactRef, ...]:
        """Return the complete ordered reference stream for one episode."""

        episode = _safe_segment(episode_id)
        event_dir = self.root / "refs" / "events" / episode
        if not event_dir.is_dir():
            return ()
        references = []
        for ref_path in sorted(event_dir.glob("*.ref.json")):
            relative = ref_path.relative_to(self.root / "refs").as_posix()
            key = relative.removesuffix(".ref.json")
            reference = self._read_ref(key)
            if reference.key != key:
                raise ArtifactIntegrityError("event reference key does not match its path")
            references.append(reference)
        return tuple(references)

    def has_event_id(self, event_id: str) -> bool:
        """Return true only for a content-verified append-only event."""

        if not isinstance(event_id, str) or not _EVENT_ID_RE.fullmatch(event_id):
            return False
        event_root = self.root / "refs" / "events"
        if not event_root.is_dir():
            return False
        for ref_path in event_root.rglob(f"*-{event_id}.ref.json"):
            try:
                reference_payload = json.loads(ref_path.read_text(encoding="utf-8"))
                reference = ArtifactRef(
                    key=reference_payload["key"],
                    sha256=reference_payload["sha256"],
                    size_bytes=reference_payload["size_bytes"],
                    media_type=reference_payload["media_type"],
                )
                event = json.loads(self.read_verified(reference))
            except (ArtifactIntegrityError, KeyError, TypeError, ValueError, json.JSONDecodeError):
                return False
            if not isinstance(event, dict) or event.get("event_id") != event_id:
                return False
            canonical_payload = {key: value for key, value in event.items() if key != "event_id"}
            expected_id = "event-" + hashlib.sha256(
                _canonical_json(canonical_payload)
            ).hexdigest()
            if expected_id != event_id or not reference.key.endswith(f"-{event_id}"):
                return False
            return True
        return False

    def seal_candidate(
        self,
        candidate_id: str,
        *,
        project: GeneratedProject,
        project_envelope_ref: ArtifactRef,
        requirement_projection_sha256: str,
        creation_event_ref: ArtifactRef,
        public_evidence_refs: tuple[ArtifactRef, ...] = (),
    ) -> ArtifactRef:
        _require_sha256(requirement_projection_sha256, "requirement projection")
        envelope_bytes = self.read_verified(project_envelope_ref)
        try:
            envelope = json.loads(envelope_bytes)
        except json.JSONDecodeError as exc:
            raise ValueError("project envelope artifact is not valid JSON") from exc
        envelope_contract = ContractRegistry().load_schema("project_envelope")
        envelope_errors = envelope_contract.validate(envelope)
        if envelope_errors:
            raise ValueError(
                "project envelope artifact is invalid: " + "; ".join(envelope_errors)
            )
        project_errors = verify_project_envelope(
            project,
            envelope,
            event_ref_resolver=self.has_event_id,
        )
        if project_errors:
            raise ValueError(
                "project envelope does not match terminal candidate: "
                + "; ".join(project_errors)
            )
        try:
            creation_event = json.loads(self.read_verified(creation_event_ref))
        except json.JSONDecodeError as exc:
            raise ValueError("creation event artifact is not valid JSON") from exc
        creation_event_id = creation_event.get("event_id") if isinstance(creation_event, dict) else None
        if not isinstance(creation_event_id, str) or not self.has_event_id(creation_event_id):
            raise ValueError("creation event is not a trusted append-only event")
        if creation_event.get("episode_id") != envelope.get("episode_id"):
            raise ValueError("creation event and project envelope episode IDs differ")
        for reference in public_evidence_refs:
            self.read_verified(reference)
        candidate = _safe_segment(candidate_id)
        project_file_refs = []
        for path, content in sorted(project.files.items()):
            file_ref = self.put_blob(
                f"candidates/{candidate}/files/{path}",
                content.encode("utf-8"),
                media_type="text/plain; charset=utf-8",
            )
            project_file_refs.append(
                {"path": path, "artifact_key": file_ref.key, "sha256": file_ref.sha256}
            )
        seal = {
            "contract_version": "terminal-candidate-v1",
            "candidate_id": candidate,
            "episode_id": envelope["episode_id"],
            "method_condition_id": envelope["method_condition_id"],
            "project_name": project.project_name,
            "project_envelope_sha256": project_envelope_ref.sha256,
            "requirement_projection_sha256": requirement_projection_sha256,
            "creation_event_id": creation_event_id,
            "project_files": project_file_refs,
            "public_evidence_sha256": [ref.sha256 for ref in public_evidence_refs],
        }
        return self.put_validated_json(
            f"seals/{candidate_id}",
            seal,
            contract_key="terminal_candidate",
        )

    def seal_public_evaluation_candidate(
        self,
        candidate_id: str,
        *,
        attempt_id: str,
        project: GeneratedProject,
        project_envelope_ref: ArtifactRef,
        requirement_projection_sha256: str,
        creation_event_ref: ArtifactRef,
    ) -> ArtifactRef:
        """Freeze one attempt before public evaluation without selecting a terminal."""

        _require_sha256(requirement_projection_sha256, "requirement projection")
        candidate = _safe_segment(candidate_id)
        attempt = _safe_segment(attempt_id)
        try:
            envelope = json.loads(self.read_verified(project_envelope_ref))
        except json.JSONDecodeError as exc:
            raise ValueError("project envelope artifact is not valid JSON") from exc
        envelope_errors = ContractRegistry().load_schema("project_envelope").validate(
            envelope
        )
        if envelope_errors:
            raise ValueError(
                "project envelope artifact is invalid: " + "; ".join(envelope_errors)
            )
        project_errors = verify_project_envelope(
            project,
            envelope,
            event_ref_resolver=self.has_event_id,
        )
        if project_errors:
            raise ValueError(
                "project envelope does not match public-evaluation candidate: "
                + "; ".join(project_errors)
            )
        try:
            creation_event = json.loads(self.read_verified(creation_event_ref))
        except json.JSONDecodeError as exc:
            raise ValueError("creation event artifact is not valid JSON") from exc
        creation_event_id = (
            creation_event.get("event_id") if isinstance(creation_event, dict) else None
        )
        if not isinstance(creation_event_id, str) or not self.has_event_id(
            creation_event_id
        ):
            raise ValueError("creation event is not a trusted append-only event")
        if creation_event.get("episode_id") != envelope.get("episode_id"):
            raise ValueError("creation event and project envelope episode IDs differ")
        event_payload = creation_event.get("payload")
        if not isinstance(event_payload, dict):
            raise ValueError("creation event payload is invalid")
        expected_identity = {
            "candidate_id": candidate,
            "attempt_id": attempt,
            "method_condition_id": envelope["method_condition_id"],
        }
        for field, expected in expected_identity.items():
            if event_payload.get(field) != expected:
                raise ValueError(f"creation event {field} does not match candidate")

        project_file_refs = []
        for path, content in sorted(project.files.items()):
            file_ref = self.put_blob(
                f"public-evaluation-candidates/{candidate}/files/{path}",
                content.encode("utf-8"),
                media_type="text/plain; charset=utf-8",
            )
            project_file_refs.append(
                {"path": path, "artifact_key": file_ref.key, "sha256": file_ref.sha256}
            )
        seal = {
            "contract_version": "public-evaluation-candidate-v1",
            "candidate_id": candidate,
            "episode_id": envelope["episode_id"],
            "attempt_id": attempt,
            "method_condition_id": envelope["method_condition_id"],
            "seal_stage": "pre_public_evaluation",
            "terminal_status": "unselected_at_seal",
            "pass_credit_authority": False,
            "project_name": project.project_name,
            "project_envelope_ref": _artifact_ref_payload(project_envelope_ref),
            "requirement_projection_sha256": requirement_projection_sha256,
            "creation_event_ref": {
                **_artifact_ref_payload(creation_event_ref),
                "event_id": creation_event_id,
            },
            "project_files": project_file_refs,
        }
        return self.put_validated_json(
            f"public-evaluation-candidate-seals/{candidate}",
            seal,
            contract_key="public_evaluation_candidate",
        )

    def seal_unverified_public_evaluation_candidate(
        self,
        candidate_id: str,
        *,
        episode_id: str,
        attempt_id: str,
        method_condition_id: str,
        project: GeneratedProject,
        project_envelope_reason: str,
        requirement_projection_sha256: str,
        creation_event_ref: ArtifactRef,
    ) -> ArtifactRef:
        """Freeze an L0-invalid attempt for public diagnosis, never terminal credit."""

        _require_sha256(requirement_projection_sha256, "requirement projection")
        candidate = _safe_segment(candidate_id)
        episode = _safe_segment(episode_id)
        attempt = _safe_segment(attempt_id)
        method = _safe_segment(method_condition_id)
        if method not in {"M0", "M1", "M2", "M3", "M4", "M5"}:
            raise ValueError("unknown method condition")
        if not isinstance(project_envelope_reason, str) or not project_envelope_reason:
            raise ValueError("project envelope reason must be non-empty")
        if not project.files:
            raise ValueError("public-evaluation candidate must contain project files")
        try:
            creation_event = json.loads(self.read_verified(creation_event_ref))
        except json.JSONDecodeError as exc:
            raise ValueError("creation event artifact is not valid JSON") from exc
        creation_event_id = (
            creation_event.get("event_id") if isinstance(creation_event, dict) else None
        )
        if not isinstance(creation_event_id, str) or not self.has_event_id(
            creation_event_id
        ):
            raise ValueError("creation event is not a trusted append-only event")
        if creation_event.get("episode_id") != episode:
            raise ValueError("creation event and candidate episode IDs differ")
        event_payload = creation_event.get("payload")
        expected_identity = {
            "candidate_id": candidate,
            "attempt_id": attempt,
            "method_condition_id": method,
        }
        if not isinstance(event_payload, dict):
            raise ValueError("creation event payload is invalid")
        for field, expected in expected_identity.items():
            if event_payload.get(field) != expected:
                raise ValueError(f"creation event {field} does not match candidate")
        project_file_refs = []
        for raw_path, content in sorted(project.files.items()):
            path = validate_project_relative_path(raw_path)
            if not isinstance(content, str):
                raise TypeError("generated project content must be text")
            file_ref = self.put_blob(
                f"public-evaluation-candidates-v2/{candidate}/files/{path}",
                content.encode("utf-8"),
                media_type="text/plain; charset=utf-8",
            )
            project_file_refs.append(
                {"path": path, "artifact_key": file_ref.key, "sha256": file_ref.sha256}
            )
        seal = {
            "contract_version": "public-evaluation-candidate-v2",
            "candidate_id": candidate,
            "episode_id": episode,
            "attempt_id": attempt,
            "method_condition_id": method,
            "seal_stage": "pre_public_evaluation",
            "terminal_status": "unselected_at_seal",
            "pass_credit_authority": False,
            "project_name": _safe_segment(project.project_name),
            "project_envelope_ref": None,
            "project_envelope_status": "unavailable",
            "project_envelope_reason": project_envelope_reason,
            "requirement_projection_sha256": requirement_projection_sha256,
            "creation_event_ref": {
                **_artifact_ref_payload(creation_event_ref),
                "event_id": creation_event_id,
            },
            "project_files": project_file_refs,
        }
        return self.put_validated_json(
            f"public-evaluation-candidate-seals-v2/{candidate}",
            seal,
            contract_key="public_evaluation_candidate_v2",
        )

    def read_public_evaluation_candidate(
        self, seal_ref: str | ArtifactRef
    ) -> GeneratedProject:
        """Reconstruct and verify a pre-public-evaluation attempt snapshot."""

        try:
            seal = json.loads(self.read_verified(seal_ref))
        except json.JSONDecodeError as exc:
            raise ArtifactIntegrityError(
                "public-evaluation candidate seal is not valid JSON"
            ) from exc
        version = seal.get("contract_version") if isinstance(seal, dict) else None
        if version not in {
            "public-evaluation-candidate-v1",
            "public-evaluation-candidate-v2",
        }:
            raise ArtifactIntegrityError(
                "public-evaluation candidate seal has an unsupported shape"
            )
        contract_errors = ContractRegistry().load_schema(
            (
                "public_evaluation_candidate"
                if version == "public-evaluation-candidate-v1"
                else "public_evaluation_candidate_v2"
            )
        ).validate(seal)
        if contract_errors:
            raise ArtifactIntegrityError(
                "public-evaluation candidate seal contract mismatch: "
                + "; ".join(contract_errors)
            )
        reference_fields = ["creation_event_ref"]
        if seal.get("project_envelope_ref") is not None:
            reference_fields.append("project_envelope_ref")
        for field in reference_fields:
            payload = seal[field]
            reference = ArtifactRef(
                key=payload["artifact_key"],
                sha256=payload["sha256"],
                size_bytes=payload["size_bytes"],
                media_type=payload["media_type"],
            )
            self.read_verified(reference)
        if not self.has_event_id(seal["creation_event_ref"]["event_id"]):
            raise ArtifactIntegrityError("creation event is no longer trusted")

        files: dict[str, str] = {}
        for record in seal["project_files"]:
            try:
                path = validate_project_relative_path(record["path"])
            except (KeyError, TypeError, ValueError) as exc:
                raise ArtifactIntegrityError(
                    "public-evaluation candidate file path is invalid"
                ) from exc
            if path in files:
                raise ArtifactIntegrityError(
                    "public-evaluation candidate contains duplicate file paths"
                )
            content = self.read_verified(record["artifact_key"])
            if record["sha256"] != hashlib.sha256(content).hexdigest():
                raise ArtifactIntegrityError(
                    "public-evaluation candidate file digest mismatch"
                )
            try:
                files[path] = content.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise ArtifactIntegrityError(
                    "public-evaluation candidate file is not UTF-8"
                ) from exc
        return GeneratedProject(seal["project_name"], files)

    def read_sealed_project(self, seal_ref: str | ArtifactRef) -> GeneratedProject:
        """Reconstruct an immutable terminal project from verified store blobs."""

        try:
            seal = json.loads(self.read_verified(seal_ref))
        except json.JSONDecodeError as exc:
            raise ArtifactIntegrityError("candidate seal is not valid JSON") from exc
        if not isinstance(seal, dict) or seal.get("contract_version") != "terminal-candidate-v1":
            raise ArtifactIntegrityError("candidate seal has an unsupported shape")
        contract_errors = ContractRegistry().load_schema("terminal_candidate").validate(seal)
        if contract_errors:
            raise ArtifactIntegrityError(
                "candidate seal contract mismatch: " + "; ".join(contract_errors)
            )
        project_name = seal.get("project_name")
        if not isinstance(project_name, str) or not project_name:
            raise ArtifactIntegrityError("candidate seal has no project name")
        records = seal.get("project_files")
        if not isinstance(records, list) or not records:
            raise ArtifactIntegrityError("candidate seal has no project files")
        files: dict[str, str] = {}
        for record in records:
            if not isinstance(record, dict):
                raise ArtifactIntegrityError("candidate seal file record is invalid")
            try:
                path = validate_project_relative_path(record.get("path"))
            except (TypeError, ValueError) as exc:
                raise ArtifactIntegrityError("candidate seal file path is invalid") from exc
            if path in files:
                raise ArtifactIntegrityError("candidate seal contains duplicate file paths")
            artifact_key = record.get("artifact_key")
            if not isinstance(artifact_key, str):
                raise ArtifactIntegrityError("candidate seal file has no artifact key")
            content = self.read_verified(artifact_key)
            if record.get("sha256") != hashlib.sha256(content).hexdigest():
                raise ArtifactIntegrityError("candidate seal file digest mismatch")
            try:
                files[path] = content.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise ArtifactIntegrityError("candidate project file is not UTF-8") from exc
        return GeneratedProject(project_name, files)

    def consume_once(self, operation_id: str, subject_sha256: str) -> ArtifactRef:
        operation = _safe_segment(operation_id)
        _require_sha256(subject_sha256, "one-shot subject")
        key = f"one-shot/{operation}"
        if self._ref_path(key).exists():
            raise OneShotViolation(f"one-shot operation already consumed: {operation}")
        return self.put_blob(
            key,
            _canonical_json(
                {
                    "one_shot_version": "one-shot-v1",
                    "operation_id": operation,
                    "subject_sha256": subject_sha256,
                }
            ),
            media_type="application/json",
        )

    def _read_ref(self, key: str) -> ArtifactRef:
        path = self._ref_path(key)
        if not path.is_file():
            raise KeyError(f"unknown artifact key: {key}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        return ArtifactRef(
            key=payload["key"],
            sha256=payload["sha256"],
            size_bytes=payload["size_bytes"],
            media_type=payload["media_type"],
        )

    def _ref_path(self, key: str) -> Path:
        parts = list(PurePosixPath(key).parts)
        parts[-1] += ".ref.json"
        return self.root / "refs" / Path(*parts)


class EpisodeBudgetLedger:
    """Minimal append-only reservation ledger; full reconciliation is CD6."""

    def __init__(
        self,
        store: ArtifactStore,
        episode_id: str,
        limits: Mapping[str, int],
    ) -> None:
        self.store = store
        self.episode_id = _safe_segment(episode_id)
        self.limits = dict(limits)
        if not self.limits or any(value < 0 for value in self.limits.values()):
            raise ValueError("budget limits must be non-empty and non-negative")
        self._used = {axis: 0 for axis in self.limits}

    def reserve(self, axis: str, amount: int = 1) -> ArtifactRef:
        if axis not in self.limits:
            raise KeyError(f"unknown budget axis: {axis}")
        if amount <= 0:
            raise ValueError("budget reservation amount must be positive")
        used_after = self._used[axis] + amount
        if used_after > self.limits[axis]:
            raise BudgetReservationError(
                f"budget exhausted for {axis}: {used_after}>{self.limits[axis]}"
            )
        event = self.store.append_event(
            self.episode_id,
            "budget_reserved",
            {
                "axis": axis,
                "amount": amount,
                "used_after": used_after,
                "limit": self.limits[axis],
            },
        )
        self._used[axis] = used_after
        return event

    def summary(self) -> dict[str, Any]:
        return {
            axis: {
                "limit": limit,
                "used": self._used[axis],
                "remaining": limit - self._used[axis],
            }
            for axis, limit in self.limits.items()
        }


def _safe_key(value: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError("artifact key must be non-empty")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or any(not part for part in path.parts):
        raise ValueError(f"unsafe artifact key: {value!r}")
    for part in path.parts:
        _safe_segment(part)
    return path.as_posix()


def _safe_segment(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]*", value):
        raise ValueError(f"unsafe artifact identifier: {value!r}")
    return value


def _require_sha256(value: str, label: str) -> None:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise ValueError(f"{label} must be lowercase SHA-256")


def _artifact_ref_payload(reference: ArtifactRef) -> dict[str, Any]:
    return {
        "artifact_key": reference.key,
        "sha256": reference.sha256,
        "size_bytes": reference.size_bytes,
        "media_type": reference.media_type,
    }


def _canonical_json(payload: Any) -> bytes:
    return (
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _write_exclusive(path: Path, content: bytes) -> None:
    try:
        with path.open("xb") as handle:
            handle.write(content)
    except FileExistsError as exc:
        raise ArtifactConflictError(f"write-once path already exists: {path}") from exc
