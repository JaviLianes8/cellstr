"""Lookup of the embedded Unicode properties: width class, grapheme and emoji data."""

from __future__ import annotations

from bisect import bisect_right

from ._ucd_data import (
    EMOJI_BIT,
    EXT_PICT_BIT,
    GCB_NAMES,
    INCB_SHIFT,
    MODIFIER_BIT,
    RUNS,
    TEXT_VS_BIT,
    UNICODE_VERSION,
    WIDTH_SHIFT,
)

__all__ = [
    "AMBIGUOUS",
    "EMOJI_BIT",
    "EXT_PICT_BIT",
    "GCB",
    "INCB_SHIFT",
    "MODIFIER_BIT",
    "TEXT_VS_BIT",
    "UNICODE_VERSION",
    "WIDTH_SHIFT",
    "prop",
]

GCB = {name: index for index, name in enumerate(GCB_NAMES)}
AMBIGUOUS = 3


def _decode(runs: str) -> tuple[list[int], list[int]]:
    """Expand the run tokens into parallel lists of run starts and property codes."""
    starts: list[int] = []
    codes: list[int] = []
    position = 0
    for token in runs.split():
        starts.append(position)
        codes.append(int(token[:3], 36))
        position += int(token[3:], 36)
    if position != 0x110000:
        raise RuntimeError("embedded Unicode tables do not cover the code space")
    return starts, codes


_STARTS, _CODES = _decode(RUNS)
_LATIN = tuple(_CODES[bisect_right(_STARTS, cp) - 1] for cp in range(0x300))


def prop(cp: int) -> int:
    """Return the packed property code of code point ``cp``.

    Bits 0-3 hold Grapheme_Cluster_Break (an index into ``GCB_NAMES``), bit 4 is
    Extended_Pictographic, bits 5-6 Indic_Conjunct_Break, bit 7 Emoji, bit 8
    Emoji_Modifier, bits 9-10 the width class (0 zero, 1 narrow, 2 wide, 3 ambiguous) and
    bit 11 tells that the code point followed by VS15 is a listed text presentation sequence.
    """
    if cp < 0x300:
        return _LATIN[cp]
    return _CODES[bisect_right(_STARTS, cp) - 1]
