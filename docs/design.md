# Repository Structure and Design Notes

### Repository Structure

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

Teaching material is not here: it lives in
[research-kit/notebooks](https://github.com/iasolb/research-kit/tree/main/notebooks),
data loaders.

### Design Notes

**Source mode locking.** The `set_dependent`, `add_independents`, and
`add_controls` methods all accept a `full` parameter. The first call locks
the source mode to either `"full"` or `"subset"`. Subsequent calls that use
a different mode raise `ValueError` immediately rather than silently mixing
columns from different DataFrames. `clear_caches()` resets the lock.

**Guard pattern.** Every method that accesses data checks `is not None` (not
bare truthiness, which raises `ValueError` on DataFrames), handles both
`full=True` and `full=False` branches explicitly, and bails early with a
printed message when the needed dataset isn't available.

**ModelSpec as bridge.** `Pond` produces a frozen `ModelSpec` dataclass via
`get_spec()`. The simulation module consumes it via
`Simulation.from_spec()`. The dependency flows one direction: `simulation.py`
can accept a `ModelSpec`, but does not import from `pond.py`.
`pond.py` knows nothing about simulations.

**Distribution registry.** `_DISTRIBUTION_REGISTRY` maps string names to
draw functions, scipy distributions, and parameter translation maps. Adding
a new distribution is a single dictionary insertion: no other code changes
are required. Correlated draws use a Gaussian copula (Cholesky
decomposition) to produce correlated samples with the correct marginals.

**Sensitivity analysis.** Includes one-at-a-time sweeps, tornado charts, and
variance-based Sobol indices via the Saltelli sampling scheme.
