"""Tool resilience utilities — schema coercion, retry, timeout, circuit breaker."""

import asyncio
import copy
import logging
import time
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
            # ── Circuit breaker check ──
            if circuit_breaker.is_open(tool_name):
                logger.error(
                    f"[TOOL:{tool_name}] BLOCKED by circuit breaker — "
                    f"tool disabled after {settings.CIRCUIT_BREAKER_THRESHOLD} consecutive failures, "
                    f"cooldown {settings.CIRCUIT_BREAKER_COOLDOWN}s"
                )
                raise RuntimeError(
                    f"The {tool_name} service is temporarily unavailable due to repeated failures. "
                    f"It will be re-enabled automatically in a few minutes. "
                    f"Please try again later."
                )

            fixed = coerce_tool_args(kwargs, raw_schema)
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

            # ── All retries exhausted ──
            logger.error(
                f"[TOOL:{tool_name}] ALL {max_retries} RETRIES EXHAUSTED — "
                f"last error: {type(last_err).__name__}: {last_err}"
            )
            circuit_breaker.record_failure(tool_name)
            raise last_err  # type: ignore[misc]

        tool.coroutine = resilient_coroutine

    return tool
