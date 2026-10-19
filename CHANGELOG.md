# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-10-19

First release on PyPI. The public API is stable from this release on: the nineteen names
in `cellstr.__all__`, their signatures, defaults, results and error types follow Semantic
Versioning. Every change against 0.2.1 is listed below.

### Changed

- Every function checks its arguments when it is called, `iter_graphemes` and
  `iter_cells` included (they used to fail only when iterated, or not at all:
  `iter_graphemes(None)` yielded nothing). A wrong type raises `TypeError` naming the
  argument, where 0.2.1 leaked `AttributeError` or an unrelated `TypeError`; a `float` or
  a `bool` is no longer accepted as a width, column, `ambiguous` or `tabsize`
  (`truncate("abcdef", 2.5)` returned `"ab"`).
- Error messages quote at most 40 characters of any argument. A huge `fillchar`,
  `position` or `align` produced a message as long as the argument, and a width past the
  interpreter's integer string limit raised that limit's error instead of cellstr's.
- Results are always exact `str`; a `str` subclass came back as itself when unchanged.
- Widths: LINE SEPARATOR and PARAGRAPH SEPARATOR (U+2028, U+2029) and every
  Default_Ignorable_Code_Point, assigned or reserved, are zero (U+3164 HANGUL FILLER was
  2, U+FFA0 1, reserved ones 1). The Prepended_Concatenation_Mark format characters such
  as U+0600 ARABIC NUMBER SIGN are visible and take their East_Asian_Width (they were 0).
  U+115F HANGUL CHOSEONG FILLER stays 2.
- An East Asian Ambiguous emoji followed by VS15 (text presentation), such as ™︎, takes
  the `ambiguous` width instead of always one cell.
- `truncate`, `truncate_detailed` and `fit` with `tabsize` measure tabs at their stops
  and turn into spaces only the tabs that are kept, so the work no longer grows with the
  tab size.
- `Cell` and `Truncation` report `cellstr` as their module, so pickles name the public
  package. The stray `cellstr.annotations` attribute is gone.
- The `cellstr` command exits with 2 for a bad command line (it was 1), including a
  `--fill` too wide for `--ambiguous 2` and `slice` with STOP before START, and with 1
  when standard input is not UTF-8 (the message gives the byte and its offset), the
  output is too large to build or it cannot be written. Usage messages are cut at 200
  characters.

### Added

- GUIDE sections "Errors" and "Differences from other measurers".
- Cross-checks of every code point against the real output of glibc 2.43 `wcwidth()`
  (`tests/fixtures/glibc-wcwidth.txt`, captured by `scripts/capture_glibc.py`) and
  against the `wcwidth` package 0.9.2, and tests over every line of the official
  emoji-test.txt and emoji-variation-sequences.txt. The manifest pins four more Unicode
  18.0.0 files: DerivedAge.txt, PropList.txt and the two emoji files.
- Python 3.10 to 3.14 classifiers, `Development Status :: 5 - Production/Stable`.

### Removed

- The `wcwidth` 0.2.13 oracle and the pinned Unicode 15.1.0 EastAsianWidth.txt it needed.

## [0.2.1]

### Changed

- The Unicode Character Database files are no longer committed. `data/ucd/MANIFEST.json`
  pins them to Unicode 18.0.0, plus the 15.1.0 EastAsianWidth.txt the oracle test uses
  (URL, size, sha256, licence), and `scripts/fetch_upstream.py`
  fetches them; the generator check and the conformance tests skip until then. The
  generated tables stay in the package and the Unicode licence notice ships in the wheel.
- The sdist ships only the sources, tests, scripts and docs.

## [0.2.0]

### Added

- Grapheme-aware width: emoji ZWJ sequences, skin tone and tag sequences, keycaps and
  regional indicator flags measure as one two-cell glyph; VS16 makes an emoji wide and
  VS15 makes it narrow. New `iter_graphemes()` (UAX #29) and `grapheme_width()`.
- `ambiguous=1 | 2` on every function for East Asian Ambiguous characters.
- `tabsize=` on every function, and `expand_tabs()` that counts display cells.
- `truncate(..., position="end" | "start" | "middle")`, `truncate_detailed()` returning
  a `Truncation`, and `fit()` to truncate or pad to an exact width.
- `iter_cells()` yielding typed `Cell` records (text, width, column, escape flag).
- Recognition of DCS, SOS, PM and APC strings, charset designations and the remaining
  single-byte escapes, alongside CSI and OSC (BEL or ST terminated).
- The `cellstr` command: `measure`, `truncate`, `pad`, `fit` and `slice` over stdin lines.
- Width, grapheme and emoji tables generated from a committed Unicode 18.0.0 UCD snapshot
  by `scripts/gen_ucd_tables.py`, with the Unicode License in `LICENSE-UNICODE`.

### Changed

- `cell_len`, `cell_slice`, `truncate` and the padding functions measure grapheme
  clusters, so emoji sequences change width: the family emoji was 6 cells and is now 2,
  a flag was 2 and stays 2, an emoji with VS15 is now 1.
- `truncate` rejects a suffix that contains a tab or a line break.
- Width tables move from a hand-vendored Unicode 15.1 extract to generated Unicode
  18.0.0 tables. Spacing marks (Mc) are one cell, as in Kuhn's wcwidth and glibc.
- `cell_slice` never splits a grapheme cluster, so accents stay on their letter.
- `ljust`, `rjust` and `center` accept any one-cell grapheme cluster as the fill.

## [0.1.0]

- First release: `cell_len`, `char_width`, `cell_slice`, `ljust`, `rjust`,
  `center`, `truncate` and `strip_ansi`, with a vendored Unicode width table and
  full type hints.
