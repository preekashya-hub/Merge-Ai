"""
Tests for Reminders & Calendar (.ics) module: deadline proximity,
RFC 5545 iCalendar generation, alarms, and urgency alerts.
"""
import unittest
from datetime import datetime
from core.reminders import ReminderEngine, DeadlineInfo


class TestReminders(unittest.TestCase):
    def setUp(self):
        # Reference anchor: Monday, Oct 12, 2026 at 10:00 AM
        self.ref_time = datetime(2026, 10, 12, 10, 0, 0)

    def test_deadline_status_due_today(self):
        info = ReminderEngine.calculate_deadline_status("5:00 PM today", reference_time=self.ref_time)
        self.assertEqual(info.status, "Due Today")
        self.assertIsNotNone(info.resolved_datetime)
        self.assertEqual(info.resolved_datetime.hour, 17)
        self.assertIn("Due Today", info.display_label)

    def test_deadline_status_upcoming_tomorrow(self):
        info = ReminderEngine.calculate_deadline_status("Tomorrow at 2:00 PM", reference_time=self.ref_time)
        self.assertEqual(info.status, "Upcoming")
        self.assertIsNotNone(info.resolved_datetime)
        self.assertEqual(info.resolved_datetime.day, 13)

    def test_deadline_status_overdue(self):
        # Specific ISO date in the past
        info = ReminderEngine.calculate_deadline_status("2026-10-01", reference_time=self.ref_time)
        self.assertEqual(info.status, "Overdue")
        self.assertIn("Overdue", info.display_label)

    def test_deadline_status_undated(self):
        info = ReminderEngine.calculate_deadline_status(None, reference_time=self.ref_time)
        self.assertEqual(info.status, "Undated")

    def test_generate_ics_single_task(self):
        ics_content = ReminderEngine.generate_task_ics(
            task_id="task_1",
            title="Submit Security Form",
            description="Compliance review",
            deadline_text="5:00 PM today",
            assignee="Dev Sharma",
            priority="High",
            evidence="Alex said asap",
            reference_time=self.ref_time,
        )

        self.assertIn("BEGIN:VCALENDAR", ics_content)
        self.assertIn("END:VCALENDAR", ics_content)
        self.assertIn("BEGIN:VEVENT", ics_content)
        self.assertIn("SUMMARY:[Merge AI] Submit Security Form", ics_content)
        self.assertIn("PRIORITY:1", ics_content)  # High priority = 1
        self.assertIn("BEGIN:VALARM", ics_content)  # Reminder alarm
        self.assertIn("TRIGGER:-PT30M", ics_content)
        self.assertIn("\r\n", ics_content)  # RFC 5545 CRLF line endings

    def test_generate_bulk_ics(self):
        tasks = [
            {
                "id": "t1",
                "task": "Task Alpha",
                "deadline": "Today at 4 PM",
                "assignee": "Rahul",
                "priority": "High",
            },
            {
                "id": "t2",
                "task": "Task Beta",
                "deadline": "Tomorrow",
                "assignee": "Priya",
                "priority": "Medium",
            },
        ]
        bulk_ics = ReminderEngine.generate_bulk_ics(tasks, reference_time=self.ref_time)
        self.assertEqual(bulk_ics.count("BEGIN:VEVENT"), 2)
        self.assertEqual(bulk_ics.count("END:VEVENT"), 2)

    def test_get_urgent_deadline_alerts(self):
        tasks = [
            {"id": "t1", "task": "Urgent Due Today", "deadline": "5 PM today", "completed": False},
            {"id": "t2", "task": "Overdue Task", "deadline": "2026-10-01", "completed": False},
            {"id": "t3", "task": "Already Done", "deadline": "5 PM today", "completed": True},
            {"id": "t4", "task": "Far Future", "deadline": "2026-11-20", "completed": False},
        ]
        alerts = ReminderEngine.get_urgent_deadline_alerts(tasks, reference_time=self.ref_time)
        # Should include t1 and t2, but not completed t3 or future t4
        alert_ids = [a["id"] for a in alerts]
        self.assertIn("t1", alert_ids)
        self.assertIn("t2", alert_ids)
        self.assertNotIn("t3", alert_ids)
        self.assertNotIn("t4", alert_ids)


if __name__ == "__main__":
    unittest.main()
