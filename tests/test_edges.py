"""Edge cases: zero-width-only text, escapes in middle cuts, argument types, emoji corners."""

from __future__ import annotations

import pytest

from cellstr import cell_len, cell_slice, char_width, grapheme_width, iter_cells, truncate

RED = "\x1b[31m"
RESET = "\x1b[0m"
LINK = "\x1b]8;;https://example.com\x1b\\"
UNLINK = "\x1b]8;;\x1b\\"


@pytest.mark.parametrize("text", ["\u200b", "\u0301", "\u1161", "\x07", "\u200b\u200d"])
def test_zero_width_only_text_survives_any_range_from_zero(text: str) -> None:
    assert cell_slice(text, 0, 5) == text
    assert cell_slice(text, 0, 1) == text
    assert cell_slice(text, 0) == text
    assert cell_slice(text, 0, 0) == ""
    assert cell_slice(text, 1) == ""
    for k in (0, 1, 10):
        assert cell_slice(text, 0, k) + cell_slice(text, k) == text


def test_trailing_zero_width_goes_to_the_range_reaching_the_end() -> None:
    assert cell_slice("a\u200b", 0, 9) == "a\u200b"
    assert cell_slice("a\u200b", 1) == ""


def test_middle_cut_keeps_each_escape_once_and_in_place() -> None:
    text = f"{RED}abcdefghij{RESET}"
    assert truncate(text, 5, "~", position="middle") == f"{RED}ab~ij{RESET}"
    linked = f"ab{LINK}cdef{UNLINK}ghij"
    result = truncate(linked, 5, "~", position="middle")
    assert result == f"ab{LINK}~{UNLINK}ij"
    assert result.count("\x1b") == linked.count("\x1b")


@pytest.mark.parametrize("suffix", ["\t", "..\n", "\r"])
def test_suffix_with_tabs_or_line_breaks_is_rejected(suffix: str) -> None:
    with pytest.raises(ValueError, match="suffix"):
        truncate("abcdef", 3, suffix, tabsize=4)


@pytest.mark.parametrize("bad", [2.0, "2", None, True])
def test_ambiguous_must_be_an_int(bad: object) -> None:
    with pytest.raises(TypeError, match="ambiguous must be an int"):
        cell_len("\u03b1", ambiguous=bad)  # type: ignore[arg-type]


@pytest.mark.parametrize("bad", [2.5, 4.0, "4", True])
def test_tabsize_must_be_an_int(bad: object) -> None:
    with pytest.raises(TypeError, match="tabsize must be an int"):
        cell_len("a\tb", tabsize=bad)  # type: ignore[arg-type]


def test_variation_selector_counts_only_right_after_the_base() -> None:
    fire_heart = "\u2764\u200d\U0001f525"
    assert grapheme_width(fire_heart + "\ufe0e") == 2
    assert grapheme_width("\u2764\ufe0e") == 1


def test_dangling_zwj_does_not_widen_a_narrow_symbol() -> None:
    assert grapheme_width("\u00a9\u200d") == char_width("\u00a9") == 1
    assert grapheme_width("\u00a9\ufe0f\u200d") == 2
    assert grapheme_width("\U0001f3f3\u200d\U0001f308") == 2


def test_a_tag_sequence_widens_any_emoji_base() -> None:
    tags = "\U000e0067\U000e0062\U000e007f"  # TAG LATIN SMALL LETTER G, B, CANCEL TAG
    assert grapheme_width("\u263a" + tags) == 2  # a one-cell emoji base
    assert grapheme_width("\U0001f3f4" + tags) == 2
    assert cell_len("x" + tags) == 1  # not an emoji: the tags are zero-width format characters


def test_ascii_controls_and_del_are_zero_width() -> None:
    controls = "".join(map(chr, range(0x20))) + "\x7f"
    assert cell_len(f"a{controls}b") == 2
    assert cell_len(f"a{controls}\u4f60") == 3  # the same on the non-ASCII path


def test_a_carriage_return_starts_a_new_line_for_tab_stops() -> None:
    assert cell_len("ab\rc\td", tabsize=4) == 7  # the tab advances from column 3 to 6
    assert cell_len("ab\r\nc\td", tabsize=4) == 7
    assert [c.width for c in iter_cells("abcde\rx\ty", tabsize=4)] == [1, 1, 1, 1, 1, 0, 1, 3, 1]
