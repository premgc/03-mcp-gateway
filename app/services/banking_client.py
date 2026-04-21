import os
import logging
from typing import Optional

import requests

# ======================================================
# ENV CONFIG (MCP READY)
# ======================================================
BANKING_API_URL = os.getenv("BANKING_API_URL")
BANKING_TIMEOUT = int(os.getenv("BANKING_TIMEOUT", "60"))
ENABLE_BANKING = os.getenv("ENABLE_BANKING", "true").lower() == "true"

# Optional Auth (future proof)
BANKING_API_KEY = os.getenv("BANKING_API_KEY")

logger = logging.getLogger(__name__)


class BankingClientError(Exception):
    pass


def get_ai_response(message: str) -> str:
    """
    MCP Smart Banking Client
    """

    # ======================================================
    # VALIDATION
    # ======================================================
    if not ENABLE_BANKING:
        return "⚠️ Banking service is disabled."

    if not BANKING_API_URL:
        logger.error("BANKING_API_URL not configured")
        return "Banking service is not configured."

    if not message or not message.strip():
        return "Message cannot be empty."

    payload = {
        "question": message.strip()
    }

    headers = {
        "Content-Type": "application/json"
    }

    if BANKING_API_KEY:
        headers["x-api-key"] = BANKING_API_KEY

    # ======================================================
    # API CALL (WITH RETRY)
    # ======================================================
    for attempt in range(2):  # simple retry
        try:
            logger.info(f"Calling Banking API (attempt {attempt+1})")

            response = requests.post(
                f"{BANKING_API_URL}/query",
                json=payload,
                headers=headers,
                timeout=BANKING_TIMEOUT
            )

            response.raise_for_status()
            break

        except requests.exceptions.Timeout:
            logger.warning("Banking API timeout (attempt %s)", attempt + 1)

        except requests.exceptions.ConnectionError as e:
            logger.error("Connection error: %s", e)

        except requests.exceptions.HTTPError as e:
            body = response.text if response else ""
            logger.error("HTTP error: %s | Response: %s", e, body)
            return f"Banking AI error: {body}"

        except Exception as e:
            logger.exception("Unexpected error calling Banking API")
            return f"Banking AI error: {str(e)}"

    else:
        return "Banking AI service is unavailable. Please try later."

    # ======================================================
    # RESPONSE PARSE
    # ======================================================
    try:
        data = response.json()

        if isinstance(data, str):
            return data

        if not isinstance(data, dict):
            logger.warning("Unexpected response type: %s", type(data))
            return "Invalid response from Banking AI."

        reply: Optional[str] = data.get("reply")

        if not reply:
            logger.warning("Empty reply: %s", data)
            return "No response from Banking AI."

        return reply

    except Exception as e:
        logger.error("Invalid JSON response: %s", e)
        return "Invalid response from Banking AI."