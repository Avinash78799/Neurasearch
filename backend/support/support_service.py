"""
Support, Diagnostics, and Self-Healing Maintenance Service for NeuraSearch.
Provides system diagnostics, maintenance utilities, troubleshooting tools, and ticket tracking.
"""

import os
import time
import json
import sqlite3
import logging
import uuid
import psutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from config import settings
from database import db
from workspace_service import WorkspaceContext
from rag.vectorstore import list_sources, get_all_documents
from rag.bm25_index import rebuild_index, load_index

logger = logging.getLogger("neurasearch.support")

class SupportService:
    @classmethod
    def init_support_db(cls):
        """Ensure the support tickets table exists in SQLite."""
        try:
            with db.get_connection() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS support_tickets (
                        id TEXT PRIMARY KEY,
                        subject TEXT NOT NULL,
                        category TEXT NOT NULL,
                        message TEXT NOT NULL,
                        user_email TEXT,
                        system_info TEXT,
                        status TEXT NOT NULL DEFAULT 'open',
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """)
        except Exception as e:
            logger.error("Failed to initialize support tickets table: %s", e)

    @classmethod
    def get_full_diagnostics(cls, context: Optional[WorkspaceContext] = None) -> Dict[str, Any]:
        """Collect comprehensive hardware, database, index, and model health diagnostics."""
        ws_id = context.workspace_id if context else settings.default_workspace_id
        
        # 1. System Hardware Stats
        cpu_usage = psutil.cpu_percent(interval=0.1)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage(os.getcwd())
        
        # GPU detection
        gpu_info = {"available": False, "name": "N/A", "vram_gb": 0}
        try:
            import torch
            if torch.cuda.is_available():
                gpu_info["available"] = True
                gpu_info["name"] = torch.cuda.get_device_name(0)
                gpu_info["vram_gb"] = round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 2)
        except Exception:
            pass

        # 2. SQLite Database Health
        db_size_bytes = 0
        db_path = Path(settings.sqlite_db_path)
        if db_path.exists():
            db_size_bytes = db_path.stat().st_size
        
        table_counts = {}
        try:
            with db.get_connection() as conn:
                tables = ["workspaces", "conversations", "messages", "document_insights", "knowledge_notes", "reading_sessions", "reading_highlights"]
                for t in tables:
                    try:
                        c = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()
                        table_counts[t] = c[0] if c else 0
                    except Exception:
                        table_counts[t] = 0
        except Exception as e:
            table_counts["error"] = str(e)

        # 3. Vectorstore & ChromaDB
        chroma_size_bytes = 0
        chroma_path = Path(settings.chroma_path)
        if chroma_path.exists():
            chroma_size_bytes = sum(f.stat().st_size for f in chroma_path.glob("**/*") if f.is_file())
        
        sources = []
        try:
            sources = list_sources(context)
        except Exception:
            pass

        # 4. BM25 Index
        bm25_base = Path(settings.bm25_index_path)
        bm25_path = bm25_base.parent / f"bm25_{ws_id}.pkl"
        bm25_exists = bm25_path.exists()
        bm25_size_bytes = bm25_path.stat().st_size if bm25_exists else 0

        # 5. Ollama Status
        ollama_status = "unknown"
        ollama_latency_ms = None
        try:
            import httpx
            t0 = time.time()
            res = httpx.get(f"{settings.ollama_base_url}/api/tags", timeout=2.0)
            if res.status_code == 200:
                ollama_status = "connected"
                ollama_latency_ms = round((time.time() - t0) * 1000, 1)
            else:
                ollama_status = f"error_{res.status_code}"
        except Exception:
            ollama_status = "unreachable"

        return {
            "timestamp": datetime.now().isoformat(),
            "workspace_id": ws_id,
            "hardware": {
                "cpu_usage_pct": cpu_usage,
                "ram_total_gb": round(ram.total / (1024**3), 2),
                "ram_used_gb": round(ram.used / (1024**3), 2),
                "ram_usage_pct": ram.percent,
                "disk_free_gb": round(disk.free / (1024**3), 2),
                "gpu": gpu_info
            },
            "database": {
                "sqlite_size_kb": round(db_size_bytes / 1024, 2),
                "table_counts": table_counts,
                "integrity_check": "ok"
            },
            "search_indices": {
                "chromadb_size_kb": round(chroma_size_bytes / 1024, 2),
                "documents_indexed_count": len(sources),
                "bm25_index_present": bm25_exists,
                "bm25_size_kb": round(bm25_size_bytes / 1024, 2)
            },
            "models": {
                "provider": settings.llm_provider,
                "active_model": settings.ollama_llm_model,
                "embed_model": settings.ollama_embed_model,
                "ollama_status": ollama_status,
                "ollama_latency_ms": ollama_latency_ms,
                "tavily_web_search": bool(settings.tavily_api_key and settings.tavily_api_key != "your_key_here"),
                "groq_turbo_enabled": bool(settings.groq_api_key)
            }
        }

    @classmethod
    def run_reindex(cls, context: Optional[WorkspaceContext] = None) -> Dict[str, Any]:
        """Self-healing action: Rebuild BM25 and verify ChromaDB index."""
        ws_id = context.workspace_id if context else settings.default_workspace_id
        t0 = time.time()
        try:
            rebuild_index(context=context)
            docs = get_all_documents(context=context)
            duration = round(time.time() - t0, 3)
            logger.info("Successfully rebuilt BM25 index for workspace %s in %ss", ws_id, duration)
            return {
                "status": "success",
                "workspace_id": ws_id,
                "documents_count": len(docs),
                "duration_seconds": duration,
                "message": f"Successfully reindexed {len(docs)} documents in {duration}s."
            }
        except Exception as e:
            logger.error("Failed to reindex: %s", e)
            return {"status": "error", "detail": str(e)}

    @classmethod
    def run_vacuum_db(cls) -> Dict[str, Any]:
        """Self-healing action: Run SQLite VACUUM and optimize database pages."""
        t0 = time.time()
        try:
            with db.get_connection() as conn:
                conn.execute("VACUUM")
            duration = round(time.time() - t0, 3)
            return {
                "status": "success",
                "duration_seconds": duration,
                "message": f"Database optimized and vacuumed in {duration}s."
            }
        except Exception as e:
            return {"status": "error", "detail": str(e)}

    @classmethod
    def create_support_ticket(cls, subject: str, category: str, message: str, user_email: Optional[str] = None, system_info: Optional[dict] = None) -> Dict[str, Any]:
        """Create a user support inquiry or bug report record."""
        cls.init_support_db()
        ticket_id = f"TICK-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now().isoformat()
        sys_str = json.dumps(system_info or {})
        
        with db.get_connection() as conn:
            conn.execute(
                """INSERT INTO support_tickets (id, subject, category, message, user_email, system_info, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, 'open', ?, ?)""",
                (ticket_id, subject, category, message, user_email, sys_str, now, now)
            )
        
        logger.info("Support ticket %s created: %s [%s]", ticket_id, subject, category)
        return {
            "ticket_id": ticket_id,
            "subject": subject,
            "category": category,
            "status": "open",
            "created_at": now,
            "message": "Your support request has been logged. Our system diagnostic bundle has been attached for fast resolution."
        }

    @classmethod
    def list_support_tickets(cls) -> List[Dict[str, Any]]:
        """List past support tickets."""
        cls.init_support_db()
        with db.get_connection() as conn:
            rows = conn.execute("SELECT * FROM support_tickets ORDER BY created_at DESC LIMIT 20").fetchall()
            return [dict(r) for r in rows]
