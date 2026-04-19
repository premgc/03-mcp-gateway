import logging
from typing import Dict, Any, Optional

from app.services.banking_client import get_ai_response
from app.services.jira_client import create_jira_ticket

logger = logging.getLogger(__name__)


# ======================================================
# INTENT DETECTION (PRODUCTION SAFE)
# ======================================================
def is_jira_request(user_input: str) -> bool:
    text = user_input.lower().strip()

    if "ticket" in text or "jira" in text:
        return True

    action_words = ["create", "raise", "log", "report", "open"]

    if any(word in text for word in action_words) and "issue" in text:
        return True

    return False


# ======================================================
# EXTRACT JIRA DETAILS (UPDATED)
# ======================================================

# ======================================================
# MAIN AGENT (PRODUCTION)
# ======================================================
def run_agent(user_input: str) -> str:
    """
    MCP Routing Logic
    """

    if not user_input or not user_input.strip():
        return "Please enter a valid message."

    try:
        text = user_input.strip()

        # ======================================================
        # JIRA FLOW
        # ======================================================
        if is_jira_request(text):
            logger.info("Routing to Jira Agent")

            jira_response = create_jira_ticket(
                summary=text,
                description=f"Auto-created from MCP Gateway: {text}"
            )

            logger.info(f"Jira Response: {jira_response}")

            if not jira_response or not jira_response.get("success"):
                raise Exception(f"Invalid Jira response: {jira_response}")

            jira_data = extract_jira_details(jira_response)

            issue_id = jira_data["issue_id"]
            issue_url = jira_data["issue_url"]

            # ======================================================
            # ✅ FINAL RESPONSE (AS YOU REQUESTED)
            # ======================================================
            if issue_url:
                return (
                    f"✅ Jira Ticket Created Successfully\n\n"
                    f"🆔 Ticket No: {issue_id}\n"
                    f"🔗 Open Ticket: {issue_url}"
                )

            # fallback if URL missing
            return (
                f"✅ Jira Ticket Created Successfully\n\n"
                f"🆔 Ticket No: {issue_id}"
            )

        # ======================================================
        # BANKING FLOW
        # ======================================================
        logger.info("Routing to Smart Banking AI")

        banking_reply = get_ai_response(text)

        if not banking_reply:
            return "No response from Banking AI."

        return banking_reply

    except Exception:
        logger.exception("Agent error")
        return "Something went wrong. Please try again."