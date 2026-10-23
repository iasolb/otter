# Experiment module

The experiment module provides sample-size planning, group assignment, and post-experiment comparison.

```python
from otter.experiment import sample_size_for_mean, assign_groups, compare_groups

# How many units to detect a 2% lift on a metric averaging 120, sd 300?
size = sample_size_for_mean(baseline_mean=120, baseline_sd=300, min_lift_pct=2)
size.treatment_n, size.control_n, size.total_n

# Randomise reproducibly, then measure.
assign_groups(user_ids, {"control": 0.5, "treatment": 0.5}, seed=1)
compare_groups(data, group_col="group", metric_cols=["revenue", "orders"],
               control="control", treatment="treatment")
```

Comparisons use Welch's t-test and Benjamini-Hochberg correction across metrics.

- **`cuped_pre=`** uses a pre-period covariate to reduce variance. The covariate must be measured before assignment.
- **`pretest_balance()`** evaluates pre-period metrics to assess randomization. An empty pre-period is reported as uninformative.

`detectable_lift_for_mean()` and `detectable_lift_for_proportion()` estimate detectable effects for a fixed sample size.
