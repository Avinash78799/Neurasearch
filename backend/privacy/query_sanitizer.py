"""
NeuraSearch v2.0 — Privacy Query Sanitizer
Transforms private context, confidential details, and PII into generalized, non-confidential search queries.
"""

import re
import logging
import math
from typing import Tuple, List, Dict, Any

logger = logging.getLogger("neurasearch.privacy.sanitizer")

# Patterns for sensitive entities to redact or generalize
EMAIL_PATTERN = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
PHONE_PATTERN = r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
IP_PATTERN = r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"
FINANCIAL_PATTERN = r"[\$€£¥]\s*\d+(?:[.,]\d+)*(?:\s*(?:million|billion|k|M|B))?"

# Substring keyword matching: match keywords anywhere inside a token
INTERNAL_CODE_PATTERN = r"(?i)\b[A-Z0-9_-]*(?:SECRET|API|PRIVATE|KEY|TOKEN|CONFIDENTIAL|INTERNAL|CREDENTIAL|PASSWORD)[A-Z0-9_-]*\b"

# High-entropy token pattern (hex/base64/uuid/alphanumeric tokens 20+ chars)
LONG_TOKEN_PATTERN = r"\b[A-Za-z0-9_-]{20,}\b"


def _shannon_entropy(token: str) -> float:
    """Calculate Shannon entropy for a given token string."""
    if not token:
        return 0.0
    prob = [token.count(c) / len(token) for c in set(token)]
    return -sum(p * math.log2(p) for p in prob)


def sanitize_and_generalize_query(raw_query: str, private_context: str = "") -> Tuple[str, List[str], Dict[str, Any]]:
    """
    Sanitize a user query or private context before outbound transmission.
    Returns:
        (sanitized_query, redacted_items, audit_metadata)
    """
    redacted_items = []
    sanitized = raw_query

    # 1. Redact direct PII patterns
    for pat, label in [
        (EMAIL_PATTERN, "[REDACTED_EMAIL]"),
        (PHONE_PATTERN, "[REDACTED_PHONE]"),
        (IP_PATTERN, "[REDACTED_IP]"),
        (FINANCIAL_PATTERN, "[REDACTED_FINANCIAL]"),
        (INTERNAL_CODE_PATTERN, "[REDACTED_SECRET]"),
    ]:
        matches = re.findall(pat, sanitized)
        if matches:
            redacted_items.extend(matches)
            sanitized = re.sub(pat, label, sanitized)

    # 2. Redact high-entropy / long arbitrary secret tokens (20+ chars or entropy > 3.2)
    potential_tokens = re.findall(r"\b[A-Za-z0-9_-]{16,}\b", sanitized)
    for tok in potential_tokens:
        if tok.startswith("REDACTED_") or tok.startswith("[REDACTED_"):
            continue
        if len(tok) >= 20 or _shannon_entropy(tok) >= 3.2:
            redacted_items.append(tok)
            sanitized = re.sub(r"\b" + re.escape(tok) + r"\b", "[REDACTED_SECRET]", sanitized)


    # 3. Generalization rules for company-specific confidential phrasing
    confidential_phrases = [
        r"(?i)\bour\s+company's\s+secret\b",
        r"(?i)\bour\s+internal\s+strategy\b",
        r"(?i)\bconfidential\s+client\s+list\b",
        r"(?i)\bproprietary\s+code\b",
        r"(?i)\bmy\s+private\s+database\b",
    ]
    for c_pat in confidential_phrases:
        if re.search(c_pat, sanitized):
            sanitized = re.sub(c_pat, "industry standard methods", sanitized)
            redacted_items.append("confidential corporate phrasing")

    audit_metadata = {
        "original_length": len(raw_query),
        "sanitized_length": len(sanitized),
        "redacted_count": len(redacted_items),
        "has_modifications": len(redacted_items) > 0
    }

    return sanitized.strip(), redacted_items, audit_metadata

