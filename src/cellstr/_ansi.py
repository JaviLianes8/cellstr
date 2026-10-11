"""ANSI escape sequence detection and removal."""

from __future__ import annotations

import re
from typing import NamedTuple

# Matches CSI sequences (colours, cursor moves), OSC sequences (titles, hyperlinks)
# and the remaining two-character Fe escapes, but never their introducer alone.
_ANSI_RE = re.compile(r"\x1b(?:\[[0-?]*[ -/]*[@-~]|\][\s\S]*?(?:\x07|\x1b\\)|[@-Z\\^_])")


def strip_ansi(text: str) -> str:
    """Return ``text`` with every ANSI escape sequence removed."""
    return _ANSI_RE.sub("", text)


class Segment(NamedTuple):
    """A run of ``text`` tagged as either an escape sequence or printable text."""

    text: str
    is_escape: bool


def segments(text: str) -> list[Segment]:
    """Split ``text`` into ordered printable and escape segments."""
    out: list[Segment] = []
    last = 0
    for match in _ANSI_RE.finditer(text):
        if match.start() > last:
            out.append(Segment(text[last : match.start()], False))
        out.append(Segment(match.group(), True))
        last = match.end()
    if last < len(text):
        out.append(Segment(text[last:], False))
    return out
