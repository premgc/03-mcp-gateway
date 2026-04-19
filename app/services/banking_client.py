import os
import logging
from typing import Optional

import requests

BANKING_API_URL = os.getenv(
    "BANKING_API_URL",
    "http://127.0.0.1:8000/api/banking/ask"
).strip()

TIMEOUT = int(os.getenv("BANKING_TIMEOUT", "60"))

logger = logging.getLogger(__name__)


class BankingClientError(Exception):
    pass


def get_ai_response(message: str) -> str:
    """
    Calls Smart Banking AI service and returns reply string.
    Request contract:
      { "question": "..." }
    Response contract:
      { "reply": "..." }
    """

    if not message or not message.strip():
        return "Message cannot be empty."

    payload = {
        "question": message.strip()
    }

    try:
        response = requests.post(
            BANKING_API_URL,
            json=payload,
            timeout=TIMEOUT
        )
        response.raise_for_status()

    except requests.exceptions.Timeout:
        logger.error("Banking API timeout")
        return "Banking AI is taking too long to respond. Please try again."

    except requests.exceptions.ConnectionError as e:
        logger.error("Connection error: %s", e)
        return "Cannot connect to Smart Banking AI service."

    except requests.exceptions.HTTPError as e:
        body = ""
        try:
            body = response.text
        except Exception:
            body = "<no response body>"
        logger.error("HTTP error: %s | Response: %s", e, body)
        return f"Banking AI returned an error: {body}"

    except Exception as e:
        logger.exception("Unexpected error calling Banking API")
        return f"Banking AI error: {str(e)}"

    try:
        data = response.json()

        if isinstance(data, str):
            return data

        if not isinstance(data, dict):
            logger.warning("Unexpected response type from Banking API: %s", type(data))
            return "Invalid response from Smart Banking AI."

        reply: Optional[str] = data.get("reply")

        if not reply:
            logger.warning("Empty reply from Banking API: %s", data)
            return "No response from Smart Banking AI."

        return reply

    except Exception as e:
        logger.error("Invalid JSON response: %s", e)
        return "Invalid response from Smart Banking AI."