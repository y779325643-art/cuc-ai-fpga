"""Per-episode model-call budget and first-class call events."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable

from sr2fpga_agent.block_cost_accounting import ModelCostLedger
from sr2fpga_agent.providers import ModelOutputTruncated, ModelOutputEmpty


class ModelCallBudgetExceeded(RuntimeError):
    pass


@dataclass
class ModelCallBudget:
    max_calls: int
    event_sink: Callable[[dict[str, Any]], None] | None = None
    attempt_cost_ledger: ModelCostLedger | None = None
    attempt_cost_ledger_provider: Callable[[], ModelCostLedger | None] | None = None
    max_parser_schema_retries: int = 0
    standalone_max_calls: int | None = None
    budget_scope: str = "standalone"
    calls_used: int = 0
    failed_calls: int = 0
    parser_schema_retries_used: int = 0
    call_records: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.max_calls < 0:
            raise ValueError("model-call budget must be non-negative")
        if self.max_parser_schema_retries < 0:
            raise ValueError("parser/schema retry budget must be non-negative")
        if (
            self.standalone_max_calls is not None
            and self.standalone_max_calls < self.max_calls
        ):
            raise ValueError("standalone model-call ceiling cannot be below runtime ceiling")
        if self.budget_scope not in {"standalone", "paired_block_exclusive"}:
            raise ValueError("unknown model-call budget scope")
        if (self.standalone_max_calls is None) != (self.budget_scope == "standalone"):
            raise ValueError(
                "paired-block exclusive budgets require a standalone model-call ceiling"
            )
        if (
            self.attempt_cost_ledger is not None
            and self.attempt_cost_ledger_provider is not None
        ):
            raise ValueError("configure one attempt-cost ledger source")

    def client(self, client: Any, stage: str) -> "BudgetedModelClient":
        return BudgetedModelClient(client, self, stage)

    def reserve(self, stage: str, operation: str, input_chars: int) -> tuple[int, float]:
        if self.calls_used >= self.max_calls:
            ledger = self._cost_ledger()
            if ledger is not None:
                ledger.record_budget_exhausted(
                    "logical_model_calls",
                    1,
                    stage=stage,
                    visibility_class="accounting",
                    limit=self.max_calls,
                    used_after=self.calls_used + 1,
                )
            raise ModelCallBudgetExceeded(
                f"model-call budget exhausted before {stage}: "
                f"used={self.calls_used}, max={self.max_calls}"
            )
        call_id = self.calls_used
        self.calls_used += 1
        started = time.monotonic()
        ledger = self._cost_ledger()
        if ledger is not None:
            ledger.reserve(
                "logical_model_calls",
                1,
                stage=stage,
                visibility_class="accounting",
                limit=self.max_calls,
                used_after=self.calls_used,
            )
        self._emit(
            {
                "event": "model_call_started",
                "call_id": call_id,
                "stage": stage,
                "operation": operation,
                "input_chars": input_chars,
                "model_calls_used": self.calls_used,
                "model_calls_max": self.max_calls,
            }
        )
        return call_id, started

    def finish(
        self,
        call_id: int,
        stage: str,
        operation: str,
        started: float,
        *,
        output_chars: int = 0,
        error: Exception | None = None,
        provider_transport_attempts: int | None = None,
        provider_token_usage: dict[str, int | None] | None = None,
        provider_response_provenance: dict[str, Any] | None = None,
        provider_response_details: dict[str, Any] | None = None,
    ) -> None:
        token_usage = _normalized_token_usage(provider_token_usage)
        response_provenance = _normalized_response_provenance(
            provider_response_provenance
        )
        record: dict[str, Any] = {
            "call_id": call_id,
            "stage": stage,
            "operation": operation,
            "status": "failed" if error is not None else "completed",
            "duration_seconds": time.monotonic() - started,
            "output_chars": output_chars,
            "token_accounting": (
                "provider_reported"
                if all(token_usage[axis] is not None for axis in token_usage)
                else "partial_or_unavailable_provider_response"
            ),
            **token_usage,
            "provider_transport_attempts": provider_transport_attempts,
            "provider_response_provenance": response_provenance,
        }
        if error is not None:
            self.failed_calls += 1
            record["error_type"] = type(error).__name__
            record["error"] = "provider_call_failed"
            if isinstance(error, (ModelOutputTruncated, ModelOutputEmpty)):
                record["error"] = error.failure_category
        if provider_response_details is not None:
            record["provider_response_details"] = dict(provider_response_details)
        self.call_records.append(record)
        ledger = self._cost_ledger()
        if ledger is not None:
            token_reason = "provider_token_usage_unavailable"
            transport_reason = "provider_transport_attempt_count_unavailable"
            unavailable_axes = {
                axis: token_reason for axis, value in token_usage.items() if value is None
            }
            if provider_transport_attempts is None:
                unavailable_axes["provider_transport_attempts"] = transport_reason
            ledger.record_cost(
                stage=stage,
                visibility_class="accounting",
                status="failed" if error is not None else "completed",
                duration_seconds=record["duration_seconds"],
                cost_delta={
                    **token_usage,
                    "provider_transport_attempts": provider_transport_attempts,
                },
                unavailable_axes=unavailable_axes,
            )
        self._emit(
            {
                "event": "model_call_failed" if error is not None else "model_call_finished",
                **record,
            }
        )

    def reserve_parser_schema_retry(self, stage: str, operation: str) -> None:
        used_after = self.parser_schema_retries_used + 1
        ledger = self._cost_ledger()
        if used_after > self.max_parser_schema_retries:
            if ledger is not None:
                ledger.record_budget_exhausted(
                    "planner_parser_schema_retries",
                    1,
                    stage=stage,
                    visibility_class="accounting",
                    limit=self.max_parser_schema_retries,
                    used_after=used_after,
                )
            raise ModelCallBudgetExceeded(
                f"parser/schema retry budget exhausted before {stage}: "
                f"used={self.parser_schema_retries_used}, "
                f"max={self.max_parser_schema_retries}"
            )
        self.parser_schema_retries_used = used_after
        if ledger is not None:
            ledger.reserve(
                "planner_parser_schema_retries",
                1,
                stage=stage,
                visibility_class="accounting",
                limit=self.max_parser_schema_retries,
                used_after=used_after,
            )
        self._emit(
            {
                "event": "parser_schema_retry_reserved",
                "stage": stage,
                "operation": operation,
                "parser_schema_retries_used": used_after,
                "parser_schema_retries_max": self.max_parser_schema_retries,
            }
        )

    def summary(self) -> dict[str, Any]:
        token_totals: dict[str, int | None] = {}
        for axis in ("input_tokens", "output_tokens", "cached_tokens"):
            values = [record.get(axis) for record in self.call_records]
            token_totals[axis] = (
                sum(values)
                if values and all(isinstance(value, int) for value in values)
                else None
            )
        if token_totals and all(value is not None for value in token_totals.values()):
            token_accounting = "provider_reported"
        elif self.call_records:
            token_accounting = "partial_or_unavailable_provider_response"
        else:
            token_accounting = "unavailable_provider_response"
        summary = {
            "max_model_calls": self.max_calls,
            "model_calls_used": self.calls_used,
            "model_calls_failed": self.failed_calls,
            "remaining_model_calls": self.max_calls - self.calls_used,
            "max_parser_schema_retries": self.max_parser_schema_retries,
            "parser_schema_retries_used": self.parser_schema_retries_used,
            "remaining_parser_schema_retries": (
                self.max_parser_schema_retries - self.parser_schema_retries_used
            ),
            "token_accounting": token_accounting,
            **token_totals,
            "calls": list(self.call_records),
        }
        if self.standalone_max_calls is not None:
            summary["standalone_max_model_calls"] = self.standalone_max_calls
            summary["model_call_budget_scope"] = self.budget_scope
        return summary

    def _emit(self, payload: dict[str, Any]) -> None:
        if self.event_sink is not None:
            self.event_sink(payload)

    def _cost_ledger(self) -> ModelCostLedger | None:
        if self.attempt_cost_ledger_provider is not None:
            return self.attempt_cost_ledger_provider()
        return self.attempt_cost_ledger


class BudgetedModelClient:
    """Delegate chat operations while charging one model call per invocation."""

    def __init__(self, client: Any, budget: ModelCallBudget, stage: str) -> None:
        self._client = client
        self._budget = budget
        self._stage = stage

    @property
    def config(self) -> Any:
        return getattr(self._client, "config", None)

    def for_stage(self, stage: str) -> "BudgetedModelClient":
        return BudgetedModelClient(self._client, self._budget, stage)

    def with_output_format(self, response_format: str) -> "BudgetedModelClient":
        factory = getattr(self._client, "with_output_format", None)
        client = factory(response_format) if callable(factory) else self._client
        return BudgetedModelClient(client, self._budget, self._stage)

    def chat(self, messages: list[dict[str, str]]) -> str:
        return self._call("chat", messages)

    def stream_chat(self, messages: list[dict[str, str]]) -> str:
        return self._call("stream_chat", messages)

    def record_parser_schema_retry(self, operation: str) -> None:
        self._budget.reserve_parser_schema_retry(self._stage, operation)

    def _call(self, operation: str, messages: list[dict[str, str]]) -> str:
        input_chars = sum(len(str(item.get("content", ""))) for item in messages)
        call_id, started = self._budget.reserve(self._stage, operation, input_chars)
        try:
            result = getattr(self._client, operation)(messages)
        except Exception as exc:
            self._budget.finish(
                call_id,
                self._stage,
                operation,
                started,
                error=exc,
                provider_transport_attempts=self._consume_transport_attempt_count(),
                provider_token_usage=self._consume_token_usage(),
                provider_response_provenance=self._consume_response_provenance(),
                provider_response_details=self._consume_response_details(),
            )
            raise
        self._budget.finish(
            call_id,
            self._stage,
            operation,
            started,
            output_chars=len(result),
            provider_transport_attempts=self._consume_transport_attempt_count(),
            provider_token_usage=self._consume_token_usage(),
            provider_response_provenance=self._consume_response_provenance(),
            provider_response_details=self._consume_response_details(),
        )
        return result

    def _consume_transport_attempt_count(self) -> int | None:
        consumer = getattr(self._client, "consume_transport_attempt_count", None)
        if not callable(consumer):
            return None
        count = consumer()
        if isinstance(count, bool) or not isinstance(count, int) or count < 1:
            return None
        return count

    def _consume_token_usage(self) -> dict[str, int | None] | None:
        consumer = getattr(self._client, "consume_token_usage", None)
        return consumer() if callable(consumer) else None

    def _consume_response_provenance(self) -> dict[str, Any] | None:
        consumer = getattr(self._client, "consume_response_provenance", None)
        return consumer() if callable(consumer) else None

    def _consume_response_details(self) -> dict[str, Any] | None:
        consumer = getattr(self._client, "consume_response_details", None)
        return consumer() if callable(consumer) else None


def client_for_stage(client: Any, stage: str) -> Any:
    factory = getattr(client, "for_stage", None)
    return factory(stage) if callable(factory) else client


def record_parser_schema_retry(client: Any, operation: str) -> None:
    recorder = getattr(client, "record_parser_schema_retry", None)
    if callable(recorder):
        recorder(operation)


def _normalized_token_usage(
    usage: dict[str, int | None] | None,
) -> dict[str, int | None]:
    normalized: dict[str, int | None] = {}
    for axis in ("input_tokens", "output_tokens", "cached_tokens"):
        value = usage.get(axis) if isinstance(usage, dict) else None
        normalized[axis] = (
            value
            if isinstance(value, int) and not isinstance(value, bool) and value >= 0
            else None
        )
    return normalized


def _normalized_response_provenance(
    provenance: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if not isinstance(provenance, dict):
        return None
    seed = provenance.get("requested_decoding_seed")
    if seed is not None and (
        not isinstance(seed, int) or isinstance(seed, bool) or seed < 0
    ):
        return None
    seed_status = provenance.get("deterministic_seed_control")
    if seed_status not in {
        "not_requested",
        "requested_unverified",
        "supported",
        "unsupported",
        "unavailable",
    }:
        return None
    forwarding_status = provenance.get("seed_forwarding_status")
    if forwarding_status not in {"not_requested", "forwarded", "not_forwarded"}:
        return None
    if seed is None and (
        forwarding_status != "not_requested" or seed_status != "not_requested"
    ):
        return None
    if seed is not None and (
        forwarding_status == "not_requested" or seed_status == "not_requested"
    ):
        return None
    fingerprint_status = provenance.get("system_fingerprint_status")
    if fingerprint_status not in {"reported", "unavailable", "invalid", "conflicting"}:
        return None
    fingerprint = provenance.get("provider_system_fingerprint")
    if fingerprint is not None and (
        not isinstance(fingerprint, str) or not fingerprint.strip()
    ):
        return None
    if (fingerprint_status == "reported") != (fingerprint is not None):
        return None
    provider_adapter = provenance.get("provider_adapter")
    provider_model = provenance.get("provider_model")
    gateway_digest = provenance.get("gateway_base_url_sha256")
    if provider_adapter not in {"openai_compatible", "anthropic_compatible"}:
        return None
    if not isinstance(provider_model, str) or not provider_model.strip():
        return None
    if not isinstance(gateway_digest, str) or len(gateway_digest) != 64:
        return None
    try:
        int(gateway_digest, 16)
    except ValueError:
        return None
    return {
        "provider_adapter": provider_adapter,
        "provider_model": provider_model,
        "gateway_base_url_sha256": gateway_digest,
        "requested_decoding_seed": seed,
        "seed_forwarding_status": forwarding_status,
        "deterministic_seed_control": seed_status,
        "provider_system_fingerprint": fingerprint,
        "system_fingerprint_status": fingerprint_status,
    }
