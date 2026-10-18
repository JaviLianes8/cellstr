# cellstr 1.0.0 certification report

The 1.0.0 certification bar (19 items) applied to cellstr. PyPI has no `cellstr` project
(https://pypi.org/pypi/cellstr/json answered 404 on 2026-10-18), so 1.0.0 is the first
release there and there is no published version to upgrade from. Every change against 0.2.1,
the `main` branch at 54ff864, is still listed in the CHANGELOG.

Progress:
- [x] Branch `release/1.0.0` created from `main` (54ff864, 0.2.1)
- [x] Baseline gates on 0.2.1
- [ ] API review and 1.0.0 changes (item 1)
- [ ] Errors, typing, docstrings and doctests (items 2 to 5)
- [ ] Ground truth: Unicode files fetched live, glibc output, wcwidth 0.9.2, official test files (item 7)
- [ ] Contract, fuzz and author mutation round (items 6, 9, 18)
- [ ] Docs: README, GUIDE, CHANGELOG (items 11, 12)
- [ ] Packaging, e2e and every Python (items 8, 10, 13, 14)
- [ ] Gates (item 15)
- [ ] PR and trace guard CLEAN
- [ ] Five QA lenses (item 19)
- [ ] Independent review (item 16)

## Baseline on 0.2.1 (before any change)

Fresh clone of `release/1.0.0` at 54ff864 with the seven Unicode files of the manifest
re-fetched on 2026-10-18 (every size and SHA-256 matched): `ruff format --check .`,
`ruff check .`, `mypy --strict src`, `mypy --strict src tests scripts` and
`python scripts/gen_ucd_tables.py --check` exit 0; `pytest` 2,537 passed in 48 s.

Defects found in 0.2.1 by reading and then reproducing:

- Arguments of the wrong type leaked internal errors: `cell_len(["a"])` raised
  `AttributeError`, `truncate("abc", 2, 5)` and `cell_len(None)` a `TypeError` about
  iteration, `ljust("a", "5")` a `TypeError` about subtraction; `list(iter_graphemes(None))`
  returned `[]`.
- Floats were accepted as widths and columns: `truncate("abcdef", 2.5)` returned `"ab"`,
  `cell_slice("abcdef", 1.5, 3.5)` returned `"c"`.
- Error messages quoted the whole argument: a 1,000,000 character `fillchar` or `position`
  produced a 1,000,050 character message, and `truncate("x", -10**5000)` raised the
  interpreter's integer-to-string limit error instead of cellstr's own message.
- `iter_cells("x", ambiguous=5)` raised only when iterated.
- `cellstr.annotations` existed as a stray public attribute, and pickles of `Cell` and
  `Truncation` named the private module `cellstr._cells` / `cellstr._truncate`.
- A `str` subclass came back as itself when the text was unchanged
  (`type(truncate(S("abc"), 10))` was `S`).
- Widths that both independent references disagree with (see Ground truth): the
  Prepended_Concatenation_Mark format characters such as U+0600 ARABIC NUMBER SIGN measured
  0 although Unicode calls them visible, U+3164 HANGUL FILLER 2, U+FFA0 1, U+2028 and U+2029
  1, and reserved Default_Ignorable_Code_Point code points 1.
- The README linked LICENSE, LICENSE-UNICODE and GUIDE.md relatively (broken on PyPI) and
  its comparison with the `wcwidth` package was out of date: wcwidth 0.9.2 (2026-10-05) has
  `width()` with escape sequences, `ljust`, `rjust`, `center`, `clip`, `wrap`,
  `iter_graphemes`, an ambiguous-width option and Unicode 18.0.0 tables.
- `scripts/gen_ucd_tables.py` had 202 lines; `scripts/release.ps1` refused any upload once
  the name existed on PyPI, and neither script checked the exit code of the tools it ran.
