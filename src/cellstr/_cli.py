"""Command line interface: measure, truncate, pad, fit and slice stdin lines by cells."""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Callable, Sequence
from typing import NoReturn

from . import __version__
from ._cells import cell_len
from ._ops import cell_slice, center, check_fill, ljust, rjust
from ._truncate import fit, truncate

EPILOG = """\
examples:
  printf 'abc\\n\\344\\275\\240\\345\\245\\275\\n' | cellstr measure
  printf 'abc\\n\\344\\275\\240\\345\\245\\275\\n' | cellstr measure --max
  printf 'a long status message\\n' | cellstr truncate 10
  printf '/usr/local/lib/python3/site-packages\\n' | cellstr truncate 16 --position middle
  printf 'id\\n12345\\n' | cellstr pad 8 --align right
  printf 'name\\na much longer name\\n' | cellstr fit 10
  printf '\\x1b[31mred text\\x1b[0m\\n' | cellstr slice 4

Every command reads UTF-8 lines from stdin and writes one result line per input line,
keeping each line ending. ANSI escape sequences are ignored when measuring and kept in
the output. --ambiguous 2 counts East Asian Ambiguous characters (Greek, Cyrillic, box
drawing) as two cells, as CJK terminals draw them. Errors go to stderr with exit
status 1.
"""


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        self.print_usage(sys.stderr)
        self.exit(1, f"{self.prog}: error: {message}\n")


def _cells(text: str) -> int:
    try:
        value = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"not an integer: {text!r}") from None
    if value < 0:
        raise argparse.ArgumentTypeError(f"must not be negative: {value}")
    return value


def _positive(text: str) -> int:
    value = _cells(text)
    if value == 0:
        raise argparse.ArgumentTypeError("must be at least 1")
    return value


def _add(sub: argparse._SubParsersAction[_Parser], name: str, text: str, example: str) -> _Parser:
    common = _Parser(add_help=False)
    common.add_argument(
        "--ambiguous",
        type=int,
        choices=(1, 2),
        default=1,
        help="cells for East Asian Ambiguous characters (default 1)",
    )
    common.add_argument(
        "--tabsize",
        type=_positive,
        default=None,
        metavar="N",
        help="expand tabs to stops every N cells (default: tabs count as zero)",
    )
    return sub.add_parser(
        name,
        parents=[common],
        help=text,
        description=text,
        epilog=f"example:\n  {example}\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )


def _cut_options(parser: _Parser) -> None:
    parser.add_argument("-s", "--suffix", default="...", help="marks the cut (default ...)")
    parser.add_argument(
        "--position",
        choices=("end", "start", "middle"),
        default="end",
        help="where to cut (default end)",
    )


def _pad_options(parser: _Parser) -> None:
    parser.add_argument(
        "--align", choices=("left", "right", "center"), default="left", help="default left"
    )
    parser.add_argument("--fill", default=" ", help="one-cell padding character (default space)")


def build_parser() -> argparse.ArgumentParser:
    """Return the argument parser for the ``cellstr`` command."""
    parser = _Parser(
        prog="cellstr",
        description="Measure, truncate, pad and slice text by terminal display cells.",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"cellstr {__version__}")
    sub = parser.add_subparsers(dest="command", required=True, parser_class=_Parser)
    measure = _add(sub, "measure", "print the display width of each line", "cellstr measure")
    measure.add_argument("--max", action="store_true", help="print only the widest width")
    cut = _add(sub, "truncate", "cut each line to N cells", "cellstr truncate 20 --suffix '~'")
    cut.add_argument("width", type=_cells, metavar="N", help="maximum width in cells")
    _cut_options(cut)
    pad = _add(sub, "pad", "pad each line to N cells", "cellstr pad 12 --align center")
    pad.add_argument("width", type=_cells, metavar="N", help="target width in cells")
    _pad_options(pad)
    fitted = _add(sub, "fit", "truncate or pad each line to exactly N cells", "cellstr fit 12")
    fitted.add_argument("width", type=_cells, metavar="N", help="exact width in cells")
    _cut_options(fitted)
    _pad_options(fitted)
    piece = _add(sub, "slice", "keep the cells in columns [START, STOP)", "cellstr slice 2 10")
    piece.add_argument("start", type=_cells, metavar="START", help="first column, from 0")
    piece.add_argument("stop", type=_cells, nargs="?", metavar="STOP", help="end column")
    return parser


def _lines(text: str) -> list[tuple[str, str]]:
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


def _run(args: argparse.Namespace, text: str) -> str:
    lines = _lines(text)
    if args.command == "measure":
        widths = [cell_len(b, ambiguous=args.ambiguous, tabsize=args.tabsize) for b, _ in lines]
        return f"{max(widths, default=0)}\n" if args.max else "".join(f"{w}\n" for w in widths)
    if args.command in ("pad", "fit"):
        check_fill(args.fill, args.ambiguous)
    if args.command == "slice" and args.stop is not None and args.stop < args.start:
        raise ValueError(f"STOP ({args.stop}) must not be less than START ({args.start})")
    change = _transform(args)
    return "".join(change(body) + end for body, end in lines)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line tool and return its exit status."""
    args = build_parser().parse_args(argv)
    try:
        result = _run(args, sys.stdin.buffer.read().decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        print(f"cellstr: error: {exc}", file=sys.stderr)
        return 1
    try:
        sys.stdout.buffer.write(result.encode("utf-8", "surrogatepass"))
        sys.stdout.buffer.flush()
    except BrokenPipeError:
        # The reader went away (for example `| head -1`); exit quietly like other filters.
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
    return 0
