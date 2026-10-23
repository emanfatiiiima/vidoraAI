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

    Also accepts the shapes smaller local models (Ollama's JSON mode forces an
    object) tend to produce instead of a bare array:

    - ``{"topics": [...], "note": "..."}`` -> the first list value
    - ``{"1": "idea", "2": "idea"}``       -> the string values
    - ``[{"title": "idea"}, ...]``          -> the first string of each object

    Returns ``None`` if no usable strings are found.
    """
    data = parse_ai_json(text)
    if isinstance(data, dict):
        lists = [value for value in data.values() if isinstance(value, list)]
        data = lists[0] if lists else list(data.values())
    if not isinstance(data, list):
        return None
    items = [_first_string(item) for item in data]
    # Some models also quote each title: "\"My title\"" -> "My title".
    items = [item.strip().strip("\"“”").strip() for item in items if item]
    return [item for item in items if item] or None


def _first_string(item: Any) -> str | None:
    """``item`` itself if it's a string, else the first string value of an object."""
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        return next((v for v in item.values() if isinstance(v, str) and v.strip()), None)
    return None
