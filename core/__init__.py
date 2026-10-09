"""
Merge AI Core Package
Modular architecture for privacy-first chat briefing, auto-detection,
task extraction, and calendar reminders.
"""
from .whatsapp_parser import WhatsAppParser, ParsedMessage
from .auto_detector import AutoDetector, DetectionReport
from .ollama_client import OllamaClient
from .priority_engine import PriorityEngine, PriorityItem
from .reminders import ReminderEngine, DeadlineInfo, UserReminder
from .retrieval import ConversationRetriever
from .summarizer import ChatSummarizer
from .task_extractor import TaskExtractor
from .chat_analyzer import ChatAnalyzer
from .privacy import PrivacyAuditor

__all__ = [
    "WhatsAppParser",
    "ParsedMessage",
    "AutoDetector",
    "DetectionReport",
    "OllamaClient",
    "PriorityEngine",
    "PriorityItem",
    "ReminderEngine",
    "DeadlineInfo",
    "ConversationRetriever",
    "ChatSummarizer",
    "TaskExtractor",
    "ChatAnalyzer",
    "PrivacyAuditor",
]
