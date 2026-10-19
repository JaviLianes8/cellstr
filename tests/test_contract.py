"""The complete public promise of cellstr, one test per clause.

Width vectors below are derived from the UCD 18.0.0 files (data/ucd/, fetched): each
named code point's East_Asian_Width, General_Category and emoji properties were read from
EastAsianWidth.txt, DerivedGeneralCategory.txt and emoji-data.txt. The slicing and
padding clauses are hand-written statements of the documented behaviour.
"""

from __future__ import annotations

import importlib.resources
import inspect
import re
from pathlib import Path

import pytest
from conftest import needs_ucd

import cellstr
from cellstr import (
    UNICODE_VERSION,
    Cell,
    Truncation,
    cell_len,
    cell_slice,
    char_width,
    fit,
    iter_cells,
    strip_ansi,
    truncate,
)

ROOT = Path(__file__).resolve().parent.parent

# The public API. This list is the contract; the test below fails if they disagree.
PUBLIC_API: list[str] = [
    "UNICODE_VERSION",
    "Align",
    "Cell",
    "Position",
    "Truncation",
    "cell_len",
    "cell_slice",
    "center",
    "char_width",
    "expand_tabs",
    "fit",
    "grapheme_width",
    "iter_cells",
    "iter_graphemes",
    "ljust",
    "rjust",
    "strip_ansi",
    "truncate",
    "truncate_detailed",
]
# 0.1.0 signatures must keep working: same names, same positional parameters.
LEGACY = {
    "cell_len": ["text"],
    "char_width": ["char"],
    "strip_ansi": ["text"],
    "cell_slice": ["text", "start", "stop"],
    "ljust": ["text", "width", "fillchar"],
    "rjust": ["text", "width", "fillchar"],
    "center": ["text", "width", "fillchar"],
    "truncate": ["text", "width", "suffix"],
}
# (code point, width with ambiguous=1, width with ambiguous=2, UCD source of the value)
UCD_VECTORS = [
    (0x0041, 1, 1, "EastAsianWidth Na"),
    (0x00A1, 1, 2, "EastAsianWidth A"),
    (0x0300, 0, 0, "DerivedGeneralCategory Mn"),
    (0x20DD, 0, 0, "DerivedGeneralCategory Me"),
    (0x200B, 0, 0, "DerivedGeneralCategory Cf"),
    (0x00AD, 1, 2, "Cf, but SOFT HYPHEN is visible; EastAsianWidth A"),
    (0x0903, 1, 1, "DerivedGeneralCategory Mc, EastAsianWidth N"),
    (0x1160, 0, 0, "Hangul medial vowel, GraphemeBreakProperty V"),
    (0x3000, 2, 2, "EastAsianWidth F"),
    (0x4E00, 2, 2, "EastAsianWidth W"),
    (0x9FFF, 2, 2, "EastAsianWidth W, last CJK Unified Ideograph of the block"),
    (0xFF61, 1, 1, "EastAsianWidth H"),
    (0x1F600, 2, 2, "EastAsianWidth W, Emoji_Presentation"),
    (0x263A, 1, 1, "EastAsianWidth N, Emoji without Emoji_Presentation"),
    (0x2E3A, 1, 1, "EastAsianWidth N"),
    (0x3FFFD, 2, 2, "EastAsianWidth W, reserved (Cn) in Plane 3"),
    (0xE000, 1, 2, "EastAsianWidth A (private use)"),
    (0x10FFFF, 1, 1, "EastAsianWidth N (noncharacter)"),
    (0x0600, 1, 1, "Cf, but PropList Prepended_Concatenation_Mark: visible"),
    (0x110CD, 1, 1, "Cf, but PropList Prepended_Concatenation_Mark: visible"),
    (0xFFF9, 0, 0, "Cf, not a Prepended_Concatenation_Mark"),
    (0x3164, 0, 0, "Lo, DerivedCoreProperties Default_Ignorable_Code_Point"),
    (0xFFA0, 0, 0, "Lo, DerivedCoreProperties Default_Ignorable_Code_Point"),
    (0x115F, 2, 2, "Default_Ignorable_Code_Point, but a leading jamo; EastAsianWidth W"),
    (0x2065, 0, 0, "Cn, Default_Ignorable_Code_Point (reserved)"),
    (0xE0FFF, 0, 0, "Cn, Default_Ignorable_Code_Point (reserved)"),
    (0x2028, 0, 0, "DerivedGeneralCategory Zl"),
    (0x2029, 0, 0, "DerivedGeneralCategory Zp"),
    (0x1F1E6, 1, 1, "Regional_Indicator, EastAsianWidth N"),
    (0x302E, 2, 2, "DerivedGeneralCategory Mc, EastAsianWidth W"),
]
SAMPLE = "\x1b[1mNa\u00efve\x1b[0m caf\u00e9 \U0001f469\u200d\U0001f4bb "
SAMPLE += "\U0001f1ef\U0001f1f5 \u4f60e\u0301!"


def test_all_lists_exactly_the_public_api() -> None:
    assert sorted(cellstr.__all__) == sorted(PUBLIC_API)
    for name in cellstr.__all__:
        assert hasattr(cellstr, name)


def test_legacy_signatures_still_accept_the_old_calls() -> None:
    for name, params in LEGACY.items():
        signature = inspect.signature(getattr(cellstr, name))
        positional = [
            p.name for p in signature.parameters.values() if p.kind is p.POSITIONAL_OR_KEYWORD
        ]
        assert positional == params, name
        others = [p for p in signature.parameters.values() if p.kind is not p.POSITIONAL_OR_KEYWORD]
        assert all(p.kind is p.KEYWORD_ONLY and p.default is not p.empty for p in others), name


def test_version_matches_pyproject_and_changelog() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version = "([^"]+)"', pyproject, re.M)
    assert match is not None and match.group(1) == cellstr.__version__
    assert re.fullmatch(r"\d+\.\d+\.\d+", cellstr.__version__)
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert f"## [{cellstr.__version__}]" in changelog


def test_the_package_ships_type_information_and_a_script() -> None:
    assert importlib.resources.files("cellstr").joinpath("py.typed").is_file()
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'cellstr = "cellstr._cli:main"' in pyproject


@needs_ucd
def test_unicode_version_is_the_snapshot_version() -> None:
    head = (ROOT / "data" / "ucd" / "EastAsianWidth.txt").read_text(encoding="utf-8")[:60]
    assert f"EastAsianWidth-{UNICODE_VERSION}.txt" in head


@pytest.mark.parametrize(("cp", "narrow", "wide", "source"), UCD_VECTORS)
def test_width_vectors_from_the_ucd(cp: int, narrow: int, wide: int, source: str) -> None:
    assert char_width(chr(cp)) == narrow, source
    assert char_width(chr(cp), ambiguous=2) == wide, source


def test_measuring_ignores_escapes_and_counts_clusters() -> None:
    assert cell_len(SAMPLE) == cell_len(strip_ansi(SAMPLE)) == 21


def test_cells_cover_the_text_exactly_and_add_up() -> None:
    cells = list(iter_cells(SAMPLE))
    assert all(isinstance(c, Cell) for c in cells)
    assert "".join(c.text for c in cells) == SAMPLE
    assert sum(c.width for c in cells) == cell_len(SAMPLE)
    assert all(c.width == 0 for c in cells if c.escape)


def test_slices_never_exceed_the_range_and_keep_every_escape() -> None:
    for start in range(0, 24):
        for stop in range(start, 25):
            piece = cell_slice(SAMPLE, start, stop)
            assert cell_len(piece) <= stop - start
            assert piece.count("\x1b") == SAMPLE.count("\x1b")


def test_truncation_never_exceeds_the_width() -> None:
    for width in range(0, 25):
        for position in ("end", "start", "middle"):
            result = truncate(SAMPLE, width, position=position)
            assert cell_len(result) <= width


def test_fit_is_always_exact() -> None:
    for width in range(0, 25):
        assert cell_len(fit(SAMPLE, width)) == width


def test_results_are_immutable_records() -> None:
    result = Truncation("ab", 2, 2, False)
    with pytest.raises(AttributeError):
        result.text = "x"  # type: ignore[misc]
    assert Cell("a", 1, 0, False)._fields == ("text", "width", "column", "escape")
