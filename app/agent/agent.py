import logging
from typing import Dict, Any

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
# EXTRACT JIRA DETAILS (SAFE PARSER)
# ======================================================
def extract_jira_details(jira_response: Dict[str, Any]) -> Dict[str, Any]:

    if not jira_response:
        return {"issue_id": None, "issue_url": None}

    issue_id = jira_response.get("issue_id")
    issue_url = jira_response.get("issue_url") or jira_response.get("url")

    # handle nested response
    if not issue_id and "reply" in jira_response:
        reply = jira_response["reply"]
        issue_id = reply.get("issue_id")
        issue_url = reply.get("issue_url")

    return {
        "issue_id": issue_id,
        "issue_url": issue_url
    }


# ======================================================
# MAIN AGENT (MCP CORE LOGIC)
# ======================================================
def run_agent(user_input: str) -> str:

    if not user_input or not user_input.strip():
        return "Please enter a valid message."

    try:
        text = user_input.strip()

        # ======================================================
        # JIRA FLOW (FIXED)
        # ======================================================
        if is_jira_request(text):
            logger.info("Routing to Jira Agent")

            jira_response = create_jira_ticket(
                summary=text,
                description=f"Auto-created from MCP Gateway: {text}"
            )

            logger.info(f"Jira Response: {jira_response}")

            # ✅ Handle empty response
            if not jira_response:
                return "❌ Jira service is unavailable. Try later."

            # ✅ Handle string response (THIS FIXES YOUR ERROR)
            if isinstance(jira_response, str):
                return jira_response

            # ✅ Handle dict safely
            if not jira_response.get("success"):
                return "❌ Failed to create Jira ticket."

            jira_data = extract_jira_details(jira_response)

            issue_id = jira_data["issue_id"]
            issue_url = jira_data["issue_url"]

            if issue_url:
                return (
                    f"✅ Jira Ticket Created Successfully\n\n"
                    f"🆔 Ticket No: {issue_id}\n"
                    f"🔗 Open Ticket: {issue_url}"
                )

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
            return "❌ No response from Banking AI."

        return banking_reply

    except Exception as e:
        logger.exception("Agent error")
        return "❌ Something went wrong. Please try again."