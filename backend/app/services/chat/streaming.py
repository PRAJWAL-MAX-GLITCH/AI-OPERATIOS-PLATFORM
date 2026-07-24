"""
SSE Streaming Helpers
=====================
Server-Sent Events (SSE) utilities for streaming LLM tokens to clients.

Protocol:
  data: {"token": "Hello", "done": false}\n\n
  data: {"token": " world", "done": false}\n\n
  data: {"done": true, "session_id": "...", "citations": [...]}\n\n
  data: [DONE]\n\n
"""
from __future__ import annotations
import json
import asyncio
from typing import AsyncIterator, Optional
import structlog

logger = structlog.get_logger(__name__)


def format_sse_token(token: str) -> str:
    """Format a single token as an SSE data event."""
    data = json.dumps({"token": token, "done": False})
    return f"data: {data}\n\n"


def format_sse_final(
    session_id: str,
    citations: list[dict],
    total_tokens: int = 0,
) -> str:
    """Format the final SSE event with metadata."""
    data = json.dumps({
        "done":         True,
        "session_id":   session_id,
        "citations":    citations,
        "total_tokens": total_tokens,
    })
    return f"data: {data}\n\n"


def format_sse_error(error: str) -> str:
    """Format an SSE error event."""
    data = json.dumps({"error": error, "done": True})
    return f"data: {data}\n\n"


def format_sse_done() -> str:
    """Standard SSE stream termination signal."""
    return "data: [DONE]\n\n"


async def token_stream_to_sse(
    token_iterator: AsyncIterator[str],
    session_id: str,
    citations: list[dict],
) -> AsyncIterator[str]:
    """
    Convert a raw token iterator to SSE-formatted events.
    Yields SSE data strings ready to send as StreamingResponse.
    """
    try:
        token_count = 0
        async for token in token_iterator:
            if token:
                yield format_sse_token(token)
                token_count += 1
                # Small yield to allow other coroutines to run
                if token_count % 10 == 0:
                    await asyncio.sleep(0)

        # Send final metadata event
        yield format_sse_final(session_id, citations, token_count)
        yield format_sse_done()

    except asyncio.CancelledError:
        logger.info("sse_stream_cancelled", session_id=session_id)
        yield format_sse_error("Stream cancelled by client")
        raise

    except Exception as exc:
        logger.error("sse_stream_error", session_id=session_id, error=str(exc))
        yield format_sse_error(str(exc))
        yield format_sse_done()
