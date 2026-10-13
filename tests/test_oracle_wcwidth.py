"""Cross-check against the ``wcwidth`` package, used here only as a test oracle.

Every code point is compared. Each disagreement must be explained by one of the
documented reasons (GUIDE.md, "Differences from the wcwidth package"):

* data: the oracle's tables are Unicode 15.1.0 and ours are newer, so the code point is
  new, or its East_Asian_Width or General_Category changed. The 15.1.0 values come from
  data/ucd/EastAsianWidth-15.1.0.txt, which is not committed: scripts/fetch_upstream.py
  fetches it from https://www.unicode.org/Public/15.1.0/ucd/EastAsianWidth.txt as pinned
  in data/ucd/MANIFEST.json (its comments carry the General_Category of every assigned
  code point). These tests skip until the Unicode data is fetched.
* policy: spacing marks (Mc) are 1 cell here, as in Kuhn's wcwidth and glibc, and 0 in
  the oracle; SOFT HYPHEN, LINE SEPARATOR and PARAGRAPH SEPARATOR are 1 (Kuhn); a lone
  emoji skin tone modifier is 2 (it is East Asian Wide) where the oracle says 0.
"""

from __future__ import annotations

import hashlib
import re
from collections import Counter
from pathlib import Path

import pytest
from conftest import MANIFEST, UCD, needs_ucd

from cellstr import cell_len, char_width

wcwidth = pytest.importorskip("wcwidth")

pytestmark = needs_ucd
OLD = UCD / "EastAsianWidth-15.1.0.txt"
_ROW = re.compile(r"^([0-9A-F]+)(?:\.\.([0-9A-F]+))?\s*;\s*(\w+)\s*#\s*(\w\w|L&)")


def _table(path: Path, with_gc: bool) -> dict[int, tuple[str, str]]:
    found: dict[int, tuple[str, str]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = _ROW.match(line) if with_gc else None
        if match:
            low, high = int(match.group(1), 16), int(match.group(2) or match.group(1), 16)
            for cp in range(low, high + 1):
                found[cp] = (match.group(3), match.group(4))
    return found


def _categories() -> dict[int, str]:
    out: dict[int, str] = {}
    for line in (UCD / "DerivedGeneralCategory.txt").read_text(encoding="utf-8").splitlines():
        match = re.match(r"^([0-9A-F]+)(?:\.\.([0-9A-F]+))?\s*;\s*(\w+)", line)
        if match:
            low, high = int(match.group(1), 16), int(match.group(2) or match.group(1), 16)
            for cp in range(low, high + 1):
                out[cp] = match.group(3)
    return out


def _reason(
    cp: int,
    ours: int,
    theirs: int,
    old: dict[int, tuple[str, str]],
    new: dict[int, tuple[str, str]],
    gc: dict[int, str],
) -> str | None:
    if cp not in old:
        return "data: new since 15.1"
    if new.get(cp, ("N", ""))[0] != old[cp][0]:
        return "data: East_Asian_Width changed"
    if gc.get(cp, "Cn") != old[cp][1] and old[cp][1] != "L&":
        return "data: General_Category changed"
    if gc.get(cp) == "Mc" and theirs == 0:
        return "policy: spacing mark"
    if cp in (0x00AD, 0x2028, 0x2029) and (ours, theirs) == (1, 0):
        return "policy: Kuhn width 1"
    if 0x1F3FB <= cp <= 0x1F3FF and (ours, theirs) == (2, 0):
        return "policy: lone skin tone"
    return None


def test_the_15_1_fixture_is_the_file_as_fetched() -> None:
    digest = hashlib.sha256(OLD.read_bytes()).hexdigest()
    assert digest == MANIFEST[OLD.name]["sha256"]


def test_every_code_point_agrees_or_has_a_documented_reason() -> None:
    if wcwidth.list_versions()[-1] != "15.1.0":
        pytest.skip("the documented differences are pinned to an oracle built on Unicode 15.1.0")
    old = _table(OLD, True)
    new = _table(UCD / "EastAsianWidth.txt", True)
    gc = _categories()
    reasons: Counter[str] = Counter()
    unexplained = []
    for cp in range(0x110000):
        ours = char_width(chr(cp))
        theirs = max(0, wcwidth.wcwidth(chr(cp), "latest"))
        if ours == theirs:
            reasons["agree"] += 1
            continue
        reason = _reason(cp, ours, theirs, old, new, gc)
        reasons[reason or "unexplained"] += 1
        if reason is None:
            unexplained.append(hex(cp))
    assert unexplained == []
    # The exact figures published in GUIDE.md, "Differences from the wcwidth package".
    assert dict(reasons) == {
        "agree": 1_112_200,
        "data: new since 15.1": 1263,
        "data: East_Asian_Width changed": 188,
        "data: General_Category changed": 1,
        "policy: spacing mark": 452,
        "policy: Kuhn width 1": 3,
        "policy: lone skin tone": 5,
    }


SEQUENCES = {
    "family ZWJ sequence": ("\U0001f468\u200d\U0001f469\u200d\U0001f467", 2),
    "VS16 emoji presentation": ("\u2764\ufe0f", 2),
    "text default emoji": ("\u2764", 1),
    "flag": ("\U0001f1ea\U0001f1f8", 2),
    "skin tone sequence": ("\U0001f44d\U0001f3fd", 2),
    "keycap": ("1\ufe0f\u20e3", 2),
    "combining accent": ("e\u0301", 1),
    "conjoining Hangul": ("\u1100\u1161\u11a8", 2),
    "CJK and ASCII": ("ab\u4f60\u597d", 6),
}


@pytest.mark.parametrize("name", list(SEQUENCES))
def test_strings_agree_with_wcswidth(name: str) -> None:
    text, width = SEQUENCES[name]
    assert cell_len(text) == width == wcwidth.wcswidth(text)


def test_documented_string_differences() -> None:
    # VS15 asks for text presentation: one cell here, the oracle keeps two.
    assert (cell_len("\u231a\ufe0e"), wcwidth.wcswidth("\u231a\ufe0e")) == (1, 2)
    # A Devanagari spacing vowel sign takes a cell here, as in glibc; the oracle says 0.
    assert (cell_len("\u0915\u093f"), wcwidth.wcswidth("\u0915\u093f")) == (2, 1)
