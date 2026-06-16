"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()

LLM_MODEL = "llama-3.3-70b-versatile"


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


def _call_groq(system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
    """Send a chat completion request to Groq and return the response text."""
    client = _get_groq_client()
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
    )
    return response.choices[0].message.content.strip()


def _format_wardrobe(wardrobe: dict) -> str:
    """Format wardrobe items into a readable bullet list for LLM prompts."""
    lines = []
    for item in wardrobe.get("items", []):
        line = (
            f"- {item['name']} ({item['category']}, "
            f"colors: {', '.join(item['colors'])})"
        )
        if item.get("notes"):
            line += f" — {item['notes']}"
        lines.append(line)
    return "\n".join(lines)


def _format_new_item(new_item: dict) -> str:
    """Format a listing dict into a readable summary for LLM prompts."""
    brand = new_item.get("brand") or "unknown brand"
    return (
        f"Title: {new_item['title']}\n"
        f"Category: {new_item['category']}\n"
        f"Description: {new_item['description']}\n"
        f"Style tags: {', '.join(new_item['style_tags'])}\n"
        f"Colors: {', '.join(new_item['colors'])}\n"
        f"Brand: {brand}\n"
        f"Price: ${new_item['price']:.2f}\n"
        f"Platform: {new_item['platform']}"
    )


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform
    """
    listings = load_listings()
    tokens = [word.lower() for word in description.split() if len(word) >= 3]

    scored: list[tuple[int, float, dict]] = []

    for listing in listings:
        if max_price is not None and listing["price"] > max_price:
            continue
        if size is not None and size.lower() not in listing["size"].lower():
            continue

        searchable = (
            listing["title"].lower()
            + " "
            + listing["description"].lower()
            + " "
            + " ".join(tag.lower() for tag in listing["style_tags"])
        )

        score = sum(1 for token in tokens if token in searchable)
        if score > 0:
            scored.append((score, listing["price"], listing))

    scored.sort(key=lambda entry: (-entry[0], entry[1]))
    return [listing for _, _, listing in scored]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.
    """
    item_summary = _format_new_item(new_item)
    wardrobe_items = wardrobe.get("items", [])

    if not wardrobe_items:
        system_prompt = (
            "You are a personal stylist helping someone style a thrift find. "
            "The user has not added any wardrobe items yet. Suggest 1–2 general "
            "outfit formulas that would work with this piece — name categories "
            "of items (e.g., wide-leg jeans, chunky sneakers) rather than specific "
            "owned pieces. Include styling tips and the overall vibe. "
            "Keep it to 2–6 sentences."
        )
        user_prompt = (
            f"The user is considering buying this thrift item:\n\n"
            f"{item_summary}\n\n"
            f"Suggest how to style it without knowing their existing wardrobe."
        )
    else:
        wardrobe_text = _format_wardrobe(wardrobe)
        system_prompt = (
            "You are a personal stylist. Given a thrift item and the user's "
            "existing wardrobe, suggest 1–2 complete outfit combinations. "
            "Reference wardrobe pieces by their exact names. Include specific "
            "styling tips (tucking, layering, rolling sleeves, etc.) and the "
            "overall vibe. Keep it to 2–6 sentences."
        )
        user_prompt = (
            f"The user is considering buying this thrift item:\n\n"
            f"{item_summary}\n\n"
            f"Their wardrobe:\n{wardrobe_text}\n\n"
            f"Suggest outfit combinations using the new item and named pieces "
            f"from their wardrobe."
        )

    try:
        return _call_groq(system_prompt, user_prompt, temperature=0.7)
    except Exception:
        return "Could not generate outfit suggestions right now. Try again in a moment."


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.
    """
    if not outfit or not outfit.strip():
        return (
            "Can't create a fit card — no outfit suggestion was provided. "
            "Run outfit styling first."
        )

    system_prompt = (
        "You write casual, authentic Instagram/TikTok outfit captions for "
        "thrift finds. Write in first person. Sound like a real person sharing "
        "an OOTD — not a product description. Mention the item name, price, "
        "and platform naturally once each. Capture the outfit vibe in specific "
        "terms. Keep it to 2–4 sentences. No hashtags unless they feel natural."
    )
    user_prompt = (
        f"Item: {new_item['title']}\n"
        f"Price: ${new_item['price']:.2f}\n"
        f"Platform: {new_item['platform']}\n\n"
        f"Outfit styling:\n{outfit}\n\n"
        f"Write a shareable fit card caption."
    )

    try:
        return _call_groq(system_prompt, user_prompt, temperature=0.9)
    except Exception:
        return "Could not generate a fit card right now. Try again in a moment."
