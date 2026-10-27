"""Opt-in: calls the real model with one email. Run with `make test-live` (RUN_LIVE=1 and ANTHROPIC_API_KEY set)."""

import os
from pathlib import Path

import pytest

from inbox_worker.infrastructure.claude_model import ClaudeModel
from inbox_worker.infrastructure.prompt_file import read_prompt

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(
        os.environ.get("RUN_LIVE") != "1" or not os.environ.get("ANTHROPIC_API_KEY"),
        reason="set RUN_LIVE=1 and ANTHROPIC_API_KEY to call the real model",
    ),
]


def test_the_real_model_extracts_a_valid_ticket_from_a_cancel_email():
    from inbox_worker.application.extraction import TicketExtractor

    prompt = read_prompt(Path(__file__).resolve().parents[2] / "prompts/extract.v1.md")
    model = ClaudeModel(os.environ.get("MODEL_ID", "claude-haiku-5-5"), os.environ["ANTHROPIC_API_KEY"])
    result = TicketExtractor(model, prompt.text, prompt.version).extract(
        "Hi, please cancel order 4417, it was a mistake."
    )
    assert result.ticket.intent == "cancel" and result.ticket.order_number == "4417" and result.calls <= 2
