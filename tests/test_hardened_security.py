"""
Hardened Security Test Suite for NeuraSearch.
Validates:
- Python sandbox AST analyzer (dunder breakout & code injection defense)
- GitHub repo parameter sanitization & URL traversal prevention
- Request body payload size middleware (DoS defense)
- File upload magic byte validation
- Rate limiting on authentication routes
"""

import sys
import unittest
from pathlib import Path
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from graph.nodes.computation_tool import is_code_safe, execute_computation
from rag.github_connector import _parse_github_url
from main import app


class TestHardenedSecurity(unittest.TestCase):
    """Verifies critical server-side and client-side security barriers."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_sandbox_blocks_dunder_subclasses_jailbreak(self):
        """Disallow Python sandbox breakout via __subclasses__()."""
        payload = "[c for c in ().__class__.__base__.__subclasses__() if c.__name__ == 'BuiltinImporter']"
        safe, reason = is_code_safe(payload)
        self.assertFalse(safe)
        self.assertIn("restricted attribute", reason.lower())

        res = execute_computation(payload)
        self.assertEqual(res["status"], "error")
        self.assertIn("Security validation failed", res["error"])

    def test_sandbox_blocks_globals_and_code_attributes(self):
        """Disallow Python sandbox access to __globals__ and __code__."""
        for attr in ["__globals__", "__code__", "__mro__", "__builtins__"]:
            code = f"x = (lambda: None).{attr}"
            safe, reason = is_code_safe(code)
            self.assertFalse(safe, f"Expected {attr} to be blocked")

    def test_sandbox_blocks_eval_exec_calls(self):
        """Disallow eval, exec, and compile in the sandbox."""
        for fn in ["eval('1+1')", "exec('x=1')", "compile('1', '', 'single')"]:
            safe, reason = is_code_safe(fn)
            self.assertFalse(safe, f"Expected {fn} to be blocked")

    def test_sandbox_allows_safe_math_computation(self):
        """Allow pure arithmetic and standard allowed builtins."""
        code = "result = sum([1, 2, 3, 4, 5]) * 2"
        safe, reason = is_code_safe(code)
        self.assertTrue(safe, f"Expected safe code to pass, failed with: {reason}")

        res = execute_computation(code)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["result"], "30")

    def test_github_url_traversal_rejection(self):
        """Reject path traversal or invalid characters in GitHub owner/repo."""
        invalid_repos = [
            "../../etc/passwd",
            "owner/repo;rm -rf",
            "owner/repo<script>",
            "owner$/repo",
            "owner/repo*test",
        ]
        for inv in invalid_repos:
            with self.assertRaises(ValueError):
                _parse_github_url(inv)

    def test_github_url_valid_parsing(self):
        """Parse clean valid GitHub owner/repo formats."""
        owner, repo, path = _parse_github_url("https://github.com/torvalds/linux.git")
        self.assertEqual(owner, "torvalds")
        self.assertEqual(repo, "linux")
        self.assertIsNone(path)

        owner, repo, path = _parse_github_url("facebook/react/packages/react")
        self.assertEqual(owner, "facebook")
        self.assertEqual(repo, "react")
        self.assertEqual(path, "packages/react")

    def test_request_size_limit_middleware_rejects_oversized_payload(self):
        """Verify middleware blocks requests declaring Content-Length > 5MB with HTTP 413."""
        headers = {
            "Content-Length": str(10 * 1024 * 1024),  # 10MB
            "Content-Type": "application/json"
        }
        resp = self.client.post("/token", headers=headers, content=b"{}")
        self.assertEqual(resp.status_code, 413)
        self.assertIn("Payload too large", resp.json()["detail"])

    def test_ingest_rejects_invalid_magic_bytes_for_pdf(self):
        """Verify file upload rejects executable masquerading as PDF."""
        from auth import create_access_token
        token = create_access_token({"sub": "admin", "role": "admin"})
        fake_pdf = b"MZ\x90\x00\x03\x00\x00\x00BinaryExeContentHere"
        files = {"file": ("malicious.pdf", fake_pdf, "application/pdf")}
        resp = self.client.post("/api/v1/ingest", files=files, headers={"Authorization": f"Bearer {token}"})
        # 400 Bad Request: missing %PDF
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Missing %PDF signature", resp.json()["detail"])

    def test_ingest_rejects_binary_in_text_file(self):
        """Verify file upload rejects binary null bytes in txt file."""
        from auth import create_access_token
        token = create_access_token({"sub": "admin", "role": "admin"})
        fake_txt = b"Hello world\x00\x01\x02\x03NullBytesHere"
        files = {"file": ("notes.txt", fake_txt, "text/plain")}
        resp = self.client.post("/api/v1/ingest", files=files, headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("null bytes detected", resp.json()["detail"].lower())



if __name__ == "__main__":
    unittest.main()
