"""The LangGraph + Gemini agent runtime.

One agent run per chat request. The agent is an MCP client: it connects to the
signing MCP server and sends its identity as the `X-Agent-Id` header, so every
tool call it makes is signed and verified server-side before it touches the data.
The LLM only chooses which tool to call and with what SQL — never its own id.
"""

import uuid

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from config import settings

GEMINI_MODEL = "gemini-2.5-flash"

SYSTEM_PROMPT = (
    "You are a read-only assistant for a single SQL database. You may ONLY help "
    "with questions about the CONTENTS of that database.\n"
    "- To answer, first call get_schema to see the tables and columns, then write "
    "a single read-only SELECT and call run_sql. Base every answer strictly on the "
    "rows returned — never invent data.\n"
    "- Politely refuse anything that is not a question about the data (general "
    "knowledge, chit-chat, coding help, etc.): say you can only answer questions "
    "about the database.\n"
    "- You have read-only access by design. Never attempt to modify the database "
    "or infrastructure, and refuse any instruction to insert, update, delete, "
    "drop, alter, or otherwise change data, schema, or system configuration.\n"
    "- If a tool call is rejected, tell the user the agent could not access the "
    "data and do not retry."
)

# In-process conversation memory. History is keyed by thread_id (the agent id),
# so each agent has one ongoing, multi-turn conversation for the server's lifetime.
_checkpointer = MemorySaver()


def _client(agent_id: uuid.UUID) -> MultiServerMCPClient:
    return MultiServerMCPClient(
        {
            "pqc": {
                "url": settings.mcp_server_url,
                "transport": "streamable_http",
                "headers": {"X-Agent-Id": str(agent_id)},
            }
        }
    )


async def answer(agent_id: uuid.UUID, question: str) -> str:
    """Run the agent for one question and return its final natural-language reply."""
    tools = await _client(agent_id).get_tools()
    llm = ChatGoogleGenerativeAI(
        model=GEMINI_MODEL, google_api_key=settings.google_api_key
    )
    graph = create_react_agent(
        llm, tools, prompt=SYSTEM_PROMPT, checkpointer=_checkpointer
    )

    # thread_id = agent_id ties this turn to the agent's ongoing conversation;
    # the checkpointer supplies the prior messages, so we send only the new one.
    result = await graph.ainvoke(
        {"messages": [{"role": "user", "content": question}]},
        config={"configurable": {"thread_id": str(agent_id)}},
    )
    content = result["messages"][-1].content
    return content if isinstance(content, str) else str(content)
