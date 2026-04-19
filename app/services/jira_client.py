import os
import logging
import requests

logger = logging.getLogger(__name__)

JIRA_AGENT_URL = os.getenv(
    "JIRA_AGENT_URL",
    "http://127.0.0.1:801/api/jira/create-ticket"
)


class JiraClientError(Exception):
    pass


def create_jira_ticket(summary: str, description: str):
    payload = {
        "summary": summary,
        "description": description
    }

    try:
        response = requests.post(
            JIRA_AGENT_URL,
            json=payload,
            timeout=30
        )

        response.raise_for_status()

    except requests.exceptions.Timeout:
        logger.error("Jira timeout")
        raise JiraClientError("Jira service timeout")

    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error: {e}")
        raise JiraClientError("Cannot connect to Jira service")

    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error: {e} | {response.text}")
        raise JiraClientError("Jira returned error")

    except Exception as e:
        logger.exception("Unexpected Jira error")
        raise JiraClientError(str(e))

    try:
        return response.json()
    except Exception:
        raise JiraClientError("Invalid Jira response")