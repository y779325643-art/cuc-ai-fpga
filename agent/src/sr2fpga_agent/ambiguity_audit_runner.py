"""Independent evaluator-side runner for sealed Paper-1 ambiguity cases."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

from sr2fpga_agent.artifact_store import ArtifactStore
from sr2fpga_agent.ambiguity_events import (
    AmbiguityAuditEventInterceptor,
    write_ambiguity_audit_events,
)
from sr2fpga_agent.contract_registry import ContractRegistry
from sr2fpga_agent.models import PlatformProfile, ProjectRequest
from sr2fpga_agent.requirement_audit import (
    ClarificationAnswerBranch,
    RequirementAuditGold,
    build_requirement_audit_artifact,
    build_requirement_audit_case,
    validate_requirement_audit_artifact,
    write_requirement_audit_artifact,
)
from sr2fpga_agent.requirement_boundary import evaluate_requirement_boundary


AMBIGUITY_CASE_MANIFEST_VERSION = "ambiguity-case-manifest-v1"
CLARIFICATION_REPLAY_VERSION = "clarification-replay-v1"


def build_ambiguity_case_manifest(
    audit_run_id: str,
    cases: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build and validate one evaluator-owned sealed case manifest."""

    payload = {
        "contract_version": AMBIGUITY_CASE_MANIFEST_VERSION,
        "audit_run_id": audit_run_id,
        "visibility_class": "evaluator_only",
        "cases": cases,
    }
    manifest = {**payload, "manifest_sha256": _sha256(payload)}
    validate_ambiguity_case_manifest(manifest)
    return manifest


def load_ambiguity_case_manifest(path: Path | str) -> dict[str, Any]:
    manifest_path = Path(path)
    if not manifest_path.is_file():
        raise ValueError(f"ambiguity case manifest does not exist or is not a file: {manifest_path}")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"ambiguity case manifest is not readable JSON: {manifest_path}: {error}") from error
    if not isinstance(manifest, dict):
        raise ValueError("ambiguity case manifest must be a JSON object")
    validate_ambiguity_case_manifest(manifest)
    return manifest


def run_ambiguity_audit_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    """Execute Phase A only; no project method or generator is reachable here."""

    artifact, _ = run_ambiguity_audit_with_events(manifest)
    return artifact


def run_ambiguity_audit_with_events(
    manifest: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Execute Phase A and retain the evaluator-owned event authority."""

    validate_ambiguity_case_manifest(manifest)
    events = AmbiguityAuditEventInterceptor(
        audit_run_id=manifest["audit_run_id"],
        manifest_sha256=manifest["manifest_sha256"],
    )
    case_ids: set[str] = set()
    cases = []
    for sealed_case in manifest["cases"]:
        case_id = sealed_case["ambiguity_case_id"]
        if case_id in case_ids:
            raise ValueError(f"duplicate ambiguity_case_id: {case_id}")
        case_ids.add(case_id)
        events.phase_a_started(case_id)
        public = sealed_case["public_projection"]
        platform = PlatformProfile(**public["platform"])
        request = ProjectRequest(
            task_type="unclassified",
            width=public["width_bits"],
            project_name=case_id,
            description=public["requirement"],
        )
        private = sealed_case["evaluator_only"]
        branches = tuple(
            ClarificationAnswerBranch(
                branch_id=item["branch_id"],
                answer_facts=item["answer_facts"],
                expected_replay_disposition=item["expected_replay_disposition"],
            )
            for item in private.get("clarification_answer_branches", ())
        )
        case = build_requirement_audit_case(
                request,
                platform,
                base_requirement_cluster_id=sealed_case["base_requirement_cluster_id"],
                ambiguity_case_id=case_id,
                gold=RequirementAuditGold(
                    disposition=private["disposition"],
                    reason_ids=tuple(private["reason_ids"]),
                    fact_ids=tuple(private["fact_ids"]),
                    capability_ids=tuple(private["capability_ids"]),
                    clarification_answer_branches=branches,
                ),
            )
        cases.append(case)
        result = case["boundary_result"]
        events.phase_a_completed(
            case_id,
            execution_status=result["execution_status"],
            predicted_disposition=result["predicted_disposition"],
            counters=result["counters"],
            infrastructure_status="available",
        )
    phase_a = build_requirement_audit_artifact(manifest["audit_run_id"], cases)
    return phase_a, events.build_artifact(
        phase_a_audit_sha256=phase_a["audit_sha256"]
    )


class ClarificationReplayAuthority:
    """Evaluator-owned, persistent exactly-once Phase B authority."""

    def __init__(self, evaluator_store: ArtifactStore) -> None:
        self._store = evaluator_store

    def run(
        self,
        manifest: dict[str, Any],
        phase_a_artifact: dict[str, Any],
    ) -> dict[str, Any]:
        validate_ambiguity_case_manifest(manifest)
        validate_requirement_audit_artifact(phase_a_artifact)
        if manifest["audit_run_id"] != phase_a_artifact["audit_run_id"]:
            raise ValueError("Phase A audit_run_id does not match the sealed manifest")
        phase_cases = {
            item["ambiguity_case_id"]: item for item in phase_a_artifact["cases"]
        }
        replays = []
        for sealed_case in manifest["cases"]:
            branches = sealed_case["evaluator_only"].get(
                "clarification_answer_branches", ()
            )
            if not branches:
                continue
            case_id = sealed_case["ambiguity_case_id"]
            phase_case = phase_cases.get(case_id)
            if phase_case is None:
                raise ValueError(f"Phase A artifact is missing ambiguity case: {case_id}")
            self._verify_phase_a_eligibility(sealed_case, phase_case)
            branch = branches[0]
            replays.append(self._run_one(manifest, sealed_case, phase_case, branch))
        payload = {
            "contract_version": CLARIFICATION_REPLAY_VERSION,
            "audit_run_id": manifest["audit_run_id"],
            "manifest_sha256": manifest["manifest_sha256"],
            "phase_a_audit_sha256": phase_a_artifact["audit_sha256"],
            "visibility_class": "evaluator_only",
            "replays": replays,
        }
        artifact = {**payload, "artifact_sha256": _sha256(payload)}
        validate_clarification_replay_artifact(artifact)
        return artifact

    def _verify_phase_a_eligibility(
        self,
        sealed_case: dict[str, Any],
        phase_case: dict[str, Any],
    ) -> None:
        result = phase_case["boundary_result"]
        if result["execution_status"] != "completed":
            raise ValueError("clarification replay requires a completed Phase A result")
        if result["predicted_disposition"] != "needs_clarification":
            raise ValueError(
                "clarification replay requires Phase A needs_clarification"
            )
        public = sealed_case["public_projection"]
        phase_public = phase_case["generation_visible_projection"]
        platform = PlatformProfile(**public["platform"])
        if (
            phase_public["public_requirement"] != public["requirement"]
            or phase_public["width_bits"] != public["width_bits"]
            or phase_public["platform_profile_id"] != platform.name
            or phase_public["platform_profile_sha256"] != _sha256(asdict(platform))
        ):
            raise ValueError("Phase A public projection does not match the sealed case")

    def _run_one(
        self,
        manifest: dict[str, Any],
        sealed_case: dict[str, Any],
        phase_case: dict[str, Any],
        branch: dict[str, Any],
    ) -> dict[str, Any]:
        requested_fact_ids = set(phase_case["boundary_result"]["fact_ids"])
        answered_fact_ids = set(branch["answer_facts"])
        if answered_fact_ids != requested_fact_ids:
            raise ValueError(
                "clarification answer facts must exactly match Phase A requested fact IDs"
            )
        phase_a_case_sha256 = _sha256(phase_case)
        answer_sha256 = _sha256(branch["answer_facts"])
        lineage = {
            "manifest_sha256": manifest["manifest_sha256"],
            "phase_a_case_sha256": phase_a_case_sha256,
            "ambiguity_case_id": sealed_case["ambiguity_case_id"],
            "branch_id": branch["branch_id"],
            "answer_sha256": answer_sha256,
        }
        lineage_sha256 = _sha256(lineage)
        marker = self._store.consume_once(
            f"clarification-{lineage_sha256}", lineage_sha256
        )
        public = sealed_case["public_projection"]
        request = ProjectRequest(
            task_type="unclassified",
            width=public["width_bits"],
            project_name=sealed_case["ambiguity_case_id"],
            description=public["requirement"],
        )
        started = time.monotonic()
        decision = evaluate_requirement_boundary(
            request,
            PlatformProfile(**public["platform"]),
            clarification_facts=branch["answer_facts"],
        )
        elapsed_ms = (time.monotonic() - started) * 1000.0
        expected = branch["expected_replay_disposition"]
        return {
            "base_requirement_cluster_id": sealed_case[
                "base_requirement_cluster_id"
            ],
            "ambiguity_case_id": sealed_case["ambiguity_case_id"],
            "branch_id": branch["branch_id"],
            "phase_a_case_sha256": phase_a_case_sha256,
            "answer_sha256": answer_sha256,
            "lineage_sha256": lineage_sha256,
            "one_shot_marker_sha256": marker.sha256,
            "replayed_fact_ids": sorted(answered_fact_ids),
            "expected_replay_disposition": expected,
            "actual_replay_disposition": decision.disposition,
            "closure": decision.disposition == expected,
            "generation_boundary_crossed": False,
            "counters": {
                "model_calls": 0,
                "tool_calls": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "cached_tokens": 0,
                "wall_time_ms": elapsed_ms,
            },
        }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Run the evaluator-owned SR2FPGA requirement ambiguity audit."
    )
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--replay-output", type=Path)
    parser.add_argument("--evaluator-store", type=Path)
    parser.add_argument("--outcome-output", type=Path)
    parser.add_argument("--witness-artifact", type=Path)
    parser.add_argument("--events-output", type=Path)
    parser.add_argument("--observation-id", default="deterministic")
    args = parser.parse_args(argv)
    if (args.replay_output is None) != (args.evaluator_store is None):
        parser.error("--replay-output and --evaluator-store must be provided together")
    if args.outcome_output is not None and args.replay_output is None:
        parser.error("--outcome-output requires Phase B replay output and evaluator store")
    if args.outcome_output is not None and args.witness_artifact is None:
        parser.error("--outcome-output requires an evaluator-owned witness artifact")
    if args.outcome_output is not None and args.events_output is None:
        parser.error("--outcome-output requires an evaluator-owned event log")
    manifest = load_ambiguity_case_manifest(args.manifest)
    artifact, events = run_ambiguity_audit_with_events(manifest)
    write_requirement_audit_artifact(args.output, artifact)
    if args.events_output is not None:
        write_ambiguity_audit_events(args.events_output, events)
    if args.replay_output is not None:
        replay = ClarificationReplayAuthority(ArtifactStore(args.evaluator_store)).run(
            manifest, artifact
        )
        _write_replay_artifact(args.replay_output, replay)
        if args.outcome_output is not None:
            from sr2fpga_agent.ambiguity_outcome import (
                AmbiguityAuditObservation,
                build_ambiguity_outcome,
                write_ambiguity_outcome,
            )
            from sr2fpga_agent.ambiguity_witness import (
                load_ambiguity_witness_artifact,
                validate_witness_manifest_binding,
            )

            witness = load_ambiguity_witness_artifact(args.witness_artifact)
            validate_witness_manifest_binding(manifest, witness)
            outcome = build_ambiguity_outcome(
                manifest,
                witness,
                [AmbiguityAuditObservation(args.observation_id, artifact, events, replay)],
            )
            write_ambiguity_outcome(args.outcome_output, outcome)


def validate_ambiguity_case_manifest(manifest: dict[str, Any]) -> None:
    contract = ContractRegistry().load_schema("ambiguity_case_manifest")
    errors = contract.validate(manifest)
    if errors:
        raise ValueError("invalid ambiguity case manifest: " + "; ".join(errors))
    payload = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    if manifest["manifest_sha256"] != _sha256(payload):
        raise ValueError("ambiguity case manifest SHA-256 does not match its canonical payload")


def validate_clarification_replay_artifact(artifact: dict[str, Any]) -> None:
    contract = ContractRegistry().load_schema("clarification_replay")
    errors = contract.validate(artifact)
    if errors:
        raise ValueError("invalid clarification replay artifact: " + "; ".join(errors))
    payload = {key: value for key, value in artifact.items() if key != "artifact_sha256"}
    if artifact["artifact_sha256"] != _sha256(payload):
        raise ValueError("clarification replay SHA-256 does not match its canonical payload")


def _write_replay_artifact(path: Path, artifact: dict[str, Any]) -> None:
    validate_clarification_replay_artifact(artifact)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _sha256(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


if __name__ == "__main__":
    main()
