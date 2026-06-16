"""
Milestone 5 — deliberate failure mode checks.
Run: python run_failure_checks.py

Use output from this script (or the Gradio UI) for your demo screenshot/recording.
"""

from agent import run_agent
from tools import create_fit_card, search_listings, suggest_outfit
from utils.data_loader import get_empty_wardrobe, get_example_wardrobe


def section(title: str) -> None:
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


section("FAILURE 1: search_listings — no results")
results = search_listings("designer ballgown", size="XXS", max_price=5)
print(f"Return value: {results}")
print(f"Type: {type(results).__name__}, length: {len(results)}")

section("FAILURE 1 (agent): full pipeline stops gracefully")
session = run_agent(
    "designer ballgown size XXS under $5",
    get_example_wardrobe(),
)
print(f"session['error']: {session['error']}")
print(f"session['fit_card']: {session['fit_card']}")
print(f"session['outfit_suggestion']: {session['outfit_suggestion']}")

section("FAILURE 2: suggest_outfit — empty wardrobe")
items = search_listings("vintage graphic tee", size=None, max_price=50)
print(f"Using item: {items[0]['title']}")
advice = suggest_outfit(items[0], get_empty_wardrobe())
print(f"Response ({len(advice)} chars):\n{advice}")

section("FAILURE 3: create_fit_card — empty outfit string")
err = create_fit_card("", items[0])
print(f"Response: {err}")

section("All failure checks complete.")
