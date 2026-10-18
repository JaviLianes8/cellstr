"""Cross-check against the ``wcwidth`` package 0.9.2, used here only as a test oracle.

wcwidth 0.9.2 (released 2026-10-05) is an independent implementation built on the same
Unicode 18.0.0 data, with its own published rules
(https://wcwidth.readthedocs.io/en/latest/specs.html, read on 2026-10-18). Every
disagreement must belong to one of the policy differences documented in GUIDE.md
("Differences from other measurers"); the counts are pinned so a new one fails:

* spacing marks (Mc): 1 cell here (2 when East Asian Wide), as in Kuhn's rules and glibc;
  0 in wcwidth's single character function, and a cluster holding one is capped at 2 there.
* a lone regional indicator: 1 here (East_Asian_Width N), 2 in wcwidth.
* an emoji sequence whose first code point is a one-cell emoji not followed by VS16, with a
  skin tone or a ZWJ: 2 here (an emoji sequence draws as one wide glyph), 1 in wcwidth.
"""

from __future__ import annotations

import importlib.metadata
import random
from collections import Counter

import pytest
from conftest import UCD, needs_ucd

from cellstr import cell_len, char_width, grapheme_width, iter_graphemes

wcwidth = pytest.importorskip("wcwidth")
pytestmark = [
    needs_ucd,
    pytest.mark.skipif(
        importlib.metadata.version("wcwidth") != "0.9.2",
        reason="the documented differences are pinned to wcwidth 0.9.2",
    ),
]
REGIONAL = range(0x1F1E6, 0x1F200)


def _spacing_marks() -> set[int]:
    marks: set[int] = set()
    for raw in (UCD / "DerivedGeneralCategory.txt").read_text(encoding="utf-8").splitlines():
        data = raw.split("#", 1)[0]
        if data.split(";")[-1].strip() == "Mc":
            low, _, high = data.split(";")[0].strip().partition("..")
            marks.update(range(int(low, 16), int(high or low, 16) + 1))
    return marks


@pytest.mark.parametrize("ambiguous", [1, 2])
def test_every_code_point_agrees_or_has_a_documented_reason(ambiguous: int) -> None:
    marks = _spacing_marks()
    reasons: Counter[str] = Counter()
    for cp in range(0x110000):
        ours = char_width(chr(cp), ambiguous=ambiguous)
        theirs = max(0, wcwidth.wcwidth(chr(cp), ambiguous_width=ambiguous))
        if ours == theirs:
            reasons["agree"] += 1
        elif cp in marks and theirs == 0:
            reasons["spacing mark"] += 1
        elif cp in REGIONAL and (ours, theirs) == (1, 2):
            reasons["lone regional indicator"] += 1
        else:
            reasons[f"unexplained {cp:04X}"] += 1
    assert reasons == {"agree": 1_113_609, "spacing mark": 477, "lone regional indicator": 26}


def test_grapheme_clusters_are_the_same_on_random_text() -> None:
    rng = random.Random(29)
    pool = [cp for cp in range(0x110000) if not 0xD800 <= cp <= 0xDFFF]
    for _ in range(20_000):
        text = "".join(chr(rng.choice(pool)) for _ in range(rng.randrange(1, 9)))
        assert list(iter_graphemes(text)) == list(wcwidth.iter_graphemes(text)), text


def test_cluster_widths_differ_only_for_the_documented_reasons() -> None:
    rng = random.Random(31)
    marks = _spacing_marks()
    pool = [cp for cp in range(0x20, 0x110000) if not 0xD800 <= cp <= 0xDFFF]
    checked = 0
    for _ in range(40_000):
        text = "".join(chr(rng.choice(pool)) for _ in range(rng.randrange(1, 4)))
        for cluster in iter_graphemes(text):
            if any(ord(ch) in marks for ch in cluster) or cluster in map(chr, REGIONAL):
                continue
            checked += 1
            assert grapheme_width(cluster) == wcwidth.width(cluster), cluster
    assert checked > 50_000


def test_the_emoji_test_file_differs_only_for_text_default_bases() -> None:
    differences: Counter[str] = Counter()
    for raw in (UCD / "emoji-test.txt").read_text(encoding="utf-8").splitlines():
        data = raw.split("#", 1)[0]
        if ";" not in data:
            continue
        points, status = (part.strip() for part in data.split(";"))
        cps = [int(token, 16) for token in points.split()]
        text = "".join(map(chr, cps))
        if cell_len(text) == wcwidth.width(text):
            continue
        assert char_width(text[0]) == 1 and len(cps) > 1 and cps[1] != 0xFE0F, points
        assert (cell_len(text), wcwidth.width(text)) == (2, 1), points
        differences[status] += 1
    assert differences == {"fully-qualified": 45, "minimally-qualified": 40, "unqualified": 14}


def test_documented_string_differences() -> None:
    hand = "\U0001f590\U0001f3fb"  # a text-default emoji with a skin tone, fully qualified
    assert (cell_len(hand), wcwidth.width(hand)) == (2, 1)
    fire_heart = "❤‍\U0001f525"  # unqualified ZWJ sequence (no VS16)
    assert (cell_len(fire_heart), wcwidth.width(fire_heart)) == (2, 1)
    assert (cell_len("\U0001f1ea"), wcwidth.width("\U0001f1ea")) == (1, 2)
    kssi = "क्षि"  # a conjunct with a spacing vowel sign
    assert (cell_len(kssi), wcwidth.width(kssi)) == (3, 2)


@pytest.mark.parametrize(
    "text",
    ["family \U0001f468‍\U0001f469‍\U0001f467", "❤️", "é", "你好"],
)
def test_strings_without_documented_differences_agree(text: str) -> None:
    assert cell_len(text) == wcwidth.width(text)
    assert cell_len(text, ambiguous=2) == wcwidth.width(text, ambiguous_width=2)
