tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "get current datetime of the location",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_numbers",
            "description": "get addition of two numbers",
            "parameters": {
                "type": "object",
                "properties": {
                    "number1": {"type": "number", "description": "first number"},
                    "number2": {"type": "number", "description": "second number"}
                },
                "required": ["number1", "number2"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "word_count",
            "description": "get total words in a sentence",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "how many words are there in sentence"}
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for current, real-time, or recent information — such as news, events, or facts that may have changed after the model's training data. Use this when the question needs up-to-date information you would not otherwise know.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to look up on the web"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_document",
            "description": "Search Shreyansh's resume (education, skills, projects, experience) and information about the WorkPilot AI project (features, tech stack, architecture). Use this tool when the user asks questions about Shreyansh's background or about WorkPilot AI specifically.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query or question to look up in the document"
                    }
                },
                "required": ["query"]
            }
        }
    }
]