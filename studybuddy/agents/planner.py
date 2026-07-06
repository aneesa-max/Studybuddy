"""
PlannerAgent
============
AI-powered study planner that generates a structured JSON learning plan
for any topic using Google Gemini (gemini-2.5-flash).

Usage
-----
    from agents.planner import PlannerAgent

    planner = PlannerAgent()
    plan = planner.create_plan(topic="Photosynthesis", subject="Biology")
    print(plan)

Output schema
-------------
{
  "topic": str,
  "subject": str,
  "subtopics": [
    {
      "order": int,          # 1-indexed position in the learning path
      "name": str,           # Subtopic title
      "estimated_minutes": int  # Suggested study time
    },
    ...  # always 3 items
  ]
}
"""

from __future__ import annotations

import json
import os
import re
import textwrap

from google import genai
from google.genai import types
from dotenv import load_dotenv

# ── Constants ──────────────────────────────────────────────────────────────────

MODEL_NAME = "gemini-2.5-flash"

SYSTEM_PROMPT = textwrap.dedent("""\
    You are an expert academic curriculum designer.
    When given a topic and subject, you produce a concise, structured
    learning plan broken into exactly 3 subtopics.

    Rules:
    - Return ONLY valid JSON — no markdown fences, no extra commentary.
    - The JSON must match this exact schema:
      {
        "topic": "<string>",
        "subject": "<string>",
        "subtopics": [
          {
            "order": <int>,
            "name": "<string>",
            "estimated_minutes": <int>
          }
        ]
      }
    - "subtopics" must contain exactly 3 objects, ordered from foundational
      to advanced.
    - "estimated_minutes" should be a realistic integer (e.g. 10–60).
    - Do not add any fields beyond those listed above.
""")

USER_PROMPT_TEMPLATE = (
    'Create a 3-subtopic learning plan for the topic "{topic}" '
    'within the subject "{subject}".'
)

# ── Agent ──────────────────────────────────────────────────────────────────────


class PlannerAgent:
    """Generates a JSON learning plan using Gemini 1.5 Flash."""

    def __init__(self, api_key: str | None = None) -> None:
        """
        Parameters
        ----------
        api_key:
            Google Gemini API key. If *None*, the value is read from the
            ``GOOGLE_API_KEY`` environment variable (loaded from ``.env``).
        """
        load_dotenv()
        resolved_key = api_key or os.getenv("GOOGLE_API_KEY")

        if not resolved_key or resolved_key == "your_google_api_key_here":
            raise EnvironmentError(
                "GOOGLE_API_KEY is not set.\n"
                "Edit your .env file and add a valid key from "
                "https://aistudio.google.com/app/apikey"
            )

        self._client = genai.Client(api_key=resolved_key)
        self._config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
        )

    # ── Public API ─────────────────────────────────────────────────────────────

    def create_plan(self, topic: str, subject: str) -> dict:
        """
        Generate a 3-subtopic learning plan.

        Parameters
        ----------
        topic:   The specific concept to study (e.g. "Photosynthesis").
        subject: The broader academic subject (e.g. "Biology").

        Returns
        -------
        A dict matching the schema described in the module docstring.

        Raises
        ------
        ValueError  – if Gemini returns malformed or non-JSON output.
        """
        prompt = USER_PROMPT_TEMPLATE.format(topic=topic, subject=subject)
        response = self._client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=self._config,
        )
        raw = response.text.strip()

        # Strip accidental markdown code fences if the model adds them anyway
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        try:
            plan = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Gemini returned non-JSON output:\n{raw}"
            ) from exc

        self._validate(plan)
        return plan

    # ── Validation ─────────────────────────────────────────────────────────────

    @staticmethod
    def _validate(plan: dict) -> None:
        """Raise ValueError if *plan* does not match the expected schema."""
        required_top = {"topic", "subject", "subtopics"}
        if not required_top.issubset(plan):
            raise ValueError(
                f"Missing top-level keys. Expected {required_top}, "
                f"got {set(plan)}"
            )

        subtopics = plan["subtopics"]
        if not isinstance(subtopics, list) or len(subtopics) != 3:
            raise ValueError(
                f"'subtopics' must be a list of exactly 3 items, "
                f"got {len(subtopics) if isinstance(subtopics, list) else type(subtopics)}"
            )

        required_sub = {"order", "name", "estimated_minutes"}
        for i, st in enumerate(subtopics):
            if not required_sub.issubset(st):
                raise ValueError(
                    f"Subtopic {i} is missing keys. "
                    f"Expected {required_sub}, got {set(st)}"
                )


# ── Quick test ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    # Force UTF-8 output on Windows to avoid charmap codec errors
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    try:
        from rich.console import Console
        from rich.json import JSON
        from rich.panel import Panel

        console = Console()

        # ── Run the planner ────────────────────────────────────────────────────
        console.print("\n[bold cyan]Study Buddy -- Planner Agent[/bold cyan]\n")

        planner = PlannerAgent()                          # loads key from .env

        test_cases = [
            {"topic": "Newton's Laws of Motion", "subject": "Physics"},
            {"topic": "The French Revolution",   "subject": "History"},
        ]

        for tc in test_cases:
            console.print(
                f"[bold yellow]► Topic:[/bold yellow] {tc['topic']}  "
                f"[bold yellow]Subject:[/bold yellow] {tc['subject']}"
            )
            plan = planner.create_plan(**tc)
            console.print(
                Panel(
                    JSON(json.dumps(plan, indent=2)),
                    title="Learning Plan",
                    border_style="green",
                )
            )

        console.print("[bold green]✓ All tests passed.[/bold green]\n")

    except EnvironmentError as e:
        print(f"\n⚠  Configuration error:\n  {e}\n", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"\n⚠  Validation error:\n  {e}\n", file=sys.stderr)
        sys.exit(1)
    except Exception as e:  # noqa: BLE001
        print(f"\n⚠  Unexpected error:\n  {e}\n", file=sys.stderr)
        sys.exit(1)
