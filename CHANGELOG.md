# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
