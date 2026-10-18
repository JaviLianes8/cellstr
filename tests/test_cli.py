"""Drive the command line tool in a real child process (``python -m cellstr``)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import cellstr

SRC = Path(__file__).resolve().parent.parent / "src"
FAMILY = "\U0001f468\u200d\U0001f469\u200d\U0001f467"


def run(*args: str, stdin: bytes = b"") -> subprocess.CompletedProcess[bytes]:
    env = dict(os.environ, PYTHONPATH=str(SRC))
    return subprocess.run(
        [sys.executable, "-m", "cellstr", *args],
        input=stdin,
        capture_output=True,
        env=env,
        timeout=60,
        check=False,
    )


def test_measure_prints_one_width_per_line() -> None:
    done = run("measure", stdin=f"abc\n\u4f60\u597d\r\n{FAMILY}\n\x1b[31mred\x1b[0m".encode())
    assert (done.returncode, done.stdout, done.stderr) == (0, b"3\n4\n2\n3\n", b"")


def test_measure_max_and_policies() -> None:
    assert run("measure", "--max", stdin=b"a\nabcd\nab\n").stdout == b"4\n"
    assert run("measure", "--max", stdin=b"").stdout == b"0\n"
    assert run("measure", "--ambiguous", "2", stdin="\u03b1\u03b2\n".encode()).stdout == b"4\n"
    assert run("measure", "--tabsize", "4", stdin=b"a\tb\n").stdout == b"5\n"


def test_truncate_keeps_line_endings_and_positions() -> None:
    done = run("truncate", "8", stdin=b"hello world\r\nshort\nlast line here")
    assert done.stdout == b"hello...\r\nshort\nlast ..."
    done = run("truncate", "12", "--position", "middle", stdin=b"/usr/local/lib/python\n")
    assert done.stdout == b"/usr/...thon\n"
    done = run("truncate", "3", "-s", "~", "--position", "start", stdin=b"abcdef\n")
    assert done.stdout == b"~ef\n"


def test_pad_and_fit_align_by_cells() -> None:
    assert run("pad", "4", "--align", "right", stdin="\u4f60\n".encode()).stdout == (
        "  \u4f60\n".encode()
    )
    assert run("pad", "5", "--fill", ".", "--align", "center", stdin=b"ab\n").stdout == b".ab..\n"
    done = run("fit", "6", stdin="name\n\u5f20\u4f1f\u5f20\u4f1f\nlonger name\n".encode())
    assert done.stdout == "name  \n\u5f20... \nlon...\n".encode()


def test_slice_keeps_escapes() -> None:
    done = run("slice", "4", stdin=b"\x1b[31mred text\x1b[0m\n")
    assert done.stdout == b"\x1b[31mtext\x1b[0m\n"
    assert run("slice", "1", "3", stdin=b"abcdef\n").stdout == b"bc\n"


def test_usage_errors_go_to_stderr_with_status_two() -> None:
    usage = [
        ("truncate", "-1"),
        ("truncate", "x"),
        ("pad", "3", "--fill", "ab"),
        ("fit", "3", "--fill", "─", "--ambiguous", "2"),
        ("truncate", "3", "-s", "a\tb"),
        ("slice", "5", "2"),
        ("measure", "--tabsize", "0"),
        ("nope",),
        (),
    ]
    for args in usage:
        done = run(*args, stdin=b"abc\n")
        assert done.returncode == 2, args
        assert done.stdout == b"" and b"error" in done.stderr, args


def test_unreadable_input_is_status_one() -> None:
    bad = run("measure", stdin=b"ok\n\xff\n")
    assert (bad.returncode, bad.stdout) == (1, b"")
    expected = "cellstr: error: standard input is not valid UTF-8 (byte 0xff at offset 3)"
    assert bad.stderr.decode().splitlines() == [expected]


def test_help_shows_runnable_examples_and_version() -> None:
    done = run("--help")
    assert done.returncode == 0
    for command in ("measure", "truncate", "pad", "fit", "slice"):
        assert f"| cellstr {command}" in done.stdout.decode()
    for command in ("measure", "truncate", "pad", "fit", "slice"):
        assert b"example:" in run(command, "--help").stdout
    assert run("--version").stdout.strip() == f"cellstr {cellstr.__version__}".encode()


def test_parser_defaults() -> None:
    from cellstr._cli import build_parser

    parser = build_parser()
    args = parser.parse_args(["fit", "3", "--align", "right"])
    assert (args.width, args.align, args.suffix) == (3, "right", "...")
