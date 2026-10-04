import pytest
import pandas as pd
import numpy as np
from otter import Pond


def _base_df():
    # Simple numeric dataframe with a few columns used in tests
    return pd.DataFrame({
        "a": [1, 2, 3],
        "b": [10, 20, 30],
        "c": [0.5, 0.7, 0.2],
        "d": [5, 6, 7],
    })


def test_calculate_and_attach_full():
    df = _base_df()
    pond = Pond(df)
    pond.calculate_and_attach(["a", "b"], lambda dfm: dfm["a"] + dfm["b"], "sum_ab", full=True)
    assert "sum_ab" in pond.data.columns
    assert (pond.data["sum_ab"] == pond.data["a"] + pond.data["b"]).all()


def test_calculate_and_attach_pool_after_create_pool():
    df = _base_df()
    pond = Pond(df)
    # create pool with condition on 'a'
    pond.create_pool(condition=lambda d: d["a"] > 1)
    pond.calculate_and_attach(["a", "b"], lambda d: d["a"] * 2, "twice_a", full=False)
    # pool should have the new column with values defined on the pool rows
    assert "twice_a" in pond.pool.columns
    assert (pond.pool["twice_a"] == pond.pool["a"] * 2).all()


def test_normalize_and_attach_pool_full_false():
    df = _base_df()
    pond = Pond(df)
    pond.create_pool(condition=lambda d: d["a"] > 0)
    pond.normalize_and_attach("a", lambda s: s / s.max(), "a_norm", full=False)
    assert "a_norm" in pond.pool.columns
    # verify normalization on the pool only
    pool = pond.pool
    expected = pool["a"] / pool["a"].max()
    assert np.allclose(pool["a_norm"].to_numpy(), expected.to_numpy())


def test_add_controls_after_create_pool():
    df = _base_df()
    pond = Pond(df)
    pond.create_pool(condition=lambda d: d["a"] > 0)
    pond.normalize_and_attach("a", lambda s: s, "noop", full=False)
    pond.add_controls("a_norm", full=False)
    # The controls should include the Series named 'a_norm' from the pool
    assert pond.controls and pond.controls[-1].name == "a_norm"


def test_source_mode_conflict_raises():
    df = _base_df()
    pond = Pond(df)
    # start in full mode by setting dependent from full data
    pond.set_dependent("d", full=True)
    # now try to set another variable from pool without clearing caches
    with pytest.raises(ValueError) as exc:
        pond.set_dependent("a", full=False)
    assert "Source mode conflict" in str(exc.value)


def test_get_spec_no_independents_raises():
    df = _base_df()
    pond = Pond(df)
    with pytest.raises(RuntimeError):
        pond.get_spec()


def test_spec_columns_and_all_columns_and_repr():
    df = _base_df()
    pond = Pond(df)
    pond.add_independents("a", "b")
    pond.add_controls("c")
    pond.set_dependent("d", full=True)
    spec = pond.get_spec()
    # columns should be independents + controls
    assert spec.columns == ("a", "b") + ("c",)
    # all_columns should start with dependent when set
    assert spec.all_columns[0] == spec.dependent
    # repr should mention dependent and lists of independents and controls
    rep = repr(spec)
    assert "dependent" in rep
    assert "independents" in rep or "independents" in rep
    assert "ModelSpec" in rep


def test_no_valid_dataset_before_pool_prints():
    df = _base_df()
    pond = Pond(df)
    # before any pool, trying to add independents with full=False
    pond2 = Pond(df)
    pond2.add_independents("a", full=False)  # should print and do nothing
    # no pool and no independents yet
    assert pond2.independents == []


def test_series_input_accepted():
    s = pd.Series([1, 2, 3], name="val")
    pond = Pond(s)
    assert isinstance(pond.data, pd.DataFrame)
    assert list(pond.data.columns) == ["val"]


def test_bad_to_pandas_and_bad_dict_handling():
    class BadLoader:
        def to_pandas(self):
            raise RuntimeError("boom")

    # 1) Bad object with to_pandas raising
    pond_bad = Pond(BadLoader())
    # data should be an empty DataFrame due to load failure
    assert isinstance(pond_bad.data, pd.DataFrame)
    assert pond_bad.data.shape[0] == 0
    # 2) dict with incompatible column lengths should be refused rather than half-loaded
    bad_dict = {"a": [1, 2], "b": [3]}  # mismatched lengths
    pond_bad_dict = Pond(bad_dict)
    assert isinstance(pond_bad_dict.data, pd.DataFrame)
    assert pond_bad_dict.data.shape[0] == 0
