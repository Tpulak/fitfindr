# FitFindr

FitFindr is a multi-tool AI agent that helps users find secondhand clothing and figure out how to wear it. Given a natural-language search query, the agent searches mock thrift listings, suggests outfits based on the user's wardrobe, and generates a shareable fit card caption — while handling failures gracefully when a tool returns nothing useful.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Mac/Linux

pip install -r requirements.txt
```

Create a `.env` file in the project root (never commit this):

```
GROQ_API_KEY=your_key_here
```

Get a free key at [console.groq.com](https://console.groq.com).

### Run the app

```bash
python app.py
```

Open the URL shown in your terminal (usually `http://localhost:7860`).

### Run tests

```bash
pytest tests/ -v
python run_failure_checks.py   # deliberate failure mode verification
python agent.py                # CLI happy path + no-results path
```

## Project structure

```
fitfindr/
├── agent.py              # Planning loop and session state
├── app.py                # Gradio UI
├── tools.py              # Three agent tools
├── planning.md           # Design spec (written before implementation)
├── data/
│   ├── listings.json     # 40 mock secondhand listings
│   └── wardrobe_schema.json
├── utils/data_loader.py
├── tests/
│   ├── test_tools.py
│   └── test_agent.py
└── run_failure_checks.py
```

---

## Tool inventory

### 1. `search_listings`

| | |
|---|---|
| **Purpose** | Search the mock listings dataset and return matching items ranked by relevance |
| **Inputs** | `description` (`str`) — keywords to match against title, description, and style tags<br>`size` (`str \| None`) — optional size filter (case-insensitive substring match)<br>`max_price` (`float \| None`) — optional maximum price inclusive |
| **Output** | `list[dict]` — matching listings sorted by keyword score (desc), then price (asc). Each dict contains `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, `platform`. Returns `[]` if nothing matches. |

### 2. `suggest_outfit`

| | |
|---|---|
| **Purpose** | Given a thrift item and the user's wardrobe, suggest 1–2 complete outfit combinations using Groq (`llama-3.3-70b-versatile`) |
| **Inputs** | `new_item` (`dict`) — a listing dict from `search_listings`<br>`wardrobe` (`dict`) — wardrobe with an `items` key (list of wardrobe item dicts); may be empty |
| **Output** | `str` — 2–6 sentences of outfit suggestions in plain English. References named wardrobe pieces when available; gives general pairing advice when wardrobe is empty. |

### 3. `create_fit_card`

| | |
|---|---|
| **Purpose** | Generate a short, casual, shareable outfit caption (Instagram/TikTok style) for the thrift find |
| **Inputs** | `outfit` (`str`) — outfit suggestion from `suggest_outfit`<br>`new_item` (`dict`) — listing dict for the item (used for title, price, platform) |
| **Output** | `str` — 2–4 sentence first-person caption. Uses temperature 0.9 for variation across runs. |

---

## Planning loop

The agent runs a **conditional linear loop** in `run_agent()` — it does not call all three tools unconditionally.

```
1. Initialize session dict
2. Parse query (regex) → {description, size, max_price}
3. search_listings()
      ├── results empty → set session["error"], return early
      └── results found → continue
4. selected_item = search_results[0]
5. suggest_outfit(selected_item, wardrobe)
6. create_fit_card(outfit_suggestion, selected_item)
7. Return session
```

**What changes behavior:**

- **Empty search results** — the agent stops immediately. It does not call `suggest_outfit` or `create_fit_card`. Only `session["error"]` is populated.
- **Non-empty search results** — the full three-tool pipeline runs. The same `selected_item` dict flows into both LLM tools without the user re-entering anything.
- **Empty vs. populated wardrobe** — does not change which tools are called; it changes the *content* of `suggest_outfit` (general advice vs. wardrobe-specific combos).

**Query parsing** uses regex (no LLM call):
- Price: `under $30`, `under 30`, `max $30`, `$30 or less`
- Size: `size M`, `in size L`, `size 8`
- Description: remaining text after price/size phrases are stripped

---

## State management

All state for one interaction lives in a single **session dict** created by `_new_session()` and updated in place by `run_agent()`.

| Key | Set when | Consumed by |
|-----|----------|-------------|
| `query` | Session init | Reference / debug |
| `parsed` | After regex parse | `search_listings` |
| `search_results` | After search | Empty check; source for `selected_item` |
| `selected_item` | Top search result | `suggest_outfit`, `create_fit_card` |
| `wardrobe` | Session init (from UI) | `suggest_outfit` |
| `outfit_suggestion` | After `suggest_outfit` | `create_fit_card` |
| `fit_card` | After `create_fit_card` | UI panel 3 |
| `error` | On search failure | UI panel 1 (early exit) |

**State flow (happy path):**

```
query → parsed → search_results[0] → selected_item
                                         ↓
                              outfit_suggestion
                                         ↓
                                    fit_card
```

The Gradio handler in `app.py` reads the completed session and maps `selected_item`, `outfit_suggestion`, and `fit_card` to the three output panels. If `error` is set, only panel 1 shows the message.

---

## Error handling

| Tool | Failure mode | What happens |
|------|-------------|--------------|
| `search_listings` | No results match | Tool returns `[]`. Agent sets a helpful error and returns early. |
| `suggest_outfit` | Empty wardrobe | Tool calls LLM with a general-styling prompt — not treated as an error. Agent continues normally. |
| `create_fit_card` | Empty outfit string | Tool returns an error message string without calling the LLM. |
| `app.py` | Empty user query | Returns `"Please enter a search query."` without calling the agent. |

### Concrete examples (from testing)

**1. No search results**

Query: `designer ballgown size XXS under $5`

```
No listings found for 'designer ballgown' (size: XXS, max price: $5).
Try using broader keywords like 'graphic tee' or 'vintage top',
increasing your budget, or dropping the size filter.
```

Verified: `session["fit_card"]` and `session["outfit_suggestion"]` remain `None`. `suggest_outfit` and `create_fit_card` are never called.

**2. Empty wardrobe**

Query: `vintage graphic tee under $30` with "Empty wardrobe (new user)" selected.

`suggest_outfit` returns general pairing advice (e.g., high-waisted mom jeans and chunky sneakers) instead of referencing specific owned pieces. The agent still produces a fit card in panel 3.

**3. Empty outfit input**

```python
create_fit_card("", item)
# → "Can't create a fit card — no outfit suggestion was provided. Run outfit styling first."
```

---

## Spec reflection

The final implementation closely follows `planning.md`:

- **Matched:** Conditional planning loop with early exit on empty search, regex query parsing, session dict state passing, all three tool signatures and failure modes, Groq LLM for outfit and fit card tools.
- **Refined during implementation:** Search scoring tokenizes on words ≥3 characters and breaks ties by lower price — this occasionally ranks a tangentially related item (e.g., a mesh top whose description mentions "graphic tee") above a direct match. Acceptable for the mock dataset; a production version would weight title/style_tags higher than description mentions.
- **Test coverage added beyond spec:** `tests/test_agent.py` verifies that downstream tools are not invoked when search fails, and `run_failure_checks.py` provides a repeatable failure-mode demo script.

---

## AI usage

This project was built milestone-by-milestone using Cursor (Claude) as the primary AI coding assistant, with `planning.md` as the source of truth.

### Instance 1 — Tool implementations (Milestone 3)

**Input given to AI:** Tool 1–3 spec blocks from `planning.md` (inputs, return values, scoring logic, failure modes) plus the existing stubs in `tools.py`.

**Output produced:** Implementations of `search_listings`, `suggest_outfit`, and `create_fit_card`, plus `tests/test_tools.py`.

**What I changed before accepting:**
- Reviewed that `search_listings` uses `load_listings()` rather than re-reading JSON
- Confirmed empty wardrobe and empty outfit paths return strings, not exceptions
- Added `unittest.mock` patches in tests so pytest does not hit the Groq API on every run
- Ran live verification to check fit card tone and temperature variation

### Instance 2 — Planning loop and UI (Milestone 4)

**Input given to AI:** Planning Loop section, State Management section, Architecture diagram, and the TODO steps in `agent.py` and `app.py`.

**Output produced:** `_parse_query()`, `run_agent()`, `_format_listing()`, and `handle_query()`.

**What I changed before accepting:**
- Verified regex parsing against all example queries in `app.py` (including `in size M` and `under $30`)
- Confirmed early exit leaves `fit_card` and `outfit_suggestion` as `None` (not empty strings)
- Ran `python agent.py` to validate state passing: `selected_item is search_results[0]`
- Added `tests/test_agent.py` in Milestone 5 to lock in failure behavior

---

## Demo video guide

Record a **3–5 minute** video covering these three moments. Suggested narration script:

### Part 1 — Happy path (~2 min)

1. Run `python app.py` and open the UI.
2. Select **Example wardrobe**.
3. Enter: `vintage graphic tee under $30`
4. Click **Find it**.
5. **Narrate:** "The agent parsed my query to extract the description and $30 price cap, then called `search_listings`. The top result is stored in session state as `selected_item` — that same item flows into `suggest_outfit` without me re-entering it."
6. Point to all three panels: listing, outfit idea, fit card.

### Part 2 — State passing (~30 sec)

7. **Narrate:** "The listing in panel 1 is the exact dict passed to the outfit tool. The outfit text in panel 2 is what went into `create_fit_card`. The user never re-typed the item between steps."
8. Optional: run `python agent.py` in a terminal alongside the UI to show the session dict output.

### Part 3 — Failure handling (~1 min)

9. Submit: `designer ballgown size XXS under $5` (or click the example query).
10. **Narrate:** "Search returned nothing, so the agent stopped early. It tells me what to try differently instead of calling the outfit or fit card tools with empty input."
11. Show panels 2 and 3 are empty.
12. Optional second failure: select **Empty wardrobe** and run a happy-path query to show general styling advice in panel 2.

### Recording tips

- Windows: Xbox Game Bar (`Win + G`) or OBS
- Mac: QuickTime or built-in screenshot toolbar
- Keep the terminal visible for at least one shot to show the agent is doing real work

---

## Example queries

| Query | Expected behavior |
|-------|-------------------|
| `vintage graphic tee under $30` | Full pipeline — all 3 panels populate |
| `90s track jacket in size M` | Search with size filter |
| `designer ballgown size XXS under $5` | No results — error in panel 1 only |
