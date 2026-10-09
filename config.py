"""
CatchUp AI - Configuration
Centralized configuration settings for local Ollama connection, chunking, and priorities.
"""
import os

# Ollama Connection Settings
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
REQUEST_TIMEOUT: int = int(os.getenv("OLLAMA_REQUEST_TIMEOUT", "90"))

# Processing & Chunking Parameters
DEFAULT_CHUNK_SIZE: int = int(os.getenv("CHAT_CHUNK_SIZE", "30"))
MAX_RETRIEVAL_RESULTS: int = int(os.getenv("MAX_RETRIEVAL_RESULTS", "12"))
MAX_UPLOAD_SIZE_MB: int = 15

# Application Branding
APP_NAME: str = "Merge AI"
APP_TAGLINE: str = "Less scrolling. More understanding."
APP_VERSION: str = "1.0.0"

# Priority Weightings & Thresholds
HIGH_PRIORITY_KEYWORDS: list[str] = [
    "urgent", "asap", "deadline", "critical", "important", "emergency", 
    "blocking", "blocked", "action required", "must be", "by today", "immediately"
]

MEDIUM_PRIORITY_KEYWORDS: list[str] = [
    "please", "needed", "tomorrow", "prepare", "submit", "review", 
    "schedule", "meeting", "check", "reminder", "update"
]
