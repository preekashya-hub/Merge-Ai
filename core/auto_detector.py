"""
Merge AI - Auto-Detector Engine
Automatically inspects raw chat exports before parsing to detect encoding,
line endings, locale date/time patterns, separators, media markers,
and calculates a parsing confidence score.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class DetectionReport:
    """Detailed inspection report produced by the Auto-Detector."""
    encoding: str = "UTF-8"
    line_ending: str = "LF (Unix)"
    detected_schema: str = "Android Standard (Hyphen)"
    date_format_hint: str = "DD/MM/YY"
    time_format_hint: str = "24-hour"
    separator_type: str = "Hyphen (' - ')"
    total_lines: int = 0
    header_lines: int = 0
    continuation_lines: int = 0
    system_message_count: int = 0
    media_message_count: int = 0
    detected_senders: List[str] = field(default_factory=list)
    confidence_score: float = 0.0  # 0.0 to 1.0
    confidence_level: str = "Low"  # "High", "Moderate", "Low"
    pattern_sample: str = ""
    diagnostics: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "encoding": self.encoding,
            "line_ending": self.line_ending,
            "detected_schema": self.detected_schema,
            "date_format_hint": self.date_format_hint,
            "time_format_hint": self.time_format_hint,
            "separator_type": self.separator_type,
            "total_lines": self.total_lines,
            "header_lines": self.header_lines,
            "continuation_lines": self.continuation_lines,
            "system_message_count": self.system_message_count,
            "media_message_count": self.media_message_count,
            "sender_count": len(self.detected_senders),
            "senders": self.detected_senders[:8],
            "confidence_score": round(self.confidence_score * 100, 1),
            "confidence_level": self.confidence_level,
            "pattern_sample": self.pattern_sample,
            "diagnostics": self.diagnostics,
        }


class AutoDetector:
    """Pre-parse intelligence engine that analyzes raw WhatsApp files."""

    SYSTEM_PATTERNS = [
        "messages and calls are end-to-end encrypted",
        "created group",
        "added",
        "removed",
        "left",
        "changed the subject",
        "changed the group",
        "changed this group's",
        "security code changed",
        "you were added",
        "pinned a message",
        "disappearing messages",
    ]

    MEDIA_PATTERNS = [
        "<media omitted>",
        "image omitted",
        "video omitted",
        "audio omitted",
        "sticker omitted",
        "document omitted",
        "gif omitted",
        "contact card omitted",
    ]

    # Pattern definitions for schema detection
    RE_ANDROID_HYPHEN = re.compile(
        r"^(\d{1,4}[/\.-]\d{1,2}[/\.-]\d{2,4}),?\s+(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AaPp][Mm])?)\s*[-–—]\s*(.*)$"
    )
    RE_IOS_BRACKETS = re.compile(
        r"^\[(\d{1,4}[/\.-]\d{1,2}[/\.-]\d{2,4}),?\s+(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AaPp][Mm])?)\]\s*(.*)$"
    )
    RE_COLON_SEP = re.compile(
        r"^(\d{1,4}[/\.-]\d{1,2}[/\.-]\d{2,4}),?\s+(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AaPp][Mm])?):\s*(.*)$"
    )

    @staticmethod
    def detect_encoding(raw_bytes: bytes) -> str:
        """Identifies text encoding from byte header."""
        if not raw_bytes:
            return "UTF-8"
        if raw_bytes.startswith(b"\xef\xbb\xbf"):
            return "UTF-8-BOM"
        if raw_bytes.startswith(b"\xff\xfe"):
            return "UTF-16-LE"
        if raw_bytes.startswith(b"\xfe\xff"):
            return "UTF-16-BE"

        # Try UTF-8 decode
        try:
            raw_bytes.decode("utf-8")
            return "UTF-8"
        except UnicodeDecodeError:
            pass

        # Try ISO-8859-1 (Latin-1)
        try:
            raw_bytes.decode("iso-8859-1")
            return "ISO-8859-1"
        except Exception:
            return "Unknown"

    @staticmethod
    def detect_line_endings(text: str) -> str:
        """Determines line ending format."""
        if "\r\n" in text:
            return "CRLF (Windows)"
        elif "\r" in text:
            return "CR (Classic Mac)"
        return "LF (Unix/Linux)"

    def inspect(self, raw_text: str, detected_encoding: str = "UTF-8") -> DetectionReport:
        """
        Runs comprehensive inspection across text lines to identify schema,
        delimiters, locale formats, and parsing viability.
        """
        report = DetectionReport()
        report.encoding = detected_encoding
        report.line_ending = self.detect_line_endings(raw_text)

        if not raw_text or not raw_text.strip():
            report.diagnostics.append("Empty or whitespace-only input provided.")
            return report

        lines = raw_text.splitlines()
        report.total_lines = len(lines)

        android_matches = 0
        ios_matches = 0
        colon_matches = 0

        date_samples: List[Tuple[str, str, str]] = []
        is_12hr = False
        is_24hr = False
        senders_found: set[str] = set()
        system_count = 0
        media_count = 0
        first_valid_sample = ""

        for line in lines:
            line_str = line.strip("\r")
            if not line_str.strip():
                continue

            match_a = self.RE_ANDROID_HYPHEN.match(line_str)
            match_i = self.RE_IOS_BRACKETS.match(line_str)
            match_c = self.RE_COLON_SEP.match(line_str)

            active_match = match_a or match_i or match_c

            if active_match:
                report.header_lines += 1
                if not first_valid_sample:
                    first_valid_sample = line_str

                if match_a:
                    android_matches += 1
                elif match_i:
                    ios_matches += 1
                elif match_c:
                    colon_matches += 1

                date_part = active_match.group(1)
                time_part = active_match.group(2)
                payload = active_match.group(3)

                # Time format detection (12h vs 24h)
                if re.search(r"[a-z]", time_part, re.IGNORECASE):
                    is_12hr = True
                else:
                    is_24hr = True

                # Date parts collection
                d_splits = re.split(r"[/\.-]", date_part)
                if len(d_splits) == 3:
                    date_samples.append((d_splits[0], d_splits[1], d_splits[2]))

                # Check system or user
                lower_payload = payload.lower()
                if any(p in lower_payload for p in self.SYSTEM_PATTERNS) or ":" not in payload:
                    system_count += 1
                else:
                    # Sender extraction
                    colon_pos = payload.find(":")
                    if colon_pos != -1:
                        sender = payload[:colon_pos].strip()
                        senders_found.add(sender)
                        msg_body = payload[colon_pos + 1 :].strip()
                        if any(m in msg_body.lower() for m in self.MEDIA_PATTERNS):
                            media_count += 1
            else:
                report.continuation_lines += 1

        report.pattern_sample = first_valid_sample
        report.system_message_count = system_count
        report.media_message_count = media_count
        report.detected_senders = sorted(list(senders_found))

        # Determine schema & separator
        if ios_matches > android_matches and ios_matches > colon_matches:
            report.detected_schema = "iOS Enclosed Format"
            report.separator_type = "Brackets ('[Timestamp] Sender:')"
        elif android_matches >= ios_matches and android_matches > 0:
            report.detected_schema = "Android Standard Format"
            report.separator_type = "Hyphen (' - Sender:')"
        elif colon_matches > 0:
            report.detected_schema = "Direct Colon Separator"
            report.separator_type = "Colon (': Sender:')"
        else:
            report.detected_schema = "Unrecognized / Custom Format"
            report.separator_type = "None detected"

        # Time format determination
        if is_12hr and is_24hr:
            report.time_format_hint = "Mixed (12-hour AM/PM and 24-hour)"
        elif is_12hr:
            report.time_format_hint = "12-hour (AM/PM)"
        elif is_24hr:
            report.time_format_hint = "24-hour (Standard)"
        else:
            report.time_format_hint = "Unknown"

        # Date format determination (DD/MM vs MM/DD)
        report.date_format_hint = self._infer_date_format(date_samples)

        # Confidence calculation
        if report.total_lines > 0 and report.header_lines > 0:
            # Ratio of recognized headers + continuations over total non-empty lines
            ratio = (report.header_lines + report.continuation_lines) / max(report.total_lines, 1)
            # Bonus for detecting senders
            sender_bonus = 0.15 if len(report.detected_senders) > 0 else 0.0
            score = min(0.85 * ratio + sender_bonus, 1.0)
            report.confidence_score = score

            if score >= 0.80:
                report.confidence_level = "High"
            elif score >= 0.50:
                report.confidence_level = "Moderate"
            else:
                report.confidence_level = "Low"
        else:
            report.confidence_score = 0.0
            report.confidence_level = "Low"
            report.diagnostics.append("Could not find standard WhatsApp timestamp headers in file.")

        # Diagnostics notes
        if report.system_message_count > 0:
            report.diagnostics.append(f"Identified {report.system_message_count} system notifications.")
        if report.media_message_count > 0:
            report.diagnostics.append(f"Identified {report.media_message_count} omitted media attachments.")
        if len(report.detected_senders) > 0:
            report.diagnostics.append(f"Found {len(report.detected_senders)} unique conversation participants.")

        return report

    def _infer_date_format(self, date_samples: List[Tuple[str, str, str]]) -> str:
        """Infers whether dates are DD/MM/YY, MM/DD/YY, or YYYY-MM-DD."""
        if not date_samples:
            return "DD/MM/YY (Default)"

        first = date_samples[0]
        # Check if 4-digit year is first: YYYY-MM-DD
        if len(first[0]) == 4:
            return "YYYY-MM-DD (ISO)"

        # Check values across samples to see if first or second component exceeds 12
        first_exceeds_12 = False
        second_exceeds_12 = False

        for part1, part2, _ in date_samples:
            try:
                v1 = int(part1)
                v2 = int(part2)
                if v1 > 12:
                    first_exceeds_12 = True
                if v2 > 12:
                    second_exceeds_12 = True
            except ValueError:
                continue

        if first_exceeds_12:
            return "DD/MM/YY (Day First)"
        if second_exceeds_12:
            return "MM/DD/YY (Month First)"

        # Default fallback
        return "DD/MM/YY (Auto-adapted)"
