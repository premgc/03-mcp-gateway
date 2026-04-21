from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

# DO NOT import agent at top to avoid circular import
# from app.agent.agent import run_agent  ❌ REMOVE THIS

router = APIRouter()
logger = logging.getLogger(__name__)


# ======================================================
# REQUEST MODEL
# ======================================================
class ChatRequest(BaseModel):
    message: str


# ======================================================
# ROUTE
# ======================================================
@router.post("/chat")
def chat(req: ChatRequest):
    try:
        # ✅ Import inside function (prevents circular import)
        from app.agent.agent import run_agent

        logger.info(f"Incoming request: {req.message}")

        reply = run_agent(req.message)

        return {
            "success": True,
            "reply": reply
        }

    except Exception as e:
        logger.error(f"Chat processing failed: {str(e)}")

        raise HTTPException(
            status_code=500,
            detail=f"MCP processing error: {str(e)}"
        )


# ======================================================
# HEALTH
# ======================================================
@router.get("/health")
def health():
    return {
        "status": "MCP Gateway running",
        "service": "ok"
    }