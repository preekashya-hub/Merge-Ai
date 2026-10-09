"""
Chat Analyzer Orchestrator
Coordinates parsing, local chunked summarization, task extraction,
priority scoring, and evidence-grounded Q&A.
"""
from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional, Tuple

from config import OLLAMA_BASE_URL, OLLAMA_MODEL
from .ollama_client import OllamaClient
from .priority_engine import PriorityEngine
from .privacy import PrivacyAuditor
from .retrieval import ConversationRetriever, SearchResult
from .summarizer import ChatSummarizer
from .task_extractor import ExtractedTask, TaskExtractor
from .whatsapp_parser import ParsedMessage, WhatsAppParser

logger = logging.getLogger(__name__)


class ChatAnalyzer:
    """End-to-end analyzer for WhatsApp chat transcripts."""

    def __init__(
        self,
        base_url: str = OLLAMA_BASE_URL,
        model: str = OLLAMA_MODEL,
        user_name: Optional[str] = None,
    ):
        self.user_name = user_name
        self.client = OllamaClient(base_url=base_url, model=model)
        self.parser = WhatsAppParser(user_name=user_name)
        self.priority_engine = PriorityEngine(user_name=user_name)
        self.summarizer = ChatSummarizer(self.client)
        self.task_extractor = TaskExtractor(self.client, self.priority_engine)

    def parse_chat(self, raw_text: str, redact_phones: bool = False) -> List[ParsedMessage]:
        """Parses chat text and optionally redacts phone numbers."""
        messages = self.parser.parse(raw_text)
        if redact_phones:
            messages = PrivacyAuditor.sanitize_messages(messages, redact_phones=True)
        return messages

    def analyze_full_briefing(
        self,
        messages: List[ParsedMessage],
        existing_tasks: Optional[List[ExtractedTask]] = None,
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> Dict[str, Any]:
        """
        Runs the full briefing pipeline:
        1. Summarize conversation
        2. Extract action items & priorities
        3. Identify high-priority announcements and urgent notices
        """
        if not messages:
            return {
                "summary": {},
                "tasks": [],
                "warnings": ["No messages provided for analysis."],
            }

        # Step 1: Consolidated Briefing
        if progress_callback:
            progress_callback(0.05, "Beginning local chat summarization...")
        briefing = self.summarizer.generate_consolidated_briefing(
            messages, progress_callback=progress_callback
        )

        # Step 2: Task Extraction
        if progress_callback:
            progress_callback(0.75, "Extracting action items, deadlines, and responsibilities...")
        tasks = self.task_extractor.extract_tasks(messages, existing_tasks=existing_tasks)

        if progress_callback:
            progress_callback(1.0, "Analysis complete!")

        return {
            "briefing": briefing,
            "tasks": tasks,
            "warnings": self.parser.warnings,
        }

    def answer_question(
        self,
        question: str,
        messages: List[ParsedMessage],
        retriever: Optional[ConversationRetriever] = None,
    ) -> Dict[str, Any]:
        """
        Answers a user question grounded strictly in the conversation transcript:
        1. Local keyword/semantic retrieval for top candidate messages.
        2. Prompting Ollama with retrieved context only.
        3. Validating cited source message IDs.
        """
        if not messages:
            return {
                "answer": "No messages available to answer your question.",
                "sources": [],
            }

        if retriever is None:
            retriever = ConversationRetriever(messages)

        # Retrieve top 8 most relevant messages
        search_results = retriever.search(question, limit=8)

        if not search_results:
            return {
                "answer": "No matching messages or evidence were found in this conversation to answer that question.",
                "sources": [],
            }

        retrieved_messages = [r.message for r in search_results]
        valid_ids = {m.id: m for m in messages}

        # Format context for Ollama
        context_lines = []
        for m in retrieved_messages:
            context_lines.append(f"[{m.id}] {m.raw_timestamp} - {m.sender}: {m.text}")
        context_str = "\n".join(context_lines)

        prompt = f"""You are Merge AI. Answer the following question about a WhatsApp group chat using ONLY the provided conversation messages.

Rules:
1. Ground your answer strictly on the provided messages.
2. If the messages do not provide enough evidence, say clearly: "Based on the provided messages, this information could not be determined."
3. Do not assume or extrapolate facts not explicitly mentioned.
4. Cite supporting message IDs using square brackets like [msg_1].

QUESTION:
{question}

RETRIEVED CONVERSATION EVIDENCE:
\"\"\"
{context_str}
\"\"\"

Provide a clear, direct answer with citation IDs."""

        res = self.client.generate(prompt=prompt, temperature=0.1)
        if not res.get("success"):
            # Provide direct excerpt answer if LLM is offline
            answer_text = (
                f"Note: Local Ollama is unavailable ({res.get('error', 'connection refused')}). "
                f"Displaying top matching conversation messages directly."
            )
            return {
                "answer": answer_text,
                "sources": retrieved_messages[:4],
                "error": res.get("error"),
            }

        raw_answer = res.get("text", "").strip()

        # Extract cited IDs like [msg_4]
        import re
        cited_ids = re.findall(r"\[(msg_\d+)\]", raw_answer)
        valid_cited_messages = [valid_ids[cid] for cid in cited_ids if cid in valid_ids]

        # If model didn't cite properly or cited none, use top retrieved messages
        if not valid_cited_messages:
            valid_cited_messages = retrieved_messages[:3]

        return {
            "answer": raw_answer,
            "sources": valid_cited_messages,
        }
