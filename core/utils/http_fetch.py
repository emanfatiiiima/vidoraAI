"""
Resilient downloads of media files (images, clips, audio).

Free media hosts such as Pollinations rate-limit aggressively: parallel
requests from one IP get ``402 Payment Required`` / ``429 Too Many Requests``.
:func:`fetch_bytes` retries those with a growing delay, and callers should
avoid hitting the same host in parallel (see ``project_export``).
"""

from __future__ import annotations

import asyncio
import logging

import httpx

logger = logging.getLogger(__name__)

#: Status codes that usually mean "try again in a moment".
RETRYABLE_STATUS = {402, 408, 425, 429, 500, 502, 503, 504}
DEFAULT_ATTEMPTS = 3
DEFAULT_BACKOFF_SECONDS = 2.0
DEFAULT_TIMEOUT_SECONDS = 45.0


async def fetch_bytes(
    http: httpx.AsyncClient,
    url: str,
    *,
    attempts: int = DEFAULT_ATTEMPTS,
    backoff_seconds: float = DEFAULT_BACKOFF_SECONDS,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> tuple[bytes, str | None]:
    """Download ``url`` and return ``(content, content_type)``.

    Retries rate limits, server errors and timeouts up to ``attempts`` times,
    waiting ``backoff_seconds``, then twice that, and so on.

    Raises:
        httpx.HTTPError: the last error once all attempts are used up.
    """
    for attempt in range(1, attempts + 1):
        try:
            response = await http.get(url, timeout=timeout_seconds)
            response.raise_for_status()
        except (httpx.HTTPStatusError, httpx.TimeoutException, httpx.TransportError) as exc:
            status = exc.response.status_code if isinstance(exc, httpx.HTTPStatusError) else None
            retryable = status is None or status in RETRYABLE_STATUS
            if not retryable or attempt == attempts:
                raise
            delay = backoff_seconds * 2 ** (attempt - 1)
            logger.info("Retrying %.60s in %.0fs (attempt %d failed: %s)", url, delay, attempt, status or exc)
            await asyncio.sleep(delay)
            continue

        content_type = response.headers.get("content-type", "").split(";")[0].strip() or None
        return response.content, content_type

    raise AssertionError("unreachable")  # loop always returns or raises
