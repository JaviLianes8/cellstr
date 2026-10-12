# cellstr guide

This guide explains how `cellstr` decides how wide text is, where terminals disagree, and
how to pick the policy that matches yours.

## The rules

Width is decided per extended grapheme cluster (UAX #29), the unit a reader sees as one
character. Escape sequences are never part of a cluster: they count as zero cells, and an
escape sequence between two code points ends the cluster before it.

**Single code points** follow Markus Kuhn's reference `wcwidth`
(https://www.cl.cam.ac.uk/~mgk25/ucs/wcwidth.c), applied to Unicode 18.0.0 data:

| Code points | Cells |
| --- | --- |
| U+0000, C0 and C1 controls, DEL | 0 (Kuhn returns -1 for controls; 0 is easier to add up) |
| Nonspacing and enclosing marks (General_Category Mn, Me) | 0 |
| Format characters (Cf), such as ZERO WIDTH SPACE and ZERO WIDTH JOINER | 0 |
| SOFT HYPHEN U+00AD | 1, or `ambiguous` since it is East Asian Ambiguous (it is visible) |
| Hangul medial vowels and final consonants U+1160..U+11FF, U+D7B0..U+D7FF | 0 |
| East_Asian_Width W (wide) and F (fullwidth) | 2 |
| East_Asian_Width A (ambiguous) | `ambiguous`, 1 by default |
| Everything else, including spacing marks (Mc) | 1 |

Unassigned code points follow the defaults in the header of EastAsianWidth.txt: wide in
the CJK ideograph blocks and in Planes 2 and 3, narrow elsewhere.

**Clusters of several code points** add up their code points, which keeps accents at zero
and a Hangul syllable built from jamo at two, except for emoji sequences, which draw as a
single glyph:

| Cluster | Example | Cells |
| --- | --- | --- |
| Emoji + VS16 (U+FE0F, emoji presentation) | ❤️ | 2 |
| Emoji + VS15 (U+FE0E, text presentation) | ⌚︎ | 1 |
| Emoji modifier sequence (skin tone) | 👍🏽 | 2 |
| Emoji ZWJ sequence | 👨‍👩‍👧 | 2 |
| Emoji tag sequence (subdivision flag) | 🏴󠁧󠁢󠁳󠁣󠁴󠁿 | 2 |
| Pair of regional indicators (flag) | 🇯🇵 | 2 |
| Keycap sequence | 1️⃣ | 2 |

```python
from cellstr import char_width, grapheme_width

char_width("❤")  # -> 1
grapheme_width("❤️")  # -> 2
grapheme_width("⌚︎")  # -> 1
grapheme_width("\U0001f44d\U0001f3fd")  # -> 2
grapheme_width("각")  # -> 2
char_width("é"), char_width("́")  # -> (1, 0)
```

## Where terminals disagree

No standard says how many cells a character takes, so terminals make different choices.
These are the cases that matter in practice.

**East Asian Ambiguous characters.** Greek and Cyrillic letters, box drawing, circled
digits and many symbols are one cell in Western use and two in legacy CJK use. Most
terminals let the user choose: xterm has the `cjkWidth` resource, GNOME Terminal and
other VTE terminals have an "Ambiguous-width characters" preference, and iTerm2 can treat
ambiguous characters as double width. Pass `ambiguous=2` (or `--ambiguous 2` on the
command line) when your users run such a setting, typically with a CJK locale.

```python
from cellstr import cell_len, ljust

cell_len("── α")  # -> 4
cell_len("── α", ambiguous=2)  # -> 7
ljust("ж", 3, ambiguous=2)  # -> "ж "
```

**Emoji ZWJ sequences.** A terminal that measures code point by code point, as glibc's
`wcwidth` does, advances the cursor six cells for the family emoji (2 + 0 + 2 + 0 + 2)
and often draws three separate faces. Terminals that segment grapheme clusters draw one
glyph in two cells. `cellstr` measures two. If your
terminal works per code point, measure with the recipe below.

**Variation selectors.** VS16 asks for emoji presentation. Terminals that ignore it keep
a text-default symbol such as U+2764 at one cell and let the colour glyph overflow into
the next cell; `cellstr` measures two. VS15 asks for text presentation: `cellstr` measures
one cell, while terminals that ignore it, and the `wcwidth` package, keep the emoji at two.

**Spacing marks.** Vowel signs in Indic scripts such as U+093F are spacing marks (Mc).
Kuhn's reference gives them one cell (only Mn, Me and Cf are zero there), the `wcwidth`
package gives them zero. `cellstr` gives one, so कि is two cells here.

**Code point by code point recipe.** For a terminal without grapheme support, add up
single code points yourself:

```python
from cellstr import char_width, strip_ansi

text = "\U0001f468‍\U0001f469‍\U0001f467"
sum(char_width(ch) for ch in strip_ansi(text))  # -> 6
```

## Slicing, padding and truncation

- `cell_slice(text, start, stop)` keeps the clusters that sit fully inside the half-open
  column range. A wide cluster cut by either edge is dropped whole, so the result can be
  one cell short; `fit()` pads that cell back. Every escape sequence is kept, so a
  hyperlink or colour that opens before the range still closes after it.
- `ljust`, `rjust` and `center` pad with a one-cell fill character and never shorten text.
- `truncate(..., position=...)` cuts at the end (keep the start), at the start (keep the
  end, useful for log tails) or in the middle (keep both ends, useful for paths).
  `truncate_detailed` returns a `Truncation` with the result, its width, the original
  width and whether anything was cut.
- With `tabsize` set, tabs advance to the next tab stop, counted from the start of the
  line, and become spaces in slices and padded output so the layout does not shift.

```python
from cellstr import cell_slice, fit, truncate

link = "\x1b]8;;https://example.com\x1b\\docs\x1b]8;;\x1b\\"
cell_slice(link, 0, 2)  # -> "\x1b]8;;https://example.com\x1b\\do\x1b]8;;\x1b\\"
log = "12:00:01 worker-7 job finished"
truncate(log, 16, position="start")  # -> "... job finished"
fit("\x1b[1mok\x1b[0m", 4, align="center")  # -> " \x1b[1mok\x1b[0m "
```

## Differences from the wcwidth package

`tests/test_oracle_wcwidth.py` compares every code point with `wcwidth` 0.2.13 (whose
newest tables are Unicode 15.1.0). The package is only a test oracle, never a runtime
dependency. Result: 1,112,200 of 1,114,112 code points agree (99.83 %). Every one of the
1,912 differences has a recorded reason, and the test fails on any new one:

| Reason | Code points |
| --- | --- |
| Assigned after Unicode 15.1 | 1,263 |
| East_Asian_Width changed after 15.1 (for example the trigrams U+2630..U+2637 became W) | 188 |
| General_Category changed after 15.1 (U+1171E became Mc) | 1 |
| Spacing marks (Mc): 1 here, as in Kuhn's reference, 0 in `wcwidth` | 452 |
| SOFT HYPHEN, LINE SEPARATOR, PARAGRAPH SEPARATOR: 1 here (Kuhn), 0 in `wcwidth` | 3 |
| Lone skin tone modifier: 2 here (it is East Asian Wide), 0 in `wcwidth` | 5 |

For strings, `cellstr` and `wcswidth` agree on ZWJ sequences, flags, skin tones, VS16
and keycaps. They differ on VS15 and spacing marks, as described above.

## Unicode data

`data/ucd/` holds the Unicode 18.0.0 files the tables are built from, fetched unmodified
from unicode.org; `data/ucd/SOURCES.txt` records the URLs, the date and SHA-256 sums. To
move to a new Unicode version, replace the files, update `SOURCES.txt`, run
`python scripts/gen_ucd_tables.py` and the test suite. `tests/test_ucd_tables.py` fails if
the committed tables differ from a fresh run of the generator.
