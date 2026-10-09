"""
Tests for WhatsApp parser: formats, multiline, system messages, media placeholders, and order.
"""
import unittest
from core.whatsapp_parser import WhatsAppParser


class TestWhatsAppParser(unittest.TestCase):
    def setUp(self):
        self.parser = WhatsAppParser()

    def test_standard_android_format(self):
        sample = (
            "10/12/26, 09:17 - Alex Rivera: Morning team! Welcome to Project Apollo.\n"
            "10/12/26, 09:20 - Priya Patel: Morning Alex! Excited to get started.\n"
        )
        messages = self.parser.parse(sample)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].id, "msg_1")
        self.assertEqual(messages[0].sender, "Alex Rivera")
        self.assertEqual(messages[0].text, "Morning team! Welcome to Project Apollo.")
        self.assertEqual(messages[0].message_type, "user")
        self.assertEqual(messages[1].id, "msg_2")
        self.assertEqual(messages[1].sender, "Priya Patel")

    def test_ios_bracketed_format(self):
        sample = (
            "[10/12/26, 09:17:22] Alex Rivera: Hey everyone\n"
            "[10/12/26, 09:18:05] Maya Lin: Hello Alex\n"
        )
        messages = self.parser.parse(sample)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].sender, "Alex Rivera")
        self.assertEqual(messages[0].text, "Hey everyone")
        self.assertEqual(messages[1].sender, "Maya Lin")

    def test_multiline_messages(self):
        sample = (
            "10/12/26, 09:28 - Maya Lin: Good morning!\n"
            "I have a few questions regarding the mobile navigation flow.\n"
            "Can we discuss this during our standup?\n"
            "10/12/26, 09:30 - Alex Rivera: Absolutely Maya.\n"
        )
        messages = self.parser.parse(sample)
        self.assertEqual(len(messages), 2)
        self.assertTrue(messages[0].multiline)
        self.assertIn("mobile navigation flow", messages[0].text)
        self.assertIn("Can we discuss this", messages[0].text)
        self.assertEqual(messages[1].sender, "Alex Rivera")

    def test_system_and_media_messages(self):
        sample = (
            "10/12/26, 09:15 - Messages and calls are end-to-end encrypted.\n"
            "10/12/26, 09:16 - Alex Rivera created group \"Project Apollo\"\n"
            "10/12/26, 09:50 - Maya Lin: <Media omitted>\n"
        )
        messages = self.parser.parse(sample)
        self.assertEqual(len(messages), 3)
        self.assertEqual(messages[0].message_type, "system")
        self.assertEqual(messages[1].message_type, "system")
        self.assertEqual(messages[2].message_type, "media")

    def test_order_preservation(self):
        sample = (
            "10/12/26, 09:01 - User A: First\n"
            "10/12/26, 09:02 - User B: Second\n"
            "10/12/26, 09:03 - User C: Third\n"
        )
        messages = self.parser.parse(sample)
        self.assertEqual([m.sender for m in messages], ["User A", "User B", "User C"])
        self.assertEqual([m.id for m in messages], ["msg_1", "msg_2", "msg_3"])

    def test_malformed_and_empty_lines(self):
        sample = (
            "Random leading unformatted junk line\n"
            "10/12/26, 09:01 - User A: Valid line\n"
            "\n"
            "10/12/26, 09:02 - User B: Another line\n"
        )
        messages = self.parser.parse(sample)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].sender, "User A")
        self.assertTrue(len(self.parser.warnings) > 0)


if __name__ == "__main__":
    unittest.main()
