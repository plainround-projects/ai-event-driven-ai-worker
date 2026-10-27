"""The sample inbox: 1,000 email events with unique ids, 2% delivered twice and 1% poison, from a seed."""

from __future__ import annotations

import base64
import json
import random
from dataclasses import dataclass

from inbox_worker.domain.events import POISON_MARKER

TEMPLATES = (
    "Hi, please cancel order {n}. I ordered it by mistake.",
    "I would like my money back for order {n}, it arrived damaged.",
    "Where is my order {n}? It has not arrived yet.",
    "This is unacceptable, order {n} is late again and I want a refund.",
    "Could you cancel {n}? I found it cheaper elsewhere.",
    "Can I get the tracking for order {n}, please?",
)
POISON_KINDS = (
    "malformed_body",
    "malformed_body",
    "malformed_body",
    "too_large",
    "too_large",
    "too_large",
    "bad_encoding",
    "bad_encoding",
    "schema_failure",
    "schema_failure",
)


@dataclass(frozen=True, slots=True)
class GeneratedInbox:
    """The deliveries in arrival order, and what was planted: duplicates and poison by event id."""

    deliveries: tuple[tuple[str, str], ...]
    duplicates: frozenset[str]
    poison: dict[str, str]


def _payload(event_id: str, body: str) -> str:
    return json.dumps({"event_id": event_id, "body": body})


def generate_events(
    count: int = 1000, seed: int = 2610, duplicate_rate: float = 0.02, poison_rate: float = 0.01
) -> GeneratedInbox:
    """`count` events, `duplicate_rate` of them delivered twice, `poison_rate` of them unprocessable."""
    rng = random.Random(seed)
    poison_count = round(count * poison_rate)
    poison_slots = set(rng.sample(range(count), poison_count))
    kinds = list(POISON_KINDS[:poison_count])
    rng.shuffle(kinds)
    deliveries: list[tuple[str, str]] = []
    poison: dict[str, str] = {}
    for number in range(count):
        event_id = f"e-{number + 1:04d}"
        if number in poison_slots:
            kind = kinds.pop()
            poison[event_id] = kind
            if kind == "malformed_body":
                deliveries.append((event_id, '{"event_id": "' + event_id + '", "body": '))
            elif kind == "too_large":
                deliveries.append((event_id, _payload(event_id, "Please cancel order 4417. " + "x" * 300_000)))
            elif kind == "bad_encoding":
                broken = base64.b64encode(b"Please cancel order 4417 \xff\xfe\xfa").decode()
                deliveries.append((event_id, json.dumps({"event_id": event_id, "body_b64": broken})))
            else:
                deliveries.append((event_id, _payload(event_id, f"{POISON_MARKER} please cancel order 4417.")))
        else:
            deliveries.append((event_id, _payload(event_id, rng.choice(TEMPLATES).format(n=rng.randint(1000, 9999)))))
    healthy = [event_id for event_id, _ in deliveries if event_id not in poison]
    repeated = frozenset(rng.sample(healthy, round(count * duplicate_rate)))
    by_id = dict(deliveries)
    result = list(deliveries)
    for event_id in sorted(repeated):
        result.insert(
            rng.randint(result.index((event_id, by_id[event_id])) + 1, len(result)), (event_id, by_id[event_id])
        )
    return GeneratedInbox(tuple(result), repeated, poison)
