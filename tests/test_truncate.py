"""Truncation at the end, start and middle, detailed results and exact fitting."""

from __future__ import annotations

import pytest

from cellstr import Truncation, cell_len, cell_slice, fit, truncate, truncate_detailed

RED = "\x1b[31m"
RESET = "\x1b[0m"
FAMILY = "\U0001f468\u200d\U0001f469\u200d\U0001f467"


def test_truncate_adds_suffix_and_respects_width() -> None:
    assert truncate("hello world", 8) == "hello..."


def test_truncate_returns_short_text_unchanged() -> None:
    assert truncate("hi", 10) == "hi"
    assert truncate("", 0) == ""


def test_truncate_without_room_for_suffix_hard_cuts() -> None:
    assert truncate("hello", 2) == "he"
    assert truncate("hello", 2, position="start") == "lo"
    assert truncate("hello", 0) == ""


def test_truncate_accounts_for_wide_cells() -> None:
    assert truncate("\u4f60\u597d\u4e16", 4, "") == "\u4f60\u597d"
    assert truncate("\u4f60\u597d\u4e16", 4) == "..."
    assert truncate("\u4f60\u597d\u4e16", 5) == "\u4f60..."


def test_truncate_positions() -> None:
    path = "/usr/local/lib/python"
    assert truncate(path, 12, position="end") == "/usr/loca..."
    assert truncate(path, 12, position="start") == "...ib/python"
    assert truncate(path, 12, position="middle") == "/usr/...thon"


def test_truncate_middle_gives_the_odd_cell_to_the_left() -> None:
    assert truncate("abcdefghij", 6, "~", position="middle") == "abc~ij"


def test_truncate_never_splits_an_emoji_sequence() -> None:
    result = truncate(f"ab{FAMILY}cd", 4, "~")
    assert result == "ab~" and cell_len(result) == 3


def test_truncate_rejects_bad_arguments() -> None:
    with pytest.raises(ValueError, match="width must not be negative, not -1"):
        truncate("x", -1)
    with pytest.raises(ValueError, match="position"):
        truncate("x", 1, position="left")  # type: ignore[arg-type]


def test_truncate_with_tabs_and_ambiguous_policy() -> None:
    assert truncate("a\tbcdef", 6, "", tabsize=4) == "a   bc"
    assert truncate("\u03b1\u03b2\u03b3", 4, "~", ambiguous=2) == "\u03b1~"


def test_truncate_turns_tabs_into_the_spaces_kept_at_each_cut() -> None:
    # "ab\tcdef\tgh" with stops every 4 cells draws as "ab  cdef    gh" (14 cells).
    text = "ab\tcdef\tgh"
    assert truncate(text, 8, "~", tabsize=4, position="middle") == "ab  ~ gh"
    assert truncate(text, 8, "~", tabsize=4, position="start") == "~f    gh"
    assert truncate(text, 8, "~", tabsize=4) == "ab  cde~"
    assert truncate_detailed(text, 20, tabsize=4) == Truncation("ab  cdef    gh", 14, 14, False)


def test_truncate_work_does_not_grow_with_the_tab_size() -> None:
    result = truncate_detailed("a\tb" * 1000, 10, tabsize=10**9)
    assert result == Truncation("a      ...", 10, 1000 * 10**9 + 1, True)


def test_truncate_detailed_reports_the_outcome() -> None:
    assert truncate_detailed("hello world", 8) == Truncation("hello...", 8, 11, True)
    assert truncate_detailed("hi", 8) == Truncation("hi", 2, 2, False)
    short = truncate_detailed("\u4f60\u597d\u4e16", 3, "")
    assert short == Truncation("\u4f60", 2, 6, True)
    assert short.text == "\u4f60" and short.truncated


def test_fit_truncates_or_pads_to_the_exact_width() -> None:
    assert fit("hello world", 8) == "hello..."
    assert fit("hi", 5) == "hi   "
    assert fit("hi", 5, align="right") == "   hi"
    assert fit("hi", 5, align="center", fillchar=".") == ".hi.."
    assert fit("\u4f60\u597d\u4e16", 5, suffix="") == "\u4f60\u597d "


def test_fit_rows_line_up() -> None:
    rows = ["name", "\u5f20\u4f1f", FAMILY + " family", f"{RED}error{RESET}", "e\u0301clair"]
    for row in rows:
        assert cell_len(fit(row, 6)) == 6


def test_fit_rejects_bad_options() -> None:
    with pytest.raises(ValueError, match="align"):
        fit("x", 3, align="middle")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="fillchar"):
        fit("x", 3, fillchar="\u4f60")


def test_middle_cut_gives_a_cell_one_side_cannot_use_to_the_other() -> None:
    wide = "\u4f60" * 5
    assert truncate_detailed(wide, 9, position="middle") == Truncation(
        "\u4f60\u4f60...\u4f60", 9, 10, True
    )
    assert truncate_detailed(wide, 5, position="middle") == Truncation("\u4f60...", 5, 10, True)
    assert truncate_detailed(wide, 8, position="middle").width == 7


def test_a_cut_is_short_by_less_than_the_cluster_it_drops() -> None:
    conjunct = "\u0915\u094d\u0937\u093f"  # three cells: two letters joined, a spacing sign
    assert cell_slice(f"a{conjunct}bcd", 0, 3) == "a"
    assert truncate_detailed(f"a{conjunct}bcd", 6) == Truncation("a...", 4, 7, True)
    assert fit(f"a{conjunct}bcd", 6) == "a...  "


def test_a_middle_cut_with_no_room_for_the_suffix_keeps_the_start() -> None:
    assert truncate("abcdefgh", 2, "....", position="middle") == "ab"


def test_a_suffix_that_fills_the_width_exactly_is_kept() -> None:
    for position in ("end", "start", "middle"):
        assert truncate("abcdef", 3, position=position) == "..."
        assert truncate("abcdef", 2, position=position) in ("ab", "ef")


def test_a_middle_cut_through_one_tab_spanning_both_sides() -> None:
    text = "abcdefgh\tijklmnop"
    cut = truncate(text, 22, "~", position="middle", tabsize=8)
    assert cut == "abcdefgh   ~  ijklmnop"


def test_fit_pads_ambiguous_text_with_the_ambiguous_policy() -> None:
    assert fit("\u03b1\u03b2", 6, ambiguous=2) == "\u03b1\u03b2  "
    assert cell_len(fit("\u03b1\u03b2\u03b3\u03b4", 5, ambiguous=2), ambiguous=2) == 5
