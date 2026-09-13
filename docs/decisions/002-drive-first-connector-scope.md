# ADR 002: Google Drive + Local Folder Only for v1

**Status:** Accepted

## Context
Company knowledge is scattered across Google Drive, Notion, and local files.
Building shallow support for all three in v1 risks a permission model that
is correct nowhere.

## Decision
Build one connector fully correct (Google Drive: ingestion, permissions,
incremental sync) plus local folder ingestion (no permission model needed).
Design — but do not build — the Notion connector, against the same
`Connector` interface (see `connectors/notion.py`).

## Consequences
- v1 covers a real but partial slice of scattered company knowledge.
- The connector interface (`connectors/base.py`) is proven out by two real
  implementations before a third is attempted, reducing the risk of
  designing an abstraction that doesn't actually fit new sources.
- Notion support is deferred to Phase 2, prioritized in the RICE table in
  the PRD.
