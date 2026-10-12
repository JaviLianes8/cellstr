"""Run every case of the official Unicode GraphemeBreakTest.txt against iter_graphemes.

The fixture is data/ucd/GraphemeBreakTest.txt, fetched unmodified from unicode.org
(see data/ucd/SOURCES.txt for the URL, date and checksum).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from cellstr import UNICODE_VERSION, iter_graphemes

FIXTURE = Path(__file__).resolve().parent.parent / "data" / "ucd" / "GraphemeBreakTest.txt"


def _cases() -> list[tuple[int, list[str]]]:
    cases: list[tuple[int, list[str]]] = []
    for number, raw in enumerate(FIXTURE.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        clusters: list[str] = []
        current = ""
        for token in line.split()[1:]:
            if token == "\u00f7":
                clusters.append(current)
                current = ""
            elif token != "\u00d7":
                current += chr(int(token, 16))
        cases.append((number, clusters))
    return cases


CASES = _cases()


def test_fixture_matches_the_embedded_unicode_version() -> None:
    header = FIXTURE.read_text(encoding="utf-8").splitlines()[0]
    match = re.search(r"GraphemeBreakTest-(\d+\.\d+\.\d+)\.txt", header)
    assert match is not None
    assert match.group(1) == UNICODE_VERSION


def test_fixture_is_complete() -> None:
    # Unicode 18.0.0 ships 853 cases; a truncated fixture would silently test less.
    assert len(CASES) == 853


@pytest.mark.parametrize(("line", "expected"), CASES, ids=[f"line{n}" for n, _ in CASES])
def test_official_case(line: int, expected: list[str]) -> None:
    text = "".join(expected)
    assert list(iter_graphemes(text)) == expected, f"GraphemeBreakTest.txt line {line}"
