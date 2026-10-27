# Changelog

All notable changes to this project are recorded here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-10-27

### Added

- A signed webhook (HMAC over timestamp and body, five-minute age limit, constant-time compare, size limit) that enqueues and answers 202, with the model nowhere on its path.
- A PostgreSQL queue read with row locks and leases, a processed-events table, tickets, an outbox, a fake mail sender that records each send, and dead letters with a reason, attempt count, last error and payload hash.
- A worker with a bounded thread pool, classified errors, jittered exponential backoff, per-event deadlines, a redrive command, graceful shutdown and tolerance of a database restart.
- A generator for 1,000 events (2% delivered twice, 1% poison), a burst measurement at two concurrency settings, a crash test that kills a real child process after the model call and after the commit, and a fake model with delay, error rate and a rate limit.
- A recorded adapter with an authored smoke cassette, a Claude adapter and an opt-in live test, and a versioned prompt file.
- Layered package with the dependency rule enforced by import-linter, unit, integration and end-to-end tests, ruff, mypy, hash-pinned lock files, a Dockerfile and a CI workflow.
