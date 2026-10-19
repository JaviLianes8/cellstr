"""The argument parser of the ``cellstr`` command and the checks it cannot make alone."""

from __future__ import annotations

import argparse
import sys
from typing import NoReturn

from . import __version__
from ._args import show
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
for a bad command line, 1 when the input is not UTF-8 or the output is too large to
build or cannot be written.
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
        # int() also refuses a number past the interpreter's digit limit.
        kind = "too large" if text.strip().lstrip("+").isdecimal() else "not an integer"
        raise argparse.ArgumentTypeError(f"{kind}: {show(text)}") from None
    if value < 0:
        raise argparse.ArgumentTypeError(f"must not be negative: {show(value)}")
    return value


def _positive(text: str) -> int:
    value = _cells(text)
    if value == 0:
        raise argparse.ArgumentTypeError("must be at least 1")
    return value


def _utf8(text: str) -> str:
    # On POSIX an undecodable byte in an argument arrives as a lone surrogate.
    if any("\ud800" <= ch <= "\udfff" for ch in text):
        raise argparse.ArgumentTypeError("not valid UTF-8 text")
    return text


def _suffix(text: str) -> str:
    if any(ch in text for ch in "\t\n\r"):
        raise argparse.ArgumentTypeError("must not contain tabs or line breaks")
    return _utf8(text)


def _fill(text: str) -> str:
    try:
        return check_fill(_utf8(text), 1)
    except ValueError:
        raise argparse.ArgumentTypeError(f"not one one-cell character: {show(text)}") from None


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
    created = sub.add_parser(
        name,
        parents=[common],
        help=text,
        description=text,
        epilog=f"example:\n  {example}\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    created.set_defaults(usage=created)  # later checks report against this command
    return created


def _cut_options(parser: _Parser) -> None:
    parser.add_argument(
        "-s", "--suffix", type=_suffix, default="...", help="marks the cut (default ...)"
    )
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
    parser.add_argument(
        "--fill", type=_fill, default=" ", help="one-cell padding character (default space)"
    )


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


def check_combinations(args: argparse.Namespace) -> None:
    """Refuse the option combinations argparse cannot check alone, as usage errors."""
    command: argparse.ArgumentParser = args.usage
    if args.command in ("pad", "fit") and args.ambiguous == 2:
        try:
            check_fill(args.fill, 2)
        except ValueError:
            command.error(f"argument --fill: two cells wide with --ambiguous 2: {show(args.fill)}")
    if args.command == "slice" and args.stop is not None and args.stop < args.start:
        command.error(f"STOP ({args.stop}) must not be less than START ({args.start})")
