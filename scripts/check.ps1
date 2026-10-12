# Local quality gate. Run before every commit. No CI runs in the cloud.
$ErrorActionPreference = "Stop"

ruff format --check .
ruff check .
mypy --strict src tests scripts
python scripts/gen_ucd_tables.py --check
pytest
