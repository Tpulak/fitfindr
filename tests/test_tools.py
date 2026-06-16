"""Tests for FitFindr tools — run with: pytest tests/ -v"""

from unittest.mock import patch

import pytest

from tools import create_fit_card, search_listings, suggest_outfit
from utils.data_loader import get_empty_wardrobe, get_example_wardrobe, load_listings


# ── search_listings ───────────────────────────────────────────────────────────

def test_search_returns_results():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    assert isinstance(results, list)
    assert len(results) > 0
    assert "title" in results[0]
    assert "price" in results[0]


def test_search_empty_results():
    results = search_listings("designer ballgown", size="XXS", max_price=5)
    assert results == []


def test_search_price_filter():
    results = search_listings("jacket", size=None, max_price=10)
    assert all(item["price"] <= 10 for item in results)


def test_search_size_filter():
    results = search_listings("track jacket", size="M", max_price=100)
    assert len(results) > 0
    assert all("m" in item["size"].lower() for item in results)


# ── suggest_outfit ────────────────────────────────────────────────────────────

def test_suggest_outfit_empty_wardrobe():
    listings = search_listings("vintage graphic tee", size=None, max_price=50)
    assert len(listings) > 0

    mock_response = (
        "This faded band tee works great with wide-leg denim and chunky sneakers "
        "for a classic 90s grunge look."
    )
    with patch("tools._call_groq", return_value=mock_response):
        result = suggest_outfit(listings[0], get_empty_wardrobe())

    assert isinstance(result, str)
    assert len(result) > 0
    assert result == mock_response


def test_suggest_outfit_with_wardrobe():
    listings = search_listings("vintage graphic tee", size=None, max_price=50)
    mock_response = (
        "Pair the band tee with your baggy straight-leg jeans and chunky white sneakers."
    )
    with patch("tools._call_groq", return_value=mock_response):
        result = suggest_outfit(listings[0], get_example_wardrobe())

    assert isinstance(result, str)
    assert len(result) > 0


def test_suggest_outfit_api_error():
    listings = load_listings()
    with patch("tools._call_groq", side_effect=Exception("API down")):
        result = suggest_outfit(listings[0], get_example_wardrobe())

    assert "Could not generate outfit suggestions" in result


# ── create_fit_card ───────────────────────────────────────────────────────────

def test_create_fit_card_empty_outfit():
    item = load_listings()[0]
    result = create_fit_card("", item)
    assert "Can't create a fit card" in result


def test_create_fit_card_whitespace_outfit():
    item = load_listings()[0]
    result = create_fit_card("   ", item)
    assert "Can't create a fit card" in result


def test_create_fit_card_success():
    item = load_listings()[0]
    outfit = "Pair with baggy jeans and chunky sneakers for a grunge look."
    mock_caption = "thrifted this tee on depop for $19 and it goes so hard with my wide-legs"
    with patch("tools._call_groq", return_value=mock_caption):
        result = create_fit_card(outfit, item)

    assert isinstance(result, str)
    assert len(result) > 0
    assert result == mock_caption


def test_create_fit_card_api_error():
    item = load_listings()[0]
    outfit = "Pair with baggy jeans and chunky sneakers."
    with patch("tools._call_groq", side_effect=Exception("API down")):
        result = create_fit_card(outfit, item)

    assert "Could not generate a fit card" in result
