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


## Day 14 — Build Log

Goal
Support multiple, isolated conversations instead of one shared messages/database history for everyone.

Part A — Schema migration

Chose ALTER TABLE over delete/recreate — more realistic, production-style approach
Added conversation_id TEXT column via ALTER TABLE messages ADD COLUMN conversation_id TEXT
Discovered along the way: timestamp column was never actually present either (original CREATE TABLE IF NOT EXISTS ran once, early on, before timestamp DEFAULT CURRENT_TIMESTAMP was added to the code — so it silently never took effect on the real table). Fixed with a second ALTER TABLE.
Verified structure with PRAGMA table_info(messages) instead of guessing from row output
Removed the one-time migration lines after running them once (no IF NOT EXISTS safety net on ALTER TABLE — running twice would error)

Key learning: CREATE TABLE IF NOT EXISTS only creates a table if it's missing — later changes to that SQL in code don't retroactively apply to an already-existing table.

Part B — Updated core functions in agent.py

save_message(conversation_id, role, content) — now stores which conversation each row belongs to
load_message(conversation_id) — now filters with WHERE conversation_id = ?, so old rows (with conversation_id = None) never leak into a new, real conversation
get_reply(conversation_id, text, messages) — now threads conversation_id through every internal save_message call

Part C — Wired through both entry points

main.py: uses a fixed conversation_id = "terminal_session" — reasoning: it's always one person, one continuous session, so no real need for a different ID each time. The fixed value exists purely to satisfy the shared function signature, not because main.py itself needs multi-conversation support.
test_api.py: conversation_id comes from the incoming request (chat.conversation_id) — genuinely dynamic, since different callers need genuinely separate histories
messages is now built fresh, inside the /chat endpoint per request, instead of once at file startup

Two real bugs found and fixed during this step:

Leftover res = load_message() debug line still sitting at the top level of agent.py from Day 9 — broke on startup once load_message required an argument. Same root cause as Day 8's ghost "hello" rows: leftover top-level code silently running on every import/run.
Duplicate save_message function accidentally left in test_api.py — never actually called (since get_reply already calls the real one in agent.py), but risked silently diverging from the real version if ever edited separately. Deleted.

Part D — Real test, not just code review
Sent 3 requests through /docs:

conversation_id: "test_user_1" — "my name is Shreyansh"
conversation_id: "test_user_2" — "what is my name" → correctly did NOT know (separate conversation)
conversation_id: "test_user_1" — "what is my name" → correctly answered "Shreyansh"

Confirmed: conversation isolation genuinely works.


## Day 15 — Build Log

Goal
Learn and implement the core mechanism behind RAG (Retrieval-Augmented Generation) — chunking, embeddings, and similarity search — as a standalone proof of concept before integrating it into the agent.

Part A — Concept understood first, before any code

Problem: pasting an entire document into every request is expensive, slow, and makes it harder for the model to find what's relevant
RAG's fix: break document into chunks → embed each chunk → embed the question → find the most similar chunk(s) via cosine similarity → send only those to the model
Key distinction clarified: the similarity score doesn't answer the question — it just identifies which chunk is worth showing the model; the model still does the actual reasoning

What an embedding actually is

Not "so the computer understands text" (computers already process text as data)
Correct framing: a list of numbers where texts with similar meaning end up with similar numbers, even with completely different wording (e.g. "cat sat on the mat" vs "feline rested on the rug")

Part B — Got embeddings working standalone

Used sentence-transformers (all-MiniLM-L6-v2) — runs locally, free, no API key
First run downloaded the model (~91MB, one-time, slow on this hardware — expected, not a bug)
Confirmed: any input text → 384-number embedding, always the same size regardless of input length
Learned: fixed embedding size is what makes comparison between different texts possible later (cosine similarity needs equal-length vectors)

Part C — Chunked a real document + embedded each piece

Wrote a 3-fact test document (about self, WorkPilot, and Earth — deliberately unrelated topics to make similarity testing clear)
Split into chunks using .split("\n") — same .split() method from word_count, applied differently
model.encode(chunks) embedded all chunks at once (list in, list of embeddings out — no loop needed)
Verified len(chunks) == len(chunk_embeddings) before trusting the result

Part D — Similarity search, tested and verified

Used util.cos_sim(question_embedding, chunk_embeddings) to score each chunk against a test question
Question: "what programming language is used in this project?"
Result: correctly matched the WorkPilot/Python chunk (score 0.59) over the unrelated Bennett University chunk (0.29) and Earth chunk (0.10)
Notable: the question never said "Python" — it matched on meaning ("programming language" ≈ "Python is used as..."), not exact keyword overlap — real proof embeddings capture semantic meaning, not literal text matching

Outcome
Built the full RAG mechanism end-to-end, standalone: chunk → embed → compare → retrieve. Not yet integrated into the actual agent (get_reply) — that's a natural next step for a future day, once this foundation is solid.


## ## Day 16 — Build Log

**Goal**
Turn yesterday's standalone RAG mechanism into a real tool the agent can call during conversation.

---

**Part A — Moved RAG logic into a reusable module (`tools/rag.py`)**
- Model loading, document chunking, and embedding generation all happen **once**, at import time — not on every tool call
- `search_document(query)` reuses the pre-computed `chunk_embeddings`, so each call is fast
- Wrote a 6-fact document (about self + WorkPilot's features/architecture) — deliberately distinct topics so similarity search has something meaningful to differentiate
- Used `if __name__ == "__main__":` to keep test code from running on import — new pattern learned today, useful for separating "test this file directly" from "this file gets imported elsewhere"
- Verified standalone first, same discipline as every previous tool (Day 4, Day 10): prove it works in isolation before wiring it in

**Part B — Added as a real tool**
- Wrote schema for `search_document` in `tools/schemas.py`
- Key lesson on `description` writing: a tool's `description` should say *when to use this tool*, not act like a system prompt — and the `query` parameter's own description should be short, just describing what goes in that one field, not repeat the whole tool description
- Deliberately scoped this tool's description narrowly ("questions about Shreyansh or WorkPilot AI") so it doesn't overlap or compete with `web_search`'s territory (current events) — clear separation between tools matters for the model choosing correctly
- Added `search_document` to `available_tool` in `agent.py`

**Part C — Tested through the real agent**
- Asked "which tech stack am I using in WorkPilot AI" through `main.py`
- Model correctly selected `search_document` (not `web_search`, not general knowledge) and answered accurately from the document

**Bugs hit and fixed along the way**
- `get_reply(text, messages)` in `main.py` was missing the `conversation_id` argument — same bug pattern as Day 14, caught and fixed manually
- Leftover full-table `print(cursor.fetchall())` debug line, still running on every startup since Day 8/9 — finally removed
- `CREATE TABLE` SQL text was out of sync with the real (already-migrated) table structure — updated to include `conversation_id` and `timestamp` for code accuracy, without needing to re-run `ALTER TABLE` (table already had these columns from Day 14's migration)

---

**Outcome**
Agent now has 5 working tools: `get_current_time`, `add_numbers`, `word_count`, `web_search` (live, external), and `search_document` (RAG, static knowledge). This is a genuine multi-tool agent with both real-time and static-knowledge retrieval capabilities — a meaningful milestone for the project.

## Day 17 — Build Log

Goal
Move RAG from a hardcoded string to a real file, and handle realistic document quirks (long facts, blank lines).

Part A — Read from a real file

Created knowledge/about.txt, moved the hardcoded document there
Used with open(...) as f: to read it — automatically closes the file even if an error occurs
Confirmed identical behavior to the hardcoded version — same chunks, same search results

Part B — Handled realistic document issues

Multi-sentence facts: confirmed (not "fixed" — nothing needed fixing) that a long fact spanning multiple sentences stays as ONE chunk, as long as there's no literal Enter key press in the middle. Visual line-wrapping on screen ≠ an actual newline character in the file — these are different things, and .split("\n") only reacts to the real character.
Blank lines: found a real bug — a blank line in the file produced an empty string chunk (''). Fixed with a filter: chunks = [chunk for chunk in chunks if chunk.strip() != ""]

Part C — Real bug found and diagnosed using debug prints, not guessing

Asked a question with a typo ("reg" instead of "RAG") — got a wrong, unhelpful answer
Added targeted debug prints in both agent.py (which tool got called) and rag.py (which chunk got retrieved, and with what query)
Traced the exact cause: the embedding for the typo "reg" ended up closest to an unrelated chunk (FastAPI/REST), since "reg" carries no real meaning to match against
Re-tested with the typo fixed — correct chunk retrieved, accurate answer generated
Key finding: this wasn't a code bug — it was a genuine demonstration of a known RAG limitation: query quality directly affects retrieval quality. Every other part of the pipeline (tool selection, chunking, similarity search, embedding) worked correctly throughout; only a flawed query led to a flawed result.

Outcome
RAG pipeline is now file-based, handles blank lines correctly, and has been genuinely stress-tested — including finding and correctly diagnosing a real retrieval failure caused by query ambiguity, not a code defect.

Good — that confirms Part D. Let's finish up.

**Before logging — quick cleanup reminder:** go remove those `DEBUG:` print statements from `agent.py` and `rag.py` now that everything's verified working. They've done their job.



## Day 18 — Build Log

**Goal**
Improve `search_document` to retrieve multiple relevant chunks instead of just one, and avoid misleading answers on unrelated questions.

---

**Part A — Top-3 retrieval**
- Replaced `scores.argmax()` (single best match) with `scores.topk(3)`
- Learned `topk` returns a named object with `.values` (scores, sorted highest first) and `.indices` (positions in the original list)
- Bug found: forgot to add a `return` statement while experimenting with the new logic — function fell through and returned `None` by default (same Python rule from Day 3-4, resurfaced in a new context)

**Part B — Combined results into one readable string**
- Looped through `top_results.indices`, built a combined string with blank lines between chunks — same pattern as `web_search`'s summary-building loop

**Part C — Similarity threshold**
- Tested real scores side by side: relevant question ≈ 0.27, unrelated question ("capital of France") ≈ 0.06
- Chose threshold of `0.15` — roughly midway, comfortable margin on both sides
- Verified both directions: relevant questions still return real chunks; unrelated questions now return "No relevant information found" instead of a misleading low-quality match
- Key insight: absolute similarity scores for this model/document are naturally low (never near 1.0) — what matters is the *relative gap* between relevant and irrelevant queries, not any fixed "good" number in isolation

**Part D — Tested through full agent**
- Confirmed `main.py` still produces clean, accurate answers with the new multi-chunk retrieval

---

**Outcome**
RAG tool now retrieves multiple relevant pieces of context instead of a single chunk, and gracefully declines to answer when nothing in the document is actually relevant — a more robust, production-realistic retrieval behavior.


## Day 19 — Build Log (Complete)

Goal
Extend RAG to support real PDF documents. Ended up being a much deeper, multi-part investigation than originally scoped — genuinely valuable.

Part A — PDF text extraction

Used pypdf's PdfReader, joined all pages into one full_text block
Observed real extraction messiness on the research paper: ligature issues, mid-sentence line breaks, author/citation metadata mixed into flow

Part B — First chunking strategy: sentence-based (for the research paper)

Replaced line-based .split("\n") with regex sentence-splitting: re.split(r'(?<=[.!?]) ', full_text)
Learned regex lookbehind (?<=...): splits after a match without discarding it
Fixed a real bug: replacing \n with spaces before splitting caught additional real sentence boundaries (195 → 296 chunks)
Documented known limitations honestly: abbreviations like "N." get misread as sentence-ends; messy title/author-block chunk

Part C — Wired in, found and fixed a real bug

Tool description was stale after swapping .txt → PDF — model correctly (given outdated info) avoided the tool, defaulting to web_search
Fixed by updating the description to match the new content

The deeper investigation — tool-selection inconsistency

After the description fix, search_document worked for one question but not others, even when rephrased closely
Root cause: the research paper is extremely well-documented publicly — web_search could always plausibly answer too, so the model inconsistently chose between two valid-seeming tools
Key learning: not every problem has a fixable root cause — LLM tool selection is probabilistic, not deterministic; a stronger, more assertive description helped but didn't guarantee consistency
Isolated the problem correctly using standalone testing (search_document alone, bypassing the model) — confirmed retrieval itself was always working correctly; the inconsistency was purely in the model's choice, not the code

The real fix — switched to a private document (resume) instead

Reasoning: RAG's actual use case is private/unsearchable content — web_search has nothing to compete with for a resume, removing the ambiguity entirely
This is closer to how RAG is used in real production systems (internal docs, personal notes) than competing with public knowledge

Discovered chunking must match document structure — found and fixed 2 more real bugs

Sentence-based splitting failed badly on the resume (headers/bullets have little punctuation) — produced one giant blob
Bug: leftover full_text.replace("\n", " ") line destroyed newlines needed for the new split — len(chunks) collapsed to 1
Fixed: removed that line, joined pages with \n instead of space, switched to paragraph-based splitting: re.split(r'\n\s*\n', full_text)
Result: 8 meaningful chunks — each project's title+link+description stayed together as one coherent unit
Updated tool description again, now describing resume content specifically

Verified through the real agent — accurate, correctly-grounded answers about actual projects and tech stack, tool called reliably every time (no more competition with web_search)

Final review — found one more real chunking imperfection, documented not fixed

"EDUCATION DETAILS" heading ended up isolated from its actual data (CGPA, university, dates), which got merged into the Certifications chunk instead — likely due to page layout (heading and data physically separated in the PDF)
Noted as a real, known limitation: chunking based on blank-line structure can occasionally separate a heading from its content when a document's layout doesn't place them adjacently

Overall outcome
Built genuine understanding of three different chunking strategies (line-based, sentence-based, paragraph-based) and when each one applies, based on real trial and error across three different document types. Discovered and correctly diagnosed a genuine LLM tool-selection limitation, distinct from a code bug. This was the most investigation-heavy day of the project so far — multiple real, layered bugs found and fixed through systematic, evidence-based debugging rather than guessing.


## Day 20 — Build Log

**Goal**
Extend `search_document` to search across multiple knowledge sources (resume + about.txt) instead of just one, with source tracking.

---

**Part A — Design thinking first**
- Core problem: combining chunks from multiple documents into one list loses track of where each chunk came from
- Solution: a **parallel list** (`chunk_sources`) — same length, same order as `chunks`, where `chunks[i]` and `chunk_sources[i]` always describe the same chunk
- Reasoned through two failure modes of parallel lists getting out of sync: a **length mismatch** crashes loudly (`IndexError`), while a **misalignment** (same length, wrong pairing) fails silently — the more dangerous case, since it produces confidently wrong source attribution with no error at all

**Part B — Built reusable loader functions**
- `load_and_chunk_pdf(filepath)` and `load_and_chunk_txt(filepath)` — same chunking logic as before, just wrapped as reusable functions instead of one-off inline code
- Combined both sources: `all_chunks = resume_chunks + about_chunks`, `all_sources = (["resume"] * len(resume_chunks)) + (["about"] * len(about_chunks))`
- Caught and fixed a real bug during the refactor: had two separate, duplicate blocks doing the same PDF-loading (one via the new function, one still using old inline code) — cleaned up to a single source of truth
- Caught a second real bug: `chunk_embeddings` was still built from the old, resume-only variable after combining sources — fixed by rebuilding it from `all_chunks`

**Part C — Source labels in results**
- `search_document` now prefixes each returned chunk with `[Source: resume]` or `[Source: about]`

**Part D — Tested with real evidence**
- Confirmed both sources retrievable through one combined tool — resume questions correctly pulled resume chunks, WorkPilot questions correctly pulled about.txt chunks
- One answer initially looked incomplete (missing some tools) — investigated with a debug print rather than assuming a bug
- **Key finding:** the underlying retrieval was correct and identical both times (same query → same chunks, deterministic); the inconsistency was purely in the model's final summarization step, which isn't fully deterministic
- Reinforced a general debugging principle: check the actual underlying data before assuming a code bug when a final LLM-generated answer looks off — retrieval and generation are two different layers with different reliability characteristics

---

**Outcome**
`search_document` now searches across multiple knowledge sources with accurate origin tracking, tested and confirmed working for both PDF and plain-text sources combined in a single tool.


