import tomllib
from pathlib import Path


def test_pyproject_classifier_and_pytyped_marker():
    # Resolve repo root relative to this test file
    root = Path(__file__).resolve().parent.parent

    # 1) The classifier is declared in pyproject.toml
    pyproject_path = root / "pyproject.toml"
    with pyproject_path.open("rb") as f:
        pyproject = tomllib.load(f)

    classifiers = pyproject.get("project", {}).get("classifiers", [])
    assert "Typing :: Typed" in classifiers, "Typing :: Typed classifier not declared in [project].classifiers"

    # 2) The package ships the py.typed marker file
    marker_path = root / "src" / "otter" / "py.typed"
    assert marker_path.exists(), "py.typed marker file is missing in the shipped package (src/otter/py.typed)"
