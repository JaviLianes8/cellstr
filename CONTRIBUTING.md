# Contributing

Thanks for taking the time. This project keeps a small, predictable shape.

## Setup

```
pip install -r requirements-dev.txt
python scripts/fetch_upstream.py
```

The fetch step is optional: it downloads the Unicode data files listed in
`data/ucd/MANIFEST.json` (checked against their sha256) into `data/ucd/`, which
git ignores. The generator check and the tests that need them skip until they are there.

## Before you open a pull request

- Keep public API in `src/cellstr/__init__.py`; internals live in `_`-prefixed modules.
- Add a test for the behaviour you change. Tests inject time, disk and network; they
  never touch the real thing.
- Never edit `src/cellstr/_ucd_*.py` by hand: they are generated from the fetched `data/ucd/` files
  by `python scripts/gen_ucd_tables.py` (see `data/ucd/MANIFEST.json`).
- Run `scripts/check.ps1` (format, lint, types, table freshness, tests) and make sure it
  passes. The wheel end-to-end test needs network access for the build backend;
  offline, run `pytest -m "not e2e"`.
- One logical change per commit, imperative subject line.

Open an issue first if the change is large or shifts the public API.
