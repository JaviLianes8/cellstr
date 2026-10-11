import importlib.resources
import inspect

import cellstr

PUBLIC_API: list[str] = [
    "UNICODE_VERSION",
    "cell_len",
    "cell_slice",
    "center",
    "char_width",
    "ljust",
    "rjust",
    "strip_ansi",
    "truncate",
]

EXPECTED_SIGNATURES = {
    "cell_len": "(text: 'str') -> 'int'",
    "char_width": "(char: 'str') -> 'int'",
    "strip_ansi": "(text: 'str') -> 'str'",
    "cell_slice": "(text: 'str', start: 'int' = 0, stop: 'int | None' = None) -> 'str'",
    "ljust": "(text: 'str', width: 'int', fillchar: 'str' = ' ') -> 'str'",
    "rjust": "(text: 'str', width: 'int', fillchar: 'str' = ' ') -> 'str'",
    "center": "(text: 'str', width: 'int', fillchar: 'str' = ' ') -> 'str'",
    "truncate": "(text: 'str', width: 'int', suffix: 'str' = '...') -> 'str'",
}


def test_all_lists_exactly_the_public_api() -> None:
    assert sorted(cellstr.__all__) == sorted(PUBLIC_API)


def test_every_exported_name_resolves() -> None:
    for name in cellstr.__all__:
        assert hasattr(cellstr, name)


def test_public_signatures_are_pinned() -> None:
    for name, signature in EXPECTED_SIGNATURES.items():
        assert str(inspect.signature(getattr(cellstr, name))) == signature


def test_version_is_a_three_part_string() -> None:
    parts = cellstr.__version__.split(".")
    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)


def test_the_package_ships_type_information() -> None:
    assert importlib.resources.files("cellstr").joinpath("py.typed").is_file()
