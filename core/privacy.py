"""
Privacy Auditor & Sanitizer
Enforces privacy-first operational rules: in-memory guarantees, phone number redaction,
and clear session data wiping.
"""
from __future__ import annotations

import re
from typing import List

from .whatsapp_parser import ParsedMessage


class PrivacyAuditor:
    """Verifies local processing boundaries and assists in sanitization."""

    # International and domestic phone number pattern
    RE_PHONE_NUMBER = re.compile(
        r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}"
    )

    # Email pattern
    RE_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b")

    @classmethod
    def sanitize_text(cls, text: str, redact_phones: bool = True, redact_emails: bool = False) -> str:
        """Masks sensitive telephone numbers or emails if requested by user."""
        cleaned = text
        if redact_phones:
            cleaned = cls.RE_PHONE_NUMBER.sub("[PHONE REDACTED]", cleaned)
        if redact_emails:
            cleaned = cls.RE_EMAIL.sub("[EMAIL REDACTED]", cleaned)
        return cleaned

    @classmethod
    def sanitize_messages(cls, messages: List[ParsedMessage], redact_phones: bool = True) -> List[ParsedMessage]:
        """Returns messages with personal phone numbers masked in text and sender fields."""
        sanitized: List[ParsedMessage] = []
        for m in messages:
            san_sender = cls.sanitize_text(m.sender, redact_phones=redact_phones)
            san_text = cls.sanitize_text(m.text, redact_phones=redact_phones)
            sanitized.append(
                ParsedMessage(
                    id=m.id,
                    raw_timestamp=m.raw_timestamp,
                    sender=san_sender,
                    text=san_text,
                    message_type=m.message_type,
                    timestamp=m.timestamp,
                    multiline=m.multiline,
                )
            )
        return sanitized

    @staticmethod
    def get_privacy_statement() -> dict:
        return {
            "local_only": True,
            "external_ai_apis": "None (100% Local Ollama)",
            "telemetry_present": False,
            "data_persistence": "Volatile Streamlit In-Memory Session Only",
            "disk_writes": "Disabled (No chat transcripts saved to disk)",
            "network_egress": "Localhost HTTP only (http://localhost:11434)",
            "memory_disclaimer": (
                "Clearing the session immediately resets Python variables and UI state. "
                "However, as with all operating systems and virtual machines, forensic erasure "
                "from OS RAM swap or process memory cannot be cryptographically guaranteed."
            ),
        }
