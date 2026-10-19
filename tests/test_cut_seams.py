"""Contracts for the seams a cut creates: where the suffix goes and what may glue there.

Each vector is hand-written and pins one rule of ``_splice`` or ``Joiner`` that the
random fuzz in test_stray_escapes.py does not reach on its own.
"""

from __future__ import annotations

from cellstr import cell_len, fit, iter_graphemes, truncate, truncate_detailed


def test_a_middle_cut_puts_the_suffix_after_a_whole_tab_and_the_text_kept_after_it() -> None:
    cut = truncate("a\tbcdefghijklmnop", 10, "~", position="middle", tabsize=4)
    assert cut == "a   b~mnop" and cell_len(cut) == 10


def test_a_zero_width_cluster_at_the_middle_cut_column_goes_with_the_dropped_part() -> None:
    assert truncate("abc\u200bdefghij", 7, "~", position="middle") == "abc~hij"
    assert truncate("ab\u200bcdefghij", 7, "~", position="middle") == "ab\u200bc~hij"


def test_a_stray_escape_in_the_suffix_follows_the_cell_slice_rule() -> None:
    # Kept before a non-ASCII character, dropped before printable ASCII.
    assert truncate("abcdefgh", 5, suffix="\x1b\xe9") == "abcd\x1b\xe9"
    assert truncate("abcdefgh", 5, suffix="\x1b!") == "abcd!"
    assert truncate("abcdefgh", 5, suffix="\x1b") == "abcde"


def test_a_middle_cut_keeps_a_zwj_with_its_emoji_when_the_right_part_does_not_fit() -> None:
    cut = truncate_detailed("\U0001f600\u200dabc\u231a\ufe0e", 3, "", position="middle")
    assert cut.text == "\U0001f600\u200d" and cut.width == cell_len(cut.text) == 2


def test_a_middle_cut_leaves_out_a_right_cluster_wider_than_its_part() -> None:
    cut = truncate_detailed("a\U0001f1e6x\U0001f1e6\U0001f3fb", 4, "", position="middle")
    assert cut.text == "a\U0001f1e6" and cut.width == 2
    assert list(iter_graphemes(cut.text)) == ["a", "\U0001f1e6"]


def test_an_orphan_mark_after_a_multi_cluster_suffix_joins_its_last_letter() -> None:
    cut = truncate("abc\t\u0301xyz", 6, suffix="\U0001f600x", position="start", tabsize=8)
    assert cut == "\U0001f600x\u0301xyz" and cell_len(cut) == 6


def test_an_orphan_glued_to_a_lone_skin_tone_modifier_is_kept() -> None:
    # A lone modifier is a two-cell symbol that a variation selector does not widen.
    cut = truncate("\U0001f3fb\t\ufe0fab", 4, "", position="middle", tabsize=8)
    assert cut == "\U0001f3fb\ufe0fab" and cell_len(cut) == 4


def test_a_suffix_starting_with_an_extender_never_widens_the_kept_emoji() -> None:
    for text, suffix in [
        ("\u2764ab", "\ufe0f"),
        ("\u2764ab", "\U000e0067"),
        ("\U0001f1faab", "\U000e007f"),
        ("\u2764ab", "\u200d\ufe0f"),
    ]:
        cut = truncate_detailed(text, 1, suffix)
        assert cut.width == cell_len(cut.text) <= 1, (text, suffix, cut)
        assert cell_len(fit(text, 1, suffix=suffix)) == 1
        assert truncate(cut.text, 1, suffix) == cut.text
    assert truncate("\u2764ab", 2, "\ufe0f~") == "\u2764~"
    assert truncate("ab\u2764cd", 3, "\U000e0067~", position="middle") == "a\U000e0067~d"


def test_a_suffix_extender_that_does_not_widen_stays() -> None:
    assert truncate("abcd", 3, "\u0301~") == "ab\u0301~"
    assert truncate("\u2764abc", 3, "\u0301") == "\u2764ab\u0301"


def test_a_cut_may_move_a_lone_mark_onto_a_new_letter_at_the_same_width() -> None:
    # A combining mark that followed a control rides on the letter now before it.
    cut = truncate_detailed("abcdefg\t\u0301xy", 4, "", position="middle", tabsize=4)
    assert cut.text == "ab\u0301xy" and cut.width == cell_len(cut.text) == 4
