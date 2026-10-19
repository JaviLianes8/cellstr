"""Display-cell-accurate length, slicing, padding and truncation for terminal text.

Every function measures what a terminal draws: ANSI escape sequences count as nothing,
East Asian wide characters as two cells, combining marks and other zero-width code
points as nothing, and an emoji sequence or a flag as one two-cell glyph. Width data
comes from the Unicode Character Database, version ``UNICODE_VERSION``. ``Position``
and ``Align`` are the values ``truncate`` and ``fit`` accept for ``position`` and
``align``.

>>> import typing
>>> from cellstr import UNICODE_VERSION, Align, Position, fit
>>> UNICODE_VERSION
'18.0.0'
>>> typing.get_args(Position), typing.get_args(Align)
(('end', 'start', 'middle'), ('left', 'right', 'center'))
>>> fit("cellstr", 5, align="right", position="middle")
'c...r'
"""

from ._ansi import strip_ansi
from ._cells import Cell, cell_len, expand_tabs, iter_cells
from ._graphemes import iter_graphemes
from ._ops import cell_slice, center, ljust, rjust
from ._props import UNICODE_VERSION
from ._truncate import Align, Position, Truncation, fit, truncate, truncate_detailed
from ._width import char_width, grapheme_width

__version__ = "1.0.0"

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
