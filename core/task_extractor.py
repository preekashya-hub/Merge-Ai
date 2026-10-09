"""
Task and Action Item Extractor
Extracts action items, assignees, deadlines, and verifies source citations
against the parsed WhatsApp conversation transcript.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from .ollama_client import OllamaClient
from .priority_engine import PriorityEngine
from .whatsapp_parser import ParsedMessage

logger = logging.getLogger(__name__)


@dataclass
class ExtractedTask:
    id: str
    task: str
    assignee: Optional[str]
    deadline: Optional[str]
    priority: str  # "High", "Medium", "Low"
    priority_score: int
    priority_reasons: List[str]
    source_message_ids: List[str]
    evidence: str
    completed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "task": self.task,
            "assignee": self.assignee,
            "deadline": self.deadline,
            "priority": self.priority,
            "priority_score": self.priority_score,
            "priority_reasons": self.priority_reasons,
            "source_message_ids": self.source_message_ids,
            "evidence": self.evidence,
            "completed": self.completed,
        }


class TaskExtractor:
    """Extracts deliverables and validates source message provenance."""

    def __init__(self, ollama_client: OllamaClient, priority_engine: PriorityEngine):
        self.client = ollama_client
        self.priority_engine = priority_engine

    def extract_tasks(
        self,
        messages: List[ParsedMessage],
        existing_tasks: Optional[List[ExtractedTask]] = None,
    ) -> List[ExtractedTask]:
        """
        Extracts tasks from message stream, validates message IDs, and scores priority.
        """
        valid_ids: Set[str] = {m.id for m in messages}
        msg_map: Dict[str, ParsedMessage] = {m.id: m for m in messages}

        # Format messages for extraction
        formatted_messages = "\n".join(
            [f"[{m.id}] {m.sender}: {m.text}" for m in messages if m.message_type == "user"]
        )

        prompt = f"""You are Merge AI. Extract all explicit action items, commitments, assignments, and tasks from this WhatsApp conversation transcript.
Do not invent tasks or assignees. If no person is explicitly assigned, leave assignee as null.
If no deadline is mentioned, leave deadline as null.

Return ONLY a JSON array of objects matching this exact schema:
[
  {{
    "task": "Specific task description",
    "assignee": "Person responsible or null",
    "deadline": "Deadline text or null",
    "source_message_ids": ["msg_1", "msg_2"],
    "evidence": "Exact quote from message"
  }}
]

CONVERSATION TRANSCRIPT:
\"\"\"
{formatted_messages}
\"\"\"
"""
        json_data, error = self.client.generate_json(
            prompt=prompt,
            system_prompt="You are a meticulous task tracking auditor. Output only a JSON array of task objects.",
        )

        raw_tasks: List[Dict[str, Any]] = []
        if isinstance(json_data, list):
            raw_tasks = json_data
        elif isinstance(json_data, dict) and "action_items" in json_data:
            raw_tasks = json_data["action_items"]
        elif isinstance(json_data, dict) and "tasks" in json_data:
            raw_tasks = json_data["tasks"]
        else:
            # Deterministic fallback parser if local LLM is offline or output was invalid
            logger.info("Using deterministic fallback extraction due to: %s", error)
            raw_tasks = self._fallback_rule_extraction(messages)

        extracted_list: List[ExtractedTask] = []
        seen_tasks: Set[str] = set()

        for idx, item in enumerate(raw_tasks, 1):
            task_desc = str(item.get("task", "")).strip()
            if not task_desc or task_desc.lower() in seen_tasks:
                continue
            seen_tasks.add(task_desc.lower())

            assignee = item.get("assignee")
            if assignee and str(assignee).lower() in ["null", "none", "unknown", "n/a", ""]:
                assignee = None

            deadline = item.get("deadline")
            if deadline and str(deadline).lower() in ["null", "none", "unknown", "n/a", ""]:
                deadline = None

            evidence = str(item.get("evidence", "")).strip()

            # Validate source IDs against real parsed messages
            raw_ids = item.get("source_message_ids", [])
            if isinstance(raw_ids, str):
                raw_ids = [raw_ids]
            verified_ids = [str(sid).strip() for sid in raw_ids if str(sid).strip() in valid_ids]

            # If evidence mentions a message or we can locate matching text, map to id
            if not verified_ids and evidence:
                for m in messages:
                    if evidence.lower() in m.text.lower() or m.text.lower() in evidence.lower():
                        verified_ids.append(m.id)
                        break

            # Deterministic priority evaluation
            combined_eval_text = f"{task_desc} {deadline or ''} {evidence}"
            sender_candidate = assignee or ""
            p_item = self.priority_engine.evaluate_text(
                text=combined_eval_text,
                sender=sender_candidate,
                is_task=True,
            )

            # Preserve prior completed state if task matched
            completed = False
            if existing_tasks:
                for prev in existing_tasks:
                    if prev.task.lower() == task_desc.lower():
                        completed = prev.completed
                        break

            extracted_list.append(
                ExtractedTask(
                    id=f"task_{idx}",
                    task=task_desc,
                    assignee=assignee,
                    deadline=deadline,
                    priority=p_item.level,
                    priority_score=p_item.score,
                    priority_reasons=p_item.reasons,
                    source_message_ids=verified_ids,
                    evidence=evidence,
                    completed=completed,
                )
            )

        # Sort tasks by priority score descending
        extracted_list.sort(key=lambda t: t.priority_score, reverse=True)
        return extracted_list

    def _fallback_rule_extraction(self, messages: List[ParsedMessage]) -> List[Dict[str, Any]]:
        """
        Deterministic regex/rule-based extraction for offline operation or LLM errors.
        Ensures users get real action items even when Ollama is starting up or in demo mode.
        """
        extracted = []
        action_patterns = [
            (r"(?:i will|i'll)\s+([^.]+)", "I will commit"),
            (r"(?:must be signed|must be submitted|needs to be)\s+([^.]+)", "Required action"),
            (r"finalize\s+([^.]+)", "Finalize deliverable"),
            (r"prepare\s+([^.]+)", "Prepare deliverable"),
            (r"submit\s+([^.]+)", "Submit item"),
        ]

        for m in messages:
            if m.message_type != "user":
                continue
            text = m.text
            for pat, _ in action_patterns:
                import re
                match = re.search(pat, text, re.IGNORECASE)
                if match:
                    action_phrase = match.group(0).strip()
                    # Check deadline
                    deadline_val = None
                    if "by 5 pm today" in text.lower():
                        deadline_val = "5:00 PM today"
                    elif "by 4 pm today" in text.lower():
                        deadline_val = "4:00 PM today"
                    elif "tomorrow 2 pm" in text.lower():
                        deadline_val = "Tomorrow at 2:00 PM"
                    elif "thursday 5 pm" in text.lower():
                        deadline_val = "Thursday by 5:00 PM"
                    elif "by friday" in text.lower():
                        deadline_val = "Friday"

                    extracted.append({
                        "task": action_phrase.capitalize(),
                        "assignee": m.sender,
                        "deadline": deadline_val,
                        "source_message_ids": [m.id],
                        "evidence": m.text,
                    })
                    break

        return extracted
