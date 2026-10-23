# Simulation module

`simulation.py` provides a Monte Carlo framework for models with uncertain inputs. `Pond.get_spec()` and `Simulation.from_spec()` fit distributions from observed data, infer the correlation structure, and create a simulation.

```python
from otter import Pond
from otter import Simulation

pond = Pond("labor_data.csv", clean)
pond.normalize_and_attach("income", log_transform, "log_income")
pond.set_dependent("log_income")
pond.add_independents("education", "experience")
pond.add_controls("female")

spec = pond.get_spec()

sim = Simulation.from_spec(
    spec,
    model=lambda row: 8.0 + 0.08 * row["education"] + 0.02 * row["experience"],
    n_iterations=10_000,
    seed=42,
)
result = sim.run()
```

The module supports sensitivity analysis, scenario comparison, convergence diagnostics, and plotting.

# Simulation Module API

## `DistributionSpec(name, dist_type, params, empirical_data=None)`

Define an uncertain variable and its probability distribution. Construction validates the distribution type and required parameters.

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

## `InputManager`

Collect uncertain variables, fit distributions from data, manage correlation, and draw samples.

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

When a correlation matrix is set, draws use a Gaussian copula with Cholesky decomposition and an inverse-CDF transform to generate correlated samples with the specified marginal distributions. Without a correlation matrix, draws are independent.

## `ModelFunction(func, vectorized=False)`

Wrap a user-supplied model function.

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

## `MonteCarloEngine(inputs, model, n_iterations=10_000, seed=None)`

Run the simulation loop.

```python
engine = MonteCarloEngine(mgr, model, n_iterations=10_000, seed=42)
result = engine.run()
result = engine.run(store_draws=False)  # save memory on large runs
```

## `SimulationResult`

Store simulation outcomes and summary statistics.

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

## `Simulation(variables, model, *, n_iterations=10_000, seed=None, ...)`

The top-level facade connects the simulation components. Use `DistributionSpec` lists for manual configuration or `Simulation.from_spec()` with a `ModelSpec` from `Pond`.

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
    correlation_matrix=corr_matrix,  # optional
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

Plotting uses `SimulationPlotter` rather than the facade, keeping plotting dependencies separate from the simulation engine. See [Plotting](#plotting).

## `Simulation.from_spec(spec, model, *, dist_type, overrides, include_dependent, ...)`

Build a `Simulation` from a `ModelSpec`. The method fits distributions from observed data, infers the correlation matrix, and returns a ready-to-run simulation.

Two modes are available:

- **Standard:** provide `model` and set `include_dependent=False`. Distributions are fit to independents and controls, and the model function generates outcomes from simulated inputs.
- **Joint distribution:** set `model=None` and `include_dependent=True`. Distributions are fit to all variables, including the dependent variable, and the simulation returns correlated draws without applying a model.

Providing both `model` and `include_dependent=True` raises `ValueError`.

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

## Sensitivity Analysis

Access sensitivity analysis through `sim.sensitivity` or by constructing `SensitivityAnalyzer(engine)` directly.

```python
# Tornado: which variable drives the most swing?
tornado = sim.sensitivity.tornado()
# Returns DataFrame: variable, low_value, high_value, low_outcome, high_outcome, swing
# Sorted by swing descending

# One-at-a-time: sweep a single variable across its range
oat = sim.sensitivity.one_at_a_time("revenue", n_steps=20)
# Returns DataFrame: variable_value, outcome

# Sobol indices: variance-based global sensitivity
sobol = sim.sensitivity.sobol_indices(n_samples=5_000, seed=99)
# Returns DataFrame: variable, S1, S1_conf, sorted by S1 descending
```

## Scenario Comparison

Define named scenarios using distribution parameter overrides and compare their outcomes with the baseline:

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

Specify only parameters that differ from the base case.

## Convergence Diagnostics

Check whether a simulation has run a sufficient number of iterations:

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

## Plotting

Each plot method is a static method on `SimulationPlotter` and returns a Plotly `Figure`. Call methods on the class without creating an instance.

```python
from otter import SimulationPlotter

fig = SimulationPlotter.histogram(result)                         # distribution with CI shading
fig = SimulationPlotter.cumulative_density(result)                # empirical CDF with percentile markers
fig = SimulationPlotter.convergence_plot(result.outcomes)         # running mean ± SE
fig = SimulationPlotter.tornado_chart(tornado)                    # sensitivity swings
fig = SimulationPlotter.scenario_comparison(results)              # overlaid KDE curves
fig = SimulationPlotter.histogram_comparison(results)             # overlaid histograms
fig = SimulationPlotter.tornado_comparison([t1, t2], ["a", "b"])  # side-by-side tornados

fig.show()                              # interactive
fig.write_html("output.html")           # standalone page, no extra install
fig.write_image("output.png", scale=2)  # static image, needs otter[plots] (kaleido)
```

## Supported Distributions

Add distributions by inserting an entry into `_DISTRIBUTION_REGISTRY` at the top of `simulation.py`. Each entry defines sample drawing, parameter validation, fitting from data, and inverse-CDF transformation for correlated draws.
