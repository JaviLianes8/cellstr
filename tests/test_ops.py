"""Grapheme-safe slicing, padding and tab expansion (hand-written vectors)."""

from __future__ import annotations

import pytest

from cellstr import cell_len, cell_slice, center, expand_tabs, ljust, rjust

RED = "\x1b[31m"
RESET = "\x1b[0m"
FAMILY = "\U0001f468\u200d\U0001f469\u200d\U0001f467"
SPAIN = "\U0001f1ea\U0001f1f8"
LINK = "\x1b]8;;https://example.com\x1b\\"
UNLINK = "\x1b]8;;\x1b\\"


def test_slice_counts_display_cells() -> None:
    assert cell_slice("hello world", 0, 5) == "hello"
    assert cell_slice("hello world", 6) == "world"


def test_slice_keeps_escape_sequences() -> None:
    assert cell_slice(f"{RED}hello{RESET}", 0, 3) == f"{RED}hel{RESET}"


def test_slice_keeps_osc8_hyperlinks_open_and_closed() -> None:
    text = f"see {LINK}the docs{UNLINK} now"
    assert cell_slice(text, 4, 7) == f"{LINK}the{UNLINK}"
    assert cell_len(text) == len("see the docs now")


def test_slice_drops_a_wide_char_straddling_either_edge() -> None:
    assert cell_slice("a\u4f60b", 0, 2) == "a"
    assert cell_slice("a\u4f60b", 2) == "b"
    assert cell_slice("a\u4f60b", 0, 3) == "a\u4f60"


def test_slice_never_splits_a_grapheme_cluster() -> None:
    assert cell_slice(f"x{FAMILY}y", 0, 2) == "x"
    assert cell_slice(f"x{FAMILY}y", 1, 3) == FAMILY
    assert cell_slice(f"{SPAIN}{SPAIN}", 2) == SPAIN
    assert cell_slice("e\u0301te\u0301", 0, 1) == "e\u0301"
    assert cell_slice("\u1100\u1161\u11a8!", 0, 2) == "\u1100\u1161\u11a8"


def test_slice_splits_back_into_the_original() -> None:
    text = "na\u00efve e\u0301 \u4f60\u597d \x07end"
    for k in range(cell_len(text) + 1):
        if k not in (9, 11):  # inside a wide character
            assert cell_slice(text, 0, k) + cell_slice(text, k) == text, k


def test_slice_keeps_trailing_zero_width_only_in_the_range_reaching_the_end() -> None:
    assert cell_slice("ab\x07", 0, 2) == "ab\x07"
    assert cell_slice("ab\x07", 2) == ""
    assert cell_slice("\x07") == "\x07"


def test_slice_bounds() -> None:
    assert cell_slice("abc", 2, 1) == ""
    assert cell_slice("abc", 5) == ""
    assert cell_slice("abc", 0, 99) == "abc"
    with pytest.raises(ValueError):
        cell_slice("abc", -1)
    with pytest.raises(ValueError):
        cell_slice("abc", 0, -1)


def test_slice_with_tabs_keeps_the_layout() -> None:
    assert cell_slice("a\tb", 0, 4, tabsize=4) == "a   "
    assert cell_slice("a\tbc", 4, tabsize=4) == "bc"
    assert cell_slice("a\tb", 0, 2) == "a\tb"


def test_slice_honours_the_ambiguous_policy() -> None:
    assert cell_slice("\u03b1\u03b2\u03b3", 0, 2) == "\u03b1\u03b2"
    assert cell_slice("\u03b1\u03b2\u03b3", 0, 2, ambiguous=2) == "\u03b1"


def test_padding_by_display_width() -> None:
    assert ljust("\u4f60", 4) == "\u4f60  "
    assert rjust("ab", 5) == "   ab"
    assert center("ab", 6) == "  ab  "
    assert center("ab", 5) == " ab  "
    assert ljust(FAMILY, 4, ".") == FAMILY + ".."


def test_padding_ignores_escapes_and_leaves_wide_text_alone() -> None:
    assert rjust(f"{RED}7{RESET}", 3) == f"  {RED}7{RESET}"
    assert ljust("hello", 3) == "hello"
    assert center("x", 0) == "x"


def test_padding_with_an_ambiguous_fill_character() -> None:
    assert ljust("ab", 4, "\u2500") == "ab\u2500\u2500"
    with pytest.raises(ValueError):
        ljust("ab", 4, "\u2500", ambiguous=2)


@pytest.mark.parametrize("fill", ["", "ab", "\u4f60", "\x07", "\x1b"])
def test_padding_rejects_unusable_fill_characters(fill: str) -> None:
    with pytest.raises(ValueError, match="fillchar"):
        rjust("x", 4, fill)


def test_fill_may_be_a_one_cell_grapheme_cluster() -> None:
    assert ljust("x", 3, "e\u0301") == "xe\u0301e\u0301"


def test_padding_expands_tabs_when_asked() -> None:
    assert rjust("a\tb", 10, tabsize=4) == "     a   b"


def test_expand_tabs_counts_display_cells() -> None:
    assert expand_tabs("\u4f60\tx", 4) == "\u4f60  x"
    assert expand_tabs(f"{RED}ab{RESET}\tc", 4) == f"{RED}ab{RESET}  c"
    assert expand_tabs("ab\n\tc") == "ab\n        c"
    assert expand_tabs("no tabs") == "no tabs"
    assert "a\tb".expandtabs(8) == expand_tabs("a\tb")


def test_expand_tabs_rejects_bad_tab_sizes() -> None:
    with pytest.raises(ValueError):
        expand_tabs("a\tb", 0)
