"""Filter a table by SQL WHERE text, pushed to the backend that holds it.

Decided 2026-09-27: the lazy pool is written as SQL text,
``create_pool(where=\"state = 'MA'\")``, pushed to the backend; the callable form
stays for in-memory data. duckdb is an OPTIONAL extra, ``otter[duckdb]``.

WHY SQL TEXT. A callable needs the whole table in memory before it can run. A
WHERE clause can be handed to the engine that holds the data, so only the
matching rows are ever pulled. That is the point for a warehouse-sized object:
the pool is small even when the table is not.

Two backends today:
  * a duckdb relation: the WHERE is pushed down with ``relation.filter`` and
    only the pool is materialised. The full table never is.
  * an in-memory frame: duckdb runs the WHERE over the frame and returns the
    matching ROW POSITIONS, so the pool keeps the frame's own index and
    ``attach(..., to_full=False)`` still lines up.

A BigQuery backend is a later, thin addition: no BigQuery credential was
reachable where this was built, so it could not be tested.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

INSTALL_HINT = (
    "create_pool(where=...) needs duckdb, which is an optional extra: "
    "pip install otter[duckdb]"
)

# A column name no real table uses, carrying each row's position through the
# query so the pool can be cut from the original frame with its index intact.
_POS = "__otter_row_position__"


def is_lazy(obj: Any) -> bool:
    """True for a source whose rows should stay in their engine until filtered."""
    return type(obj).__name__ == "DuckDBPyRelation" and callable(
        getattr(obj, "filter", None)
    )


def _duckdb() -> Any:
    try:
        import duckdb
    except ImportError as exc:
        raise ImportError(INSTALL_HINT) from exc
    return duckdb


def filter_lazy(relation: Any, where: str) -> pd.DataFrame:
    """Push `where` down to a duckdb relation and materialise only the matches."""
    return relation.filter(where).df()


def filter_frame(frame: pd.DataFrame, where: str) -> pd.DataFrame:
    """The rows of an in-memory frame matching SQL `where`, index preserved.

    Geometry columns are left out of what duckdb sees (it cannot read shapely
    objects) and come back untouched, because the pool is cut from `frame`.
    """
    duckdb = _duckdb()
    plain = [c for c in frame.columns if str(frame[c].dtype) != "geometry"]
    probe = pd.DataFrame(
        {c: frame[c].to_numpy() for c in plain}
    ).assign(**{_POS: np.arange(len(frame))})
    con = duckdb.connect()
    try:
        con.register("otter_pool_source", probe)
        hits = con.execute(
            f'SELECT "{_POS}" FROM otter_pool_source WHERE {where}'
        ).fetchnumpy()[_POS]
    finally:
        con.close()
    return frame.iloc[np.sort(np.asarray(hits, dtype=np.int64))].copy()
