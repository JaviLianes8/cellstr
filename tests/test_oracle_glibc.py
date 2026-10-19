"""Cross-check char_width against glibc's wcwidth(), captured from a real run.

tests/fixtures/glibc-wcwidth.txt is the output of scripts/capture_glibc.py: glibc 2.43
(Ubuntu 26.04 LTS under WSL 2, locale C.UTF-8) asked for every code point on 2026-10-18;
tests/fixtures/MANIFEST.json records how it was made, its size and its sha256. glibc 2.43
knows Unicode 17.0, so the code points DerivedAge.txt dates 18.0 are left out. Every other
disagreement belongs to one of the differences GUIDE.md documents, and the counts are
pinned so a new one fails. The comparison needs the fetched Unicode data files.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
from collections import Counter
from pathlib import Path

import pytest
from conftest import UCD, needs_ucd

from cellstr import char_width

FIXTURES = Path(__file__).resolve().parent / "fixtures"
GLIBC = FIXTURES / "glibc-wcwidth.txt"


def _glibc() -> list[int]:
    widths: list[int | None] = [None] * 0x110000
    for line in GLIBC.read_text(encoding="utf-8").splitlines():
        if not line.startswith("#"):
            first, last, width = line.split()
            low, high = int(first, 16), int(last, 16)
            widths[low : high + 1] = [int(width)] * (high - low + 1)
    assert None not in widths
    return [width for width in widths if width is not None]


def _property(name: str) -> dict[int, str]:
    found: dict[int, str] = {}
    for raw in (UCD / name).read_text(encoding="utf-8").splitlines():
        data = raw.split("#", 1)[0]
        if ";" in data:
            span, value = (part.strip() for part in data.split(";")[:2])
            low, _, high = span.partition("..")
            found.update(dict.fromkeys(range(int(low, 16), int(high or low, 16) + 1), value))
    return found


def test_the_fixture_is_the_recorded_capture() -> None:
    entry = json.loads((FIXTURES / "MANIFEST.json").read_text(encoding="utf-8"))[GLIBC.name]
    data = GLIBC.read_bytes()
    assert (len(data), hashlib.sha256(data).hexdigest()) == (entry["size"], entry["sha256"])
    assert data.startswith(b"# glibc 2.43 wcwidth(), locale C.UTF-8")


def test_the_runs_cover_every_code_point_in_order() -> None:
    expected_start = 0
    for line in GLIBC.read_text(encoding="utf-8").splitlines():
        if not line.startswith("#"):
            first, last, width = line.split()
            assert int(first, 16) == expected_start and int(last, 16) >= int(first, 16)
            assert int(width) in (-1, 0, 1, 2)
            expected_start = int(last, 16) + 1
    assert expected_start == 0x110000
    assert len(_glibc()) == 0x110000


@needs_ucd
def test_every_code_point_agrees_or_has_a_documented_reason() -> None:
    glibc = _glibc()
    gc = _property("DerivedGeneralCategory.txt")
    age = _property("DerivedAge.txt")
    eaw = _property("EastAsianWidth.txt")
    reasons: Counter[str] = Counter()
    for cp in range(0x110000):
        ours, theirs, category = char_width(chr(cp)), glibc[cp], gc.get(cp, "Cn")
        if age.get(cp) == "18.0":
            reasons["new in Unicode 18.0"] += 1
        elif theirs == -1 and category == "Cc" and ours == 0:
            reasons["control: 0 here, -1 (not printable) in glibc"] += 1
        elif theirs == -1 and category in ("Zl", "Zp") and ours == 0:
            reasons["line or paragraph separator: 0 here, -1 in glibc"] += 1
        elif theirs == -1 and category in ("Cn", "Cs"):
            reasons["unassigned, noncharacter or surrogate: -1 in glibc"] += 1
        elif ours == theirs:
            reasons["agree"] += 1
        elif category == "Cf" and (ours, theirs) == (0, 1):
            reasons["format character: 0 here, 1 in glibc"] += 1
        elif eaw.get(cp) == "A" and (ours, theirs) == (1, 2):
            reasons["East Asian Ambiguous: 1 here, 2 in glibc"] += 1
        else:
            reasons[f"unexplained {cp:04X}: {ours} here, {theirs} in glibc"] += 1
    assert reasons == {
        "agree": 297_241,
        "new in Unicode 18.0": 13_007,
        "control: 0 here, -1 (not printable) in glibc": 64,
        "line or paragraph separator: 0 here, -1 in glibc": 2,
        "unassigned, noncharacter or surrogate: -1 in glibc": 803_771,
        "format character: 0 here, 1 in glibc": 19,
        "East Asian Ambiguous: 1 here, 2 in glibc": 8,
    }


@needs_ucd
def test_every_known_code_point_agrees_with_glibc_or_with_wcwidth() -> None:
    wcwidth = pytest.importorskip("wcwidth")
    if importlib.metadata.version("wcwidth") != "0.9.2":
        pytest.skip("the figures are pinned to wcwidth 0.9.2")
    glibc = _glibc()
    gc = _property("DerivedGeneralCategory.txt")
    age = _property("DerivedAge.txt")
    agreement: Counter[str] = Counter()
    for cp, version in age.items():
        if version == "18.0" or gc.get(cp, "Cn") in ("Cn", "Cs"):
            continue
        ours = char_width(chr(cp))
        with_glibc = ours == max(0, glibc[cp])
        with_wcwidth = ours == max(0, wcwidth.wcwidth(chr(cp)))
        agreement[("neither", "wcwidth", "glibc", "both")[2 * with_glibc + with_wcwidth]] += 1
    assert agreement == {"both": 296_810, "glibc": 497, "wcwidth": 27}
