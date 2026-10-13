"""Run every case of the official Unicode GraphemeBreakTest.txt against iter_graphemes.

The file is data/ucd/GraphemeBreakTest.txt, which is not committed:
`python scripts/fetch_upstream.py` fetches it as pinned in data/ucd/MANIFEST.json.
These tests skip until then.
"""

from __future__ import annotations

import re

import pytest
from conftest import UCD, needs_ucd, ucd_fetched

from cellstr import UNICODE_VERSION, iter_graphemes

FIXTURE = UCD / "GraphemeBreakTest.txt"
pytestmark = needs_ucd


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


CASES = _cases() if ucd_fetched() else []


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
