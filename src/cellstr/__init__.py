"""Display-cell-accurate length, slicing, padding and truncation for terminal text."""

from __future__ import annotations

from ._ansi import strip_ansi
from ._ops import cell_slice, center, ljust, rjust, truncate
from ._table import UNICODE_VERSION
from ._width import cell_len, char_width

__version__ = "0.1.0"

__all__ = [
    "UNICODE_VERSION",
    "cell_len",
    "cell_slice",
    "center",
    "char_width",
    "ljust",
    "rjust",
    "strip_ansi",
    "truncate",
]
