"""
agents package
==============
All agent definitions live here.

Available agents
----------------
- OrchestratorAgent  – routes user queries to specialist agents
- TutorAgent         – explains concepts and answers questions
- QuizAgent          – generates quizzes and evaluates answers
- SummaryAgent       – summarises study material
"""

from agents.orchestrator import OrchestratorAgent
from agents.tutor import TutorAgent
from agents.quiz import QuizAgent
from agents.summary import SummaryAgent

__all__ = [
    "OrchestratorAgent",
    "TutorAgent",
    "QuizAgent",
    "SummaryAgent",
]
