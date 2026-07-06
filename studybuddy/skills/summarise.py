"""
summarise_skill
===============
Shared text-condensation helper used by SummaryAgent (and others).
"""

from __future__ import annotations


def summarise_skill(text: str, *, max_bullets: int = 7) -> str:
    """
    Condense *text* into a bullet-point summary.

    Parameters
    ----------
    text:        Raw text to summarise.
    max_bullets: Target maximum number of bullet points.

    Returns
    -------
    A formatted string summary.

    TODO: Replace the stub with a real Gemini call or chain.
    """
    # ── Stub implementation ───────────────────────────────────────────────────
    sentences = [s.strip() for s in text.split(".") if s.strip()]
    bullets = sentences[:max_bullets]
    return "\n".join(f"• {b}." for b in bullets) or "• (no content to summarise)"
