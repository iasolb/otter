# Pond API

### `Pond(source, handler=None, *, shapefile=False)`

Constructor. Accepts a CSV filepath, shapefile path, DataFrame, or
GeoDataFrame. The optional `handler` function transforms the data after
loading.

```python
# From a CSV with a cleaning function
def clean(df):
    df.columns = df.columns.str.lower()
    df["married"] = (df["marital_status"] == "married").astype(int)
    df = df.drop_duplicates()
    return df.dropna(subset=["wage"])  

pond = Pond("data.csv", clean)

# From a CSV without cleaning
pond = Pond("data.csv")

# From a shapefile
pond = Pond("regions.shp", shapefile=True)

# From an existing DataFrame or GeoDataFrame
pond = Pond(existing_df)
pond = Pond(existing_df, clean)
```

The `handler` function receives a `pd.DataFrame` (or `gpd.GeoDataFrame` for
shapefiles) and must return one. If the source type is unsupported, a
`TypeError` is raised. The `shapefile` parameter is keyword-only.

### `create_pool(condition)`

Creates a working subset of the full dataset based on a boolean condition.

```python
pond.create_pool(lambda df: df["age"] > 30)
pond.create_pool(lambda df: (df["income"] > 20000) & (df["employed"] == 1))
pond.create_pool(lambda df: df["country"].isin(["US", "UK", "CA"]))
```

### `reset_pool()`

Clears the working subset back to `None`.

### `set_dependent(col, full=True)`

Sets the dependent (outcome) variable. Locks the source mode (see Design
Notes).

```python
pond.set_dependent("log_income")
pond.set_dependent("log_income", full=False)
```

### `add_independents(*cols, full=True)`

Adds one or more independent (predictor) variables.

```python
pond.add_independents("education", "experience", "tenure")
pond.add_independents("education", "experience", full=False)
```

### `add_controls(*cols, full=True)`

Adds one or more control variables.

```python
pond.add_controls("female", "married", "region_code")
pond.add_controls("female", "married", full=False)
```

### `get_X()` / `get_y()`

Returns the design matrix as a `pd.DataFrame` or the dependent variable as
a `pd.Series`.

### `get_spec()`

Returns a frozen `ModelSpec` snapshot of the current variable specification.
Contains copies of the design matrix, dependent variable, column name
metadata, and the source DataFrame. Nothing mutates after creation.

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

`ModelSpec` is the bridge between `Pond` and the simulation
module: pass it to `Simulation.from_spec()` to build a data-driven Monte
Carlo simulation.

### `attach(col_name, series, to_full=True, quiet=False)`

Attaches a precomputed Series to the full dataset or subset.

```python
from otter import square

pond.attach("age_sq", square(pond.data["age"]))
pond.attach("age_sq", square(pond.pool["age"]), to_full=False)
```

### `normalize_and_attach(source_col, normalizing_function, new_colname, full=True)`

Applies a single-column transformation and attaches the result.

```python
from otter import log_transform, z_score, mean_center, min_max_scale

pond.normalize_and_attach("income", log_transform, "log_income")
pond.normalize_and_attach("gpa", z_score, "gpa_z")
pond.normalize_and_attach("age", mean_center, "age_centered")
pond.normalize_and_attach("score", min_max_scale, "score_scaled")
pond.normalize_and_attach("wage", log_transform, "log_wage", full=False)
```

### `calculate_and_attach(source_cols, func, new_colname, full=True)`

Applies a multi-column transformation and attaches the result. The function
receives a DataFrame subset of the specified columns.

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

### `clear_caches()`

Clears the dependent, independents, controls, and source mode lock so you
can set up a new specification without reinitializing.
