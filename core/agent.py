from dotenv import load_dotenv
import os
import truststore
truststore.inject_into_ssl()
from groq import Groq
import json
from tools.functions import get_current_time, add_numbers, word_count,web_search
from tools.schemas import tools
import sqlite3

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
conn = sqlite3.connect("conversations.db", check_same_thread=False)
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

def load_message():
    cursor.execute("select role, content from messages order by id")
    rows = cursor.fetchall()
    result = []
    for row in rows:
        role = row[0]
        content = row[1]
        if role == "tool" or (role == "assistant" and content.startswith("[requested tool:")):
            continue
        result.append({"role": role, "content": content})
    return result
res=load_message()
# print(res)
cursor.execute("SELECT * FROM messages")
print(cursor.fetchall())

available_tool = {
    "get_current_time": get_current_time,
    "add_numbers": add_numbers,
    "word_count": word_count,
    "web_search": web_search
}

def get_reply(text, messages):
    messages.append({"role": "user", "content": text})
    save_message("user", text)
    
    max_rounds = 5
    rounds = 0
    
    while True:
        rounds += 1
        if rounds > max_rounds:
            fallback = "I wasn't able to complete this after several attempts. Please try rephrasing your question."
            messages.append({"role": "assistant", "content": fallback})
            save_message("assistant", fallback)
            return fallback
        
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=messages,
            tools=tools
        )
        tool_calls = response.choices[0].message.tool_calls
        
        if tool_calls:
            call = tool_calls[0]
            tool_name = call.function.name
            tool_id = call.id
            tool_args = json.loads(call.function.arguments)

            try:
                result = available_tool[tool_name](**tool_args)
            except Exception as e:
                result = f"Error: the tool '{tool_name}' does not exist. Do not attempt to call it again — inform the user this action is not available."

            messages.append({
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "id": call.id,
                    "type": "function",
                    "function": {"name": call.function.name, "arguments": call.function.arguments}
                }]
            })
            save_message("assistant", f"[requested tool: {tool_name}]")
            
            messages.append({"role": "tool", "tool_call_id": tool_id, "content": str(result)})
            save_message("tool", str(result))
            
            # loop continues automatically — goes back to top, calls API again
            continue
        
        else:
            final_text = response.choices[0].message.content
            messages.append({"role": "assistant", "content": final_text})
            save_message("assistant", final_text)
            return final_text