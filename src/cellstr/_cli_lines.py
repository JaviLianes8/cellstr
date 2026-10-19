"""The work of each ``cellstr`` command, applied line by line to a decoded text."""

from __future__ import annotations

import argparse
from collections.abc import Callable

from ._cells import cell_len
from ._ops import cell_slice, center, ljust, rjust
from ._truncate import fit, truncate


def split_lines(text: str) -> list[tuple[str, str]]:
    """Split ``text`` on LF into ``(body, line ending)`` pairs, keeping CR LF and LF."""
    pairs: list[tuple[str, str]] = []
    parts = text.split("\n")
    for index, body in enumerate(parts):
        last = index == len(parts) - 1
        if last and not body:
            break
        end = "" if last else "\n"
        if body.endswith("\r"):
            body, end = body[:-1], "\r" + end
        pairs.append((body, end))
    return pairs


def _transform(args: argparse.Namespace) -> Callable[[str], str]:
    policy = {"ambiguous": args.ambiguous, "tabsize": args.tabsize}
    if args.command == "truncate":
        return lambda s: truncate(s, args.width, args.suffix, position=args.position, **policy)
    if args.command == "fit":
        options = {"suffix": args.suffix, "position": args.position, "fillchar": args.fill}
        return lambda s: fit(s, args.width, align=args.align, **options, **policy)
    if args.command == "pad":
        pad = {"left": ljust, "right": rjust, "center": center}[args.align]
        return lambda s: pad(s, args.width, args.fill, **policy)
    return lambda s: cell_slice(s, args.start, args.stop, **policy)


def run(args: argparse.Namespace, text: str) -> str:
    """Return the output of the command in ``args`` for the input ``text``."""
    lines = split_lines(text)
    if args.command == "measure":
        widths = [cell_len(b, ambiguous=args.ambiguous, tabsize=args.tabsize) for b, _ in lines]
        return f"{max(widths, default=0)}\n" if args.max else "".join(f"{w}\n" for w in widths)
    change = _transform(args)
    return "".join(change(body) + end for body, end in lines)
