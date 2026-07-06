"""
app.py — Study Buddy Flask Backend
====================================
Exposes three REST endpoints consumed by index.html:

  POST /api/plan       { topic, subject }              → learning plan JSON
  POST /api/question   { subject, subtopic, difficulty } → question JSON
  POST /api/evaluate   { question, answer, difficulty }  → evaluation JSON

Run:
    python app.py
Then open:  http://localhost:5000
"""

from __future__ import annotations

import os
import re
import time
import sys

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

# ── Bootstrap ──────────────────────────────────────────────────────────────────
load_dotenv()

app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)   # allow fetch from any origin during development

# Lazy-initialise agents once on first request (avoids slow startup)
_planner    = None
_questioner = None
_evaluator  = None


def _get_api_key() -> str:
    key = os.getenv("GOOGLE_API_KEY", "")
    if not key or key == "your_google_api_key_here":
        raise EnvironmentError("GOOGLE_API_KEY is not configured in .env")
    return key


def _agents():
    global _planner, _questioner, _evaluator
    if _planner is None:
        from agents.planner            import PlannerAgent
        from agents.question_generator import QuestionGeneratorAgent
        from agents.evaluator          import EvaluatorAgent
        key = _get_api_key()
        _planner    = PlannerAgent(api_key=key)
        _questioner = QuestionGeneratorAgent(api_key=key)
        _evaluator  = EvaluatorAgent(api_key=key)
    return _planner, _questioner, _evaluator


def _retry(fn, *args, retries: int = 1, delay: float = 8.0, **kwargs):
    """Call fn(*args, **kwargs), retrying once on transient API errors."""
    from google.genai import errors as genai_errors
    for attempt in range(retries + 1):
        try:
            return fn(*args, **kwargs)
        except (ValueError, genai_errors.ServerError) as exc:
            if attempt < retries:
                time.sleep(delay)
            else:
                raise
        except genai_errors.ClientError as exc:
            # Parse the suggested retry delay from the 429 message
            match = re.search(r"retry in\s+([\d.]+)s", str(exc), re.IGNORECASE)
            wait  = float(match.group(1)) + 2 if match else 65.0
            if attempt < retries:
                time.sleep(wait)
            else:
                raise


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Serve the frontend."""
    return send_from_directory(".", "index.html")


@app.route("/api/plan", methods=["POST"])
def api_plan():
    """
    Body:   { "topic": str, "subject": str }
    Returns: { "topic", "subject", "subtopics": [...] }
    """
    body = request.get_json(force=True, silent=True) or {}
    topic   = (body.get("topic")   or "").strip()
    subject = (body.get("subject") or "").strip()

    if not topic or not subject:
        return jsonify(error="Both 'topic' and 'subject' are required."), 400

    try:
        planner, _, _ = _agents()
        plan = _retry(planner.create_plan, topic=topic, subject=subject)
        return jsonify(plan)
    except EnvironmentError as exc:
        return jsonify(error=str(exc)), 503
    except Exception as exc:        # noqa: BLE001
        return jsonify(error=f"PlannerAgent error: {exc}"), 500


@app.route("/api/question", methods=["POST"])
def api_question():
    """
    Body:   { "subject": str, "subtopic": str, "difficulty": str }
    Returns: { "subject", "subtopic", "difficulty", "question" }
    """
    body       = request.get_json(force=True, silent=True) or {}
    subject    = (body.get("subject")    or "").strip()
    subtopic   = (body.get("subtopic")   or "").strip()
    difficulty = (body.get("difficulty") or "easy").strip().lower()

    if not subject or not subtopic:
        return jsonify(error="'subject' and 'subtopic' are required."), 400

    try:
        _, questioner, _ = _agents()
        result = _retry(
            questioner.generate,
            subject=subject, subtopic=subtopic, difficulty=difficulty,
        )
        return jsonify(result)
    except EnvironmentError as exc:
        return jsonify(error=str(exc)), 503
    except Exception as exc:        # noqa: BLE001
        return jsonify(error=f"QuestionGeneratorAgent error: {exc}"), 500


@app.route("/api/evaluate", methods=["POST"])
def api_evaluate():
    """
    Body:   { "question": str, "answer": str, "difficulty": str }
    Returns: { "score", "correct", "feedback", "hint", "next_difficulty" }
    """
    body       = request.get_json(force=True, silent=True) or {}
    question   = (body.get("question")   or "").strip()
    answer     = (body.get("answer")     or "").strip()
    difficulty = (body.get("difficulty") or "easy").strip().lower()

    if not question or not answer:
        return jsonify(error="'question' and 'answer' are required."), 400

    try:
        _, _, evaluator = _agents()
        result = _retry(
            evaluator.evaluate,
            question=question, student_answer=answer, difficulty=difficulty,
        )
        return jsonify(result)
    except EnvironmentError as exc:
        return jsonify(error=str(exc)), 503
    except Exception as exc:        # noqa: BLE001
        return jsonify(error=f"EvaluatorAgent error: {exc}"), 500


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Ensure UTF-8 console output on Windows
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    print("Study Buddy backend starting on http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
