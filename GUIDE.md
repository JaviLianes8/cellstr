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
| LINE SEPARATOR U+2028 and PARAGRAPH SEPARATOR U+2029 (Zl, Zp) | 0 |
| Default_Ignorable_Code_Point, assigned or reserved, such as U+3164 HANGUL FILLER | 0 |
| Hangul medial vowels and final consonants U+1160..U+11FF, U+D7B0..U+D7FF | 0 |
| SOFT HYPHEN U+00AD | 1, or `ambiguous` since it is East Asian Ambiguous (it is visible) |
| Prepended_Concatenation_Mark, such as U+0600 ARABIC NUMBER SIGN (Cf, but visible) | by East_Asian_Width, like any other character |
| U+115F HANGUL CHOSEONG FILLER (default ignorable, but a leading jamo) | 2 |
| East_Asian_Width W (wide) and F (fullwidth) | 2 |
| East_Asian_Width A (ambiguous) | `ambiguous`, 1 by default |
| Everything else, including spacing marks (Mc) | 1 |

The rows that refine Kuhn's 2007 table follow both references below: assigned default
ignorables are zero, and the prepended concatenation marks and U+115F keep their width,
in glibc and in the `wcwidth` package alike; the separators and the reserved default
ignorables are zero in `wcwidth` and not printable (-1) in glibc. See "Differences from
other measurers".

Unassigned code points follow the defaults in the header of EastAsianWidth.txt: wide in
the CJK ideograph blocks and in Planes 2 and 3, narrow elsewhere.

**Clusters of several code points** add up their code points, which keeps accents at zero
and a Hangul syllable built from jamo at two, except for emoji sequences, which draw as a
single glyph:

| Cluster | Example | Cells |
| --- | --- | --- |
| Emoji + VS16 (U+FE0F, emoji presentation); a cluster that a lone skin tone modifier starts adds up instead (see "Variation selectors") | ❤️ | 2 |
| Emoji + VS15 (U+FE0E, text presentation), for the 371 sequences emoji-variation-sequences.txt lists | ⌚︎ | 1, or `ambiguous` for an East Asian Ambiguous emoji such as ™︎ |
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
grapheme_width("\U0001f1ef"), grapheme_width("\U0001f1ef\ufe0f")  # -> (1, 2)
grapheme_width("\U0001f3fe\ufe0f"), grapheme_width("\U0001f3fe\ufe0f\u1b3b")  # -> (2, 3)
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
the next cell; `cellstr` measures two. VS15 asks for text presentation, and Unicode lists
the emoji that have one (emoji-variation-sequences.txt; UTS #51 ED-8a). For those,
`cellstr` measures one cell (the `ambiguous` width for an East Asian Ambiguous emoji such
as ™), while terminals that ignore VS15 keep a wide emoji at two. After any other emoji,
such as U+1F600 😀, VS15 is not sanctioned and changes nothing, so 😀︎ stays two cells.
VS16 makes every emoji two cells, sanctioned or not, so a lone regional indicator, one
cell on its own, is two cells with VS16. The `wcwidth` package 0.9.2 gives the same width
for every emoji followed by VS15 or VS16, except a lone regional indicator (see below).
A skin tone modifier on its own (not after an emoji it modifies) is a two-cell symbol,
not an emoji sequence: a cluster it starts adds up its code points like any other, so
🏾 with VS16 is two cells and with a spacing mark after that three (two in `wcwidth`).

**Spacing marks.** Vowel signs in Indic scripts such as U+093F are spacing marks (Mc).
Kuhn's reference and glibc give them one cell (only Mn, Me and Cf are zero there); the
`wcwidth` package gives a lone one zero and caps a cluster holding one at two cells.
`cellstr` gives one, so क्षि (a conjunct with a vowel sign) is three cells here and two
in `wcwidth`.

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
  short by less than the width of that cluster: one cell for a CJK character, two for a
  three-cell conjunct such as क्षि. `fit()` pads the missing cells back. Every escape
  sequence is kept, so a hyperlink or colour that opens before the range still closes
  after it.
- `ljust`, `rjust` and `center` pad with a one-cell fill character and never shorten text.
- `truncate(..., position=...)` cuts at the end (keep the start), at the start (keep the
  end, useful for log tails) or in the middle (keep both ends, useful for paths). A
  middle cut gives the odd cell to the left part, and when a wide cluster leaves a cell
  of one part unused, the other part takes it. `truncate_detailed` returns a
  `Truncation` with the result, its width, the original width and whether anything was
  cut.
- With `tabsize` set, tabs advance to the next tab stop, counted from the start of the
  line, and become spaces in slices and padded output so the layout does not shift.
- The result of slicing, truncation, padding or `expand_tabs` never holds an escape
  sequence that the text (and the suffix) did not hold, and its width is the sum of the
  pieces it keeps. A stray ESC, one that starts no complete sequence (such as the ESC of
  an unterminated `ESC ]` or `ESC [`), is a zero-width control; it is dropped when the
  next character in the result is printable ASCII, which could otherwise extend it into
  a new sequence. A cut, a tab expansion or a suffix can also put a cluster after a new
  neighbour that it joins. It stays only when the joined cluster measures the sum of the
  two: a combining mark that followed a tab ends up on a space or on the letter kept
  before the cut, at the same width, and two lone regional indicators that a middle cut
  brings together become a flag, two cells as before. Any other one is dropped, wider or
  narrower: VS16 or a tag character after U+2764, a skin tone modifier after an emoji, an
  emoji after a kept ZWJ. This holds for the start of a suffix too, so
  `truncate("👍abc", 4, "🏽")` is the thumbs up alone, two
  cells and no suffix; `fit()` pads the missing cells back.
- `strip_ansi` removes every escape sequence and every stray ESC, and nothing else. An
  escape sequence or a stray ESC ends the cluster before it, so removing one can join the
  clusters on either side into one cluster, and the stripped text may then measure
  differently: `cell_len("\u2764\x1b[0m\ufe0f")` is 1 but the stripped text, U+2764
  followed by VS16, is a two-cell emoji.
- Only the 7-bit escape forms are recognised. The 8-bit C1 introducers (U+009B CSI,
  U+009D OSC, U+0090 DCS and the rest) are zero-width controls, and the text after them
  is measured and kept as text.

```python
from cellstr import cell_len, cell_slice, fit, strip_ansi, truncate

link = "\x1b]8;;https://example.com\x1b\\docs\x1b]8;;\x1b\\"
cell_slice(link, 0, 2)  # -> "\x1b]8;;https://example.com\x1b\\do\x1b]8;;\x1b\\"
log = "12:00:01 worker-7 job finished"
truncate(log, 16, position="start")  # -> "... job finished"
fit("\x1b[1mok\x1b[0m", 4, align="center")  # -> " \x1b[1mok\x1b[0m "
cell_len("\u2764\x1b[0m\ufe0f"), cell_len(strip_ansi("\u2764\x1b[0m\ufe0f"))  # -> (1, 2)
```

## Errors

Every function checks its arguments when it is called, the generators `iter_graphemes`
and `iter_cells` included, and raises these built-in exceptions for a bad argument:

- `TypeError` for an argument of the wrong type: text that is not a `str`, a width,
  column, `ambiguous` or `tabsize` that is not an integer (`bool` and `float` are
  refused; any object with `__index__` is accepted).
- `ValueError` for a value out of range: a negative width or column for `cell_slice`,
  `truncate` and `fit`, `ambiguous` other than 1 or 2, `tabsize` below 1, a `position`
  or `align` outside the documented choices, a `fillchar` that is not one one-cell
  character, a suffix with a tab or a line break, or a `char_width` or `grapheme_width`
  argument that is not exactly one code point or one cluster.

A valid width or tab size so large that the result cannot be built raises
`OverflowError` or `MemoryError`, as `str.ljust` and `str.expandtabs` do: for example
`ljust("a", 10**20)` or `expand_tabs("\t", 10**20)`.

Padding to a width at or below the text's width adds nothing, as `str.ljust` does: the
text comes back unchanged, except that with `tabsize` its tabs are expanded and that a
stray ESC is dropped as described above. A slice whose stop is before its start holds no
printable text; it keeps the escape sequences. Messages name the argument and quote at
most 40 characters of its value, so a huge or hostile argument never produces a huge
message. A `str` subclass is read as a plain `str` and every result is an exact `str`.

```python
from cellstr import cell_len, truncate

try:
    truncate("abc", -1)
except ValueError as exc:
    message = str(exc)
message  # -> "width must not be negative, not -1"
try:
    cell_len(b"abc")
except TypeError as exc:
    message = str(exc)
message  # -> "text must be a str, not bytes"
```

The `cellstr` command exits with 0 on success, 2 for a bad command line (as `argparse`
does) and 1 when standard input is not UTF-8 or the output is too large to build or
cannot be written, with a one-line message on standard error.

## Differences from other measurers

Two independent measurers are run over every code point by the test suite; neither is a
runtime dependency, and the tests fail on any difference without a recorded reason.

**glibc `wcwidth()`** (`tests/test_oracle_glibc.py`). `tests/fixtures/glibc-wcwidth.txt`
is the real output of glibc 2.43 (Ubuntu 26.04 under WSL 2, locale C.UTF-8) for all
1,114,112 code points, captured by `scripts/capture_glibc.py` on 2026-10-18. glibc 2.43
knows Unicode 17.0, so the 13,007 code points new in 18.0 are left out. Of the rest:

| Result | Code points |
| --- | --- |
| Same width | 297,241 |
| Unassigned, noncharacter or surrogate: -1 (not printable) in glibc | 803,771 |
| Controls: 0 here, -1 in glibc | 64 |
| LINE and PARAGRAPH SEPARATOR: 0 here, -1 in glibc | 2 |
| Format characters (Cf): 0 here, 1 in glibc | 19 |
| East Asian Ambiguous: 1 here (the default policy), 2 in glibc | 8 |

**The `wcwidth` package 0.9.2** (`tests/test_oracle_wcwidth.py`), released 2026-10-05
on the same Unicode 18.0.0 data. With either ambiguous policy, 1,113,545 code points
get the same value from `wcwidth.wcwidth()`. The 64 controls are 0 here and -1 (not
printable) there, and the other 503 are the 477 spacing marks (Mc, see above) and the 26
regional indicators, which are one cell alone here (East_Asian_Width N) and two in
`wcwidth`.
Grapheme clusters are identical on 20,000 random strings, and cluster widths agree on
more than 50,000 random clusters free of those two cases. In emoji-test.txt the only
other difference is an emoji sequence whose first code point is a one-cell emoji not
followed by VS16, such as 🖐🏻 or an unqualified ZWJ sequence: two cells here, because
it draws as one emoji glyph, one cell in `wcwidth` (99 of the 5,244 lines).

Of every assigned code point known to Unicode 17.0, comparing the values exactly as each
returns them (so -1 is not read as 0): 296,744 get the same width from `cellstr`, glibc
and `wcwidth`; 497 match glibc only (471 spacing marks, 26 regional indicators); 29 match
`wcwidth` only (19 format characters, 8 East Asian Ambiguous, U+2028 and U+2029); and the
64 controls match neither, being 0 here and -1 in both.

## Unicode data

The tables are built from the Unicode 18.0.0 data files, which are not committed:
`data/ucd/MANIFEST.json` pins their URLs, sizes and SHA-256 sums, and
`python scripts/fetch_upstream.py` fetches them into `data/ucd/` (the tests that read them
skip until then). To move to a new Unicode version, update the manifest, fetch, run
`python scripts/gen_ucd_tables.py` and the test suite. `tests/test_ucd_tables.py` fails if
the committed tables differ from a fresh run of the generator.
