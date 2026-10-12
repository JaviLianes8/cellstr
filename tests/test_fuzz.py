"""Seeded fuzzing of slicing, truncation, padding and measuring over hostile text."""

from __future__ import annotations

import random

import pytest

from cellstr import (
    cell_len,
    cell_slice,
    expand_tabs,
    fit,
    grapheme_width,
    iter_cells,
    iter_graphemes,
    truncate,
    truncate_detailed,
)

PIECES = [
    "a",
    "Z",
    " ",
    "\u4f60",
    "\uff21",
    "\uac00",
    "\u1100\u1161\u11a8",
    "e\u0301",
    "\u0301",
    "\u0915\u094d\u0937\u093f",
    "\U0001f468\u200d\U0001f469\u200d\U0001f467",
    "\U0001f1ea\U0001f1f8",
    "\U0001f1ea",
    "\U0001f44d\U0001f3fd",
    "\U0001f3fd",
    "\u2764\ufe0f",
    "\u231a\ufe0e",
    "1\ufe0f\u20e3",
    "\u200b",
    "\u200d",
    "\u00ad",
    "\u03b1",
    "\u2500",
    "\x07",
    "\t",
    "\r\n",
    "\x1b[31m",
    "\x1b[0m",
    "\x1b]8;;https://example.com\x1b\\",
    "\x1b]8;;\x07",
]
SEEDS = range(300)


def _text(rng: random.Random, plain: bool = False) -> str:
    pool = [p for p in PIECES if "\x1b" not in p] if plain else PIECES
    return "".join(rng.choice(pool) for _ in range(rng.randrange(0, 14)))


def _clusters(text: str) -> list[str]:
    return [c.text for c in iter_cells(text) if not c.escape]


def _is_run(part: list[str], whole: list[str]) -> bool:
    return any(whole[i : i + len(part)] == part for i in range(len(whole) - len(part) + 1))


@pytest.mark.parametrize("seed", SEEDS)
def test_slicing_is_safe(seed: int) -> None:
    rng = random.Random(seed)
    text = _text(rng)
    total = cell_len(text)
    start = rng.randrange(0, total + 2)
    stop = rng.randrange(start, total + 3)
    ambiguous = rng.choice((1, 2))
    piece = cell_slice(text, start, stop, ambiguous=ambiguous)
    width = cell_len(piece, ambiguous=ambiguous)
    assert width <= stop - start
    widest = max([1, *(c.width for c in iter_cells(text, ambiguous=ambiguous))])
    # Only the clusters straddling the two edges may be dropped.
    assert width >= min(stop, cell_len(text, ambiguous=ambiguous)) - start - 2 * (widest - 1)
    assert _is_run(_clusters(piece), _clusters(text)), "a grapheme cluster was split"
    assert piece.count("\x1b") == text.count("\x1b")


@pytest.mark.parametrize("seed", SEEDS)
def test_plain_slices_split_back_into_the_text(seed: int) -> None:
    rng = random.Random(seed)
    text = _text(rng, plain=True)
    inside_wide = {c.column + i for c in iter_cells(text) for i in range(1, c.width)}
    for k in range(cell_len(text) + 1):
        if k not in inside_wide:
            assert cell_slice(text, 0, k) + cell_slice(text, k) == text


@pytest.mark.parametrize("seed", SEEDS)
def test_truncation_and_fit_respect_the_width(seed: int) -> None:
    rng = random.Random(seed)
    text = _text(rng)
    width = rng.randrange(0, 12)
    suffix = rng.choice(["...", "~", "", "\u2026", "\u4f60"])
    position = rng.choice(["end", "start", "middle"])
    result = truncate_detailed(text, width, suffix, position=position)  # type: ignore[arg-type]
    assert result.width == cell_len(result.text) <= width
    assert result.truncated == (cell_len(text) > width)
    if not result.truncated:
        assert result.text == text
    assert _is_run(_clusters(truncate(text, width, "")), _clusters(text))
    assert cell_len(fit(text, width, suffix=suffix, position=position)) == width  # type: ignore[arg-type]


@pytest.mark.parametrize("seed", SEEDS)
def test_measuring_agrees_with_cluster_widths(seed: int) -> None:
    rng = random.Random(seed)
    plain = _text(rng, plain=True)
    assert cell_len(plain) == sum(grapheme_width(g) for g in iter_graphemes(plain))
    assert cell_len(plain, ambiguous=2) >= cell_len(plain)
    text = _text(rng)
    assert cell_len(text) == sum(c.width for c in iter_cells(text))


@pytest.mark.parametrize("seed", SEEDS)
def test_tab_expansion_matches_tab_aware_measuring(seed: int) -> None:
    rng = random.Random(seed)
    text = _text(rng)
    size = rng.randrange(1, 9)
    expanded = expand_tabs(text, size)
    assert "\t" not in expanded
    assert cell_len(expanded) == cell_len(text, tabsize=size)
