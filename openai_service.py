"""Minimal, UI-independent OpenAI Responses API service."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping, Sequence
from typing import Any, Protocol

from openai import APIConnectionError, APIError, APITimeoutError, OpenAI


DEFAULT_OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5-mini")
DEFAULT_TIMEOUT_SECONDS = 30.0
DEFAULT_MAX_RETRIES = 1


class OpenAIServiceError(RuntimeError):
    """A safe, user-presentable OpenAI service failure."""


class ResponsesClient(Protocol):
    responses: Any


def _streamlit_secret(name: str) -> str | None:
    """Read an optional Streamlit secret without requiring a secrets file."""
    try:
        import streamlit as st

        value = st.secrets.get(name)
    except Exception:
        return None
    return str(value).strip() if value else None


def get_openai_api_key() -> str | None:
    """Resolve the API key from the environment, then Streamlit secrets."""
    environment_value = os.getenv("OPENAI_API_KEY", "").strip()
    return environment_value or _streamlit_secret("OPENAI_API_KEY")


def _structured_context_text(context: Any) -> str:
    if context is None:
        return ""
    if isinstance(context, str):
        return context.strip()
    if isinstance(context, Mapping) or (
        isinstance(context, Sequence) and not isinstance(context, (bytes, bytearray))
    ):
        return json.dumps(context, ensure_ascii=False, sort_keys=True, default=str)
    return str(context).strip()


def generate_text(
    prompt: str,
    context: Any = None,
    *,
    model: str = DEFAULT_OPENAI_MODEL,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    max_output_tokens: int | None = None,
    client: ResponsesClient | None = None,
) -> str:
    """Generate text from a prompt and optional structured context.

    The optional client is intended for credential-free tests. Production calls
    create the official SDK client only when this function is explicitly invoked.
    """
    clean_prompt = str(prompt or "").strip()
    if not clean_prompt:
        raise OpenAIServiceError("A prompt is required before text can be generated.")

    if client is None:
        api_key = get_openai_api_key()
        if not api_key:
            raise OpenAIServiceError(
                "OpenAI is not configured. Set OPENAI_API_KEY in the environment or Streamlit secrets."
            )
        client = OpenAI(
            api_key=api_key,
            timeout=timeout_seconds,
            max_retries=DEFAULT_MAX_RETRIES,
        )

    context_text = _structured_context_text(context)
    request_input = clean_prompt
    if context_text:
        request_input = f"Structured context:\n{context_text}\n\nTask:\n{clean_prompt}"

    request_options: dict[str, Any] = {"model": model, "input": request_input}
    if max_output_tokens is not None:
        request_options["max_output_tokens"] = max(1, int(max_output_tokens))

    try:
        response = client.responses.create(**request_options)
    except APITimeoutError as exc:
        raise OpenAIServiceError("OpenAI did not respond before the request timed out.") from exc
    except APIConnectionError as exc:
        raise OpenAIServiceError("OpenAI could not be reached. Please try again later.") from exc
    except APIError as exc:
        raise OpenAIServiceError("OpenAI could not complete the request. Please try again later.") from exc

    output_text = str(getattr(response, "output_text", "") or "").strip()
    if not output_text:
        raise OpenAIServiceError("OpenAI returned an empty response. Please try again.")
    return output_text
