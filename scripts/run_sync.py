"""
Usage: python scripts/run_sync.py --local-folder ./sample_docs
"""

import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

load_dotenv()

from connectors.local_folder import LocalFolderConnector
from ingestion.sync import sync_connector
from retrieval.vector_store import VectorStore
from storage.db import init_db


def main():
    parser = argparse.ArgumentParser(description="Sync documents into the vector store.")
    parser.add_argument("--local-folder", help="Path to local folder to index")
    parser.add_argument(
        "--drive",
        action="store_true",
        help="Sync from Google Drive (requires credentials.json in project root)",
    )
    parser.add_argument(
        "--drive-folder-id",
        type=str,
        default=None,
        help="Optional Google Drive folder ID to restrict sync to a single folder",
    )
    args = parser.parse_args()

    init_db()
    store = VectorStore()

    if args.drive:
        from connectors.google_drive import GoogleDriveConnector

        connector = GoogleDriveConnector(folder_id=args.drive_folder_id)
        count = sync_connector(connector, "google_drive", store)
        folder_msg = f" (folder: {args.drive_folder_id})" if args.drive_folder_id else ""
        print(f"Indexed {count} documents from Google Drive{folder_msg}")
    elif args.local_folder:
        connector = LocalFolderConnector(args.local_folder)
        count = sync_connector(connector, "local_folder", store)
        print(f"Indexed {count} documents from {args.local_folder}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

