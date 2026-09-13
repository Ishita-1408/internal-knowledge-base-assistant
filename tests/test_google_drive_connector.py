"""
Unit tests for GoogleDriveConnector using mocks.
Tests OAuth initialization, Docs/Sheets/Slides export, binary doc extraction,
metadata capture, ACL retrieval, incremental sync, and deletion detection.
"""

import io
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from connectors.base import DocMeta
from connectors.google_drive import GoogleDriveConnector


@pytest.fixture
def mock_drive_connector():
    with patch("connectors.google_drive.Credentials") as mock_creds_cls, \
         patch("connectors.google_drive.build") as mock_build:
        mock_creds = MagicMock()
        mock_creds.valid = True
        mock_creds_cls.from_authorized_user_file.return_value = mock_creds

        mock_service = MagicMock()
        mock_build.return_value = mock_service

        connector = GoogleDriveConnector(credentials_path="mock_creds.json", token_path="mock_token.json")
        connector.service = mock_service
        return connector


def test_drive_auth_with_valid_token(mock_drive_connector):
    assert mock_drive_connector.creds.valid is True
    assert mock_drive_connector.service is not None


def test_drive_to_docmeta(mock_drive_connector):
    mock_drive_connector.get_permissions = MagicMock(return_value=["alice@example.com", "bob@example.com"])

    item = {
        "id": "file_123",
        "name": "Remote Work Policy",
        "webViewLink": "https://drive.google.com/file/d/file_123/view",
        "modifiedTime": "2026-09-13T10:00:00Z",
        "mimeType": "application/vnd.google-apps.document",
    }

    doc = mock_drive_connector._to_docmeta(item)
    assert isinstance(doc, DocMeta)
    assert doc.doc_id == "file_123"
    assert doc.source == "google_drive"
    assert doc.title == "Remote Work Policy"
    assert doc.url == "https://drive.google.com/file/d/file_123/view"
    assert doc.acl == ["alice@example.com", "bob@example.com"]
    assert doc.is_deleted is False


def test_drive_list_documents(mock_drive_connector):
    mock_files_resource = MagicMock()
    mock_drive_connector.service.files.return_value = mock_files_resource
    mock_drive_connector.get_permissions = MagicMock(return_value=["user@example.com"])

    mock_files_resource.list.return_value.execute.return_value = {
        "files": [
            {
                "id": "doc1",
                "name": "Doc One",
                "webViewLink": "https://example.com/doc1",
                "modifiedTime": "2026-09-13T10:00:00Z",
            }
        ],
        "nextPageToken": None,
    }

    docs = mock_drive_connector.list_documents()
    assert len(docs) == 1
    assert docs[0].doc_id == "doc1"
    assert docs[0].title == "Doc One"


def test_drive_get_content_google_doc(mock_drive_connector):
    mock_files = MagicMock()
    mock_drive_connector.service.files.return_value = mock_files

    # 1. Get mimeType
    mock_files.get.return_value.execute.return_value = {
        "mimeType": "application/vnd.google-apps.document"
    }

    # 2. Mock MediaIoBaseDownload for export
    doc_text_bytes = b"This is the exported Google Doc plain text."

    def fake_download(buf, request):
        buf.write(doc_text_bytes)
        mock_dl = MagicMock()
        mock_dl.next_chunk.return_value = (None, True)
        return mock_dl

    with patch("connectors.google_drive.MediaIoBaseDownload", side_effect=fake_download):
        content = mock_drive_connector.get_content("doc_id_1")
        assert content == "This is the exported Google Doc plain text."
        mock_files.export_media.assert_called_with(
            fileId="doc_id_1", mimeType="text/plain"
        )


def test_drive_get_content_google_sheet(mock_drive_connector):
    mock_files = MagicMock()
    mock_drive_connector.service.files.return_value = mock_files

    mock_files.get.return_value.execute.return_value = {
        "mimeType": "application/vnd.google-apps.spreadsheet"
    }

    sheet_csv_bytes = b"Employee,Department,Location\nAlice,Engineering,Remote\nBob,Design,Hybrid"

    def fake_download(buf, request):
        buf.write(sheet_csv_bytes)
        mock_dl = MagicMock()
        mock_dl.next_chunk.return_value = (None, True)
        return mock_dl

    with patch("connectors.google_drive.MediaIoBaseDownload", side_effect=fake_download):
        content = mock_drive_connector.get_content("sheet_id_1")
        assert "Alice,Engineering,Remote" in content
        mock_files.export_media.assert_called_with(
            fileId="sheet_id_1", mimeType="text/csv"
        )


def test_drive_get_content_google_slides(mock_drive_connector):
    mock_files = MagicMock()
    mock_drive_connector.service.files.return_value = mock_files

    mock_files.get.return_value.execute.return_value = {
        "mimeType": "application/vnd.google-apps.presentation"
    }

    slides_text_bytes = b"Slide 1: Q1 Product Strategy\nSlide 2: Roadmap and Milestones"

    def fake_download(buf, request):
        buf.write(slides_text_bytes)
        mock_dl = MagicMock()
        mock_dl.next_chunk.return_value = (None, True)
        return mock_dl

    with patch("connectors.google_drive.MediaIoBaseDownload", side_effect=fake_download):
        content = mock_drive_connector.get_content("slides_id_1")
        assert "Slide 1: Q1 Product Strategy" in content
        mock_files.export_media.assert_called_with(
            fileId="slides_id_1", mimeType="text/plain"
        )


def test_drive_get_permissions(mock_drive_connector):
    mock_perms = MagicMock()
    mock_drive_connector.service.permissions.return_value = mock_perms

    mock_perms.list.return_value.execute.return_value = {
        "permissions": [
            {"type": "user", "emailAddress": "security@example.com", "role": "reader"},
            {"type": "user", "emailAddress": "admin@example.com", "role": "writer"},
            {"type": "domain", "role": "reader"},  # Should be filtered out
            {"type": "user", "role": "reader"},  # Missing email, filtered out
        ]
    }

    acl = mock_drive_connector.get_permissions("doc_123")
    assert acl == ["security@example.com", "admin@example.com"]


def test_drive_get_changes_since_incremental(mock_drive_connector):
    mock_changes = MagicMock()
    mock_drive_connector.service.changes.return_value = mock_changes
    mock_drive_connector.get_permissions = MagicMock(return_value=["emp@example.com"])

    # Simulate existing page token
    mock_drive_connector._page_token = "token_page_1"

    mock_changes.list.return_value.execute.return_value = {
        "changes": [
            {
                "fileId": "file_modified",
                "removed": False,
                "file": {
                    "id": "file_modified",
                    "name": "Updated Policy",
                    "modifiedTime": "2026-09-13T12:00:00Z",
                    "trashed": False,
                },
            },
            {
                "fileId": "file_deleted",
                "removed": True,
                "file": None,
            },
            {
                "fileId": "file_trashed",
                "removed": False,
                "file": {
                    "id": "file_trashed",
                    "name": "Old Policy",
                    "trashed": True,
                },
            },
        ],
        "nextPageToken": None,
        "newStartPageToken": "token_page_2",
    }

    changes = mock_drive_connector.get_changes_since(datetime.now(timezone.utc))
    assert len(changes) == 3

    # Modified doc
    assert changes[0].doc_id == "file_modified"
    assert changes[0].title == "Updated Policy"
    assert changes[0].is_deleted is False

    # Removed doc
    assert changes[1].doc_id == "file_deleted"
    assert changes[1].is_deleted is True

    # Trashed doc
    assert changes[2].doc_id == "file_trashed"
    assert changes[2].is_deleted is True

    # Check updated token
    assert mock_drive_connector._page_token == "token_page_2"


def test_drive_to_docmeta_can_share_false(mock_drive_connector):
    mock_drive_connector.get_permissions = MagicMock()
    item = {
        "id": "restricted_doc",
        "name": "Confidential Salary Grid",
        "webViewLink": "https://example.com/salary",
        "modifiedTime": "2026-09-13T10:00:00Z",
        "capabilities": {"canShare": False},
    }

    doc = mock_drive_connector._to_docmeta(item)
    assert doc is None
    # get_permissions should not even be invoked when canShare is False
    mock_drive_connector.get_permissions.assert_not_called()


def test_drive_get_permissions_403_insufficient_permissions(mock_drive_connector):
    from googleapiclient.errors import HttpError
    mock_perms = MagicMock()
    mock_drive_connector.service.permissions.return_value = mock_perms

    resp = MagicMock()
    resp.status = 403
    mock_perms.list.return_value.execute.side_effect = HttpError(resp, b'{"error": {"message": "insufficientFilePermissions"}}')

    acl = mock_drive_connector.get_permissions("doc_no_permission")
    assert acl is None


def test_drive_get_permissions_unexpected_error(mock_drive_connector):
    mock_perms = MagicMock()
    mock_drive_connector.service.permissions.return_value = mock_perms
    mock_perms.list.return_value.execute.side_effect = RuntimeError("Network breakdown")

    acl = mock_drive_connector.get_permissions("doc_error")
    assert acl is None


def test_drive_to_docmeta_unretrievable_acl_returns_none(mock_drive_connector):
    mock_drive_connector.get_permissions = MagicMock(return_value=None)
    item = {
        "id": "doc_unretrievable",
        "name": "Secret Roadmap",
        "webViewLink": "https://example.com/roadmap",
        "modifiedTime": "2026-09-13T10:00:00Z",
    }
    doc = mock_drive_connector._to_docmeta(item)
    assert doc is None


def test_drive_list_documents_skips_unretrievable_acl(mock_drive_connector):
    mock_files_resource = MagicMock()
    mock_drive_connector.service.files.return_value = mock_files_resource

    # First doc has valid ACL, second doc has None (e.g. 403)
    def fake_get_permissions(doc_id):
        if doc_id == "doc_valid":
            return ["user@example.com"]
        return None

    mock_drive_connector.get_permissions = MagicMock(side_effect=fake_get_permissions)

    mock_files_resource.list.return_value.execute.return_value = {
        "files": [
            {
                "id": "doc_valid",
                "name": "Public Handbook",
                "webViewLink": "https://example.com/handbook",
                "modifiedTime": "2026-09-13T10:00:00Z",
            },
            {
                "id": "doc_403",
                "name": "Secret M&A",
                "webViewLink": "https://example.com/ma",
                "modifiedTime": "2026-09-13T10:00:00Z",
            },
        ],
        "nextPageToken": None,
    }

    docs = mock_drive_connector.list_documents()
    assert len(docs) == 1
    assert docs[0].doc_id == "doc_valid"
    assert docs[0].title == "Public Handbook"


def test_drive_incremental_sync_skips_unretrievable_acl_and_keeps_deletions(mock_drive_connector):
    mock_changes = MagicMock()
    mock_drive_connector.service.changes.return_value = mock_changes

    def fake_get_permissions(doc_id):
        if doc_id == "file_valid":
            return ["alice@example.com"]
        return None

    mock_drive_connector.get_permissions = MagicMock(side_effect=fake_get_permissions)
    mock_drive_connector._page_token = "token_inc_1"

    mock_changes.list.return_value.execute.return_value = {
        "changes": [
            {
                "fileId": "file_valid",
                "removed": False,
                "file": {
                    "id": "file_valid",
                    "name": "Valid Doc",
                    "modifiedTime": "2026-09-13T12:00:00Z",
                    "trashed": False,
                },
            },
            {
                "fileId": "file_forbidden",
                "removed": False,
                "file": {
                    "id": "file_forbidden",
                    "name": "Forbidden Doc",
                    "modifiedTime": "2026-09-13T12:00:00Z",
                    "trashed": False,
                },
            },
            {
                "fileId": "file_deleted",
                "removed": True,
                "file": None,
            },
        ],
        "nextPageToken": None,
        "newStartPageToken": "token_inc_2",
    }

    changes = mock_drive_connector.get_changes_since(datetime.now(timezone.utc))
    assert len(changes) == 2
    # 1. Valid doc
    assert changes[0].doc_id == "file_valid"
    assert changes[0].is_deleted is False
    # 2. Deleted doc
    assert changes[1].doc_id == "file_deleted"
    assert changes[1].is_deleted is True


def test_drive_list_documents_no_folder_id_query(mock_drive_connector):
    mock_files = MagicMock()
    mock_drive_connector.service.files.return_value = mock_files
    mock_drive_connector.folder_id = None
    mock_files.list.return_value.execute.return_value = {"files": [], "nextPageToken": None}

    mock_drive_connector.list_documents()
    mock_files.list.assert_called_once()
    assert mock_files.list.call_args[1]["q"] == "trashed = false"


def test_drive_list_documents_with_folder_id_query(mock_drive_connector):
    mock_files = MagicMock()
    mock_drive_connector.service.files.return_value = mock_files
    mock_drive_connector.folder_id = "folder_abc_123"
    mock_files.list.return_value.execute.return_value = {"files": [], "nextPageToken": None}

    mock_drive_connector.list_documents()
    mock_files.list.assert_called_once()
    assert mock_files.list.call_args[1]["q"] == "'folder_abc_123' in parents and trashed = false"


def test_drive_list_documents_escapes_folder_id(mock_drive_connector):
    mock_files = MagicMock()
    mock_drive_connector.service.files.return_value = mock_files
    mock_drive_connector.folder_id = "folder'with'quotes"
    mock_files.list.return_value.execute.return_value = {"files": [], "nextPageToken": None}

    mock_drive_connector.list_documents()
    mock_files.list.assert_called_once()
    assert mock_files.list.call_args[1]["q"] == r"'folder\'with\'quotes' in parents and trashed = false"


def test_drive_incremental_sync_with_folder_filter(mock_drive_connector):
    mock_changes = MagicMock()
    mock_drive_connector.service.changes.return_value = mock_changes
    mock_drive_connector.get_permissions = MagicMock(return_value=["user@example.com"])
    mock_drive_connector._page_token = "token_folder_1"
    mock_drive_connector.folder_id = "target_folder_99"

    mock_changes.list.return_value.execute.return_value = {
        "changes": [
            {
                "fileId": "file_inside",
                "removed": False,
                "file": {
                    "id": "file_inside",
                    "name": "Inside Doc",
                    "modifiedTime": "2026-09-13T12:00:00Z",
                    "trashed": False,
                    "parents": ["target_folder_99"],
                },
            },
            {
                "fileId": "file_outside",
                "removed": False,
                "file": {
                    "id": "file_outside",
                    "name": "Outside Doc",
                    "modifiedTime": "2026-09-13T12:00:00Z",
                    "trashed": False,
                    "parents": ["different_folder_11"],
                },
            },
            {
                "fileId": "file_no_parent",
                "removed": False,
                "file": {
                    "id": "file_no_parent",
                    "name": "Root Doc",
                    "modifiedTime": "2026-09-13T12:00:00Z",
                    "trashed": False,
                },
            },
            {
                "fileId": "file_deleted",
                "removed": True,
                "file": None,
            },
        ],
        "nextPageToken": None,
        "newStartPageToken": "token_folder_2",
    }

    changes = mock_drive_connector.get_changes_since(datetime.now(timezone.utc))
    # Should only contain file_inside and file_deleted
    assert len(changes) == 2
    assert changes[0].doc_id == "file_inside"
    assert changes[0].is_deleted is False
    assert changes[1].doc_id == "file_deleted"
    assert changes[1].is_deleted is True


