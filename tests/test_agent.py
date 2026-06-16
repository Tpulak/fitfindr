"""Tests for agent planning loop and UI handler failure modes."""

from unittest.mock import patch

from agent import _parse_query, run_agent
from app import handle_query
from tools import create_fit_card, search_listings, suggest_outfit
from utils.data_loader import get_empty_wardrobe, get_example_wardrobe


# ── Tool-level failure modes (Milestone 5 verification) ─────────────────────

def test_search_no_results_returns_empty_list():
    results = search_listings("designer ballgown", size="XXS", max_price=5)
    assert results == []


def test_suggest_outfit_empty_wardrobe_returns_advice():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    assert len(results) > 0

    advice = (
        "This faded band tee works great with wide-leg denim and chunky sneakers "
        "for a classic 90s grunge look."
    )
    with patch("tools._call_groq", return_value=advice):
        result = suggest_outfit(results[0], get_empty_wardrobe())

    assert isinstance(result, str)
    assert len(result) > 0
    assert "grunge" in result.lower() or "denim" in result.lower()


def test_create_fit_card_empty_outfit_returns_error_message():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    result = create_fit_card("", results[0])
    assert "Can't create a fit card" in result


# ── Agent-level failure modes ─────────────────────────────────────────────────

def test_run_agent_stops_on_empty_search():
    session = run_agent(
        "designer ballgown size XXS under $5",
        get_example_wardrobe(),
    )

    assert session["error"] is not None
    assert "No listings found" in session["error"]
    assert "designer ballgown" in session["error"]
    assert "broader keywords" in session["error"]
    assert session["selected_item"] is None
    assert session["outfit_suggestion"] is None
    assert session["fit_card"] is None
    assert session["search_results"] == []


def test_run_agent_empty_wardrobe_still_completes():
    mock_outfit = "Pair with wide-leg jeans and chunky sneakers for a grunge look."
    mock_card = "thrifted this tee on depop for $19"

    with patch("tools._call_groq", side_effect=[mock_outfit, mock_card]):
        session = run_agent(
            "vintage graphic tee under $30",
            get_empty_wardrobe(),
        )

    assert session["error"] is None
    assert session["selected_item"] is not None
    assert session["outfit_suggestion"] == mock_outfit
    assert session["fit_card"] == mock_card


def test_run_agent_does_not_call_outfit_tools_when_search_empty():
    with patch("tools.suggest_outfit") as mock_suggest, patch(
        "tools.create_fit_card"
    ) as mock_card:
        run_agent("designer ballgown size XXS under $5", get_example_wardrobe())

    mock_suggest.assert_not_called()
    mock_card.assert_not_called()


def test_parse_query_extracts_filters():
    parsed = _parse_query("designer ballgown size XXS under $5")
    assert parsed["description"] == "designer ballgown"
    assert parsed["size"] == "XXS"
    assert parsed["max_price"] == 5.0


# ── UI handler failure modes ──────────────────────────────────────────────────

def test_handle_query_empty_input():
    listing, outfit, card = handle_query("", "Example wardrobe")
    assert listing == "Please enter a search query."
    assert outfit == ""
    assert card == ""


def test_handle_query_no_results():
    listing, outfit, card = handle_query(
        "designer ballgown size XXS under $5",
        "Example wardrobe",
    )
    assert "No listings found" in listing
    assert outfit == ""
    assert card == ""
