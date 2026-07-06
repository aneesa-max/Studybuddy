"""
main.py — Study Buddy Orchestrator
===================================
Runs a complete interactive study session for BSCS students.

Session flow
------------
1. Prompt student for a CS topic + subject folder name.
2. PlannerAgent   → 3-subtopic learning plan.
3. For each subtopic:
   a. QuestionGeneratorAgent → question at current difficulty.
   b. Student types answer.
   c. EvaluatorAgent        → score, feedback, hint, next_difficulty.
   d. Difficulty updates for next round.
4. Final summary: avg score, topics, difficulty arc, motivational line.

Error handling
--------------
JSON parse errors from any agent are retried once before aborting.
"""

from __future__ import annotations

import os
import sys
import time

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from dotenv import load_dotenv
from google.genai import errors as genai_errors
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.rule import Rule
from rich.table import Table
from rich import box

from agents.planner           import PlannerAgent
from agents.question_generator import QuestionGeneratorAgent
from agents.evaluator         import EvaluatorAgent

# ── Bootstrap ──────────────────────────────────────────────────────────────────
load_dotenv()
console = Console()

DIFF_COLOUR = {"easy": "green", "medium": "yellow", "hard": "red"}
DIFF_ORDER  = ["easy", "medium", "hard"]

MOTIVATIONAL_LINES = [
    "Every expert was once a beginner — keep going!",
    "Understanding beats memorisation every single time.",
    "Consistency is the engine of mastery. See you next session!",
    "You just made your future self smarter. Well done!",
    "The best time to study was yesterday; the next best time is now.",
]


# ── Helpers ────────────────────────────────────────────────────────────────────

def _parse_retry_delay(exc: Exception, default: float = 65.0) -> float:
    """Extract 'retry in Xs' delay from a Gemini error message, or use default."""
    import re as _re
    match = _re.search(r"retry in\s+([\d.]+)s", str(exc), _re.IGNORECASE)
    return float(match.group(1)) + 2 if match else default


def _call_with_retry(fn, label: str, **kwargs) -> dict:
    """
    Call *fn(**kwargs)* and retry once on transient errors:
    - ValueError        → JSON parse error        (wait 1 s)
    - ServerError 503   → Gemini overloaded        (wait 8 s)
    - ClientError 429   → Quota exhausted          (wait as instructed by API)
    """
    for attempt in (1, 2):
        try:
            return fn(**kwargs)
        except ValueError as exc:
            if attempt == 1:
                console.print(
                    f"[yellow]⚠  {label}: JSON parse error, retrying in 1 s…[/yellow]"
                )
                time.sleep(1)
            else:
                raise RuntimeError(
                    f"{label} failed after retry: {exc}"
                ) from exc
        except genai_errors.ServerError as exc:
            if attempt == 1:
                console.print(
                    f"[yellow]⚠  {label}: Gemini server busy (503), retrying in 8 s…[/yellow]"
                )
                time.sleep(8)
            else:
                raise RuntimeError(
                    f"{label} failed after retry (503): {exc}"
                ) from exc
        except genai_errors.ClientError as exc:
            delay = _parse_retry_delay(exc)
            if attempt == 1:
                console.print(
                    f"[yellow]⚠  {label}: quota limit hit (429), "
                    f"waiting {delay:.0f} s as instructed…[/yellow]"
                )
                time.sleep(delay)
            else:
                raise RuntimeError(
                    f"{label} failed after quota retry (429): {exc}"
                ) from exc
    return {}  # unreachable


def _difficulty_panel(current: str, next_d: str) -> str:
    if current == next_d:
        return f"[{DIFF_COLOUR[current]}]{current.upper()}[/{DIFF_COLOUR[current]}] (unchanged)"
    elif DIFF_ORDER.index(next_d) > DIFF_ORDER.index(current):
        return (
            f"[{DIFF_COLOUR[current]}]{current.upper()}[/{DIFF_COLOUR[current]}]"
            f" → [{DIFF_COLOUR[next_d]}]{next_d.upper()} ▲[/{DIFF_COLOUR[next_d]}]"
        )
    else:
        return (
            f"[{DIFF_COLOUR[current]}]{current.upper()}[/{DIFF_COLOUR[current]}]"
            f" → [{DIFF_COLOUR[next_d]}]{next_d.upper()} ▼[/{DIFF_COLOUR[next_d]}]"
        )


# ── Main session ───────────────────────────────────────────────────────────────

def run_session() -> None:
    # ── Validate API key ───────────────────────────────────────────────────────
    api_key = os.getenv("GOOGLE_API_KEY", "")
    if not api_key or api_key == "your_google_api_key_here":
        console.print(
            "[bold red]GOOGLE_API_KEY is not set.[/bold red]\n"
            "Edit [bold].env[/bold] and add your key from "
            "https://aistudio.google.com/app/apikey"
        )
        sys.exit(1)

    # ── Welcome banner ─────────────────────────────────────────────────────────
    console.print()
    console.print(
        Panel.fit(
            "[bold cyan]Study Buddy[/bold cyan]  —  AI-Powered BSCS Study Sessions\n"
            "[dim]Powered by Gemini 2.5 Flash[/dim]",
            border_style="cyan",
        )
    )
    console.print()

    # ── Step 1: Get topic & subject from student ───────────────────────────────
    console.print("[bold]Let's set up your study session.[/bold]\n")

    topic = Prompt.ask(
        "[bold green]Enter your study topic[/bold green]"
        " [dim](e.g. Process Scheduling)[/dim]"
    ).strip()

    subject = Prompt.ask(
        "[bold green]Enter the subject folder name[/bold green]"
        " [dim](e.g. operating_systems / data_structures / dbms)[/dim]"
    ).strip().lower().replace(" ", "_")

    console.print()

    # ── Step 2: Planner Agent ──────────────────────────────────────────────────
    console.print(Rule("[bold]Step 1 of 2 — Building your learning plan[/bold]"))
    console.print("[dim]PlannerAgent is generating your subtopics…[/dim]")

    planner = PlannerAgent(api_key=api_key)
    plan    = _call_with_retry(
        planner.create_plan, "PlannerAgent",
        topic=topic, subject=subject
    )
    subtopics = plan["subtopics"]

    # ── Step 3: Show the plan ──────────────────────────────────────────────────
    plan_table = Table(
        title=f"Learning Plan: {topic}",
        box=box.ROUNDED,
        border_style="cyan",
        show_lines=True,
    )
    plan_table.add_column("#",             style="bold cyan",  width=3)
    plan_table.add_column("Subtopic",      style="white",      min_width=30)
    plan_table.add_column("Est. Minutes",  style="yellow",     justify="right")

    for st in subtopics:
        plan_table.add_row(
            str(st["order"]),
            st["name"],
            f"{st['estimated_minutes']} min",
        )

    console.print()
    console.print(plan_table)
    console.print()
    Prompt.ask("[dim]Press Enter to start the session[/dim]", default="")
    console.print()

    # ── Step 4: Question → Answer → Evaluate loop ─────────────────────────────
    console.print(Rule("[bold]Step 2 of 2 — Practice Questions[/bold]"))

    q_agent  = QuestionGeneratorAgent(api_key=api_key)
    ev_agent = EvaluatorAgent(api_key=api_key)

    difficulty    = "easy"      # starting difficulty
    scores: list[int]   = []
    difficulty_arc: list[str] = [difficulty]

    for idx, subtopic in enumerate(subtopics, start=1):
        subtopic_name = subtopic["name"]
        console.print(
            f"\n[bold]Subtopic {idx}/3:[/bold] "
            f"[bold white]{subtopic_name}[/bold white]  "
            f"| Difficulty: [{DIFF_COLOUR[difficulty]}]{difficulty.upper()}[/{DIFF_COLOUR[difficulty]}]"
        )
        console.print(Rule(style="dim"))

        # ── Generate question ──────────────────────────────────────────────────
        console.print("[dim]QuestionGeneratorAgent is thinking…[/dim]")
        q_result = _call_with_retry(
            q_agent.generate, "QuestionGeneratorAgent",
            subject=subject,
            subtopic=subtopic_name,
            difficulty=difficulty,
        )
        question = q_result["question"]

        console.print(
            Panel(
                f"[bold white]{question}[/bold white]",
                title="[cyan]Your Question[/cyan]",
                border_style="cyan",
                padding=(1, 2),
            )
        )

        # ── Student answer ─────────────────────────────────────────────────────
        student_answer = Prompt.ask("\n[bold green]Your answer[/bold green]").strip()
        if not student_answer:
            student_answer = "(no answer provided)"

        console.print("[dim]EvaluatorAgent is marking your answer…[/dim]")

        # ── Evaluate ───────────────────────────────────────────────────────────
        ev_result = _call_with_retry(
            ev_agent.evaluate, "EvaluatorAgent",
            question=question,
            student_answer=student_answer,
            difficulty=difficulty,
        )

        score        = int(ev_result["score"])
        correct      = ev_result["correct"]
        feedback     = ev_result["feedback"]
        hint         = ev_result.get("hint")
        next_diff    = ev_result["next_difficulty"]

        scores.append(score)

        # ── Result panel ───────────────────────────────────────────────────────
        score_colour = "green" if score >= 70 else ("yellow" if score >= 40 else "red")

        result_tbl = Table(show_header=False, box=box.SIMPLE, padding=(0, 1))
        result_tbl.add_column("Field", style="bold cyan", no_wrap=True)
        result_tbl.add_column("Value")

        result_tbl.add_row(
            "Score",
            f"[{score_colour}][bold]{score}/100[/bold][/{score_colour}]"
        )
        result_tbl.add_row(
            "Result",
            "[bold green]Correct![/bold green]" if correct
            else "[bold red]Needs improvement[/bold red]"
        )
        result_tbl.add_row("Feedback", feedback)

        if hint:
            result_tbl.add_row("Hint", f"[yellow]{hint}[/yellow]")

        result_tbl.add_row(
            "Next Difficulty",
            _difficulty_panel(difficulty, next_diff),
        )

        console.print(
            Panel(
                result_tbl,
                title="[bold]Evaluation Result[/bold]",
                border_style=score_colour,
                padding=(0, 1),
            )
        )

        # ── Update difficulty ──────────────────────────────────────────────────
        difficulty = next_diff
        difficulty_arc.append(difficulty)

    # ── Step 5: Final Summary ──────────────────────────────────────────────────
    console.print()
    console.print(Rule("[bold cyan]Session Complete — Summary[/bold cyan]", style="cyan"))
    console.print()

    avg_score      = sum(scores) / len(scores)
    score_colour   = "green" if avg_score >= 70 else ("yellow" if avg_score >= 40 else "red")

    import random
    motivation = random.choice(MOTIVATIONAL_LINES)

    summary_tbl = Table(
        title="Your Session Report",
        box=box.ROUNDED,
        border_style="cyan",
        show_lines=True,
        min_width=55,
    )
    summary_tbl.add_column("Item",   style="bold cyan",  min_width=22)
    summary_tbl.add_column("Detail", style="white")

    summary_tbl.add_row(
        "Topic",
        f"[bold]{topic}[/bold]"
    )
    summary_tbl.add_row(
        "Subject",
        subject.replace("_", " ").title()
    )
    summary_tbl.add_row(
        "Subtopics Covered",
        "\n".join(f"{s['order']}. {s['name']}" for s in subtopics),
    )
    summary_tbl.add_row(
        "Scores",
        "  ".join(
            f"[{'green' if s >= 70 else 'yellow' if s >= 40 else 'red'}]{s}[/]"
            for s in scores
        )
    )
    summary_tbl.add_row(
        "Average Score",
        f"[{score_colour}][bold]{avg_score:.1f}/100[/bold][/{score_colour}]"
    )
    summary_tbl.add_row(
        "Difficulty Arc",
        " → ".join(
            f"[{DIFF_COLOUR[d]}]{d.upper()}[/{DIFF_COLOUR[d]}]"
            for d in difficulty_arc
        )
    )
    summary_tbl.add_row(
        "Final Difficulty",
        f"[{DIFF_COLOUR[difficulty]}][bold]{difficulty.upper()}[/bold][/{DIFF_COLOUR[difficulty]}]"
    )

    console.print(summary_tbl)
    console.print()
    console.print(
        Panel(
            f"[bold yellow]{motivation}[/bold yellow]",
            border_style="yellow",
            expand=False,
        )
    )
    console.print()


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    try:
        run_session()
    except KeyboardInterrupt:
        console.print("\n\n[bold yellow]Session interrupted. See you next time![/bold yellow]\n")
        sys.exit(0)
    except RuntimeError as e:
        console.print(f"\n[bold red]Agent error:[/bold red] {e}\n")
        sys.exit(1)
