"""
Query-time permission enforcement. This runs BEFORE any retrieved text
reaches the LLM -- see docs/decisions/001-permission-aware-retrieval.md for
why this is a hard requirement rather than a prompt instruction.
"""


def filter_by_permission(candidates: list, user_email: str) -> list:
    """
    A chunk is visible to `user_email` if:
      - its source doc has an empty ACL (public within its connector, e.g.
        local files), OR
      - `user_email` is explicitly listed in the doc's ACL.
    """
    allowed = []
    for c in candidates:
        acl = c.get("acl", [])
        if not acl or user_email in acl:
            allowed.append(c)
    return allowed
