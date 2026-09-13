# ADR 003: Near-Real-Time Sync, Not True Real-Time

**Status:** Accepted

## Context
"Real time" could mean sub-second reflection of edits (via webhooks/push
notifications) or periodic incremental sync (polling a changes API on an
interval). True push-based real-time isn't uniformly available across all
target sources (e.g., Notion's webhook support varies by plan).

## Decision
v1 uses incremental sync on a fixed interval (e.g., every 10-15 minutes) via
each source's changes/delta API (Google Drive's Changes API for the Drive
connector). Each citation displays a "last synced" timestamp so users can
judge freshness themselves rather than assuming instant accuracy.

## Consequences
- Freshness SLA is explicit (~15 min) rather than an implied "always
  current," which is more honest and avoids user trust issues from stale
  answers appearing fully current.
- Keeps sync infrastructure simple (schedule + changes API) rather than
  requiring webhook receivers and infrastructure for push notifications.
- If a source lacks a changes API entirely, this approach falls back to
  polling `list_documents()` and diffing by `last_modified`, at higher cost.
