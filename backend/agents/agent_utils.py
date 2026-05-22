"""
Shared utilities for agent JSON extraction.
"""
import json
import logging
import re

_log = logging.getLogger(__name__)


def parse_json_response(full_response: str, agent_name: str) -> dict:
    """
    Robustly extract a JSON object from a Claude agent response.

    Tries four strategies in order:
    1. Direct parse (response is already clean JSON)
    2. Strip all markdown fences, then parse
    3. raw_decode — scans for the first syntactically valid JSON object,
       ignoring any leading/trailing prose Claude may have added
    4. Fallback: return {"raw": text} so the caller never crashes
    """
    text = full_response.strip()

    # Strategy 1: direct parse
    try:
        result = json.loads(text)
        if isinstance(result, dict):
            return result
    except json.JSONDecodeError:
        pass

    # Strategy 2: strip markdown fences (handles ``` and ```json variants)
    stripped = re.sub(r"```(?:json)?\s*", "", text).strip()
    try:
        result = json.loads(stripped)
        if isinstance(result, dict):
            return result
    except json.JSONDecodeError:
        pass

    # Strategy 3: raw_decode — scans both original and fence-stripped text for the first
    # valid JSON object, ignoring any surrounding prose Claude may have added.
    decoder = json.JSONDecoder()
    for search_text in [text, stripped]:
        pos = 0
        while True:
            start = search_text.find("{", pos)
            if start == -1:
                break
            try:
                obj, _ = decoder.raw_decode(search_text, start)
                if isinstance(obj, dict):
                    return obj
            except json.JSONDecodeError:
                pass
            pos = start + 1

    _log.warning(
        "[%s] JSON extraction failed — first 400 chars: %.400s",
        agent_name,
        full_response,
    )
    return {"raw": full_response}
