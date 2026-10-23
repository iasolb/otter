# Example Workflows (full)

## OLS Regression with statsmodels

This example specifies a Mincer wage equation with log wages, centered experience, and a squared term.

```python
import numpy as np
import statsmodels.api as sm
from otter import Pond, log_transform, mean_center, square

def clean(df):
    df.columns = df.columns.str.lower()
    df["female"] = (df["gender"] == "F").astype(int)
    return df.dropna(subset=["wage", "education", "experience", "age", "gender"])

pond = Pond("labor_data.csv", clean)

pond.normalize_and_attach("wage", log_transform, "log_wage")
pond.normalize_and_attach("experience", mean_center, "exp_centered")
pond.attach("exp_centered_sq", square(pond.data["exp_centered"]))

pond.set_dependent("log_wage")
pond.add_independents("education", "exp_centered", "exp_centered_sq")
pond.add_controls("female")

X = sm.add_constant(pond.get_X())
y = pond.get_y()

model = sm.OLS(y, X).fit()
print(model.summary())
```

## Random Forest with scikit-learn

This example prepares features and standardized inputs for customer churn prediction.

```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from otter import Pond, z_score, log1p_transform, safe_ratio

pond = Pond("customer_data.csv", clean)

pond.calculate_and_attach(["revenue", "visits"], safe_ratio("revenue", "visits"), "rev_per_visit")
pond.normalize_and_attach("tenure", z_score, "tenure_z")
pond.normalize_and_attach("support_tickets", log1p_transform, "log_tickets")

pond.set_dependent("churned")
pond.add_independents("rev_per_visit", "tenure_z", "log_tickets")
pond.add_controls("gender_code", "region_code")

X = pond.get_X().fillna(0)
y = pond.get_y()

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
rf = RandomForestClassifier(n_estimators=200, random_state=42)
rf.fit(X_train, y_train)
print(classification_report(y_test, rf.predict(X_test)))
```

## Heckman Selection Model (Two-Step)

This example uses an inverse Mills ratio to account for selection into observed wages.

```python
import statsmodels.api as sm
from scipy.stats import norm
from otter import Pond, mean_center, log_transform

pond = Pond("labor_survey.csv", clean)
pond.normalize_and_attach("age", mean_center, "age_centered")

# Step 1: Probit on full sample
pond.set_dependent("employed")
pond.add_independents("age_centered", "education")
pond.add_controls("married", "children")

probit = sm.Probit(pond.get_y(), sm.add_constant(pond.get_X())).fit(disp=0)
pond.attach("imr", norm.pdf(probit.fittedvalues) / norm.cdf(probit.fittedvalues))

# Step 2: OLS on employed subset with IMR correction
pond.clear_caches()
pond.create_pool(lambda df: df["employed"] == 1)
pond.normalize_and_attach("wage", log_transform, "log_wage", full=False)

pond.set_dependent("log_wage", full=False)
pond.add_independents("age_centered", "education", full=False)
pond.add_controls("imr", full=False)

ols = sm.OLS(pond.get_y(), sm.add_constant(pond.get_X())).fit()
print(ols.summary())
```

## Monte Carlo Portfolio Simulation

This example simulates a venture portfolio's three-year value under uncertainty about growth, churn, market multiples, and discount rates.

```python
from otter import Simulation, DistributionSpec, Scenario, SimulationPlotter

def portfolio_value(row):
    base_arr = 33.0 * 12
    net_growth = row["growth_rate"] - row["churn_rate"]
    projected_arr = base_arr * (1 + net_growth) ** 3
    terminal = projected_arr * row["revenue_multiple"]
    return terminal / (1 + row["discount_rate"]) ** 3

sim = Simulation(
    variables=[
        DistributionSpec("growth_rate",       "normal",     {"mean": 0.40, "std": 0.15}),
        DistributionSpec("churn_rate",        "beta",        {"a": 2, "b": 30}),
        DistributionSpec("revenue_multiple",  "triangular",  {"left": 3, "mode": 8, "right": 20}),
        DistributionSpec("discount_rate",     "normal",     {"mean": 0.12, "std": 0.03}),
    ],
    model=portfolio_value,
    n_iterations=10_000,
    seed=42,
)

result = sim.run()
tornado = sim.sensitivity.tornado()

results = sim.compare_scenarios([
    Scenario("bull", overrides={"revenue_multiple": {"left": 8, "mode": 15, "right": 30}}),
    Scenario("bear", overrides={"revenue_multiple": {"left": 2, "mode": 4, "right": 8}}),
])

SimulationPlotter.histogram(result).write_html("distribution.html")
SimulationPlotter.tornado_chart(tornado).write_html("tornado.html")
SimulationPlotter.scenario_comparison(results).write_html("scenarios.html")
```
