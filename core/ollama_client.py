"""
Ollama Local AI Client
Provides a clean, robust interface to interact with Ollama's local HTTP API (port 11434)
for CPU/local inference without any cloud dependencies.
"""
from __future__ import annotations

import json
import logging
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional, Tuple

from config import OLLAMA_BASE_URL, OLLAMA_MODEL, REQUEST_TIMEOUT

logger = logging.getLogger(__name__)

# Try importing requests; fall back to urllib if not installed yet
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class OllamaClient:
    """Client for local Ollama API."""

    def __init__(self, base_url: str = OLLAMA_BASE_URL, model: str = OLLAMA_MODEL, timeout: int = REQUEST_TIMEOUT):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def check_connection(self) -> Tuple[bool, str]:
        """
        Pings Ollama server root or /api/tags to confirm it is alive.
        Returns (is_connected, status_message).
        """
        url = f"{self.base_url}/api/tags"
        try:
            if REQUESTS_AVAILABLE:
                resp = requests.get(url, timeout=3)
                if resp.status_code == 200:
                    return True, "Ollama is running and responding."
                return False, f"Ollama returned HTTP status {resp.status_code}."
            else:
                req = urllib.request.Request(url, headers={"User-Agent": "CatchUpAI/1.0"})
                with urllib.request.urlopen(req, timeout=3) as resp:
                    if resp.status == 200:
                        return True, "Ollama is running and responding."
                    return False, f"Ollama returned HTTP status {resp.status}."
        except Exception as e:
            err_msg = str(e)
            if "Connection refused" in err_msg or "Failed to establish" in err_msg:
                return (
                    False,
                    "Cannot reach Ollama at localhost:11434. Please launch Ollama using 'ollama serve' or start the Ollama desktop app."
                )
            return False, f"Connection error: {err_msg}"

    def list_models(self) -> List[str]:
        """Returns list of downloaded model names from the local Ollama instance."""
        url = f"{self.base_url}/api/tags"
        try:
            if REQUESTS_AVAILABLE:
                resp = requests.get(url, timeout=self.timeout)
                if resp.status_code == 200:
                    data = resp.json()
                    return [m.get("name", "") for m in data.get("models", [])]
            else:
                req = urllib.request.Request(url, headers={"User-Agent": "CatchUpAI/1.0"})
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode("utf-8"))
                        return [m.get("name", "") for m in data.get("models", [])]
        except Exception as ex:
            logger.warning("Failed to list Ollama models: %s", ex)
        return []

    def is_model_available(self, target_model: Optional[str] = None) -> bool:
        """Checks if the configured model is installed locally."""
        model_name = target_model or self.model
        models = self.list_models()
        # Handle tags like 'llama3.2:3b' vs 'llama3.2:3b-latest' or matching prefix
        target_base = model_name.split(":")[0]
        for m in models:
            if m == model_name or m.startswith(target_base):
                return True
        return False

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        json_format: bool = False,
        temperature: float = 0.2,
    ) -> Dict[str, Any]:
        """
        Executes a prompt completion against the local Ollama instance.
        """
        url = f"{self.base_url}/api/generate"
        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_ctx": 4096,  # Sized for CPU / integrated GPU stability
            },
        }
        if system_prompt:
            payload["system"] = system_prompt
        if json_format:
            payload["format"] = "json"

        try:
            raw_body = json.dumps(payload).encode("utf-8")
            if REQUESTS_AVAILABLE:
                resp = requests.post(
                    url,
                    json=payload,
                    timeout=self.timeout,
                    headers={"Content-Type": "application/json"},
                )
                if resp.status_code == 404:
                    return {
                        "success": False,
                        "error": f"Model '{self.model}' not found in local Ollama. Please run: 'ollama run {self.model}'",
                    }
                resp.raise_for_status()
                result = resp.json()
            else:
                req = urllib.request.Request(
                    url,
                    data=raw_body,
                    headers={"Content-Type": "application/json", "User-Agent": "CatchUpAI/1.0"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    result = json.loads(resp.read().decode("utf-8"))

            response_text = result.get("response", "").strip()
            return {
                "success": True,
                "text": response_text,
                "total_duration_ms": round(result.get("total_duration", 0) / 1_000_000, 2),
            }

        except Exception as exc:
            err_str = str(exc)
            if "timed out" in err_str.lower():
                return {
                    "success": False,
                    "error": f"Request to Ollama timed out ({self.timeout}s). The model may still be loading into RAM.",
                }
            return {
                "success": False,
                "error": f"Ollama generation failed: {err_str}",
            }

    def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        retries: int = 1,
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Requests JSON response and safely extracts valid JSON even if model adds outer markdown backticks.
        """
        res = self.generate(prompt=prompt, system_prompt=system_prompt, json_format=True)
        if not res.get("success"):
            return None, res.get("error", "Unknown Ollama error")

        raw_text = res.get("text", "")
        parsed = self._extract_json(raw_text)

        if parsed is not None:
            return parsed, None

        # Controlled retry if JSON parsing fails on first attempt
        if retries > 0:
            retry_prompt = (
                f"{prompt}\n\nIMPORTANT: Return ONLY a valid RFC 8259 JSON object. "
                "Do not include explanation, greetings, or markdown fences."
            )
            retry_res = self.generate(prompt=retry_prompt, system_prompt=system_prompt, json_format=True)
            if retry_res.get("success"):
                parsed_retry = self._extract_json(retry_res.get("text", ""))
                if parsed_retry is not None:
                    return parsed_retry, None

        return None, f"Failed to parse JSON from local LLM response. Raw text was: {raw_text[:200]}"

    @staticmethod
    def _extract_json(raw: str) -> Optional[Dict[str, Any]]:
        """Extracts JSON object from text, handling markdown fences or leading/trailing commentary."""
        text = raw.strip()
        # Strip markdown ```json ... ```
        if "```json" in text:
            parts = text.split("```json")
            if len(parts) > 1:
                text = parts[1].split("```")[0].strip()
        elif "```" in text:
            parts = text.split("```")
            if len(parts) > 1:
                text = parts[1].strip()

        # Try direct parse
        try:
            obj = json.loads(text)
            if isinstance(obj, dict):
                return obj
        except Exception:
            pass

        # Try finding outermost { ... }
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            snippet = text[start : end + 1]
            try:
                obj = json.loads(snippet)
                if isinstance(obj, dict):
                    return obj
            except Exception:
                pass

        return None
