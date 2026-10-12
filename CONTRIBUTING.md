# Contributing

Thanks for taking the time. This project keeps a small, predictable shape.

## Setup

```
pip install -r requirements-dev.txt
```

## Before you open a pull request

- Keep public API in `src/cellstr/__init__.py`; internals live in `_`-prefixed modules.
- Add a test for the behaviour you change. Tests inject time, disk and network; they
  never touch the real thing.
- Never edit `src/cellstr/_ucd_*.py` by hand: they are generated from `data/ucd/` by
  `python scripts/gen_ucd_tables.py` (see `data/ucd/SOURCES.txt`).
- Run `scripts/check.ps1` (format, lint, types, table freshness, tests) and make sure it
  passes. The wheel end-to-end test needs network access for the build backend;
  offline, run `pytest -m "not e2e"`.
- One logical change per commit, imperative subject line.

Open an issue first if the change is large or shifts the public API.
