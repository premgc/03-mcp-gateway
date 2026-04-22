import os
import logging
import requests
from typing import Optional

# ======================================================
# CONFIG
# ======================================================
BANKING_API_URL = os.getenv("BANKING_API_URL", "").rstrip("/")
BANKING_TIMEOUT = int(os.getenv("BANKING_TIMEOUT", "60"))
ENABLE_BANKING = os.getenv("ENABLE_BANKING", "true").lower() == "true"

logger = logging.getLogger(__name__)


# ======================================================
# MAIN FUNCTION
# ======================================================
def get_ai_response(message: str) -> str:

    # ----------------------------
    # VALIDATION
    # ----------------------------
    if not ENABLE_BANKING:
        return "⚠️ Banking service is disabled."

    if not BANKING_API_URL:
        logger.error("BANKING_API_URL not configured")
        return "❌ Banking service not configured."

    if not message or not message.strip():
        return "Please enter a valid message."

    # ----------------------------
    # API CALL
    # ----------------------------
    try:
        url = f"{BANKING_API_URL}/api/banking/ask"   # ✅ CORRECT ENDPOINT

        logger.info(f"Calling Banking API: {url}")

        response = requests.post(
            url,
            json={"question": message.strip()},
            timeout=BANKING_TIMEOUT
        )

        response.raise_for_status()

        data = response.json()

        # ----------------------------
        # RESPONSE HANDLING
        # ----------------------------
        reply = data.get("reply")

        if not reply:
            logger.warning(f"No reply in response: {data}")
            return "⚠️ No response from Banking AI."

        return reply

    except requests.exceptions.Timeout:
        logger.error("Banking API timeout")
        return "❌ Banking service timeout. Try again."

    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error: {response.status_code} | {response.text}")
        return "❌ Banking service returned an error."

    except requests.exceptions.ConnectionError:
        logger.error("Banking service unreachable")
        return "❌ Unable to connect to Banking service."

    except Exception as e:
        logger.exception("Unexpected Banking API error")
        return "❌ Banking service error."