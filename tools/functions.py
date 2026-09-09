import datetime
from dotenv import load_dotenv
import os
from tavily import TavilyClient
load_dotenv()
def get_current_time():
    now = datetime.datetime.now()
    return now.strftime("%d/%m/%y %H:%M:%S")

def add_numbers(number1, number2):
    result = number1 + number2
    return result

def word_count(text):
    result = text.split(" ")
    return len(result)

def web_search(query):
    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    response = client.search(query)
    results=response["results"]
    top_result=results[:2]
    summary=""
    for items in top_result:
        title = items["title"]
        url = items["url"]
        content = items["content"][:300]
        summary = summary + f"{title} ({url})\n{content}\n\n"
    print(summary)
    return summary
