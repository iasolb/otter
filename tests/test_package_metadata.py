"""What a stranger sees on PyPI, pinned so it cannot quietly regress.

Read as text, not with tomllib: the suite runs on Python 3.10, which has none.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")


def test_the_pypi_page_links_back_to_the_repo():
    assert "[project.urls]" in PYPROJECT
    assert 'Repository = "https://github.com/iasolb/otter"' in PYPROJECT


def test_the_pypi_page_names_the_supported_pythons():
    for version in ("3.10", "3.11", "3.12"):
        assert f'"Programming Language :: Python :: {version}"' in PYPROJECT


def test_the_readme_installs_the_package_not_its_dependencies():
    # The README is the PyPI page. It used to tell strangers to pip install
    # pandas, numpy and a requirements file, and never the package itself.
    assert "pip install otter" in README
    assert "pip install -r requirements.txt" not in README
