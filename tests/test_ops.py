import pytest

from cellstr import cell_len, cell_slice, center, ljust, rjust, truncate

RED = "\x1b[31m"
RESET = "\x1b[0m"


def test_slice_counts_display_cells() -> None:
    assert cell_slice("hello world", 0, 5) == "hello"


def test_slice_start_offset() -> None:
    assert cell_slice("hello world", 6) == "world"


def test_slice_keeps_escape_sequences() -> None:
    assert cell_slice(f"{RED}hello{RESET}", 0, 3) == f"{RED}hel{RESET}"


def test_slice_drops_a_wide_char_straddling_the_right_edge() -> None:
    assert cell_slice("a你b", 0, 2) == "a"


def test_slice_keeps_a_wide_char_fully_inside() -> None:
    assert cell_slice("a你b", 0, 3) == "a你"


def test_slice_rejects_negative_indices() -> None:
    with pytest.raises(ValueError):
        cell_slice("abc", -1)


def test_ljust_pads_by_display_width() -> None:
    assert ljust("你", 4) == "你  "


def test_rjust_pads_by_display_width() -> None:
    assert rjust("ab", 5) == "   ab"


def test_center_splits_padding() -> None:
    assert center("ab", 6) == "  ab  "


def test_padding_leaves_text_wider_than_width_untouched() -> None:
    assert ljust("hello", 3) == "hello"


def test_padding_rejects_wide_fillchar() -> None:
    with pytest.raises(ValueError):
        ljust("x", 4, "你")


def test_truncate_adds_suffix_and_respects_width() -> None:
    result = truncate("hello world", 8)
    assert result == "hello..."
    assert cell_len(result) == 8


def test_truncate_returns_short_text_unchanged() -> None:
    assert truncate("hi", 10) == "hi"


def test_truncate_without_room_for_suffix_hard_cuts() -> None:
    assert truncate("hello", 2, "...") == "he"


def test_truncate_accounts_for_wide_cells() -> None:
    result = truncate("你好世", 4, "")
    assert cell_len(result) == 4
    assert result == "你好"
