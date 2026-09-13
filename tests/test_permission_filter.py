"""
The most important test in this repo: proves the permission filter never
leaks a chunk to a user who isn't in its ACL.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from retrieval.permission_filter import filter_by_permission


def _candidate(acl):
    return {
        "text": "sensitive text",
        "doc_id": "doc1",
        "title": "t",
        "url": "",
        "acl": acl,
        "distance": 0.1,
        "last_modified": "",
    }


def test_public_doc_visible_to_everyone():
    candidates = [_candidate(acl=[])]
    result = filter_by_permission(candidates, "anyone@example.com")
    assert len(result) == 1


def test_restricted_doc_visible_only_to_listed_user():
    candidates = [_candidate(acl=["alice@example.com"])]

    assert len(filter_by_permission(candidates, "alice@example.com")) == 1
    assert len(filter_by_permission(candidates, "bob@example.com")) == 0


def test_mixed_candidates_filtered_independently():
    candidates = [
        _candidate(acl=["alice@example.com"]),
        _candidate(acl=[]),
        _candidate(acl=["carol@example.com"]),
    ]
    result = filter_by_permission(candidates, "alice@example.com")
    assert len(result) == 2  # alice's doc + the public doc, not carol's
