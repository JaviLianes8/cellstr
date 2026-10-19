"""Standard streams for the ``cellstr`` command: strict UTF-8 in, quiet stop on a lost pipe."""

from __future__ import annotations

import contextlib
import errno
import os
import sys


def say(message: str) -> None:
    """Write one error line to stderr, if there is a stderr that still works."""
    if sys.stderr is not None:
        with contextlib.suppress(OSError, ValueError):
            sys.stderr.write(f"cellstr: error: {message}\n")
            sys.stderr.flush()


def read_input() -> str:
    """Read all of stdin as strict UTF-8; ValueError with a short reason otherwise."""
    stream = sys.stdin
    if stream is None:
        raise ValueError("no standard input")
    buffer = getattr(stream, "buffer", None)
    try:
        data: str | bytes = stream.read() if buffer is None else buffer.read()
    except OSError as exc:
        raise ValueError(f"cannot read standard input ({exc.strerror or 'error'})") from None
    if isinstance(data, str):
        return data
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        where = f"byte 0x{data[exc.start]:02x} at offset {exc.start}"
        raise ValueError(f"standard input is not valid UTF-8 ({where})") from None


def write_output(text: str) -> None:
    """Write ``text`` to stdout as UTF-8 and flush; OSError when it cannot be written."""
    stream = sys.stdout
    if stream is None:
        raise OSError(errno.EBADF, "no standard output")
    buffer = getattr(stream, "buffer", None)
    if buffer is None:
        stream.write(text)
    else:
        stream.flush()
        buffer.write(text.encode("utf-8"))
        buffer.flush()
    stream.flush()


def output_lost(exc: OSError) -> int:
    """The output cannot be written: say why unless the reader simply went away; exit 1."""
    gone = isinstance(exc, (BrokenPipeError, ConnectionResetError)) or exc.errno == errno.EINVAL
    if not gone:
        say(f"cannot write the output ({exc.strerror or 'error'})")
    # Point stdout at the null device so the interpreter's final flush cannot fail again
    # (on Windows a pipe whose reader has gone reports EINVAL rather than EPIPE).
    with contextlib.suppress(AttributeError, OSError, ValueError):
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
    return 1
