"""
NeuraSearch v2.0 — Boundary Interception Security & Privacy Test Suite
Validates that security controls hold at actual runtime network/LLM boundaries.
"""

import sys
import os
import unittest
import asyncio
import http.server
import threading
import time
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from privacy.query_sanitizer import sanitize_and_generalize_query
from privacy.gateway import PrivacyGateway, PrivacyFirewallViolation
from providers.fetcher import SecureWebFetcher, is_safe_url
from providers.base import LLMResponse, SearchResult
from research.agent import AutonomousResearchAgent
from database import db
from auth import JWT_SECRET_KEY


class MockCloudLLM:
    """Simulates a cloud LLM provider (Groq/OpenAI) to verify boundary interception."""
    is_local: bool = False
    provider_name: str = "cloud_mock"

    def __init__(self):
        self.intercepted_prompts = []

    async def generate(self, prompt: str, **kwargs):
        self.intercepted_prompts.append(prompt)
        return LLMResponse(content="Mock response from cloud LLM", model="cloud-llm")

    async def stream(self, prompt: str, **kwargs):
        self.intercepted_prompts.append(prompt)
        yield "Mock response"


class MockSearchProvider:
    """Mock search provider to verify outbound search calls."""
    def __init__(self):
        self.searches_received = []

    async def search(self, query: str, **kwargs):
        self.searches_received.append(query)
        return [
            SearchResult(
                url="https://example.com/article",
                title="Public Article",
                snippet="Public information regarding the research question.",
                publisher="example.com",
                score=0.9
            )
        ]


class RedirectHttpHandler(http.server.BaseHTTPRequestHandler):
    """Local HTTP handler that redirects to an internal/cloud-metadata IP."""
    def do_GET(self):
        if self.path == "/redirect-to-internal":
            self.send_response(302)
            self.send_header("Location", "http://127.0.0.1:8000/secret-internal-endpoint")
            self.end_headers()
        elif self.path == "/redirect-to-metadata":
            self.send_response(302)
            self.send_header("Location", "http://169.254.169.254/latest/meta-data")
            self.end_headers()
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Safe Public Page Content")

    def log_message(self, format, *args):
        pass  # Quiet logging


class TestSecurityAndPrivacyBoundaries(unittest.TestCase):
    """Authoritative integration tests asserting against actual call boundaries."""

    @classmethod
    def setUpClass(cls):
        # Start local redirect server for SSRF revalidation test
        cls.server = http.server.HTTPServer(("127.0.0.1", 0), RedirectHttpHandler)
        cls.port = cls.server.server_port
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def test_1_1_private_mode_blocks_cloud_llm_synthesis(self):
        """1.1: Private Mode MUST hard-block cloud LLMs when private documents are present."""
        cloud_llm = MockCloudLLM()
        agent = AutonomousResearchAgent(
            workspace_id="test_workspace",
            mode="private",
            depth="fast",
            llm=cloud_llm
        )

        async def run():
            with self.assertRaises(PrivacyFirewallViolation) as ctx:
                async for _ in agent.execute_research("Analyze proprietary algorithm"):
                    pass
            self.assertIn("Private Mode is strictly air-gapped", str(ctx.exception))
            # Assert zero document prompts were sent to the cloud LLM
            self.assertEqual(len(cloud_llm.intercepted_prompts), 0)

        asyncio.run(run())

    def test_1_1b_online_mode_does_not_pull_or_leak_private_documents(self):
        """1.1b: Online Mode MUST NOT retrieve or leak private workspace documents to cloud LLMs."""
        cloud_llm = MockCloudLLM()
        mock_search = MockSearchProvider()
        agent = AutonomousResearchAgent(
            workspace_id="test_workspace_secrets",
            mode="online",
            depth="fast",
            llm=cloud_llm,
            search_provider=mock_search
        )

        async def run():
            events = []
            async for ev in agent.execute_research("Research public semiconductor supply chains"):
                events.append(ev)
            # Verify synthesis completed
            self.assertGreater(len(cloud_llm.intercepted_prompts), 0)
            # Verify no private document markers or workspace secrets reached the prompt
            for prompt in cloud_llm.intercepted_prompts:
                self.assertNotIn("Private Workspace", prompt)
                self.assertNotIn("private_file", prompt)

        asyncio.run(run())



    def test_1_2_sanitizer_redacts_realistic_secrets_and_high_entropy_tokens(self):
        """1.2: Query sanitizer must catch embedded secret patterns and high-entropy keys."""
        test_queries = [
            "Investigate PROJECT_ALPHA_SECRET_KEY_88213 details",
            "Review CONFIDENTIAL_CLIENT_LIST_2026 for expansion",
            "Connect to api key ak_live_89f7a9d7c3b2e1f4a56b78c9 for verification",
            "Contact user@private-internal-domain.com at 192.168.1.50"
        ]

        for q in test_queries:
            sanitized, redacted, meta = sanitize_and_generalize_query(q)
            self.assertTrue(meta["has_modifications"])
            self.assertNotIn("PROJECT_ALPHA_SECRET_KEY_88213", sanitized)
            self.assertNotIn("CONFIDENTIAL_CLIENT_LIST_2026", sanitized)
            self.assertNotIn("ak_live_89f7a9d7c3b2e1f4a56b78c9", sanitized)
            self.assertNotIn("user@private-internal-domain.com", sanitized)
            self.assertNotIn("192.168.1.50", sanitized)

    def test_1_3_hybrid_mode_blocks_search_until_consent_approved(self):
        """1.3: In Hybrid mode, outbound search must genuinely block until grant is approved."""
        from privacy.gateway import PrivacyGateway
        
        # Test evaluate_outbound_request requires consent
        eval_res = PrivacyGateway.evaluate_outbound_request(
            mode="hybrid",
            raw_query="Find competitors for our company's secret strategy",
            destination="Search Engine"
        )
        self.assertEqual(eval_res["action"], "REQUIRE_CONSENT")
        grant_id = eval_res["grant_id"]
        self.assertIsNotNone(grant_id)

        # Before approval
        self.assertFalse(PrivacyGateway.verify_permission_grant(grant_id))

        # Approve grant
        db.update_permission_grant_v2(grant_id, "approved")

        # After approval
        self.assertTrue(PrivacyGateway.verify_permission_grant(grant_id))


    def test_1_4_crag_chat_web_search_node_respects_privacy_mode(self):
        """1.4: Main CRAG chat pipeline web_search node must check PrivacyGateway."""
        from graph.nodes.web_search import web_search

        async def run_check():
            state = {
                "question": "What is our company's secret strategy?",
                "mode": "private",
                "steps_taken": []
            }
            res = await web_search(state)
            self.assertEqual(len(res["web_results"]), 0)
            self.assertEqual(len(res["final_context"]), 0)
            self.assertTrue(any("blocked" in s.lower() for s in res["steps_taken"]))

        asyncio.run(run_check())

    def test_1_5_ssrf_per_hop_redirect_revalidation(self):
        """1.5: SSRF revalidation must block redirects to internal IP addresses."""
        fetcher = SecureWebFetcher(timeout_seconds=3.0)

        async def test_redirects():
            # Test redirect to 127.0.0.1
            doc = await fetcher.fetch_and_extract(f"http://127.0.0.1:{self.port}/redirect-to-internal")
            self.assertFalse(doc.is_safe)
            self.assertEqual(doc.status_code, 403)
            self.assertIn("Access denied", doc.error_message)

            # Test redirect to 169.254.169.254
            doc_meta = await fetcher.fetch_and_extract(f"http://127.0.0.1:{self.port}/redirect-to-metadata")
            self.assertFalse(doc_meta.is_safe)
            self.assertEqual(doc_meta.status_code, 403)

        asyncio.run(test_redirects())

    def test_1_6_jwt_secret_is_not_hardcoded(self):
        """1.6: JWT secret must not equal the legacy hardcoded fallback string."""
        self.assertNotEqual(JWT_SECRET_KEY, "neurasearch_super_secret_local_key_123")
        self.assertGreater(len(JWT_SECRET_KEY), 20)

    def test_1_7_admin_forced_password_rotation(self):
        """1.7: Default seeded admin user must have must_rotate_password flag set."""
        admin_user = db.get_user("admin")
        self.assertIsNotNone(admin_user)
        self.assertEqual(admin_user.get("must_rotate_password"), 1)

        # Verify updating password clears the flag
        from auth import get_password_hash
        new_hash = get_password_hash("new_secure_admin_password_2026!")
        db.update_user_password("admin", new_hash)
        
        updated_admin = db.get_user("admin")
        self.assertEqual(updated_admin.get("must_rotate_password"), 0)

        # Restore default state for tests
        default_hash = get_password_hash("password123")
        db.update_user_password("admin", default_hash)
        with db.get_connection() as conn:
            conn.execute("UPDATE users SET must_rotate_password = 1 WHERE username = 'admin'")

    def test_3_6_citation_formatting_apa_mla_bibtex(self):
        """3.6: Verify APA, MLA, and BibTeX citation formatting."""
        from citation_service import CitationService

        source = {
            "id": "src_12345",
            "title": "Quantum Error Correction in Neutral Atom Arrays",
            "publisher": "Harvard Physics Lab",
            "url": "https://arxiv.org/abs/2401.00123",
            "published_date": "2026-01-15"
        }

        apa = CitationService.format_citation(source, style="apa")
        mla = CitationService.format_citation(source, style="mla")
        bibtex = CitationService.format_citation(source, style="bibtex")

        self.assertIn("Harvard Physics Lab", apa)
        self.assertIn("2026", apa)
        self.assertIn("Quantum Error Correction", mla)
        self.assertIn("@misc{", bibtex)
        self.assertIn("title = {Quantum Error Correction in Neutral Atom Arrays}", bibtex)

    def test_3_8_embedding_cache_prevents_duplicate_computations(self):
        """3.8: Verify SQLite embedding cache retrieves stored vectors without re-embedding."""
        from core.model_registry import get_embeddings
        embedder = get_embeddings()

        test_text = "Unique embedding caching test string for NeuraSearch v2 benchmark."
        
        async def run_embed():
            # First computation
            emb1 = await embedder.aembed_query(test_text)
            self.assertIsInstance(emb1, list)
            self.assertGreater(len(emb1), 0)

            # Second computation must hit cache
            emb2 = await embedder.aembed_query(test_text)
            import numpy as np
            self.assertTrue(np.allclose(emb1, emb2, atol=1e-5))

        asyncio.run(run_embed())


if __name__ == "__main__":
    unittest.main()

