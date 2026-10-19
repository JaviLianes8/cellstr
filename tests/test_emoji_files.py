"""Every sequence in the official emoji data files is one cluster of the documented width.

emoji-test.txt (the UTS #51 test data) and emoji-variation-sequences.txt are fetched into
data/ucd/ by scripts/fetch_upstream.py as pinned in data/ucd/MANIFEST.json; these tests
skip until then. The expected widths come from EastAsianWidth.txt and the rules GUIDE.md
states: an emoji sequence draws as one two-cell glyph, VS16 asks for emoji presentation
(two cells) and VS15 for text presentation (one cell, or the ambiguous policy for an East
Asian Ambiguous emoji).
"""

from __future__ import annotations

from collections import Counter

import pytest
from conftest import UCD, needs_ucd

from cellstr import cell_len, char_width, grapheme_width, iter_graphemes

pytestmark = needs_ucd


def _rows(name: str) -> list[tuple[str, str]]:
    """``(text, status)`` for each data line: the code points and the second field."""
    rows = []
    for raw in (UCD / name).read_text(encoding="utf-8").splitlines():
        data = raw.split("#", 1)[0]
        if ";" in data:
            points, status = (part.strip() for part in data.split(";")[:2])
            rows.append(("".join(chr(int(cp, 16)) for cp in points.split()), status))
    return rows


def _east_asian_width() -> dict[int, str]:
    found: dict[int, str] = {}
    for raw in (UCD / "EastAsianWidth.txt").read_text(encoding="utf-8").splitlines():
        data = raw.split("#", 1)[0]
        if ";" in data:
            span, value = (part.strip() for part in data.split(";"))
            low, _, high = span.partition("..")
            found.update(dict.fromkeys(range(int(low, 16), int(high or low, 16) + 1), value))
    return found


def test_every_emoji_test_sequence_is_one_cluster() -> None:
    rows = _rows("emoji-test.txt")
    statuses = Counter(status for _, status in rows)
    assert statuses == {
        "component": 9,
        "fully-qualified": 3963,
        "minimally-qualified": 1029,
        "unqualified": 243,
    }
    for text, _ in rows:
        assert list(iter_graphemes(text)) == [text], [hex(ord(ch)) for ch in text]


@pytest.mark.parametrize("ambiguous", [1, 2])
def test_qualified_sequences_and_components_are_two_cells(ambiguous: int) -> None:
    for text, status in _rows("emoji-test.txt"):
        if status != "unqualified":
            assert grapheme_width(text, ambiguous=ambiguous) == 2, [hex(ord(c)) for c in text]


def test_unqualified_emoji_keep_text_presentation_unless_joined() -> None:
    eaw = _east_asian_width()
    kinds: Counter[str] = Counter()
    for text, status in _rows("emoji-test.txt"):
        if status != "unqualified":
            continue
        points = [hex(ord(ch)) for ch in text]
        if len(text) == 1:  # a text-default emoji without VS16 keeps its own width
            expected = 2 if eaw[ord(text)] in ("W", "F") else 1
            assert char_width(text) == cell_len(text) == expected, points
            kinds[f"single code point, width {expected}"] += 1
        elif text.endswith("⃣"):  # a keycap without VS16: text presentation
            assert len(text) == 2 and cell_len(text) == 1, points
            kinds["keycap"] += 1
        else:  # a ZWJ sequence without VS16 still draws as one emoji glyph
            assert "‍" in text and cell_len(text) == 2, points
            kinds["ZWJ sequence"] += 1
    assert kinds == {
        "single code point, width 1": 201,
        "single code point, width 2": 6,
        "keycap": 12,
        "ZWJ sequence": 24,
    }


@pytest.mark.parametrize("ambiguous", [1, 2])
def test_variation_sequences_choose_the_presentation(ambiguous: int) -> None:
    eaw = _east_asian_width()
    styles: Counter[tuple[str, str]] = Counter()
    for text, style in _rows("emoji-variation-sequences.txt"):
        base = eaw[ord(text[0])]
        assert list(iter_graphemes(text)) == [text]
        # Text presentation narrows a wide emoji; an ambiguous one follows the policy.
        expected = 2 if style == "emoji style" else ambiguous if base == "A" else 1
        assert grapheme_width(text, ambiguous=ambiguous) == expected, (hex(ord(text[0])), style)
        styles[style, base] += 1
    counts = {"N": 168, "Na": 12, "A": 33, "W": 158}
    styles_expected = {(s, b): n for s in ("emoji style", "text style") for b, n in counts.items()}
    assert styles == styles_expected


def test_text_presentation_examples() -> None:
    trade_mark, watch = "™︎", "⌚︎"  # East Asian Ambiguous, Wide
    assert (grapheme_width(trade_mark), grapheme_width(trade_mark, ambiguous=2)) == (1, 2)
    assert (grapheme_width(watch), grapheme_width(watch, ambiguous=2)) == (1, 1)
    assert cell_len("™️", ambiguous=2) == cell_len("⌚️") == 2


def _emoji_bases() -> set[int]:
    bases: set[int] = set()
    for raw in (UCD / "emoji-data.txt").read_text(encoding="utf-8").splitlines():
        data = raw.split("#", 1)[0]
        if ";" in data and data.split(";")[1].strip() == "Emoji":
            low, _, high = data.split(";")[0].strip().partition("..")
            bases.update(range(int(low, 16), int(high or low, 16) + 1))
    return bases


@pytest.mark.parametrize("ambiguous", [1, 2])
def test_vs15_narrows_only_a_listed_text_presentation_sequence(ambiguous: int) -> None:
    # UTS #51 ED-8a: the only text presentation sequences are those the file lists; any
    # other variation selector after an emoji leaves the base as it is.
    listed = {text[0] for text, style in _rows("emoji-variation-sequences.txt")}
    eaw = _east_asian_width()
    kinds: Counter[str] = Counter()
    for cp in _emoji_bases():
        base = chr(cp)
        width = grapheme_width(base + "\ufe0e", ambiguous=ambiguous)
        if base in listed:
            assert width == (ambiguous if eaw[cp] == "A" else 1), hex(cp)
            kinds["listed"] += 1
        else:
            assert width == char_width(base, ambiguous=ambiguous), hex(cp)
            kinds["not listed"] += 1
    assert kinds == {"listed": 371, "not listed": 1076}
