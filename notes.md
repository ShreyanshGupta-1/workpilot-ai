## Day 2
- Built an interactive loop: system+user roles, live input, exit on "exit"/"quit"
- Bug: used `or` in exit check when I needed `and` — with `or`, at least one side is
  always True for any single string, so the loop never stopped
- Bug: exit check was placed after the API call — typing "exit" still triggered a
  wasted request. Fixed by moving the check right after input(), using `break`
  before the API call
- Learned: system role = behavior/tone, user role = actual question — both apply
  together on every request, not one-or-the-other


## Day 4
- Built full tool-calling loop: JSON schema for get_current_time, detecting 
  tool_calls, running the real function, sending result back, model replies
  in natural language
- Bug: defined tools/messages AFTER the code that used them — got NameError.
  Fixed by moving definitions above any function that references them.
- Bug: get_reply had no return statements — function returned None by default.
  Learned: Python functions return None automatically if they hit the end
  without a return.
- Bug: typo .messages instead of .message (twice) — AttributeError pointed
  me straight to the fix
- Bug: sent the raw `call` object back to the API in a new message — API
  rejected it (400 error, "tool_calls must be an array"). Learned: SDK
  response objects aren't automatically JSON-safe when reused in outgoing
  messages — had to manually rebuild {id, type, function:{name, arguments}}
  as a plain dict
- Understood: model never runs code itself — it only requests a tool via
  tool_calls; my code decides whether to actually run it

## Day 5
- Generalized tool-calling to handle multiple tools: added add_numbers (2 args)
  and word_count (1 arg) alongside get_current_time (0 args)
- Replaced hardcoded if-check with a dictionary lookup (available_tool),
  mapping tool names to real function objects, so adding new tools doesn't
  need new if statements
- Bug: json.load vs json.loads — used the file-reading version by mistake;
  json.loads() is for converting a string already in memory, which is what
  call.function.arguments is
- Learned: call.function.arguments arrives as a JSON-formatted STRING, not
  a real dictionary — had to convert it with json.loads() before using the
  values inside it
- Learned: ** unpacks a dictionary into named function arguments —
  available_tool[tool_name](**tool_args) works for any tool regardless of
  how many arguments it needs, without hardcoding argument names
- Bug: left "arguments": "{}" hardcoded in the assistant message even after
  adding real-argument tools — fixed by using the real call.function.arguments
  string, so the conversation history accurately reflects what was requested
- Bug: API rejected tool result message —

## Restructuring (post Day 6)
- Split main.py into: tools/functions.py (real tool functions), 
  tools/schemas.py (JSON tool descriptions), core/agent.py (client setup 
  + get_reply), main.py (just the loop now)
- Rule I learned: each file only imports what it directly uses — datetime 
  moved to functions.py since only get_current_time() needs it, not agent.py
- Learned: `from tools.functions import ...` resolves relative to where 
  you RUN the script from (project root, via main.py), not relative to 
  the file doing the importing (core/agent.py) — that's why it worked 
  even though agent.py isn't inside tools/
- Ran clean on first try after setup — good sign the import-resolution 
  concept was actually understood, not just guessed


## Day 7
- Built a real FastAPI server exposing the agent as a web API — a /chat POST 
  endpoint that wraps get_reply, on top of a working GET / test route
- Learned GET vs POST: GET is for visiting/retrieving (works by typing a URL 
  in the browser), POST is for sending data — can't be tested via the address 
  bar, needed FastAPI's /docs (Swagger UI) to actually construct and send a 
  POST request with a JSON body
- Learned BaseModel (pydantic): defines the expected shape of incoming JSON 
  so FastAPI can automatically validate and convert it into a usable Python 
  object inside the route function
- Bug: pip wasn't recognized in PowerShell — fixed with `python -m pip install`
  instead, sidesteps PATH issues
- Bug: "Attribute app not found in module" from uvicorn — turned out to be a 
  saved-file/naming mismatch, not a code bug
- Traced the full request flow: JSON in → FastAPI converts to a Python object 
  (via BaseModel) → my normal get_reply() code runs exactly as it does in the 
  terminal version → I return a plain dict → FastAPI converts it back to JSON 
  → sent back as the response. FastAPI only translates at the edges; the 
  actual agent logic in between is unchanged.
- Decided messages needs its own separate definition in test_api.py, not


## Day 8
- Added SQLite persistence: agent's conversation history now saves to
  conversations.db, surviving restarts
- Learned SQLite basics: connect() creates/opens a db file, cursor.execute()
  runs ONE SQL statement at a time (can't stack CREATE/INSERT/SELECT in one
  call), conn.commit() saves changes, cursor.fetchall() reads results back
- Used parameterized queries (? placeholders + tuple of values) instead of
  inserting variables directly into SQL strings — safer, avoids SQL injection
- Schema design decisions: kept it simple — id, role, content, timestamp
  (DEFAULT CURRENT_TIMESTAMP). Deliberately skipped conversation_id (only one
  conversation exists right now, no need yet) and skipped storing full
  tool_calls JSON structure (Option A: simple readable content, e.g.
  "[requested tool: get_current_time]" instead of the full nested object —
  some detail lost, but much simpler for now)
- Learned check_same_thread=False is needed for SQLite when used inside
  FastAPI, since requests can come from different threads
- Bug/design fix: database code needs to live in agent.py, not test_api.py,
  since that's where all the messages.append() calls (and thus save_message()
  calls) actually happen — same "define where it's used" lesson as Day 7
- Debugging story: saw unexplained duplicate "hello" rows (ids 1,2,9,10)
  interleaved with my real conversation (ids 3-8). Traced it back to a
  leftover hardcoded INSERT line in test_api.py from Part A testing — it
  fired every time I ran/reloaded that file, completely unrelated to my
  actual agent conversation via main.py. Lesson: a shared database file
  can be touched by multiple separate scripts, so row order reflects ALL
  writes, not just the one script I was focused on
- Removed the leftover scratch insert/select code from test_api.py

## Day 10
- Added web_search as the first real EXTERNAL tool — uses Tavily API, unlike
  earlier tools (get_current_time, add_numbers, word_count) which were all
  self-contained, no outside service involved
- Part A: tested Tavily standalone first (separate script), before touching
  the agent — same "prove it works in isolation first" discipline from Day 4
- Part B design decision: raw Tavily response is huge (8 results, each with
  title/url/content/score/id). Simplified to just title+url for top 2
  results, built into one readable string via a loop that accumulates a
  growing `summary` string
- Bug discovered in testing (Part C): model hallucinated specific dates,
  dollar figures ($3.1 billion), mission names — none of which were in the
  actual tool output (which only had title+url, no real content)
- Key learning: giving the model TOO LITTLE real data can make hallucination
  WORSE, not safer — the model still tries to give a complete-sounding
  answer, so it invents plausible details to fill the gap
- Fix: added truncated content (items["content"][:300]) alongside title/url,
  so the model has some real substance to anchor on, without sending an
  entire article's worth of text
- Result after fix: reduced hallucination (some real facts now correctly
  traced back to tool data) but did NOT eliminate it completely — model
  still occasionally blended real facts with invented ones
- Conclusion:

## Day 11

Goal
Reduce hallucination in web_search answers by tightening the system prompt.

Part A — Stricter system prompt
Updated the system message to explicitly say:

Only use facts present in tool output
Don't invent dates, numbers, names
If tool data is insufficient, say so honestly instead of guessing

Applied this in both main.py and test_api.py, since each file creates its own starting messages list.

Part B — Verified against ground truth, not just vibes
Didn't just trust that the new answer "looked better." Instead:

Added print(summary) inside web_search() to see the real tool output
Compared that raw output, word-for-word, against the model's final answer

Results — mixed, but real

✅ Some runs: details like "27 Starlink satellites" and "SLC-4E" were confirmed to genuinely come from the real tool data — prompt fix worked
❌ One run: model still said SpaceX "went public" and "delivered an earnings report" — factually wrong (SpaceX is private) — a different failure mode, not fixed by this prompt

Conclusion
Stricter prompting reduces hallucination, doesn't eliminate it. This matches Day 10's finding — hallucination is a fundamental LLM limitation, not something fully solvable with prompt/tool tweaks alone.

Part C — None bug investigated, not fixed

Traced likely cause: same pattern as Day 6 — when tool results are poor/irrelevant, model may request a tool again in the second API call
Current code only handles ONE round of tool-calling, so a second tool request means .content is None again
Decision: documented as a known edge case, not fixed today — doesn't crash the program, just an occasional bad reply. Proper fix (loop to handle multiple tool-call rounds) noted as future work, not urgent given today was meant to be a lighter day.


## Day 12 — Build Log

Goal
Fix the None bug from Day 11 — m
Part A — Understood the real gap

Old code checked tool_calls only on the first API call
Second API call just grabbed .content directly, assuming it was always plain text
If the model requested a tool again on the second call, .content was None (same rule as always — None content only happens when tool_calls is filled in instead)
Root cause traced to Day 11 data: model got a poor/irrelevant search result, likely decided to search again with a refined query

Key concept clarified

None doesn't mean "model doesn't know" — it means "model is requesting a tool in this response"
Model decides in a single step, per call: either answer directly, or request a tool — never both, never neither
This decision is independent each round — a fresh call can go either way based on what's in messages so far

Part B — Rebuilt get_reply as a loop

Replaced the fixed "call once, maybe call twice" structure with while True:
Each iteration: call API → check tool_calls → if present, run tool + save results + continue (loop again) → if not, return the text reply
Same tool-running logic as before, just now reusable every round instead of duplicated once

Part C — Added a safety limit

max_rounds = 5 — prevents infinite looping if the model keeps requesting tools indefinitely
Falls back to a clear message ("wasn't able to complete this after several attempts") if exceeded

Part D — Tested and confirmed

Re-ran the SpaceX question that previously produced None — no crash this time, loop handled a second tool request cleanly
Verified the final answer against the actual tool result in the database — content matched exactly, confirming both the loop fix and Day 11's stricter prompt are working together correctly

New minor issue spotted (not fixed today)

[:300] character truncation sometimes cuts content mid-sentence (e.g. "Microsoft Reports Over $130 Billion in New D...") — cosmetic issue, noted for future polish, not urgent