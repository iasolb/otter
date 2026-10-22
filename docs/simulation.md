# Simulation Module API

`simulation.py` provides a Monte Carlo simulation framework for running
models under uncertainty. The primary integration path is `get_spec()` +
`Simulation.from_spec()`: it fits distributions from your observed data,
infers the correlation structure, and returns a ready-to-run simulation,
no manual wiring needed.

### `DistributionSpec(name, dist_type, params, empirical_data=None)`

Defines an uncertain variable and its probability distribution. Validation
happens on construction: missing params or unknown distribution types
raise immediately.

| `dist_type` | Required `params` |
|-------------|-------------------|
| `"normal"` | `{"mean": ..., "std": ...}` |
| `"uniform"` | `{"low": ..., "high": ...}` |
| `"lognormal"` | `{"mean": ..., "sigma": ...}` |
| `"beta"` | `{"a": ..., "b": ...}` |
| `"triangular"` | `{"left": ..., "mode": ..., "right": ...}` |
| `"exponential"` | `{"scale": ...}` |
| `"empirical"` | `empirical_data=np.array([...])` |

```python
DistributionSpec("revenue",  "normal",   {"mean": 1e6, "std": 2e5})
DistributionSpec("cost",     "uniform",  {"low": 4e5, "high": 7e5})
DistributionSpec("duration", "empirical", empirical_data=observed_array)
```

### `InputManager`

Collects uncertain variables, fits distributions from data, manages
correlation, and draws samples.

```python
mgr = InputManager()

# Register manually
mgr.add_variable(DistributionSpec("x", "normal", {"mean": 0, "std": 1}))
mgr.add_variables([...])
mgr.remove_variable("x")

# Fit from observed data
mgr.fit_from_data(df, ["col_a", "col_b"], dist_type="normal")
mgr.fit_from_data(df, ["col_c"], dist_type="empirical")

# Correlation
mgr.set_correlation_matrix(np.array([[1.0, 0.6], [0.6, 1.0]]))
mgr.infer_correlation_from_data(df)

# Draw samples: returns DataFrame of shape (n, n_variables)
draws = mgr.draw(10_000, seed=42)
```

When a correlation matrix is set, draws use a Gaussian copula (Cholesky
decomposition + inverse-CDF transform) to produce correlated samples with
the correct marginal distributions. Without a correlation matrix, draws are
independent.

### `ModelFunction(func, vectorized=False)`

Wraps the user-supplied model function.

```python
# Row-wise: receives a pd.Series per iteration
model = ModelFunction(lambda row: row["revenue"] - row["cost"])

# Vectorized: receives the full DataFrame, returns an array (faster)
model = ModelFunction(
    lambda df: (df["revenue"] - df["cost"]).values,
    vectorized=True,
)

# Multi-output: return a dict per row
def multi(row):
    profit = row["revenue"] - row["cost"]
    return {"profit": profit, "margin": profit / row["revenue"]}
model = ModelFunction(multi)
```

### `MonteCarloEngine(inputs, model, n_iterations=10_000, seed=None)`

Runs the simulation loop.

```python
engine = MonteCarloEngine(mgr, model, n_iterations=10_000, seed=42)
result = engine.run()
result = engine.run(store_draws=False)  # save memory on large runs
```

### `SimulationResult`

Container for outcomes and summary statistics.

```python
result.outcomes         # np.ndarray of model outputs
result.draws            # DataFrame of input draws (if stored)

result.summarize()      # compute and cache all stats, returns dict
result.mean             # cached after summarize()
result.median
result.std
result.ci_lower         # 95% CI by default
result.ci_upper
result.percentiles      # {1: ..., 5: ..., 10: ..., 25: ..., 50: ..., 75: ..., 90: ..., 95: ..., 99: ...}

result.to_dataframe()   # draws + outcomes in one exportable DataFrame
```

### `Simulation(variables, model, *, n_iterations=10_000, seed=None, ...)` 

Top-level facade that wires everything together. Use this with manual
`DistributionSpec` lists, or use `Simulation.from_spec()` with a `ModelSpec`
from `Pond`.

```python
sim = Simulation(
    variables=[
        DistributionSpec("growth",   "normal",     {"mean": 0.4, "std": 0.15}),
        DistributionSpec("churn",    "beta",        {"a": 2, "b": 30}),
        DistributionSpec("multiple", "triangular",  {"left": 3, "mode": 8, "right": 20}),
    ],
    model=portfolio_value,
    n_iterations=10_000,
    seed=42,
)

result = sim.run()
```

The facade exposes sub-components directly:

```python
sim.engine                  # MonteCarloEngine
sim.input_manager           # InputManager
sim.sensitivity             # SensitivityAnalyzer
sim.convergence             # ConvergenceDiagnostics (class reference)
```

Plotting is not on the facade: it lives in `SimulationPlotter` (see
[Plotting](#plotting)), so the simulation engine carries no plotting
dependency.

### `Simulation.from_spec(spec, model, *, dist_type, overrides, include_dependent, ...)`

Builds a `Simulation` from a `ModelSpec`. Fits distributions from the spec's
observed data, infers the correlation matrix, and returns a ready-to-run
simulation.

Two modes:

- Standard (default): `model` provided, `include_dependent=False`. Fits
  distributions on independents + controls. The model function produces
  outcomes from simulated inputs.
- Joint distribution: `model=None`, `include_dependent=True`. Fits
  distributions on all variables including dependent. Returns correlated
  draws with no model applied.

Passing both `model` and `include_dependent=True` raises `ValueError`.

```python
# Standard mode
sim = Simulation.from_spec(spec, model=my_func, seed=42)

# With per-column overrides
sim = Simulation.from_spec(
    spec, model=my_func,
    overrides={"income": {"dist_type": "lognormal"}},
)

# Joint distribution mode
sim = Simulation.from_spec(spec, include_dependent=True, dist_type="empirical")
```

### Sensitivity Analysis

Accessed via `sim.sensitivity` or by constructing
`SensitivityAnalyzer(engine)` directly.

```python
# Tornado: which variable drives the most swing?
tornado = sim.sensitivity.tornado()
# Returns DataFrame: variable, low_value, high_value, low_outcome, high_outcome, swing
#+ Sorted by swing descending

# One-at-a-time: sweep a single variable across its range
oat = sim.sensitivity.one_at_a_time("revenue", n_steps=20)
# Returns DataFrame: variable_value, outcome

# Sobol indices: variance-based global sensitivity
sobol = sim.sensitivity.sobol_indices(n_samples=5_000, seed=99)
# Returns DataFrame: variable, S1, S1_conf, sorted by S1 descending
```

### Scenario Comparison

Define named scenarios with distribution parameter overrides, then compare
outcomes against baseline:

```python
from otter import Scenario

scenarios = [
    Scenario("bull_market", overrides={
        "multiple": {"left": 8, "mode": 15, "right": 30},
    }),
    Scenario("bear_market", overrides={
        "multiple": {"left": 2, "mode": 4, "right": 8},
        "growth": {"mean": 0.20},
    }),
]

# Full results
results = sim.compare_scenarios(scenarios)
# Returns {"baseline": SimulationResult, "bull_market": ..., "bear_market": ...}

# Summary table
summary = sim.compare_scenarios_summary(scenarios)
# Returns DataFrame: scenario, mean, median, std, ci_lower, ci_upper, min, max
```

Only the parameters that differ need to be specified: everything else stays at the base case.

### Convergence Diagnostics

Check whether the simulation ran enough iterations:

```python
# Quick report
report = sim.check_convergence(result)
# {"is_converged": True, "relative_se": 0.0051, "current_n": 10000, "suggested_n": 39261}

# Detailed: running statistics
running = ConvergenceDiagnostics.running_statistics(result.outcomes)
# DataFrame: iteration, cumulative_mean, cumulative_std

# Did it converge?
ConvergenceDiagnostics.is_converged(result.outcomes, window=1000, tolerance=0.01)

# How many iterations do I need for 0.5% precision?
ConvergenceDiagnostics.suggest_n(result.outcomes, target_tolerance=0.005)

# Snapshots at increasing N
snapshots = sim.engine.run_convergence()
# [SimulationResult(n=100), ..., SimulationResult(n=10000)], all pre-summarized
```

### Plotting

Every plot method is a static method on `SimulationPlotter` and returns a
plotly `Figure`. There is no `sim.plot`: call the methods on the class, no
instance needed.

```python
from otter import SimulationPlotter

fig = SimulationPlotter.histogram(result)                         # distribution with CI shading
fig = SimulationPlotter.cumulative_density(result)                # empirical CDF with percentile markers
fig = SimulationPlotter.convergence_plot(result.outcomes)         # running mean ± SE
fig = SimulationPlotter.tornado_chart(tornado)                    # sensitivity swings
fig = SimulationPlotter.scenario_comparison(results)              # overlaid KDE curves
fig = SimulationPlotter.histogram_comparison(results)             # overlaid histograms

fig.show()                              # interactive
fig.write_html("output.html")           # standalone page, no extra install
fig.write_image("output.png", scale=2)  # static image, needs otter[plots] (kaleido)
```

### Supported Distributions

New distributions can be added by inserting an entry into
`_DISTRIBUTION_REGISTRY` at the top of `simulation.py`. Each entry defines
how to draw samples, validate parameters, fit from data, and transform
through the inverse-CDF for correlated draws. No other code changes are
required.
