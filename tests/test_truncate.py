"""Truncation at the end, start and middle, detailed results and exact fitting."""

from __future__ import annotations

import pytest

from cellstr import Truncation, cell_len, fit, truncate, truncate_detailed

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
