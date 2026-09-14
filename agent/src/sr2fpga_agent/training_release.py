"""CD8 candidate training-release builder and read-only integrity verifier."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import shutil
from typing import Any, Mapping, Sequence
import uuid

from sr2fpga_agent.models import sha256_json as _sha256_json
from sr2fpga_agent.contract_registry import ContractRegistry
from sr2fpga_agent.repository_paths import RepositoryPaths
from sr2fpga_agent.training_pool import (
    TREATMENTS,
    TrainingViewExport,
    validate_training_pool_exports,
    validate_training_pool_manifest,
)


MANIFEST_FILENAME = "training-release-manifest.json"
POOL_PATH = "internal/training-pool-manifest.json"
_LEAKAGE_POLICY_VERSION = "training-view-leakage-v1"


@dataclass(frozen=True)
class ReleaseLeakagePolicy:
    policy_id: str
    policy_sha256: str
    forbidden_canaries: tuple[str, ...]
    forbidden_canary_set_sha256: str

    @classmethod
    def create(
        cls, *, policy_id: str, forbidden_canaries: Sequence[str] = ()
    ) -> "ReleaseLeakagePolicy":
        if not policy_id:
            raise ValueError("release leakage policy_id must be non-empty")
        canaries = tuple(sorted(set(forbidden_canaries)))
        if any(not isinstance(canary, str) or not canary for canary in canaries):
            raise ValueError("release leakage canaries must be non-empty strings")
        canary_set_sha256 = _sha256_json(canaries)
        policy_sha256 = _sha256_json(
            {
                "policy_version": _LEAKAGE_POLICY_VERSION,
                "policy_id": policy_id,
                "forbidden_canary_set_sha256": canary_set_sha256,
            }
        )
        return cls(policy_id, policy_sha256, canaries, canary_set_sha256)


def build_candidate_training_release(
    output_root: Path | str,
    *,
    pool_manifest: dict[str, Any],
    exports: Mapping[str, Sequence[TrainingViewExport]],
    leakage_policy: ReleaseLeakagePolicy,
    paths: RepositoryPaths | None = None,
) -> Path:
    """Create one immutable, unpromoted candidate release under artifacts/."""

    _validate_leakage_policy(leakage_policy)
    validate_training_pool_exports(
        pool_manifest,
        exports,
        forbidden_canaries=leakage_policy.forbidden_canaries,
    )
    files, treatments = _candidate_files(pool_manifest, exports)
    inventory = _file_inventory(files)
    identity = _release_identity(
        pool_manifest_sha256=pool_manifest["artifact_sha256"],
        leakage_policy_sha256=leakage_policy.policy_sha256,
        release_files=inventory,
    )
    without_hash = {
        "contract_version": "training-release-manifest-v1",
        "visibility_class": "public",
        "release_id": f"release-{_sha256_json(identity)}",
        "release_state": "candidate_unpromoted",
        "training_authorized": False,
        "pool_id": pool_manifest["pool_id"],
        "pool_manifest_path": POOL_PATH,
        "pool_manifest_sha256": pool_manifest["artifact_sha256"],
        "training_split_id": pool_manifest["training_split_id"],
        "e_final_set_sha256": pool_manifest["e_final_set_sha256"],
        "e_traj_set_sha256": pool_manifest["e_traj_set_sha256"],
        "official_hidden_outcome_reference_count": 0,
        "leakage_audit": {
            "policy_id": leakage_policy.policy_id,
            "policy_sha256": leakage_policy.policy_sha256,
            "forbidden_canary_set_sha256": (
                leakage_policy.forbidden_canary_set_sha256
            ),
            "status": "pass",
        },
        "treatments": treatments,
        "release_files": inventory,
    }
    manifest = {**without_hash, "artifact_sha256": _sha256_json(without_hash)}
    validate_training_release_manifest(manifest)

    repository_paths = paths or RepositoryPaths.discover()
    artifacts_root = repository_paths.artifacts_dir.resolve()
    resolved_output = Path(output_root).resolve()
    if resolved_output != artifacts_root and artifacts_root not in resolved_output.parents:
        raise ValueError("candidate training releases may be written only under artifacts/")
    final_release = resolved_output / manifest["release_id"]
    if final_release.exists():
        raise FileExistsError(f"candidate training release already exists: {final_release}")
    resolved_output.mkdir(parents=True, exist_ok=True)
    staging = resolved_output / f".staging-{manifest['release_id']}-{uuid.uuid4().hex}"
    staging.mkdir()
    try:
        for relative_path, content in sorted(files.items()):
            target = staging / Path(*relative_path.split("/"))
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        _write_json(staging / MANIFEST_FILENAME, manifest)
        staging.rename(final_release)
    except BaseException:
        if staging.exists():
            shutil.rmtree(staging)
        raise
    return final_release


def verify_candidate_training_release(
    release_root: Path | str,
    *,
    leakage_policy: ReleaseLeakagePolicy,
    paths: RepositoryPaths | None = None,
) -> dict[str, Any]:
    """Verify a complete candidate release without mutating it or authorizing training."""

    _validate_leakage_policy(leakage_policy)
    repository_paths = paths or RepositoryPaths.discover()
    artifacts_root = repository_paths.artifacts_dir.resolve()
    root = Path(release_root).resolve()
    if root != artifacts_root and artifacts_root not in root.parents:
        raise ValueError("candidate training release must be under artifacts/")
    manifest = _load_object(root / MANIFEST_FILENAME)
    validate_training_release_manifest(manifest)
    if manifest["release_state"] != "candidate_unpromoted":
        raise ValueError("candidate verifier rejects promoted releases")
    if manifest["training_authorized"] is not False:
        raise ValueError("candidate release must not authorize training")
    expected_audit = {
        "policy_id": leakage_policy.policy_id,
        "policy_sha256": leakage_policy.policy_sha256,
        "forbidden_canary_set_sha256": leakage_policy.forbidden_canary_set_sha256,
        "status": "pass",
    }
    if manifest["leakage_audit"] != expected_audit:
        raise ValueError("candidate release leakage policy mismatch")
    inventory = {record["path"]: record for record in manifest["release_files"]}
    actual_paths = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and path != root / MANIFEST_FILENAME
    }
    if actual_paths != set(inventory):
        raise ValueError("candidate release file inventory mismatch")
    for relative_path, record in inventory.items():
        content = (root / Path(*relative_path.split("/"))).read_bytes()
        if len(content) != record["size_bytes"]:
            raise ValueError(f"candidate release size mismatch: {relative_path}")
        if _sha256_bytes(content) != record["sha256"]:
            raise ValueError(f"candidate release checksum mismatch: {relative_path}")
        _validate_file_record_semantics(record)

    if manifest["pool_manifest_path"] != POOL_PATH:
        raise ValueError("candidate release pool manifest path is not canonical")
    pool_manifest = _load_object(root / Path(*POOL_PATH.split("/")))
    validate_training_pool_manifest(pool_manifest)
    if pool_manifest["artifact_sha256"] != manifest["pool_manifest_sha256"]:
        raise ValueError("candidate release pool manifest hash mismatch")
    pool_bindings = (
        (manifest["pool_id"], pool_manifest["pool_id"], "pool_id"),
        (
            manifest["training_split_id"],
            pool_manifest["training_split_id"],
            "training split",
        ),
        (
            manifest["e_final_set_sha256"],
            pool_manifest["e_final_set_sha256"],
            "E_final set",
        ),
        (
            manifest["e_traj_set_sha256"],
            pool_manifest["e_traj_set_sha256"],
            "E_traj set",
        ),
    )
    for actual, expected, label in pool_bindings:
        if actual != expected:
            raise ValueError(f"candidate release pool binding mismatch: {label}")

    exports, referenced_paths = _load_release_exports(root, manifest, pool_manifest)
    if referenced_paths != set(inventory):
        raise ValueError("candidate release contains unreferenced internal artifacts")
    validate_training_pool_exports(
        pool_manifest,
        exports,
        forbidden_canaries=leakage_policy.forbidden_canaries,
    )
    _validate_treatment_summaries(manifest, pool_manifest, exports)
    return manifest


def validate_training_release_manifest(manifest: dict[str, Any]) -> None:
    errors = ContractRegistry().load_schema("training_release_manifest").validate(manifest)
    if errors:
        raise ValueError("invalid training release manifest: " + "; ".join(errors))
    expected_artifact = _sha256_json(
        {key: value for key, value in manifest.items() if key != "artifact_sha256"}
    )
    if manifest["artifact_sha256"] != expected_artifact:
        raise ValueError("training release manifest artifact_sha256 mismatch")
    paths = [record["path"] for record in manifest["release_files"]]
    if paths != sorted(paths) or len(paths) != len(set(paths)):
        raise ValueError("training release file inventory is not canonical")
    treatments = [record["treatment"] for record in manifest["treatments"]]
    if treatments != list(TREATMENTS):
        raise ValueError("training release treatment summaries are not canonical")
    expected_release_id = "release-" + _sha256_json(
        _release_identity(
            pool_manifest_sha256=manifest["pool_manifest_sha256"],
            leakage_policy_sha256=manifest["leakage_audit"]["policy_sha256"],
            release_files=manifest["release_files"],
        )
    )
    if manifest["release_id"] != expected_release_id:
        raise ValueError("training release release_id is not canonical")


def _candidate_files(
    pool_manifest: dict[str, Any],
    exports: Mapping[str, Sequence[TrainingViewExport]],
) -> tuple[dict[str, bytes], list[dict[str, Any]]]:
    files = {POOL_PATH: _json_bytes(pool_manifest)}
    treatments: list[dict[str, Any]] = []
    for treatment in TREATMENTS:
        ordered = sorted(exports[treatment], key=lambda export: export[0]["source_episode_id"])
        rows = [export[0] for export in ordered]
        view_path = f"views/{treatment}.jsonl"
        view_bytes = b"".join(_compact_json_bytes(row) + b"\n" for row in rows)
        files[view_path] = view_bytes
        treatments.append(
            {
                "treatment": treatment,
                "view_path": view_path,
                "view_sha256": _sha256_bytes(view_bytes),
                "row_count": len(rows),
                "episode_set_sha256": _sha256_json(
                    sorted(row["source_episode_id"] for row in rows)
                ),
                "row_set_sha256": _sha256_json(
                    sorted(row["row_sha256"] for row in rows)
                ),
            }
        )
        for row, sidecar, certificate in ordered:
            sidecar_path = f"internal/sidecars/{row['row_id']}.json"
            _add_unique(files, sidecar_path, _json_bytes(sidecar))
            certificate_path = (
                "internal/eligibility/"
                f"{certificate['artifact_sha256']}.json"
            )
            _add_unique(files, certificate_path, _json_bytes(certificate))
    return files, treatments


def _file_inventory(files: Mapping[str, bytes]) -> list[dict[str, Any]]:
    return [
        {
            "path": path,
            "sha256": _sha256_bytes(content),
            "size_bytes": len(content),
            "role": _file_role(path),
            "visibility_class": (
                "model_visible" if path.startswith("views/") else "release_internal"
            ),
        }
        for path, content in sorted(files.items())
    ]


def _load_release_exports(
    root: Path,
    manifest: dict[str, Any],
    pool_manifest: dict[str, Any],
) -> tuple[dict[str, list[TrainingViewExport]], set[str]]:
    exports: dict[str, list[TrainingViewExport]] = {treatment: [] for treatment in TREATMENTS}
    referenced = {POOL_PATH}
    refs_by_treatment = {
        treatment: {
            ref["row_id"]: ref
            for ref in pool_manifest["treatment_rows"][treatment]
        }
        for treatment in TREATMENTS
    }
    summaries = {record["treatment"]: record for record in manifest["treatments"]}
    for treatment in TREATMENTS:
        view_path = summaries[treatment]["view_path"]
        referenced.add(view_path)
        rows = _load_jsonl(root / Path(*view_path.split("/")))
        for row in rows:
            ref = refs_by_treatment[treatment].get(row.get("row_id"))
            if ref is None:
                raise ValueError(f"candidate release has unregistered {treatment} row")
            sidecar_path = f"internal/sidecars/{row['row_id']}.json"
            certificate_path = (
                "internal/eligibility/"
                f"{ref['eligibility_artifact_sha256']}.json"
            )
            sidecar = _load_object(root / Path(*sidecar_path.split("/")))
            certificate = _load_object(root / Path(*certificate_path.split("/")))
            referenced.update((sidecar_path, certificate_path))
            exports[treatment].append((row, sidecar, certificate))
    return exports, referenced


def _validate_treatment_summaries(
    manifest: dict[str, Any],
    pool_manifest: dict[str, Any],
    exports: Mapping[str, Sequence[TrainingViewExport]],
) -> None:
    summaries = {record["treatment"]: record for record in manifest["treatments"]}
    for treatment in TREATMENTS:
        rows = [export[0] for export in exports[treatment]]
        summary = summaries[treatment]
        expected_path = f"views/{treatment}.jsonl"
        if summary["view_path"] != expected_path:
            raise ValueError(f"candidate release {treatment} view path is not canonical")
        if summary["row_count"] != len(rows):
            raise ValueError(f"candidate release {treatment} row count mismatch")
        if summary["episode_set_sha256"] != _sha256_json(
            sorted(row["source_episode_id"] for row in rows)
        ):
            raise ValueError(f"candidate release {treatment} episode set mismatch")
        if summary["row_set_sha256"] != _sha256_json(
            sorted(row["row_sha256"] for row in rows)
        ):
            raise ValueError(f"candidate release {treatment} row set mismatch")
        inventory_record = next(
            record
            for record in manifest["release_files"]
            if record["path"] == expected_path
        )
        if summary["view_sha256"] != inventory_record["sha256"]:
            raise ValueError(f"candidate release {treatment} view hash mismatch")
        expected_set = (
            pool_manifest["e_final_set_sha256"]
            if treatment in {"M6U", "M6F"}
            else pool_manifest["e_traj_set_sha256"]
        )
        if summary["episode_set_sha256"] != expected_set:
            raise ValueError(f"candidate release {treatment} pool set mismatch")


def _validate_file_record_semantics(record: dict[str, Any]) -> None:
    expected_role = _file_role(record["path"])
    expected_visibility = (
        "model_visible" if record["path"].startswith("views/") else "release_internal"
    )
    if record["role"] != expected_role or record["visibility_class"] != expected_visibility:
        raise ValueError(f"candidate release file semantics mismatch: {record['path']}")


def _file_role(path: str) -> str:
    if path.startswith("views/"):
        return "training_view"
    if path == POOL_PATH:
        return "training_pool_manifest"
    if path.startswith("internal/sidecars/"):
        return "eligibility_sidecar"
    if path.startswith("internal/eligibility/"):
        return "eligibility_certificate"
    raise ValueError(f"unsupported candidate release path: {path}")


def _release_identity(
    *,
    pool_manifest_sha256: str,
    leakage_policy_sha256: str,
    release_files: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "pool_manifest_sha256": pool_manifest_sha256,
        "leakage_policy_sha256": leakage_policy_sha256,
        "release_file_inventory_sha256": _sha256_json(release_files),
    }


def _validate_leakage_policy(policy: ReleaseLeakagePolicy) -> None:
    expected = ReleaseLeakagePolicy.create(
        policy_id=policy.policy_id,
        forbidden_canaries=policy.forbidden_canaries,
    )
    if policy != expected:
        raise ValueError("release leakage policy hash mismatch")


def _add_unique(files: dict[str, bytes], path: str, content: bytes) -> None:
    existing = files.get(path)
    if existing is not None and existing != content:
        raise ValueError(f"candidate release path collision: {path}")
    files[path] = content


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"invalid candidate view JSON line {line_number}: {path}") from error
        if not isinstance(row, dict):
            raise ValueError(f"candidate view row must be an object: {path}:{line_number}")
        rows.append(row)
    return rows


def _load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read candidate release JSON object: {path}") from error
    if not isinstance(value, dict):
        raise ValueError(f"candidate release JSON must be an object: {path}")
    return value


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _compact_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _write_json(path: Path, value: Any) -> None:
    path.write_bytes(_json_bytes(value))


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()
