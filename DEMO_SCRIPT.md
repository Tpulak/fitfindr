# FitFindr Demo Video Script (~4 minutes)

Use this script while screen-recording. You do not need to read it word-for-word — talk naturally, but hit every **CHECKPOINT** so the grader sees what they need.

**Before you hit record:**
1. Open terminal in the `fitfindr` folder, activate venv: `.venv\Scripts\activate`
2. Have `python app.py` ready to run (don't start it yet)
3. Optional: open `agent.py` or `planning.md` in the background if you want to reference the planning loop
4. Close unrelated tabs/notifications

**Recording tools:**
- Windows: `Win + G` → Capture → Record
- Mac: QuickTime → File → New Screen Recording
- Or OBS / Loom — any screen recorder works

---

## INTRO (0:00 – 0:20)

**[ON SCREEN: Desktop or README]**

**SAY:**
> "Hi, this is my FitFindr project for CodePath AI201. FitFindr is a multi-tool AI agent that helps you find secondhand clothes and figure out how to style them. It uses three tools — search listings, suggest outfit, and create fit card — orchestrated by a planning loop that decides what to call based on what each step returns."

**CHECKPOINT:** Name the three tools.

---

## PART 1 — Happy path, all 3 tools (0:20 – 2:00)

**[DO: In terminal, run:]**
```bash
python app.py
```

**[ON SCREEN: Browser opens to Gradio UI]**

**SAY:**
> "This is the Gradio interface. I'll search for something specific and walk through what the agent does at each step."

**[DO:]**
1. Make sure **Example wardrobe** is selected
2. Type: `vintage graphic tee under $30`
3. Click **Find it**
4. Wait for all three panels to fill in

**SAY:**
> "When I submit, the agent first parses my query with regex — it pulls out 'vintage graphic tee' as the description and thirty dollars as the max price. No LLM is used for parsing."

**[POINT TO: Top listing panel]**

**SAY:**
> "Step one is search_listings. It filters the mock dataset by price and size, scores results by keyword match, and picks the top listing. That result gets stored in session state as selected_item — I didn't have to re-enter it."

**[POINT TO: Outfit idea panel]**

**SAY:**
> "Step two is suggest_outfit. The agent passes that same selected item plus my example wardrobe into Groq. The LLM references pieces I actually own — like my baggy jeans and chunky sneakers — and suggests how to style the new find."

**[POINT TO: Fit card panel]**

**SAY:**
> "Step three is create_fit_card. It takes the outfit suggestion and the listing and generates a casual caption — the kind you'd post on Instagram after a thrift haul. All three values came from one session; the user never re-typed the item between steps."

**CHECKPOINT:** All 3 panels visible. You narrated search → outfit → fit card in order.

---

## PART 2 — State passing (2:00 – 2:40)

**[DO: Either keep Gradio open OR switch to terminal]**

**Option A — narrate over Gradio (easier):**

**SAY:**
> "To be clear on state passing: the listing in panel one is the exact dict that went into suggest_outfit. The outfit text in panel two is what went into create_fit_card. If I searched again, I'd get a fresh session — nothing carries over incorrectly."

**Option B — show terminal (stronger demo):**

**[DO: Open a second terminal tab, run:]**
```bash
python agent.py
```

**SAY:**
> "Running the agent from the command line shows the same flow. Here it prints the selected item title, the outfit suggestion, and the fit card — all from one session dict."

**CHECKPOINT:** You explicitly said state flows from search → outfit → fit card without re-entry.

---

## PART 3 — Failure handling (2:40 – 3:40)

**[ON SCREEN: Gradio UI]**

**SAY:**
> "Now I'll trigger a failure on purpose. If search returns nothing, the agent should stop and tell me what to try — it should NOT call the outfit or fit card tools."

**[DO:]**
1. Click the example query: `designer ballgown size XXS under $5`
   - OR type it manually
2. Click **Find it**

**[POINT TO: Panel 1 — error message]**

**SAY:**
> "Search returned zero results, so the agent set an error message and returned early. It tells me to broaden my keywords, raise my budget, or drop the size filter — not just 'no results found.'"

**[POINT TO: Empty panels 2 and 3]**

**SAY:**
> "Panels two and three are empty because suggest_outfit and create_fit_card were never called. That's the conditional branch in the planning loop — behavior changes based on what search returned."

**CHECKPOINT:** Error in panel 1 only. You explained why outfit/fit card were skipped.

---

## PART 4 — Bonus failure (optional, 3:40 – 4:20)

**Skip this if you're already at 4+ minutes.**

**[DO:]**
1. Select **Empty wardrobe (new user)**
2. Search: `vintage graphic tee under $30`
3. Click **Find it**

**SAY:**
> "One more failure mode: an empty wardrobe. suggest_outfit doesn't crash — it gives general styling advice instead of referencing specific owned pieces. The agent still completes the full pipeline and produces a fit card."

**CHECKPOINT:** Panel 2 shows general advice, not wardrobe-specific names.

---

## OUTRO (4:20 – 4:40)

**SAY:**
> "That's FitFindr — three tools, a conditional planning loop, session state between steps, and graceful error handling when search fails or the wardrobe is empty. Thanks for watching."

**[STOP RECORDING]**

---

## Quick checklist before submitting

- [ ] Video is 3–5 minutes
- [ ] Showed complete happy path (all 3 tools)
- [ ] Narrated state passing between tools
- [ ] Showed at least one failure (ballgown query recommended)
- [ ] Audio is audible; UI text is readable
- [ ] Repo is pushed to GitHub (without `.env`)

---

## Troubleshooting during recording

| Problem | Fix |
|---------|-----|
| Gradio won't start | Check `.env` has `GROQ_API_KEY`; run from `fitfindr` folder with venv active |
| Panels take a long time | Normal — LLM calls take 3–8 seconds; keep talking while it loads |
| Wrong item in panel 1 | Fine — explain scoring picks best keyword match under price cap |
| Groq rate limit | Wait 30 seconds and retry, or re-record the LLM portion |
