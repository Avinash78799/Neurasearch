import os
import shutil
import sqlite3
import tarfile
import logging
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("neurasearch.backup")

class BackupUtility:
    @staticmethod
    def create_backup(db_path: str, chroma_path: str, output_dir: str = "backups") -> str:
        """Create a complete production backup of SQLite DB and ChromaDB folder."""
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}"
        temp_dir = Path(output_dir) / backup_name
        temp_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Starting backup: %s", backup_name)

        try:
            # 1. Backup SQLite using sqlite3 online backup API
            if os.path.exists(db_path):
                dest_db = temp_dir / os.path.basename(db_path)
                logger.info("Backing up SQLite DB to %s", dest_db)
                src_conn = sqlite3.connect(db_path)
                dst_conn = sqlite3.connect(str(dest_db))
                with dst_conn:
                    src_conn.backup(dst_conn)
                src_conn.close()
                dst_conn.close()
            else:
                logger.warning("SQLite DB path does not exist: %s", db_path)

            # 2. Backup ChromaDB directory
            if os.path.exists(chroma_path):
                dest_chroma = temp_dir / os.path.basename(chroma_path)
                logger.info("Copying ChromaDB directory from %s to %s", chroma_path, dest_chroma)
                shutil.copytree(chroma_path, dest_chroma)
            else:
                logger.warning("ChromaDB path does not exist: %s", chroma_path)

            # 3. Archive the temporary folder
            archive_path = Path(output_dir) / f"{backup_name}.tar.gz"
            logger.info("Compressing backup archive to %s", archive_path)
            with tarfile.open(archive_path, "w:gz") as tar:
                tar.add(temp_dir, arcname=backup_name)

            # Clean up temp folder
            shutil.rmtree(temp_dir)
            logger.info("Backup completed successfully: %s", archive_path)
            return str(archive_path)

        except Exception as e:
            logger.error("Backup failed: %s", e, exc_info=True)
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            raise

    @staticmethod
    def restore_backup(archive_path: str, dest_db_path: str, dest_chroma_path: str, extract_dir: str = "backups/temp_restore") -> None:
        """Restore SQLite and ChromaDB from a backup tar.gz archive."""
        logger.info("Starting restore from archive: %s", archive_path)

        if not os.path.exists(archive_path):
            raise FileNotFoundError(f"Backup archive not found: {archive_path}")

        temp_dir = Path(extract_dir)
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        temp_dir.mkdir(parents=True, exist_ok=True)

        try:
            # 1. Extract tar.gz archive
            with tarfile.open(archive_path, "r:gz") as tar:
                tar.extractall(path=temp_dir)

            # Locate extracted subfolder
            extracted_subfolders = [f for f in temp_dir.iterdir() if f.is_dir()]
            if not extracted_subfolders:
                raise ValueError("Corrupted backup: no data folder found in archive.")
            data_dir = extracted_subfolders[0]

            # 2. Restore SQLite DB
            src_db = data_dir / os.path.basename(dest_db_path)
            if src_db.exists():
                logger.info("Restoring SQLite DB to %s via online backup copy", dest_db_path)
                src_conn = sqlite3.connect(str(src_db))
                dst_conn = sqlite3.connect(dest_db_path)
                with dst_conn:
                    src_conn.backup(dst_conn)
                src_conn.close()
                dst_conn.close()
            else:
                logger.warning("No SQLite DB file found in backup.")

            # 3. Restore ChromaDB folder
            src_chroma = data_dir / os.path.basename(dest_chroma_path)
            if src_chroma.exists():
                logger.info("Restoring ChromaDB to %s", dest_chroma_path)
                # Safely remove existing ChromaDB dir
                if os.path.exists(dest_chroma_path):
                    shutil.rmtree(dest_chroma_path)
                shutil.copytree(src_chroma, dest_chroma_path)
            else:
                logger.warning("No ChromaDB folder found in backup.")

            # Clean up temp folder
            shutil.rmtree(temp_dir)
            logger.info("Restore completed successfully.")

        except Exception as e:
            logger.error("Restore failed: %s", e, exc_info=True)
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            raise

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python backup_utility.py [backup|restore] [db_path] [chroma_path]")
        sys.exit(1)

    action = sys.argv[1]
    db_p = sys.argv[2] if len(sys.argv) > 2 else "neurasearch.db"
    chroma_p = sys.argv[3] if len(sys.argv) > 3 else "chroma_db"

    if action == "backup":
        BackupUtility.create_backup(db_p, chroma_p)
    elif action == "restore":
        if len(sys.argv) < 5:
            print("Usage for restore: python backup_utility.py restore [db_path] [chroma_path] [archive_path]")
            sys.exit(1)
        archive_p = sys.argv[4]
        BackupUtility.restore_backup(archive_p, db_p, chroma_p)
    else:
        print(f"Unknown action: {action}")
        sys.exit(1)
