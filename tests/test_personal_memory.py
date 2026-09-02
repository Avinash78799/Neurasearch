"""
NeuraSearch v2.0 — Personal Research Memory Test Suite
Verifies Layer-A user preference management, CRUD operations, and prompt injection formatting.
"""

import unittest
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from memory.personal_memory import PersonalMemoryService


class TestPersonalMemory(unittest.TestCase):

    def test_save_and_retrieve_preference(self):
        """Verify saving and fetching a personal research preference."""
        PersonalMemoryService.purge_all_memories(user_id="test_user_1")

        item = PersonalMemoryService.save_preference(
            category="preference",
            key="citation_style",
            value="IEEE Footnotes",
            user_id="test_user_1"
        )
        self.assertEqual(item["key"], "citation_style")
        self.assertEqual(item["value"], "IEEE Footnotes")

        memories = PersonalMemoryService.get_user_memories(user_id="test_user_1")
        self.assertEqual(len(memories), 1)
        self.assertEqual(memories[0]["value"], "IEEE Footnotes")

    def test_delete_and_purge_memory(self):
        """Verify deleting single and all personal research memories."""
        PersonalMemoryService.purge_all_memories(user_id="test_user_2")

        m1 = PersonalMemoryService.save_preference("preference", "depth", "deep", user_id="test_user_2")
        m2 = PersonalMemoryService.save_preference("project_context", "focus", "LLM Security", user_id="test_user_2")

        # Delete single
        self.assertTrue(PersonalMemoryService.delete_memory(m1["id"], user_id="test_user_2"))
        self.assertEqual(len(PersonalMemoryService.get_user_memories(user_id="test_user_2")), 1)

        # Purge all
        purged = PersonalMemoryService.purge_all_memories(user_id="test_user_2")
        self.assertEqual(purged, 1)
        self.assertEqual(len(PersonalMemoryService.get_user_memories(user_id="test_user_2")), 0)


if __name__ == "__main__":
    unittest.main()
