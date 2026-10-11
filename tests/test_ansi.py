from cellstr import strip_ansi
from cellstr._ansi import segments

RED = "\x1b[31m"
RESET = "\x1b[0m"


def test_strip_removes_colour_codes() -> None:
    assert strip_ansi(f"{RED}error{RESET}") == "error"


def test_strip_removes_osc_hyperlinks() -> None:
    link = "\x1b]8;;https://example.com\x07label\x1b]8;;\x07"
    assert strip_ansi(link) == "label"


def test_strip_leaves_plain_text_untouched() -> None:
    assert strip_ansi("plain") == "plain"


def test_segments_alternate_text_and_escape() -> None:
    parts = segments(f"a{RED}b{RESET}")
    assert [(p.text, p.is_escape) for p in parts] == [
        ("a", False),
        (RED, True),
        ("b", False),
        (RESET, True),
    ]


def test_segments_rejoin_to_the_original() -> None:
    text = f"{RED}x你{RESET}y"
    assert "".join(p.text for p in segments(text)) == text
