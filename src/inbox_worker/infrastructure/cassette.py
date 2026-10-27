"""Recorded model replies: a cassette maps a hash of the whole request to the reply, so tests run offline."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from inbox_worker.application.ports import ChatModel, ModelReply


class MissingRecordingError(LookupError):
    """No recording matches this request; the message says how to re-record."""


def request_key(model_id: str, system: str, user: str, prompt_version: str) -> str:
    """Hash of everything that decides the reply."""
    return hashlib.sha256(json.dumps([model_id, prompt_version, system, user]).encode()).hexdigest()


class RecordedModel:
    """Replays replies from a cassette file; a request with no recording fails loudly."""

    def __init__(self, path: Path) -> None:
        data = json.loads(path.read_text(encoding="utf-8"))
        self.model_id: str = data["model"]
        self.provenance: str = data["provenance"]
        self._entries: dict[str, dict[str, Any]] = data["entries"]

    def complete(self, system: str, user: str, prompt_version: str) -> ModelReply:
        """The recorded reply for this exact request."""
        key = request_key(self.model_id, system, user, prompt_version)
        entry = self._entries.get(key)
        if entry is None:
            raise MissingRecordingError(
                f"no recording for prompt {prompt_version} (key {key[:12]}); re-record with `make record` (needs ANTHROPIC_API_KEY)"
            )
        return ModelReply(entry["text"], self.model_id, int(entry["input_tokens"]), int(entry["output_tokens"]))


class RecordingModel:
    """Wraps a real model and writes every reply to a cassette, keyed like `RecordedModel` expects."""

    def __init__(self, inner: ChatModel, path: Path, model_id: str, provenance: str) -> None:
        self._inner = inner
        self._path = path
        self._model_id = model_id
        self._provenance = provenance
        self._entries: dict[str, dict[str, Any]] = {}

    def complete(self, system: str, user: str, prompt_version: str) -> ModelReply:
        """Call the wrapped model, remember the reply and rewrite the cassette."""
        reply = self._inner.complete(system, user, prompt_version)
        self._entries[request_key(self._model_id, system, user, prompt_version)] = {
            "text": reply.text,
            "input_tokens": reply.input_tokens,
            "output_tokens": reply.output_tokens,
        }
        document = {"provenance": self._provenance, "model": self._model_id, "entries": self._entries}
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(document, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        return reply
