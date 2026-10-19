"""Hostile input shapes cost time in proportion to their length, never quadratically.

Each shape is timed at two sizes eight times apart, keeping the fastest of three runs with
the garbage collector paused; a linear cost grows about eight times, a quadratic one
sixty-four, and the bound sits well between.
"""

from __future__ import annotations

import gc
import time
from collections.abc import Callable

import pytest

from cellstr import cell_len, cell_slice, fit, iter_cells, iter_graphemes, strip_ansi, truncate

SHAPES: dict[str, Callable[[int], str]] = {
    "plain ascii": lambda n: "a" * n,
    "wide": lambda n: "你" * n,
    "one letter with n accents": lambda n: "e" + "́" * n,
    "one ZWJ chain": lambda n: "\U0001f468" + "‍\U0001f469" * n,
    "regional indicators": lambda n: "\U0001f1ea" * n,
    "Indic linker chain": lambda n: "क" + "्क" * n,
    "Hangul jamo run": lambda n: "ᄀ" * n + "ᅡ" * n,
    "escapes": lambda n: "\x1b[31mx" * n,
    "unterminated OSC": lambda n: "\x1b]8;;" + "a" * n,
    "unterminated OSCs": lambda n: "\x1b]a" * n,
    "unterminated DCS strings": lambda n: "\x1bPa" * n,
    "lone escapes": lambda n: "\x1b" * n,
    "tabs and line breaks": lambda n: "a\tb\r\n" * n,
}
OPERATIONS: dict[str, Callable[[str], object]] = {
    "cell_len": lambda s: cell_len(s, tabsize=8),
    "cell_slice": lambda s: cell_slice(s, 3, 10**9, tabsize=8),
    "truncate middle": lambda s: truncate(s, 40, position="middle", tabsize=8),
    "fit": lambda s: fit(s, 50),
    "iter_cells": lambda s: sum(1 for _ in iter_cells(s)),
    "iter_graphemes": lambda s: sum(1 for _ in iter_graphemes(s)),
    "strip_ansi": strip_ansi,
}
SMALL = 2_000


def _fastest(operation: Callable[[str], object], text: str) -> float:
    best = float("inf")
    gc.disable()
    try:
        for _ in range(3):
            start = time.perf_counter()
            operation(text)
            best = min(best, time.perf_counter() - start)
    finally:
        gc.enable()
    return best


@pytest.mark.parametrize("shape", SHAPES)
@pytest.mark.parametrize("operation", OPERATIONS)
def test_cost_grows_linearly(shape: str, operation: str) -> None:
    run, make = OPERATIONS[operation], SHAPES[shape]
    small = _fastest(run, make(SMALL))
    large = _fastest(run, make(8 * SMALL))
    # The floor keeps timer noise on very fast calls from deciding the ratio.
    assert large <= 20 * max(small, 0.002), (small, large)
