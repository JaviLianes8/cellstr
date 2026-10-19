"""Contracts for a fill character that glues to the edge of the text it pads.

Padding puts the fill next to the first and the last cluster of the text. A fill that
would join one of them into a cluster of another width (after an orphan VS16 or skin
tone modifier at the start, before a trailing ZWJ) would leave the result wider or
narrower than ``width``. The fill cell at that seam is a space instead, so the result is
always exactly ``width`` cells and the text is kept whole. Every vector is hand-written.
"""

from __future__ import annotations

import pytest

from cellstr import cell_len, center, fit, ljust, rjust

FILLS = ["#", "*", "0", "\u2620", "\u2764", " ", "\U0001f1e6"]
STARTS = ["\ufe0fab", "\ufe0f\u20e3x", "\U0001f3fbx", "\u200d\U0001f600x", "\u0301x"]
ENDS = ["\u200d", "\ufe0f", "\U0001f468\u200d", "a\u200d", "x\U0001f1e6", "\u0600", "\u0915\u094d"]


def test_a_fill_that_would_glue_to_the_start_of_the_text_becomes_a_space() -> None:
    assert rjust("\ufe0fab", 5, "#") == "## \ufe0fab"
    assert rjust("\ufe0f\u20e3x", 5, "0") == "000 \ufe0f\u20e3x"
    assert rjust("\U0001f3fbx", 5, "\u2620") == "\u2620 \U0001f3fbx"
    assert center("\ufe0fab", 6, "*") == "* \ufe0fab**"


def test_a_fill_that_would_glue_to_the_end_of_the_text_becomes_a_space() -> None:
    assert ljust("\U0001f468\u200d", 4, "\u2620") == "\U0001f468\u200d \u2620"
    assert fit("\U0001f468\u200d", 4, fillchar="\u2620") == "\U0001f468\u200d \u2620"


def test_a_fill_that_glues_at_the_same_width_stays() -> None:
    # Two lone regional indicators form a flag of two cells, the sum of the parts.
    assert ljust("x\U0001f1e6", 3, "\U0001f1e6") == "x\U0001f1e6\U0001f1e6"
    assert rjust("\u0301x", 3, "#") == "##\u0301x"


def test_padding_is_exactly_the_width_whatever_the_fill_and_the_edges() -> None:
    for fill in FILLS:
        for text in STARTS + ENDS + [s + e for s in STARTS for e in ENDS]:
            for width in range(cell_len(text), cell_len(text) + 4):
                for pad in (ljust, rjust, center):
                    out = pad(text, width, fill)
                    assert cell_len(out) == width, (pad.__name__, text, width, fill)
                    assert text in out
                for align in ("left", "right", "center"):
                    out = fit(text, width, align=align, fillchar=fill)
                    assert cell_len(out) == width, (align, text, width, fill)


def test_a_fill_glue_is_measured_across_an_escape_sequence_as_a_break() -> None:
    # An escape sequence ends a cluster, so the fill next to it never glues.
    assert rjust("\x1b[1m\ufe0fab\x1b[0m", 5, "#") == "###\x1b[1m\ufe0fab\x1b[0m"


def test_the_fill_seam_is_measured_with_the_ambiguous_policy() -> None:
    # U+2194 is two cells under ambiguous=2; the fill next to it joins nothing.
    assert rjust("\u2194", 4, "#", ambiguous=2) == "##\u2194"
    assert ljust("\u2194", 4, "#", ambiguous=2) == "\u2194##"
    # "#" + VS16 is a two-cell emoji presentation sequence: the left fill is a space.
    assert center("\ufe0f\u2194", 5, "#", ambiguous=2) == " \ufe0f\u2194##"


def test_the_fill_seam_is_measured_with_the_policy_the_caller_passes() -> None:
    # U+2194 + ZWJ + U+2764 is one cluster: 2 cells, while the parts add up to 3 under
    # ambiguous=2 and to 2 under the default, so only the caller's policy gets these right.
    assert ljust("↔‍", 3, "❤", ambiguous=2) == "↔‍ "
    assert rjust("‍↔", 3, "❤", ambiguous=2) == " ‍↔"
    assert center("↔‍", 4, "❤", ambiguous=2) == "❤↔‍ "


def test_an_ambiguous_fill_pads_as_one_cell_under_the_default_policy() -> None:
    assert rjust("a", 3, "·") == "··a"
    assert center("", 4, "™") == "™" * 4


def test_the_left_seam_is_measured_on_the_whole_run_of_fills() -> None:
    # Regional indicator fills pair into flags, and a flag glues to a SpacingMark.
    assert rjust("ः", 3, "🇦") == "🇦 ः"
    assert cell_len(rjust("ः", 5, "🇦")) == 5
    assert cell_len(center("ः", 5, "🇦")) == 5


@pytest.mark.parametrize("fill", ["☠‍", "©‍", "❤‍"])
def test_a_fill_that_joins_its_own_copies_is_rejected(fill: str) -> None:
    # Repeated, the copies form one ZWJ sequence of two cells, so no width could hold.
    for pad in (ljust, rjust, center):
        with pytest.raises(ValueError, match="fillchar must be a single one-cell character"):
            pad("ab", 6, fill)
    with pytest.raises(ValueError, match="fillchar must be a single one-cell character"):
        fit("ab", 6, fillchar=fill)


def test_a_fill_whose_copies_add_up_pads_to_every_width() -> None:
    for fill in FILLS:
        for width in range(12):
            for pad in (ljust, rjust, center):
                assert cell_len(pad("", width, fill)) == width, (pad.__name__, fill, width)
