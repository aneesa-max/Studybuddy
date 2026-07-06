"""
SummaryAgent
============
Condenses long texts, lecture notes, or topics into concise,
structured summaries using the Gemini API (google.genai SDK).
"""

from __future__ import annotations

import os
from dotenv import load_dotenv
from google import genai
from google.genai import types


SYSTEM_PROMPT = """You are an expert at summarising and distilling information.
When asked to summarise:
- Extract the key ideas and main points
- Use bullet points for clarity
- Highlight critical terms in **bold**
- Keep the summary concise but complete
- Suggest 2-3 follow-up topics the student could explore next"""


class SummaryAgent:
    """Produces structured summaries of study material using Gemini."""

    def __init__(self, api_key: str | None = None, model: str = "gemini-2.5-flash") -> None:
        load_dotenv()
        resolved_key = api_key or os.getenv("GOOGLE_API_KEY")
        self._model_name = model
        self._client = genai.Client(api_key=resolved_key)
        self._config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
        )

    def handle(self, query: str) -> str:
        """Return a structured summary for the given content or topic."""
        try:
            response = self._client.models.generate_content(
                model=self._model_name,
                contents=query,
                config=self._config,
            )
            return response.text
        except Exception as exc:  # noqa: BLE001
            return f"[SummaryAgent error] {exc}"
