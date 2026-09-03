# Operations Manual

This guide describes how to run operational maintenance, backups, and restores for NeuraSearch.

---

## 1. Database Backups

System backups are run using `backup_utility.py`:

- **Backup database**:
  ```bash
  python backend/backup_utility.py backup ./neurasearch.db ./chroma_db
  ```
  Saves a tarball named `backup_YYYYMMDD_HHMMSS.tar.gz` in `backups/`.

- **Restore database**:
  ```bash
  python backend/backup_utility.py restore ./neurasearch.db ./chroma_db backups/backup_NAME.tar.gz
  ```

---

## 2. Workspace JSON Transfers

If you want to migrate files and notes from one workspace context to another, use the JSON API routes:
- **Export workspace**:
  `POST /api/v1/workspaces/export/{workspace_id}`
- **Import workspace**:
  `POST /api/v1/workspaces/import/{workspace_id}` (multipart file upload of exported JSON)
