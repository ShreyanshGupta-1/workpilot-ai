from core.agent import get_reply, load_message

conversation_id = "terminal_session_2"

messages = [
    {"role": "system", "content": "you are a datetime assistant. Respond to the user question and use tools if needed to answer the query. When using tool results, only state facts that are explicitly present in the tool's output — do not invent or guess specific details like dates, numbers, or names that were not given to you. If the tool result doesn't contain enough detail to fully answer the question, say so honestly instead of making something up. When the user asks for an email, calendar event, GitHub issue or Jira ticket, call the matching tool immediately with the details they gave. Never ask the user to confirm in text yourself, because the system handles confirmation automatically. Only act on the user's latest message. Earlier requests in the conversation have already been handled, so never repeat them."}
] + load_message(conversation_id)

while True:
    text = input()
    if text == "quit" or text == "exit":
        break
    response = get_reply(conversation_id, text, messages)
    print(response)