"""
Tests for Ollama client mocking, JSON extraction, error handling, and task provenance.
"""
import unittest
from unittest.mock import MagicMock, patch
from core.ollama_client import OllamaClient
from core.priority_engine import PriorityEngine
from core.task_extractor import TaskExtractor
from core.whatsapp_parser import ParsedMessage


class TestOllamaClientAndExtraction(unittest.TestCase):
    def setUp(self):
        self.client = OllamaClient(base_url="http://localhost:11434", model="llama3.2:3b")

    def test_json_extraction_from_markdown_block(self):
        raw_llm_response = """
Here is the extracted information:
```json
{
  "summary": "Team kickoff meeting",
  "action_items": []
}
```
Hope this helps!
"""
        extracted = self.client._extract_json(raw_llm_response)
        self.assertIsNotNone(extracted)
        self.assertEqual(extracted.get("summary"), "Team kickoff meeting")

    def test_json_extraction_raw_braces(self):
        raw_text = 'Sure, {"task": "Review PR", "status": "pending"} has been detected.'
        extracted = self.client._extract_json(raw_text)
        self.assertIsNotNone(extracted)
        self.assertEqual(extracted.get("task"), "Review PR")

    def test_connection_failure_handling(self):
        # Client targeting an unallocated port
        offline_client = OllamaClient(base_url="http://localhost:59999", model="llama3.2:3b", timeout=1)
        alive, msg = offline_client.check_connection()
        self.assertFalse(alive)
        self.assertIn("Cannot reach Ollama", msg)

    def test_task_extractor_provenance_validation(self):
        messages = [
            ParsedMessage(id="msg_1", raw_timestamp="10/12/26, 09:17", sender="Alex", text="Hello"),
            ParsedMessage(
                id="msg_2",
                raw_timestamp="10/12/26, 09:36",
                sender="Rahul",
                text="I will finalize the backend API documentation by tomorrow 2 PM.",
            ),
        ]

        priority_engine = PriorityEngine(user_name="Rahul")
        mock_client = MagicMock(spec=OllamaClient)

        # Mock LLM returning valid JSON with real and hallucinated IDs
        mock_client.generate_json.return_value = (
            [
                {
                    "task": "Finalize backend API documentation",
                    "assignee": "Rahul",
                    "deadline": "Tomorrow 2 PM",
                    "source_message_ids": ["msg_2", "msg_999"],  # msg_999 is invalid
                    "evidence": "I will finalize the backend API documentation",
                }
            ],
            None,
        )

        extractor = TaskExtractor(mock_client, priority_engine)
        tasks = extractor.extract_tasks(messages)

        self.assertEqual(len(tasks), 1)
        task = tasks[0]
        self.assertEqual(task.task, "Finalize backend API documentation")
        # Ensure invalid msg_999 was filtered out
        self.assertEqual(task.source_message_ids, ["msg_2"])
        self.assertIn(task.priority, ["High", "Medium"])


if __name__ == "__main__":
    unittest.main()
