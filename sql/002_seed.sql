-- DML: nothing to seed. The inbox starts empty; `inbox-worker generate-events` writes the 1,000 sample events and
-- `inbox-worker enqueue` loads them. This file exists so `make db` has the two numbered scripts every repository has.
SELECT 1;
