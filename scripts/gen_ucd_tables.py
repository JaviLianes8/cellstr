"""Generate the embedded Unicode property tables from the fetched UCD files.

Usage::

    python scripts/gen_ucd_tables.py            # rewrite src/cellstr/_ucd_*.py
    python scripts/gen_ucd_tables.py --check    # exit 1 if the files are stale

Inputs live in ``data/ucd/``, which git ignores: ``python scripts/fetch_upstream.py``
fetches them as pinned in ``data/ucd/MANIFEST.json`` (URL, Unicode version, sha256).
The output is a run-length list covering every code point from U+0000 to U+10FFFF. Each
run stores one packed code: Grapheme_Cluster_Break in bits 0-3, Extended_Pictographic in
bit 4, Indic_Conjunct_Break in bits 5-6, Emoji in bit 7, Emoji_Modifier in bit 8 and the
width class (0 zero, 1 narrow, 2 wide, 3 East Asian Ambiguous) in bits 9-10.

The width class follows Markus Kuhn's wcwidth rules applied to this Unicode version:
U+0000, controls (Cc), Mn, Me and Cf are zero except SOFT HYPHEN; Hangul medial vowels
and final consonants (U+1160..U+11FF and U+D7B0..U+D7FF) are zero; East_Asian_Width W
and F are wide; A is ambiguous; everything else is narrow.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UCD_DIR = ROOT / "data" / "ucd"
OUT_DIR = ROOT / "src" / "cellstr"

_GCB_HEAD = ("Other", "CR", "LF", "Control", "Extend", "ZWJ", "Regional_Indicator")
GCB_NAMES = (*_GCB_HEAD, "Prepend", "SpacingMark", "L", "V", "T", "LV", "LVT")
INCB_NAMES = ("None", "Linker", "Consonant", "Extend")
EXT_PICT_BIT = 1 << 4
INCB_SHIFT = 5
EMOJI_BIT = 1 << 7
MODIFIER_BIT = 1 << 8
WIDTH_SHIFT = 9
ZERO, NARROW, WIDE, AMBIGUOUS = 0, 1, 2, 3
MAX_CP = 0x10FFFF
# UAX #11: unassigned code points in these ranges default to W, every other one to N.
_EAW_BMP = ((0x3400, 0x4DBF), (0x4E00, 0x9FFF), (0xF900, 0xFAFF))
EAW_WIDE_DEFAULTS = (*_EAW_BMP, (0x20000, 0x2FFFD), (0x30000, 0x3FFFD))
ZERO_CATEGORIES = frozenset({"Cc", "Mn", "Me", "Cf"})
HANGUL_COMBINING = ((0x1160, 0x11FF), (0xD7B0, 0xD7FF))
SOFT_HYPHEN = 0x00AD
LINE_WIDTH = 88
LINES_PER_PART = 180
DIGITS = "0123456789abcdefghijklmnopqrstuvwxyz"

_LINE = re.compile(r"^([0-9A-F]{4,6})(?:\.\.([0-9A-F]{4,6}))?\s*;\s*([^#]+?)\s*(?:#|$)")


def _ranges(path: Path) -> list[tuple[int, int, str]]:
    """Return ``(first, last, value)`` for every data line of a UCD file."""
    found: list[tuple[int, int, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = _LINE.match(line)
        if match:
            first = int(match.group(1), 16)
            last = int(match.group(2) or match.group(1), 16)
            found.append((first, last, match.group(3)))
    return found


def unicode_version(ucd_dir: Path = UCD_DIR) -> str:
    """Read the Unicode version from the EastAsianWidth.txt header."""
    head = (ucd_dir / "EastAsianWidth.txt").read_text(encoding="utf-8")
    match = re.search(r"EastAsianWidth-(\d+\.\d+\.\d+)\.txt", head)
    if match is None:
        raise ValueError("cannot find the Unicode version in EastAsianWidth.txt")
    return match.group(1)


def width_classes(ucd_dir: Path = UCD_DIR) -> bytearray:
    """Return the width class of every code point (see the module docstring)."""
    eaw = ["N"] * (MAX_CP + 1)
    for first, last in EAW_WIDE_DEFAULTS:
        eaw[first : last + 1] = ["W"] * (last - first + 1)
    for first, last, value in _ranges(ucd_dir / "EastAsianWidth.txt"):
        eaw[first : last + 1] = [value] * (last - first + 1)
    classes = bytearray(
        WIDE if value in ("W", "F") else AMBIGUOUS if value == "A" else NARROW for value in eaw
    )
    for first, last, value in _ranges(ucd_dir / "DerivedGeneralCategory.txt"):
        if value in ZERO_CATEGORIES:
            classes[first : last + 1] = bytes(last - first + 1)
    for first, last in HANGUL_COMBINING:
        classes[first : last + 1] = bytes(last - first + 1)
    classes[SOFT_HYPHEN] = AMBIGUOUS if eaw[SOFT_HYPHEN] == "A" else NARROW
    return classes


def property_codes(ucd_dir: Path = UCD_DIR) -> list[int]:
    """Return one packed property code per code point, built from the UCD files."""
    codes = [width << WIDTH_SHIFT for width in width_classes(ucd_dir)]
    for first, last, value in _ranges(ucd_dir / "GraphemeBreakProperty.txt"):
        gcb = GCB_NAMES.index(value)
        for cp in range(first, last + 1):
            codes[cp] = (codes[cp] & ~0x0F) | gcb
    bits = {
        "Extended_Pictographic": EXT_PICT_BIT,
        "Emoji": EMOJI_BIT,
        "Emoji_Modifier": MODIFIER_BIT,
    }
    for first, last, value in _ranges(ucd_dir / "emoji-data.txt"):
        if value in bits:
            for cp in range(first, last + 1):
                codes[cp] |= bits[value]
    for first, last, value in _ranges(ucd_dir / "DerivedCoreProperties.txt"):
        parts = [part.strip() for part in value.split(";")]
        if parts[0] == "InCB":
            incb = INCB_NAMES.index(parts[1]) << INCB_SHIFT
            for cp in range(first, last + 1):
                codes[cp] |= incb
    return codes


def _base36(number: int, size: int = 1) -> str:
    text = ""
    while True:
        number, digit = divmod(number, 36)
        text = DIGITS[digit] + text
        if number == 0:
            return text.rjust(size, "0")


def encode_runs(codes: list[int]) -> list[str]:
    """Encode the codes as run tokens: three base-36 digits of code, then the length."""
    tokens: list[str] = []
    start = 0
    for cp in range(1, len(codes) + 1):
        if cp == len(codes) or codes[cp] != codes[start]:
            tokens.append(_base36(codes[start], 3) + _base36(cp - start))
            start = cp
    return tokens


def _wrap(tokens: list[str]) -> list[str]:
    lines: list[str] = []
    current = ""
    for token in tokens:
        if current and len(current) + len(token) + 1 > LINE_WIDTH:
            lines.append(current)
            current = ""
        current += token + " "
    if current:
        lines.append(current)
    return lines


def render(ucd_dir: Path = UCD_DIR) -> dict[str, str]:
    """Return ``{file name: source text}`` for every generated module."""
    lines = _wrap(encode_runs(property_codes(ucd_dir)))
    parts = [lines[i : i + LINES_PER_PART] for i in range(0, len(lines), LINES_PER_PART)]
    note = "# Generated by scripts/gen_ucd_tables.py from data/ucd/. Do not edit.\n"
    files: dict[str, str] = {}
    names: list[str] = []
    for number, chunk in enumerate(parts, start=1):
        name = f"_ucd_part{number}"
        names.append(name)
        body = "".join(f'    "{line}"\n' for line in chunk)
        files[f"{name}.py"] = (
            f'"""Run-length property data, part {number}."""\n\n{note}\nRUNS = (\n{body})\n'
        )
    imports = "".join(f"from .{name} import RUNS as _R{i}\n" for i, name in enumerate(names))
    joined = " + ".join(f"_R{i}" for i in range(len(names)))
    gcb = "".join(f'    "{name}",\n' for name in GCB_NAMES)
    files["_ucd_data.py"] = (
        '"""Index of the generated Unicode property data."""\n\n'
        f"{note}\nfrom __future__ import annotations\n\n{imports}\n"
        f'UNICODE_VERSION = "{unicode_version(ucd_dir)}"\n'
        f"GCB_NAMES = (\n{gcb})\n"
        f"EXT_PICT_BIT = {EXT_PICT_BIT}\nINCB_SHIFT = {INCB_SHIFT}\n"
        f"EMOJI_BIT = {EMOJI_BIT}\nMODIFIER_BIT = {MODIFIER_BIT}\nWIDTH_SHIFT = {WIDTH_SHIFT}\n"
        f"RUNS = {joined}\n"
    )
    return files


def main(argv: list[str]) -> int:
    if not (UCD_DIR / "GraphemeBreakProperty.txt").is_file():
        print("data/ucd/ is not fetched; run python scripts/fetch_upstream.py", file=sys.stderr)
        return 0 if "--check" in argv else 1
    files = render()
    current = {p.name: p.read_text(encoding="utf-8") for p in OUT_DIR.glob("_ucd_*.py")}
    stale = [name for name, text in files.items() if current.get(name) != text]
    stale += sorted(name for name in current if name not in files)
    if "--check" in argv:
        for name in stale:
            print(f"stale: {name}", file=sys.stderr)
        return 1 if stale else 0
    for name, text in files.items():
        (OUT_DIR / name).write_text(text, encoding="utf-8", newline="\n")
    for name in current:
        if name not in files:
            (OUT_DIR / name).unlink()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
