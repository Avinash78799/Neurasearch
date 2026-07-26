import unittest
import os
import shutil
import json
from pathlib import Path

from database import db
from workspace_service import WorkspaceContext, WorkspaceService
from backup_utility import BackupUtility
from workspace_transfer_service import WorkspaceTransferService
from highlight_service import HighlightService

class TestProductionHardening(unittest.TestCase):
    def setUp(self):
        self.ws_src = "ws_harden_src"
        self.ws_dst = "ws_harden_dst"
        self.ctx_src = WorkspaceContext(self.ws_src)
        self.ctx_dst = WorkspaceContext(self.ws_dst)

        db.init_db()

        # Seed source workspace
        try:
            WorkspaceService.create_workspace(self.ws_src, "Source Workspace")
        except Exception:
            pass

        # Cleanup records
        with db.get_connection() as conn:
            conn.execute("DELETE FROM reading_sessions")
            conn.execute("DELETE FROM document_highlights")
            conn.execute("DELETE FROM knowledge_items")
            conn.commit()

        # Seed data in Source Workspace
        HighlightService.create_highlight(self.ws_src, "production_doc.pdf", page_number=3, highlight_text="Hardened code highlight")
        HighlightService.save_as_note(self.ws_src, "Grounded knowledge note content", "production_doc.pdf", title="Grounded Note")

    def tearDown(self):
        # Cleanup
        with db.get_connection() as conn:
            conn.execute("DELETE FROM reading_sessions")
            conn.execute("DELETE FROM document_highlights")
            conn.execute("DELETE FROM knowledge_items")
            conn.commit()

        # Clean local temporary file folders
        if os.path.exists("backups"):
            shutil.rmtree("backups")
        if os.path.exists("test_transfer.json"):
            os.remove("test_transfer.json")

    def test_backup_and_restore_utility(self):
        """Verifies database snapshots backup and restore functionality."""
        db_path = db.db_path
        chroma_path = "test_chroma_backup" # Use temporary non-locked directory path
        
        # Ensure test_chroma_backup folder exists
        Path(chroma_path).mkdir(exist_ok=True)

        # Create backup archive
        archive_path = BackupUtility.create_backup(db_path, chroma_path, output_dir="backups")
        self.assertTrue(os.path.exists(archive_path))
        self.assertTrue(archive_path.endswith(".tar.gz"))

        # Restore from backup archive
        BackupUtility.restore_backup(archive_path, db_path, chroma_path, extract_dir="backups/temp_restore")
        self.assertTrue(os.path.exists(db_path))

        # Cleanup
        if os.path.exists(chroma_path):
            shutil.rmtree(chroma_path)

    def test_workspace_import_export_transfer(self):
        """Verifies workspace export archive generation and restoration inside separate workspace."""
        export_file = "test_transfer.json"

        # 1. Export source workspace
        WorkspaceTransferService.export_workspace(self.ws_src, export_file)
        self.assertTrue(os.path.exists(export_file))

        with open(export_file, "r", encoding="utf-8") as f:
            exported_data = json.load(f)
            
        self.assertEqual(exported_data["workspace_id"], self.ws_src)
        self.assertEqual(len(exported_data["highlights"]), 1)
        self.assertEqual(len(exported_data["notes"]), 1)

        # 2. Import into destination workspace (restoring isolated attributes)
        WorkspaceTransferService.import_workspace(self.ws_dst, export_file)

        # 3. Verify destination workspace contents
        hl_list = HighlightService.list_highlights(self.ws_dst, "production_doc.pdf")
        self.assertEqual(len(hl_list), 1)
        self.assertEqual(hl_list[0]["highlight_text"], "Hardened code highlight")
