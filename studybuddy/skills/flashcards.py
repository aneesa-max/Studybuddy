"""
flashcard_skill
===============
Creates spaced-repetition flashcards from study material.
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Flashcard:
    front: str   # Question / term
    back: str    # Answer / definition
    tags: list[str] = None  # e.g. ["biology", "chapter-3"]

    def __post_init__(self) -> None:
        if self.tags is None:
            self.tags = []


def flashcard_skill(text: str, *, num_cards: int = 5) -> list[Flashcard]:
    """
    Extract *num_cards* flashcards from *text*.

    Returns
    -------
    List of Flashcard dataclass instances.

    TODO: Replace the stub below with a Gemini structured-output call.
    """
    # ── Stub implementation ───────────────────────────────────────────────────
    return [
        Flashcard(
            front=f"[stub] Term {i + 1} from the provided material",
            back="Replace this stub with real Gemini flashcard extraction.",
            tags=["stub"],
        )
        for i in range(num_cards)
    ]
