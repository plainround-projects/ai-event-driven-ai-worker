# JSON

## What it is

JSON (JavaScript Object Notation) is the most common text format for passing structured data between programs. It has objects (`{"key": value}`), arrays (`[1, 2, 3]`), strings in double quotes, numbers, `true`, `false` and `null`. Almost every language can read and write it.

## Why this repository uses it

The only JSON file is the cassette of recorded model replies: data that is read by tests and by `make smoke`. JSON parses to plain dicts and lists.

## Where it appears

| File | What it does with JSON |
| --- | --- |
| `.import_linter_cache/feec310ddd2b588994c4a0f9238b29edbad63bb2.data.json` | JSON data |
| `.import_linter_cache/inbox_worker.meta.json` | JSON data |
| `.omc/state/sessions/6f28b667-1b81-4d8d-a94e-9da4a754b10a/pre-tool-advisory-throttle.json` | JSON data |
| `src/inbox_worker/.omc/state/sessions/6f28b667-1b81-4d8d-a94e-9da4a754b10a/pre-tool-advisory-throttle.json` | JSON data |
| `tests/fixtures/cassettes/smoke-v1.json` | Twenty recorded-style replies for the smoke run, keyed by a hash of the whole request |

## How it works underneath

A JSON file is just text. A program *parses* it: it reads the characters and builds the matching in-memory structure (in Python: `dict`, `list`, `str`, `int`/`float`, `bool`, `None`). Going the other way is *serialising* (`json.dumps`). The rules are strict: keys must be double-quoted strings, no trailing commas, no comments. Numbers have no exact decimal type, so money is kept as text or integers of cents in this repository when exactness matters.

Python's `json` module does the parsing: `json.loads(text)` for a string, `json.dumps(value)` back to text. Text must be UTF-8. `sort_keys=True` and a fixed `indent` make the output stable, so two runs produce identical files that Git can compare.

## Walkthrough of this repository's use

### `.omc/state/sessions/6f28b667-1b81-4d8d-a94e-9da4a754b10a/pre-tool-advisory-throttle.json`



One JSON object. Top-level keys: `version`, `entries`, `updated_at`. Overview (nested values are summarised):

```json
{
  "version": 1,
  "entries": "<dict of 1>",
  "updated_at": "2026-10-27T04:34:36.630Z"
}
```

### `tests/fixtures/cassettes/smoke-v1.json`

Twenty recorded-style replies for the smoke run, keyed by a hash of the whole request. Its `provenance` field says they were authored from the fake model, not recorded from a real one.

One JSON object. Top-level keys: `entries`, `model`, `provenance`. Overview (nested values are summarised):

```json
{
  "entries": "<dict of 20>",
  "model": "authored-fake-model",
  "provenance": "authored by scripts/smoke.py --author from the fake model; not a model recording. Replace with `make record`."
}
```

## Try it yourself

Run these from the repository folder (after `make up`).

```bash
python3 -m json.tool .omc/state/sessions/6f28b667-1b81-4d8d-a94e-9da4a754b10a/pre-tool-advisory-throttle.json | head -20
```

Pretty-prints the file (and proves it is valid JSON; invalid JSON gives an error with a line and column).

```bash
python3 -c "import json; d=json.load(open('.omc/state/sessions/6f28b667-1b81-4d8d-a94e-9da4a754b10a/pre-tool-advisory-throttle.json')); print(type(d).__name__, len(d))"
```

Prints the top-level type (`dict` or `list`) and its size.

## Mistakes people make

- Trailing commas or single quotes, which are not valid JSON.
- Putting comments in the file. If a note is needed, use a field like `"note"`, as `config/prices.json` does where it exists.
- Using floats for exact amounts.
- Assuming key order carries meaning; objects are unordered, so the code sorts keys when it needs stable output.
- Reading untrusted JSON and assuming its shape. The code validates the fields it needs.

## Check yourself

1. What are the two container types in JSON?
   *Answer:* Objects (key-value maps) and arrays (ordered lists).
2. Can JSON have comments?
   *Answer:* No.
3. What does `json.loads` return for `{"a": 1}`?
   *Answer:* A Python dict `{'a': 1}`.
4. Why sort keys when writing JSON for files kept in Git?
   *Answer:* So the output is the same every time and diffs show only real changes.
5. Why not store money as a JSON number?
   *Answer:* Floating-point numbers cannot represent most decimal amounts exactly.

## Further reading

- [Introducing JSON](https://www.json.org/json-en.html)
- [RFC 8259, the JSON standard](https://www.rfc-editor.org/rfc/rfc8259)
- [Python json module](https://docs.python.org/3.12/library/json.html)
