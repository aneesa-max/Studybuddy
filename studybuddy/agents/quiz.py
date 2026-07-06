"""
QuizAgent
=========
Generates multiple-choice questions and evaluates user answers
on any topic using the Gemini API (google.genai SDK).
"""

from __future__ import annotations

import os
from dotenv import load_dotenv
from google import genai
from google.genai import types


SYSTEM_PROMPT = """You are a quiz-master and assessment specialist.
When asked to create a quiz:
- Generate 3-5 clear multiple-choice questions
- Label choices (A) (B) (C) (D)
- Provide the correct answer and a brief explanation after each question
- Adjust difficulty based on the user's request
Keep the format clean and easy to read."""


class QuizAgent:
    """Generates quizzes and evaluates answers using Gemini."""

    def __init__(self, api_key: str | None = None, model: str = "gemini-2.5-flash") -> None:
        load_dotenv()
        resolved_key = api_key or os.getenv("GOOGLE_API_KEY")
        self._model_name = model
        self._client = genai.Client(api_key=resolved_key)
        self._config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
        )

    def handle(self, query: str) -> str:
        """Generate a quiz or evaluate an answer based on the query."""
        try:
            response = self._client.models.generate_content(
                model=self._model_name,
                contents=query,
                config=self._config,
            )
            return response.text
        except Exception as exc:  # noqa: BLE001
            return f"[QuizAgent error] {exc}"
