# ADR 002: Google Drive + Local Folder Connector Scope

**Status:** Accepted

## Context
Company knowledge is scattered across Google Drive, Notion, and local files.
Building shallow support across multiple tools simultaneously risks an incomplete
or insecure permission model.

## Decision
Build primary production connectors fully correct (Google Drive: ingestion, permissions,
incremental sync) plus local folder ingestion (no permission model needed).
Design future enterprise connectors against the same unified `Connector` interface (see `connectors/notion.py`).

## Consequences
- The system reliably covers core distributed company knowledge.
- The connector interface (`connectors/base.py`) is proven out by real
  implementations, reducing the risk of designing an abstraction that doesn't fit new sources.
- Additional sources can be plugged in without changing the core ingestion or retrieval engine.
