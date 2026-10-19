"""The error promise of every public function: typed, raised at the call, short messages.

A wrong type is a ``TypeError``, a wrong value a ``ValueError``; both are raised when the
function is called (also for the generators), and a message quotes at most 40 characters
of any argument, however large or hostile it is (GUIDE.md, "Errors").
"""

from __future__ import annotations

import pickle
from collections.abc import Callable

import pytest

import cellstr
from cellstr import (
    Cell,
    Truncation,
    cell_len,
    cell_slice,
    center,
    char_width,
    expand_tabs,
    fit,
    grapheme_width,
    iter_cells,
    iter_graphemes,
    ljust,
    rjust,
    strip_ansi,
    truncate,
    truncate_detailed,
)

BIG = "x" * 1_000_000
HUGE = -(10**5000)
Call = Callable[[], object]

TYPE_ERRORS: list[tuple[str, Call]] = [
    ("text must be a str, not NoneType", lambda: cell_len(None)),  # type: ignore[arg-type]
    ("text must be a str, not list", lambda: cell_len(["a"])),  # type: ignore[arg-type]
    ("char must be a str, not int", lambda: char_width(65)),  # type: ignore[arg-type]
    ("cluster must be a str, not bytes", lambda: grapheme_width(b"a")),  # type: ignore[arg-type]
    ("text must be a str, not NoneType", lambda: iter_graphemes(None)),  # type: ignore[arg-type]
    ("ambiguous must be an int, not str", lambda: iter_cells("a", ambiguous="1")),  # type: ignore[arg-type]
    ("start must be an int, not float", lambda: cell_slice("abc", 1.5)),  # type: ignore[arg-type]
    ("stop must be an int, not float", lambda: cell_slice("abc", 0, 2.5)),  # type: ignore[arg-type]
    ("width must be an int, not str", lambda: ljust("a", "5")),  # type: ignore[arg-type]
    ("width must be an int, not float", lambda: rjust("a", 5.0)),  # type: ignore[arg-type]
    ("fillchar must be a str, not int", lambda: center("a", 5, 0)),  # type: ignore[arg-type]
    ("width must be an int, not bool", lambda: truncate("abc", True)),
    ("suffix must be a str, not int", lambda: truncate_detailed("a", 3, 5)),  # type: ignore[arg-type]
    ("align must be a str, not NoneType", lambda: fit("a", 3, align=None)),  # type: ignore[arg-type]
    ("tabsize must be an int, not NoneType", lambda: expand_tabs("a", None)),  # type: ignore[arg-type]
    ("tabsize must be an int, not float", lambda: cell_len("a", tabsize=4.0)),  # type: ignore[arg-type]
    ("text must be a str, not bytes", lambda: strip_ansi(b"\x1b[0m")),  # type: ignore[arg-type]
]

VALUE_ERRORS: list[tuple[str, Call]] = [
    ("char must be a single code point", lambda: char_width("ab")),
    ("char must be a single code point", lambda: char_width("")),
    ("cluster must be exactly one grapheme cluster", lambda: grapheme_width("ab")),
    ("cluster must be exactly one grapheme cluster", lambda: grapheme_width("")),
    ("ambiguous must be 1 or 2, not 3", lambda: iter_cells("a", ambiguous=3)),
    ("ambiguous must be 1 or 2, not 0", lambda: cell_len("a", ambiguous=0)),
    ("start must not be negative, not -1", lambda: cell_slice("abc", -1)),
    ("stop must not be negative, not -2", lambda: cell_slice("abc", 0, -2)),
    ("fillchar must be a single one-cell character", lambda: ljust("a", 4, "ab")),
    ("fillchar must be a single one-cell character", lambda: rjust("a", 4, "你")),
    ("fillchar must be a single one-cell character", lambda: center("a", 4, "α", ambiguous=2)),
    ("width must not be negative, not -1", lambda: truncate("abc", -1)),
    ("suffix must not contain tabs or line breaks", lambda: truncate("abc", 2, "\n")),
    ("position must be one of 'end', 'start', 'middle'", lambda: truncate("a", 1, position="x")),  # type: ignore[arg-type]
    ("align must be one of 'left', 'right', 'center'", lambda: fit("a", 3, align="x")),  # type: ignore[arg-type]
    ("width must not be negative", lambda: fit("a", -3)),
    ("tabsize must be at least 1, not 0", lambda: expand_tabs("a", 0)),
    ("tabsize must be at least 1, not -8", lambda: cell_len("a\tb", tabsize=-8)),
]

HOSTILE: list[Call] = [
    lambda: char_width(BIG),
    lambda: grapheme_width(BIG),
    lambda: ljust("a", 3, BIG),
    lambda: truncate("a", 1, position=BIG),  # type: ignore[arg-type]
    lambda: fit("a", 1, align=BIG),  # type: ignore[arg-type]
    lambda: truncate("a", HUGE),
    lambda: cell_slice("a", HUGE),
    lambda: cell_len("a", ambiguous=-HUGE),
    lambda: expand_tabs("a", HUGE),
    lambda: cell_len(type("N" * 10_000, (), {})()),
]


@pytest.mark.parametrize(("message", "call"), TYPE_ERRORS)
def test_a_wrong_type_is_a_type_error_named_in_the_message(message: str, call: Call) -> None:
    with pytest.raises(TypeError) as caught:
        call()
    assert str(caught.value) == message


@pytest.mark.parametrize(("message", "call"), VALUE_ERRORS)
def test_a_wrong_value_is_a_value_error_named_in_the_message(message: str, call: Call) -> None:
    with pytest.raises(ValueError) as caught:
        call()
    assert str(caught.value).startswith(message)
    assert not isinstance(caught.value, TypeError)


@pytest.mark.parametrize("call", HOSTILE)
def test_messages_stay_short_for_huge_arguments(call: Call) -> None:
    with pytest.raises((TypeError, ValueError)) as caught:
        call()
    assert len(str(caught.value)) <= 100


def test_bool_is_not_accepted_as_a_number_but_index_integers_are() -> None:
    class Four:
        def __index__(self) -> int:
            return 4

    with pytest.raises(TypeError, match="ambiguous must be an int, not bool"):
        cell_len("a", ambiguous=True)
    assert expand_tabs("a\tb", Four()) == "a   b"  # type: ignore[arg-type]
    assert cell_slice("abcdef", Four()) == "ef"  # type: ignore[arg-type]


def test_the_generators_check_their_arguments_at_the_call() -> None:
    with pytest.raises(ValueError):
        iter_cells("a", tabsize=0)
    with pytest.raises(TypeError):
        iter_graphemes(1)  # type: ignore[arg-type]


def test_negative_padding_widths_leave_the_text_as_str_methods_do() -> None:
    assert ljust("ab", -5) == "ab".ljust(-5) == "ab"
    assert rjust("ab", HUGE) == center("ab", 0) == "ab"
    assert cell_slice("abc", 2, 1) == ""


def test_results_are_exact_str_even_for_a_str_subclass() -> None:
    class Text(str):
        def __len__(self) -> int:
            return 99

    for result in (
        truncate(Text("abc"), 10),
        ljust(Text("abc"), 2),
        cell_slice(Text("abc"), 0),
        expand_tabs(Text("abc")),
        strip_ansi(Text("abc")),
        fit(Text("abc"), 3),
        *iter_graphemes(Text("ab")),
        *(cell.text for cell in iter_cells(Text("ab"))),
    ):
        assert type(result) is str


def test_records_pickle_under_the_public_module() -> None:
    for record in (Cell("a", 1, 0, False), Truncation("ab", 2, 5, True)):
        data = pickle.dumps(record)
        assert b"cellstr\x94" in data and b"_cells" not in data and b"_truncate" not in data
        assert pickle.loads(data) == record
        assert type(record).__module__ == "cellstr"


def test_the_package_exports_nothing_else() -> None:
    public = {name for name in vars(cellstr) if not name.startswith("_")}
    assert public == set(cellstr.__all__)


def test_a_result_too_large_to_build_raises_overflow_error() -> None:
    # Documented in GUIDE.md "Errors": the same error str.ljust and str.expandtabs raise.
    with pytest.raises(OverflowError):
        cellstr.ljust("a", 10**20)
    with pytest.raises(OverflowError):
        cellstr.expand_tabs("\t", 10**20)
