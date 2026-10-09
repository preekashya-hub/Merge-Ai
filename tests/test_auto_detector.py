"""
Tests for Auto-Detector Engine: format detection, encodings, line endings,
date ordering inference, and confidence scoring.
"""
import unittest
from core.auto_detector import AutoDetector


class TestAutoDetector(unittest.TestCase):
    def setUp(self):
        self.detector = AutoDetector()

    def test_encoding_detection(self):
        bom_utf8 = b"\xef\xbb\xbf10/12/26, 09:17 - Alex: Hello"
        self.assertEqual(self.detector.detect_encoding(bom_utf8), "UTF-8-BOM")

        utf16_le = b"\xff\xfe1\x000\x00"
        self.assertEqual(self.detector.detect_encoding(utf16_le), "UTF-16-LE")

        standard_utf8 = b"10/12/26, 09:17 - Alex: Hello"
        self.assertEqual(self.detector.detect_encoding(standard_utf8), "UTF-8")

    def test_line_endings_detection(self):
        crlf_text = "Line 1\r\nLine 2\r\n"
        self.assertEqual(self.detector.detect_line_endings(crlf_text), "CRLF (Windows)")

        lf_text = "Line 1\nLine 2\n"
        self.assertEqual(self.detector.detect_line_endings(lf_text), "LF (Unix/Linux)")

    def test_android_schema_and_confidence(self):
        chat = (
            "10/12/26, 09:15 - Messages and calls are end-to-end encrypted.\n"
            "10/12/26, 09:17 - Alex Rivera: Morning team! Welcome to Project Apollo.\n"
            "10/12/26, 09:20 - Priya Patel: Morning Alex! Excited to get started.\n"
            "10/12/26, 09:50 - Maya Lin: <Media omitted>\n"
        )
        report = self.detector.inspect(chat)
        self.assertEqual(report.detected_schema, "Android Standard Format")
        self.assertIn("Hyphen", report.separator_type)
        self.assertEqual(report.confidence_level, "High")
        self.assertGreaterEqual(report.confidence_score, 0.8)
        self.assertEqual(report.system_message_count, 1)
        self.assertEqual(report.media_message_count, 1)
        self.assertIn("Alex Rivera", report.detected_senders)
        self.assertIn("Priya Patel", report.detected_senders)

    def test_ios_brackets_schema(self):
        chat = (
            "[10/12/26, 09:17:22] Alex Rivera: Hey everyone\n"
            "[10/12/26, 09:18:05] Maya Lin: Hello Alex\n"
        )
        report = self.detector.inspect(chat)
        self.assertEqual(report.detected_schema, "iOS Enclosed Format")
        self.assertIn("Brackets", report.separator_type)
        self.assertEqual(report.confidence_level, "High")

    def test_date_ordering_day_first(self):
        # 25/10/26 clearly indicates Day First since 25 > 12
        chat = (
            "25/10/26, 09:17 - Alex: First\n"
            "26/10/26, 09:20 - Priya: Second\n"
        )
        report = self.detector.inspect(chat)
        self.assertIn("DD/MM/YY", report.date_format_hint)

    def test_date_ordering_month_first(self):
        # 10/25/26 clearly indicates Month First since second part 25 > 12
        chat = (
            "10/25/26, 09:17 - Alex: First\n"
            "10/26/26, 09:20 - Priya: Second\n"
        )
        report = self.detector.inspect(chat)
        self.assertIn("MM/DD/YY", report.date_format_hint)

    def test_empty_input_handling(self):
        report = self.detector.inspect("")
        self.assertEqual(report.confidence_level, "Low")
        self.assertEqual(report.confidence_score, 0.0)


if __name__ == "__main__":
    unittest.main()
