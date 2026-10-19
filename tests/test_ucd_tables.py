"""The embedded tables must equal a fresh run of the generator over the fetched UCD files."""

from __future__ import annotations

import hashlib
import importlib.util
import re
from pathlib import Path
from types import ModuleType

from conftest import MANIFEST, UCD, needs_ucd

import cellstr
from cellstr._props import (
    EMOJI_BIT,
    EXT_PICT_BIT,
    GCB,
    MODIFIER_BIT,
    TEXT_VS_BIT,
    WIDTH_SHIFT,
    prop,
)

ROOT = Path(__file__).resolve().parent.parent
# The package under test: the source tree, or the installed wheel when the tests run from
# an unpacked sdist without src/, so the shipped tables are the ones checked.
PACKAGE = Path(cellstr.__file__).resolve().parent


def _generator() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "gen_ucd_tables", ROOT / "scripts" / "gen_ucd_tables.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@needs_ucd
def test_committed_tables_equal_generator_output() -> None:
    files = _generator().render(UCD)
    assert files, "generator produced nothing"
    for name, text in files.items():
        assert (PACKAGE / name).read_text(encoding="utf-8") == text, f"{name} is stale"


@needs_ucd
def test_no_stray_generated_modules() -> None:
    expected = set(_generator().render(UCD))
    assert {p.name for p in PACKAGE.glob("_ucd_*.py")} == expected


@needs_ucd
def test_generated_modules_stay_short() -> None:
    for name in _generator().render(UCD):
        assert len((PACKAGE / name).read_text(encoding="utf-8").splitlines()) <= 200


@needs_ucd
def test_snapshot_files_match_the_manifest() -> None:
    assert {p.name for p in UCD.glob("*.txt")} == set(MANIFEST)
    for name, entry in MANIFEST.items():
        data = (UCD / name).read_bytes()
        assert (len(data), hashlib.sha256(data).hexdigest()) == (entry["size"], entry["sha256"])


@needs_ucd
def test_every_snapshot_file_is_the_same_unicode_version() -> None:
    version = _generator().unicode_version(UCD)
    short = version.rsplit(".", 1)[0]  # emoji-test.txt states only "Version: 18.0"
    pattern = rf"-{re.escape(version)}\.txt|Version: ({re.escape(version)}|{re.escape(short)})$"
    for name in MANIFEST:
        head = (UCD / name).read_text(encoding="utf-8")[:2000]
        assert re.search(pattern, head, re.M), name


def test_spot_properties_from_the_tables() -> None:
    assert prop(0x0D) & 0x0F == GCB["CR"]
    assert prop(0x0301) & 0x0F == GCB["Extend"]
    assert prop(0x200D) & 0x0F == GCB["ZWJ"]
    assert prop(0x1F1E6) & 0x0F == GCB["Regional_Indicator"]
    assert prop(0xAC00) & 0x0F == GCB["LV"]
    assert prop(0x1F600) & EXT_PICT_BIT and prop(0x1F600) & EMOJI_BIT
    assert prop(0x1F3FB) & MODIFIER_BIT
    assert prop(ord("#")) & EMOJI_BIT and not prop(ord("A")) & EMOJI_BIT
    assert prop(0x0915) >> 5 & 0x03 == 2  # DEVANAGARI LETTER KA is InCB=Consonant
    assert (prop(0x4E00) >> WIDTH_SHIFT) & 0x03 == 2
    assert (prop(0x0301) >> WIDTH_SHIFT) & 0x03 == 0
    assert (prop(0x00A1) >> WIDTH_SHIFT) & 0x03 == 3  # INVERTED EXCLAMATION MARK is ambiguous
    assert (prop(0x10FFFF) >> WIDTH_SHIFT) & 0x03 == 1
    assert prop(0x231A) & TEXT_VS_BIT and prop(ord("#")) & TEXT_VS_BIT  # listed with VS15
    assert not prop(0x1F600) & TEXT_VS_BIT and not prop(ord("A")) & TEXT_VS_BIT
