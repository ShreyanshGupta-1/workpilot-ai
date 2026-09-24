from fastapi import FastAPI
from pydantic import BaseModel, Field
from core.agent import get_reply, load_message
from tools.rag import all_sources
import sqlite3


conn = sqlite3.connect("conversations.db")
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id TEXT,
        role TEXT,
        content TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")
conn.commit()

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "hello"}

class chat(BaseModel):
    title: str
    conversation_id: str

@app.post("/chat")
def create_chat(chat: chat):
    messages = [
        {"role": "system", "content": "you are a datetime assistant. Respond to the user question and use tools if needed to answer the query. When using tool results, only state facts that are explicitly present in the tool's output — do not invent or guess specific details like dates, numbers, or names that were not given to you. If the tool result doesn't contain enough detail to fully answer the question, say so honestly instead of making something up."}
    ] + load_message(chat.conversation_id)
    
    reply = get_reply(chat.conversation_id, chat.title, messages)
    return {
        "message": "chat stored",
        "reply": reply
    }

@app.get("/sources")
def list_sources():
    unique_sources = list(set(all_sources))
    return {"available_sources": unique_sources}


@app.get("/history/{conversation_id}")
def get_history(conversation_id: str):
    history = load_message(conversation_id)
    return {"conversation_id": conversation_id, "messages": history}