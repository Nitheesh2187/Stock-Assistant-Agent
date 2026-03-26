import asyncio
import logging
import time
from collections.abc import AsyncGenerator
from contextlib import AsyncExitStack
from dataclasses import dataclass, field

from groq import APIError
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage
from langchain_groq import ChatGroq
from langchain_mcp_adapters.sessions import create_session
from langchain_mcp_adapters.tools import load_mcp_tools
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.services.chat_service import add_message, get_conversation_history
from backend.tool_utils import wrap_tool, friendly_error

logger = logging.getLogger(__name__)


@dataclass
class CachedExecutor:
    """An AgentExecutor with its memory and lock, cached per conversation."""
    executor: AgentExecutor
    memory: ConversationBufferMemory
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    last_used: float = field(default_factory=time.monotonic)


class AgentManager:
    """Singleton managing shared LLM + MCP tools, with per-conversation streaming."""

    def __init__(self):
        self.llm: ChatGroq | None = None
        self.tools: list = []
        self._tool_map: dict = {}
        self._executors: dict[str, CachedExecutor] = {}
        self._exit_stack: AsyncExitStack | None = None
        self._initialized = False

    async def initialize(self):
        """Initialize LLM and persistent MCP sessions. Called once at startup."""
        if self._initialized:
            return

        logger.info("Initializing AgentManager...")

        self.llm = ChatGroq(
            model_name=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
        )

        # Open persistent MCP sessions via AsyncExitStack so they stay alive
        # until shutdown() is called.
        self._exit_stack = AsyncExitStack()
        all_tools = []

        for server_name, connection in settings.mcp_servers.items():
            try:
                session = await self._exit_stack.enter_async_context(
                    create_session(connection)
                )
                await session.initialize()
                tools = await load_mcp_tools(session)
                all_tools.extend(tools)
                logger.info(f"MCP server '{server_name}' connected ({len(tools)} tools)")
            except Exception:
                logger.exception(f"Failed to connect to MCP server '{server_name}'")

        filtered = [t for t in all_tools if t.name in settings.REQUIRED_TOOLS]
        self.tools = [wrap_tool(t) for t in filtered]
        self._tool_map = {t.name: t for t in self.tools}

        logger.info(f"AgentManager ready. Tools: {list(self._tool_map.keys())}")
        self._initialized = True

    async def shutdown(self):
        """Gracefully close all MCP sessions and their subprocesses."""
        if self._exit_stack:
            logger.info("Shutting down MCP sessions...")
            await self._exit_stack.aclose()
            self._exit_stack = None
        self._executors.clear()
        self._initialized = False
        logger.info("AgentManager shut down.")

    # ── Direct MCP tool calls (for stock data REST endpoints) ────────────────

    async def call_tool(self, tool_name: str, arguments: dict) -> str:
        """Call an MCP tool directly and return its text output."""
        tool = self._tool_map.get(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found")
        result = await tool.ainvoke(arguments)
        return result

    # ── Streaming chat (for WebSocket) ───────────────────────────────────────

    def _cache_key(self, session_id: str, symbol: str) -> str:
        return f"{session_id}_{symbol}"

    async def _get_or_create_executor(
        self,
        db: AsyncSession,
        session_id: str,
        symbol: str,
        stock_name: str,
    ) -> CachedExecutor:
        """Return a cached executor for this session+symbol, or build a new one."""
        key = self._cache_key(session_id, symbol)
        cached = self._executors.get(key)
        if cached is not None:
            cached.last_used = time.monotonic()
            return cached

        # Cold start: build memory from stored history
        history = await get_conversation_history(db, session_id, symbol)
        memory = ConversationBufferMemory(
            memory_key="chat_history", return_messages=True
        )
        for msg in history:
            if msg["role"] == "user":
                memory.chat_memory.add_message(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                memory.chat_memory.add_message(AIMessage(content=msg["content"]))

        prompt = ChatPromptTemplate.from_messages([
            ("system", settings.SYSTEM_PROMPT.format(symbol=symbol, stock_name=stock_name)),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        agent = create_tool_calling_agent(
            llm=self.llm, tools=self.tools, prompt=prompt
        )
        executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            memory=memory,
            verbose=False,
            handle_parsing_errors=True,
            max_iterations=settings.AGENT_MAX_ITERATIONS,
        )

        entry = CachedExecutor(executor=executor, memory=memory)
        self._executors[key] = entry
        logger.info(f"Created new executor for session={session_id}, symbol={symbol}")
        return entry

    def _evict_stale_executors(self) -> None:
        """Remove executors (and their locks) that haven't been used within the TTL."""
        now = time.monotonic()
        stale = [
            key for key, entry in self._executors.items()
            if now - entry.last_used > settings.EXECUTOR_TTL_SECONDS
        ]
        for key in stale:
            del self._executors[key]
            logger.info(f"Evicted stale executor: {key}")

    async def chat_stream(
        self,
        db: AsyncSession,
        session_id: str,
        symbol: str,
        user_message: str,
    ) -> AsyncGenerator[dict, None]:
        """Stream a chat response for a given session + symbol.

        Handles history reads and message persistence internally.
        On failure, yields a user-friendly error message instead of raw exceptions.

        Yields:
            Dicts with type: token | tool_start | tool_end | retry | done | error
        """
        self._evict_stale_executors()

        stock_name = symbol.split(".")[0] if "." in symbol else symbol

        cached = await self._get_or_create_executor(db, session_id, symbol, stock_name)

        async with cached.lock:
            try:
                await add_message(db, session_id, symbol, "user", user_message)

                executor = cached.executor
                memory = cached.memory

                full_response = ""
                agent_input = user_message
                max_retries = settings.MAX_STREAM_RETRIES
                stream_start = time.monotonic()

                logger.info(
                    f"[STREAM:{symbol}] Starting for session={session_id}, "
                    f"max_retries={max_retries}"
                )

                for attempt in range(1, max_retries + 1):
                    full_response = ""
                    attempt_start = time.monotonic()

                    if attempt > 1:
                        logger.info(
                            f"[STREAM:{symbol}] Self-heal attempt {attempt}/{max_retries}"
                        )

                    try:
                        async for event in executor.astream_events(
                            {"input": agent_input, "chat_history": memory.chat_memory.messages},
                            version="v2",
                        ):
                            kind = event["event"]

                            if kind == "on_chat_model_stream":
                                chunk = event["data"]["chunk"]
                                if hasattr(chunk, "content") and chunk.content:
                                    full_response += chunk.content
                                    yield {"type": "token", "content": chunk.content}

                            elif kind == "on_tool_start":
                                logger.info(f"[STREAM:{symbol}] Tool started: {event.get('name', '')}")
                                yield {"type": "tool_start", "tool_name": event.get("name", "")}

                            elif kind == "on_tool_end":
                                logger.info(f"[STREAM:{symbol}] Tool ended: {event.get('name', '')}")
                                yield {"type": "tool_end", "tool_name": event.get("name", "")}

                        # Stream completed successfully
                        elapsed = time.monotonic() - stream_start
                        logger.info(
                            f"[STREAM:{symbol}] SUCCESS — "
                            f"attempt {attempt}/{max_retries}, "
                            f"total time {elapsed:.2f}s, "
                            f"response length {len(full_response)} chars"
                        )
                        break

                    except Exception as e:
                        attempt_elapsed = time.monotonic() - attempt_start
                        is_retryable = (
                            isinstance(e, APIError) and "tool call validation" in str(e)
                        )

                        if is_retryable and attempt < max_retries:
                            logger.warning(
                                f"[STREAM:{symbol}] RETRYABLE ERROR on attempt "
                                f"{attempt}/{max_retries} after {attempt_elapsed:.2f}s — "
                                f"{type(e).__name__}: {e}"
                            )
                            agent_input = (
                                f"Your previous attempt failed with this error: {e}\n"
                                f"Please try again with the original request: {user_message}\n"
                                f"Make sure to use correct parameter types for tool calls "
                                f"(booleans should be true/false, not strings)."
                            )
                            yield {"type": "retry", "attempt": attempt, "error": str(e)}
                            continue

                        logger.error(
                            f"[STREAM:{symbol}] NON-RETRYABLE ERROR on attempt "
                            f"{attempt}/{max_retries} after {attempt_elapsed:.2f}s — "
                            f"{type(e).__name__}: {e}"
                        )
                        raise

                # Save assistant response to DB
                if full_response:
                    await add_message(db, session_id, symbol, "assistant", full_response)

                yield {"type": "done", "full_response": full_response}

            except Exception as e:
                total_elapsed = time.monotonic() - stream_start if 'stream_start' in dir() else 0
                logger.error(
                    f"[STREAM:{symbol}] FINAL FAILURE for session={session_id} "
                    f"after {total_elapsed:.2f}s — {type(e).__name__}: {e}",
                    exc_info=True,
                )
                friendly = friendly_error(e)
                await add_message(db, session_id, symbol, "assistant", friendly)
                yield {"type": "error", "content": friendly}

    def remove_executor(self, session_id: str, symbol: str) -> None:
        """Remove cached executor (and its lock) for a conversation."""
        key = self._cache_key(session_id, symbol)
        self._executors.pop(key, None)


# Singleton instance
agent_manager = AgentManager()
