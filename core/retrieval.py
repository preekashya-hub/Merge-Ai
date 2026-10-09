"""
Local Conversation Retrieval
Fast, dependency-free keyword & semantic relevance ranking for WhatsApp chat archives.
Retrieves targeted message snippets for Ollama Q&A without sending entire conversations.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Set

from .whatsapp_parser import ParsedMessage

STOPWORDS: Set[str] = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by",
    "can", "did", "do", "does", "doing", "don", "down", "during", "each", "few", "for", "from",
    "further", "had", "has", "have", "having", "he", "her", "here", "hers", "herself", "him",
    "himself", "his", "how", "i", "if", "in", "into", "is", "it", "its", "itself", "just", "me",
    "more", "most", "my", "myself", "no", "nor", "not", "now", "of", "off", "on", "once", "only",
    "or", "other", "our", "ours", "ourselves", "out", "over", "own", "s", "same", "she", "should",
    "so", "some", "such", "than", "that", "the", "their", "theirs", "them", "themselves", "then",
    "there", "these", "they", "this", "those", "through", "to", "too", "under", "until", "up",
    "very", "was", "we", "were", "what", "when", "where", "which", "while", "who", "whom", "why",
    "will", "with", "you", "your", "yours", "yourself", "yourselves"
}


@dataclass
class SearchResult:
    message: ParsedMessage
    relevance_score: float
    matched_terms: List[str]


class ConversationRetriever:
    """In-memory search index for parsed WhatsApp messages."""

    def __init__(self, messages: List[ParsedMessage]):
        self.messages = messages
        self.msg_dict: Dict[str, ParsedMessage] = {m.id: m for m in messages}
        self.doc_tokens: Dict[str, List[str]] = {}
        self.df: Dict[str, int] = {}  # Document frequency
        self._build_index()

    def _tokenize(self, text: str) -> List[str]:
        words = re.findall(r"\b[a-zA-Z0-9_\-\.\@]{2,}\b", text.lower())
        return [w for w in words if w not in STOPWORDS]

    def _build_index(self):
        """Constructs an inverted index count for TF-IDF style scoring."""
        for msg in self.messages:
            combined = f"{msg.sender} {msg.text}"
            tokens = self._tokenize(combined)
            self.doc_tokens[msg.id] = tokens
            unique_tokens = set(tokens)
            for t in unique_tokens:
                self.df[t] = self.df.get(t, 0) + 1

    def search(
        self,
        query: str,
        sender_filter: Optional[str] = None,
        limit: int = 10,
        min_score: float = 0.05,
    ) -> List[SearchResult]:
        """
        Executes a relevance-scored search over indexed messages.
        Supports exact phrase matching and keyword scoring.
        """
        if not query or not query.strip():
            return []

        clean_query = query.strip()
        query_tokens = self._tokenize(clean_query)
        exact_phrases = re.findall(r'"([^"]*)"', clean_query.lower())

        total_docs = max(len(self.messages), 1)
        results: List[SearchResult] = []

        for msg in self.messages:
            # Filter by sender if requested
            if sender_filter and sender_filter.lower() != "all":
                if msg.sender.lower() != sender_filter.lower():
                    continue

            # Skip pure media notifications in general query unless specifically asked
            if msg.message_type == "media" and "media" not in clean_query.lower():
                pass

            msg_tokens = self.doc_tokens.get(msg.id, [])
            if not msg_tokens and not exact_phrases:
                continue

            score = 0.0
            matched_terms: List[str] = []

            # 1. Exact phrase bonus
            lower_text = f"{msg.sender} {msg.text}".lower()
            for phrase in exact_phrases:
                if phrase and phrase in lower_text:
                    score += 25.0
                    matched_terms.append(f'"{phrase}"')

            # 2. Token TF-IDF style match
            for t in query_tokens:
                if t in msg_tokens:
                    tf = msg_tokens.count(t) / max(len(msg_tokens), 1)
                    doc_freq = self.df.get(t, 1)
                    idf = math.log((total_docs + 1) / (doc_freq + 0.5)) + 1.0
                    term_score = tf * idf * 10.0

                    # Boost sender name matches
                    if t in msg.sender.lower():
                        term_score *= 2.0

                    score += term_score
                    matched_terms.append(t)

            if score >= min_score or (not query_tokens and exact_phrases and score > 0):
                results.append(
                    SearchResult(
                        message=msg,
                        relevance_score=round(score, 2),
                        matched_terms=list(set(matched_terms)),
                    )
                )

        # Sort descending by relevance score
        results.sort(key=lambda r: r.relevance_score, reverse=True)
        return results[:limit]

    def get_message_by_id(self, msg_id: str) -> Optional[ParsedMessage]:
        return self.msg_dict.get(msg_id)

    def get_surrounding_context(self, msg_id: str, window: int = 1) -> List[ParsedMessage]:
        """Returns message along with preceding and succeeding messages for context."""
        idx = -1
        for i, m in enumerate(self.messages):
            if m.id == msg_id:
                idx = i
                break
        if idx == -1:
            return []

        start = max(0, idx - window)
        end = min(len(self.messages), idx + window + 1)
        return self.messages[start:end]
