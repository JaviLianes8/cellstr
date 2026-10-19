"""The cut itself: which cells survive a truncation and where the suffix goes."""

from __future__ import annotations

from ._cells import Cell
from ._join import Joiner
from ._ops import keep_range


def cut(
    found: list[Cell], total: int, room: int, where: str, suffix: str, ambiguous: int, tabs: bool
) -> str:
    """Keep ``room`` cells of ``found`` (``total`` wide) around ``suffix`` at ``where``."""
    out = Joiner(ambiguous)
    if where == "end":
        keep_range(out, found, 0, room, tabs)
        out.insert(suffix)
    elif where == "start":
        out.insert(suffix)
        keep_range(out, found, total - room, None, tabs)
    else:
        # The left part gets the odd cell. A wide cluster at one cut can leave a cell of
        # its part unused; the other part then gets it, so the result is as full as it can be.
        right = total - _first_cut_after(found, total, total - room // 2, tabs)
        budget = room - right
        left = _last_cut_before(found, budget, tabs)
        _splice(out, found, total, budget, total - (room - left), suffix, tabs)
    return out.text()


def _cuttable(cell: Cell) -> bool:
    return not cell.escape and cell.width > 0


def _last_cut_before(found: list[Cell], column: int, tabs: bool) -> int:
    """The widest left part that fits in ``column`` cells (a tab can be cut anywhere)."""
    best = 0
    for cell in filter(_cuttable, found):
        end = cell.column + cell.width
        if tabs and cell.text == "\t" and cell.column < column:
            best = min(end, column)
        elif end <= column:
            best = end
        else:
            break
    return best


def _first_cut_after(found: list[Cell], total: int, column: int, tabs: bool) -> int:
    """The first column at or after ``column`` where the right part can start."""
    for cell in filter(_cuttable, found):
        if cell.column >= column:
            return cell.column
        if cell.column + cell.width > column and tabs and cell.text == "\t":
            return column
    return total


def _splice(
    out: Joiner, found: list[Cell], total: int, head: int, rstart: int, insert: str, tabs: bool
) -> None:
    """Keep the clusters in ``[0, head)`` and ``[rstart, total)``, putting ``insert`` between.

    Every escape sequence is kept exactly once, in place, and ``insert`` goes where the
    first dropped cluster was. With ``tabs``, a tab becomes the spaces it covers on either
    side of the cut.
    """
    pending = True
    for cell in found:
        end = cell.column + cell.width
        if tabs and cell.text == "\t" and not cell.escape:
            left_spaces = max(0, min(end, head) - cell.column)
            if left_spaces:
                out.fixed(" " * left_spaces)
            if left_spaces < cell.width and pending:
                out.insert(insert)
                pending = False
            right_spaces = end - max(cell.column, rstart)
            if right_spaces > 0:
                out.fixed(" " * right_spaces)
            continue
        left = end <= head if cell.width else cell.column < head
        right = rstart <= cell.column and end <= total
        if not (cell.escape or left) and pending:
            out.insert(insert)
            pending = False
        if cell.escape:
            out.escape(cell.text)
        elif left or right:
            out.cluster(cell.text, cell.width)
    if pending:
        out.insert(insert)
