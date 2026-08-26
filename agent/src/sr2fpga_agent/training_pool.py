"""Evaluator-owned E_final/E_traj candidate pool assembly for CD8."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable, Mapping, Sequence

from sr2fpga_agent.contract_registry import ContractRegistry
from sr2fpga_agent.training_view_exporter import validate_training_view_export


TREATMENTS = ("M6U", "M6F", "M6T", "M6F_E_TRAJ")
TrainingViewExport = tuple[dict[str, Any], dict[str, Any], dict[str, Any]]


def build_training_pool_manifest(
    *,
    exports: Mapping[str, Sequence[TrainingViewExport]],
    family_by_episode: Mapping[str, str],
    forbidden_canaries: Iterable[str] = (),
) -> dict[str, Any]:
    """Build a pool only when matched treatment sets and evidence agree exactly."""

    if set(exports) != set(TREATMENTS):
        raise ValueError("training pool exports must contain exactly all treatments")
    indexed = {
        treatment: _index_exports(
            treatment, exports[treatment], forbidden_canaries=forbidden_canaries
        )
        for treatment in TREATMENTS
    }
    e_final = sorted(indexed["M6U"])
    if not e_final:
        raise ValueError("E_final must contain at least one eligible episode")
    if set(indexed["M6F"]) != set(e_final):
        raise ValueError("M6U and M6F episode IDs must match exactly")
    e_traj = sorted(indexed["M6T"])
    if set(indexed["M6F_E_TRAJ"]) != set(e_traj):
        raise ValueError("M6T and M6F_E_TRAJ episode IDs must match exactly")
    if not set(e_traj).issubset(e_final):
        raise ValueError("E_traj must be a subset of E_final")
    if set(family_by_episode) != set(e_final):
        raise ValueError("family assignments must cover E_final exactly")

    certificates: dict[str, dict[str, Any]] = {}
    for episode_id in e_final:
        m6u_certificate = indexed["M6U"][episode_id][2]
        m6f_certificate = indexed["M6F"][episode_id][2]
        if m6u_certificate["artifact_sha256"] != m6f_certificate["artifact_sha256"]:
            raise ValueError(f"M6U/M6F eligibility mismatch for {episode_id}")
        certificates[episode_id] = m6u_certificate
    for episode_id in e_traj:
        m6t = indexed["M6T"][episode_id]
        endpoint = indexed["M6F_E_TRAJ"][episode_id]
        if m6t[2]["artifact_sha256"] != certificates[episode_id]["artifact_sha256"]:
            raise ValueError(f"M6T eligibility mismatch for {episode_id}")
        if endpoint[2]["artifact_sha256"] != certificates[episode_id]["artifact_sha256"]:
            raise ValueError(f"M6F_E_TRAJ eligibility mismatch for {episode_id}")
        if (
            m6t[1]["transition_evidence_sha256"]
            != endpoint[1]["transition_evidence_sha256"]
        ):
            raise ValueError(f"transition evidence mismatch for {episode_id}")

    policy_tuples = {
        (
            certificate["policy_id"],
            certificate["policy_sha256"],
            certificate["training_split_id"],
        )
        for certificate in certificates.values()
    }
    if len(policy_tuples) != 1:
        raise ValueError("E_final certificates do not share one frozen policy and split")
    policy_id, policy_sha256, training_split_id = next(iter(policy_tuples))
    row_refs = {
        treatment: [
            _row_ref(*indexed[treatment][episode_id])
            for episode_id in sorted(indexed[treatment])
        ]
        for treatment in TREATMENTS
    }
    strata = _mixture_strata(e_final, certificates, family_by_episode)
    identity = _pool_identity(
        policy_sha256=policy_sha256,
        training_split_id=training_split_id,
        e_final_set_sha256=_set_sha256(e_final),
        e_traj_set_sha256=_set_sha256(e_traj),
        treatment_rows=row_refs,
        mixture_strata=strata,
    )
    without_hash = {
        "contract_version": "training-pool-manifest-v1",
        "visibility_class": "release_internal",
        "pool_id": f"pool-{_sha256(identity)}",
        "policy_id": policy_id,
        "policy_sha256": policy_sha256,
        "training_split_id": training_split_id,
        "e_final_episode_ids": e_final,
        "e_final_set_sha256": _set_sha256(e_final),
        "e_traj_episode_ids": e_traj,
        "e_traj_set_sha256": _set_sha256(e_traj),
        "treatment_rows": row_refs,
        "mixture_strata": strata,
    }
    manifest = {**without_hash, "artifact_sha256": _sha256(without_hash)}
    validate_training_pool_manifest(manifest)
    validate_training_pool_exports(
        manifest, exports, forbidden_canaries=forbidden_canaries
    )
    return manifest


def validate_training_pool_manifest(manifest: dict[str, Any]) -> None:
    errors = ContractRegistry().load_schema("training_pool_manifest").validate(manifest)
    if errors:
        raise ValueError("invalid training pool manifest: " + "; ".join(errors))
    expected_artifact = _sha256(
        {key: value for key, value in manifest.items() if key != "artifact_sha256"}
    )
    if manifest["artifact_sha256"] != expected_artifact:
        raise ValueError("training pool artifact_sha256 mismatch")
    e_final = manifest["e_final_episode_ids"]
    e_traj = manifest["e_traj_episode_ids"]
    if e_final != sorted(e_final) or e_traj != sorted(e_traj):
        raise ValueError("training pool episode IDs must be canonically sorted")
    if manifest["e_final_set_sha256"] != _set_sha256(e_final):
        raise ValueError("training pool E_final set hash mismatch")
    if manifest["e_traj_set_sha256"] != _set_sha256(e_traj):
        raise ValueError("training pool E_traj set hash mismatch")
    if not set(e_traj).issubset(e_final):
        raise ValueError("training pool E_traj is not a subset of E_final")
    expected_sets = {
        "M6U": set(e_final),
        "M6F": set(e_final),
        "M6T": set(e_traj),
        "M6F_E_TRAJ": set(e_traj),
    }
    seen_row_ids: set[str] = set()
    for treatment in TREATMENTS:
        refs = manifest["treatment_rows"][treatment]
        episode_ids = [ref["source_episode_id"] for ref in refs]
        if episode_ids != sorted(episode_ids) or len(episode_ids) != len(set(episode_ids)):
            raise ValueError(f"training pool {treatment} row refs are not canonical")
        if set(episode_ids) != expected_sets[treatment]:
            raise ValueError(f"training pool {treatment} episode set mismatch")
        if any(ref["treatment"] != treatment for ref in refs):
            raise ValueError(f"training pool {treatment} contains a wrong treatment ref")
        for ref in refs:
            if ref["row_id"] in seen_row_ids:
                raise ValueError("training pool contains duplicate row_id")
            seen_row_ids.add(ref["row_id"])
    _validate_mixture(manifest["mixture_strata"], e_final)
    _validate_transition_pairs(manifest)
    expected_pool_id = "pool-" + _sha256(
        _pool_identity(
            policy_sha256=manifest["policy_sha256"],
            training_split_id=manifest["training_split_id"],
            e_final_set_sha256=manifest["e_final_set_sha256"],
            e_traj_set_sha256=manifest["e_traj_set_sha256"],
            treatment_rows=manifest["treatment_rows"],
            mixture_strata=manifest["mixture_strata"],
        )
    )
    if manifest["pool_id"] != expected_pool_id:
        raise ValueError("training pool pool_id is not canonical")


def validate_training_pool_exports(
    manifest: dict[str, Any],
    exports: Mapping[str, Sequence[TrainingViewExport]],
    *,
    forbidden_canaries: Iterable[str] = (),
) -> None:
    """Reconcile every manifest ref against the complete candidate artifacts."""

    validate_training_pool_manifest(manifest)
    if set(exports) != set(TREATMENTS):
        raise ValueError("training pool exports must contain exactly all treatments")
    all_indexed = {
        treatment: _index_exports(
            treatment, exports[treatment], forbidden_canaries=forbidden_canaries
        )
        for treatment in TREATMENTS
    }
    for treatment in TREATMENTS:
        indexed = all_indexed[treatment]
        refs = {
            ref["source_episode_id"]: ref
            for ref in manifest["treatment_rows"][treatment]
        }
        if set(indexed) != set(refs):
            raise ValueError(f"training pool {treatment} artifact set mismatch")
        for episode_id, (row, sidecar, certificate) in indexed.items():
            if refs[episode_id] != _row_ref(row, sidecar, certificate):
                raise ValueError(
                    f"training pool {treatment} artifact binding mismatch for {episode_id}"
                )
    certificates = {
        episode_id: export[2]
        for episode_id, export in all_indexed["M6U"].items()
    }
    for episode_id, certificate in certificates.items():
        expected_certificate = certificate["artifact_sha256"]
        if all_indexed["M6F"][episode_id][2]["artifact_sha256"] != expected_certificate:
            raise ValueError(f"M6U/M6F eligibility mismatch for {episode_id}")
        if episode_id in all_indexed["M6T"]:
            if (
                all_indexed["M6T"][episode_id][2]["artifact_sha256"]
                != expected_certificate
                or all_indexed["M6F_E_TRAJ"][episode_id][2]["artifact_sha256"]
                != expected_certificate
            ):
                raise ValueError(f"E_traj eligibility mismatch for {episode_id}")
    policy_tuples = {
        (
            certificate["policy_id"],
            certificate["policy_sha256"],
            certificate["training_split_id"],
        )
        for certificate in certificates.values()
    }
    expected_policy = (
        manifest["policy_id"],
        manifest["policy_sha256"],
        manifest["training_split_id"],
    )
    if policy_tuples != {expected_policy}:
        raise ValueError("training pool policy does not match eligibility certificates")
    family_by_episode = _family_assignments(manifest["mixture_strata"])
    expected_strata = _mixture_strata(
        manifest["e_final_episode_ids"], certificates, family_by_episode
    )
    if manifest["mixture_strata"] != expected_strata:
        raise ValueError("training pool mixture does not match eligibility certificates")


def _index_exports(
    treatment: str,
    exports: Sequence[TrainingViewExport],
    *,
    forbidden_canaries: Iterable[str] = (),
) -> dict[str, TrainingViewExport]:
    indexed: dict[str, TrainingViewExport] = {}
    for row, sidecar, certificate in exports:
        validate_training_view_export(
            row,
            sidecar,
            certificate,
            forbidden_canaries=forbidden_canaries,
        )
        if row["treatment"] != treatment:
            raise ValueError(f"{treatment} pool contains {row['treatment']} row")
        episode_id = row["source_episode_id"]
        if episode_id in indexed:
            raise ValueError(f"duplicate {treatment} row for episode {episode_id}")
        indexed[episode_id] = (row, sidecar, certificate)
    return indexed


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


def _mixture_strata(
    episode_ids: list[str],
    certificates: Mapping[str, dict[str, Any]],
    family_by_episode: Mapping[str, str],
) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str], list[str]] = {}
    for episode_id in episode_ids:
        family = family_by_episode[episode_id]
        if not isinstance(family, str) or not family:
            raise ValueError(f"invalid family assignment for {episode_id}")
        certificate = certificates[episode_id]
        key = (family, certificate["source_class"], certificate["failure_origin"])
        groups.setdefault(key, []).append(episode_id)
    return [
        {
            "family_id": family,
            "source_class": source_class,
            "failure_origin": failure_origin,
            "episode_ids": sorted(ids),
            "episode_count": len(ids),
        }
        for (family, source_class, failure_origin), ids in sorted(groups.items())
    ]


def _validate_mixture(strata: list[dict[str, Any]], e_final: list[str]) -> None:
    covered: list[str] = []
    keys: list[tuple[str, str, str]] = []
    for stratum in strata:
        ids = stratum["episode_ids"]
        if ids != sorted(ids) or stratum["episode_count"] != len(ids):
            raise ValueError("training pool mixture stratum is not canonical")
        covered.extend(ids)
        keys.append(
            (
                stratum["family_id"],
                stratum["source_class"],
                stratum["failure_origin"],
            )
        )
    if keys != sorted(keys) or len(keys) != len(set(keys)):
        raise ValueError("training pool mixture strata are not canonical")
    if sorted(covered) != e_final or len(covered) != len(set(covered)):
        raise ValueError("training pool mixture does not partition E_final")


def _validate_transition_pairs(manifest: dict[str, Any]) -> None:
    m6t = {
        ref["source_episode_id"]: ref["transition_evidence_sha256"]
        for ref in manifest["treatment_rows"]["M6T"]
    }
    endpoints = {
        ref["source_episode_id"]: ref["transition_evidence_sha256"]
        for ref in manifest["treatment_rows"]["M6F_E_TRAJ"]
    }
    if m6t != endpoints:
        raise ValueError("training pool transition evidence pairs do not match")


def _family_assignments(strata: Sequence[dict[str, Any]]) -> dict[str, str]:
    return {
        episode_id: stratum["family_id"]
        for stratum in strata
        for episode_id in stratum["episode_ids"]
    }


def _pool_identity(
    *,
    policy_sha256: str,
    training_split_id: str,
    e_final_set_sha256: str,
    e_traj_set_sha256: str,
    treatment_rows: Mapping[str, list[dict[str, Any]]],
    mixture_strata: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "policy_sha256": policy_sha256,
        "training_split_id": training_split_id,
        "e_final_set_sha256": e_final_set_sha256,
        "e_traj_set_sha256": e_traj_set_sha256,
        "treatment_row_sha256": {
            treatment: _sha256(treatment_rows[treatment]) for treatment in TREATMENTS
        },
        "mixture_sha256": _sha256(mixture_strata),
    }


def _set_sha256(episode_ids: Sequence[str]) -> str:
    return _sha256(sorted(episode_ids))


def _sha256(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
