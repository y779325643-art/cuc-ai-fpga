"""Bounded development probe for provider decoding-seed repeatability."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

from sr2fpga_agent.artifact_store import ArtifactStore
from sr2fpga_agent.provider_seed_capability import (
    ProviderSeedProbeObservation,
    write_development_provider_seed_capability,
)
from sr2fpga_agent.providers import OpenAICompatibleClient, OpenAICompatibleConfig
from sr2fpga_agent.runner import _load_env_file


_PROBE_PROMPT = "Return a strict JSON object with status set to ok."
_PROBE_TEMPERATURE = 0.1
_SELF_REVIEW_VERSION = "provider-seed-probe-cli-self-review-v1"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Run a bounded development-only provider seed repeatability probe."
    )
    parser.add_argument("--artifact-root", required=True, type=Path)
    parser.add_argument("--model", required=True)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--api-key-env", required=True)
    parser.add_argument("--env-file", type=Path, default=Path(""))
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--max-tokens", type=int, default=32)
    parser.add_argument(
        "--documentation-status",
        choices=(
            "not_checked",
            "seed_undocumented",
            "unsupported_documented",
            "best_effort_documented",
            "deterministic_documented",
        ),
        default="not_checked",
    )
    parser.add_argument("--documentation-snapshot", type=Path)
    parser.add_argument("--documentation-source-url")
    args = parser.parse_args(argv)

    if args.seed < 0:
        raise SystemExit("--seed must be >= 0")
    if args.repetitions < 2:
        raise SystemExit("--repetitions must be >= 2")
    if args.max_tokens < 1:
        raise SystemExit("--max-tokens must be >= 1")
    if args.documentation_status == "not_checked":
        if (
            args.documentation_snapshot is not None
            or args.documentation_source_url is not None
        ):
            raise SystemExit(
                "documentation snapshot and source URL require a checked documentation status"
            )
        documentation_snapshot_sha256 = None
        documentation_source_url_sha256 = None
        documentation_review = None
    else:
        if args.documentation_snapshot is None:
            raise SystemExit(
                "--documentation-snapshot is required for a checked documentation status"
            )
        if not isinstance(args.documentation_source_url, str) or not args.documentation_source_url.strip():
            raise SystemExit(
                "--documentation-source-url is required for a checked documentation status"
            )
        try:
            documentation_snapshot_sha256 = hashlib.sha256(
                args.documentation_snapshot.read_bytes()
            ).hexdigest()
        except OSError as exc:
            raise SystemExit(
                "documentation snapshot is unreadable: "
                + str(args.documentation_snapshot)
            ) from exc
        documentation_source_url_sha256 = hashlib.sha256(
            args.documentation_source_url.strip().encode("utf-8")
        ).hexdigest()
        documentation_review = {
            "review_type": "self_reviewed_development",
            "reviewer_provenance_sha256": _sha256_json(
                {
                    "review_version": _SELF_REVIEW_VERSION,
                    "documentation_status": args.documentation_status,
                    "documentation_snapshot_sha256": documentation_snapshot_sha256,
                    "documentation_source_url_sha256": documentation_source_url_sha256,
                }
            ),
        }
    _load_env_file(args.env_file)
    api_key = os.environ.get(args.api_key_env, "")
    if not api_key:
        raise SystemExit(f"{args.api_key_env} is not set")

    observations: list[ProviderSeedProbeObservation] = []
    client = None
    try:
        client = OpenAICompatibleClient(
            OpenAICompatibleConfig(
                api_key=api_key,
                model=args.model,
                base_url=args.base_url,
                timeout_seconds=30,
                max_tokens=args.max_tokens,
                transport_attempts=1,
                seed=args.seed,
            )
        )
        for _ in range(args.repetitions):
            try:
                output = client.chat(
                    [{"role": "user", "content": _PROBE_PROMPT}]
                )
                if not isinstance(output, str) or not output.strip():
                    raise ValueError("provider probe response was empty or non-text")
                usage, fingerprint = _consume_probe_context(client)
                encoded_output = output.encode("utf-8")
                observations.append(
                    ProviderSeedProbeObservation(
                        status="completed",
                        output_sha256=hashlib.sha256(encoded_output).hexdigest(),
                        system_fingerprint=fingerprint,
                        input_tokens=usage.get("input_tokens"),
                        output_tokens=usage.get("output_tokens"),
                        cached_tokens=usage.get("cached_tokens"),
                        output_size_bytes=len(encoded_output),
                    )
                )
            except Exception as exc:
                usage, fingerprint = _consume_probe_context_after_failure(client)
                observations.append(
                    ProviderSeedProbeObservation(
                        status="failed",
                        system_fingerprint=fingerprint,
                        input_tokens=usage.get("input_tokens"),
                        output_tokens=usage.get("output_tokens"),
                        cached_tokens=usage.get("cached_tokens"),
                        failure_category=_categorize_probe_exception(exc),
                    )
                )
                break
    except Exception as exc:
        if not observations:
            usage, fingerprint = _consume_probe_context_after_failure(client)
            observations.append(
                ProviderSeedProbeObservation(
                    status="failed",
                    system_fingerprint=fingerprint,
                    input_tokens=usage.get("input_tokens"),
                    output_tokens=usage.get("output_tokens"),
                    cached_tokens=usage.get("cached_tokens"),
                    failure_category=_categorize_probe_exception(exc),
                )
            )

    reference = write_development_provider_seed_capability(
        ArtifactStore(args.artifact_root),
        provider_adapter="openai_compatible",
        provider_model=args.model,
        gateway_base_url=args.base_url,
        protocol={
            "prompt_sha256": hashlib.sha256(
                _PROBE_PROMPT.encode("utf-8")
            ).hexdigest(),
            "seed": args.seed,
            "temperature": _PROBE_TEMPERATURE,
            "max_tokens": args.max_tokens,
            "repetitions": args.repetitions,
            "probe_implementation_sha256": hashlib.sha256(
                Path(__file__).read_bytes()
            ).hexdigest(),
        },
        documentation_status=args.documentation_status,
        documentation_snapshot_sha256=documentation_snapshot_sha256,
        documentation_source_url_sha256=documentation_source_url_sha256,
        documentation_review=documentation_review,
        observations=observations,
    )
    payload = json.loads(ArtifactStore(args.artifact_root).read_verified(reference))
    print(
        json.dumps(
            {
                "artifact_ref": reference.to_dict(),
                "probe_status": payload["probe_status"],
                "seed_control_classification": payload[
                    "seed_control_classification"
                ],
                "paired_confirmatory_eligible": payload[
                    "paired_confirmatory_eligible"
                ],
                "provider_token_usage_status": payload[
                    "provider_token_usage_status"
                ],
                "documentation_snapshot_sha256": payload[
                    "documentation_snapshot_sha256"
                ],
                "documentation_source_url_sha256": payload[
                    "documentation_source_url_sha256"
                ],
                "documentation_review_type": (
                    payload["documentation_review"]["review_type"]
                    if payload["documentation_review"] is not None
                    else None
                ),
                "failed_repetitions": payload["failed_repetitions"],
                "failure_categories": payload["failure_categories"],
                "input_tokens": payload["input_tokens"],
                "output_tokens": payload["output_tokens"],
            },
            sort_keys=True,
        )
    )


def _consume_probe_context(client) -> tuple[dict[str, int | None], str | None]:
    usage = client.consume_token_usage() or {}
    if not isinstance(usage, dict):
        raise ValueError("provider token usage was not an object")
    provenance = client.consume_response_provenance() or {}
    if not isinstance(provenance, dict):
        raise ValueError("provider response provenance was not an object")
    fingerprint = (
        provenance.get("provider_system_fingerprint")
        if provenance.get("system_fingerprint_status") == "reported"
        else None
    )
    if fingerprint is not None and (
        not isinstance(fingerprint, str) or not fingerprint.strip()
    ):
        raise ValueError("provider system fingerprint was invalid")
    return usage, fingerprint.strip() if isinstance(fingerprint, str) else None


def _consume_probe_context_after_failure(
    client,
) -> tuple[dict[str, int | None], str | None]:
    if client is None:
        return {}, None
    try:
        usage = client.consume_token_usage() or {}
    except Exception:
        usage = {}
    if not isinstance(usage, dict):
        usage = {}
    try:
        provenance = client.consume_response_provenance() or {}
    except Exception:
        provenance = {}
    fingerprint = (
        provenance.get("provider_system_fingerprint")
        if isinstance(provenance, dict)
        and provenance.get("system_fingerprint_status") == "reported"
        else None
    )
    if not isinstance(fingerprint, str) or not fingerprint.strip():
        fingerprint = None
    return usage, fingerprint.strip() if isinstance(fingerprint, str) else None


def _categorize_probe_exception(exc: Exception) -> str:
    if isinstance(exc, (ValueError, TypeError, KeyError, json.JSONDecodeError)):
        return "response_invalid"
    return _categorize_probe_failure(str(exc))


def _sha256_json(payload: object) -> str:
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _categorize_probe_failure(message: str) -> str:
    normalized = message.lower()
    if "http 401" in normalized:
        return "authentication"
    if "http 403" in normalized:
        return "authorization"
    if "quota" in normalized or "insufficient_quota" in normalized:
        return "quota"
    if "http 429" in normalized:
        return "rate_limit"
    if "seed" in normalized and any(
        marker in normalized
        for marker in ("unsupported", "not supported", "unknown", "unrecognized")
    ):
        return "seed_rejected"
    if "model" in normalized and any(
        marker in normalized
        for marker in ("not found", "does not exist", "not available", "unsupported")
    ):
        return "model_unavailable"
    if "timed out" in normalized or "timeout" in normalized:
        return "timeout"
    if any(marker in normalized for marker in ("invalid chat completion", "did not contain", "truncated")):
        return "response_invalid"
    if any(f"http {status}" in normalized for status in range(500, 600)):
        return "provider_error"
    if "request failed" in normalized or "url" in normalized:
        return "network"
    return "unknown"


if __name__ == "__main__":
    main()
