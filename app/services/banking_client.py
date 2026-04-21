import os
import logging
from typing import Optional, Union

from app.services.banking_service import process_query

# ======================================================
# ENV CONFIG
# ======================================================
ENABLE_BANKING = os.getenv("ENABLE_BANKING", "true").lower() == "true"

logger = logging.getLogger(__name__)


class BankingClientError(Exception):
    pass


# ======================================================
# MAIN FUNCTION
# ======================================================
def get_ai_response(message: str) -> str:
    """
    MCP Smart Banking Client (INTERNAL CALL - PRODUCTION SAFE)
    """

    # ======================================================
    # FEATURE FLAG CHECK
    # ======================================================
    if not ENABLE_BANKING:
        logger.warning("Banking service is disabled via config")
        return "⚠️ Banking service is currently disabled."

    # ======================================================
    # INPUT VALIDATION
    # ======================================================
    if not message or not message.strip():
        return "Please enter a valid message."

    try:
        clean_msg = message.strip()

        logger.info(f"Calling Banking Service (internal) | Query: {clean_msg}")

        # ======================================================
        # DIRECT FUNCTION CALL (NO HTTP)
        # ======================================================
        result: Union[str, dict, None] = process_query(clean_msg)

        # ======================================================
        # RESPONSE HANDLING
        # ======================================================
        if not result:
            logger.warning("Empty response from banking_service")
            return "No response from Banking AI."

        # If service returns string
        if isinstance(result, str):
            return result

        # If service returns dict
        if isinstance(result, dict):
            reply: Optional[str] = result.get("reply") or result.get("response")

            if reply:
                return reply

            logger.warning(f"Unexpected dict format: {result}")
            return "Invalid response from Banking AI."

        # Unexpected type
        logger.warning(f"Unsupported response type: {type(result)}")
        return "Unexpected response from Banking AI."

    except Exception as e:
        logger.exception("Banking service error")

        # Do NOT expose raw error in production
        return "❌ Banking service is temporarily unavailable. Please try again."