"""Clipboard URL extractor.

`extract_urls()` parses URLs out of clipboard text for the manual
"Add from clipboard" flow. There is intentionally no auto-watching:
all clipboard imports are user-initiated.
"""
from __future__ import annotations

import re

URL_RE = re.compile(r"(https?://\S+|ftp://\S+|magnet:\?\S+)", re.IGNORECASE)


def extract_urls(text: str) -> list[str]:
    if not text:
        return []
    seen: set[str] = set()
    out: list[str] = []
    for raw in URL_RE.findall(text):
        url = raw.rstrip(").,;'\"")
        if url not in seen:
            seen.add(url)
            out.append(url)
    return out
