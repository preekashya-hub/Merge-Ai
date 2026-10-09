"""
Merge AI - Reminders & Calendar Integration Engine
Handles deadline proximity status calculation, in-app urgency alerts,
and RFC 5545 compliant iCalendar (.ics) export for individual and bulk tasks.
"""
from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class DeadlineInfo:
    status: str  # "Due Today", "Upcoming", "Overdue", "Undated"
    resolved_datetime: Optional[datetime]
    badge_color: str
    display_label: str
    countdown: str = ""
    delta_seconds: int = 999999999


@dataclass
class UserReminder:
    id: str
    target_id: str
    target_type: str  # 'task', 'deadline', 'meeting'
    title: str
    reminder_time: datetime
    offset_type: str  # 'at_time', '1_hour_before', '1_day_before', 'custom'
    is_triggered: bool = False
    snoozed_until: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "target_id": self.target_id,
            "target_type": self.target_type,
            "title": self.title,
            "reminder_time": self.reminder_time.isoformat(),
            "offset_type": self.offset_type,
            "is_triggered": self.is_triggered,
            "snoozed_until": self.snoozed_until.isoformat() if self.snoozed_until else None,
        }


class ReminderEngine:
    """Manages deadline proximity calculations and RFC 5545 .ics generation."""

    PRODID = "-//Merge AI//Personal Chat Briefing Assistant//EN"

    @classmethod
    def calculate_deadline_status(
        cls,
        deadline_text: Optional[str],
        reference_time: Optional[datetime] = None,
    ) -> DeadlineInfo:
        """
        Evaluates deadline proximity against reference_time (defaults to now).
        Returns status ('Due Today', 'Upcoming', 'Overdue', 'Undated').
        """
        now = reference_time or datetime.now()
        today = now.date()

        if not deadline_text or not deadline_text.strip():
            return DeadlineInfo(
                status="Undated",
                resolved_datetime=None,
                badge_color="#64748b",
                display_label="No Date",
            )

        clean = deadline_text.strip().lower()
        target_dt: Optional[datetime] = None

        # 1. Check ISO format YYYY-MM-DD
        iso_match = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})(?:[T\s](\d{1,2}):(\d{2}))?", clean)
        if iso_match:
            try:
                y, m, d = int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3))
                hr = int(iso_match.group(4)) if iso_match.group(4) else 17
                mn = int(iso_match.group(5)) if iso_match.group(5) else 0
                target_dt = datetime(y, m, d, hr, mn)
            except ValueError:
                pass

        # 2. Check "today" or time today
        if not target_dt and "today" in clean:
            time_match = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", clean)
            target_hour = 17
            target_minute = 0
            if time_match:
                try:
                    raw_hr = int(time_match.group(1))
                    raw_mn = int(time_match.group(2)) if time_match.group(2) else 0
                    meridiem = time_match.group(3)
                    if meridiem:
                        if meridiem == "pm" and raw_hr < 12:
                            raw_hr += 12
                        elif meridiem == "am" and raw_hr == 12:
                            raw_hr = 0
                    target_hour = raw_hr
                    target_minute = raw_mn
                except ValueError:
                    pass
            target_dt = datetime(today.year, today.month, today.day, target_hour, target_minute)

        # 3. Check "tomorrow"
        if not target_dt and "tomorrow" in clean:
            t_date = today + timedelta(days=1)
            target_hour = 14
            time_match = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", clean)
            if time_match:
                try:
                    raw_hr = int(time_match.group(1))
                    meridiem = time_match.group(3)
                    if meridiem and meridiem == "pm" and raw_hr < 12:
                        raw_hr += 12
                    target_hour = raw_hr
                except ValueError:
                    pass
            target_dt = datetime(t_date.year, t_date.month, t_date.day, target_hour, 0)

        # 4. Check specific days of week: "thursday", "friday", etc.
        weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        if not target_dt:
            for idx, w_name in enumerate(weekdays):
                if w_name in clean:
                    days_ahead = (idx - now.weekday()) % 7
                    if days_ahead == 0 and "next" in clean:
                        days_ahead = 7
                    target_date = today + timedelta(days=days_ahead if days_ahead > 0 else 7)
                    target_dt = datetime(target_date.year, target_date.month, target_date.day, 17, 0)
                    break

        # Calculate status based on target_dt
        if target_dt:
            delta_secs = int((target_dt - now).total_seconds())
            if target_dt < now and target_dt.date() < today:
                days_past = max(1, (today - target_dt.date()).days)
                return DeadlineInfo(
                    status="Overdue",
                    resolved_datetime=target_dt,
                    badge_color="#ef4444",
                    display_label=f"Overdue ({target_dt.strftime('%b %d')})",
                    countdown=f"Overdue by {days_past}d",
                    delta_seconds=delta_secs,
                )
            elif target_dt.date() == today:
                return DeadlineInfo(
                    status="Due Today",
                    resolved_datetime=target_dt,
                    badge_color="#f59e0b",
                    display_label=f"Due Today ({target_dt.strftime('%I:%M %p')})",
                    countdown=f"Due today at {target_dt.strftime('%I:%M %p')}",
                    delta_seconds=delta_secs,
                )
            else:
                days_left = max(1, (target_dt.date() - today).days)
                c_str = f"Due tomorrow ({target_dt.strftime('%I:%M %p')})" if days_left == 1 else f"Due in {days_left} days"
                return DeadlineInfo(
                    status="Upcoming",
                    resolved_datetime=target_dt,
                    badge_color="#10b981",
                    display_label=f"Upcoming ({target_dt.strftime('%b %d')})",
                    countdown=c_str,
                    delta_seconds=delta_secs,
                )

        return DeadlineInfo(
            status="Undated",
            resolved_datetime=None,
            badge_color="#818cf8",
            display_label=deadline_text[:16],
            countdown="Undated",
            delta_seconds=999999999,
        )

    @classmethod
    def escape_ics_text(cls, text: str) -> str:
        """Escapes special characters per RFC 5545 specifications."""
        if not text:
            return ""
        return (
            text.replace("\\", "\\\\")
            .replace(";", "\\;")
            .replace(",", "\\,")
            .replace("\n", "\\n")
            .replace("\r", "")
        )

    @classmethod
    def generate_task_ics(
        cls,
        task_id: str,
        title: str,
        description: str,
        deadline_text: Optional[str] = None,
        assignee: Optional[str] = None,
        priority: str = "Medium",
        evidence: Optional[str] = None,
        reference_time: Optional[datetime] = None,
    ) -> str:
        """
        Creates an RFC 5545 single-event .ics calendar string.
        """
        return cls.generate_bulk_ics(
            tasks=[{
                "id": task_id,
                "task": title,
                "description": description,
                "deadline": deadline_text,
                "assignee": assignee,
                "priority": priority,
                "evidence": evidence,
            }],
            calendar_name=f"Merge AI - {title[:20]}",
            reference_time=reference_time,
        )

    @classmethod
    def generate_bulk_ics(
        cls,
        tasks: List[Dict[str, Any]],
        calendar_name: str = "Merge AI Action Items",
        reference_time: Optional[datetime] = None,
    ) -> str:
        """
        Generates a complete RFC 5545 .ics calendar containing all tasks.
        Compatible with Google Calendar, Outlook, and Apple Calendar.
        """
        now = reference_time or datetime.now()
        dtstamp = now.strftime("%Y%m%dT%H%M%SZ")

        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            f"PRODID:{cls.PRODID}",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
            f"X-WR-CALNAME:{cls.escape_ics_text(calendar_name)}",
            "X-WR-TIMEZONE:UTC",
        ]

        for idx, t in enumerate(tasks, 1):
            t_id = t.get("id", f"task_{idx}")
            title = t.get("task", "Action Item")
            deadline_str = t.get("deadline")
            assignee = t.get("assignee") or "Unassigned"
            priority = str(t.get("priority", "Medium")).upper()
            evidence = t.get("evidence", "")

            # Calculate event timing
            d_info = cls.calculate_deadline_status(deadline_str, reference_time=now)
            event_dt = d_info.resolved_datetime or (now + timedelta(days=idx, hours=10))
            event_end = event_dt + timedelta(hours=1)

            dtstart = event_dt.strftime("%Y%m%dT%H%M%S")
            dtend = event_end.strftime("%Y%m%dT%H%M%S")

            # Map priority to RFC 5545 priority integer (1=High, 5=Medium, 9=Low)
            ics_prio = 1 if priority == "HIGH" else 5 if priority == "MEDIUM" else 9

            event_desc = (
                f"Task: {title}\\n"
                f"Assignee: {assignee}\\n"
                f"Priority: {priority}\\n"
                f"Deadline: {deadline_str or 'None'}\\n"
                f"Source Citation: {evidence or 'Extracted via Merge AI'}"
            )

            uid = f"{t_id}-{uuid.uuid4().hex[:8]}@merge.ai"

            lines.extend([
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTAMP:{dtstamp}",
                f"DTSTART:{dtstart}",
                f"DTEND:{dtend}",
                f"SUMMARY:[Merge AI] {cls.escape_ics_text(title)}",
                f"DESCRIPTION:{event_desc}",
                f"PRIORITY:{ics_prio}",
                "STATUS:CONFIRMED",
                "TRANSP:OPAQUE",
                "BEGIN:VALARM",
                "ACTION:DISPLAY",
                f"DESCRIPTION:Reminder: {cls.escape_ics_text(title)}",
                "TRIGGER:-PT30M",
                "END:VALARM",
                "END:VEVENT",
            ])

        lines.append("END:VCALENDAR")
        # Ensure standard CRLF line endings as per RFC 5545
        return "\r\n".join(lines) + "\r\n"

    @classmethod
    def get_urgent_deadline_alerts(
        cls,
        tasks: List[Any],
        reference_time: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Filters tasks for active urgency alerts (Due Today or Overdue).
        """
        alerts = []
        for t in tasks:
            task_dict = t.to_dict() if hasattr(t, "to_dict") else t
            if task_dict.get("completed"):
                continue
            deadline = task_dict.get("deadline")
            info = cls.calculate_deadline_status(deadline, reference_time=reference_time)
            if info.status in ["Due Today", "Overdue"]:
                alerts.append({
                    "id": task_dict.get("id"),
                    "task": task_dict.get("task"),
                    "assignee": task_dict.get("assignee"),
                    "deadline": deadline,
                    "status": info.status,
                    "label": info.display_label,
                    "color": info.badge_color,
                })
        return alerts
