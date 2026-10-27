# 3. A fake model with a real rate-limit shape, and an authored smoke cassette

Status: accepted, 2026-10-27

## Context

No model key was available when this was built, and the load tests would be expensive and noisy against a real model anyway. The lesson also asks for a "real-model smoke run on 20 events".

## Decision

`FakeModel` takes a delay, an error rate and a maximum request rate. The rate is a token bucket: a call over the limit raises the same retryable error a provider's 429 would, and is counted. Throughput and rate-limit errors therefore depend on concurrency the way they would against a real limit, rather than being a fixed percentage. For the smoke run, `scripts/smoke.py` has three modes: replay `tests/fixtures/cassettes/smoke-v1.json` (default), author that file from the fake model, and record from the real model into `live-v1.json` (`make record`, needs a key). The committed cassette says in its `provenance` field that it is authored and not a model recording, and its requests are keyed by the prompt version, model name, system text and email so a changed prompt cannot silently replay.

## Alternatives considered

- **A fixed rate-limit percentage:** simple, and exactly what hides the relation between concurrency and limits.
- **Calling a real model in CI:** needs a secret and costs money on every run.

## Consequences

- The offline results show the worker's behavior (retries, parking, draining), not a model's.
- The real adapter is exercised only by `make test-live` and `make record`, neither run here.
