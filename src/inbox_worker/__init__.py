"""A worker for the support inbox: a signed webhook, a Postgres queue, one model step per event, effects applied once, backoff, dead letters, crash recovery and a burst measurement."""
