"""Display-cell-accurate length, slicing, padding and truncation for terminal text.

Every function measures what a terminal draws: ANSI escape sequences count as nothing,
East Asian wide characters as two cells, combining marks and other zero-width code
points as nothing, and an emoji sequence or a flag as one two-cell glyph. Width data
comes from the Unicode Character Database, version ``UNICODE_VERSION``.
"""

from __future__ import annotations

from ._ansi import strip_ansi
from ._cells import Cell, cell_len, expand_tabs, iter_cells
from ._graphemes import iter_graphemes
from ._ops import cell_slice, center, ljust, rjust
from ._props import UNICODE_VERSION
from ._truncate import Align, Position, Truncation, fit, truncate, truncate_detailed
from ._width import char_width, grapheme_width

__version__ = "0.2.1"

__all__ = [
    "UNICODE_VERSION",
    "Align",
    "Cell",
    "Position",
    "Truncation",
    "cell_len",
    "cell_slice",
    "center",
    "char_width",
    "expand_tabs",
    "fit",
    "grapheme_width",
    "iter_cells",
    "iter_graphemes",
    "ljust",
    "rjust",
    "strip_ansi",
    "truncate",
    "truncate_detailed",
]
