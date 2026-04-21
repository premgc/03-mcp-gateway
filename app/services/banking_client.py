import os
import logging
from typing import Optional

import requests

BANKING_API_URL = os.getenv("BANKING_API_URL")
BANKING_TIMEOUT = int(os.getenv("BANKING_TIMEOUT", "60"))
ENABLE_BANKING = os.getenv("ENABLE_BANKING", "true").lower() == "true"

logger = logging.getLogger(__name__)


def get_ai_response(message: str) -> str:

    if not ENABLE_BANKING:
        return "Banking service disabled"

    if not message or not message.strip():
        return "Please enter a valid message"

    try:
        response = requests.post(
            BANKING_API_URL,   # ✅ IMPORTANT → NO /chat
            json={"question": message.strip()},
            timeout=BANKING_TIMEOUT
        )

        response.raise_for_status()

        data = response.json()

        return data.get("reply", "No response from Banking AI")

    except Exception as e:
        logger.exception("Banking API error")
        return "Banking service error"