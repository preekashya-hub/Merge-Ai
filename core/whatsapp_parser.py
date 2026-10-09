"""
Merge AI - WhatsApp Chat Export Parser
Handles varied mobile OS formats (Android, iOS), 12h/24h timestamps,
multiline continuations, media placeholders, and system messages.
Integrates tightly with AutoDetector for automated schema identification.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Tuple

from .auto_detector import AutoDetector, DetectionReport


@dataclass
class ParsedMessage:
    id: str
    raw_timestamp: str
    sender: str
    text: str
    message_type: str = "user"  # 'user', 'system', 'media'
    timestamp: Optional[datetime] = None
    multiline: bool = False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "raw_timestamp": self.raw_timestamp,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "sender": self.sender,
            "text": self.text,
            "message_type": self.message_type,
            "multiline": self.multiline,
        }


class WhatsAppParser:
    """Robust parser for WhatsApp chat exports (.txt files) with integrated Auto-Detector."""

    PATTERN_ANDROID = re.compile(
        r"^(\d{1,4}[/\.-]\d{1,2}[/\.-]\d{2,4}),?\s+(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AaPp][Mm])?)\s*[-–—]\s*(.*)$"
    )
    PATTERN_IOS = re.compile(
        r"^\[(\d{1,4}[/\.-]\d{1,2}[/\.-]\d{2,4}),?\s+(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AaPp][Mm])?)\]\s*(.*)$"
    )
    PATTERN_COLON = re.compile(
        r"^(\d{1,4}[/\.-]\d{1,2}[/\.-]\d{2,4}),?\s+(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AaPp][Mm])?):\s*(.*)$"
    )

    SYSTEM_PHRASES = [
        "messages and calls are end-to-end encrypted",
        "created group",
        "added",
        "removed",
        "left",
        "changed the subject",
        "changed the group",
        "changed this group's",
        "changed the icon",
        "security code changed",
        "you were added",
        "pinned a message",
        "disappearing messages",
    ]

    MEDIA_PHRASES = [
        "<media omitted>",
        "image omitted",
        "video omitted",
        "audio omitted",
        "sticker omitted",
        "document omitted",
        "gif omitted",
        "contact card omitted",
    ]

    DATE_FORMATS = [
        "%d/%m/%y, %H:%M",
        "%d/%m/%Y, %H:%M",
        "%m/%d/%y, %H:%M",
        "%m/%d/%Y, %H:%M",
        "%d/%m/%y, %I:%M %p",
        "%d/%m/%Y, %I:%M %p",
        "%m/%d/%y, %I:%M %p",
        "%m/%d/%Y, %I:%M %p",
        "%d.%m.%y, %H:%M",
        "%d.%m.%Y, %H:%M",
        "%Y-%m-%d, %H:%M",
        "%d/%m/%y, %H:%M:%S",
        "%d/%m/%Y, %H:%M:%S",
        "%m/%d/%y, %H:%M:%S %p",
        "%m/%d/%Y, %I:%M:%S %p",
    ]

    def __init__(self, user_name: Optional[str] = None):
        self.user_name = user_name
        self.warnings: List[str] = []
        self.auto_detector = AutoDetector()
        self.latest_report: Optional[DetectionReport] = None

    def inspect_chat(self, raw_text: str, encoding: str = "UTF-8") -> DetectionReport:
        """Runs the AutoDetector engine on the raw chat text."""
        self.latest_report = self.auto_detector.inspect(raw_text, detected_encoding=encoding)
        return self.latest_report

    def _parse_timestamp(self, date_str: str, time_str: str) -> Tuple[str, Optional[datetime]]:
        cleaned_time = re.sub(r"\s+", " ", time_str.strip())
        raw_combined = f"{date_str.strip()}, {cleaned_time}"
        std_date = date_str.strip().replace(".", "/")

        for fmt in self.DATE_FORMATS:
            try:
                candidate = f"{std_date}, {cleaned_time}"
                dt = datetime.strptime(candidate, fmt)
                return raw_combined, dt
            except ValueError:
                continue

        return raw_combined, None

    def _extract_sender_and_text(self, payload: str) -> Tuple[str, str, str]:
        clean_payload = payload.strip()
        lower_payload = clean_payload.lower()

        if any(phrase in lower_payload for phrase in self.SYSTEM_PHRASES):
            return "System", clean_payload, "system"

        sender_match = re.match(r"^([^:\n]+?):\s*(.*)$", clean_payload, re.DOTALL)
        if sender_match:
            sender = sender_match.group(1).strip()
            text = sender_match.group(2).strip()

            if any(m in text.lower() for m in self.MEDIA_PHRASES):
                return sender, text, "media"
            return sender, text, "user"

        return "System", clean_payload, "system"

    def parse(self, text_content: str, run_auto_detect: bool = True) -> List[ParsedMessage]:
        """
        Parses WhatsApp export text into ordered ParsedMessage objects.
        Multiline lines are appended to preceding message.
        """
        self.warnings = []
        if not text_content or not text_content.strip():
            return []

        if run_auto_detect:
            self.inspect_chat(text_content)

        text_content = text_content.lstrip("\ufeff")
        lines = text_content.splitlines()

        messages: List[ParsedMessage] = []
        current_msg: Optional[ParsedMessage] = None
        msg_counter = 0

        for line_num, line in enumerate(lines, 1):
            trimmed_line = line.strip("\r")
            if not trimmed_line.strip() and current_msg is None:
                continue

            match_android = self.PATTERN_ANDROID.match(trimmed_line)
            match_ios = self.PATTERN_IOS.match(trimmed_line)
            match_colon = self.PATTERN_COLON.match(trimmed_line)

            match = match_android or match_ios or match_colon

            if match:
                if current_msg:
                    messages.append(current_msg)

                msg_counter += 1
                date_str = match.group(1)
                time_str = match.group(2)
                payload = match.group(3)

                raw_ts, dt = self._parse_timestamp(date_str, time_str)
                sender, text, msg_type = self._extract_sender_and_text(payload)

                current_msg = ParsedMessage(
                    id=f"msg_{msg_counter}",
                    raw_timestamp=raw_ts,
                    sender=sender,
                    text=text,
                    message_type=msg_type,
                    timestamp=dt,
                    multiline=False,
                )
            else:
                if current_msg:
                    current_msg.text += f"\n{trimmed_line}"
                    current_msg.multiline = True
                else:
                    if trimmed_line.strip():
                        self.warnings.append(
                            f"Header line {line_num} could not be linked to a message: '{trimmed_line[:40]}...'"
                        )

        if current_msg:
            messages.append(current_msg)

        return messages
