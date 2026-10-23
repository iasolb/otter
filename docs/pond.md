# Pond API

`Pond` manages a dataset, working subsets, and the variable specification used to prepare model inputs.

## `Pond(source, handler=None, *, shapefile=False)`

Construct a pond from a CSV filepath, shapefile path, DataFrame, or GeoDataFrame. The optional `handler` function transforms the data after loading.

```python
# From a CSV with a cleaning function
def clean(df):
    df.columns = df.columns.str.lower()
    df["married"] = (df["marital_status"] == "married").astype(int)
    df = df.drop_duplicates()
    return df.dropna()

pond = Pond("data.csv", clean)

# From a CSV without cleaning
pond = Pond("data.csv")

# From a shapefile
pond = Pond("regions.shp", shapefile=True)

# From an existing DataFrame or GeoDataFrame
pond = Pond(existing_df)
pond = Pond(existing_df, clean)
```

The `handler` function receives a `pd.DataFrame` or, for shapefiles, a `gpd.GeoDataFrame`, and returns a DataFrame. Unsupported source types raise `TypeError`. The `shapefile` parameter is keyword-only.

## `create_pool(condition)`

Create a working subset of the full dataset from a boolean condition.

```python
pond.create_pool(lambda df: df["age"] > 30)
pond.create_pool(lambda df: (df["income"] > 20000) & (df["employed"] == 1))
pond.create_pool(lambda df: df["country"].isin(["US", "UK", "CA"]))
```

## `reset_pool()`

Clear the working subset and set it to `None`.

## `set_dependent(col, full=True)`

Set the dependent (outcome) variable. This call locks the source mode described in [Design Notes](design.md#design-notes).

```python
pond.set_dependent("log_income")
pond.set_dependent("log_income", full=False)
```

## `add_independents(*cols, full=True)`

Add one or more independent (predictor) variables.

```python
pond.add_independents("education", "experience", "tenure")
pond.add_independents("education", "experience", full=False)
```

## `add_controls(*cols, full=True)`

Add one or more control variables.

```python
pond.add_controls("female", "married", "region_code")
pond.add_controls("female", "married", full=False)
```

## `get_X()` / `get_y()`

Return the design matrix as a `pd.DataFrame` or the dependent variable as a `pd.Series`.

## `get_spec()`

Return a frozen `ModelSpec` snapshot of the current variable specification. It contains copies of the design matrix, dependent variable, column name metadata, and source DataFrame. The snapshot does not change after creation.

```python
spec = pond.get_spec()

spec.X              # DataFrame: same as get_X()
spec.y              # Series: same as get_y()
spec.independents   # ("education", "experience")
spec.controls       # ("female",)
spec.dependent      # "log_income"
spec.columns        # ("education", "experience", "female")
spec.all_columns    # ("log_income", "education", "experience", "female")
spec.source_label   # "full" or "subset"
spec.n              # number of observations
spec.data           # copy of the source DataFrame (for distribution fitting)
```

`ModelSpec` connects `Pond` to the simulation module. Pass it to `Simulation.from_spec()` to build a data-driven Monte Carlo simulation.

## `attach(col_name, series, to_full=True, quiet=False)`

Attach a precomputed Series to the full dataset or subset.

```python
from otter import square

pond.attach("age_sq", square(pond.data["age"]))
pond.attach("age_sq", square(pond.pool["age"]), to_full=False)
```

## `normalize_and_attach(source_col, normalizing_function, new_colname, full=True)`

Apply a single-column transformation and attach the result.

```python
from otter import log_transform, z_score, mean_center, min_max_scale

pond.normalize_and_attach("income", log_transform, "log_income")
pond.normalize_and_attach("gpa", z_score, "gpa_z")
pond.normalize_and_attach("age", mean_center, "age_centered")
pond.normalize_and_attach("score", min_max_scale, "score_scaled")
pond.normalize_and_attach("wage", log_transform, "log_wage", full=False)
```

## `calculate_and_attach(source_cols, func, new_colname, full=True)`

Apply a multi-column transformation and attach the result. The function receives a DataFrame subset containing the specified columns.

```python
from otter import interaction, row_mean, row_sum, safe_ratio

pond.calculate_and_attach(["education", "experience"], interaction, "edu_x_exp")
pond.calculate_and_attach(["math", "reading", "science"], row_mean, "avg_score")
pond.calculate_and_attach(["q1", "q2", "q3", "q4"], row_sum, "annual_total")
pond.calculate_and_attach(
    ["revenue", "visits"],
    safe_ratio("revenue", "visits"),
    "rev_per_visit",
    full=False
)
```

## `clear_caches()`

Clear the dependent, independent, and control variables and the source mode lock to define a new specification without reinitializing.
