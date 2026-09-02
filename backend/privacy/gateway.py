"""
NeuraSearch v2.0 — Central Privacy Gateway & Policy Engine
Enforces strict tripartite research rules, blocks silent data exfiltration, and manages outbound permission grants.
"""

import logging
import uuid
from typing import Dict, Any, Optional, Tuple, List
from providers.base import ResearchMode, DataClassification, SearchResult
from privacy.query_sanitizer import sanitize_and_generalize_query
from database import db
from core.exceptions import NeuraSearchError

logger = logging.getLogger("neurasearch.privacy.gateway")


class PrivacyFirewallViolation(NeuraSearchError):
    """Raised when an operation attempts to violate privacy boundaries."""
    def __init__(self, message: str, code: str = "PRIVACY_FIREWALL_VIOLATION"):
        super().__init__(message, code)


class PrivacyGateway:
    """
    Central Policy Enforcement Point (PEP).
    Validates all tool calls and data transitions against strict privacy rules.
    """

    @staticmethod
    def evaluate_outbound_request(
        mode: str,
        raw_query: str,
        destination: str,
        session_id: Optional[str] = None,
        user_id: str = "admin",
        contains_private_context: bool = False
    ) -> Dict[str, Any]:
        """
        Evaluates whether an outbound request is permitted, blocked, or requires explicit user approval.
        Returns:
            {
                "action": "ALLOW" | "BLOCK" | "REQUIRE_CONSENT",
                "sanitized_query": str,
                "grant_id": Optional[str],
                "reason": str
            }
        """
        mode = mode.lower()

        # RULE 1: PRIVATE MODE -> STRICT AIR-GAP
        if mode == ResearchMode.PRIVATE.value:
            event_id = str(uuid.uuid4())
            db.log_privacy_event_v2(
                event_id=event_id,
                user_id=user_id,
                event_type="BLOCKED_EXTERNAL_CALL",
                data_classification=DataClassification.PRIVATE.value,
                details={"reason": "Private mode is air-gapped. External search is strictly disabled.", "destination": destination},
                session_id=session_id
            )
            return {
                "action": "BLOCK",
                "sanitized_query": "",
                "grant_id": None,
                "reason": "Air-gapped: Outbound web search is strictly prohibited in Private Mode."
            }

        # RULE 2: ONLINE MODE -> ALLOW WITH SANITIZATION (NO PRIVATE CONTEXT)
        if mode == ResearchMode.ONLINE.value:
            if contains_private_context:
                raise PrivacyFirewallViolation("Online mode cannot be supplied with raw private workspace context.")
            
            sanitized, redacted, _ = sanitize_and_generalize_query(raw_query)
            return {
                "action": "ALLOW",
                "sanitized_query": sanitized,
                "grant_id": None,
                "reason": "Online mode permitted for public queries."
            }

        # RULE 3 & 4: HYBRID MODE -> EXPLICIT OUTBOUND CONSENT GATEWAY
        if mode == ResearchMode.HYBRID.value:
            sanitized, redacted, audit_meta = sanitize_and_generalize_query(raw_query)
            
            if contains_private_context or audit_meta.get("has_modifications"):
                grant_id = f"grant_{uuid.uuid4().hex[:12]}"
                db.create_permission_grant_v2(
                    grant_id=grant_id,
                    session_id=session_id or "default_session",
                    proposed_query=sanitized,
                    raw_context_summary=f"Redacted {len(redacted)} sensitive item(s)" if redacted else "Derived from private workspace",
                    destination=destination,
                    user_id=user_id
                )
                db.log_privacy_event_v2(
                    event_id=str(uuid.uuid4()),
                    user_id=user_id,
                    event_type="OUTBOUND_CONSENT_REQUESTED",
                    data_classification=DataClassification.USER_APPROVED_PRIVATE.value,
                    details={"grant_id": grant_id, "destination": destination, "proposed_query": sanitized},
                    session_id=session_id
                )
                return {
                    "action": "REQUIRE_CONSENT",
                    "sanitized_query": sanitized,
                    "grant_id": grant_id,
                    "reason": "Hybrid mode: Outbound search requires explicit user authorization."
                }
            else:
                return {
                    "action": "ALLOW",
                    "sanitized_query": sanitized,
                    "grant_id": None,
                    "reason": "Hybrid mode: Clean public query without private context."
                }

        raise PrivacyFirewallViolation(f"Unrecognized research mode: '{mode}'")

    @staticmethod
    def verify_permission_grant(grant_id: str) -> bool:
        """Verify that a permission grant exists and was approved by the user."""
        grant = db.get_permission_grant_v2(grant_id)
        if not grant:
            return False
        return grant.get("status") == "approved"
