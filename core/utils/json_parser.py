"""
Helpers for parsing JSON returned by LLMs.

LLMs often wrap JSON in markdown code fences or wrap a list inside an object
(e.g. ``{"topics": [...]}`` when JSON mode forces an object). These helpers
normalise those quirks.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# Matches ```json and ``` fences anywhere in the text.
_CODE_FENCE_RE = re.compile(r"```json|```")


def parse_ai_json(text: str | None) -> Any | None:
    """Parse JSON produced by an LLM.

    - Strips markdown code fences.
    - If the result is an object with exactly one key whose value is a list,
      that list is returned instead (``{"items": [...]}`` -> ``[...]``).

    Returns ``None`` when the text is not valid JSON.
    """
    if not text:
        return None

    cleaned = _CODE_FENCE_RE.sub("", text).strip()
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning("Could not parse AI response as JSON: %.200s", cleaned)
        return None

    if isinstance(data, dict) and len(data) == 1:
        (only_value,) = data.values()
        if isinstance(only_value, list):
            return only_value
    return data


def parse_ai_string_list(text: str | None) -> list[str] | None:
    """Parse an LLM response that should be a JSON array of strings.

    Non-string items are dropped. Returns ``None`` if the response is not a
    JSON array or contains no usable strings.
    """
    data = parse_ai_json(text)
    if not isinstance(data, list):
        return None
    items = [item.strip() for item in data if isinstance(item, str) and item.strip()]
    return items or None
