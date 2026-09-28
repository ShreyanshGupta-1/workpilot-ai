## Live results: both passed

- **Math:** answered normally, so the history cap didn't break ordinary requests.
- **Jira:** returned a 200 with a plain-language reply: *"I couldn't create the Jira ticket because the necessary Jira credentials aren't set up in this environment."* That was the best outcome I listed.

The same request returned a raw 500 earlier, so the safety net and lazy loading both work on the live app. The action tools fail cleanly on Render, as intended, since `/chat` has no authentication yet.

## README update

Replace the whole README with this:

```markdown
# WorkPilot AI

WorkPilot AI is an agentic AI assistant that answers questions, searches the web, retrieves answers from a personal knowledge base (RAG), and takes real actions: sending email, scheduling calendar events, creating GitHub issues, and creating Jira tickets. It uses tool-calling with multi-round reasoning and remembers conversations across sessions.

## Live Demo
Try it here: https://workpilot-ai-xumd.onrender.com/docs

Notes on the hosted demo:
- It runs on a free tier and spins down after inactivity. In testing, the first request after inactivity took about 2 minutes, because the app re-computes its knowledge base embeddings at startup. Later requests are fast.
- **The action tools (email, calendar, GitHub, Jira) are disabled on the live demo.** The `/chat` endpoint has no authentication, so I deliberately did not put credentials on the server. If you ask for one of these actions, the agent replies that credentials aren't set. Everything else works: time, math, word count, web search, and knowledge-base questions.
- Conversation history is stored in SQLite on ephemeral storage, so it can reset when the server restarts.

## Features
- Answers general questions using an LLM (Groq)
- Fetches real-time information from the web (Tavily)
- Answers questions from a personal knowledge base using RAG, with PDF and text sources and source attribution
- **Sends email** through the Gmail API (OAuth2)
- **Creates calendar events** through the Google Calendar API, resolving relative dates like "tomorrow at 3pm"
- **Creates GitHub issues** through the GitHub API
- **Creates Jira tickets** through the Jira API
- Tells the current date and time, performs basic math, counts words
- Multi-round tool calling: the agent can call several tools in one turn
- Persistent memory in SQLite, with isolated conversations via `conversation_id`
- Only the most recent messages are sent to the model, to stay within token limits
- REST API with `/chat`, `/sources` and `/history/{conversation_id}` endpoints
- Failed or unknown tool calls, and rejected model calls, return a friendly message instead of crashing
- Tools that need credentials load them lazily, so a missing credential disables only that tool

## Tech Stack
- Python
- Groq API (LLM)
- FastAPI, Uvicorn, Pydantic
- SQLite
- Tavily API (web search)
- Google Gemini API (embeddings for RAG)
- pypdf (PDF text extraction)
- Gmail API and Google Calendar API (OAuth2)
- PyGithub
- python-jira
- Render (deployment)

## Setup

1. Clone the repo
   ```
   git clone https://github.com/ShreyanshGupta-1/workpilot-ai.git
   cd workpilot-ai
   ```

2. Create and activate a virtual environment
   ```
   python -m venv venv
   venv\Scripts\activate
   ```

3. Install dependencies
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root:
   ```
   GROQ_API_KEY=your_groq_key
   TAVILY_API_KEY=your_tavily_key
   GEMINI_API_KEY=your_gemini_key
   GITHUB_TOKEN=your_github_token
   JIRA_EMAIL=your_atlassian_email
   JIRA_API_TOKEN=your_jira_api_token
   JIRA_DOMAIN=yoursite.atlassian.net
   ```
   The GitHub and Jira variables are only needed for those tools.

5. Set up Google access (only for the email and calendar tools)
   - In Google Cloud Console, enable the Gmail API and Google Calendar API
   - Create an OAuth client (Desktop app) and save it as `credentials.json` in the project root
   - Add your Google account as a test user on the OAuth consent screen
   - On first use, a browser window asks for consent and creates `token.json`

6. Add knowledge sources (optional)

   Put `.pdf` or `.txt` files in `knowledge/`. The app still starts if the resume file is missing.

7. Run it

   Terminal chat:
   ```
   python main.py
   ```
   API:
   ```
   uvicorn api:app --reload
   ```
   Then open `http://127.0.0.1:8000/docs`.

## Known Limitations
- `/chat` has no authentication, so the action tools should stay off on any public deployment
- Knowledge base embeddings are computed at startup rather than cached, which slows cold starts
- The calendar timezone (Asia/Kolkata) and the default Jira project key are hardcoded
- Conversation memory is capped to recent messages; older history stays in the database but is not sent to the model

## Roadmap
- API key authentication for `/chat`, then enabling the action tools on the hosted demo
- Cache embeddings to speed up startup
- Persistent hosted database instead of ephemeral SQLite
- Reading tools: inbox, calendar, and Jira and GitHub queries
- Confirmation step before irreversible actions
```

## Commit the README

```
git add README.md
git commit -m "Update README with action tools, live-demo limits, and setup"
git push
```

Check `git status` first. Only `README.md` and `notes.md` should show.

