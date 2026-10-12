"""Run the examples written in the public docstrings."""

from __future__ import annotations

import doctest
import importlib

import pytest

MODULES = [
    "cellstr._ansi",
    "cellstr._cells",
    "cellstr._graphemes",
    "cellstr._ops",
    "cellstr._truncate",
    "cellstr._width",
]


@pytest.mark.parametrize("name", MODULES)
def test_docstring_examples(name: str) -> None:
    result = doctest.testmod(importlib.import_module(name))
    assert result.attempted > 0
    assert result.failed == 0
