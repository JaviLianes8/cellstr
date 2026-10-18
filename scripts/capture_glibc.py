"""Print glibc's wcwidth() for every code point, run-length encoded, for the oracle test.

Run it on a Linux system with glibc, under a UTF-8 locale:

    python3 -I scripts/capture_glibc.py > tests/fixtures/glibc-wcwidth.txt

Each data line is ``FIRST LAST WIDTH`` (hex, hex, decimal) for a run of code points with
the same result; -1 means glibc does not consider the code point printable. The header
lines start with ``#`` and name the glibc version, the locale and the system.
"""

from __future__ import annotations

import ctypes
import locale
import platform
import sys
from pathlib import Path


def _system() -> str:
    release = Path("/etc/os-release")
    if release.is_file():
        for line in release.read_text(encoding="utf-8").splitlines():
            if line.startswith("PRETTY_NAME="):
                return line.split("=", 1)[1].strip('"')
    return platform.platform()


def main() -> int:
    chosen = locale.setlocale(locale.LC_CTYPE, "C.UTF-8")
    libc = ctypes.CDLL("libc.so.6")
    libc.wcwidth.argtypes = [ctypes.c_uint32]
    libc.wcwidth.restype = ctypes.c_int
    libc.gnu_get_libc_version.restype = ctypes.c_char_p
    version = libc.gnu_get_libc_version().decode("ascii")
    out = sys.stdout
    out.write(f"# glibc {version} wcwidth(), locale {chosen}, {_system()}\n")
    out.write("# FIRST LAST WIDTH, every code point U+0000..U+10FFFF\n")
    start, previous = 0, libc.wcwidth(0)
    for cp in range(1, 0x110000):
        width = libc.wcwidth(cp)
        if width != previous:
            out.write(f"{start:04X} {cp - 1:04X} {previous}\n")
            start, previous = cp, width
    out.write(f"{start:04X} 10FFFF {previous}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
