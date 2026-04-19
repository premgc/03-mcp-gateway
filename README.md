Model Context Protocol (
One chat interface
→ One MCP Host / Orchestrator
→ Two separate MCP servers

Smart Banking MCP Server
JIRA MCP Server

That lets you keep:

separate repos
separate services/web apps
separate business logic
one common assistant/chat experience

This fits MCP well because MCP is designed for one host app to coordinate connections to one or more MCP servers that expose capabilities to the model.
End-to-end architecture diagram
┌─────────────────────────────────────────────────────────────┐
│                        END USER                             │
│                 "Create a Jira ticket for                  │
│          Outlook issue and show my recent spending"        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  CHAT UI / FRONTEND                         │
│  Web App / ChatBolt / Teams / Internal portal               │
│  - user login                                                │
│  - chat window                                                │
│  - conversation history                                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                MCP HOST / AI ORCHESTRATOR                   │
│                                                             │
│  Components:                                                │
│  - LLM Gateway (Azure OpenAI / GPT)                         │
│  - MCP Client Manager                                       │
│  - Conversation Memory                                      │
│  - Intent / Tool Routing                                    │
│  - Guardrails / AuthZ / Audit                               │
│                                                             │
│  Connects to:                                               │
│  - Smart Banking MCP Server                                 │
│  - JIRA MCP Server                                          │
└─────────────────────────────────────────────────────────────┘
                   │                               │
                   │ MCP Client                    │ MCP Client
                   ▼                               ▼
┌───────────────────────────────┐     ┌───────────────────────────────┐
│   SMART BANKING MCP SERVER    │     │        JIRA MCP SERVER        │
│                               │     │                               │
│  Exposes via MCP:             │     │  Exposes via MCP:             │
│  - Tools                      │     │  - Tools                      │
│  - Resources                  │     │  - Resources                  │
│  - Prompts (optional)         │     │  - Prompts (optional)         │
└───────────────────────────────┘     └───────────────────────────────┘
               │                                         │
               ▼                                         ▼
┌───────────────────────────────┐     ┌───────────────────────────────┐
│  Banking Service / API Layer  │     │      Jira Service / API       │
│  - Python/FastAPI             │     │      - Python/FastAPI         │
│  - query logic                │     │      - create/update/search   │
│  - analytics logic            │     │      - Jira REST integration  │
└───────────────────────────────┘     └───────────────────────────────┘
               │                                         │
               ▼                                         ▼
┌───────────────────────────────┐     ┌───────────────────────────────┐
│   Data + Search Layer         │     │          Atlassian Jira       │
│  - Transactions DB            │     │          Cloud / Server       │
│  - Azure SQL / Delta Lake     │     └───────────────────────────────┘
│  - Vector Index / AI Search   │
│  - Knowledge docs             │
└───────────────────────────────┘


What each layer does
A. Chat UI

This is your single front end.
Examples:

ChatBolt
internal web app
Teams bot
portal UI

User types:

“Show my last 10 transactions”
“Create a Jira ticket for Outlook not working”
“Summarize spending and raise a support issue”

The UI should only handle:

login/session
sending the prompt
showing model response
optionally rendering buttons/forms
B. MCP Host / AI Orchestrator

This is the brain in the middle.

It should contain:

1. LLM layer

Use:

Azure OpenAI / GPT
system prompt
conversation history
tool-calling enabled
2. MCP client manager

The host opens MCP client connections to both servers. MCP architecture separates the host application from the clients that communicate with specific servers.

3. Intent + routing

It decides:

banking question → Smart Banking MCP tools
ticket question → JIRA MCP tools
mixed question → call both
4. Guardrails
PII masking
permission checks
allow/deny tools
output validation
audit logs
5. Memory / session context

Keep chat history and user context so the model understands follow-up questions like:

“Create a ticket for that issue”
“Now show only UPI transactions”
C. Smart Banking MCP Server

This MCP server should expose banking capabilities as tools, and optionally expose schemas/help docs as resources. MCP servers can expose tools for executable actions and resources for contextual data.

Suggested tools
get_recent_transactions(account_id, days)
get_transaction_types()
get_spending_by_category(start_date, end_date)
get_balance(account_id)
search_banking_knowledge(query)
summarize_statement(file_id)
detect_anomalies(account_id, period)
Suggested resources
account metadata
product documentation
category definitions
schema descriptions
FAQ / policy docs
Suggested prompts
“Summarize monthly spend”
“Analyze unusual transactions”
“Explain charges in plain English”

Prompts are optional, but MCP supports servers exposing prompt templates too.

D. JIRA MCP Server

This MCP server wraps your JIRA integration and exposes ticket operations as tools.

Suggested tools
create_jira_ticket(summary, description, priority, issue_type)
get_jira_ticket(issue_key)
search_jira_tickets(query)
add_comment(issue_key, comment)
update_status(issue_key, status)
assign_ticket(issue_key, assignee)
list_my_open_tickets()
Suggested resources
project list
issue types
priorities
workflows
allowed transitions
Suggested prompts
“Create IT support ticket”
“Summarize open incidents”
“Prepare ticket update note”
4) Typical request flow
Example 1: Banking-only question

User:
“Show me unique transaction types with count.”

Flow:

User sends prompt from chat UI
MCP host sends prompt to LLM
LLM decides Smart Banking tool is needed
MCP host calls Smart Banking MCP server tool:
get_transaction_types_with_count()
Server fetches from DB / analytics layer
Result returns to host
LLM formats clean reply
Chat UI shows answer
Example 2: JIRA-only question

User:
“Create ticket: Outlook email not working on laptop.”

Flow:

User sends prompt
LLM identifies JIRA action
Host calls JIRA MCP tool:
create_jira_ticket(...)
JIRA MCP server calls Atlassian REST API
Jira returns issue key + URL
Host returns natural-language response:
Ticket created
issue number
ticket URL
Example 3: Cross-app orchestration

User:
“My laptop crashed and I can’t access banking reports. Create a Jira ticket and also tell me what reports were due today.”

Flow:

Prompt enters host
Host/LLM plans a multi-tool action
Calls Smart Banking tool:
get pending reports / due reports
Calls JIRA tool:
create issue
Combines both outputs
Returns one answer

This is where MCP shines: one host can coordinate multiple server capabilities in one user flow. That’s consistent with MCP’s architecture and emerging agent-oriented direction.

5) Recommended deployment architecture for your case

Since you want Smart Banking and JIRA kept separate, use this:

Separate repos
smart-banking-app
jira-agent
mcp-host-orchestrator
Separate services
Smart Banking Web/API
JIRA Web/API
MCP Host Web/API
Optional MCP wrappers

You can either:

build MCP directly into each app, or
create thin MCP wrapper services in front of them

Best practical pattern:

Repo 1: smart-banking-app
  - existing banking business logic
  - banking APIs
  - optional MCP server adapter

Repo 2: jira-agent
  - existing jira business logic
  - jira APIs
  - optional MCP server adapter

Repo 3: mcp-host-orchestrator
  - chat ui backend
  - Azure OpenAI integration
  - MCP clients for both services
  - auth / logging / audit

This keeps your apps independent but still allows one unified assistant.

6) Azure deployment view
Azure Front Door / App Gateway
        │
        ▼
Azure App Service / Container Apps
   ├── MCP Host / Orchestrator
   ├── Smart Banking Service
   └── JIRA Service

Supporting Azure Services
   ├── Azure OpenAI
   ├── Azure SQL / Cosmos / PostgreSQL
   ├── ADLS / Delta Lake
   ├── Azure AI Search / Vector Index
   ├── Key Vault
   ├── Application Insights
   ├── Entra ID
   └── Storage / Log Analytics
Azure role of each service
Azure OpenAI: LLM reasoning and tool-use
Azure SQL / Delta / ADLS: banking data storage
Azure AI Search / vector store: RAG for banking knowledge
Key Vault: Jira token, DB secrets, OpenAI keys
App Insights: tracing, telemetry, failures
Entra ID: user authentication and RBAC
7) Security architecture

For your use case, this is very important.

Identity
User signs in with Microsoft Entra ID
Host gets user identity / role
Pass only required identity context to tools
Secrets

Keep these in Azure Key Vault:

Jira API token
Jira base URL
DB connection strings
Azure OpenAI key
Search service keys
Authorization

The host should check:

can this user create Jira tickets?
can this user access banking data?
which accounts or customers can they see?

MCP has an authorization model for HTTP-based transports, and enterprise readiness/security are active areas in the project roadmap.

Data protection
mask account numbers
redact PII in logs
avoid dumping raw statements into prompts unless needed
log all tool calls with user/time/result status
8) Data flow for Smart Banking

For Smart Banking, I’d split it into two paths:

A. Structured data path

For queries like:

balances
transactions
spending by category
monthly totals

Use:

Azure SQL / Delta tables
direct tool calls
deterministic SQL / API logic
B. Knowledge / RAG path

For queries like:

explain charges
summarize statement note
explain banking policy
search internal finance knowledge

Use:

document ingestion
chunking
embeddings
vector search / AI Search
retrieved context sent to LLM

So Smart Banking MCP Server can expose both:

operational tools
knowledge-search tools
9) Suggested MCP tool map
Smart Banking MCP tools
Tool: get_recent_transactions
Tool: get_transaction_types
Tool: get_spending_by_category
Tool: get_balance
Tool: search_knowledge_base
Tool: summarize_statement
Tool: detect_anomaly
Tool: generate_monthly_summary
JIRA MCP tools
Tool: create_ticket
Tool: get_ticket
Tool: search_tickets
Tool: add_comment
Tool: update_ticket_status
Tool: assign_ticket
Tool: list_open_tickets
Shared orchestration utilities
Tool: user_profile_lookup
Tool: permission_check
Tool: notification_send
Tool: audit_log_write
10) Conversation orchestration logic

A clean orchestration rule could be:

If prompt contains banking analytics intent:
    use Smart Banking tools

If prompt contains support / issue / incident / ticket intent:
    use JIRA tools

If prompt contains both:
    do multi-step plan
    call both servers
    merge result

Example:

User: “Raise a Jira issue because I can’t access transaction reports, and tell me the last successful refresh.”

Execution:

Smart Banking tool → get last report refresh
JIRA tool → create support ticket
Final answer merges both
11) Recommended folder structure

Since you asked earlier about keeping repos separate, this is the clean version.

Repo 1 — Smart Banking
smart-banking-app/
 ├── app/
 │   ├── api/
 │   ├── services/
 │   ├── data/
 │   ├── rag/
 │   └── main.py
 ├── mcp/
 │   ├── server.py
 │   ├── tools.py
 │   ├── resources.py
 │   └── prompts.py
 ├── requirements.txt
 └── Dockerfile
Repo 2 — JIRA
jira-agent/
 ├── app/
 │   ├── routes/
 │   ├── services/
 │   ├── models/
 │   └── main.py
 ├── mcp/
 │   ├── server.py
 │   ├── tools.py
 │   ├── resources.py
 │   └── prompts.py
 ├── requirements.txt
 └── Dockerfile
Repo 3 — MCP Host
mcp-host-orchestrator/
 ├── app/
 │   ├── chat/
 │   ├── llm/
 │   ├── mcp_clients/
 │   ├── auth/
 │   ├── memory/
 │   ├── guardrails/
 │   └── main.py
 ├── ui/
 ├── requirements.txt
 └── Dockerfile
12) Best-practice architecture choice for you

For your exact scenario, I recommend:

Option A — Best overall

One UI + one MCP host + two separate MCP servers

Why:

clean separation
easier maintenance
each app can evolve independently
easiest to add more later, like:
Email
Confluence
SharePoint
SQL DB tools
Option B — Faster prototype

Keep your existing banking app and JIRA app as normal APIs, then add:

thin MCP wrapper around each API
one central host

This is often the fastest way to retrofit MCP into existing apps.

13) Future expansion

Later you can add more MCP servers:

Confluence MCP Server → knowledge pages
Email MCP Server → send incident emails
Calendar MCP Server → schedule meetings
SQL MCP Server → query metadata
Document MCP Server → fetch PDFs and policies

That is aligned with MCP’s model of exposing capabilities from different servers to a host/client ecosystem.

14) Practical end-to-end example

User says:

“Create a Jira ticket saying Smart Banking transaction dashboard is not loading, and also show me the latest transaction count.”

What happens
UI sends prompt to MCP host
Host sends conversation + available tools to GPT
GPT decides:
call get_transaction_count() on Smart Banking
call create_jira_ticket() on JIRA
Host executes both via MCP clients
Servers return results
GPT formats final reply:
✅ Jira ticket created successfully
🆔 SCRUM-29
🔗 URL: ...

📊 Latest transaction count: 235
15) Plain-English summary

Think of it like this:

Chat UI = receptionist
MCP Host = manager
Smart Banking MCP Server = banking specialist
JIRA MCP Server = IT support specialist

The receptionist takes the request.
The manager decides which specialist to use.
The specialists do the work.
The manager combines the answer and gives one clean response back.
