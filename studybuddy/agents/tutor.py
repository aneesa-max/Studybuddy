"""
TutorAgent
==========
Explains concepts, answers study questions, and provides examples
using the Gemini API (google.genai SDK).
"""

from __future__ import annotations

import os
from dotenv import load_dotenv
from google import genai
from google.genai import types


SYSTEM_PROMPT = """You are an expert tutor and study assistant.
Your role is to:
- Explain concepts clearly and concisely
- Use real-world analogies when helpful
- Break complex ideas into digestible steps
- Encourage curiosity and deeper thinking
Keep answers focused and educational."""


class TutorAgent:
    """Answers conceptual questions using Gemini."""

    def __init__(self, api_key: str | None = None, model: str = "gemini-2.5-flash") -> None:
        load_dotenv()
        resolved_key = api_key or os.getenv("GOOGLE_API_KEY")
        self._model_name = model
        self._client = genai.Client(api_key=resolved_key)
        self._config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
        )

    def handle(self, query: str) -> str:
        """Return a tutoring response for the given query."""
        try:
            response = self._client.models.generate_content(
                model=self._model_name,
                contents=query,
                config=self._config,
            )
            return response.text
        except Exception as exc:  # noqa: BLE001
            return f"[TutorAgent error] {exc}"
