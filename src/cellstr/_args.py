"""Argument checks shared by the public functions, with short error messages.

Every message names the argument and quotes at most ``_LIMIT`` characters of a value, so a
huge or hostile argument can never produce a huge message or a second exception. Types are
read with ``type()``, which an object cannot fake the way it can fake ``__class__``.
"""

from __future__ import annotations

import operator
from typing import SupportsIndex, cast

_LIMIT = 40


def _cut(text: str) -> str:
    return text if len(text) <= _LIMIT else text[: _LIMIT - 3] + "..."


def type_name(value: object) -> str:
    """The class name of ``value``, cut short, never raising."""
    try:
        name = type(value).__name__
    except Exception:
        name = None
    return _cut(name) if type(name) is str else "object"


def show(value: object) -> str:
    """A short, safe rendering of a ``str`` or ``int`` value for an error message."""
    kind = type(value)
    if kind is bool:
        return repr(value)
    if issubclass(kind, int):
        number = cast(int, value)
        size = int.bit_length(number)
        return int.__repr__(number) if size <= 64 else f"an integer of {size} bits"
    if issubclass(kind, str):
        head = str.__getitem__(cast(str, value), slice(0, _LIMIT + 1))
        return _cut(str.__repr__(head))
    return f"a {type_name(value)} object"


def check_text(value: object, name: str = "text") -> str:
    """Return ``value`` as an exact ``str``; anything that is not a ``str`` is a TypeError."""
    kind = type(value)
    if kind is str:
        return cast(str, value)
    if issubclass(kind, str):
        # An exact copy, so methods a subclass overrides cannot change any result.
        return str.__str__(cast(str, value))
    raise TypeError(f"{name} must be a str, not {type_name(value)}")


def check_int(value: object, name: str) -> int:
    """Return ``value`` as an exact ``int``: any ``__index__`` integer except ``bool``."""
    kind = type(value)
    if kind is int:
        return cast(int, value)
    if kind is bool:
        raise TypeError(f"{name} must be an int, not bool")
    try:
        number = operator.index(cast(SupportsIndex, value))
    except TypeError:
        raise TypeError(f"{name} must be an int, not {type_name(value)}") from None
    return number if type(number) is int else int.__index__(number)


def check_width(value: object, name: str = "width") -> int:
    """Return a non-negative integer width or column."""
    number = check_int(value, name)
    if number < 0:
        raise ValueError(f"{name} must not be negative, not {show(number)}")
    return number


def check_ambiguous(value: object) -> int:
    """Return ``ambiguous`` after checking it is 1 or 2."""
    number = check_int(value, "ambiguous")
    if number not in (1, 2):
        raise ValueError(f"ambiguous must be 1 or 2, not {show(number)}")
    return number


def check_positive(value: object, name: str) -> int:
    """Return an integer of at least 1."""
    number = check_int(value, name)
    if number < 1:
        raise ValueError(f"{name} must be at least 1, not {show(number)}")
    return number


def check_tabsize(value: object) -> int | None:
    """Return ``tabsize``: None (tabs are zero-width controls) or a positive integer."""
    return None if value is None else check_positive(value, "tabsize")


def check_choice(value: object, name: str, choices: tuple[str, ...]) -> str:
    """Return ``value`` when it is one of ``choices``."""
    text = check_text(value, name)
    if text not in choices:
        allowed = ", ".join(repr(choice) for choice in choices)
        raise ValueError(f"{name} must be one of {allowed}, not {show(text)}")
    return text
