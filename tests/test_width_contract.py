"""char_width over every code point equals the documented rule applied to the raw UCD files.

The expected values are computed here, independently of the generator, straight from the
fetched data/ucd/ files (not committed; scripts/fetch_upstream.py fetches them as pinned in
data/ucd/MANIFEST.json, and these tests skip until then): EastAsianWidth.txt,
DerivedGeneralCategory.txt, DerivedCoreProperties.txt and PropList.txt. The rule is the one
GUIDE.md states: Markus Kuhn's wcwidth with controls at 0 and three refinements
(Prepended_Concatenation_Mark visible, Default_Ignorable_Code_Point zero, Zl and Zp zero).
"""

from __future__ import annotations

import pytest
from conftest import UCD, needs_ucd

from cellstr import char_width

pytestmark = needs_ucd
LAST = 0x10FFFF
ZERO_GC = ("Cc", "Mn", "Me", "Cf", "Zl", "Zp")


def _fields(name: str) -> list[tuple[range, str]]:
    rows: list[tuple[range, str]] = []
    for raw in (UCD / name).read_text(encoding="utf-8").splitlines():
        data = raw.split("#", 1)[0]
        if ";" not in data:
            continue
        span, value = (part.strip() for part in data.split(";")[:2])
        low, _, high = span.partition("..")
        rows.append((range(int(low, 16), int(high or low, 16) + 1), value))
    return rows


def _with(name: str, value: str) -> set[int]:
    return {cp for span, found in _fields(name) if found == value for cp in span}


def _expected(ambiguous: int) -> list[int]:
    eaw = ["N"] * (LAST + 1)
    # The unassigned-default rules stated in the EastAsianWidth.txt header.
    for low, high in ((0x3400, 0x4DBF), (0x4E00, 0x9FFF), (0xF900, 0xFAFF)):
        eaw[low : high + 1] = ["W"] * (high - low + 1)
    for low, high in ((0x20000, 0x2FFFD), (0x30000, 0x3FFFD)):
        eaw[low : high + 1] = ["W"] * (high - low + 1)
    for span, value in _fields("EastAsianWidth.txt"):
        for cp in span:
            eaw[cp] = value
    gc = ["Cn"] * (LAST + 1)
    for span, value in _fields("DerivedGeneralCategory.txt"):
        for cp in span:
            gc[cp] = value
    ignorable = _with("DerivedCoreProperties.txt", "Default_Ignorable_Code_Point")
    visible = _with("PropList.txt", "Prepended_Concatenation_Mark") | {0x00AD, 0x115F}
    widths = []
    for cp in range(LAST + 1):
        hangul = 0x1160 <= cp <= 0x11FF or 0xD7B0 <= cp <= 0xD7FF
        if cp not in visible and (gc[cp] in ZERO_GC or cp in ignorable or hangul):
            widths.append(0)
        elif eaw[cp] in ("W", "F"):
            widths.append(2)
        elif eaw[cp] == "A":
            widths.append(ambiguous)
        else:
            widths.append(1)
    return widths


@pytest.mark.parametrize("ambiguous", [1, 2])
def test_char_width_of_every_code_point(ambiguous: int) -> None:
    expected = _expected(ambiguous)
    wrong = [
        hex(cp)
        for cp in range(LAST + 1)
        if char_width(chr(cp), ambiguous=ambiguous) != expected[cp]
    ]
    assert wrong == []


def test_the_snapshot_covers_every_width_class() -> None:
    counts = {width: 0 for width in (0, 1, 2)}
    for width in _expected(1):
        counts[width] += 1
    ambiguous = sum(1 for a, b in zip(_expected(1), _expected(2), strict=True) if a != b)
    assert counts[0] > 6000 and counts[2] > 180000 and ambiguous > 100000


def test_the_refinements_cover_what_they_name() -> None:
    # Fixed facts of the 18.0.0 files: if a new Unicode version moves them, the GUIDE's
    # list of refinements needs a fresh look.
    marks = _with("PropList.txt", "Prepended_Concatenation_Mark")
    assert len(marks) == 13 and all(char_width(chr(cp)) == 1 for cp in marks)
    ignorable = _with("DerivedCoreProperties.txt", "Default_Ignorable_Code_Point")
    nonzero = sorted(cp for cp in ignorable if char_width(chr(cp)))
    assert nonzero == [0x00AD, 0x115F]
    assert char_width("\u2028") == char_width("\u2029") == 0
