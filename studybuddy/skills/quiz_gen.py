"""
quiz_gen_skill
==============
Generates multiple-choice questions (MCQs) from a block of text.
"""

from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class MCQuestion:
    question: str
    choices: list[str]          # e.g. ["A) ...", "B) ...", ...]
    answer: str                 # e.g. "A"
    explanation: str = ""


def quiz_gen_skill(text: str, *, num_questions: int = 3) -> list[MCQuestion]:
    """
    Generate *num_questions* MCQs from *text*.

    Returns
    -------
    List of MCQuestion dataclass instances.

    TODO: Replace the stub below with a Gemini structured-output call.
    """
    # ── Stub implementation ───────────────────────────────────────────────────
    return [
        MCQuestion(
            question=f"[stub] Question {i + 1} about the provided text?",
            choices=["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"],
            answer="A",
            explanation="Replace this stub with real Gemini quiz generation.",
        )
        for i in range(num_questions)
    ]
