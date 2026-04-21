import os
import logging
import requests

logger = logging.getLogger(__name__)

# ======================================================
# ENV CONFIG (MCP READY)
# ======================================================
JIRA_AGENT_BASE_URL = os.getenv("JIRA_AGENT_URL")
JIRA_TIMEOUT = int(os.getenv("JIRA_TIMEOUT", "20"))
ENABLE_JIRA = os.getenv("ENABLE_JIRA", "true").lower() == "true"

if JIRA_AGENT_BASE_URL:
    JIRA_CREATE_TICKET_URL = f"{JIRA_AGENT_BASE_URL}/create-ticket"
else:
    JIRA_CREATE_TICKET_URL = None


# ======================================================
# CUSTOM ERROR
# ======================================================
class JiraClientError(Exception):
    pass


# ======================================================
# CREATE JIRA TICKET (MCP SAFE)
# ======================================================
def create_jira_ticket(summary: str, description: str):

    # ======================================================
    # MCP VALIDATION
    # ======================================================
    if not ENABLE_JIRA:
        return "⚠️ Jira service is disabled."

    if not JIRA_CREATE_TICKET_URL:
        logger.error("JIRA_AGENT_URL not configured")
        return "Jira service is not configured."

    payload = {
        "summary": summary,
        "description": description
    }

    # ======================================================
    # API CALL (WITH RETRY)
    # ======================================================
    for attempt in range(2):
        try:
            logger.info(f"Calling Jira API (attempt {attempt+1})")

            response = requests.post(
                JIRA_CREATE_TICKET_URL,
                json=payload,
                timeout=JIRA_TIMEOUT
            )

            response.raise_for_status()
            break

        except requests.exceptions.Timeout:
            logger.warning("Jira timeout (attempt %s)", attempt + 1)

        except requests.exceptions.ConnectionError as e:
            logger.error("Connection error: %s", e)

        except requests.exceptions.HTTPError:
            logger.error(f"HTTP error: {response.status_code} | {response.text}")
            return "❌ Jira returned an error. Please try again."

        except Exception as e:
            logger.exception("Unexpected Jira error")
            return f"❌ Jira error: {str(e)}"

    else:
        return "❌ Jira service is unavailable. Try later."

    # ======================================================
    # RESPONSE PARSE
    # ======================================================
    try:
        data = response.json()

        issue_key = data.get("issue_key")
        issue_id = data.get("issue_id")
        url = data.get("url")

        # ======================================================
        # CHATBOLT FRIENDLY RESPONSE ⭐
        # ======================================================
        return f"""
✅ Jira Ticket Created Successfully

🆔 Ticket No: {issue_id or "N/A"}
🔑 Key: {issue_key or "N/A"}
🔗 URL: {url or "Not available"}
""".strip()

    except Exception:
        logger.error("Invalid JSON response from Jira")
        return "❌ Invalid response from Jira service"