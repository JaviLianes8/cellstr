# cellstr 1.0.0 certification report

The 1.0.0 certification bar (19 items) applied to cellstr. PyPI has no `cellstr` project
(https://pypi.org/pypi/cellstr/json answered 404 on 2026-10-18 and again on 2026-10-19), so 1.0.0 is the first
release there and there is no published version to upgrade from. Every change against 0.2.1,
the `main` branch at 54ff864, is still listed in the CHANGELOG.

Progress:
- [x] Branch `release/1.0.0` created from `main` (54ff864, 0.2.1)
- [x] Baseline gates on 0.2.1
- [x] API review and 1.0.0 changes (item 1)
- [x] Errors, typing, docstrings and doctests (items 2 to 5)
- [x] Ground truth: Unicode files fetched live, glibc output, wcwidth 0.9.2, official test files (item 7)
- [x] Contract, fuzz and author mutation round (items 6, 9, 18)
- [x] Docs: README, GUIDE, CHANGELOG (items 11, 12)
- [x] Packaging, e2e and every Python (items 8, 10, 13, 14)
- [x] Gates (item 15)
- [x] PR #4 and trace guard CLEAN
- [x] QA round 1: five lenses run, every finding fixed (see QA lenses)
- [x] QA round 2: round 1 confirmed fixed, eleven new findings fixed, none disputed (8366709)
- [x] QA round 3: round 2 confirmed fixed, thirteen new findings fixed, none disputed (c0d8725)
- [x] QA round 4: round 3 confirmed fixed, five new findings fixed, none disputed (2dc700f)
- [ ] Five QA lenses PASS on re-verification (item 19)
- [ ] Independent review (item 16)

## Scorecard

| # | Item | Result |
| --- | --- | --- |
| 1 | Public API reviewed for stability | PASS: the 19 names of 0.2.1 kept with their signatures and defaults, pinned by `tests/test_contract.py`; every behaviour change in the CHANGELOG |
| 2 | `__all__` exact, no private imports in docs | PASS: the package namespace holds exactly `__all__` (tested) |
| 3 | Docstrings with runnable examples, doctests | PASS: every function and class has a doctest; the constants and type aliases are shown in the package docstring, which runs too; README and GUIDE outputs run as tests |
| 4 | Typed end to end | PASS: `mypy --strict src tests scripts`, `py.typed` shipped, no `Any` in the public API |
| 5 | Typed, documented, bounded errors | PASS: `TypeError` and `ValueError` raised at the call, GUIDE "Errors", messages quote at most 40 characters |
| 6 | Contract tests of every public name | PASS: `test_contract.py`, `test_errors_contract.py`, `test_width_contract.py` |
| 7 | Real ground truth | PASS: ten Unicode 18.0.0 files fetched live, glibc 2.43 output captured twice, wcwidth 0.9.2 run live |
| 8 | Real e2e from the wheel | PASS: wheel built, installed in fresh venvs, CLI and `-I -m cellstr` from an empty folder; no PyPI release to upgrade from |
| 9 | Seeded fuzz, no crash, hang or blowup | PASS: `test_fuzz.py` (seeded), `test_scaling.py` (13 shapes by 7 operations, linear) |
| 10 | Supported Pythons | PASS: CPython 3.10.19, 3.11.5, 3.12.12, 3.13.2, 3.14.2, 3.14.2 free-threaded |
| 11 | README and `twine check` | PASS: `twine check --strict` on wheel and sdist, absolute links, badge, honest comparison |
| 12 | Dated CHANGELOG section | PASS: 1.0.0, 2026-10-19 |
| 13 | pyproject 1.0.0, Production/Stable | PASS |
| 14 | sdist and wheel contents | PASS |
| 15 | Gates each exit 0 | PASS: see Gates |
| 16 | Independent reviewer | pending (next stage) |
| 17 | PR and trace guard | PR #4 "cellstr 1.0.0" from `release/1.0.0`, trace guard CLEAN; merge and publish left to the maintainer |
| 18 | Contracts bite (mutations) | PASS: author round of 30 mutants, 29 killed, 1 equivalent |
| 19 | Five independent QA lenses | round 1 on 8380f22: 25 findings, all fixed; round 2 on af60316: round 1 confirmed, 11 new findings, all fixed in 8366709, none disputed; round 3 on 0ca1732: 13 new findings, all fixed in c0d8725; round 4 on e057b96: 5 new findings, all fixed in 2dc700f, none disputed; re-verification pending |

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

## API review (item 1)

Kept: the nineteen public names of 0.2.1 (`cell_len`, `char_width`, `grapheme_width`,
`iter_graphemes`, `iter_cells`, `Cell`, `cell_slice`, `ljust`, `rjust`, `center`, `fit`,
`truncate`, `truncate_detailed`, `Truncation`, `expand_tabs`, `strip_ansi`,
`UNICODE_VERSION`, `Align`, `Position`), their positional parameters (the 0.1.0 ones are
pinned), keyword-only options with defaults, and return types. Changed, all in the
CHANGELOG: arguments checked at the call with `TypeError` or `ValueError` and short
messages; `float` and `bool` refused as integers; exact `str` results; the zero-width
refinements (separators, default ignorables) and the visible prepended concatenation
marks; VS15 on an ambiguous emoji follows the `ambiguous` policy; tab-aware truncation in
time proportional to the text; `Cell` and `Truncation` under the `cellstr` module; CLI
exit status 2 for usage errors. Internal: the CLI parser moved to `_cli_parser.py` to keep
every file under 200 lines; `scripts/check.ps1` and `scripts/release.ps1` check every
tool's exit status.

## Ground truth (item 7)

- Unicode 18.0.0 data, ten files listed with URL, size, sha256 and licence in
  `data/ucd/MANIFEST.json`: DerivedAge, DerivedCoreProperties, DerivedGeneralCategory,
  EastAsianWidth, GraphemeBreakProperty, GraphemeBreakTest, PropList and emoji-data under
  https://www.unicode.org/Public/18.0.0/ucd/, emoji-test.txt at
  https://www.unicode.org/Public/18.0.0/emoji/emoji-test.txt and
  emoji-variation-sequences.txt. Fetched on 2026-10-18 by `scripts/fetch_upstream.py`
  and fetched again on 2026-10-19: every size and sha256 matched. Not committed, not
  shipped. Used by the table generator check, the whole GraphemeBreakTest.txt
  (`test_grapheme_conformance.py`), every line of emoji-test.txt (5,244 sequences, each
  one cluster of the documented width) and of emoji-variation-sequences.txt (742
  sequences, both styles, both ambiguous policies) in `test_emoji_files.py`, and the
  property lookups of the oracle tests.
- glibc `wcwidth()`, real program output: `scripts/capture_glibc.py` run under Ubuntu
  26.04 LTS in WSL 2 (glibc 2.43-2ubuntu2.4, Python 3.14.4, locale C.UTF-8) on 2026-10-18
  wrote `tests/fixtures/glibc-wcwidth.txt` (every code point, run-length encoded; how it
  was made, its size and sha256 in `tests/fixtures/MANIFEST.json`). Run again on
  2026-10-19: byte for byte the same file (sha256 2c21aae4...dce6). `test_oracle_glibc.py`
  explains every one of the 1,114,112 results; the counts are in GUIDE.md.
- The `wcwidth` package 0.9.2 (released 2026-10-05, same Unicode 18.0.0 data), an
  independent implementation run live by `test_oracle_wcwidth.py`: every code point under
  both ambiguous policies, grapheme clusters on 20,000 seeded random strings, cluster
  widths on more than 50,000 random clusters and every line of emoji-test.txt; each
  difference has a documented reason and the counts are pinned.
- Three-way: of every assigned code point known to Unicode 17.0, with each value compared
  as returned (-1 is not read as 0), 296,744 get the same width from `cellstr`, glibc and
  `wcwidth`; 497 match glibc only, 29 match `wcwidth` only, and the 64 controls match
  neither (0 here, -1 in both). Before QA round 1 this line read -1 as 0 (296,810, 497
  and 27).
- Kuhn's reference `wcwidth.c` (https://www.cl.cam.ac.uk/~mgk25/ucs/wcwidth.c, read on
  2026-10-18) for the single code point rules the GUIDE states. The hand-written width
  vectors in `test_contract.py` are labelled with the UCD property each comes from.

## Contracts, fuzz and hostile input (items 6, 9)

`test_contract.py` pins `__all__`, the legacy signatures, the version in pyproject and
CHANGELOG, `py.typed`, 30 UCD width vectors under both policies and the slicing,
truncation and fit invariants. `test_errors_contract.py` pins every function's
`TypeError` and `ValueError` with its message, short messages for 1,000,000 character and
16,000-bit arguments, `__index__` integers accepted and `bool` refused, exact `str`
results for a `str` subclass, pickles under `cellstr`, and the package namespace.
`test_fuzz.py` runs seeded hostile text through slicing, truncation, fitting, measuring
and tab expansion. `test_scaling.py` times thirteen hostile shapes (n combining marks on
one letter, a ZWJ chain, regional indicator runs, an Indic linker chain, Hangul jamo
runs, escapes, unterminated OSC and DCS strings, lone escapes, tabs and line breaks)
through seven operations at 2,000 and 16,000 repetitions, the fastest of three runs with
the garbage collector paused: a linear cost grows about 8 times, a quadratic one 64, and
the test fails above 20. On this PC the worst growth was 11.5 times, for calls near the
2 ms floor; unterminated DCS strings through `cell_len` grew 4.0, 4.1 and 4.2 times for
each fourfold step from 2,000 to 128,000.

## Author mutation round (item 18)

30 mutants over every module, each applied alone to a copy of a fresh clone of the pushed
branch on another machine (Elena's PC), the full suite except the wheel build run with
`-x` and a 300 s per-test limit, the Unicode files and wcwidth 0.9.2 present. First run
at 4c61489 (mutants 1 to 15), second at 8111cf7 (16 to 30, and 5, 6 and 12 again).
Mutants 5, 6 and 12 survived the first run; the contracts in `test_edges.py` were added
and all three are killed at 8111cf7. Mutant 16 is equivalent: `splice` is called only when
the text is wider than the limit, so some cluster always ends past the head and the
suffix is always inserted inside the loop; the final `if pending` is a guard that cannot
fire.

| # | Module | Mutation | Result | First test that failed |
| --- | --- | --- | --- | --- |
| 1 | `_width.py` | ambiguous policy ignored | killed | `test_cli.py::test_measure_max_and_policies` |
| 2 | `_width.py` | VS16 gives one cell | killed | `test_docs_examples.py::test_documented_results_are_true[GUIDE.md]` |
| 3 | `_width.py` | VS15 ignores the ambiguous policy | killed | `test_emoji_files.py::test_variation_sequences_choose_the_presentation[2]` |
| 4 | `_width.py` | a flag of two regional indicators is one cell | killed | `test_contract.py::test_measuring_ignores_escapes_and_counts_clusters` |
| 5 | `_width.py` | tag sequences not recognised | killed (after the new contract) | `test_edges.py::test_a_tag_sequence_widens_any_emoji_base` |
| 6 | `_width.py` | DEL counted as printable ASCII | killed (after the new contract) | `test_edges.py::test_ascii_controls_and_del_are_zero_width` |
| 7 | `_width.py` | an empty char raises the wrong error | killed | `test_errors_contract.py::test_a_wrong_value_is_a_value_error_named_in_the_message` |
| 8 | `_graphemes.py` | GB3: CR LF split | killed | `test_grapheme_conformance.py::test_official_case[line29]` |
| 9 | `_graphemes.py` | GB12/13: regional indicator pairing off by one | killed | `test_docs_examples.py::test_documented_results_are_true[README.md]` |
| 10 | `_graphemes.py` | GB9c: Indic conjunct rule inverted | killed | `test_grapheme_conformance.py::test_official_case[line60]` |
| 11 | `_cells.py` | tab stops counted from the start of the text | killed | `test_ops.py::test_expand_tabs_counts_display_cells` |
| 12 | `_cells.py` | CR does not start a new line for tab stops | killed (after the new contract) | `test_edges.py::test_a_carriage_return_starts_a_new_line_for_tab_stops` |
| 13 | `_ops.py` | slice drops a wide cluster ending at the limit (off by one) | killed | `test_cli.py::test_truncate_keeps_line_endings_and_positions` |
| 14 | `_ops.py` | center puts the odd cell left | killed | `test_cli.py::test_pad_and_fit_align_by_cells` |
| 15 | `_ops.py` | fill width not checked | killed | `test_cli.py::test_usage_errors_go_to_stderr_with_status_two` |
| 16 | `_ops.py` | middle cut: final suffix guard removed | equivalent (see above) | none |
| 17 | `_ops.py` | tab spaces right of a middle cut dropped | killed | `test_truncate.py::test_truncate_turns_tabs_into_the_spaces_kept_at_each_cut` |
| 18 | `_truncate.py` | middle cut head rounds down | killed | `test_cli.py::test_truncate_keeps_line_endings_and_positions` |
| 19 | `_truncate.py` | text exactly at the width is truncated | killed | `test_fuzz.py::test_truncation_and_fit_respect_the_width[47]` |
| 20 | `_truncate.py` | hard cut loses a cell | killed | `test_contract.py::test_truncation_never_exceeds_the_width` |
| 21 | `_truncate.py` | start cut keeps one cell too few | killed | `test_cli.py::test_truncate_keeps_line_endings_and_positions` |
| 22 | `_truncate.py` | Truncation reports the limit as the original width | killed | `test_doctests.py::test_docstring_examples[cellstr._truncate]` |
| 23 | `_args.py` | negative width accepted | killed | `test_docs_examples.py::test_documented_results_are_true[GUIDE.md]` |
| 24 | `_args.py` | bool accepted as an int | killed | `test_edges.py::test_ambiguous_must_be_an_int[True]` |
| 25 | `_args.py` | long values quoted in full | killed | `test_errors_contract.py::test_messages_stay_short_for_huge_arguments` |
| 26 | `_args.py` | a str subclass returned as itself | killed | `test_errors_contract.py::test_results_are_exact_str_even_for_a_str_subclass` |
| 27 | `_ansi.py` | OSC ended by ST not recognised | killed | `test_ansi.py::test_every_family_is_removed_and_measured_as_nothing` |
| 28 | `_cli_lines.py` | the CLI loses the CR of CR LF lines | killed | `test_cli.py::test_truncate_keeps_line_endings_and_positions` |
| 29 | `_cli_lines.py` | `measure --max` prints the smallest width | killed | `test_cli.py::test_measure_max_and_policies` |
| 30 | `_cli.py` | unreadable input exits 2 | killed | `test_cli.py::test_unreadable_input_is_status_one` |

## Packaging, e2e and Pythons (items 8, 10, 13, 14)

- PyPI has no `cellstr` (404 on 2026-10-19), so there is no release to upgrade from.
- On this PC at bdee1f0, from a fresh clone of the pushed branch: `python -m build` made
  `cellstr-1.0.0-py3-none-any.whl` and `cellstr-1.0.0.tar.gz`; `twine check --strict`
  passed both. The wheel holds the 16 modules of `cellstr/`, `py.typed`, the entry point,
  and `licenses/LICENSE` and `licenses/LICENSE-UNICODE` (the Unicode License covers the
  generated tables); no tests, data or scripts. The sdist holds `src`, `tests` (with the
  glibc fixture, which is program output written by `scripts/capture_glibc.py`),
  `scripts/gen_ucd_tables.py`, `fetch_upstream.py` and `capture_glibc.py`, the Unicode
  manifest only (no Unicode text), README, GUIDE, CHANGELOG, CONTRIBUTING, both licences,
  `pyproject.toml` and `.gitignore`; no scratch files. Metadata: version 1.0.0,
  `Development Status :: 5 - Production/Stable`, Python 3.10 to 3.14 classifiers,
  `License-Expression: MIT`, Homepage, Source, Issues and Changelog URLs, keywords, no
  runtime dependencies.
- Every interpreter on this PC from `requires-python` up: CPython 3.10.19, 3.11.5,
  3.12.12, 3.13.2, 3.14.2 and 3.14.2 free-threaded. For each, a fresh venv with only the
  built wheel plus pytest, pytest-timeout and wcwidth 0.9.2, and the sdist's own suite run
  with its `src` folder removed and the fetched Unicode files present (the tables test
  then checks the installed modules): 2,617 passed and 1 skipped each (the wheel build,
  which needs the source tree and runs in the gates). Then, from an empty folder, the
  installed `cellstr.exe` (`measure`, `truncate 16 --position middle`,
  `pad 8 --align right`, `slice 1 3` on coloured text, `--version`, a usage error exiting
  2 and invalid UTF-8 exiting 1) and `python -I -m cellstr measure --max`, all with the
  expected output. CPython 3.8 and 3.9 are installed here but below `requires-python`.
  The commits after bdee1f0 add `tests/test_scaling.py` and touch only the scripts, the
  CHANGELOG and this report; the final gates below include the scaling test.
- The gates run builds the wheel from the tree with pip, installs it into a throwaway venv
  and drives the installed script by subprocess (`tests/test_e2e_wheel.py`).

## Gates (item 15)

Final run at 8ee1e4a on Elena's PC (CPython 3.14), from a fresh clone of the pushed branch
with the ten Unicode files present and wcwidth 0.9.2 installed: `ruff format --check .`,
`ruff check .`, `mypy --strict src`, `mypy --strict src tests scripts` and
`python scripts/gen_ucd_tables.py --check` exit 0; `pytest` 2,709 passed, none skipped,
in 30 s (the wheel build and the glibc and wcwidth oracles included). The commit after it
changes only this report. An earlier run at 199cc05 on the laptop failed one timing case
(growth 9.1 times against a bound of 9 for four times the input); the scaling test was
then widened to eight times the input with the collector paused (8ee1e4a).

## QA lenses (item 19)

### Round 1, on 8380f22

Five independent lenses: (a) API and docs, (b) correctness and ground truth, (c)
adversarial and robustness, (d) packaging and real e2e, (e) contract strength with its
own mutation round. Each behaviour finding got a test that fails on 8380f22 (checked by
running the new tests against the 8380f22 sources: 15 failed) and then a fix; each
surviving mutant of lens e got a test, and each of the eight mutants was applied again
and is now killed. Every behaviour change is in the CHANGELOG.

| Lens | Id | Finding | Fix |
| --- | --- | --- | --- |
| a | A1 | GUIDE "Errors": a reversed slice is not empty (escapes kept); padding with `tabsize` expands tabs | GUIDE reworded |
| a | A2 | README: `ambiguous=2` "to any function", but `strip_ansi` and `iter_graphemes` have none | README names the exceptions |
| a | A3 | Three-way agreement counts read glibc's -1 as 0 | exact counts in GUIDE, `test_oracle_glibc.py` compares as returned |
| a | A4 | CHANGELOG versions before 1.0.0 had no dates | dates from the git history |
| a | A5 | CONTRIBUTING claimed tests never touch disk or network | accurate sentence |
| b | F1 | VS15 narrowed every emoji, not only the listed text presentation sequences | VS15 narrows only the 371 sequences of emoji-variation-sequences.txt (a generated table bit); contract over every Emoji base, both policies, and against `wcwidth` 0.9.2 for VS15 and VS16 |
| b | F2 | Middle cut could be two cells short with ordinary wide characters | the cell one part cannot use goes to the other; `test_truncate.py` |
| b | F3 | "One cell short" false for clusters wider than two cells | GUIDE and docstrings: short by less than the width of the cluster at the cut; pinned with a three-cell conjunct |
| b | F4 | 8-bit C1 introducers measured as text | documented scope (README, GUIDE, `strip_ansi` docstring): only the 7-bit forms; pinned in `test_ansi.py` |
| b | F5 | `wcwidth` and three-way counts read -1 as 0 | exact counts (1,113,545 plus 64 controls; 296,744 / 497 / 29 / 64) in GUIDE and tests |
| c | F1 | `strip_ansi` could leave a live sequence (not idempotent) | stray ESC removed too; result holds no ESC; fuzz checks idempotence |
| c | F2 | Cuts glued a stray ESC to new text, creating escapes | a stray ESC is dropped when the next character in the result is printable ASCII or the result ends; unterminated `ESC P` / `ESC X` read as stray like `ESC ]`; `test_stray_escapes.py` with a seeded fuzz that the escapes out equal the escapes in (plus the suffix's) |
| c | F3 | Tab expansion turned `ESC [` + tab into a CSI | same rule in `expand_tabs` and padding; fuzz checks `cell_len(expand_tabs(t, n)) == cell_len(t, tabsize=n)` |
| c | F4 | A cut could fuse clusters into a wider one | an orphan zero-width cluster that would widen the cluster before it is dropped; fuzz checks `fit` is exactly the width and `truncate_detailed` within it |
| c | F5 | `OverflowError` and `MemoryError` undocumented | GUIDE "Errors" documents them; pinned in `test_errors_contract.py` |
| d | D1 | `hatchling` without a lower bound degrades PEP 639 metadata | `hatchling>=1.27` |
| d | D2 | sdist lacked `requirements-dev.txt` and `scripts/check.ps1` named by CONTRIBUTING | both added to the sdist |
| e | E1 | CSI ending in `~` unpinned | `test_csi_sequences_ending_in_a_tilde`, bracketed paste |
| e | E2 | nF with several intermediates unpinned | `ESC $ ( B` test |
| e | E3 | middle cut with no room for the suffix unpinned | `test_a_middle_cut_with_no_room_for_the_suffix_keeps_the_start` |
| e | E4 | one tab spanning both sides of a middle cut unpinned | `test_a_middle_cut_through_one_tab_spanning_both_sides` |
| e | E5 | suffix exactly filling the width unpinned | `test_a_suffix_that_fills_the_width_exactly_is_kept` |
| e | E6 | `fit` padding under `ambiguous=2` unpinned | `test_fit_pads_ambiguous_text_with_the_ambiguous_policy` |
| e | E7 | CLI `STOP = START - 1` unpinned | `test_slice_stop_just_before_start_is_a_usage_error` |
| e | E8 | CLI message cap unpinned | `test_a_huge_bad_argument_gives_a_short_message` |

Lens b's observations (unterminated strings as text, an interrupted CSI, a lone regional
indicator with VS16, Old Hangul L L V, noncharacters) were noted as consistent with the
documented policy and need no change.

Fixes in commit 624971b, report in 885be0a. Gates at 885be0a on Elena's PC (CPython 3.14),
from a fresh clone of the branch with the ten Unicode files present and wcwidth 0.9.2:
`ruff format --check .`, `ruff check .`, `mypy --strict src`, `mypy --strict src tests
scripts` and `python scripts/gen_ucd_tables.py --check` exit 0; `pytest` 2,741 passed,
none skipped, in 43 s. The commit after it changes only this report.

Disputed findings: none.

### Round 2, on af60316

The same five lenses re-ran their round 1 findings on af60316: every one is fixed (lens a
A1 to A5, lens b F1 to F5, lens c F1 to F5, and lens e's eight mutants E1 to E8 all
killed). They also swept the code changed since 8380f22 and reported these:

| Lens | Id | Finding | Fix |
| --- | --- | --- | --- |
| a | A6 | GUIDE named `strip_ansi` under "a result never holds a cluster the text did not hold", but removing an escape can join the clusters on either side (U+2764, ESC, VS16: 1 cell before, 2 after) | docs: the promise is limited to slicing, truncation, padding and `expand_tabs`; `strip_ansi` has its own GUIDE bullet with the example (run as a test), its docstring and the README say the stripped text can measure differently |
| b | N1 | GUIDE: "after any other emoji a variation selector changes nothing", but VS16 widens a lone regional indicator; the "Emoji + VS16 = 2" row fails when a lone skin tone modifier starts the cluster (modifier, VS16, spacing mark: 3) | docs: the sentence is limited to VS15 and says VS16 widens every emoji, a lone regional indicator included; the table row, the GUIDE and the `grapheme_width` docstring say a cluster that a lone modifier starts adds up its code points; both cases are GUIDE examples run as tests |
| b | N2 | "never holds a cluster that the text did not hold" false: a combining mark after a tab or control can join a new neighbour (same width) | docs: the promise is "an escape sequence or a wider cluster", as the CHANGELOG and `_join.py` already said; GUIDE and the `cell_slice` docstring say such a mark stays and joins its new neighbour at the same width; pinned in `test_cut_seams.py` |
| c | G1 | a suffix starting with an extender (VS16, a tag, ZWJ) glued to the last kept emoji or regional indicator and widened it: `truncate_detailed` over `width`, `fit` not exact, `truncate` not idempotent | behaviour: `Joiner.fixed` applies the no-widening rule to the clusters at the start of added text, so such a cluster of the suffix is dropped; contract in `test_cut_seams.py`, and the seeded fuzz of `test_stray_escapes.py` now has VS16, tag and ZWJ suffixes and checks idempotence; CHANGELOG |
| e | F1 (N34) | tab wholly in the left part of a middle cut, suffix placement unpinned | `test_a_middle_cut_puts_the_suffix_after_a_whole_tab_and_the_text_kept_after_it` |
| e | F2 (N36) | zero-width cluster at the head column of a middle cut unpinned | `test_a_zero_width_cluster_at_the_middle_cut_column_goes_with_the_dropped_part` |
| e | F3 (N23) | stray ESC inside the suffix unpinned | `test_a_stray_escape_in_the_suffix_follows_the_cell_slice_rule` |
| e | F4 (N12) | GB11 across a cut seam unpinned | `test_a_cut_never_fuses_across_an_emoji_zwj_seam` |
| e | F5 (N10) | regional indicator run across a seam unpinned | `test_a_cut_never_joins_two_lone_regional_indicators_into_a_flag` |
| e | F6 (N11) | orphan mark after a multi-cluster suffix unpinned | `test_an_orphan_mark_after_a_multi_cluster_suffix_joins_its_last_letter` |
| e | F7 (N20) | modifier-headed case of the no-fusion rule unpinned | `test_an_orphan_glued_to_a_lone_skin_tone_modifier_is_kept` |

The new tests were run against the af60316 sources first: the G1 contract and the three
seeds of the extended fuzz failed, the rest (which pin behaviour that was already right)
passed. Each of the seven surviving mutants of lens e was then applied again, exactly as
lens e wrote it, and `tests/test_cut_seams.py` now fails for every one, each on the test
named above. The only behaviour change is G1, listed in the CHANGELOG.

Fixes in commit 8366709. Gates at 8366709 on Elena's PC (CPython 3.14), from a fresh clone
of the branch with the ten Unicode files fetched and wcwidth 0.9.2: `ruff format --check
.`, `ruff check .`, `mypy --strict src`, `mypy --strict src tests scripts` and `python
scripts/gen_ucd_tables.py --check` exit 0; `pytest` 2,751 passed, none skipped, in 61 s.
The commit after it changes only this report.

Disputed findings: none.

### Round 3, on 0ca1732

Lenses a, b and e re-ran their round 2 findings on 0ca1732: A6, N1 and N2 are fixed, and
lens e's seven round 2 mutants are killed. Their sweep of the new suffix seam found that
a glued piece could also make the joined cluster narrower, not only wider, and nine
surviving mutants of the old `Joiner._grows` and `_add_fixed` rules:

| Lens | Id | Finding | Fix |
| --- | --- | --- | --- |
| a | A7 | a suffix could fuse with the kept text into a narrower cluster (thumbs up + skin tone: 4 cells kept, 2 shown), against "its width is the width of the pieces it keeps" | behaviour: see the rule below; GUIDE, `truncate_detailed` docstring and CHANGELOG say a dropped piece can leave the result shorter still, or without the suffix |
| a | A8 | a zero-width suffix cluster after an emoji was dropped even when it did not widen it (U+2764 + U+0301 is one cell) | behaviour: it now stays, as the docs said |
| b | N3 | a cut or a suffix could fuse two kept pieces into a narrower emoji the text did not hold (man, ZWJ ... laptop became the technologist emoji, 2 cells for 4) | behaviour: see the rule below |
| e | M1 to M9 | mutants of `_grows` and `_add_fixed` survived (ambiguous policy, multi-code-point suffix cluster, `tail[0]`, `!=`, `<= 1`, EXT_PICT head, forgotten scan state) | the code they mutate is gone; each repro is pinned in `tests/test_fusion_seams.py` with its value under the new rule |
| e | O1 | docs said only a widening suffix cluster goes, but one that keeps or narrows the width could go too and the suffix could vanish | docs: the rule and the vanishing suffix are documented |

The rule now, in `Joiner._add`: a piece that joins the cluster before it in the result
stays only when the joined cluster measures the sum of the two widths, measured with the
caller's ambiguous policy; otherwise it is dropped, whether it comes from the text or is
the start of the suffix. The joiner keeps the last cluster of the result (across glues)
and measures the glued text with the same segmentation as the whole result. So every
result is exactly as wide as the pieces it keeps; A7, A8, N3 and O1 hold by
construction. The old break-state scanner (`scan`, `Scan`) is no longer used and is gone.
Two round 2 test names promised more than their cases checked (lens b): they are now
`test_a_middle_cut_keeps_a_zwj_with_its_emoji_when_the_right_part_does_not_fit` and
`test_a_middle_cut_leaves_out_a_right_cluster_wider_than_its_part`, and the real seams
are pinned in `tests/test_fusion_seams.py` (two lone regional indicators that a cut
brings together form a flag, two cells as before, which the rule allows).

The new tests were run against the 0ca1732 sources first: 5 of their functions failed
(A7, N3 middle and suffix, A8, the ambiguous policy), the rest pin values the old code
already gave. Mutation check of the new joiner, 15 mutants applied one at a time (glued
or head width with ambiguous=1, `!=` to `>` and to `<`, open cluster forgotten or ignored
after a glue, suffix cluster width with ambiguous=1 or 0, suffix split per code point,
`tail[0]` in both may-join checks, last cluster taken as the whole piece, the width check
skipped, the open cluster not reset after the rest of a suffix or after an escape): all
15 killed, by `tests/test_fusion_seams.py` or `tests/test_stray_escapes.py`. CHANGELOG
updated (the `cell_slice`/`truncate` seam entry).

Fix in commit c0d8725. Gates at c0d8725 on Elena's PC (CPython 3.14), from a fresh clone
of the branch with the ten Unicode files fetched and wcwidth 0.9.2, pytest-timeout 300 s:
`ruff format --check .`, `ruff check .`, `mypy --strict src`, `mypy --strict src tests
scripts` and `python scripts/gen_ucd_tables.py --check` exit 0; `pytest` exits 0 on
2,765 collected tests. The commit after it changes only this report.

Disputed findings: none.

### Round 4, on e057b96

Lenses b and e re-ran their round 3 findings on e057b96: N3 is fixed (lens b, with the
Unicode 18.0.0 GraphemeBreakTest.txt fetched live, 853 of 853 cases passing) and the
nine round 3 mutants M1 to M9 are killed, with O1 fixed in the docs (lens e). Lens b's
sweep of padding found a seam the joiner never saw, and lens e's 38 mutants of the
rewritten `_join.py` left four survivors (30 killed, 4 proven equivalent):

| Lens | Id | Finding | Fix |
| --- | --- | --- | --- |
| b | N4 | `ljust`, `rjust`, `center` and `fit` padded by plain concatenation, so a fill that joins the cluster at the edge of the text changed its width: `rjust("️ab", 5, "#")` was 6 cells (`#` + VS16 is an emoji), `ljust("👨‍", 4, "☠")` 3 | behaviour: see the rule below; docstring of `ljust`, GUIDE and CHANGELOG |
| e | N1 (S29) | `while` to `if` in `Joiner._add_fixed` survived: only the first leading suffix cluster was checked | pinned: `truncate("😀abcdef", 4, "‍💻")` is the grin and its ZWJ |
| e | N2 (S38) | `break` after the first leading suffix cluster survived (same gap) | killed by the same test |
| e | N3 (S16) | open cluster kept as the whole glued text survived | pinned: `cell_slice("↔︎कक", 0, 3)`, the same text after a tab in `expand_tabs` and a start cut keep both consonants |
| e | N4 (S32) | `_last_cluster` returning all after the first boundary survived | pinned: an orphan mark after a suffix of a letter and three regional indicators (`position="middle"`, `tabsize=8`) stays, 8 cells |

The padding rule now, in `_ops._pad`: the fill cell next to the text is a space when the
fill would join the cluster at that edge into one of another width, measured on the
whole padded text with the caller's ambiguous policy. A space joins only as the sum of
the widths (checked for every code point on both sides), and copies of a valid fill
never glue to each other at another width (checked for every valid fill), so a padded
result is exactly `width` cells and holds the text whole. A fill that glues at the same
width (a regional indicator after a lone one, `#` before a combining acute) stays. The
API is unchanged.

The new tests (`tests/test_pad_seams.py`, three functions added to
`tests/test_fusion_seams.py`) were run against the e057b96 sources first: the four pad
seam functions that pin the new rule failed, and the three joiner pins passed (they
pin values the code already gave). Each of S29, S38, S16 and S32 applied to the fixed
sources fails `tests/test_fusion_seams.py`. Mutation check of `_pad`, seven mutants one
at a time (each seam check removed, the right check measured without the left fill, the
space put on the far side of each fill run, the body measured with ambiguous=1, the
centre split swapped): all seven killed by `tests/test_pad_seams.py`. A seeded fuzz of
60,000 random texts from 23 seam-prone pieces and 23 fill and ambiguous policy pairs (13 fills)
and the four padding functions with every alignment found no result off `width`.

Fix in commit 2dc700f. Gates at 2dc700f on Elena's PC (CPython 3.14), from a private
clone of the branch with the ten Unicode files fetched (all ten verified against the
manifest) and wcwidth 0.9.2, pytest-timeout 300 s: `ruff format --check .`, `ruff check
.`, `mypy --strict src`, `mypy --strict src tests scripts` and `python
scripts/gen_ucd_tables.py --check` exit 0; `pytest` 2,774 passed in 53 s. The commit
after it changes only this report and one docstring word ("before" an orphan at the
start of the text).

Disputed findings: none.
