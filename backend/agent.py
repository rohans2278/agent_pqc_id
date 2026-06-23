"""The LangGraph + Gemini agent runtime.

One agent run per chat request. The agent is an MCP client: it connects to the
signing MCP server and sends its identity as the `X-Agent-Id` header, so every
tool call it makes is signed and verified server-side before it touches the data.
The LLM only chooses which tool to call and with what SQL — never its own id.
"""

import uuid

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

from config import settings

GEMINI_MODEL = "gemini-2.0-flash"

SYSTEM_PROMPT = (
    "You answer questions about a SQL database. First call get_schema to learn "
    "the available tables and columns. Then write a single read-only SELECT "
    "query and call run_sql to execute it. Base your answer only on the rows "
    "returned. If a tool call is rejected, tell the user the agent could not "
    "access the data and do not retry."
)


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
    graph = create_react_agent(llm, tools, prompt=SYSTEM_PROMPT)

    result = await graph.ainvoke(
        {"messages": [{"role": "user", "content": question}]}
    )
    content = result["messages"][-1].content
    return content if isinstance(content, str) else str(content)
