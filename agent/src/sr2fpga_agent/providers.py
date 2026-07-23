"""Generic OpenAI- and Anthropic-compatible LLM providers."""

from __future__ import annotations

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

@dataclass(frozen=True)
class OpenAICompatibleConfig:
    """OpenAI-compatible chat completions API configuration."""

    api_key: str
    model: str = "deepseek-v4-pro"
    base_url: str = "https://api.deepseek.com"
    timeout_seconds: int = 120
    max_tokens: int = 0
    transport_attempts: int = 3
    retry_backoff_seconds: float = 0.5


class OpenAICompatibleClient:
    """Small stdlib HTTP client for OpenAI-compatible chat completions."""

    def __init__(self, config: OpenAICompatibleConfig) -> None:
        self.config = config

    def chat(self, messages: list[dict[str, str]]) -> str:
        payload = self._chat_payload(messages)
        data = self._request_with_retries(
            payload,
            lambda response: _read_chat_completion_json(response, self.config.timeout_seconds),
        )

        try:
            return str(data["choices"][0]["message"]["content"])
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(
                "OpenAI-compatible API response did not contain choices[0].message.content"
            ) from exc

    def stream_chat(self, messages: list[dict[str, str]]) -> str:
        payload = self._chat_payload(messages)
        payload["stream"] = True
        return self._request_with_retries(
            payload,
            lambda response: _read_streaming_chat_content(response, self.config.timeout_seconds),
        )

    def _chat_payload(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": _messages_for_model(self.config.model, messages),
            "temperature": 0.1,
        }
        if _model_supports_json_response_format(self.config.model):
            payload["response_format"] = {"type": "json_object"}
        if self.config.max_tokens > 0:
            payload["max_tokens"] = self.config.max_tokens
        return payload

    def _request_with_retries(self, payload: dict[str, Any], reader: Callable[[Any], Any]) -> Any:
        last_error: _TransientOpenAICompatibleError | None = None
        attempts = max(1, self.config.transport_attempts)
        for attempt in range(attempts):
            try:
                return self._request_once(payload, reader)
            except _TransientOpenAICompatibleError as exc:
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
        url = self.config.base_url.rstrip("/") + "/chat/completions"
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


class AnthropicCompatibleClient:
    """Small stdlib HTTP client for Anthropic-compatible Messages APIs."""

    def __init__(self, config: AnthropicCompatibleConfig) -> None:
        self.config = config

    def chat(self, messages: list[dict[str, str]]) -> str:
        data = self._request_with_retries(
            _anthropic_messages_payload(self.config, messages),
            lambda response: _read_chat_completion_json(response, self.config.timeout_seconds),
        )
        return _read_anthropic_message_text(data)

    def stream_chat(self, messages: list[dict[str, str]]) -> str:
        payload = _anthropic_messages_payload(self.config, messages)
        payload["stream"] = True
        return self._request_with_retries(
            payload,
            lambda response: _read_anthropic_streaming_text(response, self.config.timeout_seconds),
        )

    def _request_with_retries(self, payload: dict[str, Any], reader: Callable[[Any], Any]) -> Any:
        last_error: _TransientOpenAICompatibleError | None = None
        attempts = max(1, self.config.transport_attempts)
        for attempt in range(attempts):
            try:
                return self._request_once(payload, reader)
            except _TransientOpenAICompatibleError as exc:
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


def _read_anthropic_streaming_text(response: Any, timeout_seconds: int) -> str:
    chunks: list[str] = []
    started_at = time.monotonic()
    while True:
        raw_line = _read_streaming_line(response, timeout_seconds, started_at)
        if not raw_line:
            break
        line = raw_line.decode("utf-8", errors="replace").strip()
        if not line or line.startswith(":") or not line.startswith("data:"):
            continue
        data = line.removeprefix("data:").strip()
        try:
            event = json.loads(data)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Anthropic-compatible streaming response contained invalid event data") from exc
        event_type = str(event.get("type", "")) if isinstance(event, dict) else ""
        if event_type == "content_block_delta":
            delta = event.get("delta", {})
            if isinstance(delta, dict) and delta.get("type") == "text_delta":
                chunks.append(str(delta.get("text", "")))
        elif event_type == "error":
            error = event.get("error", {})
            if isinstance(error, dict):
                raise RuntimeError(f"{error.get('type', 'error')}: {error.get('message', '')}")
            raise RuntimeError(f"Anthropic-compatible streaming response error: {error}")
        elif event_type == "message_stop":
            break
    text = "".join(chunks)
    if not text:
        raise RuntimeError("Anthropic-compatible streaming response contained no text")
    return text


def _read_streaming_chat_content(response: Any, timeout_seconds: int) -> str:
    chunks: list[str] = []
    started_at = time.monotonic()
    while True:
        raw_line = _read_streaming_line(response, timeout_seconds, started_at)
        if not raw_line:
            break
        if time.monotonic() - started_at > timeout_seconds:
            raise _TransientOpenAICompatibleError("OpenAI-compatible API response read timed out")
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
            raise RuntimeError("OpenAI-compatible streaming response contained invalid chat completion data") from exc
        if isinstance(event, dict) and "error" in event:
            raise RuntimeError(f"OpenAI-compatible streaming response error: {event['error']}")
        choices = event.get("choices") if isinstance(event, dict) else None
        if not choices:
            continue
        try:
            delta = choices[0].get("delta", {})
        except (AttributeError, IndexError, TypeError) as exc:
            raise RuntimeError("OpenAI-compatible streaming response contained invalid chat completion data") from exc
        content = delta.get("content")
        if content is not None:
            chunks.append(str(content))
    return "".join(chunks)


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
