"""ANSI escape sequence detection and removal."""

from __future__ import annotations

import re
from typing import NamedTuple

# One alternative per ECMA-48 escape family, longest first so a string introducer is never
# mistaken for a two-character escape:
#   CSI     ESC [ params intermediates final        colours (SGR), cursor moves
#   OSC     ESC ] ... BEL or ST                     titles, OSC 8 hyperlinks
#   strings ESC P / X / ^ / _ ... ST                DCS, SOS, PM, APC
#   nF      ESC intermediates final                 charset designation such as ESC ( B
#   Fp/Fe/Fs ESC one final byte                     ESC 7, ESC 8, ESC =, ESC c, ESC M
# An unterminated OSC or string sequence is never swallowed to the end of the text: at most
# its introducer counts as an escape and the rest is measured as text, so nothing visible
# silently disappears.
_ANSI_RE = re.compile(
    r"\x1b(?:"
    r"\[[0-?]*[ -/]*[@-~]"
    r"|\][^\x07\x1b]*(?:\x07|\x1b\\)"
    r"|[PX^_][^\x1b]*\x1b\\"
    r"|[ -/]+[0-~]"
    r"|[0-Z\\`-~]"
    r")"
)


def strip_ansi(text: str) -> str:
    """Return ``text`` with every ANSI escape sequence removed.

    Recognised: CSI sequences (SGR colours and styles, cursor movement), OSC sequences
    ended by BEL or ST (window titles, OSC 8 hyperlinks), DCS, SOS, PM and APC strings,
    charset designations and the single-byte escapes.

    >>> strip_ansi("\\x1b[1;31merror\\x1b[0m: \\x1b]8;;https://example.com\\x07docs\\x1b]8;;\\x07")
    'error: docs'
    """
    return _ANSI_RE.sub("", text)


class Segment(NamedTuple):
    """A run of ``text`` tagged as either an escape sequence or printable text."""

    text: str
    is_escape: bool


def segments(text: str) -> list[Segment]:
    """Split ``text`` into ordered printable and escape segments."""
    if "\x1b" not in text:
        return [Segment(text, False)] if text else []
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
