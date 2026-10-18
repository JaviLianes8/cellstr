"""Extended grapheme cluster segmentation per UAX #29, using embedded UCD tables."""

from __future__ import annotations

from collections.abc import Iterator

from ._args import check_text
from ._props import EXT_PICT_BIT, GCB, INCB_SHIFT, prop

_CR = GCB["CR"]
_LF = GCB["LF"]
_CONTROL = GCB["Control"]
_EXTEND = GCB["Extend"]
_ZWJ = GCB["ZWJ"]
_RI = GCB["Regional_Indicator"]
_PREPEND = GCB["Prepend"]
_SPACING = GCB["SpacingMark"]
_L = GCB["L"]
_V = GCB["V"]
_T = GCB["T"]
_LV = GCB["LV"]
_LVT = GCB["LVT"]

_BREAKERS = frozenset({_CR, _LF, _CONTROL})
_AFTER_L = frozenset({_L, _V, _LV, _LVT})
_AFTER_LV_V = frozenset({_V, _T})
_AFTER_LVT_T = frozenset({_T})
_INCB_LINKER = 1
_INCB_CONSONANT = 2
_INCB_EXTEND = 3


def grapheme_ends(s: str) -> Iterator[int]:
    """Yield the end index (exclusive) of every extended grapheme cluster in ``s``.

    The last value yielded is ``len(s)``; nothing is yielded for the empty string.
    """
    if not s:
        return
    code = prop(ord(s[0]))
    prev = code & 0x0F
    ri_run = 1 if prev == _RI else 0
    incb = (code >> INCB_SHIFT) & 0x03
    after_linker = incb == _INCB_LINKER
    emoji = 1 if code & EXT_PICT_BIT else 0  # 1: pictograph Extend*, 2: then ZWJ
    for index in range(1, len(s)):
        code = prop(ord(s[index]))
        cur = code & 0x0F
        incb = (code >> INCB_SHIFT) & 0x03
        pict = code & EXT_PICT_BIT
        if not _joins(prev, cur, incb, pict, after_linker, emoji, ri_run):
            yield index
        after_linker = incb == _INCB_LINKER or (after_linker and incb == _INCB_EXTEND)
        if pict or (emoji == 1 and cur == _EXTEND):
            emoji = 1
        elif emoji == 1 and cur == _ZWJ:
            emoji = 2
        else:
            emoji = 0
        ri_run = ri_run + 1 if cur == _RI else 0
        prev = cur
    yield len(s)


def _joins(
    prev: int, cur: int, incb: int, pict: int, after_linker: bool, emoji: int, ri_run: int
) -> bool:
    """Return True when there is no boundary between ``prev`` and ``cur``."""
    if prev == _CR and cur == _LF:  # GB3
        return True
    if prev in _BREAKERS or cur in _BREAKERS:  # GB4, GB5
        return False
    if prev == _L and cur in _AFTER_L:  # GB6
        return True
    if prev in (_LV, _V) and cur in _AFTER_LV_V:  # GB7
        return True
    if prev in (_LVT, _T) and cur in _AFTER_LVT_T:  # GB8
        return True
    if cur in (_EXTEND, _ZWJ, _SPACING) or prev == _PREPEND:  # GB9, GB9a, GB9b
        return True
    if incb == _INCB_CONSONANT and after_linker:  # GB9c
        return True
    if pict and prev == _ZWJ and emoji == 2:  # GB11
        return True
    return prev == _RI and cur == _RI and ri_run % 2 == 1  # GB12, GB13


def iter_graphemes(text: str) -> Iterator[str]:
    """Return an iterator over the extended grapheme clusters of ``text`` (UAX #29).

    A grapheme cluster is what a reader perceives as one character: a base letter with
    its combining marks, a Hangul syllable built from jamo, an emoji ZWJ sequence, a
    flag made of two regional indicators, an Indic conjunct, or a CR LF pair. The
    clusters come left to right and concatenate back to ``text`` exactly. Escape
    sequences get no special treatment here; ``iter_cells`` handles terminal text.
    ``text`` is checked when the function is called, not when iteration starts.

    >>> [len(g) for g in iter_graphemes("e\\u0301\\U0001f1ea\\U0001f1f8!")]
    [2, 2, 1]
    """
    return _clusters(check_text(text))


def _clusters(text: str) -> Iterator[str]:
    start = 0
    for end in grapheme_ends(text):
        yield text[start:end]
        start = end
