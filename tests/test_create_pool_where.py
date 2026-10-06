"""create_pool(where=...): SQL text, pushed to the backend that holds the data.

The point of the lazy path is that the FULL table is never pulled when only the
pool is used, so the relation test asserts that directly rather than trusting
the row count.
"""

from __future__ import annotations

import sys

import duckdb
import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import Point

from otter.pond import Pond


def _frame() -> pd.DataFrame:
    return pd.DataFrame(
        {"state": ["MA", "NY", "MA", "VT"], "age": [25, 40, 52, 33]},
        index=[10, 11, 12, 13],
    )


class TestCreatePoolWhere:
    def test_where_on_a_frame_keeps_the_frames_own_index(self) -> None:
        pond = Pond(_frame())
        pond.create_pool(where="state = 'MA'")
        assert list(pond.pool.index) == [10, 12]
        assert list(pond.pool["age"]) == [25, 52]

    def test_where_on_a_frame_lines_up_with_attach_to_the_pool(self) -> None:
        pond = Pond(_frame())
        pond.create_pool(where="age > 30")
        pond.attach("double", pond.data["age"] * 2, to_full=False, quiet=True)
        assert list(pond.pool["double"]) == [80, 104, 66]

    def test_where_on_a_relation_never_pulls_the_full_table(self) -> None:
        con = duckdb.connect()
        rel = con.sql(
            "SELECT * FROM (VALUES ('MA', 25), ('NY', 40), ('MA', 52)) t(state, age)"
        )
        pond = Pond(rel)
        pond.create_pool(where="state = 'MA'")
        assert sorted(pond.pool["age"]) == [25, 52]
        assert pond._data is None, "the full table was materialised for a pool"

    def test_a_relations_full_table_is_pulled_on_first_use(self) -> None:
        con = duckdb.connect()
        rel = con.sql("SELECT * FROM range(5) t(n)")
        pond = Pond(rel)
        assert len(pond.data) == 5

    def test_a_pool_from_where_feeds_the_model_spec(self) -> None:
        pond = Pond(_frame())
        pond.create_pool(where="state = 'MA'")
        pond.set_dependent("age", full=False)
        pond.add_independents("age", full=False)
        spec = pond.get_spec()
        assert spec.n == 2 and spec.source_label == "pool"

    def test_geometry_columns_survive_a_where(self) -> None:
        gdf = gpd.GeoDataFrame(
            {"state": ["MA", "NY"]}, geometry=[Point(0, 0), Point(1, 1)]
        )
        pond = Pond(gdf)
        pond.create_pool(where="state = 'NY'")
        assert list(pond.pool.geometry) == [Point(1, 1)]

    def test_condition_and_where_together_or_neither_is_refused(self) -> None:
        pond = Pond(_frame())
        with pytest.raises(ValueError):
            pond.create_pool(lambda df: df["age"] > 1, where="age > 1")
        with pytest.raises(ValueError):
            pond.create_pool()

    def test_missing_duckdb_names_the_extra_to_install(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setitem(sys.modules, "duckdb", None)
        pond = Pond(_frame())
        with pytest.raises(ImportError, match=r"otter\[duckdb\]"):
            pond.create_pool(where="age > 1")

    def test_the_duckdb_extra_is_declared(self) -> None:
        # tomllib is stdlib only from 3.11; on 3.10 assert against the text.
        from pathlib import Path

        text = (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(encoding="utf-8")
        if sys.version_info >= (3, 11):
            import tomllib

            extras = tomllib.loads(text)["project"]["optional-dependencies"]
            assert any(req.startswith("duckdb") for req in extras.get("duckdb", []))
        else:
            assert '\nduckdb = ["duckdb' in text

    def test_the_callable_form_still_works(self) -> None:
        pond = Pond(_frame())
        pond.create_pool(lambda df: df["state"] == "VT")
        assert list(pond.pool.index) == [13]
