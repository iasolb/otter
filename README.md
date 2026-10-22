![PyPI version](https://img.shields.io/pypi/v/otter)
![Python versions](https://img.shields.io/pypi/pyversions/otter)
![License](https://img.shields.io/badge/License-MIT-blue.svg)
![Tests](https://github.com/iasolb/otter/actions/workflows/tests.yml/badge.svg)

# otter

An econometrics and research-workflow library built on pandas.

- Features: Pond and pools, transforms, the simulation module, the experiment module.
- Installation: `pip install otter` with optional extras `otter[duckdb]` and `otter[plots]`.
- Note: otter-grader provides a top-level otter module; they belong in separate environments.

## Installation

```bash
pip install otter
```

Two optional extras:

```bash
pip install "otter[duckdb]"   # create_pool(where="...") runs SQL through duckdb
pip install "otter[plots]"    # kaleido, for plotly's static image export
```

From a checkout, with the test dependencies:

```bash
pip install -e ".[dev]"
```

## Quick Start

```python
import numpy as np
from otter import Pond
from otter import mean_center, log_transform, z_score

def clean(df):
    df.columns = df.columns.str.lower().str.strip()
    df = df.dropna(subset=["income", "age", "education"])
    df["female"] = (df["gender"] == "F").astype(int)
    return df

# Initialize from from a CSV with a cleaning function
pond = Pond("survey_data.csv", clean)

# Transform with named functions from transforms.py
pond.normalize_and_attach("income", log_transform, "log_income")
pond.normalize_and_attach("age", mean_center, "age_centered")

# Create a working subset
pond.create_pool(lambda df: (df["age"] >= 18) & (df["employed"] == 1))

# Set up variables from the subset
pond.set_dependent("log_income", full=False)
pond.add_independents("age_centered", "education", full=False)
pond.add_controls("female", full=False)

# Retrieve design matrix and outcome vector
X = pond.get_X()
y = pond.get_y()

# Or get a frozen snapshot with full metadata
spec = pond.get_spec()
```

Documentation
- Pond API: https://github.com/iasolb/otter/blob/main/docs/pond.md
- Transforms Reference: https://github.com/iasolb/otter/blob/main/docs/transforms.md
- Simulation Module API: https://github.com/iasolb/otter/blob/main/docs/simulation.md
- Experiment Module: https://github.com/iasolb/otter/blob/main/docs/experiment.md
- Example Workflows (full): https://github.com/iasolb/otter/blob/main/docs/examples.md
- Repository Structure: https://github.com/iasolb/otter/blob/main/docs/design.md
- Design Notes: https://github.com/iasolb/otter/blob/main/docs/design.md
- Learning it: https://github.com/iasolb/otter/blob/main/docs/index.md
- Start here: https://github.com/iasolb/otter/blob/main/docs/index.md

Contributing
- `pip install -e ".[dev]"`, then `pytest`.

License
- MIT, see LICENSE
