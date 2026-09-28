from dotenv import load_dotenv
import os
import re
import inspect
import truststore
truststore.inject_into_ssl()
from groq import Groq
import json
from tools.functions import (
    get_current_time, add_numbers, word_count, web_search,
    send_email, create_event, create_github_issue, create_jira_issue,
)
from tools.schemas import tools
import sqlite3
from tools.rag import search_document

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
conn = sqlite3.connect("conversations.db", check_same_thread=False)
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
# One pending action per conversation. INSERT OR REPLACE keeps it that way.
cursor.execute("""
    CREATE TABLE IF NOT EXISTS pending_actions (
        conversation_id TEXT PRIMARY KEY,
        tool_name TEXT,
        args_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")
conn.commit()


def save_message(conversation_id, role, content):
    cursor.execute(
        "INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)",
        (conversation_id, role, str(content))
    )
    conn.commit()


MAX_HISTORY_MESSAGES = 12

def load_message(conversation_id, limit=MAX_HISTORY_MESSAGES):
    cursor.execute(
        """
        SELECT role, content FROM messages
        WHERE conversation_id = ?
          AND role != 'tool'
          AND NOT (role = 'assistant' AND content LIKE '[requested tool:%')
          AND NOT (role = 'assistant' AND content LIKE '%Reply ''yes'' to confirm%')
          AND NOT (role = 'assistant' AND content LIKE 'Done. %')
          AND NOT (role = 'assistant' AND content LIKE 'Okay, I cancelled%')
        ORDER BY id DESC
        LIMIT ?
        """,
        (conversation_id, limit),
    )
    rows = cursor.fetchall()[::-1]  # back to oldest-first
    result = [{"role": r[0], "content": r[1]} for r in rows]
    while result and result[0]["role"] != "user":
        result.pop(0)
    return result


available_tool = {
    "get_current_time": get_current_time,
    "add_numbers": add_numbers,
    "word_count": word_count,
    "web_search": web_search,
    "search_document": search_document,
    "send_email": send_email,
    "create_event": create_event,
    "create_github_issue": create_github_issue,
    "create_jira_issue": create_jira_issue,
}


# ---------- Confirmation gate ----------

# Tools with real-world, irreversible effects. They never run without an explicit "yes".
ACTION_TOOLS = {
    "send_email": "Send an email",
    "create_event": "Create a calendar event",
    "create_github_issue": "Create a GitHub issue",
    "create_jira_issue": "Create a Jira ticket",
}
CONFIRM_WORDS = {"yes", "y", "confirm", "confirmed", "yes confirm", "yes please", "go ahead", "do it"}
CANCEL_WORDS = {"no", "n", "cancel", "stop", "dont", "dont do it", "no cancel"}
PENDING_MINUTES = 10


def normalize(text):
    """'Yes!' -> 'yes'. Exact matching only, so partial answers never count as a confirmation."""
    return " ".join(re.sub(r"[^a-z ]", "", text.lower()).split())


def save_pending(conversation_id, tool_name, tool_args):
    cursor.execute(
        "INSERT OR REPLACE INTO pending_actions (conversation_id, tool_name, args_json) VALUES (?, ?, ?)",
        (conversation_id, tool_name, json.dumps(tool_args)),
    )
    conn.commit()


def get_pending(conversation_id):
    """Returns (tool_name, args) if there is a pending action younger than PENDING_MINUTES."""
    cursor.execute(
        "SELECT tool_name, args_json FROM pending_actions "
        "WHERE conversation_id = ? AND created_at >= datetime('now', ?)",
        (conversation_id, f"-{PENDING_MINUTES} minutes"),
    )
    row = cursor.fetchone()
    if not row:
        return None
    return row[0], json.loads(row[1])


def clear_pending(conversation_id):
    cursor.execute("DELETE FROM pending_actions WHERE conversation_id = ?", (conversation_id,))
    conn.commit()


def args_are_valid(tool_name, tool_args):
    """True if the arguments fit the tool's signature. Checked before asking the user to confirm."""
    try:
        inspect.signature(available_tool[tool_name]).bind(**tool_args)
        return True
    except (KeyError, TypeError):
        return False


def format_confirmation(tool_name, tool_args):
    lines = [f"{ACTION_TOOLS[tool_name]}? Here is exactly what will be done:", ""]
    for key, value in tool_args.items():
        lines.append(f"- {key}: {value}")
    lines.append("")
    lines.append("Reply 'yes' to confirm. Any other message cancels this action.")
    return "\n".join(lines)


def run_tool(tool_name, tool_args):
    """Runs a tool. Returns (ok, text)."""
    if tool_name not in available_tool:
        return False, f"the tool '{tool_name}' does not exist"
    try:
        return True, str(available_tool[tool_name](**tool_args))
    except Exception as e:
        return False, f"the tool '{tool_name}' failed: {e}"


def finish(conversation_id, messages, text):
    messages.append({"role": "assistant", "content": text})
    save_message(conversation_id, "assistant", text)
    return text


# ---------- Main agent loop ----------

def get_reply(conversation_id, text, messages):
    messages.append({"role": "user", "content": text})
    save_message(conversation_id, "user", text)

    # 1) Is the user answering a pending confirmation?
    pending = get_pending(conversation_id)
    if pending:
        tool_name, tool_args = pending
        clear_pending(conversation_id)  # usable once only, even if the tool then fails
        answer = normalize(text)
        if answer in CONFIRM_WORDS:
            ok, result = run_tool(tool_name, tool_args)
            reply = f"Done. {result}" if ok else f"That action failed: {result}"
            return finish(conversation_id, messages, reply)
        if answer in CANCEL_WORDS:
            return finish(conversation_id, messages, "Okay, I cancelled that action.")
        # Any other message drops the old request and is handled as a new one below.
    if not pending and normalize(text) in (CONFIRM_WORDS | CANCEL_WORDS):
        return finish(conversation_id, messages,
                      "There's nothing waiting for confirmation right now. What would you like me to do?")
    max_rounds = 5
    rounds = 0

    while True:
        rounds += 1
        if rounds > max_rounds:
            return finish(conversation_id, messages,
                          "I wasn't able to complete this after several attempts. Please try rephrasing your question.")

        try:
            response = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=messages,
                tools=tools
            )
        except Exception as e:
            print(f"MODEL CALL ERROR: {type(e).__name__}: {e}")
            return finish(conversation_id, messages,
                          "Sorry, I couldn't process that request. Please try rephrasing it.")

        tool_calls = response.choices[0].message.tool_calls

        if tool_calls:
            call = tool_calls[0]
            tool_name = call.function.name
            tool_id = call.id
            tool_args = json.loads(call.function.arguments)

            # 2) Irreversible action with valid arguments: stop and ask first.
            if tool_name in ACTION_TOOLS and args_are_valid(tool_name, tool_args):
                save_pending(conversation_id, tool_name, tool_args)
                return finish(conversation_id, messages, format_confirmation(tool_name, tool_args))

            # 3) Everything else runs immediately. Bad action arguments also land here and
            #    fail harmlessly at the call, so the model sees the error and can correct it.
            ok, result = run_tool(tool_name, tool_args)
            if not ok:
                result = f"Error: {result}. Do not retry — tell the user what went wrong."

            messages.append({
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "id": call.id,
                    "type": "function",
                    "function": {"name": call.function.name, "arguments": call.function.arguments}
                }]
            })
            save_message(conversation_id, "assistant", f"[requested tool: {tool_name}]")

            messages.append({"role": "tool", "tool_call_id": tool_id, "content": result})
            save_message(conversation_id, "tool", result)
            continue

        reply = response.choices[0].message.content or ""
        # The model asked for confirmation in plain text instead of calling the tool.
        # Nothing is pending, so a "yes" would go nowhere. Say so honestly.
        if re.search(r"reply .?yes.? to confirm|need your confirmation", reply, re.IGNORECASE):
            reply = ("I couldn't prepare that action. Please state the full request again, "
                     "for example: send an email to <address> with subject \"...\" and body \"...\".")
        return finish(conversation_id, messages, reply)