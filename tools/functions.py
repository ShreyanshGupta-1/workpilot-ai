import datetime
import os
import base64
from email.mime.text import MIMEText

from dotenv import load_dotenv
from tavily import TavilyClient
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from github import Github
from jira import JIRA

load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/gmail.send',
          'https://www.googleapis.com/auth/gmail.readonly',
          'https://www.googleapis.com/auth/calendar.events']


# ---------- Simple tools ----------

def get_current_time():
    now = datetime.datetime.now()
    return now.strftime("%d/%m/%y %H:%M:%S")


def add_numbers(number1, number2):
    return number1 + number2


def word_count(text):
    return len(text.split(" "))


def web_search(query):
    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    response = client.search(query)
    top_results = response["results"][:2]
    summary = ""
    for item in top_results:
        summary += f"{item['title']} ({item['url']})\n{item['content'][:300]}\n\n"
    return summary


# ---------- Lazy service clients (nothing runs at import time) ----------

_google_creds = None
_gmail_service = None
_calendar_service = None
_github_client = None
_jira_client = None


def _get_google_creds():
    global _google_creds
    if _google_creds and _google_creds.valid:
        return _google_creds

    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        elif os.path.exists('credentials.json'):
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        else:
            raise RuntimeError(
                "Google is not authorized on this machine, so Gmail and Calendar tools are unavailable here."
            )
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    _google_creds = creds
    return creds


def _gmail():
    global _gmail_service
    if _gmail_service is None:
        _gmail_service = build('gmail', 'v1', credentials=_get_google_creds())
    return _gmail_service


def _calendar():
    global _calendar_service
    if _calendar_service is None:
        _calendar_service = build('calendar', 'v3', credentials=_get_google_creds())
    return _calendar_service


def _github():
    global _github_client
    if _github_client is None:
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            raise RuntimeError("GITHUB_TOKEN is not set, so the GitHub tool is unavailable.")
        _github_client = Github(token)
    return _github_client


def _jira():
    global _jira_client
    if _jira_client is None:
        domain = os.getenv("JIRA_DOMAIN")
        email = os.getenv("JIRA_EMAIL")
        api_token = os.getenv("JIRA_API_TOKEN")
        if not (domain and email and api_token):
            raise RuntimeError("Jira credentials are not set, so the Jira tool is unavailable.")
        _jira_client = JIRA(server=f"https://{domain}", basic_auth=(email, api_token))
    return _jira_client


# ---------- Real-world action tools ----------

def send_email(to, subject, body):
    message = MIMEText(body)
    message['to'] = to
    message['subject'] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    _gmail().users().messages().send(userId='me', body={'raw': raw}).execute()
    return f"Email sent to {to} with subject '{subject}'"


def create_event(summary, start_time, end_time):
    event = {
        'summary': summary,
        'start': {'dateTime': start_time, 'timeZone': 'Asia/Kolkata'},
        'end': {'dateTime': end_time, 'timeZone': 'Asia/Kolkata'},
    }
    created = _calendar().events().insert(calendarId='primary', body=event).execute()
    return f"Event '{summary}' created: {created.get('htmlLink')}"


def create_github_issue(repo_name, title, body):
    repo = _github().get_repo(repo_name)
    issue = repo.create_issue(title=title, body=body)
    return f"Issue created: {issue.html_url}"


def create_jira_issue(project_key, summary, description):
    jira = _jira()
    issue_dict = {
        'project': {'key': project_key},
        'summary': summary,
        'description': description,
        'issuetype': {'name': 'Task'},
    }
    new_issue = jira.create_issue(fields=issue_dict)
    return f"Jira issue created: {new_issue.key} - {jira.server_url}/browse/{new_issue.key}"

def list_calendar_events(days_ahead=7):
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    later = (datetime.datetime.utcnow() + datetime.timedelta(days=days_ahead)).isoformat() + 'Z'
    events_result = _calendar().events().list(
        calendarId='primary',
        timeMin=now,
        timeMax=later,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    events = events_result.get('items', [])
    if not events:
        return f"No events found in the next {days_ahead} day(s)."
    lines = []
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        lines.append(f"- {event.get('summary', '(no title)')} at {start}")
    return "\n".join(lines)


def list_jira_issues(project_key):
    jira = _jira()
    issues = jira.search_issues(f'project={project_key} AND resolution=Unresolved', maxResults=20)
    if not issues:
        return f"No open issues found in project {project_key}."
    lines = [f"- {issue.key}: {issue.fields.summary}" for issue in issues]
    return "\n".join(lines)


def list_github_issues(repo_name):
    repo = _github().get_repo(repo_name)
    issues = repo.get_issues(state='open')
    lines = []
    for issue in issues[:20]:
        lines.append(f"- #{issue.number}: {issue.title}")
    if not lines:
        return f"No open issues found in {repo_name}."
    return "\n".join(lines)


def check_inbox(max_results=5):
    service = _gmail()
    results = service.users().messages().list(userId='me', maxResults=max_results, labelIds=['INBOX']).execute()
    message_ids = results.get('messages', [])
    if not message_ids:
        return "Inbox is empty or no recent messages found."
    lines = []
    for m in message_ids:
        msg = service.users().messages().get(
            userId='me', id=m['id'], format='metadata',
            metadataHeaders=['From', 'Subject', 'Date']
        ).execute()
        headers = {h['name']: h['value'] for h in msg['payload']['headers']}
        lines.append(f"- From: {headers.get('From', '?')} | Subject: {headers.get('Subject', '(no subject)')} | Date: {headers.get('Date', '?')}")
    return "\n".join(lines)