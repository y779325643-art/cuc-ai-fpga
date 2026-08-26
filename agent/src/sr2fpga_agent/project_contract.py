"""Registered project-package validation and trusted project-envelope building."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Mapping, Sequence

from jsonschema import Draft202012Validator

from sr2fpga_agent.models import GeneratedProject
from sr2fpga_agent.method_contract import method_contract, method_policy_sha256
from sr2fpga_agent.path_safety import validate_project_relative_path
from sr2fpga_agent.repository_paths import RepositoryPaths


PROJECT_PACKAGE_CONTRACT_KEY = "project_package"
PROJECT_ENVELOPE_CONTRACT_KEY = "project_envelope"
PROJECT_ENVELOPE_INTEGRITY_SCHEME = "sr2fpga-json-sortkeys-merkle-sha256-v1"
_PROJECT_PACKAGE_DIGEST_DOMAIN = b"sr2fpga-project-package-v1\0"
_SHA256_LENGTH = 64
_BEHAVIOR_BEGIN = b"SR2FPGA_BEHAVIOR_BEGIN"
_BEHAVIOR_END = b"SR2FPGA_BEHAVIOR_END"


def load_registered_project_schema(
    contract_key: str,
    paths: RepositoryPaths | None = None,
) -> dict[str, Any]:
    """Load a registered project contract without allowing path escape."""

    if contract_key not in {
        PROJECT_PACKAGE_CONTRACT_KEY,
        PROJECT_ENVELOPE_CONTRACT_KEY,
    }:
        raise ValueError(f"unsupported project contract key: {contract_key!r}")

    repository_paths = paths or RepositoryPaths.discover()
    manifest_path = repository_paths.contracts_dir / "manifest.json"
    registry = json.loads(manifest_path.read_text(encoding="utf-8"))
    entry = registry.get("contracts", {}).get(contract_key)
    if not isinstance(entry, dict):
        raise ValueError(f"contracts manifest is missing {contract_key!r}")

    version = str(entry.get("version", "")).strip()
    relative_text = str(entry.get("path", "")).strip()
    relative = PurePosixPath(relative_text)
    if not relative_text or relative.is_absolute() or ".." in relative.parts:
        raise ValueError(
            f"contracts manifest has unsafe {contract_key} path: {relative_text!r}"
        )

    schema_path = (repository_paths.root / Path(*relative.parts)).resolve()
    contracts_root = repository_paths.contracts_dir.resolve()
    if schema_path != contracts_root and contracts_root not in schema_path.parents:
        raise ValueError(
            f"registered {contract_key} schema escapes contracts/: {relative_text!r}"
        )

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    contract_version = (
        schema.get("properties", {}).get("contract_version", {}).get("const")
    )
    if version != contract_version:
        raise ValueError(
            f"registered {contract_key} version {version!r} does not match "
            f"schema const {contract_version!r}"
        )
    return schema


def validate_project_package_manifest(
    manifest: Any,
    paths: RepositoryPaths | None = None,
) -> list[str]:
    """Validate canonical manifest schema plus cross-field path invariants."""

    errors = _validate_registered_project_contract(
        PROJECT_PACKAGE_CONTRACT_KEY,
        manifest,
        paths,
    )
    if not isinstance(manifest, dict):
        return errors

    source_paths = _record_paths(manifest.get("sources"), "$.sources", errors)
    artifact_paths = _record_paths(manifest.get("artifacts"), "$.artifacts", errors)
    overlap = sorted(set(source_paths) & set(artifact_paths))
    if overlap:
        errors.append(
            "$.artifacts: paths also declared as sources: " + ", ".join(overlap)
        )
    top = manifest.get("top")
    top_source = top.get("source") if isinstance(top, dict) else None
    if isinstance(top_source, str) and top_source not in source_paths:
        errors.append("$.top.source: must reference one entry in $.sources")
    return errors


def validate_project_envelope(
    envelope: Any,
    paths: RepositoryPaths | None = None,
) -> list[str]:
    """Validate schema plus the envelope and file-tree digests."""

    errors = _validate_registered_project_contract(
        PROJECT_ENVELOPE_CONTRACT_KEY,
        envelope,
        paths,
    )
    if not isinstance(envelope, dict):
        return errors

    expected_envelope_sha256 = _sha256_json(
        {key: value for key, value in envelope.items() if key != "envelope_sha256"}
    )
    if envelope.get("envelope_sha256") != expected_envelope_sha256:
        errors.append("$.envelope_sha256: does not match the canonical envelope payload")

    file_records = envelope.get("files")
    if isinstance(file_records, list):
        leaves: list[tuple[str, str]] = []
        seen_paths: set[str] = set()
        seen_casefold_paths: dict[str, str] = {}
        duplicate_paths: set[str] = set()
        casefold_collisions: set[tuple[str, str]] = set()
        for index, record in enumerate(file_records):
            if not isinstance(record, dict):
                continue
            path = record.get("path")
            digest = record.get("sha256")
            if not isinstance(path, str) or not isinstance(digest, str):
                continue
            try:
                normalized_path = validate_project_relative_path(path)
            except ValueError as exc:
                errors.append(f"$.files[{index}].path: {exc}")
                continue
            if normalized_path in seen_paths:
                duplicate_paths.add(normalized_path)
            seen_paths.add(normalized_path)
            casefold_path = normalized_path.casefold()
            previous_path = seen_casefold_paths.get(casefold_path)
            if previous_path is not None and previous_path != normalized_path:
                casefold_collisions.add(tuple(sorted((previous_path, normalized_path))))
            else:
                seen_casefold_paths[casefold_path] = normalized_path
            leaves.append((normalized_path, digest))
        if duplicate_paths:
            errors.append(
                "$.files: duplicate file paths: " + ", ".join(sorted(duplicate_paths))
            )
        if casefold_collisions:
            rendered = ", ".join(
                f"{left} <> {right}" for left, right in sorted(casefold_collisions)
            )
            errors.append("$.files: casefold-colliding file paths: " + rendered)
        if leaves:
            expected_root = _merkle_root(leaves)
            if envelope.get("project_merkle_root_sha256") != expected_root:
                errors.append(
                    "$.project_merkle_root_sha256: does not match envelope file records"
                )
    return errors


def verify_project_envelope(
    project: GeneratedProject,
    envelope: Any,
    paths: RepositoryPaths | None = None,
    *,
    event_ref_resolver: Callable[[str], bool] | None = None,
) -> list[str]:
    """Verify an envelope against the exact current project bytes."""

    errors = validate_project_envelope(envelope, paths)
    if not isinstance(envelope, dict):
        return errors

    normalized_project = _normalized_project_files(project, errors)
    envelope_records = envelope.get("files")
    records_by_path: dict[str, Mapping[str, Any]] = {}
    if isinstance(envelope_records, list):
        for record in envelope_records:
            if not isinstance(record, Mapping):
                continue
            path = record.get("path")
            if not isinstance(path, str):
                continue
            try:
                normalized_path = validate_project_relative_path(path)
            except ValueError:
                continue
            records_by_path.setdefault(normalized_path, record)

    project_paths = set(normalized_project)
    envelope_paths = set(records_by_path)
    missing_records = sorted(project_paths - envelope_paths)
    unknown_records = sorted(envelope_paths - project_paths)
    if missing_records:
        errors.append(
            "$.files: missing records for project paths: " + ", ".join(missing_records)
        )
    if unknown_records:
        errors.append(
            "$.files: records reference unknown project paths: "
            + ", ".join(unknown_records)
        )

    actual_leaves: list[tuple[str, str]] = []
    for path, content in sorted(normalized_project.items()):
        content_bytes = content.encode("utf-8")
        actual_digest = _sha256_bytes(content_bytes)
        actual_leaves.append((path, actual_digest))
        record = records_by_path.get(path)
        if record is not None and record.get("sha256") != actual_digest:
            errors.append(f"$.files[{path}].sha256: does not match project bytes")
        if record is not None and record.get("owner") == "composite":
            _verify_composite_regions(
                path,
                content_bytes,
                record,
                errors,
                event_ref_resolver,
            )

    if not actual_leaves:
        return errors
    actual_root = _merkle_root(actual_leaves)
    if envelope.get("project_merkle_root_sha256") != actual_root:
        errors.append(
            "$.project_merkle_root_sha256: does not match current project bytes"
        )

    try:
        manifest = _project_manifest(project)
    except ValueError as exc:
        errors.append(f"$.project_package_sha256: {exc}")
        return errors
    package_errors = validate_project_package_manifest(manifest, paths)
    errors.extend(f"$.project_package_sha256: {error}" for error in package_errors)
    manifest_roles = _manifest_file_roles(manifest)
    undeclared_project_paths = sorted(project_paths - set(manifest_roles))
    missing_project_paths = sorted(set(manifest_roles) - project_paths)
    if undeclared_project_paths:
        errors.append(
            "$.project_package_sha256: manifest does not declare project paths: "
            + ", ".join(undeclared_project_paths)
        )
    if missing_project_paths:
        errors.append(
            "$.project_package_sha256: manifest references missing project paths: "
            + ", ".join(missing_project_paths)
        )
    for path in sorted(project_paths & envelope_paths & set(manifest_roles)):
        if records_by_path[path].get("file_role") != manifest_roles[path]:
            errors.append(
                f"$.files[{path}].file_role: does not match project manifest"
            )
    manifest_digest = _sha256_json(manifest)
    expected_package_digest = _project_package_digest(manifest_digest, actual_root)
    if envelope.get("project_package_sha256") != expected_package_digest:
        errors.append(
            "$.project_package_sha256: does not match manifest and current project root"
        )
    if any(record.get("owner") == "composite" for record in records_by_path.values()):
        condition = envelope.get("method_condition_id")
        try:
            method_contract(condition)
            expected_policy = method_policy_sha256(condition)
        except (KeyError, ValueError):
            errors.append("$.method_condition_id: composite envelope requires a registered method")
        else:
            if envelope.get("method_policy_sha256") != expected_policy:
                errors.append(
                    "$.method_policy_sha256: does not match the registered method policy"
                )
    return errors


def project_package_sha256(
    project: GeneratedProject,
    paths: RepositoryPaths | None = None,
) -> str:
    """Return the method-neutral digest of a complete canonical project package."""

    manifest = _project_manifest(project)
    errors = validate_project_package_manifest(manifest, paths)
    normalized = _normalized_project_files(project, errors)
    declared = set(_manifest_file_roles(manifest))
    actual = set(normalized)
    if declared != actual:
        missing = sorted(declared - actual)
        extra = sorted(actual - declared)
        if missing:
            errors.append("manifest references missing project paths: " + ", ".join(missing))
        if extra:
            errors.append("manifest does not declare project paths: " + ", ".join(extra))
    if errors:
        raise ValueError("invalid project package: " + "; ".join(errors))
    leaves = [
        (path, _sha256_bytes(content.encode("utf-8")))
        for path, content in normalized.items()
    ]
    return _project_package_digest(_sha256_json(manifest), _merkle_root(leaves))


def build_project_envelope(
    project: GeneratedProject,
    *,
    episode_id: str,
    method_condition_id: str,
    method_policy_sha256: str,
    snapshot_id: str,
    file_policies: Mapping[str, Mapping[str, Any]],
    evaluator_material_refs: Sequence[Mapping[str, Any]] = (),
    paths: RepositoryPaths | None = None,
) -> dict[str, Any]:
    """Build a hash-bound envelope from explicit trusted ownership policy.

    The candidate manifest supplies build intent only. Ownership, editability,
    file digests, and the project root are reconstructed here by the trusted
    caller. Legacy manifests are deliberately rejected rather than labelled as
    project-package-v1.
    """

    manifest = _project_manifest(project)
    package_errors = validate_project_package_manifest(manifest, paths)
    if package_errors:
        raise ValueError(
            "manifest.json does not satisfy project-package-v1: "
            + "; ".join(package_errors)
        )
    _require_non_empty("episode_id", episode_id)
    _require_non_empty("method_condition_id", method_condition_id)
    _require_non_empty("snapshot_id", snapshot_id)
    _require_sha256("method_policy_sha256", method_policy_sha256)
    if evaluator_material_refs:
        raise ValueError(
            "evaluator material references require CD3 trusted authority"
        )

    project_paths = set(project.files)
    policy_paths = set(file_policies)
    missing_policies = sorted(project_paths - policy_paths)
    unknown_policies = sorted(policy_paths - project_paths)
    if missing_policies:
        raise ValueError(
            "file ownership policy is missing project paths: "
            + ", ".join(missing_policies)
        )
    if unknown_policies:
        raise ValueError(
            "file ownership policy references unknown project paths: "
            + ", ".join(unknown_policies)
        )

    roles = _manifest_file_roles(manifest)
    undeclared_project_paths = sorted(project_paths - set(roles))
    missing_project_paths = sorted(set(roles) - project_paths)
    if undeclared_project_paths:
        raise ValueError(
            "project-package-v1 does not declare project paths: "
            + ", ".join(undeclared_project_paths)
        )
    if missing_project_paths:
        raise ValueError(
            "project-package-v1 references missing project paths: "
            + ", ".join(missing_project_paths)
        )
    path_errors: list[str] = []
    _normalized_project_files(project, path_errors)
    if path_errors:
        raise ValueError("project paths are not canonical: " + "; ".join(path_errors))

    file_records: list[dict[str, Any]] = []
    merkle_leaves: list[tuple[str, str]] = []
    for raw_path in sorted(project.files):
        relative_path = validate_project_relative_path(raw_path)
        content_sha256 = _sha256_bytes(project.files[raw_path].encode("utf-8"))
        policy = dict(file_policies[raw_path])
        unexpected = set(policy) - {"owner", "origin", "editable", "regions"}
        if unexpected:
            raise ValueError(
                f"file ownership policy for {raw_path!r} has unknown fields: "
                + ", ".join(sorted(unexpected))
            )
        if policy.get("owner") == "composite" or "regions" in policy:
            raise ValueError(
                "composite ownership and region provenance require CD3 trusted authority"
            )
        record: dict[str, Any] = {
            "path": relative_path,
            "sha256": content_sha256,
            "file_role": roles[relative_path],
            "owner": policy.get("owner"),
            "origin": policy.get("origin"),
            "editable": policy.get("editable"),
            "snapshot_id": snapshot_id,
        }
        if "regions" in policy:
            record["regions"] = policy["regions"]
        file_records.append(record)
        merkle_leaves.append((relative_path, content_sha256))

    manifest_digest = _sha256_json(manifest)
    project_merkle_root = _merkle_root(merkle_leaves)
    envelope_without_hash: dict[str, Any] = {
        "contract_version": "project-envelope-v1",
        "integrity_scheme": PROJECT_ENVELOPE_INTEGRITY_SCHEME,
        "episode_id": episode_id,
        "method_condition_id": method_condition_id,
        "method_policy_sha256": method_policy_sha256,
        "project_package_sha256": _project_package_digest(
            manifest_digest,
            project_merkle_root,
        ),
        "project_merkle_root_sha256": project_merkle_root,
        "files": file_records,
        "evaluator_material_refs": [],
    }
    envelope = {
        **envelope_without_hash,
        "envelope_sha256": _sha256_json(envelope_without_hash),
    }
    envelope_errors = validate_project_envelope(envelope, paths)
    if envelope_errors:
        raise ValueError(
            "project envelope does not satisfy project-envelope-v1: "
            + "; ".join(envelope_errors)
        )
    return envelope


def build_composite_project_envelope(
    project: GeneratedProject,
    *,
    episode_id: str,
    method_condition_id: str,
    snapshot_id: str,
    trusted_builder_event_id: str,
    model_generation_event_id: str,
    event_ref_resolver: Callable[[str], bool],
    paths: RepositoryPaths | None = None,
) -> dict[str, Any]:
    """Build a trusted envelope for skeleton RTL with model behavior regions."""

    contract = method_contract(method_condition_id)
    if not contract.uses_deterministic_skeleton:
        raise ValueError("composite project envelope requires a skeleton method")
    for label, event_id in (
        ("trusted_builder_event_id", trusted_builder_event_id),
        ("model_generation_event_id", model_generation_event_id),
    ):
        if not isinstance(event_id, str) or not event_ref_resolver(event_id):
            raise ValueError(f"{label} does not resolve to a trusted append-only event")

    manifest = _project_manifest(project)
    package_errors = validate_project_package_manifest(manifest, paths)
    if package_errors:
        raise ValueError(
            "manifest.json does not satisfy project-package-v1: "
            + "; ".join(package_errors)
        )
    _require_non_empty("episode_id", episode_id)
    _require_non_empty("snapshot_id", snapshot_id)
    normalized_errors: list[str] = []
    normalized_files = _normalized_project_files(project, normalized_errors)
    if normalized_errors:
        raise ValueError("project paths are not canonical: " + "; ".join(normalized_errors))
    roles = _manifest_file_roles(manifest)
    if set(normalized_files) != set(roles):
        raise ValueError("project-package-v1 path set does not match project files")

    records: list[dict[str, Any]] = []
    leaves: list[tuple[str, str]] = []
    composite_count = 0
    for path, content in sorted(normalized_files.items()):
        content_bytes = content.encode("utf-8")
        digest = _sha256_bytes(content_bytes)
        record: dict[str, Any] = {
            "path": path,
            "sha256": digest,
            "file_role": roles[path],
            "owner": "trusted_builder",
            "origin": "deterministic",
            "editable": False,
            "snapshot_id": snapshot_id,
        }
        if roles[path] == "rtl_source" and _BEHAVIOR_BEGIN in content_bytes:
            record.update(
                {
                    "owner": "composite",
                    "editable": True,
                    "regions": _derive_composite_regions(
                        path,
                        content_bytes,
                        trusted_builder_event_id=trusted_builder_event_id,
                        model_generation_event_id=model_generation_event_id,
                    ),
                }
            )
            composite_count += 1
        elif roles[path] == "system_his":
            record.update(
                {
                    "owner": "model",
                    "origin": "model_generated",
                    "editable": False,
                }
            )
        records.append(record)
        leaves.append((path, digest))
    if composite_count == 0:
        raise ValueError("composite project envelope requires model behavior regions")

    root = _merkle_root(leaves)
    payload: dict[str, Any] = {
        "contract_version": "project-envelope-v1",
        "integrity_scheme": PROJECT_ENVELOPE_INTEGRITY_SCHEME,
        "episode_id": episode_id,
        "method_condition_id": contract.method_condition.value,
        "method_policy_sha256": method_policy_sha256(contract.method_condition),
        "project_package_sha256": _project_package_digest(_sha256_json(manifest), root),
        "project_merkle_root_sha256": root,
        "files": records,
        "evaluator_material_refs": [],
    }
    envelope = {**payload, "envelope_sha256": _sha256_json(payload)}
    errors = verify_project_envelope(
        project,
        envelope,
        paths,
        event_ref_resolver=event_ref_resolver,
    )
    if errors:
        raise ValueError(
            "project envelope does not satisfy trusted composite policy: "
            + "; ".join(errors)
        )
    return envelope


def _derive_composite_regions(
    path: str,
    content: bytes,
    *,
    trusted_builder_event_id: str,
    model_generation_event_id: str,
) -> list[dict[str, Any]]:
    _validate_behavior_marker_order(path, content)
    regions: list[dict[str, Any]] = []
    cursor = 0
    pair_index = 0
    trusted_index = 0
    safe_path = "".join(character if character.isalnum() else "-" for character in path)
    while True:
        begin = content.find(_BEHAVIOR_BEGIN, cursor)
        if begin < 0:
            break
        begin_end = begin + len(_BEHAVIOR_BEGIN)
        end = content.find(_BEHAVIOR_END, begin_end)
        if end < 0:
            raise ValueError(f"{path}: behavior region has no end marker")
        nested = content.find(_BEHAVIOR_BEGIN, begin_end, end)
        if nested >= 0:
            raise ValueError(f"{path}: behavior regions cannot be nested")
        regions.append(
            _region_record(
                f"{safe_path}-trusted-{trusted_index:03d}",
                "trusted_builder",
                cursor,
                begin_end,
                content,
                False,
                trusted_builder_event_id,
            )
        )
        trusted_index += 1
        if end <= begin_end:
            raise ValueError(f"{path}: behavior region must contain model bytes")
        regions.append(
            _region_record(
                f"{safe_path}-model-{pair_index:03d}",
                "model",
                begin_end,
                end,
                content,
                True,
                model_generation_event_id,
            )
        )
        pair_index += 1
        cursor = end
    if pair_index == 0:
        raise ValueError(f"{path}: no behavior region markers found")
    if content.find(_BEHAVIOR_END, cursor + len(_BEHAVIOR_END)) >= 0:
        raise ValueError(f"{path}: behavior region has an unmatched end marker")
    regions.append(
        _region_record(
            f"{safe_path}-trusted-{trusted_index:03d}",
            "trusted_builder",
            cursor,
            len(content),
            content,
            False,
            trusted_builder_event_id,
        )
    )
    return regions


def _validate_behavior_marker_order(path: str, content: bytes) -> None:
    search = 0
    pairs = 0
    while True:
        begin = content.find(_BEHAVIOR_BEGIN, search)
        end_before_begin = content.find(_BEHAVIOR_END, search)
        if begin < 0:
            if end_before_begin >= 0:
                raise ValueError(f"{path}: behavior region has an unmatched end marker")
            break
        if end_before_begin >= 0 and end_before_begin < begin:
            raise ValueError(f"{path}: behavior region has an unmatched end marker")
        begin_end = begin + len(_BEHAVIOR_BEGIN)
        end = content.find(_BEHAVIOR_END, begin_end)
        if end < 0:
            raise ValueError(f"{path}: behavior region has no end marker")
        nested = content.find(_BEHAVIOR_BEGIN, begin_end, end)
        if nested >= 0:
            raise ValueError(f"{path}: behavior regions cannot be nested")
        pairs += 1
        search = end + len(_BEHAVIOR_END)
    if pairs == 0:
        raise ValueError(f"{path}: no behavior region markers found")


def _region_record(
    region_id: str,
    owner: str,
    start: int,
    end: int,
    content: bytes,
    editable: bool,
    event_id: str,
) -> dict[str, Any]:
    if end <= start:
        raise ValueError(f"{region_id}: region byte range must be non-empty")
    return {
        "region_id": region_id,
        "owner": owner,
        "start_byte": start,
        "end_byte": end,
        "sha256": _sha256_bytes(content[start:end]),
        "editable": editable,
        "event_refs": [event_id],
    }


def _verify_composite_regions(
    path: str,
    content: bytes,
    record: Mapping[str, Any],
    errors: list[str],
    event_ref_resolver: Callable[[str], bool] | None,
) -> None:
    regions = record.get("regions")
    if not isinstance(regions, list) or not regions:
        return
    if event_ref_resolver is None:
        errors.append(f"$.files[{path}].regions: trusted event resolver is required")
    try:
        expected_regions = _derive_composite_regions(
            path,
            content,
            trusted_builder_event_id="event-" + "0" * 64,
            model_generation_event_id="event-" + "1" * 64,
        )
    except ValueError as exc:
        errors.append(f"$.files[{path}].regions: {exc}")
        expected_regions = []
    cursor = 0
    has_editable_model = False
    refs_by_owner: dict[str, tuple[str, ...]] = {}
    for index, region in enumerate(regions):
        if not isinstance(region, Mapping):
            continue
        start = region.get("start_byte")
        end = region.get("end_byte")
        if not isinstance(start, int) or isinstance(start, bool) or not isinstance(end, int) or isinstance(end, bool):
            continue
        if start != cursor or end <= start or end > len(content):
            errors.append(
                f"$.files[{path}].regions[{index}]: byte ranges must be ordered, contiguous, and in bounds"
            )
            cursor = max(cursor, end)
            continue
        if region.get("sha256") != _sha256_bytes(content[start:end]):
            errors.append(
                f"$.files[{path}].regions[{index}].sha256: does not match project bytes"
            )
        owner = region.get("owner")
        editable = region.get("editable")
        if owner == "model" and editable is True:
            has_editable_model = True
        if owner == "trusted_builder" and editable is not False:
            errors.append(
                f"$.files[{path}].regions[{index}].editable: trusted region must be immutable"
            )
        refs = region.get("event_refs")
        if isinstance(refs, list) and owner in {"model", "trusted_builder"}:
            normalized_refs = tuple(str(item) for item in refs)
            previous_refs = refs_by_owner.setdefault(str(owner), normalized_refs)
            if previous_refs != normalized_refs:
                errors.append(
                    f"$.files[{path}].regions[{index}].event_refs: owner event lineage is inconsistent"
                )
        if isinstance(refs, list) and event_ref_resolver is not None:
            for event_id in refs:
                try:
                    resolved = isinstance(event_id, str) and event_ref_resolver(event_id)
                except Exception:
                    resolved = False
                if not resolved:
                    errors.append(
                        f"$.files[{path}].regions[{index}].event_refs: unresolved event {event_id!r}"
                    )
        cursor = end
    actual_layout = [
        (
            region.get("start_byte"),
            region.get("end_byte"),
            region.get("owner"),
            region.get("editable"),
        )
        for region in regions
        if isinstance(region, Mapping)
    ]
    expected_layout = [
        (
            region["start_byte"],
            region["end_byte"],
            region["owner"],
            region["editable"],
        )
        for region in expected_regions
    ]
    if expected_regions and actual_layout != expected_layout:
        errors.append(f"$.files[{path}].regions: layout does not match behavior markers")
    if cursor != len(content):
        errors.append(f"$.files[{path}].regions: byte ranges must cover the complete file")
    if record.get("editable") is not has_editable_model:
        errors.append(
            f"$.files[{path}].editable: must equal the presence of an editable model region"
        )


def _validate_registered_project_contract(
    contract_key: str,
    payload: Any,
    paths: RepositoryPaths | None,
) -> list[str]:
    validator = Draft202012Validator(load_registered_project_schema(contract_key, paths))
    errors = sorted(
        validator.iter_errors(payload),
        key=lambda error: (
            tuple(str(part) for part in error.absolute_path),
            error.message,
        ),
    )
    return [
        f"{_json_path(error.absolute_path)}: {error.message}"
        for error in errors
    ]


def _project_manifest(project: GeneratedProject) -> dict[str, Any]:
    content = project.files.get("manifest.json")
    if content is None:
        raise ValueError("manifest.json is required")
    try:
        manifest = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"manifest.json is not valid JSON: {exc.msg}") from exc
    if not isinstance(manifest, dict):
        raise ValueError("manifest.json must contain a JSON object")
    return manifest


def _manifest_file_roles(manifest: Mapping[str, Any]) -> dict[str, str]:
    roles = {"manifest.json": "project_manifest"}
    for source in manifest.get("sources", []):
        if isinstance(source, Mapping) and isinstance(source.get("path"), str):
            roles[source["path"]] = "rtl_source"
    for artifact in manifest.get("artifacts", []):
        if (
            isinstance(artifact, Mapping)
            and isinstance(artifact.get("path"), str)
            and isinstance(artifact.get("role"), str)
        ):
            roles[artifact["path"]] = artifact["role"]
    return roles


def _record_paths(value: Any, label: str, errors: list[str]) -> list[str]:
    if not isinstance(value, list):
        return []
    paths: list[str] = []
    duplicates: set[str] = set()
    seen: set[str] = set()
    for record in value:
        if not isinstance(record, dict) or not isinstance(record.get("path"), str):
            continue
        path = record["path"]
        try:
            normalized = validate_project_relative_path(path)
        except ValueError as exc:
            errors.append(f"{label}: {exc}")
            continue
        if normalized in seen:
            duplicates.add(normalized)
        seen.add(normalized)
        paths.append(normalized)
    if duplicates:
        errors.append(f"{label}: duplicate paths: " + ", ".join(sorted(duplicates)))
    return paths


def _normalized_project_files(
    project: GeneratedProject,
    errors: list[str],
) -> dict[str, str]:
    normalized_files: dict[str, str] = {}
    casefold_paths: dict[str, str] = {}
    collisions: set[tuple[str, str]] = set()
    for raw_path, content in project.files.items():
        try:
            normalized_path = validate_project_relative_path(raw_path)
        except ValueError as exc:
            errors.append(f"$.project.files[{raw_path!r}]: {exc}")
            continue
        casefold_path = normalized_path.casefold()
        previous_path = casefold_paths.get(casefold_path)
        if previous_path is not None and previous_path != normalized_path:
            collisions.add(tuple(sorted((previous_path, normalized_path))))
        else:
            casefold_paths[casefold_path] = normalized_path
        normalized_files[normalized_path] = content
    if collisions:
        rendered = ", ".join(
            f"{left} <> {right}" for left, right in sorted(collisions)
        )
        errors.append("$.project.files: casefold-colliding paths: " + rendered)
    return normalized_files


def _merkle_root(leaves: Sequence[tuple[str, str]]) -> str:
    if not leaves:
        raise ValueError("project envelope requires at least one file")
    nodes = [
        hashlib.sha256(f"{path}\0{digest}".encode("utf-8")).digest()
        for path, digest in sorted(leaves)
    ]
    while len(nodes) > 1:
        if len(nodes) % 2:
            nodes.append(nodes[-1])
        nodes = [
            hashlib.sha256(nodes[index] + nodes[index + 1]).digest()
            for index in range(0, len(nodes), 2)
        ]
    return nodes[0].hex()


def _sha256_json(value: Any) -> str:
    canonical = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return _sha256_bytes(canonical.encode("utf-8"))


def _project_package_digest(manifest_digest: str, project_merkle_root: str) -> str:
    _require_sha256("manifest_digest", manifest_digest)
    _require_sha256("project_merkle_root", project_merkle_root)
    payload = (
        _PROJECT_PACKAGE_DIGEST_DOMAIN
        + bytes.fromhex(manifest_digest)
        + bytes.fromhex(project_merkle_root)
    )
    return _sha256_bytes(payload)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _require_non_empty(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")


def _require_sha256(name: str, value: str) -> None:
    if (
        not isinstance(value, str)
        or len(value) != _SHA256_LENGTH
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{name} must be a lowercase SHA-256 hex digest")


def _json_path(parts: Any) -> str:
    path = "$"
    for part in parts:
        if isinstance(part, int):
            path += f"[{part}]"
        else:
            path += f".{part}"
    return path
