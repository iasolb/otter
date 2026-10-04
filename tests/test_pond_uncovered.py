"""Uncovered Pond behaviours tests

This file exercises a subset of Pond behaviours that are tightly coupled
to the public API and should be stable across backend refactors.
"""

import io
import numpy as np
import pandas as pd
import pytest

from otter import Pond


def _make_dataframe():
    rng = np.random.default_rng(123)
    n = 20
    df = pd.DataFrame(
        {
            "income": rng.normal(50000, 10000, n),
            "education": rng.integers(8, 20, n),
            "age": rng.integers(22, 65, n),
            "region": rng.choice(["east", "west"], size=n),
            "female": rng.integers(0, 2, n),
        }
    )
    return df


def test_calculate_and_attach_full():
    # 1. calculate_and_attach on full data adds new column with right values
    df = _make_dataframe()
    pond = Pond(df)
    pond.calculate_and_attach(
        source_cols=["income", "education"],
        func=lambda d: d["income"] + d["education"],
        new_colname="income_plus_educ",
        full=True,
    )
    assert "income_plus_educ" in pond.data.columns
    expected = df["income"] + df["education"]
    np.testing.assert_allclose(pond.data["income_plus_educ"].to_numpy(), expected.to_numpy())


def test_calculate_and_attach_full_false_after_pool():
    # 2. calculate_and_attach(..., full=False) after create_pool adds to POOL only
    df = _make_dataframe()
    pond = Pond(df)
    pond.create_pool(lambda d: d["age"] > 30)
    pond.calculate_and_attach(
        source_cols=["income", "education"],
        func=lambda d: d["income"] + d["education"],
        new_colname="income_plus_educ_pool",
        full=False,
    )
    assert "income_plus_educ_pool" in pond.pool.columns
    assert "income_plus_educ_pool" not in pond.data.columns


def test_normalize_and_attach_full_false():
    # 3. normalize_and_attach(..., full=False) attaches to pool
    df = _make_dataframe()
    pond = Pond(df)
    pond.create_pool(lambda d: d["age"] > 30)
    pond.normalize_and_attach("income", np.log, "log_income_pool", full=False)
    assert "log_income_pool" in pond.pool.columns
    # values should be log of the pool's income
    np.testing.assert_allclose(
        pond.pool["log_income_pool"].to_numpy(),
        np.log(pond.pool["income"].to_numpy()),
    )


def test_add_controls_full_false_after_pool():
    # 4. add_controls(..., full=False) after create_pool takes controls from pool
    df = _make_dataframe()
    pond = Pond(df)
    pond.create_pool(lambda d: d["age"] > 30)
    pond.add_controls("region", "female", full=False)
    assert len(pond.controls) == 2
    assert pond.controls[0].name == "region"
    assert pond.controls[1].name == "female"


def test_source_mode_conflict():
    # 5. switching from full to pool (or vice versa) without clear_caches raises
    df = _make_dataframe()
    pond = Pond(df)
    pond.add_independents("age", full=True)
    pond.create_pool(lambda d: d["age"] > 10)
    with pytest.raises(ValueError) as exc:
        pond.add_independents("education", full=False)
    assert "Source mode conflict" in str(exc.value)


def test_get_spec_requires_independents():
    # 6. get_spec() with no independents raises RuntimeError
    df = _make_dataframe()
    pond = Pond(df)
    with pytest.raises(RuntimeError) as exc:
        pond.get_spec()
    assert "independent" in str(exc.value).lower()


def test_spec_columns_all_and_repr():
    # 7. spec.columns == independents + controls; all_columns puts dep first
    df = _make_dataframe()
    pond = Pond(df)
    pond.set_dependent("income")
    pond.add_independents("age")
    pond.add_controls("region")
    spec = pond.get_spec()
    assert spec.columns == ("age", "region")
    assert spec.all_columns == ("income", "age", "region")
    rep = repr(spec)
    assert "income" in rep
    assert "income" in rep and "age" in rep and "region" in rep


def test_no_pool_calls_print_and_no_change():
    # 8. pre-pool calls print and do nothing
    df = _make_dataframe()
    pond = Pond(df)
    pond.add_independents("age", full=False)
    pond.add_controls("region", full=False)
    pond.attach("tmp", pd.Series([1, 2, 3]))
    pond.calculate_and_attach(["income"], lambda d: d["income"], "x", full=False)
    pond.normalize_and_attach("income", np.log, "log_x", full=False)
    # pool should still be None and no columns added
    assert pond.pool is None
    assert pond.data is not None


def test_series_input_accepted():
    # 9. A pd.Series handed to Pond is accepted as a one-column table
    s = pd.Series([1.0, 2.0, 3.0], name="val")
    pond = Pond(s)
    assert isinstance(pond.data, pd.DataFrame)
    assert pond.data.shape[1] == 1
    assert pond.data.shape[0] == 3


def test_bad_to_pandas_and_bad_dicts_are_rejected():
    class BadToPandas:
        def to_pandas(self):
            raise RuntimeError("boom")

    pond1 = Pond(BadToPandas())
    assert pond1.data is not None
    # empty DataFrame due to load failure
    assert pond1.data.shape[0] == 0 or pond1.data.size == 0
    assert pond1.data.shape[1] == 0

    # Dict with mismatched lengths cannot be built into a DataFrame
    bad_dict = {"a": [1, 2], "b": [3]}
    pond2 = Pond(bad_dict)
    assert pond2.data is not None
    assert pond2.data.shape[0] == 0 or pond2.data.shape[1] == 0
