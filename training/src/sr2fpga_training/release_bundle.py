"""Read-only inspection of promoted SR2FPGA training release bundles."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from types import MappingProxyType
from typing import Any, Iterable, Mapping

from jsonschema import Draft202012Validator

from .contracts import TrainingContractError, load_registered_schema
from .release_reader import validate_training_view_row_v2


MANIFEST_FILENAME = "training-release-manifest.json"
POOL_PATH = "internal/training-pool-manifest.json"
TREATMENTS = ("M6U", "M6F", "M6T", "M6F_E_TRAJ")
_LEAKAGE_POLICY_VERSION = "training-view-leakage-v1"


@dataclass(frozen=True)
class PromotionAuthorizationExpectation:
    campaign_freeze_sha256: str
    training_plan_sha256: str
    promotion_record_sha256: str


@dataclass(frozen=True)
class TrainingLeakagePolicyExpectation:
    policy_id: str
    policy_sha256: str
    forbidden_canaries: tuple[str, ...]
    forbidden_canary_set_sha256: str

    @classmethod
    def create(
        cls, *, policy_id: str, forbidden_canaries: Iterable[str] = ()
    ) -> "TrainingLeakagePolicyExpectation":
        if not policy_id:
            raise TrainingContractError("release leakage policy_id must be non-empty")
        canaries = tuple(sorted(set(forbidden_canaries)))
        if any(not isinstance(canary, str) or not canary for canary in canaries):
            raise TrainingContractError("release leakage canaries must be non-empty")
        canary_set_sha256 = _sha256_json(canaries)
        policy_sha256 = _sha256_json(
            {
                "policy_version": _LEAKAGE_POLICY_VERSION,
                "policy_id": policy_id,
                "forbidden_canary_set_sha256": canary_set_sha256,
            }
        )
        return cls(policy_id, policy_sha256, canaries, canary_set_sha256)


@dataclass(frozen=True)
class InspectedTrainingRelease:
    root: Path
    manifest: Mapping[str, Any]
    treatment_paths: Mapping[str, Path]

    def treatment_path(self, treatment: str) -> Path:
        try:
            return self.treatment_paths[treatment]
        except KeyError as error:
            raise TrainingContractError(
                f"release does not declare treatment {treatment!r}"
            ) from error


def inspect_promoted_release(
    release_root: Path | str,
    *,
    authorization: PromotionAuthorizationExpectation,
    leakage_policy: TrainingLeakagePolicyExpectation,
) -> InspectedTrainingRelease:
    """Inspect a promoted release without creating data or authorizing a run."""

    _validate_authorization_expectation(authorization)
    _validate_leakage_policy_expectation(leakage_policy)
    root = Path(release_root).resolve()
    manifest = _load_object(root / MANIFEST_FILENAME)
    _validate_release_manifest(manifest)
    if manifest["release_state"] != "promoted":
        raise TrainingContractError("Training rejects candidate_unpromoted releases")
    if manifest["training_authorized"] is not True:
        raise TrainingContractError("promoted release must set training_authorized=true")
    if manifest["authorization"] != {
        "campaign_freeze_sha256": authorization.campaign_freeze_sha256,
        "training_plan_sha256": authorization.training_plan_sha256,
        "promotion_record_sha256": authorization.promotion_record_sha256,
    }:
        raise TrainingContractError("release promotion authorization mismatch")
    if manifest["leakage_audit"] != {
        "policy_id": leakage_policy.policy_id,
        "policy_sha256": leakage_policy.policy_sha256,
        "forbidden_canary_set_sha256": (
            leakage_policy.forbidden_canary_set_sha256
        ),
        "status": "pass",
    }:
        raise TrainingContractError("release leakage policy mismatch")

    inventory = {record["path"]: record for record in manifest["release_files"]}
    actual_paths = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and path != root / MANIFEST_FILENAME
    }
    if actual_paths != set(inventory):
        raise TrainingContractError("release file inventory mismatch")
    for relative_path, record in inventory.items():
        content = _release_path(root, relative_path).read_bytes()
        if len(content) != record["size_bytes"]:
            raise TrainingContractError(f"release size mismatch: {relative_path}")
        if _sha256_bytes(content) != record["sha256"]:
            raise TrainingContractError(f"release checksum mismatch: {relative_path}")
        _validate_file_semantics(record)

    if manifest["pool_manifest_path"] != POOL_PATH:
        raise TrainingContractError("release pool manifest path is not canonical")
    pool = _load_object(_release_path(root, POOL_PATH))
    _validate_pool_manifest(pool)
    bindings = (
        (manifest["pool_id"], pool["pool_id"], "pool_id"),
        (manifest["pool_manifest_sha256"], pool["artifact_sha256"], "pool hash"),
        (manifest["training_split_id"], pool["training_split_id"], "training split"),
        (manifest["e_final_set_sha256"], pool["e_final_set_sha256"], "E_final"),
        (manifest["e_traj_set_sha256"], pool["e_traj_set_sha256"], "E_traj"),
    )
    for actual, expected, label in bindings:
        if actual != expected:
            raise TrainingContractError(f"release pool binding mismatch: {label}")

    treatment_paths, referenced = _inspect_treatments(
        root,
        manifest,
        pool,
        forbidden_canaries=leakage_policy.forbidden_canaries,
    )
    if referenced != set(inventory):
        raise TrainingContractError("release contains unreferenced internal artifacts")
    return InspectedTrainingRelease(
        root=root,
        manifest=MappingProxyType(manifest),
        treatment_paths=MappingProxyType(treatment_paths),
    )


def _inspect_treatments(
    root: Path,
    manifest: dict[str, Any],
    pool: dict[str, Any],
    *,
    forbidden_canaries: tuple[str, ...],
) -> tuple[dict[str, Path], set[str]]:
    summaries = {record["treatment"]: record for record in manifest["treatments"]}
    inventory = {record["path"]: record for record in manifest["release_files"]}
    refs = {
        treatment: {
            record["row_id"]: record
            for record in pool["treatment_rows"][treatment]
        }
        for treatment in TREATMENTS
    }
    mixture = {
        episode_id: (
            stratum["source_class"],
            stratum["failure_origin"],
        )
        for stratum in pool["mixture_strata"]
        for episode_id in stratum["episode_ids"]
    }
    treatment_paths: dict[str, Path] = {}
    referenced = {POOL_PATH}
    seen_certificates: dict[str, dict[str, Any]] = {}
    for treatment in TREATMENTS:
        summary = summaries[treatment]
        expected_view_path = f"views/{treatment}.jsonl"
        if summary["view_path"] != expected_view_path:
            raise TrainingContractError(f"{treatment} view path is not canonical")
        view_path = _release_path(root, expected_view_path)
        if expected_view_path not in inventory:
            raise TrainingContractError(f"{treatment} view is absent from inventory")
        treatment_paths[treatment] = view_path
        referenced.add(expected_view_path)
        rows = _load_rows(view_path, forbidden_canaries=forbidden_canaries)
        if summary["row_count"] != len(rows):
            raise TrainingContractError(f"{treatment} row count mismatch")
        if summary["episode_set_sha256"] != _sha256_json(
            sorted(row["source_episode_id"] for row in rows)
        ):
            raise TrainingContractError(f"{treatment} episode set mismatch")
        if summary["row_set_sha256"] != _sha256_json(
            sorted(row["row_sha256"] for row in rows)
        ):
            raise TrainingContractError(f"{treatment} row set mismatch")
        inventory_record = inventory[expected_view_path]
        if summary["view_sha256"] != inventory_record["sha256"]:
            raise TrainingContractError(f"{treatment} view hash mismatch")
        expected_pool_set = (
            pool["e_final_set_sha256"]
            if treatment in {"M6U", "M6F"}
            else pool["e_traj_set_sha256"]
        )
        if summary["episode_set_sha256"] != expected_pool_set:
            raise TrainingContractError(f"{treatment} pool set mismatch")

        if {row["row_id"] for row in rows} != set(refs[treatment]):
            raise TrainingContractError(f"{treatment} pool row reference mismatch")
        for row in rows:
            ref = refs[treatment][row["row_id"]]
            sidecar_path = f"internal/sidecars/{row['row_id']}.json"
            certificate_path = (
                "internal/eligibility/"
                f"{ref['eligibility_artifact_sha256']}.json"
            )
            sidecar = _load_object(_release_path(root, sidecar_path))
            certificate = _load_object(_release_path(root, certificate_path))
            referenced.update((sidecar_path, certificate_path))
            _validate_linked_artifacts(row, sidecar, certificate, ref, pool)
            previous = seen_certificates.setdefault(
                certificate["episode_id"], certificate
            )
            if previous["artifact_sha256"] != certificate["artifact_sha256"]:
                raise TrainingContractError(
                    f"episode {certificate['episode_id']} uses multiple eligibility certificates"
                )
            expected_source = mixture.get(certificate["episode_id"])
            if expected_source != (
                certificate["source_class"],
                certificate["failure_origin"],
            ):
                raise TrainingContractError("release mixture/certificate mismatch")
    return treatment_paths, referenced


def _validate_linked_artifacts(
    row: dict[str, Any],
    sidecar: dict[str, Any],
    certificate: dict[str, Any],
    ref: dict[str, Any],
    pool: dict[str, Any],
) -> None:
    _validate_registered("training_view_eligibility_sidecar", sidecar)
    _validate_registered("training_eligibility", certificate)
    _validate_self_hash(sidecar, "artifact_sha256", "eligibility sidecar")
    _validate_self_hash(certificate, "artifact_sha256", "eligibility certificate")
    if certificate["eligibility_status"] != "eligible":
        raise TrainingContractError("release contains an ineligible certificate")
    if certificate["official_hidden_outcome_ref_count"] != 0:
        raise TrainingContractError("release references official hidden outcomes")
    if (
        certificate["policy_id"] != pool["policy_id"]
        or certificate["policy_sha256"] != pool["policy_sha256"]
        or certificate["training_split_id"] != pool["training_split_id"]
    ):
        raise TrainingContractError("release eligibility policy/split mismatch")
    bindings = (
        (sidecar["row_id"], row["row_id"], "sidecar row_id"),
        (sidecar["row_sha256"], row["row_sha256"], "sidecar row hash"),
        (sidecar["source_episode_id"], row["source_episode_id"], "sidecar episode"),
        (sidecar["snapshot_id"], row["snapshot_id"], "sidecar snapshot"),
        (sidecar["treatment"], row["treatment"], "sidecar treatment"),
        (
            sidecar["eligibility_artifact_sha256"],
            certificate["artifact_sha256"],
            "sidecar certificate",
        ),
        (
            sidecar["eligibility_evidence_bundle_sha256"],
            certificate["evidence_bundle_sha256"],
            "sidecar evidence bundle",
        ),
        (row["source_episode_id"], certificate["episode_id"], "certificate episode"),
        (ref, _row_ref(row, sidecar, certificate), "pool row ref"),
    )
    for actual, expected, label in bindings:
        if actual != expected:
            raise TrainingContractError(f"release artifact binding mismatch: {label}")
    expected_snapshot = (
        certificate["initial_snapshot_sha256"]
        if row["treatment"] == "M6U"
        else certificate["project_envelope_sha256"]
    )
    if sidecar["snapshot_envelope_sha256"] != expected_snapshot:
        raise TrainingContractError("release snapshot envelope mismatch")
    if (
        row["treatment"] == "M6U"
        and row["snapshot_id"] != certificate["initial_snapshot_id"]
    ):
        raise TrainingContractError("release M6U row is not the initial snapshot")


def _validate_release_manifest(manifest: dict[str, Any]) -> None:
    _validate_registered("training_release_manifest", manifest)
    _validate_self_hash(manifest, "artifact_sha256", "training release manifest")
    file_paths = [record["path"] for record in manifest["release_files"]]
    if file_paths != sorted(file_paths) or len(file_paths) != len(set(file_paths)):
        raise TrainingContractError("release file inventory is not canonical")
    treatments = [record["treatment"] for record in manifest["treatments"]]
    if treatments != list(TREATMENTS):
        raise TrainingContractError("release treatment summaries are not canonical")
    expected_release_id = "release-" + _sha256_json(
        {
            "pool_manifest_sha256": manifest["pool_manifest_sha256"],
            "leakage_policy_sha256": manifest["leakage_audit"]["policy_sha256"],
            "release_file_inventory_sha256": _sha256_json(manifest["release_files"]),
        }
    )
    if manifest["release_id"] != expected_release_id:
        raise TrainingContractError("release_id is not canonical")


def _validate_pool_manifest(pool: dict[str, Any]) -> None:
    _validate_registered("training_pool_manifest", pool)
    _validate_self_hash(pool, "artifact_sha256", "training pool manifest")
    e_final = pool["e_final_episode_ids"]
    e_traj = pool["e_traj_episode_ids"]
    if e_final != sorted(e_final) or e_traj != sorted(e_traj):
        raise TrainingContractError("pool episode IDs are not canonical")
    if pool["e_final_set_sha256"] != _sha256_json(e_final):
        raise TrainingContractError("pool E_final hash mismatch")
    if pool["e_traj_set_sha256"] != _sha256_json(e_traj):
        raise TrainingContractError("pool E_traj hash mismatch")
    if not set(e_traj).issubset(e_final):
        raise TrainingContractError("pool E_traj is not an E_final subset")
    expected_sets = {
        "M6U": set(e_final),
        "M6F": set(e_final),
        "M6T": set(e_traj),
        "M6F_E_TRAJ": set(e_traj),
    }
    seen_rows: set[str] = set()
    for treatment in TREATMENTS:
        refs = pool["treatment_rows"][treatment]
        episodes = [ref["source_episode_id"] for ref in refs]
        if (
            episodes != sorted(episodes)
            or len(episodes) != len(set(episodes))
            or set(episodes) != expected_sets[treatment]
        ):
            raise TrainingContractError(f"pool {treatment} episode refs mismatch")
        if any(ref["treatment"] != treatment for ref in refs):
            raise TrainingContractError(f"pool {treatment} has wrong treatment ref")
        for ref in refs:
            if ref["row_id"] in seen_rows:
                raise TrainingContractError("pool contains duplicate row_id")
            seen_rows.add(ref["row_id"])
    transition_refs = {
        treatment: {
            ref["source_episode_id"]: ref.get("transition_evidence_sha256")
            for ref in pool["treatment_rows"][treatment]
        }
        for treatment in ("M6T", "M6F_E_TRAJ")
    }
    if transition_refs["M6T"] != transition_refs["M6F_E_TRAJ"]:
        raise TrainingContractError("pool transition evidence mismatch")
    covered: list[str] = []
    keys: list[tuple[str, str, str]] = []
    for stratum in pool["mixture_strata"]:
        ids = stratum["episode_ids"]
        if ids != sorted(ids) or stratum["episode_count"] != len(ids):
            raise TrainingContractError("pool mixture stratum is not canonical")
        covered.extend(ids)
        keys.append(
            (
                stratum["family_id"],
                stratum["source_class"],
                stratum["failure_origin"],
            )
        )
    if (
        keys != sorted(keys)
        or len(keys) != len(set(keys))
        or sorted(covered) != e_final
        or len(covered) != len(set(covered))
    ):
        raise TrainingContractError("pool mixture does not partition E_final")
    expected_pool_id = "pool-" + _sha256_json(
        {
            "policy_sha256": pool["policy_sha256"],
            "training_split_id": pool["training_split_id"],
            "e_final_set_sha256": pool["e_final_set_sha256"],
            "e_traj_set_sha256": pool["e_traj_set_sha256"],
            "treatment_row_sha256": {
                treatment: _sha256_json(pool["treatment_rows"][treatment])
                for treatment in TREATMENTS
            },
            "mixture_sha256": _sha256_json(pool["mixture_strata"]),
        }
    )
    if pool["pool_id"] != expected_pool_id:
        raise TrainingContractError("pool_id is not canonical")


def _load_rows(
    path: Path, *, forbidden_canaries: tuple[str, ...]
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    row_ids: set[str] = set()
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as error:
        raise TrainingContractError(f"cannot read release view: {path}") from error
    for line_number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as error:
            raise TrainingContractError(
                f"invalid release view JSON line {line_number}: {path}"
            ) from error
        if not isinstance(row, dict):
            raise TrainingContractError(f"release view row must be an object: {path}")
        validate_training_view_row_v2(row, forbidden_canaries=forbidden_canaries)
        if row["row_id"] in row_ids:
            raise TrainingContractError(f"duplicate release row_id: {row['row_id']}")
        row_ids.add(row["row_id"])
        rows.append(row)
    return rows


def _row_ref(
    row: dict[str, Any], sidecar: dict[str, Any], certificate: dict[str, Any]
) -> dict[str, Any]:
    ref = {
        "source_episode_id": row["source_episode_id"],
        "treatment": row["treatment"],
        "row_id": row["row_id"],
        "row_sha256": row["row_sha256"],
        "sidecar_artifact_sha256": sidecar["artifact_sha256"],
        "eligibility_artifact_sha256": certificate["artifact_sha256"],
    }
    if "transition_evidence_sha256" in sidecar:
        ref["transition_evidence_sha256"] = sidecar["transition_evidence_sha256"]
    return ref


def _validate_registered(key: str, artifact: dict[str, Any]) -> None:
    schema = load_registered_schema(key)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(artifact),
        key=lambda error: (tuple(str(part) for part in error.absolute_path), error.message),
    )
    if errors:
        rendered = "; ".join(error.message for error in errors)
        raise TrainingContractError(f"invalid registered {key}: {rendered}")


def _validate_self_hash(artifact: dict[str, Any], field: str, label: str) -> None:
    expected = _sha256_json({key: value for key, value in artifact.items() if key != field})
    if artifact[field] != expected:
        raise TrainingContractError(f"{label} {field} mismatch")


def _validate_authorization_expectation(
    authorization: PromotionAuthorizationExpectation,
) -> None:
    for field, value in (
        ("campaign_freeze_sha256", authorization.campaign_freeze_sha256),
        ("training_plan_sha256", authorization.training_plan_sha256),
        ("promotion_record_sha256", authorization.promotion_record_sha256),
    ):
        if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
            raise TrainingContractError(f"invalid expected promotion {field}")


def _validate_leakage_policy_expectation(
    policy: TrainingLeakagePolicyExpectation,
) -> None:
    expected = TrainingLeakagePolicyExpectation.create(
        policy_id=policy.policy_id,
        forbidden_canaries=policy.forbidden_canaries,
    )
    if policy != expected:
        raise TrainingContractError("release leakage policy expectation mismatch")


def _validate_file_semantics(record: dict[str, Any]) -> None:
    path = record["path"]
    if path.startswith("views/"):
        expected = ("training_view", "model_visible")
    elif path == POOL_PATH:
        expected = ("training_pool_manifest", "release_internal")
    elif path.startswith("internal/sidecars/"):
        expected = ("eligibility_sidecar", "release_internal")
    elif path.startswith("internal/eligibility/"):
        expected = ("eligibility_certificate", "release_internal")
    else:
        raise TrainingContractError(f"unsupported release file path: {path}")
    if (record["role"], record["visibility_class"]) != expected:
        raise TrainingContractError(f"release file role/visibility mismatch: {path}")


def _release_path(root: Path, relative_path: str) -> Path:
    target = (root / Path(*relative_path.split("/"))).resolve()
    if target != root and root not in target.parents:
        raise TrainingContractError(f"release path escapes root: {relative_path}")
    return target


def _load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise TrainingContractError(f"cannot read release JSON object: {path}") from error
    if not isinstance(value, dict):
        raise TrainingContractError(f"release JSON must be an object: {path}")
    return value


def _sha256_json(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return _sha256_bytes(raw.encode("utf-8"))


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()
