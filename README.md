# otter

An econometrics and research-workflow library built on pandas.

[![PyPI version](https://badge.fury.io/py/otter.svg)](https://pypi.org/project/otter/)
[![Python versions](https://img.shields.io/pypi/pyversions/otter.svg)](https://www.python.org/)
[![MIT License](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/iasolb/otter/blob/main/LICENSE)
[![Tests](https://github.com/iasolb/otter/actions/workflows/test.yml/badge.svg)](https://github.com/iasolb/otter/actions)

Otter provides a modular toolkit for econometrics and research workflows, built on top of pandas.

## Features
- Pond and pools
- Column transforms
- Monte Carlo simulation with sensitivity analysis
- Experiment design

## Installation
- Install from PyPI
  - pip install otter
- Install with development dependencies
  - pip install -e ".[dev]"
- Note: otter-grader is optional for evaluation workflows; install separately if you plan to use it.

## Quick Start
```
# Quick Start sample (unchanged from the original README)
# Initialize from a CSV, and perform a simple workflow as described in the docs.
```

## Documentation
Documentation pages (absolute links):
- Pond API: https://github.com/iasolb/otter/blob/main/docs/pond.md
- Transforms: https://github.com/iasolb/otter/blob/main/docs/transforms.md
- Simulation: https://github.com/iasolb/otter/blob/main/docs/simulation.md
- Experiments: https://github.com/iasolb/otter/blob/main/docs/experiment.md
- Examples: https://github.com/iasolb/otter/blob/main/docs/examples.md
- Design: https://github.com/iasolb/otter/blob/main/docs/design.md
- Getting started: https://github.com/iasolb/otter/blob/main/docs/index.md

## Contributing
```bash
pip install -e ".[dev]"
pytest
```

## License
MIT License — https://github.com/iasolb/otter/blob/main/LICENSE
