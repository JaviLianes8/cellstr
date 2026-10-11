"""Width-aware slicing, padding and truncation.

Escape sequences are always kept in place so colour and style survive the
operation, while only printable cells count toward a width.
"""

from __future__ import annotations

from ._ansi import segments
from ._width import cell_len, char_width


def cell_slice(text: str, start: int = 0, stop: int | None = None) -> str:
    """Return the cells of ``text`` in the half-open column range ``[start, stop)``.

    A wide character is kept only when both its cells fall inside the range.
    All escape sequences are preserved regardless of the range.
    """
    if start < 0 or (stop is not None and stop < 0):
        raise ValueError("cell_slice does not support negative indices")
    limit = cell_len(text) if stop is None else stop
    out: list[str] = []
    column = 0
    for segment in segments(text):
        if segment.is_escape:
            out.append(segment.text)
            continue
        for ch in segment.text:
            width = char_width(ch)
            if column >= start and column + width <= limit:
                out.append(ch)
            column += width
    return "".join(out)


def _fill(fillchar: str) -> str:
    if len(fillchar) != 1 or char_width(fillchar) != 1:
        raise ValueError("fillchar must be a single one-cell character")
    return fillchar


def ljust(text: str, width: int, fillchar: str = " ") -> str:
    """Pad ``text`` on the right to ``width`` display cells."""
    pad = max(0, width - cell_len(text))
    return text + _fill(fillchar) * pad


def rjust(text: str, width: int, fillchar: str = " ") -> str:
    """Pad ``text`` on the left to ``width`` display cells."""
    pad = max(0, width - cell_len(text))
    return _fill(fillchar) * pad + text


def center(text: str, width: int, fillchar: str = " ") -> str:
    """Centre ``text`` within ``width`` display cells."""
    pad = max(0, width - cell_len(text))
    left = pad // 2
    fill = _fill(fillchar)
    return fill * left + text + fill * (pad - left)


def truncate(text: str, width: int, suffix: str = "...") -> str:
    """Shorten ``text`` to at most ``width`` cells, ending with ``suffix``.

    When ``suffix`` alone would not fit, the text is cut to ``width`` with no
    suffix. ``text`` is returned unchanged when it already fits.
    """
    if width < 0:
        raise ValueError("width must be non-negative")
    if cell_len(text) <= width:
        return text
    suffix_width = cell_len(suffix)
    if suffix_width > width:
        return cell_slice(text, 0, width)
    return cell_slice(text, 0, width - suffix_width) + suffix
