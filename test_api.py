from fastapi import FastAPI
from pydantic import BaseModel, Field
from core.agent import get_reply,load_message
import sqlite3
conn = sqlite3.connect("conversations.db")
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        role TEXT,
        content TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")
conn.commit()
def save_message(role, content):
    cursor.execute(
        "INSERT INTO messages (role, content) VALUES (?, ?)",
        (role, str(content))
    )
    conn.commit()

cursor.execute("SELECT * FROM messages")
print(cursor.fetchall())
app = FastAPI()
messages=[
    {"role": "system", "content": "you are a datetime assistant. Respond to the user question and use tools if needed to answer the query. When using tool results, only state facts that are explicitly present in the tool's output — do not invent or guess specific details like dates, numbers, or names that were not given to you. If the tool result doesn't contain enough detail to fully answer the question, say so honestly instead of making something up."}
]+load_message()
@app.get("/")
def read_root():
    return {"message": "hello"}
class chat(BaseModel):
    title: str



@app.post("/chat")
def create_chat(chat:chat):
    reply = get_reply(chat.title, messages)
    return{
        "message":"chat stored",
        "reply":reply 
    }