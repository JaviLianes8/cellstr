"""Command line interface: measure, truncate, pad, fit and slice stdin lines by cells."""

from __future__ import annotations

from collections.abc import Sequence

from ._cli_io import output_lost, read_input, say, write_output
from ._cli_lines import run
from ._cli_parser import build_parser, check_combinations

__all__ = ["build_parser", "main"]


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line tool and return its exit status.

    0 on success, 2 for a bad command line, 1 when standard input cannot be read as
    UTF-8, the output is too large to build or it cannot be written (for example when
    the reader of a pipe goes away, as with ``| head -1``).
    """
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        check_combinations(args)
    except SystemExit as exc:  # --help and --version (0) or a usage error (2)
        status = exc.code if isinstance(exc.code, int) else 2
        if status == 0:
            try:  # argparse wrote through the text layer of stdout: push it out now
                write_output("")
            except OSError as lost:
                return output_lost(lost)
        return status
    try:
        write_output(run(args, read_input()))
    except OSError as exc:
        return output_lost(exc)
    except ValueError as exc:
        say(str(exc))
        return 1
    except (MemoryError, OverflowError):  # such as pad 10**15: more cells than memory holds
        say("the output is too large to build")
        return 1
    return 0
