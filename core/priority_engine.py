"""
Priority Engine
Deterministic, transparent Python-based scoring engine for messages and tasks.
Evaluates deadline proximity, direct user mentions, urgency phrases, and plan changes.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional

from config import HIGH_PRIORITY_KEYWORDS, MEDIUM_PRIORITY_KEYWORDS


@dataclass
class PriorityItem:
    score: int  # 0 to 100
    level: str  # "High", "Medium", "Low"
    reasons: List[str] = field(default_factory=list)


class PriorityEngine:
    """Computes deterministic priority score with explicit factor tracking."""

    # Urgency patterns
    RE_URGENT = re.compile(r"\b(urgent|asap|critical|blocking|emergency|immediately|high priority)\b", re.IGNORECASE)
    RE_DEADLINE_TODAY = re.compile(r"\b(by\s+today|today\s+by|\b5\s*pm\s+today|eod\s+today|tonight)\b", re.IGNORECASE)
    RE_DEADLINE_GENERAL = re.compile(r"\b(deadline|due\s+date|due|submit\s+by|finish\s+by|tomorrow|by\s+tomorrow|by\s+\w+day|by\s+\d+)\b", re.IGNORECASE)
    RE_PLAN_CHANGE = re.compile(r"\b(rescheduled|cancelled|postponed|moved to|change of plans|pushed back)\b", re.IGNORECASE)
    RE_ACTION_REQUEST = re.compile(r"\b(please\s+(?:review|send|submit|sign|check|verify|fix|update)|action required)\b", re.IGNORECASE)

    def __init__(self, user_name: Optional[str] = None):
        self.user_name = user_name.strip() if user_name and user_name.strip() else None

    def evaluate_text(
        self,
        text: str,
        sender: str = "",
        message_time: Optional[datetime] = None,
        is_task: bool = False,
    ) -> PriorityItem:
        """
        Evaluates a text string or message for priority scoring.
        Returns PriorityItem with score (0-100), level ('High', 'Medium', 'Low'), and explanation reasons.
        """
        score = 10  # Baseline
        reasons: List[str] = []

        if not text:
            return PriorityItem(score=0, level="Low", reasons=["Empty content"])

        lower = text.lower()

        # 1. Critical Urgency Keywords (+35)
        if self.RE_URGENT.search(text):
            score += 35
            reasons.append("Contains explicit urgency language ('urgent' / 'asap' / 'critical')")

        # 2. Deadline Proximity (+30 for today, +20 for general deadline)
        if self.RE_DEADLINE_TODAY.search(text):
            score += 30
            reasons.append("Identified immediate deadline ('today' / 'EOD')")
        elif self.RE_DEADLINE_GENERAL.search(text):
            score += 20
            reasons.append("Identified upcoming deadline or submission requirement")

        # 3. Direct Mentions of configured User Name or Assignment (+25)
        if self.user_name:
            user_pattern = rf"(?:@|\b){re.escape(self.user_name.lower())}\b"
            if is_task and sender and sender.lower() == self.user_name.lower():
                score += 25
                reasons.append(f"Task assigned directly to you ('{self.user_name}')")
            elif re.search(user_pattern, lower) and (not sender or sender.lower() != self.user_name.lower()):
                score += 25
                reasons.append(f"Direct mention of your name ('{self.user_name}')")

        # 4. Plan changes (+20)
        if self.RE_PLAN_CHANGE.search(text):
            score += 20
            reasons.append("Mentions schedule/plan modification ('rescheduled' / 'cancelled')")

        # 5. Direct Action Requests (+15)
        if self.RE_ACTION_REQUEST.search(text):
            score += 15
            reasons.append("Direct action request ('please review/submit/sign')")

        # 6. Task flag (+10)
        if is_task:
            score += 10
            reasons.append("Identified as an actionable deliverable")

        # Bound score between 0 and 100
        score = min(max(score, 0), 100)

        # Categorize
        if score >= 65:
            level = "High"
        elif score >= 40:
            level = "Medium"
        else:
            level = "Low"

        if not reasons:
            reasons.append("Standard routine conversation item")

        return PriorityItem(score=score, level=level, reasons=reasons)
