# Reference

## Documentation

## Pages

- [Documentation index](index.md)
- [Pond API](pond.md)
- [Transforms Reference](transforms.md)
- [Simulation module](simulation.md)
- [Experiment module](experiment.md)
- [Example Workflows (full)](examples.md)
- [Repository Structure and Design Notes](design.md)

## Learning it

The notebooks are maintained in [research-kit](https://github.com/iasolb/research-kit), alongside the data loaders used in the examples. The learning paths cover an introduction to pandas workflows and more advanced research workflows.

## Start here

The `02-your-first-question` notebook in [research-kit/notebooks](https://github.com/iasolb/research-kit/tree/main/notebooks) demonstrates an end-to-end workflow, from formulating a question to interpreting a regression.

## Running Tests

Run the test suite from the repository root:

```bash
pytest tests/test_pond.py -v
```

The test suite covers the `Pond` class and the functions in `transforms.py` using synthetic data.

```bash
pytest tests/test_pond.py::TestSubset -v
pytest tests/test_pond.py::TestTransforms::test_z_score -v
```
