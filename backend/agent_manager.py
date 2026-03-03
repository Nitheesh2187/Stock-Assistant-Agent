import asyncio
import json
import logging
import sys
from collections.abc import AsyncGenerator

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage
from langchain_groq import ChatGroq
from langchain_mcp_adapters.client import MultiServerMCPClient

from backend.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are analyzing {symbol} ({stock_name}).
You are a helpful stock market assistant with access to real-time stock data, financial analysis tools, and web scraping capabilities.

You can help with:
- Real-time stock quotes and price data
- Company fundamentals and financial metrics
- Latest stock news and market developments
- Comprehensive stock analysis
- Web scraping for additional research

You provide information for educational and research purposes only.
Never recommend buying, selling, or holding any specific stock.
Always present data clearly and explain your reasoning."""


class AgentManager:
    """Singleton managing shared LLM + MCP tools, with per-conversation streaming."""

    def __init__(self):
        self.llm: ChatGroq | None = None
        self.tools: list = []
        self._tool_map: dict = {}
        self._conversation_locks: dict[str, asyncio.Lock] = {}
        self._initialized = False

    async def initialize(self):
        """Initialize LLM and MCP tools. Called once during app lifespan startup."""
        if self._initialized:
            return

        logger.info("Initializing AgentManager...")

        # Initialize LLM
        self.llm = ChatGroq(
            model_name=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
        )

        # Connect to MCP servers and get tools
        self._mcp_client = MultiServerMCPClient(
            {
                "stock_tools": {
                    "command": sys.executable,
                    "args": ["-m", "stock_mcp.server"],
                    "transport": "stdio",
                },
                "firecrawl-mcp": {
                    "command": "npx",
                    "args": ["-y", "firecrawl-mcp"],
                    "env": {"FIRECRAWL_API_KEY": settings.FIRECRAWL_API_KEY},
                    "transport": "stdio",
                },
            }
        )

        all_tools = await self._mcp_client.get_tools()

        required = {
            "get_stock_quote",
            "get_stock_fundamentals",
            "get_stock_news",
            "get_stock_analysis",
            "firecrawl_scrape",
        }
        self.tools = [t for t in all_tools if t.name in required]
        self._tool_map = {t.name: t for t in self.tools}

        logger.info(f"AgentManager ready. Tools: {list(self._tool_map.keys())}")
        self._initialized = True

    # ── Direct MCP tool calls (for stock data REST endpoints) ────────────────

    async def call_tool(self, tool_name: str, arguments: dict) -> str:
        """Call an MCP tool directly and return its text output."""
        tool = self._tool_map.get(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found")
        result = await tool.ainvoke(arguments)
        return result

    # ── Streaming chat (for WebSocket) ───────────────────────────────────────

    def _get_lock(self, conversation_id: str) -> asyncio.Lock:
        if conversation_id not in self._conversation_locks:
            self._conversation_locks[conversation_id] = asyncio.Lock()
        return self._conversation_locks[conversation_id]

    async def chat_stream(
        self,
        conversation_id: str,
        user_message: str,
        symbol: str,
        stock_name: str,
        history: list[dict],
    ) -> AsyncGenerator[dict, None]:
        """Stream a chat response for a given conversation.

        Args:
            conversation_id: Unique conversation ID (for locking).
            user_message: The user's input.
            symbol: Stock ticker symbol.
            stock_name: Human-readable stock name.
            history: List of {"role": ..., "content": ...} dicts from DB.

        Yields:
            Dicts with type: token | tool_start | tool_end | done | error
        """
        lock = self._get_lock(conversation_id)

        async with lock:
            try:
                # Build memory from DB history
                memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
                for msg in history:
                    if msg["role"] == "user":
                        memory.chat_memory.add_message(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        memory.chat_memory.add_message(AIMessage(content=msg["content"]))

                # Build prompt with stock context
                prompt = ChatPromptTemplate.from_messages([
                    ("system", SYSTEM_PROMPT.format(symbol=symbol, stock_name=stock_name)),
                    MessagesPlaceholder(variable_name="chat_history"),
                    ("human", "{input}"),
                    MessagesPlaceholder(variable_name="agent_scratchpad"),
                ])

                agent = create_tool_calling_agent(llm=self.llm, tools=self.tools, prompt=prompt)
                executor = AgentExecutor(
                    agent=agent,
                    tools=self.tools,
                    memory=memory,
                    verbose=False,
                    handle_parsing_errors=True,
                    max_iterations=5,
                )

                full_response = ""
                async for event in executor.astream_events(
                    {"input": user_message, "chat_history": memory.chat_memory.messages},
                    version="v2",
                ):
                    kind = event["event"]

                    if kind == "on_chat_model_stream":
                        chunk = event["data"]["chunk"]
                        if hasattr(chunk, "content") and chunk.content:
                            full_response += chunk.content
                            yield {"type": "token", "content": chunk.content}

                    elif kind == "on_tool_start":
                        yield {"type": "tool_start", "tool_name": event.get("name", "")}

                    elif kind == "on_tool_end":
                        yield {"type": "tool_end", "tool_name": event.get("name", "")}

                yield {"type": "done", "full_response": full_response}

            except Exception as e:
                logger.exception("Error in chat_stream")
                yield {"type": "error", "content": str(e)}

    def remove_lock(self, conversation_id: str):
        self._conversation_locks.pop(conversation_id, None)


# Singleton instance
agent_manager = AgentManager()
