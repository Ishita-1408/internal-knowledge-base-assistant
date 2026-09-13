# ADR 001: Permission-Aware Retrieval (Query-Time Filtering)

**Status:** Accepted

## Context
The assistant indexes documents from sources with their own access controls
(e.g., Google Drive). A user must never see an answer or citation drawn from
a document they aren't authorized to view in the source system.

## Options Considered
1. **Prompt-based restriction** — tell the LLM in the system prompt to "only
   use documents the user has access to."
2. **Permission-aware retrieval** — attach each chunk's ACL as metadata at
   index time, and filter retrieved candidates against the querying user's
   identity *before* any chunk reaches the LLM.

## Decision
Option 2. Filtering happens in `retrieval/permission_filter.py`, between
vector search and prompt construction.

## Consequences
- Requires storing and periodically refreshing ACL metadata per document,
  adding sync complexity.
- Requires over-fetching candidates (top_k=20) so enough remain after
  filtering to generate a good answer.
- In exchange, access control is enforced structurally rather than relying
  on model behavior — an LLM instruction is not a security boundary, since
  it can be bypassed by prompt injection or model error. This is a hard
  requirement, not a nice-to-have.
