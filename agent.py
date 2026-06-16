"""
agent.py

The FitFindr planning loop. Orchestrates the three tools in response to a
natural language user query, passing state between them via a session dict.

Complete tools.py and test each tool in isolation before implementing this file.

Usage (once implemented):
    from agent import run_agent
    from utils.data_loader import get_example_wardrobe

    result = run_agent(
        query="vintage graphic tee under $30, size M",
        wardrobe=get_example_wardrobe(),
    )
    print(result["fit_card"])
    print(result["error"])   # None on success
"""

import re

from tools import search_listings, suggest_outfit, create_fit_card


# ── session state ─────────────────────────────────────────────────────────────

def _new_session(query: str, wardrobe: dict) -> dict:
    """
    Initialize and return a fresh session dict for one user interaction.

    The session dict is the single source of truth for everything that happens
    during a run — it stores the original query, parsed parameters, tool results,
    and any error that caused early termination.

    You may add fields to this dict as needed for your implementation.
    """
    return {
        "query": query,              # original user query
        "parsed": {},                # extracted description / size / max_price
        "search_results": [],        # list of matching listing dicts
        "selected_item": None,       # top result, passed into suggest_outfit
        "wardrobe": wardrobe,        # user's wardrobe dict
        "outfit_suggestion": None,   # string returned by suggest_outfit
        "fit_card": None,            # string returned by create_fit_card
        "error": None,               # set if the interaction ended early
    }


def _parse_query(query: str) -> dict:
    """
    Extract description, size, and max_price from a natural-language query using regex.

    Documented in planning.md — no LLM call.
    """
    remaining = query
    max_price = None
    size = None

    price_patterns = [
        r"under\s*\$?\s*(\d+(?:\.\d+)?)",
        r"max\s*\$?\s*(\d+(?:\.\d+)?)",
        r"\$(\d+(?:\.\d+)?)\s*or\s*less",
    ]
    for pattern in price_patterns:
        match = re.search(pattern, remaining, re.IGNORECASE)
        if match:
            max_price = float(match.group(1))
            remaining = remaining[: match.start()] + remaining[match.end() :]
            break

    size_match = re.search(r"(?:in\s+)?size\s+(\S+)", remaining, re.IGNORECASE)
    if size_match:
        size = size_match.group(1).strip(",.")
        remaining = remaining[: size_match.start()] + remaining[size_match.end() :]

    description = re.sub(r"\s+", " ", remaining).strip(" ,.-")
    if not description:
        description = query.strip()

    return {"description": description, "size": size, "max_price": max_price}


def _no_results_message(parsed: dict) -> str:
    """Build a helpful error message when search_listings returns nothing."""
    size_label = parsed["size"] if parsed["size"] else "any"
    price_label = f"${parsed['max_price']:.0f}" if parsed["max_price"] else "none"
    return (
        f"No listings found for '{parsed['description']}' "
        f"(size: {size_label}, max price: {price_label}). "
        f"Try using broader keywords like 'graphic tee' or 'vintage top', "
        f"increasing your budget, or dropping the size filter."
    )


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Main agent entry point. Runs the FitFindr planning loop for a single
    user interaction and returns the completed session dict.

    Args:
        query:    Natural language user request
                  (e.g., "vintage graphic tee under $30, size M")
        wardrobe: User's wardrobe dict — use get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py

    Returns:
        The session dict after the interaction completes. Check session["error"]
        first — if it is not None, the interaction ended early and the other
        output fields (outfit_suggestion, fit_card) will be None.
    """
    session = _new_session(query, wardrobe)

    session["parsed"] = _parse_query(query)
    parsed = session["parsed"]

    session["search_results"] = search_listings(
        parsed["description"],
        parsed["size"],
        parsed["max_price"],
    )

    if not session["search_results"]:
        session["error"] = _no_results_message(parsed)
        return session

    session["selected_item"] = session["search_results"][0]

    session["outfit_suggestion"] = suggest_outfit(
        session["selected_item"],
        session["wardrobe"],
    )

    session["fit_card"] = create_fit_card(
        session["outfit_suggestion"],
        session["selected_item"],
    )

    return session


# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )
    if session["error"]:
        print(f"Error: {session['error']}")
    else:
        print(f"Found: {session['selected_item']['title']}")
        print(f"\nOutfit: {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== No-results path ===\n")
    session2 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    print(f"Error message: {session2['error']}")
