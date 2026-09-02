"""
NeuraSearch v2.0 — Personal Research Memory Service
Stores inspectable, editable, and deletable research preferences and project context.
Enforces that user memory is strictly isolated and NEVER used as global model training data.
"""

import logging
import uuid
from typing import List, Dict, Any, Optional
from database import db

logger = logging.getLogger("neurasearch.memory.personal")


class PersonalMemoryService:
    """Manages Layer-A Personal Research Memory for users."""

    @staticmethod
    def get_user_memories(user_id: str = "admin") -> List[Dict[str, Any]]:
        """Retrieve all active memory items for the user."""
        return db.get_private_memory_v2(user_id=user_id, active_only=True)

    @staticmethod
    def save_preference(
        category: str,
        key: str,
        value: str,
        user_id: str = "admin",
        confidence: float = 1.0,
        source: str = "user_explicit"
    ) -> Dict[str, Any]:
        """Save or update a personal research preference."""
        memory_id = f"mem_{uuid.uuid4().hex[:12]}"
        db.save_private_memory_v2(
            memory_id=memory_id,
            user_id=user_id,
            category=category,
            key=key,
            value=value,
            confidence=confidence,
            source=source
        )
        logger.info("Saved personal memory [%s]: %s = %s", category, key, value)
        return {
            "id": memory_id,
            "category": category,
            "key": key,
            "value": value,
            "user_id": user_id
        }

    @staticmethod
    def delete_memory(memory_id: str, user_id: str = "admin") -> bool:
        """Delete a single memory item."""
        return db.delete_private_memory_v2(memory_id=memory_id, user_id=user_id)

    @staticmethod
    def purge_all_memories(user_id: str = "admin") -> int:
        """Permanently delete all research memories for a user."""
        count = db.purge_all_memory_v2(user_id=user_id)
        logger.info("Purged all %d memories for user %s", count, user_id)
        return count

    @staticmethod
    def format_memory_for_prompt(user_id: str = "admin") -> str:
        """Format active memory preferences into a prompt injection block."""
        memories = PersonalMemoryService.get_user_memories(user_id)
        if not memories:
            return ""

        lines = ["\n[USER RESEARCH PREFERENCES & PROJECT CONTEXT]:"]
        for m in memories:
            lines.append(f"- {m['category'].upper()}: {m['key']} -> {m['value']}")
        return "\n".join(lines)
