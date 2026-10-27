"""The real adapter: Claude through the official SDK. The key comes from the environment, never from code."""

from __future__ import annotations

from typing import Any

import anthropic

from inbox_worker.application.ports import ModelReply
from inbox_worker.domain.errors import ModelCallError, RetryableModelError
from inbox_worker.infrastructure.environment import ConfigurationError


class ClaudeModel:
    """One Messages API call per request. Rate limits, server errors, timeouts and dropped connections are retryable."""

    def __init__(
        self, model_id: str, api_key: str | None, *, timeout_seconds: float = 30.0, client: Any = None
    ) -> None:
        if client is None:
            if not api_key:
                raise ConfigurationError("ANTHROPIC_API_KEY must be set to use the Claude adapter")
            client = anthropic.Anthropic(api_key=api_key, timeout=timeout_seconds, max_retries=0)
        self._client = client
        self._model_id = model_id

    def complete(self, system: str, user: str, prompt_version: str) -> ModelReply:
        """Send the prompt as the system text and the email as the user message."""
        try:
            message = self._client.messages.create(
                model=self._model_id, max_tokens=300, system=system, messages=[{"role": "user", "content": user}]
            )
        except (anthropic.RateLimitError, anthropic.APITimeoutError, anthropic.APIConnectionError) as error:
            raise RetryableModelError(f"{type(error).__name__}: {error}") from error
        except anthropic.APIStatusError as error:
            if error.status_code >= 500:
                raise RetryableModelError(f"{type(error).__name__}: {error}") from error
            raise ModelCallError(f"{type(error).__name__}: {error}") from error
        if message.stop_reason == "refusal":
            raise ModelCallError("the model declined the request (stop_reason=refusal)")
        text = "".join(block.text for block in message.content if block.type == "text")
        return ModelReply(text, message.model, message.usage.input_tokens, message.usage.output_tokens)
