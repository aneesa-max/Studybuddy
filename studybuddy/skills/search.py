"""
search_skill
============
Retrieves relevant documents or web content to ground agent responses.
Plug in your preferred search backend (e.g. Google Search, Tavily, etc.).
"""

from __future__ import annotations


def search_skill(query: str, *, max_results: int = 5) -> list[dict]:
    """
    Search for information relevant to *query*.

    Parameters
    ----------
    query:       The search query string.
    max_results: Maximum number of results to return.

    Returns
    -------
    List of dicts with keys: ``title``, ``url``, ``snippet``.

    TODO: Replace the stub below with a real search API call.
    """
    # ── Stub implementation ───────────────────────────────────────────────────
    return [
        {
            "title": f"[stub] Result {i + 1} for '{query}'",
            "url": "https://example.com",
            "snippet": "Replace this stub with a real search API.",
        }
        for i in range(max_results)
    ]
