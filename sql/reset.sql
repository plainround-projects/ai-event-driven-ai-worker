-- Empty every table and restart the id counters. Run by `make reset` and by the tests.
TRUNCATE sent_mail, outbox, tickets, processed_events, dead_letters, deliveries RESTART IDENTITY;
