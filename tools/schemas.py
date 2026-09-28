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
    },
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "Send a real email to a specified recipient using Gmail. Use this tool only when the user explicitly asks to send, compose, or email something to someone. This action is real and cannot be undone, so only use it when the user's intent to send an email is clear.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string",
                        "description": "The recipient's email address"
                    },
                    "subject": {
                        "type": "string",
                        "description": "The subject line of the email"
                    },
                    "body": {
                        "type": "string",
                        "description": "The main content/message of the email"
                    }
                },
                "required": ["to", "subject", "body"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_event",
            "description": "Create a real event on the user's Google Calendar. Use this tool only when the user explicitly asks to schedule, book, or create a calendar event or meeting. This action is real and creates an actual calendar entry, so only use it when the user's intent, date, and time are clear. If the user gives a relative date/time like 'tomorrow' or 'next Monday at 3pm', convert it to the exact ISO 8601 format (YYYY-MM-DDTHH:MM:SS) based on the current date, which you can get from the get_current_time tool if needed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string",
                        "description": "A short title or description of the event"
                    },
                    "start_time": {
                        "type": "string",
                        "description": "The event's start date and time in ISO 8601 format, e.g. '2026-09-27T15:00:00'"
                    },
                    "end_time": {
                        "type": "string",
                        "description": "The event's end date and time in ISO 8601 format, e.g. '2026-09-27T15:30:00'"
                    }
                },
                "required": ["summary", "start_time", "end_time"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_github_issue",
            "description": "Create a real issue on a GitHub repository. Use this tool only when the user explicitly asks to create, file, or open an issue on GitHub. This action is real and creates an actual public or private issue, so only use it when the user's intent is clear.",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo_name": {
                        "type": "string",
                        "description": "The full repository name in 'owner/repo' format, e.g. 'ShreyanshGupta-1/workpilot-ai'. Always include the owner/username — never just the repo name alone."
                    },
                    "title": {
                        "type": "string",
                        "description": "The title of the issue"
                    },
                    "body": {
                        "type": "string",
                        "description": "The detailed description or body text of the issue"
                    }
                },
                "required": ["repo_name", "title", "body"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_jira_issue",
            "description": "Create a real issue/ticket in a Jira project. Use this tool only when the user explicitly asks to create a Jira ticket, task, or issue. This action is real and creates an actual tracked item, so only use it when the user's intent is clear. The project key for this user's project is 'KAN' unless they specify a different one. Arguments must be named exactly: project_key, summary (the ticket title), description.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_key": {
                        "type": "string",
                        "description": "The Jira project key, e.g. 'KAN'. Use 'KAN' by default unless the user names a different project key."
                    },
                    "summary": {
                        "type": "string",
                        "description": "A short title/summary of the issue"
                    },
                    "description": {
                        "type": "string",
                        "description": "A detailed description of the issue"
                    }
                },
                "required": ["project_key", "summary", "description"]
            }
        }
    }
]