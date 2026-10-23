# otter

An econometrics and research-workflow library built on pandas.

[![PyPI version](https://img.shields.io/pypi/v/otter)](https://pypi.org/project/otter/)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/otter)](https://pypi.org/project/otter/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://github.com/iasolb/otter/actions/workflows/tests.yml/badge.svg)](https://github.com/iasolb/otter/actions/workflows/tests.yml)

## Features

- **Pond and pools:** manage datasets, model variables, and working subsets.
- **Transforms:** attach reusable single- and multi-column transformations.
- **Simulation module:** run Monte Carlo analysis, sensitivity analysis, and scenarios.
- **Experiment module:** calculate sample sizes, assign groups, and compare outcomes.

## Installation

```bash
pip install otter
```

Optional dependencies are available through these extras:

```bash
pip install "otter[duckdb]"   # create_pool(where="...") runs SQL through duckdb
pip install "otter[plots]"    # kaleido, for plotly's static image export
```

`otter-grader` also provides a top-level `otter` module, so the two packages belong in separate environments.

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

# Initialize from a CSV with a cleaning function
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

## Documentation

The facade exposes sub-components directly:

```python
sim.engine
sim.input_manager
sim.sensitivity
sim.convergence
SimulationPlotter.histogram(result)
```

- [Documentation index](https://github.com/iasolb/otter/blob/main/docs/index.md)
- [Pond API](https://github.com/iasolb/otter/blob/main/docs/pond.md)
- [Transforms reference](https://github.com/iasolb/otter/blob/main/docs/transforms.md)
- [Simulation module](https://github.com/iasolb/otter/blob/main/docs/simulation.md)
- [Experiment module](https://github.com/iasolb/otter/blob/main/docs/experiment.md)
- [Example workflows](https://github.com/iasolb/otter/blob/main/docs/examples.md)
- [Repository structure and design notes](https://github.com/iasolb/otter/blob/main/docs/design.md)

## Contributing

Install the development dependencies and run the test suite:

```bash
pip install -e ".[dev]"
```

```bash
pytest
```

## License

otter is licensed under the [MIT License](LICENSE).
