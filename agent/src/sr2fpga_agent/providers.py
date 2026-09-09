"""Generic OpenAI- and Anthropic-compatible LLM providers."""

from __future__ import annotations

import hashlib
import http.client
import json
import select
import signal
import ssl
import sys
import threading
import time
import urllib.error
import urllib.request
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Callable


_MISSING_SYSTEM_FINGERPRINT = object()

@dataclass(frozen=True)
class OpenAICompatibleConfig:
    """OpenAI-compatible API configuration."""

    api_key: str
    model: str = "deepseek-v4-pro"
    base_url: str = "https://api.deepseek.com"
    timeout_seconds: int = 120
    max_tokens: int = 0
    transport_attempts: int = 3
    retry_backoff_seconds: float = 0.5
    seed: int | None = None
    wire_api: str = "chat_completions"
    reasoning_effort: str = ""
    disable_response_storage: bool = False

    def __post_init__(self) -> None:
        _validate_requested_seed(self.seed)
        if self.wire_api not in {"chat_completions", "responses"}:
            raise ValueError("wire_api must be chat_completions or responses")
        if self.reasoning_effort not in {
            "",
            "none",
            "minimal",
            "low",
            "medium",
            "high",
            "xhigh",
        }:
            raise ValueError("reasoning_effort is not supported")
        if not isinstance(self.disable_response_storage, bool):
            raise ValueError("disable_response_storage must be a boolean")
        if self.wire_api != "responses" and self.reasoning_effort:
            raise ValueError("reasoning_effort requires wire_api=responses")
        if self.wire_api != "responses" and self.disable_response_storage:
            raise ValueError(
                "disable_response_storage requires wire_api=responses"
            )


class OpenAICompatibleClient:
    """Small stdlib HTTP client for OpenAI-compatible APIs."""

    def __init__(self, config: OpenAICompatibleConfig) -> None:
        self.config = config
        self._transport_state = threading.local()

    def consume_transport_attempt_count(self) -> int | None:
        """Return and clear this thread's most recent request-attempt count."""

        count = getattr(self._transport_state, "last_attempt_count", None)
        if hasattr(self._transport_state, "last_attempt_count"):
            del self._transport_state.last_attempt_count
        return count

    def consume_token_usage(self) -> dict[str, int | None] | None:
        usage = getattr(self._transport_state, "last_token_usage", None)
        if hasattr(self._transport_state, "last_token_usage"):
            del self._transport_state.last_token_usage
        if hasattr(self._transport_state, "token_usage_attempt_count"):
            del self._transport_state.token_usage_attempt_count
        return _present_token_usage(dict(usage)) if isinstance(usage, dict) else None

    def consume_response_provenance(self) -> dict[str, Any] | None:
        if not getattr(self._transport_state, "response_provenance_available", False):
            return None
        self._transport_state.response_provenance_available = False
        fingerprints = tuple(
            sorted(getattr(self._transport_state, "system_fingerprints", set()))
        )
        invalid = getattr(self._transport_state, "invalid_system_fingerprint", False)
        if invalid and fingerprints:
            fingerprint = None
            fingerprint_status = "conflicting"
        elif invalid:
            fingerprint = None
            fingerprint_status = "invalid"
        elif len(fingerprints) == 1:
            fingerprint = fingerprints[0]
            fingerprint_status = "reported"
        elif fingerprints:
            fingerprint = None
            fingerprint_status = "conflicting"
        else:
            fingerprint = None
            fingerprint_status = "unavailable"
        seed_requested = self.config.seed is not None
        seed_forwarded = seed_requested and self.config.wire_api != "responses"
        if not seed_requested:
            forwarding_status = "not_requested"
            seed_control = "not_requested"
        elif seed_forwarded:
            forwarding_status = "forwarded"
            seed_control = "requested_unverified"
        else:
            forwarding_status = "not_forwarded"
            seed_control = "unsupported"
        return {
            "provider_adapter": "openai_compatible",
            "provider_model": self.config.model,
            "gateway_base_url_sha256": hashlib.sha256(
                self.config.base_url.rstrip("/").encode("utf-8")
            ).hexdigest(),
            "requested_decoding_seed": self.config.seed,
            "seed_forwarding_status": forwarding_status,
            "deterministic_seed_control": seed_control,
            "provider_system_fingerprint": fingerprint,
            "system_fingerprint_status": fingerprint_status,
        }

    def chat(self, messages: list[dict[str, str]]) -> str:
        self._reset_token_usage()
        self._reset_response_provenance()
        payload = self._chat_payload(messages)
        data = self._request_with_retries(
            payload,
            lambda response: _read_chat_completion_json(response, self.config.timeout_seconds),
        )

        self._store_token_usage(_openai_token_usage(data))
        self._store_system_fingerprint(_provider_system_fingerprint(data))
        if self.config.wire_api == "responses":
            return _read_responses_text(data)
        try:
            return str(data["choices"][0]["message"]["content"])
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(
                "OpenAI-compatible API response did not contain choices[0].message.content"
            ) from exc

    def stream_chat(self, messages: list[dict[str, str]]) -> str:
        self._reset_token_usage()
        self._reset_response_provenance()
        payload = self._chat_payload(messages)
        payload["stream"] = True
        if self.config.wire_api == "responses":
            return self._request_with_retries(
                payload,
                lambda response: _read_streaming_responses_content(
                    response,
                    self.config.timeout_seconds,
                    usage_sink=self._store_token_usage,
                ),
            )
        return self._request_with_retries(
            payload,
            lambda response: _read_streaming_chat_content(
                response,
                self.config.timeout_seconds,
                usage_sink=self._store_token_usage,
                fingerprint_sink=self._store_system_fingerprint,
            ),
        )

    def _store_token_usage(self, usage: dict[str, int | None] | None) -> None:
        attempts = getattr(self._transport_state, "token_usage_attempt_count", 0)
        existing = getattr(self._transport_state, "last_token_usage", None)
        self._transport_state.last_token_usage = _accumulate_token_usage(
            existing, usage, has_existing_attempt=attempts > 0
        )
        self._transport_state.token_usage_attempt_count = attempts + 1

    def _reset_token_usage(self) -> None:
        self._transport_state.last_token_usage = None
        self._transport_state.token_usage_attempt_count = 0

    def _reset_response_provenance(self) -> None:
        self._transport_state.system_fingerprints = set()
        self._transport_state.invalid_system_fingerprint = False
        self._transport_state.response_provenance_available = True

    def _store_system_fingerprint(self, fingerprint: Any) -> None:
        if fingerprint is _MISSING_SYSTEM_FINGERPRINT:
            return
        if isinstance(fingerprint, str) and fingerprint.strip():
            self._transport_state.system_fingerprints.add(fingerprint.strip())
            return
        self._transport_state.invalid_system_fingerprint = True

    def _chat_payload(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        if self.config.wire_api == "responses":
            payload: dict[str, Any] = {
                "model": self.config.model,
                "input": messages,
                "store": not self.config.disable_response_storage,
            }
            if _model_supports_json_response_format(self.config.model):
                payload["text"] = {"format": {"type": "json_object"}}
            if self.config.reasoning_effort:
                payload["reasoning"] = {"effort": self.config.reasoning_effort}
            if self.config.max_tokens > 0:
                payload["max_output_tokens"] = self.config.max_tokens
            return payload
        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": _messages_for_model(self.config.model, messages),
            "temperature": 0.1,
        }
        if _model_supports_json_response_format(self.config.model):
            payload["response_format"] = {"type": "json_object"}
        if self.config.max_tokens > 0:
            payload["max_tokens"] = self.config.max_tokens
        if self.config.seed is not None:
            payload["seed"] = self.config.seed
        return payload

    def _request_with_retries(self, payload: dict[str, Any], reader: Callable[[Any], Any]) -> Any:
        last_error: _TransientOpenAICompatibleError | None = None
        attempts = max(1, self.config.transport_attempts)
        self._transport_state.last_attempt_count = 0
        for attempt in range(attempts):
            self._transport_state.last_attempt_count += 1
            usage_attempts_before = getattr(
                self._transport_state, "token_usage_attempt_count", 0
            )
            try:
                return self._request_once(payload, reader)
            except _TransientOpenAICompatibleError as exc:
                if (
                    getattr(self._transport_state, "token_usage_attempt_count", 0)
                    == usage_attempts_before
                ):
                    self._store_token_usage(None)
                last_error = exc
                if attempt + 1 >= attempts:
                    break
                delay = self.config.retry_backoff_seconds * (attempt + 1)
                if delay > 0:
                    time.sleep(delay)
        if last_error is not None:
            raise RuntimeError(str(last_error)) from last_error
        raise RuntimeError("OpenAI-compatible API request did not run")

    def _request_once(self, payload: dict[str, Any], reader: Callable[[Any], Any]) -> Any:
        endpoint = "/responses" if self.config.wire_api == "responses" else "/chat/completions"
        url = self.config.base_url.rstrip("/") + endpoint
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(
                request,
                timeout=self.config.timeout_seconds,
                context=_default_ssl_context(),
            ) as response:
                try:
                    with _response_read_deadline(self.config.timeout_seconds):
                        return reader(response)
                except TimeoutError as exc:
                    raise _TransientOpenAICompatibleError(
                        "OpenAI-compatible API response read timed out"
                    ) from exc
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            message = f"OpenAI-compatible API request failed with HTTP {exc.code}: {body}"
            if exc.code in TRANSIENT_HTTP_STATUS_CODES:
                raise _TransientOpenAICompatibleError(message) from exc
            raise RuntimeError(message) from exc
        except TimeoutError as exc:
            raise _TransientOpenAICompatibleError("OpenAI-compatible API request timed out") from exc
        except urllib.error.URLError as exc:
            raise _TransientOpenAICompatibleError(f"OpenAI-compatible API request failed: {exc.reason}") from exc
        except http.client.IncompleteRead as exc:
            raise _TransientOpenAICompatibleError(
                f"OpenAI-compatible API response truncated (IncompleteRead): {exc}"
            ) from exc


@dataclass(frozen=True)
class AnthropicCompatibleConfig:
    """Anthropic Messages API configuration."""

    api_key: str
    model: str = "claude-opus-4-8"
    base_url: str = "https://api.anthropic.com/v1"
    timeout_seconds: int = 120
    max_tokens: int = 16384
    anthropic_version: str = "2023-06-01"
    transport_attempts: int = 3
    retry_backoff_seconds: float = 0.5
    requested_seed: int | None = None

    def __post_init__(self) -> None:
        _validate_requested_seed(self.requested_seed)


class AnthropicCompatibleClient:
    """Small stdlib HTTP client for Anthropic-compatible Messages APIs."""

    def __init__(self, config: AnthropicCompatibleConfig) -> None:
        self.config = config
        self._transport_state = threading.local()

    def consume_transport_attempt_count(self) -> int | None:
        """Return and clear this thread's most recent request-attempt count."""

        count = getattr(self._transport_state, "last_attempt_count", None)
        if hasattr(self._transport_state, "last_attempt_count"):
            del self._transport_state.last_attempt_count
        return count

    def consume_token_usage(self) -> dict[str, int | None] | None:
        usage = getattr(self._transport_state, "last_token_usage", None)
        if hasattr(self._transport_state, "last_token_usage"):
            del self._transport_state.last_token_usage
        if hasattr(self._transport_state, "token_usage_attempt_count"):
            del self._transport_state.token_usage_attempt_count
        return _present_token_usage(dict(usage)) if isinstance(usage, dict) else None

    def consume_response_provenance(self) -> dict[str, Any] | None:
        if not getattr(self._transport_state, "response_provenance_available", False):
            return None
        self._transport_state.response_provenance_available = False
        return {
            "provider_adapter": "anthropic_compatible",
            "provider_model": self.config.model,
            "gateway_base_url_sha256": hashlib.sha256(
                self.config.base_url.rstrip("/").encode("utf-8")
            ).hexdigest(),
            "requested_decoding_seed": self.config.requested_seed,
            "seed_forwarding_status": (
                "not_forwarded"
                if self.config.requested_seed is not None
                else "not_requested"
            ),
            "deterministic_seed_control": (
                "unsupported"
                if self.config.requested_seed is not None
                else "not_requested"
            ),
            "provider_system_fingerprint": None,
            "system_fingerprint_status": "unavailable",
        }

    def chat(self, messages: list[dict[str, str]]) -> str:
        self._reset_token_usage()
        self._reset_response_provenance()
        data = self._request_with_retries(
            _anthropic_messages_payload(self.config, messages),
            lambda response: _read_chat_completion_json(response, self.config.timeout_seconds),
        )
        self._store_token_usage(_anthropic_token_usage(data))
        return _read_anthropic_message_text(data)

    def stream_chat(self, messages: list[dict[str, str]]) -> str:
        self._reset_token_usage()
        self._reset_response_provenance()
        payload = _anthropic_messages_payload(self.config, messages)
        payload["stream"] = True
        return self._request_with_retries(
            payload,
            lambda response: _read_anthropic_streaming_text(
                response,
                self.config.timeout_seconds,
                usage_sink=self._store_token_usage,
            ),
        )

    def _store_token_usage(self, usage: dict[str, int | None] | None) -> None:
        attempts = getattr(self._transport_state, "token_usage_attempt_count", 0)
        existing = getattr(self._transport_state, "last_token_usage", None)
        self._transport_state.last_token_usage = _accumulate_token_usage(
            existing, usage, has_existing_attempt=attempts > 0
        )
        self._transport_state.token_usage_attempt_count = attempts + 1

    def _reset_token_usage(self) -> None:
        self._transport_state.last_token_usage = None
        self._transport_state.token_usage_attempt_count = 0

    def _reset_response_provenance(self) -> None:
        self._transport_state.response_provenance_available = True

    def _request_with_retries(self, payload: dict[str, Any], reader: Callable[[Any], Any]) -> Any:
        last_error: _TransientOpenAICompatibleError | None = None
        attempts = max(1, self.config.transport_attempts)
        self._transport_state.last_attempt_count = 0
        for attempt in range(attempts):
            self._transport_state.last_attempt_count += 1
            usage_attempts_before = getattr(
                self._transport_state, "token_usage_attempt_count", 0
            )
            try:
                return self._request_once(payload, reader)
            except _TransientOpenAICompatibleError as exc:
                if (
                    getattr(self._transport_state, "token_usage_attempt_count", 0)
                    == usage_attempts_before
                ):
                    self._store_token_usage(None)
                last_error = exc
                if attempt + 1 >= attempts:
                    break
                delay = self.config.retry_backoff_seconds * (attempt + 1)
                if delay > 0:
                    time.sleep(delay)
        if last_error is not None:
            raise RuntimeError(str(last_error)) from last_error
        raise RuntimeError("Anthropic-compatible API request did not run")

    def _request_once(self, payload: dict[str, Any], reader: Callable[[Any], Any]) -> Any:
        url = self.config.base_url.rstrip("/") + "/messages"
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "x-api-key": self.config.api_key,
                "anthropic-version": self.config.anthropic_version,
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(
                request,
                timeout=self.config.timeout_seconds,
                context=_default_ssl_context(),
            ) as response:
                try:
                    with _response_read_deadline(self.config.timeout_seconds):
                        return reader(response)
                except TimeoutError as exc:
                    raise _TransientOpenAICompatibleError(
                        "Anthropic-compatible API response read timed out"
                    ) from exc
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            message = f"Anthropic-compatible API request failed with HTTP {exc.code}: {body}"
            if exc.code in TRANSIENT_HTTP_STATUS_CODES:
                raise _TransientOpenAICompatibleError(message) from exc
            raise RuntimeError(message) from exc
        except TimeoutError as exc:
            raise _TransientOpenAICompatibleError("Anthropic-compatible API request timed out") from exc
        except urllib.error.URLError as exc:
            raise _TransientOpenAICompatibleError(f"Anthropic-compatible API request failed: {exc.reason}") from exc
        except http.client.IncompleteRead as exc:
            raise _TransientOpenAICompatibleError(
                f"Anthropic-compatible API response truncated (IncompleteRead): {exc}"
            ) from exc


def _default_ssl_context() -> ssl.SSLContext:
    for module_name in ("sr2fpga_agent.deepseek", "sr2fpga_agent.deepseek"):
        legacy_module = sys.modules.get(module_name)
        legacy_factory = getattr(legacy_module, "_default_ssl_context", None)
        if legacy_factory is not None and legacy_factory is not _default_ssl_context:
            return legacy_factory()
    try:
        import certifi
    except ModuleNotFoundError:
        return ssl.create_default_context()
    return ssl.create_default_context(cafile=certifi.where())


TRANSIENT_HTTP_STATUS_CODES = {408, 429, 500, 502, 503, 504}


class _TransientOpenAICompatibleError(RuntimeError):
    pass


@contextmanager
def _response_read_deadline(timeout_seconds: int):
    if timeout_seconds <= 0 or not hasattr(signal, "SIGALRM") or threading.current_thread() is not threading.main_thread():
        yield
        return

    def _raise_timeout(_signum, _frame):
        raise TimeoutError("response read deadline exceeded")

    previous_handler = signal.getsignal(signal.SIGALRM)
    signal.signal(signal.SIGALRM, _raise_timeout)
    signal.setitimer(signal.ITIMER_REAL, timeout_seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)


def _model_supports_json_response_format(model: str) -> bool:
    return not model.startswith("claude-")


def _validate_requested_seed(seed: int | None) -> None:
    if seed is not None and (
        not isinstance(seed, int) or isinstance(seed, bool) or seed < 0
    ):
        raise ValueError("seed must be a non-negative integer or None")


def _provider_system_fingerprint(data: Any) -> Any:
    if not isinstance(data, dict) or "system_fingerprint" not in data:
        return _MISSING_SYSTEM_FINGERPRINT
    return data["system_fingerprint"]


def _messages_for_model(model: str, messages: list[dict[str, str]]) -> list[dict[str, str]]:
    if not model.startswith("claude-"):
        return messages
    system_parts: list[str] = []
    rewritten: list[dict[str, str]] = []
    for message in messages:
        role = message.get("role", "")
        content = str(message.get("content", ""))
        if role == "system":
            system_parts.append(content)
            continue
        rewritten.append({"role": role, "content": content})
    if not system_parts:
        return rewritten
    system_text = "\n\n".join(system_parts)
    if rewritten and rewritten[0].get("role") == "user":
        first = rewritten[0]
        rewritten[0] = {
            "role": "user",
            "content": f"System instructions:\n{system_text}\n\nUser request:\n{first.get('content', '')}",
        }
        return rewritten
    return [{"role": "user", "content": f"System instructions:\n{system_text}"}] + rewritten


def _read_chat_completion_json(response: Any, timeout_seconds: int) -> Any:
    return json.loads(_read_response_body(response, timeout_seconds).decode("utf-8"))


def _read_responses_text(data: Any) -> str:
    if not isinstance(data, dict):
        raise RuntimeError("OpenAI-compatible Responses API response was not an object")
    if isinstance(data.get("output_text"), str) and data["output_text"]:
        return data["output_text"]
    chunks: list[str] = []
    output = data.get("output")
    if isinstance(output, list):
        for item in output:
            if not isinstance(item, dict) or not isinstance(item.get("content"), list):
                continue
            for part in item["content"]:
                if (
                    isinstance(part, dict)
                    and part.get("type") == "output_text"
                    and part.get("text") is not None
                ):
                    chunks.append(str(part["text"]))
    if chunks:
        return "".join(chunks)
    raise RuntimeError("OpenAI-compatible Responses API response did not contain output text")


def _read_response_body(response: Any, timeout_seconds: int) -> bytes:
    chunks: list[bytes] = []
    started_at = time.monotonic()
    while True:
        chunk = response.read(65536)
        if not chunk:
            break
        chunks.append(chunk)
        if time.monotonic() - started_at > timeout_seconds:
            raise _TransientOpenAICompatibleError("OpenAI-compatible API response read timed out")
    return b"".join(chunks)


def _anthropic_messages_payload(
    config: AnthropicCompatibleConfig,
    messages: list[dict[str, str]],
) -> dict[str, Any]:
    system_parts: list[str] = []
    anthropic_messages: list[dict[str, str]] = []
    for message in messages:
        role = str(message.get("role", ""))
        content = str(message.get("content", ""))
        if role == "system":
            system_parts.append(content)
        elif role in {"user", "assistant"}:
            anthropic_messages.append({"role": role, "content": content})
    if not anthropic_messages:
        anthropic_messages.append({"role": "user", "content": "Return a JSON object."})
    payload: dict[str, Any] = {
        "model": config.model,
        "max_tokens": config.max_tokens,
        "messages": anthropic_messages,
        "temperature": 0.1,
    }
    if system_parts:
        payload["system"] = "\n\n".join(system_parts)
    return payload


def _read_anthropic_message_text(data: Any) -> str:
    try:
        content = data["content"]
    except (KeyError, TypeError) as exc:
        raise RuntimeError("Anthropic-compatible API response did not contain content") from exc
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        chunks: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text" and item.get("text") is not None:
                chunks.append(str(item["text"]))
        if chunks:
            return "".join(chunks)
    raise RuntimeError("Anthropic-compatible API response did not contain text content")


def _openai_token_usage(data: Any) -> dict[str, int | None] | None:
    if not isinstance(data, dict) or not isinstance(data.get("usage"), dict):
        return None
    usage = data["usage"]
    input_tokens = _nonnegative_int(usage.get("prompt_tokens"))
    if input_tokens is None:
        input_tokens = _nonnegative_int(usage.get("input_tokens"))
    output_tokens = _nonnegative_int(usage.get("completion_tokens"))
    if output_tokens is None:
        output_tokens = _nonnegative_int(usage.get("output_tokens"))
    details = usage.get("prompt_tokens_details")
    if not isinstance(details, dict):
        details = usage.get("input_tokens_details")
    cached_tokens = (
        _nonnegative_int(details.get("cached_tokens"))
        if isinstance(details, dict)
        else None
    )
    if input_tokens is None and output_tokens is None and cached_tokens is None:
        return None
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cached_tokens": cached_tokens,
    }


def _anthropic_token_usage(data: Any) -> dict[str, int | None] | None:
    if not isinstance(data, dict) or not isinstance(data.get("usage"), dict):
        return None
    usage = data["usage"]
    uncached_input = _nonnegative_int(usage.get("input_tokens"))
    cache_creation = _nonnegative_int(usage.get("cache_creation_input_tokens"))
    cache_read = _nonnegative_int(usage.get("cache_read_input_tokens"))
    output_tokens = _nonnegative_int(usage.get("output_tokens"))
    input_tokens = (
        uncached_input + cache_creation + cache_read
        if None not in (uncached_input, cache_creation, cache_read)
        else None
    )
    if input_tokens is None and output_tokens is None and cache_read is None:
        return None
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cached_tokens": cache_read,
    }


def _nonnegative_int(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value


def _read_anthropic_streaming_text(
    response: Any,
    timeout_seconds: int,
    *,
    usage_sink: Callable[[dict[str, int | None] | None], None] | None = None,
) -> str:
    chunks: list[str] = []
    token_usage: dict[str, int | None] = {
        "input_tokens": None,
        "output_tokens": None,
        "cached_tokens": None,
    }
    started_at = time.monotonic()
    try:
        while True:
            raw_line = _read_streaming_line(response, timeout_seconds, started_at)
            if not raw_line:
                raise _TransientOpenAICompatibleError("Anthropic stream ended before message_stop")
            line = raw_line.decode("utf-8", errors="replace").strip()
            if not line or line.startswith(":") or not line.startswith("data:"):
                continue
            data = line.removeprefix("data:").strip()
            try:
                event = json.loads(data)
            except json.JSONDecodeError as exc:
                raise RuntimeError(
                    "Anthropic-compatible streaming response contained invalid event data"
                ) from exc
            event_type = str(event.get("type", "")) if isinstance(event, dict) else ""
            if event_type == "message_start":
                message = event.get("message")
                usage = _anthropic_token_usage(message)
                _merge_token_usage(token_usage, usage)
            elif event_type == "message_delta":
                usage = _anthropic_token_usage({"usage": event.get("usage")})
                _merge_token_usage(token_usage, usage)
            elif event_type == "content_block_delta":
                delta = event.get("delta", {})
                if isinstance(delta, dict) and delta.get("type") == "text_delta":
                    chunks.append(str(delta.get("text", "")))
            elif event_type == "error":
                error = event.get("error", {})
                if isinstance(error, dict):
                    raise RuntimeError(
                        f"{error.get('type', 'error')}: {error.get('message', '')}"
                    )
                raise RuntimeError(f"Anthropic-compatible streaming response error: {error}")
            elif event_type == "message_stop":
                break
        text = "".join(chunks)
        if not text:
            raise RuntimeError("Anthropic-compatible streaming response contained no text")
        return text
    finally:
        if usage_sink is not None:
            usage_sink(_present_token_usage(token_usage))


def _read_streaming_chat_content(
    response: Any,
    timeout_seconds: int,
    *,
    usage_sink: Callable[[dict[str, int | None] | None], None] | None = None,
    fingerprint_sink: Callable[[str | None], None] | None = None,
) -> str:
    chunks: list[str] = []
    token_usage: dict[str, int | None] = {
        "input_tokens": None,
        "output_tokens": None,
        "cached_tokens": None,
    }
    started_at = time.monotonic()
    try:
        while True:
            raw_line = _read_streaming_line(response, timeout_seconds, started_at)
            if not raw_line:
                raise _TransientOpenAICompatibleError("Chat stream ended before [DONE]")
            if time.monotonic() - started_at > timeout_seconds:
                raise _TransientOpenAICompatibleError(
                    "OpenAI-compatible API response read timed out"
                )
            line = raw_line.decode("utf-8", errors="replace").strip()
            if not line or line.startswith(":"):
                continue
            if not line.startswith("data:"):
                continue
            data = line.removeprefix("data:").strip()
            if data == "[DONE]":
                break
            try:
                event = json.loads(data)
            except json.JSONDecodeError as exc:
                raise RuntimeError(
                    "OpenAI-compatible streaming response contained invalid chat completion data"
                ) from exc
            if isinstance(event, dict) and "error" in event:
                raise RuntimeError(f"OpenAI-compatible streaming response error: {event['error']}")
            if fingerprint_sink is not None:
                fingerprint_sink(_provider_system_fingerprint(event))
            _merge_token_usage(token_usage, _openai_token_usage(event))
            choices = event.get("choices") if isinstance(event, dict) else None
            if not choices:
                continue
            try:
                delta = choices[0].get("delta", {})
            except (AttributeError, IndexError, TypeError) as exc:
                raise RuntimeError(
                    "OpenAI-compatible streaming response contained invalid chat completion data"
                ) from exc
            content = delta.get("content")
            if content is not None:
                chunks.append(str(content))
        return "".join(chunks)
    finally:
        if usage_sink is not None:
            usage_sink(_present_token_usage(token_usage))


def _read_streaming_responses_content(
    response: Any,
    timeout_seconds: int,
    *,
    usage_sink: Callable[[dict[str, int | None] | None], None] | None = None,
) -> str:
    chunks: list[str] = []
    completed_text = ""
    token_usage: dict[str, int | None] = {
        "input_tokens": None,
        "output_tokens": None,
        "cached_tokens": None,
    }
    started_at = time.monotonic()
    try:
        while True:
            raw_line = _read_streaming_line(response, timeout_seconds, started_at)
            if not raw_line:
                raise _TransientOpenAICompatibleError("Responses stream ended before response.completed")
            line = raw_line.decode("utf-8", errors="replace").strip()
            if not line or line.startswith(":") or not line.startswith("data:"):
                continue
            raw_data = line.removeprefix("data:").strip()
            if raw_data == "[DONE]":
                raise _TransientOpenAICompatibleError("Responses stream ended before response.completed")
            try:
                event = json.loads(raw_data)
            except json.JSONDecodeError as exc:
                raise RuntimeError(
                    "OpenAI-compatible streaming response contained invalid Responses API data"
                ) from exc
            if not isinstance(event, dict):
                continue
            event_type = str(event.get("type", ""))
            if event_type == "response.output_text.delta":
                chunks.append(str(event.get("delta", "")))
            elif event_type == "response.output_text.done":
                completed_text = str(event.get("text", ""))
            elif event_type == "response.completed":
                response_data = event.get("response")
                _merge_token_usage(token_usage, _openai_token_usage(response_data))
                break
            elif event_type in {"error", "response.failed", "response.incomplete"}:
                detail = event.get("error") or event.get("response") or event
                raise RuntimeError(
                    f"OpenAI-compatible streaming Responses API error: {detail}"
                )
        return "".join(chunks) or completed_text
    finally:
        if usage_sink is not None:
            usage_sink(_present_token_usage(token_usage))


def _merge_token_usage(
    target: dict[str, int | None],
    update: dict[str, int | None] | None,
) -> None:
    if update is None:
        return
    for axis, value in update.items():
        if value is not None:
            target[axis] = value


def _present_token_usage(
    usage: dict[str, int | None],
) -> dict[str, int | None] | None:
    return usage if any(value is not None for value in usage.values()) else None


def _accumulate_token_usage(
    existing: Any,
    update: dict[str, int | None] | None,
    *,
    has_existing_attempt: bool,
) -> dict[str, int | None]:
    axes = ("input_tokens", "output_tokens", "cached_tokens")
    normalized_update = {
        axis: (
            update.get(axis)
            if isinstance(update, dict)
            and isinstance(update.get(axis), int)
            and not isinstance(update.get(axis), bool)
            and update.get(axis) >= 0
            else None
        )
        for axis in axes
    }
    if not has_existing_attempt:
        return normalized_update
    normalized_existing = {
        axis: (
            existing.get(axis)
            if isinstance(existing, dict)
            and isinstance(existing.get(axis), int)
            and not isinstance(existing.get(axis), bool)
            and existing.get(axis) >= 0
            else None
        )
        for axis in axes
    }
    return {
        axis: (
            normalized_existing[axis] + normalized_update[axis]
            if normalized_existing[axis] is not None
            and normalized_update[axis] is not None
            else None
        )
        for axis in axes
    }


def _read_streaming_line(response: Any, timeout_seconds: int, started_at: float) -> bytes:
    fd = _response_fileno(response)
    if fd is not None and timeout_seconds > 0:
        remaining = timeout_seconds - (time.monotonic() - started_at)
        if remaining <= 0:
            raise _TransientOpenAICompatibleError("OpenAI-compatible API response read timed out")
        readable, _, _ = select.select([fd], [], [], remaining)
        if not readable:
            raise _TransientOpenAICompatibleError("OpenAI-compatible API response read timed out")
    return response.readline()


def _response_fileno(response: Any) -> int | None:
    if hasattr(response, "fileno"):
        try:
            return int(response.fileno())
        except (OSError, TypeError, ValueError):
            return None
    fp = getattr(response, "fp", None)
    raw = getattr(fp, "raw", None)
    sock = getattr(raw, "_sock", None)
    if sock is None:
        return None
    try:
        return int(sock.fileno())
    except (OSError, TypeError, ValueError):
        return None
