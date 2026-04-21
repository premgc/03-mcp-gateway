from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

from app.agent.agent import run_agent

# ======================================================
# LOGGING
# ======================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger(__name__)

APP_NAME = "MCP Gateway"
APP_VERSION = "1.0.0"


# ======================================================
# LIFECYCLE
# ======================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("%s started successfully", APP_NAME)
    yield
    logger.info("%s shutting down", APP_NAME)


# ======================================================
# APP
# ======================================================
app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="Gateway for routing chatbot requests to Banking AI and Jira Agent",
    lifespan=lifespan
)


# ======================================================
# CORS
# ======================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ======================================================
# REQUEST / RESPONSE MODELS
# ======================================================
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User message")


class ChatResponse(BaseModel):
    success: bool
    reply: str


# ======================================================
# HTML UI
# ======================================================
CHAT_UI_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Chandrika BI Solutions LTD - MCP Chatbot</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            background: #f4f4f4;
        }
        .header {
            background: #007bff;
            color: white;
            padding: 15px;
            text-align: center;
            font-size: 20px;
            font-weight: bold;
        }
        #chat-container {
            max-width: 900px;
            margin: 20px auto;
            height: 85vh;
            display: flex;
            flex-direction: column;
            background: white;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        #chat-body {
            flex: 1;
            overflow-y: auto;
            padding: 12px;
            background: #fafafa;
        }
        .msg {
            margin: 10px 0;
            line-height: 1.5;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        .user {
            text-align: right;
            color: #0d47a1;
        }
        .bot {
            text-align: left;
            color: #1b5e20;
        }
        #chat-input {
            display: flex;
            border-top: 1px solid #ccc;
            background: white;
        }
        #chat-input input {
            flex: 1;
            padding: 12px;
            border: none;
            outline: none;
            font-size: 14px;
        }
        #chat-input button {
            padding: 12px 18px;
            background: #007bff;
            color: white;
            border: none;
            cursor: pointer;
            font-size: 14px;
        }
        #chat-input button:hover {
            background: #0056b3;
        }
        #chat-input button:disabled {
            background: #9bbce0;
            cursor: not-allowed;
        }
    </style>
</head>
<body>
    <div class="header">Chandrika BI Solutions LTD - MCP Chatbot</div>

    <div id="chat-container">
        <div id="chat-body">
            <div class="msg bot"><b>Bot:</b> Welcome 👋</div>
        </div>

        <div id="chat-input">
            <input id="msg" placeholder="Type your question..." onkeydown="handleKey(event)" />
            <button id="sendBtn" onclick="send()">Send</button>
        </div>
    </div>

    <script>
        function escapeHtml(text) {
            const div = document.createElement("div");
            div.textContent = text;
            return div.innerHTML;
        }

        function appendMessage(role, label, message) {
            const body = document.getElementById("chat-body");
            const cssClass = role === "user" ? "user" : "bot";
            body.innerHTML += "<div class='msg " + cssClass + "'><b>" + label + ":</b> " + escapeHtml(message) + "</div>";
            body.scrollTop = body.scrollHeight;
        }

        function handleKey(event) {
            if (event.key === "Enter") {
                send();
            }
        }

        async function send() {
            const input = document.getElementById("msg");
            const button = document.getElementById("sendBtn");
            const message = input.value.trim();

            if (!message) return;

            appendMessage("user", "You", message);
            input.value = "";
            button.disabled = true;

            try {
                const res = await fetch("/chat", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ message: message })
                });

                const data = await res.json();
                const reply = data.reply || "No response";

                appendMessage("bot", "Bot", reply);
            } catch (err) {
                appendMessage("bot", "Bot", "Error connecting to server");
            } finally {
                button.disabled = false;
                input.focus();
            }
        }
    </script>
</body>
</html>
"""


# ======================================================
# UI
# ======================================================
@app.get("/", response_class=HTMLResponse)
def home():
    return CHAT_UI_HTML


# ======================================================
# CHAT API
# ======================================================
@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    try:
        message = req.message.strip()

        if not message:
            return ChatResponse(
                success=False,
                reply="Please enter a valid message."
            )

        logger.info("Incoming request: %s", message)

        reply = run_agent(message)

        if reply is None:
            reply = "No response generated."

        return ChatResponse(
            success=True,
            reply=str(reply)
        )

    except Exception as e:
        logger.exception("Chat error")
        return ChatResponse(
            success=False,
            reply=f"Error: {str(e)}"
        )


# ======================================================
# HEALTH
# ======================================================
@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": APP_NAME,
        "version": APP_VERSION
    }


# ======================================================
# GLOBAL EXCEPTION HANDLER
# ======================================================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "reply": "Internal server error"
        }
    )