import os
import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)

# ======================================================
# CONFIG
# ======================================================
JIRA_AGENT_BASE_URL = os.getenv("JIRA_AGENT_URL", "").strip().rstrip("/")
JIRA_TIMEOUT = int(os.getenv("JIRA_TIMEOUT", "20"))
ENABLE_JIRA = os.getenv("ENABLE_JIRA", "true").lower() == "true"

if JIRA_AGENT_BASE_URL:
    JIRA_CREATE_TICKET_URL = f"{JIRA_AGENT_BASE_URL}/api/jira/create-ticket"
else:
    JIRA_CREATE_TICKET_URL = None


# ======================================================
# CUSTOM ERROR
# ======================================================
class JiraClientError(Exception):
    pass


# ======================================================
# MAIN FUNCTION
# ======================================================
def create_jira_ticket(summary: str, description: str) -> str:
    if not ENABLE_JIRA:
        return "⚠️ Jira service is disabled."

    if not JIRA_CREATE_TICKET_URL:
        logger.error("JIRA_AGENT_URL not configured")
        return "❌ Jira service is not configured."

    summary = (summary or "").strip()
    description = (description or "").strip()

    if not summary:
        return "❌ Jira summary cannot be empty."

    payload = {
        "summary": summary,
        "description": description
    }

    response: Optional[requests.Response] = None

    for attempt in range(2):
        try:
            logger.info("Calling Jira API (attempt %s): %s", attempt + 1, JIRA_CREATE_TICKET_URL)

            response = requests.post(
                JIRA_CREATE_TICKET_URL,
                json=payload,
                timeout=JIRA_TIMEOUT,
                headers={"Content-Type": "application/json"}
            )

            response.raise_for_status()
            break

        except requests.exceptions.Timeout:
            logger.warning("Jira timeout (attempt %s)", attempt + 1)

        except requests.exceptions.ConnectionError as e:
            logger.error("Jira connection error (attempt %s): %s", attempt + 1, e)

        except requests.exceptions.HTTPError:
            status_code = response.status_code if response is not None else "unknown"
            body = response.text if response is not None else ""
            logger.error("Jira HTTP error: %s | %s", status_code, body)
            return "❌ Jira returned an error. Please try again."

        except Exception as e:
            logger.exception("Unexpected Jira error")
            return f"❌ Jira error: {str(e)}"

    else:
        return "❌ Jira service is unavailable. Try later."

    try:
        data = response.json()

        success = data.get("success", True)
        issue_id = data.get("issue_id")
        issue_key = data.get("issue_key")
        issue_url = data.get("url")
        message = data.get("message")

        if not success:
            logger.error("Jira API returned unsuccessful response: %s", data)
            return f"❌ {message or 'Failed to create Jira ticket.'}"

        if not issue_id and not issue_key:
            logger.error("Invalid Jira success response: %s", data)
            return "❌ Jira created an invalid response. Please try again."

        lines = [
            "✅ Jira Ticket Created Successfully",
            "",
            f"🆔 Ticket No: {issue_id or 'N/A'}",
            f"🔑 Key: {issue_key or 'N/A'}",
        ]

        if issue_url:
            lines.append(f"🔗 URL: {issue_url}")

        return "\n".join(lines)

    except ValueError:
        logger.error("Invalid JSON response from Jira: %s", response.text if response else "")
        return "❌ Invalid response from Jira service."

    except Exception:
        logger.exception("Unexpected response parsing error from Jira")
        return "❌ Jira response parsing failed."