-- The queries the lesson's steps run. Each statement is preceded by a one-line comment.
-- Queue depth by status
SELECT status, COUNT(*) AS deliveries FROM deliveries GROUP BY status ORDER BY status;
-- Events whose effects were applied, and the tickets and acknowledgments they produced (all three must be equal)
SELECT (SELECT COUNT(*) FROM processed_events) AS processed, (SELECT COUNT(*) FROM tickets) AS tickets, (SELECT COUNT(*) FROM outbox) AS outbox_rows, (SELECT COUNT(*) FROM sent_mail) AS mails_sent;
-- Events with more than one ticket (must be empty)
SELECT event_id, COUNT(*) AS tickets FROM tickets GROUP BY event_id HAVING COUNT(*) > 1;
-- Event ids that were delivered but have no ticket and are not dead-lettered (lost events; must be empty at the end of a run)
SELECT DISTINCT d.event_id FROM deliveries d WHERE NOT EXISTS (SELECT 1 FROM tickets t WHERE t.event_id = d.event_id) AND NOT EXISTS (SELECT 1 FROM dead_letters x WHERE x.event_id = d.event_id) ORDER BY d.event_id;
-- How many events arrived once, twice or more (after the replay every event has at least two deliveries)
SELECT deliveries, COUNT(*) AS events FROM (SELECT event_id, COUNT(*) AS deliveries FROM deliveries GROUP BY event_id) per_event GROUP BY deliveries ORDER BY deliveries;
-- Dead letters by reason
SELECT reason, COUNT(*) AS events, MAX(attempts) AS most_attempts FROM dead_letters GROUP BY reason ORDER BY reason;
-- Event to ticket time: median and 95th percentile in seconds
SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM t.created_at - d.received_at)) AS p50_seconds, percentile_cont(0.95) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM t.created_at - d.received_at)) AS p95_seconds FROM tickets t JOIN LATERAL (SELECT MIN(received_at) AS received_at FROM deliveries WHERE event_id = t.event_id) d ON true;
