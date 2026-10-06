"""Every test imports only what the oldest supported Python (3.10) has.

A bare `import tomllib` (stdlib from 3.11) turned CI's 3.10 leg red twice,
2026-09-17 and 2026-10-04, and the publish job is gated on the tests, so no
release could run. A local run on a newer Python cannot see it, so this reads
the test sources instead: such an import must sit under a
`sys.version_info` check.
"""

import ast
from pathlib import Path

TESTS = Path(__file__).resolve().parent
NEWER_THAN_310 = {"tomllib"}


def _bare_imports(node: ast.AST, guarded: bool = False) -> list[int]:
    """Line numbers of NEWER_THAN_310 imports not under a version check."""
    if isinstance(node, ast.If) and "version_info" in ast.unparse(node.test):
        found: list[int] = []
        for child in node.body:
            found += _bare_imports(child, True)
        for child in node.orelse:
            found += _bare_imports(child, guarded)
        return found
    found = []
    if not guarded and isinstance(node, (ast.Import, ast.ImportFrom)):
        names = (
            [alias.name for alias in node.names]
            if isinstance(node, ast.Import)
            else [node.module or ""]
        )
        if any(name.split(".")[0] in NEWER_THAN_310 for name in names):
            found.append(node.lineno)
    for child in ast.iter_child_nodes(node):
        found += _bare_imports(child, guarded)
    return found


def test_no_test_imports_a_module_newer_than_310_unguarded() -> None:
    offenders = [
        f"{path.name}:{line}"
        for path in sorted(TESTS.rglob("*.py"))
        for line in _bare_imports(ast.parse(path.read_text(encoding="utf-8")))
    ]
    assert not offenders, offenders


def test_the_check_catches_a_bare_import() -> None:
    assert _bare_imports(ast.parse("def f():\n    import tomllib\n")) == [2]


def test_the_check_allows_a_guarded_import() -> None:
    src = "import sys\nif sys.version_info >= (3, 11):\n    import tomllib\n"
    assert _bare_imports(ast.parse(src)) == []


def test_the_else_branch_is_not_guarded() -> None:
    src = "import sys\nif sys.version_info >= (3, 11):\n    pass\nelse:\n    import tomllib\n"
    assert _bare_imports(ast.parse(src)) == [5]
