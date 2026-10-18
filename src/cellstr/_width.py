"""Display width of code points, grapheme clusters and whole strings."""

from __future__ import annotations

from ._ansi import segments
from ._args import check_ambiguous, check_text, show
from ._graphemes import grapheme_ends
from ._props import AMBIGUOUS, EMOJI_BIT, EXT_PICT_BIT, GCB, MODIFIER_BIT, WIDTH_SHIFT, prop

_RI = GCB["Regional_Indicator"]
_VS15 = "\ufe0e"
_VS16 = "\ufe0f"
_ZWJ = "\u200d"
_TAGS = range(0xE0020, 0xE0080)


def code_width(code: int, ambiguous: int) -> int:
    """Width of a code point from its packed property code."""
    width = code >> WIDTH_SHIFT
    return ambiguous if width == AMBIGUOUS else width


def char_width(char: str, *, ambiguous: int = 1) -> int:
    """Display cells a single code point occupies on its own: 0, 1 or 2.

    U+0000, the C0 and C1 controls, DEL, nonspacing and enclosing marks (Mn, Me), format
    characters (Cf, except SOFT HYPHEN) and Hangul medial vowels and final consonants are
    zero. East Asian Wide and Fullwidth characters are two. East Asian Ambiguous
    characters take ``ambiguous`` cells (1 by default, 2 for CJK terminals). Everything
    else is one. This is Markus Kuhn's wcwidth, except that controls are 0 instead of -1.

    >>> char_width("a"), char_width("\\u4f60"), char_width("\\u0301"), char_width("\\u2500")
    (1, 2, 0, 1)
    >>> char_width("\\u2500", ambiguous=2)
    2
    """
    char = check_text(char, "char")
    if len(char) != 1:
        raise ValueError(f"char must be a single code point, not {show(char)}")
    return code_width(prop(ord(char)), check_ambiguous(ambiguous))


def _emoji_sequence(rest: str) -> bool:
    """True when ``rest`` (after an emoji base) holds a modifier, a tag or a ZWJ + pictograph."""
    joined = False
    for ch in rest:
        code = prop(ord(ch))
        if code & MODIFIER_BIT or ord(ch) in _TAGS or (joined and code & EXT_PICT_BIT):
            return True
        joined = joined or ch == _ZWJ
    return False


def cluster_width(cluster: str, ambiguous: int) -> int:
    """Width of one grapheme cluster, without validating the input."""
    code = prop(ord(cluster[0]))
    if len(cluster) == 1:
        return code_width(code, ambiguous)
    rest = cluster[1:]
    if code & (EMOJI_BIT | EXT_PICT_BIT) and not code & MODIFIER_BIT:
        # A variation selector only counts right after the base.
        if code & EMOJI_BIT and rest[0] in (_VS15, _VS16):
            return 1 if rest[0] == _VS15 else 2
        if _emoji_sequence(rest):
            return 2
    if code & 0x0F == _RI and prop(ord(rest[0])) & 0x0F == _RI:
        return 2
    return sum(code_width(prop(ord(ch)), ambiguous) for ch in cluster)


def grapheme_width(cluster: str, *, ambiguous: int = 1) -> int:
    """Display cells one extended grapheme cluster occupies.

    ``cluster`` must be exactly one cluster, such as an item from ``iter_graphemes``.
    Emoji sequences draw as a single glyph: an emoji followed by VS16 (U+FE0F), a skin
    tone modifier, a ZWJ sequence, a tag sequence or a pair of regional indicators (a
    flag) is two cells, and an emoji followed by VS15 (U+FE0E) is one. Any other cluster
    is the sum of its code points, which keeps combining marks at zero and conjoining
    Hangul jamo at the width of the syllable.

    >>> grapheme_width("\\U0001f468\\u200d\\U0001f469\\u200d\\U0001f467")
    2
    >>> grapheme_width("\\u2764\\ufe0f"), grapheme_width("\\u2764"), grapheme_width("e\\u0301")
    (2, 1, 1)
    """
    cluster = check_text(cluster, "cluster")
    if not cluster or next(grapheme_ends(cluster)) != len(cluster):
        raise ValueError(f"cluster must be exactly one grapheme cluster, not {show(cluster)}")
    return cluster_width(cluster, check_ambiguous(ambiguous))


def _plain_width(text: str, ambiguous: int) -> int:
    if text.isascii():
        return sum(1 for ch in text if " " <= ch <= "~")
    total = 0
    start = 0
    for end in grapheme_ends(text):
        total += cluster_width(text[start:end], ambiguous)
        start = end
    return total


def text_width(text: str, ambiguous: int) -> int:
    """Width of ``text`` with no tab stops to honour; an escape sequence ends a cluster."""
    if "\x1b" not in text:
        return _plain_width(text, ambiguous)
    return sum(_plain_width(s.text, ambiguous) for s in segments(text) if not s.is_escape)
