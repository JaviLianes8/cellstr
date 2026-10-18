"""Command line interface: measure, truncate, pad, fit and slice stdin lines by cells."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from typing import NoReturn

from . import __version__
from ._args import show
from ._cli_io import output_lost, read_input, say, write_output
from ._cli_lines import run
from ._ops import check_fill

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
drawing) as two cells, as CJK terminals draw them. Errors go to stderr: exit status 2
for a bad command line, 1 when the input is not UTF-8 or the output cannot be written.
"""
_MESSAGE_LIMIT = 200


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        if len(message) > _MESSAGE_LIMIT:
            message = message[: _MESSAGE_LIMIT - 3] + "..."
        self.print_usage(sys.stderr)
        self.exit(2, f"{self.prog}: error: {message}\n")


def _cells(text: str) -> int:
    try:
        value = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"not an integer: {show(text)}") from None
    if value < 0:
        raise argparse.ArgumentTypeError(f"must not be negative: {show(value)}")
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


def _check(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    """Refuse the option values argparse cannot check alone, as usage errors."""
    try:
        if args.command in ("pad", "fit"):
            check_fill(args.fill, args.ambiguous)
        if args.command in ("truncate", "fit") and any(ch in args.suffix for ch in "\t\n\r"):
            raise ValueError("suffix must not contain tabs or line breaks")
    except ValueError as exc:
        parser.error(str(exc))
    if args.command == "slice" and args.stop is not None and args.stop < args.start:
        parser.error(f"STOP ({args.stop}) must not be less than START ({args.start})")


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line tool and return its exit status.

    0 on success, 2 for a bad command line, 1 when standard input cannot be read as
    UTF-8 or the output cannot be written (for example when the reader of a pipe goes
    away, as with ``| head -1``).
    """
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        _check(parser, args)
    except SystemExit as exc:  # --help and --version (0) or a usage error (2)
        status = exc.code if isinstance(exc.code, int) else 2
        if status == 0:
            try:  # argparse wrote through the text layer of stdout: push it out now
                write_output("")
            except OSError as lost:
                return output_lost(lost)
        return status
    try:
        result = run(args, read_input())
    except ValueError as exc:
        say(str(exc))
        return 1
    try:
        write_output(result)
    except OSError as exc:
        return output_lost(exc)
    return 0
