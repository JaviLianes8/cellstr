"""ANSI escape sequence recognition (hand-written vectors per ECMA-48 family)."""

from __future__ import annotations

import pytest

from cellstr import cell_len, strip_ansi
from cellstr._ansi import segments

RED = "\x1b[31m"
RESET = "\x1b[0m"


@pytest.mark.parametrize(
    "escape",
    [
        "\x1b[31m",
        "\x1b[38;2;255;0;0m",
        "\x1b[38:5:208m",
        "\x1b[2K",
        "\x1b[?25l",
        "\x1b]0;window title\x07",
        "\x1b]8;id=1;https://example.com\x1b\\",
        "\x1b]8;;\x07",
        "\x1bP+q544e\x1b\\",
        "\x1b_application data\x1b\\",
        "\x1b(B",
        "\x1b#8",
        "\x1b7",
        "\x1b8",
        "\x1bc",
        "\x1bM",
        "\x1b=",
    ],
)
def test_every_family_is_removed_and_measured_as_nothing(escape: str) -> None:
    assert strip_ansi(f"a{escape}b") == "ab"
    assert cell_len(f"a{escape}b") == 2


def test_strip_leaves_plain_text_untouched() -> None:
    assert strip_ansi("plain [31m text") == "plain [31m text"


def test_unterminated_osc_does_not_swallow_the_rest() -> None:
    assert cell_len("\x1b]8;;https://x") == len("]8;;https://x")


def test_lone_escape_is_a_zero_width_control() -> None:
    assert cell_len("a\x1b") == 1


def test_segments_alternate_text_and_escape() -> None:
    parts = segments(f"a{RED}b{RESET}")
    assert [(p.text, p.is_escape) for p in parts] == [
        ("a", False),
        (RED, True),
        ("b", False),
        (RESET, True),
    ]


def test_segments_rejoin_to_the_original() -> None:
    text = f"{RED}x\u4f60{RESET}y\x1b]8;;u\x07z"
    assert "".join(p.text for p in segments(text)) == text
    assert segments("") == []
