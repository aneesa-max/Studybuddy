"""
skills package
==============
Reusable, composable capabilities shared across agents.

Available skills
----------------
- search      – web / document retrieval
- summarise   – text condensation
- quiz_gen    – MCQ / flashcard generation
- flashcards  – spaced-repetition helpers
"""

from skills.search import search_skill
from skills.summarise import summarise_skill
from skills.quiz_gen import quiz_gen_skill
from skills.flashcards import flashcard_skill

__all__ = [
    "search_skill",
    "summarise_skill",
    "quiz_gen_skill",
    "flashcard_skill",
]
