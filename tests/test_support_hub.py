import unittest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from support.support_service import SupportService
from workspace_service import WorkspaceContext

class TestSupportHub(unittest.TestCase):
    def setUp(self):
        self.context = WorkspaceContext(workspace_id="ws_support_test", username="tester")

    def test_full_diagnostics(self):
        diag = SupportService.get_full_diagnostics(context=self.context)
        self.assertIn("hardware", diag)
        self.assertIn("database", diag)
        self.assertIn("search_indices", diag)
        self.assertIn("models", diag)
        self.assertEqual(diag["workspace_id"], "ws_support_test")

    def test_create_and_list_support_ticket(self):
        ticket = SupportService.create_support_ticket(
            subject="Test Latency Issue",
            category="hardware_performance",
            message="Evaluating Eco profile performance on laptop.",
            user_email="dev@example.com",
            system_info={"gpu": "GTX 1650"}
        )
        self.assertTrue(ticket["ticket_id"].startswith("TICK-"))
        self.assertEqual(ticket["subject"], "Test Latency Issue")
        self.assertEqual(ticket["status"], "open")

        tickets = SupportService.list_support_tickets()
        self.assertTrue(len(tickets) > 0)
        found = any(t["id"] == ticket["ticket_id"] for t in tickets)
        self.assertTrue(found)

    def test_run_vacuum_db(self):
        res = SupportService.run_vacuum_db()
        self.assertEqual(res["status"], "success")
        self.assertIn("duration_seconds", res)

if __name__ == "__main__":
    unittest.main()
