import pytest

from cellstr import cell_len, char_width

RED = "\x1b[31m"
RESET = "\x1b[0m"


def test_ascii_width_is_one_per_character() -> None:
    assert cell_len("hello") == 5


def test_ansi_sequences_do_not_count() -> None:
    assert cell_len(f"{RED}WARN{RESET}") == 4


def test_wide_characters_count_as_two_cells() -> None:
    assert cell_len("你好") == 4


def test_fullwidth_forms_count_as_two_cells() -> None:
    assert char_width(chr(0xFF21)) == 2


def test_combining_marks_add_no_width() -> None:
    assert cell_len("é") == 1


def test_zero_width_joiner_adds_no_width() -> None:
    assert char_width("‍") == 0


def test_control_characters_are_zero_width() -> None:
    assert char_width("\x07") == 0


def test_char_width_rejects_multi_character_input() -> None:
    with pytest.raises(ValueError):
        char_width("ab")
