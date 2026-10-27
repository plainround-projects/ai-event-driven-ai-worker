# Hashing with SHA-256 (hashlib)

## What it is

A *hash function* turns any data into a short fixed-size fingerprint. SHA-256 gives 64 hexadecimal characters. The same input always gives the same fingerprint; a one-character change gives a completely different one; and you cannot get the input back from the fingerprint. Python's `hashlib` module provides it.

## Why this repository uses it

Three jobs need a fingerprint. Webhook signatures use SHA-256 inside an HMAC. Dead letters store a 12-character SHA-256 prefix of the payload, so two entries can be compared without displaying the raw email. Recorded model replies are keyed by a hash of the whole request.

## Where it appears

| File | What it does with Hashing with SHA-256 (hashlib) |
| --- | --- |
| `src/inbox_worker/domain/events.py` | hashes text with SHA-256 |
| `src/inbox_worker/domain/signature.py` | hashes text with SHA-256 |
| `src/inbox_worker/infrastructure/cassette.py` | hashes text with SHA-256 |
| `src/inbox_worker/infrastructure/postgres.py` | hashes text with SHA-256 |

## How it works underneath

`hashlib.sha256(data).hexdigest()` takes bytes (not text; text is encoded first, here as UTF-8) and returns the fingerprint as text. Because the output is fixed-size and practically unique, programs use hashes for several jobs: to detect that a file changed, to key a cache by its input, to chain records so that editing one breaks all later ones, and to store a password-like token without keeping the token itself.

Every repository here uses SHA-256 for the purposes shown in the walkthrough. A hash is not encryption (nothing is hidden or recoverable) and not, by itself, proof of who wrote the data; for that a *keyed* hash such as HMAC is used (see the HMAC note where it applies).

## Walkthrough of this repository's use

### `src/inbox_worker/domain/events.py`

The function's docstring (left out of the listing) says: *The event id a receiver files a payload under; a payload that is not an event gets a stable placeholder so it can still be queued, parked and shown to a person.*

```python
def event_id_of(payload: str) -> str:
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        data = None
    if isinstance(data, dict) and isinstance(data.get("event_id"), str) and data["event_id"].strip():
        return str(data["event_id"]).strip()
    return "unparsed-" + hashlib.sha256(payload.encode("utf-8", "replace")).hexdigest()[:12]
```

- `def event_id_of(payload: str) -> str:`: The function `event_id_of`.
- `try:`: Another line of the function (a statement or a continuation of the one above).
- `data = json.loads(payload)`: Stores `json.loads(payload)` in `data`.
- `except json.JSONDecodeError:`: Another line of the function (a statement or a continuation of the one above).
- `data = None`: Stores `None` in `data`.
- `if isinstance(data, dict) and isinstance(data.get("event_id"), str) and data["event_id"].strip():`: Another line of the function (a statement or a continuation of the one above).
- `return str(data["event_id"]).strip()`: Gives back `str(data["event_id"]).strip()`.
- `return "unparsed-" + hashlib.sha256(payload.encode("utf-8", "replace")).hexdigest()[:12]`: Gives back `"unparsed-" + hashlib.sha256(payload.encode("utf-8", "replace")).hexdigest()[:12]`.

### `src/inbox_worker/domain/signature.py`

The function's docstring (left out of the listing) says: *The signature a sender attaches. Signing the timestamp too is what stops a captured request being replayed later.*

```python
def sign(secret: bytes, timestamp: float, body: str) -> str:
    return hmac.new(secret, f"{int(timestamp)}.{body}".encode(), hashlib.sha256).hexdigest()
```

- `def sign(secret: bytes, timestamp: float, body: str) -> str:`: The function `sign`.
- `return hmac.new(secret, f"{int(timestamp)}.{body}".encode(), hashlib.sha256).hexdigest()`: Gives back `hmac.new(secret, f"{int(timestamp)}.{body}".encode(), hashlib.sha256).hexdigest()`.

### `src/inbox_worker/infrastructure/cassette.py`

The function's docstring (left out of the listing) says: *Hash of everything that decides the reply.*

```python
def request_key(model_id: str, system: str, user: str, prompt_version: str) -> str:
    return hashlib.sha256(json.dumps([model_id, prompt_version, system, user]).encode()).hexdigest()
```

- `def request_key(model_id: str, system: str, user: str, prompt_version: str) -> str:`: The function `request_key`.
- `return hashlib.sha256(json.dumps([model_id, prompt_version, system, user]).encode()).hexdigest()`: `hashlib.sha256(DATA)` computes the SHA-256 hash of the bytes `DATA`; `.hexdigest()` writes it as 64 hexadecimal characters. `DATA` here is `json.dumps([model_id, prompt_version, system, user]).encode()`.

### `src/inbox_worker/infrastructure/postgres.py`

The function's docstring (left out of the listing) says: *Park the delivery with what a person needs to act; both writes are one transaction.*

```python
    def dead_letter(self, delivery: Delivery, reason: str, error: str) -> None:
        digest = hashlib.sha256(delivery.payload.encode("utf-8", "replace")).hexdigest()[:12]
        with self._database.connection() as connection, connection.transaction():
            connection.execute(
                "INSERT INTO dead_letters (event_id, reason, attempts, last_error, payload_hash, payload) VALUES (%s, %s, %s, %s, %s, %s)",
                (delivery.event_id, reason, delivery.attempts, error, digest, delivery.payload),
            )
            connection.execute(
                "UPDATE deliveries SET status = 'dead', locked_until = NULL, last_error = %s WHERE delivery_id = %s",
                (error, delivery.delivery_id),
            )
```

- `def dead_letter(self, delivery: Delivery, reason: str, error: str) -> None:`: The function `dead_letter`.
- `digest = hashlib.sha256(delivery.payload.encode("utf-8", "replace")).hexdigest()[:12]`: Stores `hashlib.sha256(delivery.payload.encode("utf-8", "replace")).hexdigest()[:12]` in `digest`.
- `with self._database.connection() as connection, connection.transaction():`: Another line of the function (a statement or a continuation of the one above).
- `connection.execute(`: Another line of the function (a statement or a continuation of the one above).
- `"INSERT INTO dead_letters (event_id, reason, attempts, last_error, payload_hash, payload) VALUES (%s, %s, %s, %s, %s, %s)",`: Another line of the function (a statement or a continuation of the one above).
- `(delivery.event_id, reason, delivery.attempts, error, digest, delivery.payload),`: Another line of the function (a statement or a continuation of the one above).
- `connection.execute(`: Another line of the function (a statement or a continuation of the one above).
- `"UPDATE deliveries SET status = 'dead', locked_until = NULL, last_error = %s WHERE delivery_id = %s",`: Another line of the function (a statement or a continuation of the one above).
- `(error, delivery.delivery_id),`: Another line of the function (a statement or a continuation of the one above).

## Try it yourself

Run these from the repository folder (after `make up`).

```bash
python3 -c "import hashlib; print(hashlib.sha256(b'abc').hexdigest())"
```

Prints `ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad`, the well-known SHA-256 of the three bytes `abc`. Run it twice: always the same.

```bash
python3 -c "import hashlib; print(hashlib.sha256(b'abd').hexdigest())"
```

One character different, a completely different fingerprint.

## Mistakes people make

- Hashing text without fixing the encoding. The code encodes explicitly to UTF-8.
- Joining fields without a separator, so different field splits give the same text (`ab`+`c` and `a`+`bc`). The audit chain uses a separator character that data cannot contain.
- Thinking a short truncated hash is as safe as the full one. Truncated hashes shown in reports are labels for people, not security.
- Using a hash alone to protect a password. Real password storage needs a slow, salted hash.
- Comparing hashes with a timing-leaky check where an attacker could exploit it (the signature check uses a constant-time comparison).

## Check yourself

1. Can you recover the input from a SHA-256 hash?
   *Answer:* No. It is a one-way function.
2. What changes if one character of the input changes?
   *Answer:* The whole hash changes.
3. Why must you encode text to bytes first?
   *Answer:* Hash functions work on bytes, and different encodings give different bytes.
4. What is a hash chain?
   *Answer:* Records where each one includes the hash of the previous one, so any edit breaks every later link.
5. Is a hash the same as encryption?
   *Answer:* No. Nothing is hidden and nothing can be decrypted.

## Further reading

- [hashlib](https://docs.python.org/3.12/library/hashlib.html)
- [FIPS 180-4, the SHA standard](https://csrc.nist.gov/pubs/fips/180-4/upd1/final)
