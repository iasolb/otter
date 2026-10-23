"""The README and API docs name attributes that must exist.

It listed `sim.plot` on the Simulation facade and said plots were matplotlib
Figures saved with `.savefig`. There is no `sim.plot` (AttributeError), and
the plots are plotly figures from static `SimulationPlotter` methods
(2026-10-17). These tests read the names out of README.md and docs/, so a new
wrong claim fails the same way.
"""

import re
from pathlib import Path

from otter import DistributionSpec, Simulation, SimulationPlotter

ROOT = Path(__file__).resolve().parent.parent
DOCUMENTATION = "\n".join(
    path.read_text(encoding="utf-8")
    for path in [ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md"))]
)
FENCE = "`" * 3  # spelled out so this file can be quoted inside a fenced block


def _facade_block() -> str:
    after = DOCUMENTATION.split("The facade exposes sub-components directly:", 1)[1]
    return after.split(FENCE, 2)[1]


def test_every_facade_attribute_the_readme_lists_exists():
    named = re.findall(r"^sim\.(\w+)", _facade_block(), flags=re.M)
    assert named, "the facade block was not found in README.md or docs/"
    sim = Simulation(
        variables=[DistributionSpec("x", "normal", {"mean": 0, "std": 1})],
        model=lambda row: row["x"],
        n_iterations=10,
        seed=1,
    )
    missing = [attr for attr in named if not hasattr(sim, attr)]
    assert missing == []


def test_every_plotter_method_the_readme_calls_exists():
    named = set(re.findall(r"SimulationPlotter\.(\w+)\(", DOCUMENTATION))
    assert named, "no SimulationPlotter calls found in README.md or docs/"
    missing = sorted(name for name in named if not hasattr(SimulationPlotter, name))
    assert missing == []


def test_the_readme_never_describes_plots_as_matplotlib():
    assert "sim.plot." not in DOCUMENTATION         # a call through the missing attribute
    assert ".savefig(" not in DOCUMENTATION
    assert "matplotlib" not in DOCUMENTATION
