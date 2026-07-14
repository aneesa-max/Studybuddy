# 🎓 Study Buddy

A multi-agent AI study assistant powered by **Google ADK** and **Gemini**.

---

## Architecture

```
studybuddy/
├── main.py                  # Entry point — boots the orchestrator
├── .env                     # API keys (never commit this!)
├── requirements.txt
│
├── agents/                  # Specialist AI agents
│   ├── __init__.py
│   ├── orchestrator.py      # Routes queries to the right agent
│   ├── tutor.py             # Explains concepts & answers questions
│   ├── quiz.py              # Generates quizzes & evaluates answers
│   └── summary.py           # Summarises study material
│
└── skills/                  # Reusable capabilities shared across agents
    ├── __init__.py
    ├── search.py            # Web / document retrieval
    ├── summarise.py         # Text condensation helper
    ├── quiz_gen.py          # MCQ generation
    └── flashcards.py        # Spaced-repetition flashcard creation
```

### Agent routing

```
User input
    │
    ▼
OrchestratorAgent  ──── "quiz" / "test" ──────▶ QuizAgent
    │
    ├──── "summarise" / "tldr" ────▶ SummaryAgent
    │
    └──── (everything else) ───────▶ TutorAgent
```

---

## Quick Start

### 1. Clone & create a virtual environment

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # macOS / Linux
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Add your Gemini API key

Edit `.env`:

```env
GOOGLE_API_KEY=your_real_key_here
```

Get a free key at <https://aistudio.google.com/app/apikey>.

### 4. Run

```bash
python main.py
```

---

## Extending the project

| What you want to add | Where to add it |
|---|---|
| A new specialist agent | `agents/my_agent.py` + register in `agents/__init__.py` |
| A new reusable capability | `skills/my_skill.py` + register in `skills/__init__.py` |
| Wire up real search | Replace stub in `skills/search.py` |
| Persistent memory | Add a `memory/` package |
| REST API | Add `api/` with FastAPI |

---

## License

MIT
