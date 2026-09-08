"""Execution-only inference backend adapters for M12.5."""

from __future__ import annotations

from dataclasses import dataclass
import http.client
import json
import math
import os
import socket
import time
from pathlib import Path
import re
from typing import Any, Mapping
import urllib.error
import urllib.request
from urllib.parse import urlsplit

from .inference import (
    InferenceBackendError,
    InferenceIntegrityError,
    InferenceRequest,
    InferenceResult,
    InferenceTarget,
    model_output_schema,
    sha256,
)


OPENAI_CHAT_COMPLETIONS_JSON_SCHEMA = "openai_chat_completions_json_schema"
STRUCTURED_OUTPUT_DIALECTS = frozenset({OPENAI_CHAT_COMPLETIONS_JSON_SCHEMA})
_SCHEMA_NAME = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_-]{0,63}\Z")


def _http_json_bytes(value: Any) -> bytes:
    """Return the canonical UTF-8 JSON representation used on the wire."""
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")


@dataclass(frozen=True)
class StructuredHTTPBody:
    """One deterministic structured-output body and its measurable parts."""

    dialect: str
    endpoint: str
    schema_name: str
    body_bytes: bytes
    prompt_bytes: bytes
    messages_bytes: bytes
    schema_bytes: bytes
    response_format_bytes: bytes
    response_format_envelope_bytes: int
    request_envelope_bytes: int

    def manifest(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0.0",
            "dialect": self.dialect,
            "method": "POST",
            "endpoint": self.endpoint,
            "content_type": "application/json",
            "schema_name": self.schema_name,
            "prompt_bytes": len(self.prompt_bytes),
            "prompt_sha256": sha256(self.prompt_bytes),
            "messages_bytes": len(self.messages_bytes),
            "messages_sha256": sha256(self.messages_bytes),
            "structured_schema_bytes": len(self.schema_bytes),
            "structured_schema_sha256": sha256(self.schema_bytes),
            "response_format_bytes": len(self.response_format_bytes),
            "response_format_sha256": sha256(self.response_format_bytes),
            "response_format_envelope_bytes": self.response_format_envelope_bytes,
            "request_envelope_bytes": self.request_envelope_bytes,
            "request_body_bytes": len(self.body_bytes),
            "request_body_sha256": sha256(self.body_bytes),
        }


def build_openai_structured_request(
    *, dialect: str, endpoint: str, model: str, prompt: str,
    max_output_tokens: int, target_max_output_tokens: int,
    schema_name: str, schema: Mapping[str, Any],
) -> StructuredHTTPBody:
    """Purely build the exact OpenAI-compatible JSON Schema request body."""
    if dialect != OPENAI_CHAT_COMPLETIONS_JSON_SCHEMA:
        raise InferenceIntegrityError("structured output dialect is unsupported")
    try:
        parsed = urlsplit(endpoint)
    except (TypeError, ValueError) as error:
        raise InferenceIntegrityError("structured output endpoint is invalid") from error
    if parsed.path != "/v1/chat/completions" or parsed.query or parsed.fragment:
        raise InferenceIntegrityError(
            "OpenAI-compatible JSON Schema requires exact /v1/chat/completions endpoint",
        )
    if not isinstance(model, str) or not model or "\x00" in model:
        raise InferenceIntegrityError("structured output model is invalid")
    if not isinstance(prompt, str) or not prompt or "\x00" in prompt:
        raise InferenceIntegrityError("structured output prompt is invalid")
    if (
        type(max_output_tokens) is not int or max_output_tokens < 1
        or type(target_max_output_tokens) is not int
        or max_output_tokens > target_max_output_tokens
    ):
        raise InferenceIntegrityError("structured output token ceiling is invalid")
    if not isinstance(schema_name, str) or _SCHEMA_NAME.fullmatch(schema_name) is None:
        raise InferenceIntegrityError("structured output schema name is invalid")
    if not isinstance(schema, Mapping):
        raise InferenceIntegrityError("structured output schema is invalid")

    messages = [{"role": "user", "content": prompt}]
    response_format = {
        "type": "json_schema",
        "json_schema": {
            "name": schema_name,
            "strict": True,
            "schema": dict(schema),
        },
    }
    body = {
        "model": model,
        "messages": messages,
        "max_tokens": max_output_tokens,
        "response_format": response_format,
        "stream": False,
        "temperature": 0,
    }
    prompt_bytes = prompt.encode("utf-8")
    messages_bytes = _http_json_bytes(messages)
    schema_bytes = _http_json_bytes(schema)
    response_format_bytes = _http_json_bytes(response_format)
    body_bytes = _http_json_bytes(body)
    response_format_envelope_bytes = len(response_format_bytes) - len(schema_bytes)
    request_envelope_bytes = (
        len(body_bytes) - len(messages_bytes) - len(response_format_bytes)
    )
    if response_format_envelope_bytes < 0 or request_envelope_bytes < 0:
        raise InferenceIntegrityError("structured request component accounting failed")
    return StructuredHTTPBody(
        dialect, endpoint, schema_name, body_bytes, prompt_bytes,
        messages_bytes, schema_bytes, response_format_bytes,
        response_format_envelope_bytes, request_envelope_bytes,
    )


class FakeInferenceBackend:
    """Deterministic offline backend; explicit test authorization is required."""

    is_test_double = True

    def __init__(
        self, *, result: InferenceResult | None = None,
        failure: str | None = None,
    ):
        self.result = result or InferenceResult("{}", 1, 1, 0, True, wall_time_seconds=0, finish_reason="stop")
        self.failure = failure
        self.calls: list[dict[str, Any]] = []

    def preflight(self, target: InferenceTarget) -> Mapping[str, Any]:
        if target.backend_type != "fake":
            raise InferenceBackendError("BACKEND_FAILURE", "fake backend received another backend type", sent=False)
        return {"ready": True, "test_double": True, "network": False}

    def complete(self, request: InferenceRequest, target: InferenceTarget) -> InferenceResult:
        self.calls.append({"request_hash": request.request_hash, "target_id": target.target_id})
        if self.failure == "timeout":
            raise InferenceBackendError("TIMEOUT", "simulated timeout", sent=True)
        if self.failure == "backend_failure":
            raise InferenceBackendError("BACKEND_FAILURE", "simulated backend failure", sent=True)
        if self.failure == "pre_send_failure":
            raise InferenceBackendError("BACKEND_FAILURE", "simulated pre-send failure", sent=False)
        if self.failure == "crash_after_admission":
            raise RuntimeError("simulated crash after admission")
        if self.failure == "schema_invalid":
            return InferenceResult("not-json", 1, 1, 0, True, wall_time_seconds=0, finish_reason="stop")
        return self.result


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        return None


class LocalOpenAICompatibleBackend:
    """Bounded OpenAI-compatible HTTP client restricted to explicit loopback."""

    is_test_double = False

    def __init__(
        self, *, project_root: str | Path | None = None,
        max_response_bytes: int = 1_048_576,
        structured_output_dialect: str | None = None,
    ):
        if type(max_response_bytes) is not int or max_response_bytes < 1024:
            raise ValueError("max_response_bytes must be an integer >= 1024")
        self.max_response_bytes = max_response_bytes
        self.project_root = None if project_root is None else Path(project_root).resolve()
        if (
            structured_output_dialect is not None
            and structured_output_dialect not in STRUCTURED_OUTPUT_DIALECTS
        ):
            raise ValueError("structured_output_dialect is unsupported")
        self.structured_output_dialect = structured_output_dialect
        self._opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect())

    def preflight(self, target: InferenceTarget) -> Mapping[str, Any]:
        if target.backend_type != "local_openai_compatible" or not target.local or target.endpoint is None:
            raise InferenceBackendError("BACKEND_FAILURE", "local backend target is invalid", sent=False)
        # ModelRegistry already validates scheme, authority, and exact loopback
        # host. Repeat the security-sensitive checks at the execution boundary.
        from urllib.parse import urlsplit
        parsed = urlsplit(target.endpoint)
        if parsed.scheme not in {"http", "https"} or (parsed.hostname or "").lower() not in {"127.0.0.1", "localhost", "::1"}:
            raise InferenceBackendError("BACKEND_FAILURE", "local endpoint is not loopback", sent=False)
        if target.timeout_seconds <= 0:
            raise InferenceBackendError("BACKEND_FAILURE", "local timeout is invalid", sent=False)
        if (
            "structured_output" in target.capabilities
            and self.structured_output_dialect is None
        ):
            raise InferenceBackendError(
                "BACKEND_FAILURE", "structured output dialect is not explicit", sent=False,
            )
        return {
            "ready": True, "test_double": False, "network": "loopback_only",
            "redirects": False,
            "structured_output_dialect": self.structured_output_dialect,
        }

    @staticmethod
    def _integer(value: Any) -> int | None:
        return value if type(value) is int and 0 <= value <= 2**63 - 1 else None

    def complete(self, request: InferenceRequest, target: InferenceTarget) -> InferenceResult:
        self.preflight(target)
        if len(request.prompt.encode("utf-8")) > max(4096, target.context_limit * 16):
            raise InferenceBackendError("BACKEND_FAILURE", "prompt exceeds the target request bound", sent=False)
        body: bytes
        if "structured_output" in target.capabilities:
            if self.project_root is None:
                raise InferenceBackendError(
                    "BACKEND_FAILURE",
                    "structured output requires an explicit project root",
                    sent=False,
                )
            try:
                schema = model_output_schema(self.project_root, request)
            except InferenceIntegrityError as error:
                raise InferenceBackendError(
                    "BACKEND_FAILURE", "structured output schema is unavailable or unsafe",
                    sent=False,
                ) from error
            suffix = ".schema.json"
            raw_name = request.requested_output_schema
            schema_name = (
                raw_name[:-len(suffix)] if raw_name.endswith(suffix)
                else Path(raw_name).stem
            ).replace("-", "_")
            try:
                structured = build_openai_structured_request(
                    dialect=str(self.structured_output_dialect),
                    endpoint=str(target.endpoint), model=target.model,
                    prompt=request.prompt,
                    max_output_tokens=request.max_output_tokens,
                    target_max_output_tokens=target.max_output_tokens,
                    schema_name=schema_name, schema=schema,
                )
            except InferenceIntegrityError as error:
                raise InferenceBackendError(
                    "BACKEND_FAILURE", "structured request contract is invalid",
                    sent=False,
                ) from error
            body = structured.body_bytes
        elif "structured_output" in request.required_capabilities:
            raise InferenceBackendError(
                "ROUTE_CAPABILITY_INSUFFICIENT",
                "target does not support the requested structured output",
                sent=False,
            )
        else:
            body = _http_json_bytes({
                "model": target.model,
                "messages": [{"role": "user", "content": request.prompt}],
                "max_tokens": request.max_output_tokens,
                "stream": False,
            })
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if target.api_key_env is not None:
            secret = os.environ.get(target.api_key_env)
            if not secret:
                raise InferenceBackendError("BACKEND_FAILURE", "configured credential environment variable is unavailable", sent=False)
            headers["Authorization"] = "Bearer " + secret
        http_request = urllib.request.Request(target.endpoint, data=body, headers=headers, method="POST")
        started = time.monotonic()
        try:
            with self._opener.open(http_request, timeout=target.timeout_seconds) as response:
                raw = response.read(self.max_response_bytes + 1)
                if len(raw) > self.max_response_bytes:
                    raise InferenceBackendError("BACKEND_FAILURE", "backend response exceeds size limit", sent=True)
        except urllib.error.HTTPError as error:
            raise InferenceBackendError("BACKEND_FAILURE", f"local backend returned HTTP {error.code}", sent=True) from error
        except (TimeoutError, socket.timeout) as error:
            raise InferenceBackendError("TIMEOUT", "local backend timed out", sent=True) from error
        except (http.client.RemoteDisconnected, ConnectionResetError, BrokenPipeError) as error:
            raise InferenceBackendError("BACKEND_FAILURE", "local backend closed the connection", sent=True) from error
        except urllib.error.URLError as error:
            if isinstance(error.reason, (TimeoutError, socket.timeout)):
                raise InferenceBackendError("TIMEOUT", "local backend timed out", sent=True) from error
            raise InferenceBackendError("BACKEND_FAILURE", "local backend connection failed", sent=True) from error
        elapsed = max(0, math.ceil(time.monotonic() - started))
        try:
            envelope = json.loads(raw.decode("utf-8"))
            choices = envelope["choices"]
            choice = choices[0]
            content = choice["message"]["content"]
            finish = choice.get("finish_reason") or "unknown"
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError, IndexError, TypeError) as error:
            raise InferenceBackendError("BACKEND_FAILURE", "local backend response envelope is malformed", sent=True) from error
        if not isinstance(content, str):
            raise InferenceBackendError("BACKEND_FAILURE", "local backend content is invalid", sent=True)
        normalized_finish = {"stop": "stop", "length": "length", "tool_calls": "tool_call", "tool_call": "tool_call"}.get(finish, "unknown")
        usage = envelope.get("usage")
        input_tokens = output_tokens = cache_tokens = None
        usage_available = False
        if isinstance(usage, Mapping):
            input_tokens = self._integer(usage.get("prompt_tokens"))
            output_tokens = self._integer(usage.get("completion_tokens"))
            details = usage.get("prompt_tokens_details")
            cache_tokens = self._integer(details.get("cached_tokens")) if isinstance(details, Mapping) else 0
            usage_available = input_tokens is not None and output_tokens is not None and cache_tokens is not None
            if not usage_available:
                input_tokens = output_tokens = cache_tokens = None
        return InferenceResult(
            content, input_tokens, output_tokens, cache_tokens,
            usage_available, wall_time_seconds=elapsed,
            finish_reason=normalized_finish,
        )


class RemoteOpenAICompatibleBackend(LocalOpenAICompatibleBackend):
    """Bounded HTTPS client with redirects and environment proxies disabled."""

    is_test_double = False

    def preflight(self, target: InferenceTarget) -> Mapping[str, Any]:
        if target.backend_type != "remote_openai_compatible" or target.local or target.endpoint is None:
            raise InferenceBackendError("BACKEND_FAILURE", "remote backend target is invalid", sent=False)
        from urllib.parse import urlsplit
        parsed = urlsplit(target.endpoint)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username is not None or parsed.password is not None:
            raise InferenceBackendError("BACKEND_FAILURE", "remote endpoint must be explicit HTTPS", sent=False)
        if target.api_key_env is None:
            raise InferenceBackendError("BACKEND_FAILURE", "remote target lacks a credential environment variable name", sent=False)
        if target.timeout_seconds <= 0:
            raise InferenceBackendError("BACKEND_FAILURE", "remote timeout is invalid", sent=False)
        return {
            "ready": os.environ.get(target.api_key_env) is not None,
            "test_double": False,
            "network": "explicit_https_only",
            "redirects": False,
            "proxies": False,
            "credential_source": "environment",
        }


__all__ = [
    "FakeInferenceBackend", "LocalOpenAICompatibleBackend",
    "OPENAI_CHAT_COMPLETIONS_JSON_SCHEMA", "RemoteOpenAICompatibleBackend",
    "STRUCTURED_OUTPUT_DIALECTS", "StructuredHTTPBody",
    "build_openai_structured_request",
]
