"""ModelSpec.to_numpy: numpy is otter's compute type, the DataFrame its boundary."""

import numpy as np
import pandas as pd
import pytest

from otter.pond import ModelSpec


def _spec(X: pd.DataFrame, y=None, dependent=None) -> ModelSpec:
    return ModelSpec(X=X, y=y, independents=tuple(X.columns), controls=(),
                     dependent=dependent, source_label="full", n=len(X),
                     data=X.copy())


def test_x_and_y_come_back_as_float_arrays():
    X = pd.DataFrame({"a": [1, 2, 3], "b": [0.5, 1.5, 2.5]})
    y = pd.Series([1, 0, 1], name="t")
    Xn, yn = _spec(X, y, "t").to_numpy()
    assert isinstance(Xn, np.ndarray) and Xn.dtype == np.float64
    assert Xn.shape == (3, 2)
    assert Xn[:, 1].tolist() == [0.5, 1.5, 2.5]
    assert isinstance(yn, np.ndarray) and yn.tolist() == [1.0, 0.0, 1.0]


def test_no_dependent_gives_no_y():
    X = pd.DataFrame({"a": [1.0, 2.0]})
    _, yn = _spec(X).to_numpy()
    assert yn is None


def test_columns_keep_the_specs_order():
    X = pd.DataFrame({"b": [10, 20], "a": [1, 2]})
    Xn, _ = _spec(X).to_numpy()
    assert Xn[:, 0].tolist() == [10.0, 20.0]


def test_a_text_column_is_refused_by_name():
    X = pd.DataFrame({"a": [1, 2], "name": ["x", "y"]})
    with pytest.raises(ValueError, match="name"):
        _spec(X).to_numpy()


def test_changing_the_array_never_changes_the_spec():
    X = pd.DataFrame({"a": [1.0, 2.0]})
    spec = _spec(X)
    Xn, _ = spec.to_numpy()
    Xn[0, 0] = 99.0
    assert spec.X["a"].tolist() == [1.0, 2.0]
