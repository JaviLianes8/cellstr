"""Widths of code points, grapheme clusters and strings (hand-written vectors)."""

from __future__ import annotations

import pytest

from cellstr import cell_len, char_width, grapheme_width, iter_cells, iter_graphemes

RED = "\x1b[31m"
RESET = "\x1b[0m"
FAMILY = "\U0001f468\u200d\U0001f469\u200d\U0001f467"
SPAIN = "\U0001f1ea\U0001f1f8"
SCOTLAND = "\U0001f3f4\U000e0067\U000e0062\U000e0073\U000e0063\U000e0074\U000e007f"


def test_ascii_width_is_one_per_character() -> None:
    assert cell_len("hello") == 5


def test_ansi_sequences_do_not_count() -> None:
    assert cell_len(f"{RED}WARN{RESET}") == 4


def test_wide_and_fullwidth_characters_count_two() -> None:
    assert cell_len("\u4f60\u597d") == 4
    assert char_width("\uff21") == 2
    assert char_width("\uac00") == 2


def test_zero_width_code_points() -> None:
    for ch in ("\u0301", "\u20dd", "\u200b", "\u200d", "\u2060", "\ufeff", "\x00", "\x07"):
        assert char_width(ch) == 0, hex(ord(ch))


def test_hangul_medial_and_final_jamo_are_zero() -> None:
    assert (char_width("\u1161"), char_width("\u11a8"), char_width("\ud7b0")) == (0, 0, 0)
    assert cell_len("\u1100\u1161\u11a8") == 2


def test_soft_hyphen_and_spacing_marks_take_a_cell() -> None:
    assert char_width("\u00ad") == 1
    assert char_width("\u093f") == 1


def test_ambiguous_policy() -> None:
    for ch in ("\u03b1", "\u0436", "\u2500", "\u2460", "\u00b1"):
        assert char_width(ch) == 1
        assert char_width(ch, ambiguous=2) == 2
    assert cell_len("\u0436\u2500x", ambiguous=2) == 5


@pytest.mark.parametrize("value", [0, 3, True, -1])
def test_ambiguous_must_be_one_or_two(value: int) -> None:
    with pytest.raises(ValueError, match="ambiguous"):
        cell_len("x", ambiguous=value)


def test_char_width_rejects_other_lengths() -> None:
    for bad in ("", "ab", FAMILY):
        with pytest.raises(ValueError):
            char_width(bad)


@pytest.mark.parametrize(
    ("cluster", "width"),
    [
        (FAMILY, 2),
        (SPAIN, 2),
        (SCOTLAND, 2),
        ("\U0001f44d\U0001f3fd", 2),
        ("\u261d\U0001f3fb", 2),
        ("\u2764\ufe0f", 2),
        ("\u2764", 1),
        ("\u231a", 2),
        ("\u231a\ufe0e", 1),
        ("1\ufe0f\u20e3", 2),
        ("1\u20e3", 1),
        ("\U0001f3f3\ufe0f\u200d\U0001f308", 2),
        ("e\u0301\u0302", 1),
        ("\u0915\u094d\u0937", 2),
        ("\r\n", 0),
        ("\U0001f1ea", 1),
        ("\U0001f3fd\U0001f3fd", 4),
        (" \U0001f3fd", 3),
    ],
)
def test_grapheme_width(cluster: str, width: int) -> None:
    assert grapheme_width(cluster) == width
    assert cell_len(cluster) == width


def test_grapheme_width_wants_exactly_one_cluster() -> None:
    for bad in ("", "ab", SPAIN + SPAIN):
        with pytest.raises(ValueError, match="one grapheme"):
            grapheme_width(bad)


def test_ambiguous_emoji_with_vs16_is_wide_under_both_policies() -> None:
    assert grapheme_width("\u2660\ufe0f") == grapheme_width("\u2660\ufe0f", ambiguous=2) == 2
    assert grapheme_width("\u2660") == 1 and grapheme_width("\u2660", ambiguous=2) == 2


def test_strings_sum_their_clusters() -> None:
    text = f"a{FAMILY}b{SPAIN}\u4f60e\u0301"
    assert cell_len(text) == 1 + 2 + 1 + 2 + 2 + 1
    assert [grapheme_width(g) for g in iter_graphemes(text)] == [1, 2, 1, 2, 2, 1]


def test_tabs_are_zero_unless_a_tabsize_is_given() -> None:
    assert cell_len("a\tb") == 2
    assert cell_len("a\tb", tabsize=8) == 9
    assert cell_len("\u4f60\tb", tabsize=4) == 5
    assert cell_len(f"{RED}ab{RESET}\tc", tabsize=4) == 5


def test_tab_stops_restart_after_a_line_break() -> None:
    assert cell_len("abc\n\tx", tabsize=4) == 3 + 4 + 1


@pytest.mark.parametrize("value", [0, -2, True])
def test_tabsize_must_be_positive(value: int) -> None:
    with pytest.raises(ValueError, match="tabsize"):
        cell_len("a\tb", tabsize=value)


def test_iter_cells_reports_escapes_columns_and_widths() -> None:
    cells = list(iter_cells(f"{RED}a\u4f60{RESET}{SPAIN}"))
    assert [(c.text, c.width, c.column, c.escape) for c in cells] == [
        (RED, 0, 0, True),
        ("a", 1, 0, False),
        ("\u4f60", 2, 1, False),
        (RESET, 0, 3, True),
        (SPAIN, 2, 3, False),
    ]
    assert "".join(c.text for c in cells) == f"{RED}a\u4f60{RESET}{SPAIN}"


def test_iter_cells_is_lazy_and_validates_on_first_step() -> None:
    cells = iter_cells("x", ambiguous=5)
    with pytest.raises(ValueError):
        next(cells)
