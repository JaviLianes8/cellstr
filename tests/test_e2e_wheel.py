"""Build the real wheel, install it into a throwaway venv and drive the installed script.

Nothing is mocked: this needs network access for pip to fetch the build backend.
"""

from __future__ import annotations

import os
import subprocess
import sys
import venv
import zipfile
from pathlib import Path

import pytest

import cellstr

ROOT = Path(__file__).resolve().parent.parent
FAMILY = "\U0001f468\u200d\U0001f469\u200d\U0001f467"


def _run(cmd: list[str], stdin: bytes = b"") -> subprocess.CompletedProcess[bytes]:
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    return subprocess.run(cmd, input=stdin, capture_output=True, env=env, timeout=600, check=False)


@pytest.mark.e2e
def test_wheel_installs_and_the_script_works(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    built = _run(
        [sys.executable, "-m", "pip", "wheel", "--no-deps", "-q", "-w", str(dist), str(ROOT)]
    )
    assert built.returncode == 0, built.stderr.decode(errors="replace")
    wheels = list(dist.glob("cellstr-*.whl"))
    assert [w.name for w in wheels] == [f"cellstr-{cellstr.__version__}-py3-none-any.whl"]
    names = zipfile.ZipFile(wheels[0]).namelist()
    assert "cellstr/py.typed" in names and "cellstr/_ucd_part1.py" in names
    assert any(n.endswith("licenses/LICENSE-UNICODE") for n in names)
    assert not [n for n in names if n.startswith(("data/", "tests/", "scripts/"))]

    env_dir = tmp_path / "venv"
    venv.EnvBuilder(with_pip=True, clear=True).create(env_dir)
    bindir = env_dir / ("Scripts" if os.name == "nt" else "bin")
    python = bindir / ("python.exe" if os.name == "nt" else "python")
    script = bindir / ("cellstr.exe" if os.name == "nt" else "cellstr")
    installed = _run([str(python), "-m", "pip", "install", "-q", "--no-index", str(wheels[0])])
    assert installed.returncode == 0, installed.stderr.decode(errors="replace")
    assert script.is_file()

    text = f"ab\u4f60\u597d\n{FAMILY}\n\x1b[31mred\x1b[0m\n"
    done = _run([str(script), "measure"], text.encode())
    assert (done.returncode, done.stdout) == (0, b"6\n2\n3\n")
    done = _run([str(script), "truncate", "5"], "\u4f60\u597d\u4e16\u754c\n".encode())
    assert done.stdout == "\u4f60...\n".encode()
    done = _run([str(script), "fit", "4", "--align", "right"], f"{FAMILY}\n".encode())
    assert done.stdout == f"  {FAMILY}\n".encode()
    done = _run([str(script), "slice", "1", "3"], f"x{FAMILY}y\n".encode())
    assert done.stdout == f"{FAMILY}\n".encode()
    failed = _run([str(script), "pad", "3", "--fill", "\u4f60"], b"abc\n")
    assert failed.returncode == 1 and b"error" in failed.stderr and failed.stdout == b""
    version = _run([str(script), "--version"])
    assert version.stdout.strip() == f"cellstr {cellstr.__version__}".encode()
    helped = _run([str(script), "--help"])
    assert helped.returncode == 0 and b"examples:" in helped.stdout

    probe = "import cellstr; print(cellstr.UNICODE_VERSION, cellstr.__file__)"
    shown = _run([str(python), "-c", probe]).stdout.decode()
    assert shown.startswith(f"{cellstr.UNICODE_VERSION} ") and str(env_dir) in shown
