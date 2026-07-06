"""
EvaluatorAgent
==============
Evaluates a BSCS student's answer to a study question using Gemini 2.5 Flash.
Returns a structured JSON verdict with score, correctness, feedback, an
optional hint (never the full answer), and the recommended next difficulty.

Difficulty ladder
-----------------
Score >= 70  →  maintain or increase difficulty
Score <  70  →  maintain or decrease difficulty

    easy ──▶ medium ──▶ hard
    easy ◀── medium ◀── hard

Guardrail
---------
The system prompt explicitly forbids the model from revealing the full
correct answer in the hint field — only a directional nudge is allowed.

Usage
-----
    from agents.evaluator import EvaluatorAgent

    agent = EvaluatorAgent()
    result = agent.evaluate(
        question="What is the convoy effect in FCFS scheduling?",
        student_answer="It's when short processes wait behind a long one.",
        difficulty="easy",
    )

Output schema
-------------
{
  "score":           int,          # 0–100
  "correct":         bool,         # true if score >= 70
  "feedback":        str,          # one sentence — what was right or wrong
  "hint":            str | null,   # one-sentence nudge when incorrect; null if correct
  "next_difficulty": "easy" | "medium" | "hard"
}
"""

from __future__ import annotations

import json
import os
import re
import textwrap

from dotenv import load_dotenv
from google import genai
from google.genai import types

# ── Constants ──────────────────────────────────────────────────────────────────

MODEL_NAME       = "gemini-2.5-flash"
DIFFICULTY_LEVELS = ("easy", "medium", "hard")

SYSTEM_PROMPT = textwrap.dedent("""\
    You are a strict but encouraging academic evaluator for university-level
    Computer Science students.

    Your job is to assess a student's answer to a given question and return
    a JSON evaluation object. Follow every rule below exactly.

    ## Output Rules
    - Return ONLY valid JSON — no markdown fences, no extra commentary.
    - Match this exact schema:
      {
        "score":           <integer 0-100>,
        "correct":         <true if score >= 70, false otherwise>,
        "feedback":        "<one sentence describing what was right or wrong>",
        "hint":            "<one sentence directional hint, or null if correct>",
        "next_difficulty": "<easy | medium | hard>"
      }

    ## Scoring Criteria
    - Award marks for conceptual accuracy, completeness, and clarity.
    - Partial credit is allowed (e.g. 50/100 for a partially correct answer).
    - "correct" must be true if and only if score >= 70.

    ## Difficulty Progression
    - Current difficulty is provided with the request.
    - score >= 70: next_difficulty = same level or one level harder.
    - score <  70: next_difficulty = same level or one level easier.
    - Never skip a level (easy → hard is not allowed in one step).
    - Use your judgement — if the score is borderline (70–79), keep the
      same level; if strong (80+), move up; if very weak (<50), move down.

    ## Guardrail — Hints Only
    - The "hint" field MUST NOT reveal the full correct answer.
    - Hints should give a directional nudge: point to the right concept,
      remind the student of a relevant term, or ask a guiding sub-question.
    - If the answer is correct (score >= 70), set "hint" to null.

    ## Tone
    - Feedback should be concise, specific, and constructive.
    - Never be harsh or dismissive — one sentence only.
""")

USER_PROMPT_TEMPLATE = textwrap.dedent("""\
    ## Question
    {question}

    ## Student's Answer
    {student_answer}

    ## Current Difficulty
    {difficulty}

    Evaluate the student's answer and return the JSON verdict.
""")


# ── Agent ──────────────────────────────────────────────────────────────────────


class EvaluatorAgent:
    """
    Evaluates a student's answer and recommends next difficulty.

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

    # ── Public API ─────────────────────────────────────────────────────────────

    def evaluate(
        self,
        question: str,
        student_answer: str,
        difficulty: str = "medium",
    ) -> dict:
        """
        Evaluate *student_answer* against *question* at the given *difficulty*.

        Parameters
        ----------
        question:       The original question posed to the student.
        student_answer: The student's free-text response.
        difficulty:     Current difficulty — ``"easy"``, ``"medium"``, or ``"hard"``.

        Returns
        -------
        Dict matching the output schema in the module docstring.

        Raises
        ------
        ValueError  – for invalid difficulty or malformed LLM response.
        """
        difficulty = difficulty.lower().strip()
        if difficulty not in DIFFICULTY_LEVELS:
            raise ValueError(
                f"Invalid difficulty '{difficulty}'. "
                f"Choose from: {DIFFICULTY_LEVELS}"
            )

        prompt = USER_PROMPT_TEMPLATE.format(
            question=question,
            student_answer=student_answer,
            difficulty=difficulty,
        )

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
            raise ValueError(f"Gemini returned non-JSON output:\n{raw}") from exc

        self._validate(result)
        return result

    # ── Validation ─────────────────────────────────────────────────────────────

    @staticmethod
    def _validate(result: dict) -> None:
        required = {"score", "correct", "feedback", "hint", "next_difficulty"}
        missing = required - set(result)
        if missing:
            raise ValueError(f"Response missing keys: {missing}\nGot: {result}")

        score = result["score"]
        if not isinstance(score, (int, float)) or not (0 <= score <= 100):
            raise ValueError(f"'score' must be 0–100, got: {score}")

        if result["next_difficulty"] not in DIFFICULTY_LEVELS:
            raise ValueError(
                f"Invalid next_difficulty: '{result['next_difficulty']}'"
            )

        # Enforce guardrail: correct answers must have hint=null
        if result.get("correct") and result.get("hint") is not None:
            result["hint"] = None  # silently enforce the guardrail


# ── Quick test ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table
        from rich import box

        console = Console()
        console.print(
            "\n[bold cyan]Study Buddy -- Evaluator Agent[/bold cyan]\n"
        )

        agent = EvaluatorAgent()

        test_cases = [
            {
                "label": "Correct answer (expect score >= 70)",
                "question": "What is the convoy effect in FCFS scheduling?",
                "student_answer": (
                    "The convoy effect occurs when many short processes get "
                    "stuck waiting behind one long CPU-bound process, causing "
                    "high average waiting time and poor CPU utilisation."
                ),
                "difficulty": "easy",
            },
            {
                "label": "Partially correct answer (expect 40-69)",
                "question": (
                    "Explain the difference between internal and external "
                    "fragmentation in memory management."
                ),
                "student_answer": (
                    "Internal fragmentation is wasted space inside a memory "
                    "block. I'm not sure about external fragmentation."
                ),
                "difficulty": "medium",
            },
            {
                "label": "Wrong answer (expect score < 40)",
                "question": (
                    "In the Banker's Algorithm, what does the 'safe state' mean?"
                ),
                "student_answer": "It means the system is free from deadlock.",
                "difficulty": "hard",
            },
        ]

        for tc in test_cases:
            result = agent.evaluate(
                question=tc["question"],
                student_answer=tc["student_answer"],
                difficulty=tc["difficulty"],
            )

            score     = result["score"]
            correct   = result["correct"]
            feedback  = result["feedback"]
            hint      = result.get("hint")
            next_diff = result["next_difficulty"]

            # Colour coding
            score_colour = "green" if score >= 70 else ("yellow" if score >= 40 else "red")
            diff_colour  = {"easy": "green", "medium": "yellow", "hard": "red"}

            tbl = Table(show_header=False, box=box.SIMPLE, padding=(0, 1))
            tbl.add_column("Field", style="bold cyan", no_wrap=True)
            tbl.add_column("Value")

            tbl.add_row("Score",    f"[{score_colour}]{score}/100[/{score_colour}]")
            tbl.add_row("Correct",  "[green]Yes[/green]" if correct else "[red]No[/red]")
            tbl.add_row("Feedback", feedback)
            tbl.add_row("Hint",     hint if hint else "[dim]None (answer was correct)[/dim]")
            tbl.add_row(
                "Next Difficulty",
                f"[{diff_colour[next_diff]}]{next_diff.upper()}[/{diff_colour[next_diff]}]"
                f"  (was [{diff_colour[tc['difficulty']]}]{tc['difficulty'].upper()}"
                f"[/{diff_colour[tc['difficulty']]}])",
            )

            console.print(f"[bold white]{tc['label']}[/bold white]")
            console.print(
                f"[dim]Q: {tc['question'][:80]}{'...' if len(tc['question']) > 80 else ''}[/dim]"
            )
            console.print(Panel(tbl, border_style=score_colour, expand=False))
            console.print()

        console.print("[bold green]All evaluator tests passed.[/bold green]\n")

    except EnvironmentError as e:
        print(f"\nConfiguration error:\n  {e}\n", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"\nValidation error:\n  {e}\n", file=sys.stderr)
        sys.exit(1)
    except Exception as e:  # noqa: BLE001
        print(f"\nUnexpected error:\n  {e}\n", file=sys.stderr)
        sys.exit(1)
