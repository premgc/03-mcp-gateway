import os
import requests

JIRA_AGENT_URL = os.getenv("JIRA_AGENT_URL", "").rstrip("/")


class JiraToolError(Exception):
    pass


def create_jira_ticket(summary: str, description: str):
    if not JIRA_AGENT_URL:
        raise JiraToolError("JIRA_AGENT_URL not configured")

    payload = {
        "summary": summary,
        "description": description
    }

    try:
        response = requests.post(
            f"{JIRA_AGENT_URL}/api/jira/create-ticket",
            json=payload,
            timeout=30
        )
    except Exception as e:
        raise JiraToolError(f"Connection failed: {e}")

    if response.status_code != 200:
        raise JiraToolError(f"Jira error: {response.text}")

    return response.json()