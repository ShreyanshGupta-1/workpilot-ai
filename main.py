from core.agent import get_reply,cursor, conn, load_message

messages = [
    {"role": "system", "content": "you are a datetime assistant. Respond to the user question and use tools if needed to answer the query. When using tool results, only state facts that are explicitly present in the tool's output — do not invent or guess specific details like dates, numbers, or names that were not given to you. If the tool result doesn't contain enough detail to fully answer the question, say so honestly instead of making something up."}
]+load_message()

while True:
    text = input()
    if text == "quit" or text == "exit":
        break
    response = get_reply(text, messages)
    print(response)