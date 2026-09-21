"""Tests for the widened Pond door: any in-memory tabular object."""

import pandas as pd
import pytest

from otter import Pond
from otter.pond import _to_frame


class _FakeArrowTable:
    """Stands in for pyarrow.Table / polars / duckdb: exposes to_arrow()."""

    def __init__(self, frame):
        self._frame = frame

    def to_arrow(self):
        return self

    def to_pandas(self):
        return self._frame


class _FakeBigQueryResult:
    """Stands in for a BigQuery RowIterator, which names it to_dataframe()."""

    def __init__(self, frame):
        self._frame = frame

    def to_dataframe(self):
        return self._frame


class _NotTabular:
    pass


def _sample_frame():
    return pd.DataFrame({"a": [1, 2, 3], "b": [4.0, 5.0, 6.0]})


def test_to_frame_passes_a_dataframe_straight_through():
    df = _sample_frame()
    assert _to_frame(df) is df


def test_to_frame_prefers_arrow_when_an_object_offers_it():
    df = _sample_frame()
    assert _to_frame(_FakeArrowTable(df)).equals(df)


def test_to_frame_reads_a_bigquery_style_to_dataframe():
    df = _sample_frame()
    assert _to_frame(_FakeBigQueryResult(df)).equals(df)


def test_to_frame_accepts_a_dict_of_columns():
    assert list(_to_frame({"a": [1, 2]}).columns) == ["a"]


def test_to_frame_accepts_a_list_of_row_dicts():
    out = _to_frame([{"a": 1}, {"a": 2}])
    assert len(out) == 2 and list(out.columns) == ["a"]


def test_to_frame_returns_none_for_something_that_is_not_tabular():
    # NONE IS A REAL ANSWER, never an empty frame: "not a table" and "an
    # empty table" are different facts and Pond reports them differently.
    assert _to_frame(_NotTabular()) is None
    assert _to_frame(42) is None
    assert _to_frame(None) is None


def test_pond_accepts_an_arrow_style_object_end_to_end():
    pond = Pond(_FakeArrowTable(_sample_frame()))
    assert len(pond.data) == 3
    pond.set_dependent("a")
    pond.add_independents("b")
    assert pond.get_spec().n == 3


def test_pond_still_refuses_a_non_tabular_source_and_says_its_type():
    pond = Pond(_NotTabular())
    assert len(pond.data) == 0
    with pytest.raises(Exception):
        pond.set_dependent("a")
