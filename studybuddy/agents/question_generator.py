"""
QuestionGeneratorAgent
======================
Generates a single exam-quality question (plus correct answer) for a given
subtopic, subject, and difficulty level using Gemini 2.5 Flash.

Progressive disclosure
----------------------
Before calling the LLM, the agent loads a SKILL.md file from
``skills/<subject>/SKILL.md``.  This grounds the model in subject-specific
vocabulary and difficulty guidance *only when that subject is requested* —
nothing is pre-loaded at import time.

Usage
-----
    from agents.question_generator import QuestionGeneratorAgent

    agent = QuestionGeneratorAgent()
    result = agent.generate(
        subject="operating_systems",
        subtopic="Process Scheduling",
        difficulty="medium",
    )
    # result → {"question": "...", "answer": "...", "difficulty": "medium",
    #            "subtopic": "...", "subject": "..."}

Output schema
-------------
{
  "subject":    str,
  "subtopic":   str,
  "difficulty": "easy" | "medium" | "hard",
  "question":   str,
  "answer":     str
}
"""

from __future__ import annotations

import json
import os
import re
import textwrap
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

# ── Constants ──────────────────────────────────────────────────────────────────

MODEL_NAME = "gemini-2.5-flash"
DIFFICULTY_LEVELS = ("easy", "medium", "hard")

# Base directory of the project (two levels up from this file: agents/ → root)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_SKILLS_DIR   = _PROJECT_ROOT / "skills"

SYSTEM_PROMPT = textwrap.dedent("""\
    You are an expert academic question writer and examiner.
    Your task is to generate exactly ONE high-quality exam question
    with its correct answer for a given subtopic and difficulty level.

    You will be provided with:
    1. A SUBJECT CONTEXT section containing vocabulary and difficulty guidance.
    2. The target subtopic, subject, and difficulty.

    Rules:
    - Return ONLY valid JSON — no markdown fences, no commentary.
    - Match this exact schema:
      {
        "subject":    "<string>",
        "subtopic":   "<string>",
        "difficulty": "<easy|medium|hard>",
        "question":   "<string>",
        "answer":     "<string>"
      }
    - "question" must be a complete, standalone question string.
    - "answer"   must be a concise but complete correct answer.
    - Difficulty guide:
        easy   → recall / definition questions
        medium → application / calculation / comparison questions
        hard   → analysis / multi-step / edge-case questions
    - Do not add any fields beyond those listed above.
""")

USER_PROMPT_TEMPLATE = textwrap.dedent("""\
    ## SUBJECT CONTEXT
    {skill_context}

    ---

    ## REQUEST
    Subject:    {subject}
    Subtopic:   {subtopic}
    Difficulty: {difficulty}

    Generate one question and its correct answer following the JSON schema.
""")


# ── Agent ──────────────────────────────────────────────────────────────────────


class QuestionGeneratorAgent:
    """
    Generates a single exam question grounded by a subject SKILL.md file.

    Parameters
    ----------
    api_key:
        Google Gemini API key. Falls back to ``GOOGLE_API_KEY`` env var.
    """

    def __init__(self, api_key: str | None = None) -> None:
        load_dotenv()
        resolved_key = api_key or os.getenv("GOOGLE_API_KEY")

        if not resolved_key or resolved_key == "your_google_api_key_here":
            raise EnvironmentError(
                "GOOGLE_API_KEY is not set.\n"
                "Edit your .env and add a key from "
                "https://aistudio.google.com/app/apikey"
            )

        self._client = genai.Client(api_key=resolved_key)
        self._config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
        )

    # ── Progressive disclosure: load SKILL.md only when needed ───────────────

    def _load_skill_context(self, subject: str) -> str:
        """
        Read ``skills/<subject>/SKILL.md`` and return its content.

        Falls back gracefully with a warning if the file doesn't exist,
        so the agent still works — just without extra context.
        """
        skill_path = _SKILLS_DIR / subject / "SKILL.md"
        if skill_path.exists():
            return skill_path.read_text(encoding="utf-8")

        # Soft fallback — warn but don't crash
        print(
            f"[QuestionGeneratorAgent] WARNING: No SKILL.md found at "
            f"'{skill_path}'. Proceeding without subject context.\n"
            f"  Create 'skills/{subject}/SKILL.md' to enable progressive disclosure."
        )
        return f"No specific context available for subject: {subject}"

    # ── Public API ─────────────────────────────────────────────────────────────

    def generate(
        self,
        subject: str,
        subtopic: str,
        difficulty: str = "medium",
    ) -> dict:
        """
        Generate one question + answer for the given subtopic.

        Parameters
        ----------
        subject:    Subject folder name under ``skills/`` (e.g. ``"operating_systems"``).
        subtopic:   Specific concept to question (e.g. ``"Process Scheduling"``).
        difficulty: One of ``"easy"``, ``"medium"``, or ``"hard"``.

        Returns
        -------
        Dict matching the output schema described in the module docstring.

        Raises
        ------
        ValueError  – for invalid difficulty or malformed LLM output.
        """
        difficulty = difficulty.lower().strip()
        if difficulty not in DIFFICULTY_LEVELS:
            raise ValueError(
                f"Invalid difficulty '{difficulty}'. "
                f"Must be one of: {DIFFICULTY_LEVELS}"
            )

        # ── Progressive disclosure: load subject context ───────────────────────
        skill_context = self._load_skill_context(subject)

        # ── Build prompt ───────────────────────────────────────────────────────
        prompt = USER_PROMPT_TEMPLATE.format(
            skill_context=skill_context,
            subject=subject.replace("_", " ").title(),
            subtopic=subtopic,
            difficulty=difficulty,
        )

        # ── Call Gemini ────────────────────────────────────────────────────────
        response = self._client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=self._config,
        )
        raw = response.text.strip()

        # Strip accidental markdown fences
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        try:
            result = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Gemini returned non-JSON output:\n{raw}"
            ) from exc

        self._validate(result)
        return result

    # ── Validation ─────────────────────────────────────────────────────────────

    @staticmethod
    def _validate(result: dict) -> None:
        required = {"subject", "subtopic", "difficulty", "question", "answer"}
        missing = required - set(result)
        if missing:
            raise ValueError(
                f"Response is missing required keys: {missing}\nGot: {result}"
            )
        if result.get("difficulty") not in DIFFICULTY_LEVELS:
            raise ValueError(
                f"Unexpected difficulty value: '{result.get('difficulty')}'"
            )


# ── Quick test ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

    try:
        from rich.console import Console
        from rich.json import JSON
        from rich.panel import Panel
        from rich.table import Table

        console = Console()
        console.print("\n[bold cyan]Study Buddy -- Question Generator Agent[/bold cyan]\n")

        agent = QuestionGeneratorAgent()

        test_cases = [
            {"subject": "operating_systems", "subtopic": "Process Scheduling", "difficulty": "easy"},
            {"subject": "operating_systems", "subtopic": "Process Scheduling", "difficulty": "medium"},
            {"subject": "operating_systems", "subtopic": "Process Scheduling", "difficulty": "hard"},
        ]

        for tc in test_cases:
            diff_colour = {"easy": "green", "medium": "yellow", "hard": "red"}[tc["difficulty"]]
            console.print(
                f"[bold]Subject:[/bold] {tc['subject']}  "
                f"[bold]Subtopic:[/bold] {tc['subtopic']}  "
                f"[bold]Difficulty:[/bold] [{diff_colour}]{tc['difficulty'].upper()}[/{diff_colour}]"
            )

            result = agent.generate(**tc)

            # Pretty question/answer table
            table = Table(show_header=False, box=None, padding=(0, 2))
            table.add_column("Field",  style="bold cyan",  no_wrap=True)
            table.add_column("Value",  style="white")
            table.add_row("Q", result["question"])
            table.add_row("A", result["answer"])

            console.print(
                Panel(table, border_style=diff_colour, expand=False)
            )
            console.print()

        console.print("[bold green]All tests passed.[/bold green]\n")

    except EnvironmentError as e:
        print(f"\nConfiguration error:\n  {e}\n", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"\nValidation error:\n  {e}\n", file=sys.stderr)
        sys.exit(1)
    except Exception as e:  # noqa: BLE001
        print(f"\nUnexpected error:\n  {e}\n", file=sys.stderr)
        sys.exit(1)
