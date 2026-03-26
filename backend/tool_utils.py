"""Tool resilience utilities — schema coercion, retry, timeout, circuit breaker, cache."""

import asyncio
import copy
import json
import logging
import time
from dataclasses import dataclass
from typing import Any

from groq import APIError
from langchain_core.tools import StructuredTool

from backend.config import settings

logger = logging.getLogger(__name__)


# ── Circuit Breaker ──────────────────────────────────────────────────────────

class CircuitBreaker:
    """Tracks consecutive failures per tool. After THRESHOLD failures,
    the tool is temporarily disabled for COOLDOWN seconds."""

    def __init__(self):
        self._failures: dict[str, int] = {}
        self._tripped_at: dict[str, float] = {}

    def is_open(self, tool_name: str) -> bool:
        """Return True if the circuit is open (tool is disabled)."""
        if tool_name not in self._tripped_at:
            return False
        elapsed = time.monotonic() - self._tripped_at[tool_name]
        if elapsed >= settings.CIRCUIT_BREAKER_COOLDOWN:
            self._reset(tool_name)
            logger.info(
                f"Circuit breaker reset for tool '{tool_name}' "
                f"after {settings.CIRCUIT_BREAKER_COOLDOWN}s cooldown"
            )
            return False
        return True

    def record_success(self, tool_name: str) -> None:
        """Reset failure count on success."""
        if tool_name in self._failures:
            self._failures[tool_name] = 0

    def record_failure(self, tool_name: str) -> None:
        """Record a failure. Trips the circuit if threshold is reached."""
        self._failures[tool_name] = self._failures.get(tool_name, 0) + 1
        if self._failures[tool_name] >= settings.CIRCUIT_BREAKER_THRESHOLD:
            self._tripped_at[tool_name] = time.monotonic()
            logger.warning(
                f"Circuit breaker TRIPPED for tool '{tool_name}' after "
                f"{self._failures[tool_name]} consecutive failures. "
                f"Disabled for {settings.CIRCUIT_BREAKER_COOLDOWN}s."
            )

    def _reset(self, tool_name: str) -> None:
        self._failures.pop(tool_name, None)
        self._tripped_at.pop(tool_name, None)


circuit_breaker = CircuitBreaker()


# ── Tool Cache ───────────────────────────────────────────────────────────────

@dataclass
class CacheEntry:
    result: Any
    cached_at: float  # time.monotonic


class ToolCache:
    """In-memory TTL cache for tool call results.
    Also serves stale data as fallback when a tool call fails."""

    def __init__(self):
        self._store: dict[str, CacheEntry] = {}

    def _key(self, tool_name: str, arguments: dict) -> str:
        args_str = json.dumps(arguments, sort_keys=True, default=str)
        return f"{tool_name}:{args_str}"

    def get(self, tool_name: str, arguments: dict) -> tuple[Any | None, bool]:
        """Return (cached_result, is_fresh). Returns (None, False) on miss."""
        key = self._key(tool_name, arguments)
        entry = self._store.get(key)
        if entry is None:
            return None, False

        ttl = settings.TOOL_CACHE_TTL.get(tool_name, 0)
        age = time.monotonic() - entry.cached_at
        is_fresh = age < ttl
        return entry.result, is_fresh

    def get_stale(self, tool_name: str, arguments: dict) -> Any | None:
        """Return cached result regardless of TTL (for fallback). None if no entry."""
        key = self._key(tool_name, arguments)
        entry = self._store.get(key)
        if entry is None:
            return None
        age = time.monotonic() - entry.cached_at
        logger.info(
            f"[CACHE:{tool_name}] Returning STALE data (age={age:.0f}s) as fallback"
        )
        return entry.result

    def put(self, tool_name: str, arguments: dict, result: Any) -> None:
        key = self._key(tool_name, arguments)
        self._store[key] = CacheEntry(result=result, cached_at=time.monotonic())
        logger.debug(f"[CACHE:{tool_name}] Stored result, key={key[:80]}")

    def clear(self) -> None:
        self._store.clear()


tool_cache = ToolCache()


# ── Output Guardrail ─────────────────────────────────────────────────────────

# Phrases that indicate trading advice — checked case-insensitively
_UNSAFE_PHRASES = [
    "you should buy",
    "you should sell",
    "you should hold",
    "i recommend buying",
    "i recommend selling",
    "i recommend holding",
    "i suggest buying",
    "i suggest selling",
    "consider buying",
    "consider selling",
    "consider purchasing",
    "consider investing",
    "strong buy",
    "strong sell",
    "it is a good time to buy",
    "it is a good time to sell",
    "it's a good time to buy",
    "it's a good time to sell",
    "target price of",
    "price target of",
    "i advise you to",
    "my recommendation is",
    "you should invest in",
    "accumulate this stock",
    "add to your portfolio",
    "exit your position",
    "book profits",
    "buy at current levels",
    "sell at current levels",
]


def check_guardrail(response: str) -> str:
    """Check the LLM response for trading advice. If flagged, append a disclaimer.
    Returns the (possibly modified) response."""
    response_lower = response.lower()
    flagged = [phrase for phrase in _UNSAFE_PHRASES if phrase in response_lower]

    if flagged:
        logger.warning(
            f"[GUARDRAIL] Response flagged for trading advice — "
            f"matched phrases: {flagged}"
        )
        return response + settings.GUARDRAIL_DISCLAIMER

    return response


# ── User-friendly error messages ─────────────────────────────────────────────

def friendly_error(error: Exception) -> str:
    """Convert a raw exception into a user-friendly message."""
    err_str = str(error)

    if isinstance(error, (TimeoutError, asyncio.TimeoutError)):
        return (
            "I'm sorry, but the data service is taking too long to respond right now. "
            "This could be due to high demand or temporary server issues. "
            "Please try again in a moment."
        )

    if isinstance(error, APIError) and "tool call validation" in err_str:
        return (
            "I encountered a technical issue while processing your request. "
            "I've already tried to correct it, but it persisted. "
            "Please try rephrasing your question or ask about something else."
        )

    if "rate limit" in err_str.lower() or "429" in err_str:
        return (
            "I've hit the rate limit for the data service. "
            "Please wait a minute and try again."
        )

    if "circuit breaker" in err_str.lower() or "temporarily unavailable" in err_str.lower():
        return err_str  # already friendly

    return (
        "I'm sorry, I wasn't able to complete your request due to a temporary issue. "
        "Please try again shortly. If the problem persists, try asking a different question."
    )


# ── Tool schema coercion ────────────────────────────────────────────────────

def coerce_schema_types(schema: dict) -> dict:
    """Widen boolean/integer fields to also accept string equivalents.
    Prevents Groq from rejecting tool calls where the LLM outputs "true" instead of true."""
    schema = copy.deepcopy(schema)
    props = schema.get("properties", {})
    for _, prop_def in props.items():
        prop_type = prop_def.get("type")
        if prop_type == "boolean":
            prop_def.pop("type", None)
            prop_def["anyOf"] = [{"type": "boolean"}, {"type": "string"}]
        elif prop_type == "integer":
            prop_def.pop("type", None)
            prop_def["anyOf"] = [{"type": "integer"}, {"type": "string"}]
    return schema


def coerce_tool_args(arguments: dict[str, Any], schema: dict) -> dict[str, Any]:
    """Coerce string values to their expected types based on the tool's JSON schema."""
    props = schema.get("properties", {})
    coerced = dict(arguments)
    for key, value in coerced.items():
        if not isinstance(value, str) or key not in props:
            continue
        expected_type = props[key].get("type")
        if expected_type == "boolean":
            coerced[key] = value.lower() in ("true", "1", "yes")
        elif expected_type == "integer":
            try:
                coerced[key] = int(value)
            except ValueError:
                pass
        elif expected_type == "number":
            try:
                coerced[key] = float(value)
            except ValueError:
                pass
    return coerced


# ── Tool wrapper (coercion + retry + timeout + circuit breaker) ──────────────

def wrap_tool(tool: StructuredTool) -> StructuredTool:
    """Wrap a LangChain tool with:
    1. Schema widening — so Groq accepts string representations of booleans/integers
    2. Argument coercion — converts "true" → true before calling the MCP server
    3. Retry with timeout — retries failed tool calls, each with a timeout
    4. Circuit breaker — disables tool after too many consecutive failures
    """
    original_schema = tool.args_schema
    original_coroutine = tool.coroutine

    if isinstance(original_schema, dict):
        tool.args_schema = coerce_schema_types(original_schema)

    if original_coroutine:
        raw_schema = original_schema if isinstance(original_schema, dict) else {}
        tool_name = tool.name

        async def resilient_coroutine(**kwargs):
            fixed = coerce_tool_args(kwargs, raw_schema)
            ttl = settings.TOOL_CACHE_TTL.get(tool_name, 0)

            # ── 1. Check fresh cache ──
            if ttl > 0:
                cached_result, is_fresh = tool_cache.get(tool_name, fixed)
                if is_fresh:
                    logger.info(f"[TOOL:{tool_name}] CACHE HIT (fresh, ttl={ttl}s)")
                    return cached_result

            # ── 2. Circuit breaker check ──
            if circuit_breaker.is_open(tool_name):
                logger.error(
                    f"[TOOL:{tool_name}] BLOCKED by circuit breaker — "
                    f"tool disabled after {settings.CIRCUIT_BREAKER_THRESHOLD} consecutive failures, "
                    f"cooldown {settings.CIRCUIT_BREAKER_COOLDOWN}s"
                )
                # Try stale cache as fallback before raising
                if ttl > 0:
                    stale = tool_cache.get_stale(tool_name, fixed)
                    if stale is not None:
                        return stale
                raise RuntimeError(
                    f"The {tool_name} service is temporarily unavailable due to repeated failures. "
                    f"It will be re-enabled automatically in a few minutes. "
                    f"Please try again later."
                )

            # ── 3. Call MCP server with retry + timeout ──
            last_err = None
            max_retries = settings.TOOL_CALL_RETRIES

            logger.info(
                f"[TOOL:{tool_name}] Invoking with args={fixed}, "
                f"timeout={settings.TOOL_CALL_TIMEOUT}s, max_retries={max_retries}"
            )

            for attempt in range(1, max_retries + 1):
                start = time.monotonic()
                try:
                    result = await asyncio.wait_for(
                        original_coroutine(**fixed),
                        timeout=settings.TOOL_CALL_TIMEOUT,
                    )
                    elapsed = time.monotonic() - start
                    logger.info(
                        f"[TOOL:{tool_name}] SUCCESS on attempt {attempt}/{max_retries} "
                        f"in {elapsed:.2f}s"
                    )
                    circuit_breaker.record_success(tool_name)

                    # Store in cache
                    if ttl > 0:
                        tool_cache.put(tool_name, fixed, result)

                    return result

                except asyncio.TimeoutError:
                    elapsed = time.monotonic() - start
                    last_err = TimeoutError(
                        f"Tool '{tool_name}' timed out after {settings.TOOL_CALL_TIMEOUT}s"
                    )
                    logger.warning(
                        f"[TOOL:{tool_name}] TIMEOUT after {elapsed:.2f}s "
                        f"(attempt {attempt}/{max_retries})"
                    )

                except Exception as e:
                    elapsed = time.monotonic() - start
                    last_err = e
                    logger.warning(
                        f"[TOOL:{tool_name}] ERROR on attempt {attempt}/{max_retries} "
                        f"after {elapsed:.2f}s — {type(e).__name__}: {e}"
                    )

                if attempt < max_retries:
                    backoff = 1 * attempt
                    logger.info(
                        f"[TOOL:{tool_name}] Retrying in {backoff}s "
                        f"(attempt {attempt + 1}/{max_retries})..."
                    )
                    await asyncio.sleep(backoff)

            # ── 4. All retries exhausted — try stale cache as fallback ──
            logger.error(
                f"[TOOL:{tool_name}] ALL {max_retries} RETRIES EXHAUSTED — "
                f"last error: {type(last_err).__name__}: {last_err}"
            )
            circuit_breaker.record_failure(tool_name)

            if ttl > 0:
                stale = tool_cache.get_stale(tool_name, fixed)
                if stale is not None:
                    logger.info(
                        f"[TOOL:{tool_name}] Returning stale cache as fallback "
                        f"after all retries failed"
                    )
                    return stale

            raise last_err  # type: ignore[misc]

        tool.coroutine = resilient_coroutine

    return tool
