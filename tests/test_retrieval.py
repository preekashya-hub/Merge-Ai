"""
Tests for local conversation retrieval: keyword search, phrases, sender filtering, and context window.
"""
import unittest
from core.whatsapp_parser import ParsedMessage
from core.retrieval import ConversationRetriever


class TestConversationRetriever(unittest.TestCase):
    def setUp(self):
        self.messages = [
            ParsedMessage(
                id="msg_1",
                raw_timestamp="10/12/26, 09:17",
                sender="Alex Rivera",
                text="Welcome to the Project Apollo coordination group.",
            ),
            ParsedMessage(
                id="msg_2",
                raw_timestamp="10/12/26, 09:42",
                sender="Alex Rivera",
                text="DECISION: We have decided to use PostgreSQL instead of MongoDB.",
            ),
            ParsedMessage(
                id="msg_3",
                raw_timestamp="10/12/26, 10:15",
                sender="Alex Rivera",
                text="URGENT: The security compliance questionnaire must be signed by Dev before 5 PM today.",
            ),
            ParsedMessage(
                id="msg_4",
                raw_timestamp="10/12/26, 10:18",
                sender="Dev Sharma",
                text="On it! I will review the security checklist and submit by 4 PM today.",
            ),
        ]
        self.retriever = ConversationRetriever(self.messages)

    def test_keyword_search_relevance(self):
        results = self.retriever.search("PostgreSQL")
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0].message.id, "msg_2")

    def test_sender_filtering(self):
        results = self.retriever.search("security", sender_filter="Dev Sharma")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].message.sender, "Dev Sharma")

    def test_context_window(self):
        context = self.retriever.get_surrounding_context("msg_3", window=1)
        # Should include msg_2, msg_3, msg_4
        self.assertEqual(len(context), 3)
        self.assertEqual([m.id for m in context], ["msg_2", "msg_3", "msg_4"])

    def test_empty_query(self):
        results = self.retriever.search("")
        self.assertEqual(results, [])


if __name__ == "__main__":
    unittest.main()
