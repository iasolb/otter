import sys
from pathlib import Path


def _classifier_declared(pyproject: Path, classifier: str) -> bool:
    """Is this classifier declared in pyproject.toml?

    `tomllib` IS STDLIB ONLY FROM 3.11 and this package supports >=3.10, so a
    bare `import tomllib` failed COLLECTION on the oldest Python it claims to
    support. Measured on CI 2026-09-17: 3.11 green, 3.10 red with
    `ModuleNotFoundError: No module named 'tomllib'`, and because the publish
    job is gated on the tests, the release never ran at all. This repo's CI had
    been red on `main` since 2026-09-14 for exactly this and nothing looked.

    On 3.10 this asserts against the file TEXT rather than skipping. A skipped
    test here would read as green while asserting nothing.
    """
    if sys.version_info >= (3, 11):
        import tomllib

        with pyproject.open("rb") as fh:
            data = tomllib.load(fh)
        return classifier in data.get("project", {}).get("classifiers", [])
    return classifier in pyproject.read_text(encoding="utf-8")


def test_pyproject_classifier_and_pytyped_marker():
    # Resolve repo root relative to this test file
    root = Path(__file__).resolve().parent.parent

    # 1) The classifier is declared in pyproject.toml
    pyproject_path = root / "pyproject.toml"
    assert _classifier_declared(pyproject_path, "Typing :: Typed"), \
        "Typing :: Typed classifier not declared in [project].classifiers"

    # 2) The package ships the py.typed marker file
    marker_path = root / "src" / "otter" / "py.typed"
    assert marker_path.exists(), "py.typed marker file is missing in the shipped package (src/otter/py.typed)"
