"""Results never hold an escape sequence or a cluster that the input did not have.

A stray ESC (one that starts no complete sequence) and an orphan extender (a variation
selector, a tag or a joiner cut off from its base) are harmless where they sit, but once a
cut or a tab expansion puts new text after them they can swallow that text into a new
escape sequence or fuse with it into a wider cluster. Hand-written vectors, then a seeded
fuzz over the same building blocks.
"""

from __future__ import annotations

import random

import pytest

from cellstr import (
    cell_len,
    cell_slice,
    center,
    expand_tabs,
    fit,
    ljust,
    rjust,
    strip_ansi,
    truncate,
    truncate_detailed,
)
from cellstr._ansi import segments


def escapes(text: str) -> list[str]:
    return [s.text for s in segments(text) if s.is_escape]


def test_strip_ansi_leaves_no_escape_behind() -> None:
    assert strip_ansi("\x1b\x1b[0m[31mred") == "[31mred"
    assert strip_ansi("\x1b\x1b[0m]52;c;SGVsbG8=\x07") == "]52;c;SGVsbG8=\x07"
    assert strip_ansi("a\x1b") == "a"


def test_cut_never_glues_a_stray_escape_to_new_text() -> None:
    assert truncate_detailed("\x1b\u4f60abc", 2, "~").text == "~"
    assert fit("\x1b\u4f60abc", 2, suffix="~") == "~ "
    middle = truncate_detailed("\x1b\u4f60[31mred", 5, "...", position="middle")
    assert escapes(middle.text) == [] and middle.width == cell_len(middle.text) == 5
    sliced = cell_slice("\x1bPab\x1b\u4f60\x1b\\", 0, 2)
    assert sliced == "Pa\x1b\\" and cell_len(sliced) == 2


def test_an_unterminated_string_introducer_is_a_stray_escape() -> None:
    # ESC P and ESC X with no ST behave like ESC ], ESC ^ and ESC _: the letter is text.
    assert cell_len("\x1bPab") == cell_len("\x1bXab") == cell_len("\x1b^ab") == 3
    assert strip_ansi("\x1bPab") == "Pab"


def test_a_stray_escape_before_a_non_ascii_character_is_kept() -> None:
    assert cell_slice("a\x1b\u4f60b", 0) == "a\x1b\u4f60b"
    assert cell_slice("\x1b\x1b[31mx", 0) == "\x1b\x1b[31mx"
    assert ljust("a\x1b", 3) == "a  "


def test_tab_expansion_never_creates_an_escape() -> None:
    assert expand_tabs("\x1b[\t~", 4) == "[   ~"
    assert cell_len(expand_tabs("\x1b[\t~", 4)) == cell_len("\x1b[\t~", tabsize=4) == 5
    detailed = truncate_detailed("\x1b\t~", 20, tabsize=8)
    assert detailed.text == "        ~" and detailed.width == cell_len(detailed.text) == 9
    assert ljust("\x1b[\t~", 6, tabsize=4) == "[   ~ "


def test_a_cut_never_fuses_clusters_into_a_wider_one() -> None:
    text = "\u2764\xad\U000e0067"
    cut = truncate_detailed(text, 1, "", position="middle")
    assert cut.text == "\u2764" and cut.width == cell_len(cut.text) == 1
    assert cell_len(fit(text, 1, suffix="", position="middle")) == 1
    assert truncate("\u2764\xad\ufe0f", 1, "", position="middle") == "\u2764"
    assert cell_slice("\u2764\x1b\ufe0fx", 0) == "\u2764\x1b\ufe0fx"


BLOCKS = [
    "a", "b", "~", "[", "]", "P", "\\", "(", "$", "0", "3", ";", "m", " ", "\t", "\n",
    "\x07", "\x1b", "\x1b", "\x1b[31m", "\x1b[0m", "\x1b]8;;u\x07", "\x1bP1\x1b\\",
    "\u4f60", "\u2764", "\ufe0f", "\ufe0e", "\u200d", "\U0001f600", "\U0001f3fb",
    "\U000e0067", "\xad", "\u0301", "\U0001f1ea", "\u1100", "\u1161", "#", "\u03b1",
]  # fmt: skip
SUFFIXES = ["...", "", "~", "\x1b[0m\u2026", "\x1b"]


def _texts(seed: int, count: int) -> list[str]:
    rng = random.Random(seed)
    return ["".join(rng.choices(BLOCKS, k=rng.randrange(0, 12))) for _ in range(count)]


def _clean(text: str) -> bool:
    """True when every ESC outside an escape sequence is followed by no printable ASCII."""
    position = 0
    for segment in segments(text):
        if not segment.is_escape:
            for index, char in enumerate(segment.text, start=position + 1):
                after = text[index : index + 1]
                if char == "\x1b" and (not after or " " <= after <= "~"):
                    return False
        position += len(segment.text)
    return True


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_fuzz_cuts_keep_exactly_the_escapes_and_the_width(seed: int) -> None:
    rng = random.Random(seed + 100)
    for text in _texts(seed, 3000):
        width, policy = rng.randrange(0, 14), rng.choice([1, 2])
        tabs = rng.choice([None, 4])
        start, stop = sorted((rng.randrange(0, 14), rng.randrange(0, 14)))
        sliced = cell_slice(text, start, stop, ambiguous=policy, tabsize=tabs)
        assert escapes(sliced) == escapes(text) and _clean(sliced), (text, start, stop)
        assert cell_len(sliced, ambiguous=policy) <= stop - start, (text, start, stop)
        for suffix in SUFFIXES:
            for position in ("end", "start", "middle"):
                options = {"position": position, "ambiguous": policy, "tabsize": tabs}
                cut = truncate_detailed(text, width, suffix, **options)  # type: ignore[arg-type]
                assert cut.width == cell_len(cut.text, ambiguous=policy) <= width, (text, cut)
                used = cut.truncated and cell_len(suffix, ambiguous=policy) <= width
                expected = escapes(text) + (escapes(suffix) if used else [])
                assert sorted(escapes(cut.text)) == sorted(expected), (text, cut)
                assert _clean(cut.text), (text, cut)
                fitted = fit(text, width, suffix=suffix, **options)  # type: ignore[arg-type]
                assert cell_len(fitted, ambiguous=policy) == width, (text, suffix, fitted)


@pytest.mark.parametrize("seed", [4, 5])
def test_fuzz_expansion_and_padding_keep_the_escapes_and_the_width(seed: int) -> None:
    for text in _texts(seed, 4000):
        expanded = expand_tabs(text, 4)
        assert escapes(expanded) == escapes(text) and _clean(expanded), text
        assert cell_len(expanded) == cell_len(text, tabsize=4), (text, expanded)
        assert strip_ansi(strip_ansi(text)) == strip_ansi(text) and "\x1b" not in strip_ansi(text)
        for pad in (ljust, rjust, center):
            padded = pad(text, 9, "~", tabsize=4)
            assert escapes(padded) == escapes(text) and _clean(padded), (text, padded)
            assert cell_len(padded) == max(9, cell_len(text, tabsize=4)), (text, padded)
