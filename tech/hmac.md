# HMAC signatures (hmac)

## What it is

An *HMAC* is a hash computed with a secret key. Only someone who knows the key can produce the right value for a message, so it proves two things: the message was not changed, and it came from someone holding the key. The webhook uses it to reject forged and tampered requests.

## Why this repository uses it

The webhook is open to the internet, so any caller could post a forged or replayed event. An HMAC over the timestamp and body proves the sender holds the secret and the request is fresh. The model is not on this path, which is what keeps the endpoint fast.

## Where it appears

| File | What it does with HMAC signatures (hmac) |
| --- | --- |
| `src/inbox_worker/domain/signature.py` | `sign` and `verify` |
| `src/inbox_worker/interfaces/webhook.py` | calls `verify` on every request |
| `src/inbox_worker/interfaces/cli.py` | `webhook-demo` and `bench-webhook` sign requests |

## How it works underneath

The sender computes `HMAC-SHA256(key, timestamp + "." + body)` and sends the result in a header. The receiver recomputes it with its own copy of the key and compares. Including the *timestamp* inside the signed text, and rejecting requests older than five minutes, stops a captured valid request from being sent again later (a *replay*). The comparison uses `hmac.compare_digest`, which takes the same time however many leading characters match, so an attacker cannot learn the signature one character at a time by measuring response times. The two rejection reasons are kept distinct (`signature mismatch` and `request too old`) so a person reading the log knows which attack or mistake it was.

## Walkthrough of this repository's use

The whole signature module:

From `src/inbox_worker/domain/signature.py`:

```python
MAX_AGE_SECONDS = 300
TAMPERED = "signature mismatch (tampered or wrong secret)"
TOO_OLD = "request too old (replay rejected)"
BAD_TIMESTAMP = "timestamp is not a number"
```

- `MAX_AGE_SECONDS = 300`: The longest age of a request the receiver accepts: 300 seconds, five minutes.
- `TAMPERED = "signature mismatch (tampered or wrong secret)"`: The fixed reason text for a wrong signature.
- `TOO_OLD = "request too old (replay rejected)"`: The fixed reason text for an old request.
- `BAD_TIMESTAMP = "timestamp is not a number"`: The fixed reason text for a timestamp that is not a number.

```python
def sign(secret: bytes, timestamp: float, body: str) -> str:
    """The signature a sender attaches. Signing the timestamp too is what stops a captured request being replayed later."""
    return hmac.new(secret, f"{int(timestamp)}.{body}".encode(), hashlib.sha256).hexdigest()
```

- `def sign(secret: bytes, timestamp: float, body: str) -> str:`: Computes the signature a sender attaches. `secret` is bytes (a secret key), `timestamp` the time of sending in seconds, `body` the request text.
- `"""The signature a sender attaches. Signing the timestamp too is what stops a captured request being replayed later."""`: The docstring: signing the timestamp too is what stops a captured request being replayed later.
- `return hmac.new(secret, f"{int(timestamp)}.{body}".encode(), hashlib.sha256).hexdigest()`: `hmac.new(key, message, digest)` computes the HMAC. The message is the timestamp (as a whole number), a dot and the body, encoded to bytes: signing both together binds the signature to the moment it was made. `hashlib.sha256` is the hash function used inside the HMAC. `.hexdigest()` writes the result as 64 hexadecimal characters.

```python
def verify(secret: bytes, timestamp: str, body: str, signature: str, now: float) -> tuple[bool, str]:
    """(ok, reason). Age is checked first and cheaply; the comparison is constant-time."""
    try:
        sent_at = float(timestamp)
    except ValueError:
        return False, BAD_TIMESTAMP
    if abs(now - sent_at) > MAX_AGE_SECONDS:
        return False, TOO_OLD
    if not hmac.compare_digest(sign(secret, sent_at, body), signature):
        return False, TAMPERED
    return True, "ok"
```

- `def verify(secret: bytes, timestamp: str, body: str, signature: str, now: float) -> tuple[bool, str]:`: Checks a received request. It returns a pair: whether it is acceptable, and the reason.
- `"""(ok, reason). Age is checked first and cheaply; the comparison is constant-time."""`: The docstring: the age is checked first, cheaply, and the comparison takes constant time.
- `try:`: Guards the number conversion.
- `sent_at = float(timestamp)`: The timestamp arrives as header text; turn it into a number.
- `except ValueError:`: It was not a number.
- `return False, BAD_TIMESTAMP`: Reject with that reason.
- `if abs(now - sent_at) > MAX_AGE_SECONDS:`: `abs(...)` ignores the sign, so a timestamp too far in the past *or* the future is refused. This check comes before the signature so old requests are refused cheaply.
- `return False, TOO_OLD`: Reject: `request too old (replay rejected)`.
- `if not hmac.compare_digest(sign(secret, sent_at, body), signature):`: Recomputes the signature and compares it with the received one using `hmac.compare_digest`, which takes the same time however many leading characters match, so response times reveal nothing about the correct signature.
- `return False, TAMPERED`: Reject: `signature mismatch (tampered or wrong secret)`.
- `return True, "ok"`: Accept.

## Try it yourself

Run these from the repository folder (after `make up`).

```bash
make webhook-demo
```

Prints three lines: `valid request: (True, 'ok')`, `tampered body: (False, 'signature mismatch (tampered or wrong secret)')`, `replayed old request: (False, 'request too old (replay rejected)')`.

```bash
.venv/bin/pytest tests/unit/domain -q -k signature
```

Runs the signature tests.

```bash
python3 -c "import hmac,hashlib; print(hmac.new(b'key', b'1.body', hashlib.sha256).hexdigest())"
```

Prints a 64-character signature; change one letter of the key and it changes completely.

## Mistakes people make

- Signing the body but not the timestamp; a valid request could be replayed forever.
- Comparing signatures with `==`, which leaks timing.
- Putting the secret in the code. It is a setting; the committed value is only a placeholder for local use.
- Rejecting with one vague error, which makes debugging hard.
- Having no way to rotate the key; a production system accepts two keys during a change.

## Check yourself

1. What does an HMAC prove?
   *Answer:* The message is unchanged and was made by someone who knows the key.
2. Why is the timestamp part of the signed text?
   *Answer:* So an old captured request cannot be replayed.
3. Why `compare_digest`?
   *Answer:* It compares in constant time, so timing reveals nothing.
4. How old may a request be?
   *Answer:* Five minutes.
5. Is an HMAC encryption?
   *Answer:* No. The message is not hidden; it is authenticated.

## Further reading

- [hmac](https://docs.python.org/3.12/library/hmac.html)
- [RFC 2104: HMAC](https://www.rfc-editor.org/rfc/rfc2104)
