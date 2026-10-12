"""char_width over every code point equals the documented rule applied to the raw UCD files.

The expected values are computed here, independently of the generator, straight from
data/ucd/EastAsianWidth.txt and data/ucd/DerivedGeneralCategory.txt (fetched unmodified
from unicode.org, see data/ucd/SOURCES.txt). The rule is Markus Kuhn's wcwidth with
controls at 0, as documented in GUIDE.md.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from cellstr import char_width

UCD = Path(__file__).resolve().parent.parent / "data" / "ucd"
LAST = 0x10FFFF


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
    widths = []
    for cp in range(LAST + 1):
        if cp == 0x00AD:  # SOFT HYPHEN: Cf but visible, East Asian Ambiguous
            widths.append(ambiguous if eaw[cp] == "A" else 1)
        elif gc[cp] in ("Cc", "Mn", "Me", "Cf") or 0x1160 <= cp <= 0x11FF or 0xD7B0 <= cp <= 0xD7FF:
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
    assert counts[0] > 2000 and counts[2] > 180000 and ambiguous > 100000
