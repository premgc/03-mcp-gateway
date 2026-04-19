from fastapi import APIRouter
from pydantic import BaseModel

from app.agent.agent import run_agent

router = APIRouter()


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
    reply = run_agent(req.message)

    return {
        "success": True,
        "reply": reply
    }


# ======================================================
# HEALTH
# ======================================================
@router.get("/health")
def health():
    return {"status": "MCP Gateway running"}