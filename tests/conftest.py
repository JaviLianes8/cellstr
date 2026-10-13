"""Access to the Unicode data files that scripts/fetch_upstream.py fetches into data/ucd/.

The files are not committed: data/ucd/MANIFEST.json pins their URL, Unicode version, size
and sha256. Tests that read them skip while they are absent and fail if one differs.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

UCD = Path(__file__).resolve().parent.parent / "data" / "ucd"
MANIFEST: dict[str, dict[str, Any]] = json.loads(
    (UCD / "MANIFEST.json").read_text(encoding="utf-8")
)


def ucd_fetched() -> bool:
    """True when every file in the manifest is present."""
    return all((UCD / name).is_file() for name in MANIFEST)


needs_ucd = pytest.mark.skipif(
    not ucd_fetched(), reason="Unicode data not fetched; run python scripts/fetch_upstream.py"
)
