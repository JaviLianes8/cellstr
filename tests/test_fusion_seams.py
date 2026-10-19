"""Contracts for a piece that glues to its new neighbour at a seam: it stays only at the same width.

A cut, a tab expansion or a suffix can put two pieces next to each other that were not
neighbours in the input, and the second can then join the cluster the first one ends.
The rule pinned here: the joined cluster must measure the sum of the two parts, so the
result is exactly as wide as the pieces it keeps. A piece that would make the joined
cluster wider or narrower is left out. Every vector is hand-written.
"""

from __future__ import annotations

from cellstr import Truncation, cell_len, fit, truncate, truncate_detailed

MAN_ZWJ = "\U0001f468\u200d"
LAPTOP = "\U0001f4bb"
GRIN_ZWJ = "\U0001f600\u200d"


def test_a_suffix_that_would_narrow_the_kept_emoji_is_dropped() -> None:
    # The skin tone joins the thumbs up into one two-cell emoji: 2 + 2 cells would show as 2.
    cut = truncate_detailed("\U0001f44dabc", 4, "\U0001f3fd")
    assert cut == Truncation("\U0001f44d", 2, 5, True)
    assert truncate("\U0001f44dabcdef", 4, "\U0001f3fd") == "\U0001f44d"


def test_a_middle_cut_never_fuses_two_emoji_across_a_zwj_seam() -> None:
    cut = truncate_detailed(MAN_ZWJ + " and " + LAPTOP, 4, "", position="middle")
    assert cut == Truncation(MAN_ZWJ, 2, 9, True)
    assert cell_len(fit(MAN_ZWJ + " and " + LAPTOP, 4, suffix="", position="middle")) == 4


def test_a_suffix_never_fuses_with_the_kept_text_across_a_zwj_seam() -> None:
    assert truncate_detailed(MAN_ZWJ + "abcdef", 4, LAPTOP) == Truncation(MAN_ZWJ, 2, 8, True)
    cut = truncate_detailed("abcdef" + LAPTOP, 4, MAN_ZWJ, position="start")
    assert cut == Truncation(MAN_ZWJ, 2, 8, True)
    for suffix in ["\u231a\U0001f3fb", "\u2764\ufe0f"]:
        assert truncate(GRIN_ZWJ + "abcdef", 4, suffix) == GRIN_ZWJ, suffix
    assert truncate(GRIN_ZWJ + "abcdef", 3, "\u2194\ufe0e") == GRIN_ZWJ


def test_a_zero_width_suffix_cluster_that_keeps_the_emoji_width_stays() -> None:
    assert truncate_detailed("\u2764abc", 1, "\u0301") == Truncation("\u2764\u0301", 1, 4, True)
    assert truncate("\U0001f600abc", 2, "\u0301") == "\U0001f600\u0301"
    assert truncate("\U0001f600abc", 2, "\ufe0f") == "\U0001f600\ufe0f"


def test_a_spacing_mark_glued_to_an_emoji_stays_at_the_sum_of_the_widths() -> None:
    cut = truncate_detailed("\U0001f600abc", 3, "\u0903")
    assert cut == Truncation("\U0001f600\u0903", 3, 5, True)


def test_a_regional_indicator_suffix_completing_a_flag_stays() -> None:
    assert truncate_detailed("a\U0001f1e6bcd", 3, "\U0001f1e7").text == "a\U0001f1e6\U0001f1e7"


def test_a_tag_after_a_pictograph_that_is_not_an_emoji_is_dropped() -> None:
    # U+1F02C is reserved, Extended_Pictographic but not Emoji: one cell, two with a tag.
    cut = truncate_detailed("\U0001f02cabc", 1, "\U000e0067")
    assert cut == Truncation("\U0001f02c", 1, 4, True)


def test_the_glue_is_measured_with_the_ambiguous_policy() -> None:
    # Two cells either way under ambiguous=2, so the mark stays; ambiguous=1 measures
    # the same text at one cell and also keeps it.
    assert truncate("\u2194abc", 2, "\u0301", ambiguous=2) == "\u2194\u0301"
    assert truncate("\u2194abc", 2, "\u0301") == "\u2194a\u0301"
    assert truncate(GRIN_ZWJ + "abcdef", 4, "\u2194\ufe0e", ambiguous=2) == GRIN_ZWJ
    assert truncate(GRIN_ZWJ + "abcdef", 4, "\u2194\ufe0e") == GRIN_ZWJ + "a\u2194\ufe0e"
    assert truncate(GRIN_ZWJ + "abcdef", 4, "\u2194\u200d\u2194", ambiguous=2) == GRIN_ZWJ


def test_a_second_orphan_after_a_glued_suffix_measures_the_whole_cluster() -> None:
    text = "\U0001f600abcd\t\U000e007fxy"
    cut = truncate(text, 5, "\u0903", position="middle", tabsize=8)
    assert cut == "\U0001f600\u0903xy" and cell_len(cut) == 5


def test_every_glued_seam_keeps_the_width_of_the_pieces() -> None:
    for text, width, suffix in [
        ("\U0001f44dabc", 4, "\U0001f3fd"),
        (MAN_ZWJ + "abcdef", 4, LAPTOP),
        ("\u2764abc", 1, "\u0301"),
        (GRIN_ZWJ + "abcdef", 4, "\u231a\U0001f3fb"),
    ]:
        cut = truncate_detailed(text, width, suffix)
        assert cut.width == cell_len(cut.text) <= width
        assert truncate(cut.text, width, suffix) == cut.text
        assert cell_len(fit(text, width, suffix=suffix)) == width


def test_a_suffix_cluster_glued_after_a_prepended_mark_is_measured_whole() -> None:
    # U+0600 is Prepend: the cluster after it joins it, and the sum of the widths decides.
    text = "\u0600\tabc"
    assert truncate_detailed(text, 3, "\u2194", ambiguous=2) == Truncation(
        "\u0600\u2194", 3, 4, True
    )
    assert truncate_detailed(text, 2, "\u2194") == Truncation("\u0600\u2194", 2, 4, True)
    # Glued, the two-code-point emoji presentation sequence loses its VS16 width: dropped.
    assert truncate_detailed(text + "d", 3, "\u2764\ufe0f") == Truncation("\u0600", 1, 5, True)
    assert truncate(text + "d", 2, "\u2194\ufe0e") == "\u0600\u2194\ufe0e"


def test_two_lone_regional_indicators_meeting_at_a_cut_form_a_flag_at_the_same_width() -> None:
    cut = truncate_detailed("\U0001f1e6xyz\U0001f1e7", 2, "", position="middle")
    assert cut == Truncation("\U0001f1e6\U0001f1e7", 2, 5, True)


def test_a_mark_after_a_suffix_of_several_clusters_is_measured_on_its_last_one() -> None:
    # The suffix starts with a two-cell emoji presentation sequence; the mark joins only
    # the letter after it, at the same width.
    cut = truncate("abc\t\u0301xyz", 6, suffix="\u2764\ufe0fx", position="start", tabsize=8)
    assert cut == "\u2764\ufe0fx\u0301xyz" and cell_len(cut) == 6


def test_an_orphan_after_the_rest_of_a_suffix_is_measured_on_that_rest() -> None:
    # The ZWJ of the suffix glues to the heart; the tag that the cut brings next glues
    # only to the "x" after it, at the same width.
    cut = truncate("a\u2764bcd\t\U000e0067yz", 5, "\u200dx", position="middle", tabsize=8)
    assert cut == "a\u2764\u200dx\U000e0067yz" and cell_len(cut) == 5
