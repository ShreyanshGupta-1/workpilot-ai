# WorkPilot AI

WorkPilot AI is an agentic AI assistant that can answer questions, fetch 
real-time information via web search, retrieve answers from a personal 
knowledge base (resume + project documentation) using RAG, tell the current 
date and time, and perform simple text/math operations — using real 
tool-calling, multi-round reasoning, and persistent memory across 
conversations.

## Features
- Answers general questions using an LLM (Groq)
- Fetches real-time information from the web (web search tool)
- Retrieves answers from a personal knowledge base using Retrieval-Augmented 
  Generation (RAG) — supports both PDF and plain-text sources, with source 
  attribution (e.g. resume vs. project notes)
- Tells the current date and time
- Performs basic math (adds numbers)
- Counts words in a sentence
- Supports multi-round tool calling — the agent can call a tool more than 
  once per question if needed before giving a final answer
- Remembers conversation history across sessions (SQLite persistence)
- Supports multiple, isolated conversations via `conversation_id`
- Exposes the agent as a REST API (`/chat` endpoint) via FastAPI
- Lists available knowledge sources via a `/sources` endpoint
- Handles unknown/failed tool calls gracefully without crashing

## Tech Stack
- Python
- Groq API (LLM)
- FastAPI (web framework)
- Uvicorn (server)
- SQLite (database)
- Tavily API (web search)
- Pydantic (request validation)
- sentence-transformers (text embeddings for RAG)
- pypdf (PDF text extraction)

## Setup

1. Clone the repo

git clone https://github.com/ShreyanshGupta-1/workpilot-ai.git
cd workpilot-ai


2. Create and activate a virtual environment

python -m venv venv
venv\Scripts\activate


3. Install dependencies

pip install -r requirements.txt


4. Create a `.env` file in the project root with:

GROQ_API_KEY=your_groq_key_here
TAVILY_API_KEY=your_tavily_key_here


5. Add knowledge sources (optional)

   Place a resume or other documents in the `knowledge/` folder 
   (`.pdf` or `.txt` supported) for the RAG-based search tool to use.

6. Run the agent

   **Terminal chat version:**

python main.py


   **API version:**

uvicorn api:app --reload

   Then visit `http://127.0.0.1:8000/docs` to test the `/chat` and 
   `/sources` endpoints interactively.

## Roadmap
Planned future integrations (not yet built):
- Email (Gmail) integration
- Calendar integration
- GitHub integration
- Jira integration
- Support for additional chunking strategies per document type
