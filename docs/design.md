# Repository Structure

```
otter/
├── pyproject.toml         # Package metadata (pip install .)
├── requirements.txt       # Dependencies (core + optional)
├── LICENSE                # MIT
├── .gitignore
├── README.md
├── src/otter/
│   ├── __init__.py        # public API re-exports
│   ├── pond.py              # Core data handling class + ModelSpec
│   ├── experiment.py      # Power, assignment, lift, CUPED, balance checks
│   ├── transforms.py      # Reusable single- and multi-column transforms
│   ├── simulation.py      # Monte Carlo simulation module
│   └── plotter.py         # Plotly plotting for simulation results
└── tests/
    ├── test_pond.py       # Pond and transforms, on synthetic data
    └── test_experiment.py # design, assignment, lift, CUPED, balance
```

Teaching notebooks are maintained in [research-kit](https://github.com/iasolb/research-kit/tree/main/notebooks), where examples use otter with the associated data loaders.

# Design Notes

**Source mode locking.** The `set_dependent`, `add_independents`, and `add_controls` methods accept a `full` parameter. The first call sets the source mode to either `"full"` or `"subset"`. Calls using a different mode raise `ValueError`. `clear_caches()` resets the lock.

**Guard pattern.** Methods that access data check for `None`, handle `full=True` and `full=False` explicitly, and return early with a message when required data is unavailable. This avoids DataFrame truth-value ambiguity.

**ModelSpec as bridge.** `Pond` produces a frozen `ModelSpec` dataclass through `get_spec()`. The simulation module consumes it through `Simulation.from_spec()`. The dependency flows in one direction: `simulation.py` accepts a `ModelSpec` without importing from `pond.py`, and `pond.py` does not depend on simulations.

**Distribution registry.** `_DISTRIBUTION_REGISTRY` maps distribution names to draw functions, scipy distributions, and parameter translation maps. Adding a distribution requires an entry in the registry. Correlated draws use a Gaussian copula: Cholesky decomposition is applied to standard normal draws, followed by each variable's inverse CDF.

**Sensitivity analysis.** The module includes one-at-a-time sweeps, tornado charts, and variance-based Sobol indices through the Saltelli sampling scheme.
