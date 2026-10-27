"""Prompts as files: a two-fence header (version, owner), then the prompt text."""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple


class PromptFileError(ValueError):
    """A prompt file does not have the two-fence header with a version and an owner."""


class PromptFile(NamedTuple):
    """A versioned prompt."""

    version: str
    owner: str
    text: str


def read_prompt(path: Path) -> PromptFile:
    """Read `---`, header lines, `---`, then the prompt text; both fences are required."""
    parts = path.read_text(encoding="utf-8").split("---\n", 2)
    if len(parts) != 3 or parts[0].strip():
        raise PromptFileError(f"{path.name}: expected a leading '---' fence, a header and a closing '---' fence")
    fields = dict(line.split(": ", 1) for line in parts[1].strip().splitlines() if ": " in line)
    for required in ("version", "owner"):
        if required not in fields:
            raise PromptFileError(f"{path.name}: header lacks {required}")
    return PromptFile(fields["version"], fields["owner"], parts[2].strip())
