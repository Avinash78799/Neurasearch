import sys
import os
import unittest
import uuid
import asyncio
from pathlib import Path

# Add backend directory to sys.path
backend_dir = str(Path(__file__).resolve().parent.parent / "backend")
sys.path.append(backend_dir)

from database import db
from config import settings
from workspace_service import WorkspaceContext, WorkspaceService
from graph.graph import crag_graph
from graph.nodes.computation_tool import execute_computation
from research.engine import ResearchPlanner, ResearchExecutor, run_deep_research

class TestResearchEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        WorkspaceService.ensure_default_workspace()

    def setUp(self):
        self.ws_id = f"ws_research_{uuid.uuid4().hex[:6]}"
        WorkspaceService.create_workspace(self.ws_id, f"Workspace Research {self.ws_id}")
        self.context = WorkspaceContext(self.ws_id)

    def test_computation_tool_sandbox(self):
        # 1. Safe Arithmetic Calculation
        code_safe = """
a = 15
b = 30
result = a * b + 100
"""
        res = execute_computation(code_safe)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["result"], "550")
        self.assertIsNone(res["error"])

        # 2. Safe Date & Math Evaluation
        code_date = """
import datetime
import math
d1 = datetime.datetime(2026, 7, 5)
d2 = datetime.datetime(2026, 7, 10)
diff = (d2 - d1).days
result = diff * math.pi
"""
        res_date = execute_computation(code_date)
        self.assertEqual(res_date["status"], "success")
        self.assertTrue(res_date["result"].startswith("15.7079"))

        # 3. Unsafe Sandbox Execution: file system write attempt
        code_unsafe_fs = """
with open("hack.txt", "w") as f:
    f.write("hacked")
result = "success"
"""
        res_fs = execute_computation(code_unsafe_fs)
        self.assertEqual(res_fs["status"], "error")
        self.assertIn("name 'open' is not defined", res_fs["error"])

        # 4. Unsafe Sandbox Execution: system commands
        code_unsafe_os = """
import os
os.system("echo hacked")
result = "success"
"""
        res_os = execute_computation(code_unsafe_os)
        self.assertEqual(res_os["status"], "error")
        # Should raise error because os module in sys.modules is blocked (None)
        self.assertIn("blocked in sandbox", res_os["error"])

    def test_research_blueprint_lifecycle(self):
        session_id = str(uuid.uuid4())
        question = "What are the latest breakthroughs in local LLM inference engines?"
        blueprint = ["Breakthroughs in llama.cpp", "ONNX and FlashRank optimizations", "Local GPU vs CPU v2.1 specs"]
        
        # Save session as blueprint
        db.save_research_session(session_id, self.ws_id, "blueprint", question, blueprint, thread_id=session_id)
        
        # Retrieve session
        session = db.get_research_session(session_id, context=self.context)
        self.assertIsNotNone(session)
        self.assertEqual(session["status"], "blueprint")
        self.assertEqual(session["original_question"], question)
        self.assertEqual(len(session["blueprint"]), 3)
        
        # Update session status
        db.update_research_session_status(session_id, "completed", context=self.context)
        session_updated = db.get_research_session(session_id, context=self.context)
        self.assertEqual(session_updated["status"], "completed")

    def test_langgraph_sqlite_saver_checkpoint(self):
        # Verify that we can invoke the compiled graph with checkpointer and it persists state
        thread_id = f"thread_{uuid.uuid4().hex}"
        config = {"configurable": {"thread_id": thread_id}}
        
        # Trigger checkpoints table creation directly
        crag_graph.checkpointer.setup()
            
        import sqlite3
        conn = sqlite3.connect(settings.sqlite_db_path)
        cursor = conn.cursor()
        
        # Check if checkpoints table is generated in sqlite by SqliteSaver
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='checkpoints'")
        self.assertIsNotNone(cursor.fetchone())
        
        conn.close()

if __name__ == "__main__":
    unittest.main()
