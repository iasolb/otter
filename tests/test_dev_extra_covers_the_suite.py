"""The dev extra installs everything the suite imports, so CI can collect it.

CI installs `.[dev]`, and it was red from 2026-09-28 because
tests/test_create_pool_where.py imports duckdb, which only the `duckdb` extra
installed. Read as text, not with tomllib, because CI also runs Python 3.10.
"""

import re
from pathlib import Path

PYPROJECT = Path(__file__).resolve().parents[1] / "pyproject.toml"


def _dev_extra() -> str:
    found = re.search(r"^dev = \[(.*)\]$", PYPROJECT.read_text(encoding="utf-8"), re.M)
    assert found, "pyproject.toml has no one-line dev extra"
    return found.group(1)


def test_the_dev_extra_brings_duckdb() -> None:
    assert '"duckdb' in _dev_extra()


def test_the_dev_extra_still_brings_pytest() -> None:
    assert '"pytest' in _dev_extra()
