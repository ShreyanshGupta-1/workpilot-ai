from dotenv import load_dotenv
import os
import truststore
truststore.inject_into_ssl()
from tavily import TavilyClient

load_dotenv()
client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
response = client.search("latest news about AI agents")
print(response)