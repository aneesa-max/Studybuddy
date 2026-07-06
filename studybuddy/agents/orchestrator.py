"""
OrchestratorAgent
=================
Top-level agent that receives user input, decides which specialist
agent to invoke, and returns the final response.

Routing logic (simple keyword dispatch — swap for an LLM router later):
  • "quiz" / "test me"  → QuizAgent
  • "summarise" / "tldr" → SummaryAgent
  • everything else      → TutorAgent
"""

from __future__ import annotations

from rich.console import Console
from rich.prompt import Prompt

from agents.tutor import TutorAgent
from agents.quiz import QuizAgent
from agents.summary import SummaryAgent

console = Console()

QUIZ_KEYWORDS = {"quiz", "test", "question", "mcq", "flashcard"}
SUMMARY_KEYWORDS = {"summarise", "summarize", "summary", "tldr", "tl;dr", "overview"}


class OrchestratorAgent:
    """Routes user queries to the appropriate specialist agent."""

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self._tutor = TutorAgent(api_key=api_key)
        self._quiz = QuizAgent(api_key=api_key)
        self._summary = SummaryAgent(api_key=api_key)

    # ── Routing ───────────────────────────────────────────────────────────────

    def _route(self, query: str) -> str:
        lower = query.lower()
        if any(kw in lower for kw in QUIZ_KEYWORDS):
            return "quiz"
        if any(kw in lower for kw in SUMMARY_KEYWORDS):
            return "summary"
        return "tutor"

    def handle(self, query: str) -> str:
        route = self._route(query)
        console.print(f"[dim]→ routing to [bold]{route}[/bold] agent[/dim]")

        if route == "quiz":
            return self._quiz.handle(query)
        if route == "summary":
            return self._summary.handle(query)
        return self._tutor.handle(query)

    # ── REPL loop ─────────────────────────────────────────────────────────────

    def run(self) -> None:
        """Start an interactive study session in the terminal."""
        console.print(
            "\n[bold cyan]Study Buddy[/bold cyan] — type [bold]exit[/bold] to quit.\n"
        )
        while True:
            try:
                query = Prompt.ask("[bold green]You[/bold green]").strip()
            except (KeyboardInterrupt, EOFError):
                break

            if query.lower() in {"exit", "quit", "q"}:
                console.print("[bold yellow]Goodbye! Keep studying! 📚[/bold yellow]")
                break

            if not query:
                continue

            response = self.handle(query)
            console.print(f"\n[bold blue]Buddy:[/bold blue] {response}\n")
